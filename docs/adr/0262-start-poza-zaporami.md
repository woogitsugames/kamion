# ADR 0262 — start regionu za zamknięciem krawędzi kafla, nigdy w zaporach
Status: Accepted — kod w main `5f51007ee` (s23, recenzja `docs/reports/REVIEW-2026-11-15-s23-code-spawn-fix-0262.md`: SCAL warunkowo); oględziny 20/20 regionów i sekcja „Wyniki” uzupełnione 2026-11-16 (agent `spawn-fix-0262`).
Powiązane: ADR 0229 (wybór regionu, `region_catalog.json`, `startS`), ADR 0169 (jedno źródło zamknięć krawędzi kafla,
60 m w głąb), ADR 0082 (`WorldBoundary`, siatka bezpieczeństwa), ADR 0214/0215 + D65 (plac budowy S19, stara DK65).

## Kontekst
Zgłoszenie właściciela (A16, APK d67-full z main `52188a91f`, 15.11): „wszystkie starty są takie: z tyłu koniec drogi,
z przodu bloki”; w jednym regionie ciężarówka stoi w rzędzie zapór betonowych z biało-czerwonymi deskami, naczepa
wyrzucona w górę (`artifacts/owner-a16-s22/3.webp`).

Przyczyna jest jedna dla wszystkich regionów (sprawdzone na danych 21 regionów katalogu):
- trasa startowa kafla korytarza (`route_start.json`) zaczyna się **na krawędzi kafla** (pierwszy węzeł = `boundary`);
  tak jest w 20 z 21 regionów, wyjątkiem jest region C (start w bazie, w środku kafla);
- importer zamyka każdą drogę przeciętą krawędzią kafla rzędem zapór + deskami U-20, odsuniętym od krawędzi
  (`WorldEdgeBuilder.ClosureSetbackM` = 60 m, na krótkiej krawędzi grafu 80 % jej długości, ADR 0169). Deski stoją od
  strony wnętrza kafla — zamknięcie jest pomyślane dla kierowcy nadjeżdżającego od środka;
- start był stały: 12 m od początku trasy (`RegionStart.DefaultStartS`, `WorldSceneBuilder spawnS`, katalog ADR 0229),
  czyli **po zewnętrznej stronie zamknięcia**. Zmierzone stacje zamknięcia na trasie: 60 m w 16 regionach, 54 m
  (dk65-06, knyszyn-w), 20 m (bialystok-knyszynska), **14 m (dk65-05 — ciągnik w rzędzie zapór, zrzut właściciela)**.

Odrzucone hipotezy: odwrócony kierunek trasy (drugie zamknięcie stoi przy `length − 60`, trasy biegną od krawędzi do
krawędzi); zapory placu budowy D65 (`construction_site` to piasek i hałdy w terenie oraz siatka poza pasem 4 m od dróg;
trasy nie używają dróg wyciętych z grafu — test). Przed ADR 0229 w APK był tylko region C, więc błędu nie było widać.

## Decyzja
1. **Reguła** (`Game.World.StartClearance`, czysta geometria w układzie regionu): start stoi za każdym zamknięciem,
   przez które trasa **wjeżdża** do kafla (kierunek trasy przeciwny do kierunku drogi „ku krawędzi”), co najmniej
   `BehindClosureM` = 25 m dalej wzdłuż trasy (WORKING_VALUE: tył naczepy 13,7 m za rzędem zapór). Obrys zestawu z
   definicji pojazdu: przód ciągnika +5,15 m, tył naczepy −11,30 m od punktu startu, szerokość 2,55 m, zapas 0,5 m
   (test pilnuje zgodności z `TractorDimensions`, `TrailerDimensions` i JSON-ami fizyki).
2. **Źródło danych: katalog.** `scripts/export-region-catalog.py`: gdy pierwszy węzeł trasy jest `boundary`,
   `startS` = 60 + 25 + 5 = **90 m** (największe odsunięcie zamknięcia + zapas + 5 m na skośny rząd: pas ruchu
   przecina go do 1,2 m dalej niż oś drogi, zmierzone w bialystok-maczka), inaczej 12 m; nadal z zapasem
   `MIN_AHEAD_M` = 100 m do końca trasy. Dokładna geometria zamknięć nie jest kopiowana do Pythona (ADR 0169 p. 2) —
   sędzią jest test EditMode na prawdziwych zamknięciach. `route_start.json` i dane regionów się nie zmieniają.
   W dk65-05 start 90 m wypada za skrzyżowaniem z wysepką (zamknięcie 14 m, skrzyżowanie tuż za nim).
