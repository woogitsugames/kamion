# Pakiet research `mistral-s8-loop-s23` — pętla S8 ↔ DW671 ↔ Tykocin (D82)

Dane referencyjne dla 15 nowych kafli pętli (D82, `docs/11_DECYZJE_WLASCICIELA.md`; research `docs/owner/MAP-DECISIONS-2026-11-16.md` sekcja (b)), żeby lider mógł je zbudować „najpierw przejezdne” (D63) z prawdziwymi przekrojami, węzłami, MOP i oznakowaniem. **Tylko dane tekstowe (JSON/MD), żadnych obrazów** — zakaz zdjęć/kadrów; linki + identyfikatory + metadane. Bez marek (nazwy firm tylko jako funkcja obiektu). Każda liczba: zmierzona (narzędzie + dane wejściowe w repo), zacytowana (źródło + data) albo `ESTIMATED` / `UNVERIFIED`.

Zakazane źródła nie były używane (żadne Google Maps/Street View/Earth/3D Tiles, Bing Streetside, Apple Look Around, Yandex). Użyte: OSM API 0.6 (ODbL), GUGiK WMS ortofoto + BDOT10k (open data), Dz.U./ELI, gov.pl (e-TOLL), Panoramax API (tylko pokrycie, CC BY 4.0). Mapillary: niedostępne (brak tokena właściciela) → patrz UNVERIFIED w `SIGNS.md`.

## Pliki i schematy

| plik | zawartość | główne pola |
|---|---|---|
| `tiles.json` | 15 kafli pętli: id, kolejność jazdy, bbox EPSG:2180 + WGS84, styki z istniejącymi regionami, treść OSM per kafel | `tiles[].id/lattice_ij/bbox_epsg2180/bbox_wgs84/order/route_note/stays_with_existing/content_osm` |
| `xsec/s8.json`, `s8_links.json`, `dw671.json`, `dk64.json`, `junction_roads.json` | pomiary przekrojów z ortofoto GUGiK WMS (289 stacji; metoda ADR 0272, narzędzie `xsec/measure_loop_xsec.py`) | wiersz = stacja: `way, s, x, y, asphalt_L/R/w, paved_L/R/w, lines[], grass_L/R` (EPSG:2180; L = lewo od kierunku jazdy, ujemne) |
| `xsec/summary.json`, `xsec/README.md` | mediany per grupa/way, pas dzielący S8 (oś–oś), zgodność z Dz.U. 2022 poz. 1518 | — |
| `junctions.json` | 5 węzłów S8 (Białystok Zachód, Choroszcz, Tykocin, Rzędziany, Jeżewo): typ (ESTIMATED), droga poprzeczna, łącznice z długościami (geometria OSM) i `maxspeed`, limity na S8 | `junctions[].name/wgs84/epsg2180/type/crossroad/ramps[].length_m/...` |
| `mop.json` | 2 MOP na pętli (Radule, Złotoria): obszar, odległość od S8, miejsca TIR/osobowe (ESTIMATED z ortofoto), stacje paliw w promieniu 2 km | `mop_on_loop[].parking_bays_est`, `fuel_within_2km_of_loop[]` |
| `signs.json` + `SIGNS.md` | znaki z OSM (węzły `traffic_sign`, tagi na way: maxspeed/maxspeed:hgv/toll:hgv/maxweight/maxaxleload) + porównanie z Dz.U. (2019 poz. 2310/2311 znaki; 2022 poz. 1518 geometria; 2024 poz. 1251 PoRD; e-TOLL) | `osm_sign_nodes[]`, `way_restrictions`, SIGNS.md §2 tabela przepis↔pomiar |
| `destinations.json` | cele dla ciężarówki w promieniu 2,5 km od dróg pętli: funkcja (bez marek), położenie WGS84+EPSG:2180, powierzchnia, kafel, odległość od drogi, brama (ESTIMATED z topologii OSM) | `destinations[].functions/kinds/wgs84/epsg2180/area_m2/tile/dist_to_loop_road_m/truck_gate_est` |
| `settlements.md` | typologia zabudowy 19 miejscowości pętli: liczba budynków OSM + BDOT10k (2002), kondygnacje, funkcje (BDOT `OT_BUBD_A`) | tabela per `place` |
| `raw/osm/manifest.json` | manifest pobrań OSM API 0.6: 112 komórek siatki ADR 0203 (15 kafli + pierścień), URL, UTC, SHA256, liczba elementów (surowe JSON poza gitem w `Data/raw/osm_api_s8loop/`) | `cells[].url/utc/sha256` |
| `raw/osm/loop_roads.json` | wszystkie way `highway` w 15 kaflach z tagami i geometrią EPSG:2180 — dane wejściowe do pomiarów `xsec/` | `ways[].id/tags/geometry_2180/length_m/cells` |
| `raw/osm/loop_nodes.json` | węzły z tagami w 15 kaflach (węzły drogowe, znaki, miejscowości, usługi; nazwy marek usunięte) | `nodes[].id/lat/lon/x/y/cell/tags` |
| `RAPORT.md` | raport końcowy (≤40 linii) | — |

## Konwencje

- Siatka kafli: ADR 0203 — `x = 776971 + 2048·i`, `y = 595199 + 2048·j` (EPSG:2180), kafel 2048×2048 m. Zestaw pętli: (−5…−9,0), (−9…−12,−1), (−12…−14,−2), (−13,−1…1) = 15 unikalnych komórek (komórki (−13,−2), (−14,−2) mają obie drogi — węzeł Jeżewo).
- ID kafli: `s8-01`…`s8-12` (kolejność jazdy po S8 od dk65-01 do Jeżewa), `dw671-jezewo-01…03` (powrót DW671; istnieją już `dw671-tykocin-01` zbudowany i `dw671-tykocin-02..09` w PR #115).
- Współrzędne: EPSG:2180 (metry) + WGS84 (lat/lon) — oba w każdym rekordzie z położeniem.
- Statusy: `ESTIMATED` (wyprowadzone z pomiaru/danych, nie bezpośrednio), `UNVERIFIED` (do potwierdzenia przez właściciela/lidera).
- Brak plików > 5 MB; same dane tekstowe.

## Odtworzenie

1. OSM: jedna komórka siatki = `GET https://api.openstreetmap.org/api/0.6/map.json?bbox=<WGS84 bbox komórki>` (UA `osm-research-client/1.0`, pauza 1,5 s, HTTP 400 → podział na 4 ćwiartki) — logika opisana w `raw/osm/manifest.json.note`.
2. Przekroje: `uv run --project tools/worldgen python research/mistral-s8-loop-s23/xsec/measure_loop_xsec.py` (WMS GUGiK, patrz `xsec/README.md`).
3. Reszta: wyprowadzenia z `raw/osm/*.json` (skrypty sesji opisane w `RAPORT.md`).
