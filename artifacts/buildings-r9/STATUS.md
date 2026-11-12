# buildings-r9 — ADR 0132 zabudowa r9 (gałąź `buildings-r9`, z main f8b85fa2)

## krok 1 — środowisko + kod r1 (świat r1 w kolejce slotu heavy, NIC jeszcze nie zrenderowane w Unity)
- Worktree `.claude/worktrees/buildings-r9`, kopie `Data/raw/{derived,cc0}`, `art-source/world/{cc0/_raw,megascans}`, `_Generated`, `Library`;
  junctiony gugik/osm/refs/mapillary/fab. `fir_tree_01` obecny (atlas z fotografii gałązek).
- UWAGA baza: import skopiowany z main pochodzi sprzed scalenia 0124 (regen „e” lidera w toku) — `base/Low-overcast` to NIE jest
  main z 0124. Bazę do budżetu zrobić NA KOŃCU: robocopy `game/Assets/_Generated` z main po commicie „regenerate … e” →
  `pwsh artifacts/buildings-r9/base.ps1` (render bez importu) → `python artifacts/buildings-r9/budget2.py base/Low-overcast rN/Low-overcast`.
- Diagnoza P1-c: „wiata” z recenzji to kamera `r16_door_3` stojąca WEWNĄTRZ domu (ściany back-face culled: daszek nad drzwiami,
  ościeża, okap, grunt pod budynkiem). W generatorze nie ma wiaty na działkach. Poprawka: kamery nie stają w obrysie budynku.
- Kod (niezrenderowany w silniku; podgląd brył w Blenderze `kitprev/sheet_{a,b}.jpg`):
  * `plot_canopy.py` + `Data/Regions/<id>/plot_canopy.json`: korony z ortofoto GUGiK 0,25 m (3500 koron ≤ 45 m od domów, 2070 drzew,
    426 iglastych, pokrycie 19,8 %); `plots.build`: korona r ≥ 2,3 m → instancja `tree_{birch,linden,maple,pine,alder}` (istniejące
    prototypy, 0 nowych materiałów), 1,25–2,3 m → drzewko w kicie (rdzeń + karty na powierzchni, ~65 tris), < 1,25 m → krzew;
    iglaste → świerk / tuja kitu; pas przed płotem ≥ 3 m od jezdni; krzewy zarastające płot (≤ 1/3 przęseł).
  * żywopłot: przekrój zaokrąglony, stacje co 1,28 m (wysokość ±5–11 cm, grubość ±12 %), okluzja w długości normalnej
    (shader `WorldPlotKit`), liście 1:1 (dwa pasma v), pędy nad linią wierzchu.
  * skrzynka na listy na słupku 12 cm w kolorze innym niż rama; wolny odcinek płotu bocznego < 3,2 m usuwany; podjazd „dwa pasy”
    na starych działkach bez garażu; tint wieku old 0,80 → 0,72, przechył 3° → 4,5°; ramki otworów LOD1 domów.
  * testy `tests/gis/test_buildings_r9.py` (7), poprawiony `test_buildings_r8.py`.
- NASTĘPNY KROK: `Get-Content artifacts/buildings-r9/r1/round.log` (czekać na `ROUND DONE`; jeśli proces zginął:
  `pwsh artifacts/buildings-r9/round.ps1 -Round r1`) → `cat artifacts/buildings-r9/r1/plan_dry.txt` → obejrzeć
  `r1/extra_hc/960/r1[567]_*.jpg`, `r1/extra_low/960/*.jpg` → `bash artifacts/buildings-r9/pairs.sh r1` (SUB=extra_hc OUT=pairs_r1).

## krok 2 — swiat r1 zbudowany (14:31), import + rendery w toku
- `build_world` r1: exit 0, 554 s; High 4071 submeshy / 14,293 mln tris, Low 3053 / 4,646 mln (r2c z 0124: 4073 / 14,184; 3054 / 4,532).
- Dzialki 99: drzewa-instancje 119 na 60 dzialkach (brzoza 35, lipa 30, klon 26, sosna 17, olcha 11; h 11-19 m), drzewka kitu 192,
  swierki 53, tuje 521, krzewy 213 + zarastanie plotow, zywoplot 477 m; kit 93 941 tris (0124: 52 022); odcinki plotu usuniete 4;
  podjazdy "dwa pasy" 11; bramy 43 / obnizenia 43; plot nie przecina stref drzwi (0).
- Testy czastkowe: `test_buildings_r8/r9` 12 passed (pelny pytest gis, fidelity, EditMode - po rundzie wizualnej).
- NASTEPNY KROK: `Get-Content artifacts/buildings-r9/r1/round.log` (czekac na `ROUND DONE`; jesli zginelo:
  `pwsh artifacts/buildings-r9/round.ps1 -Round r1 -SkipWorld`) -> `grep -n "error CS\|Shader error" artifacts/buildings-r9/r1/import.log`
  -> obejrzec `r1/extra_hc/960/*.jpg`.

