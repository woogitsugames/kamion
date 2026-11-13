# ADR0153 — independent preflight review

Status: **CODE REVIEW: CHANGES REQUIRED; VISUAL REVIEW PENDING**. Reviewed candidate working tree against 421f1b4fb, without running Unity, adb, generation or tests. No visual PASS is issued without matched PNGs. Read CLAUDE.md, docs/06_GRAFIKA_ANTI_AI_SLOP.md and .claude/skills/visual-qa/SKILL.md.

## Findings

1. **P1 — atlas LOD1 disables the existing LOD0 plate shader globally.** Location: tools/worldgen/streetscape/export.py:219 and tools/worldgen/streetscape/vehicle_lod_atlas.py:63. Consolidation removes the standalone car_plate primitive from every car/van LOD1. WorldCarPlateMaterials.ValidLibrary requires that primitive at both LOD0 and LOD1 (54 total), and ValidNativeLibrary has the same constraint. Configure (invoked by RegionImporter.cs:219) first resets car_plate to ordinary URP Lit, then fails eligibility. Thus unchanged LOD0 geometry still loses ADR0089 instance-specific plate remapping. Adapt the existing eligibility checks to distinguish atlas LOD1 while preserving complete native LOD0 corner validation; add an integration regression asserting the LOD0 material remains enabled after the candidate import.

2. **P2 — refrigeration grille is flattened into a solid swatch.** Location: tools/worldgen/streetscape/vehicle_lod_atlas.py:60 and :83-88. reefer_grille is not merely its M.color: its louvre_slats texture_set produces _STRIPES in WorldPbrMaterials (0.06 m period, alternating linear 0.012 and approximately 0.085-0.09). life_props.py:242 explicitly places that grille on BOTH LODs with metre UVs. Replacing all UVs by a constant and sampling a 0.03 swatch removes the authored horizontal grille and changes its mean response. Bake a suitably filtered grille rectangle into the atlas and preserve mapped local coordinates, or document an intentional silhouette-distance simplification with paired proof. Current PNG-value tests cannot catch this.

3. **P2 — declared metallic preservation changes the actual existing response on several details.** Location: tools/worldgen/streetscape/vehicle_lod_atlas.py:87. The atlas encodes M.metal unconditionally and VehicleLodAtlasMaterials enables _MetallicScale=1. Existing ordinary materials go through LookDevAssets.WorldMaterial:147-148, where metal <=0.5 uses World Surface, whose shader is dielectric (fixed F0=0.04 and full diffuse). Examples affected: rim_dusty=0.45, rim_dark=0.5, car_lamp=0.5, trailer_chassis=0.5, trailer_doors/front=0.3. They become genuinely metallic at the LOD boundary, reducing diffuse and tinting reflection. This is a code-proven response change; its visibility needs pairs. Preserve the previous effective response for the consolidation baseline or explicitly isolate and accept this material change separately.

## Positive static checks

- Primary-paint primitives remain the same objects and preserve UV1 payload through consolidation.
- Secondary positions, normals and triangle winding are concatenated without coordinate transforms; index offsets appear correct.
- Atlas image y convention and plate affine UV transform agree: palette lives at lower image half / v<0.5; the plate region at upper image half / v>0.5.
- Alias=1 is consumed only after LOD1 exists; importer shares both the native mesh and material start, and does not allocate a duplicate native mesh.
- Vehicle cull remains 300 m; existing car/van boundaries are numerically unchanged; yard split at100m aliases equal geometry.

## Material uncertainties and remaining gates

- No device cost claim: World PBR replaces previously simpler World Surface / some Lit detail passes, and samples base/mask/normal/macro even on Low. Fewer submeshes is not proof of lower GPU time. Need actual Low frame telemetry.
- No compressed ASTC / native Half2 image check has been performed. Source-PNG centre tests do not measure phone texture error.
- Atlas tests validate flat source parameters and geometry but do not exercise WorldCarPlateMaterials eligibility or the grille pattern.
- Need matched before/after Low and High PNGs at LOD0/1 boundary, grille front, metallic wheels/chassis and multiple instances with plate variation. Review every supplied comparison; final visual result remains pending.

## Follow-up static review — three proposed fixes

Reviewed the updated sources only; did not run Unity, adb, tests or generation. **All three original failure mechanisms are addressed in code. No additional blocking regression found in these fixes.** This is not visual acceptance and does not certify generated A or B assets.

- **LOD0 plate remap:** ValidLibrary permits the two-primitive replacement only for `.lod1` whose corresponding root explicitly sets `vehicle_lod_atlas=true`; `.lod0` retains the exact original plate/corner checks. The native route recognizes exactly one World PBR material with `KamionVehicleLodAtlas=1` only at LOD1; LOD0 still calls ValidNativePlate unchanged. Legacy libraries retain the 54-plate outcome; migrated libraries require 27 original plates plus 27 migrated LOD1s. The import test now checks the actual custom plate shader and keyword, which targets the original integration failure. No code-level bypass of LOD0 validation found.
- **Grille:** UV range maps 1.68 x .78 m into x=8..1016, v=136..248; this corresponds to image rows264..376 inside padded rows256..384, without overlapping the solid palette in rows384..512 or plate block in rows0..256. Baking has 13 periods with the same dark/light phase as the source `_STRIPES` expression, and smoothness=.45. Original loss of the horizontal pattern is fixed.
- **Effective metallic:** The new strict `metal > .5` threshold agrees with LookDevAssets.WorldMaterial. Former dielectric detail materials retain effective metal=0; rim/rim_steel/trailer_alu retain their original nonzero values. The revised PNG assertion checks this effective baseline instead of simply mirroring raw manifest metal.

**Small remaining fidelity uncertainty (not a newly demonstrated defect):** source grille `_STRIPES` also multiplies albedo by `0.9 + 0.2*macro.a`, and uses derivative-based edge filtering. The new image stores the nominal stripe levels and relies on texture filtering/mips. Thus it preserves the authored pattern, period and nominal smoothness, but not pixel-exact source response. Judge the actual magnitude and distant filtering in matched PNGs; do not label it byte-identical shading. The ASTC and device-cost gates from the original review remain open.
