# gptpro-p7-s8-signs-2 — badanie znaków drogowych, rejon Białegostoku (uzupełnienie paczki G3)

Data wykonania: **2026-11-13** (wszystkie daty dostępu). Paczka uzupełnia G3
(`research/gptpro/3-s8-signs`, 152 pozycje) o: (1) oś czasu bramownic przy
rondzie Putry, (2) drugi sezon dla tablic korytarza północnego, (3) recheck
25 pozycji G3, (4) kontekst urzędowy zmian oznakowania 2026 (S19/S8/DK65).

## Cel

Dostarczyć zespołowi gry Kamion zweryfikowane fakty o treści, geometrii
i historii oznakowania kierunkowego w rejonie Białegostoku, z datami,
źródłami i jawnym oznaczeniem pewności (SOURCED/ESTIMATED/UNVERIFIED),
bez dublowania pozycji już obecnych w G3.

## Metoda

- **Mapillary Graph API** (publiczny token odczytu): metadane kadrów przez
  zapytania bbox (endpoint `/images/{id}` i `?ids=` od 13.11.2026 nie odpowiada),
  miniatury `thumb_1024` (1024 px ≤ limit 1600 px). Kadry Mapillary w paczce
  służą **wyłącznie jako referencja** (CC BY-SA 4.0, zasada share-alike —
  patrz LICENSE-DATA.md).
- **Analiza wizyjna** kadrów (model wizyjny), każdorazowo ze weryfikacją
  względem odczytów G3 i z adnotacją rozbieżności.
- **Selekcja kadrów po nagłówku kamery**: dopasowanie azymutu kamery do
  azymutu kamery→tablica (tolerancja ±30°, dystans ≤260 m). UWAGA metodologiczna:
  dla kadrów użytkownika quickness805 `compass_angle` odbiega o ~90° od
  `computed_compass_angle` (obrócone mocowanie kamery) — w P7 używano
  `computed_compass_angle`.
- **Wikimedia Commons**: plik CC0 (Rakoon) pobrany jako miniatura serwerowa
  1280 px.
- **OpenStreetMap/Overpass** (ODbL): geometria dróg i węzły skrzyżowań do
  lokalizacji kandydatów (instance overpass.private.coffee).
- **Dokumenty urzędowe**: komunikaty GDDKiA i wykonawcy PORR/UNIBEP (klauzule
  organizacji ruchu) — tylko linki (fotografie w stopkach CC BY-NC-ND).
- Zakazane źródła (Google Maps/Street View/Earth) — nieużyte.

## Ustalenia (wypunktowane)

### Oś czasu oznakowania przy rondzie Putry (P7-001…P7-006)

- **Bramownica A** (ul. Andersa, przed rozdzieleniem na estakadę DK8 i łącznicę
  do ronda): układ stabilny 2018–2024. Prawa tablica: „8 E 67 Augustów /
  19 Kuźnica PL BY"; **„675 Centrum" jest na OSOBNEJ małej tablicy pod główną**
  (obecność potwierdzona odczytem SOURCED G3-P005, 2024). W 2020 kartusz 675 był
  czytelny (P7-001, odczyt z 2020 r.), ale reanaliza na miniaturze 1024 px
  (2026-11-13) nie potwierdziła czytelności — oznaczono UNVERIFIED. W 2024
  kartusz jest automatycznie rozmyty (P7-002, jak G3-P013).
  → **Gra `andersa-putry-approach-gantry` wymaga poprawy GEOMETRII (dwie tablice,
  nie jedna), nie treści.**
- **Wysięgnik B** (łącznica Maczka–Putry): istniał z tablicami w 2018
  (czadzik, kadr 1240467703063612) i 2020-08-15 (P7-003: E67 Warszawa,
  E67 Augustów, 19 Kuźnica, Centrum — reanaliza 2026-11-13 potwierdziła).
  W 2024-07-26 **brak tablic i brak widocznej konstrukcji** (P7-004,
  potwierdzone 3 kadrami kino). Oznakowanie łącznicy zdemontowano między
  2020-08-15 a 2024-07-26; dokładna data UNVERIFIED.
  → Gra odwzorowująca wysięgnik B pokazuje stan sprzed usunięcia.
