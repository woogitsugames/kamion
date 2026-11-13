# M52 — Źródła

Konwencja statusów: SOURCED (potwierdzone źródłem urzędowym), UNVERIFIED, ESTIMATED (z metodą),
REFERENCE_ONLY (NC/ND), REFERENCE_NOT_TEXTURE (CC BY-SA — referencja, nie tekstura).

## Prawo / dokumenty urzędowe

### ELI / Dz.U.

1. **Obwieszczenie Ministra Infrastruktury z dnia 9 września 2019 r. w sprawie ogłoszenia
   jednolitego tekstu rozporządzenia Ministra Infrastruktury w sprawie szczegółowych warunków
   technicznych dla znaków i sygnałów drogowych** — Dz.U. 2019 poz. 2311.
   - ELI: https://eli.gov.pl/eli/DU/2019/2311/1
   - PDF (zał. 2, znaki poziome — część c2): https://eli.gov.pl/api/acts/DU/2019/2311/text/I/D20192311-c2.pdf
   - PDF (tekst gł. + zał. 1 — część c1): https://eli.gov.pl/api/acts/DU/2019/2311/text/I/D20192311-c1.pdf
   - Licencja: dokument urzędowy (Dz.U.), domena publiczna / wolne wykorzystanie.
   - Mapowanie stron: PDF c2 str. N = Dz.U. str. N+525 (PDF s.1 = Dz.U. s.526).
   - Rysunki zał. 2 są rastrowe; wymiary odczytane z rysunków metodą programową
     (binaryzacja + identyfikacja glifów + weryfikacja skali z rysunków o znanych wymiarach
     z tekstu: P-7 — 0,24/0,12 m; P-10 — przejście 4,0 m; P-11 — 1,8/3,0 m; tabela 5.3 — P-21).

### BIP Białystok (zadania 3, 5, 6)

2. **„Wytyczne do projektowania dokumentacji projektowej budowy, rozbudowy i przebudowy ulic
   w Białymstoku” — wersja „13 LIPCA 2018 R. / 2025 R.”** (aktualna; nowsza niż zał. 5 z 13.07.2018).
   - BIP zasób 103311 (PDF, 21 str., 1,6 MB):
     https://www.bip.bialystok.pl/resource/103311/Za%C5%82.+nr+5_Wytyczne+do+projektowania.pdf
   - Odczyty: płytki dotykowe przy zejściach (pkt II.2), azyle/wyspy dzielące (str. 20),
     włazy/wpusty (pkt III.11–III.13, PN-EN 124).
   - Licencja: dokument urzędowy (BIP). Data dostępu: 2026-11-13.
3. **Stara wersja wytycznych (13.07.2018)** — BIP zasób 99308; kopia z SWW (PDF, 22 str.):
   https://www.bip.bialystok.pl/resource/99985/143161/Za%C5%82.+nr+5_wytyczne+do+projektowania.pdf
   - Użyta wyłącznie do porównania zmian 2025 vs 2018. Data dostępu: 2026-11-13.
4. **bialystok.pl — „Dekada Rynku Kościuszki”** (otwarcie po modernizacji: 7.08.2009):
   https://www.bialystok.pl/pl/aktualnosci/dekada-rynku-kosciuszki — kontekst zadania 5.
   (strona urzędowa UM Białystok). Data dostępu: 2026-11-13.

### Artykuły naukowe (zadanie 5)

5. **Tofiluk W. (2015)**, *Central square in Białystok — changes in the city’s main public
   space in the 21st century*, Civil and Environmental Engineering Reports (CEER)
   2015;19(4):121–131. DOI: https://doi.org/10.1515/ceer-2015-0058
   - Ustalenie: nawierzchnia Rynku Kościuszki = płyty granitowe + kostka brukowa;
     modernizacja 2006–2009; projekt: Zenon Zabagło (konkurs SARP).
   - Licencja: artykuł naukowy (cytowanie faktów; nie materiał teksturny).
6. **Grycel A. (2016)**, *Rewitalizacja Rynku Kościuszki w Białymstoku* (academia.edu) —
   tylko referencja, brak dostępu do pełnych wymiarów płyt → niepotwierdzające.

