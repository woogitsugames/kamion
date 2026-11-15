"""Tabela A/B GPU z sesji `scripts/gpu-ab-a16.ps1` (ADR 0241, B-113).

Sesja = katalog `artifacts/gpu-ab/<ts>/`:

    session.json                       metadane sesji (serial, tier, fps, apk ...)
    runs/<nazwa>/run.json              {variant, segment, repeat, block, extras, valid, rejectReason,
                                        batteryTempBeforeC, warmupSeconds}; block = klucz pary z bazą
                                        (przebieg bazowy z tym samym block; domyślnie = repeat)
    runs/<nazwa>/frametimes.csv        z telefonu (format v1, perfgate.formats)
    runs/<nazwa>/metrics.json          z device-metrics.ps1 (PSS, temperatura; opcjonalny)

Wynik: `results.csv` (jeden wiersz na przebieg), `summary.csv` (wariant x odcinek: mediany po
powtórzeniach i różnica względem wariantu bazowego z TEGO SAMEGO bloku), `REPORT.md`.

Percentyle liczone jak w `scripts/device-metrics.ps1` (nearest-rank, po odcięciu rozgrzewki).
Liczby w raporcie są pomiarem tylko wtedy, gdy przebiegi pochodzą z telefonu; kolumna
„szacunek" pochodzi z katalogu wariantów (ESTIMATED / UNVERIFIED, ze źródłem).

    uv run --project tools/perf python -m perfgate.gpuab report artifacts/gpu-ab/<ts>
    uv run --project tools/perf python -m perfgate.gpuab catalog --sources game/Assets/_Project
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .formats import FrameRow, ParseError, parse_frametimes_csv
from .metrics import percentile

SCHEMA_CATALOG = "truck-sim-pl/gpu-ab-variants/1"
DEFAULT_CATALOG = Path(__file__).resolve().parents[2] / "gpu-ab-variants.json"
EST_STATUSES = ("REFERENCE", "ESTIMATED", "UNVERIFIED")
ROLES = ("baseline", "lever", "ceiling", "control", "diagnostic")
AB_SETTLE_S = 0.75  # ExtraViewCostMonitor: klatki 0,75 s po przełączeniu A/B nie są liczone
MIN_SAMPLES = 100   # jak gate3-run.ps1: przebieg z mniejszą liczbą klatek nie jest pomiarem
BUDGET_GPU_P95_MS = 33.3  # B-113: GPU p95 A16 Low 34,3-34,5 > 33,3


class GpuAbError(ValueError):
    pass


# ---------------------------------------------------------------- katalog wariantów
def load_catalog(path: Path | None = None) -> dict:
    path = Path(path) if path else DEFAULT_CATALOG
    try:
        cat = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise GpuAbError(f"{path}: nie da się wczytać katalogu wariantów ({e})")
    problems = validate_catalog(cat)
    if problems:
        raise GpuAbError(f"{path}: " + "; ".join(problems))
    return cat


def validate_catalog(cat: dict) -> list[str]:
    """Lista problemów (pusta = katalog poprawny)."""
    out: list[str] = []
    if cat.get("schema") != SCHEMA_CATALOG:
        out.append(f"schema != {SCHEMA_CATALOG}")
    variants = cat.get("variants") or []
    ids = [v.get("id") for v in variants]
    if len(ids) != len(set(ids)):
        out.append("powtórzone id wariantu")
    base = cat.get("baseline")
    for v in variants:
        vid = v.get("id")
        if not vid or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", vid):
            out.append(f"zły id wariantu: {vid!r}")
        extras = v.get("extras")
        if not isinstance(extras, dict):
            out.append(f"{vid}: extras nie jest obiektem")
            continue
        for k, val in extras.items():
            if not re.fullmatch(r"rq_[a-z0-9_]+", k):
                out.append(f"{vid}: klucz {k!r} nie jest przełącznikiem rq_*")
            if not isinstance(val, str) or not val or re.search(r"[,=\s]", val):
                out.append(f"{vid}: wartość {k}={val!r} (wymagany niepusty tekst bez ',', '=' i spacji)")
        if v.get("role") not in ROLES:
            out.append(f"{vid}: rola {v.get('role')!r} spoza {ROLES}")
        if v.get("est_status") not in EST_STATUSES:
            out.append(f"{vid}: est_status {v.get('est_status')!r} spoza {EST_STATUSES}")
        if not v.get("est_source"):
            out.append(f"{vid}: brak est_source (każdy szacunek ma źródło albo opis braku pomiaru)")
        est = v.get("est_gpu_ms")
        if est is not None and (not isinstance(est, list) or len(est) != 2):
            out.append(f"{vid}: est_gpu_ms musi być [od, do] albo null")
        if not isinstance(v.get("default"), bool):
            out.append(f"{vid}: default musi być true/false")
    if base not in ids:
        out.append(f"wariant bazowy {base!r} nie istnieje")
    else:
        b = next(v for v in variants if v["id"] == base)
        if b.get("extras"):
            out.append("wariant bazowy musi mieć puste extras (stan wysyłkowy)")
    return out


def launch_keys_in_sources(root: Path) -> set[str]:
    """Literały "rq_*" w źródłach C# gry (klucze czytane przez RenderOverrides / GpuAbOverrides ...)."""
    keys: set[str] = set()
    rx = re.compile(r'"(rq_[a-z0-9_]+)"')
    for p in Path(root).rglob("*.cs"):
        if "/Tests/" in p.as_posix():
            continue
        keys.update(rx.findall(p.read_text(encoding="utf-8", errors="replace")))
    return keys


