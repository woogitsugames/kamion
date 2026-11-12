Przygotowanie r3 — źródła i zakres, 12 listopada 2026.

Referencja cm92458760 została obejrzana w oryginale i zweryfikowana haszem w r2. Widoczny jest mokry asfalt z lokalnym odbiciem nieba, znaków i roślin przy przejściu; kostka pozostaje czytelna. Nie ma podstaw do włączenia całej nawierzchni w jednolitą lustrzaną taflę. Poza C / WORKING_VALUE i photometric_use=false zostają zachowane.

ADR 0080 opisuje wcześniejsze mokro jako FAIL: jasny plastikowy asfalt, zlewające się oznakowanie, mała zmiana kostki. Do czasu baseline nie włączamy mokro w żadnym presettcie.

Istniejący KamionWetSurface steruje przyciemnieniem albedo, smoothness filmu i udziałem kałuż z mapy makro. WorldPBR używa zmienionego tn do obliczenia nw po tej funkcji. WorldSurface używa normalnej geometrycznej i pomocniczego tnWet=(0,0,1), więc niewykorzystanie tego tnWet samo w sobie nie dowodzi błędu wymagającego zmiany shadera.

Recenzja main batch2 wymaga sprawdzenia klina tła w 2948/303305. Niezależny preflight potwierdza ostry kontur w starych czterech parach; możliwa sylwetka istniejącej geometrii i zbyt krótki dystans fog po kompresji far-field. Hipoteza nie jest root cause. Najpierw cztery świeże PNG po edge r1; jeśli problem zostanie, odróżnić Apron od WorldFarField w edytorowym QA. Bez zmian geometrii lub plików edge/Claude.

R3 zmienia na razie wyłącznie dowody edytorowe i skrypty własnej rundy. Produkcyjny shader mokro i presety są bez zmian. Generator/import/baseline biegną w jednym szeregowym pipeline, którego Python czeka na heavy.
Dodatkowy odczyt rodzica: obejrzano dwa oryginalne PNG r1 Low-clear (2948595898752384: 1280×720; 303305168125936: 2048×1152). Klin ma prosty ukośny górny kontur i zasłania chmury nad halami. Dla starego kadru2948 punkt około x1120,y395 leży wewnątrz płaszczyzny; to ręczna wskazówka do oględzin, nie skalibrowany ROI i nie dowód renderera. Po świeżej geometrii punkt trzeba zweryfikować ponownie. P1 pozostaje otwarte do baseline i maski.
