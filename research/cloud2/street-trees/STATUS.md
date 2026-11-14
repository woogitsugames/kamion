# STATUS — R5 street-trees (research/cloud2-street-trees)

## Krok 1 (2026-11-14 17:15 UTC) — OSM
- Overpass (overpass-api.de, kumi, private.coffee) nieosiągalny przez proxy (reset/timeout 17:05–17:10 UTC) → ekstrakt PBF
  `download.openstreetmap.fr/extracts/europe/poland/podlaskie.osm.pbf` (state 2026-11-13T01:06:06Z, sha256 82939b5f…), pyosmium.
- Białystok (relacja 2910925): 2549 `natural=tree`, 35 `tree_row`, 138 `barrier=hedge`. species 3,2 %, genus 3,4 %, leaf_type 60,1 %, height 6,0 %.
- Trasa C: 1 drzewo (pomnik), Dojlidy: 5 drzew bez gatunku. Szpalery: 111 rzędów / 911 drzew, odstęp mediana 7,13 m (p10 4,28; p90 15,57).
- NASTĘPNY KROK: dokumenty UM/BIP (gatunki), Dz.U. 2022 poz. 1518, allometria (DOI), fenologia, kadry.
  `uv run --with osmium --with shapely python -I tools/osm_extract_trees.py files/osm/podlaskie.osm.pbf files/osm/`
