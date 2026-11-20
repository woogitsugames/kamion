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
- 15:10 BLOKADA KOLEJKI: slot heavy 3/3 zajęty przez tory regen-wave-2 (A od 14:10, C od 14:08, B od 15:02 — duże kafle), r1 (build_world
  knyszyn + tykocin, ~27 min) czeka w kolejce FIFO od 14:28 (`run-r1.ps1` w tle; RAM wolne 43 GB, CPU 25 % — lider może dopuścić 4. slot:
  `$env:KAMION_HEAVY_SLOTS=4`, sam limitu nie podnoszę). W międzyczasie runda t1 „same tekstury”: 5 zestawów dachówek zbudowane
  (`build_all.py --only …`, 30 s) i import światów baseline z nowymi zestawami + render (pula unity): `artifacts/roof-tiles-s24/t1.status`
  (esówka / stara esówka w silniku; karpiówka, zakładkowa i płoty dopiero po build_world). `before.status` przemianowany na
  `before.status.hold` na czas t1 (wstrzymuje start build_world r1, który nadpisałby GLB pod importem).
  NASTĘPNY KROK: po `exit=0` w t1.status: `mv artifacts/roof-tiles-s24/before.status.hold artifacts/roof-tiles-s24/before.status`;
  `bash artifacts/roof-tiles-s24/sbs.sh t1`; obejrzeć `sbs/*-t1.jpg`
- 15:20 Rundy t1 / t2 (same tekstury, światy baseline) obejrzane: `artifacts/roof-tiles-s24/sbs/crop-klattow-roof-t1.jpg`, `-t2.jpg`,
  `crop-above-k-t1.jpg`, `crop-above-t-t1.jpg`, `crop-into-town-t1.jpg`. Szachownica znikła, widać wałki i „oczka” pod krawędziami.
  Po t1: stara esówka plamistsza (łaty zwietrzałe, 19 % ciemnych, 8 % jasnych), cień rzędu 0,70 → 0,56, kafel 2,8 → 4,2 m, macro [6, 0.16].
  (W t1 / t2 blachodachówka ma teksturę esówki — skutek importu starego świata z nową nazwą zestawu; znika po build_world.)
  r1 nadal w kolejce slotu heavy (regen-wave-2 A / B / C).
  NASTĘPNY KROK: po `exit=0` w `artifacts/roof-tiles-s24/r1.status`: `bash artifacts/roof-tiles-s24/sbs.sh r1`; `uv run --project tools/worldgen python artifacts/roof-tiles-s24/budget.py r1`
- 15:25 (po watchdogu) Wnioski z t1 Tykocin / Knyszyn ulica (`sbs/crop-above-t-t1.jpg`, `crop-into-town-t1.jpg`): czerwone dachy z reguły —
  drobniejszy rysunek, wałki i rzędy zamiast kraty prostokątów, ton w plamach; z 60–150 m bez mory. Brązowe (zakładkowa) i grafitowa
  blachodachówka do oceny dopiero po build_world (r1). Rendery oglądam odtąd jako arkusze / wycinki ≤ 1500 px, po kilka, wnioski tutaj.
  Stan kolejki 15:20: heavy 3/3 (regen-wave-2 A / B / C), czekają: roof-tiles-s24, s8-north-s24.
  NASTĘPNY KROK: po `exit=0` w `artifacts/roof-tiles-s24/r1.status`: `bash artifacts/roof-tiles-s24/sbs.sh r1`; `uv run --project tools/worldgen python artifacts/roof-tiles-s24/budget.py r1`
- 15:42 EditMode Win64 (stan t2): 1485 / 1383 passed / 1 failed / 101 skipped; porażka `RegionSelectTests…routeLengthM` kafla C (2398,27 vs
  2397,47 — katalog po road-widen w origin/main, poza gałęzią; brak zmian C# w tej gałęzi). Log: `artifacts/roof-tiles-s24/editmode.log`.
  r1 dalej w kolejce heavy (regen-wave-2 trzyma 3/3 od 14:08–15:02).
  NASTĘPNY KROK: bez zmian (po `exit=0` w r1.status: sbs.sh r1 + budget.py r1).
