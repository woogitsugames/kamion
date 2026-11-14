# Przegląd R8 (cloud2 mobile-gpu-a16): GPU A16 / S24+ i plan oszczędności Low (s20, 2026-11-14)

**Werdykt: FIX (lekki).** Pakiet jest rzetelny. Wszystkie kluczowe twierdzenia, które sprawdziłem, zgadzają się ze źródłami:
- enum `AndroidBlitType` i wartość `androidBlitType: 0`,
- datasheet Arm (MSAA 2× → 4×, liczby G57 na rdzeń),
- wariant S24+,
- 4 wpisy UUM,
- liczby z ADR 0013/0106/0136.

`fetch.py` przechodzi (exit 0). Seed audytu da się odtworzyć. W gicie nie ma binariów. Przedziały P1–P10 są uczciwie oznaczone jako UNVERIFIED i każdy ma metodę.

Do poprawy przed scaleniem jest **1 × P1**: P11 i P12 mają status SOURCED i są podane jako „zysk GPU (ms)” wobec celu p95 przy limicie 30 FPS. Te liczby to jednak Δ GPU **p50 bez limitu FPS** z ADR 0106. Samo repo (ADR 0136 r2c) pokazuje, że takie Δ może prawie zniknąć przy limicie: 1,29 → 0,17 ms. Poza tym są tylko uwagi P2.

## 1. Zakres i metoda
- Gałąź `origin/research/cloud2-mobile-gpu-a16` @ `2ccf5b0`, osobny worktree `/workspace/wt/review-mobile-gpu-a16` (usunięty po recenzji). `git diff --stat origin/main...HEAD` pokazuje tylko 10 plików tekstowych w `research/cloud2/mobile-gpu-a16/` (1578 linii). Nie ma PDF, obrazów ani binariów. `.gitignore` = `files/`.
- Źródła pobrałem **niezależnie** do scratchu i sprawdziłem w nich cytaty:
  - datasheet Arm: s.1 i s.2 **obejrzane jako obrazy** (s.2 w 200 dpi, wycinki Core Config/Texturing/Valhall ISA); s.3 jako tekst (noty);
  - BPG 101897 i10: s.22, 23, 61, 67, 76, 77, 95 + fragment o Fragment Prepass;
  - UnityCsReference (commit pakietu, gałąź `master`, gałąź `6000.3`);
  - Unity 6.3 Android Player settings;
  - gpuinfo 53265, 53260 i lista G57 MC2;
  - Unity Issue Tracker API: 23555, 7525, 18470, 20394;
  - gsmManiaK, Samsung Exynos 2400.
- Repo: `ProjectSettings.asset`, `ProjectVersion.txt`, `URP_Low.asset`, `DEVICE_MATRIX.md`, ADR 0013/0106/0113/0136, `REVIEW-2026-11-14-s20-gate3-phone.md`.

## 2. Tabela kryteriów
| Kryterium | Wynik |
|---|---|
| Format (README, manifest z kolumnami min. + specyficzne, sources, fetch.py, audit, STATUS z następnym krokiem, .gitignore) | **TAK** |
| fetch.py | **TAK.** `python3 -I fetch.py` z pustego `files/`: ok=28, changed=8 (strony dynamiczne, oczekiwane), errors=0, 9,4 MB. PDF Arm (sha `fae47a2f…`, `9d54788e…`), pliki GitHub i JSON trackera mają zgodne sha256 |
| Seed audytu | **TAK.** `random.Random(20261114).sample(sorted(ids), 27)` = dokładnie zbiór z `audit_20_percent.json`. FAIL R8-029 poprawiony uczciwie. Bliźniaczy R8-030 sprawdziłem: 53260 ma `maxBoundDescriptorSets 4` ✓ |
| Brak binariów w gicie | **TAK** |
| Źródła dozwolone, licencje | **TAK.** Brak Google/Bing/Apple/Yandex. Materiały producentów oznaczone jako „referencja” i niecommitowane. gpuinfo CC BY 4.0, Vulkan-Samples Apache-2.0, libGPUCounters MIT |
| Liczby z pamięci jako SOURCED | **NIE stwierdzono.** Jedyna rzecz „z pamięci” (numeracja GraphicsDeviceType, R8-101) ma status ESTIMATED z dopiskiem UNVERIFIED. Wartość sprawdziłem: 0x15 = Vulkan, 0x0b = GLES3 |
| Zgodność README ↔ manifest | **TAK**, z drobnymi wyjątkami (P2-7) |
| Dublowanie `research/` | **NIE.** Żaden inny pakiet nie zawiera Mali-G57 ani Blit Type. ADR-y są cytowane, nie przepisywane |
| Użyteczność | **TAK.** Ranking z komendą weryfikacji, „nie robić”, luki jawne (zegar GPU, szyna, sterownik na naszym A16) |

