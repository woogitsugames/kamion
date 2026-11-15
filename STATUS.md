# STATUS — regionpacks-0234 (F1, ADR 0234, osobne paczki regionów, D67)
- [start] worktree od origin/main 25924f60b; przeczytane ADR 0011/0012/0229 (#104), BuildCommands, env.ps1, build-android.ps1.
- NASTĘPNY KROK: runtime `Game.World.Packs` + komenda `RegionPackCommands.BuildRegionPacks` + testy EditMode.
- [krok 1] runtime `Game.World.Packs` (manifest, ścieżki, sha256, resolver stanów, instalator incoming/, etykiety PL, IRegionPackProvider, RegionPackService) + edytor `RegionPackPlanner`/`RegionPackCommands.BuildRegionPacks` + `RegionPackTests` (EditMode). Chmura: .NET 8 + NUnit z zaślepką JsonUtility(STJ) 42/42 zielone; Service/Commands kompilują się na zaślepkach API. Nieskompilowane w Unity.
- NASTĘPNY KROK: `scripts/build-region-packs.ps1` + `scripts/estimate-region-packs.py` + ADR 0234.
- [krok 2] `scripts/build-region-packs.ps1` (build + weryfikacja sha256 + `-Push` adb do incoming/), `scripts/estimate-region-packs.py` (tabela ESTIMATED), ADR 0234 (decyzja, rozmiary, propozycja PAD, diff dla #104 w zał. A). Indeks ADR (README) nie regenerowany — lider (konflikty z innymi PR).
- NASTĘPNY KROK (lider): `pwsh scripts/test.ps1 -Platform EditMode` → `pwsh scripts/build-region-packs.ps1 -Regions dk65-06` → push + A16.
