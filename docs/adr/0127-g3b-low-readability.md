# ADR 0127 — G3-B legibility on Low: lattice portal at distance, HV tower, noise screens

Status: implemented on branch `g3b-lowread` (base main `31e54e00`, 2026-11-12); not merged. Gate 3 is NOT re-judged
here (visual-critic).
Source: `docs/reports/visual/REVIEW-2026-11-12-s11-0125.md` — P1 "bramownica z daleka (LOD)", P1 "czytelność słupa WN
i ekranów", P2 "tablice wiszą pod górnym pasem"; open blockers 5 and 6 of gate 3 (D51). Starting point: ADR 0125.

## Findings (measured before anything was changed)

| Review item | What the code / data says | Cause |
|---|---|---|
| Portal reads as a closed grey frame at 40-120 m | `sign_gantry_*` fell under the generic `sign_` LOD policy `[50, 250]` m. Low has lodBias 0.5, so the lattice (LOD0) ended at **25 m** and the whole portal and its boards were **culled at 125 m**. LOD1 was two solid boxes (columns 0.6 x 0.6 m, beam 0.8 x 1.0 m). `gantry_steel` was metal 0.9: it mirrored the overcast dome and had the sky's own luminance. | LOD policy + LOD1 mesh + material |
| Boards hang under the top chord | `landmarks.build`: board top = beam top - 0.15 m. Mapillary 275528677534382 (front) and 3281350541967811 (back): the faces cover the beam and their tops stand above the top chord. | layout rule |
| Board backs with white dots | `props.board` used a 15 % patch of the `plate_back` texture (rivet dots) stretched over a 5-8 m board. | material |
| HV tower thin, bright, no silhouette | `props.pylon`: one mesh for both LODs, legs r = 0.06-0.08 m, lacing r = 0.025-0.03 m, base 6.4 m wide, two arms; `steel_galv_dark` metal 0.9. At ~200 m a pixel of the 1280 px frame is ~0.2 m: the lacing is 0.25 px wide and as bright as the sky. The photo (3678296072299092) shows a slender double-circuit tower with **three** arm levels, black against the sky. The conductors (3, at 23 m, +-5 m) met no arm. | mesh + material |
| Screen posts thin, sheet makes no plane | Deck screens: 0.14 m posts every 3 m; ground barriers: 0.16 m posts. `noise_glass` runs the parked-car glass model: reflected rays below ~15 deg elevation get the diffuse ground radiance ("clutter" between parked cars), so a screen seen along the road - where the Fresnel term is highest - mirrored a dark floor instead of the horizon sky. | post size + reflection model |
| 1801374: screen 20-40 m ahead instead of beside the camera | GUGiK orthophoto 2024 + BDOT10k OT_OIKM_L + OSM (`artifacts/g3b-lowread/crops/ortho-1801374.jpg`): two barriers on the right - the set-back one along the house plots starts at local N = 70 (15 m right of the camera, which stands at N = 70.7) and the kerb-side one at N = 93. Both are generated where the orthophoto has them. With the 58.7 deg frame the set-back barrier only enters the view ~27 m ahead; the photo is far wider than that. **World position correct; camera FOV / pose (SBS stream).** The set-back barrier was however `solid` south of N ~ 90, the photo has it glazed from its corner. | pose / FOV + style zone |

| Review s12-0130: "portal ~27 % too low, 7.4 m vs 8.5-9 m (UNVERIFIED)" | GUGiK hi-res orthophoto (WMS ORTO HighResolution, `crops/ortho-gantry-hr.jpg`): the beam is **14.0 m** long (350 px at 0.04 m), the feet ~0.5 m behind the kerbs; the rule gave 16 m. Column shadow 6.1 m. Frontal photo 275528677534382: (beam top above the horizon) / (column spacing) = 0.354 -> 5.0 m + eye ~1.3 m = **6.2-6.5 m** for a 14 m span; board bottoms ~5.5 m. So H / span was right (0.44-0.46) and the portal was 14 % too **wide**, not too low: a pose resected from the legs of a 16 m portal stands 14 % too far and sees it lower. 8.5-9 m is not supported by either source. | span (fixed); height kept by rule (7.0 m, boards are ~0.6 m taller than the real ones) |
| Review s12-0130: "1801374: fence of posts instead of a tall panel screen" | The generic barrier is 4.0 m with a 1.8 m band; the photo read against its 0.6 m plinth: band ~1.6 m, glazing ~3.1 m -> ~5.2 m. | height + style zone |

## Decision

1. **Portal / cantilever LOD1 = lattice** (`life_props.sign_gantry`, `sign_cantilever`): the same chords and zig-zag
   lacing as LOD0 with 3-sided members a third thicker (chord r 0.06 -> 0.08 m, lacing 0.03 -> 0.045 m), column lacing
   only on the two faces across the road. LOD0 column lacing is now a closed zig-zag (was every second diagonal).
2. **LOD policy** (`InstanceImporter.Policy` + mirror `build_world.instance_ends`): `sign_gantry_*`,
   `sign_cantilever_*` `[100, 800]` m, overhead boards `board_OB_*` `[50, 800]` m. Low: lattice LOD0 to 50 m, LOD1 and
   boards to 400 m. Other signs unchanged.
