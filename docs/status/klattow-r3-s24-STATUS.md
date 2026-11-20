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
