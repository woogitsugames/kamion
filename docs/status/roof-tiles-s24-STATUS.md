# STATUS roof-tiles-s24 (dachówka ceramiczna + atlas płotów plot_kit, ADR 0316)

- 13:30 Worktree z main (10adb1a5a), prywatna kopia derived. Kamery QA: `look_roofs_above` (knyszyn), Tykocin
  `look_tykocin_rynek_n/_s`, `look_tykocin_roofs_above`, `look_tykocin_zlota` (nowy `control_cameras_place.authored.json`).
  Baseline w tle (build_world knyszyn + tykocin na kodzie main → import High → render High clear): `artifacts/roof-tiles-s24/before.status`.
  Nowe zestawy dachówek (esówka, stara esówka, karpiówka, zakładkowa) napisane i obejrzane w podglądzie — do czasu końca
  baseline leżą poza worktree (import baseline buduje zestawy z kodu main).
  NASTĘPNY KROK: po `exit=0` w `artifacts/roof-tiles-s24/before.status`: wgrać `sets_roof.py`, materiały, reguły dachów,
  `pwsh artifacts/roof-tiles-s24/run-round.ps1 -Tag r1 -World -Sets roof_tiles,roof_tiles_old,roof_karpiowka,roof_zakladkowa,roof_metal_tile`
- 14:10 `git merge origin/main` (a31564b90: road-widen D94) bez konfliktów. Pierwszy baseline (kod sprzed scalenia) padł na imporcie
  (brak `SM_CabInterior_LOD0.fbx` — skopiowany z main) → zarchiwizowany `artifacts/roof-tiles-s24/before-premerge/`; zestawy PBR High
  zbudowane z kodu main (972 s). Baseline na scalonym kodzie w tle: `artifacts/roof-tiles-s24/before.status`.
  Gotowe poza worktree (scratch, czekają na koniec budowy świata baseline): `sets_roof.py` (esówka 4,2 m, stara esówka, karpiówka,
  zakładkowa), łatka `plot_kit.py` (rzędy `picket_wood`, `picket_paint`, siatka neutralna + tint), łatka materiałów / reguł / `roofs.py`.
  NASTĘPNY KROK: po `world-tykocin exit=0` w before.status wgrać łatki worldgen + testy; po `exit=0` całości:
  `pwsh artifacts/roof-tiles-s24/run-round.ps1 -Tag r1 -World -Sets roof_tiles,roof_tiles_old,roof_karpiowka,roof_zakladkowa,roof_metal_tile`
- 14:35 Baseline gotowy (`artifacts/roof-tiles-s24/before/{knyszyn,tykocin}`, High clear; świat sprzed scalenia road-widen — kolejka slotu
  heavy 3/3 + 4 czekających, drugi build baseline odpuszczony; drogi w „przed” są sprzed D94, budynki / działki bez różnic).
  Kamery przed: look-dom-klattow-street 556 draws / 1 495 926 tris; look-roofs-above 542 / 1 618 590; gardens-tykocka-eye 725 / 1 538 467;
  tykocin roofs-above 309 / 914 027, zlota 332 / 1 035 051. Kod worldgen + testy wgrane i wypchnięte (c1f535291); pytest powiązanych
  plików: 144 passed (1 własny test poprawiony). Runda r1 czeka na slot heavy (`artifacts/roof-tiles-s24/run-r1.ps1` w tle:
  zestawy → build_world knyszyn + tykocin → import → render): `artifacts/roof-tiles-s24/r1.status`.
  NASTĘPNY KROK: po `exit=0` w r1.status: `bash artifacts/roof-tiles-s24/sbs.sh r1`, obejrzeć `artifacts/roof-tiles-s24/sbs/*-r1.jpg`
