# ADR 0071 - Hero depot hall: Kwadrat Park (player base) as an authored Blender asset

Status: proposed (2026-11-10) - asset, generator hook and importer done; visual-critic review pending

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
