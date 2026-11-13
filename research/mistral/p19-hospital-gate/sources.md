# sources.md — pełne źródła (mistral-p19-hospital-gate)

Wszystkie URL-e pobierane/odczytywane 2026-11-13 (data dostępu w kolumnie; dokumenty Dz.U. — cytaty i strony w manifest.csv).

## 1. OSM (ODbL, © OpenStreetMap contributors)
- Eksport API 0.6 (bbox wokół bramy; stan map: 2026-11-13):
  `https://api.openstreetmap.org/api/0.6/map?bbox=23.1870,53.1070,23.1950,53.1120`
- Node bramy (szlaban): `https://www.openstreetmap.org/node/2448457849`
- Droga dojazdowa: way 73881452 (service); droga za bramą: way 883955523 (service)
- Obrys szpitala: way 239477156 (amenity=hospital, Żurawia 14)
- Portiernia: way 296211509; budynek główny: way 236884780; parking: way 276840492
- Ogrodzenia: way 883955509 (koniec przy bramie: node 8220895799), way 883955508
- Ulica Żurawia: way 73881451 (unclassified, hgv=no, maxweight=3,5)
- Inne: node 3323248741 (barrier=gate), node 14123795058 (traffic_mirror), node 10202945270 (post_box)
- Transformacja WGS84↔EPSG:2180: własny moduł TM/GRS80 (zwalidowany w P6/M49, Δ<0,5 m)

## 2. Wikimedia Commons (CC0 / CC BY 3.0 pl)
Wyszukiwanie: API `commons.wikimedia.org/w/api.php` (geosearch `list=geosearch&gscoord=53.1095,23.1906&gsradius=10000`; kategoria `Category:Uniwersytecki Szpital Kliniczny w Białymstoku`; katalog plików użytkownika Rakoon; extmetadata — licencje). Kadry pobierane przez `https://commons.wikimedia.org/w/thumb.php?f=<nazwa>&width=1600` (JPG ≤1600 px).

Kadry użyte (obejrzane):
- F01 (P11-129, CC0, Rakoon, 2019-11-10): `https://commons.wikimedia.org/wiki/File:6739_Uniwersytecki_Szpital_Kliniczny_w_Bia%C5%82ymstoku,_%C5%BBurawia_14_November_2019.jpg`
- F02 (CC0): `https://commons.wikimedia.org/wiki/File:8858_November_2022_in_Bia%C5%82ystok.jpg`
- F03 (CC0): `https://commons.wikimedia.org/wiki/File:20230814_182338_August_2023_in_Bia%C5%82ystok.jpg`
- F04 (CC0): `https://commons.wikimedia.org/wiki/File:20230814_181655_August_2023_in_Bia%C5%82ystok.jpg`
- F05 (CC0): `https://commons.wikimedia.org/wiki/File:20200726_084447_Bia%C5%82ystok_July_2020.jpg` — REJECTED dla bramy szpitala (południowa strona ulicy)
- F06 (CC0): `https://commons.wikimedia.org/wiki/File:8860_November_2022_in_Bia%C5%82ystok.jpg`
- F07 (CC0): `https://commons.wikimedia.org/wiki/File:20230814_180637_August_2023_in_Bia%C5%82ystok.jpg`
- F08 (CC0): `https://commons.wikimedia.org/wiki/File:8861_November_2022_in_Bia%C5%82ystok.jpg` — brama WORD (inny obiekt)
- F09 (CC BY 3.0 pl): PNG — REJECTED (format)
- F10 (CC0): `https://commons.wikimedia.org/wiki/File:20200726_084816_Wojew%C3%B3dzki_o%C5%9Brodek_ruchu_drogowego_w_Bia%C5%82ystoku_July_2020.jpg` — WORD
- F11, F17, F18, F22, F23 (CC BY 3.0 pl, Podlaski Urząd Wojewódzki w Białymstoku, 2020-12-10): szpital tymczasowy (wnętrza/konferencja) — poza obrębem bramy
- F12 (CC0): `https://commons.wikimedia.org/wiki/File:20221117_130338_November_2022_in_Bia%C5%82ystok.jpg`
- F13 (CC0): `https://commons.wikimedia.org/wiki/File:20221117_122654_November_2022_in_Bia%C5%82ystok.jpg`
- F14 (CC0): `https://commons.wikimedia.org/wiki/File:20200726_084417_%C5%BBurawia_Street_in_Bia%C5%82ystok_July_2020.jpg`
- F15 (CC0): `https://commons.wikimedia.org/wiki/File:8857_November_2022_in_Bia%C5%82ystok.jpg`
- F16 (CC0): `https://commons.wikimedia.org/wiki/File:20221117_122456_November_2022_in_Bia%C5%82ystok.jpg`
- F19 (CC0): `https://commons.wikimedia.org/wiki/File:20200726_084355_ul._%C5%BBurawia_July_2020.jpg`
- F20 (CC0): `https://commons.wikimedia.org/wiki/File:20221117_124435_November_2022_in_Bia%C5%82ystok.jpg`
- F21 (CC0): `https://commons.wikimedia.org/wiki/File:20221117_124436_November_2022_in_Bia%C5%82ystok.jpg`
- F24 (CC BY 3.0 pl): `https://commons.wikimedia.org/wiki/File:Szpital_tymczasowy_przy_ul._%C5%BBurawiej_w_Bia%C5%82ymstoku_przyjmuje_ju%C5%BC_pacjent%C3%B3w_07.jpg`

