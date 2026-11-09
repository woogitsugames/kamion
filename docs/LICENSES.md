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
