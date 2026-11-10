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

## Not done / open
- Car grime is still only the `car_grime` texture set (weak at distance); no wheel / sill dirt geometry or decals.
- Alpha-blended car glass is not sorted per instance (dark tint hides the order); cost on the phone not measured.
- Transparent PMMA panels (photo `Andersa,_Maczka_streets_in_Białystok_2.jpg`) stand on the viaduct parapet,
  which is bridge geometry, and BDOT10k OT_OIKM_L has no material attribute. Open until a data source or an
  authored_override exists.
- Kerbside parking on streets without an OSM `parking:*` polygon (lane tags on ways are not in
  streetscape_sources yet).
