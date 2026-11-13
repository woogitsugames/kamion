# P8 — truck-restrictions-2: OSM vs rzeczywistość — ograniczenia ruchu ciężarówek w Białymstoku i na dojazdach S8/DK8/DK19/DK65

**Projekt:** Kamion (mobilny symulator ciężarówki z naczepą, świat Białegostoku 1:1)
**Paczka:** gptpro-p8-truck-restrictions-2.zip | **Data wykonania:** 2026-11-13 | **Pozycji w manifeście:** 41

## 1. Cel

Domknięcie pozycji UNVERIFIED z zadania P8 w zakresie research/g10-truck-restrictions:
skrajnia pod wiaduktami, odcinki e-TOLL dla pojazdów >3,5 t, status uchwały LI/794/18
i „klas tonażowych", znaki B-5/B-18/B-20, rozstrzygnięcie sprzecznych tagów OSM oraz
wnioski dla pipeline gry.

## 2. Metoda

- OSM: dane pobrane bezpośrednio z api.openstreetmap.org (API 0.6, kafelki bbox,
  stan na 2026-11-13); pozycje ways z tagami maxweight/hgv/toll:hgv/maxheight
  zestawione z dokumentami urzędowymi. Overpass niedostępny (HTTP 429) — użyto API 0.6.
- Dokumenty: Dz.U. (dziennikustaw.gov.pl, ELI), Ministerstwo Finansów (e-TOLL: pełna
  lista odcinków od 1.02.2026, lista nowych odcinków, lista sekcji od 24.06.2025),
  GDDKiA Oddział Białystok, BIP/bialystok.pl (uchwała LI/794/18 z załącznikiem POŚPH,
  komunikaty ZDM), LexLege (rozporządzenie o znakach i sygnałach drogowych).
- PDF-y z zakodowanym tekstem (CMap bez standardowego ToUnicode) dekodowane własnym
  skryptem (mapowanie CID→Unicode), co pozwoliło odczytać pełną treść załączników.
- Zdjęcia (zasada A paczki 02): brak przeglądarki i tokenu API Mapillary — kluczy
  image nie zgadywano; pozycje zdjęciowe oznaczono UNVERIFIED (patrz pkt 4).
- Zakaz Google Maps/Street View — zachowany. Mapillary tylko jako potencjalne
  źródło CC BY-SA 4.0 (treści faktograficzne wolne, wycinki zdjęć = referencja
  z atrybucją, share-alike — nie jako tekstury).
- Współrzędne WGS84 (6 miejsc), wyliczone ze środków geometrii ways OSM (API 0.6).

## 3. Najważniejsze ustalenia

### 3.1. Skrajnia pod wiaduktami (pkt 1 zadania)
- **Brak potwierdzonego znaku B-16/tabliczki wysokości** dla badanych obiektów
  (rondo Putry, wiadukty Andersa, al. Tysiąclecia, ronda Wolnej Ukrainy
  i Żołnierzy Wyklętych, al. Niepodległości) — w OSM te ways nie mają tagu
  maxheight (jedyny maxheight w rejonie: way 549993393 = 3 m, obiekt serwisowy).
- **Korekta założenia z zadania:** ustawowa skrajnia to **nie 4,0 m**. Wg § 80 ust. 1
  rozporządzenia w sprawie warunków technicznych dróg publicznych (Dz.U. 2022
  poz. 1518): **5,00 m — drogi klasy A lub S; 4,50 m — klasy GP/G/Z/L/D**.
- § 80 ust. 2 dopuszcza redukcję do **4,20 m** (zgoda zarządcy drogi i organu ruchu),
  poniżej 4,20 m — dodatkowo opinia komendanta PSP. Wynika stąd, że pod wiaduktami
  dróg ekspresowych (S8 nad al. Niepodległości) skrajnia to 5,00 m, a pod wiaduktami
  dróg niższych klas 4,50 m — o ile nie ma znaku B-16 z mniejszą wartością.
