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
