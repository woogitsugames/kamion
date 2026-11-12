# ADR 0141 — Map edge and background: far skyline beyond the Low far plane, road closures in render groups

Status: implemented on branch `edge-r6c` (base main `76c88d4fd`, main `611f116c9` merged in, 2026-11-12, s13); not merged.
A visual-critic review is still required; the D51 notes below are the author's. Phone: NOT measured (see Risks).
Source: ADR 0129 open point "kominy EC poza far clip Low (1187 m > 900 m)", ADR 0126 open point "kominy EC za
pierzeją", GPT handover `edge-r6` (B9 skyline, closures), ADR 0082 / 0085 / 0121 (map edge, far-field), ADR 0116 (EC stacks).

## Context

1. **Skyline.** The Low tier has a 900 m far plane. In four G3-B photo frames (Mapillary 3281350541967811,
   150280503737744, 297817221966185, 1528935774382039; CC BY-SA 4.0, reference only) the two red/white EC Białystok
   stacks stand 1251–1475 m from the camera (`artifacts/edge-r6c/skyline_probe.py`), so on Low they were cut by the
   far plane and the horizon behind the trade frontage was empty. The same applies to the tall blocks of the far-field
   ring seen from the DK8 viaduct: the whole western far-field sector is beyond 900 m.
2. **Closures.** The 36 road closures at the region edge were one renderer each with 4 materials (4 draws per
   closure) and a single U-20 board without a sign.
3. Diagnosed and **not** changed here: in SBS 303305168125936 the 48–56 m blocks (elevation +2.5..+3.7°, 645–741 m)
   are hidden by the BDOT forest `2BE4B432-6BC0` (pines 21–23 m at 160–240 m, elevation +4.4..+5.8°), i.e. by
   region vegetation, not by the far-field; the pose of that frame also has ~11° heading error.

## Decision

1. **Generator** (`tools/worldgen/streetscape/far_field.py`): a separate glTF node `far_skyline` in both far-field
   tiers. It receives, with unchanged geometry, ring buildings with source height >= 24 m (block / office / hall) and
   ring chimneys >= 40 m (both thresholds WORKING_VALUE: 24 m at 900 m is 1.5° above the horizon). A ring chimney
   within 25 m of a region landmark stack (`overrides.yaml kind=landmark` + `ec_chimneys.json`) is dropped and
   replaced by a plain banded cone with the stack's source height, diameters and band limits ("stand-in"). No
   position or height is invented. The flag travels in `TEXCOORD_1.x`: `-(x + 16)` = "clamp" (visible at any
   distance), `-(x + 4096)` = "beyond" (visible only behind the far plane). Triangles are sorted far-to-near.
2. **Shader** (`WorldSurface.shader`, only under `_FAR_FACADE`, i.e. only `M_far_field_buildings`; ForwardLit and
   DepthOnly): `KamionFarSkyline` changes clip-space z only. Screen position, perspective size and fog distance stay
   true. "clamp" vertices farther than `far - 40 m` are held 40..30 m in front of the far plane and at least
   4e-6 NDC in front of it (the URP skybox is drawn ~1e-6 NDC in front of the far plane; measured in the editor:
   3–6 m = 3.7e-7 NDC was overwritten by the sky). "beyond" is the exact complement of the far-plane clip, so the
   stand-in appears where the region's hero mesh is cut and the two never overlap. Orthographic cameras: unchanged /
   no stand-in. The far plane, fog and every other material are untouched.
3. **Import** (`WorldEdgeBuilder.BuildFarField`): renderer `WorldEdge/FarSkyline`, bounds = whole tile, no shadows.
4. **Closures** (`WorldEdgeBuilder`): colliders stay one box per closure. The visible part is clustered by single
   linkage at 150 m (WORKING_VALUE) into render groups, one mesh per group with 2 materials (concrete barriers;
   paint as linear vertex colour on the far-field paint material): 2 draws per group instead of 4 per closure.
   Each closure: concrete barrier row (2.0 m elements, 0.60 / 0.20 / 0.81 m), in front of it a double U-20 board
   (0.25 m boards, 0.5 m red/white fields as ADR 0082; 0.20 m gap and 1.20 m top edge WORKING_VALUE) and, on
   carriageways >= 5.5 m, a B-1 disc (0.90 m, rim 0.09 m, centre 1.85 m: WORKING_VALUE).

