# STATUS klattow-r3-s24 (runda 3: Dom Klattow + lamus, ADR 0305)

- 09:10 Worktree z origin/main (8ad119ad9), prywatna kopia derived. Baseline (import knyszyn + render 5 kamer High clear)
  w tle: `artifacts/klattow-r3-s24/before.status` (pierwsza proba padla na braku SM_CabInterior_LOD0.fbx - skopiowany z main).
- 10:00 Lamus przepisany (`streetscape/knyszyn_lamus_0305.py`): gont jako geometria schodkowa (29 rzedow x 4 polacie, stopien
  3,5 cm, rzad 0,214 m), zalamanie polaci 27 st / 51 st, okap 0,9 m, kalenica 6,8 m, wole oko, podcien 2,1 m na 6 slupach
  z mieczami po obu stronach, oczep + konce belek + platew, podest deskowy z podwalina 0,25 m przed slupy, stopien.
  Test na sucho: LOD0 861 tris, LOD1 86. Podglad Blender: `artifacts/klattow-r3-s24/preview-lamus-*.png`.
  Materialy: `wood_planks_weathered` (nowy), `log_wall_raw` szarobrazowy, zestawy `fieldstone` i `wood_shingles` przepisane
  (kamien: gladka kopula bez ostrza, zaprawa ciemniejsza od sredniego kamienia; gont: 7 rzedow na kafel 1,5 m).
  Zmierzone: chodnik Koscielnej z reguly 2,0 m, os 6,06 m od sciany, kraweznik 2,75 m -> ganek 1,31 m za kraweznikiem;
  ortofoto + zdjecie 01: chodnik ~1,1 m. Slupa energetycznego nie ma w danych (BDOT/OSM) - nie dodany.
  NASTEPNY KROK: nadpisanie `sidewalk_w_left` (roads/network.py + overrides.yaml), `plot_fence.tint` (plots.py), krzew + pnacze
  w `knyszyn_dom_klattow_0305.py`, testy; potem `pwsh artifacts/klattow-r3-s24/run-round.ps1 -Tag r1 -World` (w tle).
- 10:12 Kod rundy 3 gotowy (commit cc78b3b84), pytest test_dom_klattow_0305: 27 passed. Baseline renderu z kopii derived niemozliwy
  (GLB z main nowsze niz manifest galezi: brak materialu plaster_peach__far_ribbon) - 'przed' dla kamer = runda 2 z ADR, dla kafla = manifest z gita.
  Runda r1 (mats + build_world + import + render) czeka w kolejce slotu heavy: `artifacts/klattow-r3-s24/r1.status`.
  NASTEPNY KROK: po `exit=0` w r1.status: `bash artifacts/klattow-r3-s24/sbs.sh r1` i obejrzec `artifacts/klattow-r3-s24/sbs/*-r1.jpg`
- 11:15 r1: mats 6 s, build_world knyszyn 20 min (exit 0): dom LOD0 4404 / LOD1 99 tris, lamus 861 / 86, ogrod 78 tris; plot 1,53 m od sciany przy
  chodniku 1,10 m (os drogi nierownolegla do sciany) -> nadpisanie 0,70 m + ROAD_CLEAR_M 0,05 (wejdzie w r2). Import padal na bledzie z main:
  brak materialu plaster_peach__far_ribbon w tabeli (kafel 1_4) - dopisany do materials.py i recznie do manifestu r1. Import + render r1 w tle.
  NASTEPNY KROK: po `exit=0` w artifacts/klattow-r3-s24/r1.status: `bash artifacts/klattow-r3-s24/sbs.sh r1`; potem `pwsh artifacts/klattow-r3-s24/run-round.ps1 -Tag r2 -World`
- 11:25 r1 obejrzana (sbs/*-r1.jpg): gont schodkowy i zalamanie czytelne, podmurowka naturalna, plot dzialki brazowy (szare sztachety zielonkawe),
  krzew / drzewko / pnacze sa. Kamery r1: look-dom-klattow 627 draws / 1 486 884 tris, -street 556 / 1 468 778, -gable-e 241 / 957 477,
  -yard 99 / 377 229, look-lamus 459 / 1 121 469. Poprawki do r2: chodnik 0,70 m, tint plotu [0.9,1.4,1.1], zrab szarszy, wole oko wieksze,
  podwalina podestu 0,28 m, krzew r 1,2 m, nowa kamera look_lamus_plebanski_close (kadr zdjecia 02, 1,7 m).
  NASTEPNY KROK: `pwsh artifacts/klattow-r3-s24/run-round.ps1 -Tag r2 -World -Cameras look_dom_klattow,look_dom_klattow_street,look_dom_klattow_yard,look_dom_klattow_gable_e,look_lamus_plebanski,look_lamus_plebanski_close`; po exit=0: `bash artifacts/klattow-r3-s24/sbs.sh r2`