3. **Importer** (`WorldSceneBuilder`): zapieczony spawn sceny = `startS` z katalogu, a potem `SafeStartS` na
   zamknięciach zbudowanych w tym samym imporcie (ostrzeżenie w logu, gdy katalog jest nieaktualny). Kamery kontrolne
   `truck-at-gate` / `cab-gate` idą za spawnem.
4. **Bezpiecznik w runtime** (`Game.Gameplay.SpawnSafety`, `DrivingLabBootstrap.ResolveRouteStart`), raz na start /
   respawn, nie w pętli jazdy: (a) `SafeStartS` na `WorldBoundary.closures` sceny — naprawia też sceny zapieczone przed
   tym ADR i start z `scene=<id>` bez menu (zapieczony punkt 12 m); (b) pudło zestawu (0,5 m zapasu, od 0,5 do 4,0 m
   nad jezdnią, pochylone wzdłuż drogi) sprawdzane `Physics.OverlapBoxNonAlloc` (stały bufor, bez wyzwalaczy, bez
   colliderów pojazdu); zajęte → przesuwanie wzdłuż trasy co 2 m, najdalej 200 m, do pierwszego wolnego miejsca.
   Każde przesunięcie = `LogWarning [START] start moved along the route: route_s a -> b (powód)`; brak wolnego miejsca =
   `LogError` i start w miejscu po kroku (a). Log `[START] region=…` pokazuje `route_s` po przesunięciu.
5. Jedna stała 12 m: `StartClearance.DefaultStartS` (`RegionStart.DefaultStartS` wskazuje na nią).

## Budżet
Draws/tris: bez zmian (żadnej nowej geometrii). Runtime: jednorazowo przy starcie ≤ 101 zapytań `OverlapBoxNonAlloc`
+ jedno przejście po polilinii trasy na zamknięcie; zero pracy i zero alokacji w pętli jazdy. Telefon: niemierzone
(zadanie bez adb).

## Walidacja
- `tests/gis/test_start_clear_0262.py` (44 przypadki: katalog = wynik eksportera, start za zamknięciem dla tras od
  krawędzi, pierwsze 300 m bez dróg zamkniętych / w budowie / wyciętych z grafu). Na katalogu z main: **21 failed**
  (`artifacts/spawn-fix-0262/pytest-red-main-catalog.log`).
- EditMode `StartClearanceTests`: obrys z definicji pojazdu; geometria syntetyczna; dla każdego regionu katalogu
  (a) start za zamknięciem wjazdowym z zapasem ≥ 0,5 m do desek, (b) brak rzędu zapór na trasie przez 300 m przed
  zderzakiem; kategoria `WorldScenes`: w zaimportowanej scenie pudło zestawu w punkcie startu nie dotyka żadnego
  collidera, a ciągnik przesuwany po trasie przez 300 m nie trafia na nic na jezdni (region bez sceny = pominięty).
- Wyniki przebiegów i rendery: sekcja „Wyniki” niżej.

## Wyniki (2026-11-16)
Źródła liczb: stacje zamknięć — `artifacts/spawn-fix-0262/editmode-red.log` (prawdziwe `ResolveClosures`, przebieg sprzed
scalenia z main; po nim zmieniły się tylko trasy dk65-11 i knyszyn-s, po 1 linii `route_start.json`); `startS` i długość
trasy — `region_catalog.json` po scaleniu `origin/main` (`1311c25de`). „Wolne” = stacja zamknięcia wyjazdowego (albo
koniec trasy, gdy trasa nie wychodzi przez zamknięcie) minus `startS`; od zderzaka 5,15 m mniej. Rendery edytora:
reimport Low + kamery `truck-at-gate` / `cab-gate` (clear, 1280×720) w worktree na `221a30be4` (przed scaleniem),
20/20 `import=0 qa=0` (`artifacts/spawn-fix-0262/renders/<id>.status`, arkusze `renders/_sheets/<id>.jpg`).
Wszystkie 20 par obejrzane.

