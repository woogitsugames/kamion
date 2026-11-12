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

Wygenerowany GLB: LOD0 9344 → 9584 trójkąty, LOD1 2828 → 2818, LOD2 164 → 164.
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
Końcowy przebieg `after-budget`: 122 obrazy są pikselowo identyczne z baseline;
największa zmiana dotyczy remizy. Obejrzano ponownie wszystkie 24 arkusze po korekcie budżetu.
Pofałdowane cienie dachów w High-above występują również w baseline przy tym samym
pełnym przebiegu. Wczesnego fokusu z inną kolejnością kamer nie używa się do oceny tej regresji.
Wszystkie 96 warunków Low: draws siatek +0, draws instancji +0, maksymalna delta
sumy trójkątów 0,0% w statystykach zaokrąglonych do tysiąca. Dokładna delta LOD1
samej remizy wynosi -10 trójkątów. To szacunki edytora, bez deklaracji wyniku GPU.
`budget-after-budget.csv` zawiera każdą kamerę, siatki i instancje osobno.

Pełny GIS wykrył w pierwszym kandydacie przekroczenie starego limitu całego modelu
Low (2860 zamiast 2828). Nie podniesiono limitu: rdzenie trzech iglaków Low mają
pięć zamiast sześciu gładko cieniowanych boków. Oszczędność 42 trójkątów pokrywa
32 trójkąty pasa zacieków, zachowując wszystkie karty igliwia i osiem poziomów koron.
Dodano kontrolę całego Low do testu remizy. Osobny przebieg `after → after-budget`
ma 126 obrazów identycznych; największe różnice dotyczą sylwetki iglaków Low.

Mediana Y szkła Low-overcast: lewa góra/dół 64,72/66,93 → 59,93/48,86;
prawa 68,65/67,72 → 62,65/48,86. High-overcast: 71,93/74,65 → 66,65/54,86
oraz 74,79/73,93 → 68,72/54,86. Gradient góra–dół jest czytelny; High pozostaje
nieco jaśniejszy od orientacyjnego celu fotografii. Dokładne ROI: `glass-after-budget.json`.
Materiał wnętrza jest autorskim WORKING_VALUE, nie pomiarem transmisji szyby.

Wszystkie 64 wpisy chunków i roads_qa są identyczne względem świeżego baseline.
W manifeście względem świeżego baseline zmienił się tylko materiał fire_station.
Końcowy generator: 1260,6 s czasu ściennego, w tym 775 s udokumentowanej pauzy
ops-watchdog; nie jest to benchmark CPU. Bez fallback=True.
Shared shadery, globalne światło i źródła dróg nie są zmieniane.
EditMode: 261/261. Pełny GIS przed korektą: 493 passed, 2 failed, 1 xfailed (662 s).
Po korekcie i regeneracji powtórzono dwa powiązane pliki: remiza 7/7, hero building 10/10.
Własna porażka limitu jest rozwiązana. Drugą porażką był zastany stale fidelity_qa;
wszystkie siedem jego niezgodnych wejść jest niezmienionych od bazy rundy
(`stale-fidelity-proof.json`). Nie zmieniano raportu ani źródeł dróg. Nie deklaruje
się pełnego GIS jako PASS; całego zestawu nie powtarzano po lokalnej redukcji rdzeni.

Wygenerowane agregaty świata po świeżej regeneracji zawierają również odświeżenie
wcześniej nieaktualnych danych z bazy main. Ich różnice poza remizą występowały już
w świeżym baseline; dowód zachowania 64 chunków i roads_qa dotyczy porównania
baseline → kandydat. Konflikty tych agregatów przy integracji: wersja main i regeneracja.

Ocena fotografii: PARTIAL. Tuje Low mają gładkie normalne bez wzrostu geometrii,
a iglaki ciemniejsze i szersze rdzenie. Ich korony nadal mają rozpoznawalną
proceduralną sylwetkę; nie jest to fotograficzny PASS. Po wiadukcie i kominach
należy wrócić do organicznej budowy koron. Zacieki podążają za obróbką, pigment
tynku D48 pozostaje bez zmian; odwzorowanie zabrudzeń jest nadal przybliżeniem.
Telefon i niezależna recenzja pozostają po stronie lidera. Nie deklaruje się zamknięcia bramki 3.

