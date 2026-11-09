# LICENSES — rejestr źródeł i zasobów

Każde pobrane źródło danych, zasób graficzny, dźwięk, czcionka i narzędzie, którego wynik trafia do repo lub buildu, ma tu wpis. Manifesty maszynowe (URL, data, SHA256, CRS) leżą w `Data/SourceManifests/*.json`; surowe pliki w `data/raw/` (poza gitem). Zakaz źródeł Google: ADR 0002.

## Dane geograficzne

| ID | Źródło | URL (snapshot) | Pobrano (UTC) | SHA256 | Licencja | Atrybucja | W gicie? | Użycie |
|---|---|---|---|---|---|---|---|---|
| `osm-geofabrik-podlaskie` | OpenStreetMap, wycinek województwa podlaskiego (Geofabrik) | https://download.geofabrik.de/europe/poland/podlaskie-261108.osm.pbf | 2026-11-09T09:31:29Z | `0ff26cd42f175a5711c69b6d3087a9dcd3bb93367eda16809c75a11ce6c3869d` | ODbL 1.0 | „© OpenStreetMap contributors” | nie (manifest: `Data/SourceManifests/osm-geofabrik-podlaskie.json`) | analiza kandydatów D4 (`tools/worldgen/analyze_candidates.py`), mapy w `docs/reports/map/` |

### Uwagi ODbL (do przeglądu prawnego przed wydaniem w sklepie)
- **Wytworzone obrazy** (`docs/reports/map/*.png`) to w rozumieniu ODbL *Produced Work*: wymagana atrybucja „© OpenStreetMap contributors” (jest na każdej mapie); share-alike nie obejmuje samego obrazu.
- **Baza pochodna** (np. przyszły graf dróg, GeoJSON, paczka regionu z geometrią z OSM) to *Derivative Database*: jeśli będzie udostępniana publicznie (także jako część buildu gry, z której da się ją wyodrębnić), może podlegać share-alike (ODbL §4.4) — do udostępnienia na ODbL lub w formie pozwalającej odtworzyć zmiany. Status: `LEGAL_REVIEW_REQUIRED` przed sklepem.
- Atrybucja OSM musi być widoczna w grze (ekran „O grze”/napisy) — ADR 0002.
- Danych OSM nie łączymy z Mapillary (CC BY-SA) w jednej bazie (docs/05 §3).

## GUGiK (jeszcze nie pobrane)
Zbiory planowane dla obszaru startowego (NMT, BDOT10k, modele 3D budynków LoD1/LoD2, modele 3D drzew) — status i zasięg w `docs/map-decisions.md`. Strona GUGiK deklaruje dla modeli 3D budynków „dostępne bezpłatnie i możliwe do dowolnego wykorzystania” (geoportal.gov.pl, sprawdzone 2026-11-09). Wpis z SHA256 zostanie dodany przy pierwszym pobraniu.

## Narzędzia (biblioteki Pythona w `tools/worldgen`, wersje w `tools/worldgen/uv.lock`)
Używane tylko w pipeline, nie są dystrybuowane w buildzie: osmium (pyosmium, BSD-2), shapely (BSD-3), pyproj (MIT), geopandas (BSD-3), networkx (BSD-3), matplotlib (PSF-based/matplotlib licence), numpy (BSD-3), Pillow (MIT-CMU), requests (Apache-2.0).

## Audio

Wszystkie dźwięki poniżej są **w 100% syntetyzowane naszym kodem** (numpy/scipy) — bez nagrań, sampli, banków dźwięków ani generatorów AI. Brak praw osób trzecich; licencja = licencja projektu. Opis modelu: `docs/AUDIO_DESIGN.md`.

| ID | Źródło | Autor | Licencja | Data | W gicie? | Użycie / modyfikacje |
|---|---|---|---|---|---|---|
| `audio-engine-r6-synth` | `tools/audio/engine_synth.py` + `render_all.py` (synteza impulsowa R6, kolejność 1-5-3-6-2-4) | projekt (agent audio) | własna (projekt) | 2026-11-09 | generator tak; WAV nie (`art-source/audio/generated/`, odtwarzalne) | pętle silnika 16 rpm × 3 obciążenia × ext/cab, hamulec silnikowy 13 rpm × ext/cab |
| `audio-sfx-synth` | `tools/audio/sfx_synth.py` | projekt (agent audio) | własna (projekt) | 2026-11-09 | generator tak; WAV nie | gwizd turbo, lift-off, zwolnienie hamulca, hamulec postojowy, osuszacz, zmiana biegu, opony, wiatr, wycie przekładni |
| `audio-previews` | render powyższych (`art-source/audio/previews/*.ogg`) | projekt | własna (projekt) | 2026-11-09 | tak | podglądy do odsłuchu (każda pętla 2× pod rząd) |
| `audio-drive-demo` | `tools/audio/render_demo.py` (lustro runtime, skryptowana telemetria) | projekt | własna (projekt) | 2026-11-09 | tak (`art-source/audio/demo/`) | demo 30 s kabina + zewnątrz do oceny właściciela |

### Narzędzia audio (biblioteki Pythona w `tools/audio`, wersje w `tools/audio/uv.lock`)
Tylko pipeline, nie trafiają do buildu: numpy (BSD-3), scipy (BSD-3), soundfile (BSD-3; dołączony libsndfile LGPL-2.1, z koderem Vorbis BSD-3 — używany tylko do zapisu plików offline), matplotlib (licencja matplotlib), Pillow (MIT-CMU, kwantyzacja PNG raportów). Formuły biquadów: RBJ Audio EQ Cookbook (wzory publiczne). K-weighting LUFS: ITU-R BS.1770-4 (współczynniki normy).
