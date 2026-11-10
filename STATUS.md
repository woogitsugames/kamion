# STATUS light-r10 (ADR 0080 — oświetlenie i atmosfera świata r10)
Gałąź: worktree-agent-ac7c9571184d27443. Worktree gotowy (junctiony Data/raw/*, Data/photos; derived, _Generated, Library skopiowane).

- Baseline: `artifacts/light-r10/before/High-overcast` (30 kamer), metryki `scripts/light-metrics.py` (nowy): p10 36,2 / p50 52,1, sky_sigma 5,6, trawa sat 23,5 / sigma 2,0; zdjęcia overcast (132 szt.): p10 16,5 / p50 50,4, trawa sat 34,8 / sigma 4,4. Referencje: `artifacts/light-r10/refs/sheet.jpg`.
- WIP shadery (NIESKOMPILOWANE jeszcze w Unity): `KamionAtmosphere.hlsl` (mgła wysokościowa, toe dla Low, mokra nawierzchnia), `Sky.shader` (warstwa chmur, overcast kierunkowy), `WorldPBR` (wariacja trawy, mokro), `WorldSurface` (mokro), MixFog -> KamionMixFog w 7 shaderach.
- BRAKUJE: strona C# (globalne uniformy `_KamionHaze/_KamionHazeColor/_KamionTone/_KamionWet/_KamionCloud*`, tekstura chmur, pola LightingPreset/QualityProfile/RenderOverrides, SkyModel overcast kierunkowy), SSAO Ultra, testy, ADR 0080.
- NASTĘPNY KROK: dopisać `Rendering/Runtime/Sky/WorldAtmosphere.cs` + pola presetu, potem render:
  `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting overcast -OutputDir artifacts/light-r10/r1/High-overcast` (najpierw sprawdź blokadę `artifacts/locks/PHONE_RUN` w main; po renderze `git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset`).

## Przejęcie (agent 2, 2026-11-10 22:xx)
- 0e1565a: zacommitowany WIP poprzednika (runda 2: chmury, mgiełka 1.6, film wody, SSAO Ultra renderer). Strona C# JEST zrobiona (a86bf28) — powyższe „BRAKUJE” nieaktualne poza testami i ADR 0080.
- r3 High overcast (6 kamer świata, `artifacts/light-r10/r3`): p10 40,4 / p50 57,2 / sky_top 87,7 / sky_sigma 7,6 / trawa sat 22,8 sigma 1,9. Zdjęcia overcast (refs): p10 ~17-20 / p50 ~50-52 / sky_top 88 / sky_hor 77 / sigma 8,3 / trawa sat 33-35.
- Sweep (`artifacts/light-r10/sweep/High-L<look>-ev<ev>`): C+ev-0.33: p10 31,5 p50 49,1; C+ev-0.67: p10 27,3 p50 43,2 (niebo szarzeje 81/68 - źle). Nowe warianty krzywej bez zmiany ekspozycji: D (toe .8/.30/.50): p10 32,4 p50 52,7; E (toe .9/.40/.60 ~ gamma 1,45 wokół nieba): p10 29,0 p50 49,5 sky_top 86,8 trawa sat 34,9 - najbliżej zdjęć.
- NASTĘPNY KROK: zestaw wariantów dla właściciela (High, 9 kamer) + Low parity + koszt:
  `bash <scratch>/vqa.sh artifacts/light-r10/owner/High-2-E High overcast "rq_look=4" "stretch-02,route-putry-approach,kwadrat-park-gate,g3a-eye-s0262,stretch-01,putry-above,cab-gate,truck-34,cab-driver"` (= `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting overcast -Rq rq_look=4 -Cameras ... -OutputDir ...`; przed startem sprawdź `artifacts/locks/PHONE_RUN` w main, po renderze `git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset`).
