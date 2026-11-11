# buildings-r16 — ADR 0124 zabudowa r8 (gałąź `buildings-r8`, z main 3540bbdf)

## krok 1 — baza i kod r1 (WIP)
- Baza „przed” (= main): `base/` — build_world 480 s, import 801 s, Low/High overcast (stats.txt), extra High + Low.
- Kod r1 (niezrenderowany jeszcze): `plot_kit.py` atlas v2 (pary rzędów płotów po 5,12 m; karty tuj/świerków z fotografii
  gałązek CC0 Poly Haven fir_tree_01; żywopłot; duże drzewo; deski szare), `plots.py` (brama tylko z dojazdem do
  krawężnika, który da się obniżyć: 43 bramy / 43 obniżenia, 11 przesuniętych, 5 zamienionych na furtkę; strefy schodów
  i bram garażowych wycinają płot: 0 przecięć; pas kostki jako wielokąt bez jezdni i bez kamienia krawężnika;
  krawężnik 10 cm na 5 łańcuchach ulic domów, 1573 m; przewody na słupach lamp; warstwa chunka `plots`),
  shader `Kamion/World PlotKit` (jedna karta płotu, normalne roślin z COLOR_0), `PlotViewCull` (działki > 70 m poza
  lusterkami), zacieki `WorldPBR` (kształt per koniec parapetu). Sucho: plot_kit 52,0 k tris (r7: 57,0 k).
- Reguła koordynatora: ciężki Python tylko w slocie `-Pool heavy` (`world.ps1`), pełny pytest na końcu.
- NASTĘPNY KROK: `pwsh artifacts/buildings-r16/world.ps1 -Round r1` → `pwsh artifacts/buildings-r16/full_round.ps1 -Round r1`
  → `python artifacts/buildings-r16/budget2.py artifacts/buildings-r16/base/Low-overcast artifacts/buildings-r16/r1/Low-overcast`
