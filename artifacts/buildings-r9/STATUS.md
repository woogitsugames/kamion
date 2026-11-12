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
