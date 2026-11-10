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
