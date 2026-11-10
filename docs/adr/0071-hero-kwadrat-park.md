# ADR 0071 - Hero depot hall: Kwadrat Park (player base) as an authored Blender asset

Status: proposed (2026-11-10) - asset, generator hook, importer, yard, automatic boom done and tested on WorldC; visual-critic review pending (leader)

## Context
The route starts in the yard of Kwadrat Park. The main hall (`bdot:9962cca0…`, 21 399 m², LoD1 2024 height 10.16 m) was
a generic rule-built hall (ADR 0012): silver sandwich box, dock row by rule, canopy. The yard is private: Mapillary,
KartaView and Panoramax have no frame inside it. Open references that do show the hall:

| Source | Licence | What it shows |
|---|---|---|
| GUGiK orthophoto 2024-05-27, 0.25 m (`Data/raw/derived/<id>/ortho_0p25m.tif`) | GUGiK open data | footprint, roof (bitumen, staggered grid of small roof lights, white membrane field behind the SE facade, lighter lower roof inside the inner ring), red roofs of two small SE protrusions, truck rigs standing **parallel** to the SE wall, paved forecourt with nose-in cars in front of the trade units |
| BDOT10k + LoD1 2024 | GUGiK open data / CC BY 4.0 | footprint ring (three protrusions on the SE side), height |
| `20210904_101250_September_2021_in_Białystok.jpg`, Rakoon, Wikimedia Commons | CC0 | south corner from the access road: light grey horizontally profiled sheet, dark coping, vermilion-framed strip of small-pane windows high on the SE facade, vermilion louvre panel on the SW facade at the corner, tall vermilion portal further along the SE facade, roof fans; trade units (grey, strip windows, asphalt forecourt) |
| `20241222_122132_December_2024_in_Białystok.jpg`, Rakoon, Wikimedia Commons | CC0 | SW facade from far: one long light facade with a continuous window band |

Photos are reference only (no pixels in the build). The directory `artifacts/refs/kwadrat-park/` named in the task did
not exist; the crops used are in `artifacts/kwadrat-r9/refs/`.

**The dock row is not visible in any open source** (facade base behind a hedge in the photo, in shadow on the
orthophoto). "11 bram" in `docs/owner/PHOTO-LIST.md` is the output of the old generator rule, not an observation; the
orthophoto neither confirms nor refutes it.

## Decision
1. **Override `kind: hero_depot`** (`Data/Regions/<id>/overrides.yaml`, entry `kwadrat-park-hero`) handled by
   `tools/worldgen/streetscape/hero_depot.py`, the same pattern as `hero_bridge` (ADR 0067):
   - `plan()` (before the buildings are meshed) writes the spec
     `Data/Regions/<id>/generated/landmarks/kwadrat_park.spec.json`: BDOT footprint with the authored protrusions split off
     as annexes, LoD1 height, smoothed ground every 4 m along every facade, authored facade features (keyed by a point
     near the facade midpoint, stations `u_m` along the facade), roof layout, segment cuts (<= 46 m, never through an
     opening). It compares the spec sha256 with `art-source/world/landmarks/kwadrat_park/kwadrat_park_meta.json`; a
     stale asset is rebuilt with Blender when `KAMION_BLENDER` / `blender` is available, otherwise the hall keeps its
     generic geometry and the override is listed in `overrides_stale` and streetscape QA `hero_depots.stale`.
   - `buildings_mesh.build(heroes=…)` takes the dock rows of the hero building from the spec in the dict shape of
     `docks_for()` (aprons, parked trailers, tyre scrub, yard props, dock zones keep working) and drops the building's
     `buildings` / `buildings_low` geometry when the asset is ready. **The collision prism of the footprint stays.**
   - `apply()` adds one instance per segment (`landmark_depot_kwadrat_park_NN`, 16 facade segments + `_roof`, yaw 0,
     anchor = segment centre at the reference ground) and one collision block per dock for the two rubber bumpers
     (0.12 m proud, 0.55 m high under the dock floor), so a trailer stops at the bumpers.
