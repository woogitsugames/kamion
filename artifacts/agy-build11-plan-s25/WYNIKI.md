# Plan i skrypt pomiaru buildu #11 (`agy-build11-plan-s25`)

- **Gałąź / worktree:** `agy-build11-plan-s25` (`C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\agy-build11-plan-s25`)
- **Zakres:** przygotowanie planu, tabeli pomiarowej, progów decyzji, listy kontrolnej odsłuchu i skryptu [measure.ps1](file:///C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/agy-build11-plan-s25/artifacts/build11-s25/measure.ps1) (bez uruchamiania Unity ani buildu).

---

## 1. Co sprawdzono w kodzie i danych (tylko odczyt)

1. **`art-source/truck/interior/export/SM_CabInterior_LOD0.fbx`:** obecne poza gitem (`17 644 652 B`, `2026-11-27 17:47`); `pwsh -NoProfile -File scripts/cab-lod0.ps1 -Require` zwróciło `exit 0` (`[cab-lod0] OK`).
2. **Kolejność buildu (`chain.status` buildu #10, `BuildCommands.cs`, `WorldTruckInstaller.cs`, `check-build-scenes.py`):**
   - `Game.Editor.Setup.TruckAssetBuilder.BuildBatch` (+ opcjonalnie `WorldTruckInstaller.InstallBatch` dla `WorldC`) pod slotem `-Pool unity`,
   - `pwsh scripts/check-build-scenes.py --regions d67-full --require-tiles --require-high` (54 regiony `d67-full` w `region_catalog.json`),
   - `pwsh scripts/build-windows.ps1 -Slot -Regions d67-full` + `scripts/package-windows.py <dir> --dry-run`.
3. **Kamery i punkty startu 8 kafli miejskich + C (`regen-wave-14-s25`, `codex-city-budget-s25/WYNIKI.md`):**
   - Wszystkie 10 najgorszych kamer `frame_estimate` są obecne w `control_cameras.json` (wypiekane do scen przez `WorldSceneBuilder` jako `ControlCamera`, wywoływane przez `-qacam <id>`, bo `Gate3Cameras.Norm` normalizuje `_` i `-`):
     - `bialystok-wygoda`: `roundabout_01_above` (`3 445 913` H / `1 331 924` L) — **`route_start.json` ma tylko `91 m` (2643 m od ronda), więc działa wyłącznie `qacam`**.
     - `bialystok-bojary`: `route_s0612` (`3 282 640` H / `1 455 719` L; `route_s=612`).
     - `bialystok-maczka`: `route_s0440` (`3 252 236` H / `1 255 584` L; `route_s=440`).
     - `bialystok-mickiewicza`: H `dw678_ciolkowskiego` (`3 193 215` H; `route_s=2038`), L `roundabout_03_above` (`1 418 992` L — **425 m od trasy, Low wymaga `qacam`**).
     - `bialystok-kleeberga`: `route_s0159` (`2 639 902` H / `1 098 311` L; `route_s=159`).
     - `knyszyn`: `gardens_tykocka_eye` (`2 297 014` H / `765 410` L; `route_s=649`).
     - `bialystok-krywlany`: `route_s0461` (`2 296 069` H / `913 831` L; `route_s=461`).
     - `monki`: `route_s0170` (`2 109 118` H / `694 685` L; `route_s=170`).
     - `bialystok-industrial-c` (REF): `stretch_04` (`1 972 103` H / `947 240` L; `route_s=360`).
   - Ponieważ `DrivingLabBootstrap.ActivateControlCamera` (`-qacam`) wyłącza `mainCamera` i HUD (bez lusterek), `measure.ps1` w trybie domyślnym (`-CityMode both`) dodaje przebiegi `Cab` (`route_s=...`) dla `bojary`, `maczka`, `mickiewicza` H i `c`.
4. **Flagi A/B w kodzie C#:**
   - `rq_mirror_main=0` (`RenderOverrides.cs` / `ExtraViews.cs` → `MirrorOverrides.MainMinHeight = 0`; wymaga trybu `Cab`, np. `bialystok-bojary` `route_s=612`).
   - `rq_cardedge=0` (`RenderOverrides.cs` → `WorldInstances.cs` `_KamionCardEdge = 0`, czyli wyłączenie `VegCardEdge` na kartach liści; na `bialystok-maczka` `qacam=route_s0440`).
   - `-farRing off` + `-stream 1` (`FarRing.ReadSwitch` obsługuje `-farRing off` z linii poleceń oraz `KAMION_FAR_RING=off`; `WorldSceneBuilder.AddEdgeCameras` dodaje `edge-north` do każdej sceny regionu → test na `knyszyn-w` `qacam=edge-north,stream=1`).
   - Uwaga do `pc-metrics.ps1`: D76 `emulation` w `tools/pcperf/budgets/pc-machines.json` wymaga `1920x1080`, `-WindowMode borderless`, `-VSync 0`, `Low/30` lub `High/60` (pomiary #10 na GTX 1070 miały status `informational`).
5. **Odsłuch (krok 4):** opracowano checklistę na podstawie `DrivingActionCatalog.cs`, `TruckAudioController.cs`, `TruckAudioController.CabMechanisms.cs`, `BrakeSquealGate.cs`, `TrailerRattleGate.cs`, `DrivingHud.Desktop.cs` i `DrivingLabSceneBuilder.cs`:
   - Wycieraczki: `U` (`Off/Intermittent/Slow/Fast`), `wiper_dry`/`wiper_wet` (`_KamionWet >= 0.25`, np. `-rq_wet 1`) + `wiper_park`.
   - Pisk hamulca: `S`/`↓` przy `1–15 km/h`, ciśnienie `0.22–0.65`, żądanie `0.12–0.75` ≥ `0.10 s`, bez `Space`/`HillHold`, `p = 0.28`, `cooldown = 3 s`.
   - Klakson: `K` oraz przycisk `DesktopHorn` na HUD PC (min. `0.22 s`, `horn_air_loop`/`horn_air_cab_loop`).
   - Grzechot naczepy: sprzężona naczepa (`Cargo24t`), `> 1.5 km/h`, `> 1.6 m/s²` / `> 0.28 m/s` zawieszenia / `cobbles`/`gravel`/`grass` (pas przeszkód i pasy nawierzchni w `DrivingLab`, albo pobocze/bruk w świecie + `T`/`G`).

---

## 2. Utworzone pliki

- [artifacts/build11-s25/README.md](file:///C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/agy-build11-plan-s25/artifacts/build11-s25/README.md) — pełna instrukcja kroków (1)–(4), tabela do wypełnienia (z wartościami bazowymi #10, `frame_estimate`, `rt_pc`), checklista odsłuchu oraz progi decyzji dla wariantów budżetu miast (`A`/`B`/`C`) i dalekiego planu (`A`/`B1`/`B2`/`C`).
- [artifacts/build11-s25/measure.ps1](file:///C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/agy-build11-plan-s25/artifacts/build11-s25/measure.ps1) — skrypt PowerShell z `-WhatIf` / `-DryRun`, `-Steps`, `-Resume`, `-CityMode qacam|route|both`, `-IncludeUncappedAB`, obsługą slotów `unity-slot.ps1` (`unity` i `heavy`), ochroną przed równoległym `Unity.exe` / `build_world.py` / `Kamion.exe` oraz agregacją `pc-report.json` → `summary.csv` + `summary.md`.
- [artifacts/agy-build11-plan-s25/WYNIKI.md](file:///C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/agy-build11-plan-s25/artifacts/agy-build11-plan-s25/WYNIKI.md) oraz aktualizacja [STATUS.md](file:///C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/agy-build11-plan-s25/STATUS.md).

---

## 3. Weryfikacja

- `pwsh -NoProfile -File artifacts/build11-s25/measure.ps1 -WhatIf` → **`exit 0`** (34 przebiegi + Preflight + TruckBuild + Build + Summary, bez uruchamiania Unity ani playera).
- `pwsh -NoProfile -File artifacts/build11-s25/measure.ps1 -DryRun -Steps Measure,Summary -Exe "C:\fake\Kamion.exe" -IncludeUncappedAB` → **`exit 0`** (40 przebiegów z A/B bez limitu FPS).
- `pwsh -NoProfile -File scripts/cab-lod0.ps1 -Require` → **`exit 0`** (`SM_CabInterior_LOD0.fbx` obecny).
- Zweryfikowano klucze agregatora `pc-report.json` na rzeczywistym raporcie buildu #10 (`World_knyszyn-w_High High 60 PASS informational 3303909.0 1377.0 8.387 5.289 0`).
- **Czego nie zrobiono (zgodnie z zakazem):** nie uruchamiano Unity, nie budowano playera Windows, nie uruchamiano `pc-metrics` na żywo.

---

## 4. Następny krok dla lidera

Po zakończeniu fali 14 i scaleniu gałęzi:
```powershell
pwsh artifacts/build11-s25/measure.ps1 -WhatIf
pwsh artifacts/build11-s25/measure.ps1 -Steps Preflight,TruckBuild,Build,Measure,Summary
```