## Validation

Run on the branch after `git merge main` (`611f116c9`, no conflicts) and a full regeneration.

- `build_world.py`: 615 s, exit 0. Far-field Low 24500 -> 24548 tris (skyline node 2024), High 118524 -> 118588
  (skyline 5296); stand-ins: `ec-bialystok-chimney-1`, `ec-bialystok-chimney-2` (`far_field_qa.json`).
- Closures: 36 closures in 6 render groups, 8588 tris (rebuild log).
- `pytest tests/gis tests/gate3` (heavy slot, 14 min): 845 passed, 1 xfailed, 1 failed =
  `test_road_fidelity::test_report_not_stale` (the report on main is stale after the CRLF hash fix `a4cb9995`);
  after `fidelity/run.py` (exit 0, report committed) `tests/gis/test_road_fidelity.py`: 9 passed, 1 xfailed.
  New: `tests/gis/test_far_field.py` skyline cases (55 passed in the far-field files).
- EditMode: @@EDITMODE@@
- import-region: @@IMPORT@@
- Budget, Low, 120 cameras (control + gate3 + 42 SBS), `artifacts/edge-r6c/stats-diff.py`:

| Run | draws (min / median / max) | shadow casters (sum) | trisK (sum) |
|---|---|---|---|
| after vs baseline (same base main `76c88d4fd`, clean A/B) | -51 / -13 / +3 | 0 | +116 of 33055 (+0.35 %) |
| merged vs baseline (also contains main `76c88d4fd..611f116c9`) | @@MERGED@@ |

  The +1..+3 draws are the skyline renderer; the savings are the closure groups. Budget not worsened.
- Pairs (photo | before | after for SBS frames, before over after for control cameras), 960 px:
  `artifacts/edge-r6c/pairs/{Low-clear,Low-overcast}/*.jpg` (101 + 101), merged run:
  `artifacts/edge-r6c/pairs-merged/`; full-resolution horizon crops `artifacts/edge-r6c/crops/`.

### D51 (author's notes; visual-critic pending)

- 297817, 3281350, 150280, 1528935 (Low, clear and overcast): both EC stacks now stand on the horizon behind the
  frontage, red/white bands readable, in the direction where the photos show them; before: empty sky. This closes
  the open point of ADR 0129 on Low.
- 150280: the stacks in the render are visibly smaller and further left than on the photo (crop
  `crops/z150280.jpg`). Position and height come from source data, so this is the SBS pose / FOV of that frame, not
  the skyline; not corrected here.
- `edge-*`, `dk8-dk19-exit`: closures read as a closed road (double board + B-1) instead of a bare striped plank.
- Not done: haze on the stacks is the ordinary distance fog of the tier; at 1.3–1.5 km on Low-clear they are a
  little crisper than on the photos (owner / critic call).

## Risks / open

1. **GLES / Vulkan on the phone: UNVERIFIED.** The skyline depth sits 4e-6 NDC in front of the far plane. On a
   24-bit or 16-bit depth buffer, or with a non-reversed z (GLES3), the skyline can lose against the skybox or
   z-fight with it. `KamionNdcInFrontOfFar` has a non-reversed branch (`1 - 8e-6`) that was never executed on a
   device. To check on A16 during integration (Low, frame 297817 / route G3-B): stacks visible, no flicker; if not,
   raise the two constants or draw the skyline renderer after the skybox.
2. Beyond the far plane all skyline objects share almost one depth; ordering relies on the far-to-near index order
   inside one mesh. Region geometry closer than the far plane always wins (correct).
3. Thresholds 24 m / 40 m / 150 m link distance and the sign dimensions are WORKING_VALUE.
4. Known, not from this branch: 2 EditMode failures in `CarPaintMaterialTests` (present on main).
5. `docs/adr/README.md` index not regenerated here (`tools/docs/adr_index.py`, leader).
