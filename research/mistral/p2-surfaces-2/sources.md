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
   - HTML ELI (api.sejm.gov.pl): https://api.sejm.gov.pl/eli/acts/DU/2019/2311/text.html —
     załączniki w HTML oznaczone „patrz oryginał” (tekst zał. 2 niedostępny w HTML; odczyt
     2026-11-13, sesja M52-FIX).
   - Licencja: dokument urzędowy (Dz.U.), domena publiczna / wolne wykorzystanie.
   - Mapowanie stron: PDF c2 str. N = Dz.U. str. N+525 (PDF s.1 = Dz.U. s.526).
   - Rysunki zał. 2 są rastrowe; w M52 odczyt programowy (binaryzacja + identyfikacja glifów +
     walidacja skali z wartości znanych z tekstu). **M52-FIX: semantyka podpisów dolnych
     (zużycie farby m²/mb) i etykiety „4,00”/„2,00” (kreska/przerwa) ustalone na podstawie
     odczytów wizualnych przeglądu s17 (poz. 13) + walidacji arytmetycznej.**
   - Uwaga M52-FIX: PDF c2 (41 MB) nie został ponownie pobrany w sesji rewizji (brak dostępu
     do pobrania binarnego w środowisku sesji); nowe renderowanie i oględziny rysunków —
     zalecane w rundzie z dostępem do PDF.

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

### KartaView (OpenStreetCam) — kadry z kamer pojazdów

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
   - **M52-FIX: wszystkie sekwencje Jaroszówki prowadzą estakadą Andersa (wiaduktem DK19) nad
     rondem Pamięci Bieżeństwa** (potwierdzenie wizualne przeglądu s17 dla jar-01/07/12/20);
     endpoint nearby-photos (POST) niedostępny w sesji rewizji.

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

- **Panoramax** — M52: 0 zdjęć przy kaflu Jaroszówka; **M52-FIX (2026-11-13, API)**:
  bbox ronda (23.1620–23.1720 E, 53.1505–53.1540 N — całe rondo + wloty + ring) → **0 kadrów**;
  szerszy bbox (~3,2 × 2,1 km) → 6 kadrów w klastrze rondo Putry (~1,2 km od kafla — inne
  skrzyżowanie). Zapytanie: `https://api.panoramax.xyz/api/search?bbox=23.1620,53.1505,23.1720,53.1540`.
  Wynik negatywny zapisany w manifeście jako M52-117.
- **Mapillary**: brak tokenu API w środowisku → pominięte; ewentualne użycie = UNVERIFIED.
- **Google Maps / Street View / Earth / 3D Tiles**: zakazane (zasady paczki) — niewykorzystane.
- **Blogi / portale branżowe (tioman.pl itp.)**: źródła wtórne, odrzucone jako niepotwierdzające
  (wymiary znaków P-* tylko z Dz.U.). **M52-FIX: tioman.pl (linia warunkowego zatrzymania)**
  użyty wyłącznie do kontroli krzyżowej hipotez reinterpretacji P-12/P-13/P-14 — nie stanowi
  podstawy żadnego statusu.
- Wszystkie PDF urzędowe użyte w analizie ≤5 MB; JPG ≤1600 px.

## Źródła rewizji M52-FIX (13.11.2026)

13. **Przegląd s17 — `docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p6p8p9p5.md`**
    (repozytorium, origin/main) — **źródło odczytów wizualnych** użytych w rewizji:
    - rysunki zał. 2 (oględziny): 2.2.1.8 (s. 538) — P-3a: linie 0,12 / odstęp 0,12 / 0,12,
      kreska 4,00, przerwa 2,00, podpis „0,20 m²/mb”; 2.2.1.10 (s. 540) — P-4: 0,12×3,
      podpis 0,24; 2.2.1.11 (s. 540) — P-5: 0,12×3, kreska 4,00 / przerwa 2,00, podpis 0,32;
      2.2.1.12 (s. 541) — P-6: 0,12, kreska 4,00, przerwa 2,00, podpis 0,08;
    - kadry Jaroszówki (oględziny jar-01/07/12/20): estakada Andersa nad rondem — bariery
      mostowe, kominy EC w tle, latarnie dwuramienne;
    - wytyczne ZDM 2025 i wymogi (płytki, wyspy) — cytaty potwierdzone.
    - Licencja: dokument wewnętrzny repozytorium (origin/main).