- Wiadukty zinwentaryzowane w manifeście (P8-001 … P8-010) wraz z ways OSM
  i współrzędnymi; wszystkie = BRAK_ZNAKU/UNVERIFIED co do rzeczywistej skrajni
  (do potwierdzenia zdjęciami Mapillary po uzyskaniu tokenu lub inwentaryzacją
  w terenie).

### 3.2. e-TOLL dla pojazdów >3,5 t (pkt 2 zadania)
- Podstawa prawna: rozporządzenie RM z 22.03.2011 (t.j. Dz.U. 2022 poz. 2539,
  ostatnia zmiana Dz.U. 2024 poz. 1574) + **nowelizacja z 8.01.2026 (Dz.U. 2026
  poz. 33, obowiązuje od 1.02.2026)**.
- Pełna lista MF odcinków płatnych od 1.02.2026 (P8-015, files/P8-015.pdf):
  **S8 płatna do węzła Choroszcz włącznie** — sekcje: Rzędziany–Tykocin (5470 m),
  Tykocin–Choroszcz (3490 m), „Węzeł Choroszcz — Choroszcz (skrzyżowanie z DP
  nr 2287B)" (960 m). **Obwodnica Białegostoku (S8) — bezpłatna.**
- **DK8:** tylko 3 sekcje przy Augustowie (ostatnia: „Janówka — Węzeł Raczki",
  7419 m); w rejonie Białegostoku DK8 bezpłatna. **DK19: 0 sekcji; DK65: 0 sekcji.**
  **S19:** płatna tylko na południu kraju; nowo otwarty odcinek Krynice–Dobrzyniewo–
  Białystok Zachód (20.10.2026, GDDKiA) — bezpłatny.
- Porównanie z OSM: **tagi toll:hgv=yes na S8 pokrywają się z listą** (ways płatne
  na zachód do węzła Choroszcz, lon 22,9866–23,0096; od węzła na wschód — brak
  tagu; nowe ways S19;65 przy węźle Białystok Zachód — bez tagu). ZGODNE.
- Nowy odcinek S19 (10,2 km, otwarty 20.10.2026): 8 wiaduktów, nośność 11,5 t/oś
  (GDDKiA) — do monitoringu w kolejnej paczce (możliwa przyszła zmiana OSM).

### 3.3. Uchwała LI/794/18 — identyfikacja i status (pkt 3 zadania)
- **Korekta założenia z zadania:** uchwała Nr LI/794/18 Rady Miasta Białystok
  z 18.06.2018 **nie jest planem transportowym** — to uchwała w sprawie
  **Programu ochrony środowiska przed hałasem dla miasta Białegostoku (POŚPH)**.
- W tabelach działań POŚPH (~s. 23-24 załącznika) występują listy ulic:
  „Ulice, na których obowiązują ograniczenia ruchu ciężkiego" (36 pozycji —
  m.in. Hetmańska, Lipowa, Piastowska, Al. Solidarności, Wasilkowska; **bez**
  progu tonażowego) oraz „Kontrole respektowania ograniczeń ruchu ciężkiego"
  (~40 pozycji — tu są m.in. **J.K. Branickiego i Zwierzyniecka**, ale bez progu t).
- **„Klasy tonażowe 3,5/12/40 t" — NIEPOTWIERDZONE.** W treści uchwały i załącznika
  nie występują. Jedyne wartości: planowana akcja „Zakaz ruchu pojazdów ciężarowych
  o DMC > 12 t" dla ul. Sławińskiego, Żeromskiego i Skrzetuskiego (znak B-5);
  3,5 t to ustawowa definicja znaku B-5; „40 t" — brak w ogóle.
- Status: BIP oznacza POŚPH jako **dokument archiwalny**; aktualny jest POŚ miasta
  na lata 2025-2030 (perspektywa 2031-2034); POŚPH dla woj. podlaskiego — uchwała
  sejmiku LXII/931/2024 (ELI POL_WOJ_PL/2024/1130). Następcy POŚPH-miasto nie ma.
