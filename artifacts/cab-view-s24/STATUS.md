# cab-view-s24 — STATUS

## 2026-11-18 17:5x krok 1: kod wariantów
- Gra dziś: ControlSettings.cabFov = 55° (pionowe), suwak „Pole widzenia” 45–75° co 5° JUŻ ISTNIEJE (UI/ControlSettingsPanel.cs:228); QA cab-driver = 62°; pochylenie spoczynkowe DriverHead.RestPitchDownDeg = 6°; oko = DriverEyePoint (dims.json driver_eye_point_m [-0.55, 0.45, 2.50], R46 +635 mm).
- Dodane: `Camera/CabViewVariants.cs` (5 wariantów, tylko QA), kamery QA `cab-view-*` w TruckAssetBuilder.AddControlCameras, `Editor/VisualQA/CabViewQa.cs` (`-qaTruckPose E,N,heading`, `-qaCabViewAudit <tsv>`), 2 haki w VisualQaRunner.
- Library + World/bialystok-industrial-c + Truck/Trailer skopiowane z win-build; cab-lod0 -Build (Blender) w toku.
- NASTĘPNY KROK: po `artifacts/cab-view-s24/logs/cab-lod0.status` exit=0 → slot Unity → `-executeMethod Game.World.Import.WorldTruckInstaller.InstallBatch -buildTarget Win64` → render `pwsh scripts/visual-qa.ps1 -Scene WorldC_High -Tier High -Pc -BuildTarget Win64 -Width 1920 -Height 1080 -Lighting clear -Cameras cab-view-0-fov55,...`

## 2026-11-18 18:1x krok 2–3: rendery + WARIANTY.md (KONIEC)
- TRAKT + naczepa zbudowane i zainstalowane w WorldC/WorldC_High (TRUCK_RESULT: OK); 11 kamer × 2 miejsca (start, rondo) wyrenderowane 1920×1080 High -Pc clear (VISUALQA_RESULT OK rendered=11 ×2); audit.tsv z kątami lusterek.
- Wynik: lusterka boczne leżą 54–76° od osi — żaden FOV ≤ 75° ich nie pokaże; okienka D70 tak. Rekomendacja: 70°/6° (wariant B). Nowe P2: panel HUD zasłania fizyczne zegary.
- NASTĘPNY KROK (lider/właściciel): decyzja wariantu → zmiana `ControlSettings.cabFov` (55) i kamery QA `cab-driver` (62) na wybraną wartość; ADR.

## 2026-11-18 krok 4: wdrożenie D90 / ADR 0294 (po decyzji właściciela)
- ControlSettings.DefaultCabFovDeg = 70, schemat 6 (55→70 jednorazowo, inne wartości zostają), cab-driver QA = 70; HudVisibility.IsCabView + DrivingHudContext.CameraModeOverride (render QA zna tryb kamery), CabViewQa.IsCabCameraId, kamera QA chase-hud; testy CabView0294Tests + poprawione ControlSettingsTests/Controls0243Tests; ADR 0294, D90, indeks ADR.
- Rendery po zmianie: start/ i rondo/ (pasek w kabinie znika, w chase-hud jest). Stare w przed-d90/.
- NASTĘPNY KROK: wynik EditMode `artifacts/cab-view-s24/logs/tests.status`, potem `git merge origin/main`, commit, push.