## r3 — kominy EC Białystok

Świeży baseline po merge main 14ccbaf1 odtwarza świat bez fallback=True (575,6 s).
Runda obejmuje wyłącznie dwa landmarki istniejących overrides; life_props.py,
props.py, roads, źródła budynków i overrides.yaml pozostają poza zmianą.
Przygotowany wariant używa własnej biblioteki GLB i konfiguracji regionu,
podłączanej do istniejącego plan/apply hero. Zweryfikowana zgodność spec,
konfiguracji, wersji buildera i GLB jest warunkiem pominięcia starej instancji.
Brak lub niezgodność oznacza zachowanie starego komina. Nie dodaje się shaderów,
przebiegów ani pól QualityProfile. Finalnie trzy materiały na obu LOD zamiast czterech/trzech w baseline; Low z bliska także używa LOD0.

Źródła: Rakoon, zdjęcie 20200711 073128 Elektrociepłownia Białystok, CC BY 3.0
(lokalna kopia pomniejszona 3840×2160, oryginał 4608×2592 niezweryfikowany lokalnie);
OSM ways 628899553/554 (© OpenStreetMap contributors, ODbL);
zapytanie ENEA z maja 2025 o komin jednoprzewodowy nr 2: 120 m, góra 4,80 m,
podstawa 7,65 m; rekord wykonawcy EMKA: komin wieloprzewodowy 120 m.
Linki i atrybucja w candidate_ec_chimneys.json oraz chimney-technical-sources.json r2.
Zdjęcie EMKA obejrzano wyłącznie w cache TEMP, nie reprodukuje się go w artefaktach.
Numery zakładowe nie są numerami override. Rozpoznanie jednego/trzech wylotów
opiera się na fotografii i położeniach OSM; szczegółowe wymiary głowic są robocze.

GPS zdjęcia nie pozwalał odtworzyć obu zwieńczeń przy H=120 m. Dopasowanie
perspektywy dwóch pionowych osi i technicznej średnicy komina jednoprzewodowego
zapisuje fit_photo_pose.py/json. Roboczy najlepszy wynik: lokalnie E546,00/N−756,75,
U140,70, heading134,28°, pitch1,08°, roll0,14°, f2724 px w zdjęciu3840 px.
Nie jest to geodezyjna poza: ręczne piksele głowic, niepewna wysokość wylotów,
brak dystorsji i interpretacja obrysu OSM ograniczają wnioskowanie.
W QA pomija się mały roll, zachowuje całą wysokość zdjęcia i centralny poziomy
kadr renderu 2340→1920. Nie prostuje się kominów na podstawie ich wyglądu.

Hipoteza pełnego malowania od ziemi co15 m została odrzucona w przygotowaniu r2.
Wariant do renderu ma biały dół i pasy co12 m: pojedynczy od36 m,
wieloprzewodowy od60 m. To WORKING_VALUE z dopasowania, nie pomiar budowli.
Wysokość120 m obu i położenia poziome pozostają bez zmian. Trzon wieloprzewodowy
8,27 m przy ziemi i u góry jest WORKING_VALUE (OSM obrys + szerokość na zdjęciu),
zamiast starej roboczej góry4,8 m. Galerie i trzy wyloty mają autorskie wymiary
robocze. Finalną geometrię, PNG i wyniki końcowych testów podano poniżej.


Finalna korekta: jeden/trzy wyloty, białe galerie z pionową fascią 0,25 m,
20 segmentów trzonu High / 12 Low. Tris single 700/204 →676/292,
multi700/204 →636/274. Wszystkie61 kamer × Low/High × clear/overcast:
244 pary,95 identycznych PNG; obejrzano32 arkusze. Low122 pomiary,
draws mesh i instanced osobno +0, całkowite tris od−0,3185% do+0,3718%.
To estymaty generatora, nie pomiar GPU ani telefonu. Pierwszy wariant przekroczył
budżet dwóch zbliżeń i miał znikające galerie; nie jest wariantem do integracji.
Końcowy odczyt macierzy WorldInstances.SyncOrigin: obie osie0°, po3 submeshe
na każdym LOD, progi650/20000. XY/yaw zachowane; Z+3/+9 mm względem baseline.
125468 instancji poza EC i roads_qa identyczne. Przy równoległej korekcie podpomostu
potwierdzono7283 pozostałe prymitywy bajtowo we wszystkich128 chunkach;
nie deklaruje się identyczności całych GLB po zmianie farby i usunięciu plam.
Klasyfikacja czerwone/nie-czerwone w stałych oknach Low-overcast:
multi49,0→21,1%, single55,5→0,0%. Próg chromy i poza robocza ograniczają miarę.
Fotografia nadal PARTIAL: materiał kominów za szary/jednolity, szczegóły głowic
oraz średnica multi robocze. Zdjęcie Rakoon CC BY3.0, starsze Hiuppo CC BY-SA2.5;
EMKA tylko tekst H120m jako źródło techniczne, bez zamkniętych fotografii w pakiecie.

