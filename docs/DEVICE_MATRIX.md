# Device matrix

| Role | Device | Model | SoC | GPU | RAM | Android / API | Screen | Profile |
|---|---|---|---|---|---|---|---|---|
| Daily test (minimum) | Samsung Galaxy A16 | SM-A165F (a16nseea) | MediaTek MT6789 (Helio G99) | Mali-G57 MC2 (`ro.hardware.egl=meow`; GPU name per MT6789 spec, confirm via GL_RENDERER on Boot screen) | 3.57 GiB (MemTotal 3 740 844 kB) | 16 / 36 | 1080×2340 | **Low** (auto, `QualityProfile.deviceRules`; GPU confirmed `Mali-G57 MC2`, Vulkan 1.1); Medium selectable (DK8 forest 27 FPS) |
| Quality target (always connected) | Samsung Galaxy S24+ | SM-S926B (e2sxeea), serial RZCX60VE8ZY | Samsung Exynos 2400 (s5e9945) | Xclipse 940 (RDNA3-based; `ro.hardware.egl=samsung`) | 10.9 GiB (MemTotal 11 472 024 kB) | 17 / 37 | 1440×3120 | High/Ultra |
| Occasional (owner's daily phone) | Samsung Galaxy Z Fold 8 Ultra | TBD | TBD | | | | | foldable/tablet-like UI, aspect-ratio and fold/unfold tests; never assume it is attached |

Measured 2026-11-09 via `adb shell getprop`. adb serial RFGL34SJYDZ.

Implication: ~4 GB RAM and a 2-core Mali-G57 are far below the quality target. Low/Medium budgets must be strict (see PERFORMANCE_BUDGETS.md once Stage 0 measures the empty scene). Target 30 FPS on this device is a WORKING_VALUE until measured.

Scripts must address devices by serial (`adb -s`), support installing on all attached devices, and skip absent ones gracefully.

## PC (D73 / D74, ADR 0269)
| Role | Class (D74) | Tier (auto, `PcTierTable.DefaultFor`) | Status |
|---|---|---|---|
| Minimum | i5-6400 / Ryzen 3 1200, GTX 660 / RX 460 / Intel HD 630 (2 GB VRAM), 8 GB | Low, 1080p 30 fps | no machine attached — UNMEASURED |
| Recommended | i5-9600 / Ryzen 5 3600, GTX 1660 / RX 590, 12 GB | High, 1080p 60 fps | no machine attached — UNMEASURED |
| Dev (not a reference) | Core Ultra 7 270K Plus, RTX 5070 12 GB, 64 GB | High (auto ceiling; Ultra from the menu) | ADR 0261 run on mobile High assets only |

Auto rules: software / integrated GPU → Low; RAM < 7 000 MB → Low; VRAM unknown → Medium; VRAM < 3 500 MB → Low, < 5 500 MB → Medium,
else High; High needs RAM ≥ 11 000 MB. Never Ultra. All thresholds WORKING_VALUE.
