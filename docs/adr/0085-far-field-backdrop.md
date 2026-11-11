# ADR 0085 — Far-field backdrop beyond the 2 × 2 km region tile (real GIS ring, radial foreshortening, 4-sector batching)
Status: Accepted (worldgen / rendering-perf), 2026-11-11. Extends ADR 0082 (`WorldEdgeBuilder`).

## Context
ADR 0082 added `WorldEdgeBuilder` to prevent roads from ending in a white void at the $\pm 1024\text{ m}$ boundary of `bialystok-industrial-c`: it placed concrete barriers with U-20 boards 60 m inside each boundary road exit, road stubs, a runtime recovery safety net (`WorldBoundary`), and a `terrain_grass` apron extruded to 2600 m.

However, beyond the U-20 closures at all four main exits (`al. Tysiąclecia Państwa Polskiego` N and S, `ul. Gen. Stanisława Maczka` E and W), the horizon was an empty green prairie (`r0-before`), whereas in real Białystok those directions show:
- **North (`edge-north`, `dk8-dk19-exit`):** dense coniferous/mixed pine stands of Las Pietrasze (including powiat 2002 outside the municipal boundary) and overhead HV lines;
- **East (`edge-east`):** Wygoda / Pieczurki industrial halls, multi-storey residential blocks, brick office buildings, chimneys, and HV lattice pylons;
- **South (`edge-south`):** Białostoczek / Osiedle Tysiąclecia 5–11 storey wielka-płyta residential blocks, commercial/industrial halls along the railway corridor, and the tall red/white-banded chimneys of Elektrociepłownia Białystok;
- **West (`edge-west`):** Bacieczki / Dziesięciny / Zawady commercial halls, residential block estates, HV power lines, and the edge of Las Bacieczki.

Additionally, `QualityProfile.cs` sets `cameraFarClip = 900f` on `Low` tier (Samsung Galaxy A16 4G budget) and `2500f` on `High` tier, and requires the far-field backdrop on `Low` to add at most ~4 draw calls, $\le 30\text{k}$ triangles, and $\le 1\text{ MB}$ of textures (or zero new textures by reusing existing world materials).

## Options
| Option | Draw calls / Tris (Low) | Visual fidelity (300–2000 m) | Low 900 m far-clip compatibility |
|---|---|---|---|
| 1. Cylindrical skybox / panorama card | 1 draw / <1k tris | Poor parallax when driving along the border; flat painted look (`docs/06` violation) | Yes |
| 2. Full chunk generation out to 6 × 6 km | >80 draws / >400k tris | High | Clipped at 900 m on Low; exceeds A16 memory & GPU budget |
| 3. **4-sector GIS ring backdrop with radial perspective foreshortening + vertex-coloured `_FAR_FACADE` & `_HLOD_EDGE`** | **+2 to +4 draws per camera / 24.8k tris total across all 4 sectors** | **True 3D parallax, calibrated `docs/06` linear albedos, procedural window grids, alpha-tested tree crowns, `KamionFogTau` aerial haze** | **Yes — 0–4.2 km ring mapped smoothly into $d_{\text{eff}} \le 650\text{ m}$** |

## Decision
We adopt **Option 3**:

1. **Real Open GIS Ring Extraction (`tools/worldgen/streetscape/far_field.py`):**
   - Extracts a ring out to $4200\text{ m}$ from the region origin (`x: 777995, y: 596223` EPSG:2180) from three open datasets pinned by SHA256 in `Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json` and `docs/LICENSES.md`:
     - **GUGiK BDOT10k (`2061` GPKG):** `OT_PTLZ_A` (forests by `KATEGORIA`: conifer / mixed / broadleaf), `OT_BUBD_A` (building footprints, `FUNKCJAOGOLNABUDYNKU`, `PRZEWAZAJACAFUNKCJABUDYNKU`, `LICZBAKONDYGNACJI`), `OT_BUWT_P` (chimneys `komin`, HV pylons `słup energetyczny`, towers `maszt` with `WYSOKOSC`), `OT_SULN_L` (overhead HV power lines).
     - **GUGiK LoD1 2024 (`2061_lod1_2024.zip`):** exact `measuredHeight` joined by `buildingId` / `LOKALNYID`.
     - **OpenStreetMap (`podlaskie-261108.osm.pbf`, ODbL):** supplements `landuse=forest` / `natural=wood`, buildings (`building:levels`, `height`), `man_made=chimney`, and `power=tower` / `power=line` outside the city boundary (powiat 2002 north of `N = +1024 m`).
   - Total extracted ring features for `bialystok-industrial-c`: **472** forest polygons, **8,470** buildings (`2,474` residential blocks, `1,620` halls, `3,429` offices/commercial, `947` pitched-roof houses), **16** industrial/district-heating chimneys, **302** HV pylons/towers, and **107** power-line spans.

