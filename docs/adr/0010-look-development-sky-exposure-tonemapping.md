# ADR 0010 — Look development: sky, daylight calibration, exposure, tonemapping, per-tier rendering
Status: Accepted (rendering-perf), 2026-11-09. Supersedes the tier table of ADR 0006 (values now live in `QualityProfile`).
Evidence: `docs/reports/visual/unity-look/` (renders), EditMode `SkyModelTests`, PlayMode `WorldCRouteTests`.
Answers visual review 2026-11-09 item #6 ("the Unity look first").

## Context
The DrivingLab used Unity's default procedural skybox (saturated blue gradient, hard horizon seam), trilight ambient picked
by eye, a sun of intensity 1.6 and no tonemapping decision. Mobile URP has no physical sky, no auto-exposure worth its cost
on Mali-G57 MC2 and no real-time GI. We need a look that is calibrated (docs/06 §4) and affordable on the Galaxy A16.

## Decision

### One daylight model drives everything (`Game.Rendering.SkyModel`)
- Clear sky: **Preetham, Shirley, Smits (1999)** Perez distribution + CIE xy chromaticity (turbidity T). Overcast: **CIE
  standard overcast sky** L(θ) = Lz (1 + 2 cos θ)/3, achromatic.
- Absolute levels from the **IESNA Lighting Handbook** daylight-availability fits (coefficients quoted from memory of the
  handbook: `WORKING_VALUE` until checked against the text): direct normal 127.5 klx · exp(−0.21 m), clear diffuse
  0.8 + 15.5 sin(h)^0.5 klx, overcast 0.3 + 21.0 sin(h) klx; air mass m after Kasten and Young (1989). The Preetham dome is
  normalised to that horizontal illuminance (test: dome integral within 6 %).
- Preetham's chromaticity turns magenta in the last degrees above the horizon (artefact visible in the first render);
  chromaticity is evaluated no lower than 6° elevation.
- Sun colour from Rayleigh + Ångström aerosol attenuation along the air mass (warm white at 42°).
- From that one model: sun light (direction, colour, intensity), sky shader `Kamion/Sky` (same formulas on the GPU),
  **L2 ambient SH** (sky + Lambertian ground, projected on the CPU), a 64 px RGBAHalf **reflection cubemap**, and the
  **fog colour** (mean horizon radiance) — so the horizon of the sky and the fogged terrain match (no seam).
- Unity's `SphericalHarmonicsL2.AddDirectionalLight` has its own normalisation (a uniform unit sphere evaluates to ≈ 1.89,
  not 1). The probe is rescaled by a calibration with a uniform sphere; `SkyModelTests.AmbientProbe_ReproducesSkyIrradiance`
  checks irradiance/π for up, side and down within 12 % (measured ≤ 3 %). Before this fix the ambient was 1.9× too bright.

### Exposure: fixed, "exposed units"
- No auto-exposure pass. Light, sky and ambient are pre-multiplied by k = 1 / (1.2 · 2^EV100) (Lagarde and de Rousiers 2014).
- EV100 from an incident-light meter on the preset's horizontal illuminance, EV = log2(E / 2.5) (C = 250), plus exposure
  compensation (+0.5 EV clear, +0.3 EV overcast, `WORKING_VALUE`). Clear 42° → EV 14.5, overcast 30° → EV 12.3: sunny-16
  and overcast EV 12–13 hold (test `IncidentMeterExposure_SunnySixteen`).
- Presets: `LP_Clear` (sun 42°, az 200°, T 2.5, visibility 30 km) and `LP_Overcast` (fully overcast, T 4, visibility 12 km).
  Both are assets in `Rendering/Settings/Lighting/`; time of day / season comes later.
- Fog = aerial perspective: exponential, density 3.912 / visibility (Koschmieder), colour = horizon radiance.

