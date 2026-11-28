# Plan i procedura pomiarowa buildu #11 (`build11-s25`)

Zestaw gotowy do uruchomienia przez lidera po zakończeniu fali 14 i scaleniu zmian do gałęzi budującej (`win-build` / `main`).
Wszystkie wartości progowe klas D74/D83 w `tools/pcperf/budgets/pc-budgets.json` mają status `WORKING_VALUE`.

---

## 1. Stan wstępny i weryfikacja artefaktów przed buildem

- **`art-source/truck/interior/export/SM_CabInterior_LOD0.fbx`:** plik poza gitem (`art-source/truck/interior/.gitignore`), **zweryfikowany na dysku** (`17 644 652 B`, `2026-11-27 17:47`).
- Weryfikacja automatyczna przed buildem:
  - `pwsh scripts/cab-lod0.ps1 -Require` (exit `0` = FBX obecny; gdyby zaginął na świeżym checkoucie: `pwsh scripts/cab-lod0.ps1 -Build`, ok. 9 min Blender 4.2).
  - `uv run --no-project python scripts/check-build-scenes.py --regions d67-full --require-tiles --require-high` (54 regiony zestawu `d67-full`, Low + High + kafelki streamingowe).
- **Ważna uwaga sprzętowa:** pomiary `pc-metrics` w buildzie #10 (`artifacts/full-build-10-s24/`) wykonano na **GTX 1070 + i5-10400F (D3D11, `informational`)**, natomiast maszyna deweloperska **RTX 5070 + Core Ultra 7 270K** jest wpisana w `tools/pcperf/budgets/pc-machines.json` jako `emulation` (D76, wymaga `1920x1080`, `WindowMode borderless|exclusive`, `VSync 0`, `Low/30` lub `High/60`). Skrypt `measure.ps1` wymusza te parametry w każdym przebiegu klasy.

---

## 2. Kolejność wykonania przez lidera

Wszystkie kroki można podejrzeć bez uruchamiania Unity ani playera:
```powershell
pwsh artifacts/build11-s25/measure.ps1 -WhatIf
# lub na już zbudowanym exe:
pwsh artifacts/build11-s25/measure.ps1 -DryRun -Steps Measure,Summary -Exe artifacts/win/kamion-<ver>-<sha>-regions/Kamion.exe
```

### Krok (1) — Preflight i `TruckAssetBuilder`
```powershell
pwsh scripts/cab-lod0.ps1 -Require
pwsh scripts/unity-slot.ps1 -Acquire -Pool unity -Owner build11-s25
# W środowisku worktree z env.ps1:
# Unity.exe -batchmode -projectPath game -logFile artifacts/logs/build11-TruckAssetBuilder.log -buildTarget Win64 -quit -executeMethod Game.Editor.Setup.TruckAssetBuilder.BuildBatch
# Opcjonalnie (gdy WorldC był importowany przed rebuildem TRAKT): -executeMethod Game.World.Import.WorldTruckInstaller.InstallBatch
pwsh scripts/unity-slot.ps1 -Release -Pool unity -Owner build11-s25
uv run --no-project python scripts/check-build-scenes.py --regions d67-full --require-tiles --require-high
```
Po wyjściu z Unity sprawdź `git status --porcelain -- game/ProjectSettings/` i w razie zmian cofnij `git checkout -- game/ProjectSettings/QualitySettings.asset`.

### Krok (2) — Build Windows x64 (`d67-full`)
```powershell
pwsh scripts/build-windows.ps1 -Slot -SlotOwner build11-s25 -Regions d67-full
# Dry-run weryfikacji paczki (wspiera --dry-run):
uv run --no-project python scripts/package-windows.py artifacts/win/kamion-<ver>-<sha>-regions --dry-run
```

