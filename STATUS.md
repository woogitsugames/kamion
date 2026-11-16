# STATUS — rynek-p1-s23 (D41, ADR 0227 dopisek)

- (e) DONE: przyczyna uskoku DK65 płd. = narożnik mieszany (wiejskie ramię + krawężnik) ronda kompaktowego: połowa wiejska
  dostawała goły krawężnik bez pasa trawy, conform NMT 2022 (stary rów) spadał 0,5–0,74 m w 1,5 m. Poprawka `meshing.build_corner_strips`
  (tylko j.compact): trawa za całym krawężnikiem + soft footprint → spadek ≤ 0,28 m (repro: NMT z WCS GUGiK, tylko liczby).
- (d) DONE: klucz `outer_diameter_m` (14–40 m, max(2 m, 40 %) od promienia OSM, inaczej stale), scalanie opcji compact_roundabout w network.load, override knyszyn 26,0 m WORKING_VALUE na końcu overrides.yaml; test_roundabout_0274: baseline 0218 bez D41, dolna granica wysepki S 28→27.
- (a) DONE: pomiar WMS (qa/market_canopy_ortho.py): okapy 27,1 × 7,2 m, prześwity 1,15 / 1,17 m, 14,2 m; override `knyszyn-market-canopy-eaves-d41` (market_canopy_geometry_d41) podmienia obrysy po id, inset 0; JSON+README w docs/reports/rynek-p1/.
- (b) DONE: pawilon bdot:de62e5a9 dach namiotowy (jeden wierzchołek) + żółte ściany jako dane `kind: market_pavilion_d41` (walidacja, stale→domyślny dach), stage przekazuje overrides do KMB.build.
- (c) DONE: `kind: tree_crown_shape` (height_to_spread 1,0–3,0) w plantings.authored_trees; lipy Rynku 1,75 ESTIMATED (VCE 2901-1055, 70 ft × 40 ft): korony 8,8–11,4 m zamiast 9,3–12,9 m.
- Testy: 362 passed, 2 skipped (zestaw -k z zadania).
- NASTĘPNY KROK: dopisek ADR 0227 D41 + PR → `gh api repos/woogitsugames/kamion/pulls`
