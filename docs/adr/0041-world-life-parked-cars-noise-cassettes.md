# ADR 0041: World life: parked cars from every car park, third prop LOD, noise-barrier cassettes

- Status: accepted (world-builder, 2026-11-10)
- Context: REVIEW-2026-11-10-r5 W-H3+ ("zero life": no parked cars in street frames) and W-N2 (noise barriers are
  flat mint slabs).

## Findings
- `life.parking` filled only paved items flagged `parking`. `paved.collect` gives BDOT10k OT_PTPL_A yards priority
  over OSM car parks without a `surface` tag, so the yard polygon swallowed the car park and its flag: 25 of 42 OSM
  `amenity=parking` areas in tile C had 0 cars, among them two lots 20 m and 71 m from gate 3 cameras.
- The 16 OSM `parking=street_side` strips are 4.1-5.0 m wide. The 16 m two-row module never fits them.
- Cars used the default prop policy (30 / 120 m at lodBias 1), so on Low (0.5) every car was culled beyond 60 m.
- The manifest pointed `noise_panel` at texture set `noise_cassette`, but that set did not exist. The importer
  therefore fell back to the flat colour.

## Decision
1. Bays are laid in every paved item that is a car park or overlaps the union of OSM `amenity=parking` and BDOT
   `OT_KUKO_A rodzaj=parking`. Dock aprons are excluded. Strips with a short side under 7 m get one row: parallel
   bays at 6.0 m pitch if narrower than 3.6 m, otherwise perpendicular bays at 2.5 m. In strips the nose or tail
   may overhang the kerb line by 0.45 m. Occupancy is `OCCUPANCY = 0.72` (WORKING_VALUE). The 5 m route corridor,
   road, building and taken-space tests are unchanged.
2. Props may carry an optional `<proto>.lod2` node (export.py, InstanceImporter). Cars and vans get a roughly
   40-triangle prism LOD2. Their policy is 25 / 90 / 400 m at lodBias 1, which gives 12 / 45 / 200 m on Low.
3. Two generated modulation sets (sets_facade.py):
   - `noise_cassette`: 4.0 x 0.5 m absorbing cassettes, joint lips, perforation grain, per-element tone, spray
     grime up to about 0.9 m, run-off below the joints. It sits on the existing 0.5 m concrete plinth and the
     HEB posts every 4 m.
   - `car_grime`: road film on sills and bumpers, dust on top, rain runs. Paint UV = (y, z) in metres. LOD0 also
     gets a dark sill strip.
4. Every bus shelter gets a litter bin next to it.
5. `noise_panel` colour is 0.30 / 0.33 / 0.31 with metal 0.1. At 0.17 and metal 0.3 the cassettes rendered near-black on Low overcast.

