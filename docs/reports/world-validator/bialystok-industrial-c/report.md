# World validator — region `bialystok-industrial-c`

Schema `truck-sim-pl/world-validator/1`. Ramka: lokalne E/N w metrach (EPSG:2180 minus origin regionu); lat/lon = WGS84. Kafelek = chunk 256 m z `generated/world_manifest.json`.

Znaleziska: **558** (error 56, warn 88, info 414), z czego na trasie G3 (±60 m): **56**, czas walidatora: 0.7 s

## Liczby wg kategorii

| kategoria | liczba | na trasie G3 |
|---|---|---|
| building_height_default | 53 | 9 |
| building_height_vs_storeys | 17 | 0 |
| building_in_carriageway | 19 | 1 |
| building_roof_only | 14 | 4 |
| duplicate_parallel | 342 | 28 |
| object_in_carriageway | 56 | 3 |
| object_in_object | 12 | 0 |
| object_on_kerb | 34 | 7 |
| road_profile_deviation | 3 | 1 |
| sign_facing_away | 3 | 3 |
| terrain_wall | 5 | 0 |

## Top 20 znalezisk (posortowane: severity, trasa G3, odległość, kategoria)

| # | kategoria | E (m) | N (m) | id | szczegół | kafelek |
|---|---|---|---|---|---|---|
| 1 | sign_facing_away | 647.2 | -559.8 | `rule:maxspeed:c:w1090234575:8722811971-9986085571` | sign B-33_30 faces away from the route driver (offset 4.4 m) (53.153192, 23.169046) | [6_6](Data/raw/derived/bialystok-industrial-c/world/chunk_6_6.glb#6_6) |
| 2 | sign_facing_away | -283.0 | -179.4 | `osm:node/3097201643` | sign D-6 faces away from the route driver (offset 10.8 m) (53.157089, 23.155498) | [2_4](Data/raw/derived/bialystok-industrial-c/world/chunk_2_4.glb#2_4) |
| 3 | sign_facing_away | -435.4 | -33.6 | `rule:maxspeed:c:w174538883:1852129070-1852128980` | sign B-33_20 faces away from the route driver (offset 9.6 m) (53.158476, 23.153352) | [2_4](Data/raw/derived/bialystok-industrial-c/world/chunk_2_4.glb#2_4) |
| 4 | building_in_carriageway | 61.6 | -393.0 | `osm:way/279896718` | building footprint intersects the carriageway by 127.4 m2 (53.154994, 23.160455) | [4_5](Data/raw/derived/bialystok-industrial-c/world/chunk_4_5.glb#4_5) |
| 5 | building_in_carriageway | -188.1 | -158.3 | `bdot:2BE4B431-C7B4-1BF0-E053-CC2BA8C0D140` | building footprint intersects the carriageway by 5.5 m2 (53.157229, 23.156933) | [3_4](Data/raw/derived/bialystok-industrial-c/world/chunk_3_4.glb#3_4) |
| 6 | building_in_carriageway | 492.7 | -768.8 | `osm:way/236606117` | building footprint intersects the carriageway by 58.8 m2 (53.151398, 23.166559) | [5_7](Data/raw/derived/bialystok-industrial-c/world/chunk_5_7.glb#5_7) |
| 7 | building_in_carriageway | -654.6 | -23.9 | `bdot:2BE4B431-B151-1BF0-E053-CC2BA8C0D140` | building footprint intersects the carriageway by 11.9 m2 (53.158677, 23.150088) | [1_4](Data/raw/derived/bialystok-industrial-c/world/chunk_1_4.glb#1_4) |
| 8 | building_in_carriageway | -288.5 | -388.6 | `bdot:2BE4B431-C728-1BF0-E053-CC2BA8C0D140` | building footprint intersects the carriageway by 7.1 m2 (53.155216, 23.155235) | [2_5](Data/raw/derived/bialystok-industrial-c/world/chunk_2_5.glb#2_5) |
| 9 | building_in_carriageway | -342.1 | -362.2 | `bdot:2BE4B431-CA03-1BF0-E053-CC2BA8C0D140` | building footprint intersects the carriageway by 1.6 m2 (53.155481, 23.154458) | [2_5](Data/raw/derived/bialystok-industrial-c/world/chunk_2_5.glb#2_5) |
| 10 | object_in_carriageway | -580.9 | -148.1 | `canopy:1958` | tree centre 1.38 m inside the carriageway edge (53.157525, 23.151081) | [1_4](Data/raw/derived/bialystok-industrial-c/world/chunk_1_4.glb#1_4) |
| 11 | object_in_carriageway | -578.9 | -150.1 | `canopy:1979` | tree centre 1.04 m inside the carriageway edge (53.157506, 23.151109) | [1_4](Data/raw/derived/bialystok-industrial-c/world/chunk_1_4.glb#1_4) |
| 12 | object_in_carriageway | -585.1 | -145.6 | `canopy:1912` | tree centre 0.72 m inside the carriageway edge (53.157549, 23.151020) | [1_4](Data/raw/derived/bialystok-industrial-c/world/chunk_1_4.glb#1_4) |
| 13 | building_in_carriageway | -312.4 | -420.6 | `bdot:2BE4B431-C727-1BF0-E053-CC2BA8C0D140` | building footprint intersects the carriageway by 58.4 m2 (53.154941, 23.154851) | [2_5](Data/raw/derived/bialystok-industrial-c/world/chunk_2_5.glb#2_5) |
| 14 | building_in_carriageway | -395.7 | -358.8 | `bdot:2BE4B431-C9E1-1BF0-E053-CC2BA8C0D140` | building footprint intersects the carriageway by 7.7 m2 (53.155538, 23.153662) | [2_5](Data/raw/derived/bialystok-industrial-c/world/chunk_2_5.glb#2_5) |
| 15 | building_in_carriageway | -454.4 | -328.9 | `bdot:2BE4B431-C9E2-1BF0-E053-CC2BA8C0D140` | building footprint intersects the carriageway by 23.6 m2 (53.155838, 23.152811) | [2_5](Data/raw/derived/bialystok-industrial-c/world/chunk_2_5.glb#2_5) |
| 16 | object_in_carriageway | -732.9 | 921.1 | `canopy:739` | tree centre 0.84 m inside the carriageway edge (53.167193, 23.149739) | [1_0](Data/raw/derived/bialystok-industrial-c/world/chunk_1_0.glb#1_0) |
| 17 | object_in_carriageway | -730.6 | 923.6 | `canopy:749` | tree centre 1.07 m inside the carriageway edge (53.167215, 23.149775) | [1_0](Data/raw/derived/bialystok-industrial-c/world/chunk_1_0.glb#1_0) |
| 18 | object_in_carriageway | -735.6 | 924.6 | `canopy:729` | tree centre 1.50 m inside the carriageway edge (53.167226, 23.149702) | [1_0](Data/raw/derived/bialystok-industrial-c/world/chunk_1_0.glb#1_0) |
| 19 | object_in_carriageway | -570.6 | -234.9 | `canopy:2065` | tree centre 0.69 m inside the carriageway edge (53.156741, 23.151159) | [1_4](Data/raw/derived/bialystok-industrial-c/world/chunk_1_4.glb#1_4) |
| 20 | building_in_carriageway | -341.3 | -453.4 | `bdot:2BE4B431-C729-1BF0-E053-CC2BA8C0D140` | building footprint intersects the carriageway by 76.4 m2 (53.154662, 23.154390) | [2_5](Data/raw/derived/bialystok-industrial-c/world/chunk_2_5.glb#2_5) |

Pełna lista: `world_validator.json` obok tego raportu. Kamery kontrolne: `control_cameras.json`.
