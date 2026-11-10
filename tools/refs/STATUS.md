# STATUS: otwarte źródła referencji (D43, ADR 0066), stan 2026-11-10

Gałąź: worktree-agent-ab1fb0a47d2f0a491 (nie scalona; integruje lider).

## Zrobione
- Kod: `tools/refs/{refs_common,open_sources,gugik_ortho,bialystok_open_data}.py`, testy `tests/refs/test_open_sources.py` (48 zielonych).
- ADR 0066, README `tools/refs`.
- Pobrane (poza gitem, `Data/raw/refs/<źródło>/`, junction `Data/raw` -> główny katalog): KartaView 79 zdjęć (pokrycie ujęć 13-55, 41/55), Panoramax 23 (17/55),
  GUGiK ortofoto 55 kadrów 160 m (WMS bywa zwraca białe kafle, klient ponawia), dane Miasta Białystok (ArcGIS Online, brak drzew/oświetlenia/znaków).
- Montaże: `artifacts/refs/<źródło>/` (w worktree; skopiować do głównego `artifacts/refs` przed usunięciem worktree).

## W toku / do zrobienia
1. Commons (`--source commons --categories`) działa w tle; Openverse zwracał 504 (API chwilowo niedostępne), ponowić:
   `uv run --project tools/refs python tools/refs/open_sources.py --source openverse --interval 1.5`
2. `docs/REFERENCES.md`: dopisać tabelę źródeł; `docs/LICENSES.md`: wpisy źródeł (KartaView/Panoramax/Commons/Openverse/GUGiK ortho/Miasto Białystok).
3. Skopiować artifacts/refs z worktree do głównego repo, odpiąć junctiony (`Data/raw`, `artifacts`?) przed usunięciem worktree.
4. Raport końcowy (<= 20 linii).

## Komendy
    uv run --project tools/refs pytest tests/refs -q
    uv run --project tools/refs python tools/refs/open_sources.py --source kartaview --radius 80
    uv run --project tools/refs python tools/refs/open_sources.py --source panoramax --radius 100
    uv run --project tools/refs python tools/refs/open_sources.py --source commons --radius 600 --categories
    uv run --project tools/refs python tools/refs/gugik_ortho.py --interval 1.5
    uv run --project tools/refs python tools/refs/bialystok_open_data.py --catalog

## Log
- 19:59 commons: geosearch+imageinfo gotowe (cache 163), pobrano 83 plików, potem stoi na 429/Retry-After z upload.wikimedia.org. Następny krok: gdy proces skończy
  (lub po ubiciu) ponowić tę samą komendę (cache + manifest wznawiają bez duplikatów), potem openverse (API zwracało 504).
- Openverse: 504 na każde zapytanie o 19:4x; ponowić `open_sources.py --source openverse --interval 1.5`.
