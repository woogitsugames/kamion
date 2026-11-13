# sources.md — źródła i metody (P1B, luki paczki P1)

Data dostępu do wszystkich źródeł: **2026-11-13** (uzupełnienia API podczas audytu: 2026-11-13).

## Dozwolone źródła — co użyto

### 1. KartaView (dawn. OpenStreetCam) — główne źródło kadrów poziomu kierowcy
- API: `POST https://api.kartaview.org/1.0/list/nearby-photos/` (parametry lat, lng, radius [m]) — siatka 40 punktów (5×8), promień 2500 m; pobrano **4373 kadrów** w obszarze zainteresowania.
- Metadane pojedynczych kadrów: `GET https://api.kartaview.org/2.0/photo/?id=<id>` — pozycja (lat/lng), `heading` (azymut kamery w stopniach), `shotDate`, `storage`, `imageLthUrl` (plik 1280×720 przez CDN `cdn.kartaview.org/pr:sharp/<base64>`).
- Obrazy: wariant `lth` 1280×720 (≤1600 px, wymóg spełniony). Uwaga: host `storage*.openstreetcam.org` bywa niedostępny (HTTP 502) — pobierano przez CDN KartaView.
- **Licencja: CC BY-SA 4.0** (zgodnie z warunkami serwisu KartaView; pole license nie występuje w API). Konsekwencja: kadry KartaView w pakiecie Kamion służą jako **referencja, nie tekstura** (ShareAlike); autorzy (użytkownicy KartaView) podani w kolumnie `autor`: telenavdrives, TMishaaa, gpsmapper999, ziozzzzz.
- Sesje użyte w P1B: telenavdrives 2018-03-23 (trasa: ulice willowe — Białostoczek, Kombatantów/Sokólska, Motoszko, Wileńska, Skidelska, Bitwy Białostockiej, wiadukt Al. Tysiąclecia), TMishaaa 2021-06-23 (Andersa/rondo), gpsmapper999 2019-08-25 (Batorego/rondo), ziozzzzz 2016-08-24 (rondo/bypass Andersa).

### 2. Wikimedia Commons — kadrach z poziomu drogi/pieszego, licencja CC0
- Geowyszukiwanie: `action=query&generator=geosearch&ggscoord=...&ggsradius=...&ggsnamespace=6` (prefiks ggs wymagany); metadata: `prop=imageinfo&iiurlwidth=1280&iiprop=url|size|extmetadata`.
- Wybrane pliki: seria „…December 2022 in Białystok” (2022-12-03), „April 2024 in Białystok” (2024-04-01), „Rondo Pamięci Bieżeństwa…” (2020-11-02), „Sitarska Street…” (2019-11-09) — wszystkie **CC0, autor: Rakoon**.
- Obrazy: miniatury 1280×720 (≤1600 px ✓). Pozycje z EXIF GPS; brak EXIF GPSImgDirection → kierunek `UNVERIFIED`.

### 3. Panoramax — sprawdzone, brak kadrów wypełniających luki
- `GET https://api.panoramax.xyz/api/search?bbox=23.06,53.13,23.20,53.175&limit=500` — **280 kadrów** w obszarze (producer: stanton 2019-08/09 — korytarze Andersa/Tysiąclecia/Maczka; mapcomplete/ZX_OSM_USER 2026-09/11 — rejon zachodni, poza celami; 2020-11 — 1 kadr poza celami).
- Licencja CC BY-SA 4.0 (pole license w API); azymut z `properties.view.azimuth`.
- **Wynik: żaden kadr Panoramax nie wypełnia luk P1B** → w manifest.csv kolumna `panoramax_id` pusta (odnotowano dla jasności; porównanie deduplikacyjne po `panoramax_id`/URL wykonano wobec pustego zbioru).

### 4. Openverse — sprawdzone, 0 wyników
- `GET https://api.openverse.org/v1/images/?q=<nazwa ulicy> Białystok` dla wszystkich ulic luk — **result_count=0**; źródło pominięte (brak materiału).

### 5. Mapillary — NIE sprawdzono: brak tokenu API
- Zgodnie z zasadą „nie zgaduj kluczy”: Mapillary **UNVERIFIED/pominięty**.

### 6. OpenStreetMap — geometrie osi ulic i struktur
- `GET https://api.openstreetmap.org/api/0.6/map.json?bbox=...` — 45 kafli (siatka: lat 53.136–53.172, lon 23.076–23.184); odstępy ≥5 s między kafelmi.
- Ways użyte do przypisania: nazwane ulice + struktury (ids w README).

## Źródła ZAKAZANE — nie użyto
- Google Maps / Street View / Earth / 3D Tiles: **nie wykorzystano w żadnym kroku**.

## Metody
- **Przypisanie do ulicy**: dystans equirectangular do lokalnego układu XY (R=6371000; oś Y przez lat0), odległość punkt–odcinek z clampem t∈[0,1]; kadr przypisano do ulicy, gdy dystans do osi way OSM ≤ **25 m** (metoda identyczna dla KV/Pmax/Commons). Gdy kadr leży ≤25 m od osi dwóch ulic (Kombatantów/Sokólska — wspólna jezdnia), przypisano do **najbliższej** osi i odnotowano w uwagach.
- **Kierunek (azymut)**: z API KartaView (pole heading, stopnie) lub EXIF; dla Commons bez EXIF GPSImgDirection → `UNVERIFIED`.
- **Sezon**: z daty + weryfikacja wizualna (model wizyjny, wywołania na miniaturach): liście / bez liści / śnieg.
- **Pora dnia**: z godziny EXIF/API + weryfikacja wizualna (wszystkie OK-kadry: dzień).
- **Wymiary plików**: KartaView lth 1280×720; Commons thumb 1280×720 (wymóg ≤1600 px ✓).
- **Selekcja**: priorytet 2023+, dzień, bez rozmycia, bez dużych pojazdów; kadry sprzeczne z celem (sezon) lub nocne/wschodniosłone → status ODRZUCONE z powodem w kolumnie `odrzucone_powód`.
- **Deduplikacja**: manifest P1 nie istnieje w repo (sprawdzono main/gałęzie/PR/code search) → deduplikacja wewnątrz zbioru P1B po id źródła i URL.
