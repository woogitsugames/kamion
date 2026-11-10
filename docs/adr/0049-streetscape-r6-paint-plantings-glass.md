# ADR 0049 - Review r6 streetscape: worn road paint over the real asphalt, Bieżeństwa plantings, clear noise screens, dock scrub shapes, poles on the terrain collider

Status: accepted (2026-11-10)

## Context
Review r6 (`docs/reports/visual/REVIEW-2026-11-10-r6.md`): W-H6 P1 lines and arrows snow-white on the A16 (median 246-249
sRGB, accept clear <= 217 / overcast <= 190), W-N12 P2 Rondo Bieżeństwa without hedges and a splitter island reading as an
empty concrete tub (accept `photo_biezenstwa_ground` p10 <= 24 %), W-N2 P2 noise screens: large perforation dimples and
uniform mint transparent panels, W-N11 P2 the same tyre-scrub arc at every dock door. HANDOVER: one real terrain wall
`j:n1847044961` (Rondo Putry) and 3 lamps 0.301-0.305 m above the ground (audit tolerance 0.30).

## Decision
1. **Road paint** (`marking_white`): Kamion/World PBR keyword `_DECAL_PAINT` (one more value of the existing decal
   `shader_feature_local` group, no extra variant axis) instead of the flat Kamion/World Surface colour. The base set is
   the road's own `asphalt_worn` in the same world-planar UV (calibrated, tint 1, cracks / photo detail as on the road);
   the paint film albedo stays 0.60 (0.55-0.65). TEXCOORD_1 per vertex (`roads.markings._paint_uv1`): x = lane coordinate
   on the carriageway convention (wheel paths at ~0.26 / 0.74 of a lane line up with the asphalt's polished paths),
   y = exposure (transverse P-8 / P-10 / P-13 / P-14 vs longitudinal lines) + a deterministic age 0..1 per mark.
   Shader: film worn through to the asphalt on the aggregate peaks (Var.R) in the wheel paths of transverse marks and a
   little everywhere with age, neutral grey traffic film 0.43 x (0.75..1.25 by age) (darker in wheel paths), wear thresholded into sharp-edged bare spots, distance
   pre-filter towards the asphalt beneath by line coverage (0.12 m lines, 0.4 m transverse). Effective albedo of the
   film ~0.25-0.45 (aged marking; WORKING_VALUE, EN 1436 luminance classes not measured here).
2. **Plantings** (`streetscape.plantings`, override `kind: plantings`, `biezenstwa-plantings`): OSM has no hedges here;
   4 hedge beds traced from the GUGiK 2024 orthophoto (EPSG:2180, OSM centrelines overlay it within 1-2 m) become
   closed berberis hedge masses 0.6-0.8 m (lawn rim kept, wavy clipped top, foot tucked 3 cm into the ground,
   `hedge_berberis` + new modulation set `hedge_foliage`). Kerb-enclosed islands (holes of the road footprint) named by a
   point are filled to the kerb top: the north splitter island with pavers (the orthophoto shows pavers there, not soil -
   the review's "soil and shrubs" applies to the ring centre), the ring centre with `bed_soil` (new set `soil_bed`, 3 cm
   under the kerb top) and sparse red shrub clumps that keep out from under the viaduct deck (piers). Fills carry
   collision. Vegetation never places trees in the beds. Stale targets are reported with the nearest holes.
3. **Noise screens**: `noise_glass` uses Kamion/World Car Glass (clear sheet, opacity 0.10, Fresnel sky reflection, road
   spray film on the lowest ~0.9 m from UV0 written by `roads.meshing`); the absorbing cassettes get round 10 mm holes on
   a 25 mm staggered grid in the normal / AO only (no albedo term) and `SurfaceSet.aa_tiers`: a Gaussian low-pass
   (sigma 0.6 x downsample factor) before each tier's box downsample, so Medium / Low carry no aliased dimples. The
   OSM barrier=wall concrete fence pointed at a missing set `concrete_fence_panel` (fallback detail map shimmered into
   the "dimples" of the review): new modulation set, 2 m bays x 0.5 m panels, pores, splash grime.
4. **Dock scrub**: 5 shapes (arc, wider arc from the other end, S-jog, skewed straight, tight hook) + "none" (~25 %),
   picked per door by hash and never equal to the neighbouring door; 1-3 passes; per-pass opacity 0.6-1.4 in TEXCOORD_1.y
   (the shader multiplies the decal alpha by it).
5. **Poles vs terrain**: the pole seat's terrain fallback is the minimum of the 1 m conformed terrain and the 4 m
   `terrain_lod2` grid the importer cooks as `col_terrain` (same min-filter and triangle diagonal as
   `terrain_mesh.chunks`), so a lamp on a verge never stands above the collider the audit (and the wheels) see.
6. **Junction fill**: patches whose Delaunay fill fails (narrow forks) use a constrained Delaunay of the outline
   (`meshing._cdt_fill`, no Steiner points: seam with the ribbons unchanged) before the ear-clip fallback.

## Evidence (editor, Unity 6000.3.28f1, Low tier = A16 tier, 2340x1080 downscaled to 1024; phone UNVERIFIED)
Dirs: `artifacts/world-fixes/streetscape-r6/{before,final}/sm/<tier_light>/` (+ `metrics.txt`; estimator: paint pixels =
asphalt grey + 40, saturation < 0.18, region 250-700 x 300-473 - on the old A16 frames it reproduces the review's 242-246).
| | before | after (dirt 0.43) |
|---|---|---|
| paint median, Low clear, s1382 / s1582 | 226 / 223 | 169 / 181 |
| paint median, Low overcast, s1382 / s1582 | 236 / 233 | 175 / 186 |
| paint median, High clear, s1582 | - | 200 |
| `photo_biezenstwa_ground` p10, Low clear (overcast) | 28.7 % (43.9) | 22.4 % (36.4) |
| terrain walls > 0.15 m (ratchet) | 14 (1 junction) | 13 (0 junction) |
| gate3-evidence `objects_vs_terrain` | FAIL (3 lamps 0.301-0.305 m) | PASS |
| dock scrub shapes (207 doors) | 1 | none 48, arc ~60, jog ~31, skew ~26, hook ~20, far arc ~15 |
The dirt film was tuned 0.30 -> 0.42 -> 0.36 -> 0.39 -> 0.43 on these frames (0.39 gave overcast s1582 191).
Independent `visual-critic` pass on the first iteration: numbers PASS, look FAIL (beige paint, soft "ghost" wear,
slab-like hedges, black shrub domes); fixed after it: neutral film tint, threshold (chipped) wear, clipped hedge profile
with steep sides and a pink-bordeaux tint, more and lower shrubs. Not re-reviewed.
`gate3-evidence` albedo_histogram / texel_density FAIL lists are mostly car / glass materials of other branches;
from this change `M_noise_glass` (the audit reads `_BaseColor` 255 of the car-glass shader, same as `M_car_glass_tint`)
and `M_marking_white` texel density 2062 /m (the audit uses the strip UV0, the paint samples world-planar asphalt at
the road's 1025 /m).

## Consequences
- Markings: +1 texture fetch (Var) per paint pixel, all tiers; same draw count (one marking material).
- Hedges / beds: a few hundred triangles in the furniture / paved layers of one chunk.
- Open: phone confirmation of paint medians (editor read ~20 levels darker than the old A16 build at clear);
  hedge heights / species and the splitter island surface to confirm at the owner's photo session; tyre scrub decals
  (`decal_tyre`) render on High but not in the Low WorldC frame (pre-existing, cause not found); paint/asphalt
  contrast ~1.5 (critic asks >= 1.8, i.e. darker asphalt - not touched here); concrete fence (`concrete_fence`, OSM
  barrier=wall) got the missing `concrete_fence_panel` set but stays plain.

## Addendum 2026-11-10 - hedges read as plants, not boxes
Context: the 0.6-0.8 m berberis masses of Decision 2 read as solid boxes ("bryły") in WorldC: one closed smooth mesh,
straight silhouette, flat top, uniform side, nothing at the foot. Reference: CC0 Commons photo 20201102_152339 (Rakoon),
clipped red berberis cushions on the lawns of Rondo Pamięci Bieżeństwa. No Google sources.

Decision (generator only, `streetscape.plantings` + new `streetscape.hedge_textures`; no Unity code change, the
importer's existing `texture` + `alpha_cutoff` path = URP Lit alpha clip, double sided, coverage-preserving mips):
1. Hedge = **dark opaque core** (`hedge_<sp>`, hedge_foliage set, albedo ~0.4 x leaf, half the perimeter vertices, 1.3 x
   5 cm inside the shell) + **alpha leaf shell** 5 cm outside it (`hedge_shell_<sp>`, 0.6 m tile of drawn leaves at
   true size, berberis coverage 0.73, gaps show the core = depth; shell open below 14 % of the height so the foot
   reads dark / woody) + **loose-shoot alpha cards** (`hedge_sprig_<sp>`, 2 x 2 atlas of leafy tufts under a ragged
   top outline, cell 0.3 m) on the top edge (every ~0.17 m for berberis), the upper sides (35 %) and the crown
   (~1.4 /m2), rooted 25 % inside the shell, leaning out, random yaw: ragged top and end silhouettes.
2. **One plant every 0.55-0.85 m** along the perimeter: outward lump (0.08 m) and crown height (dome 0.2 h); 7 % thin /
   missing plants become dips; lumpy 2-D crown on the top fill (0.6 m). Cross-section per species: berberis
   `cushion` (barrel sides, rounded 0.4 m shoulder, like the photo), privet / hornbeam / thuja `box`.
3. **Species table** (`SPECIES`: berberis_red, privet, hornbeam, thuja; heights 0.6-0.8 / 1.2-1.7 / 1.4-2.0 /
   1.6-2.2 m, WORKING_VALUE) chosen per bed (`plant` in the override) or per OSM way; per-hedge hashed height, UV
   offset and rotation, so no two neighbouring beds repeat.
4. **OSM `barrier=hedge`** (`osm_hedges`, none in tile C): hedge along the way, cut at the road footprint, opened at
   every gate / entrance node within 1 m (tag `width`, else 1.2 m wicket, 4 m sliding / vehicle gate), square
   softened ends at the gate posts; species from species/genus tags, needleleaved -> thuja, default privet.
5. Textures are our own drawings (leaves from primitives), `docs/LICENSES.md` `world-misc-textures`.

Numbers (WorldC editor, 1600 x 740; stats.txt draw/tri estimates before SRP batching):

| | before (r6) | after |
|---|---|---|
| hedge tris, 4 beds (flat ground, same polygons) | 5 678 | 16 929 (core 4 711, shell 9 408, shoots 2 810) |
| hedge + 25 island shrubs, whole region | ~9 200 | 27 645 (one chunk) |
| `hedge_a_close` Low: draws / shadow draws / tris | 197 / 73 / 257 k | 199 / 75 / 276 k |
| `hedge_a_close` High | 219 / 453 / 327 k | 221 / 459 / 346 k |
| `photo_biezenstwa_ground` Low draws / tris | 285 / 288 k | 287 / 306 k |
| `photo_biezenstwa_ground` p10, Low clear / overcast | 22.4 % / 36.5 % | 22.7 % / 36.5 % |
| hedge side mean sRGB, Low overcast (photo 64, 46, 37) | 40, 26, 26 | 68, 46, 43 |
| furniture mesh memory Low / High | 6.6 / 6.6 MB | 7.0 / 7.0 MB |
| new textures (8 PNG, 512 px) | - | 1.3 MB in art-source; 2 used in tile C |

Low budget (`docs/06` §6, 300-400 draws, 400-600 k tris) holds: +2 draws, +2 shadow draws, +19 k tris in the frames
that see the roundabout. Iterations: (1) shell pink and glossy, shoots invisible (twigs lost in the mips), slab
profile; (2) cushion profile, browner leaves, rough 0.97, dense leafy tufts; (3) core halved, colour tuned to the photo.
Evidence: `artifacts/world-fixes/hedges/` (before/, after/, sheets/before_after_*.jpg, sheets/reference_montage.jpg,
hedge_cameras.json = two extra close-up cameras via `visual-qa.ps1 -Gate3`).

Open: no phone measurement (alpha-clip overdraw on the A16 `UNVERIFIED`; furniture is in LOD0-1 on both tiers, a
Low-only shell / shoot cut-off needs an importer layer split - leader); shell gaps read as dark speckles at 10-20 m on
Low; the beds are wider than the photo's (traced from the orthophoto, heights / species still to confirm at the
owner's photo session); independent `visual-critic` review not done in this task (subagents not allowed here).
