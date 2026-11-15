# ADR 0241: A/B GPU na A16 Low — przełączniki uruchomieniowe, katalog wariantów i skrypt sesji pomiarowej

Status: propozycja (rendering-perf, chmura D runda 2 / F8, gałąź `gpu-ab-0241` z main `25924f60b`), 2026-11-15.
**Kod C# nieskompilowany i skrypt PowerShell nieuruchomiony w chmurze** (brak Unity, pwsh i telefonu) — weryfikuje lider.
Powiązane: B-113 (`docs/owner/BACKLOG-S21.md`), ADR 0106 (rozkład GPU A16, `rq_ab`), 0113, 0136, 0013, 0046 (adaptacyjna skala),
R8 `research/cloud2/mobile-gpu-a16/` (+ errata `docs/reports/REVIEW-2026-11-14-s20-cloud2-r8.md`), F6 = ADR 0239 (płoty Low),
F7 = ADR 0240 (cienie Low), D50 (bez skali < 0,75 na Low).

## Kontekst
Bramka 3 na A16 (Mali-G57 MC2), Low, limit 30 FPS, APK `77cfd94bf8`: GPU p50 32,1 ms (G3-A) / 31,3 (G3-B), GPU p95 34,3–34,5 ms
przy budżecie 33,3 ms (HANDOVER s20, 14.11 07:4x–08:0x; `REVIEW-2026-11-14-s20-gate3-phone.md`). Każda nowa treść dokłada ms, a
rozkład z ADR 0106 pochodzi z treści sprzed s11 i z pomiaru bez limitu klatek; R8 pokazał, że taka różnica przy limicie 30 FPS może
prawie zniknąć (ADR 0136 r2c: 1,29 → 0,17 ms). Brakowało jednego, powtarzalnego sposobu: ten sam APK, lista wariantów, powtórzenia,
kontrola temperatury i blokady telefonu, jedna tabela.

Stan zastany (sprawdzony w kodzie): większość przełączników już jest — `RenderOverrides` czyta argumenty uruchomienia
(Android: intent extras `am start -e klucz wartość`, `AndroidPlatformServices.GetLaunchArgument` → `getStringExtra`; tak samo
`build-android.ps1 -Tier/-Fps` przekazują `tier`/`fps`, a `device-metrics.ps1 -Extra k=v,…` dowolne klucze). Istnieją: `rq_scale`,
`rq_msaa`, `rq_post`, `rq_shadow` (0 = cienie wyłączone), `rq_lod`, `rq_far`, `rq_thin`, `rq_cull`, `rq_card`, `rq_hlod`,
`rq_trees`, `rq_mirror_off`, `rq_glassfast` oraz przeplatane okna `rq_ab` (ADR 0106). Brakowało: kopii głębi / koloru (URP depth /
opaque texture) i wyłączenia impostorów oraz części HLOD lasu **na cały przebieg** (były tylko jako klucze `rq_ab`).

## Decyzja
1. **Nowe przełączniki** w osobnym pliku `Game.Rendering.GpuAbOverrides` (`game/Assets/_Project/Rendering/Runtime/GpuAbOverrides.cs`):
   `rq_depthtex 0|1`, `rq_opaquetex 0|1` (zapis do aktywnego assetu URP tylko w pamięci, jak dotychczasowe `rq_msaa`),
   `rq_impostors 0`, `rq_hlodpart 1|2` (te same haki `WorldInstances`, których używa `rq_ab`: `AbImpostorOff`, `AbHlodPart`),
   `rq_abtag <id>` (etykieta wariantu; tylko log `[GPUAB] … abtag=<id>`, nie włącza ścieżki override). Haki w istniejącym kodzie:
   trzy jednowierszowe (`RenderOverrides.Any`, `RenderOverrides.Parse`, `QualityProfileApplier.ApplyPipelineOverrides`) + ogon linii logu.
2. **Żadne ustawienie domyślne się nie zmienia.** Nie dotknięto `QualityProfile.cs`, `QualityProfile.asset`, `ProjectSetup.cs`,
   assetów URP ani `ProjectSettings/`. Bez argumentu każdy przełącznik jest `null`, współdzielone flagi A/B nie są zapisywane,
   `RenderOverrides.ApplyTo` zwraca tier bez zmian — pilnują tego testy EditMode `GpuAbOverridesTests` (m.in.
   `NoArguments_EveryDefaultTierIsUnchanged`, `NoArguments_PipelineAssetIsNotWritten`, `TagAlone_IsLoggedButChangesNothing`).
