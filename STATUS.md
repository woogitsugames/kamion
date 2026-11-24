# STATUS mirror-res-s24 (ADR 0342: jakość obrazu lusterek na PC)
- krok 1: baza "przed" (High, DrivingLab, edytor GTX 1070) w artifacts/mirror-res-s24/before (zrzuty + stats.txt + natywne tekstury lusterek).
- krok 2: kod: mirrorMsaa / mirrorShadows / mirrorWindowTexelsPerPixel w tierach PC (High 4x, 1.0; Ultra 4x, 1.5; Low/Medium bez zmian), HUD podaje wysokość okienka w px, A/B rq_mirror_msaa/rq_mirror_shadows + KAMION_MIRROR_MSAA/SHADOWS. Testy MirrorQuality0342Tests.
- NASTĘPNY KROK: pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 ; potem pwsh artifacts/mirror-res-s24/run_unity.ps1 -Tag after -TimeFrames 20
- krok 3: EditMode Win64 1429/0; bench edytora: MSAA4 1,68 vs 1,63 ms/parę, cienie +0,66; ADR 0342 napisany. Player pominięty (decyzja lidera). Dowody: artifacts/mirror-res-s24.
