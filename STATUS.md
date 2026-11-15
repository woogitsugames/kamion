# STATUS — streaming-0235 (F2, ADR 0235, baza region-select-0229)

- [krok 1] Graf sąsiedztwa kafli: `tools/worldgen/streaming/tile_graph.py` → `game/Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming/tile_graph.json`
  (21 kafli, 17 portali trasy, korytarz D67 C..knyszyn = 17 kafli). pytest `tests/gis/test_tile_graph_0235.py` 7/7.
- NASTĘPNY KROK: logika decyzyjna C# (`Game.World.Streaming.StreamingPolicy`) + testy EditMode.
- [krok 2] Czysta logika C# (nieskompilowana w chmurze): `World/Runtime/Streaming/{TileGraph,StreamingPolicy,TilePlacement,EdgeSides}.cs`,
  `Core/FloatingOrigin.cs`, `WorldRegionRoot.PlaceAt`; testy EditMode `WorldStreamingPolicyTests` (19).
- NASTĘPNY KROK: runtime `WorldStreamer` (LoadSceneAsync additive, aktywacja rozłożona, cooking async) + import sceny `_Tile`.
- [krok 3] `WorldStreamer` (LoadSceneAsync Additive, allowSceneActivation, aktywacja chunków ≤ 2 ms/klatkę, cooking async
  `WorldCollisionCooker.BeginCook/PollCook`, szwy otwierane dopiero gdy oba kafle Ready, rebase originu w FixedUpdate),
  `RegionScenes.TileSceneNameFor`. NASTĘPNY KROK: integracja (bootstrap, safety net, kamera, autopilot) + import `_Tile`.
