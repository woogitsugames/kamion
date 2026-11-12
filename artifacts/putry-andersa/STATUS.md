# putry-andersa (ADR 0146) STATUS
2026-11-12 19:24 start. Worktree .claude/worktrees/putry-andersa, branch putry-andersa (base main 70b67fc7b).
Zakres: brief P1-3 (latarnie Putry / pobocze Putry / Andersa 810896), potem z REVIEW s14-0139: portal Andersa P1 (tablice ~0,6 m za wysoko w 275528; beam_depth 0,55 vs _b6), P2 (slupy ekranu dwuteownik, czerwony pas gzymsu, para tablic ostrzegawczych 275528). Lider: zmergowac main (0139, 97996ef6) przed buildem, generated -> ours.
Krok 1 (w toku): analiza latarni na ortofoto 0,08 m (artifacts/putry-andersa/tools/ortho.py, look/z_p*.jpg).
 - z_p9/z_p8: podstawa slupa stoi NA GRUNCIE w szczelinie (cien na zwirze od podstawy do sciany NE), nie na konsoli pomostu.
 - Hipoteza robocza: ogniskowa SfM Mapillary 494288 (1.27) jest bledna (iPhone natywnie ~0.82) -> "glowice 6 m nad okiem" z ADR 0143 wynika z FOV, nie z wysokosci slupow. Do potwierdzenia liczbami (modul linii P-1, rozstaw ramion z orto, cien oprawy na pomoscie).
NASTEPNY KROK: python artifacts/putry-andersa/tools/ortho.py crop -503 -24 12 3 look/z.jpg ; pomiar cieni -> decyzja o wysokosci/podstawie slupow.
PHONE_RUN lock istnieje (a16-perf r2b) -> Unity czeka.