| Region | Zamknięcie wjazd. [m] | Wyjazd. [m] | startS [m] | Trasa [m] | Wolne [m] | Render edytora (oględziny) |
|---|---|---|---|---|---|---|
| bialystok-industrial-c | brak | brak (szlaban bazy 244) | 12 | 2397,47 | — | bez renderu w tym zadaniu; zrzut exe OK |
| bialystok-maczka | 61,2 | 1993,8 | 90 | 2054,08 | 1903,8 | OK; zestaw na obiekcie z barierami, w kadrze widać deski drogi bocznej poniżej — własne zamknięcie zasłania zestaw (potwierdza je liczba, nie obraz) |
| bialystok-kleeberga | 60,0 | 2161,0 | 90 | 2221,20 | 2071,0 | OK; zapory za naczepą; zestaw stoi na lewym z trzech pasów jezdni (trasa nie biegnie prawym pasem) |
| bialystok-knyszynska | 20,8 | 2902,2 | 90 | 2961,35 | 2812,2 | OK; zapory daleko z tyłu; zestaw na pasie ze strzałką „prosto”, nie na skrajnym prawym |
| dk65-01 | 60,0 | 571,6 | 90 | 631,76 | 481,6 | OK |
| dk65-02 | 60,0 | 2340,7 | 90 | 2400,68 | 2250,7 | OK |
| dk65-03 | 60,0 | — | 90 | 484,43 | 394,4 (koniec trasy) | OK |
| dk65-04 | 60,0 | 2074,5 | 90 | 2079,43 | 1984,5 | OK; przed kabiną z lewej wlot drogi bocznej z wysepką |
| dk65-05 | 14,5 | 2141,9 | 90 | 2201,88 | 2051,9 | OK; rząd zapór 75,5 m (stacje 14,5 → 90) za punktem startu, start za skrzyżowaniem z wysepką, wiata po prawej |
| dk65-06 | 54,6 | 1641,8 | 90 | 1701,95 | 1551,8 | OK z uwagą: start na wlocie ronda (węzeł ~9 m przed zderzakiem wg recenzji), przed kabiną wyspa ronda; przejazd wolny, ale to nie prosta |
| dk65-07 | 60,0 | 862,4 | 90 | 865,60 | 772,4 | OK; przed kabiną z lewej wlot drogi bocznej |
| dk65-08 | 60,0 | 2295,1 | 90 | 2355,15 | 2205,1 | OK |
| dk65-09 | 60,0 | — | 90 | 352,36 | 262,4 (koniec trasy) | OK; < 300 m, bo trasa się kończy |
| dk65-10 | 60,0 | 2555,4 | 90 | 2615,35 | 2465,4 | OK |
| dk65-11 | 60,0 (stara trasa) | — | 90 | 377,82 | 287,8 (koniec trasy) | OK; < 300 m, bo trasa się kończy |
| knyszyn-s | 60,0 (stara trasa) | 2360,7 | 90 | 2420,72 | 2270,7 | OK |
| knyszyn | 60,0 | — | 90 | 1159,85 | 1069,9 (koniec trasy) | OK |
| knyszyn-w | 53,9 | 1928,7 | 90 | 1988,70 | 1838,7 | OK; w dolnej krawędzi kadru kamery zewnętrznej obiekt tuż przy kamerze (kosmetyka kamery kontrolnej) |
| dk65-monki-01 | 60,0 | 1125,0 | 90 | 1185,04 | 1035,0 | OK |
| dw671-tykocin-01 | 60,0 | 2567,3 | 90 | 2608,56 | 2477,3 | OK; wąska jezdnia, zestaw na prawej połowie |
| bialystok-dojlidy | 60,3 | 2129,9 | 90 | 2133,17 | 2039,9 | OK; trasa kończy się 3,3 m za rzędem wyjazdowym (nie na krawędzi kafla) |

W każdym z 20 renderów: zestaw stoi na jezdni w osi pasa, rząd zapór z deskami jest za naczepą (albo zasłonięty —
maczka), przed kabiną nie ma zapór ani przeszkód na pasie do granicy widoczności. Wymóg „≥ 300 m wolnej trasy”
potwierdza test `WorldScenes` (ciągnik przesuwany 300 m po trasie bez collidera) — zielony 61/61 w przebiegu sprzed
scalenia (`artifacts/spawn-fix-0262/editmode-green.xml`); przebieg lidera `artifacts/int-pc-s23/editmode-20261115-225152.xml`
(730/731) nie zawiera `StartClearanceTests`. Przebieg po scaleniu: patrz niżej „Po scaleniu”.

