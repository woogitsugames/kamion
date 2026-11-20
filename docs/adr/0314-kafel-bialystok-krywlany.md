# ADR 0314 — Kafel bialystok-krywlany (ADR 0278 kafel 4): domknięcie trasy C ↔ Dojlidy przez DK19

Status: Proposed (krywlany-s24, 2026-11-20; numer 0314 — następny wolny po 0313 z HANDOVER.md; do przyjęcia przez lidera
przy scaleniu). Powiązane: ADR 0278 (plan mapy, kafel 4 = siatka (0,−3)), 0290 (kafle DK19 i luka krywlany), 0203 (siatka),
0209/0212 (pin NMT), 0285 (trasy łączące), 0275 (szwy), D63 (najpierw przejezdne), D81 (C ↔ Dojlidy), D93 pkt 4.

## Kontekst
ADR 0290 zostawił lukę: Ciołkowskiego DW678 schodzi z mickiewicza na N krawędź Dojlid, przecina ich NW narożnik i wychodzi
na zachód do kafla 4, który nie istniał; trasa Dojlid zaczyna się na ich W krawędzi (Dywizjonu 303). Korytarz
`bialystok-dojlidy-dk19` kończył się na mickiewicza, a krywlany i Dojlidy były w `missing`.

## Decyzja
1. **Kafel 2048 × 2048 m** `bialystok-krywlany`, bbox EPSG:2180 776971, 589055 – 779019, 591103, powiat 2061, NMT 2025
   (pin jak Dojlidy i mickiewicza), ORTO 2024 0,25 m, BDOT10k + LoD1/LoD2 2061, OSM z przypiętego pbf 261108.
   Definicja i pliki authored z generatora `tools/worldgen/qa/krywlany_tile_0278.py` (ta sama ścieżka ciężarówki co
   `qa/dk19_tiles_0278.py`). `overrides.yaml` pusty (rough first, D63).
2. **Trasa kontrolna** = kawałek korytarza w kaflu: od szwu z Dojlidami na Ciołkowskiego (779019, 591055,7) przez rondo
   i Dywizjonu 303 do wejścia trasy Dojlid (779019, 590253), ~1205 m (OSM API 0.6 z 2026-11-16).
3. **Narożnik Dojlid (~87 m Ciołkowskiego, way 279881972)** nie jest częścią żadnej trasy kafla, a mickiewicza i krywlany
   stykają się tylko narożnikiem (streamer otwiera szwy N/E/S/W). Zamiast zmieniać trasę Dojlid (kafel zbudowany) —
   **link** `dojlidy-ciolkowskiego-corner-to-krywlany` w `Data/Streaming/route_links.yaml` (kafel Dojlidy, `head_from`
   koniec trasy mickiewicza, `tail_to` start trasy krywlany). Korytarz: `[C, wygoda, bojary, mickiewicza, dojlidy,
   krywlany, dojlidy]` — Dojlidy dwa razy (najpierw link narożnika, potem ich trasa).
4. **Narzędzia danych**: (a) `gugik_index.get_feature` ponawia zapytanie WFS (5×, przerwa 30·n s) — 20.11 indeks
   mapy.geoportal.gov.pl zrywał połączenia/timeout; (b) `build_region.build_ortho` przyjmuje arkusz ORTO z WKT
   „ETRF2000-PL / CS92” bez kodu EPSG (arkusze N-34-107-C-b-3-1/-3-3 z 2024) jako EPSG:2180 przez WarpedVRT bez
   reprojekcji — sprawdzone: ten sam datum (ETRF2000 Poland, GRS 1980) i parametry TM (lon_0 19, k 0,9993, x_0 500000,
   y_0 −5300000), WKT kończy się AUTHORITY["EPSG","2180"]. Inny CRS nadal kończy się błędem `merge`.
5. **`graph_filter.authored.json`** (mechanizm ADR 0204): import r1 przerwany „closure rows overlap after ResolveClosures”
   (Witolda Sławińskiego × Witolda Sławińskiego); `qa/edge_closures_check.py` wskazał 2 pary NOT CUT na W krawędzi (brak
   tam sąsiada): serwisowe 211179100 × 251389617 i Sławińskiego 257258194 × 271890047 (ulica wchodzi jednym węzłem do
   kafla i wychodzi 16 m dalej obok skrzyżowania z primary 251388401). Usunięte z grafu: 251389617, 271890047 (żadna na
   trasie). Po przebudowie: 0 par NOT CUT.
