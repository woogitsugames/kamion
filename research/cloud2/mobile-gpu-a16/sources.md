# Źródła — R8 mobile-gpu-a16

Data dostępu wszystkich źródeł: **2026-11-14**. Pliki lokalne w `files/` (poza gitem, `fetch.py` je odtwarza).
„Referencja” = wolno cytować krótko i linkować; plików nie redystrybuujemy (są tylko lokalnie, `.gitignore`).

## Producenci sprzętu
| # | Tytuł | URL | Status prawny | Do czego |
|---|---|---|---|---|
| S1 | MediaTek Helio G99 — strona produktu | https://www.mediatek.com/products/smartphones-2/mediatek-helio-g99 | © MediaTek, referencja | GPU Mali-G57 MC2, LPDDR4X 4266 Mbps, CPU |
| S2 | Arm GPU Datasheet (Mali/Immortalis, © 2024, 3 s.) | https://documentation-service.arm.com/static/6659a973876c8d213b7870b5 | © Arm, referencja | rdzeń G57: FP32/FP16 ops, px/teksele na cykl, tile 256 bit/px, MSAA 2×→4×, koszty filtrowania |
| S3 | Arm GPU Best Practices Developer Guide 101897_0304_10_en, Issue 10 (2025-01-31, 135 s.) | https://developer.arm.com/documentation/101897 (PDF: https://documentation-service.arm.com/static/67a62b17091bfc3e0a947695) | Arm Non-Confidential, referencja | early ZS/FPK, discard/A2C, depth prepass, MSAA, blending, tekstury, precyzja (strony w manifeście) |
| S4 | Samsung Semiconductor — Exynos 2400 | https://semiconductor.samsung.com/processor/mobile-processor/exynos-2400/ | © Samsung, referencja | Xclipse 940 = RDNA 3, „hexa-core GPU” |
| S5 | gsmManiaK: „Samsung Galaxy S24+ w Polsce z procesorem Exynos 2400…” | https://www.gsmmaniak.pl/1463367/samsung-galaxy-s24-plus-w-polsce-z-procesorem-exynos-2400-na-100-procent/ | © gsmManiaK, referencja (media) | wariant PL = SM-S926B Exynos (źródło wtórne; główny dowód = pomiar w repo) |

## Bazy danych sprzętu (Vulkan)
| # | Tytuł | URL | Licencja | Do czego |
|---|---|---|---|---|
| S6 | gpuinfo — raport 53265 (SM-A165F, Mali-G57 MC2, Android 17, Vulkan 1.3.303) | https://vulkan.gpuinfo.org/displayreport.php?id=53265 | CC BY 4.0 | limity, cechy, ASTC/FP16/subgroup |
| S7 | gpuinfo — raport 53260 (SM-A165F, Android 14, Vulkan 1.1.177) | https://vulkan.gpuinfo.org/displayreport.php?id=53260 | CC BY 4.0 | stary sterownik: deskryptory 500000, zestawy 4 |
| S8 | gpuinfo — raport 52490 (SM-S926B, Xclipse 940, Android 17, Vulkan 1.3.304) | https://vulkan.gpuinfo.org/displayreport.php?id=52490 | CC BY 4.0 | limity S24+ |
| S9 | gpuinfo — lista raportów Mali-G57 MC2 (API JSON) | https://vulkan.gpuinfo.org/listreports.php?devicename=Mali-G57+MC2 | CC BY 4.0 | znalezienie raportów SM-A165F (396 raportów G57 MC2) |
| S10 | gpuinfo — lista raportów samsung SM-S926B (API JSON) | https://vulkan.gpuinfo.org/listreports.php?devicename=samsung+SM-S926B&platform=android | CC BY 4.0 | 7/8 raportów = Xclipse 940 |

Zapytania API gpuinfo (GET, 2026-11-14 ok. 17:05 UTC) — pełne URL-e w `manifest.csv` (`url_pliku`), np.
`https://vulkan.gpuinfo.org/api/internal/reports.php?filter[devicename]=samsung SM-S926B&filter[platform]=android&…&length=50&order[0][dir]=desc`.
Hurtowe pobieranie listy urządzeń (3596 wpisów) zostało zablokowane przez politykę sesji — nie było potrzebne.

