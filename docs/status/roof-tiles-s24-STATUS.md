# STATUS roof-tiles-s24 (dachówka ceramiczna + atlas płotów plot_kit, ADR 0316)

- 13:30 Worktree z main (10adb1a5a), prywatna kopia derived. Kamery QA: `look_roofs_above` (knyszyn), Tykocin
  `look_tykocin_rynek_n/_s`, `look_tykocin_roofs_above`, `look_tykocin_zlota` (nowy `control_cameras_place.authored.json`).
  Baseline w tle (build_world knyszyn + tykocin na kodzie main → import High → render High clear): `artifacts/roof-tiles-s24/before.status`.
  Nowe zestawy dachówek (esówka, stara esówka, karpiówka, zakładkowa) napisane i obejrzane w podglądzie — do czasu końca
  baseline leżą poza worktree (import baseline buduje zestawy z kodu main).
  NASTĘPNY KROK: po `exit=0` w `artifacts/roof-tiles-s24/before.status`: wgrać `sets_roof.py`, materiały, reguły dachów,
  `pwsh artifacts/roof-tiles-s24/run-round.ps1 -Tag r1 -World -Sets roof_tiles,roof_tiles_old,roof_karpiowka,roof_zakladkowa,roof_metal_tile`