## 3. Punkty zlecone przez lidera (a)–(g)
| | Twierdzenie | Weryfikacja | Wynik |
|---|---|---|---|
| a | `androidBlitType: 0` = Always | UnityCsReference `Editor/Mono/PlayerSettingsAndroid.bindings.cs`: commit `cf583fb` (l.376–386) i `master`: `Always = 0, Never = 1, Auto = 2`. **Gałąź `6000.3` (wersja projektu 6000.3.28f1), l.222–232: identycznie.** `game/ProjectSettings/ProjectSettings.asset` l.77: `androidBlitType: 0`. Opis Always/Never/Auto w dokumentacji Unity 6.3 zgodny z R8-080 | **PASS.** P2-3: cytować gałąź 6000.3 zamiast commita z master |
| b | Datasheet: na G57 MSAA 2× jest podnoszone do 4× | s.1 obejrzana: wiersz „2xMSAA” ma scalony napis *„Automatically promoted to 4xMSAA”* przez kolumny Mali-G71 … Immortalis-G715 (w tym G57). ✓ od G720 | **PASS** |
| b′ | Sprzeczność z ADR 0013 | ADR 0013 (A16, Medium, las DK8, GPU p50): 4× 61,3 ms, 2×/1× 50,4/50,4 ms. Dla Kamion/Vegetation: 64,7 vs 36,9 ms. ADR 0106: 2×→1× = 0. Jeśli 2× = 4× w sprzęcie, koszty 2× i 4× powinny być równe, a zmierzone są bardzo różne. **Wniosek o sprzeczności jest uczciwy.** Hipotezy mają status UNVERIFIED, a rozstrzygnięcie zaproponowano narzędziem (RenderDoc for Arm: liczba próbek przy `msaa: 2`). Zastrzeżenia w P2-1 i P2-2: w tabelach podano „2 = 4× w sprzęcie” jak fakt; brak jednej obserwacji gpuinfo | **PASS** (z P2) |
| c | G57 na rdzeń | s.2 (obraz 200 dpi), kolumna Mali-G57: Arithmetic units 2, warp 16, threads 1024, **FP16 128, FP32 64**, Fragments 2, **Pixels 2**, **Texels 4** (Bilinear 4), texture cache 32K, **Tile bits/pixel 256**. Depth format with reference ×2, ASTC bez decode_mode ×2. Valhall ISA: 33–64 rejestry → 512 wątków. Brak Fragment Prepass: BPG — *„From Mali-G725 and Immortalis-G925 onwards, there is a new feature called Fragment Prepass.”* (wniosek dla G57 poprawny) | **PASS.** P2-6: datasheet nie pisze dosłownie „na rdzeń” |
| d | S24+ PL = Exynos 2400 / Xclipse 940 | `docs/DEVICE_MATRIX.md` l.6: SM-S926B, `Samsung Exynos 2400 (s5e9945)`, `Xclipse 940 (RDNA3-based; ro.hardware.egl=samsung)`, nota „Measured … via adb shell getprop”. Samsung: *„The Exynos 2400 features an Xclipse 940 GPU, built on AMD RDNA™ 3”*, *„hexa-core GPU”* ✓. gsmManiaK: cytat dosłownie zgodny ✓, ale artykuł jest z **2024-01-09**, sprzed premiery (*„To już w zasadzie pewne”*) | **PASS.** P2-5: surowego zrzutu getprop S24+ nie ma w repo; Xclipse 940 wywnioskowano z nazwy SoC; prasa to prognoza |
| e | UUM w trackerze | Wszystkie 4 istnieją (API `externalKey`). **UUM-147578**: 6000.3.X fixedInVersion `6000.3.28f1` (released) ✓; Redmi Note 11S / Mali-G57 MC2 na liście „Not reproducible” ✓. **UUM-137912**: 6000.3.X status open ✓, 6000.6 fix `6000.6.3f1` ✓; A15 5G / G57 MC2 „Not reproducible” ✓ (reprodukcja na A54/A25). **UUM-28518**: tytuł i stos ✓, G57 MC2 na liście GPU klienta ✓; README pomija stan (state 102, porty 2020.3/2021.3 status 4, zgłoszenie z 2020.3.31f1). **UUM-107530**: ✓ Adreno 618, Mali G76/G77/G78/G710 nie reprodukują; README pomija stan (state 103 dla 2022.3/6000.0/6000.1, bez `fixedInVersion`) | **PASS.** P2-4: dopisać stan |
| f | P1–P10 jako UNVERIFIED z uzasadnieniem | R8-119…R8-128: wszystkie UNVERIFIED, każdy ma `metoda` (mechanizm + źródło + sposób szacunku) i `weryfikacja`. Żaden nie jest przebrany za SOURCED. Słabsze miejsca: górna granica 1,5 ms dla P1/P2 bez rachunku (P2-8). **Problem jest w P11/P12 (SOURCED)**, patrz P1-1 | **PASS dla P1–P10**; P11/P12 → P1-1 |
| g | ADR 0106/0136 | 0106: LOD bias ×0,6 = **1,4** ✓; far 900→720 = **0,7** ✓; szyba 3,6–4,3, raster+blend ≈1,2 ✓; MSAA 2×→1× = 0 ✓; HLOD ściany 1,8 ✓. 0136: governor przy limicie 30 FPS *„dodaje ~1,5–2 ms”* ✓ (użyte poprawnie: to nie te same „1,5–2 ms” co treść s11–s12); impostory 1,37→0,51 ✓ (−0,86); auta +1,29 GPU ✓; cull 100 m −0,17 ✓; 25 m/512 px = szum ✓; versionCode ✓; cytat „wymaga zmiany treści, nie cięcia profilu” ✓. Gate3 GPU p95 34,28/34,51 ✓ | **PASS** (kontekst pomiaru → P1-1) |

