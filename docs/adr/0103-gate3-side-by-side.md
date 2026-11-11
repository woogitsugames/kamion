# ADR 0103 — georeferenced photo | render evidence for gate 3

Status: tooling and 160 comparison sheets delivered; **gate 3 NOT accepted**.
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
images. Prepare/compose make no network requests. No Google or saved credentials.

New data files under `Data/Regions/bialystok-industrial-c/`:

- `sbs_references.json`: photo, author, licence, page URL, timestamp, hash, dimensions,
  GPS, true/grid heading, station and route distance. Not combined into an OSM database.
- `sbs_authored_overrides.json`: per-camera adjustments, preserved across regeneration.
- `sbs_cameras.json`: disabled photo-match cameras, consumable via existing `-Gate3`.
- `sbs_intrinsics.json`: public camera parameters fetched explicitly from Mapillary;
  27 fisheye / 13 perspective, 38 orientation 1 / 2 orientation 3 in this set.

WGS84 is transformed to EPSG:2180 and the region origin is subtracted for E/N.
True-north compass is transformed using a 20 m geodesic, so meridian convergence is
accounted for. U is **absolute NMT altitude**, not origin-relative Unity Y; terrain is
bilinearly sampled from the copied R16. Default eye height 2.2 m and horizontal FOV
90 degrees are fallback **WORKING_VALUE** without cached intrinsics. Thumbnails have
no focal-length EXIF. The current set instead uses the cached intrinsic calibration
and matching rectified-view FOV. Vertical FOV is `2 atan(tan(hfov/2)/aspect)`. `seat=file` prevents existing
gate-camera raycasts from silently changing the authored pose. Deck-level cameras
need `absolute_u_m` if bare-earth NMT is below the photographed bridge.

Horizon/vanishing-point fractions were estimated manually from the inspected contact
sheets before rectification (uncertainty roughly +/-0.04 of image height). Their
central horizon ray is unprojected with the lens model and projected into the
rectified frame. They set pitch using
`atan((2*horizon-1)*tan(vfov/2))`. These are initial fits, **not verified same-shot poses**.
GPS/heading/SfM calibration accuracy and roll remain unverified. Distortion is corrected
using the cached lens model; it is not a claim that the SfM calibration is exact.
Position/heading/FOV/eye corrections must be based on multiple stable landmarks,
not merely on matching histogram brightness.

## Run and calibrate

From the dedicated worktree:

```powershell
# Explicit, optional metadata refresh (existing secret loader; Authorization header only):
uv run --project tools/refs python tools/refs/sbs_gate3.py fetch-intrinsics
uv run --project tools/refs python tools/refs/sbs_gate3.py prepare
pwsh scripts/sbs-gate3.ps1 -EditMode
```

