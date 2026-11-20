# krywlany-s24 — STATUS (kafel bialystok-krywlany, ADR 0278 kafel 4, D93/D63)

- Worktree `.claude/worktrees/krywlany-s24` (gałąź krywlany-s24, -CopyDerived). Kafel = siatka (0,-3): bbox 776971,589055–779019,591103, powiat 2061.
- Krok 1 (gotowe): `tools/worldgen/qa/krywlany_tile_0278.py` (kawałek korytarza c-to-dojlidy-g10: krywlany 1205 m od szwu Dojlid na Ciołkowskiego (779019,591055.7) do wejścia trasy Dojlid (779019,590253); stub w Dojlidach 87 m z mickiewicza), wpis `regions.py`, pliki authored (overrides.yaml pusty, sources.authored.json pin NMT 2025, route_endpoints.json).
- Dane: NMT 2025 arkusze N-34-107-C-b-3-2/-4 są na dysku (Dojlidy), -3-1/-3-3 brak → ingest pobierze z GUGiK (2 NMT + 2 ORTO).
- NASTĘPNY KROK: `uv run --project tools/worldgen tools/worldgen/ingest.py --region bialystok-krywlany --dry-run`
- Krok 1b (gotowe): `Data/Streaming/route_links.yaml` — link `dojlidy-ciolkowskiego-corner-to-krywlany` (narożnik Dojlid 87 m, head_from mickiewicza, tail_to krywlany) + korytarz `bialystok-dojlidy-dk19` = [... mickiewicza, dojlidy, krywlany, dojlidy] (mickiewicza|krywlany to tylko narożnik, nie krawędź).
- Ingest dry-run #1: GUGiK WFS (indeks arkuszy) zerwał połączenie (RemoteDisconnected) — ponawiam. NASTĘPNY KROK: `uv run --project tools/worldgen tools/worldgen/ingest.py --region bialystok-krywlany --dry-run` (log artifacts/logs/krywlany-ingest-dry2.log)
- 2026-11-20: GUGiK WFS (mapy.geoportal.gov.pl Skorowidze) nie odpowiada (dry-run #2 ReadTimeout, curl 000 po 10 s); opendata.geoportal.gov.pl OK. Dodane ponowienia w `gugik_index.get_feature` (5×). W tle `artifacts/krywlany-s24/run/ingest-wait.sh` (sonda co 3 min do 2 h → ingest; log `artifacts/krywlany-s24/run/ingest.log`, koniec = linia INGEST_EXIT).
- NASTĘPNY KROK (po INGEST_EXIT=0): `uv run tools/worldgen/build_region.py --region bialystok-krywlany`