2. **Asset generator** `tools/blender/world/landmarks/make_depot.py` (headless, deterministic, spec in -> GLB + meta out;
   `--render <dir>` writes control renders from fixed cameras incl. the station of the CC0 photo and a north-up top
   view). LOD0 / LOD1 / LOD2 per segment; glTF axes (-dE, dU, dN) like `street_props.glb`; materials are **world
   material names** (`streetscape/materials.py`), UV0 in metres, so the engine binds the region PBR sets (and the CC0
   scan sets of ADR 0063 when that lands) - the asset carries no textures of its own.
3. **Docks do not move.** 11 docks, first door 7.815 m from the south corner, pitch 4.0 m, door 3.0 x 3.0 m, dock floor
   1.20 m above the yard (`roads.standards`), exactly the positions of the previous rule
   (`centre_on_len_m: 55.63` = the first SE footprint edge). No gameplay scene or test refers to WorldC docks
   (`DrivingLabLayout` docks are the lab scene); route, spawn and yard are unchanged. Measured: the yard along the
   dock row is level within 0.12 m.
4. **Engine**: `InstanceImporter` loads prototypes also from `art-source/world/landmarks/**/*.glb` (identical code to
   ADR 0067, so the two branches merge without conflict in substance) and gives `landmark_depot*` the LOD ends
   100 / 400 / 20000 m (x lodBias: High 150 / 600 m, Low 50 / 200 m; never culled) with LOD0 + LOD1 casting shadows.
   `build_world.instance_ends` mirrors it (`tests/gis/test_hero_depot.py::test_instance_policy_in_sync`).
5. **Yard corrections from the orthophoto / photo** (separate overrides): `kwadrat-park-units-forecourt`
   (`paved_area`, asphalt + parking in front of the trade units, where BDOT has no paved polygon and the generator
   laid grass) and `kwadrat-park-trade-units` (grey wall for `bdot:7abd670e`).

## What is seen and what is assumed
| Element | Status |
|---|---|
| Footprint, height, annex footprints (6.1 x 2.6, 12.1 x 3.7, 6.1 x 2.6 m) | data (BDOT10k, LoD1): high |
| Light grey horizontal sheet (`kp_wall`), dark coping, vermilion frames (`kp_accent`), strip of small-pane windows on SE from the corner, louvre panel on SW at the corner, tall portal on SE, roof fans | CC0 photo 2021: medium (colour values by eye, WORKING_VALUE) |
| Strip sill 6.6 m / height 2.0 m / frame 0.22 m, coping 0.30 m, portal 12.6 m | WORKING_VALUE: proportions of the photo crop against the 10.2 m LoD1 height; camera station solved from the louvre scale (~95 m south of the corner) |
| Roof: bitumen, roof lights 1.2 m at 6 x 6 m staggered, white field, lower light roof in the inner ring (+5.0 m) | orthophoto: medium; sizes WORKING_VALUE |
| Red roofs of annexes 1 and 3 | orthophoto: medium; annex heights 3.4 / 4.6 m WORKING_VALUE |
| **11 docks, shelters, levellers, bumpers, wheel guides, numbering, signal and flood lights, stair door** | **WORKING_VALUE** (typical Polish logistics hall, `roads.standards`), not visible in any source |
| Doors, drive-in doors, downpipes, wall lights, office window rows on SW, everything on NW; NE = party wall | WORKING_VALUE |
| Gate, boom barriers, gatehouse, fence (`kwadrat-park-gate-kit`, unchanged) | WORKING_VALUE; the 2021 CC0 photo shows an open access road without a visible gate at its station - to be verified |

## Numbers
- Asset: 17 prototypes, LOD0 / LOD1 / LOD2 = 13 648 / 2 034 / 652 triangles for the whole hall (budget in the test:
  60 000 / 6 000 / 1 200), 30 materials, all existing world materials + 4 new (`kp_wall`, `kp_accent`,
  `kp_glass_block`, `kp_roof_white`); GLB 1.3 MB.