def unknown_catalog_keys(cat: dict, sources_root: Path) -> list[str]:
    known = launch_keys_in_sources(sources_root)
    out = []
    for v in cat["variants"]:
        for k in v["extras"]:
            if k not in known:
                out.append(f"{v['id']}: {k}")
    return out


def format_estimate(v: dict) -> str:
    est = v.get("est_gpu_ms")
    status = v.get("est_status", "")
    if est is None:
        return f"brak liczby ({status})"
    lo, hi = est

    def f(x):
        return "?" if x is None else f"{x:+.2f}".replace("+0.00", "0").replace("-0.00", "0")

    body = f(lo) if lo == hi else f"{f(lo)} … {f(hi)}"
    return f"{body} ms ({status})"


# ---------------------------------------------------------------- pojedynczy przebieg
@dataclass
class AbSplit:
    """Przeplatane okna rq_ab w jednym przebiegu (kolumna `ab`: 0 = A wysyłkowe, 1 = B)."""

    n_a: int
    n_b: int
    gpu_p50_a: float
    gpu_p50_b: float

    @property
    def delta_gpu_p50(self) -> float:
        return self.gpu_p50_b - self.gpu_p50_a


@dataclass
class RunResult:
    name: str
    variant: str
    segment: str
    repeat: int
    valid: bool
    block: str = ""   # klucz parowania z bazą (run.json "block"; domyślnie numer powtórzenia)
    reject_reason: str = ""
    samples: int = 0
    mean_fps: float | None = None
    p50_ms: float | None = None
    p95_ms: float | None = None
    p99_ms: float | None = None
    max_ms: float | None = None
    over33: int | None = None
    over40: int | None = None
    gpu_p50_ms: float | None = None
    gpu_p95_ms: float | None = None
    gpu_p99_ms: float | None = None
    gpu_samples: int = 0
    cpu_p50_ms: float | None = None
    cpu_p95_ms: float | None = None
    render_scale_min: float | None = None
    render_scale_max: float | None = None
    pss_mb: float | None = None
    battery_before_c: float | None = None
    battery_after_c: float | None = None
    thermal_status: int | None = None
    ab_delta_gpu_p50: float | None = None
    extras: dict = field(default_factory=dict)


def split_ab(rows: list[FrameRow], settle_s: float = AB_SETTLE_S) -> AbSplit | None:
    """GPU p50 w oknach A i B (bez klatek do `settle_s` po każdej zmianie stanu). None = brak rq_ab."""
    gpu = {"0": [], "1": []}
    last_state, switch_t = None, None
    for r in rows:
        if r.ab not in ("0", "1"):
            last_state = None
            continue
        if r.ab != last_state:
            last_state, switch_t = r.ab, r.t_s
        if r.t_s - switch_t < settle_s or r.gpu_ms <= 0:
            continue
        gpu[r.ab].append(r.gpu_ms)
    if not gpu["0"] or not gpu["1"]:
        return None
    return AbSplit(len(gpu["0"]), len(gpu["1"]), percentile(gpu["0"], 0.5), percentile(gpu["1"], 0.5))


