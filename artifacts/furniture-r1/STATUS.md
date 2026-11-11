# ADR 0102 — strumień I
Worktree z main 9e6e9fde. Przeczytano wymagane zasady i recenzje; kopie lokalnych danych oraz junctiony referencji przygotowane. Bez telefonów/adb.
NASTĘPNY KROK: uv run --project tools/worldgen python -m pytest tests/gis -q

Audyt: QA bazowe 147 stopni >5 cm, max 1.087 m. Zdjęcie Mapillary p26 obejrzane (referencja lokalna). WIP: kontakt osi z widoczną siatką, fundament -1.25/+0.08 m, obejmy dopasowane do stożka; bez nowych materiałów. Wymiary WORKING_VALUE, ocena Unity nadal oczekuje PHONE_RUN.
NASTĘPNY KROK: uv run --project tools/worldgen python -m pytest tests/gis/test_furniture_r1.py -q

WIP r1: atlas zużycia lokalizowany wysokością (skany CC0 brushed_concrete/corrugated_iron_03), LOD starych lamp i obejmy, U-słupek tylko z tagu OSM, schodkowe przęsła z zakopanymi stopami słupków. Materiały wyłącznie addytywne furniture_*. PHONE_RUN nadal istnieje. Bazowe GIS nadal w toku (testy determinizmu).
NASTĘPNY KROK: uv run --project tools/worldgen python tools/worldgen/roads/build_world.py --region bialystok-industrial-c

GIS bazowe: 370 passed, 1 xfailed / 635.18 s. Regresje ADR0102: 6 passed. Korekta po audycie kodu: fundament -0.45/+0.08 m, lokalne przesunięcie lampy do 1.05 m przy ostrym uskoku zamiast głębokiego zakopania. Jawne wysokości na wiaduktach zachowane. Low starej betonowej lampy 105→91 tris, pozostałe porównane Low bez wzrostu slotów.
NASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1
