# ADR 0060 - Dark accents of the world (sky occlusion, ground grime, dark noise cassettes), clipped berberis band, grass chroma (D38), stones in the Bieżeństwa ring centre

Status: accepted (2026-11-10), numbers in the evidence section

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
See the addendum below (filled from `artifacts/world-r8/`).

## Consequences
- Draw calls / triangles: hedge band smaller than the r7 masses (fewer tris); no new materials except `bed_stones`.
- Shader: one more `shader_feature_local` (_GRIME) in WorldPBR; `_SkyOcc` / `_DripBand` / `_CrownShade` are uniforms.
- Phone: UNVERIFIED (no A16 / S24+ frames in this change).