- **Realne, aktualne ograniczenia (XI 2025, ZDM):** przekierowanie tranzytu >3,5 t
  z ul. Suchowolca na Kuronia/Dywizjonu 303/Ciołkowskiego oraz zakaz >8 t na
  Mickiewicza (między Kuronia a Ciołkowskiego) — komunikat ZDM z 19.11.2025.
  **OSM jest z tym ZGODNE** (Suchowolca: maxweight=3.5+hgv=no; Mickiewicza:
  maxweight=8). Nowa stała organizacja na Bitwy Białostockiej/drodze dojazdowej:
  komunikat ZDM z 20.11.2025 (ruch jednokierunkowy, kontraruch rowerowy).

### 3.4. Sprzeczne tagi OSM (pkt 3 i 4 zadania)
- **Bitwy Białostockiej (way 178208423):** hgv=no + goods=delivery = zakaz ciężkich
  z wyjątkiem dostaw; podstawy urzędowej (numeru zarządzenia) **nie znaleziono** —
  UNVERIFIED. Nowa droga dojazdowa (way 1456381393) również hgv=no.
- **Sokólska (way 188396757):** hgv=no, oneway=yes; zarządzenia **nie znaleziono** —
  UNVERIFIED.
- **Warszawska (way 842154286):** maxweight=12 t **razem z** hgv=no + goods=delivery
  — **sprzeczność wewnętrzna OSM** (SPRZECZNE); brak potwierdzenia urzędowego 12 t.
- **Branickiego i Zwierzyniecka:** OSM ma maxweight=8 na wschodnich odcinkach;
  twierdzenie „plan 12 t" **NIEPOTWIERDZONE** — POŚPH nie przewiduje dla nich progu
  12 t (występują tylko na liście kontrolek, bez progu). Podstawy 8 t nieustalone —
  UNVERIFIED (prawdopodobnie znak B-18).
- **Korekta znaków (Dz.U. 2019 poz. 2310 t.j.):** B-5 = zakaz wjazdu samochodów
  ciężarowych (DMC >3,5 t domyślnie), B-16 = wysokość, B-18 = rzeczywista masa
  całkowita, B-19 = nacisk osi napędowej; **B-20 to znak STOP** — nie ograniczenie
  tonażu. Ograniczenia parametrów to seria B-15…B-19.
- **Zdjęcia znaków przy Bitwy Białostockiej i Sokólskiej: UNVERIFIED** — brak tokenu
  API Mapillary (zasada A: kluczy nie zgadywano), brak zdjęć na Wikimedia Commons.
- **Numery zarządzeń ustanawiających zakazy: nieustalone** — pozycja P8-040 wskazuje
  drogę domknięcia (rejestr organizacji ruchu ZDM Białystok).

### 3.5. Wnioski dla pipeline gry (pkt 5 zadania)
**Tagi do grafu dróg:** `maxweight`, `maxweight:hgv`, `maxaxleload`, `maxlength`,
`hgv:conditional`, `maxheight`, `toll:hgv`.

**Reguła rozstrzygania sprzeczności (priorytety):**
1. **Źródło urzędowe** (organizacja ruchu ZDM/GDDKiA, Dz.U., lista e-TOLL MF) —
   najwyższy priorytet; wygrywa z każdym tagiem OSM.
2. **OSM** — gdy brak źródła urzędowego; uwzględniać data_check tagów (świeżość).
3. **Wartość ustawowa/domyślna** — gdy brak obu: skrajnia wg § 80 Dz.U. 2022
   poz. 1518 (4,50/5,00 m), brak zakazu, nośność 11,5 t/oś na drogach krajowych
   klas S/GP.

**Reguły szczegółowe:**
- `maxheight=default` — ignorować (nie znak, tylko domniemanie);
- `hgv=no` + `goods=delivery` — zakaz HGV z wyjątkiem dostaw (dopuszczalne
  zjazdy do punktów ładowania, waga limitowana pozostałymi tagami);
- sprzeczność typu `maxweight=12 t` + `hgv=no` (Warszawska): dopóki brak wartości
  urzędowej — **przyjmuj bardziej restrykcyjną interpretację** (hgv=no), z flagą
  do weryfikacji; jeśli pojawi się źródło urzędowe — stosować punkt 1;