## krok 3 — r1 obejrzane, r2 w toku (16:28)
- r1: import 1598 s (maszyna obciazona), brak `Shader error` / `error CS`; rendery `r1/Low-overcast`, `r1/extra_hc`, `r1/extra_low`,
  arkusze `r1/sheet_{street,fix,garden,low}.jpg`. Widac: drzewa nad dachami, krzewy przy plotach, zywoplot zaokraglony, dwa pasy,
  skrzynka na slupku. Zle: r1 vs r2c(0124) najgorsza kamera Low +18 draw (`r10_shed_2`, instancje: 15 prototypow drzew),
  ramki LOD1 7 cm niewidoczne, panel przy bramie `r16_drive_3` nadal (to sciana boczna + szczelina 0,3 m przy slupku bramy).
- r2 (kod 7ac5589d): brama dosuwana do naroznika (slupek bramy = slupek narozny), 4 gatunki x 1 wariant instancji, ramka LOD1 12 cm.
- Baza = import main z 14:03 (main z 0124, integracja e) skopiowany 16:28 do `_Generated` -> `base/` (Low + extra_low + 8 kamer hc).
- NASTEPNY KROK: `Get-Content artifacts/buildings-r9/r2/round.log` (czekac na `CHAIN DONE`; jesli zginelo po `build_world exit 0`:
  `pwsh artifacts/buildings-r9/round.ps1 -Round r2 -SkipWorld`, potem pytest/fidelity/EditMode jak w `r2_chain.ps1`) ->
  `python artifacts/buildings-r9/budget2.py artifacts/buildings-r9/base/Low-overcast artifacts/buildings-r9/r2/Low-overcast`

## krok 4 — stop na limit sesji (ok. 16:40); w tle dziala lancuch r2
- Budzet r1 vs main (base = import main 14:03, Low overcast, 67 kamer): MR +8 (najg. +1; +1 submesh `chunk_2_5 buildings_lod1|plaster_white`
  z ramek LOD1 - poprawione w 848ff8945), instancjonowane +52 (najg. `r10_shed_2` +19, `r10_house_2` +11), tris siatek +322 k
  (najg. +34 k), tris instancji +10 k. Region Low: 3053 submeshy / 4,646 mln (main 3052 / 4,572).
- W TLE (nie zabijac): `artifacts/buildings-r9/r2_chain.ps1 -Round r2` - czeka w kolejce slotu heavy na `build_world` r2
  (kod 848ff8945: brama do naroznika, 4 gatunki x 1 wariant drzew, ramka LOD1 12 cm), potem import + rendery + fidelity +
  pelny pytest gis + EditMode. Logi: `artifacts/buildings-r9/r2/round.log`, `r2.world.out`, `r2.round.out`, `r2/plan_dry.txt`,
  `r2/{build_world,import,fidelity,pytest_gis,editmode}.log`.
- Otwarte: obejrzec r2, budzet r2 vs base, pary render | Mapillary (`pairs.sh`), ADR 0132 sekcja Liczby + samokrytyka,
  LICENSES (bez nowych zasobow; ortofoto GUGiK jako zrodlo pozycji), kopia dowodow do main `artifacts/buildings-r9/`, visual-critic.
- NASTEPNY KROK: `Get-Content artifacts/buildings-r9/r2/round.log` (czekac na `CHAIN DONE`; jesli lancuch zginal:
  przed `build_world exit 0` -> `pwsh artifacts/buildings-r9/r2_chain.ps1 -Round r2` (UWAGA: nadpisze `_Generated` kopia z main i
  powtorzy baze; aby pominac baze uzyj `pwsh artifacts/buildings-r9/round.ps1 -Round r2`), po nim ->
  `pwsh artifacts/buildings-r9/round.ps1 -Round r2 -SkipWorld`) ->
  `python artifacts/buildings-r9/budget2.py artifacts/buildings-r9/base/Low-overcast artifacts/buildings-r9/r2/Low-overcast`

## krok 5 — sesja 13 (17:25): lancuch r2 zyje (kolejka heavy), kit Low/Medium (e553c32a2)
- Lancuch `r2_chain.ps1` z s12 zyje (PID pwsh 16:28), `r2.world.out`: "queue ahead=1"; build_world r2 wezmie JUZ kod e553c32a2.
- Polecenie lidera: zielen nie moze pogorszyc Low (A16 Low FAIL GPU p95 35,2-35,5 ms; drzewa +2,53 ms). Zrobione:
  `Kit.low` (True / False = tylko High / "only" = tylko Low) + warstwa `plots_low` -> w `chunk_*.low.glb` jako wezel `plots`
  (High bez zmian). Low: ploty, bramy, zywoplot, swierki, kosze 1:1; tuje w rzedach `thuja_lite` 14 tris (39), tuje pojedyncze
  4 tris, drzewka `fruit_tree_lite` 10 tris (65); krzewy / zarastanie plotow / byliny tylko High. Kit r1/r2 = 94 170 tris
  (0124: 52 406); rozbicie: plot 20,6k, bramy 11,9k, tuje rzedy 17,2k, drzewka 12,5k, zywoplot 9,3k, krzewy 17,0k, byliny 1,2k.
