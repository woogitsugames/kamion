# ADR 0006 — Graphics API, Android targets and quality tiers
Status: Accepted (build-qa, Stage 0), 2026-11-09
Applied by code: `Game.Editor.Setup.ProjectSetup.ApplyAll` (`scripts/setup-project.ps1`), guarded by EditMode tests `ProjectConfigTests`.

## Decision
| Setting | Value | Why |
|---|---|---|
| Identity | product `Kamion` (working title), company `woogitsugames`, id `com.woogitsugames.kamion`, version `0.1.0`, versionCode = git commit count | owner brief |
| Scripting | IL2CPP, ARM64 only, managed stripping Low, IL2CPP config Release | Play requires 64-bit; ARMv7 devices are below our minimum anyway |
| Graphics APIs | **Vulkan first, OpenGL ES 3 fallback** (automatic off) | Vulkan: lower CPU driver overhead (we will be draw-call bound on city scenes), required for modern Mali/Xclipse/Adreno tuning; GLES3 kept only as fallback for devices with broken/blacklisted Vulkan drivers — removing it later is an option once the device matrix shows no GLES-only device |
| Colour space | Linear | physically based lighting (docs/06) |
| Min API | **29** (Android 10) | thermal status API (`PowerManager.getCurrentThermalStatus`), mature Vulkan 1.1 drivers; devices older than Android 10 do not meet the RAM/GPU floor anyway |
| Target API | **36** (Android 16) | Google Play requirement, verified 2026-11-09 on developer.android.com/google/play/requirements/target-sdk: *"Starting August 31 2026: New apps and app updates must target Android 16 (API level 36) or higher"* (extension possible only to 2026-11-01). The Unity 6000.3.28f1 Android module ships platforms 34/35/36/37; we pin 36 explicitly instead of "highest installed" so builds are reproducible |
| Orientation | auto-rotation, landscape left/right only | driving game; the phone may be held either way |
| Display | render outside safe area (full screen, UI keeps to `Screen.safeArea`), optimized frame pacing (Swappy) on | cut-out phones (A16 notch, Fold) |
| Frame rate | `Application.targetFrameRate` 30 default, 60 selectable (launch extra `-e fps 60`, overlay button, saved in PlayerPrefs); vSync 0 | 30 FPS on Galaxy A16 is a WORKING_VALUE until Stage 1+ measurements |
| Quality tiers | quality levels Low / Medium / High / Ultra, each with its own URP asset `Assets/_Project/Rendering/Settings/URP_<Tier>.asset`; Android default Medium, desktop High | separate assets let rendering-perf tune each tier without touching others |

Tier values (all WORKING_VALUE, rendering-perf owns tuning):

| Tier | Render scale | MSAA | HDR | Shadow dist | Shadow map | Cascades | Soft shadows |
|---|---|---|---|---|---|---|---|
| Low | 0.75 | off | off | 30 m | 512 | 1 | off |
| Medium | 0.85 | 2× | off | 50 m | 1024 | 1 | off |
| High | 1.0 | 4× | on (R11G11B10) | 80 m | 2048 | 2 | on |
| Ultra | 1.0 | 4× | on | 120 m | 2048 | 4 | on |

Renderer: all tiers share the template `Mobile_Renderer` (URP **Forward** path). ADR 0001 mentions Forward+; switching is left to rendering-perf once there are enough lights to measure the difference.

## Consequences
- Every APK targets API 36; when Google raises the requirement (historically each August), update `ProjectSetup.TargetSdk` + this ADR.
- GLES3 fallback roughly doubles shader variants/build time; revisit once the device matrix is wider.
- The diagnostics overlay (UI choice: uGUI built in code, Screen Space–Camera canvas, legacy built-in font) is chosen because the editor visual-QA renderer can capture it with `Camera.Render`; it is a dev tool, not the game UI (UI Toolkit remains open for the real HUD/menus).
