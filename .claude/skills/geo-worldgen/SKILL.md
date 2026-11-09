---
name: geo-worldgen
description: Pipeline danych świata z OSM i GUGiK do paczki regionu Unity (ingest z manifestem, normalizacja CRS, graf dróg z provenance, geometria, teren, budynki, roślinność, chunki, raport QA). Używaj przy generowaniu i regeneracji fragmentów Białegostoku i kolejnych regionów.
---
# Geo worldgen

1. **Wybór obszaru**: bbox w EPSG:2180 + bufor; zapis w `Data/Regions/<id>/region.yaml`.
2. **Ingest**: `uv run tools/worldgen/ingest.py --region <id>` — wycinek OSM (Geofabrik `podlaskie-latest.osm.pbf` → `osmium extract`), NMT, BDOT10k, LoD1/LoD2 (CityGML), modele drzew (jeśli dostępne), ortofoto (tylko referencja). Manifesty z SHA256 w `Data/SourceManifests/`. **Nigdy Google.**
3. **Normalizacja**: reprojekcja, wysokości (sprawdź układ wysokościowy), czyszczenie, łączenie OSM↔BDOT z raportem konfliktów.
4. **Graf**: `build_graph.py` → pasy, kierunki, turn:lanes, zakazy, ograniczenia, provenance + confidence.
5. **Geometria i teren**: `build_roads.py`, `build_junctions.py`, `build_terrain.py` — format pośredni (np. glTF/binarny + JSON) w `artifacts/regions/<id>/`.
6. **Zabudowa i otoczenie**: `build_buildings.py` (typologie fasad), `scatter_vegetation.py`, `place_props.py`, `build_signage.py`.
7. **Overrides**: `apply_overrides.py` z `Data/Regions/<id>/overrides/*.yaml` (po ID obiektów).
8. **QA**: `qa_report.py` → `artifacts/regions/<id>/qa.md` + mapa PNG problemów (render z własnych danych). Obejrzyj.
9. **Import Unity**: `scripts/import-region.ps1 -Region <id>` (batchmode importer) → chunki, LOD/HLOD, kolizje, Addressables, manifest regionu.
10. **Weryfikacja**: przejazd testowy (bot jedzie po grafie pasów, raportuje wpadnięcia pod teren, dziury kolizji, skoki wysokości) + `visual-qa` na punktach kontrolnych.

Zasada: jeśli generator daje zły wynik — popraw generator; override tylko dla rzeczy, których dane nie opisują.
