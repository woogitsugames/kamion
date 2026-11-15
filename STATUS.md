# STATUS — streaming-0235 (F2, ADR 0235, baza region-select-0229)

- [krok 1] Graf sąsiedztwa kafli: `tools/worldgen/streaming/tile_graph.py` → `game/Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming/tile_graph.json`
  (21 kafli, 17 portali trasy, korytarz D67 C..knyszyn = 17 kafli). pytest `tests/gis/test_tile_graph_0235.py` 7/7.
- NASTĘPNY KROK: logika decyzyjna C# (`Game.World.Streaming.StreamingPolicy`) + testy EditMode.