## Silnik / API
| # | Tytuł | URL | Status | Do czego |
|---|---|---|---|---|
| S11 | Unity 6.3 — Configure for better performance in URP | https://docs.unity3d.com/6000.3/Documentation/Manual/urp/configure-for-better-performance.html | © Unity, referencja | zalecenia URP mobile |
| S12 | Unity 6.3 — Anti-aliasing in URP | https://docs.unity3d.com/6000.3/Documentation/Manual/urp/anti-aliasing.html | © Unity, referencja | FXAA vs MSAA na tiled GPU |
| S13 | Unity 6.3 — Universal Render Pipeline asset reference | https://docs.unity3d.com/6000.3/Documentation/Manual/urp/universalrp-asset.html | © Unity, referencja | Render Scale/UI, soft shadows, HDR precision, Store Actions |
| S14 | Unity 6.3 — Android Player settings | https://docs.unity3d.com/6000.3/Documentation/Manual/class-PlayerSettingsAndroid.html | © Unity, referencja | Blit Type, Fixed DPI |
| S15 | UnityCsReference — PlayerSettingsAndroid.bindings.cs (commit cf583fb) | https://github.com/Unity-Technologies/UnityCsReference/blob/cf583fbe6da6b9fb11e3a1ac03f23df4eb120e9b/Editor/Mono/PlayerSettingsAndroid.bindings.cs | Unity Reference-Only License | enum AndroidBlitType (Always = 0) |
| S16 | Khronos Vulkan-Samples — performance/msaa, render_passes, subpasses (commit b4fb432) | https://github.com/KhronosGroup/Vulkan-Samples/tree/b4fb432b80234e54cf7be7411f20b65494a5b0f5/samples/performance | Apache-2.0 | zmierzone pasmo (Mali-G76): resolve MSAA, LOAD vs CLEAR, subpasy |
| S17 | Qualcomm — Adreno GPU on Mobile: Best Practices (80-78185-2) | https://docs.qualcomm.com/doc/80-78185-2/topic/mobile_best_practices.html (md: https://docs.qualcomm.com/bundle/publicresource/80-78185-2/topics/mobile_best_practices.md) | © Qualcomm, referencja | LRZ/discard/A2C, MSAA 2×, SurfaceFlinger upscale |

## Narzędzia
| # | Tytuł | URL | Status | Do czego |
|---|---|---|---|---|
| S18 | Arm Learning Paths — Arm Performance Studio install guide | https://learn.arm.com/install-guides/ams/ | © Arm, referencja | „free of charge” |
| S19 | Arm Learning Paths — Profile an Android application (setup tasks) | https://learn.arm.com/learning-paths/mobile-graphics-and-gaming/ams/setup_tasks/ | © Arm, referencja | Unity: Development Build wymagany |
| S20 | Android GPU Inspector — supported devices | https://developer.android.com/agi/supported-devices | CC BY 4.0 | A16/G57 nie na liście |
| S21 | ARM-software/libGPUCounters README (commit 847a04a) | https://github.com/ARM-software/libGPUCounters/blob/847a04a1597d132a3746e9c6374d3977cea89a6d/README.md | MIT | liczniki Mali w aplikacji |

## Znane problemy (Unity Issue Tracker; treść przez publiczne API JSON)
| # | Klucz | URL | Do czego |
|---|---|---|---|
| S22 | UUM-147578 — Rendering corruption on ARM Mali GPU (FrameBuffer + DepthTexture, Vulkan) | https://issuetracker.unity3d.com/issues/rendering-corruption-on-arm-mali-gpu-when-using-shader-with-framebuffer-and-depthtexture-with-vulkan-api (API: https://issuetracker.unity.com/api/v1.0/issues/23555) | naprawione w 6000.3.28f1 (wersja projektu) |
| S23 | UUM-137912 — crash DoF Bokeh na Vulkan | https://issuetracker.unity3d.com/issues/android-app-crashes-when-volume-depth-of-field-is-set-to-bokeh-while-using-vulkan-graphics-api (API …/issues/7525) | G57 MC2 nie reprodukuje; DoF w projekcie off |
| S24 | UUM-28518 — libGLES_mali.so crash (FrameTimingManagerGLES) | https://issuetracker.unity3d.com/issues/android-libgles-mali-dot-so-crash (API …/issues/18470) | ryzyko przy fallbacku GLES |
| S25 | UUM-107530 — Runtime performance deteriorates on certain Android devices (Vulkan) | https://issuetracker.unity3d.com/issues/build-performance-deteriorates-on-certain-android-devices-when-graphics-api-is-set-to-vulkan-on-an-upgraded-project (API …/issues/20394) | Adreno; Mali nie reprodukuje |

Inne wyszukane, nieużyte (strona usunięta po migracji trackera — „Page not found”): `urp-android-vulkan-depthshader-is-not-rendered-on-devices-with-mali-gpu…`, `android-vulkan-scene-glitches-out-and-app-freezes-whenever-phone-is-in-landscape-mode-on-mali-devices…`.

## Repo projektu (commit 81c9bae)
`docs/DEVICE_MATRIX.md`, `docs/PERFORMANCE_BUDGETS.md`, ADR 0013, 0106, 0113, 0136, 0177, `docs/reports/REVIEW-2026-11-14-s20-gate3-phone.md`,
`game/Assets/_Project/Rendering/Settings/URP_Low.asset`, `Mobile_Renderer.asset`, `Rendering/Resources/QualityProfile.asset`,
`game/ProjectSettings/ProjectSettings.asset`, `ProjectVersion.txt` — sha256 w manifeście.

## Niedostępne / nieużyte
- developer.arm.com (strony produktów, np. Mali-G57) — 403 dla curl i przekierowanie dla WebFetch; zastąpione PDF-ami z documentation-service.arm.com.
- Qualcomm Game Developer Guide FAQ (developer.qualcomm.com/.../gdg/gpu/faq.html) — przekierowuje na ogólną stronę; zastąpione docs.qualcomm.com 80-78185-2.
- Samsung PL — specyfikacja S24 (samsung.com/pl/smartphones/galaxy-s24/specs/) przekierowuje na S26 → brak oficjalnego PL źródła wariantu.
- Zegar GPU Helio G99: brak w źródłach producenta; nie otwarto tablicy OPP jądra → UNVERIFIED.
