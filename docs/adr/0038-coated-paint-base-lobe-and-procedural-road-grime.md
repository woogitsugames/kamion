# ADR 0038: Coated paint base lobe, orange peel, procedural road grime

Status: Accepted (rendering-perf), 2026-11-10. Review: `docs/reports/visual/REVIEW-2026-11-09-r4.md` E1 (paint like
grey plastic) and E4 (truck sterile clean). Builds on ADR 0021. Frames: `docs/reports/visual/truck-E1E4/`.

## Verified before the change (editor, WorldC `truck-34`, High)
- E1: the coat from ADR 0021 was active. The "plastic" look came from the **base** lobe: GGX at roughness 0.36 with
  F0 0.04 under the coat. It gives a broad soft sheen, which is what plastic looks like. The trailer curtain (a tinted
  `_IsPaint` slot) also got the full clear coat (`_ClearCoat` default 1), so at low sun it shone like a lacquered panel.
- E4: the only dirt was the baked `M.g` mask × `_Dirt` 0.5. Nothing tied it to the ground or the wheels.

## Decision
1. **Coated base lobe**: under the coat, base roughness = max(roughness, `_CoatedBaseRoughness` 0.6) × coat mask. The
   gloss comes only from the coat (F0 0.04, roughness 0.08).
2. **Orange peel**: three crossed ripples with a wavelength of about 6 mm in the vehicle frame, tilting the coat normal
   (slope `_OrangePeel` 0.012). When a ripple is smaller than a pixel it fades out and goes into the coat roughness
   instead (no aliasing). At game distances this is effectively a slight haze.
3. **Coat horizon occlusion**: a reflection vector below the geometric surface gets `saturate(1 + 1.2 R·Ng)²`.
4. **No metallic flake**: fleet white is a solid paint (manifest `liveries.white`, `_Flake` 0).
5. **Curtain without lacquer**: `_ClearCoat` 0 on `MI_Trl_Curtain` (`TrailerAssetBuilder`).
6. **Procedural road grime**: `ContactShadowCaster` (one per vehicle) publishes its vehicle frame and up to 4 axles
   (forward offset, wheel-centre height, radius) into global arrays `_KamionGrime*`:
   - The frame's origin is the mean wheel-contact point, with the axes of the vehicle root.
   - The vehicle's MeshRenderers get the slot via `MeshRenderer.SetShaderUserValue` (read in the shader as
     `unity_RendererUserValue`). This is compatible with the SRP batcher: no property blocks.
   - Coverage = saturate(1.8 × `_Dirt` × max(0.8 × baked M.g, procedural)).
   - The procedural part has a solid band up to 0.4 × edge, where edge = `_GrimeHeight` 0.8 m ± 25 % with wavy noise.
     A dust film reaches 2 × edge.
   - Wheel-arch spray rings sit around each axle, wider and stronger behind the wheel. Vertical streak noise fades
     out below a pixel.
   - Cavities hold more grime (× 1.4 at AO 0, × 0.85 on open panels). Non-paint slots get × `_GrimeChassis` 1.3.
   - Tyres and rims (rendering layers 8/9) get radial dust, which does not depend on rotation.
   - `_Dirt` 0–1 is still the gameplay parameter.
7. **Tier switch**: `QualityProfile.vehicleGrimeDetail` (all tiers on) sets the global `_KamionGrimeDetailOff`. When off,
   only the height band is drawn, with no arch loop or streak noise. `rq_a8=0` also turns it off.

## Measured
- Editor, Low, WorldC `truck-34` overcast, 120 timed renders: 3.12 / 3.32 ms with the change. With `rq_a8=0` (clear
  coat, grime detail and contact shadows all off) it was 3.05 ms. Delta ≤ 0.3 ms, which is at the run-to-run noise
  level (before: 4.35 ms in a cold run). **Not a phone number**: the A16 Low delta is still to be measured
  (`device-metrics.ps1` with and without `rq_a8=0`).
- Pixel means, High overcast, before → after: door bottom behind the front wheel 170 → 163 sRGB, tyre 96 → 89.
  The curtain is darker and matte at low sun.

## Consequences
- The generated materials are outside git. The new parameters are explicit in both builders. Existing
  `_Generated/**/*.mat` need a builder rerun (or the same values set by hand) to pick them up, because a missing
  float reads as 0 in batchmode, not as the shader default.