The network step caches only public fields, never URLs carrying access tokens or
credentials, and downloads no photos. Offline prepare reprojects the original photos
to a pinhole view using `[focal,k1,k2]`, per the primary
[MapillaryJS camera contract](https://mapillary.github.io/mapillary-js/api/interfaces/api.CameraEnt/)
and [normalization](https://github.com/mapillary/mapillary-js/blob/main/src/geo/Transform.ts).
Normalized focal starts at `max(source_focal,0.5)` (horizontal FOV <=90 degrees for
landscape frames) and increases until every output pixel has a source sample.
It uses bilinear sampling, no invented/fill pixels, stores derivatives only under
`artifacts/sbs-gate3/rectified/`, and records original and comparison-image hashes.
Mapillary thumbnails are already upright; centered radial models are invariant to
orientation 3 (180 degrees); orientation 6/8 or unsupported projections fail explicitly.
Computed compass from the same API is preferred when available; `heading_source`
can explicitly select `original` or `computed`. The FOV of the
Unity camera equals this rectified view. Original full-frame photos are preserved.

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

With cached intrinsics, do not override render-only `horizontal_fov_deg`; change the
rectification policy together with its FOV instead. `absolute_u_m` overrides NMT+eye when necessary. Keep uncertainty visible until a
reviewer compares the actual pair. Re-run prepare after changing overrides, then
re-render; compose alone cannot update the camera image. `-ComposeOnly` regenerates
sheets from existing renders; it does not run Unity. `-Tiers Low -Lighting clear` is
a smaller render pass; the default matrix remains required for final evidence.

`horizon_y_fraction` is measured on the **original** photo. During comparison-sheet
calibration, use `rectified_horizon_y_fraction` to specify the fraction directly on
the rectified panel instead; this takes precedence and avoids applying the lens
transform twice. Mask polygons likewise refer to the comparison panels.

## Sheets and metrics

Each 960-pixel-wide sheet has photo | render, 25% grid, red horizon line, attribution,
source link and normalized 32-bin sRGB luma histograms. Metrics use rectified comparison
pixels before sheet resizing/overlays (or original pixels if no intrinsic cache).
They include full-frame luma, histogram L1 difference, sky/asphalt mean-luma and
area ratios (separate fields), and source/render hashes. These values describe the
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
and REFERENCES. CC BY-SA photo panels are rectified/cropped/resized/overlaid reference derivatives;
the render is a separate panel. Photo pixels stay outside git/build/textures.

The local set has **no coverage of the first ~300 m of G3-A**. Its 20 photos cluster
near Rondo Bieżeństwa; it must not be presented as complete segment coverage. Public
photos also do not replace the owner's same-place photos/approval in docs/03.

## Delivered evidence and calibration

Final output: `artifacts/sbs-gate3/sheets/{Low,High}-{overcast,clear}/`, 40 pairs each;
matching `metrics.json`, raw render/stat groups, `SUMMARY.json`, overview contacts
under `review/`, and `VISUAL-REVIEW.md`. Original round is retained under `r0/`.
The final two calibration rounds rerender only proven changed poses (exact pose
diff assertions), retaining the other identical-pose frames; stats-r2/r3 supersede
the affected entries in the original aspect-group stats. A full wrapper run from
the committed final JSON reproduces all final cameras without the incremental steps.

Eight photos were visibly taken from bridge decks: seven at Bieżeństwa
(`1406533339711789`, `223210302566110`, `309664504075286`, `2948595898752384`,
`454716650857984`, `303305168125936`, `320215796381417`) and one at Putry
(`494288258686575`). Bare-earth NMT put them below the deck. Their authored U uses
existing generated deck stations or an existing bridge-road asphalt ray hit, plus
nominal 1.7 m eye; the world geometry is unchanged. The lane correction for
`454716650857984` moves its original GPS 2.95 m SW from the rail into the right lane.

Representative original/SfM coordinate and heading probes were rendered and viewed
(`probe-sheet-*.jpg`). Original GPS fits the close richlv sequence better than its
SfM translations; explicit per-image deltas retain this choice. SfM optical heading
is retained for the oblique richlv images; the original travel compass is not a
substitute for optical heading. Frame `1406533339711789` instead uses its original
300.8-degree compass: SfM's 187.8 degrees conflicts with the road/sunset framing.
API `computed_altitude` values around 2–5 in this set are not used as absolute NMT
altitudes. GPS, nominal eye height, road-height model, horizon and roll retain
WORKING_VALUE uncertainty; no camera is advertised as survey-grade ground truth.

All 160 frames and sheets were decoded and render hashes/metadata checked. Overview
contacts of all four states and selected full sheets were viewed; self-review is
explicitly not an independent visual-critic review. Existing EditMode: 226/226 passed;
GIS/refs details are in REPORT. Independent review and owner gate acceptance remain.

No world/runtime/shader/material changes; new cameras are loaded only by the editor
command, not copied into runtime Resources or saved into a scene. Runtime draw/GPU
delta is zero by construction; this is **not a new device measurement**. Raw
SceneStats estimates and separate instanced estimates are preserved, not equated
to GPU counters. Changing camera pose changes visible-content estimates and cannot
be interpreted as a runtime regression between r0 and the final camera.
Expected merge conflicts: additive tail sections in LICENSES/REFERENCES only; new
SBS files do not modify cameras or world files owned by other streams.