## 4. Moja próbka (seed 777, `random.Random(777).sample(sorted(ids), 14)` = 10,4 %)
| id | Co sprawdziłem | Wynik |
|---|---|---|
| R8-001 | DEVICE_MATRIX l.5: SM-A165F, MT6789, Mali-G57 MC2 | PASS |
| R8-011 | datasheet s.2 (obraz): FP16 ops/cycle G57 = 128 | PASS |
| R8-020 | datasheet s.1 (obraz): FP16/R11G11B10 accelerated blending ✓ od G57 | PASS |
| R8-027 | gpuinfo JSON: recordsFiltered 396; 53265 (54.1.0/1.3.303/17.0) i 53260 (32.1.0/1.1.177/14.0) | PASS |
| R8-030 | 53265: `maxBoundDescriptorSets 7`; 53260: `4` | PASS |
| R8-031 | 53265: subgroupSize 16, operacje ✓ (w `wartość` brak `partitioned_bit_nv`, nieistotne) | PASS |
| R8-059 | Qualcomm md: „MSAAx2 is likely to be practically free” | PASS |
| R8-070 | BPG s.76: trilinear / 3D / FP32 2×, mipmapy | PASS |
| R8-074 | BPG s.95: „Global world position. UI texture coordinates.” | PASS |
| R8-086 | Qualcomm md: LAZILY_ALLOCATED … „especially MSAA attachments” | PASS |
| R8-087 | Unity URP configure-for-better-performance: „disable LOD Cross Fade” | PASS |
| R8-095 | BPG s.77: „one cycle per texel … manually de-rate” | PASS |
| R8-100 | ProjectVersion.txt: 6000.3.28f1 | PASS |
| R8-115 | URP_Low.asset: renderScale 0.75, MSAA 2, HDR 0, depth/opaque 0, 1024, 1 kaskada, 35, soft 0, SRP Batcher 1 | PASS |

Dodatkowo, poza losowaniem (punkty a–g): R8-010, 012, 013, 014, 019, 021, 038–041, 053, 055, 080, 081, 096–099, 101, 110, 117, 119–133. Wszystkie zgodne co do cytatu i liczby. **Wynik: 14/14 PASS w próbce, 0 FAIL.**

## 5. Uwagi

### P0 (blokuje PR)
Brak.

### P1 (musi być poprawione przed scaleniem)
1. **R8-129 (P11), R8-130 (P12), README §4 kolumny „Zysk GPU” i „Status liczby”.** Wartości 0,7 i 1,4 ms to Δ **GPU p50 bez limitu FPS** (ADR 0106: „G3-B Low, bez limitu, … `rq_ab`”), zmierzone na treści sprzed s11. README stawia je obok celu **GPU p95 przy limicie 30 FPS** i przy P12 opisuje jako „największą zmierzoną dźwignię”. ADR 0136 r2c pokazuje, że Δ bez limitu może nie przełożyć się na p95 przy limicie: auta +1,29 ms bez limitu, a cull 100 m przy limicie daje −0,17 ms. Dolne granice przedziałów (1,0 i 0,5 ms) nie mają źródła.

   **Poprawka:**
   - w `metoda`/`uwagi` R8-129/130 i w README zapisać: „Δ GPU p50 bez limitu (0106), treść sprzed s11; zysk p95 przy limicie 30 FPS UNVERIFIED, może być znacznie mniejszy (0136 r2c)”;
   - przedział zysku dać jako UNVERIFIED (np. „0–1,4”) albo podać tylko zmierzoną liczbę z tym kontekstem;
   - SOURCED zostawić wyłącznie dla samej liczby z 0106.