- E1 is only partly solved. The plastic sheen and the shiny curtain are gone. On a white solid paint, a physically
  correct coat reflection is small (Fc 0.04–0.1 against a diffuse of ~0.47 × sky). The reviewer has to judge whether
  the horizon reflection on the doors now reads. If not, the next lever is the reflection content (capture/box
  projection, lighting owner), not a bigger F0.
- All constants are WORKING_VALUE until compared with owner photos of a fleet truck after a wet week.

## Addendum r6 (2026-11-10): coat lobe width, analytic ground, fp16 GGX, curtain soiling (review r6 E1, T-N1)
- **Coat lobe.** The orange-peel term added `4 * slope` to the *perceptual* roughness squared (alpha 0.054, a satin coat
  that blurred horizon and ground into one grey). Now three crossed ripples of slope s give an RMS slope ~1.22 s, i.e.
  GGX alpha ~1.75 s, added in quadrature to the coat alpha (alpha ~0.022 when the ripple is sub-pixel).
- **Ground in the reflection (Low/Medium).** `KamionVehicleEnv.hlsl`: below the horizon the coat (and the glass) see an
  analytic ground plane from the point's height above the road (vehicle frame), hazed by the scene fog over the hit
  distance, instead of the direction-only SkyModel cube that fades from horizon colour to ground over ~15 deg. High/Ultra
  keep the vehicle capture (`_KamionVehicleCapture = 1`), which already holds the real ground. Cost: one extra cube
  sample + ~15 ALU per coat / glass pixel on Low/Medium (rides on the `clearCoat` tier switch for paint); phone cost
  UNVERIFIED.
- **fp16 GGX bug.** `CoatDirect` evaluated `NoH^2 (a2 - 1) + 1` in half: at alpha^2 ~ 4e-5 it cancels to ~0 and the peak
  overflows fp16 -> inf/NaN = black blotches on the sun-grazed cab side and curtain top at low sun (already speckled at
  HEAD, solid once the coat got sharper). Now float, `1 - NoH^2 (1 - a2)`, alpha floor 0.01 (sun disc as an area light),
  clamp 2048. Same fix in `Kamion/Truck Glass`. On phone GPUs half is real fp16, so this matters more on device.
  Side effect: the inflated low-sun glare is gone (High lowsun door max 92 -> 86 %, curtain mid 68 -> 61 %).
- **Curtain (T-N1).** The baked M.g of the curtain atlas held a blotchy patch on the rear third ("mould"). The curtain
  material now ignores it (`_CurtainGrime.x = 1`) and uses a low-frequency model in the trailer object frame: tyre spray
  band 0.3-0.5 m above the curtain bottom (undulating top edge >= 1.5 m wavelength, densest 0.9 m behind each axle and
  from the bogie to the rear), wake film over the rear 1.3 m, runoff streaks below the roof rail at posts every 3.4 m
  (energy-preserving below a pixel). Values WORKING_VALUE (`TrailerAssetBuilder`, axles/floor from dims.json).
- **Measured (editor, truck-34 1024 px, before -> after):** curtain middle (1.7-2.6 m) cell deviation after removing the
  smooth view-angle gradient 5.7-9.0 -> 1.6-4.0 pts; bottom 0.4 m darker than middle by 3.2/4.2 -> 8.9/9.1 pts (Low/High
  overcast), 14-16 at low sun; dark clusters > 3x3 px below 50 % of the local mean: 0 (low sun before the fp16 fix: 2).
  Door vertical profile (x 512-535, y 218-262) max - min: 3.1/5.3 -> 2.8/5.3 pts overcast. **E1's >= 15 pts is not met
  and is not reachable physically in this frame**: the camera is at 2.1 m, i.e. at the belt line, so the whole door
  panel below it reflects ground (the horizon reflection sits under the window seal), and at the 60 deg view the coat
  Fresnel is ~0.07: 0.07 x (horizon - ground) ~ 2-3 pts on a white solid paint. Raising it would need a non-physical F0.
  The lacquer now reads where the horizon crosses curved panels (cab corners, roof deflector); a dark livery or a lower
  camera shows it more. Evidence: `artifacts/owner/modern-front/r6-shading/{before,after,compare}/`.