Licencje: CC0 — domena publiczna (tekstury dozwolone); CC BY 3.0 pl — „referencja, nie tekstura”, atrybucja: Podlaski Urząd Wojewódzki w Białymstoku.

## 3. GUGiK (otwarte dane)
- Ortofotomapa WCS: `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WCS/HighResolution?service=WCS&version=1.0.0&request=GetCoverage&coverage=Orthoimagery_High_Resolution&crs=EPSG:2180&bbox=780310.119,590827.441,780430.119,590947.441&width=2400&height=2400&format=image/png` (wycinek 120×120 m, GSD 0,05 m; warianty JPG/PNG w archiwum) + kontekst 400 m @0,25 m/px
- Skorowidz ortofotomapy WFS: `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WFS/Skorowidze` — dla wycinka: nalot **2025**, GSD 0,05 m (skorowidz.xml w archiwum)
- BDOT10k/NMPT: nie pobrano (usługi PZGIK bez odpowiedzi w sesji — patrz README sekcja 9)

## 4. Dokumenty urzędowe (ISAP/ELI)
- Rozporządzenie MRB w sprawie znaków i sygnałów drogowych (Dz.U. 2019 poz. 2311 z późn. zm.):
  - ELI: `https://eli.gov.pl/eli/DU/2019/2311/ogl`
  - Tekst (PDF c1): `https://eli.gov.pl/api/acts/DU/2019/2311/text/I/D20192311-c1.pdf` (525 str.; zał. 1 — znaki pionowe)
  - Załączniki (PDF c2): `https://eli.gov.pl/api/acts/DU/2019/2311/text/I/D20192311-c2.pdf` (381 str.; zał. 2 — znaki poziome)
  - Cytowane strony: tabela 1.1 (Dz.U. str. 4/PDF 9), tabela 1.11 (str. 32/PDF 37), odległość od jezdni (str. 26/PDF 31), B-20 (str. 91/PDF 96), tabela 3.1 (str. 92/PDF 97), B-33 (str. 135/PDF 140), C-2 (str. 154/PDF 159)

## 5. Źródła sprawdzone bez wyników / niedostępne
- **Panoramax** (CC BY-SA 4.0): API `https://api.panoramax.xyz/api/search?bbox=23.1870,53.1070,23.1950,53.1120` — 0 kadrów (2026-11-13)
- **KartaView**: API `https://api.kartaview.org/2.0/photo/?lat=53.1095&lng=23.1906&radius=5000` — 0 zdjęć w promieniu 5 km (kontrola pozytywna: API odpowiada)
- **Openverse**: API `https://api.openverse.org/v1/images/?q=...` — HTTP 504 (retry), następnie strona challenge Cloudflare — 0 kadrów
- **Mapillary**: brak tokenu — nie sondowano (zgodnie z zasadami D43/zadania)
- **Google Maps/Street View/Earth/3D Tiles**: ZAKAZ — nieużyte

## 6. Narzędzia i metody
- Oględziny kadrów: analiza obrazu (pytania tematyczne, wielokrotne niezależne odczyty); liczby z wizji tylko jakościowo (lekcja P6 — brak powtarzalności)
- Pomiar szerokości wjazdu: cięciwa między node'ami geometrii OSM (metoda P6 G07/G08) + rzut prostopadły; obliczenia w EPSG:2180
- Ekstrakcja tekstu PDF: własny parser (tabele /Contents + ToUnicode CMap); dekoder PNG (zlib + unfilter) do analizy orto