3. **`gantry_steel`** 0.42 / metal 0.9 -> 0.25 / metal 0.3, rough 0.7 (weathered zinc; darker than the overcast sky).
4. **Boards stand on the portal beam**: tops `BOARD_ABOVE_BEAM_M` = 0.25 m above the top chord; the tallest board
   keeps the 5.2 m clearance, so the portal is 0.4 m lower than before. Cantilevers keep the hung layout (ADR 0069).
   Overhead board backs: new plain material `board_back` (same draw count as before).
5. **HV tower** (`props.pylon`): 32 m double-circuit lattice tower, shaft 4.6 m at the foot (orthophoto: ~5 m) ->
   1.5 m under the lowest arm, three arm levels at 20 / 24 / 28 m, tips 3.3 m from the axis, peak, insulator strings.
   LOD1 (from 40 m on Low) keeps the silhouette with members ~1.6 x thicker and coarser panels. New material
   `pylon_steel` (0.12, metal 0.2). Conductors (`furniture.power_lines`): six phase wires under the arm tips + the earth
   wire on the peak (were three wires in one plane).
6. **Noise screens**: deck screens - posts 0.22 m every 2.0 m (Mapillary 494288258686575), sheet material
   `noise_glass_lined`; ground barriers - posts 0.22 m. `Kamion/World Car Glass` gets the keyword `_SCREEN_SHEET`
   (materials with `"screen": {...}` in the manifest): horizon sky in near-horizontal reflections (`_HorizonSky`), a
   uniform matt film of aged PMMA (`_Haze`) and printed horizontal lines along UV0 v (`_Stripe`, deck screens only,
   replaced by their mean coverage when a period is under ~2 px). Alpha stays 0.10 (review: reflection, not opacity).
   Car panes compile without the keyword: unchanged.
7. **Style zones**: the set-back barrier east of al. Tysiąclecia is glazed from its south corner (new zone in
   `andersa-ne-noise-barrier-glazed`); zones may carry `height_m` - the two zones at camera 1801374 are 5.2 m with
   the band top at 2.2 m (WORKING_VALUE).
8. **Portal span**: `sign_gantry` override key `columns_en` (column feet, region-local E,N, from the orthophoto);
   `andersa-putry-approach-gantry` is 14 m wide (was 16 m by rule). Height stays by rule.

All sizes are WORKING_VALUE read off the cited Mapillary frames (CC BY-SA, reference only) against lane width / kerb;
no manufacturer drawings in the repo.

## Changes outside this stream's usual files (minimal)

- `game/Assets/_Project/World/Import/InstanceImporter.cs`: two policy lines. `RegionImporter.cs`: `CarGlassMaterial`
  reads the optional `screen` block.
- `streetscape/materials.py`: `pylon_steel`, `board_back`, `noise_glass_lined`, `screen` block on `noise_glass`,
  `gantry_steel` values. `streetscape/furniture.py`: HV conductor attachment, post width.

## Not done / open

- SBS camera poses and FOV (1801374, 494288, 275528, 837235, 3281350, 297817): SBS stream.
- HV tower arms vs the photo: BDOT10k / OSM run the 110 kV line NE-SW through the tower (-181,79 -> -369,-69 ->
  -575,-214), i.e. across Andersa, so the arms (across the line) point almost at camera 3678296 (8 deg off) and are
  seen end-on; the photo shows them broadside. Either the real tower is an angle / branch type or the pose differs:
  UNVERIFIED, geometry follows the data.
- Tower height and arm dimensions are WORKING_VALUE (BDOT10k has no height); insulators stay the generic grey.
- The deck screen has no hand rail in front of it (photo 494288 shows a tube railing on the kerb side): ADR 0110
  removed it on purpose (three rail systems side by side); not reopened here.
- Phone numbers (A16) for the changed frames: next gate measurement.

## Results

Final cycle after `git merge main` (bedc52d12), build 3 + import + render, 2026-11-12. Evidence in
`artifacts/g3b-lowread/`: `pairs-final/` (Low overcast), `pairs-final-clear/` (Low clear), `stats-diff-final.txt`,
`pytest-gis.log`, `editmode.log`, `STATUS.md`.

- Tests: pytest `tests/gis tests/gate3` 832 passed, 1 xfailed; EditMode 402 / 402; fidelity exit 0.
  `test_street_r9::test_cantilever_prototype_reach_and_mirror` budget changed from "LOD1 = two boxes (<= 24 tris)" to
  "<= 300 tris" (the cantilever LOD1 lattice has 240).
- Cost on Low, editor estimate, 20 G3-B photo-pose cameras, before = main before this ADR
  (`artifacts/sbs-poses/final`), so the delta also contains what main merged in between: total draws (static +
  instanced) min / median / max **-17 / -1 / +11**; static triangles -6k .. +6k, instanced 0 .. +4k per frame.
  No phone measurement in this stream (A16 GPU budget already FAIL): the change is cost-neutral in the editor
  estimate, to be confirmed at the next gate run.
- D51 ("would a driver recognise the place?"), frames viewed in both lightings: 275528 / 837235 / 381800 / 297817 -
  the Andersa portal reads as a lattice frame with boards on the beam from the far frames on, proportions close to
  the photo after the 14 m span; 3678296 - the HV tower is a dark three-arm silhouette with conductors (arm
  orientation open, see above); 494288 - the viaduct screen reads as a light lined sheet between heavy dark posts;
  1801374 - a tall glazed screen on a dark band instead of the post fence. Remaining differences are pose / FOV
  (SBS stream) and the daylight boards being brighter than the dusk photos.
