# Częściowa notatka R5 — referencja High QA

Stan w chwili wcześniejszego przekazania: 2026-11-12 13:36:45 +01:00. Po zamknięciu rundy aktualny status podaje REPORT.md w katalogu nadrzędnym.

Runda gpt-light-r5 pozostaje w toku: końcowy GIS czeka na heavy. To wcześniejsze przekazanie istotnego ustalenia, nie REPORT ani zakończenie rundy; nie stanowi gotowości do scalenia.

VisualQaRunner.RenderToPixels tworzy ARGB32 również dla High. Czysty lab native-grade-lab-v6 bezpośrednio rejestruje R8G8B8A8_SRGB przed post w dotychczasowym torze mimo HDR=true/post=true. Osobna referencja Editor zachowuje R16G16B16A16_SFloat przed post przy końcowym ARGB32 i zgadza się ze zwykłym celem HDR na polach testowych do1 poziomuRGB. To diagnoza tego toruQA, nie telefonu lub runtime. Nie zmieniono wspólnego VisualQaRunner.

Nie należy automatycznie interpretować wcześniejszych różnic tonów i białych powierzchni High jako dowodu odpowiedzi HDR urządzenia. Historyczne pomiary nadal opisują swój tor ARGB32. Próbka formatów Clear/Overcast/Night jest załączona; pełny bake ma5presetów,65PNG i manifest w worktree.

Źródła pełnego dowodu: C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/gpt-light/artifacts/light-r5/native-grade-lab-v6. Niezależna recenzja NATIVE-HDR-REVIEW.md opisuje v3; v6 po korekcie inicjalizacji ma65/65 PNG identycznych SHA256 z obejrzaną v5, a39 wcześniejszych identycznych z v3. FINAL-HDR-REVIEW.md potwierdza czysty v6 i wszystkie327 High HDR końcowego świata. Pomiary są wąskie, bez wholeframe/GPU/A16 PASS.

