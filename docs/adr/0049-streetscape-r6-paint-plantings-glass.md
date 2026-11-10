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

## Addendum r7 (2026-11-10): paint / asphalt contrast (review r6 W-H6, critic asks >= 1.8)

Measured first. The Low tier has no tone curve (plain sRGB clip), so the display ratio is the albedo ratio ^ (1/2.2)
plus a small additive specular term on the asphalt; the paint cap (Low clear <= 217, overcast <= 190 sRGB) and a 1.8
ratio together allow at most ~105 sRGB of asphalt in Low overcast. Before: asphalt ~121 (Low clear) - 128 (High
overcast), so the ratio could not reach 1.8 by changing the paint alone.

Decision (WORKING_VALUE, all in the generators, no shader change):
- **Aged AC albedo 0.13 -> 0.08**: `asphalt_worn` target (`_src/build_all.py`, `sets_asphalt.worn`) and the manifest
  colour of `road_asphalt` / `yard_asphalt` / `path_asphalt` (`build_world.py`, `streetscape/materials.py`) - they
  must stay equal: the importer tints a calibrated set by colour / set mean, and the `_DECAL_PAINT` base under worn
  marks samples the set untinted. Source: new asphalt concrete ~0.05, rising with ageing and soiling to ~0.15
  ('Cool Pavements' review, arXiv:2409.12242, p. 7; broadband solar albedo, not visible-band). 0.08 sits in the
  lower half of the aged range; 0.09 was tried and gave median 1.71-1.78 (`after2/`).
- **Paint film 0.60 / traffic film 0.43 -> 0.55 / 0.38**: mean effective albedo 0.55 x 0.62 = 0.34 (per-mark range
  ~0.28-0.41 by age, soiling and wheel paths), i.e. EN 1436 white in-service luminance factor class B2 (beta >= 0.30)
  to B3 (>= 0.40) (class limits as tabulated in a thermoplastic maker's EN 1436 data sheet; the standard text itself
  not read here, UNVERIFIED). Film 0.55 keeps the critic's 0.55-0.65 range; wear, chips, age and dirt variation unchanged.
- **Yard stall paint** (`marking_yard`, flat, no film): 0.46 -> 0.36 (was 220 sRGB in Low clear by estimate).
- Test `tests/gis/test_streetscape_r6.py::test_asphalt_albedo_matches_set_and_contrast` (colour = set mean +-3 %,
  target 0.07-0.12, nominal paint/asphalt >= 4) and the effective film 0.30-0.40 check.

Evidence (editor, Unity 6000.3.28f1, 2340x1080, WorldC; `artifacts/world-fixes/paint-contrast/{before,after1,after2,final}/<tier>_<light>/`
+ `metrics.json`, before/after sheets in `sheets/`). Estimator `scripts/paint-contrast.py`: paint = the
`-Mask ':marking_white'` pixels eroded 2 px in the lower 60 % of the frame, asphalt = a 4-14 px ring around them
(sat < 0.25), display luma Rec.709 on sRGB values; 5 cameras (g3a_eye_s0262, g3b_eye_s1382 / s1432 / s1582 where
present, g3b_rondo_putry_approach, photo_biezenstwa_ground). Ratio = median over frames; paint = max over frames of the
per-frame paint median; p99 = max channel, worst frame.

| tier / light | ratio before | ratio after | paint median before -> after | paint p99 max ch. before -> after | asphalt before -> after |
|---|---|---|---|---|---|
| Low clear | 1.46 | **1.75** | 195 -> **194** (<= 217) | 218 -> 218 | 121 -> 100 |
| Low overcast | 1.50 | **1.77** | 191 -> **191** (<= 190: at the cap) | 204 -> 202 | 122 -> 103 |
| Low lowsun | 1.47 | 1.80 | 100 -> 101 | 119 -> 118 | 65 -> 54 |
| Low dusk | 1.57 | 1.86 | 95 -> 95 | 119 -> 119 | 57 -> 49 |
| High clear | 1.51 | 1.78 | 221 -> 220 | 247 -> 247 | 125 -> 109 |
| High overcast | 1.54 | 1.77 | 213 -> 214 | 238 -> 235 | 128 -> 112 |
| High lowsun | 1.45 | 1.71 | 107 -> 108 | 128 -> 127 | 71 -> 61 |
| High dusk | 1.51 | 1.75 | 102 -> 102 | 125 -> 126 | 64 -> 56 |

Best single frames reach 1.86-1.99 (g3b_eye_s1582); `photo_biezenstwa_ground` stays ~1.05-1.1 (its P-10 zebra is
mostly worn through in the wheel paths and far away, so the masked pixels are largely asphalt).

Consequences / open:
- The median is 1.71-1.86, not >= 1.8 everywhere. At asphalt 0.08 the Low overcast paint cap (190) is the limit:
  more ratio needs darker asphalt than aged AC literature supports or a narrower per-mark dirt spread (the age
  variation lowers some frames' median). Left for the owner's photo session (measure real paint / asphalt in
  Bialystok at overcast) rather than tuned to the number.
- High tier: the tone curve (ADR 0016, white clip 0.7) lifts paint ~25 levels above Low; High clear p99 247 on
  `g3a_eye_s0262` / `photo_biezenstwa_ground` is close to clip (unchanged by this addendum, curve not touched).
- Darker asphalt makes the whole road frame darker (Low clear asphalt 0.47 -> 0.39 display) against the r5 photo
  match (0.48); phone A16 / S24+ confirmation UNVERIFIED (no phone frames in this change).
- Cost: none (same textures, same draws; asphalt_worn PNG bytes ~ -1.5 %).
- `world_manifest.json`: only the 5 material entries changed (a full `build_world.py` run gave the same material
  values; its GLB hashes and an unrelated +-2 road triangles were not committed). The lead's next world regeneration
  rewrites the hashes. `_renders/tiling_asphalt_worn.jpg` preview not re-rendered (Blender).