### Krok (3) — Pomiary `scripts/pc-metrics.ps1`
Pełna seria uruchamiana przez:
```powershell
pwsh artifacts/build11-s25/measure.ps1 -Steps Measure,Summary -Exe artifacts/win/kamion-<ver>-<sha>-regions/Kamion.exe
# Z opcjonalnymi parami A/B bez limitu FPS (-Fps 1000) dla rozdzielenia kosztu GPU/CPU:
pwsh artifacts/build11-s25/measure.ps1 -Steps Measure,Summary -Exe <exe> -IncludeUncappedAB
# Wznowienie po przerwaniu:
pwsh artifacts/build11-s25/measure.ps1 -Steps Measure,Summary -Exe <exe> -Resume
```

**Zakres przebiegów w `measure.ps1`:**
1. **Porównanie z buildem #10 (`RefDurationSeconds = 90 s`):** `knyszyn-w` i `dk65-07` w klasach `zalecany` (`High/60`) oraz `min` (`Low/30`).
2. **8 kafli miejskich > 2,0 M `frame_estimate` + `bialystok-industrial-c` (`DurationSeconds = 45 s`, > 600 klatek także przy 30 FPS):**
   - W trybie `qacam=<id>` (dokładna pozycja najgorszej kamery z `artifacts/codex-city-budget-s25/WYNIKI.md` — zweryfikowana w `control_cameras.json`):
     - `bialystok-wygoda`: `qacam=roundabout_01_above` (High & Low — **`route_start.json` ma tylko 91 m w rogu SW, 2643 m od ronda, więc działa wyłącznie `qacam`**)
     - `bialystok-bojary`: `qacam=route_s0612` (High & Low)
     - `bialystok-maczka`: `qacam=route_s0440` (High & Low)
     - `bialystok-mickiewicza`: High `qacam=dw678_ciolkowskiego`, Low `qacam=roundabout_03_above` (**Low 425 m od trasy → wymaga `qacam`**)
     - `bialystok-kleeberga`: `qacam=route_s0159` (High & Low)
     - `knyszyn`: `qacam=gardens_tykocka_eye` (High & Low)
     - `bialystok-krywlany`: `qacam=route_s0461` (High & Low)
     - `monki`: `qacam=route_s0170` (High & Low)
     - `bialystok-industrial-c` (REF): `qacam=stretch_04` (High & Low)
   - W trybie `Cab` (`route_s=<m>`, widoczna kabina + lusterka klasy II/IV na kluczowych gęstych kaflach):
     - `bialystok-bojary` (`route_s=612`, High/60 i Low/30), `bialystok-maczka` (`route_s=440`, High/60), `bialystok-mickiewicza` (`route_s=2038`, High/60), `bialystok-industrial-c` (`route_s=360`, High/60 i Low/30).
     - *Uwaga metodologiczna:* `DrivingLabBootstrap.ActivateControlCamera` (`-qacam`) wyłącza `mainCamera` i HUD (lusterka w oknach nie renderują się), dlatego testy z `route_s` są potrzebne do uchwycenia pełnego budżetu z kabiną i lusterkami.
3. **Izolacje A/B (`High/60`, opcjonalnie z `-IncludeUncappedAB`):**
   - **Lusterka `rq_mirror_main=0`:** `bialystok-bojary` `route_s=612` (tryb `Cab`, bo w `qacam` lusterka są wyłączone!) — bazowo vs `rq_mirror_main=0`.
   - **Karty liści `rq_cardedge=0` (`VegCardEdge`):** `bialystok-maczka` `qacam=route_s0440` (kafel z największym udziałem drzew w `frame_estimate`) — bazowo vs `rq_cardedge=0`.
   - **Far ring `-farRing off` na `edge-north` z `-stream 1`:** `knyszyn-w` `qacam=edge-north,stream=1` vs `qacam=edge-north,stream=1,farRing=off` (`FarRing.cs` obsługuje zarówno `-farRing off`, jak i `KAMION_FAR_RING=off`; skrypt zeruje zmienną środowiskową przed każdym przebiegiem).

---

## 3. Lista kontrolna odsłuchu (krok 4 — jazda ręczna w buildzie #11)