## Zdjęcia (zadania 2–5)

### KartaView (OpenStreetCam) — kadry z poziomu jezdni

7. **KartaView (dawniej OpenStreetCam) — zdjęcia: API + CDN** — licencja **CC BY-SA 4.0**
   → w projekcie komercyjnym: REFERENCE_NOT_TEXTURE (referencja kolorystyczna/geometryczna,
   nie tekstura).
   - API: `POST https://api.kartaview.org/1.0/list/nearby-photos/` (lat, lng, radius w metrach).
   - CDN: `https://cdn.kartaview.org/insecure/<base64 nazwa pliku>` (pole `name` z API).
   - Sekwencje użyte (dostęp 2026-11-13, HTTP 200):
     - https://kartaview.org/sequence/14055 (2016-08-24, user ziozzzzz) — Jaroszówka + Andersa;
     - https://kartaview.org/sequence/2769366 (2019-08-25, user gpsmapper999) — Jaroszówka + Andersa;
     - https://kartaview.org/sequence/3686129 (2021-06-23, user TMishaaa) — Jaroszówka, Andersa, Tysiąclecia/Sokólska;
     - https://kartaview.org/sequence/1155711 (2018-03-23, user telenavdrives) — trasa startowa (kontekst).
   - Kadry przekadrowane do ≤1600 px; pola: data, azymut (heading), pozycja WGS84 — patrz manifest.

### Wikimedia Commons (zadanie 5 — Rynek Kościuszki)

8. **„6321 August 2019 in Rynek Kosciuszki Bialystok.jpg”** — autor: Rakoon; licencja **CC0**
   (użycie komercyjne dozwolone). https://commons.wikimedia.org/wiki/File:6321_August_2019_in_Rynek_Kosciuszki_Bialystok.jpg
9. **„6323 Rynek Kosciuszki in Bialystok, August 2019.jpg”** — autor: Rakoon; licencja **CC0**.
   https://commons.wikimedia.org/wiki/File:6323_Rynek_Kosciuszki_in_Bialystok,_August_2019.jpg
10. **„Rynek Kościuszki in Białystok (1).jpg”** — autor: Radosław Botev; licencja
    **CC BY 3.0 pl** (komercyjne OK z atrybucją; traktowane jako referencja kolorystyczna).
    https://commons.wikimedia.org/wiki/File:Rynek_Ko%C5%9Bciuszki_in_Bia%C5%82ystok_(1).jpg
   - Data dostępu: 2026-11-13. Kadry przekadrowane do ≤1600 px (pliki `files/rynek/` w paczce ZIP).

### OpenStreetMap (dane wektorowe — kontekst organizacyjny)

11. **OSM map API** (bbox centrum Białegostoku, 6 kafelków XML; dostęp 2026-11-13) —
    geometrie ulic, przejścia (`crossing`, `tactile_paving`), azyl (way 287037716,
    `traffic_calming=island`, Świętojańska), surface Rynku Kościuszki.
    Licencja: **ODbL** — dane referencyjne (tylko organizacja/kontekst, nie tekstura).
    https://www.openstreetmap.org/copyright
12. **Nominatim** (geokodowanie nazw ulic; wymagany UA; dostęp 2026-11-13).

### Źródła sprawdzone i odrzucone / niedostępne

- **Panoramax**: 0 zdjęć przy kaflu Jaroszówka (najbliższe ~1,5 km, DK8 na północy) —
  sprawdzone, odnotowane; brak materiału do zadań 2–4.
- **Mapillary**: brak tokenu API w środowisku → pominięte; ewentualne użycie = UNVERIFIED.
- **Google Maps / Street View / Earth / 3D Tiles**: zakazane (zasady paczki) — niewykorzystane.
- **Blogi / portale branżowe (tioman.pl itp.)**: źródła wtórne, odrzucone jako
  niepotwierdzające (wymiary znaków P-* tylko z Dz.U.).
- Wszystkie PDF urzędowe użyte w analizie ≤5 MB; JPG ≤1600 px.
