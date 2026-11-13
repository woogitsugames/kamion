"""Compact review evidence, with per-camera image metrics and hashes before cleanup."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def main():
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    p.add_argument("--after", default="after")
    args = p.parse_args()
    metrics = []
    for condition in ("Low-clear", "Low-overcast", "High-clear", "High-overcast"):
        before = args.root / "before" / condition
        after = args.root / args.after / condition
        pairs = args.root / "pairs" / condition
        pairs.mkdir(parents=True, exist_ok=True)
        sheets = args.root / "sheets" / condition
        sheets.mkdir(parents=True, exist_ok=True)
        files = sorted(f for f in before.glob("*.png") if not f.stem.endswith(("_mask", "_envcube")))
        rows = []
        for f in files:
            g = after / f.name
            a, b = Image.open(f).convert("RGB"), Image.open(g).convert("RGB")
            if a.size != b.size:
                raise ValueError(f"Resolution changed: {f}")
            delta = np.abs(np.asarray(a, dtype=float) - np.asarray(b, dtype=float))
            entry = dict(condition=condition, camera=f.stem, mae=float(delta.mean()),
                         p99=float(np.percentile(delta, 99)), fraction_channels_gt10=float((delta > 10).mean()),
                         before_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),
                         after_sha256=hashlib.sha256(g.read_bytes()).hexdigest())
            metrics.append(entry)
            a.thumbnail((480, 222), Image.Resampling.LANCZOS)
            b.thumbnail((480, 222), Image.Resampling.LANCZOS)
            pair = Image.new("RGB", (960, 252), "white")
            pair.paste(a, (0, 30)); pair.paste(b, (480, 30))
            ImageDraw.Draw(pair).text((8, 7), f"{f.stem} | PRZED                               PO | MAE {entry['mae']:.3f}", fill="black")
            pair.save(pairs / f"{f.stem}.jpg", quality=88)
            rows.append((entry["mae"], pair))
        # All images, ordered by change so the largest differences are reviewed first.
        rows.sort(key=lambda r: r[0], reverse=True)
        for start in range(0, len(rows), 3):
            page = Image.new("RGB", (960, 756), "white")
            for offset, (_, pair) in enumerate(rows[start:start + 3]):
                page.paste(pair, (0, offset * 252))
            page.save(sheets / f"sheet-{start//3:03d}.jpg", quality=88)
    (args.root / "image-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pairs": len(metrics), "changed": sum(m["mae"] > 0 for m in metrics),
                      "max_mae": max(m["mae"] for m in metrics)}))


if __name__ == "__main__":
    main()
