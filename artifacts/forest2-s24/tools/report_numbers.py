"""forest2-s24: numbers of round 2 (ADR 0339 addendum) -> artifacts/forest2-s24/numbers.txt

    uv run --project tools/worldgen python artifacts/forest2-s24/tools/report_numbers.py <round> [ablation-dir]

before = artifacts/forest-height-s24/r5-after-qa/<id>.streetscape_qa.json + r5-after/<id>/High-*/stats.txt (round 1 as
merged, built 2026-11-24 from main before later merges); after = <round>/<id>/streetscape_qa.json + stats.txt.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
A = REPO / "artifacts" / "forest2-s24"
MAIN_A = Path(r"C:\Users\matma\Documents\Claude\kamion\artifacts\forest-height-s24")
ROUND = sys.argv[1]
TILES = ("dk65-05", "dk65-04", "dw671-tykocin-03")


def qa(p):
    return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else None


def worst(q, key):
    f = q["mesh_budget"]["frame_estimate"]
    w = max(f, key=lambda x: x[key])
    return w["camera"], w[key]


def cam_stats(p):
    out, cur = {}, None
    if not Path(p).exists():
        return out
    for line in Path(p).read_text(encoding="utf-8").splitlines():
        m = re.match(r"(\S+): objects=\d+ drawsEst=(\d+) .*trisExact=(\d+)", line)
        if m:
            cur = m.group(1)
            out[cur] = {"draws": int(m.group(2)), "tris": int(m.group(3))}
            continue
        m = re.match(r"\s+(\S+) instanced .*: draws (\d+), instances (\d+), .*trianglesExact (\d+)", line)
        if m and m.group(1) == cur:
            out[cur].update(idraws=int(m.group(2)), inst=int(m.group(3)), itris=int(m.group(4)))
    return out


L = [f"# ADR 0339 runda 2 — liczby prototypu (runda {ROUND})", ""]
L += ["## Generator (`streetscape_qa.json`): przed = runda 1 (r5, jak scalona) → po = runda 2", "",
      "| Kafel | instancje roślin | brzoza + brzoza młoda | klon + lipa + olsza | sosna + świerk | HLOD lasu: komórki, trójkąty | wys. okapu p10 / p50 / p90 / max [m] | cięcia skali | najgorsza klatka High | najgorsza klatka Low |",
      "|---|---|---|---|---|---|---|---|---|---|"]
for r in TILES:
    b, a = qa(MAIN_A / "r5-after-qa" / f"{r}.streetscape_qa.json"), qa(A / ROUND / r / "streetscape_qa.json")
    if not a or not b:
        continue
    tb, ta = b["vegetation"]["trees"], a["vegetation"]["trees"]
    s = lambda t, ks: sum(t.get("tree_" + k, 0) for k in ks)  # noqa: E731
    hb, ha = b["vegetation"]["forest_hlod"], a["vegetation"]["forest_hlod"]
    cb, ca = b["vegetation"]["forest_chm"], a["vegetation"]["forest_chm"]
    hh = lambda c: " / ".join(str(c["canopy_h_m"][k]) for k in ("p10", "p50", "p90", "max"))  # noqa: E731
    L.append(f"| `{r}` | {sum(tb.values())} → {sum(ta.values())} | {s(tb, ('birch', 'birchyoung'))} → {s(ta, ('birch', 'birchyoung'))} "
             f"| {s(tb, ('maple', 'linden', 'alder'))} → {s(ta, ('maple', 'linden', 'alder'))} | {s(tb, ('pine', 'spruce', 'pineyoung'))} → {s(ta, ('pine', 'spruce', 'pineyoung'))} "
             f"| {hb['cells']}, {hb['triangles']} → {ha['cells']}, {ha['triangles']} ({(ha['triangles'] / hb['triangles'] - 1) * 100:+.1f} %) "
             f"| {hh(cb)} → {hh(ca)} | {ca.get('scale_capped', 0)} z {ca['mature'] + ca['young']} "
             f"| `{worst(b, 'tris_high')[0]}` {worst(b, 'tris_high')[1]} → `{worst(a, 'tris_high')[0]}` {worst(a, 'tris_high')[1]} "
             f"| `{worst(b, 'tris_low')[0]}` {worst(b, 'tris_low')[1]} → `{worst(a, 'tris_low')[0]}` {worst(a, 'tris_low')[1]} |")
    fb = {f["camera"]: f for f in b["mesh_budget"]["frame_estimate"]}
    fa = {f["camera"]: f for f in a["mesh_budget"]["frame_estimate"]}
    for key in ("tris_high", "tris_low"):
        d = {c: fa[c][key] - fb[c][key] for c in fa if c in fb}
        if d:
            lo, hi = min(d, key=d.get), max(d, key=d.get)
            L.append(f"|  | Δ {key} po {len(d)} kamerach: min {d[lo]:+d} (`{lo}`), max {d[hi]:+d} (`{hi}`), suma {sum(d.values()):+d} | | | | | | | | |")
if len(sys.argv) > 2:
    ab = qa(A / sys.argv[2] / "streetscape_qa.json")
    a = qa(A / ROUND / "dk65-05" / "streetscape_qa.json")
    if ab and a:
        L += ["", "### Czysta ablacja `dk65-05`: ten sam kod i ten sam main, `KAMION_FOREST_CHM_R2=0` → runda 2", "",
              "| | runda 1 (R2=0) | runda 2 | Δ |", "|---|---|---|---|"]
        for name, f in (("instancje roślin", lambda q: sum(q["vegetation"]["trees"].values())),
                        ("HLOD lasu — trójkąty", lambda q: q["vegetation"]["forest_hlod"]["triangles"]),
                        ("najgorsza klatka High", lambda q: worst(q, "tris_high")[1]),
                        ("najgorsza klatka Low", lambda q: worst(q, "tris_low")[1])):
            L.append(f"| {name} | {f(ab)} | {f(a)} | {f(a) - f(ab):+d} ({(f(a) / f(ab) - 1) * 100:+.2f} %) |")
        fb = {f["camera"]: f for f in ab["mesh_budget"]["frame_estimate"]}
        fa = {f["camera"]: f for f in a["mesh_budget"]["frame_estimate"]}
        for key in ("tris_high", "tris_low"):
            d = {c: fa[c][key] - fb[c][key] for c in fa if c in fb}
            lo, hi = min(d, key=d.get), max(d, key=d.get)
            L.append(f"| Δ {key} po {len(d)} kamerach | | | min {d[lo]:+d} (`{lo}`), max {d[hi]:+d} (`{hi}`), suma {sum(d.values()):+d} |")
        L.append(f"| gatunki (instancje) | {json.dumps(ab['vegetation']['trees'], sort_keys=True)} | {json.dumps(a['vegetation']['trees'], sort_keys=True)} | |")
L += ["", "## Kamery kontrolne lasu (edytor, High, 1920 × 1080; `stats.txt`, szacunek przed batchingiem SRP)", "",
      "| Kafel | Kamera | trójkąty przed → po | draws (szac.) przed → po | instancje: draws / trójkąty przed → po |", "|---|---|---|---|---|"]
for r in TILES:
    sb, sa = cam_stats(MAIN_A / "r5-after" / r / "High-clear" / "stats.txt"), cam_stats(A / ROUND / r / "High-clear" / "stats.txt")
    for c in sa:
        if c in sb:
            x, y = sb[c], sa[c]
            L.append(f"| `{r}` | `{c}` | {x['tris']} → {y['tris']} ({(y['tris'] / x['tris'] - 1) * 100:+.1f} %) | {x['draws']} → {y['draws']} "
                     f"| {x.get('idraws')} / {x.get('itris')} → {y.get('idraws')} / {y.get('itris')} |")
(A / "numbers.txt").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
sys.stdout.buffer.write(("\n".join(L) + "\n").encode("utf-8"))
