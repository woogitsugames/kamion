# ADR 0103 — georeferenced photo | render evidence for gate 3

Status: implemented tooling; **gate/evidence acceptance pending renders and pose calibration**.
Scope: stream J only, branch `gpt-sbs-gate3`, base main `9e6e9fde` (2026-11-11).

## Problem

The existing gate reference map associates a ground photo with aerial and approximate
route cameras. It cannot establish the same-shot comparison required by docs/03.
We need photo-derived cameras without touching world generators, scenes or other
agents' `control_cameras.json`.

## Decision

`tools/refs/sbs_gate3.py prepare` reads the local Mapillary JSONL manifest and verifies
each selected image's SHA256. It selects 20 unique photos within 40 m of each G3-A/B
polyline, distributes them by station, excludes panoramas/missing heading/unknown
licence and rejects dark upper-half thumbnails (median <=65 sRGB). This last filter
excludes night but **does not exclude sunset**; the inspected set contains low-sun
images. No Google, network request, tokens or image URLs carrying credentials.

New data files under `Data/Regions/bialystok-industrial-c/`:

- `sbs_references.json`: photo, author, licence, page URL, timestamp, hash, dimensions,
  GPS, true/grid heading, station and route distance. Not combined into an OSM database.
- `sbs_authored_overrides.json`: per-camera adjustments, preserved across regeneration.
- `sbs_cameras.json`: disabled photo-match cameras, consumable via existing `-Gate3`.

WGS84 is transformed to EPSG:2180 and the region origin is subtracted for E/N.
True-north compass is transformed using a 20 m geodesic, so meridian convergence is
accounted for. U is **absolute NMT altitude**, not origin-relative Unity Y; terrain is
bilinearly sampled from the copied R16. Default eye height 2.2 m and horizontal FOV
90 degrees are **WORKING_VALUE**, not extracted intrinsics. Thumbnails have no focal
length EXIF. Vertical FOV is `2 atan(tan(hfov/2)/aspect)`. `seat=file` prevents existing
gate-camera raycasts from silently changing the authored pose. Deck-level cameras
need `absolute_u_m` if bare-earth NMT is below the photographed bridge.

Horizon/vanishing-point fractions were estimated manually from the inspected contact
sheets (uncertainty roughly +/-0.04 of image height). They set pitch using
`atan((2*horizon-1)*tan(vfov/2))`. These are initial fits, **not verified same-shot poses**.
GPS/heading accuracy, lens distortion and roll remain unverified. A pinhole renderer
cannot exactly match the strongly curved wide-angle photos without lens calibration.
Position/heading/FOV/eye corrections must be based on multiple stable landmarks,
not merely on matching histogram brightness.

## Run and calibrate

From the dedicated worktree:

```powershell
uv run --project tools/refs python tools/refs/sbs_gate3.py prepare
pwsh scripts/sbs-gate3.ps1 -EditMode
```

The wrapper checks the main `artifacts/locks/PHONE_RUN` before **every** Unity start,
waits in 60-second intervals, then runs EditMode and Low/High x overcast/clear serially.
It renders aspect groups at 1280x960 or 1280x720 (no image stretch/crop), keeps each
group's stats and restores tracked rendering settings and ProjectSettings afterwards.
No adb/phone operations. Copying the main Library is optional and was done locally.

Calibration fields per camera (all optional, no implicit modifications):

```json
{
  "east_delta_m": 0,
  "north_delta_m": 0,
  "heading_delta_deg": 0,
  "eye_height_m": 2.2,
  "horizontal_fov_deg": 90,
  "horizon_y_fraction": 0.65,
  "pose_status": "WORKING_VALUE",
  "note": "Explain measured landmarks and uncertainty here"
}
```

`absolute_u_m` overrides NMT+eye when necessary. Keep uncertainty visible until a
reviewer compares the actual pair. Re-run prepare after changing overrides, then
re-render; compose alone cannot update the camera image. `-ComposeOnly` regenerates
sheets from existing renders; it does not run Unity. `-Tiers Low -Lighting clear` is
a smaller render pass; the default matrix remains required for final evidence.

## Sheets and metrics

Each 960-pixel-wide sheet has photo | render, 25% grid, red horizon line, attribution,
source link and normalized 32-bin sRGB luma histograms. Metrics use original image
pixels before resizing/overlays. They include full-frame luma, histogram L1 difference,
sky/asphalt area estimates and source/render hashes. These values describe the
images, not physical albedo or a quality PASS. Weather, camera white balance,
season, age of the scene, car hood and lens distortion affect comparisons.

The default sky/asphalt masks are explicit **WORKING_VALUE RGB/position heuristics**,
not a semantic classifier. For measured ratios, author separate normalized polygons
in `authored_overrides.<id>.masks.photo` and `.render`, each with `sky` and `asphalt`
arrays of polygons, e.g. `"sky": [[[0.7,0.05],[0.95,0.05],[0.95,0.3]]]`.
Overlapping masks and invalid polygons fail; zero asphalt yields null, not infinity.
Composition fails on a missing render, incorrect aspect or altered source image.
Synthetic composer test images never count toward the real evidence target.

## Licences, coverage and consequences

Every photo is recorded in `docs/refs/sbs-gate3-attribution.md`, linked by LICENSES
and REFERENCES. CC BY-SA photo panels are resized/overlaid reference derivatives;
the render is a separate panel. Photo pixels stay outside git/build/textures.

The local set has **no coverage of the first ~300 m of G3-A**. Its 20 photos cluster
near Rondo Bieżeństwa; it must not be presented as complete segment coverage. Public
photos also do not replace the owner's same-place photos/approval in docs/03.

No world/runtime/shader/material changes; no new draw calls by design. Runtime cost
and editor per-view stats remain UNVERIFIED until the guarded render run completes.
EditMode and independent visual review remain pending while PHONE_RUN blocks Unity.
Expected merge conflicts: additive tail sections in LICENSES/REFERENCES only; new
SBS files do not modify cameras or world files owned by other streams.