2. **Radial Perspective Foreshortening for Low `cameraFarClip = 900 m`:**
   - Distance $d$ outside the $\pm 1024\text{ m}$ boundary is mapped via:
     $$d_{\text{eff}}(d) = \begin{cases} d & d \le 140\text{ m} \\ 140 + 520\bigl(1 - e^{-(d - 140)/950}\bigr) & d > 140\text{ m} \end{cases}$$
     with horizontal footprint scale $s_{xy}(d) = \operatorname{clamp}\bigl(\frac{d_{\text{eff}}+140}{d+140}, 0.32, 1.0\bigr)$ and vertical height scale $s_h(d) = \bigl(\frac{d_{\text{eff}}+160}{d+160}\bigr)^{0.62}$.
   - This keeps the entire $0\text{–}4.2\text{ km}$ ring within $d_{\text{eff}} \le 650\text{ m}$ (inside `Low` tier's $900\text{ m}$ far clip plane even from `dk8-dk19-exit`) while preserving true angular skyline proportions and `KamionFogTau` atmospheric extinction.

3. **4 Disjoint Frustum Sectors × 2 Submeshes (Zero New Textures):**
   - Geometry is partitioned into 4 sector nodes (`far_north`, `far_east`, `far_south`, `far_west`) whose angular boundaries are aligned with the 4 border road exits. Each sector has at most **2 primitives**:
     - **Submesh 0 (`M_far_field_buildings`, `Kamion/World Surface` + `_FAR_FACADE`):** single combined mesh for residential blocks, industrial halls, offices, pitched-roof houses, red/white-banded chimneys, HV lattice pylons, and dark under-canopy forest mounds (subdivided into $\le 320\text{ m}$ cells so triangle fans never bridge concave road corridors). `WorldSurface.shader` was extended so `_FAR_FACADE` multiplies base albedo by `COLOR_0.rgb` (calibrated `docs/06` §3 linear albedos) and selects the window mode from `COLOR_0.a` (`1.0` = punched block/office window grid from `TEXCOORD_1`, `0.75` = industrial/clerestory ribbon glazing, `< 0.5` = windowless wall/roof/chimney/pylon/canopy). Existing `buildings_lod1` meshes without vertex colors default to `COLOR = (1,1,1,1)` in Unity, remaining 100% backwards-compatible.
     - **Submesh 1 (`M_forest_edge_mixed`, `Kamion/Vegetation` + `_HLOD_EDGE`):** alpha-tested double-sided tree-crown curtains along stand edges facing the tile (`facing_tile >= 0.44` to avoid dark grazing-angle radial curtains) and frontal transverse interior tree-crown ribs, reusing the existing baked `forest_edge_mixed` atlas (0 bytes of new texture memory).

4. **Synchronized Apron Grading & Ground Masks (`WorldEdgeBuilder.cs`):**
   - `BuildApron` and `BorderElevation.z_at_eff` both smooth the perimeter terrain elevation with the exact same local circular moving average (`w = 6`, `±96 m`) and ease locally over $260\text{ m}$ (`t * t * (3 - 2t)`), ensuring zero height gap between the terrain apron and far-field buildings/forests even in steep border valleys (`edge-east` at $E = +1024\text{ m}, N = -980.1\text{ m}$ where heightmap rises $12\text{ m}$ northward).
   - Parallel slip-road stubs within $30\text{ m}$ are deduplicated and graded smoothly onto the apron surface, eliminating the `edge-west` embankment wall artifact.
   - Apron vertices write spatially coherent `COLOR_0` ground masks (`G` forest needle/leaf litter, `B` unmown dry meadow grass, `A` bare soil/urban earth, `R` road-shoulder grit) consumed by `_GroundMasks` on `M_terrain_grass`.

## Measured Performance Budget (`stats.txt`)
| Camera (`WorldC`, Low tier) | `r0-before` drawsEst | `r2` drawsEst | Delta Draws | `r0-before` shadowDraws | `r2` shadowDraws | `r0-before` trisK | `r2` trisK |
|---|---|---|---|---|---|---|---|
| `edge-north` | 43 | 47 | **+4** | 21 | 21 (**+0**) | 59 | 71 (**+12k**) |
| `edge-east` | 46 | 50 | **+4** | 18 | 18 (**+0**) | 63 | 85 (**+22k**) |
| `edge-south` | 114 | 116 | **+2** | 69 | 69 (**+0**) | 124 | 140 (**+16k**) |
| `edge-west` | 46 | 48 | **+2** | 15 | 15 (**+0**) | 70 | 78 (**+8k**) |
| `dk8-dk19-exit` | 77 | 81 | **+4** | 2 | 2 (**+0**) | 106 | 118 (**+12k**) |

- **Total Low far-field triangles (all 4 sectors combined):** `24,826` ($\le 30\text{k}$ budget; `far_north: 4,003`, `far_east: 6,204`, `far_south: 11,211`, `far_west: 3,408`).
- **Total High far-field triangles (all 4 sectors combined):** `118,902` (`far_north: 19,350`, `far_east: 35,030`, `far_south: 47,581`, `far_west: 16,941`).
- **New texture memory:** `0 B` (reuses `M_forest_edge_mixed` and procedural `M_far_field_buildings`).
- **Colliders / Shadow Casters:** `0` colliders, `ShadowCastingMode.Off`, `receiveShadows = false`.

## Revision r2 (stream H, 2026-11-11; validation in progress)

The r1 centroid-only building selection duplicated boundary-crossing buildings. Its cached rectangles contain 17 intersections with the region, including the long hall covering the cream office in edge-south. Region geometry owns a whole building when any source component touches/intersects the tile. The extractor now rejects such BDOT/OSM footprints before selecting the largest component, and separately rejects rounded minimum rectangles overlapping the tile. The mesh builder repeats the guard before and after distance compression. Cache schema /10 also keys the origin, half-size, ring extent and region buildings.geojson SHA256. Two additional exterior rectangles overlapped full regional building footprints beyond the tile; the exclusion includes those complete regional outlines as well as the tile. Both raw and compressed rectangles must be disjoint from this union, including at extraction time: distance compression can move a fully exterior rectangle onto the exterior part of a regional building. The mesh builder retains its independent defensive guard.

Regressions cover all four edges, boundary contact, a MultiPolygon whose small component crosses the tile, and a concave building outside the NE corner whose rectangular LoD would enter it. Both tiers must emit no geometry for a crossing hall, while a fully external hall remains. Real-data QA checks every cached rectangle.

Atmosphere integration with ADR 0098: r2 adds no fog constants, keywords or private colour blends. Far facades use WorldSurface/KamionFogTau + KamionMixFog; forest silhouettes use the existing vegetation atmosphere. The lighting owner can adjust the common atmosphere without an edge-specific competing preset. Optical depth still uses compressed render distance (inherited limitation); physical-distance haze is UNVERIFIED and must not be claimed from editor triangle counts.

Supplementary edge-pietrasze-horizon (road-seated driver eye) and edge-pietrasze-overview (18.2 m above NMT, diagnostic only) accompany the unchanged dk8-dk19-exit camera. Existing NMT inside the tile supplies the border elevation; the exterior apron remains the smoothed-border approximation, not a measured full-ring NMT surface.

Performance baseline for r2 is argon-edge + main 9e6e9fde on the same imported world. The original r1 addition relative to main without a backdrop cost +2..4 estimated draws; r2 does not erase that inherited cost. Render comparisons and current test results belong in artifacts/edge-far-r2/REPORT.md; old r1 claims above are historical, not revalidation of this revision.


