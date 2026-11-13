"""Byte-compare two derived world directories (ADR 0173).

    uv run --project tools/worldgen python tools/worldgen/qa/compare_world.py <dir_a> <dir_b> [--detail 5]

Prints one line per differing file. For instances_*.json it also says whether the difference is only the order
of the instances (same multiset) or real content (counts per prototype, positions). Exit 1 when anything differs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _instances(p: Path):
    d = json.loads(p.read_text(encoding="utf-8"))
    return d.get("instances", d) if isinstance(d, dict) else d


def _inst_detail(a: Path, b: Path) -> str:
    try:
        ia, ib = _instances(a), _instances(b)
    except Exception as e:  # noqa: BLE001
        return f"unreadable ({e})"
    if not isinstance(ia, list) or not isinstance(ib, list):
        return "not a list"
    ka = Counter(json.dumps(x, sort_keys=True) for x in ia)
    kb = Counter(json.dumps(x, sort_keys=True) for x in ib)
    if ka == kb:
        return f"ORDER ONLY ({len(ia)} instances)"
    pa = Counter(x.get("p") for x in ia if isinstance(x, dict))
    pb = Counter(x.get("p") for x in ib if isinstance(x, dict))
    dp = {k: pb.get(k, 0) - pa.get(k, 0) for k in set(pa) | set(pb) if pa.get(k, 0) != pb.get(k, 0)}
    only_a, only_b = sum((ka - kb).values()), sum((kb - ka).values())
    return f"CONTENT {len(ia)}->{len(ib)} instances, {only_a} only in A, {only_b} only in B, per-prototype delta {dp}"


def compare(da: Path, db: Path, detail: int = 5) -> list[str]:
    fa = {p.name for p in da.iterdir() if p.is_file()}
    fb = {p.name for p in db.iterdir() if p.is_file()}
    out = [f"ONLY_A {n}" for n in sorted(fa - fb)] + [f"ONLY_B {n}" for n in sorted(fb - fa)]
    n_detail = 0
    for n in sorted(fa & fb):
        a, b = da / n, db / n
        if a.stat().st_size == b.stat().st_size and _sha(a) == _sha(b):
            continue
        line = f"DIFF {n} {a.stat().st_size} -> {b.stat().st_size} B"
        if n.startswith("instances_") and n.endswith(".json") and n_detail < detail:
            line += " :: " + _inst_detail(a, b)
            n_detail += 1
        out.append(line)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--detail", type=int, default=5)
    x = ap.parse_args()
    lines = compare(Path(x.a), Path(x.b), x.detail)
    print("\n".join(lines) if lines else "IDENTICAL")
    sys.exit(1 if lines else 0)


if __name__ == "__main__":
    main()
