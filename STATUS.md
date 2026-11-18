# STATUS regen-c-s24

- 17:25 worktree z main 4f34ce0d2; Library kopiowana z win-build (robocopy w tle). Budżet C przed (z manifestu w git): LOD0 vis 10 933 015 tris, sloty materiałów 1962 (max 75/chunk), glb 526 MB.
- 17:25 start build_world C --context (slot heavy) -> fidelity -> export-route -> route_links (`artifacts/regen-c-s24/tools/step1.ps1`, status `artifacts/regen-c-s24/step1.status`).
- 17:40 recenzja Knyszyna: FAIL anti-slop / PASS warunkowy D51 -> docs/reports/REVIEW-2026-11-18-s24-knyszyn.md.
- NASTĘPNY KROK: `Get-Content artifacts/regen-c-s24/step1.status` (czekaj na exit=0), potem `uv run --project tools/worldgen python -m pytest tests/gis -q` (slot heavy).
- 17:49 regen C exit=0 (build_world 979 s, fidelity 466 s, export-route, route_links). Budżet (30-budget.py jak c-regen2-s23): 23 kamery, tris High/Low bez zmian (max stretch_04 1 983 417), far_field Low 25 389, GREEN; manifest materiały 340->341 (roof_sheet_grey), glb +0,93 MB (+58 196 B/chunk). Commit 667976f41.
- 17:50 start pytest tests/gis (czeka na slot heavy) i łańcuch Unity: import Win64 -> VQA WorldC High clear -> EditMode Win64 (`artifacts/regen-c-s24/{pytest,unity}.status`).
- NASTĘPNY KROK: `Get-Content artifacts/regen-c-s24/unity.status, artifacts/regen-c-s24/pytest.status`; po vqa obejrzyj `artifacts/regen-c-s24/vqa-High-clear/{putry_above,route_putry_approach,g3b_rondo_putry_approach,g3b_eye_s1482,...}.png`.
- 18:19 import Win64 C: próba 1 exit=2 (brak SM_CabInterior_LOD0.fbx poza gitem na nowym PC; skopiowany z win-build), próba 2 exit=0 (64 chunki, Low+High); VQA WorldC High clear exit=0 (55 kamer, 53 s). EditMode Win64 próba 1: 1340/1224 pass/7 fail (wszystkie z ciężarówką kanoniczną — przez brak LOD0), powtórka w kolejce slotu unity.
- Kamery C obejrzane (sbs vs vegetation-r3/before High clear): putry-above, route-putry-approach, g3b-rondo-putry-approach, g3b-eye-s1482, driver-andersa-to-putry, edge-*: narożniki ronda Putry, ekrany, mur s1482 bez regresji. edge-south: płaska jasnoszara łata (~7x4 m) z ciemną obwódką na jezdni — do sprawdzenia (decal_patch?).
- Uwaga: import przeliczył manifest_sha256 w region.yaml (LF) — niezacommitowane, decyzja lidera.
- NASTĘPNY KROK: `Get-Content artifacts/regen-c-s24/unity3.status, artifacts/regen-c-s24/pytest.status`.
- 19:00 pytest tests/gis: 2479 passed, 1 skipped, 2 xfailed (2936 s) — zielono, test_ec_chimneys i test_export_is_deterministic przeszły.
- EditMode Win64 powtórka (po imporcie z LOD0): 1340 / 1252 pass / 1 fail / 87 skip; jedyny fail DrivingScenesFullTruckTests.ArtPrefabs_HavePinnedGuids — Trailer prefab w `_Generated/Trailer` (poza gitem, kopia z main) ma GUID cac16030… zamiast pinned ab5e5ba6… → środowiskowe na nowym PC (main ma ten sam stary prefab; przebudowa naczepy = lider).
- Commit region.yaml/build_manifest.json: manifest_sha256 źródeł przeliczone przez import po przejściu repo na LF.
- NASTĘPNY KROK (lider): scal regen-c-s24; na main przebuduj naczepę (Kamion/Setup) i powtórz EditMode; sprawdź łatę na jezdni w edge-south.
