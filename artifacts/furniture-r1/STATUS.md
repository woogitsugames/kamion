# ADR 0102 — strumień I
Worktree z main 9e6e9fde. Przeczytano wymagane zasady i recenzje; kopie lokalnych danych oraz junctiony referencji przygotowane. Bez telefonów/adb.
NASTĘPNY KROK: uv run --project tools/worldgen python -m pytest tests/gis -q

Audyt: QA bazowe 147 stopni >5 cm, max 1.087 m. Zdjęcie Mapillary p26 obejrzane (referencja lokalna). WIP: kontakt osi z widoczną siatką, fundament -1.25/+0.08 m, obejmy dopasowane do stożka; bez nowych materiałów. Wymiary WORKING_VALUE, ocena Unity nadal oczekuje PHONE_RUN.
NASTĘPNY KROK: uv run --project tools/worldgen python -m pytest tests/gis/test_furniture_r1.py -q

WIP r1: atlas zużycia lokalizowany wysokością (skany CC0 brushed_concrete/corrugated_iron_03), LOD starych lamp i obejmy, U-słupek tylko z tagu OSM, schodkowe przęsła z zakopanymi stopami słupków. Materiały wyłącznie addytywne furniture_*. PHONE_RUN nadal istnieje. Bazowe GIS nadal w toku (testy determinizmu).
NASTĘPNY KROK: uv run --project tools/worldgen python tools/worldgen/roads/build_world.py --region bialystok-industrial-c

GIS bazowe: 370 passed, 1 xfailed / 635.18 s. Regresje ADR0102: 6 passed. Korekta po audycie kodu: fundament -0.45/+0.08 m, lokalne przesunięcie lampy do 1.05 m przy ostrym uskoku zamiast głębokiego zakopania. Jawne wysokości na wiaduktach zachowane. Low starej betonowej lampy 105→91 tris, pozostałe porównane Low bez wzrostu slotów.
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1

Regenerated baseline from 9e6e9fde; furniture source restored to branch HEAD.
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)

Regeneracja bazowego kodu zakończona 297.2 s; QA odtwarza 147 / 1.087 m. W logu brak fallback=True. Dodano stałą kamerę zwykłego ogrodzenia OSM 590134608; kamery mają seat=file, tył znaku wyznaczony z yaw. Import Unity czeka na PHONE_RUN.
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1

Dopracowano mapowanie atlasu: metry fizyczne (9 m atlas dla lamp, 0.9 m dla słupków) zamiast rozciągania strefy brudu z wysokością lampy. Istniejąca stopa otrzymała ten sam skan betonu przez addytywny materiał furniture_footing, bez dodatkowego slotu. Testy regresji: 6 passed.
NASTĘPNY KROK: czekać na PHONE_RUN; pipeline walidacji działa.

Przegląd współdzielonych helperów: terenowe stopy słupków ograniczone opcją ground_feet=True wyłącznie do nowego panel_fence. Bariery/ekrany korzystające z jawnego zb zachowują poprzednią geometrię; dedykowana regresja mostu 8 m przechodzi. Łącznie 7 nowych testów zielonych.
NASTĘPNY KROK: pipeline czeka na PHONE_RUN przed importem bazowym.

Produkty bazowe zachowane w ignorowanym Data/raw/derived/bialystok-industrial-c/furniture-r1-before. Build wariantu po zmianach w toku (build-after.log), bez Unity. Pipeline rozszerzony o wybieranie snapshotów, aby GIS i generację wykonać podczas blokady telefonu.
NASTĘPNY KROK: po build-after: python artifacts/furniture-r1/products.py save after; uv run --project tools/worldgen python -m pytest tests/gis -q

Build po zmianach 307.2 s, bez wzrostu błędów spójności dróg (65, identyczne kategorie jak baza). QA stopni 147→135, maksimum 1.087→0.517 m (najgorszy teraz sign_post). 100 lokalnych korekt podpór lamp; najgorsza pozostała rozbieżność w korektach 0.167 m. To relief podparcia, nie pomiar liczby wiszących obiektów. Produkty after zachowane poza gitem.
NASTĘPNY KROK: uv run --project tools/worldgen python -m pytest tests/gis -q
