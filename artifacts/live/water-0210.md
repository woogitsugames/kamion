# water-0210 (ADR 0210)
- water stage in build_world (opt-in region.yaml water.enabled; dk65-02 on). r1 world: 84.6k water nodes, sheet 88.7k m2 / 16.7k tris; tests/gis/test_water_0210.py 8/8.
- running: import+vqa r1 (chain.status), determinism C+Dojlidy (determinism.status)
- NEXT: pwsh artifacts/water-0210/tools/chain.ps1 -Tag r2 (after tuning)
