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
## Addendum 2026-11-10 r6b (truck-artist, review r6 C-N7 / C-R2) - geometry and vertex data only, shader untouched; needs visual-critic review
Frames: `artifacts/owner/modern-front/r6b/` (`before` = main bb7549d, `v1` = first pass, `after` = final; `measure.py`,
`rimprof.py`, `leak.py`; cab-dash, 1024 px space, editor).
- **C-N7 was not a gap.** The headlamp bucket of the modern front reaches up to 75 mm inside the fitted interior wall in
  the lower front corners (shell wall 30 mm; lamp plan radius 0.286 m about the corner centre vs the trim's 0.346 m, x
  0.87-1.2, z up to 1.545 m), so the emissive DRL guide stood inside the cab: 720 of the sampled lamp points were in
  direct sight of the eye (`leak.py`). Fix: `footwell_wall_cnr_{s}` in `build_interior.build_shell`, a quarter-round
  kick moulding (plan radius 0.262 m, floor to 1.60 m, both sides; one band + cap at LOD2). Lamp points in sight: 720
  -> 0 (LOD0 / 1 / 2). Pixels > 70 % in 860-1024 x 300-473: High / Low overcast 113 / 107 -> 0 / 0 (max 30.6 / 29.0 %),
  lowsun 0 / 0. `check_fit.py` PASS (36 vertices behind a lamp pocket = 0.15 %, limit 0.2 %; 0 in the glass zone).
