# STATUS light-r10 (ADR 0080 — oświetlenie i atmosfera świata r10)
Gałąź: worktree-agent-ac7c9571184d27443. Worktree gotowy (junctiony Data/raw/*, Data/photos; derived, _Generated, Library skopiowane).

- Baseline: `artifacts/light-r10/before/High-overcast` (30 kamer), metryki `scripts/light-metrics.py` (nowy): p10 36,2 / p50 52,1, sky_sigma 5,6, trawa sat 23,5 / sigma 2,0; zdjęcia overcast (132 szt.): p10 16,5 / p50 50,4, trawa sat 34,8 / sigma 4,4. Referencje: `artifacts/light-r10/refs/sheet.jpg`.
- WIP shadery (NIESKOMPILOWANE jeszcze w Unity): `KamionAtmosphere.hlsl` (mgła wysokościowa, toe dla Low, mokra nawierzchnia), `Sky.shader` (warstwa chmur, overcast kierunkowy), `WorldPBR` (wariacja trawy, mokro), `WorldSurface` (mokro), MixFog -> KamionMixFog w 7 shaderach.
- BRAKUJE: strona C# (globalne uniformy `_KamionHaze/_KamionHazeColor/_KamionTone/_KamionWet/_KamionCloud*`, tekstura chmur, pola LightingPreset/QualityProfile/RenderOverrides, SkyModel overcast kierunkowy), SSAO Ultra, testy, ADR 0080.
- NASTĘPNY KROK: dopisać `Rendering/Runtime/Sky/WorldAtmosphere.cs` + pola presetu, potem render:
  `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting overcast -OutputDir artifacts/light-r10/r1/High-overcast` (najpierw sprawdź blokadę `artifacts/locks/PHONE_RUN` w main; po renderze `git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset`).
