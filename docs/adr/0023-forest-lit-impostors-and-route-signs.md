# ADR 0023 — Lit multi-view impostors, lit HLOD edge walls, forest understorey; signs from OSM and roundabout signing (world v3.4)

Status: Accepted (world-builder), 2026-11-09. Extends ADR 0012 (instancing), ADR 0013 (Kamion/Vegetation), ADR 0015
(forest HLOD), ADR 0016 (tone curve), ADR 0022 (world materials).
Evidence: `docs/reports/visual/world-c/v34/README.md` (before / after frames, editor GPU timings),
`tests/gis/test_world_v34.py`, `Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json` (`route_signs`,
`route_checks`, `roundabout_signs`, `osm_signs`, `vegetation.understorey`).

## Context
- Reviews r3 / r4 and the v3.3 README: the DK8 forest from the cab shows "lollipops" (isolated crown specks above the
  HLOD silhouette, W-H8), black spots in crowns (W1), a beige "camouflage" on the stand edge at low sun (W2), dotted
  crown arcs on Low and trunks standing like a fence on a swept beige floor (X4).
- Causes found in this task:
  - impostors were two crossed quads with one side view baked under a uniform white sky: at grazing angles the second
    quad is a sliver, both quads overdraw, and the lighting baked into the colour cannot follow the sun (low sun);
  - HLOD edge texture: interior trees were darkened by hand (×0.3 material copies) and the bake kept sub-texel crown
    tips at the top of the texture; far away coverage-preserving mips turn those tips into isolated dots along the
    wall tops (`artifacts/vqa/abl`: the arcs vanish with `rq_hlod=0`);
  - the forest floor was one beige albedo and the stands had no understorey.
- Signs: tile C has one `traffic_sign` node in the OSM extract area (outside the tile) and 22 give-way / stop nodes;
  the start route (G3) had A-7 + C-12 at roundabout entries but no splitter-island C-9, no exit direction boards and no
  roundabout diagram boards; plates were flat cards without rim, clamps or a real back.

## Decisions
### 1. Impostors: N views, lit at run time
- `make_trees.py` bakes every tree from IMP_NF = 6 azimuths (60°) in three Cycles passes: albedo (emission of the
  material base colour, sRGB), view-space normal and sky visibility (white diffuse, uniform sky, direct only).
  The packer (numpy in Blender) opens the coverage (drops 1–2 texel twigs), dilates colour and normal under the
  alpha (no fringe when mips or alpha-to-coverage switch an edge texel on), and writes `impostor_<tree>.png`
  (RGB albedo + A coverage, 6 × 256 × 384) and `impostor_<tree>_n.png` (RG normal, B visibility, linear, half
  resolution).
- Engine: `Kamion/Vegetation` `_IMPOSTOR`: one quad per tree, turned to the camera about the tree axis (cylindrical
  billboard, all passes), the two views around the camera azimuth cross-faded (`_KamionImpostorBlend` = 1 on Medium+,
  nearest view on Low = half the fetches), lit like the leaf cards (Lambert sun + shadow, transmission, SH from the
  sky model up / side / down per vertex blended by the texel normal), visibility applied to ambient (0.45) and sun
  (0.25) so the impostor crown matches the LOD1 cards at the switch distance (WORKING_VALUE, see the table in the
  README). The impostor colour is the leaf texture albedo, so the far tree goes through the same tone curve
  (ADR 0016) as the near one.
### 2. HLOD edge walls lit the same way
- The edge texture is baked from the same three passes with the stand interior **not** darkened by hand: its
  darkness is the sky visibility of the occlusion pass. Speck islands < 600 texels (~1.4 m²) are removed.
- `forest_edge_<mix>` gets `normal_ref` in the manifest; Unity draws it with `_HLOD_EDGE` (wall-space normal, tangent
  frame from screen derivatives, SH per pixel, visibility 1.0 / 0.6). The canopy stays an opaque URP Lit surface with
  the visibility multiplied into its colour.
### 3. Forest floor and understorey
- `vegetation.place`: hazel and young pine / birch (1.2–7.5 m, one per ~60 m²) inside every BDOT10k "las" polygon;
  they carry `fc` like the stand trees (replaced by the HLOD far away). The edge bake uses the same mix.
- `Kamion/World PBR` `_GROUNDMASKS`: forest floor = needle litter patches with feather moss / bilberry from the
  64 m macro map instead of one beige albedo.
### 4. Signs
- `streetscape/signs_route.py`: OSM `traffic_sign=PL:<code>` nodes (direction forward / backward / degrees, else the
  side they are mapped on), give-way / stop nodes with a direction away from junction centres, roundabouts (C-9 on
  splitter islands, E-2a style boards at exits from OSM `destination` / `ref` / `name`, E-1 style diagram boards
  80 m before GP/G entries of rings ≥ 18 m). Unknown codes are reported, never invented.
- New faces B-1, B-2, B-36, C-9 and the diagram board; every face is aged (film toward the lower edge, mottle,
  specks, faded red, darker rim; deterministic per code).
- Plates: 25 mm folded rim, mill-finish back texture with a blank label, two galvanised clamps on the post.
- `route_audit` lists every sign within 12 m of the start route (`route_signs`, chainage, facing) and checks every
  roundabout on the route for A-7 + C-12 (+ E-1 where placed) facing the route driver (`route_checks`).

## Consequences
- Texture memory (ASTC 6×6 + mips): impostors ≈ 7.9 MB (v3.3: 1.05 MB), Android max size 2048 for the impostor atlases
  only; edge normal maps ≈ 0.2 MB.
- GPU (editor, RTX 5070, forest = frame − frame without trees): Low DK8 1.33 → 1.23 ms, High DK8 1.62 → 1.85 ms
  (repeat noise ±0.15 ms). Low keeps the v3.3 thinning strides (a later start cost +25 % instances). A16 Low DK8 is
  estimated unchanged (≈ 26–27 ms GPU, budget 33 ms) — UNVERIFIED until the next device run.
- Edge textures repeat in U only (V clamped): the v3.3 dotted arcs over the DK8 forest were the wall tops sampling the
  wrapped bottom rows (ablation renders in `artifacts/vqa/abl`, not versioned).
- Plates / boards: the face is +y in the prototype frame and u runs against +x (seen from the front in Unity, local +x
  is on the viewer's left): v3.3 discs and boards showed their back, and digits would have been mirrored.
- Blender control renders show impostor view 0 turned to the camera and multiply the HLOD albedo by its visibility.
- Placement distances of E-1 / E-2a and the sign colours of boards are WORKING_VALUE until checked against
  [ZNAKI-Z1] Załącznik 4 tables.
