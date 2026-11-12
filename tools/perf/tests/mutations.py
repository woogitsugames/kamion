"""Mutacje definicji metryk do testu mutacyjnego (weryfikacja B).

Każda mutacja psuje JEDNĄ definicję; odpowiedni test pytest musi przez to
zakończyć się FAIL. Aktywacja przez zmienną środowiskową PERFGATE_MUTATION
(patrz conftest.py); sterownik: tools/perf/mutation_check.py.
"""

import numpy as np


def apply(name: str) -> None:
    import perfgate.compare as compare
    import perfgate.formats as formats
    import perfgate.metrics as metrics
    import perfgate.quality as quality

    if name == "percentile-linear":
        metrics.nearest_rank_percentile = lambda s, p: float(np.percentile(s, p * 100))

    elif name == "alternation-threshold-0.9":
        orig = metrics.compute_frame_metrics

        def cfm(rows, warmup_s=5.0, target_fps=metrics.DEFAULT_TARGET_FPS):
            fm = orig(rows, warmup_s, target_fps)
            kept = [r for r in rows if r.t_s >= warmup_s] or list(rows)
            ft = np.array([r.frame_ms for r in kept])
            if len(ft) > 1:
                alt = np.abs(np.diff(ft)) >= 0.9 * fm.target_ms  # zmutowany próg
                fm.alternation_count = int(alt.sum())
                fm.alternation_pct = 100.0 * float(alt.sum() / (len(ft) - 1))
            return fm

        metrics.compute_frame_metrics = cfm

    elif name == "over-1.5x-1.4":
        orig = metrics.compute_frame_metrics

        def cfm(rows, warmup_s=5.0, target_fps=metrics.DEFAULT_TARGET_FPS):
            fm = orig(rows, warmup_s, target_fps)
            kept = [r for r in rows if r.t_s >= warmup_s] or list(rows)
            ft = np.array([r.frame_ms for r in kept])
            over = ft > 1.4 * fm.target_ms  # zmutowany próg
            fm.over_1_5x_count = int(over.sum())
            fm.over_1_5x_pct = 100.0 * float(over.mean())
            return fm

        metrics.compute_frame_metrics = cfm

    elif name == "janky-1.5x":
        orig = metrics.compute_frame_metrics

        def cfm(rows, warmup_s=5.0, target_fps=metrics.DEFAULT_TARGET_FPS):
            fm = orig(rows, warmup_s, target_fps)
            kept = [r for r in rows if r.t_s >= warmup_s] or list(rows)
            ft = np.array([r.frame_ms for r in kept])
            j = ft > 1.5 * fm.target_ms  # zmutowany próg janky
            fm.janky_count = int(j.sum())
            fm.janky_pct = 100.0 * float(j.mean())
            return fm

        metrics.compute_frame_metrics = cfm

    elif name == "fps-span-off-by-one":
        orig = metrics.compute_frame_metrics

        def cfm(rows, warmup_s=5.0, target_fps=metrics.DEFAULT_TARGET_FPS):
            fm = orig(rows, warmup_s, target_fps)
            fm.mean_fps = fm.n / (fm.span_s + 1.0)  # zmutowany mianownik
            return fm

        metrics.compute_frame_metrics = cfm

    elif name == "warmup-strict-gt":
        orig = metrics.compute_frame_metrics

        def cfm(rows, warmup_s=5.0, target_fps=metrics.DEFAULT_TARGET_FPS):
            kept = [r for r in rows if r.t_s > warmup_s] or list(rows)  # > zamiast >=
            return orig(kept, warmup_s=0.0, target_fps=target_fps)

        metrics.compute_frame_metrics = cfm

    elif name == "gpu-zero-included":
        orig = metrics.compute_frame_metrics

        def cfm(rows, warmup_s=5.0, target_fps=metrics.DEFAULT_TARGET_FPS):
            fm = orig(rows, warmup_s, target_fps)
            kept = [r for r in rows if r.t_s >= warmup_s] or list(rows)
            gpu = np.array([r.gpu_ms for r in kept])  # 0.0 włączone — błąd definicji
            fm.gpu_n = int(len(gpu))
            fm.gpu_p50_ms = metrics.percentile(gpu, 0.50)
            fm.gpu_p95_ms = metrics.percentile(gpu, 0.95)
            fm.gpu_p99_ms = metrics.percentile(gpu, 0.99)
            return fm

        metrics.compute_frame_metrics = cfm

    elif name == "window-min-frames-1000":
        orig = metrics.sliding_windows

        def sw(rows, warmup_s=5.0, target_fps=30, window_s=10.0, stride_s=1.0, min_frames=5):
            return orig(rows, warmup_s, target_fps, window_s, stride_s, min_frames=1000)

        metrics.sliding_windows = sw

    elif name == "throttle-status-4":
        metrics.THROTTLE_STATUS_THRESHOLD = 4  # MODERATE przestaje być throttlingiem

    elif name == "scale-drop-0.5":
        orig = metrics.analyze_diag_series

        def ads(diags):
            res = orig(diags)
            if not diags:
                return res
            res.throttle_t_s = None
            res.throttle_reason = None
            res.scale_drop_t_s = None
            t = np.array([d.t_s for d in diags], dtype=float)
            scale = np.array(
                [d.get_float("scale") if d.get_float("scale") is not None else np.nan for d in diags],
                dtype=float,
            )
            ok = ~np.isnan(scale)
            if ok.any():
                base = float(scale[ok][0])
                if base > 0:
                    dropped = np.where(ok & (scale <= 0.5 * base))[0]  # zmutowany próg
                    if len(dropped):
                        res.scale_drop_t_s = float(t[int(dropped[0])])
                        if res.throttle_t_s is None:
                            res.throttle_t_s = float(t[int(dropped[0])])
                            res.throttle_reason = "zmutowany próg skali 0.5"
            return res

        metrics.analyze_diag_series = ads

    elif name == "pss-leak-threshold-1000":
        metrics.PSS_LEAK_SLOPE_MB_PER_MIN = 1000.0

    elif name == "battery-min-10":
        quality.BATTERY_MIN_LEVEL_PCT = 10

    elif name == "temp-max-100":
        quality.START_TEMP_MAX_C = 100.0

    elif name == "verdict-swap":
        orig = compare.compare_runs

        def cr(*a, **kw):
            res = orig(*a, **kw)
            for r in res:
                if r.verdict == "regression":
                    r.verdict = "improvement"
                elif r.verdict == "improvement":
                    r.verdict = "regression"
            return res

        compare.compare_runs = cr

    elif name == "unknown-column-ok":
        import csv as _csv
        from pathlib import Path as _P

        def pfc(path):
            path = _P(path)
            with path.open(newline="", encoding="utf-8") as f:
                reader = _csv.reader(f)
                header = [h.strip() for h in next(reader)]
                idx = {c: i for i, c in enumerate(header)}
                rows = []
                for rec in reader:
                    if not rec:
                        continue
                    if len(rec) < len(header):
                        rec = rec + [""] * (len(header) - len(rec))
                    rows.append(
                        formats.FrameRow(
                            frame=int(rec[idx["frame"]]),
                            t_s=float(rec[idx["t_s"]]),
                            frame_ms=float(rec[idx["frame_ms"]]),
                            cpu_main_ms=float(rec[idx["cpu_main_ms"]]),
                            gpu_ms=float(rec[idx["gpu_ms"]]),
                            render_scale=float(rec[idx["render_scale"]]),
                            mirror_n=float(rec[idx["mirror_n"]]) if rec[idx["mirror_n"]].strip() else 0.0,
                            ab=rec[idx["ab"]].strip(),
                        )
                    )
                return rows

        formats.parse_frametimes_csv = pfc  # brak walidacji nieznanych kolumn

    else:
        raise ValueError(f"nieznana mutacja: {name}")


MUTATIONS = [
    "percentile-linear",
    "alternation-threshold-0.9",
    "over-1.5x-1.4",
    "janky-1.5x",
    "fps-span-off-by-one",
    "warmup-strict-gt",
    "gpu-zero-included",
    "window-min-frames-1000",
    "throttle-status-4",
    "scale-drop-0.5",
    "pss-leak-threshold-1000",
    "battery-min-10",
    "temp-max-100",
    "verdict-swap",
    "unknown-column-ok",
]
