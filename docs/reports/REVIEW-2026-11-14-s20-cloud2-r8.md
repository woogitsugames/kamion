# Przegląd PR #59 — R8 mobile-gpu-a16 (cloud2) — s20, 2026-11-14

**Werdykt: SCAL z erratą.** Pakiet jest dokumentowy (bez kadrów). Twierdzenia, które sprawdziłem sam, zgadzają się ze źródłami: datasheet Arm, BPG, enum `AndroidBlitType` na gałęzi 6000.3, `androidBlitType: 0` w repo, URP_Low i liczby z ADR 0013/0136. Dla ADR 0106 sprawdziłem l.21 („G3-B Low, bez limitu … `rq_ab`”) oraz l.38–39 („far clip 900 → 720 / 450 m | 0,7 / 1,4”, „LOD bias ×0,6 | 1,4”). Jedyne P1 recenzji wewnętrznej (P11/P12 jako zysk p95) jest jednak poprawione **tylko w README**. W manifeście zostały dolne granice 0,5/1,0 ms i zdanie o „największej zmierzonej dźwigni”, a nagłówek README ma nieaktualne liczniki statusów. Do tego `fetch.py` wysyła w User-Agent nazwę projektu, czego zabrania prompt chmury. To dwie szybkie poprawki tekstowe, które nie zmieniają wniosków, dlatego werdykt to errata, a nie FIX.

