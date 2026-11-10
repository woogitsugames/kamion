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

## Not done / open
- Transparent PMMA panels (photo `Andersa,_Maczka_streets_in_Białystok_2.jpg`) stand on the viaduct parapet,
  which is bridge geometry, and BDOT10k OT_OIKM_L has no material attribute. Open until a data source or an
  authored_override exists.
- Kerbside parking on streets without an OSM `parking:*` polygon (lane tags on ways are not in
  streetscape_sources yet).
