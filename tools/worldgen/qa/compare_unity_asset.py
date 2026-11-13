"""Semantic compare of two Unity text-serialised .asset files (ADR 0173).

    python tools/worldgen/qa/compare_unity_asset.py <a.asset> <b.asset>

Unity gives every sub-asset added with AddObjectToAsset a random local fileID on each import and writes the
sub-assets in fileID order, so two imports of identical data are not byte-identical. This tool replaces each
fileID by the referenced object's (class, m_Name, occurrence) key and compares the objects by that key.
Prints IDENTICAL or the differing objects; exit 1 when the content differs.
"""

from __future__ import annotations

import hashlib
import re
import sys
from collections import Counter
from pathlib import Path

HDR = re.compile(r"^--- !u!(\d+) &(-?\d+)", re.M)
NAME = re.compile(r"^  m_Name: (.*)$", re.M)
REF = re.compile(r"fileID: (-?\d+)")


def objects(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    heads = list(HDR.finditer(text))
    objs, seen = [], Counter()
    for k, h in enumerate(heads):
        body = text[h.end(): heads[k + 1].start() if k + 1 < len(heads) else len(text)]
        m = NAME.search(body)
        base = (h.group(1), m.group(1) if m else "")
        seen[base] += 1
        objs.append((h.group(2), base + (seen[base],), body))
    # occurrence index of equal (class, name) pairs follows file order = fileID order: unstable. Re-key duplicates by
    # the content hash (with references removed) so equal objects pair up whatever their fileIDs.
    dup = {b for b, n in seen.items() if n > 1}
    ids = {}
    for fid, key, body in objs:
        if key[:2] in dup:
            key = key[:2] + (hashlib.sha1(REF.sub("fileID: _", body).encode()).hexdigest()[:12],)
        ids[fid] = key
    out = {}
    for fid, _, body in objs:
        norm = REF.sub(lambda m: "fileID: " + ("|".join(map(str, ids[m.group(1)])) if m.group(1) in ids else m.group(1)),
                       body)
        out[ids[fid]] = hashlib.sha256(norm.encode()).hexdigest()
    return out


def main():
    a, b = objects(Path(sys.argv[1])), objects(Path(sys.argv[2]))
    diff = sorted(set(a) ^ set(b), key=str) + sorted((k for k in set(a) & set(b) if a[k] != b[k]), key=str)
    print(f"objects {len(a)} / {len(b)}")
    if not diff:
        print("IDENTICAL (content; fileIDs and object order ignored)")
        return 0
    for k in diff[:30]:
        print("DIFF", k, "A" if k in a else "-", "B" if k in b else "-")
    print(f"{len(diff)} differing objects")
    return 1


if __name__ == "__main__":
    sys.exit(main())