- **C-R2, authored zones (no noise).** New per-vertex attributes `tint_add` / `rough_add` (`set_attr_w`) go into the
  vertex colour in `a6_export.consolidate` (contract unchanged). Dash top: dust film towards the windscreen base,
  thicker in the corners (tint x up to 1.6 = albedo ~0.07: a film, not wear of the black pad; WORKING_VALUE), wiped /
  polished front lip in three reach zones (roughness -0.42, tint x 0.88), twin-needle seam 38 mm behind the lip (decal
  strip, dropped at LOD2). Rim: two hand patches (10 / 2 o'clock to the thumb rests) + a lighter one at 12, weighted to
  the palm side of the section, replace the two gaussians x per-vertex hash; `WEAR_MUL` rim 2.1 -> 2.5, knob 1.4 ->
  1.8; seat: one shaped patch on the door-side bolster (hash and sine "creases" removed), backrest bolster 0.7 -> 0.85.
  Black parts (mean tint < 0.04): worn spots get tint x (1 - 0.3 w) so the shader's worn albedo stays ~0.05.
- **Measured.** Plastic pixels (mask `CAB_Interior:MI_Cab_Plastic`) in 640-1000 x 190-300: luminance std High / Low
  overcast 10.8 / 10.1 -> 11.5 / 10.8 points of 255 (the >= 3 target was already met by the two mouldings; the flat top
  itself moved by +-5 points locally). Rim (mask, 15 deg sectors): worn 43 vs unworn 37-38 of 255 before and after
  (12 o'clock patch 37 -> 41); rim p50 16.1 / 14.1 % unchanged (C-N6 holds), p99 : p50 1.59 -> 1.73.
- **Open (C-R2 not closed).** With the r6 shader the wear of a black part is worth ~+5 / 255 (+13 %) in overcast,
  whatever the mask: albedo capped at 0.05 and the shade is specular + lift dominated. The patches have a shape now but
  do not read at 1024 px; more needs a shader decision (rendering-perf), e.g. the cap or a bounded probe term on worn
  spots. 0.5-1 mm grain: the detail sets already are 0.5 mm (rim), 0.7 mm (dash), 1.25 mm (seat leather) cells; at
  1024 px one pixel on the dash is ~0.9 mm, so the grain is sub-pixel there by construction. No control camera sees
  the driver's seat bolster or the stitched seam at readable size: UNVERIFIED in frame. Interior LOD0 / 1 / 2:
  97 103 / 43 329 / 21 984 (was 96 811 / 43 128 / 21 960; LOD2 limit 22 000), `interior/check_export.py` PASS.


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

## Addendum r8 (2026-11-10, rendering-perf): worn black leather - neutral grey lift + glossy polish (supersedes the r6 black wear cap 0.05); needs visual-critic review
HANDOVER open point / r6b "Open (C-R2 not closed)": rim and seat wear invisible under the r6 cap (worn albedo of black
parts <= 0.05 linear). Evidence: `artifacts/truck-fixes/wheel-wear/` (`before` = main 799b3af, `v1` = albedo 0.075 + leather
roughness floor 0.30, `v2` = final values set by hand in the .mat, `iso-a015` = albedo 0.15 sensitivity, `after` = rebuilt;
`metrics-*.json`, `measure.py`, `wornmask.py`, `white.py`, `rim_before_after_vs_s730.jpg`). WorldC, editor, 2340x1080.
- **Why the cap was not the whole story (measured).** The worn zone is taken from the frames themselves (rim pixels whose
  luma changes when only the wear model changes, `wornmask.py`), compared with unworn rim in the same height band. A
  black rim in the cab is ~90 % specular: the probe reflection x AO (0.15, cloth block) x cab gain, while its diffuse light
  is the enclosed sky (x 0.4) + fill x AO. Worn albedo 0.05 -> 0.085 adds +2.3 / 255 in overcast; even 0.15 (sRGB 108,
  not plausible for black leather) adds only +6.5 and breaks D33 at low sun (rim lit R-B 6.0 %, worn part 6.9 %).
- **Decision.** (a) Black parts (mean tint < ~0.1): a hand burnishes and thins the pigmented finish, so worn spots go
  towards a NEUTRAL grey `_WearBlackAlbedo` = 0.085 linear (sRGB 81) x detail variation, lerped by the shaped wear wk - no
  longer x the warm tint, no cap (WORKING_VALUE: no measured albedo of worn black automotive leather; new black leather
  0.02-0.04). (b) Per-slot roughness floor of worn spots `_WearRoughMin`: leather 0.12 (hand-polished, glossy, not the
  0.08 of lacquer), other slots 0.08 as before; a surface glossier than its floor keeps its value. 0.30 (satin) was tried
  (v1) and read weaker: the grazing Fresnel of URP's EnvironmentBRDF is what makes a polished tube read. C# mirror
  `Game.Rendering.CabWearModel` (constants used by TruckAssetBuilder), EditMode `CabInteriorWearTests` on the exported rim:
  worn albedo 0.055-0.09 (rim: 0.0825), x >= 1.8 the unworn, chroma <= 6 %, roughness floor..unworn - 0.12. The generator's
  `BLACK_WEAR_DARKEN` (a6_export) stays: the shader's lerp to the neutral target overrides it at full wear.
- **Albedo audit.** The cab slots are not in the gate3 albedo audit (corridor world materials). Consistent with review
  r7 N-11 / docs/06: unworn black leather 0.027 linear (sRGB ~46) >= 32 sRGB, worn 0.085 (81) inside 30..240. No exception.
- **Measured (worn / unworn-neighbour luma of 255, ratio; before -> after).** overcast High 44.3 / 36.2 (1.22) ->
  46.6 / 36.3 (1.29), Low 43.4 / 35.5 (1.22) -> 45.8 / 35.5 (1.29); low sun High 44.3 / 36.6 (1.21) -> 50.2 / 36.9 (1.36), worn p95 59 -> 67, Low 1.22 -> 1.36.
  (The 1.22 before is geometry: the patches sit on the upper rim.) cab-dash black < 3 % unchanged on all four (High 1.44 /
  1.34 %, Low 1.63 / 1.44 %); rim p50 overcast 41.9 -> 42.0 (High), 40.0 -> 41.0 (Low).
- **D33 (low sun) PASS.** Rim lit third R-B High 4.1 -> 4.7 %, Low 3.5 -> 4.2 % (worn part 4.9 / 4.8 %) <= 6 %; sat
  18.1 -> 19.0 % / 16.4 -> 18.0 % <= the white van in the same frame (sunlit side through the windscreen, 22.3 / 26.2 %).
- **Open.** Overcast wear still reads only as a faint sheen (+~2.5 / 255): the in-cab reflection is the open-sky probe
  x a constant AO (the rim rotates: cloth-block AO), so a smoother lobe has no structure to reflect. Physically the
  reflection of a glossy interior part sees the sky only through the glazing and the dark interior elsewhere (and the
  probe specular, unlike the SH diffuse, is not enclosed - `_CabEnclosure` applies to SH only). Fix = directional glazing
  visibility of the probe specular in the cab frame (windscreen / door glass apertures already in CabInteriorLighting,
  ~6-10 ALU) or a rotation-invariant rim AO per section angle (generator); both change every glossy interior surface
  (rim p50, C-N6, black %) and need their own review. Seat bolster wear: same leather slot and model, but no control
  camera sees the driver's bolster (UNVERIFIED in frame). Phone (A16): UNVERIFIED. Cost: +3 ALU / cab pixel, no texture.

## Addendum r8b (2026-11-10, truck-artist): steering wheel remodelled (generator + export only, shader untouched); needs visual-critic review
Context: in `cab-dash` / `cab-driver` the wheel read as a plain smooth ring on plank spokes with a pillow hub
(`artifacts/truck-fixes/wheel-wear/rim_before_after_vs_s730.jpg`). Reference = style only (`Scania_S730_dash.jpg`,
CC BY-SA 3.0, docs/REFERENCES.md); no brand shape copied: own trapezoid pad, twin lower spokes with satin inlays (owner
sheets B2.1), TRAKT wordmark.
- **Model (`build_interior.build_wheel`).** Pivot / axis unchanged (`WHEEL_C`, `wheel_frame`, STEERING_WHEEL group
  prefixes). Rim centre line 470 mm, 499 mm over the leather (WORKING_VALUE, class 450-500 mm), section 35 x 29 mm with
  fuller grip zones (+10 % / +8 %), finger ridges at the back, thumb rests above the side spokes (+9 mm inner bulge),
  a 1 mm seam groove on the inner side turned 35 deg to the driver, cross seams at 10:45 / 1:15 ending the perforated
  grip leather (`leather_wheel_perf`, same hide, perforation flag). Spokes: moulded D-sections rising 12 deg from a
  26 mm dish and flaring into the rim; switch pods (gloss bezel, concave +/- rocker on the thumb side, four keys,
  generic pictograms; `cruise` drawn into the free cell 23 of the icon atlas). Hub: bowl shell, bezel, 1.5 mm parting
  gap, low crowned cover, wordmark embossed tone-on-tone (`emboss` 0.12, 0.6 mm proud) instead of satin letters.
  Column: two-shell shroud with a wider switch housing, parting line, rubber gaiters, flattened stalks.
- **Thread = geometry on LOD0.** The alpha-tested stitch decal is 1-2 px in `cab-dash` and vanished in the mips, so each
  stitch is a ridge (2 quads) in an opaque `thread_wheel` material (Fabric slot, trim colour x 4.5): 1.6 mm thread,
  6.5 mm pitch (real ~1 mm / 5 mm: WORKING_VALUE, heavier for phone resolution), ~1.9 k tris. LOD1 keeps one decal
  ribbon, LOD2 none.
- **AO probe (`a6_export`, object property `ao_probe`).** Parts stacked on a panel that buries the receiver under them
  took the occlusion of the buried point (keys and pictograms rendered black on the first export); they now take the
  value at a named open point of the receiver. The gloss bezel keeps its recess value (black frame round the keys).
- **Budgets.** Interior LOD0 / 1 / 2: 103 285 / 44 190 / 21 479 (was 97 187 / 43 297 / 21 958; limits 120 000 / 45 000 /
  22 000). STEERING_WHEEL 9 432 -> 14 354 / 4 858 -> 5 124 / 3 016 -> 2 174 (LOD2 pods = one key block). Draw calls,
  textures and material slots unchanged (decal atlas re-exported for the new pictogram). `check_export.py` PASS,
  `check_fit.py` PASS on LOD0 / 1 / 2 (0 vertices outside).
- **Limits (honest).** At 2340 x 1080 the rim is ~0.8 mm / px: the stitch rows are 1-2 px and read as a fine dashed
  line, the perforation does not resolve (it does in close views), the wordmark is deliberately faint. Phone (A16 /
  S24+): UNVERIFIED. Stalk pictograms: none (no atlas cell free).
Evidence: `artifacts/owner/interior/wheel-r8/` (Blender control cameras `kolo`, `piasta`, `kciuk`, `szew`, `zegary`,
`kierownica`; Unity WorldC `cab-dash` / `cab-driver` Low / High x overcast / lowsun before / after, 1:1 crops, montage
against the S730 reference).
