# STATUS — knyszyn-look-s23 (podobieństwo Knyszyna: zabudowa i punkty orientacyjne, D51)
Gałąź `knyszyn-look-s23` (z origin/main 64e54592e), worktree `.claude/worktrees/knyszyn-look-s23`. Raport: `docs/reports/knyszyn-look/README.md`.
- Krok 1: inwentarz OSM vs buildings.geojson (`tools/worldgen/qa/landmark_inventory.py`; knyszyn 87 obiektów, -w 12, -s 0). Mapillary 400 klatek (brak Szkolnej). Commons: tylko linki.
- Krok 2: generator — `roof_material` także dla dachów spadzistych nie-domów, nowy `roof_sheet_grey` (tylko z nadpisań), `wall_material` / `typology: dom_drewniany` dla domów; `pipeline.generated_overrides` (pliki generowane przed overrides.yaml).
- Krok 3: dane — `overrides.ortho_roofs.json` (1577 dachów z ortofoto 2025; 4/4 zgodne z ręcznymi z ADR 0227), `overrides.class_fixes.json` (99 OSM-only < 60 m² → gospodarczy 3 m, 49 → dom, 20 usługowych z wzniosem LoD2 ≥ 1,5 m → dach spadzisty), ręczne: poczta, dom narożny 2E17, Dom Klattów, parking dyskontu (3 poligony), 6 kamer `look_*`.
- Krok 4: „przed” = build origin/main + nowe kamery: `artifacts/knyszyn-look-s23/vqa-before/High-clear` (75 PNG). „Po”: `chain.ps1 -Tag after`.
- UWAGA: `Data/raw/derived/knyszyn/world` (junction do main) zawiera build TEJ gałęzi po kroku „po”; main po scaleniu innych PR-ów musi przebudować kafel.
- NASTĘPNY KROK: `pwsh -NoProfile -File artifacts/knyszyn-look-s23/chain.ps1 -Tag after` (jeśli `chain-after.status` nie kończy się CHAIN DONE), potem `uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider -k "knyszyn or typology or buildings"`.
