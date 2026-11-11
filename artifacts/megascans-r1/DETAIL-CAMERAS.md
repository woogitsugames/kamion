# Driver detail cameras ? WORKING_VALUE QA only

The cameras follow the unmodified exported `route_start.json` autopilot line. They do not move or add world assets. These are material-legibility test viewpoints, not surveyed viewpoints or production control-camera changes.

| Camera | Route s (m) | Existing generated asset | Along-route before asset (m) | 3D eye-to-asset (m) | Asset offset from route (m) |
|---|---:|---|---:|---:|---:|
| `megascans_eye_manhole_s0928` | 927.944 | `metal-manhole-cover` | 8.000 | 8.370 | 0.000 |
| `megascans_eye_gully_s0482` | 481.737 | `square-rusty-drain` | 8.000 | 8.834 | 2.950 |
| `megascans_eye_verge_s0523` | 522.995 | `fab_elderberry` | 8.000 | 9.533 | 4.476 |

All cameras: vertical FOV 70?, eye 2.3 m above the actual exported asphalt-collision triangle, horizontal offset **0 m** from the authoritative route, look 25 m along the same route. The three sampled points hit `road_collision` / `collision_asphalt` through the existing `streetscape.furniture.SurfaceTop(..., collision=True)` sampler. The JSON records the resulting absolute U height; evidence includes the collision sample and exact source coordinates.

**Capture constraint:** `Gate3Cameras.HeightAboveRoad("driver_eye")` is hard-coded to 2.5 m. These JSON entries therefore use `seat: "file"` to preserve the requested 2.3 m without an engine change. At capture, verify their positions with the existing `Gate3Cameras.TryGroundY` raycast (the root may use an artifact-only editor probe); the expected physical hit is `pos.U - 2.3 m`. Do not silently switch to `seat: "road"`, because that would render from 2.5 m. Unity physical-raycast proof remains pending until capture.

The drainage candidates were read from actual current `chunk_*.low.glb` geometry: connected quad vertices of `fab_drainage`, with UV V flipped back exactly as `GlbReader.ReadVec2(..., true)` does, then identified by the accepted atlas rectangles. The vegetation candidate comes from the current `instances_*.json`; no illustrative or invented asset coordinates. All selected points avoid the known corridor s1432?1480.

- `megascans_eye_manhole_s0928`: `Data/raw/derived/bialystok-industrial-c/world/chunk_4_5.low.glb`; asset ENU `[43.981, -434.241989, 139.494747]`; eye ENU `[51.032244, -438.020873, 141.954724]`; asphalt collision U `139.654724`.
- `megascans_eye_gully_s0482`: `Data/raw/derived/bialystok-industrial-c/world/chunk_5_6.low.glb`; asset ENU `[443.797997, -631.26326, 140.005749]`; eye ENU `[449.418578, -637.674554, 142.319211]`; asphalt collision U `140.019211`.
- `megascans_eye_verge_s0523`: `Data/raw/derived/bialystok-industrial-c/world/instances_5_6.json`; asset ENU `[403.975, -619.216, 139.909]`; eye ENU `[413.080488, -618.152082, 142.524826]`; asphalt collision U `140.224826`.

Regenerate the artifact only:
```powershell
uv run --project tools/worldgen python artifacts/megascans-r1/build_detail_cameras.py
```

Capture the same camera JSON against the genuinely baked before scene and after scene independently; do not manufacture pre-change frames by recolouring the after scene.
```powershell
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Gate3 artifacts/megascans-r1/detail-cameras.json -Cameras megascans_eye_manhole_s0928,megascans_eye_gully_s0482,megascans_eye_verge_s0523 -OutputDir artifacts/megascans-r1/detail-after/Low-overcast
```
