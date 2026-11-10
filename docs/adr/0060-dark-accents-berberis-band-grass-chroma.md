# ADR 0060 - Dark accents of the world (sky occlusion, ground grime, dark noise cassettes), clipped berberis band, grass chroma (D38), stones in the Bieżeństwa ring centre

Status: accepted (2026-11-10); N-2 target not met, see Evidence

## Context
Review r7 §10 / §14 (pkt 5, 7) and r8: N-2 "milky" world - p10 of the overcast control frames 35-37 % luma against
22.7 % in the CC0 Bieżeństwa photo (acceptance: mean p10 <= 28 at p50 +-3, without darkening everything); N-4 / N-22
berberis reads as a red sofa / brick carpet with straight seams (acceptance: 0.5-0.7 m, narrow band, straight side
without "sausages", lighter shoot tips, p50 18-24, sigma in the mask >= 5, close-up R-B 9-13, sat <= 40). Owner
decisions D38 (grass albedo saturation 35-40, material only), D37 (relative paint cap), D42 (Mapillary CC BY-SA
photos as reference only).

## Decision
1. **Sky occlusion data** (`_SkyOcc`, Kamion/World PBR and Kamion/World Surface, default 0 = old look). The world is lit by
   the sky SH and a sky reflection probe, no screen-space AO. Manifest key `sky_occ: [down, horizon]` (importer
   `RegionImporter.CreateMaterial`): down-facing faces (deck soffits, eaves, canopy / balcony undersides, window reveal
   heads) get `1 - down * max(-n.y, 0)` of the ambient (the ground they see is shaded by the same structure); glazing
   gets `1 - horizon` of the near-horizontal reflection (R.y < 0.45: a window sees the street, not the horizon sky).
   Rule in `streetscape/materials.py` (structures [0.5, 0], glass [0, 0.6], far facades [0.5, 0.6]); bridge soffit 0.6.
   Never on cars, ground, vegetation, decals, collision.
2. **Ground grime** (`_GRIME`, WorldPBR, paving / behaton / yard concrete / slabs / yard + path asphalt): dirty joints
   on all tiers (Var.B, Low had joint dirt only through the Medium+ jitter block) and damp / oily hollows in the low
   spots (Var.R) of the macro wear patches (~16 % of the area, x0.58-0.62 albedo, gloss 0.62). Carriageways
   (`_ROADWEAR`): damp lowest 0.25 m of the gutter and an oil / soot drip band between the wheel paths (`_DripBand`
   0.22 aged, 0.06 SMA). Low +1 fetch (Var) on grime materials only.
3. **Leaf cards** (`Kamion/Vegetation _CrownShade` 0.5): the lower crown sees less sky; card normals are crown-radial
   (make_trees.py), so the ambient is scaled by the card's height on the crown. Impostors / HLOD keep their baked
   visibility.
4. **Noise cassettes** `noise_panel` albedo 0.30 -> 0.05 (dark powder-coated absorbers; Mapillary 2018-07 / 2024-07 at
   g3b_eye_s1482 / s1632 read near-black under the glass panes). The largest single source of real dark pixels on G3-B.
5. **Berberis** (`streetscape.plantings`): height 0.5-0.65 m; a 1.1-1.4 m band along the traced bed's centre line (mid
   points of cross-sections perpendicular to the long axis, smoothed, buffered, kept inside the bed with a 0.3 m lawn
   rim) instead of the whole 3-8 m bed (the wide flat top + crown relief below the core top gave the seams and the
   sofa); `clipped` profile (straight side, ~6 deg batter, 0.24 m rounded arris, flat top), lumps 0.025 m, dome 0.05,
   side shoots 12 %, edge shoots leaning out 0.5-1.1 rad; texture: deeper inner leaves darker (deep 0.45) and 40 % of the
   outer leaves light copper-tan (146, 88, 64 sRGB) - the photo's lighter tips. Profiles `cushion` / `box` unchanged
   for other species. Override key `band_m` per bed.
6. **Ring centre of Rondo Bieżeństwa** (authored override `biezenstwa-plantings`): `fill: stones` (`bed_stones`,
   gravel_compacted set) without shrubs: Mapillary 2020-08-15 photos 201270605169291 / 2818555625124739 /
   3970163613102941 (CC BY-SA, reference only, D42) show loose stones under the viaduct, not soil with red shrubs.
   Hedge beds on the lawns stay (dark-red hedge visible in 2818555625124739).
7. **Grass chroma (D38)**: `GRASS_CHROMA` 1.40 on the summer albedo of `grass_verge` about its own luminance (hue and
   mean luminance kept; the engine takes the hue from the set), `_GrassFill` re-measured. No post / exposure change.
8. **D37**: no QA / test had a hard 217 cap (only a comment in `test_streetscape_r6.py`, updated to the relative rule).