def analyse_frames(rows: list[FrameRow], warmup_s: float) -> dict:
    kept = [r for r in rows if r.t_s >= warmup_s]
    if not kept:
        return {"samples": 0}
    ft = [r.frame_ms for r in kept]
    gpu = [r.gpu_ms for r in kept if r.gpu_ms > 0]
    cpu = [r.cpu_main_ms for r in kept if r.cpu_main_ms > 0]
    span = kept[-1].t_s - kept[0].t_s
    scales = [r.render_scale for r in kept]
    out = {
        "samples": len(ft),
        "mean_fps": round(len(ft) / span, 2) if span > 0 else None,
        "p50_ms": percentile(ft, 0.50),
        "p95_ms": percentile(ft, 0.95),
        "p99_ms": percentile(ft, 0.99),
        "max_ms": max(ft),
        "over33": sum(1 for x in ft if x > 33.4),   # jak device-metrics.ps1
        "over40": sum(1 for x in ft if x > 40.0),   # metryka ADR 0177
        "gpu_samples": len(gpu),
        "render_scale_min": min(scales),
        "render_scale_max": max(scales),
    }
    if gpu:
        out.update(gpu_p50_ms=percentile(gpu, 0.50), gpu_p95_ms=percentile(gpu, 0.95), gpu_p99_ms=percentile(gpu, 0.99))
    if cpu:
        out.update(cpu_p50_ms=percentile(cpu, 0.50), cpu_p95_ms=percentile(cpu, 0.95))
    ab = split_ab(kept)
    if ab:
        out["ab_delta_gpu_p50"] = round(ab.delta_gpu_p50, 3)
    return out


def load_run(run_dir: Path) -> RunResult:
    run_dir = Path(run_dir)
    meta_path = run_dir / "run.json"
    if not meta_path.exists():
        raise GpuAbError(f"{run_dir}: brak run.json")
    meta = json.loads(meta_path.read_text(encoding="utf-8-sig"))
    for k in ("variant", "segment", "repeat"):
        if k not in meta:
            raise GpuAbError(f"{meta_path}: brak pola {k}")
    res = RunResult(
        name=run_dir.name,
        variant=str(meta["variant"]),
        segment=str(meta["segment"]),
        repeat=int(meta["repeat"]),
        valid=bool(meta.get("valid", True)),
        block=str(meta.get("block") or meta["repeat"]),
        reject_reason=str(meta.get("rejectReason") or ""),
        battery_before_c=meta.get("batteryTempBeforeC"),
        extras=dict(meta.get("extras") or {}),
    )
    if not res.valid:
        res.reject_reason = res.reject_reason or "oznaczony jako nieważny w run.json"
        return res
    csv_path = run_dir / "frametimes.csv"
    if not csv_path.exists():
        res.valid, res.reject_reason = False, "brak frametimes.csv"
        return res
    try:
        rows = parse_frametimes_csv(csv_path)
    except ParseError as e:
        res.valid, res.reject_reason = False, f"frametimes.csv: {e}"
        return res
    for k, v in analyse_frames(rows, float(meta.get("warmupSeconds", 25))).items():
        setattr(res, k, v)
    if res.samples < MIN_SAMPLES:
        res.valid, res.reject_reason = False, f"za mało klatek po rozgrzewce ({res.samples} < {MIN_SAMPLES})"
    mj = run_dir / "metrics.json"
    if mj.exists():
        m = json.loads(mj.read_text(encoding="utf-8-sig"))
        res.pss_mb = m.get("pssMb")
        res.battery_after_c = m.get("batteryTempC")
        res.thermal_status = m.get("thermalStatus")
    return res


def load_session(session_dir: Path) -> list[RunResult]:
    runs_dir = Path(session_dir) / "runs"
    if not runs_dir.is_dir():
        raise GpuAbError(f"{session_dir}: brak katalogu runs/")
    runs = [load_run(d) for d in sorted(runs_dir.iterdir()) if d.is_dir() and (d / "run.json").exists()]
    if not runs:
        raise GpuAbError(f"{session_dir}: brak przebiegów (runs/*/run.json)")
    return runs


# ---------------------------------------------------------------- zestawienie
@dataclass
class SummaryRow:
    variant: str
    segment: str
    runs: int
    rejected: int
    gpu_p50_ms: float | None = None
    gpu_p95_ms: float | None = None
    gpu_p95_min: float | None = None
    gpu_p95_max: float | None = None
    frame_p50_ms: float | None = None
    frame_p95_ms: float | None = None
    frame_p99_ms: float | None = None
    over40: float | None = None
    cpu_p50_ms: float | None = None
    pss_mb: float | None = None
    battery_before_c: float | None = None
    battery_after_c: float | None = None
    thermal_max: int | None = None
    d_gpu_p50_ms: float | None = None
    d_gpu_p95_ms: float | None = None
    d_gpu_p50_min: float | None = None
    d_gpu_p50_max: float | None = None
    pairs: int = 0
    baseline_spread_gpu_p50: float | None = None
    significant: str = ""
    gpu_p95_within_budget: str = ""
    ab_delta_gpu_p50: float | None = None
    estimate: str = ""
    role: str = ""


