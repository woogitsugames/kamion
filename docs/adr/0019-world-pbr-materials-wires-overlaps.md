# ADR 0019 — World PBR texture sets in Unity, power-line ribbons, marking overlaps (world v3.3)

Status: Accepted (world-builder), 2026-11-09. Extends ADR 0012 (tiers), ADR 0015 (far facades), ADR 0018 (overlaps).
Evidence: `docs/reports/visual/world-c/README.md` (v3.3 before/after frames), `tests/gis/test_world_v33.py`.

## Context
- REVIEW r4 §5: the world in Unity reads as "a mobile game from 2014" — flat untextured yard, box halls, dotted wires
  without poles, sterile asphalt (W-H1, W-H2, W-H6). The generated PBR sets of `art-source/world/materials` (lead decision:
  generated, not versioned) were never used by the engine; Unity drew one grey 512 px detail map per surface kind.
- W-H4: the same frame showed a different building on Low and High.
- r3 W3 / r4 W-H5: kerbed islands and verges looked like troughs with green vertical walls.

## Decisions
### 1. One PBR shader for generated sets (`Kamion/World PBR`, `game/Assets/_Project/Environment/Shaders`)
- Contract = `materials_spec.json`. A manifest material with `texture_set` naming a set of the spec gets the shader;
  others keep `Kamion/World Surface`. Kinds: `tiling_set` (calibrated albedo; tint = manifest colour / set mean, so the
  generator now writes the set means as manifest colours), `modulation_set` (new facade / prop sets, neutral mean 0.5,
  albedo = 2 × manifest colour × map, mesh UV0 in metres), `decal_atlas` (oil).
- UV: world planar (ground), mesh UV0 (kerbs, walls, props), TEXCOORD_1 along/across the road for `road_concrete`
  (5 m joints across the carriageway, longitudinal joints on lane lines); junction patches fall back to planar.
- Layers: macro_variation on every material (64 m + rotated 264 m octave on Medium+), crack layer on worn asphalt
  (faded by the macro wear mask), photo detail on asphalt within 25 m (Medium+), per-element tone jitter from Var.G
  (faded below ~2 px per element), road wear from TEXCOORD_1 (wheel paths, gutter grime), patch age, oil atlas cell,
  procedural tyre scrub (alpha) and cast-iron gully grates.
- Tiers: Low = base, normal, mask, one macro sample (4 samples); Medium/High add Var, cracks, macro octave, detail.
  Aniso / mip bias per tier through `QualityProfileApplier.worldTextures` (PBR textures appended).
- Textures: the import script builds missing sets (`build_all.py`, deterministic, all tiers so the spec stays
  byte-identical) and Unity copies `-MaterialTier` (default **Medium**: 1024 px per 4 m tile = 3.9 mm/texel) into
  `_Generated/World/<id>/Textures/PBR` with ASTC per spec. One material set serves Low and High content (WORKING_VALUE;
  High-tier 2048 maps for the flagship need per-quality mipmap-limit groups = ProjectSettings, lead decision).
- `road_asphalt_new` (asphalt_sma_fresh): no resurfacing date exists in OSM / BDOT10k; 25 % of public chains (class Z
  and up, not roundabouts, not bridges; hash of the chain id) are resurfaced, junction patches stay worn, no repair
  patches on them. Override `surface: asphalt_new` / `asphalt` wins. WORKING_VALUE.

### 2. TEXCOORD_1 is flipped back on import
The generator writes every UV set with v flipped (glTF convention); `GlbReader` flipped TEXCOORD_0 only, so TEXCOORD_1
arrived as 1 − v. Far facades (ADR 0015) drew panes on the plinth strip and the ground floor only, which made the same
block a bare box on Low (LOD1) and a windowed block on High (LOD0): W-H4 / W-H7. Both sets are now flipped back.

### 3. Power lines: supports from the line geometry, conductors as ribbons
- BDOT10k `OT_SULN_L` angle points carry a support unless a mapped pole/tower stands within 10 / 15 m (then the span
  ends on it and its cross-arm is turned across the line); straight runs get intermediate supports every ≤ 80 m (MV,
  concrete pole) / 350 m (HV, lattice tower). WORKING_VALUE spans. Tile C: 44 of 74 angle points had no support.
- Conductors are a separate node `wires`: thin vertical ribbons with TEXCOORD_0 = (side, half width) and COLOR_0 =
  tangent. `Kamion/World Wire` rebuilds the centre line and expands it towards the camera to ≥ 1.2 px with alpha =
  physical / drawn width (continuous faint line instead of dotted geometry) and fades it out with the pole cull
  distance (`_KamionWireFade`, set by `WorldInstances` from the pole prototypes): a wire never outlives its poles.

### 4. Overlapping markings (ADR 0018 overlap zones)
Marking triangles of one chain whose centre lies ≥ 0.25 m inside another chain's carriageway (same level within 1 m,
inside its trimmed range) are removed (`markings.drop_overlapping`). Lines on a shared touching edge are kept.

### 5. Terrain under grass strips
Footprint nodes covered only by `verge_grass` and ≥ 2 nodes from any hard surface keep the terrain 0.04 m under the
grass instead of 0.35 m (`conform.SOFT_UNDER`): the 1–2 m terrain grid no longer dips inside narrow islands and behind
verges, so the strips' flanges stop showing as green walls. The 0.30 m clearance test still holds for every hard surface
and its 2-node neighbourhood.

### 6. Yard detail (Kwadrat Park, W-H1)
Painted truck-stand lines (0.12 m, worn paint `marking_yard`) between the 3.8 m stands along yard edges and a front
line at 17.5 m, never in the dock manoeuvring zone; yard gullies on a jittered 24 m grid; street gullies every ~35 m at
kerbed edges (low side of one-way carriageways). Facade sets for halls (sandwich panels, trapezoid sheet, precast plinth,
sectional doors), blocks (plaster, large-panel joints, brick) and props (curtain folds, container corrugation).

## Consequences
- APK: + PBR textures of the Medium tier, ASTC (spec estimate summed in the import report `pbr_textures_gpu_bytes_astc`);
  meshes: + TEXCOORD_1 (f16×2) on road ribbons, + UV0 on kerbs / walls / props, + `wires` node. Numbers in the report.
- Fragment cost on the A16 is not measured (no phone in this task): Low draws 4 texture samples on ground instead of 2.
  UNVERIFIED until the next device run; the Low path can drop the normal map if it costs > 1 ms.
- Blender control renders keep their own procedural materials (`render_control.py`); `road_asphalt_new` added there.
