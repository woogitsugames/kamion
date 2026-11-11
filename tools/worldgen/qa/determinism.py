"""Determinism probe of the road stage (ADR 0096).

    uv run --project tools/worldgen python tools/worldgen/qa/determinism.py --region <id> [--out parts.json]

Prints `TOTAL <sha256> <parts>`: one hash over every mesh part (layer, material, source id, vertices, triangles) of
roads.pipeline.build (pass 1, raw NMT). Run it under different PYTHONHASHSEED values: the hash must not change
(tests/gis/test_determinism.py). `--out` writes the per-part hashes, to diff two runs part by part.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def parts_hash(parts):
    """(total sha256, rows [index, layer, material, src, vertices, triangles, sha16]) of a MeshBuf part list."""
    tot, rows = hashlib.sha256(), []
    for i, p in enumerate(parts):
        h = hashlib.sha256()
        h.update(f"{p.layer}|{p.mat}|{p.src}".encode("utf-8"))
        h.update(np.ascontiguousarray(np.asarray(p.V, np.float64)).tobytes())
        h.update(np.ascontiguousarray(np.asarray(p.T, np.int64)).tobytes())
        d = h.hexdigest()[:16]
        tot.update(d.encode("ascii"))
        rows.append([i, p.layer, p.mat, p.src, int(len(p.V)), int(len(p.T)), d])
    return tot.hexdigest(), rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    from roads import pipeline
    w = pipeline.build(a.region)
    total, rows = parts_hash(w.buf.parts)
    if a.out:
        Path(a.out).write_text(json.dumps({"total": total, "parts": rows}), encoding="utf-8")
    print("TOTAL", total, len(rows))


if __name__ == "__main__":
    main()
