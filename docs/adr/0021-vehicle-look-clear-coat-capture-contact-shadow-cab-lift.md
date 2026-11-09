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