def _med(vals):
    vals = [v for v in vals if v is not None]
    return round(statistics.median(vals), 3) if vals else None


def summarise(runs: list[RunResult], catalog: dict | None = None, baseline: str | None = None) -> list[SummaryRow]:
    baseline = baseline or (catalog or {}).get("baseline") or "baseline"
    by_id = {v["id"]: v for v in (catalog or {}).get("variants", [])}
    groups: dict[tuple[str, str], list[RunResult]] = {}
    order: list[tuple[str, str]] = []
    for r in runs:
        key = (r.variant, r.segment)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(r)
    out: list[SummaryRow] = []
    for variant, segment in order:
        all_runs = groups[(variant, segment)]
        ok = [r for r in all_runs if r.valid]
        row = SummaryRow(variant=variant, segment=segment, runs=len(ok), rejected=len(all_runs) - len(ok))
        cat = by_id.get(variant)
        if cat:
            row.estimate, row.role = format_estimate(cat), cat.get("role", "")
        if ok:
            p95s = [r.gpu_p95_ms for r in ok if r.gpu_p95_ms is not None]
            row.gpu_p50_ms = _med(r.gpu_p50_ms for r in ok)
            row.gpu_p95_ms = _med(p95s)
            row.gpu_p95_min = min(p95s) if p95s else None
            row.gpu_p95_max = max(p95s) if p95s else None
            row.frame_p50_ms = _med(r.p50_ms for r in ok)
            row.frame_p95_ms = _med(r.p95_ms for r in ok)
            row.frame_p99_ms = _med(r.p99_ms for r in ok)
            row.over40 = _med(r.over40 for r in ok)
            row.cpu_p50_ms = _med(r.cpu_p50_ms for r in ok)
            row.pss_mb = _med(r.pss_mb for r in ok)
            row.battery_before_c = _med(r.battery_before_c for r in ok)
            row.battery_after_c = _med(r.battery_after_c for r in ok)
            th = [r.thermal_status for r in ok if r.thermal_status is not None]
            row.thermal_max = max(th) if th else None
            row.ab_delta_gpu_p50 = _med(r.ab_delta_gpu_p50 for r in ok)
            if row.gpu_p95_max is not None:
                row.gpu_p95_within_budget = "TAK" if row.gpu_p95_max <= BUDGET_GPU_P95_MS else "NIE"
        base_ok = [r for r in groups.get((baseline, segment), []) if r.valid and r.gpu_p50_ms is not None]
        if base_ok:
            b50 = [r.gpu_p50_ms for r in base_ok]
            row.baseline_spread_gpu_p50 = round(max(b50) - min(b50), 3)
        if variant != baseline and ok and base_ok:
            base_by_block = {r.block: r for r in base_ok}
            d50, d95 = [], []
            for r in ok:
                b = base_by_block.get(r.block)
                if b is None or r.gpu_p50_ms is None:
                    continue
                d50.append(r.gpu_p50_ms - b.gpu_p50_ms)
                if r.gpu_p95_ms is not None and b.gpu_p95_ms is not None:
                    d95.append(r.gpu_p95_ms - b.gpu_p95_ms)
            row.pairs = len(d50)
            if d50:
                row.d_gpu_p50_ms = _med(d50)
                row.d_gpu_p50_min, row.d_gpu_p50_max = round(min(d50), 3), round(max(d50), 3)
                row.d_gpu_p95_ms = _med(d95)
                same_sign = all(d > 0 for d in d50) or all(d < 0 for d in d50)
                # Istotne dopiero, gdy każda para ma ten sam znak, mediana wychodzi poza rozrzut bazy
                # i są co najmniej 3 pary; inaczej to szum pomiaru (ADR 0136 r2c: +-0,3 ms).
                if len(d50) < 3:
                    row.significant = "ZA MAŁO PAR"
                elif same_sign and abs(row.d_gpu_p50_ms) > (row.baseline_spread_gpu_p50 or 0.0):
                    row.significant = "TAK"
                else:
                    row.significant = "NIE (szum)"
        out.append(row)
    return out


