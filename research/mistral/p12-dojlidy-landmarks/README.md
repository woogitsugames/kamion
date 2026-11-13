# P12 — Dojlidy/Krywlany: obiekty charakterystyczne, typologia zabudowy i generatory ruchu (D60)

**Kamion — badanie rozpoznawalności kafla Dojlidy/Krywlany (D60), pod bramkę rozpoznawalności D51** (gracz z Białegostoku ma rozpoznać miejsce po układzie, znakach i obiektach charakterystycznych). Stan badania: 13 listopada 2026. Gałąź: `research/mistral-p12-dojlidy-landmarks`, wyjście z najnowszego `origin/main` (8a7296af). Materiał po polsku.

Zawartość: [Zakres i bbox](#zakres-i-bbox) · [Metoda i źródła](#metoda-i-źródła) · [Landmarki](#1-landmarki-39) · [Typologia zabudowy](#2-typologia-zabudowy-przy-drogach) · [Wyposażenie dróg](#3-wyposażenie-dróg) · [Generatory ruchu ciężarówek](#4-generatory-ruchu-ciężarówek) · [Korytarz tranzytu](#korytarz-tranzytu-ciężarówek--35-t) · [Luki](#luki-i-usterki) · [Pliki](#pliki-badania)

## Zakres i bbox

`Data/Regions/bialystok-dojlidy/region.yaml` **nie istnieje** — bbox ustalono samodzielnie (ustalenie własne, zgodnie z decyzją D60). Kafel badawczy **dokładnie 2000×2000 m**, osiowo w EPSG:2180, tak by objąć **lotnisko Białystok-Krywlany** (płyta, hangary, pasy startowe) oraz **rdzeń strefy przemysłowej Dojlidy** (KAN, Masterpress, BPN-T, Rosti, Bravilor, PSS Społem) wraz z korytarzem tranzytu ciężarowego **Kuronia → Dywizjonu 303 → Ciołkowskiego**:

| Parametr | Wartość |
|---|---|
| BBOX EPSG:2180 (xmin, ymin, xmax, ymax) | **[778660, 589590, 780660, 591590]** |
| Środek (WGS84) | 53.107162, 23.179805 |
| Rogi WGS84 | SW 53.098717, 23.164035 · SE 53.097669, 23.193834 · NW 53.116653, 23.165771 · NE 53.115605, 23.195582 |
| Zakres WGS84 | ok. 53.0984–53.1166 N, 23.1640–23.1956 E |

Transformacja EPSG:2180 zaimplementowana w `tools/epsg2180.py` (TM, GRS80, k0=0,9993, λ0=19°E) i skalibrowana na istniejący kafel `bialystok-industrial-c` (zgodność ~1 m).

**Obiekty poza kaflem, świadomie w katalogu** (bramka D51 działa z jezdni, nie od linii działki): browar Dojlidy (~650 m na wschód), BIAFORM z kominami (~240–1100 m), BIAWAR (~560 m), BISON (~210 m), Odlewnia, kościół NSM (~900 m), pałace Hasbacha i Lubomirskich (~600 m). Każdy taki wpis ma jawną flagę `poza_kaflem` w `manifest.csv` i `data/landmarks.json`.

## Metoda i źródła

- **OSM** (ODbL): wyciąg API `/api/0.6/map` bbox 23.160–23.198, 53.0955–53.118 (kafel + bufor ~300 m): **23 271 węzłów, 4 179 dróg/obiektów** (ts 2026-11-13T10:0x). Obiekty poza kaflem — Overpass (maps.mail.ru; końcówki czasem 504, retry). Parsowanie: `tools/parse_osm.py`.
- **GUGiK LoD1 2024** (CC BY 4.0): `measuredHeight` dla **1 189 budynków kafla** (mediana 6,81 m; p90 9,72 m; max 24,44 m — budynek sądu).
- **GUGiK BDOT10k** (schemat 2021, powiat 2061, stan 2024-09): funkcje budynków i kondygnacje dla **1 256 budynków kafla** → klasy typologii.
- **GUGiK ortofoto** (WMS StandardResolution, otwarte dane — komercyjne użycie OK): kadry dowodowe 800×800 px (0,5 m/px, 400×400 m) do `files/` (poza gitem, w ZIP). Data nalotu UNVERIFIED (skorowidz WMS → HTTP 401).
- **Kolor dachu = ESTIMATED** metodą: mediana RGB w dysku r = min(√(A/π)/2, 8 m) wokół centroidu, z kadru ortofoto; klasyfikacja paletą referencyjną + reguły barwy (czerwona/rdzawa gdy R>G+25 ∧ R>B+25 itd.) — `tools/frames_colors.py`. Dla P12-039 (Pałac Hasbacha) próbka pobrana metodą PNG-probe (16×16 px, dekodowanie czystym Pythonem) — tożsamy dysk r ≤ 8 m.
- **Zdjęcia uliczne**: Panoramax (CC BY-SA 4.0) — **0 kadrów w bbox**; KartaView — API 404; Mapillary — brak tokenu → UNVERIFIED. Dlatego **kolory/materiały elewacji są UNVERIFIED** dla większości obiektów (wyjątki: zdjęcia Commons — browar, sąd, pałac Hasbacha, lotnisko).
- Zakazane źródła (Google Maps/Street View/Earth/3D Tiles) **nie były używane**.
- Pełny rejestr z datami i licencjami: [sources.md](sources.md). Konwencja statusów jak w G10: SOURCED (źródło potwierdza) / ESTIMATED (metoda oszacowania podana) / UNVERIFIED (brak legalnego źródła).

## 1. Landmarki (39)

Pełne dane (WSG84, wysokość + źródło, kolor/materiał, droga i odległość widoczności, URL, licencja, uwagi) — w `manifest.csv` (P12-001…039). Poniżej skrót; „poza kaflem" = obiekt poza bbox, widoczny z dróg kafla.

| ID | Obiekt | WGS84 (lat, lon) | h [m] (źródło) | Dach (ESTIMATED z ortofoto) | Widoczny z drogi (odl.) |
|---|---|---|---|---|---|
| P12-001 | Pas startowy asfaltowy 09R/27L lotniska Krywlany (1350×30 m) | 53.100906, 23.173246 | 0 (nawierzchnia; ele. ~153 m n.p.m. — Wikipedia) | asfaltobeton | Dywizjonu 303 (150 m) |
| P12-002 | Pas startowy trawiasty 09L/27R (860×160 m) | 53.102241, 23.171011 | 0 (trawa) | trawa | Dywizjonu 303 (145 m) |
| P12-003 | Płyta postojowa (apron) — cz. trawiasta | 53.104152, 23.164840 | 0 | trawa | Krywlany (55 m) |
| P12-004 | Hangar Aeroklubu Białostockiego | 53.104534, 23.164520 | UNVERIFIED | ocynk | Krywlany (40 m) |
| P12-005 | Silo/wieża przy płycie | 53.104809, 23.170474 | UNVERIFIED | jasna/biała | Krywlany (60 m) |
| P12-006 | Hala Sekcji Modelarskiej Aeroklubu | 53.104922, 23.165101 | 3,4 (LoD1) | jasna/biała | Krywlany (45 m) |
| P12-007 | Zrzutowisko (13 994 m²) | 53.103317, 23.166141 | 0 (trawa) | trawa | Krywlany (160 m) |
| P12-008 | Magazyn logistyczno-produkcyjny KAN (28 212 m²) | 53.104351, 23.190790 | 15,05 (LoD1) | ocynk | Karpińskiego (50 m) |
| P12-009 | Hala Masterpress (druk przemysłowy) | 53.105609, 23.191144 | 12,17 (LoD1) | jasnoszara | Kuronia (60 m) |
| P12-010 | Hala Bravilor (wyposażenie gastronomiczne) | 53.105330, 23.187331 | 12,72 (LoD1) | jasna/biała | Kuronia (45 m) |
| P12-011 | Hala Rosti (opakowania/tworzywa) | 53.103746, 23.193953 | 18,92 (LoD1) | jasna/biała | Myśliwska (60 m) |
| P12-012 | Inkubator Technologiczny BPN-T (5 kond.) | 53.106874, 23.193275 | 18,09 (LoD1) | ocynk | Żurawia (60 m) |
| P12-013 | Hala Kuronia 3 (tekstylia — Kontri) | 53.106752, 23.191379 | 6,01 (LoD1) | jasna/biała | Kuronia (30 m) |
| P12-014 | Hale hurtowni PSS „Społem" (D303 8) | 53.105347, 23.171971 | UNVERIFIED | jasna/biała | Dywizjonu 303 (95 m) |
| P12-015 | Hale magazynowe Hake 9/11 | 53.105761, 23.169482 | UNVERIFIED | jasna/biała | Hake (50 m) |
| P12-016 | Hala w budowie — Spadochroniarzy 2 (19 420 m²) | 53.106974, 23.173746 | UNVERIFIED (budowa) | szara | Spadochroniarzy (95 m) |
| P12-017 | Stacja RPZ11 110/15 kV (słupy 110 kV) | 53.107141, 23.189694 | UNVERIFIED | ocynk | Kuronia (80 m) |
| P12-018 | Sąd Rejonowy (Mickiewicza 103) | 53.106828, 23.185689 | **24,44** (LoD1; najwyższy kafel) | szara (płyta/papa) | Mickiewicza (45 m) |
| P12-019 | Archiwum Państwowe (Mickiewicza 101) | 53.107864, 23.184172 | 12,22 (LoD1) | szara | Mickiewicza (25 m) |
| P12-020 | Szpital Uniwersytecki — pawilon A **z lądowiskiem** (Żurawia 14) | 53.108979, 23.189920 | 14,85 (LoD1, pawilon E1) | ocynk | Żurawia (80 m) |
| P12-021 | WORD — plac manewrowy (Wiewiórcza 64) | 53.109778, 23.192799 | 5,27 (LoD1) | ocynk | Wiewiórcza (15 m) |
| P12-022 | Delegatura ABW (Żurawia 69; strefa ogrodzona) | 53.109132, 23.192011 | 11,67 (LoD1) | szara | Żurawia (60 m) |
| P12-023 | Społeczne LO im. Jana Pawła II (Mickiewicza 95) | 53.109891, 23.182440 | 13,23 (LoD1) | ocynk | Mickiewicza (30 m) |
| P12-024 | Dom zakonny przy rondzie (Ciołkowskiego 11/1) | 53.114142, 23.177087 | 11,64 (LoD1) | czerwonorudawa dachówka | Ciołkowskiego (20 m) |
| P12-025 | Hala sklepowo-dyskontowa (Wiewiórcza 51) | 53.110733, 23.191520 | 6,69 (LoD1) | ocynk | Wiewiórcza (30 m) |
| P12-026 | Pawilon handlowy na osiedlu (Niedźwiedzia 26) | 53.114620, 23.190051 | 6,39 (LoD1) | czerwonorudawa dachówka | Sokola (15 m) |
| P12-027 | Zespół bloków osiedla Dojlidy (Żubrów/Niedźwiedzia) | 53.113143, 23.191491 | 9,9–16,3 (LoD1, 3 kond.) | szara (płyta/papa) | Niedźwiedzia (25 m) |
| P12-028 | Blok Mickiewicza 83 (przy rondzie) | 53.106206, 23.168883* | 15,31 (LoD1) | szara | Mickiewicza (20 m) |
| P12-029 | Hotelik Żwirki i Wigury 26 | 53.115067, 23.170296 | 11,24 (LoD1) | szara | Żwirki i Wigury (35 m) |
| P12-030 | Maszty telekomunikacyjne (2 szt.) | 53.115871, 23.177037 | UNVERIFIED | — (trójnogi) | Zwierzyniecka/Żurawia (15 m) |
| P12-031 | **Browar Dojlidy** — hala warzelni (poza kaflem) | 53.106122, 23.203755 | UNVERIFIED | jasna/biała; fasada: ceglana czerwona (ESTIMATED ze zdjęcia) | D303 z kafla, sylwetka (600 m) |
| P12-032 | Zbiorniki fermentacyjne browaru (~30 cylindrów, poza kaflem) | 53.107450, 23.204940 | UNVERIFIED | jasna/biała | D303 z kafla (650 m) |
| P12-033 | BIAFORM — hala + 2 kominy (poza kaflem) | 53.113602, 23.201396 | UNVERIFIED | szara | sylweta kominów z Kuronia/Żurawia (400 m) |
| P12-034 | Zakład BISON (poza kaflem) | 53.103528, 23.197561 | UNVERIFIED | jasna/biała | Kuronia południowa (250 m) |
| P12-035 | Zakład BIAWAR (poza kaflem) | 53.103364, 23.202254 | UNVERIFIED | jasna/biała | Dojlidy Fabryczne (550 m) |
| P12-036 | Odlewnia Białystok (poza kaflem) | 53.104296, 23.197727 | UNVERIFIED | jasnoszara | Kuronia/Karpińskiego (300 m) |
| P12-037 | Kościół NSM w Dojlidach (1980; poza kaflem) | 53.110592, 23.209624 | UNVERIFIED (wieża) | szara | Dojlidy Fabryczne (360 m) |
| P12-038 | ROD ×3 (Mickiewicza, Ekologiczny, Relaks — 352 891 m² łącznie) | 53.113951, 23.183098 | 6,69 (mediana altan, LoD1) | szara | Mickiewicza (30 m) |
| P12-039 | Pałac Hasbacha + Pałac Lubomirskich (poza kaflem) | 53.113753, 23.202591 | UNVERIFIED | ocynk | Dojlidy Fabryczne od Ronda Hasbacha (65 m) |

\* centroid zespołu bloków; pełne pozycje w `manifest.csv`.

Zdjęcia z licencjami: każdy landmark ma kadr ortofoto GUGiK (`files/P12-A01…A26.jpg`, otwarte dane — licencja komercyjna); browar, lotnisko, sąd i pałac Hasbacha dodatkowo zdjęcia Wikimedia Commons CC BY-SA 3.0/4.0 (P12-P01…P05; pełne URL-e i autorzy w sources.md). Kadry A21–A26 pokrywają obiekty poza kaflem.

## 2. Typologia zabudowy przy drogach

**Metoda**: census — wszystkie budynki kafla (1 307 po dopasowaniu OSM↔LoD1↔BDOT10k) przypisane do klas wg funkcji BDOT10k/typu OSM; próba = budynki w buforze **30 m** od dróg bez service (**911 budynków**). Wysokości: rozkłady `measuredHeight` z LoD1 2024. Odległości budynków od drogi: **p50 = 21 m, p90 = 55 m, max 214 m**. Kolory dachów: próbkowanie ortofoto (metoda wyżej) — `data/typologia-colors.json`.

| Klasa | N w buforze 30 m | % bufora | h mediana [m] (p10–p90) | Dachy — dominujące barwy (próbki) | Dach / charakter |
|---|---|---|---|---|---|
| Domy jednorodzinne | 736 | **80,8%** | 7,4 (5,51–9,83) | szara 34,0%; grafitowa 14,6%; ocynk 14,1%; czerwonorudawa+czerwona 14,4% (N=745) | dwuspadowe (ESTIMATED z ortofoto); elewacje UNVERIFIED |
| Gospodarcze i inne | 129 | 14,2% | 3,93 (2,90–7,03) | zbliżone do domów | parterowe, dwuspadowe/płaskie |
| Handlowo-usługowe | 29 | 3,2% | 4,49 (3,67–7,74) | szara/jasnoszara | pawilony parterowe, dachy płaskie (LoD1 roofType=1000) |
| Bloki wielorodzinne | 12 | 1,3% | 10,97 (7,27–16,34) | szara 66,7% (N=18) | płyta/papa, dachy płaskie (roofType=1000) |
| Hale przemysłowe | 4 | 0,4% | 5,43 (3,76–12,17) | szara 28,6%; ocynk 23,8%; jasnoszara 19,0%; biała 14,3% (N=21) | konstrukcja stalowa, ściana kasetonowa (ESTIMATED) |
| Altany ROD | 1 | 0,1% | 6,69 (N_h=9) | szara 71,4% (N=7) | drewno (ESTIMATED), dach dwuspadowy |

Region to w ~81% zabudowa jednorodzinna przy drogach — ale **sygnał rozpoznawalności D51 budują przemysł i lotnisko**: w całym kaflu jest 29 hal (4 w buforze 30 m dróg głównych), wielkoprzestrzenne ogrodzone zakłady przy Kuronia/Karpińskiego/D303 oraz osiedlowe bloki (20 szt., 12 przy drogach) wzdłuż Mickiewicza/Niedźwiedziej.

## 3. Wyposażenie dróg

- **Przystanki**: 25 (19 z wiatą `shelter=yes`, 6 tylko słupek) — pełna lista z pozycjami w `manifest.csv` (P12-046…070). **Wiaty — typ i kolor**: wg ZDiT/Radio Białystok w regionie stoją stare wiaty oszklone z czerwonymi elementami (typ „modern"); od 2026 trwa wymiana **90 szt. w mieście** na antracytowe aluminium z półokrągłym dachem (typ „Stare Miasto", 4,1 mln zł). Który wariant stoi na danym przystanku — **UNVERIFIED** (brak pokrycia zdjęciowego). Źródło: Radio Białystok (id 262755) + OSM.
- **Znaki PL:A-11a** (przystanek na żądanie): 8 szt. przy progach zwalniających (traffic_calming=bump) — pozycje w manifest (P12-072).
- **Bollardy**: grupa 4 szt. przy zatoczce Żurawia/Wiewiórcza (53.11034–358, 23.189876–936).
- **Latarnie**: **LUKA** — w OSM kafla tylko 1 street_lamp (Prusa 1, 53.11564, 23.176561); oświetlenie sieci głównej nie ma pokrycia w OSM (typ/wysokość UNVERIFIED; do Mapillary/KartaView — obecnie niedostępne).
- **Bariery drogowe**: brak barier ochronnych w OSM kafla; zabezpieczenie wlotów realizują bollardy i wyspa ronda Ciołkowskiego/Mickiewicza.
- **Ekrany akustyczne**: **0** — brak w OSM i brak śladów na ortofoto wzdłuż korytarza tranzytu D303.
- **Ogrodzenia zakładów**: 88 odcinków `barrier=fence`; strefy ogrodzone: lotnisko, BPN-T (Żurawia), zakłady Kuronia/Karpińskiego, teren ABW (Żurawia 69). Materiał oceniony z ortofoto: siatka stalowa (ESTIMATED).
- **Drogowskazy E-\* na wlotach**: OSM nie mapuje tablic kierunkowych w regionie (brak destination/direction). UM Białystok (ZDM) wymienił w XII 2025 tablice na trzech wlotach regionu: **Suchowolca/Plażowa/Kuronia** (53.10613, 23.19414 — poz. ESTIMATED z osi jezdni OSM), **Ciołkowskiego/Mickiewicza** (53.116172, 23.177083), **Ciołkowskiego/Dywizjonu 303** (53.113261, 23.175357). Treść tablic (numery E/DK) UNVERIFIED.
- **Sygnalizacja**: 14 grup `highway=traffic_signals` w kaflu (w tym skrzyżowania Kuronia/Mickiewicza, Ciołkowskiego/Mickiewicza z przejściami z sygnalizacją akustyczną).

## 4. Generatory ruchu ciężarówek

17 zakładów/baz z pozycją bramy (z OSM `barrier=gate/lift_gate`, dopasowanie: najbliższa brama do centroidu — metoda w uwagach wiersza) lub jawnie UNVERIFIED dla obiektów poza kaflem. Pełne dane w `manifest.csv` (P12-080…096). Skrót:

| Zakład | Profil | Brama (pozycja) | Status |
|---|---|---|---|
| Centrum logistyczno-produkcyjne KAN (Karpińskiego 5) | logistyka instalacji sanitarnych | 53.103498, 23.190006 (OSM lift_gate) | SOURCED |
| Masterpress S.A. (Kuronia 4) | druk przemysłowy | 53.106018, 23.192241 (OSM) | SOURCED |
| Bravilor (Kuronia 2, SSSE) | produkcja gastronomiczna | 53.105887, 23.187439 (OSM) | SOURCED |
| Rosti Poland (Myśliwska 18) | opakowania/tworzywa | 53.103204, 23.193609 (OSM) | SOURCED |
| BPN-T / Inkubator (Żurawia 71) | park technologiczny | 53.107451, 23.193443 (OSM) | SOURCED |
| PSS „Społem" — hurtownia (D303 8) | centrum dystrybucji | wjazd z D303 UNVERIFIED (najbliższa brama OSM 386 m) | SOURCED (obiekt) |
| Hale Hake 9/11 | magazyny; operator UNVERIFIED (katalogi: tekstylia) | wjazd z Hake UNVERIFIED | UNVERIFIED |
| Kontri (Kuronia 3) | tekstylia techniczne | 53.107292, 23.192212 (OSM) | SOURCED |
| Hala w budowie (Spadochroniarzy 2) | przyszły magazyn; inwestor UNVERIFIED | UNVERIFIED | UNVERIFIED |
| Art-Glas (Wiewiórcza 4) | hurtownia szkła (dostawy płaskiego szkła) | 53.110652, 23.185712 (OSM) | SOURCED |
| Zintronic (Modzelewskiego 2) | produkcja kamer/monitoringu | 53.110652, 23.185712 (OSM) | SOURCED |
| Lotnisko Krywlany (Aeroklub Białostocki) | paliwo lotnicze, hangary | najbliższa brama OSM 53.099362, 23.177153 (mapa bram niepełna) | SOURCED |
| Browar Dojlidy (poza kaflem) | dostawy słodu/piwa | UNVERIFIED (od Dojlidy Fabryczne) | SOURCED (obiekt) |
| Biaform (poza kaflem) | sklejka — dostawy drewna | UNVERIFIED | SOURCED |
| Zakład przyrządów BISON-BIAL (Myśliwska 13) | fabryka uchwytów | UNVERIFIED | UNVERIFIED (katalogi) |
| NIBE-BIAWAR (Kalicińskiego 1, poza kaflem) | armatura/kotły | UNVERIFIED | SOURCED |
| Odlewnia Białystok S.A. (Myśliwska 11) | odlewnia metali | UNVERIFIED | UNVERIFIED (katalogi) |

Kontekst ruchu ciężarowego: **od 19–20.11.2025 tranzyt > 3,5 t przekierowano na ciąg Kuronia → Dywizjonu 303 → Ciołkowskiego** (zakazy na Suchowolca i Dojlidy Fabryczne; zakaz > 8 t na Mickiewicza między Kuronia a Ciołkowskiego; od I 2026 Dojlidy bez tranzytu) — szersze opracowanie w `research/g10-truck-restrictions/`. Przyszłe generatory: hala widowiskowo-sportowa przy Ciołkowskiego (30 tys. m², do ~2028, UNIBEP — [akadera.bialystok.pl](https://akadera.bialystok.pl/bialystok-wybuduje-hale-widowiskowo-sportowa-nowoczesny-obiekt-powstanie-przy-ulicy-ciolkowskiego/)) oraz plany lotniska pasażerskiego Krywlany (investmap 29.10.2026 — tylko referencja).

## Korytarz tranzytu ciężarówek > 3,5 t

```
Kuronia (rondo z Mickiewicza, sygnalizacja) → na wschód do Karpińskiego (zakłady: KAN, Masterpress, Bravilor, Kontri, stacja 110 kV)
                                          → Dywizjonu 303 (na północ: hurtownia Społem, lotnisko na zachodzie; na południe: browar)
                                          → Ciołkowskiego (rondo z Mickiewicza — zakaz > 8 t dalej na Mickiewicza)
```

Ten ciąg jest osią odczuwalności „ciężarówkowej" regionu: wzdłuż niego leżą wszystkie duże generatory kafla, przystanki z wiatami i 3 z 4 grup sygnalizacji.

## Luki i usterki

1. **Elewacje budynków UNVERIFIED** — brak legalnego pokrycia zdjęciami ulicznymi (Panoramax 0 kadrów, KartaView 404, Mapillary bez tokenu). Kolory fasad podane tylko tam, gdzie jest zdjęcie Commons (browar: cegła).
2. **Latarnie** — pokrycie OSM zerowe (1 obiekt); typ i rozstaw UNVERIFIED.
3. **Data nalotu ortofoto UNVERIFIED** — skorowidz WMS PZGiK zwraca HTTP 401; kadry mogą pochodzić z różnych sesji (widoczna budowa hali Spadochroniarzy 2 → sesja ≥ 2024/2025).
4. **Inwestor hali Spadochroniarzy 2 UNVERIFIED** (kontekst SSSE niepotwierdzony); operator hal Hake 9/11 UNVERIFIED (katalogi firm).
5. **Wysokości**: maszty, silo, kominy browaru/BIAFORM, obiekty poza kaflem (browar, BIAFORM, BISON, BIAWAR, Odlewnia, kościół, pałace) — bez LoD1/height w OSM → UNVERIFIED (świadomie nie ekstrapolowano).
6. **Wiaty przystankowe** — nie wiadomo, które przystanki dostały już nowe antracytowe (wymiana od 2026 trwa).
7. **Treść drogowskazów E-\* na wlotach UNVERIFIED** (komunikat ZDM potwierdza lokalizacje, nie treść tablic).
8. **Bramy zakładów poza kaflem** — niedomapowane w OSM → UNVERIFIED.
9. **Ekrany akustyczne**: brak (potwierdzone negatywnie OSM + ortofoto; ryzyko planowych przy hali sportowej — UNVERIFIED).
10. Overpass (maps.mail.ru) niestabilny (504) — wyciągi wschodnie wykonane z retry; wyniki spójne z API głównym.

## Pliki badania

```
research/mistral/p12-dojlidy-landmarks/
├── README.md            ← ten plik
├── manifest.csv         ← 95 wierszy (39 landmarków, 6 typologii, 33 wyposażenia, 17 generatorów); UTF-8 BOM, RFC 4180
├── sources.md           ← rejestr źródeł z licencjami i datami
├── audit_20_percent.json← samokontrola 20% (seed 20261113, losowanie warstwowe, 19/95 wierszy, wynik: 19 OK)
├── .gitignore           ← files/ + nazwa ZIPa
├── tools/               ← epsg2180.py, parse_osm.py, parse_lod1.py, match_buildings.py,
│                          frames_colors.py, typologia_colors.py, gen_manifest.py, gen_audit.py
└── data/                ← landmarks.json (39), landmark-colors.json, matched-with-roads.json,
                           road-geom.json, region-summary.json, osm-pois.json, typologia.json,
                           typologia-colors.json, osm-east-strip.json, osm-hasbach.json, area-geom.json
```

Zdjęcia (26 kadrów ortofoto + 5 zdjęć Commons) **nie trafiają do gita** (`files/` w .gitignore); paczka `mistral-p12-dojlidy-landmarks-files.zip` (SHA-256 w opisie PR) jest dostarczana poza repozytorium — patrz opis PR.

Dokument powiązany: `research/gptpro/2-next-regions/README.md` (D60), `research/g5-street-furniture/README.md` i `research/g7-street-greenery/README.md` (format), `research/g10-truck-restrictions/` (zakazy i korytarz tranzytu).
