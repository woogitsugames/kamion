r"""Summary of all open reference manifests: images per source, licences, authors, route coverage per shot.

  uv run --project tools/refs python tools/refs/summarize.py [--md]  # --md prints the per-source Markdown rows
Writes artifacts/refs/open_sources_coverage.json (shot nr -> {source: count}) for the lead.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import refs_common as rc  # noqa: E402

SOURCES = ["kartaview", "panoramax", "commons", "openverse", "gugik-ortho", "bialystok-open-data"]


def summarize(raw_root: Path = rc.RAW_ROOT):
    pts = rc.parse_photo_list()
    out, cov = {}, {p["nr"]: {} for p in pts}
    for s in SOURCES:
        ents = rc.load_manifest(raw_root / s / "manifest.jsonl")
        lic = Counter(e.get("license_key") for e in ents.values())
        out[s] = {"count": len(ents), "licenses": dict(lic), "authors": len({e.get("author") for e in ents.values()}),
                  "shots_with_images": sorted({n for e in ents.values() for n in e.get("shots", []) if n < 100})}
        for e in ents.values():
            for n in e.get("shots", []):
                if n in cov:
                    cov[n][s] = cov[n].get(s, 0) + 1
    return out, cov


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--md", action="store_true")
    a = ap.parse_args(argv)
    out, cov = summarize()
    for s, v in out.items():
        print(f"{s}: {v['count']} items, licences {v['licenses']}, {v['authors']} authors, shots {len(v['shots_with_images'])}/55")
    street = [s for s in ("kartaview", "panoramax", "commons")]
    none = [n for n, c in cov.items() if not any(c.get(s) for s in street)]
    print("shots without street-level/Commons image:", none)
    p = rc.ART_ROOT / "open_sources_coverage.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"summary": out, "per_shot": cov, "no_street_or_commons": none}, indent=1), encoding="utf-8")
    print("written", p)


if __name__ == "__main__":
    main()