- Frame estimate `kwadrat_park_gate` and the Unity control renders: see `artifacts/kwadrat-r9/STATUS.md` (measured
  after each build; not repeated here to avoid stale numbers).

## Consequences
- The hall no longer changes with the hashed style pick; changing a facade means editing the override and rebuilding
  the asset (automatic in `build_world` when Blender is found, otherwise the generic hall comes back and QA says so).
- Instanced prototypes have no parapet run-off UV1 and no baked sky visibility of the chunk meshes (ADR 0064); wear
  comes from the shared PBR sets and from geometry (one open and one half-open door, a dock without wheel guides,
  lost bumpers, sagging shelter curtains, shifted number plates - hashed, stable between builds).
- Owner photo session items 1, 3, 6, 7, 9 decide the dock count / type, the door layout and the gate; each is one
  line in the override.

## Rejected
- Moving / re-counting docks from the orthophoto: the source does not show them; moving them would change the start
  yard for a guess.
- An own texture atlas for the hall (as the viaduct): the hall is 600 m of facade; tiling world sets in metres give
  the texel density of the rest of the world and inherit the CC0 scans of ADR 0063.
- Canopy over the dock row (old hero flag): not visible under the strip windows in the CC0 photo.

## r10 (2026-11-10): yard life, gate, automatic barrier
1. **Trailers at the hero docks.** They never stood there: `life.START_CLEAR_*` (r5 interim rule: no parked truck
   prototype within 120 m of the route start / 45 m of its first 250 m) covers the whole yard. The hero dock row is
   exempt (`dock_trailers`: `sp.free` instead of `sp.vehicle_free`); yard rows and rigs keep the rule.
2. **Cars in the truck yard.** BDOT10k `OT_KUKO_A rodzaj=parking` (8 328 m2) spans the whole manoeuvring yard, so the
   parking rule laid two rows of cars across it. New override `kind: depot_yard` (`streetscape/depot_yard.py`, entry
   `kwadrat-park-yard`): `no_parking_epsg2180` (cut out of the parking regions), `clear_lamps_epsg2180` + `lamps`
   (columns at the pole feet read off the orthophoto shadows, west edge of the lane; prototype `lamp_arc_9m`, the
   arched single-arm column of the CC0 photo), `props` (two dark 40 ft containers of the orthophoto).
3. **Gate.** The CC0 photo 20210904_101250 looks along the access road into the depot: no gate leaf and no fence
   across the forecourt; the orthophoto agrees. `depot_gate` got the additive flags `sliding_gate` / `fence`
   (default true); the Kwadrat kit sets both false. Gatehouse and booms stay (WORKING_VALUE, start anchor).
4. **Automatic boom (map audit MA-003, owner report: the boom did not open and had no collision).** The kit places
   `barrier_base` (housing, rest post) and `barrier_boom` (hinge frame, instance key `barrier: {L, open_deg, lane,
   travel}`). The importer turns every such boom into a GameObject with `Game.World.DepotBarrier`
   (`InstanceImporter.Barrier`, `WorldSceneBuilder.BuildBarriers`; layer Ignore Raycast so wheel rays never stand on
   it): presence loop 25 m before / 6 m behind the boom (any non-kinematic rigidbody, so the trailer keeps it open),
   opening 3.5 s / closing 4.0 s after 1.5 s free (WORKING_VALUE; drives of 6 m booms: 3-6 s), kinematic boom =
   solid when closed or moving, break-away above 1.5 m/s closing speed: the boom is released as a 14 kg dynamic body
   one step before the contact, so the engine solves a truck-vs-light-boom impact instead of an immovable wall.
   No allocation after Awake (`OverlapBoxNonAlloc`, fixed buffer). PlayMode `DepotBarrierTests` (3): approach ->
   open (3.46 s) -> combination passes -> closed; closed boom stops 1.5 t at 1 m/s; 7.5 t at 6 m/s breaks the boom
   and keeps 5.99 m/s.
   Open: the released boom is a free body (no bent hinge / shear-pin joint); a straight loop box can see a vehicle
   on the neighbouring lane behind the island nose; the OSM `lift_gate` props elsewhere are still static.

