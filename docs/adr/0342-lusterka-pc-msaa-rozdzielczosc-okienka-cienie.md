# ADR 0342 — Lusterka na PC: MSAA tekstury, wysokość tekstury od okienka, przełącznik cieni

Status: Proposed, 2026-11-24 (agent mirror-res-s24, gałąź `mirror-res-s24`). Zamyka otwarty pkt 1-2 ADR 0340 i P2-5 z ADR 0265.
Powiązane: 0340 (aliasing lusterek), 0265/0283 (okienka D70), 0136 r2 (`mirrorResolutionScale`), 0068/0243 (budżet kamer lusterek), D74 (budżety PC).

## Problem
Tekstura lusterka (RT 171 x 384 px na High) była bez MSAA (`antiAliasing = 1`, `allowMSAA = false`), więc słupki kabiny i pasy
firanki schodkowały. Okienko na 1080p ma ok. 312 px wysokości szkła (0,30 wysokości zawartości minus 2 x 6 j.), więc RT 384 jest
tam już większa od okienka: na 1080p główny zysk daje MSAA, nie rozdzielczość. Rozdzielczość pomaga dopiero na 1440p / 4K.

## Decyzja (dane w tierach PC, `PcTierSettings`, wszystko `WORKING_VALUE`)
| tier | mirrorMsaa | mirrorWindowTexelsPerPixel | mirrorShadows |
|---|---|---|---|
| Low, Medium | 1 (bez zmian) | 0 (wył.) | wył. |
| High | 4 | 1,0 | wył. |
| Ultra | 4 | 1,5 | wył. |
- Wysokość RT klasy II = max(wysokość tieru, wysokość szkła okienka w px x texelsPerPixel), maks. 1024 (`VehicleCameraBudget.HeightForWindow`).
  Wysokość okienka podaje HUD desktopowy (`MirrorOverrides.WindowPixelHeight`); bez okienka lub na telefonie = 0 = bez zmian.
- MSAA: `RenderTexture.antiAliasing` + `camera.allowMSAA` ustawiane w `RenderTextureMirror.EnsureTarget` (URP bierze próbki z RT).
- Cienie: `UniversalAdditionalCameraData.renderShadows` z tieru; domyślnie wyłączone na wszystkich tierach (patrz pomiar).
- Mobilne `QualityProfile.Tier` i Low/Medium PC: pola 0 = zachowanie sprzed 0342. `rq_mirror_legacy 1` = stary obraz.
- A/B: launch args `rq_mirror_msaa=<1|2|4|8>`, `rq_mirror_shadows=<0|1>`; edytor `KAMION_MIRROR_MSAA`, `KAMION_MIRROR_SHADOWS`,
  `KAMION_MIRROR_BENCH=1` (pomiar GPU konfiguracji, przeplatane rundy).
- Zmian w `ProjectSettings/QualitySettings.asset` nie ma (dane tierów PC są w kodzie, `PcTierTable`).

## Pomiar (edytor, GTX 1070, DrivingLab, para lusterek klasy II, 5 przeplatanych rund x 30 renderów, synchronizacja odczytem piksela)
Edytorowy proxy, NIE player (`UNVERIFIED` w playerze). Mediana ms na parę: bez MSAA 1,63; MSAA 2 1,77; **MSAA 4 1,68**; MSAA 8 1,67;
MSAA 4 + cienie **2,34** (+0,66, +40 %); MSAA 4 przy teksturze x1,5 1,97; x1,5 + cienie 2,71. Scena placu jest lekka (mały koszt
pass'u cieni tu, w świecie z lasem większy) - stąd cienie wyłączone. Surowe czasy klatek kamer kontrolnych (`stats.txt`) nie nadają się do
porównania między przebiegami (współdzielone GPU, baza 27 ms vs 18 ms "po").
Obraz: `artifacts/mirror-res-s24/cmp/L_before_after.jpg` (natywna tekstura, x4) - krawędzie słupka kabiny gładsze po; cienie w tym kadrze
bez widocznej różnicy (nie ma rzucających obiektów w kadrze lusterka).

## Otwarte
1. Pomiar w playerze (`pc-metrics.ps1 ... -Tier High -Fps 60 -Class zalecany`, knyszyn-w, z `-ExtraArgs rq_mirror_msaa=1` vs domyślne) - brak buildu Windows
   i danych świata w tym worktree; polecenie dla lidera w raporcie.
2. Włączenie cieni lusterek (Ultra?) dopiero po pomiarze w świecie z lasem; wystarczy `mirrorShadows = true` w `PcTierTable.Defaults()`.
3. Wartości 1,0 / 1,5 / 4x - `WORKING_VALUE`, kierunek ocenia właściciel/krytyk na buildzie.
Pliki: `Core/ExtraViews.cs`, `Vehicle/Runtime/RenderTextureMirror.cs`, `Rendering/Runtime/{PcTierTable,PcGraphicsTiers,QualityProfile,QualityProfileApplier,RenderOverrides}.cs`,
`UI/Driving/DrivingHud.Desktop.cs`, `Editor/VisualQA/{MirrorDump,VisualQaRunner}.cs`, test `MirrorQuality0342Tests`.
