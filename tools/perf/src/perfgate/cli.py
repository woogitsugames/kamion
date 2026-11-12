"""CLI perfgate: report | compare | history | check | formats.

Przykłady:
  uv run --project tools/perf perfgate report artifacts/device/RFGL34SJYDZ/20261111-122732
  uv run --project tools/perf perfgate compare artifacts/perf-low-r1/final/gate3-Low-A artifacts/perf-low-r2/final/gate3-Low-A
  uv run --project tools/perf perfgate history artifacts/perf-low-r2/final --out artifacts/perf-low-r2/final/perfgate-history.md
  uv run --project tools/perf perfgate check artifacts/perf-low-r1/diag0/base0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from . import __version__
from .compare import compare_runs
from .formats import FORMATS, ParseError, load_run_dir
from .metrics import (
    analyze_diag_series,
    compute_frame_metrics,
    detect_target_fps,
    sliding_windows,
)
from .quality import check_run_quality
from .report import generate_report


def _load_frames(run_dir: Path, warmup_s: float):
    run = load_run_dir(run_dir)
    if run["frames"] is None:
        raise ParseError(f"{run_dir}: brak frametimes.csv")
    tf = detect_target_fps(run, None)
    kept = [r for r in run["frames"] if r.t_s >= warmup_s] or list(run["frames"])
    ft = np.array([r.frame_ms for r in kept], dtype=float)
    gpu = np.array([r.gpu_ms for r in kept if r.gpu_ms > 0], dtype=float)
    return run, tf, ft, gpu


def cmd_report(args) -> int:
    rp = generate_report(
        Path(args.run_dir),
        out_dir=Path(args.out) if args.out else None,
        warmup_s=args.warmup_s,
        target_fps=args.target_fps,
        window_s=args.window_s,
    )
    print(f"raport: {rp}")
    return 0


def cmd_compare(args) -> int:
    run_a, tf, ft_a, gpu_a = _load_frames(Path(args.dir_a), args.warmup_s)
    run_b, _, ft_b, gpu_b = _load_frames(Path(args.dir_b), args.warmup_s)
    target_ms = 1000.0 / tf
    comps = compare_runs(ft_a, ft_b, target_ms, gpu_a, gpu_b, boot=args.boot, seed=args.seed)
    print(f"# porównanie: A = {args.dir_a}  vs  B = {args.dir_b}  (cel {tf} FPS = {target_ms:.3f} ms)")
    print(f"# bootstrap B={args.boot}, seed={args.seed}; CI 95 % różnicy B - A")
    print("")
    print(f"| metryka | A | B | diff (B-A) | CI95 lo | CI95 hi | werdykt |")
    print("|---|---|---|---|---|---|---|")
    for c in comps:
        f = lambda v: "n/a" if v is None else f"{v:.3f}"
        print(f"| {c.name} | {f(c.a)} | {f(c.b)} | {f(c.diff)} | {f(c.ci95_lo)} | {f(c.ci95_hi)} | {c.verdict} |")
    if args.out:
        Path(args.out).write_text(
            "\n".join(
                [f"# porównanie {args.dir_a} vs {args.dir_b}", ""]
                + [
                    f"| {c.name} | {c.a} | {c.b} | {c.diff} | {c.ci95_lo} | {c.ci95_hi} | {c.verdict} |"
                    for c in comps
                ]
            ),
            encoding="utf-8",
        )
    return 0


def cmd_history(args) -> int:
    run_dirs = sorted({p.parent for root in args.root for p in Path(root).rglob("frametimes.csv")})
    if args.limit:
        run_dirs = run_dirs[: args.limit]
    rows = []
    for d in run_dirs:
        try:
            run = load_run_dir(d)
            tf = detect_target_fps(run, args.target_fps)
            fm = compute_frame_metrics(run["frames"], warmup_s=args.warmup_s, target_fps=tf)
            therm = analyze_diag_series(run.get("diags") or [])
            q = check_run_quality(run, warmup_s=args.warmup_s)
            mj = run.get("metrics") or {}
            rows.append((d, fm, therm, q, tf, mj.get("serial", "?")))
        except ParseError as e:
            print(f"UWAGA: pominięto {d}: {e}", file=sys.stderr)
    lines = [
        f"# Historia bramek — {len(rows)} pomiarów pod {', '.join(args.root)}",
        "",
        "| pomiar | telefon | cel FPS | n | FPS śr. | p50 | p95 | p99 | max | GPU p95 | >1.5x % | naprz. % | T start | T trend °C/min | throttling | PSS max MB | PSS trend MB/min | jakość |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for d, fm, therm, q, tf, serial in rows:
        lines.append(
            f"| `{d}` | {serial} | {tf} | {fm.n} | {fm.mean_fps:.2f} | {fm.p50_ms:.2f} | {fm.p95_ms:.2f} | "
            f"{fm.p99_ms:.2f} | {fm.max_ms:.2f} | {fm.gpu_p95_ms if fm.gpu_p95_ms is not None else float('nan'):.2f} | "
            f"{fm.over_1_5x_pct:.2f} | {fm.alternation_pct:.2f} | "
            f"{therm.temp_start_c if therm.temp_start_c is not None else float('nan'):.1f} | {therm.temp_slope_c_per_min:+.3f} | "
            f"{'t=' + format(therm.throttle_t_s, '.0f') + 's' if therm.throttle_t_s is not None else 'brak'} | "
            f"{therm.pss_max_mb if therm.pss_max_mb is not None else float('nan'):.0f} | {therm.pss_slope_mb_per_min:+.2f} | "
            f"{'VALID' if q.valid else 'ODRZUCONY: ' + '; '.join(q.reasons)} |"
        )
    out = "\n".join(lines) + "\n"
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        print(f"tabela historii: {args.out} ({len(rows)} pomiarów)")
    else:
        print(out)
    return 0


def cmd_check(args) -> int:
    run = load_run_dir(Path(args.run_dir))
    q = check_run_quality(run, warmup_s=args.warmup_s)
    if q.valid:
        print(f"VALID: {args.run_dir}")
        return 0
    print(f"DO ODRZUCENIA: {args.run_dir}")
    for r in q.reasons:
        print(f"- {r}")
    for e in q.evidence:
        print(f"  dowód: {e}")
    return 1


def cmd_formats(args) -> int:
    print("# Rozpoznane formaty pomiarów (wersja, opis)")
    for name, (ver, desc) in FORMATS.items():
        print(f"- `{name}` ({ver}): {desc}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfgate", description=__doc__)
    ap.add_argument("--version", action="version", version=f"perfgate {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("report", help="raport MD + PNG dla katalogu pomiaru")
    p.add_argument("run_dir")
    p.add_argument("--out", default=None)
    p.add_argument("--warmup-s", type=float, default=5.0)
    p.add_argument("--target-fps", type=int, default=None, choices=[30, 60])
    p.add_argument("--window-s", type=float, default=10.0)
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("compare", help="bootstrapowe porównanie dwóch przebiegów")
    p.add_argument("dir_a")
    p.add_argument("dir_b")
    p.add_argument("--warmup-s", type=float, default=5.0)
    p.add_argument("--boot", type=int, default=20000)
    p.add_argument("--seed", type=int, default=20261113)
    p.add_argument("--out", default=None)
    p.set_defaults(fn=cmd_compare)

    p = sub.add_parser("history", help="zbiorcza tabela wszystkich pomiarów pod root (można podać kilka)")
    p.add_argument("root", nargs="+")
    p.add_argument("--out", default=None)
    p.add_argument("--warmup-s", type=float, default=5.0)
    p.add_argument("--target-fps", type=int, default=None, choices=[30, 60])
    p.add_argument("--limit", type=int, default=None)
    p.set_defaults(fn=cmd_history)

    p = sub.add_parser("check", help="werdykt jakości pomiaru (exit 1 = do odrzucenia)")
    p.add_argument("run_dir")
    p.add_argument("--warmup-s", type=float, default=5.0)
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("formats", help="lista rozpoznanych formatów i wersji")
    p.set_defaults(fn=cmd_formats)

    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except ParseError as e:
        print(f"BŁĄD parsowania: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