## r10b (2026-11-10): verification on the world scene
- **Boom on WorldC.** `WorldCBarrierTests` (PlayMode, imported scene, 40 t combination on the start route with the
  path follower): both imported booms are closed and solid (a ray along the lane hits the boom collider, boom
  0.7-1.3 m over the road); the boom on the route lane (s = 247.4 m) starts opening with the tractor at s = 216.5 m,
  is fully open after 3.49 s (85 deg with the tractor origin 8 m before it at 20.0 km/h), is never touched, closes
  with the combination at s = 308.4 m; the other lane's boom does not move; max |dv| per 10 ms step 0.050 m/s; the
  loop query returns at most 11 colliders (buffer 128).
- **Script-mode stepping.** The first run of that test failed (boom still closed, |dv| 6.06 m/s): tests that step
  `Physics.Simulate` themselves do not run the boom's FixedUpdate per step. `DepotBarrier.Tick(dt)` is now public and
  FixedUpdate only calls it in `SimulationMode.FixedUpdate` (same contract as `VehicleBody`); `WorldCRouteTests` and
  `WorldCBarrierTests` step every boom. In the game (FixedUpdate mode) nothing changes.
- **Boom bands.** `Mesh.tube` maps the length to v, the `boom_red_white` stripes follow u: one boom rendered all
  red, the other all white. `life_props._boom_tube` writes u = metres along the boom (`test_boom_bands_run_along_the_boom`).
- **Still WORKING_VALUE / open.** Gatehouse, housings and boom positions on the exit lane: no open photo of the gate
  exists (`artifacts/refs/kwadrat-park/INDEX.md`, ADR 0066: gap), the orthophoto shows one thin line across the entry
  lane only. A hit that is not predicted by the loop sensor (kinematic boom, first contact) still stops the vehicle
  for one step before the boom is released; the sensor path covers bodies with convex / primitive colliders.

## r11 (2026-11-10): fixes after the visual-critic review (`docs/reports/visual/REVIEW-2026-11-10-0071-0080.md`, part A)

Verdict of the review: FAIL (quality) - "plac wygląda jak gra mobilna z okolic 2016 r.". What changed, by finding:

1. **A1 (P0) block size - the cause is global, not this ADR.** `WorldPbrMaterials.Create` never wrote `_Tile` (noted
   in ADR 0067), so every texture set is sampled every 4 m whatever its `tile_m`. The CC0 scan set `behaton_i_grey`
   (ADR 0063) is 1.92 x 1.92 m of real paving with 106 segmented blocks (`materials_spec.json`,
   `source.elements_per_tile`) = 0.0348 m2 per block (a 200 x 165 mm block: 0.033 m2); stretched to 4 m every block is
   4 / 1.92 = 2.08x too large: 0.20 m -> 0.42 m, which is what the reviewer measured in the frame (0.4-0.5 m). The
   renders of ADR 0080 showed small blocks because that worktree (and the PNGs on disk in the main checkout, dated
   before the scan fetch) still held the old PROCEDURAL set (20 blocks across a 4 m tile), i.e. textures that did not
   match the spec in git. Fix at the source: sets segmented into physical elements (`source.elements_per_tile`:
   behaton, 20 x 10 paving, 35 cm slabs) always get their real tile (`_Tile` = `tile_m`); the element size is a scale
   cue. Effect on other surfaces: footways (`paving_20x10_grey`, 3.1 m scan) were 4 / 3.1 = 1.29x too large and are
   now right. **Not changed, still open for the lead (ADR 0067 "znane")**: every other set is still sampled at 4 m
   although its `tile_m` differs (`concrete_cast_5m_joints` 10 m: the "5 m" slabs render 2 m; `kerb_concrete_1m`
   2 x 0.5 m; `sandwich_ribbed` 6 m; `box_panel` / `curtain_folds` 4.8 x 2.7 m; `brick` 1.4 m; `plaster` 2 m) - these
   looks were reviewed at 4 m and belong to other agents' scopes (buildings, roads, light).
