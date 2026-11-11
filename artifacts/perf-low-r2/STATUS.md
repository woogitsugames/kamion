# STATUS — perf-low-r2 (ADR 0113, rendering-perf)

## 2026-11-11 16:00 — krok 1: kod forest fast path + PSO/spike (bez pomiaru)
- Library skopiowana z main (8,2 GB). Lider mierzy (PHONE_RUN 15:43) — czekam z Unity.
- `Kamion/Vegetation`: `_KAMION_VEG_FAST` (global multi_compile, kolor): ściany HLOD L2 SH per wierzchołek (L0+L1 per piksel),
  brak pobrania mapy cieni za zanikiem URP (fade jak URP Lit); `_VegZWrite`/`_VegOffset` = tryb jednoprzebiegowy ścian HLOD.
- Nowy `Kamion/Forest Canopy` (M_ForestCanopy, QualityProfile.canopyMaterial): BRDF URP Lit (metal 0), SH/env/fog per wierzchołek, bez cieni.
- `ForestFastPath` (Rendering/Runtime): Shipping = QualityProfile.forestFast (Low on, rev 113, migracja w ProjectSetup);
  A/B `rq_ab` forestfast|vegfast|hlod1pass|canopyfast|veganiso; `rq_forestfast 0|1`. Haki w WorldInstances (Register/Unregister/Canopy).
- `PsoWarmup`: GraphicsStateCollection warm-up z Resources/Pso (`pso_warm 0` = A/B), trace `pso_trace <s> pso_tag <t>`,
  `spike_probe 1` → `[SPIKE]` (markery profilera w buildzie Development).
- NASTĘPNY KROK: (po zwolnieniu PHONE_RUN) `pwsh scripts/test.ps1 -Platform EditMode` (kompilacja), potem
  `pwsh scripts/build-android.ps1 -Tier Low` → `pwsh -NoProfile -File artifacts/perf-low-r2/phone-diag.ps1 -Apk <apk> -OutTag diag1 -Segment B -Uncapped -Runs "ab_forest=rq_ab=forestfast;ab_veg=rq_ab=vegfast;ab_1pass=rq_ab=hlod1pass;ab_canopy=rq_ab=canopyfast;ab_aniso=rq_ab=veganiso"`
