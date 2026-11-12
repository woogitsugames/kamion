# D / ADR0099 read-only preflight

Preparation only: no road/material production change, no Unity or phone action.
D's dependency is satisfied by main merge471438fb (ADR0095). Current-main
products were inspected while F/G/E rendering waits for the leader phone run.

Existing effects must be measured before adding duplicates:
- WorldPBR.shader already has ROADWEAR wheel polish, gutter damp/grit and centre
  drip bands, plus oil/patch/tyre decals and DECAL_PAINT wheel-path chipping.
- CRACKS is guarded by _KAMION_WORLD_DETAIL, so it is deliberately absent on Low.
  Enabling the existing two crack samples on Low is not a free budget change.
- WorldPbrMaterials already binds these layers and road parameters. Macro wear,
  cracks, paint and tyre bands are not wholly missing features.
- Yard_wear/life/gate modules already place local decals. Preserve calibrated
  asphalt mean and C sky-road relationship; avoid uniform new dirt everywhere.

Measured current-main GLB attribute coverage (road-wear-uv-preflight.json):
128 High/Low GLBs match their manifest hashes. Old road_asphalt has valid lane
UVs on62.443percent of121022vertices; road_asphalt_new on all3365vertices.
These are VERTEX counts, not area/pixel coverage. Junction sentinel sections
intentionally have no lane coordinate; they cannot be fixed by simply increasing
WheelPolish. Two small old-road primitives omit UV1 entirely: chunk2_3(9vertices)
and chunk5_4(162vertices), identical in Low/High. WorldMeshBake allocates zero UV
for missing data, so those vertices default to lane0/edge0 rather than (-1,5).
Treat that as a narrow mask/importer-contract issue, not an allegation that all
road wear is absent. No roads/* or geometry changes are authorized for D.

Next agent should lock its own current-main baseline, verify actual materials,
inspect real Mapillary road photographs, then choose additive masks/material
changes with regional/traffic context. Keep position/index/normal topology proof,
no extra draws, and measure samples/memory/visible route cost. Any extra shader
work needs an honest budget limit; CPU stats are not phone GPU milliseconds.
Preserve existing Tile, weather/runoff, macro/panel/splash and other streams'
shared includes and semantics. Final own GIS/EditMode/LowHigh four-condition
images and independent review remain required; this preflight is not DoD.
