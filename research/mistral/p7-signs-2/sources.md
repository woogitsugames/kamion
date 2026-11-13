# Źródła — research/mistral-p7-signs-2

Wszystkie daty dostępu: 2026-11-13 (chyba że zaznaczono inaczej). Zdjęcia pobierano wyłącznie z licencji
dozwolonych w komercyjnym użyciu (CC0, CC BY, CC BY-SA 4.0, dokumenty urzędowe — art. 4 pr. aut.).

## Dozwolone i użyte

### Panoramax (api.panoramax.xyz)
- Endpoint zdjęć: `GET /api/search?bbox=left,bottom,right,top` (kolejność rogów: lewy-dolny, prawy-górny),
  paginacja przez `links[].rel="next"`. Zdjęcia HD: pole `assets.hd.href` w feature (host
  panoramax.openstreetmap.fr).
- Licencja: domyślnie CC BY-SA 4.0. **Share-alike: zdjęcia Panoramax służą jako referencja/odczyt tekstu,
  nie jako tekstura w grze.**
- Autorskie harvesty (pliki robocze, poza repo): pan_putry.json (93), pan_north.json (200),
  pan_ne65.json (147), pan_west.json (200), pan_south.json (200), pan_nefix.json (137).
- Kluczowe sekwencje:
  - stanton, 2019-08-15: ul. Gen. S. Maczka (WS) → łącznica → rondo Putry → al. Tysiąclecia (N) do ~53.171
    — użyta dla P7-005..P7-008 (PUTRY_W_GANTRY, wjazdy na rondo) i P7-006 (bramownice NB za rondem).
  - stanton, 2019-09-01: al. Tysiąclecia (S) → rondo Putry → ul. Gen. S. Maczka (WB) — użyta dla
    P7-001..P7-003 (najazd N) i P7-009 (konstrukcja na Maczka W).
  - 1 zdjęcie 2020-11-24 (a68677d0…, Maczka WB, az=265) — brak bramownicy w kadrze, wykluczone.
  - su91, 2025-10-03: DK65 SE od Grabówki — po geokodowaniu: wieś Grabówka ul. Jodłowa (polana z krzyżem),
    NIE korytarz DK65 — wykluczone.
  - su91, 2025-09-02: Karakule; mapcomplete, 2026-11-11: ul. Jarzębinowa; ZX_OSM_USER, 2026-09-22:
    ul. Swobodna — poza korytarzami zadania.
- UWAGA metodyczna: w serii stanton 2019-09-01 (jazda WB) EXIF GPSImgDirection jest błędny (14–21° przy
  trajektorii wyraźnie zachodniej, lon maleje 23.1511→23.1443) — azymut przyjmowano z view:azimuth
  Panoramax (268°), co udokumentowano w P7-009.

