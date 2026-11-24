"""forest-height-s24: numbers of the ADR 0339 prototype tiles -> artifacts/forest-height-s24/numbers.txt

    uv run --project tools/worldgen python artifacts/forest-height-s24/tools/summary.py [after-round, default r2-after]

Sources: Data/Regions/<id>/forest_chm.json, generated/streetscape_qa.json (after), r0-before-qa/<id>.streetscape_qa.json
(the QA file of main before the rebuild - an OLDER build of main, not the same code), <round>/dk65-05-classrule/
streetscape_qa.json (the same code with KAMION_FOREST_CHM=0: the clean baseline), stats.txt of the control cameras.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
A = REPO / "artifacts" / "forest-height-s24"
ROUND = sys.argv[1] if len(sys.argv) > 1 else "r2-after"
TILES = ("dk65-04", "dk65-05", "dw671-tykocin-03")


def qa(p):
    return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else None


def frames(q):
    f = q["mesh_budget"]["frame_estimate"]
    hi = max(f, key=lambda x: x["tris_high"])
    lo = max(f, key=lambda x: x["tris_low"])
    return hi["camera"], hi["tris_high"], lo["camera"], lo["tris_low"]


def cam_stats(p):
    out = {}
    if not Path(p).exists():
        return out
    cur = None
    for line in Path(p).read_text(encoding="utf-8").splitlines():
        m = re.match(r"(\S+): objects=\d+ drawsEst=(\d+) .*trisExact=(\d+)", line)
        if m:
            cur = m.group(1)
            out[cur] = {"draws": int(m.group(2)), "tris": int(m.group(3))}
            continue
        m = re.match(r"\s+\S+ instanced .*draws (\d+), instances (\d+), .*forest HLOD cells (\d+), trianglesExact (\d+)", line)
        if m and cur:
            out[cur].update({"inst_draws": int(m.group(1)), "instances": int(m.group(2)), "hlod_cells": int(m.group(3)),
                             "inst_tris": int(m.group(4))})
    return out


L = [f"# ADR 0339 — liczby prototypu (runda {ROUND})", ""]
L += ["## Model koron (NMPT − NMT) i drzewostany", "",
      "| Kafel | wierzch koron p10 / p50 / p90 / p99 [m] | drzewostany | luki [m²] | drzewa: w lukach / przerzedzone / młode / dojrzałe | wys. drzew okapu p10 / p50 / p90 / max [m] |",
      "|---|---|---|---|---|---|"]
for t in TILES:
    c = qa(REPO / "Data" / "Regions" / t / "forest_chm.json")
    q = qa(REPO / "Data" / "Regions" / t / "generated" / "streetscape_qa.json")
    fc = (q or {}).get("vegetation", {}).get("forest_chm")
    if not c or not fc:
        L.append(f"| `{t}` | (brak przebudowy) | | | | |")
        continue
    s, h = c["stats"]["top_m"], fc.get("canopy_h_m", {})
    L.append(f"| `{t}` | {s['p10']} / {s['p50']} / {s['p90']} / {s['p99']} | {fc['stands']} | {fc['openings_m2']:.0f} | "
             f"{fc['gap']} / {fc['thinned']} / {fc['young']} / {fc['mature']} | {h.get('p10')} / {h.get('p50')} / {h.get('p90')} / {h.get('max')} |")
L += ["", "## Budżet generatora (`streetscape_qa.json`)", "",
      "„Przed” = plik QA z main sprzed przebudowy (starszy build main, inny kod niż HEAD — różnice nie pochodzą tylko z tego ADR).", "",
      "| Kafel | drzewa (instancje) przed → po | HLOD lasu: komórki, trójkąty przed → po | najgorsza klatka High przed → po | najgorsza klatka Low przed → po |",
      "|---|---|---|---|---|"]
for t in TILES:
    a, b = qa(A / "r0-before-qa" / f"{t}.streetscape_qa.json"), qa(REPO / "Data" / "Regions" / t / "generated" / "streetscape_qa.json")
    if not a or not b or "forest_chm" not in b["vegetation"]:
        continue
    ha, hb = a["vegetation"]["forest_hlod"], b["vegetation"]["forest_hlod"]
    fa, fb = frames(a), frames(b)
    L.append(f"| `{t}` | {sum(a['vegetation']['trees'].values())} → {sum(b['vegetation']['trees'].values())} | "
             f"{ha['cells']}, {ha['triangles']} → {hb['cells']}, {hb['triangles']} | `{fa[0]}` {fa[1]} → `{fb[0]}` {fb[1]} | "
             f"`{fa[2]}` {fa[3]} → `{fb[2]}` {fb[3]} |")
ab = qa(A / ROUND / "dk65-05-classrule" / "streetscape_qa.json")
b = qa(REPO / "Data" / "Regions" / "dk65-05" / "generated" / "streetscape_qa.json")
if ab and b and "forest_chm" in b["vegetation"]:
    L += ["", "### Czysta ablacja `dk65-05`: ten sam kod, `KAMION_FOREST_CHM=0` → model koron", "",
          "| | reguła klasowa | model koron | Δ |", "|---|---|---|---|"]
    ta, tb = sum(ab["vegetation"]["trees"].values()), sum(b["vegetation"]["trees"].values())
    L.append(f"| instancje drzew / krzewów / runa | {ta} | {tb} | {tb - ta:+d} ({100.0 * (tb - ta) / ta:+.1f} %) |")
    ha, hb = ab["vegetation"]["forest_hlod"], b["vegetation"]["forest_hlod"]
    L.append(f"| HLOD lasu — trójkąty w kaflu | {ha['triangles']} | {hb['triangles']} | {hb['triangles'] - ha['triangles']:+d} "
             f"({100.0 * (hb['triangles'] - ha['triangles']) / ha['triangles']:+.1f} %) |")
    fa = {f["camera"]: f for f in ab["mesh_budget"]["frame_estimate"]}
    fb = {f["camera"]: f for f in b["mesh_budget"]["frame_estimate"]}
    for key, name in (("tris_high", "High"), ("tris_low", "Low")):
        wa, wb = max(fa.values(), key=lambda f: f[key]), max(fb.values(), key=lambda f: f[key])
        L.append(f"| najgorsza klatka {name} (szacunek generatora) | `{wa['camera']}` {wa[key]} | `{wb['camera']}` {wb[key]} | {wb[key] - wa[key]:+d} |")
        d = sorted(((fb[c][key] - fa[c][key], c) for c in fa if c in fb))
        L.append(f"| Δ {name} po kamerach: min / max / suma ({len(d)} kamer) | | | {d[0][0]:+d} (`{d[0][1]}`) / {d[-1][0]:+d} (`{d[-1][1]}`) / {sum(x for x, _ in d):+d} |")
    L.append(f"| gatunki okapu + podszyt (instancje) | {json.dumps(ab['vegetation']['trees'], sort_keys=True)} | {json.dumps(b['vegetation']['trees'], sort_keys=True)} | |")
L += ["", "## Kamery kontrolne lasu (edytor, tier High, 1920 × 1080; `stats.txt`: szacunek przed batchingiem SRP)", "",
      "| Kafel | Kamera | światło | trójkąty przed → po | draws (szac.) przed → po | instancje: draws / trójkąty przed → po | komórki HLOD w kadrze |",
      "|---|---|---|---|---|---|---|"]
for t in TILES:
    for light in ("clear", "overcast"):
        sa, sb = cam_stats(A / "r0-before" / t / f"High-{light}" / "stats.txt"), cam_stats(A / ROUND / t / f"High-{light}" / "stats.txt")
        for cam in sorted(set(sa) & set(sb)):
            x, y = sa[cam], sb[cam]
            L.append(f"| `{t}` | `{cam}` | {light} | {x['tris']} → {y['tris']} ({100.0 * (y['tris'] - x['tris']) / x['tris']:+.1f} %) | {x['draws']} → {y['draws']} | "
                     f"{x.get('inst_draws')} / {x.get('inst_tris')} → {y.get('inst_draws')} / {y.get('inst_tris')} | {x.get('hlod_cells')} → {y.get('hlod_cells')} |")
(A / "numbers.txt").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
print("\n".join(L))
