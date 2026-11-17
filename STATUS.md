# STATUS cabin-pc-s23 (D84: wnętrze ciężarówki na PC)
- Krok A (5d03d1b48): `DrivingVehiclePrefabs` = jedna ścieżka (DrivingLab, WorldSceneBuilder, WorldTruckInstaller), graybox tylko z ostrzeżeniem `[VEHICLE] FALLBACK`; DrivingLab.unity z TRAKT + naczepą art + rig nieba (EnvironmentLighting, WorldVolume, QualityProfileApplier); przypięte GUID-y prefabów; test `DrivingScenesFullTruckTests` 5/5.
- Krok B/C: plastik kabiny = syntezowany stippling (`tools/blender/truck/interior/plastic_grain.py`, nachylenie normalnych mediana 6,9°, p95 14,1°) zamiast embossu ze skanu skóry; ekran nawigacji bez mapy ciemny. ADR: `docs/adr/DRAFT-d84-kabina-pc-jedna-sciezka-instalacji.md`.
- Rendery High 1920x1080: `artifacts/cabin-pc-s23/{lab1,lab2-clear,lab2-dusk,p2-clear,p2-dusk,p3-clear,w1-clear,w1-dusk}`, przed/po `ab-grain-crop.jpg`.
- t1 (przed merge, Android): PlayMode 191/0/9; EditMode exit=10 — porażki tylko `StartClearanceTests.ImportedScene_*` (nieaktualny import regionów w worktree: spawn 12 m vs 90 m, brak Spawn_DepotGate).
- s23b (cabin-pc-s23b): merge origin/main 68d55c46a (ff080a821): STATUS = nasz, `Trailer_Curtainsider_Graybox.prefab` = main (generowany, osie 7,63 m).
- W toku: łańcuch Win64 `artifacts/cabin-pc-s23/chain-b.ps1` → kroki b-assets (Truck+TrailerAssetBuilder), b-edit, b-play, b-vqa (WorldC -Pc High clear/dusk → `b-w1-clear`, `b-w1-dusk`).
- NASTĘPNY KROK: `Get-ChildItem artifacts/cabin-pc-s23/b-*.status | % { $_.Name; Get-Content $_ }`; po zielonych testach i obejrzeniu zrzutów `git push -u origin cabin-pc-s23`.
- Dla lidera po scaleniu: `pwsh scripts/build-lab.ps1 -SkipAudio` nie jest konieczne (scena w gicie); w main wymagane `-executeMethod Game.Editor.Setup.TruckAssetBuilder.BuildBatch` (nowe tekstury plastiku do _Generated) przed buildem Windows.