### Wikimedia Commons (commons.wikimedia.org)
- API: geosearch (gsprimary, `gsnamespace=6` — uwaga: nie „namespace"), promienie od punktu ronda Putry;
  imageinfo (licencja, autor, DateTimeOriginal, wymiary, GPS w extmetadata; klucze „File:…" z podkreślnikami
  w zbiorcach meta, nazwy ze spacjami).
- **Rate-limit agresywny (429)** — praktyka: backoff rosnący (10/20/30 s), pauzy ~4–8 s między plikami,
  pobieranie batchami po 5 tytułów. Przy 429 na upload.wikimedia.org pomaga odczekanie; thumb 1600 px
  (iiurlwidth=1600) zamiast oryginałów. Uwaga: dla części plików API zwraca thumb 1920 px mimo
  iiurlwidth=1600 — każdy plik w files/ dodatkowo przeskalowywano w dół do ≤1600 px.
- Autor Rakoon, licencja CC0 (tekstura dozwolona). Geokwerenda korytarzy (systematyczny triage): odległość
  pliku ≤60 m od osi korytarzy (Tysiąclecia N-S lon≈23.1518; Andersa E lat≈53.1587; Maczka W lat≈53.1595)
  i ≤900 m od ronda → 40 plików-kandydatów. Wyniki triage:
  - 2021-04-30/05-03/05-26 — użyte już przez G3 (odsyłam, nie powtarzam).
  - 2022-07-25: seria G3-C006..C011 (bramownice ronda) + NOWE 5 kadrów z najazdu S pobranych w tej paczce
    (132504/132632/132659/132717/132812, 181–334 m od ronda): 132632 → P7-010 (tablica kierunkowa na słupie,
    treść UNVERIFIED); pozostałe kadry bez oznakowania ronda (Shell/Bricomarché, zabudowa; 132504: zgłoszona
    przez model „bramownica Gdańsk/Gdynia/Sopot" NIEPOTWIERDZONA na wycinkach pełnej rozdzielczości — odrzucona).
  - 2022-12-03: najbliższy kadr 27.6 m od środka ronda — skrzyżowanie, bez bramownicy w kadrze.
  - 2022-10-16: ścieżki leśne — wykluczona.
  - 2024-02-19, 2024-04-01, 2024-06-26, 2024-11-13, 2024-12-22, 2024-12-29, 2025-02-08, 2025-03-02,
    2025-04-02: triage zakończony (geotagi + odczyty wzrokowe) — kadry miejskie/podmiejskie 0,9–1,3 km od
    ronda lub poza osiami korytarzy; brak oznakowania korytarzy ronda. Wyjątki na osi Tysiąclecia S
    (103324, 112303, 112827, 122602): ulice/osiedla, brak tablic kierunkowych korytarza (rower, tablice
    uliczne „ul. Wileńska"/„ul. Grodzieńska", budynek mieszkalny).
  - 2024-05-30: seria Jurowce (18 plików CC0, las/staw — wykluczona) + **122644 → P7-004** (tablica E-1,
    SOURCED) + 122501 (1,1 km SE od ronda, jedna nieczytelna tablica przydrożna — poza korytarzami) +
    122602 (patrz wyżej).

### OSM (api.openstreetmap.org)
- `GET /api/0.6/map?bbox=left,bottom,right,top` — chunki ~0.02°; refs jezdni wokół ronda Putry:
  Andersa E: `19;65` (do ronda Św. Cyryla i Metodego, dalej DW676), Maczka W: `8;65`, al. Tysiąclecia N:
  `8;19`, Wasilków trunk: `19`. Korytarz północny: DK8 przez Zawady→Jurowce→Korycin; S8 kończy się w
  Choroszczy (węzeł Białystok Zachód), S19 obwodnica płn.-zach. (potwierdzenie geometrii, nie treści tablic).

### Dokumenty urzędowe i media (art. 4 pr. aut.; użyte do osi czasu — szczegóły w timeline_andersa.md)
- bialystok.pl, 03.07.2019 — organizacja ruchu: 2 pasy skrętu ku Augustowowi (łącznica/rondo).
- gov.pl (GDDKiA), 14.10.2025 — DK65 Fasty: powrót na stały przebieg.
- gov.pl, 20.10.2026 — S19 Krynice–Białystok Zachód otwarta; węzeł łączy S19+S8.
- bialystokonline, 02.12.2025 — wymiana tablic ZDiT (Ciołkowskiego/Suchowolca; kierowanie TIR >3,5 t).
- radioriva, 5.11–18.12.2026 — prace przy ul. Andersa (nie numeryzują treści bramownic ronda).
- Numery zarządzeń ZDiT dot. epok bramownic Andersa: NIE ZNALEZIONO w dostępnych BIP — udokumentowane jako brak.

## Sprawdzone i niedostępne / wykluczone

- **KartaView** (api.openstreetcam.org, api.kartaview.org): endpointy nie odpowiadają (HTTP 000/404)
  — brak danych z tego źródła; udokumentowane próby.
- **Mapillary**: wymaga tokenu autoryzacyjnego; zgodnie z zasadami — nie zgaduję kluczy; materiał Mapillary
  oznaczam UNVERIFIED / tylko referencja (epoki G3: 2021-05, 2022-07-25, 2024-07, 2024-08-15).
- **Google Maps/Street View/Earth/3D Tiles**: zakazane w zadaniu — nieużyte.
- **Openverse** (api.openverse.org): działa; kwerendy w rejonie Białegostoku nie zwróciły zdjęć bramownic
  ronda Putry poza tymi już obecnymi w Commons.
- **su91 2025-10-03 (Panoramax)**: geokodowanie (Nominatim) wykazało wieś Grabówka/ul. Jodłowa — polana
  z krzyżem, NIE korytarz DK65 — wykluczone.

## Licencje i użycie

- CC BY-SA 4.0 (Panoramax): odczyt tekstu z kadru = dozwolony; **tekstura w grze: NIE (share-alike)**
  — oznaczenie „referencja, nie tekstura" w kolumnie uwagi/README.
- CC0 (Rakoon/Commons): tekstura dozwolona.
- Dokumenty urzędowe (BIP GDDKiA/ZDiT): art. 4 pr. aut. — dozwolone cytowanie/odczyt.