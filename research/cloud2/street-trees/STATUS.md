# STATUS — R5 street-trees (research/cloud2-street-trees)

## Krok 1 (2026-11-14 17:15 UTC) — OSM
- Overpass (overpass-api.de, kumi, private.coffee) nieosiągalny przez proxy (reset/timeout 17:05–17:10 UTC) → ekstrakt PBF
  `download.openstreetmap.fr/extracts/europe/poland/podlaskie.osm.pbf` (state 2026-11-13T01:06:06Z, sha256 82939b5f…), pyosmium.
- Białystok (relacja 2910925): 2549 `natural=tree`, 35 `tree_row`, 138 `barrier=hedge`. species 3,2 %, genus 3,4 %, leaf_type 60,1 %, height 6,0 %.
- Trasa C: 1 drzewo (pomnik), Dojlidy: 5 drzew bez gatunku. Szpalery: 111 rzędów / 911 drzew, odstęp mediana 7,13 m (p10 4,28; p90 15,57).
- NASTĘPNY KROK: dokumenty UM/BIP (gatunki), Dz.U. 2022 poz. 1518, allometria (DOI), fenologia, kadry.
  `uv run --with osmium --with shapely python -I tools/osm_extract_trees.py files/osm/podlaskie.osm.pbf files/osm/`

## Krok 2 (2026-11-14 17:40 UTC) — dokumenty
- Łaska 2015 (DOI 10.1515/biorc-2015-0013) Tab. 1 i 3 pobrane (PDF, pressto.amu.edu.pl): pełna tabela 36 gatunków × 4 transekty.
- NIK LBI.403.7.2023: „Miasto nie posiadało … kompleksowej inwentaryzacji zieleni”, „Urząd nie ewidencjonował gatunków” (s. 24, 30).
- BIP DGK-IV.271.2.2017: zał. 2 (lista gatunków do nasadzeń w pasach drogowych, obwód pnia 14–16 cm, korona od 1,8–2,0 m, 3 paliki),
  zał. 3 (liczba drzew w pielęgnacji per ulica: Andersa 228, Maczka 527, razem 3207 liściastych).
- Dz.U. 2022 poz. 1518: brak liczbowej odległości drzew od jezdni (tylko § 26 strefa bez przeszkód, § 80 skrajnia 4,50/2,50 m);
  Dz.U. 2016 poz. 124 § 53 ust. 1 i 3: pas zieleni ≥ 3,0 m, pień ≥ 3,0 m od krawędzi jezdni.
- NASTĘPNY KROK: allometria (USDA RDS-2016-0005, publikacje EU), szkółki (tuje), fenologia, kadry.

## Krok 3–5 (2026-11-14 18:40 UTC) — allometria, szkółki, fenologia, kadry
- UTD (RDS-2016-0005) → data/utd_allometry.json (wys./korona wg klas obwodu i wieku).
- e-katalogroslin (ZSzP): Smaragd 2,5 m × 0,7 m po 10 latach, co 0,5–0,6 m; Brabant 3,5 × 1,5 m, co 0,6–0,8 m; ligustr do 2,5 m.
- Fenologia: Czernecki i in. 2018 (PMC6028898): leszczyna DOY 70, opad liści brzozy DOY 301 (tekst) + odczyt z Fig. 2.
- Kadry obejrzane: 54 (KartaView 18, Panoramax 10, Commons 26); opisy w tools/frame_notes.py.
- NASTĘPNY KROK: `uv run --with shapely --with pyproj python -I tools/build_manifest.py` → manifest.csv, potem fetch.py, audit, README.

## Krok 6 (2026-11-14 ~19:20 UTC) — zamknięcie na polecenie lidera (limit sesji)
- manifest.csv 210 wierszy (tools/build_manifest.py), fetch.py 62/62 OK (33,6 MB), audit 42/42 PASS (seed 20261114, 11 kadrów + wykres obejrzane ponownie), README, sources.md.
- Nie zrobiono: poprawka fenologii dla Białegostoku, dokumenty przetargów 2020/2023, grab/berberys, kadry z azymutem dla Dojlid.
- NASTĘPNY KROK (po recenzji): `cd research/cloud2/street-trees && python3 -I fetch.py && uv run --with shapely --with pyproj python -I tools/build_manifest.py`
