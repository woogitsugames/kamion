# cab-view-s24 — STATUS

## 2026-11-18 17:5x krok 1: kod wariantów
- Gra dziś: ControlSettings.cabFov = 55° (pionowe), suwak „Pole widzenia” 45–75° co 5° JUŻ ISTNIEJE (UI/ControlSettingsPanel.cs:228); QA cab-driver = 62°; pochylenie spoczynkowe DriverHead.RestPitchDownDeg = 6°; oko = DriverEyePoint (dims.json driver_eye_point_m [-0.55, 0.45, 2.50], R46 +635 mm).
- Dodane: `Camera/CabViewVariants.cs` (5 wariantów, tylko QA), kamery QA `cab-view-*` w TruckAssetBuilder.AddControlCameras, `Editor/VisualQA/CabViewQa.cs` (`-qaTruckPose E,N,heading`, `-qaCabViewAudit <tsv>`), 2 haki w VisualQaRunner.
- Library + World/bialystok-industrial-c + Truck/Trailer skopiowane z win-build; cab-lod0 -Build (Blender) w toku.
- NASTĘPNY KROK: po `artifacts/cab-view-s24/logs/cab-lod0.status` exit=0 → slot Unity → `-executeMethod Game.World.Import.WorldTruckInstaller.InstallBatch -buildTarget Win64` → render `pwsh scripts/visual-qa.ps1 -Scene WorldC_High -Tier High -Pc -BuildTarget Win64 -Width 1920 -Height 1080 -Lighting clear -Cameras cab-view-0-fov55,...`