- Naprawa: brama dosuwana do naroznika (r2) znikala, gdy front sasiada jest wspolliniowy (`_Near.parallel`) -> `snap()` w `layout`
  (test r7 3 failed -> 26 passed r7+r8+r9).
- Instancje drzew ogrodowych (117) sa wspolne dla Low i High (jeden `WorldInstanceSet`) - filtr per tier wymaga zmiany
  `World/Import/InstanceImporter` + `World/Runtime/WorldInstances` (poza wlasnoscia) -> zmierzyc na r2 i zglosic liderowi.
- NASTEPNY KROK: `Get-Content artifacts/buildings-r9/r2/round.log` (po `build_world exit 0`: `grep tris_low r2/build_world.log`,
  czekac na `ROUND DONE`) -> `python artifacts/buildings-r9/budget2.py artifacts/buildings-r9/base/Low-overcast artifacts/buildings-r9/r2/Low-overcast`
  -> `git merge main` (generated --ours) -> `pwsh artifacts/buildings-r9/round.ps1 -Round r3` + pytest gis + fidelity + EditMode.

## krok 6 — r2 zmierzone i obejrzane, merge main, r3 w toku (18:02)
- r2 (kod e553c32a2, przed merge): build_world exit 0 792 s; region Low 3052 submeshy / 4 603 634 tris (main 3052 / 4 572 k);
  `plots` Low 51 508 (main 52 406), High 94 172; `buildings_lod1` +31 432 (ramki okien). Import 576 s, 0 bledow.
- Budzet Low r2 vs base (67 kamer, `r2/budget_low.txt`): MR draws +0, shadow -1, instancjonowane +23 (najg. `r10_shed_2` +14,
  `r10_house_2` +10; kamery trasy/kabiny -2..+3), instancje +81, tris siatek +258 k (najg. +29 k - ramki LOD1), tris instancji +10 k.
- Decyzja: ramki LOD1 WYLACZONE (`buildings_mesh.LOD1_HOUSE_FRAME_M = 0.0`, 0.12 wlacza) -> Low tris siatek ~ base w r3.
- Obejrzane: `r2/sheet_hc_{a,b}.jpg`, `r2/sheet_low_a.jpg` vs `base/sheet_low_a.jpg`, `pairs_r2/low_*.jpg`.
- `git merge main` b2f86cb7c (konflikty: 2x generated json + street_props.glb -> ours). Lancuch r2 zabity po ROUND DONE.
- W TLE: `r3_chain.ps1 -Round r3` (pwsh PID 60960; log `r3/round.log`, `r3.chain.out`): build_all, build_world, export-route,
  fidelity, pytest gis (slot heavy wziety 18:02), potem import + Low overcast + 8 kamer hc + EditMode; koniec = `CHAIN DONE`.
- NASTEPNY KROK: `Get-Content artifacts/buildings-r9/r3/round.log` (czekac na `CHAIN DONE`; jesli zginelo po `pytest(gis) exit`:
  `pwsh artifacts/buildings-r9/round.ps1 -Round r3 -SkipWorld; pwsh artifacts/buildings-r9/editmode.ps1 -Round r3`) ->
  `python artifacts/buildings-r9/budget2.py artifacts/buildings-r9/base/Low-overcast artifacts/buildings-r9/r3/Low-overcast`
  -> commit generated -> ADR Liczby -> kopia `artifacts/buildings-r9` do main.

## krok 7 — r3 zakonczone i zmierzone (19:19); 2 testy budzetu HIGH czerwone -> decyzja lidera
- Lancuch r3: `CHAIN DONE`. build_world 0 (High 4070 / 14 272 032, Low 3050 / 4 582 476), fidelity 0, import 776 s bez bledow,
  EditMode 407/407. Pytest gis 819 passed / 3 failed: determinizm (moj kod ramek LOD1, `set` -> `sorted`, POPRAWIONE, zielony);
  estymata kadru HIGH > 2,0 M: `stretch_04` 2 027 946 (main 1 986 709), `route_onramp_andersa_above` 2 009 629 (main 1 981 768) -
  kit posesji High +41,8 k przy zapasie main 13 k. Low bez zmian. Warianty A/B/C w ADR 0132 "Otwarte: budzet High".
