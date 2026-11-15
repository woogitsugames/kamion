"""Streaming / region-pack run report (ADR 0273 §7) from a player log, the frame CSV and an optional memory CSV.

    uv run python scripts/stream-report.py --log artifacts/logs/win-run-<ts>.log \
        [--frames <persistentDataPath>/diag/frametimes.csv] [--memory artifacts/win/mem.csv] \
        [--threshold-ms 33.3] [--max-spikes 12] [--memory-limit-mb 6144] [--gate]

Reads only what the game already prints: "[STREAM] ..." (WorldStreamer), "[PACKS] ..." (RegionPackService),
"[SAFETY] reset ..." (WorldSafetyNet), frametimes.csv (DiagnosticsSampler: frame,t_s,frame_ms,...) and a memory CSV
with columns t_s,working_set_mb[,private_mb] (PowerShell sampler in ADR 0273). Works for a Windows player log and for a
logcat dump (Android). --gate: exit 1 when a criterion of ADR 0273 §7 fails (resets, late tiles, spikes, memory).
No third-party packages.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

RE_READY = re.compile(r"\[STREAM\] ready (\S+): load (\d+) ms, activation (\d+) ms \((\d+) chunks\), vehicle (-?\d+) m from the tile, "
                      r"resident (\d+) tiles / (\d+) MB")
RE_ON = re.compile(r"\[STREAM\] on: (.*)")
RE_OFF = re.compile(r"\[STREAM\] off: (.*)")
RE_PIN = re.compile(r"\[STREAM\] pinned (\S+) \((.*)\)")
RE_RESET = re.compile(r"\[SAFETY\] reset #(\d+) reason=(\S+)")


def percentile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    i = min(len(sorted_vals) - 1, max(0, int(-(-q * len(sorted_vals) // 1)) - 1))
    return sorted_vals[i]


def parse_log(text: str) -> dict:
    r: dict = {"on": None, "off": None, "ready": [], "loads": 0, "unloads": 0, "over_budget": 0, "closed_seams": 0,
               "pins": [], "resets": [], "packs_acquire": 0, "packs_release": 0, "packs_errors": 0}
    for line in text.splitlines():
        if "[STREAM]" in line:
            if m := RE_ON.search(line):
                r["on"] = m.group(1).strip()
            elif m := RE_OFF.search(line):
                r["off"] = m.group(1).strip()
            elif m := RE_READY.search(line):
                r["ready"].append({"scene": m.group(1), "load_ms": int(m.group(2)), "activation_ms": int(m.group(3)),
                                   "chunks": int(m.group(4)), "vehicle_m": int(m.group(5)), "resident": int(m.group(6)),
                                   "resident_mb": int(m.group(7))})
            elif m := RE_PIN.search(line):
                r["pins"].append({"tile": m.group(1), "why": m.group(2)})
            elif "[STREAM] load " in line:
                r["loads"] += 1
            elif "[STREAM] unload" in line:
                r["unloads"] += 1
            elif "over budget" in line:
                r["over_budget"] += 1
            elif "seam stays closed" in line:
                r["closed_seams"] += 1
        elif "[PACKS]" in line:
            if "[PACKS] acquire " in line:
                r["packs_acquire"] += 1
            elif "[PACKS] release " in line:
                r["packs_release"] += 1
            elif "failed" in line.lower() or "invalid" in line.lower() or "rejected" in line.lower():
                r["packs_errors"] += 1
        elif m := RE_RESET.search(line):
            r["resets"].append({"n": int(m.group(1)), "reason": m.group(2)})
    return r


def parse_frames(path: Path, threshold_ms: float) -> dict:
    ms: list[float] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                ms.append(float(row["frame_ms"]))
            except (KeyError, ValueError):
                continue
    s = sorted(ms)
    return {"frames": len(ms), "over_threshold": sum(1 for v in ms if v > threshold_ms), "threshold_ms": threshold_ms,
            "p50": percentile(s, 0.50), "p95": percentile(s, 0.95), "p99": percentile(s, 0.99), "max": s[-1] if s else 0.0}


def parse_memory(path: Path) -> dict:
    ws: list[float] = []
    priv: list[float] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                ws.append(float(row["working_set_mb"]))
                if row.get("private_mb"):
                    priv.append(float(row["private_mb"]))
            except (KeyError, ValueError):
                continue
    return {"samples": len(ws), "peak_working_set_mb": max(ws) if ws else 0.0, "peak_private_mb": max(priv) if priv else 0.0}


def gate(log: dict, frames: dict | None, mem: dict | None, max_spikes: int, memory_limit_mb: float | None) -> list[str]:
    fails = []
    if log["on"] is None:
        fails.append("streaming was not on (launch argument stream=1? neighbour tile scenes in the build?)")
    if log["resets"]:
        fails.append(f"{len(log['resets'])} safety-net reset(s)")
    late = [r["scene"] for r in log["ready"] if r["vehicle_m"] <= 0]
    if late:
        fails.append(f"tile(s) ready only with the vehicle already inside: {', '.join(late)}")
    if frames is not None and frames["over_threshold"] > max_spikes:
        fails.append(f"{frames['over_threshold']} frames > {frames['threshold_ms']} ms (limit {max_spikes})")
    if mem is not None and memory_limit_mb and mem["peak_working_set_mb"] > memory_limit_mb:
        fails.append(f"peak working set {mem['peak_working_set_mb']:.0f} MB > {memory_limit_mb:.0f} MB")
    return fails


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--frames", type=Path)
    ap.add_argument("--memory", type=Path)
    ap.add_argument("--threshold-ms", type=float, default=33.3)
    ap.add_argument("--max-spikes", type=int, default=12)
    ap.add_argument("--memory-limit-mb", type=float)
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    log = parse_log(a.log.read_text(encoding="utf-8", errors="replace"))
    frames = parse_frames(a.frames, a.threshold_ms) if a.frames and a.frames.exists() else None
    mem = parse_memory(a.memory) if a.memory and a.memory.exists() else None
    fails = gate(log, frames, mem, a.max_spikes, a.memory_limit_mb)
    if a.json:
        print(json.dumps({"log": log, "frames": frames, "memory": mem, "gate_failures": fails}, indent=1))
    else:
        print(f"STREAM  {'on: ' + log['on'] if log['on'] else 'OFF: ' + (log['off'] or 'no [STREAM] line')}")
        print(f"tiles   loads {log['loads']}, ready {len(log['ready'])}, unloads {log['unloads']}, over-budget {log['over_budget']}, "
              f"closed seams {log['closed_seams']}, pins {[p['tile'] for p in log['pins']]}")
        if log["ready"]:
            lo = sorted(r["load_ms"] for r in log["ready"])
            ac = sorted(r["activation_ms"] for r in log["ready"])
            print(f"timing  load ms p50 {percentile(lo, .5):.0f} / max {lo[-1]}, activation ms p50 {percentile(ac, .5):.0f} / max {ac[-1]}, "
                  f"min vehicle distance at ready {min(r['vehicle_m'] for r in log['ready'])} m, "
                  f"max resident {max(r['resident_mb'] for r in log['ready'])} MB (ESTIMATED)")
        print(f"packs   acquire {log['packs_acquire']}, release {log['packs_release']}, errors {log['packs_errors']}")
        print(f"safety  resets {len(log['resets'])} {[r['reason'] for r in log['resets']]}")
        if frames:
            print(f"frames  {frames['frames']}: p50 {frames['p50']:.1f} / p95 {frames['p95']:.1f} / p99 {frames['p99']:.1f} / max {frames['max']:.1f} ms, "
                  f"> {frames['threshold_ms']} ms: {frames['over_threshold']}")
        if mem:
            print(f"memory  peak working set {mem['peak_working_set_mb']:.0f} MB, private {mem['peak_private_mb']:.0f} MB ({mem['samples']} samples)")
        print("GATE    " + ("PASS" if not fails else "FAIL: " + "; ".join(fails)))
    return 1 if (a.gate and fails) else 0


if __name__ == "__main__":
    sys.exit(main())
