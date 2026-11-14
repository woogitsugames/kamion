# sources.md — pełne źródła (mistral-p19-hospital-gate)

Wszystkie URL-e pobierane/odczytywane 2026-11-13; poprawki M62-FIX — 2026-11-14 (data dostępu w kolumnie; dokumenty Dz.U. — cytaty i strony w manifest.csv).

## 1. OSM (ODbL, © OpenStreetMap contributors)
- Eksport API 0.6 (bbox wokół bramy; stan map: 2026-11-13):
  `https://api.openstreetmap.org/api/0.6/map?bbox=23.1870,53.1070,23.1950,53.1120`
- Node bramy (szlaban): `https://www.openstreetmap.org/node/2448457849`
- Obrys szpitala: way 239477156 (amenity=hospital, Żurawia 14)
- Portiernia: way 296211509; budynek główny: way 236884780; parking: way 276840492
- Ogrodzenia: way 883955509 (koniec przy bramie: node 8220895799), way 883955508
- Ulica Żurawia: way 73881451 (unclassified, maxspeed=40, hgv=no, maxweight=3.5, surface=paved) — biegnie ~16 m na E/NE od bramy
- Dojazd od ulicy: way 883955523 (874174759 na Żurawiej → 3323248759 → brama); za bramą: way 73881452 (brama → 874174701 → service 642905692, 1552407066)
- Teren na E od Żurawiej: way 236884785 (landuse=military, barrier=fence) z masztem node 8220945933 (man_made=mast, lattice) — obiekt z F05/F06
- Inne: node 3323248741 (barrier=gate), node 14123795058 (traffic_mirror), node 10202945270 (post_box)
- Transformacja WGS84↔EPSG:2180: własny moduł TM/GRS80 (zwalidowany w P6/M49, Δ<0,5 m)

## 2. Wikimedia Commons (CC0 / CC BY 3.0 pl)
Wyszukiwanie (M62-FIX, 2026-11-14): geosearch `list=geosearch&gscoord=53.1094568|23.1906473&gsradius=300&gsnamespace=6&gslimit=500` — **25 plików** (pełna lista: README §4.2); kategorie `Category:University Hospital in Białystok (Żurawia)` (9 plików) i `Category:Żurawia Street in Białystok` (14 plików + 4 podkategorie); kategoria `Szpital tymczasowy przy ul. Żurawiej w Białymstoku` nie istnieje (0). Kadry pobrane jako miniatury 960 px (`upload.wikimedia.org/.../960px-…` lub `commons.wikimedia.org/w/thumb.php?f=<nazwa>&width=960`); F01 dodatkowo 3840 px (`thumb.php … width=3840`) do wycinków. Każdy kadr obejrzany OSOBNO 2026-11-14 (jeden plik = jedno wywołanie modelu wizyjnego).