3. **Katalog wariantów jako dane**: `tools/perf/gpu-ab-variants.json` — 26 wariantów (9 domyślnych), każdy = zestaw `rq_*`,
   rola (`lever` kandydat, `ceiling` pułap przez wyłączenie, `control` zmiana o znanym kierunku, `diagnostic` poza D50) i szacunek
   zmiany GPU p50 ze statusem i źródłem. Test pytest sprawdza, że każdy klucz katalogu jest czytany przez źródła gry.
4. **Skrypt sesji** `scripts/gpu-ab-a16.ps1` (domyślnie `-Serial RFGL34SJYDZ -Tier Low -Fps 30`): jedna instalacja APK, potem dla
   każdego powtórzenia (≥ 3) i miejsca bloki „baza + do 4 wariantów” (`-BaselineEvery`), kolejność wariantów odwracana w parzystych
   powtórzeniach. Każdy przebieg = `device-metrics.ps1 -Launch …` z tymi samymi argumentami co `gate3-run.ps1` (tryb `Drive`:
   odcinki G3-A/G3-B, autopilot 30 km/h, 40 t, rozgrzewka 25 s; tryb `Camera`: stała kamera bramki, 60 s, rozgrzewka 20 s).
   Przed przebiegiem: bateria < 36 °C (inaczej `am force-stop` i czekanie, po 20 min koniec sesji), poziom ≥ 20 %, brak keyguarda,
   ekran `Awake`. Po przebiegu: keyguard, status termiczny < 2, log startu autopilota/kamery, linia `[GPUAB] … abtag=<wariant>`
   (dowód, że APK zna przełączniki i argumenty doszły). Przebieg odrzucony zapisuje się z `valid=false` i nie wchodzi do tabeli.
   Blokada `PHONE_RUN` jak w `gate12-phone.ps1`; dzieci `pwsh` przez `Start-Process` bez potoku (zawieszenie z s20).
5. **Parser i tabela**: `tools/perf/src/perfgate/gpuab.py` (`python -m perfgate.gpuab report <sesja>`) → `results.csv` (przebieg),
   `summary.csv` i `REPORT.md` (wariant × miejsce: mediany klatki p50/p95/p99, GPU p50/p95, CPU, PSS, temperatura przed/po, termika,
   liczba klatek > 40 ms). Różnica = wariant − baza **z tego samego bloku**; „istotne” tylko gdy wszystkie pary mają ten sam znak,
   par ≥ 3 i |mediana| > rozrzut bazy. Percentyle jak w `device-metrics.ps1` (nearest-rank po rozgrzewce). Gdy przebieg ma okna
   `rq_ab`, raport podaje też B − A z kolumny `ab` (bez klatek 0,75 s po przełączeniu). Raport ostrzega o zmianie skali renderu
   w trakcie przebiegu (adaptacyjna skala, ADR 0046) i o braku próbek GPU.

## Oczekiwany zysk per wariant (ŻADNA liczba nie jest pomiarem tej rundy)
Δ GPU p50 w ms, ujemna = zysk. „0106” = `docs/adr/0106-perf-low-a16-r1.md`, tabela „Rozkład GPU klatki”: A16 Low, G3-B, **bez limitu
FPS**, okna `rq_ab`, treść sprzed s11 — przy limicie 30 FPS i dzisiejszej treści wartości mogą być wyraźnie mniejsze (R8 REVIEW P1-1).

