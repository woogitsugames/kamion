# ADR 0043 — Low-sun anti-solar sky: Hillaire multiple scattering, acceptance criterion, WB adaptation A/B

Status: Accepted in part (rendering-perf), 2026-11-10. Review: `REVIEW-2026-11-10-r5.md` L2-r5. Extends ADR 0010 (sky
model) and ADR 0016 (exposure, unchanged). Option (c) below is **not** a default: that is an owner art-direction decision.

## Context
- r5 L2: at the LowSun preset (sun 9°, azimuth 60°, T 3) the sky seen through the windscreen in `cab-dash` is khaki
  (r5: 138/135/116). The open sky above the trailer in `truck-34` is neutral.
- A Python port of `SkyModel.BuildChroma` evaluated the analytic sky without rendering (linear Rec.709, luminance 1,
  "before" = main `f40012e`):

  | view elevation | Δaz from sun 90° | 135° | 180° (anti-solar) |
  |---|---|---|---|
  | 1° | 1.15/0.98/0.75 | 1.12/0.99/0.76 | 1.13/0.99/0.74 |
  | 3° | 1.18/0.98/0.67 | 1.17/0.98/0.66 | 1.19/0.98/0.63 |
  | 10° | 0.94/1.03/0.89 | 0.92/1.03/0.89 | 0.92/1.03/0.88 |
  | 20° | 0.82/1.04/1.17 | 0.80/1.04/1.20 | 0.79/1.04/1.20 |

- Preetham, Shirley, Smits (SIGGRAPH 1999) xy chromaticity, fitted to the multiple-scattering simulations of
  Nishita et al. (1996), gives the same direction: 1.10/1.00/0.73 at 1–6° anti-solar, neutral at 10°, blue at 20°.
  Both models therefore say that, at a **fixed daylight white balance**, the hazy horizon away from a 9° sun is
  yellowish-white (sunlight reddened over air mass ≈ 6 and scattered by aerosols along a saturated horizontal path).
  Zotti, Wilkie, Purgathofer, "A Critical Review of the Preetham Skylight Model" (WSCG 2007) report that Preetham's
  colour is unreliable at low sun, so it is a cross-check, not ground truth. "Pale blue / white" in photos comes from
  the camera's auto white balance (chromatic adaptation to the warm illuminant), not from the radiance itself.
- The model's diffuse/direct ratio already exceeds the IESNA handbook fits (0.26 vs 0.20 at 9°), so making the
  bounced-light term brighter is not justified.

## Decision
1. **Hillaire 2020 multiple scattering** (`SkyModel.MultipleScatteringFraction`). Hillaire, "A Scalable and Production
   Ready Sky and Atmosphere Rendering Technique" (EGSR 2020, §5.5): with an isotropic phase, orders ≥ 3 form a geometric
   series Ψ_ms = L_2nd / (1 − f_ms), with f_ms = (1/4π) ∫∫ σ_s T dt dω. f_ms is evaluated once per band at the observer
   (16 zenith bands × 32 steps, CPU, once per preset change). At T 3 it is 0.40 (410 nm) … 0.20 (696 nm), so the higher
   orders are bluer. **GPU cost 0** (same LUT, same shader path on every tier, Low included).
   Model: anti-solar 3° goes from 1.19/0.98/0.63 to 1.13/0.99/0.75, and 1° from 1.13/0.99/0.74 to 1.06/0.99/0.87.
2. **Acceptance for sun < 10°** (leader decision, option b): "peach/white, no olive", R−G ≥ (R−B)/2 in the 8-bit render,
   or B ≥ R. Measured in the 1024 × 472 editor renders, see Evidence. This criterion is **not met**. The analytic sky
   itself fails it in linear light (1.10/0.99/0.79: R−G 0.11 < (R−B)/2 0.155), so it can only be met by a white-balance
   change (option c) or by changing the colour away from what the physics gives. The EditMode test
   `LowSun_AntiSunHorizon_IsNotOlive_AndHillaireMakesItLessWarm` guards the physical bounds instead: R−B < 0.35 and
   G − R < 0.05 (rgb/max) at 2–10° and Δaz 90–180°.
3. **Option (c): phone-style partial white-balance adaptation**, implemented but **off** (`LightingPreset.whiteBalanceAdaptation` = 0
   in every preset, asserted by a test). It is a von Kries transform in Bradford cone space (Lam 1985; as used in
   CIECAM97s and ICC v4) with degree D toward the horizontal scene illuminant (sun + sky dome). It is applied in
   `SkyModel` to the sun colour, the sky LUT, the overcast/ground neutral (`AdaptedWhite`, `_SkyOvercastColor`), the
   ambient, the fog and the reflections. That keeps the agreement between these five (ADR 0010), the luminance and the
   exposure (ADR 0016), and costs no GPU time. A/B renders at D 0.5: `-WbAdapt 0.5` on `scripts/visual-qa.ps1`.
4. **Glazing**: see Evidence. The transmitted scene through `Kamion/Truck Glass` is grey by construction (premultiplied
   "over", the tint shows only in the outside body term). Typical laminated green windscreen glass (2 × 2.1 mm float
   + 0.76 mm PVB) is specified by its visible transmittance: UN ECE Regulation No. 43 requires T_v ≥ 70 % for windscreens.
   Fe²⁺ absorption makes it slightly green-blue (transmittance higher at 500–550 nm than at 650 nm). The per-band values
   are WORKING_VALUE, from memory of glass makers' data, not checked.

## Evidence (editor, Low = WorldC, High = WorldC_High, 1024 × 472, `artifacts/owner/wb-ab/`, not in git)
Mean sRGB of the top 25 rows of `cab-dash` (through the windscreen, 1/8-width columns 1–4) and the top 60 rows of `truck-34`
(open sky, columns 0–4 away from the sun):

| render | cab-dash sky (through glass) | B−R | truck-34 open sky | B−R |
|---|---|---|---|---|
| before Low | 126–138 / 122–132 / 104–110 | −22 … −28 | 117–126 / 128–136 / 128–138 | +11 … +14 |
| Hillaire Low | 124–135 / 122–132 / 110–117 | −14 … −19 | 116–124 / 128–136 / 133–143 | +18 … +20 |
| WB 0.5 Low (A/B only) | 122–133 / 122–133 / 113–120 | −9 … −13 | 113–122 / 128–136 / 137–147 | +24 … +27 |
| before High | 117–140 / 113–136 / 98–117 | −19 … −24 | | |

## Consequences
- The anti-solar low sky is 5–8 points less warm on both tiers. It is still yellow-white rather than blue: physically
  that is what a fixed daylight white balance shows.
- The owner decides on option (c) with `artifacts/owner/wb-ab/` (before / Hillaire / WB 0.5, Low and High). If accepted,
  set `whiteBalanceAdaptation` in the presets and drop the test assertion that it is 0.
- `-qaNoGlass` (visual QA diagnostic) leaves only the grey Fresnel loss of the glazing, for comparing glass with no glass.
- Not verified on a phone. The sky path is the same shader on every tier, so there is no per-tier difference to expect.
