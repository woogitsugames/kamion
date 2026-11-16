# STATUS cabin-pc-s23 (D84: wnętrze ciężarówki na PC)
- Krok A (5d03d1b48): `DrivingVehiclePrefabs` = jedna ścieżka (DrivingLab, WorldSceneBuilder, WorldTruckInstaller), graybox tylko z ostrzeżeniem `[VEHICLE] FALLBACK`; DrivingLab.unity z TRAKT + naczepą art + rig nieba (EnvironmentLighting, WorldVolume, QualityProfileApplier); przypięte GUID-y prefabów; test `DrivingScenesFullTruckTests` 5/5.
- Krok B/C: plastik kabiny = syntezowany stippling (`tools/blender/truck/interior/plastic_grain.py`, nachylenie normalnych mediana 6,9°, p95 14,1°) zamiast embossu ze skanu skóry; ekran nawigacji bez mapy ciemny. ADR: `docs/adr/DRAFT-d84-kabina-pc-jedna-sciezka-instalacji.md`.
- Rendery High 1920x1080: `artifacts/cabin-pc-s23/{lab1,lab2-clear,lab2-dusk,p2-clear,p2-dusk,p3-clear,w1-clear,w1-dusk}`, przed/po `ab-grain-crop.jpg`.
- W toku: pełne EditMode + PlayMode (`artifacts/cabin-pc-s23/t1.status`).
- NASTĘPNY KROK: `Get-Content artifacts/cabin-pc-s23/t1.status`; po zielonych testach `git push -u origin cabin-pc-s23`.
- Dla lidera po scaleniu: `pwsh scripts/build-lab.ps1 -SkipAudio` nie jest konieczne (scena w gicie); w main wymagane `-executeMethod Game.Editor.Setup.TruckAssetBuilder.BuildBatch` (nowe tekstury plastiku do _Generated) przed buildem Windows.
