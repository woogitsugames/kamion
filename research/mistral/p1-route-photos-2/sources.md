# sources.md — źródła i metody (P1B, luki paczki P1), wersja 2 po M46-FIX

Data dostępu do wszystkich źródeł: **2026-11-13** (sesja poprawki M46-FIX: wyszukiwania świeże, tego samego dnia).

## Dozwolone źródła — co użyto

### 1. KartaView (dawn. OpenStreetCam) — główne źródło kadrów poziomu kierowcy
- API: `POST https://api.kartaview.org/1.0/list/nearby-photos/` (lat, lng, radius [m]) — w sesji M46-FIX
  wykonano **50 świeżych zapytań** wokół punktów celów (luki 1–4: osie Batorego/Brzeskiej/Buskiej/Olsztyńskiej,
  rondo + łącznice, 9 ulic luki 4, wiadukty Maczka) → **554 unikalne kadrów** po deduplikacji po id.
  Wynik negatywny dla luk: żaden kadr ≤25 m od osi ulic luki z azymutem wzdłuż osi (dostępne serie
  przejazdów: Al. Tysiąclecia 2018-03, Andersa 2019-08/2021-06, estakada nad rondem 2016-08/2019-08/2021-06).
- Metadane pojedynczych kadrów: `GET https://api.kartaview.org/2.0/photo/?id=<id>` — pozycja, `heading`
  (azymut kamery), `shotDate`, `storage`, `imageLthUrl`. Wszystkie kadry manifestu zweryfikowano wobec API
  (pozycja/azymut/data zgodne).
- Obrazy: wariant `lth` 1280×720 (≤1600 px ✓). **Fallback storage**: gdy CDN `cdn.kartaview.org` zwraca błąd
  (azure download error), plik często jest dostępny bezpośrednio z `storage*.openstreetcam.org` — tak odzyskano
  część kadrów; kadry P1B-016 i P1B-043 są trwale niedostępne (BlobNotFound i na CDN, i na storage1–5).
- **Licencja: CC BY-SA 4.0** (warunki serwisu KartaView). Kadry służą jako **referencja, nie tekstura**
  (ShareAlike); autorzy w kolumnie `autor`: telenavdrives, TMishaaa, gpsmapper999, ziozzzzz.
- Sesje użyte w P1B: telenavdrives 2018-03-23 (Al. Tysiąclecia: wiadukt, skrzyżowania, wiadukt kolejowy 1955;
  2016-10-03: Maczek/Tysiąclecia), TMishaaa 2021-06-23 (Andersa, estakada nad rondem), gpsmapper999 2019-08-25
  (Andersa, estakada, Maczek), ziozzzzz 2016-08-24 (estakada/łącznica nad rondem — P1B-048 = KV 7119871).

### 2. Wikimedia Commons — kadry z poziomu drogi/pieszego, licencja CC0
- Geowyszukiwanie: `action=query&generator=geosearch&ggscoord=...&ggsradius=...&ggsnamespace=6`
  (prefiks ggs); metadata: `prop=imageinfo&iiurlwidth=1280&iiprop=url|size|extmetadata`.
- Świeże wyszukiwanie M46-FIX: **586 plików z geolokalizacją** w promieniu ≤1000 m od punktów celów;
  **≤25 m od osi leży 5** (Sitarska ×3 — w tym plik P1B-035; rondo ×2, poziom pieszy — P1-002 z paczki P1
  i plik sąsiedni); **0 plików z poziomu kierowcy/azymutem** dla luk.
- **Autor: Rakoon** (Commons API, CC0) — series „…December 2022 in Białystok” (2022-12-03),
  „April 2024 in Białystok” (2024-04-01), „Rondo Pamięci Bieżeństwa…” (2020-11-02), „Sitarska Street…”
  (2019-11-09). W wersji 1 dla P1B-037, 039–042 podano błędnie „Hollyfeld” — poprawione w M46-FIX.
- Obrazy: miniatury 1280×720 (≤1600 px ✓). Pozycje z EXIF GPS; brak EXIF GPSImgDirection →
  kierunek `UNVERIFIED`, przypisanie wyłącznie po odległości.

