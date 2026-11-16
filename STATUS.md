# STATUS — D30 streaming-pc-s23 (chmura D r8; ADR 0235/0234/0273)
- Krok 1: merge main (konflikt DrivingLabBootstrap: main + 1 hak `WorldStreamer.TryInstallFromLaunch`, WorldSafetyNet = main); runtime paczek (#112) usunięty, zostaje `ITileSceneSource` + `BuildTileSource` + `TileSceneSourceContractTests`; zabezpieczenie sieci przez poszerzenie prostokąta regionu startowego; testy GC (`GcAllocCounter`).
- Testy: .NET 8 harness 32/32 (polityka + kontrakt + LocalUnionBounds, GC 0 B); pytest `-k "tile_graph or stream or 0235 or 0273"` 11 passed. Nieskompilowane w Unity.
- PR #157 otwarty. NASTĘPNY KROK (lider): `pwsh scripts/test.ps1 -Platform EditMode`, potem PlayMode `-Filter Game.Tests.WorldStreamingPlayModeTests`.

## D36 safetynet-corridor-s23 (chmura D r9, 16.11)
- `CorridorEdge` (czysta logika krawędzi zewnętrznej korytarza; szew z sąsiadem Ready/Loading/Activating otwarty, Unloaded/Unloading = krawędź), `WorldStreamer.TryInsideDistance` deleguje, `WorldSafetyNet.Check` +3 linie. ADR 0273 §11.
- .NET 8: 40/40 (8 nowych `CorridorEdgeTests`, zero GC). Unity EditMode/PlayMode NIEuruchomione.
- NASTĘPNY KROK (lider, po scaleniu #157): `pwsh scripts/test.ps1 -Platform EditMode -Filter 'Game.Tests.CorridorEdgeTests;Game.Tests.WorldStreamerHook0273Tests'` i PlayMode `Game.Tests.WorldSafetyNetCorridorPlayModeTests`.
