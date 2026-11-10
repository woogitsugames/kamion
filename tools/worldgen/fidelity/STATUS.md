# STATUS — fidelity-r9 (ADR 0075, road fidelity vs OSM / ortho)

Branch `fidelity-r9` (worktree agent-aee7234325983b8dc). Evidence: `artifacts/fidelity-r9/` (copied to main artifacts).

- 2026-11-10 20:40 — OSM extract is fresh: Geofabrik podlaskie snapshot 261108 (2026-11-08), downloaded 2026-11-09; no new download.
  Graph is from the same snapshot. Hi-res ortho: 49 WMS cells 128 m @ 0.08 m/px along route + Bieżeństwa + Putry
  (`Data/raw/refs/gugik-ortho-hr/<region>/`, manifest.jsonl, 27 MB). Registration vs 0.25 m sheet: |shift| <= 0.25 m (1 px).
- Package `tools/worldgen/fidelity/` (osm_truth, gen, ortho, imaging, metrics, overlays, run). NEXT:
  `uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c`
- Ownership (no duplication with ADR 0074 agent): I do NOT edit roads/junctions.py, meshing.py, markings.py geometry.
  I only read the generator; possible own fixes limited to OSM import of lane tags (roadgraph.RAW_TAGS / network.edge_section).
- 2026-11-10 21:10 — route run: axis p95 0.03 m (target met), edge p95 4.28 m all detections (sidewalk ambiguity; reliable
  road->verge metric added), lanes 25/27, gen islands absent on ortho 39 (pre-filter), lane->island on route 3, all
  "generator island on real road" (j:n12620261934 Andersa signals = likely owner bug; Bieżeństwa entry from Kwadrat Park).
  Full run (route + tile) in progress. NEXT:
  `uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c` then fill BASELINE/MET in
  tests/gis/test_road_fidelity.py and `uv run --project tools/worldgen pytest tests/gis/test_road_fidelity.py -q`.
- 2026-11-10 21:40 — full run (route + 75 tile junction windows, ~4 min). Route: axis p95 0.03 m, edge (road->verge) p95 2.04 m,
  lanes 25/25 verified, islands absent 4, lane->island bug 3 (owner bug = j:n12620261934 lane 0 through, E -283 N -197).
  Test tests/gis/test_road_fidelity.py: 8 passed, 2 xfailed. DIFFS.md final top 10. NEXT (mine): read destination:lanes /
  placement in roadgraph.RAW_TAGS (+ QA entry for dropped turn:lanes) — NOT started. NEXT command:
  `uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c && uv run --project tools/worldgen pytest tests/gis/test_road_fidelity.py -q`
- 21:50 determinism: two full runs -> identical fidelity_qa.json sha256 08b902f6...f286.
