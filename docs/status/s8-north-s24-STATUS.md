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
- [~] ingest → build_region → build_world → export-route: 03 (2068 m, road_consistency 239, na trasie 0) i korycin-01 (963 m, 9, na trasie 0) gotowe; 01/02 ingest — WFS GUGiK zrywa połączenie (SkorowidzOrtofomapy2026), retry + raport warstw niedostępnych
- [~] qa.seams 03|korycin: 0 FAIL. link C → szew N, tile_graph/route_links/katalog, qa.seams, route_obstacles
- [~] import Win64 + visual-qa High: dk8-wasilkow-03 r2 OK (WORLD_MEMORY High 200,4 MB; render węzła, ekrany akustyczne po zach. stronie, bariery; `artifacts/s8-north-s24/vqa-r2/dk8-wasilkow-03/small`). Brakował SM_CabInterior_LOD0.fbx w worktree — skopiowany z main.
- [ ] pytest + EditMode

NASTĘPNY KROK: czekaj na world dk8-wasilkow-01 (slot heavy) i ingest 02 r2; potem `pwsh -NoProfile -File tools/worldgen/qa/s8_north_s24.ps1 -Phase world -Tiles dk8-wasilkow-02 -Tag r1 -Context`