## Evidence
Editor renders, `scripts/visual-qa.ps1 -Scene WorldC`, 50 world cameras (cab-/truck-/hedge_ excluded), metric
`scripts/dark-accents.py` (Rec.709 luma on sRGB, %, mean over frames); data in `artifacts/world-r8/*_metrics.json`,
frames in `artifacts/world-r8/{before,after1..after4}/<Tier>-<light>/`, montages in `artifacts/world-r8/montage/`.

| set | p10 ov Low / Med / High | p50 ov Low / Med / High | p10 clear Low / High (p50) | grass sat ov Low / High |
|---|---|---|---|---|
| before (f9143ba) | 34.0 / 36.4 / 36.0 | 50.2 / 52.2 / 52.0 | not rendered | 26.7 / 25.0 |
| after2 (49eabe6) | 32.3 / 34.6 / 34.4 | 50.0 / 52.1 / 51.9 | - | 39.5 / 37.3 |
| after3 (0657910) | 32.3 / 34.6 / 34.4 | 50.0 / 52.1 / 51.9 | - | 38.5 / 36.2 |
| after4 (8338bc3) | 32.3 / - / 34.4 | 49.9 / - / 51.9 | 26.9 / 27.8 (46.9 / 48.9) | 38.4 / 36.2 (clear 43.4 / 40.8) |

- **N-2 NOT met** (target p10 ov <= 28, clear <= 25 at p50 +-3): -1.7 / -1.6 p10 at unchanged p50 (overcast); clear
  26.9 / 27.8. Diagnosis (p10 pixel masks, after3): in the G3-A / Kwadrat frames (p10 38-42, about 30 of 50 cameras)
  the darkest 10 % of the frame IS the near carriageway (asphalt_worn albedo 0.08, already at the low end of aged AC;
  luma ~38-42 at overcast). There is no darker 10 % to promote; the accents of this ADR (soffits, glazing, crown,
  grime, drip band) cover < 3 % of those frames. G3-B frames with the dark cassettes are already at p10 20-25.
  The Mapillary set (90 images in `Data/raw/mapillary/bialystok-industrial-c`, 2018-2024, mostly sunny) has median
  p10 13.9 / p50 47.0 / road 28.3 / sky 56.3: the photo darks are tree belts, cast shadows and an exposure that keeps
  the sky at ~56 instead of our ~90 (overcast, tonemapped near white). Asphalt was NOT darkened further: road / sky
  ratio game 42 / 90 = 0.47 vs photos 28 / 56 = 0.50. Reaching 28 at overcast needs global exposure / tonemap contrast
  (rendering-perf, owner decision) or more dark masses placed from data - both outside this ADR.
- **Glazing**: horizon occlusion 0.6 -> 0.9 (after4): office pane at g3a_ext34_s0214 sRGB 103 -> 84 (lin ~0.137 ->
  0.087); target 0.03-0.06 lin. not reached - what remains is the sky above R.y 0.45 (kept, physically right).
- **Berberis (N-4 / N-22)**, `scripts/hedge-metrics.py`, High overcast mask: s0362 p50 24.1, sigma 5.35, R-B 10.4,
  sat 33.8; hedge_a_close 22.5 / 5.1 / 8.9 / 31.4; photo-ground 24.5 / 3.5 / 9.8 / 31.6 (photo baseline p50 22.8).
  Height 0.5-0.65 m, 1.1-1.4 m band, no full-width seams (montage `hedge_a_close_before_after4.jpg`). Open: sigma < 5
  at distance, close-up R-B 8.9 (target 9-13). Mapillary p13 (2020-08-15) shows loose stones with a kerb on the bank
  right of the road under the viaduct where g3a_eye_s0362 has a hedge bed: needs a position check before replacing it
  (`montage/g3a_eye_s0362_vs_mapillary_p13.jpg`).
- **Grass (D38)**: sat overcast 36-38 (target 35-40), clear 41-43 (slightly above: the clear sky SH adds chroma).
- Tests: `pytest tests/gis` 165 passed; EditMode 137 passed / 0 failed / 2 inconclusive (TruckCabGlassTier, not this
  change) / 7 ignored. Frame budget (`streetscape_qa.json` mesh_budget): stretch_04 High 1.984 M tris (before 1.993 M,
  limit 2.0 M), Low 0.953 M.

## Consequences
- The p10 gap of ~4-6 points stays open as N-2; the next lever is not material work but overcast exposure / tonemap
  contrast (rendering-perf) and data-driven dark masses (tree groups per Mapillary p26 / p30 / p55, contact shadows
  under parked cars).
- Triangles: hedge band -9.3 k tris per frame; one new material (`bed_stones`).
- Shader: one more `shader_feature_local` (_GRIME) in WorldPBR; `_SkyOcc` / `_DripBand` / `_CrownShade` are uniforms.
- `_CrownShade` is serialized per material at creation (0.5); changing the shader default does not reach imported
  materials - drive it from the manifest if it is ever tuned.
- Phone: UNVERIFIED (no A16 / S24+ frames in this change). visual-critic review: pending (lider).