| wariant (domyślny ✓) | argumenty | rola | szacunek Δ GPU p50 | status | źródło |
|---|---|---|---|---|---|
| `scale-070` ✓ | `rq_scale 0.7` | lever (D50!) | −2,0 | ESTIMATED | 0106: 0,75 → 0,70 |
| `scale-065` / `scale-080` | `rq_scale 0.65` / `0.8` | diagnostic / control | −3,3 / +1,8 | ESTIMATED | 0106; +1,8 = 13 ms × (0,8²/0,75² − 1), 13 ms „zależne od pikseli” z 0106 |
| `msaa-1` ✓ | `rq_msaa 1` | lever | 0 | ESTIMATED | 0106, 0013; sprzeczność z datasheetem Arm (R8 §2) do rozstrzygnięcia z RenderDoc |
| `msaa-4` | `rq_msaa 4` | control | brak liczby | UNVERIFIED | 0013: +10,9 ms w lesie DK8 na Medium, dla Low G3 brak |
| `depthtex-on` ✓ | `rq_depthtex 1` | control | ≥ +0,36 | UNVERIFIED | R8 §1: pełnoekranowa warstwa 1,42 Mpx ≈ 0,36 ms przy założonym 1 GHz (zegar GPU UNVERIFIED); górna granica nieznana (MSAA) |
| `opaquetex-on` ✓ | `rq_opaquetex 1` | control | ≥ +0,36 (kopia pomniejszona może być tańsza) | UNVERIFIED | jw. |
| `post-on` / `post-off` | `rq_post 1` / `0` | control / lever (Medium) | brak liczby | UNVERIFIED | 0106: Medium = +16 ms łącznie (HDR + post + skala + detail + kaskady) |
| `shadows-off` ✓ | `rq_shadow 0` | ceiling | −0,9 | ESTIMATED | 0106: cienie (dystans 0) |
| `shadow-25` / `shadow-50` | `rq_shadow 25` / `50` | lever / control | 0 (szum ±0,3) / brak liczby | ESTIMATED / UNVERIFIED | 0136 r2c: 25 m / 512 px = szum |
| `lod-030` ✓ / `lod-040` | `rq_lod 0.3` / `0.4` | lever | −1,4…0 | ESTIMATED | 0106: LOD bias ×0,6 = 1,4; R8 P12: 0–1,4 przy limicie |
| `far-720` | `rq_far 720` | lever | −0,7…0 | ESTIMATED | 0106: 900 → 720 m; R8 P11 |
| `trees-off` | `rq_trees 0` | ceiling | −3,0…−2,4 | ESTIMATED | 0106 (przed 0113/0136 — dziś mniej) |
| `impostors-off` ✓ | `rq_impostors 0` | ceiling | −0,5 (G3-B; G3-A ≈ 0) | ESTIMATED | 0136: impostory 1,37 → 0,51 ms po ImpostorTrim |
| `hlod-walls-off` ✓ | `rq_hlodpart 2` | ceiling | −1,8…−1,5 | ESTIMATED | 0106: 1,8; 0113: ściany jednoprzebiegowo −0,28 |
| `hlod-canopy-off` | `rq_hlodpart 1` | ceiling | −0,9…0 | ESTIMATED | 0106: korony 0,9 (po 0113 mniej, niezmierzone) |
| `thin-45` / `card-025` | `rq_thin 45` / `rq_card 0.25` | lever | −0,3 / 0 | ESTIMATED | 0106: przerzedzanie ×0,5 / karty ×0,5 |
| `cull-300` / `hlod-50` | `rq_cull 300` / `rq_hlod 50` | lever | brak liczby | UNVERIFIED | brak pomiaru |
| `mirrors-off` | `rq_mirror_off 1` | ceiling (nie ustawienie — lusterka zawsze użyteczne) | −1,46…−0,75 | ESTIMATED | 0106: 0,75–1,25; 0136 r2: 1,46 |
| `glassfast-off` | `rq_glassfast 0` | control czułości | +0,9 | ESTIMATED | 0106 Decyzja pkt 1 |

Wniosek z samych szacunków (do potwierdzenia pomiarem): do zamknięcia ~1,0–1,2 ms na p95 nie wystarczy żaden pojedynczy „lever”
zgodny z D50 poza LOD bias / far clip (oba widoczne, decyzja właściciela); pułapy lasu (ściany HLOD, impostory) dotyczą głównie G3-B.
Kopie głębi/koloru i post są na Low wyłączone — warianty `*-on` mierzą koszt ewentualnego włączenia, nie oszczędność.

## Czego ta runda NIE obejmuje
- `androidBlitType` 0 vs 2 (R8 P1) to ustawienie gracza w `ProjectSettings` → para APK, nie argument uruchomienia. Skrypt to obsłuży
  bez zmian: dwie sesje z `-Apk <A>` i `-Apk <B>` (ten sam versionCode) i wariantem `baseline` + dowolnym kontrolnym; porównanie
  tabel ręcznie. Patch `ProjectSetup` + ADR — osobno, u lidera.
- Pomiar w cyklach GPU / przy stałym zegarze (R8 P8) — wymaga Arm Performance Studio albo libGPUCounters; tu tylko `-Uncapped`
  (fps 240) jako przybliżenie „bez wpływu governora” (ADR 0106: z limitem GPU p50 30,0, bez 27,9 ms).
