# STATUS — edge-far-r1 (ADR 0085: far-field backdrop)

- **Gałąź:** `argon-edge` (worktree `.claude/worktrees/argon-edge`)
- **Start:** utworzono worktree `argon-edge` z `main` (`9e04830`), skopiowano `Data/raw/derived`, `Data/raw/cc0`, `game/Assets/_Generated`, `art-source/world/materials`, `game/Library`, utworzono junctiony dla `gugik`, `osm`, `refs`, `mapillary`, wykonano `git lfs checkout`.
- **NASTĘPNY KROK:** analiza obecnego `WorldEdgeBuilder.cs`, `RegionImporter.cs` oraz dostępnych danych OSM (`podlaskie-261108.osm.pbf`) i GUGiK (BDOT10k 2061, LoD1 2061, NMT) w pierścieniu 2–6 km wokół `bialystok-industrial-c`:
  `uv run --project tools/worldgen pytest tests/gis -q`
