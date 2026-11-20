# s8-north-s24 — STATUS

Zadanie: lider s24 (D93 p.4 + D95 p.4, D63 rough first) — przedłużenie korytarza na północ w stronę Wasilkowa/Korycina.

## Ustalenie (2026-11-20)
- S8 w pbf 2026-11-08 kończy się na węźle Białystok Zachód (dk8-s8-jeroniki/dk65-01). Ekspresówka na północ od dk65-02
  (S19 Księżyno – Białystok Północ) = `highway=construction` → nieprzejezdna. Jedyna przejezdna droga do Wasilkowa/Korycina
  to **DK8 (8;19) z północnego szwu kafla C** (Al. Tysiąclecia → Białostocka → węzeł Wasilków DK8/DK19 → DK8 do Korycina).
- Kafle (siatka ADR 0203, kolumna i=0): dk8-wasilkow-01 (0,1), dk8-wasilkow-02 (0,2), dk8-wasilkow-03 (0,3, węzeł Wasilków),
  dk8-korycin-01 (0,4, wyjazd na zachodni szew). Plan: `tools/worldgen/qa/dk8_north_plan.py` → `docs/reports/map/dk8_north_plan.{json,png}`.
- Uwaga: DK8 biegnie 150–300 m od zachodniej krawędzi kolumny (łącznice węzła w (0,1) częściowo w (-1,1) — przycięte krawędzią).

## Kroki
- [x] definicje regionów + pliki authored (pin NMT 2025 jak C), skrypt `tools/worldgen/qa/s8_north_s24.ps1`
- [x] ingest → build_region → build_world → export-route: 03 (2068 m, road_consistency 239, na trasie 0) i korycin-01 (963 m, 9, na trasie 0) gotowe; 01/02 ingest — WFS GUGiK zrywa połączenie (SkorowidzOrtofomapy2026), retry + raport warstw niedostępnych
- [x] link C (swing → 0 pkt poza nawierzchnią), tile_graph/route_links/katalog/nav_trips (złącza ≤ 7 mm), qa.seams 5 kafli 0 FAIL, seam_z ≤ 0,088 m, route_obstacles 0 colliders/0 visual
- [x] import Win64 + visual-qa High (02: 199,4 MB; arkusz vqa-r1/dk8-wasilkow-02/sheet.jpg OK): dk8-wasilkow-03 r2 OK (WORLD_MEMORY High 200,4 MB; render węzła, ekrany akustyczne po zach. stronie, bariery; `artifacts/s8-north-s24/vqa-r2/dk8-wasilkow-03/small`). korycin-01 r2 OK (High 148,7 MB; DK8 przechodzi w jednojezdniową przed szwem W; brak prawej linii krawędziowej ok. s0481 — do sprawdzenia). wasilkow-01 r1 OK (High 159,0 MB; ekrany akustyczne szklane i ciemne, bariery, sygnalizacja s0740, ścieżka rowerowa; zamknięcie kafla na N widoczne tylko w scenie pojedynczego kafla). Brakował SM_CabInterior_LOD0.fbx w worktree — skopiowany z main.
- [~] EditMode r1: 1395/1501, 1 FAIL = budżet okna (domyślne 252/622 MB dla nowych kafli w tile_graph) → wpisane zmierzone WORLD_MEMORY, najgorsze okno bojary 798,4/1940,1 MB. pytest r1 przerwany (merge).
- [~] 20.11 14:05 merge origin/main (road-widen D94, ADR 0306) bez konfliktów → przebudowa 4 kafli r2 (world+route), potem route_links/swept/seams/import/vqa/pytest/EditMode

NASTĘPNY KROK: po `artifacts/s8-north-s24/run/final-world-*-r2.exit` → tile_graph/route_links/nav_trips, link_swept_check c-dk8-north-to-wasilkow, seams, `-Phase unity -Tag r3`, route_obstacles, pytest, `-Phase editmode -Tag r2`

## 14:35 r2
- 01 r2 gotowy (2071 m). road_consistency na trasie (pas 30 m): 63 bridge_kerb w pasie 0 (lewy, przy pasie dzielącym) na moście DK8 (way 145631572/3), 5,2–6,6 m od toru ciężarówki — nie w obwiedni; 1 arrow_no_exit (zjazd węzła wychodzi zachodnią krawędzią do (-1,1)). W r1 na trasie było „0”, bo route_start.json nie istniał w chwili build_world (pierwszy build) — to nie regres road-widen.
- pytest: test_dense_lod_0282[bialystok-kleeberga] FAIL także w main (istniejący).
- 02/03/korycin r2 czekają na slot heavy (3/3 zajęte: regen-wave-2 A/C, rondo-fix-cli).