14. **Panoramax API** — zapytania bbox (2026-11-13): rondo Jaroszówka → 0 kadrów;
    szeroki bbox → 6 kadrów (klaster rondo Putry). Zapis negatywu: manifest M52-117.

## Źródła i metody rewizji M52-FIX r2 (13.11.2026)

15. **Render stron Dz.U. (oględziny rysunków, zad. 1)** — ten sam dokument co poz. 1
    (Dz.U. 2019 poz. 2311, zał. 2 = część c2 PDF z eli.gov.pl,
    `https://eli.gov.pl/api/acts/DU/2019/2311/text/I/D20192311-c2.pdf`).
    Metoda r2: render stron **150 dpi** + ekstrakcja obrazów rastrowych w natywnej
    rozdzielczości ×3. PyMuPDF niedostępny w sesji — użyto własnego parsera PDF
    (dekompresja strumieni, dekodowanie DCTDecode/FlateDecode). Obejrzano każdy rysunek
    z zakresu M52: P-2a/b, P-3a/b, P-4, P-5, P-6, P-7a/b/c/d, P-10 (suplement),
    P-11, P-12, P-13, P-14, P-21a/b, P-23, P-25; odczyty etykiet zweryfikowano
    pikselowo (proporcje kreska:przerwa, podstawa:wysokość:odstęp w skali rysunku).
    Mapowanie stron bez zmian: PDF c2 str. N = Dz.U. str. N+525.
16. **Panoramax API** (r2, 2026-11-13): bbox ronda Jaroszówka
    (`https://api.panoramax.xyz/api/search?bbox=23.1620,53.1505,23.1720,53.1540`) → 0 kadrów;
    szersze bboxy → 0; bardzo szeroki (23.13–23.20 E, 53.14–53.17 N) → 10 kadrów
    w klastrze ~1,3 km NW od ronda (poza rondem).
17. **KartaView API** (r2, 2026-11-13): `https://api.kartaview.org/2.0/photo/` — zapytania
    z 2 punktów (kafl 53.1520/23.1680; środek ronda 53.1515/23.1665), promień 100/300/500 m
    → w każdym przypadku wyłącznie 3 sekwencje estakadowe (14055, 2769366, 3686129;
    dist 0–42 m), brak innych sekwencji; promień >500–800 m → HTTP 400; endpoint
    POST /nearby-tracks: timeout/niezawodny; `api.openstreetcam.org`: wygasł
    (cert mismatch + Azure 404). **Mapillary**: brak tokenu → niesprawdzony.
    Wynik negatywny zapisany w manifeście M52-117.
18. **Wyszukiwanie WWW** (r2, 2026-11-13, 2 zapytania) o czerwonym asfalcie na trasie
    startowej — bez źródła; status koloru pozostaje UNVERIFIED.

### Ograniczenia r2 (jawne)

- Kadry fotograficzne (Jaroszówka, trasa, przejścia, Rynek) **nie zostały obejrzane w r2** —
  limit 20 analiz obrazu na odpowiedź sesji wyczerpany na rysunkach Dz.U. (priorytet
  zadania 1). Opisy kadrów: przegląd s17 (jar-01/07/12/20) + podstawy przypisania
  (przebieg sekwencji, azymuty, pozycje).
- Kolumny `kolor_srgb`/`metoda_koloru` usunięte ze schematu manifestu (19 → 17 kolumn);
  wartości RGB Rynku przeniesione do uwag z adnotacją o niewiarygodności.
