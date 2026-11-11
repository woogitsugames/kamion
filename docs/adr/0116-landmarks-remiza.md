# ADR 0116 — Remiza JRG2, zgodność z fotografią 7197

## Runda r1 — 11 listopada 2026

Sesja 7, gałąź `gpt-landmarks-r1`, worktree `.claude/worktrees/gpt-landmarks`.
Punktem wyjścia jest main `5f2aa277`. Poprzedni model remizy r7 jest już scalony.
Źródło porównania: fotografia Commons „7197 May 2021 in Białystok.jpg”, Rakoon, CC0;
atrybucja i pochodzenie są opisane w ADR 0070 oraz LICENSES.

Celem są ciemne i gęste iglaki, gradient górnych i dolnych tafli łuków, zacieki mające
źródło w obróbkach oraz usunięcie fasetowania tui na Low. Bazowy pigment tynku pozostaje
zgodny z D48. Zmiany wyłącznie w generatorze i danych remizy; bez globalnej kalibracji światła.

Najpierw świeży generator, import i baseline czterech kamer remizy w Low/High, clear/overcast.
Po zmianie powtórzenie tych kadrów, a przed raportem pełny zestaw kamer trasy i testy GIS/EditMode.
Statystyki siatek i instancji są raportowane osobno. Budżet Low: brak wzrostu draws, suma
trójkątów najwyżej +2%. Statystyki edytora nie stanowią pomiaru GPU na A16.

## Stan eksperymentu r1

Baseline zakończony: 48 kamer w każdym z czterech warunków, łącznie 192 PNG.
Kandydat ma wygładzone normalne istniejących tui Low, mocniejszy gradient szkła hali,
szersze dwa iglaki i gęstszy rdzeń. Paleta iglaków mieści się w nowej, wcześniej
nieużywanej komórce tego samego atlasu. Bazowy pigment tynku D48 jest zachowany.
Pas zacieków o autorskiej głębokości 1 m podąża za obróbką łukowego dachu;
kontrola geometrii sprawdza zarówno jego krzywiznę, jak i odsunięcie od otworów.

Wygenerowany GLB: LOD0 9344 → 9584 trójkąty, LOD1 2828 → 2860, LOD2 164 → 164.
Liczba prymitywów pozostaje 3/2/1. Są to liczby modelu. Kanał alfa całej mapy jest identyczny z bazą, podobnie
jak RGBA poza istniejącą komórką igliwia. Skany i licencje pozostają dotychczasowe.

Pojedynczy zestaw GIS `test_fire_station_r7.py`: końcowo 7/7, przez pulę `heavy`.
Kontrola białego parapetu i poprzeczki wykryła błędne objęcie ich maską wnętrza;
po poprawce oba elementy zachowują poprzednie AO. Każda generacja i test
Pythona o dużym koszcie zajmują slot `heavy`; import nie uruchamia generatorów po cichu.

Osobna diagnostyka plamy przy maszcie: mediana Y wybranego ROI na High wynosi
114,83, po wyłączeniu cieni bezpośrednich 131,12; sąsiedni tynk 131,19.
Wyłączenie ambient GI albo SSAO pozostawia 114,83. Dodatkowy promień CPU od tego
punktu ku słońcu presetu overcast trafia w komórkę atlasu flagi po 6,76 m;
promienie z jasnych miejsc obok nie trafiają w przeszkodę. Źródłem jest flaga.
Nie dodano do albedo kompensującej jasnej plamy.
Dowody i dokładne ROI są w `artifacts/landmarks-r1/wall-patch-diagnostics.json`.
Geometria przeszkody: `artifacts/landmarks-r1/shadow-occluder.json`.

## Wyniki końcowego kandydata r1

Powtórzono wszystkie 48 kamer w Low/High i clear/overcast, w tej samej kolejności
co baseline: 192 pary. Obejrzano 24 arkusze po osiem par, szerokość 960 px.
112 obrazów jest pikselowo identycznych; największa zmiana dotyczy remizy.
Pofałdowane cienie dachów w High-above występują również w baseline przy tym samym
pełnym przebiegu. Wczesnego fokusu z inną kolejnością kamer nie używa się do oceny tej regresji.
Wszystkie 96 warunków Low: draws siatek +0, draws instancji +0, maksymalna delta
sumy trójkątów 0,0% w statystykach zaokrąglonych do tysiąca. Dokładny wzrost LOD1
samej remizy wynosi 32 trójkąty. To szacunki edytora, bez deklaracji wyniku GPU.
`budget-after.csv` zawiera każdą kamerę, siatki i instancje osobno.

Mediana Y szkła Low-overcast: lewa góra/dół 64,72/66,93 → 59,93/48,86;
prawa 68,65/67,72 → 62,65/48,86. High-overcast: 71,93/74,65 → 66,65/54,86
oraz 74,79/73,93 → 68,72/54,86. Gradient góra–dół jest czytelny; High pozostaje
nieco jaśniejszy od orientacyjnego celu fotografii. Dokładne ROI: `glass-glass-final.json`.
Materiał wnętrza jest autorskim WORKING_VALUE, nie pomiarem transmisji szyby.

Wszystkie 64 wpisy chunków i roads_qa są identyczne względem świeżego baseline.
W manifeście zmienił się tylko materiał fire_station. Generator 479 s, bez fallback=True.
Shared shadery, globalne światło i źródła dróg nie są zmieniane.
EditMode: 261/261. Końcowy pełny GIS: w toku; wynik będzie zapisany w REPORT.

Ocena fotografii: PARTIAL. Tuje Low mają gładkie normalne bez wzrostu geometrii,
a iglaki ciemniejsze i szersze rdzenie. Ich korony nadal mają rozpoznawalną
proceduralną sylwetkę; nie jest to fotograficzny PASS. Po wiadukcie i kominach
należy wrócić do organicznej budowy koron. Zacieki podążają za obróbką, pigment
tynku D48 pozostaje bez zmian; odwzorowanie zabrudzeń jest nadal przybliżeniem.
Telefon i niezależna recenzja pozostają po stronie lidera. Nie deklaruje się zamknięcia bramki 3.
