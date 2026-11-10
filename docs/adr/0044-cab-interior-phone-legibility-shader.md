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
