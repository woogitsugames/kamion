# ADR 0063 — CC0 surface scans as the base of the world materials (D40)

Status: Proposed (world-builder, 2026-11-10), for the lead to integrate. Changes ADR 0010 (no external textures) per owner
decision D40; extends ADR 0022 (PBR sets contract) and keeps ADR 0025 (APK masks) and ADR 0049 / D37 (paint calibration).
Evidence: `artifacts/cc0-r8/` (worktree of this task; STATUS.md, before/after control frames, montages, CSV).

## Context
- Reviews r6-r8 keep the world at 6/10; r8: "materials 6", asphalt "still a uniform fine noise", the whole frame reads as
  "a clean model from a 2012 PC game". Every ground and facade set was procedural (`_src/sets_*.py`), and procedural
  micro-detail (noise + Voronoi) is the "generator look" docs/06 §2 forbids.
- D40 (owner, 2026-11-10): CC0 scans from Poly Haven and ambientCG may be the base; the licence of every asset is checked
  and listed in `docs/LICENSES.md`; generators keep the layout, wear and variants.

## Decision
1. **Sources and pinning.** 13 Poly Haven assets (CC0 1.0, licence page checked 2026-11-10), 2k JPG maps (Diffuse,
   nor_gl, Rough, AO, Displacement), listed with URL, size, API md5 and SHA-256 in `art-source/world/cc0/cc0_manifest.json`.
   Raw files (162 MB) stay out of git in `art-source/world/cc0/_raw/`; `_src/cc0_fetch.py` downloads and verifies them
   (`scripts/import-region.ps1` calls it before the PBR build). ambientCG: allowed, not used in this version.
2. **Processing as code** (`_src/sets_scan.py`, called by `build_all.py`; `--procedural` keeps the old sets for A/B):
   partial de-lighting by the scan AO, log-luminance flattening of everything longer than 0.35-1.5 m (the 64 m macro map
   owns that scale, the scan's blotches would otherwise repeat with the tile), white balance to the previous set's mean
   colour with the scan's relative colour kept, albedo mean calibrated to the same targets as before; height from
   Frankot-Chellappa integration of the scan normals (metres, so the tier writer's normals and Toksvig smoothness keep
   working); paver / slab ids for Var.G from the displacement map (periodic labelling); 2 m isotropic scans re-assembled
   offline into 4 m tiles (16 rotated / flipped patches, variance-preserving blend: no shader cost); hybrids keep the
   procedural layout (JOMB plates, 5 m sawn joints, kerb units, large-panel joints, trapezoid ribs) and take the scan's
   micro relief, albedo ratio, roughness and AO.
3. **Polish sizes over the scan's claimed size.** Element periods are measured (autocorrelation) and scaled to the
   standard: holland 20 x 10 cm (row 103.5 mm; scan 140.8 mm -> x 0.735), NF brick course 75 mm (scan 69.7 mm -> x 1.076),
   sidewalk slab 35 x 35 cm (scan 294 mm -> x 1.199). Behaton block (~210 x 140 mm rows) kept as scanned. WORKING_VALUE.
4. **Engine.** No shader change: the sets keep the `materials_spec.json` contract (tile size now from the scan),
   `WorldPbrMaterials` reads it. Element tone jitter is halved on segmented scan sets and off on unsegmented ones
   (the photo already carries per-element tone; without ids it would step per tile).
5. **Not in this ADR:** grass / hedges (world-builder, ADR 0060), tree bark (set `bark_pine` processed but not assigned),
   glass, vehicles. `sidewalk_slab_35` is built but no manifest material uses it yet.

## Consequences
FILLED_BELOW