- Kamera główna z własnym ustawieniem „Depth/Opaque Texture = On/Off” ignoruje asset URP — `rq_depthtex`/`rq_opaquetex` działają
  tylko dla kamer „Use Pipeline Settings” (UNVERIFIED dla kamery kabiny; sprawdzić w Frame Debuggerze, czy pojawia się CopyDepth/CopyColor).

## Konflikty przewidywane (F6 = 0239 płoty, F7 = 0240 cienie pracują równolegle)
- `QualityProfile.cs`, `QualityProfile.asset`, `ProjectSetup.cs`: **brak zmian w tej gałęzi** → brak konfliktu. Jeśli F6/F7 dodają
  pola tieru + `CurrentRevision` + blok migracji w `ProjectSetup.LoadTiers`, scalają się niezależnie od 0241.
- `RenderOverrides.cs`: 4 miejsca — linia w komentarzu klasy, ogon wyrażenia `Any` (`|| GpuAbOverrides.Any`), jedna linia przed
  `PsoWarmup.Init(arg)`, ogon linii logu (`+ GpuAbOverrides.Describe()`). Jeśli F7 dopisze własny `rq_*` (np. cienie) w tych samych
  liniach `Any` / logu → konflikt tekstowy; rozwiązanie: zostawić oba dopiski (kolejność bez znaczenia).
- `QualityProfileApplier.cs`: jedna linia na końcu `ApplyPipelineOverrides`; F7 może dopisać tam `urp.*` cieni → zostawić obie.
- `WorldInstances.cs` (F6 płoty): nie zmieniane; używane są istniejące flagi `AbImpostorOff` / `AbHlodPart`.
- Po scaleniu F7: warianty `shadows-off` / `shadow-25` / `shadow-50` dalej działają (`rq_shadow` nadpisuje dystans tieru); jeśli
  F7 zmieni domyślny dystans Low z 35 m, zaktualizować opis `baseline` i ewentualnie wartości w katalogu.

## Weryfikacja
Uruchomione w chmurze: `uv run --project tools/perf pytest tools/perf/tests -q` → 61 passed (18 nowych w `test_gpuab.py`: katalog,
klucze katalogu czytane przez grę, percentyle/rozgrzewka, okna `rq_ab`, odrzucenia, parowanie po bloku, CSV/MD, CLI).
Nieuruchomione: kompilacja C# i EditMode (`GpuAbOverridesTests`, 19 przypadków), `scripts/gpu-ab-a16.ps1` (także `-DryRun` — brak
pwsh), wszystko na telefonie. Ryzyka do sprawdzenia przy kompilacji: `ScriptableObject.CreateInstance<UniversalRenderPipelineAsset>()`
w teście EditMode (URP 17.3) i publiczne settery `supportsCameraDepthTexture` / `supportsCameraOpaqueTexture`.

Komendy lidera (po scaleniu; telefon odblokowany, bez działającego Unity):
```
pwsh scripts/test.ps1 -Platform EditMode                                   # GpuAbOverridesTests
pwsh scripts/build-android.ps1                                              # czysty APK Low z tym kodem
pwsh scripts/gpu-ab-a16.ps1 -DryRun                                         # plan: 60 przebiegów, ok. 125 min
pwsh scripts/gpu-ab-a16.ps1 -Apk artifacts/apk/kamion-<ver>-<sha>.apk -Mode Camera -Uncapped      # etap 1: ranking, ok. 85 min
pwsh scripts/gpu-ab-a16.ps1 -Variants <zwycięzcy> -Segments A,B -Fps 30    # etap 2: budżet GPU p95 przy limicie
pwsh scripts/device-metrics.ps1 -Serial RFGL34SJYDZ -Launch -DurationSeconds 121 -WarmupSeconds 25 -Tier Low -Fps 30 -Scene WorldC -Autopilot route -Speed 30 -Trailer 40 -Extra telemetry=1,route_end=450,rq_abtag=lod-030,rq_lod=0.3   # pojedynczy przebieg ręcznie
uv run --project tools/perf python -m perfgate.gpuab report artifacts/gpu-ab/<ts>
```

## Otwarte
- Pomiar (cała tabela) — lider na A16; wynik dopisać do tego ADR i do `docs/PERFORMANCE_BUDGETS.md`.
- Zmiana profilu Low dopiero po pomiarze, ocenie wizualnej (`visual-qa -Rq`, kamery kontrolne) i decyzji właściciela dla wariantów
  widocznych (skala, LOD bias, far clip).
- `androidBlitType` (para APK), RenderDoc dla liczby próbek MSAA przy `msaa: 2`, pomiar w cyklach GPU (R8 P1/P8).
