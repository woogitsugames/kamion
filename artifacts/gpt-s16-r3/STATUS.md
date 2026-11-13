# STATUS — gpt-s16 r3 / ADR 0155
2026-11-13 02:31 CET. Baza r2 1f81e87ee + origin/main e638abf31; konflikty tylko wygenerowane, ours + zaplanowana regeneracja.
R1 i R2 wypchnięte, bez merge/push main. R2 pełny GIS 986 passed / 4 xfailed, EditMode 484/484, critic PASS zakresu, D51 PARTIAL.
R3: diagnoza plam pod Putrą. Kod produkcyjny jeszcze bez zmian; przedmiotem kontroli są shadow caster, bias/kaskady i wypiekane far shadows.
Przygotowano te same kontrolne/G3 kamery, wszystkie SBS i dwa zbliżenia wyspy; wartości poz klasy B / WORKING_VALUE, bez udawanej kalibracji.
NASTĘPNY KROK: pwsh artifacts/gpt-s16-r3/baseline-world.ps1 -Stage baseline
Sprzątanie: kopie całego świata zastępują hashe; dowody tylko zwarte, pełne PNG lokalne. Usuwanie r1 clear-rejected zablokowane przez automatyczny przegląd — bez obchodzenia.