### 3. Panoramax — sprawdzone świeżo (2026-11-13), brak kadrów wypełniających luki
- `GET https://api.panoramax.xyz/api/search?bbox=23.095,53.135,23.185,53.172&limit=500` —
  **186 obiektów** w obszarze (korytarze Andersa/Tysiąclecia/Maczka 2019-08/09, rejon zachodni 2026 —
  poza celami; brak azymutów wzdłuż osi ulic luk).
- Licencja CC BY-SA 4.0 (pole license w API); azymut z `properties.view.azimuth`.
- **Wynik: żaden kadr nie wypełnia luk** → kolumna `panoramax_id` pusta.

### 4. Openverse — sprawdzone, 0 wyników
- `GET https://api.openverse.org/v1/images/?q=<nazwa ulicy> Białystok` dla wszystkich ulic luk —
  **result_count=0**; źródło pominięte.

### 5. Mapillary — NIE sprawdzono: brak tokenu API
- Zgodnie z zasadą „nie zgaduj kluczy”: Mapillary **UNVERIFIED/pominięty**.

### 6. OpenStreetMap — geometrie osi ulic i struktur
- `GET https://api.openstreetmap.org/api/0.6/map.json?bbox=...` — **25 kafli** (siatka wokół celów,
  lat 53.135–53.172, lon 23.095–23.185; odstępy ≥5 s między kafelmi). **Overpass API niedostępny**
  (502/timeout) — użyto API `map.json`.
- Ways użyte do przypisania (przykłady): Andersa trunk 560802661/266084685; estakada Andersa nad rondem
  177895177 (`bridge`); ring ronda 536419699 (`junction=roundabout`, pod estakadą); wiadukt Al. Tysiąclecia
  197904073/197904079/882366264; Al. Tysiąclecia 999223586, 258841035, 946729190, 236107504, 536419697 i in.;
  Olsztyńska 363758822; Sitarska 238709156; Bełzy 213244884; Wołkowyska 100927633; Kowieńska 100927657;
  Lidzka 100927659; Grodzieńska 100927679; Maczek most 257355876, wiadukt 173985169; łącznica DK8 249431348.

## Źródła ZAKAZANE — nie użyto
- Google Maps / Street View / Earth / 3D Tiles: **nie wykorzystano w żadnym kroku**.

## Metody (v2)
- **Reguła przypisania (M46-FIX, opisana w README §1)**: kadr → ulica X tylko gdy odległość do osi way X
  ≤25 m ORAZ |azymut kamery − kierunek odcinka X| (mod 180°) ≤30°; jeśli inna ulica bliżej (lub lepiej
  współliniowa) — przypisanie do niej. Kolumny `os_way_id` i `delta_azymutu_deg` w manifeście dokumentują
  wynik reguły. **Zastrzeżenie wysokości**: reguła jest 2D — ring ronda leży pod estakadą Andersa, więc
  kadr z estakady może formalnie spełniać kryteria dla ringu; rozstrzyga weryfikacja obrazu (P1B-048:
  9,6 m od osi ringu, Δ 29,1°, obraz pokazuje estakadę/łącznicę).
- **Deduplikacja z P1 (M46-FIX)**: manifest P1 **istnieje** — `research/gptpro/p1-route-photos/manifest.csv`
  (origin/main). Porównanie plików/URL Commons: P1B-034=P1-004, P1B-036=P1-033, P1B-037=P1-052, P1B-042=P1-053
  → status `DUPLIKAT_P1`. Deduplikacja wewnątrz P1B po id źródła i URL bez zmian.
- **Kierunek (azymut)**: pole `heading` KartaView; Commons bez EXIF GPSImgDirection → `UNVERIFIED`.
- **Sezon / pora dnia**: z daty + weryfikacja wizualna (model wizyjny na każdym dostępnym obrazie — 46/48).
- **Wymiary plików**: KartaView lth 1280×720; Commons thumb 1280×720 (≤1600 px ✓).
- **Selekcja**: priorytet 2023+, dzień, bez rozmycia, bez dużych pojazdów; kadry sprzeczne z celem
  (sezon, trwale niedostępny obraz, nie spełniają reguły przypisania) → status ODRZUCONE z powodem
  w kolumnie `odrzucone_powód`.
- **Punkt_opis**: przepisany po obejrzeniu każdego dostępnego JPG (obiekt/skrzyżowanie/drogowskaz
  widoczny na obrazie), nie na podstawie samych metadanych.
