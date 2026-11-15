"""Fill ADR 0211 sections from the measured files. Usage: python adr_patch.py <tag> (run in the worktree root)."""
import re
import subprocess
import sys
from pathlib import Path

tag = sys.argv[1]
n = Path("artifacts/tunnel-0211")
adr = Path("docs/adr/0211-tunel-plyta-nad-wykopem-dk8.md")
s = adr.read_text(encoding="utf-8")


def load(d):
    out = {}
    for line in (Path(d) / "stats.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"(\S+): objects=\d+ drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)", line)
        if m:
            out[m[1]] = (int(m[2]), int(m[4]))
    return out


rows = []
cams = ["underpass-eb-szymanskiego", "underpass-wb-szymanskiego", "produkcyjna-to-rondo-szymanskiego", "route-s1110",
        "route-s1427", "tertiary-to-rondo-under-kleeberga", "tunnel-eb-inside", "tunnel-wb-inside", "cut-wall-oblique-sw",
        "rondo-szymanskiego-island-nw"]
base = Path("C:/Users/matma/Documents/Claude/kamion/artifacts/bialystok-dk65-t2-0206/vqa-r4")
tab = {}
for t in ("Low", "High"):
    tab[t] = (load(base / f"{t}-overcast"), load(n / f"vqa-{tag}" / f"{t}-overcast"))
for c in cams:
    cells = []
    for t in ("Low", "High"):
        a, b = tab[t][0].get(c), tab[t][1].get(c)
        cells.append(f"{a[0] if a else '–'} → {b[0]} | {a[1] if a else '–'} → {b[1]}")
    rows.append(f"| `{c}` | {cells[0]} | {cells[1]} |")
budget = f"""## Budżet (kamery kontrolne kafla, `stats.txt` visual-qa, overcast 1920×1080; A = ADR 0206 r4, B = 0211 {tag})
Szacunek edytora przed SRP batching (`drawsEst`, `trisK` w tys.); telefon nie mierzony (zakaz adb dla agentów).

| kamera | Low: draws A → B / tris A → B | High: draws A → B / tris A → B |
|---|---|---|
""" + "\n".join(rows) + """

Kamery poza wykopem (`route-s1427`, `tertiary-…`) bez zmian. Przy tunelu +0…10 draws i +33…35 tys. trójkątów (płyta, ściany
oporowe ~450 m/stronę z tylną ścianą, oczepy, balustrady, pokrywa gruntu). Hipotezy `docs/06` §6: trójkąty w normie
(Low ≤ 400–600 tys., High ≤ 1,5–2 mln); `drawsEst` Low przy tunelu 270–420 wobec hipotezy ≤ 300–400 — kamery trasy były
na tej granicy już w A (378–395). Region C: brak dróg `tunnel` → `plan` = None, `build` = `({}, None)`,
`build_chunks(low_cut=None)` to ścieżka sprzed zmiany — +0 trójkątów z konstrukcji (test
`test_regions_without_tunnel_roads_are_untouched`); C na gałęzi nie był przebudowywany ani renderowany (nie mierzono).
"""


def tail(path, k=1):
    p = Path(path)
    return " ".join(p.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-k:]) if p.exists() else "BRAK"


