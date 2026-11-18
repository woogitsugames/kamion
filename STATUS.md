# STATUS night-polish-s24

- 23:55 baseline renders (artifacts/night-polish-s24/base): banding High night runlen 115 px (no dither), Ultra 4.6, Low 8.8 but bands still visible (R11G11B10). Nav no-map bg 31/255, text 197.
- NEXT: apply dither + quantizer dither in Sky.shader, nav night cap, halo groups; pwsh artifacts/night-polish-s24/go.ps1 -Name after1 -Unity -Cmd ...
