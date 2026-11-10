# ADR 0044 — Cab interior legibility at phone resolution (shader side)

Status: Proposed (truck-artist), 2026-11-10. Needs visual-critic review and an A16 run. Extends the A6 shader contract
(`cab_interior_manifest.json` "shader_contract"); the manifest formula is now a lower bound, not the exact shader.

## Context
The authored grain, switch polish and wear did not read in the Unity `cab-dash` frame at 2340x1080 (Low renders 1755x810):
switch legends (10-13 mm, ~8-12 px) vanished under the 0.5 alpha clip of the mip-averaged icon atlas, wear was a +/-10 %
vertex gradient, panel gaps had the brightness of their panels in direct light (AO is ambient-only in URP), and nothing
in the cab reflects the bright glazing, so leather read as matte plastic.

## Decision (`Kamion/Cab Interior`, uniforms and vertex data only, no new sample, keyword, pass or material property)
1. Legend band of the decal atlas (uv0.y < 0.5): alpha clip 0.16, albedo x1.45, AO floor 0.8.
2. Wear: shaped term wk = sat(2.4 w (0.55 + 0.9 R)), albedo +1.3 wk, roughness -0.3 wk (floor 0.08); detail roughness
   amplitude 0.4 -> 0.6.
3. Deep AO (< 0.28) darkens the albedo down to 0.4: gaps and creases stay dark in direct light.
4. Grazing sheen: bakedGI * (1-NdotV)^3 * s (0.4 + s) * 3 * AO, non-metals.
All constants WORKING_VALUE (no owner cab photos yet).

## Measured (editor, WorldC, cab-dash, RTX 5070, 20 renders; not a phone number)
Low 1755x810: overcast 2.25 -> 2.20 ms, low sun 2.35 -> 1.91 ms (within noise). About 20 ALU more per interior pixel.
A16: UNVERIFIED.

## Open
- Wheel-rim, gear-selector and seat-bolster wear still do not read in `cab-dash`: the exported wear (uv2.x) on those
  parts is too small or absent; needs a generator pass (`WEAR_MUL`, wear painting in `build_interior.py`) and a LOD0
  re-export.
- Door pull and floor-mat heel area are outside the `cab-dash` frame.
- The sheen slightly greys the koniak leather panel at low sun on Low.
Evidence: `docs/reports/visual/interior-legibility/ba-<tier>-<lighting>.jpg` (top before, bottom after).

## Addendum 2026-11-10 (touch-point wear pass r4, truck-artist) - needs visual-critic review
Finding: the "Open" item above was not a generator gap. The exported wear reaches the shader (uv2.x up to 0.36 on the
rim, 0.87 on the seat; checked on the imported Unity meshes), but black parts (tint < ~0.1: rim, stalks, knobs,
keys) sit on the plateau of the local shadow lift (Y * gain is almost flat under the knee): raising the rim wear
0.36 -> 0.66, adding wear to the selector / park-brake knob, and even a x2.2 gain before the lift changed `cab-dash`
by 0-2 /255 (before/after diff).
A multiplier after the lift (x1.9) did nothing either: the lit value of these parts is close to zero.
Decision: 5. `wearGloss = wk * (1 - sat(8 * mean(tint)))`, colour `+= bakedGI * ao * 4.5 * wearGloss` AFTER the shadow
lift (a phone's local tone mapping keeps local contrast; a hand-polished black surface mirrors the glazing; scales with
the cab ambient, so it does not glow at dusk; no new sample, ~5 ALU). WORKING_VALUE, A16: UNVERIFIED. Follow-up for
rendering-perf: the lift flattens all detail under the knee (black parts carry no shading of their own).
Generator side (same pass): `WEAR_MUL` rim 1.6 -> 2.1, door pull 1.7 -> 2.0, armrest 1.6 -> 1.9, new `knob` 1.4 and
`dash_lower` 1.45; wear painted on the AMT selector / stalk ends, park-brake knob, light rotary, knee bolster, kick
edge, door-card kick zone, bolster creases, elbow spot. A-pillar foot / kick panel closes the light wedge at the dash
end. Sleeper privacy curtain on a ceiling track and a third-drawn passenger door curtain (never ahead of the driver's
shoulder line) against the see-through cab from outside.
Evidence: `docs/reports/visual/interior-wear/`.

## Addendum 2026-11-10 r6 (rendering-perf, review r6 C-N5/C-N6/C-N7) - supersedes decisions 4 and 5; needs visual-critic review
Root causes (measured, editor, rim = mask of `STEERING_WHEEL_LOD0:MI_Cab_Leather`, `-qaMask`):
- **Rim AO 0.02 on every tier.** The rim rotates (`NO_AO`) and samples the cloth block of the AO atlas, filled with the
  *median* of the bake: ~45 % of covered texels are fully occluded faces (p10 = 0), so the median was 0.04 (8-bit 5-6).
  Ambient, fill and reflections of the rim x 0.02, albedo x 0.4 (deep-AO darkening): black in shade, lit by the warm sun
  only. This, not the lift plateau, is why the r4 wear polish (`* ao`) did not read.
