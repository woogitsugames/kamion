# LICENSES — rejestr źródeł i zasobów

Każde pobrane źródło danych, zasób graficzny, dźwięk, czcionka i narzędzie, którego wynik trafia do repo lub buildu, ma tu wpis. Manifesty maszynowe (URL, data, SHA256, CRS) leżą w `Data/SourceManifests/*.json`; surowe pliki w `Data/raw/` (poza gitem). Zakaz źródeł Google: ADR 0002.

## Dane geograficzne

| ID | Źródło | URL (snapshot) | Pobrano (UTC) | SHA256 | Licencja | Atrybucja | W gicie? | Użycie |
|---|---|---|---|---|---|---|---|---|
| `osm-geofabrik-podlaskie` | OpenStreetMap, wycinek województwa podlaskiego (Geofabrik) | https://download.geofabrik.de/europe/poland/podlaskie-261108.osm.pbf | 2026-11-09T09:31:29Z | `0ff26cd42f175a5711c69b6d3087a9dcd3bb93367eda16809c75a11ce6c3869d` | ODbL 1.0 | „© OpenStreetMap contributors” | nie (manifest: `Data/SourceManifests/osm-geofabrik-podlaskie.json`) | analiza kandydatów D4 (`tools/worldgen/analyze_candidates.py`), mapy w `docs/reports/map/` |

### Uwagi ODbL (do przeglądu prawnego przed wydaniem w sklepie)
- **Wytworzone obrazy** (`docs/reports/map/*.png`) to w rozumieniu ODbL *Produced Work*: wymagana atrybucja „© OpenStreetMap contributors” (jest na każdej mapie); share-alike nie obejmuje samego obrazu.
- **Baza pochodna** (np. przyszły graf dróg, GeoJSON, paczka regionu z geometrią z OSM) to *Derivative Database*: jeśli będzie udostępniana publicznie (także jako część buildu gry, z której da się ją wyodrębnić), może podlegać share-alike (ODbL §4.4) — do udostępnienia na ODbL lub w formie pozwalającej odtworzyć zmiany. Status: `LEGAL_REVIEW_REQUIRED` przed sklepem.
- Atrybucja OSM musi być widoczna w grze (ekran „O grze”/napisy) — ADR 0002.
- Danych OSM nie łączymy z Mapillary (CC BY-SA) w jednej bazie (docs/05 §3).

## GUGiK (Główny Urząd Geodezji i Kartografii)
Zbiory pobrane 2026-11-09 przez `tools/worldgen/ingest.py --region bialystok-industrial-c`. Surowe pliki leżą w `Data/raw/gugik/` (poza gitem). Pełna lista plików z SHA256, datą pobrania, arkuszem i datą aktualności jest w manifestach. Tabela nie powtarza SHA256 plików, bo są ich dziesiątki: autorytatywne są manifesty JSON. Dostępność i źródła zasad licencyjnych: `docs/map-decisions.md` (sekcja „Dane GUGiK”).

| ID (manifest) | Zbiór | URL | Pliki / rozmiar | Licencja | Atrybucja | W gicie? | Użycie |
|---|---|---|---|---|---|---|---|
| `gugik-nmt-2025-bialystok-industrial-c` | NMT 1 m, PL-EVRF2007-NH, 2025-04-18 | `https://opendata.geoportal.gov.pl/NumDaneWys/NMT/83271/…` | 4 arkusze ASC, 149 MB | dane GUGiK udostępniane nieodpłatnie (PGiK art. 40a ust. 2 pkt 1, od 2020-07-31), `LEGAL_REVIEW_REQUIRED` | „Źródło danych: GUGiK (geoportal.gov.pl)” | nie | heightmapa `Data/raw/derived/…/heightmap_2049.r16` (pochodna, poza gitem), `z_terrain` w grafie |
| `gugik-orto-2024-rgb-0p25-bialystok-industrial-c` | Ortofotomapa RGB 0,25 m, 2024-05-27 | `https://opendata.geoportal.gov.pl/ortofotomapa/81427/…` | 4 GeoTIFF, 179 MB | j.w., `LEGAL_REVIEW_REQUIRED` | j.w. | nie | **tylko referencja i QA** (nie tekstura); wycinki w `docs/reports/map/bialystok-industrial-c_ortho_alignment.png` |
| `gugik-bdot10k-2061` | BDOT10k powiat 2061, GPKG, wersja 2024-09 | `https://opendata.geoportal.gov.pl/bdot10k/schemat2021/GPKG/20/2061_GPKG.zip` | 15,6 MB | j.w., `LEGAL_REVIEW_REQUIRED` | j.w. | nie | obrysy budynków, szerokość i nawierzchnia jezdni (fallback w grafie) |
| `gugik-lod2-2017-2061` | Modele 3D budynków LoD2 (stan 2017), CityGML 2.0 | `https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD2/2061_gml.zip` | 23,5 MB | **CC BY 4.0** (panel pobierania GUGiK) | „Źródło danych: GUGiK (geoportal.gov.pl), CC BY 4.0” | nie | wysokość kalenicy i okapu, typ dachu |
| `gugik-lod1-2024-2061` | Modele 3D budynków LoD1 2024, CityGML | `https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD1/2024/20/2061.zip` | 12,8 MB | **CC BY 4.0** | j.w. | nie | wysokość budynków (`measuredHeight`) |

Sprawdzone, ale **niepobrane** (opcje `ingest.py --with nmpt|trees|lidar`): NMPT 0,5 m 2025, modele 3D drzew LoD1 2023 (CC BY 4.0, 1,07 GB), LiDAR LAZ 2025 (12 pkt/m², ~4,8 GB).

### Uwagi
- Pochodne produkty w `Data/Regions/bialystok-industrial-c/` (`roads.graph.json`, `buildings.geojson`) **łączą dane ODbL (OSM) z CC BY 4.0 / danymi GUGiK**. Graf dróg to baza pochodna OSM (share-alike ODbL §4.4), a pola z BDOT10k mają oznaczone pochodzenie (`src: bdot10k`). Przed udostępnieniem publicznym (build w sklepie) potrzebny jest przegląd prawny zgodności ODbL z CC BY 4.0: `LEGAL_REVIEW_REQUIRED`.
- Mapy w `docs/reports/map/bialystok-industrial-c_*.png` to *Produced Work* z atrybucją OSM i GUGiK na każdym obrazie. Wycinki ortofoto w raporcie są małe (6 × 90 m) i służą jako dowód QA.

## Narzędzia (biblioteki Pythona w `tools/worldgen`, wersje w `tools/worldgen/uv.lock`)
Używane tylko w pipeline, nie są dystrybuowane w buildzie: osmium (pyosmium, BSD-2), shapely (BSD-3), pyproj (MIT), geopandas (BSD-3), pyogrio (MIT), networkx (BSD-3), matplotlib (PSF-based/matplotlib licence), numpy (BSD-3), Pillow (MIT-CMU), requests (Apache-2.0), rasterio (BSD-3, z wbudowanym GDAL — MIT/X), PyYAML (MIT), pytest (MIT, tylko testy).
