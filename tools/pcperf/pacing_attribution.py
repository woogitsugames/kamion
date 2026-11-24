"""Frame-pacing attribution (ADR 0333): split slow frames of a player run into "clean" and "contended" seconds.

Joins the player's per-frame CSV (frametimes.csv v1 from -shot/-quit_t runs, or frames.csv from -metrics runs) with
sysload.csv written next to it by scripts/sysload-sampler.ps1 (CPU of the game / everything else, foreground window,
GPU P-state). A frame is "contended" when the sysload sample covering it shows other processes above --other-cpu
(% of the whole machine), the game window not in the foreground, or (with --gpu-util-margin) GPU utilisation far above
what the game's own GPU time explains. The foreground rule is opt-in (--require-foreground). Gate 3 (D69: <= 12 frames > 40 ms per trip) should be judged on the clean part;
the contended part says the measurement was disturbed, not that the game hitched.

Usage:
  uv run --no-project python tools/pcperf/pacing_attribution.py <run_dir> [--threshold-ms 40] [--other-cpu 10]
      [--offset-s 0.5] [--t-min 10] [--t-max N] [--json out.json]
Exit: 0 = report written; 2 = input missing.
All thresholds are WORKING_VALUE (s24, one machine: i5-10400F / GTX 1070).
"""
from __future__ import annotations

import argparse
import bisect
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Sample:
    t: float            # t_game_s (process clock) shifted by -offset -> player clock
    cpu_other: float
    cpu_game: float
    game_fg: bool
    fg_name: str
    pstate: str
    gpu_util: float | None
    top: str


@dataclass
class Result:
    frames: int = 0
    slow: int = 0
    slow_clean: int = 0
    slow_contended: int = 0
    slow_unsampled: int = 0
    seconds_sampled: int = 0
    seconds_contended: int = 0
    reasons: Counter = field(default_factory=Counter)
    contenders: Counter = field(default_factory=Counter)
    clean_slow_list: list = field(default_factory=list)


def window_start_s(run: Path) -> float:
    """frames.csv (-metrics) counts t_s from the start of the recording window; run.json gives that start in
    realtimeSinceStartup. frametimes.csv (Boot diagnostics) already counts from the player start -> 0."""
    p = run / "run.json"
    if (run / "frames.csv").exists() and p.exists():
        try:
            return float(json.loads(p.read_text(encoding="utf-8"))["recording"]["windowStartRealtime_s"])
        except (KeyError, ValueError, TypeError):
            return 0.0
    return 0.0


