"""Raport MD + wykresy PNG dla jednego katalogu pomiaru."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .formats import load_run_dir
from .metrics import (
    THERMAL_STATUS_NAMES,
    analyze_diag_series,
    campose_alternation,
    compute_frame_metrics,
    detect_target_fps,
    resolve_warmup,
    sliding_windows,
)
from .quality import check_run_quality

# Cele bramki z docs/PERFORMANCE_BUDGETS.md (A16 Low, WORKING_VALUE — cytowane, nie wymyślane).
GATE_TARGETS_A16_LOW = {
    "p95_ms_max": 34.0,
    "p99_ms_max": 40.0,
    "pss_mb_max": 1024.0,
    "note": "WORKING_VALUE z docs/PERFORMANCE_BUDGETS.md (A16 Low: p95 <= 34.0 ms, p99 <= 40 ms, PSS <= 1.0 GB)",
}


def _fmt(v, nd=2):
    return "n/a" if v is None else f"{v:.{nd}f}"


def render_charts(run_dir: Path, out_dir: Path, rows, target_ms: float, windows) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    t = np.array([r.t_s for r in rows])
    ft = np.array([r.frame_ms for r in rows])
    gpu = np.array([r.gpu_ms for r in rows if r.gpu_ms > 0])
    made: list[str] = []

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(t, ft, lw=0.5, color="tab:blue")
    ax.axhline(target_ms, color="tab:green", lw=1, label=f"cel {target_ms:.2f} ms")
    ax.axhline(1.5 * target_ms, color="tab:orange", lw=1, ls="--", label=f"1.5x cel = {1.5 * target_ms:.2f} ms")
    ax.axhline(2.0 * target_ms, color="tab:red", lw=1, ls=":", label=f"janky > {2.0 * target_ms:.2f} ms")
    ax.set_xlabel("t [s]")
    ax.set_ylabel("frame_ms [ms]")
    ax.set_title("Czasy klatek w czasie")
    ax.legend(fontsize=8)
    p = out_dir / "frametimes.png"
    fig.savefig(p, dpi=110, bbox_inches="tight")
    plt.close(fig)
    made.append(p.name)

    if windows.windows:
        ws = windows.windows
        x = [w.t_start_s + windows.window_s / 2 for w in ws]
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(x, [w.p95_ms for w in ws], lw=1.2, label="p95 w oknie 10 s")
        ax.plot(x, [w.fps for w in ws], lw=1.2, label="FPS w oknie 10 s", color="tab:orange")
        ax2 = ax.twinx()
        ax2.plot(x, [w.alternation_pct for w in ws], lw=1, color="tab:red", alpha=0.6, label="naprzemienność %")
        ax2.set_ylabel("naprzemienność [%]")
        ax.set_xlabel("t [s]")
        ax.set_title("Okna przesuwne 10 s: p95 / FPS / naprzemienność")
        p = out_dir / "windows.png"
        fig.savefig(p, dpi=110, bbox_inches="tight")
        plt.close(fig)
        made.append(p.name)

    if gpu.size:
        fig, ax = plt.subplots(figsize=(10, 3.5))
        ax.hist(gpu, bins=80, color="tab:purple")
        ax.set_xlabel("gpu_ms [ms]")
        ax.set_title(f"Histogram czasu GPU (n={gpu.size})")
        p = out_dir / "gpu_hist.png"
        fig.savefig(p, dpi=110, bbox_inches="tight")
        plt.close(fig)
        made.append(p.name)

    return made


def render_thermal_chart(run, out_dir: Path, therm) -> str | None:
    diags = run.get("diags") or []
    if not diags:
        return None
    t = np.array([d.t_s for d in diags])
    temp = np.array([d.get_float("temp") if d.get_float("temp") is not None else np.nan for d in diags])
    pss = np.array([d.get_float("pss") if d.get_float("pss") is not None else np.nan for d in diags])
    therm_s = np.array(
        [d.get_float("thermal") if d.get_float("thermal") is not None else np.nan for d in diags]
    )
    if np.isnan(temp).all() and np.isnan(pss).all():
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 4))
    if not np.isnan(temp).all():
        ax.plot(t, temp, lw=1.2, color="tab:red", label="temp [°C]")
    if not np.isnan(pss).all():
        ax.plot(t, pss, lw=1.2, color="tab:blue", label="PSS [MB]")
    if not np.isnan(therm_s).all():
        ax.step(t, therm_s, where="post", color="tab:gray", lw=1, alpha=0.7, label="thermal status")
    if therm.throttle_t_s is not None:
        ax.axvline(therm.throttle_t_s, color="tab:red", ls="--", lw=1, label=f"throttling t={therm.throttle_t_s:.0f} s")
    ax.set_xlabel("t [s]")
    ax.set_title("Temperatura / PSS / thermal status ([DIAG])")
    ax.legend(fontsize=8)
    p = out_dir / "thermal_pss.png"
    fig.savefig(p, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return p.name


def build_report_md(run: dict, fm, windows, therm, quality, charts: list[str], target_fps: int) -> str:
    run_dir = run["dir"]
    summary = run.get("summary") or {}
    metrics_json = run.get("metrics") or {}
    battery = run.get("battery")
    thermal_txt = run.get("thermal")
    lines: list[str] = []
    lines.append(f"# Raport bramki wydajności — {run_dir.name}")
    lines.append("")
    lines.append(f"Katalog pomiaru: `{run_dir}`")
    serial = (metrics_json.get("serial") or "?")
    ts = (metrics_json.get("timestamp") or run_dir.name)
    model = (metrics_json.get("device") or {}).get("ro.product.model", "?")
    lines.append(f"Telefon: {model} (serial `{serial}`), pomiar `{ts}`")
    if summary:
        lines.append(
            f"Build: `{summary.get('build', '?')}`, tier `{summary.get('qualityTier', '?')}`, "
            f"targetFps {summary.get('targetFps', '?')}, rozdzielczość {summary.get('resolution', '?')}"
        )
    lines.append("")
    lines.append("## Werdykt jakości pomiaru")
    lines.append("")
    if quality.valid:
        lines.append("**VALID** — brak przesłanek do odrzucenia.")
    else:
        lines.append("**DO ODRZUCENIA:**")
        for r in quality.reasons:
            lines.append(f"- {r}")
    for e in quality.evidence:
        lines.append(f"  - dowód: `{e}`")
    lines.append("")
    lines.append("## Metryki klatek (po warm-up, nearest-rank jak device-metrics.ps1)")
    lines.append("")
    lines.append(f"Cel: {target_fps} FPS = {fm.target_ms:.3f} ms/klatkę")
    lines.append("")
    lines.append("| metryka | wartość |")
    lines.append("|---|---|")
    lines.append(f"| próbki (n) | {fm.n} |")
    lines.append(f"| rozpiętość | {fm.span_s:.1f} s |")
    lines.append(f"| FPS średni (n/span) | {fm.mean_fps:.2f} |")
    lines.append(f"| FPS harmoniczny (1000/mean ms) | {fm.harmonic_fps:.2f} |")
    lines.append(f"| frame_ms p50 / p95 / p99 / max | {_fmt(fm.p50_ms)} / {_fmt(fm.p95_ms)} / {_fmt(fm.p99_ms)} / {_fmt(fm.max_ms)} ms |")
    lines.append(f"| GPU p50 / p95 / p99 | {_fmt(fm.gpu_p50_ms)} / {_fmt(fm.gpu_p95_ms)} / {_fmt(fm.gpu_p99_ms)} ms (n={fm.gpu_n}) |")
    lines.append(f"| CPU main p50 / p95 / p99 | {_fmt(fm.cpu_p50_ms)} / {_fmt(fm.cpu_p95_ms)} / {_fmt(fm.cpu_p99_ms)} ms (n={fm.cpu_n}) |")
    lines.append(f"| frame pacing MAD / RMS od celu | {_fmt(fm.pacing_mad_ms)} / {_fmt(fm.pacing_rms_ms)} ms |")
    lines.append(f"| klatki > 1.5x celu (> {1.5 * fm.target_ms:.2f} ms) | {fm.over_1_5x_count} ({fm.over_1_5x_pct:.2f} %) |")
    lines.append(f"| janky frames (> 2x celu = {2.0 * fm.target_ms:.2f} ms) | {fm.janky_count} ({fm.janky_pct:.2f} %) |")
    lines.append(f"| skoki czasu klatki (|Δ| ≥ 0,5×cel; nie ADR 0152) | {fm.alternation_count}/{fm.n - 1} = {fm.alternation_pct:.2f} % |")
    lines.append("")
    lines.append("## Okna przesuwne (10 s, krok 1 s)")
    lines.append("")
    if windows.worst_p95:
        w = windows.worst_p95
        lines.append(
            f"- najgorsze okno wg p95: t={w.t_start_s:.0f}–{w.t_end_s:.0f} s, p95={w.p95_ms:.2f} ms, "
            f"FPS={w.fps:.2f}, >1.5x={w.over_1_5x_pct:.1f} %, naprzemienność={w.alternation_pct:.1f} %"
        )
    if windows.worst_fps:
        w = windows.worst_fps
        lines.append(f"- najgorsze okno wg FPS: t={w.t_start_s:.0f}–{w.t_end_s:.0f} s, FPS={w.fps:.2f}")
    if windows.worst_alternation:
        w = windows.worst_alternation
        lines.append(
            f"- najgorsze okno wg naprzemienności: t={w.t_start_s:.0f}–{w.t_end_s:.0f} s, {w.alternation_pct:.1f} %"
        )
    lines.append("")
    lines.append("## Termika i PSS (serie [DIAG])")
    lines.append("")
    if therm.n:
        lines.append(f"- próbki [DIAG]: {therm.n}")
        lines.append(
            f"- temperatura: start {_fmt(therm.temp_start_c, 1)} °C, koniec {_fmt(therm.temp_end_c, 1)} °C, "
            f"max {_fmt(therm.temp_max_c, 1)} °C, trend {therm.temp_slope_c_per_min:+.3f} °C/min"
        )
        st = therm.max_thermal_status
        lines.append(
            f"- max thermal status: {st} ({THERMAL_STATUS_NAMES.get(st, '?') if st is not None else 'n/a'})"
        )
        if therm.throttle_t_s is not None:
            lines.append(f"- **throttling wykryty od t={therm.throttle_t_s:.0f} s**: {therm.throttle_reason}")
        else:
            lines.append("- throttling: nie wykryto")
        lines.append(
            f"- PSS: min {_fmt(therm.pss_min_mb, 1)} MB, max {_fmt(therm.pss_max_mb, 1)} MB, "
            f"trend {therm.pss_slope_mb_per_min:+.3f} MB/min"
            + (" — **podejrzenie wycieku**" if therm.pss_leak_suspected else "")
        )
        if therm.scale_min is not None:
            lines.append(f"- skala renderu min: {therm.scale_min:.2f}" + (f" (spadek od t={therm.scale_drop_t_s:.0f} s)" if therm.scale_drop_t_s else ""))
    else:
        lines.append("- brak serii [DIAG] w logcacie.")
    if battery:
        lines.append(f"- bateria (koniec pomiaru): {battery['level_pct']} %, {battery['temperature_c']:.1f} °C")
    if thermal_txt:
        lines.append(f"- `Thermal Status` z dumpsys: {thermal_txt['thermal_status']}")
    mem = run.get("meminfo")
    if mem:
        lines.append(f"- PSS total z meminfo: {mem['pss_mb']:.1f} MB")
    lines.append("")
    lines.append("## Bramka (cele A16 Low z docs/PERFORMANCE_BUDGETS.md — WORKING_VALUE)")
    lines.append("")
    lines.append(f"Cel: {GATE_TARGETS_A16_LOW['note']}")
    lines.append("")
    lines.append("| kryterium | cel | zmierzone | wynik |")
    lines.append("|---|---|---|---|")
    p95_ok = fm.p95_ms <= GATE_TARGETS_A16_LOW["p95_ms_max"]
    p99_ok = fm.p99_ms <= GATE_TARGETS_A16_LOW["p99_ms_max"]
    pss_val = therm.pss_max_mb or (mem or {}).get("pss_mb")
    pss_ok = pss_val is not None and pss_val <= GATE_TARGETS_A16_LOW["pss_mb_max"]
    lines.append(f"| frame p95 | <= {GATE_TARGETS_A16_LOW['p95_ms_max']} ms | {fm.p95_ms:.2f} ms | {'PASS' if p95_ok else 'FAIL'} |")
    lines.append(f"| frame p99 | <= {GATE_TARGETS_A16_LOW['p99_ms_max']} ms | {fm.p99_ms:.2f} ms | {'PASS' if p99_ok else 'FAIL'} |")
    lines.append(
        f"| PSS max | <= {GATE_TARGETS_A16_LOW['pss_mb_max']:.0f} MB | {_fmt(pss_val, 1)} MB | {'PASS' if pss_ok else ('FAIL' if pss_val is not None else 'n/a')} |"
    )
    lines.append(f"| throttling | brak | {'wykryty t=' + f'{therm.throttle_t_s:.0f} s' if therm.throttle_t_s is not None else 'brak'} | {'FAIL' if therm.throttle_t_s is not None else 'PASS'} |")
    lines.append("")
    if charts:
        lines.append("## Wykresy")
        lines.append("")
        for c in charts:
            lines.append(f"![{c}]({c})")
        lines.append("")
    lines.append("---")
    lines.append("Wygenerowane przez `perfgate` (tools/perf) — definicje metryk w `tools/perf/README.md`.")
    return "\n".join(lines) + "\n"


def generate_report(run_dir: Path, out_dir: Path | None = None, warmup_s: float | None = None,
                    target_fps: int | None = None, window_s: float = 10.0) -> Path:
    run = load_run_dir(run_dir)
    if run["frames"] is None:
        from .formats import ParseError

        raise ParseError(f"{run_dir}: brak frametimes.csv — nie ma czego raportować")
    tf = detect_target_fps(run, target_fps)
    warmup_s = resolve_warmup(run, warmup_s)
    fm = compute_frame_metrics(run["frames"], warmup_s=warmup_s, target_fps=tf)
    windows = sliding_windows(run["frames"], warmup_s=warmup_s, target_fps=tf, window_s=window_s)
    therm = analyze_diag_series(run.get("diags") or [])
    quality = check_run_quality(run, warmup_s=warmup_s)
    out_dir = Path(out_dir) if out_dir else Path(run_dir) / "perfgate-report"
    charts = render_charts(run_dir, out_dir, run["frames"], fm.target_ms, windows)
    tc = render_thermal_chart(run, out_dir, therm)
    if tc:
        charts.append(tc)
    md = build_report_md(run, fm, windows, therm, quality, charts, tf)
    for cp in (Path(run_dir) / "campose.csv", Path(run_dir) / "diag" / "campose.csv"):
        if cp.exists():
            alt = campose_alternation(cp)
            head = "\n## Naprzemienność pozy kamery (ADR 0152, campose.csv)\n\n| kolumna | naprzemienne klatki |\n|---|---|\n"
            md += head + "".join(f"| {c} | {100 * v:.1f} % |\n" for c, v in alt.items())
            break
    rp = out_dir / "report.md"
    rp.write_text(md, encoding="utf-8")
    return rp
