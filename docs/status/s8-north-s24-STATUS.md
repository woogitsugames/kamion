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
- [ ] pytest + EditMode

NASTĘPNY KROK: czekaj na artifacts/s8-north-s24/pytest-r1.log (exit=) i artifacts/s8-north-s24/run/editmode-r1.exit; potem kopia kafli do main: robocopy .claude\worktrees\s8-north-s24\Data\raw\derived\<kafel> Data\raw\derived\<kafel> /E /MT:16 + artefakty
