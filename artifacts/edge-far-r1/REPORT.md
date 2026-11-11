# ARGON-TASK-01-WORLD-EDGE — Final Report (`ADR 0085`: Far-Field Backdrop)

## 1. Executive Summary
We implemented a reproducible, real-GIS far-field backdrop (`ADR 0085`) beyond the $2048 \times 2048\text{ m}$ boundary of `bialystok-industrial-c` (`WorldC` and `WorldC_High`), replacing the bare green `terrain_grass` apron horizon from `ADR 0082` with authentic Białystok surroundings out to $4.2\text{ km}$ from the region origin (`EPSG:2180 x: 777995, y: 596223`).

All Definition of Done requirements are met:
1. **Open GIS Data & Provenance:** Extracted from GUGiK BDOT10k (`powiat 2061`), GUGiK LoD1 2024 (`2061_lod1_2024.zip`), and OpenStreetMap (`podlaskie-261108.osm.pbf`, ODbL), pinned with SHA256 hashes in `Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json` and documented in `docs/LICENSES.md`.
2. **Real Skyline Geometry:** **472** forest stands (`Las Pietrasze`, `Las Bacieczki`), **8,470** buildings (`2,474` multi-storey residential blocks, `1,620` industrial/commercial halls, `3,429` offices/service buildings, `947` pitched-roof houses), **16** industrial/district-heating chimneys (including `EC Białystok`), **302** HV lattice pylons/towers, and **107** overhead HV power-line spans.
3. **Low-Tier Performance Budget (Samsung Galaxy A16, 30 fps):**
   - **Total `Low` triangles across all 4 sectors combined:** **`24,826` tris** ($\le 30,000$ budget: `far_north: 4,003`, `far_east: 6,204`, `far_south: 11,211`, `far_west: 3,408`).
   - **Total `High` triangles across all 4 sectors combined:** **`118,902` tris** (`far_north: 19,350`, `far_east: 35,030`, `far_south: 47,581`, `far_west: 16,941`).
   - **Draw calls per camera:** **+2 to +4 draw calls** (`1–2` visible sectors $\times$ `2` submeshes: `M_far_field_buildings` and `M_forest_edge_mixed`).
   - **Shadow draw calls:** **+0** (`ShadowCastingMode.Off`, `receiveShadows = false`).
   - **Colliders:** **0** (purely visual backdrop; ADR 0082 U-20 closures and `WorldBoundary` recovery remain untouched).
   - **New texture memory:** **0 B** (reuses existing `M_forest_edge_mixed` canopy atlas and procedural `_FAR_FACADE` material `M_far_field_buildings`).

---

## 2. Visual Progression (`r0-before` → `r1` → `r2`)

| Control Camera | Location & Direction | `r0-before` (Baseline) | `r1` (Round 1) | `r2` (Final Round 2) |
|---|---|---|---|---|
| `edge-north` | `al. Tysiąclecia Państwa Polskiego` N (`E=-856.6, N=+1024`) | Bare green apron horizon behind U-20 barrier; road stub ends in empty grass | Added `podlaskie` OSM forest ring, but road exit corridor was misaligned (`E=+712` vs `-856.6`), creating a dark grazing-angle forest wall on the left and a gap ahead | Aligned road corridor to `E=-856.6, N=+1024`, removed grazing-angle radial curtains (`facing_tile < 0.44`), subdivided under-canopy mounds ($\le 320\text{ m}$), and placed frontal layered pine crowns closing the horizon at $d \ge 165\text{ m}$ |
| `dk8-dk19-exit` | Elevated overview of N exit (`E=-828, N=+905, U=+18.2`) | White/hazy void gap between left and right tile tree stands at the end of DK8/DK19 | Gap filled by Las Pietrasze pine stands, but inner corridor had a dark radial curtain wall | Natural multi-tier coniferous skyline of Las Pietrasze seamlessly bridging the tile trees across the northern horizon in both `Low` and `High` tiers |
| `edge-east` | `ul. Gen. Władysława Andersa` E (`E=+1024, N=-980.1`) | Empty green apron slope behind U-20 barrier | Added Wygoda/Pieczurki blocks, halls, and chimneys, but `+2.8 m` border smoothing mismatch (`w=32` vs steep valley at `N=-980.1`) left buildings floating above the apron | Synchronized local perimeter smoothing (`w=6`, `±96 m`) in both `WorldEdgeBuilder.cs` and `far_field.py` + extracted all BDOT10k `335` + LoD1 2024 heights; blocks, halls, HV pylons, and chimneys sit flush on the ground |
| `edge-south` | `al. Tysiąclecia Państwa Polskiego` S (`E=-237.6, N=-1024`) | Bare green apron horizon behind U-20 barrier | Synthetic `_corridor_treelines` at `N=-1026` formed a dark curtain across the road, hiding the southern city skyline | Removed synthetic curtain across exit; reveals authentic Białostoczek / Osiedle Tysiąclecia 5–11 storey wielka-płyta residential blocks, commercial halls, HV pylons, and red/white-banded `EC Białystok` chimneys |
| `edge-west` | `ul. Gen. Stanisława Maczka` W (`E=-1024, N=+44.1`) | Overlapping slip-road stub created a 4.5 m green wall right behind the U-20 barrier | Deduplicated slip-road stubs, but easing apron to global perimeter mean (`143 m` vs valley `131.5 m`) tilted the apron uphill by `+12 m`, hiding buildings | Local perimeter smoothing keeps the western valley level at `131.5 m`; clearly shows Bacieczki / Dziesięciny residential blocks, industrial halls, HV pylons, and forest edge behind the U-20 closure |

