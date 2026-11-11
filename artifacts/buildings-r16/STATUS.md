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

## krok 4 — High zmierzony
- High overcast, 67 kamer, r1 vs baza (`budget_high_r1.txt`): MeshRenderer −49, instancje −7, razem **−56**, najgorsza **+3**
  (`trailer-34`; `cab-mirrors-right` +2, `g3b-eye-s1482` +2 — węzeł `wires`), cienie MR **−123**, trójkąty siatek **−46 k**.
  `cab-mirror-front` 954 → 954 draws, 1264 → 1265 k tris; `cab-mirrors-right` 827 → 829, 1138 → 1139 k. UWAGA: te dwie kamery
  to widok GŁÓWNY z kabiny (stats.txt liczy kamerę główną), nie kamery RT lusterek — koszt RT lusterek nadal niezmierzony
  (MirrorCostProfiler z `PlotViewCull.Enabled` on/off — do zrobienia).
- NASTĘPNY KROK: po `extra done` w `r1/round.log` obejrzeć `r1/extra/960/r16_*.jpg`.

## RAPORT KOŃCOWY (docs/09 §4) — runda r1, jedna iteracja wizualna, przerwana limitem sesji
ZADANIE: ADR 0124 — zabudowa r8. Gałąź `buildings-r8` (z main `3540bbdf`), ostatni sha: `git log -1`.
ZROBIONE (zmierzone):
1. Zjazdy: brama tylko z dojazdem do krawężnika, który da się obniżyć — 43 bramy, **43/43 obniżone** (r7: 28/48), 11 przesuniętych,
   5 → furtka; pas przy krawężniku jako wielokąt bez jezdni i bez kamienia krawężnika (`drop_check_r2.txt`, `r16_drive_0/1`).
2. Kolizje: 0 przęseł płotu w strefie schodów / bramy garażu; dojście do stóp schodów (`r10_house_2`: płot nie tnie garażu).
3. Rośliny / pręty: atlas v2 z gałązek CC0, tuja rdzeń + karty, świerk 3 karty, shader `Kamion/World PlotKit` (jedna karta płotu,
   normalne roślin z COLOR_0). `plot_kit` 56 964 → 52 022 tris.
4. Ulica: krawężnik 10 cm na 5 łańcuchach (1573 m, mediana zmierzona 10,5 cm), przewody 15 przęseł + 22 przyłącza, tint
   starzenia, przechył słupków, 462 krzewy, 15 dużych drzew, 477 m żywopłotu.
5. Budżet r1 vs r7 (67 kamer, overcast): Low razem **−12**, najgorsza **+3**; High razem **−56**, najgorsza **+3**, cienie −123,
   trójkąty −46 k (`budget_low_r1.txt`, `budget_high_r1.txt`). Instancje osobno: Low −6, High −7.
NIEZROBIONE / NIEZWERYFIKOWANE (uczciwie):
- klin trawy między podjazdem a pasem przy krawężniku na zjazdach skośnych (`r16_kerb_0`, `pairs/ref_brick_bars_P24.jpg`) — P1-r8-b częściowo;
- żywopłot z za dużymi liśćmi; rdzeń tui z rozciągniętą teksturą; jabłonie nadal jak karty; świerki / duże drzewa / `extra_low` nieobejrzane;
- zacieki: shader zmieniony, **pomiar 5 m / 20 m nie wykonany**; lusterka: `PlotViewCull` w scenie, **MirrorCostProfiler nie uruchomiony**
  (`cab-mirror-*` w stats.txt to widok główny, nie RT lusterek);
- **pełny `pytest tests/gis`, `fidelity/run.py`, EditMode nie uruchomione** (tylko `test_buildings_r5..r8`: 36 passed);
- bez `visual-critic`, bez telefonu; kamery `r16_door_*`, `r16_garden_*` źle ustawione; siatka na Low blada (P2-r8-a), mur skosem (P2-r8-d).
PLIKI: `tools/worldgen/streetscape/{plots,plot_kit,materials,stage}.py`, `tools/worldgen/roads/build_world.py`,
  `game/Assets/_Project/Environment/Shaders/{WorldPlotKit,WorldPBR}.shader`, `World/Runtime/PlotViewCull.cs`,
  `World/Import/{RegionImporter,WorldSceneBuilder,WorldSkyBake}.cs`, `Editor/VisualQA/SceneStats.cs`,
  `tests/gis/test_buildings_r{7,8}.py`, `docs/adr/0124-buildings-r8.md`, `docs/LICENSES.md`, `art-source/world/textures/plot_kit.png`.
DOWODY: `base/`, `r1/{Low-overcast,High-overcast,extra,extra_low}` (+ `960/`), `pairs/` (22), `plan_r1.png/.txt`, `drop_check_r2.txt`.
NASTĘPNY KROK (kolejna sesja, slot heavy / unity):
  `pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner claude-buildings-r8; uv run --project tools/worldgen python -m pytest tests/gis -q; uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c` (sprawdzić właściwe wywołanie fidelity)
  → `pwsh artifacts/buildings-r16/editmode.ps1` → `pwsh artifacts/buildings-r16/extra.ps1 -Round r1 -Sub sill_off -Runoff off -Only r15_sill_5m,r15_sill_20m`
  → `python artifacts/buildings-r16/sill_marks.py artifacts/buildings-r16/r1` → poprawki z listy „NIEZROBIONE” → `world.ps1 -Round r2` → `full_round.ps1 -Round r2`.
