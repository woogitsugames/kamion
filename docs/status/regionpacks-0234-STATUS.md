# regionpacks-0234 (PR #112) — FIX s22 D12 (ADR 0273)
- Merge origin/main (STATUS.md = main). Paczka = pełna scena + `_Tile` w jednym bundlu; `RegionPackLeases` (licznik referencji) zamiast `UnloadAll`; `Acquire/Release` w `IRegionPackProvider`; `-Target Android|Win64`; nazwy przez `RegionScenes`; lista kopii z Resources.
- Testy: RegionPackTests 50/50 pod .NET 8 (harness scratchpad rp4), serwis/komendy kompilują się na zaślepkach (rp5). Nieskompilowane w Unity.
- NASTĘPNY KROK (lider): `pwsh scripts/test.ps1 -Platform EditMode`; potem `pwsh scripts/build-region-packs.ps1 -Target Win64 -Regions dk65-06 -InstallLocal`.