- Budzet Low r3 vs baza (`r3/budget_low.txt`): MR +11, cienie -25, instancjonowane +186, tris siatek +60 k, tris instancji +165 k -
  z tego tresc main z merge (r3 - r2): instancjonowane +163, tris inst. +155 k. Wklad 0132 (r2 vs baza): MR +0, inst. +23, instancje +81.
- Pary / arkusze r3: `pairs_r3/sheet_base_hc.jpg`, `sheet_base_low.jpg`, `sheet_ref.jpg` (+ 29 par). ADR: Liczby r3, koszt drzew
  ogrodowych + propozycja filtra per tier, otwarty budzet High.
- NASTEPNY KROK (po decyzji lidera): wariant A -> nic w galezi (lider zmienia prog / estymator), potem
  `uv run --project tools/worldgen python -m pytest tests/gis/test_hero_bridge.py tests/gis/test_world_v31.py -q -p no:cacheprovider`;
  wariant B -> edycja `tools/worldgen/streetscape/plots.py` (thuja/bush/fruit_tree + front <= 12 m), potem
  `pwsh artifacts/buildings-r9/r3_chain.ps1 -Round r4`.

## krok 8 — decyzja lidera B: r4 w toku (19:29)
- `git merge main` 6d511d49c (generated ours). Kod r4 (7d675d793, `artifacts/buildings-r9/p_r4.py`): pelne bryly roslin tylko <= 12 m
  od frontu dzialki (`NEAR_FRONT_M`), dalej wersje lite (wspolne z Low; krzew daleki 2 karty tylko High); rdzenie 1 pas; drzewko ~48;
  tuja w rzedzie 16; zywoplot stacje 1,92 m; `"tier": "high"` w rekordach drzew ogrodowych (importer ignoruje nieznane pola).
- Suchy przebieg na danych (`r4/plan_dry.txt`): kit High 59 867 (r3 94 172; main 52 406), Low 48 884 (r3 51 508).
- W TLE: `r4_chain.ps1 -Round r4` (pwsh PID 59260; logi `r4/round.log`, `base2/round.log`, `r4.chain.out`): base2 = TRESC main zbudowana
  i zaimportowana w tym worktree (checkout sciezek z main, potem przywrocenie HEAD) -> rendery Low; potem r4: build_all, build_world,
  export-route, fidelity, import + rendery, PELNY pytest gis, EditMode; koniec = `CHAIN DONE`.
- NASTEPNY KROK: `Get-Content artifacts/buildings-r9/r4/round.log`; jesli lancuch zginal w base2: `git checkout HEAD -- tools/worldgen art-source/world Data/Regions Data/SourceManifests scripts/export-route.py`,
  potem `pwsh artifacts/buildings-r9/r4_chain.ps1 -Round r4 -SkipBase`. Po `CHAIN DONE`:
  `python artifacts/buildings-r9/budget2.py artifacts/buildings-r9/base2/Low-overcast artifacts/buildings-r9/r4/Low-overcast`, zapas testow High
  (stretch_04, route_onramp_andersa_above w `generated/streetscape_qa.json`), pary r4, ADR, commit, robocopy do main.
- [2026-11-12 19:57] WIP na polecenie lidera (limit 79 %): lancuch r4 zyje (PID 59260), etap base2. UWAGA dla przejmujacego: dopoki w
  `r4/round.log` nie ma `BASE2 DONE`, indeks/worktree ma chwilowo sciezki z main - commitowac TYLKO przez
  `git commit --only <plik>`, nigdy `git add -A` / `git commit -a`.

## krok 9 — sesja 15 (21:20): r4 zbudowane, zaimportowane, budzet zmierzony
- Lancuch r4 (PID 59260): build_world exit 0 616 s, region High 4071 / 14 239 334, Low 3051 / 4 580 678; kit High 59 867 / Low 48 884;
  fidelity 0; import 601 s, 0 `error CS` / `Shader error`. Estymata kadru HIGH: `stretch_04` 1 995 296 (base2 1 987 612, r3 2 027 946),
  `route_onramp_andersa_above` 1 986 990 (base2 1 982 699) - oba < 2 000 000. Low 947 654 / 852 975 (base2 947 656 / 852 977).
- Budzet Low r4 vs base2 (tresc main zbudowana tutaj; 67 kamer, `r4/budget_low.txt`): MR +0, cienie -1, instancjonowane +26
  (`r10_shed_2` +14, `r10_house_2` +10, reszta <= +3), instancje +126, tris siatek -9 k, tris instancji +12 k.
- W TLE nadal lancuch: pytest gis -> 8 kamer hc + kamery Low -> EditMode -> `CHAIN DONE`.
- NASTEPNY KROK: `Get-Content artifacts/buildings-r9/r4/round.log` (po `CHAIN DONE`: pary r4 vs base2, ADR Liczby r4, `git merge origin/main`, robocopy do main).