Uruchom build okienkowy (`Kamion-okno.cmd` lub `Kamion-knyszyn-w.cmd` / `Kamion-DrivingLab.cmd`) i zweryfikuj oba widoki: **kabina** oraz **zewnątrz (`C` / `Tab`)**.

| Element | Sterowanie / warunek wywołania (z kodu C#) | Gdzie najlepiej sprawdzić | Co dokładnie usłyszeć / kryterium PASS | Wynik (`PASS`/`FAIL` + uwagi) |
|---|---|---|---|---|
| **1. Wycieraczki** | Klawisz **`U`** (`CycleWipers`): przełącza `Off → Intermittent → Slow → Fast → Off`. Warstwa sucha/mokra zależy od `_KamionWet >= 0.25` (zwykła pogoda = `wiper_dry`; z `-rq_wet 1` = `wiper_wet`). | Dowolna scena (`DrivingLab` lub `knyszyn-w`), na postoju lub w ruchu. Dodatkowe uruchomienie z `-rq_wet 1` dla wariantu mokrego. | - Wyraźne szurnięcie gumy w synchronizacji z ruchem ramion (`pitch = clip.length / CycleSeconds`, szybsze na `Fast`).<br>- Przy przełączeniu z `Fast → Off` słyszalne cichsze kliknięcie/dobiegnięcie `wiper_park`.<br>- Wyraźna różnica barwy kabina vs zewnątrz i `dry` vs `wet`. | `[ ]` |
| **2. Pisk hamulca roboczego** | Klawisz **`S` / `↓`** (`Brake`). Warunki `BrakeSquealGate`: prędkość **`1–15 km/h`**, ciśnienie **`0.22–0.65`**, żądanie **`0.12–0.75`** przez `>= 0.10 s`, bez hamulca postojowego (`Space`) i bez `HillHold`. Prawdopodobieństwo **`28 %`** na jedno naciśnięcie, cooldown **`3 s`**. | `DrivingLab` (prosta lub plac) albo dowolna ulica w `knyszyn-w` / `bialystok-bojary`. | - Rozpędź zestaw do ~20 km/h (`W`), puść gaz i przy `12 → 2 km/h` wykonaj 4–6 lekkich/średnich dohamowań (nie wciskaj do oporu na dłużej).<br>- W kabinie (tłumiony) i na zewnątrz (wyraźniejszy od przedniej osi) słyszalny krótki, naturalny pisk `brake_service_squeal` z lekką zmianą wysokości (`pitch 0.90–1.10`), bez zapętlenia ani „piszczenia na postoju”. | `[ ]` |
| **3. Klakson** | Klawisz **`K`** (przytrzymanie lub krótkie muśnięcie, min. czas `0.22 s`) oraz **przycisk klaksonu na HUD PC** (lewa strona dolnego bloku HUD). | Dowolna scena jazdy (`knyszyn-w` / `DrivingLab`), także podgląd w Ustawieniach → Sterowanie. | - Natychmiastowy atak przy wciśnięciu `K`, ciągłe brzmienie bez słyszalnego szwu pętli przy przytrzymaniu 2–3 s, płynny spadek i lekkie obniżenie tonu (`1.0 → 0.95`) po puszczeniu.<br>- Przycisk HUD reaguje identycznie jak `K`.<br>- W kabinie ciszej/cieplej (`cabHornFactor = 0.7`) niż na zewnątrz (`C`). | `[ ]` |
| **4. Grzechot naczepy i siodła** | Wymaga **sprzężonej naczepy** (domyślny start `Cargo24t`). Wyzwala się od `> 1.5 km/h` przy: przyspieszeniu pionowym `> 1.6 m/s²`, szybkości zawieszenia `> 0.28 m/s`, szarpnięciu siodła (`kingpinImpulse`), jeździe po nawierzchni `cobbles`/`gravel`/`grass`, lub tuż po sprzęgnięciu (`< 0.25 s`). | **`DrivingLab`**: pas przeszkód (`Obstacle lane`: progi 8/15 cm, próg zwalniający, koleiny) oraz pasy nawierzchni (`cobbles`, `gravel`, `grass`) przy `10–35 km/h`.<br>**Świat**: zjazd kołami naczepy na pobocze / bruk; odpięcie i podpięcie (`T` / `G`). | - Losowe, niemiarowe metaliczne stuknięcia łańcuchów, klamer plandeki i luzu siodła (`chain_a/b`, `tarp_a`, `kingpin`), proporcjonalne do nierówności.<br>- Brak grzechotu na gładkim asfalcie przy stałej jeździe i na postoju.<br>- W kabinie wyraźnie ściszony (`cabTrailerRattleFactor = 0.35`), na zewnątrz (`C`) dobrze słyszalny z okolic siodła/naczepy. | `[ ]` |

---

## 4. Tabela pomiarów do wypełnienia (Build #11)

### 4A. Porównanie z buildem #10 (`knyszyn-w`, `dk65-07`)

*Baza Build #10: `0.1.0-8511a411d8`, GTX 1070 + i5-10400F, 1920×1080, High/60 (`artifacts/full-build-10-s24/evidence/`).*

| Przebieg | Klasa / tryb | Build #10 tris p95 | Build #10 DC p95 | Build #10 GPU p50/p95 [ms] | Build #10 CPU p50/p95 [ms] | **#11 tris p50 / p95** | **#11 DC p50 / p95** | **#11 GPU p50 / p95 [ms]** | **#11 CPU p50 / p95 [ms]** | **#11 frame p50 / p95 [ms]** | Werdykt |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `ref-knyszyn-w-high60` | `zalecany` (High/60) | 3 303 909 | 1 377 | 6,48 / 8,39 | 4,09 / 5,29 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `ref-knyszyn-w-low30` | `min` (Low/30) | *(brak w #10)* | — | — | — | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `ref-dk65-07-high60` | `zalecany` (High/60) | 2 253 633 | 1 034 | 7,55 / 8,21 | 3,67 / 4,48 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `ref-dk65-07-low30` | `min` (Low/30) | *(brak w #10)* | — | — | — | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |

### 4B. 8 kafli miejskich + C (`zalecany` High/60 i `min` Low/30)

*Kolumna `frame_est` / `rt_pc` pochodzi z `artifacts/codex-city-budget-s25/WYNIKI.md` (fala 14 `bb3e5eccc`, główna kamera bez cieni i lusterek; `pc-metrics` sumuje wszystkie passy).*

| ID przebiegu | Kafel (`kamera` / `route_s`) | Klasa | `frame_est` [M] | `rt_pc` [M] | **#11 tris p50 / p95** | **#11 DC p50 / p95** | **#11 GPU p50 / p95 [ms]** | **#11 CPU p50 / p95 [ms]** | **#11 frame p50 / p95 [ms]** | Werdykt |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `city-bialystok-wygoda-high60` | `wygoda` (`qacam=roundabout_01_above`) | High/60 | 3,45 | 3,00 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-bialystok-wygoda-low30` | `wygoda` (`qacam=roundabout_01_above`) | Low/30 | 1,33 | 1,31 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-bialystok-bojary-high60` | `bojary` (`qacam=route_s0612`) | High/60 | 3,28 | 2,35 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-bialystok-bojary-low30` | `bojary` (`qacam=route_s0612`) | Low/30 | 1,46 | 1,04 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `cab-bojary-high60` | `bojary` (`route_s=612`, Cab+lusterka) | High/60 | 3,28 | 2,35 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `cab-bojary-low30` | `bojary` (`route_s=612`, Cab+lusterka) | Low/30 | 1,46 | 1,04 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-bialystok-maczka-high60` | `maczka` (`qacam=route_s0440`) | High/60 | 3,25 | 1,85 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-bialystok-maczka-low30` | `maczka` (`qacam=route_s0440`) | Low/30 | 1,26 | 0,86 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `cab-maczka-high60` | `maczka` (`route_s=440`, Cab+lusterka) | High/60 | 3,25 | 1,85 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-bialystok-mickiewicza-high60` | `mickiewicza` (`qacam=dw678_ciolkowskiego`) | High/60 | 3,19 | 1,82 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-bialystok-mickiewicza-low30` | `mickiewicza` (`qacam=roundabout_03_above`) | Low/30 | 1,42 | 0,95 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `cab-mickiewicza-high60` | `mickiewicza` (`route_s=2038`, Cab+lusterka) | High/60 | 3,19 | 1,82 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-bialystok-kleeberga-high60` | `kleeberga` (`qacam=route_s0159`) | High/60 | 2,64 | 1,79 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-bialystok-kleeberga-low30` | `kleeberga` (`qacam=route_s0159`) | Low/30 | 1,10 | 0,79 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-knyszyn-high60` | `knyszyn` (`qacam=gardens_tykocka_eye`) | High/60 | 2,30 | 1,59 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-knyszyn-low30` | `knyszyn` (`qacam=gardens_tykocka_eye`) | Low/30 | 0,77 | 0,61 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-bialystok-krywlany-high60` | `krywlany` (`qacam=route_s0461`) | High/60 | 2,30 | 1,51 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-bialystok-krywlany-low30` | `krywlany` (`qacam=route_s0461`) | Low/30 | 0,91 | 0,57 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-monki-high60` | `monki` (`qacam=route_s0170`) | High/60 | 2,11 | 1,65 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-monki-low30` | `monki` (`qacam=route_s0170`) | Low/30 | 0,69 | 0,73 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-bialystok-industrial-c-high60` | `industrial-c` (`qacam=stretch_04`, REF) | High/60 | 1,97 | 1,69 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `city-bialystok-industrial-c-low30` | `industrial-c` (`qacam=stretch_04`, REF) | Low/30 | 0,95 | 0,76 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `cab-c-high60` | `industrial-c` (`route_s=360`, Cab+lusterka) | High/60 | 1,97 | 1,69 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `cab-c-low30` | `industrial-c` (`route_s=360`, Cab+lusterka) | Low/30 | 0,95 | 0,76 | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |

### 4C. Izolacje A/B (lusterka, `VegCardEdge`, `farRing`)

| Test A/B | Wariant A (baza) vs Wariant B | **A tris p95 / DC p95** | **B tris p95 / DC p95** | **A GPU/CPU p95 [ms]** | **B GPU/CPU p95 [ms]** | **Δ (B − A)** |
|---|---|---:|---:|---:|---:|---|
| Lusterka (`bojary`, `route_s=612`, Cab) | `ab-mirror-on` vs `ab-mirror-off` (`rq_mirror_main=0`) | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| `VegCardEdge` (`maczka`, `qacam=route_s0440`) | `ab-cardedge-on` vs `ab-cardedge-off` (`rq_cardedge=0`) | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |
| FarRing (`knyszyn-w`, `edge-north`, `stream=1`) | `ab-farring-on` vs `ab-farring-off` (`-farRing off`) | ___ / ___ | ___ / ___ | ___ / ___ | ___ / ___ | ___ |

---

## 5. Progi decyzji po pomiarach buildu #11

### 5A. Budżet miast — warianty A / B / C (`artifacts/codex-city-budget-s25/WYNIKI.md`)

Punkty odniesienia z `tools/pcperf/budgets/pc-budgets.json` (`WORKING_VALUE`):
- Klasa `zalecany` (D74): `frame_ms.p95 <= 18,5 ms`, `tris.p95 <= 6,0 M`, `draw_calls.p95 <= 4 000`; budżet D83 `High` na kamerę: `tris.p95 <= 4,0 M`, `DC.p95 <= 2 500`.
- Klasa `min` (D74): `frame_ms.p95 <= 36,0 ms`, `tris.p95 <= 2,0 M`, `draw_calls.p95 <= 2 000`; budżet D83 `Low`: `tris.p95 <= 1,5 M`, `DC.p95 <= 1 600`.
- Uwaga skalowania z `PC-BUDGET-2026-11-16.md`: na RTX 5070 przy High/60 najgorszy punkt z D83 (`maczka`) miał `3,28 ms` (zapas ~5× do `16,7 ms` na słabszym GTX 1660 / i5-9600), a na Low miał `1,85 ms` (zapas ~18× do `33,3 ms`). Jeśli pomiar #11 idzie na **RTX 5070**, próg `frame_ms <= 16,7 ms` sam nie wystarczy — trzeba patrzeć na `cpu_main_ms` / `gpu_ms` / `DC` / `tris`!

| Zmierzony wynik buildu #11 na 8 kaflach miejskich | Decyzja | Uzasadnienie i następny krok |
|---|---|---|
| **Wszystkie 9 kafli (w tym `wygoda`, `bojary` w `Cab`):**<br>• `zalecany`: `tris.p95 <= 6,0 M`, `DC.p95 <= 2 500` (lub `<= 3 000` na `bojary`/`wygoda`), na RTX 5070 `cpu_main_ms.p95 + gpu_ms.p95 <= 4,0 ms` (albo na GTX 1070/1660 `frame_ms.p95 <= 16,7 ms` i `gpu_ms.p95 <= 12,5 ms`)<br>• `min`: `tris.p95 <= 2,0 M`, `DC.p95 <= 1 600` (a dla Low `frame_ms.p50 <= 33,4 ms` — pamiętaj o błędzie progu `33,3` przy limicie 30 FPS!) | **Wariant C** *(rozszerzyć `test_budget_0221` na 54 kafle per typ)* **+ zostawić obecny stan miast (Wariant A jako baza)** | Geometria mieści się z zapasem w obu klasach PC. Wdrożyć Wariant C (progi ratchet per typ: `city_dense <= 3,60 M / 1,55 M`, `city_outer <= 2,40 M / 1,05 M`, `town <= 2,40 M / 0,85 M`, `rural <= 2,00 M / 0,70 M`, przy utrzymaniu `<= 2,00 M` na C) + poprawić estymator `frame_estimate` (frustum + pas terenu + `treeCardLodScale`) w kolejnym kroku. |
| **Graniczny zapas lub przekroczenie w `Cab` / `qacam`:**<br>• `tris.p95 > 6,0 M` **lub** `DC.p95 > 2 800` na `wygoda`/`bojary` **lub** na RTX 5070 `(cpu_main_ms + gpu_ms).p95 > 4,5 ms` (na GTX 1070 `gpu_ms.p95 > 13,5 ms` / spadki `< 60 FPS`) **lub** w `min` `tris.p95 > 2,0 M` / `DC.p95 > 2 000` | **Wariant B** *(redukcje w fali 15)* **+ Wariant C z zacieśnionymi progami** | Wdrożyć dźwignie o najmniejszym ryzyku wizualnym z `codex-city-budget-s25`:<br>1. **`B3` (`plots <= 200 m`, `furniture <= 300 m`)** — zbija 202–747 k tris i cienie;<br>2. **`B1` (`HLOD` kwartałów od 700 m + `LOD0 <= 200 m`)** — zbija draw calls;<br>3. **`B0` (`treeCardLodScale` 1,5 → 0,5–1,0 na High)** jeśli `ab-cardedge` / `maczka` pokazuje wysoki koszt GPU na liściach;<br>4. Na PC Low (`PcTierTable`): `lodBias` 1,0 → 0,75–0,80 jeśli `min` przekracza 2,0 M / 2 000 DC.<br>*(Dodatkowo, jeśli A/B `rq_mirror_main=0` daje `> 1,5 ms` na GTX 1070 lub `> 25 %` czasu CPU/GPU w `Cab`, rozważyć osobny ticket na rozdzielczość/harmonogram lusterek przy gęstych miastach.)* |
| **Jednoznaczny FAIL w `zalecany` lub `min`** przed uzyskaniem wyników z fali 15, brak czasu na przebudowę | **Wariant A (tymczasowo)** wyłącznie jako obejście do pomiaru + pilny ticket na Wariant B | Nie zamykać bramki; uruchomić B3+B1 w fali 15 i ponowić `measure.ps1` dla kafli z FAIL. |

### 5B. Daleki plan (`far_field`) — warianty A / B1 / B2 / C (`artifacts/agy-farfield-budget-s25/WYNIKI.md`)

Kontekst fali 14 (`HEAD`): `fields4` (ADR 0334 r4) dodał `forest_edge_mixed_far_atlas` (+4,3k .. +19,2k tris/kafel na High, **+0 DC**), a `neon-hvfar-s24` (ADR 0351) obniżył WN/SN (tak że w `knyszyn-w` całość `far_field` High spada z 63,9k do **53,3k**, a `dk65-07` jest na +3,6 % względem fali 12). Największe przyrosty leśne to `dw671-tykocin-04` (+20,9 %), `dk65-09` (+19,0 %), `dk65-08` (+16,6 %).

| Zmierzony wynik buildu #11 (`ref-*` vs #10 oraz A/B `ab-farring-on` vs `ab-farring-off`) | Decyzja | Uzasadnienie i następny krok |
|---|---|---|
| • Na `knyszyn-w` i `dk65-07`: brak regresji `tris.p95` / `DC.p95` / `gpu_ms` względem #10 (albo przyrost GPU `<= 0,3 ms` na GTX 1070 / `<= 0,1 ms` na RTX 5070), **oraz**<br>• A/B `-farRing on` vs `off` na `edge-north` (`-stream 1`): różnica `gpu_ms.p95 <= 0,4 ms` i brak ostrzeżeń / przekroczeń budżetu | **Wariant A / C** *(zostawić `HEAD` fali 14 bez zmian)* | Przyrost geometryczny `fields4` mieści się w marginesie błędu przy +0 DC, a `neon-hvfar-s24` kompensuje WN/SN. Opcjonalnie dla pewności dorzucić jeden przebieg `dw671-tykocin-04` lub `dk65-08` (`qacam=edge-north`). |
| • A/B `ab-farring-on` vs `off` albo porównanie `dk65-07` vs #10 pokazuje **zauważalny koszt GPU/overdraw** (`Δ gpu_ms.p95 > 0,5 ms` na GTX 1070 lub `> 0,2 ms` na RTX 5070) w `forest_edge_mixed_far_atlas` (`_HLOD_EDGE`), **ale** efekt kwater wieku i pojedynczych sosen/świerków nad okapem ma zostać | **Wariant B2** *(w fali 15)* | Przyciąć w `far_field.py`: `q == 0` i `total_s >= 24.0` w `end step-down` (`1` drzewo zamiast `3` na długich biegach) oraz `FAR_EMERGENT_STEP_M = (80, 130)`. Znika **~67–68 %** przyrostu tris przy zachowaniu sylwety ADR 0334 r4. |
| • Wyraźna regresja GPU/frame time na zalesionych kaflach lub odrzucenie wizualne „kępek” na skrętach BDOT | **Wariant B1** *(w fali 15)* | Usunąć pętlę `end_*` w `far_field.py` (zostaje `FAR_END_FLOOR = 0.30` i `overstorey`). Znika **78–79 %** przyrostu tris. |
| **Uwaga:** jeśli `ab-farring-on` vs `ab-farring-off` wykaże duży koszt samego mechanizmu `_FAR_RING_CLIP` (`discard` na `edge-north`), niezależnie od `fields4` | Osobna optymalizacja shadera `KamionFarRing.hlsl` | Sprawdzić czy `SectorVisible` wycina pełne sektory i czy clone materiału `_FAR_RING_CLIP` powoduje wzrost `batches`/`SetPass`. |
