# Vegetation r2 — ADR0088 — gpt-vegetation-r2

- Krok1: przeczytano pełny kontrakt S10/B, HANDOVER s9, CLAUDE, AGENT-RULES i skill visual-qa; branch z main4f7da66c. Praca wyłącznie w tym worktree; bez telefonów, main, dróg, scen/ustawień i innych worktree. Materiały Fab tylko w ignorowanych wynikach.
- NASTĘPNY KROK: `git lfs checkout` i bootstrap kopii danych oraz produktów Fab/Unity według GPT-TASK-02-S10.md.

- Krok2: git-lfs checkout + fyzické kopie derived/cc0/Fab produktů/_Generated/materialcache/Library; vstupy gugik/osm/refs/mapillary/fab junction pouze pro čtení. NASTĘPNY KROK: `uv run --project tools/worldgen python -m pytest tests/gis -q` po auditu výchozího stavu a s9recenzí.


- Krok3: odtworzono baseline świata z HEAD, nie użyto starej sceny main; build bez fallback=True, zapisano SHA surowych produktów. NASTĘPNY KROK: `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` i4zestawy kontrolne.