# ---------------------------------------------------------------- zapis
RESULT_COLUMNS = [
    "name", "variant", "segment", "repeat", "block", "valid", "reject_reason", "samples", "mean_fps", "p50_ms", "p95_ms", "p99_ms",
    "max_ms", "over33", "over40", "gpu_p50_ms", "gpu_p95_ms", "gpu_p99_ms", "gpu_samples", "cpu_p50_ms", "cpu_p95_ms",
    "render_scale_min", "render_scale_max", "pss_mb", "battery_before_c", "battery_after_c", "thermal_status", "ab_delta_gpu_p50", "extras",
]


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float):
        return f"{v:.3f}".rstrip("0").rstrip(".")
    if isinstance(v, dict):
        return " ".join(f"{k}={val}" for k, val in v.items())
    return str(v)


def write_results_csv(runs: list[RunResult], path: Path) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(RESULT_COLUMNS)
        for r in runs:
            d = asdict(r)
            w.writerow([_cell(d[c]) for c in RESULT_COLUMNS])


def write_summary_csv(rows: list[SummaryRow], path: Path) -> None:
    cols = list(SummaryRow.__dataclass_fields__)
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            d = asdict(r)
            w.writerow([_cell(d[c]) for c in cols])


def _md(v, signed=False):
    if v is None or v == "":
        return "–"
    if isinstance(v, float):
        return f"{v:+.2f}" if signed else f"{v:.2f}"
    return str(v)


