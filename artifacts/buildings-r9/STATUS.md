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