### P2 (sugestie)
1. **README §1 „Cechy G57” i §2 wiersz MSAA** („MSAA 2 (= 4× w sprzęcie G57)”): to twierdzenie Arm, a pomiar repo mu przeczy (§2 „Sprzeczność”). Napisać „wg Arm 2× → 4×; pomiar 0013/0106 temu przeczy (do zbadania)”. Teraz tabela podaje to jak fakt, a sekcja niżej jak hipotezę.
2. **Hipotezy MSAA (README §2, R8-019).**
   - Dopisać obserwację: gpuinfo 53265 ma `framebufferColorSampleCounts 1, 2, 4, …`, więc sterownik Vulkan ogłasza 2×. Ewentualny spadek do 1× musiałby zachodzić po stronie Unity/URP, a nie przez brak obsługi 2× w API.
   - Zaznaczyć, że wniosek ADR 0113 („koszt lasu = rasteryzacja/pokrycie, A2C przy MSAA 2×”) zależy od rozstrzygnięcia: przy 1× A2C działa inaczej.
3. **R8-081 / S15:** commit `cf583fb` pochodzi z `master` (enum w l.376). Dla wersji projektu podać `https://github.com/Unity-Technologies/UnityCsReference/blob/6000.3/Editor/Mono/PlayerSettingsAndroid.bindings.cs` (l.222–232; wartości identyczne) albo SHA tej gałęzi.
4. **R8-098, R8-099, README §3:** dopisać stan zgłoszeń.
   - UUM-28518: zamknięte (state 102), porty tylko 2020.3/2021.3 ze statusem 4, zgłoszenie z 2020.3.31f1; dla 6000.3 brak danych.
   - UUM-107530: state 103 dla 2022.3/6000.0/6000.1, bez `fixedInVersion`.
5. **R8-038/R8-040:**
   - Zaznaczyć, że w repo nie ma surowego zrzutu getprop S24+, tylko wpis w DEVICE_MATRIX (nota o getprop odnosi się do serialu A16).
   - „Xclipse 940” wynika z nazwy SoC `s5e9945`, nie z odczytu GL_RENDERER ani Vulkan `deviceName` na naszym telefonie.
   - gsmManiaK (2024-01-09) to prognoza sprzed premiery („w zasadzie pewne”). Dowodem rozstrzygającym jest getprop (+ gpuinfo 7/8).
6. **R8-010…014 „na rdzeń”:** datasheet pisze „specs of the chips” i „Thread count is the total shader core hardware capacity”, a nie dosłownie „per core”. Interpretację dopisać w `metoda` (jest poprawna, ale wywnioskowana).
7. **README nagłówek** „fetch.py: 27 plików, 9,4 MB” a fetch.py obsługuje 36 pozycji (26 sieciowych + 10 z repo; STATUS mówi 36). Ujednolicić.
8. **R8-119 (P1 Blit)** i **R8-120 (P2):**
   - Górna granica 1,5 ms nie ma rachunku. Dopisać wariant pasma albo obniżyć ją do rzędu jednego przebiegu.
   - Dopisać jawnie jako UNVERIFIED, czy `androidBlitType` w ogóle zmienia ścieżkę swapchainu na **Vulkan** w 6000.3 (dokumentacja tego nie precyzuje). RenderDoc i Frame Debugger są już w planie, ale ryzyko „0 ms, bo nie dotyczy Vulkana” powinno być w tabeli.
9. **README §2 „depth prepass … nie ruszać ✓”:** Depth Priming jest off, ale w samym projekcie są prepassy per materiał:
   - Kamion/Vegetation ma pass głębi + pass koloru (ADR 0013);
   - ściany HLOD to „depth prepass + A2C”, 1,8 ms (ADR 0106).

   Rada Arm (BPG s.23) dotyczy też ich. Warto podlinkować przy P3/P7, np. „sprawdzić 1 przebieg z early ZS zamiast prepassu dla ścian HLOD”, co odpowiada otwartemu punktowi 1 w 0106.