- `toll:hgv` nakładać z listy MF (od 1.02.2026), nie z OSM — OSM tylko kontrolne;
- zakazy z komunikatów ZDM wpisywać z datą obowiązywania (np. Mickiewicza >8 t
  od XI 2025, Suchowolca >3,5 t) — gra powinna móc wersjonować stan świata.

## 4. Braki i niepewności

- **Brak zdjęć Mapillary** (wiadukty, znaki B-5/B-18 przy Sokólskiej i Bitwy
  Białostockiej): brak tokenu API i przeglądarki (zasada A) — klucze nie zgadywano.
  Do domknięcia: sesja na mapillary.com/app (pKey z adresu) lub własne zdjęcia autorów.
- **Brak numerów zarządzeń ZDM** dla zakazów na Sokólskiej/Bitwy Białostockiej —
  wymagany dostęp do rejestru organizacji ruchu (ZDM, ul. Składowa 11).
- **Skrajnie pod wiaduktami** — wartości ustawowe (4,50/5,00 m) pewne, rzeczywiste
  (możliwe redukcje do 4,20 m) niepotwierdzone znakami.
- **Nowa S8/S19 wschód i obwodnica w OSM** — rozjeżdżająca się świeżość danych;
  pozycje w manifeście odzwierciedlają stan OSM na 2026-11-13.
- Duże PDF-y (>5 MB) i skany — tylko referencja, nie pobrano (projekt_planu.pdf,
  pzm2035_druk988.pdf, uch_610_2022.pdf, policja_zmiana2025.pdf, pzdw_org20.pdf).

## 5. Samokontrola 20% (zasada F)

- **Seed: 20261113** (jawny); populacja: **wszystkie 41 pozycji manifestu**
  (nie tylko pobrane); próba: `random.Random(20261113).sample(ids, 9)` = **9/41 = 22%**.
- Wylosowane: P8-001, P8-002, P8-005, P8-009, P8-012, P8-024, P8-030, P8-033, P8-039.
- Dla każdej sprawdzono: (a) działanie linku (curl, kod HTTP), (b) licencję
  (zgodność ze źródłem: ODbL / dokument urzędowy art. 4), (c) współrzędne
  (bbox geometrii ways OSM z API/kafelków ±0,002°), (d) obecność i rozmiar pliku
  (limit 5 MB).
- **Wynik: 9/9 PASS** (100%). Szczegóły w `audit_20_percent.json`.
  Uwaga metodologiczna: dla pozycji OSM linkiem źródłowym jest strona way OSM,
  a dane weryfikowano bezpośrednio przeciwko api.openstreetmap.org (HTTP 200).

## 6. Zawartość paczki

- `README.md` — niniejszy dokument (po polsku).
- `manifest.csv` — 41 pozycji (P8-001…P8-041), separator „;", UTF-8 BOM; kolumny:
  id, ulica_lub_obiekt, osm_way_id, tag_osm, wartość_osm, wartość_urzędowa,
  dokument_strona, lat, lon, zgodność (ZGODNE/SPRZECZNE/BRAK_ZNAKU/UNVERIFIED),
  data_zdjęcia, mapillary_key, url_źródła, licencja, autor, data_dostępu,
  status (SOURCED/ESTIMATED/UNVERIFIED), sezon, pora_dnia, uwagi.
- `files/` — 6 dokumentów urzędowych PDF (art. 4 ustawy o prawie autorskim),
  każdy ≤5 MB, łącznie ~7,6 MB: P8-012.pdf (Dz.U. 2022 poz. 1518), P8-014.pdf
  (Dz.U. 2026 poz. 33), P8-015.pdf (pełna lista odcinków e-TOLL od 1.02.2026),
  P8-016.pdf (nowe odcinki od 1.02.2026), P8-017.pdf (sekcje od 24.06.2025),
  P8-025.pdf (POŚPH 2018 = LI/794/18 z załącznikiem). Brak zdjęć = brak plików
  JPG (pozycje UNVERIFIED bez domniemywania źródeł).
- `sources.md` — wszystkie źródła z datą dostępu (2026-11-13).
- `audit_20_percent.json` — wynik samokontroli (seed, próba, wyniki).