Kadry (wszystkie obejrzane 2026-11-14; rola — README §4):
- F01 (P11-129, CC0, Rakoon, 2019-11-10) — **jedyny kadr bramy**: `https://commons.wikimedia.org/wiki/File:6739_Uniwersytecki_Szpital_Kliniczny_w_Bia%C5%82ymstoku,_%C5%BBurawia_14_November_2019.jpg`
- F02 (CC0) — pętla autobusowa: `https://commons.wikimedia.org/wiki/File:8858_November_2022_in_Bia%C5%82ystok.jpg`
- F03 (CC0) — wnętrze autobusu (kasownik): `https://commons.wikimedia.org/wiki/File:20230814_182338_August_2023_in_Bia%C5%82ystok.jpg`
- F04 (CC0) — skrzyżowanie z przejściem: `https://commons.wikimedia.org/wiki/File:20230814_181655_August_2023_in_Bia%C5%82ystok.jpg`
- F05 (CC0) — budynek z masztem, teren landuse=military (inny obiekt): `https://commons.wikimedia.org/wiki/File:20200726_084447_Bia%C5%82ystok_July_2020.jpg`
- F06 (CC0) — ten sam budynek z masztem co F05 (inny obiekt): `https://commons.wikimedia.org/wiki/File:8860_November_2022_in_Bia%C5%82ystok.jpg`
- F07 (CC0) — skrzyżowanie z przejściem: `https://commons.wikimedia.org/wiki/File:20230814_180637_August_2023_in_Bia%C5%82ystok.jpg`
- F08 (CC0) — budynek WORD (inny obiekt): `https://commons.wikimedia.org/wiki/File:8861_November_2022_in_Bia%C5%82ystok.jpg`
- F09 (CC BY 3.0 pl, PNG) — budynek szpitala tymczasowego: `https://commons.wikimedia.org/wiki/File:Szpital_tymczasowy_przy_ul._%C5%BBurawiej_w_Bia%C5%82ymstoku_przyjmuje_ju%C5%BC_pacjent%C3%B3w_01.png`
- F10 (CC0) — WORD: `https://commons.wikimedia.org/wiki/File:20200726_084816_Wojew%C3%B3dzki_o%C5%9Brodek_ruchu_drogowego_w_Bia%C5%82ystoku,_ul._Wiewi%C3%B3rcza_64.jpg`
- F11 (CC BY 3.0 pl) — wnętrze, biurko z monitorem: `https://commons.wikimedia.org/wiki/File:Szpital_tymczasowy_przy_ul._%C5%BBurawiej_w_Bia%C5%82ymstoku_przyjmuje_ju%C5%BC_pacjent%C3%B3w_03.jpg`
- F12 (CC0) — korytarz wewnątrz budynku: `https://commons.wikimedia.org/wiki/File:20221117_130338_November_2022_in_Bia%C5%82ystok.jpg`
- F13 (CC0) — korytarz wewnątrz budynku: `https://commons.wikimedia.org/wiki/File:20221117_122654_November_2022_in_Bia%C5%82ystok.jpg`
- F14 (CC0) — ul. Żurawia wzdłuż (**URL poprawiony**; poprzedni z „_July_2020” dawał 404): `https://commons.wikimedia.org/wiki/File:20200726_084417_%C5%BBurawia_Street_in_Bia%C5%82ystok.jpg`
- F15 (CC0) — parterowy budynek z blachy falistej innej instytucji (inny obiekt): `https://commons.wikimedia.org/wiki/File:8857_November_2022_in_Bia%C5%82ystok.jpg`
- F16 (CC0) — wejście z daszkiem do budynku z blachy z F15 (inny obiekt): `https://commons.wikimedia.org/wiki/File:20221117_122456_November_2022_in_Bia%C5%82ystok.jpg`
- F17 (CC BY 3.0 pl) — sala chorych: `https://commons.wikimedia.org/wiki/File:Szpital_tymczasowy_przy_ul._%C5%BBurawiej_w_Bia%C5%82ymstoku_przyjmuje_ju%C5%BC_pacjent%C3%B3w_05.jpg`
- F18 (CC BY 3.0 pl) — sala chorych: `https://commons.wikimedia.org/wiki/File:Szpital_tymczasowy_przy_ul._%C5%BBurawiej_w_Bia%C5%82ymstoku_przyjmuje_ju%C5%BC_pacjent%C3%B3w_06.jpg`
- F19 (CC0) — stalowa brama przesuwna przy budowie, 190 m na SE (inny obiekt): `https://commons.wikimedia.org/wiki/File:20200726_084355_ul._%C5%BBurawia_July_2020.jpg`
- F20 (CC0) — ulica osiedlowa: `https://commons.wikimedia.org/wiki/File:20221117_124435_November_2022_in_Bia%C5%82ystok.jpg`
- F21 (CC0) — dom jednorodzinny: `https://commons.wikimedia.org/wiki/File:20221117_124436_November_2022_in_Bia%C5%82ystok.jpg`
- F24 (CC BY 3.0 pl) — wypowiedź dla prasy przed budynkiem: `https://commons.wikimedia.org/wiki/File:Szpital_tymczasowy_przy_ul._%C5%BBurawiej_w_Bia%C5%82ymstoku_przyjmuje_ju%C5%BC_pacjent%C3%B3w_07.jpg`
- **Usunięte duplikaty:** F22 (= F11, plik …03.jpg) i F23 (= F17, plik …05.jpg).

Licencje: CC0 — domena publiczna (tekstury dozwolone); CC BY 3.0 pl — „referencja, nie tekstura”, atrybucja: Podlaski Urząd Wojewódzki w Białymstoku.

