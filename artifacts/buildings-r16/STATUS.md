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

## krok 2 — świat r1 zbudowany, import r1 w toku (stan na przerwanie sesji)
- Commit kodu r1 + testy `tests/gis/test_buildings_r8.py` (6/6), `test_buildings_r5..r7` zielone (pełny `pytest tests/gis` NIE uruchomiony).
- `build_world` r1: exit 0, 526 s; region High 4073 submeshy / 14,167 mln tris (baza 4085 / 14,21), Low 3054 / 4,515 mln
  (baza 3066 / 4,609); `plot_kit` 52 022 tris (r7 56 964); przewody: 6 łańcuchów, 15 przęseł 469 m, 22 przyłącza, 370 tris.
- Działki: 99, bramy 43 (wszystkie z dojazdem i obniżeniem: 43/43; 11 przesuniętych, 5 → sama furtka), płot nie przecina
  żadnej strefy schodów / bramy garażu (0). `drop_check_r2.txt`: 43/43 krawężniki obniżone o 10 cm do 3 cm (pomiar
  maks. z krawężnika − mediana asfaltu w 1,2 m: 3,0–8,0 cm, reszta to spadek poprzeczny); krawężnik ulic domów mediana 10,5 cm.
- Baza `base/` kompletna: Low/High overcast + extra + extra_low (stats.txt do budżetu).
- NIEZROBIONE / NIEZWERYFIKOWANE: żaden render r1 jeszcze nie obejrzany (import r1 trwa: shader `WorldPlotKit`, `PlotViewCull`
  i zmiana `WorldPBR` nieskompilowane w Unity!), budżet draws r1 vs baza, pomiar zacieków, lusterka (MirrorCostProfiler),
  EditMode, fidelity/run.py (dotknięty `roads/build_world.py`), ADR 0124, LICENSES (fir_tree_01 CC0 w `plot_kit`), pary referencji.
- NASTĘPNY KROK (jeśli import padł lub sesja zginęła):
  `pwsh artifacts/buildings-r16/full_round.ps1 -Round r1` (touch PNG w art-source/world/materials przed) →
  `grep -n "error CS\|Shader error" artifacts/buildings-r16/r1/import.log` →
  `python artifacts/buildings-r16/budget2.py artifacts/buildings-r16/base/Low-overcast artifacts/buildings-r16/r1/Low-overcast` (i High) →
  obejrzeć `r1/extra/960/r16_*.jpg`, `r15_front_*.jpg` → poprawki → ADR `docs/adr/0124-buildings-r8.md`.

## krok 3 — import r1 OK, Low zmierzony
- Import r1 exit 0 (568 s), brak błędów C# / shaderów; `Kamion/World PlotKit` renderuje (obejrzane `r1/Low-overcast/r10_house_2`:
  zjazd bez kostki na jezdni, krawężnik obniżony, płot nie przecina bramy garażu).
- Budżet Low overcast, 67 kamer, r1 vs baza (= r7 / main), `budget_low_r1.txt`: MeshRenderer −6, instancje −6, razem **−12**,
  najgorsza kamera **+3** (`r10_block_3`, `r10_block_4`: nowy węzeł `wires` w chunkach bez przewodów), `r10_house_1/2` **−4**
  (r7 względem świata bez działek: +11 → teraz +7); cienie MR −32; trójkąty siatek −8 k.
- W toku: `full_round.ps1 -Round r1` (High overcast, extra High, extra Low).
- NASTĘPNY KROK: `python artifacts/buildings-r16/budget2.py artifacts/buildings-r16/base/High-overcast artifacts/buildings-r16/r1/High-overcast`
  → obejrzeć `artifacts/buildings-r16/r1/extra/960/r16_*.jpg` → ADR 0124.
