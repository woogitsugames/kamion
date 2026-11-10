# ADR 0021 — Vehicle look: clear coat, own reflection capture, contact shadows, cab local shadow lift

Status: Accepted (rendering-perf), 2026-11-09. Review: `docs/reports/visual/REVIEW-2026-11-09-r3.md` E1–E3,
`REVIEW-2026-11-09-r4.md` E-N1, L1–L3. Frames: `docs/reports/visual/truck-A8/`.

## Context
- TRAKT paint read as matte grey plastic, the windscreen as clear aquarium glass, and the combination "hung" over the
  asphalt (no contact shadow, P0 in r4). In the cab view 24–42 % of the frame was below 3 % (crushed black, P0 in r4).
- Realtime reflection probes are disabled in the quality settings (ProjectSettings, lead only) and URP Complex Lit
  would double the paint shader's variants and cost.

## Decision
1. **Clear coat in `Kamion/Truck Exterior`** (paint slot only): second GGX dielectric layer, F0 0.04, roughness 0.08 over
   a 0.36 base; base × (1 − Fc) + env × Fc + coat sun highlight; dust removes the coat. Tier switch `clearCoat`.
2. **Own reflection capture** (`VehicleReflectionCapture`) instead of realtime probes: a camera of type Reflection
   (WorldInstances skips it: no instanced forest in the capture) renders one cube face every `envCaptureInterval`
   frames into a 128 px half-float cube (box-filtered mips) that a Custom-mode reflection probe around the combination
   uses. High only (`envCaptureSize`); Low/Medium keep the analytic sky + ground cubemap (static, zero cost). No
   ProjectSettings change.
3. **Contact shadow** (`ContactShadowCaster`, `Kamion/Contact Shadow`): a ray-cast ground patch per vehicle (body slabs
   + wheel blobs), occlusion = product of the 2D strip view factors at the underside height (× 0.6 for the sides closed by
   wheels and tanks), applied to the ambient share only (sky SH vs sun × shadow map at the pixel). One draw per vehicle,
   all tiers (`contactShadows`).
4. **Cab view local shadow lift**: gain 1 + k (k0/(Y + k0))³ (k 8, k0 0.004) on interior and exterior pixels only while
   the camera is in the cab, + cab enclosure 0.6 on the interior SH and +1.0 EV cab-view exposure. A global curve change
   would also lift the outdoor scene (ADR 0016 keeps that calibrated).
5. **Dusk street lamps**: lamp-glass emission from the sun elevation, nearest-lamp point lights on High (`streetLights`).

## Measured
- S24+ High, WorldC `truck-34` overcast, uncapped, same APK (`rq_a8=0` vs default): GPU p50 within thermal noise
  (8.64 cold / 10.00 warm off vs 9.73 on, capture off 9.63); CPU main +0.5 ms with the capture (first version with the
  instanced forest in every face: +4 ms, fixed by the Reflection camera type).
- A16 Low: see `docs/PERFORMANCE_BUDGETS.md` (A8).
- Editor High overcast: ground under the front bumper 12 % vs asphalt 31 % display (≈ 13 % linear, r4 target ≤ 25 %);
  cab-dash < 3 %: 19.2 → 1.4 %, p10 1.6 → 6.2 %.

## Consequences
- All constants are WORKING_VALUE until compared with owner photos.
- The capture has no shadows and no instanced props/trees; in a forest the reflections show sky where trees would be.
- The world generator's lamp glass quad faces up; the glass is drawn double-sided until world-builder flips it.

## Amendment 2026-11-10 (r4 E2, glass)
- `Kamion/Truck Glass` is a thin pane, not one interface: reflectance R2 = 2R/(1+R) from Schlick F0 0.04 (0.08 at normal
  incidence, ~0.1 at a 3/4 view, ~0.3 at 70 deg) on the capture (High) or sky cubemap (Low/Medium); transmittance
  (1 − R2) · (1 − _Opacity)^(1/cos θt) (n 1.52), so the interior darkens towards grazing angles. From the cab only the
  first surface carries the analytic dash reflection (no ghost) and the tint body term is off (no milky veil). Cost
  ~14 ALU per glass pixel, no texture, all tiers.
- Measured (editor, truck-34 overcast, windscreen median / sky median, display): High 0.402 → 0.411, Low 0.395 → 0.405,
  lowsun 0.344 → 0.372. A dielectric pane cannot reach "≥ 60 % of the sky" (r5) at a 3/4 view: that needs R2 ≈ 0.3
  (≥ 70 deg incidence). What remains is interior radiance seen from outside (cab SH share / fill) and the clipped sky
  (display 1.0), both outside the glass shader. WORKING_VALUE until compared with owner photos.

## Amendment 2026-11-10 (review r5 E-N1: contact shadow too weak on phones)
- **Bug:** `Kamion/Contact Shadow` ran in `Transparent-50`; `Mobile_Renderer` has transparent receive shadows off, so URP
  turned the main-light shadow keywords off for that pass, the shadow map was never sampled and the sun under the truck
  counted as unshadowed (ambient share << 1). Fix: queue `Geometry+499` (end of the opaque pass, same single draw).
  Editor High lowsun A/B, ground / adjacent asphalt (sRGB display): under bumper 60 → 32 %, under frame 49 → 21 %.
- **Edit-mode QA ground:** the wheel-plane fallback sat up to ~10 cm off the rendered road (trailer patch hidden under the
  asphalt). `VisualQaRunner` now cooks the world colliders like the player (`WorldCollisionCooker.Cook`), so the QA frames
  ray-cast like the phone; the fallback plane uses the lowest tyre renderer points. The vertex shader adds an 8 cm
  view-ray depth bias (the patch can still sit a few cm under the road mesh).
- **Enclosure:** occluder grows by `sideClosure` × h on each side (1.0, WORKING_VALUE: wheels, tanks, steps and bumper close
  the sides of the gap); wheel blob `wheelContactHeight` 0.05 m (was 0.18) and half contact length 0.3 × radius (was 0.45),
  i.e. a tight dark core at the tyre patch. Renamed fields, so the old serialized values in the prefab are ignored.
- Editor `truck-34` overcast after the fix (ground / adjacent asphalt, display): Low 34 / 27 / 25 % (bumper / frame / front
  tyre), Medium 35 / 29 / 28 %, High 35 / 29 / 28 %; under the trailer front 51–57 %. Phone numbers: pending (no device run).
- Cost: same draw count; +1 hard shadow-map tap (Low: no soft shadows) per patch pixel and a slightly larger patch
  (margin + h). Phone GPU delta not measured yet (UNVERIFIED, expected well under 0.1 ms on A16 Low).

## Addendum r7 (2026-11-10): the capture was a no-op until ADR 0056
The capture faces rendered without a depth buffer (skybox only) and the Custom ReflectionProbe never reached the truck
shaders. Both are fixed in ADR 0056 (2D face RT with depth + global `_KamionVehicleEnvCube`, no probe). The A8 numbers
above therefore measured a sky-only capture. All tiers now have a capture (Low/Medium 64 px, sparse, idle when parked).