em = tail(n / f"editmode-{tag}.log")
em = re.sub(r" -> .*", "", em)
sweep = (n / f"tunnel_sweep-{tag}.txt").read_text(encoding="utf-8", errors="replace").splitlines()
sweep = [x for x in sweep if x.startswith(("samples", "min horizontal"))]
route = tail(n / f"route_sweep-{tag}.txt")
pyt = tail(n / f"pytest-{tag}.log")
log = (n / f"build_world-{tag}.log").read_text(encoding="utf-8", errors="replace")
m = re.search(r"'inside': (\{[^}]*\})", log)
inside = m[1] if m else "BRAK"
valid = f"""## Walidacja ({tag}, po scaleniu origin/main 7f830369c)
- Generator: `stats.tunnel.inside` = `{inside}`; `artifacts/tunnel-0211/dev_qa.py` (siatka 1 m / 2 m / 4 m, obie
  przekątne): teren w wykopie > 0,6 m nad dnem = 0, pokrywa w wykopie poza F / pod stropem = 0.
- `tunnel_sweep.py` (kolizja z GLB): {'; '.join(sweep)}.
- `route_sweep.py`: {route}.
- EditMode: {em}. pytest `tests/gis`: {pyt}.
- Rendery `artifacts/tunnel-0211/vqa-{tag}/{{Low,High}}-overcast/` (portale: `underpass-eb/wb-szymanskiego`, wnętrze:
  `tunnel-eb/wb-inside`, wykop: `cut-wall-oblique-sw`, wyspa na płycie: `rondo-szymanskiego-island-nw`).
- Referencje (Mapillary CC BY-SA 4.0, `Data/raw/mapillary/bialystok-kleeberga/`, arkusze
  `artifacts/tunnel-0211/refs/sheet_*.jpg`): 111496044347413 i 2106529699503974 (picturehoover, 2020-06-27),
  1142430022898855 (gpsmapper, 2019-08-25), 2250499485084897 (szurek, 2017-08-10); ortofoto 2024
  `artifacts/tunnel-0211/ortho/rondo_240.jpg`. Zgodne: płyta nad całym rondem, pionowe ściany wykopu z oczepem i
  balustradą, portal z balustradą nad jezdniami, brak roślinności pod płytą, opaska przy ścianie (r5: bruk zamiast
  trawy/żwiru pod płytą i od strony ścian). Różnice — patrz „Otwarte”.
"""
opened = """## Otwarte
- visual-critic nie uruchomiony (subagent nie tworzy subagentów) — do zlecenia przez lidera na `artifacts/tunnel-0211/vqa-*/`.
- Wg zdjęć (wyżej): ściany to gładki beton kremowy z pionowymi dylatacjami i pilastrami oraz zielonym pasem oczepu —
  u nas prefabrykaty `ramp_wall_panels` (szare, układ mijany), WORKING_VALUE; potrzebny osobny materiał/tekstura.
- Wg zdjęć między jezdniami jest powierzchnia wyłączona z ruchu (malowana) i brak ściany środkowej przy portalach —
  u nas pas zieleni z krawężnikami (przekrój z OSM) i ściana środkowa (WORKING_VALUE); do poprawy przez override przekroju.
- Wg zdjęć przy ścianie biegnie opaska z kostki z odwodnieniem liniowym i krawężnikiem — u nas przekrój pobocza
  (rów 0,3 m) wybrukowany; poza odcinkiem pobocza gruntowego (ok. 40 m przed/za portalem) zostaje krawężnik + pas trawy.
- Brak opraw oświetlenia w tunelu (na zdjęciach rząd opraw sodowych pod stropem przy ścianach) i znaków w tunelu.
- `streetscape_qa.json` nadal wymienia przebieg bariery `…:L:structure` (8 m) w tunelu — geometria i kolizja są usuwane
  w `tunnels._dress_inside`; reguła `furniture.guardrails` nie zna tuneli.
- LOD2/3 terenu (300–700 m): pas 4,5 m za ścianami na dnie — z daleka cienka linia (1–2 px).
"""
a = s.index("## Budżet")
s = s[:a] + budget + "\n" + valid + "\n" + opened
dec = """7. **Wnętrze** (r5, `_dress_inside`): boczne pasy jezdni tunelowych (pobocze gruntowe: żwir + trawa z rowem) pod płytą
   oraz od strony ścian w wykopie stają się opaską brukowaną (`sidewalk_paving`, kolizja `collision_paving`; kształt
   przekroju bez zmian); bariery z reguł `furniture.guardrails` na jezdni tunelowej (reguła „obok obiektu” zostawiała
   8 m bariery z dwoma zakończeniami między ścianami tunelu) są pod płytą usuwane razem z kolizją.
"""
if "7. **Wnętrze**" not in s:
    k = s.index("\n## Budżet")
    s = s[:k].rstrip("\n") + "\n" + dec + s[k:]
adr.write_text(s, encoding="utf-8", newline="\n")
print(budget)
print(valid)
