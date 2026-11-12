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