2. **A2 (P0) sterile yard.** New block `wear` of the `depot_yard` override (`streetscape/yard_wear.py`), authored in the
   frame of the dock wall (u along the wall, o out of it), deterministic (hashed), decals on the markings layer:
   driving lines of articulated trucks (`decal_tyre` bands, 2 wheel paths x passes), relaid paving and a cable trench
   (`decal_yard_patch_light / _dark`: the yard's own block set in another tone, world-planar so the bond runs through),
   oil and grease where tractors stand coupled and under the axles (`decal_oil`, 2-5 per dock), soil washed against
   every edge of the paved yard that is not a flush road edge and along authored lines (`decal_grime`, a soft
   noise-broken band: manifest `band: true`, drawn with the `_DECAL_TYRE` path of Kamion/World PBR). SEEN on the GUGiK
   orthophoto 2024-05-27: the dark soil line from the lane edge toward the containers and the lighter rectangle in the
   middle of the yard; everything else is WORKING_VALUE (typical logistics yard; no open ground photo exists). The
   dock apron of the hero hall is `yard_concrete_worn` (darker, soiled cast concrete with the 16 m crack layer;
   manifest `cracks`).
3. **A3 (P0) hall facade without streaks / AO.** `kp_wall` carries manifest `weather: true`: the importer gives it
   the splash zone of the generated halls (`_SPLASH`, UV0.y = metres above the facade ground) and the parapet run-off
   layer (`_RUNOFF`); `make_depot.py` writes TEXCOORD_1 on every cladding face = (u in the 24 m period, 1 + metres
   below the edge that sheds water above it: the coping, or the sill of the strip windows / louvres above), and
   `InstanceImporter` keeps TEXCOORD_1 on prototype meshes whose material reads it (before: never, which is why ADR
   0071 said "instanced prototypes have no parapet run-off"). Macro tone drift 0.06 -> 0.12 on this wall; albedo
   0.62 -> 0.56 (WORKING_VALUE, see A7). Spec key `weathering` forces the asset rebuild.
4. **A4 (P1) box trailers.** `life_props.trailer`: slim telescopic landing gear (110 mm leg, 90 mm inner leg, sand
   shoe, braces, cross shaft, crank), mudguards and a mud flap over the axle group, amber side markers, pallet box,
   spare wheel, front bulkhead detail (document box, reflectors, hose bracket, hanging hoses), road film on the lower
   third of the body (`car_dirt` overlay, LOD0 + LOD1). The trailers of the hero dock row are authored
   (`depot_yard.dock_trailers`): 8 trailers on 11 docks, 7 different kinds / colours, each up to 1.2 deg off square,
   +-0.12 m sideways, 0-0.30 m off the bumpers.
5. **A5 (P1) contact shadows.** The analytic contact patch of ADR 0050 now also covers the landing gear of trailers
   (4th contact core) and the static yard props that had none: ISO containers, the gatehouse, the barrier cabinets.
6. **A6 (P1) barrier without an island.** `gate.py`: a raised kerbed island (precast kerb ring 0.15 m, +0.16 m,
   block-paved top, hard collider) fills the median between the two lanes from 2.5 m before to 3.5 m after the housing
   line; both cabinets stand on it, the rest posts across the lanes are founded at lane level; yellow steel bollards at
   both noses; saw-cut induction loops with a feeder cut (bitumen sealant decal) before and after each boom.
   WORKING_VALUE (no open photo of the gate).
7. **A7 (P1) palette.** Apron darker (0.30 -> 0.215), wall 0.62 -> 0.56, trailers in 7 kinds / colours, soil bands
   and tyre lines break the single grey. Lighting / exposure were not touched (agent "light r11" owns them).

Not done (open): A8 (tower block facade, lamp head lit by day), a sign / board at the gate (no source), phone
screenshots (`docs/06` §5.2; the leader's device queue), trailers still stand in a perfectly regular 4 m pitch
(the dock pitch).