**Exe Windows** (`artifacts/int-pc-s23/starts/`, build `cc3e1ee900-dirty`, High, start `scene=<scena>` bez menu,
7 zrzutów obejrzanych): bialystok-industrial-c, bialystok-dojlidy, dk65-05, dk65-11, knyszyn-s, knyszyn,
dw671-tykocin-01 — 7/7 droga przed kabiną wolna; w lusterkach tykocina i dk65-11 widać zapory za zestawem; kadr
dk65-05 zgadza się z renderem edytora z 90 m (ta sama wiata i bariera). Tykocin (scena zapieczona ze starym spawnem)
uratował bezpiecznik: log `start moved along the route: route_s 12.0 -> 85.0 (region-edge closure on the route)` —
runtime daje wjazd + 25 = 85 m, katalog/menu 90 m.
**Uwaga do logów:** w pozostałych sześciu logach linia `[START] region=… route_s=12.0 en=…` NIE jest pozycją startu:
`DrivingLabBootstrap.LogRegionStart` przy starcie z zapieczonego spawnu (bez `route_s`, bez przesunięcia) wypisuje
`DefaultStartS` = 12 m i z niego liczy `en`. Dowodem pozycji są zrzuty, nie ta linia.

**Po scaleniu `origin/main` (`1311c25de`), 2026-11-16** — w worktree, z poprawkami z punktu niżej:
EditMode `StartClearanceTests` + `RegionSelectTests` 61/61, skipped 0 (`artifacts/spawn-fix-0262/editmode-post-merge.xml`,
w tym kategoria `WorldScenes` na 21 scenach zaimportowanych w worktree); PlayMode `RouteSpawnTests` 5/5
(`editmode-playmode-post-merge.xml`); pytest `tests/gis/test_start_clear_0262.py` 44 passed (`pytest-post-merge.log`).
Sceny dk65-11 i knyszyn-s w worktree były importowane przed scaleniem (trasa sprzed zmiany 1 linii).

**Poprawki po recenzji (commit po `5f51007ee`, do scalenia przez lidera):**
- P2-1 (wąsko, tylko `SpawnSafety.ResolveStartS`; `StartClearance.SafeStartS`, importer i katalog bez zmian): start żądany
  bliżej niż `BehindClosureM` = 25 m przed rzędem wyjazdowym albo za nim cofa się na `stacja wyjazdu − 25 m`, a szukanie
  wolnego miejsca nie wychodzi poza tę granicę; powód w logu `region-edge closure ahead on the route`. Test PlayMode
  `RouteS_AtOrPastTheExitClosure_MovesBackInFrontOfIt` (230 m i 290 m przy wyjeździe 240 m → 215 m; 120 m bez zmian).
- Log `[START] region=…` przy starcie z zapieczonego spawnu wypisuje stację spawnu (`NearestRouteS`), nie domyślne 12 m.
  Bez osobnego testu (kompilacja + zielone przebiegi wyżej); do potwierdzenia w logu następnego exe.

## Otwarte
1. **300 m wolnej trasy**: dk65-09 (trasa 352 m) i dk65-11 (378 m) mają po starcie 90 m tylko 262 / 288 m trasy;
   na tym odcinku nie ma zamknięcia, ale wymóg „≥ 300 m” jest tam spełniony tylko jako „do końca trasy”.
2. **Binaria**: APK d67-full i exe zbudowane przed `5f51007ee` nie są naprawione — potrzebny nowy build (recenzja P2-7).
   Nowy build ze starymi scenami naprawia runtime (menu: katalog 90 m; start bez menu: bezpiecznik → wjazd + 25 m, jak
   tykocin 12 → 85). Kamery kontrolne `truck-at-gate` / `cab-gate` i zapieczony spawn 90 m wymagają reimportu regionu.
3. Po każdej zmianie `route_start.json`: `python scripts/export-region-catalog.py`, pytest i EditMode z tego ADR.
4. `BehindClosureM` = 25 m i 90 m startu to WORKING_VALUE — ocena właściciela (PC / telefon).
5. Telefon: niemierzone (D73; zadanie bez adb). Exe: pozycja startu potwierdzona zrzutami, wydajność niemierzona tutaj.
6. Uwagi z oględzin, poza zakresem tego ADR (dane tras): dk65-06 start na wlocie ronda; bialystok-kleeberga i
   -knyszynska trasa nie biegnie skrajnym prawym pasem; knyszyn-w obiekt w kadrze kamery `truck-at-gate`.
7. Z recenzji, nie zrobione: P2-2 (brak wolnego miejsca = start w kolizji z `LogError`, brak szukania wstecz), P2-3
   (`SafeStartS` bierze maksimum po wszystkich wjazdach), P2-4 (trasy < 190 m), P2-5 (test ścieżki starej sceny bez
   menu), P2-6 (test zapieczonego spawnu importera), P2-8 (pudło proste na łuku), P2-9 (bufor 128).