- **Cab gain on the direct sun.** `_CabGain` (2^(1 + meter), 5.66 at low sun) multiplied the sun patches too; isolation
  render with gain/lift off: rim lit R-B 15 -> 7 %, wear off: no change (wear is not the colour source).
- **Grazing sheen (up to 3.5x bakedGI) and wear polish (4.5x bakedGI)** reflected more than the surface receives.
Decision: (a) cloth block = *mean* cab ambient (a6_export; `ao_cloth_block.py` re-levels the exported atlases, LOD0
0.024 -> 0.150, no re-bake); (b) shader: URP PBR split, `col = sun * tau_glass + indirect * _CabGain` (the gain is the
phone's local tone mapping of the shade; sun patches are metered by the scene exposure), sun x glass transmittance
(`_CabFill.w`, the glass casts no shadow); indirect specular = URP EnvironmentBRDF x AO; sheen and wear polish removed;
black parts (tint < ~0.1) keep albedo <= 0.05 when worn (gloss only); (c) fill sky part in `SkyModel.AdaptedWhite`.
Measured (cab-dash, rim p50 / lit-third sat / R-B / p99:p50; HEAD assets rebuilt -> after):
Low overcast 9.8 -> 14.1 %, High 11.0 -> 16.1 % (diff 2.0); lowsun Low sat 33.4 -> 18.1 %, R-B 12.2 -> 3.4 %, 3.18 -> 1.93;
High 30.5 -> 18.9 %, 13.2 -> 4.2 %, 3.67 -> 2.12. Editor GPU Low 1755x810: 1.78-1.86 / 1.90-2.14 ms vs 1.78 / 1.90 (noise).
A16: UNVERIFIED. Open: lowsun sat 18-19 % > 15 % target - the sunlit share has the sun colour of LP_LowSun (sunlit grey
hall wall in the same frame 17-22 %), below that needs a WB / sun-colour decision (ADR 0043, D27); Low dusk black < 3 %
5.8 -> 8.4 % (deep shade lost the non-physical sheen; High 1.8 %); C-N7 white L = exterior `CAB_Body_LOD0:MI_Ext_Lights`
(headlamp DRL guide, emissive) seen through a gap in the passenger-side lower front of the interior - exterior/interior
geometry (truck-artist). Evidence: `artifacts/truck-interior/r6-wheel/`.

## Addendum r7 (2026-11-10, rendering-perf): cab-view display parity on Low
Measured (cab-dash, editor, share of pixels < 3 % luma / p50): Low dusk 8.7 % / 13.9 vs High 2.1 % / 15.5. High with
post-processing off (`-qaRq rq_post=0`): 9.5 % / 13.6, with the vehicle capture off: unchanged 2.1 %. So the gap is the
display transfer, not the light: High maps the scene through the D23 master curve (black floor 1.5 %, 0.0025 -> 3.8 %,
0.01 -> 11.5 %, 0.18 -> 48.4 %), Low has no LUT and writes plain sRGB (0 %, 3.2 %, 10.0 %, 46.1 %).
Decision: in the cab view on tiers without post-processing, the cab shaders (CabInterior, TruckExterior cab-view parts,
CabDisplay) write the linear value whose plain sRGB equals the D23 display: c' = c (1 + a k / (c + k)) + f k2 / (c + k2)
per channel (`KamionToeParity.hlsl`, `LookGrading.NoPostToeParity` = 0.21129, 0.206849, 0.001319, 0.000598, least-squares
fit to the master curve, <= 0.45 display points for c <= 0.2; EditMode `CabToeParityTests`). Set by CabInteriorLighting
only when the camera is in the cab and the tier has no post (`toeParity`, default on); identity everywhere else. No light
is added: it is the same tone curve the phone-look tiers already apply. The non-physical sheen stays removed (r6).
Result Low (before -> after; High): dusk 8.7 -> 4.8 % / 13.9 -> 15.0 (2.1 % / 15.5), overcast 5.0 -> 2.4 % / 20.0 -> 21.6
(1.8 % / 22.1), lowsun 2.0 % / 16.9 (1.8 % / 17.5), clear 3.9 -> 1.8 %. Cost: ~12 ALU per cab pixel; editor Low 1755x810
cab-dash 5.21 -> 4.94 ms (noise). A16 not measured. The world outside the cab on Low keeps plain sRGB (10-25 % darker
in linear than High in the toe and mids): a global Low LUT would cost a full-screen pass, not done.