Testy końca r3: EC 18/18, podpomost 15/15, EditMode 317/317,
physics/gate3 48/48 PASS. Pełny GIS 643 PASS, 1 XFAIL, 1 FAIL (720,55 s):
tylko test_report_not_stale dla overrides.yaml i roads/meshing.py. Dowód
stale-fidelity-proof.json potwierdza oba pliki niezmienione od bazy 14ccbaf1;
nie modyfikowano źródeł ani raportu dróg. Nie deklaruje się pełnego GIS PASS.
192 pliki cache (64 High, 64 Low, 64 instancje) zgodne z manifestem przed i po
teście; wszystkie źródła i assety objęte kontrolą niezmienione od finalnego renderu.


## r4 — korony iglaków remizy (przygotowanie)

Baza main b23b4df7 włączona przez merge e0fa8a6d. W konfliktach materiałów
potwierdzono identyczny AST obu helperów podpór; zachowano nowe materiały life
oraz kolejność bloków main. Dane wygenerowane przyjęto z main do regeneracji.
Ta runda pozostaje przy trzech iglakach JRG2; nie obejmuje globalnej roślinności.

Zdjęcie CC0 7197 pokazuje przerwy między nieregularnymi poziomymi gałęziami.
W natywnym zbliżeniu r3 dominują pełne, równe półki szerokiego rdzenia.
Hipoteza próby: cztery węższe pierścienie zamiast ośmiu szerokich, odzyskane
trójkąty na mniejsze i liczniejsze karty gałęzi. Liczba kart 12→32 na Low,
54→86 na High, bez zwiększenia 98/224 trójkątów na każde drzewo.
W lekkim doświadczeniu na rzeczywistych kluczach spec pole kart wyniosło
0,829/0,932/0,888 dotychczasowego pola na Low i 0,767/0,759/0,777 na High.
Pierwszą szerokość Low odrzucono przed wdrożeniem: zwiększała pole do 1,38×.
To pole powierzchni 3D, nie ekranowe nakładanie alfa ani koszt GPU.

Model produkcyjny nie został jeszcze zmieniony, baseline czeka w kolejce FIFO.
Próba wymaga renderu i porównania z fotografią; w razie regresji zostanie odrzucona.
Przygotowany audyt GLB ma ochronić wszystkie trójkąty poza trzema koronami,
progi i liczbę LOD oraz sylwetkę LOD2. Pigment tynku D48 i atlasy bez zmiany.

Wariant A odrzucono po podglądzie wszystkich ośmiu PNG (Low/High overcast,
cztery kamery). Cztery wąskie pierścienie i boczne karty dały cienki stożek
z płaskimi klinami i trójkątnymi otworami. Zachowane archiwum variants/a,
REJECTED-A.md i pary fotograficzne; techniczny audyt nie był akceptacją obrazu.
Waiter pojedynczego pliku GIS anulowany przed uzyskaniem heavy, bez uruchomienia
pytest; nie zatrzymano żadnego generatora ani cudzego procesu.

Próba B zachowuje pierwotne 12/54 karty, ich położenia, orientacje i UV, więc
nie zwiększa powierzchni alfa. Rdzeń ma osiem pierścieni, ale ich promienie
zależą od azymutu, a wysokości narożników są przesunięte wewnątrz bezpiecznej
części odstępu poziomów. Normalne wynikają z rzeczywistej powierzchni.
Konfiguracja jest WORKING_VALUE; trójkąty planowane jak w baseline, wynik obrazu
jeszcze nieznany. Atlas, tynk i rozmieszczenie zieleni pozostają bez zmian.