6. Car bodies remodelled (2026-11-10, `streetscape/life_cars.py`; replaces the box lofts that read as "a roof wedge
   on wheel boxes" at LOD1). A body is a named side profile (bumper, tail, rear glass, roof, windscreen, hood, nose)
   with a half width per point (plan taper, greenhouse tumblehome), swept across x; the sides are the profile
   polygon. Mix (WORKING_VALUE shares in `life.BODY_SHARE`): hatch 4.06 m, sedan 4.62 m, estate 4.68 m, small SUV
   4.36 m, car-derived light van 4.50 m (replaces the 5.4 m panel van). All dimensions are class-typical
   WORKING_VALUE (B/C/D segment, B/C-SUV, light van), no make or model is reproduced, no badges or grille
   signatures; plates are blank (`car_plate`, the placeholder-string plate texture is no longer used on cars).
   Palette cut to silver, grey, black, white, dark blue, red (24 car + 3 van prototypes, as before).
   - LOD0 434-514 tris (budget 600): chamfered shoulders (body-coloured pillars), wheel-arch cut-outs with liners,
     recessed wheels, framed side windows split at the B pillar, shut lines, handles, lamps, grille, mirrors, dark
     valances and sills, roof rails (estate, SUV), arch cladding (SUV).
   - LOD1 112-120 tris (budget 120): same profile, round tyre and rim discs, framed windows, lamps, plates,
     mirrors, sills.
   - LOD2 38-42 tris: LOD1 body, glazed greenhouse, one dark under-body block.
   - `test_life_prototypes_budget_and_lods` unpacked 3-tuples and broke when decision 2 added the fourth element;
     it now indexes the tuple and additionally bounds LOD2 (<= 60 tris, below LOD1). Budgets 600 / 120 unchanged.

7. Second pass on the cars (2026-11-10, coordinator review: "flat low-poly boxes"):
   - Budget raised: cars / vans LOD0 <= 4000, LOD1 <= 600, LOD2 <= 120 triangles (was 600 / 120 / ~40).
     Justification: parked cars are seen from 5-12 m beside the route; LOD0 is drawn only below 12 m on Low and
     38 m on High (policy 25 / 90 / 400 m x lodBias), so a frame holds only a few LOD0 cars. WORKING_VALUE: the
     Samsung A16 measurement of a full car park is still pending; the cap moves only on that number.
     Generated: LOD0 3.3-3.5k, LOD1 540-570, LOD2 112-120 (LOD2 = the first-pass LOD1).
   - Shell: crowned roof / bonnet / glass, shoulder arcs, barrel sides with tumblehome, rounded plan corners,
     bumpers wrapping into the sides; wheel arches cut into the side on LOD0 and LOD1 with liners and the tyres set
     35 mm inside; revolved tyres, five-spoke alloy or pressed-steel wheels with hub caps; lamp clusters wrapping
     the corners, grille + lower intake, shut lines, handles, mirrors; LOD0 glazing is alpha-blended dark tint
     (`car_glass_tint`, manifest `"blend": true`, RegionImporter makes a transparent URP Lit material) over a dark
     interior (tub, dashboard, seats, headrests, headliner); LOD1 / LOD2 glass is opaque and duller (rough 0.65)
     so it no longer mirrors the sky as light grey on Low.
   - Prop GLB normals: `export.crease_normals` welds corners by position per prototype and averages face normals
     within 38 degrees (WORKING_VALUE), for ALL props: curved shells and >= 10-gon tubes shade smooth, boxes and
     6-gon posts keep hard edges as before.
   - Placement: `life.parking` now also cuts the dock manoeuvring zones (`dock_zones`, 35 m in front of every dock
     row, the same rectangles `truck_yards` keeps free) out of every car-park region. The apron polygon alone did
     not cover the case of a car-park polygon drawn over a truck yard (Kwadrat Park yard filled with cars).

8. Third pass on the cars (2026-11-10, coordinator review: milky glass, no visible dirt, dated boxy fronts):
   - Glass: `car_glass_tint` now carries `"shader": "car_glass"` and RegionImporter builds a `Kamion/World Car Glass`
     material (`Environment/Shaders/WorldCarGlass.shader`): premultiplied dark green-grey tint (alpha 0.84), Schlick
     F0 0.04 reflection of the environment probe capped at 0.55 and darkened for rays below the horizon, sun glint,
     GPU instancing. Cause of the milky light grey on High: URP Lit blended glass at rough 0.40 mirrored the blurred
     sky dome into every pane (grazing term = smoothness + reflectivity). Dust film on the pane edges comes from UV0
     (mask coordinate written by the generator: 1 at the lower / side edges, per-car reach 0.70-1.0).
   - Road film: alpha overlays `car_dirt_1..3` (three levels: alpha 0.55 / 0.80 / 1.0, grey-brown to salt-pale;
     shared generated texture `art-source/world/textures/car_dirt.png`, `export.car_dirt_png`) on the sills and
     lower doors with spray fans behind both wheels and a ring on the arch lips, on the tail face and (thin
     splatter) the lower front bumper; LOD0 and LOD1 (LOD1: three plain runs, tail). Blend materials with a
     `texture` are URP Lit transparent with specular highlights and environment reflections off. Brake dust:
     `rim_dusty` / `tyre_dusty` on the dirtier cars. Level, alloy style and film offset are a CRC of the prototype
     name (`life_cars._style`), so the 27 prototypes differ; instances of one prototype are identical.
     All colours and amounts WORKING_VALUE (no measured reference), look: Polish winter street.
   - Shapes (generic 2015-2024 class averages, no make reproduced): cowl-forward raked windscreens (run 0.86-0.96 m),
     bonnet falling to a rounded leading edge, a slanted fascia down to the bumper peak (`FACES`: swept / wide /
     tall), slim tapered lamp housings (`car_lamp`) with a reflector strip and a main-beam unit wrapping into the
     wing, chamfered grille with slats, lower and corner intakes, tapered wrap-around tail lamps, light bar (sedan),
     bumper reflectors, roof aerial fin, higher belt lines, plan corner radius 0.80 m. Wheels: rim 0.69 r, four
     alloy styles (5 wide, 10 thin, 7 medium, 5 dark with a machined lip) + pressed steel.
   - Generated: LOD0 3378-3664, LOD1 576-600, LOD2 112-120 (budgets 4000 / 600 / 120 unchanged).

9. Fourth pass (2026-11-10, REVIEW r6 W-N6 / W-N7 / W-N8 / W-N9, HANDOVER "red frame-budget test"):
   - Frame estimate (`build_world.mesh_budget`): point props now use `instance_ends()`, a copy of
     `InstanceImporter.Policy` (incl. the LOD-count reduction) times the tier lodBias (`LOD_POLICY.<tier>.lod_bias`,
     High 1.5, Low 0.5). The previous blanket High rule "props LOD0 < 120 m, LOD1 < 650 m" predated the per-family
     policy: it counted bins, pallets and truck rigs out to 650 m that the engine culls at 180 m (High) / 60 m (Low),
     and it disagreed with the engine for cars, lamps, signs and pylons. The limits of
     `test_frame_budget_with_forest_hlod` are unchanged (High <= 2.0 M everywhere, DK8 Low <= 0.6 M).
   - Vehicles (`car_`, `van_`, `tractor_`, `trailer_`): LOD switches still scale with lodBias, the cull distance is
     FIXED at `VehicleCullM` = 300 m on every tier (`WorldInstances.IsVehicle`, `build_world.VEHICLE_CULL_M`, a test
     checks they match). Before: cars culled at 200 m on Low / 600 m on High, truck rigs (default policy 30 / 120 m)
     at 60 m / 180 m, so the same frame showed different vehicles per tier (W-N6). Cars 25 / 90 / 300 m (Low
     12.5 / 45 / 300), tractors / trailers 40 / 300 m. Landmarks get their own 650 / 20000 m (the engine fell back
     to 30 / 120 m: the EC chimneys were culled at 60 m on Low).
   - LOD2 of cars / vans is now the cheap first-pass body (`_vehicle(lod=2)`: glazed greenhouse, under-body band,
     hexagonal tyre discs), 54-58 triangles. `_build` called `_vehicle(lod=1)` (112-120 triangles) since par. 7.
   - Result (estimate, generated 2026-11-10): max High frame 2.06 M (stretch_04, red) -> 1.965 M
     (route_onramp_andersa_above); max Low frame 911 k -> 910 k (stretch_04; roads 644 k of it, docs/06 hypothesis
     400-600 k is exceeded by roads, not by vehicles: cars + rigs 25 k there); DK8 Low 356 k -> 357 k.
   - Placement (W-N7, `life.parking`): occupancy drawn per row of bays 0.55-0.90 (`OCC_ROW`), the same prototype at
     most once in any 4 consecutive stalls of a row (deterministic re-draws, `REPEAT_GAP`), yaw +-3 deg, offset
     +-0.25 m across / +-0.40 m along the bay, 12 % reversed into perpendicular bays (never on parallel kerb
     strips), body mix hatch 33 / sedan 15 / estate 24 / SUV 28 % of cars, vans 12 % (WORKING_VALUE; r6: the Polish
     2026 fleet is mostly hatchbacks, estates and small SUVs, sedans <= 25 %). Generated: 968 cars + 131 vans in
     1630 bays; shares hatch 30.4 / SUV 23.8 / estate 19.2 / sedan 14.6 / van 11.9 %, reversed 11.7 %.
   - Glass (W-N8, `WorldCarGlass.shader`, `car_glass_tint`): alpha 0.84 -> 0.65 (transmission 0.35 per face),
     both faces drawn (`Cull Off`; with back faces culled the far pane was missing, so a car was a clear window
     onto the paving behind it), inner face reflects the dark cabin (env x 0.15, no glint, diffuse x 0.3), horizon
     darkening starts below the horizon (`_Horizon` 0.30 at r.y <= -0.30, full at r.y >= 0.12; it was 0.22 already
     at the horizon, so grazing panes stayed dark), dust film only on the outer quarter of the UV0 mask and lit at
     half strength, dust 0.6 -> 0.35. Measured with `tools/worldgen/qa/car_glass_qa.py` (projected LOD0 glass
     triangles, per-pixel incidence angle, Rec.709 luma of the PNG; 7 cameras around one parked estate next to
     stretch_01). Privacy glass behind the B pillar (SUV, estate, half the hatches; `_PrivacyOpacity` 0.80, decoded
     from a UV0 u offset of 4, no extra draw); the sheet's own tint term x 0.2 (clean glass has no diffuse body);
     RegionImporter writes every look constant (an existing material asset kept its saved values).
     Result, p50 luma, criterion < 45 deg <= 20 % / >= 70 deg >= 40 %: High clear 25.4 / 33.6, High overcast
     32.5 / 46.9, Low clear 23.5 / 31.5, Low overcast 30.2 / 44.8 (before this pass, same cameras: High clear
     27.5 / 36.6). NOT MET for < 45 deg on any tier / light and for >= 70 deg in clear light. Diagnostic: with
     `_Opacity` = `_PrivacyOpacity` = 0.98, `_Reflect` = 0 and `_Dust` = 0 the panes still show a bright, textured,
     sun-lit pattern (artifacts world-fixes/cars-v4/glass/tune5), so that content does not come from the glass blend;
     the darkest 1 % of every frame is 13-16 % luma (grading floor). Open for rendering-perf.
   - Plates (W-N9): `life_cars.plate_atlas()` -> `art-source/world/textures/car_plates.png`, 4 x 8 cells of
     520 x 114 mm Polish plates (EU band, white field, black characters), one per prototype (`_plate_index`), the
     last cell is the far plate (EU band + soft grey character band) used by LOD1. Strings are seeded
     (`plate_text`): district codes BI / BIA / BSK / BMN / BBI (WORKING_VALUE shares), vehicle part without B D I O Z
     (UNVERIFIED reading of the registration ordinance), not taken from any register. `car_plate` is textured.
   - Shapes (HANDOVER "square fronts"): LOD0 bonnet lip and bumper peak are 5-point quadratic Bezier rounds (reach
     0.16 m, was a 3-point 0.11 m chamfer); LOD1 keeps a 3-point chamfer there and 70 % of the crown (it had
     knife edges and one flat facet per panel that mirrored the sky: the "identical white sheen on every bonnet"
     of r6). LOD1 tread only on the lower half of the tyre (the upper half is inside the arch). Generated: LOD0
     3538-3784, LOD1 600-632, LOD2 54-58 triangles; LOD1 cap 600 -> 650 (LOD1 is the Low car from 12.5 to 45 m;
     cost in the Low frame estimate below 3 k triangles).
   - Paint roughness spread 0.30-0.50 per colour (it was 0.35 for all but white2); road film darker grey-brown,
     alpha 0.45 / 0.62 / 0.78 (level 3 at 1.0 read as beige two-tone paint), film line and spray fans lower;
     `rim_dusty` 0.115 -> 0.17 (black disc on LOD1).
10. Glass v5 (2026-11-10, rendering-perf, W-N8 follow-up; evidence `artifacts/world-fixes/glass-plastic/`):
   - **Cause of the bright textured pattern** (par. 9, tune5): the sun glint `pow(n.h, 900) x 12` in half precision.
     Normalised half vectors carry ~1e-3 error, so n.h jittered around the lobe and the whole pane turned into a stipple
     of sun-bright pixels whenever the sun stood roughly behind the camera (debug renders: glass opaque black = pattern
     gone, glint x 0 = pattern gone). In float the same lobe is a ~2 deg halo and a GGX lobe (alpha 0.01) keeps a
     5-10 deg tail; now the glint is the mirror image of the sun disk only (half vector within 0.23 deg, x 600), float.
   - Term budget at < 45 deg (decomposition renders, front faces, High clear): reflection 0.017-0.064 linear, dust film
     0.005-0.017, transmission 0.19-0.29 of what is behind. Side panes lean ~24 deg (tumblehome; face normal z p50 0.66
     over all panes), so the reflected ray of a pane seen from 1.7 m rises 30-75 deg into the sky (median r.y 0.96 in
     glass_side_25): the panes mirror the sky around the sun at 0.6-0.8 exposed, F (1 + T^2) ~ 0.045 -> ~0.03 linear
     = ~20 % luma from the sky alone. That is physical, not a blend or interior error.
   - Reflection: sky above ~15 deg (smoothstep 0..0.26 of r.y), below it the street clutter at the diffuse ground
     radiance `_KamionGroundEnv` (cars, halls, trees, paving; WORKING_VALUE) instead of the cube's horizon haze;
     `_Reflect` 1.3 -> 1.0 with the sheet's two faces R = F (1 + T^2) (clear x 1.12, privacy x 1.04).
   - Result p50 luma < 45 / >= 70 deg (criterion <= 20 / >= 40), same 7 cameras: High clear 24.3 / 33.0 (v4 25.4 /
     33.6), Low clear 22.6 / 31.0 (23.5 / 31.5), High overcast 30.5 / 44.4 (32.5 / 46.9), Low overcast 28.2 / 42.3
     (30.2 / 44.8). glass_side_00 < 45 deg 41.7 -> 24.8 (the stipple). **Still NOT MET** for < 45 deg (all) and >= 70 deg
     in clear light: with this sky radiance a leaning pane cannot read <= 20 % without darkening the sky reflection
     below physics. Options for the reviewer / owner: accept ~23-30 % (photo check of parked cars in Bialystok light),
     or revisit the sky model's absolute radiance (ADR 0010; would change the truck paint and glass too).
   - Frame floor (darkest 1 % = 13-16 % luma clear, 17-20 % overcast) is not the grading: the D23 toe maps 0.0025 to
     3.8 % (plain sRGB 3.2 %) and Low (no LUT) has the same floor. The darkest pixels are under the parked cars, lit
     by the full sky SH (no ambient occlusion on world props / paving): open, world-builder (contact AO under cars).
   - Cost: glass pixels only, one cube sample less branching, float glint; editor Low stretch-01 5.33 -> 5.19 ms
     (noise). A16 not measured.

## Not done / open
- r6 W-N8 glass criterion not met (par. 10: physics budget of a leaning pane mirroring the sky).
- Fixed vehicle cull and the Low LOD2 at 45-300 m are not measured on the A16.
- Road film and glass dust are per prototype, not per instance; the paint `car_grime` set is unchanged.
- r6 W-N6 parity was checked on the editor frames only (fixed vehicle cull); on Low the panel fence is opaque, so
  cars behind a fence are hidden on Low and visible on High (`kwadrat-park-gate`): furniture, not the vehicle LOD.
- `Kamion/World Car Glass` and the film overlays are not measured on the phone (two more transparent draws per LOD0 car).
- Alpha-blended car glass is not sorted per instance (dark tint hides the order); cost on the phone not measured.
- Transparent PMMA panels (photo `Andersa,_Maczka_streets_in_Białystok_2.jpg`) stand on the viaduct parapet,
  which is bridge geometry, and BDOT10k OT_OIKM_L has no material attribute. Open until a data source or an
  authored_override exists.
- Kerbside parking on streets without an OSM `parking:*` polygon (lane tags on ways are not in
  streetscape_sources yet).

## AO aut — WIP (niezweryfikowane), 2026-11-10
- Zrobione: kontaktowy cień / AO pod autami, dostawczakami, ciągnikami i naczepami (ADR 0050): shader
  `Kamion/World Vehicle Contact` (analityczny view factor płyt podwozia + opon, analityczna widoczność słońca, mnożnik
  tylko na części nieba tam, gdzie mapa cieni już ciemni), osobny prototyp `contact_<hash>` na spec (≤ 7 rysowań na
  klatkę zamiast +1 na każdy batch auta), parametry `life_props.contact_spec` w extras węzła `<auto>.contact`.
- Zmierzone (edytor, stretch-01 / glass_side_00, rdzeń pod autem, luma p5 przed → po): Low clear 28 → 3.9 / 27 → 1.9 %,
  High clear 25 → 4.6 / 24 → 3.2 %, Low overcast 43 → 11.0 / 47 → 8.2 %, High overcast 48 → 11.4 / 48 → 8.2 %;
  rysowania instancjonowane stretch-01 Low 558 (wersja „submesh na LOD” dawała 619).
- Otwarte: overcast nie spełnia p5 ≤ 8 % - dodana (NIERENDEROWANA) korekta gradacji nieba CIE dla szczeliny pod
  nadwoziem (`open (1 + open) / 2` ważone udziałem światła rozproszonego); trzeba: build_world + import + render 4
  konfiguracji, ocena visual-critic, koszt Low w edytorze (-TimeFrames), test EditMode importera.
- Dowody: `artifacts/world-fixes/cars-ao/{before,after,after2,compare}` (before = siła 0, after2 = wersja z osobnym
  prototypem, bez korekty CIE); skrypty `scratchpad/ao-aut/{render.ps1,measure.py}` (sesyjny scratchpad).