def read_frames(run: Path) -> list[tuple[float, float]]:
    shift = window_start_s(run)
    for name in ("frames.csv", "frametimes.csv"):
        p = run / name
        if p.exists():
            out = []
            with p.open(newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    try:
                        out.append((float(row["t_s"]) + shift, float(row["frame_ms"])))
                    except (KeyError, ValueError):
                        continue
            return out
    return []


def _f(x: str) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def read_sysload(path: Path, offset_s: float) -> list[Sample]:
    out = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t = _f(row.get("t_game_s"))
            if t is None:
                continue
            out.append(Sample(
                t=t - offset_s,
                cpu_other=_f(row.get("cpu_other_pct")) or 0.0,
                cpu_game=_f(row.get("cpu_game_pct")) or 0.0,
                game_fg=row.get("game_fg") == "1",
                fg_name=row.get("fg_name") or "",
                pstate=row.get("gpu_pstate") or "",
                gpu_util=_f(row.get("gpu_util_pct")),
                top=row.get("top_other") or "",
            ))
    out.sort(key=lambda s: s.t)
    return out


def contention_reasons(s: Sample, other_cpu: float, require_fg: bool) -> list[str]:
    r = []
    if s.cpu_other >= other_cpu:
        r.append(f"other_cpu>={other_cpu:g}%")
    if require_fg and not s.game_fg:
        r.append("not_foreground")
    if s.pstate and s.pstate not in ("P0", "P1", "P2"):
        r.append(f"gpu_{s.pstate}")
    return r


def attribute(frames, samples, threshold_ms=40.0, other_cpu=10.0, t_min=10.0, t_max=float("inf"),
              require_fg=False, max_gap_s=2.5) -> Result:
    res = Result()
    ts = [s.t for s in samples]
    contended_secs = set()
    for s in samples:
        if contention_reasons(s, other_cpu, require_fg):
            contended_secs.add(round(s.t))
    res.seconds_sampled = len(samples)
    res.seconds_contended = len(contended_secs)
    for t, ms in frames:
        if t < t_min or t > t_max:
            continue
        res.frames += 1
        if ms <= threshold_ms:
            continue
        res.slow += 1
        # The sample at time T covers the interval (T - interval, T]: first sample with t >= frame time.
        i = bisect.bisect_left(ts, t)
        if i >= len(samples) or samples[i].t - t > max_gap_s:
            res.slow_unsampled += 1
            continue
        s = samples[i]
        reasons = contention_reasons(s, other_cpu, require_fg)
        if reasons:
            res.slow_contended += 1
            for r in reasons:
                res.reasons[r] += 1
            for item in s.top.split(";")[:3]:
                if ":" in item:
                    res.contenders[item.split(":", 1)[0]] += 1
        else:
            res.slow_clean += 1
            res.clean_slow_list.append((round(t, 2), round(ms, 1), round(s.cpu_other, 1)))
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--sysload", type=Path, default=None, help="default: <run_dir>/sysload.csv")
    ap.add_argument("--threshold-ms", type=float, default=40.0)
    ap.add_argument("--other-cpu", type=float, default=10.0, help="%% of the whole machine (WORKING_VALUE)")
    ap.add_argument("--offset-s", type=float, default=0.5,
                    help="process start -> Unity realtimeSinceStartup (UNVERIFIED, ~0.3-1 s)")
    ap.add_argument("--t-min", type=float, default=10.0)
    ap.add_argument("--t-max", type=float, default=float("inf"))
    ap.add_argument("--require-foreground", action="store_true",
                    help="count 'game not in foreground' as contention (s24 A/B E1/E2: no effect on its own, so off by default)")
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    frames = read_frames(a.run_dir)
    sl = a.sysload or (a.run_dir / "sysload.csv")
    if not frames or not sl.exists():
        print(f"missing frames.csv/frametimes.csv or {sl}", file=sys.stderr)
        return 2
    samples = read_sysload(sl, a.offset_s)
    r = attribute(frames, samples, a.threshold_ms, a.other_cpu, a.t_min, a.t_max, a.require_foreground)
    print(f"frames {r.frames}  > {a.threshold_ms:g} ms: {r.slow}  clean {r.slow_clean}  contended {r.slow_contended}"
          f"  unsampled {r.slow_unsampled}")
    print(f"sysload seconds {r.seconds_sampled}, contended {r.seconds_contended}")
    if r.reasons:
        print("reasons:", ", ".join(f"{k}={v}" for k, v in r.reasons.most_common()))
    if r.contenders:
        print("top other processes during contended slow frames:",
              ", ".join(f"{k}={v}" for k, v in r.contenders.most_common(8)))
    for x in r.clean_slow_list[:40]:
        print(f"  clean slow t={x[0]} ms={x[1]} other_cpu={x[2]}")
    if a.json:
        a.json.write_text(json.dumps({
            "frames": r.frames, "threshold_ms": a.threshold_ms, "slow": r.slow, "slow_clean": r.slow_clean,
            "slow_contended": r.slow_contended, "slow_unsampled": r.slow_unsampled,
            "seconds_sampled": r.seconds_sampled, "seconds_contended": r.seconds_contended,
            "reasons": dict(r.reasons), "contenders": dict(r.contenders.most_common(20)),
            "clean_slow": r.clean_slow_list, "other_cpu_pct": a.other_cpu, "offset_s": a.offset_s,
        }, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
