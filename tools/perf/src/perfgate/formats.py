"""Parsery formatów pomiarowych z repo (kamion).

Każdy format ma zarejestrowaną wersję. Nieznane kolumny/wartości -> ParseError
z komunikatem (zasada: żadnych cichych pominięć — telefon jest prawdą, ale
narzędzie nie może zgadywać, co znaczy kolumna, której nie zna).

Formaty (wszystkie wyprowadzone z `scripts/device-metrics.ps1`,
`scripts/build-android.ps1` i artefaktów w `artifacts/perf-low-r1|r2`):

1. frametimes.csv v1 — wiersz nagłówka dokładnie:
   `frame,t_s,frame_ms,cpu_main_ms,gpu_ms,render_scale,mirror_n,ab`
   Jednostki: t_s sekundy; frame_ms / cpu_main_ms / gpu_ms milisekundy
   (gpu_ms = 0.000 oznacza „sterownik nie raportuje" — device-metrics.ps1
   odrzuca te próbki przy percentylach GPU). `ab` może być puste.
2. metrics.json v1 — wyjście `scripts/device-metrics.ps1` (klucze: serial,
   timestamp, device, pssMb, batteryTempC, thermalStatus, frameTime,
   gpuMs, cpuMainMs, gameSummary).
3. summary.json v1 — wyjście diagnostyki gry (Boot DiagnosticsSampler):
   build, device, gpu, qualityTier, targetFps, resolution, sessionSeconds,
   frames, meanFps, p50Ms..., batteryTempC, thermalStatus, pssKb, renderScale.
4. diag-logcat.txt v1 / logcat.txt v1 — `adb logcat -v threadtime`,
   interesujące nas linie: `[BOOT] ... klucz=wartość ...` oraz
   `[DIAG] t=3s tier=Low target=240 fps=17.8 p50=33.33 ... temp=27.5C
   thermal=0 headroom=0.50 pss=889MB scale=0.75 ...` (wszystkie pola DIAG
   parsowane jako klucz=wartość; `gpu=-` = brak danych).
5. battery.txt v1 — `dumpsys battery`: `level: 80`, `temperature: 276`
   (dziesiąte stopnia C — dzielimy przez 10).
6. thermal.txt v1 — `dumpsys thermalservice`: `Thermal Status: 0`,
   `Temperature{mValue=37.5, mType=0, mName=AP, mStatus=0}` (mValue w °C,
   mStatus = poziom throttlingu tego czujnika; 0 = brak).
7. meminfo.txt v1 — `dumpsys meminfo <pkg>`: wiersz `TOTAL PSS: <kB>`
   albo `TOTAL <kB> ...` (pierwsza liczba = PSS total w kB).
8. gfxinfo.txt v1 — `dumpsys gfxinfo <pkg>` (sekcja „Profile data in ms"
   może zawierać statystyki klatek; brak sekcji = brak danych, nie błąd).
9. gate3-result.json v1 — schema `truck-sim-pl/gate3-result/1`
   (wynik przejazdu gate3; używany tylko jako metadane przebiegu).
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


class ParseError(ValueError):
    """Błąd parsowania formatu — zawiera nazwę pliku i komunikat."""


FRAMETIMES_V1_COLUMNS = (
    "frame",
    "t_s",
    "frame_ms",
    "cpu_main_ms",
    "gpu_ms",
    "render_scale",
    "mirror_n",
    "ab",
)


@dataclass
class FrameRow:
    frame: int
    t_s: float
    frame_ms: float
    cpu_main_ms: float
    gpu_ms: float
    render_scale: float
    mirror_n: float
    ab: str


@dataclass
class DiagSample:
    """Jedna linia [DIAG] z logcata (wszystkie pola klucz=wartość)."""

    wall_time: str
    t_s: float
    fields: dict[str, str] = field(default_factory=dict)

    def get_float(self, key: str) -> float | None:
        v = self.fields.get(key)
        if v is None or v == "-":
            return None
        m = _LEADING_FLOAT_RE.match(v)
        return float(m.group(0)) if m else None


@dataclass
class BootInfo:
    wall_time: str
    fields: dict[str, str] = field(default_factory=dict)


def _err(path: Path, msg: str) -> ParseError:
    return ParseError(f"{path}: {msg}")


def parse_frametimes_csv(path: Path) -> list[FrameRow]:
    """frametimes.csv v1. Nieznana kolumna -> ParseError."""
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise _err(path, "pusty plik (brak nagłówka)")
        header = [h.strip() for h in header]
        unknown = [h for h in header if h not in FRAMETIMES_V1_COLUMNS]
        if unknown:
            raise _err(
                path,
                f"nieznane kolumny {unknown}; znany format v1: {list(FRAMETIMES_V1_COLUMNS)}",
            )
        missing = [c for c in FRAMETIMES_V1_COLUMNS if c not in header]
        if missing:
            raise _err(path, f"brak wymaganych kolumn {missing}")
        idx = {c: i for i, c in enumerate(header)}
        rows: list[FrameRow] = []
        for lineno, rec in enumerate(reader, start=2):
            if not rec or all(not c.strip() for c in rec):
                continue
            if len(rec) < len(header):
                rec = rec + [""] * (len(header) - len(rec))  # puste końcowe kolumny (np. ab)
            try:
                mirror_raw = rec[idx["mirror_n"]]
                rows.append(
                    FrameRow(
                        frame=int(rec[idx["frame"]]),
                        t_s=float(rec[idx["t_s"]]),
                        frame_ms=float(rec[idx["frame_ms"]]),
                        cpu_main_ms=float(rec[idx["cpu_main_ms"]]),
                        gpu_ms=float(rec[idx["gpu_ms"]]),
                        render_scale=float(rec[idx["render_scale"]]),
                        mirror_n=float(mirror_raw) if mirror_raw.strip() else 0.0,
                        ab=rec[idx["ab"]].strip(),
                    )
                )
            except (ValueError, IndexError) as e:
                raise _err(path, f"wiersz {lineno}: nieparsowalne dane ({e}): {rec!r}")
    if not rows:
        raise _err(path, "brak wierszy danych")
    return rows


def parse_json_file(path: Path) -> dict:
    path = Path(path)
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise _err(path, f"nieparsowalny JSON: {e}")


def parse_metrics_json(path: Path) -> dict:
    """metrics.json v1 (device-metrics.ps1). Walidacja wymaganych kluczy."""
    d = parse_json_file(path)
    required = ("serial", "timestamp", "frameTime")
    missing = [k for k in required if k not in d and k != "frameTime"]
    if missing:
        raise _err(path, f"metrics.json: brak kluczy {missing}")
    return d


_LEADING_FLOAT_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")
_DIAG_RE = re.compile(r"\[DIAG\]\s*(.*)")
_BOOT_RE = re.compile(r"\[BOOT\]\s*(.*)")
_KV_RE = re.compile(r"(\w+)=('[^']*'|\S+)")


def _parse_kv(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in _KV_RE.finditer(text):
        out[m.group(1)] = m.group(2).strip("'")
    return out


def parse_logcat(path: Path) -> tuple[list[BootInfo], list[DiagSample]]:
    """diag-logcat.txt v1 / logcat.txt v1 (`-v threadtime`).

    Zwraca (linie [BOOT], próbki [DIAG]). Linia DIAG bez pola t= -> ParseError.
    """
    path = Path(path)
    boots: list[BootInfo] = []
    diags: list[DiagSample] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            m = _DIAG_RE.search(line)
            if m:
                kv = _parse_kv(m.group(1))
                if "t" not in kv:
                    raise _err(path, f"wiersz {lineno}: [DIAG] bez pola t=: {line!r}")
                t_raw = kv["t"]
                if not t_raw.endswith("s"):
                    raise _err(path, f"wiersz {lineno}: pole t= bez jednostki 's': {t_raw!r}")
                try:
                    t_s = float(t_raw[:-1])
                except ValueError:
                    raise _err(path, f"wiersz {lineno}: nieparsowalne t={t_raw!r}")
                wall = line.split(" ", 2)
                wall_time = f"{wall[0]} {wall[1]}" if len(wall) >= 2 else ""
                diags.append(DiagSample(wall_time=wall_time, t_s=t_s, fields=kv))
                continue
            m = _BOOT_RE.search(line)
            if m:
                wall = line.split(" ", 2)
                wall_time = f"{wall[0]} {wall[1]}" if len(wall) >= 2 else ""
                boots.append(BootInfo(wall_time=wall_time, fields=_parse_kv(m.group(1))))
    return boots, diags


_BATT_LEVEL_RE = re.compile(r"^\s*level:\s*(\d+)\s*$", re.MULTILINE)
_BATT_TEMP_RE = re.compile(r"^\s*temperature:\s*(\d+)\s*$", re.MULTILINE)


def parse_battery_txt(path: Path) -> dict:
    """battery.txt v1. `temperature` jest w dziesiątych °C."""
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    level = _BATT_LEVEL_RE.search(text)
    temp = _BATT_TEMP_RE.search(text)
    if not level or not temp:
        raise _err(path, "battery.txt: brak pól 'level:' lub 'temperature:'")
    return {
        "level_pct": int(level.group(1)),
        "temperature_c": int(temp.group(1)) / 10.0,
    }


_THERMAL_STATUS_RE = re.compile(r"^Thermal Status:\s*(\d+)\s*$", re.MULTILINE)
_TEMP_ENTRY_RE = re.compile(
    r"Temperature\{mValue=([-\d.]+), mType=(\d+), mName=(\w+), mStatus=(\d+)\}"
)


def parse_thermal_txt(path: Path) -> dict:
    """thermal.txt v1. mValue w °C; mStatus = throttling czujnika (0 = brak)."""
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    status = _THERMAL_STATUS_RE.search(text)
    if not status:
        raise _err(path, "thermal.txt: brak wiersza 'Thermal Status:'")
    sensors = [
        {
            "name": m.group(3),
            "type": int(m.group(2)),
            "value_c": float(m.group(1)),
            "status": int(m.group(4)),
        }
        for m in _TEMP_ENTRY_RE.finditer(text)
    ]
    return {"thermal_status": int(status.group(1)), "sensors": sensors}


_MEMINFO_TOTAL_PSS_RE = re.compile(r"TOTAL PSS:\s+(\d+)")
_MEMINFO_TOTAL_RE = re.compile(r"^\s*TOTAL\s+(\d+)\s", re.MULTILINE)


def parse_meminfo_txt(path: Path) -> dict:
    """meminfo.txt v1. PSS total w kB (pierwsza liczba wiersza TOTAL)."""
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    m = _MEMINFO_TOTAL_PSS_RE.search(text) or _MEMINFO_TOTAL_RE.search(text)
    if not m:
        raise _err(path, "meminfo.txt: brak wiersza 'TOTAL PSS:' / 'TOTAL'")
    pss_kb = int(m.group(1))
    return {"pss_kb": pss_kb, "pss_mb": pss_kb / 1024.0}


_GFXINFO_JANKY_RE = re.compile(r"Janky frames:\s*(\d+)\s*\(([\d.]+)%\)")
_GFXINFO_TOTAL_RE = re.compile(r"Total frames rendered:\s*(\d+)")


def parse_gfxinfo_txt(path: Path) -> dict:
    """gfxinfo.txt v1. Sekcja statystyk klatek opcjonalna (brak = null)."""
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    janky = _GFXINFO_JANKY_RE.search(text)
    total = _GFXINFO_TOTAL_RE.search(text)
    return {
        "total_frames": int(total.group(1)) if total else None,
        "janky_frames": int(janky.group(1)) if janky else None,
        "janky_pct": float(janky.group(2)) if janky else None,
    }


FORMATS = {
    "frametimes.csv": ("v1", "frame,t_s,frame_ms,cpu_main_ms,gpu_ms,render_scale,mirror_n,ab; ms oprócz t_s [s]"),
    "metrics.json": ("v1", "wyjście scripts/device-metrics.ps1 (serial, frameTime, gpuMs, pssMb, ...)"),
    "summary.json": ("v1", "wyjście diagnostyki gry (build, qualityTier, targetFps, p50Ms, pssKb, ...)"),
    "diag-logcat.txt": ("v1", "logcat -v threadtime, linie [BOOT]/[DIAG] klucz=wartość"),
    "logcat.txt": ("v1", "logcat -v threadtime (pełny lub przefiltrowany)"),
    "battery.txt": ("v1", "dumpsys battery: level %, temperature dziesiąte °C"),
    "thermal.txt": ("v1", "dumpsys thermalservice: Thermal Status + Temperature{mValue=°C, mStatus=}"),
    "meminfo.txt": ("v1", "dumpsys meminfo: wiersz TOTAL, pierwsza liczba = PSS total kB"),
    "gfxinfo.txt": ("v1", "dumpsys gfxinfo (opcjonalnie Janky frames / Total frames rendered)"),
    "gate3-result.json": ("truck-sim-pl/gate3-result/1", "wynik przejazdu gate3 (metadane przebiegu)"),
}


def load_run_dir(run_dir: Path) -> dict:
    """Wczytuje wszystkie rozpoznane pliki katalogu pomiaru.

    Katalog pomiaru = artifacts/device/<serial>/<ts>/ (lub równoważny,
    np. artifacts/perf-low-r1/diag0/base0). Brak pliku = pole None
    (nie błąd); uszkodzony plik = ParseError.
    """
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        raise _err(run_dir, "katalog pomiaru nie istnieje")
    out: dict = {"dir": run_dir, "files": {}}
    ft = run_dir / "frametimes.csv"
    out["frames"] = parse_frametimes_csv(ft) if ft.exists() else None
    out["files"]["frametimes.csv"] = ft.exists()
    for name, parser in (
        ("metrics.json", parse_metrics_json),
        ("summary.json", parse_json_file),
        ("battery.txt", parse_battery_txt),
        ("thermal.txt", parse_thermal_txt),
        ("meminfo.txt", parse_meminfo_txt),
        ("gfxinfo.txt", parse_gfxinfo_txt),
        ("gate3-result.json", parse_json_file),
    ):
        p = run_dir / name
        if p.exists():
            out[name.removesuffix(".json").removesuffix(".txt")] = parser(p)
            out["files"][name] = True
        else:
            out[name.removesuffix(".json").removesuffix(".txt")] = None
            out["files"][name] = False
    for name in ("diag-logcat.txt", "logcat.txt", "logcat-run.txt"):
        p = run_dir / name
        if p.exists():
            boots, diags = parse_logcat(p)
            out["boots"] = boots
            out["diags"] = diags
            out["files"][name] = True
            break
    else:
        out["boots"] = None
        out["diags"] = None
    return out
