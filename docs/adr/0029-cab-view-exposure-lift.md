# ADR 0029 — Cab-view exposure lift (cab metering, neutral shadow lift, exterior enclosure)

Status: Accepted (rendering-perf), 2026-11-10. Extends ADR 0021 §4. Review: `REVIEW-2026-11-09-r4.md` L1/L2,
`REVIEW-2026-11-10-r5.md` L1-r5, L2-r5, E2.

## Context
- ADR 0016 exposes low sun and dusk for the sunlit scene (phone scene metering). The cab interior is lit only by the sky
  through the glazing, so in the cab view it fell 2–3 EV below its overcast level: `cab-dash` < 3 % luma was 10.8 %
  (low sun) and 13.1 % (dusk) on High, 10.6 / 20.7 % on Low (editor), against the target ≤ 8 %, p10 3–6 %.
- On Low the interior AO atlas was 512 px. The LOD0 atlas is packed for 4096, so the thin islands (A-pillar trim,
  steering-wheel rim) sampled the black gutter: Low overcast `cab-dash` < 3 % was 12.1 % vs 2.1 % with the 1024 atlas.
- r5: the lift amplified the warm low-sun fill, so black plastics read brown; from outside the cab the interior looked
  too bright ("aquarium").

## Decision
1. **Cab metering** (`CabInteriorLighting.CabMeterEv`): in the cab view only, the interior gain is
   2^(cabViewEv + m) with m = clamp(0.6 · log2(key_overcast / key), 0, 1.5 EV), where key is the interior ambient
   (open-sky SH through the enclosure + first-bounce fill, exposed units) and key_overcast is the same quantity for the
   overcast reference preset (computed once). This is the phone metering the backlit cab; dusk still reads darker than day
   (partial compensation). CPU only (a few dozen flops per frame), no pass, no keyword, every tier.
2. **Low AO atlas no smaller than 1024** (`TruckAssetBuilder`: Low uses the Medium atlas). +0.26 MB on Low.
3. **Neutral lift**: the share of the output added by the local shadow lift is desaturated (`_CabShadowLift.z`,
   `shadowLiftNeutral` 0.8), in `Kamion/Cab Interior` and `Kamion/Truck Exterior`. A phone's local tone mapping lifts
   luminance, not the chroma of deep shade. Directly sunlit plastics keep the sun colour (physical). +4 ALU per pixel.
4. **Exterior enclosure** `exteriorEnclosure` 0.88 for views from outside (in-cab 0.6 stays as part of the cab-view
   tone mapping). Glazing ~4.3 m² of ~26 m², τ 0.75: the interior sees ~10–15 % of the open sky.

## Measured (editor, WorldC, 2340×1080; `cab-dash` < 3 % luma / p10)
| View | Low before → after | High before → after |
|---|---|---|
| overcast | 12.1 → 1.6 % / 6.3 | 2.4 → 2.4 % / 6.3 |
| low sun | 10.6 → 2.1 % / 5.8 | 10.8 → 3.7 % / 5.4 |
| dusk | 20.7 → 5.5 % / 4.7 | 13.1 → 6.5 % / 4.4 |

Overcast `cab-dash` p99.9 (sky through the glass) unchanged (High 95.9 %, Low 84.7 %). Low-sun plaza shade R−B
−1.7 → −5.2 (SkyModel `lowSunCool`, same commit series).

## Consequences / open
- `exteriorEnclosure` made no measurable difference in `truck-34` (High pixels identical at 0.6 and 0.88): what is seen
  through the windscreen from outside is not dominated by the `Kamion/Cab Interior` SH path (glass reflection, the view
  through the cab, interior LOD culling with lodBias). Windscreen p50 / sky p50 = 0.41 on Low and High overcast. The
  aquarium look needs the glass owner (TruckGlass) and a check of which renderers draw the interior from outside.
- Sky opposite the low sun through the windscreen is khaki (137/135/116, R−B +21) with both the old and the new glass
  (identical pixels): the error is in the sky dome near the anti-solar horizon (SkyModel), not in the glass.
- A16 r5 (23.9 % < 3 %) was build `40ae9c5`, before the 1024 atlas. The lift uses uniforms only, so
  `ShaderVariantStripper` (lightmap/debug keywords) cannot strip it. The atlas explains about half of the gap measured
  in the editor (12.1 → 1.6 %); the rest (ASTC 8×8 bleed at 512, Camera.main in the device cab rig) is UNVERIFIED until
  the next A16 run.
- All constants WORKING_VALUE until compared with owner photos.
