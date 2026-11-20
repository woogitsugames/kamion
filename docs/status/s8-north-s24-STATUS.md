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