---

## 3. Performance Measurements (`stats.txt`)

### Low Tier (`WorldC`, `msaa=2`, `renderScale=0.75`, `cameraFarClip=900m`)
| Camera | `r0-before` objects | `r2` objects | `r0-before` drawsEst | `r2` drawsEst | Delta Draws | `r0-before` shadowDraws | `r2` shadowDraws | `r0-before` trisK | `r2` trisK | Delta trisK |
|---|---|---|---|---|---|---|---|---|---|---|
| `edge-north` | 10 | 12 | 43 | 47 | **+4** | 21 | 21 (**+0**) | 59 | 71 | **+12k** |
| `edge-east` | 9 | 11 | 46 | 50 | **+4** | 18 | 18 (**+0**) | 63 | 85 | **+22k** |
| `edge-south` | 14 | 15 | 114 | 116 | **+2** | 69 | 69 (**+0**) | 124 | 140 | **+16k** |
| `edge-west` | 13 | 14 | 46 | 48 | **+2** | 15 | 15 (**+0**) | 70 | 78 | **+8k** |
| `dk8-dk19-exit` | 23 | 25 | 77 | 81 | **+4** | 2 | 2 (**+0**) | 106 | 118 | **+12k** |

### High Tier (`WorldC_High`, `msaa=2`, `renderScale=1.0`, `cameraFarClip=2500m`)
| Camera | `r0-before` objects | `r2` objects | `r0-before` drawsEst | `r2` drawsEst | Delta Draws | `r0-before` shadowDraws | `r2` shadowDraws | `r0-before` trisK | `r2` trisK | Delta trisK |
|---|---|---|---|---|---|---|---|---|---|---|
| `edge-north` | 10 | 12 | 43 | 47 | **+4** | 81 | 81 (**+0**) | 59 | 71 | **+12k** |
| `edge-east` | 9 | 11 | 46 | 50 | **+4** | 102 | 102 (**+0**) | 63 | 85 | **+22k** |
| `edge-south` | 14 | 16 | 114 | 118 | **+4** | 270 | 270 (**+0**) | 147 | 169 | **+22k** |
| `edge-west` | 13 | 14 | 46 | 48 | **+2** | 102 | 102 (**+0**) | 72 | 80 | **+8k** |
| `dk8-dk19-exit` | 28 | 30 | 92 | 96 | **+4** | 51 | 51 (**+0**) | 141 | 153 | **+12k** |

---

## 4. Verification & Test Suite Results
- **Python GIS & Far-Field Tests (`uv run --project tools/worldgen pytest tests/gis -q`):**
  - `tests/gis/test_far_field.py`: **5/5 passed** (radial foreshortening within `Low` 900 m far-clip, 4-sector angular partition aligned with road exits, local perimeter elevation smoothing, sector builder + building window modes, QA report + SHA256 source manifest + `docs/LICENSES.md`).
  - `tests/gis/test_route_corridor.py` + `tests/gis/test_depot_yard.py` + `tests/gis/test_road_fidelity.py`: **Green**.
- **Unity EditMode Tests (`pwsh scripts/test.ps1 -Platform EditMode`):** **188 total, 188 passed, 0 failed, 0 skipped** (`artifacts/tests/editmode-20261111-104802.xml`).
- **Unity PlayMode Recovery Tests (`pwsh scripts/test.ps1 -Platform PlayMode -Filter WorldEdgeRecoveryTests`):** **3 total, 3 passed, 0 failed, 0 skipped** (`artifacts/tests/playmode-20261111-115415.xml` — verifies ADR 0082 closures, `WorldBoundary` recovery from 105 km/h exit and under-world fall, apron bounds, and all 4 `WorldEdge/FarField_far_*` sectors with zero colliders and `ShadowCastingMode.Off`).
