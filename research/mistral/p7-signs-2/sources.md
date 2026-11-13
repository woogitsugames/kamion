# Źródła — research/mistral/p7-signs-2

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
  - stanton, 2019-08-15: ul. Gen. S. Maczka (WS) → łącznica → rondo Putry → al. Tysiąclecia (N) do ~53.171.
  - stanton, 2019-09-01: al. Tysiąclecia (S) → rondo Putry → ul. Gen. S. Maczka (WB).
  - 1 zdjęcie 2020-11-24 (a68677d0…, Maczka WB, az=265).
  - su91, 2025-10-03: DK65 SE od Grabówki (2 zdjęcia, az=207) — jedyne zdjęcia korytarzowe 2025 w Panoramax.
  - su91, 2025-09-02: Karakule (droga lokalna; poza korytarzami zadania — tylko weryfikacja pokrycia).
  - mapcomplete, 2026-11-11: ul. Jarzębinowa (osiedlowa — poza korytarzami zadania).
  - ZX_OSM_USER, 2026-09-22: ul. Swobodna (do weryfikacji przydatności).

### Wikimedia Commons (commons.wikimedia.org)
- API: geosearch (gsprimary, promienie od punktu ronda Putry), imageinfo (licencja, autor, data, wymiary).
- Rate-limit agresywny (429) — pobieranie z backoffem i pauzami.
- Autor Rakoon, licencja CC0 (tekstura dozwolona). Wybrane serie w promieniu ~10 km od ronda:
  - 2021-04-30/05-03/05-26 (użyte już przez G3 — nie powtarzam, tylko odsyłam),
  - 2022-07-25 (użyte przez G3 jako G3-C006..C011),
  - **2022-12-03 (najbliższy kadr 27.6 m od środka ronda — nowa obserwacja)**,
  - **2022-10-16 (okazała się ścieżkami leśnymi — po przydatnością wykluczona)**,
  - **2024-02-19, 2024-04-01, 2024-05-15, 2024-05-30, 2024-06-08, 2024-06-26, 2024-11-13, 2024-12-22,
    2024-12-29** — triage w toku,
  - **2025-02-08, 2025-03-02, 2025-04-02 (Rakoon, CC0)** — najnowsze kadry w promieniu ~1–1.6 km od ronda
    (triage w toku; żaden do tej pory nie pokazuje samych bramownic ronda).

### OSM (api.openstreetmap.org)
- `GET /api/0.6/map?bbox=left,bottom,right,top` — chunki ~0.02°; refs jezdni wokół ronda Putry:
  Andersa E: `19;65`, Maczka W: `8;65`, al. Tysiąclecia N: `8;19` (potwierdzenie geometrii, nie treści tablic).

## Sprawdzone i niedostępne / wykluczone

- **KartaView** (api.openstreetcam.org, api.kartaview.org): endpointy nie odpowiadają (HTTP 000/404)
  — brak danych z tego źródła; udokumentowane próby.
- **Mapillary**: wymaga tokenu autoryzacyjnego, którego nie posiadam; zgodnie z zasadami — nie zgaduję
  kluczy; materiał Mapillary oznaczam UNVERIFIED / tylko referencja.
- **Google Maps/Street View/Earth/3D Tiles**: zakazane w zadaniu — nieużywane.
- **Openverse** (api.openverse.org): działa; kwerendy w rejonie Białegostoku nie zwróciły zdjęć bramownic
  ronda Putry poza tymi już obecnymi w Commons (do uzupełnienia po dokończeniu triage).

## Licencje i użycie

- CC BY-SA 4.0 (Panoramax): odczyt tekstu z kadru = dozwolony; **tekstura w grze: NIE
  (share-alike)** — oznaczenie „referencja, nie tekstura" w kolumnie uwagi/README.
- CC0 (Rakoon/Commons): tekstura dozwolona.
- Dokumenty urzędowe (BIP GDDKiA/ZDiT): art. 4 pr. aut. — dozwolone cytowanie/odczyt.
