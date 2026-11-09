# Device matrix

| Role | Device | Model | SoC | GPU | RAM | Android / API | Screen | Profile |
|---|---|---|---|---|---|---|---|---|
| Daily test (minimum) | Samsung Galaxy A16 | SM-A165F (a16nseea) | MediaTek MT6789 (Helio G99) | Mali-G57 MC2 (`ro.hardware.egl=meow`; GPU name per MT6789 spec, confirm via GL_RENDERER on Boot screen) | 3.57 GiB (MemTotal 3 740 844 kB) | 16 / 36 | 1080×2340 | Low/Medium |
| Quality target (always connected) | Samsung Galaxy S24+ | SM-S926B (e2sxeea), serial RZCX60VE8ZY | Samsung Exynos 2400 (s5e9945) | Xclipse 940 (RDNA3-based; `ro.hardware.egl=samsung`) | 10.9 GiB (MemTotal 11 472 024 kB) | 17 / 37 | 1440×3120 | High/Ultra |
| Occasional (owner's daily phone) | Samsung Galaxy Z Fold 8 Ultra | TBD | TBD | | | | | foldable/tablet-like UI, aspect-ratio and fold/unfold tests; never assume it is attached |

Measured 2026-11-09 via `adb shell getprop`. adb serial RFGL34SJYDZ.

Implication: ~4 GB RAM and a 2-core Mali-G57 are far below the quality target. Low/Medium budgets must be strict (see PERFORMANCE_BUDGETS.md once Stage 0 measures the empty scene). Target 30 FPS on this device is a WORKING_VALUE until measured.

Scripts must address devices by serial (`adb -s`), support installing on all attached devices, and skip absent ones gracefully.