- Gałąź `origin/research/cloud2-mobile-gpu-a16` @ `eb7986f32` (PR #59, OPEN, nie draft). Ma 7 commitów, a fix P1 jest w `eb7986f` (17:36 UTC).
- `git diff --stat main...`: 11 plików, wyłącznie w `research/cloud2/mobile-gpu-a16/`. Są tekstowe, `.gitignore` = `files/` ✓.
- `python -I fetch.py` uruchomiłem dwa razy w kopii poza repo. Uwaga: skrypt wysłał przy tym User-Agent z nazwą projektu (E5); nie uruchamiać go ponownie przed poprawką. Wynik: sieć ok = 18, changed = 9 (strony dynamiczne, ostrzeżenie zgodnie z projektem skryptu), sha256 PDF Arm zgodne (`fae47a2f…`, `9d54788e…`). 9 × MISSING to pliki repo, oczekiwane poza worktree.
- Nic nie scalono, nic nie scommitowano, PR bez komentarza.

## 1. P1 z REVIEW.md — czy naprawdę poprawione

| Wymóg recenzji | Stan na `eb7986f` | Wynik |
|---|---|---|
| R8-129/130: status SOURCED → UNVERIFIED, z kontekstem „Δ GPU p50 bez limitu (0106), treść sprzed s11, p95 przy limicie 30 FPS niezmierzone (0136 r2c)” | `status` = UNVERIFIED ✓. Adnotacja `[REVIEW P1: …]` w `weryfikacja` ✓ | **TAK** |
| README §4: zysk jako „0–1,4” / „0–0,7” | README P12 „0–1,4”, P11 „0–0,7”, kolumna statusu z kontekstem ✓ | **TAK** |
| Dolne granice bez źródła usunąć | **Manifest nadal ma `zysk_ms_min` = 0,5 (R8-129) i 1,0 (R8-130)**, a `wartość` = „zmierzone 0,7/1,4 ms (ADR 0106)” bez kontekstu | **NIE** → E1 |
| Nie nazywać P12 zmierzoną dźwignią wobec p95 | **R8-130 `uwagi`: „największa zmierzona dźwignia profilu poza skalą”** | **NIE** → E1 |
| Spójność README ↔ manifest | Nagłówek README l.4: „SOURCED 117, UNVERIFIED 13, ESTIMATED 4”. **Manifest po fixie: 115 / 15 / 4** | **NIE** → E2 |

## 2. Tezy zlecone przez lidera

### 2a. `androidBlitType: 0` (game/ProjectSettings/ProjectSettings.asset)
- `game/ProjectSettings/ProjectSettings.asset:77` `androidBlitType: 0` ✓. Sąsiednie wpisy to `androidUseSwappy: 1` (l.75), `vulkanEnablePreTransform: 1` (l.144) i `vulkanNumSwapchainBuffers: 3` (l.142). `m_APIs: 150000000b000000` (l.543) oznacza Vulkan (0x15) przed GLES3 (0x0b).
- Enum sprawdziłem sam na gałęzi **6000.3** UnityCsReference (`Editor/Mono/PlayerSettingsAndroid.bindings.cs`): `Always = 0, Never = 1, Auto = 2` ✓. Wersja projektu to 6000.3.28f1.
- Dokumentacja 6000.3 (strona przeniesiona na docs.unity.com) mówi: Always = offscreen + blit, „usually slower”; Never/Auto = framebuffer OS. Opis Blit Type **nie wspomina Vulkana**. Sprawdziłem to przez WebFetch (streszczenie strony z cytatami), a nie przez ręczną lekturę całej strony.
- **Moja ocena:** mechanizm jest poprawnie zacytowany. Czy na Vulkanie w 6000.3 `Always` faktycznie dokłada przebieg pełnoekranowy (obok końcowego blitu URP przy renderScale 0,75 i pre-rotation), **nie wiadomo**. Dolna granica 0,3 ms w P1 (R8-119) nie ma więc oparcia. Uczciwy przedział to **0–1,5 ms, z możliwym „no-op na Vulkanie”**. Recenzja wewnętrzna zgłosiła to jako P2-8, a wykonawca tego nie poprawił. Errata E3.
- W repo nikt nie ustawia tej wartości kodem: `git grep blitType` w `game/Assets/**/*.cs` daje 0 trafień, więc `ProjectSetup.ApplyAll` jej nie zarządza. Wartość 0 to prawdopodobnie domyślne ustawienie Unity (UNVERIFIED), a nie decyzja projektu. Żaden ADR jej nie opisuje.

### 2b. MSAA na Mali-G57 vs ADR 0013
- Datasheet Arm s.1 obejrzałem przy 100 dpi oraz wycinek 3× przy 250 dpi. W wierszu „2xMSAA” jest scalona komórka „Automatically promoted to 4xMSAA” dla kolumn od Mali-G71 do Immortalis-G715, w tym G57. ✓ od G720.
- ADR 0013 (`docs/adr/0013-foliage-shader-and-medium-msaa.md`) dla A16, **Medium z HDR i post**, las DK8, GPU p50:
  - baseline 4× 61,3 ms;
  - **2× / 1× = 50,4 / 50,4 ms** (identyczne);
  - Vegetation 4× 64,7 vs 2× 36,9;
  - Lit 61,6 vs 50,4.
- „2× = 1× co do 0,1 ms” przy „4× ≫ 2×” to wynik odwrotny do „2× promowane do 4×”. **Sprzeczność istnieje i pakiet ją uczciwie nazywa.** Dodaję dwie obserwacje, których pakiet nie ma:
  1. ADR 0013 r4 pokazuje **ten sam wzór 4× ≫ 2× na S24+ (Xclipse 940, RDNA3, nie Mali)**: Vegetation 31,3 vs 18,0 ms, Lit 38,7 vs 21,6. Mechanizm specyficzny dla Arm (promocja, bufor kafla 256 bit/px) nie wyjaśnia więc różnicy 4×/2× na obu telefonach. Bardziej prawdopodobna jest przyczyna po stronie Unity/URP, np. ścieżka resolve lub zapis próbek przy 4×. Status: UNVERIFIED.
  2. Pomiary 0013 dotyczą Medium z HDR. Low (URP_Low.asset: `m_SupportsHDR: 0`, `m_MSAA: 2`, `m_RenderScale: 0.75`) nie był mierzony 4× vs 2×. ADR 0106 dla Low podaje tylko 2× → 1× = 0.
- README §1 i §2 nadal piszą „MSAA 2 (= 4× w sprzęcie G57)” jak fakt (P2-1 recenzji). Errata E4.
- Rada BPG s.23 („Avoid using depth prepasses”, obejrzana) **nie przenosi się automatycznie** na `Kamion/Vegetation`. ADR 0013 zmierzył na A16 Vegetation (depth pass + color pass) 36,9 ms wobec Lit 50,4 ms przy 2×. Prepass nie był tam izolowany, ale całość jest zmierzonym zyskiem. Nie usuwać go na podstawie BPG bez A/B.

## 3. Moja kontrola (10 obrazów, ≥ 5 liczb u źródła)

| # | Obraz | Sprawdzone | Wynik |
|---|---|---|---|
| 1 | Arm datasheet s.1 (100 dpi) | 2xMSAA → 4×; FP16/R11G11B10 accelerated blending od G57; Vulkan 1.0–1.3 | ✓ R8-019, R8-020 |
| 2 | s.1, wycinek wiersza MSAA (250 dpi) | zakres scalonej komórki G71…G715 | ✓ |
| 3 | datasheet s.2 (100 dpi) | Valhall ISA: G57 33–64 rejestry → 512 wątków; tekstury: trilinear ×2, depth z referencją ×2, ASTC bez decode_mode ×2 | ✓ R8-012…014 |
| 4 | s.2, wycinek 3× kolumny G57 (250 dpi) | 2 ALU, warp 16, 1024 wątki, FP16 128, FP32 64, 2 px/cykl, 4 teksele/cykl, tekstury 32K, tile 256 bit/px | ✓ R8-010…014 |
| 5 | BPG s.22 | „Do not use discard … forces a late ZS test”; A2C to samo | ✓ R8 tabela §2 |
| 6 | BPG s.23 | §3.5 „Avoid using depth prepasses”, FPK | ✓ (patrz zastrzeżenie §2b) |
| 7 | BPG s.61 | „Use 4x MSAA as it is not expensive”; 3,9 GB/s vs 500 MB/s | ✓ |
| 8 | BPG s.67 | blending wyłącza early ZS i FPK; unorm zamiast float | ✓ |
| 9 | BPG s.76 | trilinear 2×, FP32 2×, depth z porównaniem 2× (Valhall), mediump samplery | ✓ R8-070 |
| 10 | BPG s.77 | Mali Offline Compiler „one cycle per texel … manually de-rate” | ✓ R8-095 |

Repo (tekst): `ProjectSettings.asset:77` ✓, URP_Low l.26–66 (HDR 0, MSAA 2, scale 0,75, cienie 1024 / 1 kaskada / 35 m / soft 0) ✓, ADR 0013 tabela ✓, ADR 0136 l.14 (governor „~1,5–2 ms”) ✓, l.90 (+1,29) i l.132 (cull 100 m −0,17) ✓. DEVICE_MATRIX l.5–6: A16 = Mali-G57 MC2 „per MT6789 spec, confirm via GL_RENDERER” (nazwa GPU też jest wnioskiem, nie odczytem), S24+ = Exynos 2400 / Xclipse 940 ✓.

Licencje i zakazy: materiały producentów oznaczone są jako referencja, a pliki nie są w gicie. gpuinfo jest na CC BY 4.0. Jedyne trafienie „google” to strona AGI na developer.android.com (narzędzie, nie mapy) ✓. **User-Agent: `fetch.py:23` `UA = "Mozilla/5.0 (research fetch; kamion R8)"` zawiera nazwę projektu.** Prompt chmury (dokończenie) każe w User-Agent używać „tylko ogólnej nazwy klienta, bez nazw organizacji/repo” → E5.

## 4. Errata (do wklejenia autorowi; **E1, E2 i E5 wymagane, zanim ktokolwiek użyje manifestu**, bo `zysk_ms_min` 1,0 nadal stawia P12 na pierwszym miejscu w sortowaniu po zysku)

```
R8 errata — gałąź research/cloud2-mobile-gpu-a16 (tylko research/cloud2/mobile-gpu-a16/):
E1. make_manifest.py → manifest.csv: R8-129 zysk_ms_min 0,5 → 0; R8-130 zysk_ms_min 1,0 → 0;
    `wartość` obu: „Δ GPU p50 bez limitu FPS 0,7 / 1,4 ms (ADR 0106, treść sprzed s11); p95 przy limicie: UNVERIFIED”;
    R8-130 `uwagi`: usunąć „największa zmierzona dźwignia profilu poza skalą”.
E2. README l.4: liczniki statusów po fixie = SOURCED 115, UNVERIFIED 15, ESTIMATED 4 (przeliczyć z manifest.csv).
E3. R8-119 (P1 Blit) i README §4: zysk „0–1,5 (UNVERIFIED; dokumentacja Unity 6.3 nie mówi, czy Blit Type
    działa na Vulkanie — możliwe 0 ms)”; dolną granicę 0,3 usunąć; źródło enum: UnityCsReference gałąź 6000.3
    (Editor/Mono/PlayerSettingsAndroid.bindings.cs, Always = 0) zamiast commita z master.
E4. README §1 „Cechy G57” i §2 wiersz MSAA: „wg Arm 2× → 4× w sprzęcie; pomiar ADR 0013 (2× = 1×, 4× ≫ 2×) temu
    przeczy; ten sam wzór 4× ≫ 2× na Xclipse 940 (ADR 0013 r4) — przyczyna raczej po stronie Unity/URP (UNVERIFIED)”.
E5. fetch.py l.23: UA = "research-fetch/1.0" (bez nazwy projektu/pakietu).
E6. (P2 z REVIEW.md, opcjonalnie) P2-4 stan UUM-28518/107530, P2-5 S24+ getprop, P2-7 liczba plików fetch, P2-9 prepassy per materiał.
```

## 5. Wnioski dla gry (rendering-perf / lider)

1. **P8 przed wszystkim:** mierzyć GPU w cyklach lub przy stałym zegarze. Governor przy limicie 30 FPS dodaje ~1,5–2 ms (ADR 0136), więc bez tego A/B poniżej 1 ms jest szumem.
2. **Blit Type** (`game/ProjectSettings/ProjectSettings.asset:77`):
   - test: para APK `androidBlitType` 0 vs 2 (Auto), ten sam versionCode, `pwsh scripts/device-metrics.ps1 -Launch -DurationSeconds 90` na G3-A/G3-B;
   - przed APK: Frame Debugger/RenderDoc, czy na Vulkanie w ogóle znika jeden przebieg;
   - przy zysku: zmiana **tylko przez lidera**, jako kod w `Game.Editor.Setup.ProjectSetup.ApplyAll` (dziś wartość jest niezarządzana) + nowy ADR. `Never` odrzucić (ryzyko czarnego ekranu na części urządzeń).
3. **MSAA:** sprzeczności 2×/4× nie da się rozstrzygnąć bez telefonu. RenderDoc for Arm na A16 przy `m_MSAA: 2` pokaże liczbę próbek załącznika. Do tego czasu nie opierać decyzji Low na „2× = 4× w sprzęcie”.
4. **Nie robić na Low:** depth/opaque texture, soft shadows, FXAA, HDR, DoF Bokeh (UUM-137912 otwarte na 6000.3). Nie usuwać prepassu `Kamion/Vegetation` bez A/B (§2b).
5. Ranking z README (P8 → P1 → P3 → P4 → P6, potem P11/P12 jako decyzje właściciela) jest rozsądny jako kolejność testów. Wszystkie zyski są UNVERIFIED.
