# STATUS night-polish-s24

- 23:55 baseline renders (artifacts/night-polish-s24/base): banding High night runlen 115 px (no dither), Ultra 4.6, Low 8.8 but bands still visible (R11G11B10). Nav no-map bg 31/255, text 197.
- NEXT: apply dither + quantizer dither in Sky.shader, nav night cap, halo groups; pwsh artifacts/night-polish-s24/go.ps1 -Name after1 -Unity -Cmd ...
- 00:05 after1: dither policy (FinalDither), sky R11G11B10 dither, nav night cap 0.3 + dark no-map, halo amber/reverse K 0.15; EditMode Win64 1297 pass / 0 fail / 101 skip. Finding: QA capture renders HDR tiers through 8-bit target (bands remain 0.9 LSB steps); QA fix in VisualQaRunner (ARGBHalf target).
- NEXT: qa2 (HDR-capture A/B) then pwsh scripts/build-windows.ps1 -Slot -Regions knyszyn-w; player night shots; pc-metrics -Extra lighting=night