- **Portal C** (przed rondem Putry od łącznicy): **nie istniał w latach
  2017–2020-08** (P7-005 + 7 dodatkowych kadrów 2017–2020). **Powstał między
  2020-08-15 a 2021-05-03** (P7-006: Commons 03.05.2021, lewy dolny panel
  „675 Centrum" zaklejony czarną taśmą — świeży montaż; najpewniej wiosna 2021).
  W 2024-07-26 portal ma 4 czyste panele zgodne z G3-P001–P004.
  → W grze stan portalu C jest właściwy dla epoki 2021–2024; nie dla ≤2020.
- Numer decyzji ZDM o zmianie oznakowania (wiosna 2021) **nieustalony** —
  rejestr organizacji ruchu nie jest publikowany online (ZDM-REJESTR w sources.md).

### Drugi sezon — korytarz północny (P7-007)

- Tablica **E-1** przed rozjazdem DK8/DK19 (Wasilków; G3-MN005, kino,
  2024-07-26) potwierdzona kadem quickness805 z **2024-09-01** (11 m od pozycji
  kamery G3): ta sama tablica istnieje miesiąc później; odczyt z miniatury
  częściowy (Augustów, E 67) — pełny odczyt pozostaje w G3-MN005.

### Recheck 25 pozycji G3 (mapillary_recheck.csv)

- **24× TAK + 1× TAK z zastrzeżeniem** (G3-MC004: kierunek_deg ESTIMATED własną
  metodą G3 vs computed_compass_angle API — różnica 29,5° wynika z metody, nie błędu).
- Zgodność: klucz, data zdjęcia (± format pełnego timestampu ISO), współrzędne
  (max Δ=0 m), autor, kierunek (vs computed_compass_angle).

### Nowe obszary (DK19 SE, DK65 E, DK8 N, S19, S8) — wynik negatywny

- **16 kadrów 2024 r.** przeanalizowanych wizyjnie przy 10 skrzyżowaniach/węzłach
  (ronda DK19/DK65/DW676, Grabówka, wylot DK19, węzeł Białystok Zachód,
  łącznice DK19/DK8): **na żadnym nie stwierdzono tablic kierunkowych
  E-1/E-2/E-3/E-4** poza obiektami już udokumentowanymi w G3 (seria
  G3-MLY-S8, G3-MC, G3-P). Odcinki śródmiejskie DK19/DK65/DK8 są oznakowane
  znakami pionowymi (B-1, D-4a, B-33), bez dużych drogowskazów.
  → **Wniosek dla gry: na tych odcinkach nie ma czego modelować ponad G3.**
- **S19 Krynice–Dobrzyniewo–Białystok Zachód** (otwarta 20.10.2026): **zero
  kadrów Mapillary 2026 w całym regionie** — oznakowanie nowej S19 = UNVERIFIED
  wizyjnie; dokumentowane wyłącznie urzędowo: komunikat GDDKiA 20.10.2026
  (CONTEXT-2026), docelowa organizacja ruchu S8/S19/DK65 wprowadzona
  20.10.2026 o 08:30, **klauzula nr 1249/2024**; włączenie ul. Warszawskiej
  przy węźle Białystok Zachód — czasowa organizacja ruchu nr 200337-3.1-33,
  **klauzula nr 3860c/2026 z 21.08.2026**, wdrożona 16.09.2026 o 13:00.
- Pokrycie Mapillary regionu: najświeższe kadry 2024-09-01 (quickness805);
  jedyny 2025: fantoment 2025-03-28 (20 kadrów, centrum, bez liści); 2026: brak.
  **Stan oznakowania 2025–26 wszędzie = UNVERIFIED poza dokumentami.**

## Braki i niepewności

- Czytelność „675" na kadrze 2020 (P7-001) niepotwierdzona w reanalizie
  (miniatura 1024 px) — fakt „675 Centrum" opiera się na G3-P005 (SOURCED, 2024).
- Data demontażu wysięgnika B: między 2020-08 a 2024-07, niezwężona (rejestr
  ZDM offline; numer decyzji nieustalony).
- Data montażu portalu C: zawężona do 2020-08-15 → 2021-05-03, nie do dnia
  (brak adnotacji urzędowej; obserwacja taśmy = ESTIMATED).
- Odczyt P7-007 częściowy (rozdzielczość miniatury); pełny odczyt w G3-MN005.
- Nowe odcinki S19 (2026) bez pokrycia zdjęciowego — treści tablic nie znane.
- Endpointy Mapillary `/images/{id}` i `?ids=` przestały odpowiadać
  13.11.2026 (metadane pobierano bbox-em) — dokumentacja w sources.md.

## Samokontrola (audyt 20%)

- Seed: `Kamion-P7-audit-20-2026-11-13-v1`; metoda: `random.Random(seed)`
  + shuffle, pierwsze k pozycji. Próba: **2 z 7 = 28,6% ≥ 20%** wymaganego.
- Wylosowane: **P7-001, P7-007** — obie pozycje zweryfikowano 2026-11-13
  (odczyt wizyjny + metadane API + plik ≤1600 px); wynik: zgodne, statusy
  uzasadnione. Szczegóły: audit_20_percent.json.

## Zawartość paczki

| Plik | Opis |
|---|---|
| README.md | niniejszy dokument |
| manifest.csv | 7 pozycji P7-001…P7-007, schemat G3 + `sezon` + `pora_dnia` (45 kolumn) |
| files/ | 7 JPG ≤1600 px dłuższego boku (Mapillary thumb_1024 / Commons 1280 px) |
| asset_manifest.csv | sha256, rozmiar, wymiary, licencja, autor per plik |
| mapillary_recheck.csv | recheck 25 pozycji G3 (24×TAK + 1×TAK z zastrzeżeniem) |
| audit_20_percent.json | losowanie samokontroli (seed, 28,6%) |
| sources.md | źródła z datami dostępu i cytatami |
| LICENSE-DATA.md | licencje: ODbL, CC BY-SA 4.0 (referencja), CC0, art. 4 pr. aut. |
