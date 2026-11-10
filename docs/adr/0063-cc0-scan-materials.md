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
Measured on WorldC control cameras (9 frames per condition, bottom-centre road ROI, sRGB median; `artifacts/cc0-r8/measure.csv`):

| condition | asphalt before | asphalt after | paint/asphalt before | after | paint p-max before/after |
|---|---|---|---|---|---|
| Low overcast | 100 | 101 | 1.52 | 1.51 | 184 / 184 |
| High overcast | 105 | 105 | 1.53 | 1.52 | 203 / 204 |
| Low lowsun | 52 | 52 | 1.65 | 1.56 | 92 / 89 |
| High lowsun | 55 | 55 | 1.60 | 1.57 | 94 / 96 |

- Calibration kept: asphalt Low ov ~100 / High ov ~105, paint/asphalt >= 1.5 everywhere, no paint clipping (max <= 217).
  The 1.8 target of D37 is not reached by this change (paint material untouched); lowsun ratio dropped 0.03-0.09 because
  the scan asphalt carries lighter aggregate. Open for the paint/calibration owner.
- Look: pavers (holland 20 x 10, behaton) and concrete read as photographed surfaces, no visible tile repetition in
  close crops (`artifacts/cc0-r8/closeup/`); asphalt gains blotchy aggregate and patches, but the fine-scale texture
  sigma is lower (High ov 2.72 % vs 3.57 %), so the frame-level change on asphalt is subtle. **Not solved here:** the
  light-grey asphalt with wheel-path rut streaks and patch lines seen on Mapillary (findings #7) is a macro/wear layer
  (lane-aware masks), not a 4 m scan tile; it needs a follow-up in the road wear generator.
- Size: world/Textures/PBR 23.01 -> 20.80 MB raw; APK 156.52 MB -> ~155.4 MB; `-noWorld` APK 55.34 MB, so the world
  share is ~100.1 MB (D24 limit 110 MB). No shader change, so no GPU cost change expected (not measured on phone).
- Pipeline: `import-region.ps1` now needs network once (cc0_fetch, 162 MB, sha256-verified) or a filled
  `art-source/world/cc0/_raw/`; `build_all.py --procedural` reproduces the old sets.
- Tests: `tests/gis` 167 passed (incl. `test_cc0_scans.py`), EditMode 137 passed / 0 failed (2 inconclusive truck-glass tests, unrelated).
