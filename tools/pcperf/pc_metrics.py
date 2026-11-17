#!/usr/bin/env python3
"""Raport pomiaru PC (ADR 0266) z katalogu runu playera Windows.

Wejście (katalog z `scripts/pc-metrics.ps1` albo sam `-metrics <dir>` playera):
  run.json     — `PcFrameMetricsRecorder` (format "kamion/pc-metrics/1"): sprzęt, ekran, tier, ładowania, percentyle z gry
  frames.csv   — `frame,t_s,frame_ms,cpu_main_ms,gpu_ms,draw_calls,batches,setpass,tris,gc_count,scene`
  memory.csv   — `t_s,allocated_mb,reserved_mb,mono_used_mb,mono_heap_mb,gfx_driver_mb,gc_count` (opcjonalny)
  process.csv  — `t_s,working_set_mb,private_mb,gpu_dedicated_mb,gpu_shared_mb,gpu_temp_c,gpu_util_pct`
                 (opcjonalny, z liczników Windows / nvidia-smi w pc-metrics.ps1; puste pole = brak danych)

Wyjście: `<dir>/pc-report.json` i `<dir>/pc-report.md`; porównanie z budżetem klasy z `budgets/pc-budgets.json`.
Rodzaj pomiaru (`measurement_kind`, D76): `reference` / `emulation` / `informational` wg `budgets/pc-machines.json`;
`gate_eligible` = PASS i (reference albo emulation ze zgodną konfiguracją klasy).
Kod wyjścia: 0 = w budżecie (PASS / INCOMPLETE bez FAIL), 1 = poza budżetem (FAIL), 2 = pomiar nieważny lub brak danych.

Percentyle: nearest rank (rank = ceil(p·n), jak `FrameTimeStats`, `PcMetricsMath` i scripts/device-metrics.ps1).
Tylko biblioteka standardowa:  uv run --no-project python tools/pcperf/pc_metrics.py <dir> --class zalecany
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RUN_FORMAT = "kamion/pc-metrics/1"
BUDGET_FORMAT = "kamion/pc-budgets/1"
MACHINES_FORMAT = "kamion/pc-machines/1"
FRAMES_HEADER = ["frame", "t_s", "frame_ms", "cpu_main_ms", "gpu_ms", "draw_calls", "batches", "setpass", "tris", "gc_count", "scene"]
MEMORY_HEADER = ["t_s", "allocated_mb", "reserved_mb", "mono_used_mb", "mono_heap_mb", "gfx_driver_mb", "gc_count"]
PROCESS_HEADER = ["t_s", "working_set_mb", "private_mb", "gpu_dedicated_mb", "gpu_shared_mb", "gpu_temp_c", "gpu_util_pct"]
REPORT_THRESHOLDS_MS = (16.7, 33.3, 50.0, 66.7, 100.0)
DEFAULT_BUDGET = Path(__file__).resolve().parent / "budgets" / "pc-budgets.json"
DEFAULT_MACHINES = Path(__file__).resolve().parent / "budgets" / "pc-machines.json"
MEASUREMENT_KINDS = ("reference", "emulation", "informational")

EXIT_OK, EXIT_FAIL, EXIT_INVALID = 0, 1, 2


class FormatError(ValueError):
    """Wejście w złym formacie (nieznane kolumny, zły format run.json)."""


# ---------------------------------------------------------------- statystyka


def nearest_rank(sorted_values: list[float], p: float) -> float | None:
    """Percentyl nearest-rank z posortowanej rosnąco listy; None dla pustej."""
    n = len(sorted_values)
    if n == 0:
        return None
    rank = math.ceil(p * n - 1e-9)
    rank = max(1, min(n, rank))
    return sorted_values[rank - 1]


def summarize(values: list[float]) -> dict[str, Any] | None:
    """p50/p95/p99/max/mean dla listy (dowolna kolejność); None dla pustej."""
    if not values:
        return None
    s = sorted(values)
    return {
        "samples": len(s),
        "p50": nearest_rank(s, 0.50),
        "p95": nearest_rank(s, 0.95),
        "p99": nearest_rank(s, 0.99),
        "max": s[-1],
        "mean": sum(s) / len(s),
    }


def slope_per_minute(ts: list[float], ys: list[float]) -> float | None:
    """Nachylenie prostej MNK [jednostka/min] (trend pamięci = podejrzenie wycieku); None przy < 3 punktach."""
    n = len(ts)
    if n < 3:
        return None
    mt, my = sum(ts) / n, sum(ys) / n
    den = sum((t - mt) ** 2 for t in ts)
    if den <= 0:
        return None
    return 60.0 * sum((t - mt) * (y - my) for t, y in zip(ts, ys)) / den


# ---------------------------------------------------------------- wczytywanie


def _read_csv(path: Path, header: list[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        got = reader.fieldnames or []
        if got != header:
            raise FormatError(f"{path.name}: nagłówek {got} != oczekiwany {header}")
        return list(reader)


def _num(s: str | None) -> float | None:
    if s is None:
        return None
    s = s.strip()
    if s == "":
        return None
    v = float(s)
    return v if math.isfinite(v) else None


@dataclass
class Run:
    run: dict[str, Any]
    frames: list[dict[str, float]]
    memory: list[dict[str, float | None]]
    process: list[dict[str, float | None]]


def load_run(directory: Path) -> Run:
    run_path = directory / "run.json"
    if not run_path.exists():
        raise FileNotFoundError(f"brak {run_path}")
    run = json.loads(run_path.read_text(encoding="utf-8-sig"))
    if run.get("format") != RUN_FORMAT:
        raise FormatError(f"run.json: format {run.get('format')!r} != {RUN_FORMAT!r}")
    frames: list[dict[str, float]] = []
    fp = directory / "frames.csv"
    if fp.exists():
        for row in _read_csv(fp, FRAMES_HEADER):
            frames.append({k: float(row[k]) for k in FRAMES_HEADER})
    memory = []
    mp = directory / "memory.csv"
    if mp.exists():
        memory = [{k: _num(row[k]) for k in MEMORY_HEADER} for row in _read_csv(mp, MEMORY_HEADER)]
    process = []
    pp = directory / "process.csv"
    if pp.exists():
        process = [{k: _num(row[k]) for k in PROCESS_HEADER} for row in _read_csv(pp, PROCESS_HEADER)]
    return Run(run, frames, memory, process)


def load_budget(path: Path) -> dict[str, Any]:
    b = json.loads(path.read_text(encoding="utf-8"))
    if b.get("format") != BUDGET_FORMAT:
        raise FormatError(f"{path.name}: format {b.get('format')!r} != {BUDGET_FORMAT!r}")
    return b


def load_machines(path: Path) -> dict[str, Any]:
    """Maszyny pomiarowe (D76). Sprawdza strukturę, bo literówka w pliku po cichu zmieniłaby wynik bramki."""
    m = json.loads(path.read_text(encoding="utf-8"))
    if m.get("format") != MACHINES_FORMAT:
        raise FormatError(f"{path.name}: format {m.get('format')!r} != {MACHINES_FORMAT!r}")
    for kind in ("reference", "emulation"):
        if not isinstance(m.get(kind), list):
            raise FormatError(f"{path.name}: '{kind}' musi być listą")
        for e in m[kind]:
            if not e.get("id") or not isinstance(e.get("match"), dict) or not e["match"]:
                raise FormatError(f"{path.name}: wpis {kind} bez 'id' albo pustego 'match'")
            unknown = set(e["match"]) - set(MATCH_KEYS)
            if unknown:
                raise FormatError(f"{path.name}: {e['id']}: nieznane klucze match {sorted(unknown)}")
            if not isinstance(e.get("classes"), (dict, list)) or not e["classes"]:
                raise FormatError(f"{path.name}: {e['id']}: brak 'classes'")
            if kind == "emulation":
                if not isinstance(e["classes"], dict):
                    raise FormatError(f"{path.name}: {e['id']}: 'classes' emulacji musi być obiektem klasa -> konfiguracja")
                for cname, cfg in e["classes"].items():
                    missing = [k for k in EMULATION_KEYS if k not in cfg]
                    if missing:
                        raise FormatError(f"{path.name}: {e['id']}/{cname}: brak {missing}")
    return m


# ---------------------------------------------------------------- analiza


def _peak(rows: list[dict[str, float | None]], key: str) -> float | None:
    vals = [r[key] for r in rows if r.get(key) is not None and r[key] >= 0]
    return max(vals) if vals else None


def analyze(r: Run, warmup_s: float | None = None) -> dict[str, Any]:
    """Liczby z runu (bez budżetu)."""
    opts = r.run.get("options") or {}
    warm = float(opts.get("warmupSeconds", 5.0)) if warmup_s is None else float(warmup_s)
    win = [f for f in r.frames if f["t_s"] >= warm]
    ms = [f["frame_ms"] for f in win]
    ft = summarize(ms)
    span = (win[-1]["t_s"] - win[0]["t_s"]) if len(win) > 1 else 0.0
    out: dict[str, Any] = {
        "warmup_s": warm,
        "frames_total": len(r.frames),
        "frames_window": len(win),
        "span_s": round(span, 3),
        "mean_fps": round(len(win) / span, 2) if span > 0 else None,
        "frame_ms": ft,
        "frames_over": {
            f"{t:g}": {"count": sum(1 for v in ms if v > t), "pct": (100.0 * sum(1 for v in ms if v > t) / len(ms)) if ms else None}
            for t in REPORT_THRESHOLDS_MS
        },
        "cpu_main_ms": summarize([f["cpu_main_ms"] for f in win if f["cpu_main_ms"] > 0]),
        "gpu_ms": summarize([f["gpu_ms"] for f in win if f["gpu_ms"] > 0]),
        "draw_calls": summarize([f["draw_calls"] for f in win if f["draw_calls"] >= 0]),
        "batches": summarize([f["batches"] for f in win if f["batches"] >= 0]),
        "setpass": summarize([f["setpass"] for f in win if f["setpass"] >= 0]),
        "tris": summarize([f["tris"] for f in win if f["tris"] >= 0]),
        "scenes_in_window": sorted({int(f["scene"]) for f in win}),
    }
    gcs = [f["gc_count"] for f in win]
    out["gc"] = {"collections_in_window": int(gcs[-1] - gcs[0]) if len(gcs) > 1 else (0 if gcs else None)}

    mem = r.memory
    out["unity_memory"] = {
        "allocated_mb_peak": _peak(mem, "allocated_mb"),
        "reserved_mb_peak": _peak(mem, "reserved_mb"),
        "mono_heap_mb_peak": _peak(mem, "mono_heap_mb"),
        "gfx_driver_mb_peak": _peak(mem, "gfx_driver_mb"),
        "reserved_mb_per_min": None,
    }
    trend = [(m["t_s"], m["reserved_mb"]) for m in mem if m["t_s"] is not None and m["reserved_mb"] is not None and m["t_s"] >= warm]
    if trend:
        s = slope_per_minute([t for t, _ in trend], [y for _, y in trend])
        out["unity_memory"]["reserved_mb_per_min"] = round(s, 2) if s is not None else None

    p = r.process
    out["process"] = {
        "samples": len(p),
        "working_set_mb": {"peak": _peak(p, "working_set_mb")},
        "private_mb": {"peak": _peak(p, "private_mb")},
        "gpu_dedicated_mb": {"peak": _peak(p, "gpu_dedicated_mb")},
        "gpu_shared_mb": {"peak": _peak(p, "gpu_shared_mb")},
        "gpu_temp_c": {"peak": _peak(p, "gpu_temp_c")},
    }
    loads = [l for l in (r.run.get("loads") or []) if (l.get("seconds") or -1) >= 0]
    out["region_load_s"] = {
        "loads": [{"scene": l.get("scene"), "seconds": round(float(l["seconds"]), 3), "start": l.get("startSource")} for l in loads],
        "max": max((float(l["seconds"]) for l in loads), default=None),
    }
    return out


def metric_value(a: dict[str, Any], check: dict[str, Any]) -> float | None:
    """Wartość metryki z analizy dla wpisu budżetu."""
    m = check["metric"]
    if m == "frames_over_pct" or m == "frames_over_count":
        thr = float(check["threshold_ms"])
        ms = a.get("_ms_window")
        if ms is None:
            return None
        n = sum(1 for v in ms if v > thr)
        if m == "frames_over_count":
            return float(n)
        return 100.0 * n / len(ms) if ms else None
    cur: Any = a
    for part in m.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(f"nieznana metryka budżetu: {m}")
        cur = cur[part]
        if cur is None:
            return None
    return float(cur) if isinstance(cur, (int, float)) else None


# Tolerancja progu czasu klatki równego okresowi limitu FPS (WORKING_VALUE). Przy `targetFrameRate` = 30 player trzyma
# klatkę ~33,33–33,34 ms (zegar systemowy), a budżet zapisuje okres zaokrąglony (33,3 / 16,7); bez tolerancji gra, która
# trzyma limit idealnie, dostaje FAIL p50. Tolerancja dotyczy tylko progów `frame_ms.*` leżących w ±1 % od okresu limitu.
CAP_TOLERANCE = 0.01


def effective_limit(check: dict[str, Any], lim: float, display: dict[str, Any] | None) -> float:
    """Limit sprawdzenia po uwzględnieniu limitu FPS (próg = okres limitu → okres × (1 + CAP_TOLERANCE))."""
    if not str(check.get("metric", "")).startswith("frame_ms."):
        return lim
    fps = (display or {}).get("targetFrameRate")
    try:
        fps = float(fps)
    except (TypeError, ValueError):
        return lim
    if fps <= 0:
        return lim
    period = 1000.0 / fps
    if abs(lim - period) > period * CAP_TOLERANCE:
        return lim
    return max(lim, round(period * (1.0 + CAP_TOLERANCE), 3))


def validity(r: Run, a: dict[str, Any], budget: dict[str, Any] | None) -> list[str]:
    """Powody, dla których pomiar jest nieważny (pusta lista = ważny)."""
    reasons = []
    run = r.run
    if run.get("isEditor"):
        reasons.append("pomiar w edytorze (build jest prawdą — wymagany player Windows)")
    min_frames = int((budget or {}).get("minFramesAfterWarmup", 600))
    if a["frames_window"] < min_frames:
        reasons.append(f"za mało klatek po rozgrzewce: {a['frames_window']} < {min_frames}")
    rec = run.get("recording") or {}
    if int(rec.get("focusLost", 0)) > 0:
        reasons.append(f"okno playera straciło fokus {rec.get('focusLost')}× w trakcie pomiaru")
    if int(rec.get("droppedFrames", 0)) > 0:
        reasons.append(f"bufor klatek przepełniony ({rec.get('droppedFrames')} klatek pominiętych) — zwiększ -metricsMaxFps")
    if run.get("endReason") not in ("duration",):
        reasons.append(f"run nie zakończył się po zadanym czasie (endReason={run.get('endReason')})")
    return reasons


def context_mismatch(run: dict[str, Any], cls: dict[str, Any]) -> list[str]:
    """Różnice warunków pomiaru względem definicji klasy (rozdzielczość, tier, limit FPS)."""
    out = []
    d = run.get("display") or {}
    res = cls.get("resolution")
    if res and [d.get("width"), d.get("height")] != list(res):
        out.append(f"rozdzielczość {d.get('width')}x{d.get('height')} != klasa {res[0]}x{res[1]}")
    tier = cls.get("tier")
    if tier and d.get("qualityName") != tier:
        out.append(f"tier {d.get('qualityName')} != klasa {tier}")
    fps = cls.get("targetFps")
    if fps and d.get("targetFrameRate") not in (fps,):
        out.append(f"limit FPS {d.get('targetFrameRate')} != klasa {fps}")
    return out


def cross_check(in_game: dict[str, Any] | None, ft: dict[str, Any] | None, tol_ms: float = 0.01) -> dict[str, Any] | None:
    """Zgodność percentyli policzonych w grze (run.json inGame, float32) z parserem (CSV z 3 miejscami po przecinku)."""
    if not in_game or not ft or int(in_game.get("samples", 0)) <= 0:
        return None
    diffs = {k: abs(float(in_game[f"{k}Ms"]) - float(ft[k])) for k in ("p50", "p95", "p99")}
    return {"samples_game": int(in_game["samples"]), "samples_parser": ft["samples"],
            "max_diff_ms": round(max(diffs.values()), 4),
            "ok": max(diffs.values()) <= tol_ms and int(in_game["samples"]) == ft["samples"]}


def is_reference_machine(run: dict[str, Any], budget: dict[str, Any]) -> bool:
    """Stary mechanizm: dokładne gpu+cpu z `referenceMachines` w pliku budżetu (zachowany dla zgodności)."""
    sysj = run.get("system") or {}
    for m in budget.get("referenceMachines") or []:
        if m.get("gpu") == sysj.get("gpu") and m.get("cpu") == sysj.get("cpu"):
            return True
    return False


# klucz w `match` -> pole run.json system; *Contains = wszystkie podciągi muszą wystąpić, *Excludes = żaden (bez wielkości liter)
MATCH_KEYS = {
    "gpuContains": "gpu", "gpuExcludes": "gpu", "gpuVendorContains": "gpuVendor",
    "cpuContains": "cpu", "cpuExcludes": "cpu", "deviceModelContains": "deviceModel",
}
EMULATION_KEYS = ("resolution", "tier", "targetFps", "vSyncCount", "fullScreenModes")


def machine_matches(system: dict[str, Any] | None, match: dict[str, Any]) -> bool:
    sysj = system or {}
    for key, field in MATCH_KEYS.items():
        needles = match.get(key)
        if not needles:
            continue
        if isinstance(needles, str):
            needles = [needles]
        hay = str(sysj.get(field) or "").casefold()
        if key.endswith("Excludes"):
            if any(n.casefold() in hay for n in needles):
                return False
        elif not hay or not all(n.casefold() in hay for n in needles):
            return False
    return True


def _entry_has_class(entry: dict[str, Any], cls_name: str) -> bool:
    c = entry.get("classes")
    return cls_name in c if isinstance(c, (dict, list)) else False


def emulation_mismatch(run: dict[str, Any], cfg: dict[str, Any]) -> list[str]:
    """Różnice warunków runu względem metody emulacji klasy (D76). Brak pola w run.json = niezgodność (nie da się potwierdzić)."""
    d = run.get("display") or {}
    out = []
    res = cfg.get("resolution")
    if res and [d.get("width"), d.get("height")] != list(res):
        out.append(f"rozdzielczość {d.get('width')}x{d.get('height')} != emulacja {res[0]}x{res[1]}")
    if cfg.get("tier") and d.get("qualityName") != cfg["tier"]:
        out.append(f"tier {d.get('qualityName')} != emulacja {cfg['tier']}")
    if cfg.get("targetFps") and d.get("targetFrameRate") != cfg["targetFps"]:
        out.append(f"limit FPS {d.get('targetFrameRate')} != emulacja {cfg['targetFps']}")
    if "vSyncCount" in cfg and d.get("vSyncCount") != cfg["vSyncCount"]:
        out.append(f"VSync {d.get('vSyncCount')} != emulacja {cfg['vSyncCount']} (wymagane -VSync 0)")
    modes = cfg.get("fullScreenModes")
    if modes and d.get("fullScreenMode") not in modes:
        out.append(f"tryb ekranu {d.get('fullScreenMode')} nie jest jednym z {', '.join(modes)}")
    return out


def classify_measurement(run: dict[str, Any], budget: dict[str, Any] | None, machines: dict[str, Any] | None,
                         cls_name: str | None) -> dict[str, Any]:
    """Rodzaj pomiaru: reference (prawdziwy sprzęt klasy) / emulation (D76, zgodna konfiguracja) / informational."""
    out: dict[str, Any] = {"kind": "informational", "machine": None, "decision": None, "reasons": [], "annotation": None}
    if budget is None or not cls_name:
        out["reasons"].append("brak klasy budżetu (--class) — liczby bez porównania")
        return out
    system = run.get("system")
    if is_reference_machine(run, budget):
        out.update(kind="reference", machine="pc-budgets.json:referenceMachines")
        return out
    m = machines or {}
    for e in m.get("reference") or []:
        if _entry_has_class(e, cls_name) and machine_matches(system, e["match"]):
            out.update(kind="reference", machine=e["id"], decision=e.get("decision"))
            return out
    for e in m.get("emulation") or []:
        if not machine_matches(system, e["match"]):
            continue
        if not _entry_has_class(e, cls_name):
            out["reasons"].append(f"maszyna {e['id']} nie emuluje klasy {cls_name} (emuluje: {', '.join(e['classes'])})")
            continue
        mism = emulation_mismatch(run, e["classes"][cls_name])
        if mism:
            out["machine"] = e["id"]
            out["reasons"].extend(f"konfiguracja niezgodna z metodą emulacji: {x}" for x in mism)
            continue
        cfg = e["classes"][cls_name]
        dec = e.get("decision", "D76")
        real = cfg.get("realHardware") or f"klasy {cls_name}"
        out.update(kind="emulation", machine=e["id"], decision=dec,
                   annotation=f"EMULACJA ({dec}) — nie zastępuje pomiaru na sprzęcie klasy {cls_name} ({real}) "
                              f"przed obietnicą wymagań sprzętowych")
        return out
    if not out["reasons"]:
        sysj = system or {}
        out["reasons"].append(f"maszyna (GPU {sysj.get('gpu')!r}, CPU {sysj.get('cpu')!r}) nie jest w pc-machines.json "
                              f"jako referencyjna ani emulująca klasę {cls_name}")
    return out


def evaluate(r: Run, budget: dict[str, Any] | None, cls_name: str | None, warmup_s: float | None = None,
             allow_mismatch: bool = False, machines: dict[str, Any] | None = None) -> dict[str, Any]:
    if warmup_s is None and budget is not None and "warmupSeconds" not in (r.run.get("options") or {}):
        warmup_s = float(budget.get("warmupSeconds", 5.0))
    a = analyze(r, warmup_s)
    a["_ms_window"] = [f["frame_ms"] for f in r.frames if f["t_s"] >= a["warmup_s"]]
    report: dict[str, Any] = {
        "format": "kamion/pc-report/1",
        "run": {k: r.run.get(k) for k in ("label", "buildLabel", "development", "isEditor", "unityVersion", "endReason", "platform")},
        "system": r.run.get("system"),
        "display": r.run.get("display"),
        "options": r.run.get("options"),
        "in_game": r.run.get("inGame"),
        "metrics": {k: v for k, v in a.items() if not k.startswith("_")},
        "invalid_reasons": validity(r, a, budget),
        "cross_check": cross_check(r.run.get("inGame"), a.get("frame_ms")),
    }
    verdict = "NO_BUDGET"
    checks = []
    if budget is not None and cls_name:
        classes = budget.get("classes") or {}
        if cls_name not in classes:
            raise KeyError(f"brak klasy {cls_name!r} w budżecie (są: {', '.join(classes)})")
        cls = classes[cls_name]
        mism = context_mismatch(r.run, cls)
        report["class"] = {"name": cls_name, "label": cls.get("label"), "status": cls.get("status", budget.get("status")),
                           "context_mismatch": mism}
        report["reference_machine"] = is_reference_machine(r.run, budget)
        for c in cls.get("checks", []):
            v = metric_value(a, c)
            lim = float(c["max"])
            eff = effective_limit(c, lim, r.run.get("display"))
            st = "NO_DATA" if v is None else ("PASS" if v <= eff else "FAIL")
            name = c["metric"] + (f">{c['threshold_ms']:g}ms" if "threshold_ms" in c else "")
            checks.append({"metric": name, "value": v, "max": lim, "status": st,
                           **({"max_effective": eff} if eff != lim else {}),
                           "value_status": c.get("status", cls.get("status", budget.get("status", "WORKING_VALUE")))})
        if report["invalid_reasons"] or (mism and not allow_mismatch):
            verdict = "INVALID"
        elif any(c["status"] == "FAIL" for c in checks):
            verdict = "FAIL"
        elif any(c["status"] == "NO_DATA" for c in checks):
            verdict = "INCOMPLETE"
        else:
            verdict = "PASS"
    elif report["invalid_reasons"]:
        verdict = "INVALID"
    report["checks"] = checks
    report["verdict"] = verdict
    meas = classify_measurement(r.run, budget, machines, cls_name)
    if verdict != "PASS" and meas["kind"] != "informational":
        meas["reasons"].append(f"werdykt {verdict} (bramkę zalicza tylko PASS)")
    report["measurement_kind"] = meas["kind"]
    report["measurement"] = meas
    report["gate_eligible"] = verdict == "PASS" and meas["kind"] in ("reference", "emulation")
    return report


def exit_code(report: dict[str, Any]) -> int:
    v = report["verdict"]
    if v == "INVALID":
        return EXIT_INVALID
    if v == "FAIL":
        return EXIT_FAIL
    return EXIT_OK


# ---------------------------------------------------------------- raport MD


def _f(v: Any, nd: int = 2) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{nd}f}".replace(".", ",")
    return str(v)


def render_md(rep: dict[str, Any]) -> str:
    m = rep["metrics"]
    s = rep.get("system") or {}
    d = rep.get("display") or {}
    L = []
    L.append("# Raport pomiaru PC (ADR 0266)")
    L.append("")
    L.append(f"**Werdykt budżetu: {rep['verdict']}**" + (f" — klasa `{rep['class']['name']}` ({rep['class']['status']})" if rep.get("class") else ""))
    meas = rep.get("measurement") or {}
    kind = rep.get("measurement_kind", "informational")
    if meas.get("annotation"):
        L.append(f"**{meas['annotation']}.**")
        L.append("")
    if rep.get("class"):
        ref = "TAK" if rep.get("reference_machine") else "NIE"
        kind_txt = {"reference": "pomiar referencyjny (prawdziwy sprzęt klasy)",
                    "emulation": f"emulacja klasy na maszynie `{meas.get('machine')}` ({meas.get('decision')})",
                    "informational": "wynik informacyjny, nie zalicza bramki"}[kind]
        gate = "TAK" if rep.get("gate_eligible") else "NIE"
        L.append(f"Rodzaj pomiaru: **{kind}** — {kind_txt}. Zalicza bramkę: **{gate}**. Maszyna referencyjna: {ref}. "
                 f"Wszystkie progi to `WORKING_VALUE` do decyzji właściciela.")
        for reason in meas.get("reasons") or []:
            L.append(f"- Dlaczego nie zalicza: {reason}")
    for reason in rep["invalid_reasons"]:
        L.append(f"- POMIAR NIEWAŻNY: {reason}")
    for mm in (rep.get("class") or {}).get("context_mismatch", []):
        L.append(f"- Niezgodne warunki z klasą: {mm}")
    L.append("")
    L.append("## Maszyna i ustawienia")
    L.append(f"- CPU: {s.get('cpu')} ({s.get('cpuCores')} wątków logicznych), RAM {s.get('systemMemoryMb')} MB")
    L.append(f"- GPU: {s.get('gpu')} ({s.get('gpuMemoryMb')} MB), API {s.get('graphicsApi')}; OS {s.get('os')}")
    L.append(f"- Ekran: {d.get('width')}x{d.get('height')} {d.get('fullScreenMode')}, {_f(d.get('refreshRateHz'), 1)} Hz, "
             f"VSync {d.get('vSyncCount')}, limit FPS {d.get('targetFrameRate')}, tier {d.get('qualityName')}")
    run = rep.get("run") or {}
    L.append(f"- Build: {run.get('buildLabel')} (development={run.get('development')}, Unity {run.get('unityVersion')}), etykieta `{run.get('label')}`")
    L.append("")
    L.append("## Klatki")
    ft = m.get("frame_ms") or {}
    L.append(f"Okno: {m['frames_window']} klatek po rozgrzewce {_f(m['warmup_s'], 1)} s, {_f(m['span_s'], 1)} s, średnio {_f(m['mean_fps'], 1)} FPS.")
    L.append("")
    L.append("| | p50 | p95 | p99 | max |")
    L.append("|---|---|---|---|---|")
    for key, label in (("frame_ms", "czas klatki [ms]"), ("cpu_main_ms", "CPU główny wątek [ms]"), ("gpu_ms", "GPU [ms]"),
                       ("draw_calls", "draw calls"), ("batches", "batches"), ("tris", "trójkąty")):
        v = m.get(key)
        if v:
            nd = 2 if key.endswith("_ms") else 0
            L.append(f"| {label} | {_f(v['p50'], nd)} | {_f(v['p95'], nd)} | {_f(v['p99'], nd)} | {_f(v['max'], nd)} |")
        else:
            L.append(f"| {label} | — | — | — | — |")
    L.append("")
    L.append("Klatki ponad próg: " + ", ".join(f"> {k} ms: {v['count']} ({_f(v['pct'], 2)} %)" for k, v in m["frames_over"].items()))
    L.append("")
    L.append("## Pamięć i ładowanie")
    um, pr = m["unity_memory"], m["process"]
    L.append(f"- Unity: allocated szczyt {_f(um['allocated_mb_peak'], 0)} MB, reserved szczyt {_f(um['reserved_mb_peak'], 0)} MB, "
             f"trend reserved {_f(um['reserved_mb_per_min'], 2)} MB/min, sterownik grafiki {_f(um['gfx_driver_mb_peak'], 0)} MB (tylko development)")
    L.append(f"- Proces (liczniki Windows): prywatna szczyt {_f(pr['private_mb']['peak'], 0)} MB, working set {_f(pr['working_set_mb']['peak'], 0)} MB, "
             f"VRAM dedykowany {_f(pr['gpu_dedicated_mb']['peak'], 0)} MB, temp. GPU {_f(pr['gpu_temp_c']['peak'], 0)} °C")
    L.append(f"- GC w oknie: {m['gc']['collections_in_window']}")
    loads = m["region_load_s"]["loads"]
    L.append("- Ładowanie scen: " + (", ".join(f"{l['scene']} {_f(l['seconds'], 2)} s ({l['start']})" for l in loads) if loads else "—"))
    ig = rep.get("in_game")
    cc = rep.get("cross_check")
    if ig and cc:
        L.append(f"- Kontrola krzyżowa (percentyle liczone w grze): p50 {_f(ig.get('p50Ms'))} / p95 {_f(ig.get('p95Ms'))} / p99 {_f(ig.get('p99Ms'))} ms"
                 f" — {'zgodne' if cc['ok'] else 'NIEZGODNE'} z parserem (maks. różnica {_f(cc['max_diff_ms'], 3)} ms)")
    if rep["checks"]:
        L.append("")
        L.append("## Budżet")
        L.append("| metryka | wartość | limit | wynik | status liczby |")
        L.append("|---|---|---|---|---|")
        for c in rep["checks"]:
            lim = _f(c['max']) + (f" (z tolerancją limitu FPS {_f(c['max_effective'], 3)})" if "max_effective" in c else "")
            L.append(f"| {c['metric']} | {_f(c['value'])} | {lim} | {c['status']} | {c['value_status']} |")
    L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Raport pomiaru PC (ADR 0266)")
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--budget", type=Path, default=DEFAULT_BUDGET)
    ap.add_argument("--machines", type=Path, default=DEFAULT_MACHINES,
                    help="maszyny referencyjne / emulujące klasy (D76), format kamion/pc-machines/1")
    ap.add_argument("--class", dest="cls", default=None, help="min | zalecany | wysoki (brak = bez porównania)")
    ap.add_argument("--warmup", type=float, default=None, help="nadpisuje rozgrzewkę z run.json [s]")
    ap.add_argument("--allow-context-mismatch", action="store_true",
                    help="porównuj mimo innej rozdzielczości/tieru/limitu FPS niż klasa (wynik tylko informacyjny)")
    ap.add_argument("--out", type=Path, default=None, help="prefiks plików raportu (domyślnie <run_dir>/pc-report)")
    args = ap.parse_args(argv)
    try:
        r = load_run(args.run_dir)
        budget = load_budget(args.budget) if args.cls else None
        machines = None
        if args.cls and (args.machines != DEFAULT_MACHINES or DEFAULT_MACHINES.exists()):
            machines = load_machines(args.machines)
        rep = evaluate(r, budget, args.cls, args.warmup, args.allow_context_mismatch, machines)
    except (FileNotFoundError, FormatError, KeyError, ValueError) as e:
        print(f"pc_metrics: {e}", file=sys.stderr)
        return EXIT_INVALID
    prefix = args.out or (args.run_dir / "pc-report")
    prefix.parent.mkdir(parents=True, exist_ok=True)
    Path(str(prefix) + ".json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(str(prefix) + ".md").write_text(render_md(rep), encoding="utf-8")
    ft = rep["metrics"].get("frame_ms") or {}
    print(f"verdict={rep['verdict']} frames={rep['metrics']['frames_window']} p50={ft.get('p50')} p95={ft.get('p95')} "
          f"p99={ft.get('p99')} -> {prefix}.md kind={rep['measurement_kind']} gate_eligible={str(rep['gate_eligible']).lower()}")
    return exit_code(rep)


if __name__ == "__main__":
    sys.exit(main())
