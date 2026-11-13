# P4 — truck-regulations: wymagania przepisów dla fikcyjnego ciągnika siodłowego 4×2 (N3) + naczepy firanki 13,6 m, 3 osie (O4)

## Cel
Zebrać wymagania prawne wpływające na wygląd pojazdu i widok z kabiny dla gry „Kamion": rozmieszczenie świateł i odblasków (EKG ONZ R48), oznakowanie odblaskowe (R104, R70), lusterka (R46), osłony przeciwwjazdowe (R58, R73), wymiary i masy (96/53/WE), polskie warunki techniczne (tablice rejestracyjne, tabliczki znamionowe, tablice wyróżniające, tachograf, gaśnica, trójkąt) oraz tablice kierunkowe/ostrzegawcze spotykane w PL. Każda wartość z kategorią pojazdu (N3/O4), warunkiem i jednostką.

## Metoda
- Źródła: pełne teksty regulaminów EKG ONZ (R48 Rev.12, R46 Rev.5) pobrane z serwera UNECE przez Wayback Machine (https://web.archive.org, zapis URL z timestampem w manifest.csv); R58/R73/R104 z Dziennika Urzędowego UE (EUR-Lex/CELLAR, wydania z pełną serią poprawek); dyrektywa 96/53/WE w tekście skonsolidowanym z 2019-08-14; polskie akty prawne z API ELI Sejmu (api.sejm.gov.pl, teksty jednolite Dz.U. 2024).
- Każda liczba zweryfikowana greppem w pełnym tekście źródłowym; cytat ≤ 25 słów z numerem punktu. Cytaty EN z regulaminów EKG ONZ, PL z aktów polskich — dosłowne.
- Teksty PDF dekodowane własnym ekstraktorem (mapy ToUnicode CMap, 2-bajtowe CID) — pełne teksty w files/.
- Licencje: wszystkie dokumenty urzędowe — art. 4 ust. 1 ustawy o prawie autorskim i prawach pokrewnych (Dz.U. 1994 nr 24 poz. 83); brak praw autorskich do materiałów urzędowych (orzecznictwo SN, TSUE). Wszystkie pliki w files/ to dokumenty urzędowe — dozwolone w grze komercyjnej. Brak zdjęć w paczce (paczka normatywna), więc sezon/pora dnia nie dotyczy.
- Wersje regulaminów podane w kolumnie wersja_przepisu (seria poprawek + data), np. R48 seria 06 poprawek Rev.12 (2015).

## Najważniejsze ustalenia (dla modelarzy)
- **Ciągnik siodłowy N3 — kluczowe WYJĄTKI**: nie wymaga tylnego i bocznego oznakowania konturowego R104 (WT §12.1 pkt 17 lit. a/b wprost wyłączają ciągnik siodłowy; R48 6.21), nie wymaga tablic wyróżniających (WT §42.1 „z wyłączeniem ciągnika siodłowego"), nie podlega R58 (pkt 1.2.1 „Tractive units for articulated vehicles"). Ale: odblaski boczne są wymagalne wprost na ciągniku siodłowym (WT §12.1 pkt 11 wymienia go z nazwy).
- **Naczepa O4**: pełny kontur odblaskowy z tyłu + częściowy bok (R48 6.21.1), tablice wyróżniające żółto-czerwone z tyłu (WT §42 + zał. 10: tło żółte odblaskowe, obrzeże czerwone fluorescencyjne; dolna ≥250 mm, górna ≤2100 mm, ≤400 mm od obrysu), trójkątne odblaski tylne wierzchołkiem do góry (R48 6.15.3), 2 światła cofania obowiązkowe (R48 6.4.1/6.4.2.2 — naczepy O2/O3/O4 >6 m).
- **Lusterka (R46, N3)**: klasa II główne obowiązkowe 1+1; klasa IV szerokokątne 1+1; klasa V bliskiego widzenia 1+1 (montaż ≥2 m); klasa VI przednie 1 szt. ≥2 m; klasa I wewnętrzne na N3 OPCJONALNE; klasa III zakazana.
- **Wymiary (96/53/WE)**: pojazd przegubowy 16,50 m; szer. 2,55 m; wys. 4,00 m; sworuń–tył naczepy 12,00 m; zespół 40 t (44 t intermodalnie); oś napędowa 11,5 t.
- **Tablica rejestracyjna tylna (WT zał. 5)**: miejsce 520×120 mm, dolna krawędź ≥0,30 m, górna ≤1,20 m (absolutnie ≤2 m), środek nie na prawo od płaszczyzny symetrii.
- **Tachograf**: obowiązek z ustawy o transporcie drogowym (kara 10 000 zł, zał. kar poz. 6.1.1); WT wymaga go tylko dla autobusów i nauki jazdy.
- **Kliny pod koła: brak wymogu** w polskich warunkach technicznych (0 trafień słowa „klin" w całym tekście jednolitym — negative finding).
- **Znak „80/90" na naczepie: brak podstawy prawnej** w PL — jeśli widoczny na realnych pojazdach, jest oznaczeniem umownym (UNVERIFIED).
- **Beacon żółty**: tylko pojazdy czynności na drodze/pomocy drogowej — zwykły cargo go nie ma (WT §38).

## Tabela R48 „element → liczba → wysokość → odległość od krawędzi → kolor"
Kompletna tabela rozbита na wiersze manifestu: ciągnik N3 — P4-015…P4-052; naczepa O4 — P4-053…P4-079 (element, liczba obowiązkowa, min/max wysokość nad jezdnią, odległość od krawędzi, kolor w kolumnach: element / wartość / jednostka / warunek / cytat + wiersze kolorów P4-011…P4-014).

## Braki i niepewności (UNVERIFIED)
1. **P4-153**: wymiar tablicy jednorzędowej 520×114 mm figuruje na rysunku 1 rozporządzenia (obraz, bez warstwy tekstowej) — pośrednio potwierdzone miejscem 520×120 (WT zał. 5 §2.1).
2. **P4-156**: umiejscowienie tachografu w kabinie (zał. IB rozp. 3821/85) — załącznik niedostępny (EUR-Lex za WAF, Archive offline w czasie zbierania).
3. **P4-158**: znak ograniczenia 80/90 na naczepie — brak podstawy prawnej w WT/PoRD.
4. **P4-160**: oznaczenia kierunkowe „promilowe" — brak podstawy prawnej.
5. Pełny tekst R70 (tylko Supplement 9 serii 01 w pliku P4-010) — wymiary tablic ostrzegawczych wzięto z WT zał. 10 (dokument polski urzędowy).
6. **Kontekst wersji**: dyrektywa 96/53/WE zostanie zastąpiona rozporządzeniem (UE) 2024/5450 — dane z tekstu skonsolidowanego 2019-08-14; najnowszy konsolidat UTD (Dz.U. 2025 poz. 1490) jest skanem bez warstwy tekstowej, użyto Dz.U. 2024 poz. 1539.

## Samokontrola (20%)
- Seed: **20261113** (python3 random.seed; random.sample z 161 pozycji).
- Wylosowano 33/161 pozycji (20,5%) — wszystkie kategorie manifestu, nie tylko pobrane pliki.
- Metoda: grep wartości/cytatu w lokalnych pełnych tekstach źródłowych + kontrola plików w files/ + spójność pól; linki api.sejm.gov.pl sprawdzone live (HTTP 200); linki Wayback/EUR-Lex zweryfikowane pośrednio (pliki pobrane z tych URL przed awarią Archive, treść zgodna).
- Wynik: **33/33 OK (100%)**, korekty: 0. Szczegóły: audit_20_percent.json. Uwaga metodyczna: 7 pozycji wymagało grepa z artefaktami ekstrakcji PDF (podwójne spacje, rozdzielone łączniki typu „Side -marker").

## Zawartość paczki
- `manifest.csv` — 161 wierszy (P4-001…P4-161): 10 plików źródłowych (P4-001…010), 151 pozycji normatywnych; kolumny wg zadania + url_źródła, licencja, autor, data_dostępu, status, uwagi.
- `files/` — 10 dokumentów urzędowych (PDF ≤5 MB / HTML); tach_799.pdf (19,5 MB, rozp. 2016/799) celowo NIE w ZIP (>5 MB) — tylko referencja w manifeście (P4-155).
- `sources.md`, `audit_20_percent.json`, ten README.
