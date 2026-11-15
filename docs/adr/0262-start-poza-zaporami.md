# ADR 0262 — start regionu za zamknięciem krawędzi kafla, nigdy w zaporach
Status: Proposed (agent `spawn-fix-0262`, s22, gałąź `spawn-fix-0262`), 2026-11-15. Do weryfikacji i scalenia przez lidera.
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
   `startS` = 60 + 25 = **85 m** (największe możliwe odsunięcie zamknięcia + zapas), inaczej 12 m; nadal z zapasem
   `MIN_AHEAD_M` = 100 m do końca trasy. Dokładna geometria zamknięć nie jest kopiowana do Pythona (ADR 0169 p. 2) —
   sędzią jest test EditMode na prawdziwych zamknięciach. `route_start.json` i dane regionów się nie zmieniają.
   W dk65-05 start 85 m wypada za skrzyżowaniem z wysepką (zamknięcie 14 m, skrzyżowanie tuż za nim).
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

## Otwarte
1. **300 m wolnej trasy**: dk65-09 (trasa 352 m) i dk65-11 (378 m) mają po starcie 85 m tylko ~267 / ~293 m trasy;
   na tym odcinku nie ma zamknięcia, ale wymóg „≥ 300 m” jest tam spełniony tylko jako „do końca trasy”.
2. Sceny w APK d67-full są zapieczone ze spawnem 12 m; poprawny start daje katalog (menu) i bezpiecznik (każda ścieżka).
   Kamery kontrolne `truck-at-gate` / `cab-gate` przesuną się dopiero po reimporcie regionu.
3. Regiony przebudowywane równolegle (dk65-06…11, knyszyn-s — `dk65-r4-s21`; C, Dojlidy — `c-regen-s22`;
   dw671-tykocin-01 — `rail-fix-s21`): po ich scaleniu `python scripts/export-region-catalog.py` (zmiana
   `route_start.json` zmienia `routeLengthM`) i testy z tego ADR. Możliwy konflikt w `region_catalog.json` — rozwiązać
   przez ponowne uruchomienie eksportera.
4. `BehindClosureM` = 25 m i 85 m startu to WORKING_VALUE — ocena właściciela na telefonie.
5. Telefon: niemierzone.
