# STATUS cabin-polish-s23 (D84: wnętrze kabiny PC — polish po recenzji REVIEW-2026-11-17-s23-cabin-pc)
- Worktree z origin/main 14925a7cc. Skrypty odłączone: `artifacts/cabin-polish-s23/{run,chain,assets-win64,bl,a6}.ps1` (status `*.status`, `exit=`).
- Plastik (P1-2): `plastic_grain.py` + `cab_material_scans.json` — ziarno 2–5 mm (waga 0,7) + plamy połysku 2,5–10 cm; normalne mediana 10,3°, p95 20,7° (było 6,9°/14,1°). Z fotela 1 px ≈ 0,9 mm (wyliczone).
- Zmierzch (P1-3): `CabInteriorLighting` `nightViewEv` 0,45, `panelGlow` 0,07, wygaszanie +3°…−5°. Pomiar sRGB cab-dash dusk: piasta 20,21,28 → 12,12,13; droga 10,12,20; niebo 41,59,94.
- Geometria (`build_interior.py`, eksport a6): uszczelki + zaślepki słupka A, żebra tacek 22 mm, daszek zegarów fade 50 mm, roleta kierowcy 0,20 m, przeszycie ×3,2, wytarcie wieńca niesymetryczne. LOD0 105 121 / LOD1 43 984 / LOD2 21 551 tris; `check_export.py` PASS.
- Unity Win64: BuildBatch + InstallBatch `TRUCK_RESULT: OK`; EditMode 1247/22/37 — porażki = 20× `StartClearanceTests.ImportedScene_*` + 2× `CarPaintMaterialTests.DepositionChannel` (te same klasy co na main).
- Rendery High -Pc 1920×1080 DrivingLab: `artifacts/cabin-polish-s23/{base,r3}-{clear,dusk}`; zestawienia przed/po `view/ab-*.jpg` (skopiowane do main `artifacts/cabin-polish-s23/`).
- ADR: `docs/adr/DRAFT-d84-kabina-polish-zmierzch-i-ziarno.md`.
- Otwarte: kamery QA `cab-apillar`/`cab-driver-ab10` są w prefabie, ale nie w scenie DrivingLab (wymaga `pwsh scripts/build-lab.ps1 -SkipAudio`); brak legalnych zdjęć referencyjnych kabiny (docs/06 §5 pkt 3); roleta przy 0,20 m ledwo wchodzi w kadr; pojedyncze jaśniejsze odcinki na żebrach tacek (szew atlasu AO).
- NASTĘPNY KROK (lider): visual-critic na `view/ab-*.jpg` i `r3-*`; po scaleniu w main: `-executeMethod Game.Editor.Setup.TruckAssetBuilder.BuildBatch` + `Game.World.Import.WorldTruckInstaller.InstallBatch`.