6. **`world_edge.authored.json`** (mechanizm ADR 0295): zamknięcie wjazdu Ciołkowskiego (szew z Dojlidami) 50 m od
   krawędzi zamiast 60 m — przy skośnym przecięciu krawędzi rząd stał 67,4 m po trasie i start katalogu 90 m był 2,4 m za
   blisko (EditMode StartClearanceTests r2). Przy streamingu zamknięcie i tak otwiera wczytany kafel Dojlid.

## Zmierzone
- Ingest 2026-11-20: 8 plików, 339 074 329 B (NMT 2025 ×4, ORTO 2024 ×4); BDOT/LoD 2061 już na dysku.
- build_region r1: 396 węzłów, 455 krawędzi, 700 budynków (r2 po graph_filter: 393 / 452 w grafie GPS); teren 141,33–167,01 m EVRF2007, 0 brakujących próbek.
- Szew z Dojlidami (graf): 6/6 węzłów brzegowych, odchyłka 0,0 m.
- build_world --context r3 (po merge road-widen D94, i5-10400F): 1061 s; far_field High 174 525 / Low 63 186 tris;
  ściany terenu > 0,15 m: 7 (max 0,347 m); road consistency 23 (na trasie 1: obstacle_in_lane „kerb” na rondzie
  Wünschego s ≈ 960 m — tor przecina narożnik opaski wyspy, topview `artifacts/krywlany-s24/junctions/route-s0960-kerb.jpg`).
- Trasa kontrolna 1233 m (export-route r3); wyjście 0,14 m od wejścia trasy Dojlid → portal krywlany → dojlidy w
  `tile_graph.json`; korytarz `bialystok-dojlidy-dk19` 7 kafli, missing 0, złącza ≤ PORTAL_TOL_M.
- `qa/route_obstacles.py` (krywlany + Dojlidy + link narożnika): colliders 0, visual 0.
- Szwy (`qa/seams.py`, krywlany | Dojlidy | mickiewicza, r4): na trasie FAIL tylko „szer. jezdni ostatni build” — Dojlidy
  zbudowane przed ADR 0306 (7,5 m) vs krywlany 8,5 m; przekrój nominalny 8,5 | 8,5 OK, oś na szwie 0,011 m → znika po
  przebudowie Dojlid. Poza trasą: w107760411 (Dojlidy | mickiewicza, istniejący).
- Import Win64 r3: 64 chunki, WORLD_MEMORY Low 105,9 / High 254,0 MB (wpisane do `tile_graph.py`).
- Kamery High (visual-qa, clear): route-s0154/0461/0768/1076, roundabout-02-above, chase, truck-at-gate, cab-view —
  obejrzane (`artifacts/krywlany-s24/vqa-r3/`).
- Testy: EditMode Win64 r3 1489 / 1384 pass / 0 fail / 105 skip (r2: 3× StartClearanceTests krywlany → §6).
  pytest (14 plików gis: route_links, katalog, start_clear, seams ×4, tile_graph, map_plan, qa_tools_0219, dk19,
  generic_0166, far_field_streaming, road_widen_0306): 458 pass; 3 fail w test_route_links_s23 (json_fresh, knyszyn
  Rynek, ciągłość kleeberga|knyszynska) — te same 3 padają na main 3d55252ec (nie dotyczą krywlany).
- `route_links.json` = wersja main + link narożnika + korytarz (prywatna kopia derived worktree jest starsza od main —
  pełna regeneracja tutaj zmieniłaby linki knyszyn/tykocin); lider: `route_links.py` w main po scaleniu.

## Konsekwencje / Otwarte
- Dojlidy do przebudowy po road-widen (fala regeneracji) — wtedy szwy krywlany | Dojlidy bez FAIL.
- Rondo Wünschego: OSM (ramię SW, 2025) nowsze niż ORTO 2024; tor przez narożnik opaski wyspy — sprawdzić z
  referencją (Panoramax/Mapillary) i ewentualnie override geometrii ronda.
- Zamknięcie krawędzi E (koniec trasy) widoczne w scenie samodzielnej (route-s1076) — przy streamingu z Dojlidami otwarte.
- Fidelity kafla nie uruchomione (kolejka heavy): `uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-krywlany --fetch`.
- Krywlany poza zestawem `d67-full` (jak mickiewicza/bojary/wygoda) — decyzja lidera przy buildzie z `-Regions`.