def render_report(runs: list[RunResult], rows: list[SummaryRow], session: dict | None = None) -> str:
    s = session or {}
    lines = ["# A/B GPU — tabela wariantów (ADR 0241, B-113)", ""]
    if s:
        apk = s.get("apk") or {}
        lines += [
            f"- Sesja `{s.get('timestamp', '?')}`, telefon `{s.get('serial', '?')}`, tier {s.get('tier', '?')}, "
            f"limit klatek: {s.get('fpsLabel', s.get('fps', '?'))}, tryb: {s.get('mode', '?')}, "
            f"powtórzeń: {s.get('repeats', '?')}, rozgrzewka {s.get('warmupSeconds', '?')} s.",
            f"- APK: `{apk.get('file', '?')}` sha256 `{apk.get('sha256', '?')}`.",
        ]
    ok = [r for r in runs if r.valid]
    lines += [
        f"- Przebiegi: {len(ok)} ważnych, {len(runs) - len(ok)} odrzuconych. Percentyle: nearest-rank po rozgrzewce, jak `device-metrics.ps1`.",
        "- Δ = wariant − baza z tego samego bloku pomiarowego (baza zmierzona tuż przed wariantami bloku; mediana par; ujemna = mniej ms GPU). „Istotne” = wszystkie pary mają ten sam "
        "znak, ≥ 3 pary i |mediana| > rozrzut bazy (max − min GPU p50 bazy na tym odcinku).",
        f"- Budżet: GPU p95 ≤ {BUDGET_GPU_P95_MS} ms (kolumna „p95 ≤ budżet” liczona z NAJGORSZEGO powtórzenia; ma sens tylko przy limicie 30 FPS).",
        "- Kolumna „szacunek” to liczba SPRZED pomiaru (katalog wariantów: ESTIMATED / UNVERIFIED ze źródłem), nie wynik tej sesji.",
        "",
    ]
    for seg in dict.fromkeys(r.segment for r in rows):
        lines += [
            f"## Odcinek / kamera {seg}", "",
            "| wariant | rola | n | GPU p50 | GPU p95 (min–max) | Δ GPU p50 (min…max) | Δ GPU p95 | istotne | p95 ≤ budżet | klatka p50/p95/p99 | > 40 ms | CPU p50 | PSS MB | bat. przed/po °C | termika | szacunek |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for r in [x for x in rows if x.segment == seg]:
            p95 = "–" if r.gpu_p95_ms is None else f"{r.gpu_p95_ms:.2f} ({r.gpu_p95_min:.2f}–{r.gpu_p95_max:.2f})"
            d50 = "–" if r.d_gpu_p50_ms is None else f"{r.d_gpu_p50_ms:+.2f} ({r.d_gpu_p50_min:+.2f}…{r.d_gpu_p50_max:+.2f})"
            n = f"{r.runs}" + (f" (+{r.rejected} odrz.)" if r.rejected else "")
            lines.append(
                f"| {r.variant} | {r.role or '–'} | {n} | {_md(r.gpu_p50_ms)} | {p95} | {d50} | {_md(r.d_gpu_p95_ms, True)} | "
                f"{r.significant or '–'} | {r.gpu_p95_within_budget or '–'} | {_md(r.frame_p50_ms)} / {_md(r.frame_p95_ms)} / {_md(r.frame_p99_ms)} | "
                f"{_md(r.over40)} | {_md(r.cpu_p50_ms)} | {_md(r.pss_mb)} | {_md(r.battery_before_c)} / {_md(r.battery_after_c)} | "
                f"{_md(r.thermal_max)} | {r.estimate or '–'} |"
            )
        spread = next((x.baseline_spread_gpu_p50 for x in rows if x.segment == seg and x.baseline_spread_gpu_p50 is not None), None)
        lines += ["", f"Rozrzut bazy (GPU p50, max − min): {_md(spread)} ms.", ""]
    ab = [r for r in rows if r.ab_delta_gpu_p50 is not None]
    if ab:
        lines += ["## Okna przeplatane `rq_ab` (B − A w jednym przebiegu, GPU p50)", "", "| wariant | odcinek | Δ GPU p50 |", "|---|---|---|"]
        lines += [f"| {r.variant} | {r.segment} | {r.ab_delta_gpu_p50:+.2f} |" for r in ab]
        lines.append("")
    bad = [r for r in runs if not r.valid]
    if bad:
        lines += ["## Odrzucone przebiegi", ""] + [f"- `{r.name}` ({r.variant}, {r.segment}, powt. {r.repeat}): {r.reject_reason}" for r in bad] + [""]
    gpu_missing = [r.name for r in ok if r.gpu_samples == 0]
    if gpu_missing:
        lines += [f"**Uwaga:** brak próbek GPU (FrameTimingManager zwrócił 0) w: {', '.join(gpu_missing)}.", ""]
    scaled = [r.name for r in ok if r.render_scale_min is not None and r.render_scale_max - r.render_scale_min > 1e-3]
    if scaled:
        lines += [f"**Uwaga:** skala renderu zmieniała się w trakcie przebiegu (adaptacyjna skala zafałszowuje A/B): {', '.join(scaled)}.", ""]
    return "\n".join(lines) + "\n"


def report(session_dir: Path, catalog_path: Path | None = None, baseline: str | None = None) -> dict:
    session_dir = Path(session_dir)
    catalog = load_catalog(catalog_path)
    runs = load_session(session_dir)
    rows = summarise(runs, catalog, baseline)
    sj = session_dir / "session.json"
    session = json.loads(sj.read_text(encoding="utf-8-sig")) if sj.exists() else None
    write_results_csv(runs, session_dir / "results.csv")
    write_summary_csv(rows, session_dir / "summary.csv")
    (session_dir / "REPORT.md").write_text(render_report(runs, rows, session), encoding="utf-8")
    return {"runs": len(runs), "valid": sum(1 for r in runs if r.valid), "rows": len(rows)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfgate.gpuab", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    rp = sub.add_parser("report", help="results.csv + summary.csv + REPORT.md z katalogu sesji")
    rp.add_argument("session")
    rp.add_argument("--catalog", default=None)
    rp.add_argument("--baseline", default=None)
    cp = sub.add_parser("catalog", help="walidacja katalogu wariantów (opcjonalnie: czy gra czyta każdy klucz)")
    cp.add_argument("--catalog", default=None)
    cp.add_argument("--sources", default=None, help="game/Assets/_Project")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "report":
            r = report(Path(a.session), Path(a.catalog) if a.catalog else None, a.baseline)
            print(f"{a.session}: {r['valid']}/{r['runs']} ważnych przebiegów, {r['rows']} wierszy -> results.csv, summary.csv, REPORT.md")
            return 0 if r["valid"] else 1
        cat = load_catalog(Path(a.catalog) if a.catalog else None)
        if a.sources:
            unknown = unknown_catalog_keys(cat, Path(a.sources))
            if unknown:
                print("klucze, których gra nie czyta: " + ", ".join(unknown), file=sys.stderr)
                return 1
        for v in cat["variants"]:
            ex = ",".join(f"{k}={val}" for k, val in v["extras"].items()) or "-"
            print(f"{v['id']:<18} {'*' if v['default'] else ' '} {v['role']:<10} {ex:<24} {format_estimate(v)}")
        return 0
    except GpuAbError as e:
        print(f"BŁĄD: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
