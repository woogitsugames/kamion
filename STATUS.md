# STATUS cabin-polish-s23 (D84: wnętrze kabiny PC — polish po recenzji REVIEW-2026-11-17-s23-cabin-pc)
- Worktree z origin/main 14925a7cc. Skrypty odłączone: `artifacts/cabin-polish-s23/{run,chain,assets-win64,bl,a6}.ps1` (status `*.status`, `exit=`).
- Plastik (P1-2): `plastic_grain.py` + `cab_material_scans.json` — ziarno 2–5 mm (waga 0,7) + plamy połysku 2,5–10 cm; normalne mediana 10,3°, p95 20,7° (było 6,9°/14,1°). Z fotela 1 px ≈ 0,9 mm (wyliczone).
- Zmierzch (P1-3): `CabInteriorLighting` `nightViewEv` 0,45, `panelGlow` 0,07, wygaszanie +3°…−5°. Pomiar sRGB cab-dash dusk: piasta 20,21,28 → 12,12,13; droga 10,12,20; niebo 41,59,94.
- Geometria (`build_interior.py`, eksport a6): uszczelki + zaślepki słupka A, żebra tacek 22 mm, daszek zegarów fade 50 mm, roleta kierowcy 0,20 m, przeszycie ×3,2, wytarcie wieńca niesymetryczne. LOD0 105 121 / LOD1 43 984 / LOD2 21 551 tris; `check_export.py` PASS.
- Końcowy przebieg (`final.ps1`): eksport LOD0 105 163 / LOD1 44 003 / LOD2 21 557, `check_export.py` PASS, BuildBatch + InstallBatch `TRUCK_RESULT: OK`, EditMode Win64 1249/22/37 (20× `StartClearanceTests.ImportedScene_*` + 2× `CarPaintMaterialTests.DepositionChannel` — jak na main; nowy `CabTwilightTests` 2/2).
- Rendery High -Pc 1920×1080 DrivingLab: `artifacts/cabin-polish-s23/{base,f}-{clear,dusk}`, `f-lowsun`, `f-night`, tier mobilny `f-mob-{clear,dusk}`, WorldC `f-world-clear` (cab-apillar, cab-driver-ab10); przed/po `view/ab-*.jpg`. Kopia w main `artifacts/cabin-polish-s23/`.
- Pomiary cab-dash (sRGB): dusk piasta 20,21,28 → 10,10,11 przy drodze 10,12,20; lowsun 89 % pikseli dolnej deski > 3 % luma; szczyt legend dusk 112 → 113 (podniesienie `cab_backlight.json` 8→12 cd/m², cap 0,09 bez mierzalnego efektu — do sprawdzenia).
- Roleta wróciła do autorskiego 0,10 m. ADR: `docs/adr/DRAFT-d84-kabina-polish-zmierzch-i-ziarno.md`.
- Otwarte: lusterka/daszek poza kadrem 62° (decyzja pitch/FOV — A/B `cab-driver-ab10`), ciepła poświata niemierzalna na piaście, brak zdjęć referencyjnych (docs/06 §5 pkt 3), kurz bez zmian, pojedyncze jaśniejsze odcinki żeber tacek (atlas AO), kamery QA nie w scenie DrivingLab (`pwsh scripts/build-lab.ps1 -SkipAudio`).
- NASTĘPNY KROK (lider): visual-critic na `view/ab-*.jpg`, `f-*`; po scaleniu w main: `-executeMethod Game.Editor.Setup.TruckAssetBuilder.BuildBatch`, potem `Game.World.Import.WorldTruckInstaller.InstallBatch`.

# STATUS — alt-113-s24 (PR #113 jackknife-0228 r4, ADR 0228)
- Krok 1: merge origin/main 33541aa04 czysty (D79 osie tridemu 7,63 m, #171). bodyBoxes naczepy bez zmian i zgodne (test_dims_sync 12/12; BoxCollidery graybox nie zależą od osi). dotnet: tylko golden brake_80_0_dry_abs_comb@laden40 FAIL (jak w recenzji).
- NASTĘPNY KROK: izolacja przyczyny golden: `dotnet run -c Release --project tools/physics-runner/Runner -- --only brake_80_0_dry_abs_comb@laden40 --out <dir>` + porównanie z goldenami main/#113
