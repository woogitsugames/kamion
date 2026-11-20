# krywlany-s24 — STATUS (kafel bialystok-krywlany, ADR 0278 kafel 4, D93/D63)

- Worktree `.claude/worktrees/krywlany-s24` (gałąź krywlany-s24, -CopyDerived). Kafel = siatka (0,-3): bbox 776971,589055–779019,591103, powiat 2061.
- Krok 1 (gotowe): `tools/worldgen/qa/krywlany_tile_0278.py` (kawałek korytarza c-to-dojlidy-g10: krywlany 1205 m od szwu Dojlid na Ciołkowskiego (779019,591055.7) do wejścia trasy Dojlid (779019,590253); stub w Dojlidach 87 m z mickiewicza), wpis `regions.py`, pliki authored (overrides.yaml pusty, sources.authored.json pin NMT 2025, route_endpoints.json).
- Dane: NMT 2025 arkusze N-34-107-C-b-3-2/-4 są na dysku (Dojlidy), -3-1/-3-3 brak → ingest pobierze z GUGiK (2 NMT + 2 ORTO).
- NASTĘPNY KROK: `uv run --project tools/worldgen tools/worldgen/ingest.py --region bialystok-krywlany --dry-run`