### Tonemapping: **Neutral** (not ACES)
A/B on the same frames (`docs/reports/visual/unity-look/*_Medium-clear-ACES.jpg` vs `*_Medium-clear.jpg`): ACES darkens the
mid-tones, crushes the shadow side of the trailer to near-black and pushes the grass to a saturated green and the sky to a
deep blue — the "HDR look" docs/06 §2 forbids. Neutral keeps hue and the calibrated mid-grey; the scene reads like a phone
photo. Neutral on HDR tiers; Low has no post-processing at all (LDR, values above 1 clip — only the sun disc and specular
glints reach that range at this exposure, so Low and Medium look alike, see `truck-at-gate_Low-clear.jpg`).
No bloom, vignette, grading (explicitly zero in `VP_World`).

### Per-tier settings (`Rendering/Resources/QualityProfile.asset`, applied by `ProjectSetup` + `QualityProfileApplier`)
| | Low | Medium | High | Ultra |
|---|---|---|---|---|
| render scale | 0.75 | 0.85 | 1.0 | 1.0 |
| MSAA | 2× | 4× | 4× | 4× |
| HDR / post | off / off | R11G11B10 / Neutral + dither | same | same |
| shadows: distance, map, cascades, soft | 35 m, 1024, 1, hard | 60 m, 1024, 2, hard | 100 m, 2048, 3, soft medium | 150 m, 4096, 4, soft high |
| depth / normal bias | 1.0 / 1.0 | 1.0 / 1.0 | 0.8 / 0.8 | 0.6 / 0.6 |
| world texture aniso | 2 | 4 | 8 | 16 |
| LOD bias / far clip | 0.5 / 900 m | 0.8 / 1400 m | 1.5 / 2500 m | 2.0 / 3500 m |
| world detail layer (2nd sample + 2nd macro octave) | off | on | on | on |

Anti-aliasing on Mali-G57 MC2 (tile-based): **MSAA** resolves in tile memory; Arm's guidance is that 4× is the cheap sweet
spot on Mali, and it is the only option that fixes the geometric aliasing of kerbs and the 0.12 m markings mesh. FXAA/SMAA
cost an extra full-screen pass and blur texture detail; TAA needs motion vectors, a history buffer (bandwidth) and ghosts on
a moving truck — flagship only, later, if at all. Low keeps 2× to save resolve bandwidth on a 4 GB device. All
`UNMEASURED` until the A16 is measured (phone PIN-locked all day 2026-11-09).
Shadows: only the truck, trailer and bridges cast (terrain/roads/markings do not) — shadow cost scales with cascades × casters.
No acne at depth/normal bias 1.0 in any capture.

### Road markings at grazing angles
1. Markings are a geometry decal mesh (+6 mm); 24-bit depth at 200 m with a 0.05 m near plane resolves only ~5 cm → the
   material adds **polygon offset** (factor −1, units −4) and renders after the road (queue Geometry+10).
2. **Distance pre-filter** in `Kamion/World Surface`: albedo blends toward the asphalt albedo by the line's pixel coverage,
   `saturate(1.5 · 0.12 m / length(fwidth(xz)))`. Far dashes stop sparkling (compare the 2nd and 1st iteration renders).
3. MSAA on the geometry edges; world textures trilinear + per-tier anisotropy; mip bias 0 (negative bias re-introduced
   moiré on the kostka in the DrivingLab).

### Terrain / grass tiling
World-space planar projection (no generator UVs needed, seamless across chunks), second sample at 2.71–3.3× scale rotated
37° (Medium+), macro noise in two octaves (47 m and 194 m for grass) with a dry-grass tint. Texture low-frequency content
kept small so Low (single sample) does not show a blotchy "noise layer" (docs/06 §2).

## Consequences
- Every world scene gets lighting from `EnvironmentLighting` + presets; never hand-tuned ambient colours.
- Tonemapper change = new A/B renders + update of this ADR.
- Textures are procedural placeholders for character only; CC0 photo scans (Poly Haven / ambientCG) need the owner's OK
  to download (docs/06 §3) and would replace the detail maps without touching the shader.
- The DrivingLab still uses its old lighting; switching it is a scene-builder change (not done in this task).
- Open: the clear sky reads slightly dull/slate compared with a photo (Preetham at T 2.5 is pale; IES diffuse 13.8 klx);
  to be judged against owner photos of Białystok before changing T or compensation.