## 15:50
- merge origin/main (krywlany ADR 0314) — konflikty rozwiązane (gugik_index: retry z main + mój raport `unavailable_layers`; route_links.yaml: oba linki; katalog: wartości z main), regeneracja streaming.
- pytest r2 (przed poprawkami): 14 FAIL; moje poprawione (graph reader ADR 0274, powiat 01, sąsiad N kafla C, plan 0278 — kafle ADR 0315 = komórki planu dk8-dk19-pn-01/-jurowce/dk8-sochonie/dk8-woroszyly, plan bez zmian). Istniejące w main: dense_lod kleeberga, road_fidelity stale, zebras r9, route_links json_fresh (conftest GAMEPLAY_LANE_WIDEN_M=0 vs skrypt), knyszyn rynek, world_roads deterministic. keep_tyres/monki_corner — tylko w worktree (stara kopia derived knyszyn/monki).
- 03/korycin r2 czekają na heavy; import r3 01/02 w toku (przebudowa PBR Medium).
- 16:09 import+vqa r3 01 (High 159,0 / Low 78,7 MB) i 02 (199,3 / 86,6 MB) po merge — OK (arkusz vqa-r3/dk8-wasilkow-01/sheet.jpg). 03/korycin r2 nadal w kolejce heavy (wszystkie 3 sloty: regen-wave-2 A/B/C).
NASTĘPNY KROK (po starcie/końcu world 03 i korycin r2): `pwsh -NoProfile -File tools/worldgen/qa/s8_north_s24.ps1 -Phase unity -Tiles dk8-wasilkow-03,dk8-korycin-01 -Tag r3`, potem tile_graph (WORLD_MEMORY z logów), route_links, nav_trips, catalog, route_obstacles, seams, `-Phase editmode -Tag r2`
- 16:16 EditMode Win64 r2 (po merge krywlany + road-widen): 1505, 1398 pass, 0 FAIL, 107 skip — artifacts/tests/editmode-20261120-161228.xml
- 16:52 link wasilkow-01-to-02 (gap 0,31 m → 0; swept 0/0). Testy dotknięte: 173 pass. Artefakty i derived 01/02/03/korycin skopiowane do main (03/korycin = r1).
- W toku (odłączony pwsh): world r2 03 → korycin (czeka na heavy; regen-wave-2 trzyma 3/3 od 14:08).
NASTĘPNY KROK: po `artifacts/s8-north-s24/run/route-dk8-korycin-01-r2.exit`: `pwsh -NoProfile -File tools/worldgen/qa/s8_north_s24.ps1 -Phase unity -Tiles dk8-wasilkow-03,dk8-korycin-01 -Tag r3`; WORLD_MEMORY z logów → tools/worldgen/streaming/tile_graph.py; `uv run --project tools/worldgen python tools/worldgen/streaming/tile_graph.py; ...route_links.py; uv run --no-project python scripts/export-region-catalog.py; uv run --no-project python tools/ui/build_nav_trips.py`; seams (02|03 musi wrócić do 0 FAIL, złącze 02→03 ≤ 0,1 m, inaczej link jak 01→02); route_obstacles --corridor bialystok-wasilkow; robocopy derived 03/korycin do main.

## 18:25 r3
- merge origin/main (roof-tiles ADR 0316) czysty. Kafle NIE przebudowane po 0316 (dachy/płoty działek w GLB = r2) — zostaje do pełnej przebudowy lidera.
- 03 r2: road_consistency na trasie (pas 30 m): 88 bridge_kerb (≥ 5,3 m od toru), 95 obstacle 'none' (20 < 2,5 m od toru, s 614–626 m, łańcuch 703487195/239748583 przy zjeździe węzła — było też w r1, route_obstacles r1 = 0), 46 marking_off, 4 furniture (≥ 7,3 m). korycin-01 r2: na trasie 0.
- seams r3: 02|03 i 03|korycin 0 FAIL; 01|02 2 FAIL (service 306912739, trunk 876126468: w sieci 01 krótki odcinek 27,6 m way 876126468 przy szwie nie tworzy własnego łańcucha — szew obsługuje taper 9,0→8,5 m w 01 i link wasilkow-01-to-02).
- import r3 03/korycin w toku (przebudowa PBR Medium po merge).
