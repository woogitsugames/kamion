# STATUS light-r11 (ADR 0080 r11 — poprawki po recenzji visual-critic)
Gałąź: worktree-light-r11 (z main ad9760d). Worktree: `.claude/worktrees/light-r11`. `_Generated` skopiowane z main (poza gitem).
Zakres: asfalt overcast za ciemny, auta/korony w czerni (ambient/odbicia/mgiełka 100–500 m), odcień nieba overcast, smuga na szybie kabiny (clear). Wariant 3 (toe 0,9/0,4/0,6, −0,2 EV) bez zmian.

- Krok 0: przeczytane zasady, recenzja, ADR 0080, kod nieba/mgły/presetów.
- NASTĘPNY KROK: baseline `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting overcast -OutputDir artifacts/light-r11/before/High-overcast` (sprawdź `artifacts/locks/PHONE_RUN` w main; po renderze `git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset`).