## 3. GUGiK (otwarte dane)
- Ortofotomapa WCS: `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WCS/HighResolution?service=WCS&version=1.0.0&request=GetCoverage&coverage=Orthoimagery_High_Resolution&crs=EPSG:2180&bbox=780310.119,590827.441,780430.119,590947.441&width=2400&height=2400&format=image/png` (wycinek 120×120 m, GSD 0,05 m; warianty JPG/PNG w archiwum) + kontekst 400 m @0,25 m/px
- Skorowidz ortofotomapy WFS: `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WFS/Skorowidze` — dla wycinka: nalot **2025**, GSD 0,05 m (skorowidz.xml w archiwum)
- BDOT10k/NMPT: nie pobrano (usługi PZGIK bez odpowiedzi w sesji — patrz README sekcja 9)

## 4. Dokumenty urzędowe (ISAP/ELI)
- **Dz.U. 2019 poz. 2310** — obwieszczenie (tekst jednolity) rozporządzenia Ministrów Infrastruktury oraz Spraw Wewnętrznych i Administracji w sprawie znaków i sygnałów drogowych (tytuł wg API ELI, sprawdzone 2026-11-14; kody i znaczenie znaków: B-2, B-20, B-33, C-2): `https://eli.gov.pl/eli/DU/2019/2310/ogl` — użyte tylko do kodów; strony nie cytowane.
- **Dz.U. 2019 poz. 2311** — obwieszczenie (tekst jednolity) rozporządzenia Ministra Infrastruktury w sprawie szczegółowych warunków technicznych dla znaków i sygnałów drogowych oraz urządzeń bezpieczeństwa ruchu drogowego i warunków ich umieszczania na drogach (tytuł wg API ELI, sprawdzone 2026-11-14; wymiary, wysokości umieszczenia):
  - ELI: `https://eli.gov.pl/eli/DU/2019/2311/ogl`
  - Tekst (PDF c1): `https://eli.gov.pl/api/acts/DU/2019/2311/text/I/D20192311-c1.pdf` (525 str.; zał. 1 — znaki pionowe)
  - Załączniki (PDF c2): `https://eli.gov.pl/api/acts/DU/2019/2311/text/I/D20192311-c2.pdf` (381 str.; zał. 2 — znaki poziome)
  - Cytowane strony: tabela 1.1 (Dz.U. str. 4/PDF 9), tabela 1.11 (str. 32/PDF 37), odległość od jezdni (str. 26/PDF 31), B-20 (str. 91/PDF 96), tabela 3.1 (str. 92/PDF 97), B-33 (str. 135/PDF 140), C-2 (str. 154/PDF 159)

## 5. Źródła sprawdzone bez wyników / niedostępne (ponowione 2026-11-14)
- **Panoramax** (CC BY-SA 4.0): `https://api.panoramax.xyz/api/search?place_position=23.1906473,53.1094568&place_distance=0-300` — **0**; `…/search?bbox=23.1860,53.1067,23.1953,53.1122` — **0**; kontrola pozytywna `bbox=23.10,53.08,23.25,53.17&limit=5` — 5 (API działa)
- **KartaView**: `https://api.kartaview.org/2.0/photo/?lat=53.1094568&lng=23.1906473&radius=300` — **0** (`data: []`); kontrola pozytywna (Warszawa, r=300) — wyniki zwrócone
- **Openverse**: `https://api.openverse.org/v1/images/?q=…` — „szpital Białystok Żurawia” → **1** wynik (= F01, Wikimedia); „Zurawia Bialystok hospital” → **0**; „Żurawia Białystok”, „Zurawia Bialystok”, „Białystok hospital” → HTTP 504 (bez wyniku)
- **Overpass API**: overpass-api.de — reset połączenia, kumi.systems — timeout; zapytanie o id z zadania wykonane na `maps.mail.ru/osm/tools/overpass` (węzły) i przez OSM API 0.6 (`map?bbox=23.1880,53.1085,23.1935,53.1105`, `way/73881451/full`, `way/236884785/full`, `way/239477156/full`) — 2026-11-14
- **Mapillary**: brak tokenu — nie sondowano (zgodnie z zasadami D43/zadania)
- **Google Maps/Street View/Earth/3D Tiles**: ZAKAZ — nieużyte

## 6. Narzędzia i metody
- Oględziny kadrów: analiza obrazu (pytania tematyczne, wielokrotne niezależne odczyty); liczby z wizji tylko jakościowo (lekcja P6 — brak powtarzalności)
- Pomiar szerokości wjazdu: cięciwa między node'ami geometrii OSM (metoda P6 G07/G08) + rzut prostopadły; obliczenia w EPSG:2180
- Ekstrakcja tekstu PDF: własny parser (tabele /Contents + ToUnicode CMap); dekoder PNG (zlib + unfilter) do analizy orto
