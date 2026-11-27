# CLAUDE.md — zasady projektu TRUCK SIM PL

Ten plik jest ładowany na starcie każdej sesji. Trzymaj go aktualnym i krótkim; szczegóły są w `docs/`.

## Projekt w jednym akapicie
Realistyczny symulator (**Windows jako platforma główna od D73/ADR 0260**; Android → iOS później, lżej) ciężarówki z naczepą. Unity 6.3 LTS + URP + C#. Własna fizyka pojazdu. Świat z danych OSM + GUGiK: Białystok 1:1, potem obrzeża, Podlasie, Polska, kraje jako DLC. Jedna fikcyjna ciężarówka zrobiona perfekcyjnie. Budżet zakupów 0 zł. Jakość > tempo.

## Żelazne zasady
1. **Jakość > tempo > zakres.** Nie dodajesz funkcji spoza bieżącego etapu.
2. **Build jest prawdą.** Edytor kłamie o wydajności. Bramka = build Windows (player, nie edytor) + zmierzone liczby; referencyjny PC i FPS — do ustalenia z właścicielem (do tego czasu `WORKING_VALUE`). Wersja telefonowa (APK na Samsungu A przez `adb`) odroczona (D73), ale budżety mobilne zostają jako zabezpieczenie.
3. **Nie zmyślaj.** FPS, droga hamowania, wersje, szerokości pasów, parametry pojazdu — zmierzone, zacytowane ze źródła albo oznaczone `UNVERIFIED`/`WORKING_VALUE`.
4. **Pętla wizualna obowiązkowa** (skill `visual-qa`): render kamer kontrolnych → obejrzyj PNG → porównaj z referencją → popraw. Nigdy „skrypt przeszedł, więc wygląda dobrze”.
5. **Zero AI slop** — patrz `docs/06`. Jeśli coś wygląda jak typowa gra mobilna albo render z generatora, to nie jest gotowe.
6. **Fizyka w kodzie, nie w animacji.** Moment na koła, siły z opon, przegub fizyczny. Żadnego `transform.position +=` dla pojazdu.
7. **Wszystko jako kod/dane, odtwarzalne.** Generatory (Editor/Blender/Python) zamiast ręcznego klikania; ręczne poprawki jako jawne `authored_overrides`, które przeżywają reimport.
8. **Legalność.** Google Maps/Street View/Earth/3D Tiles — zakaz w pipeline, repo i buildzie. Każdy zasób w `docs/LICENSES.md`. Bez cudzych marek, logo, nagrań producentów. Suno na darmowym planie = brak praw komercyjnych.
9. **ADR dla każdej decyzji** spoza standardu (`docs/adr/NNNN-title.md`).
10. **Pytaj tylko gdy musisz** (zgody, konta, ocena feelingu/kierunku artystycznego, zdjęcia). Nie pytaj „czy kontynuować” po każdym drobiazgu.

## Unity — reguły techniczne
- Wersja edytora zamrożona w `ProjectSettings/ProjectVersion.txt`; pakiety w `packages-lock.json`.
- Force Text serialization, widoczne `.meta`, nigdy nie kasuj `.meta`.
- **Jeden proces Unity na katalog projektu.** Buildy/testy PlayMode serializowane (kolejka). Tylko lider zmienia `ProjectSettings/`, `Packages/`, wspólne sceny, wspólne prefaby, asmdef.
- 1 unit = 1 m, SI wewnętrznie, osie: X=wschód, Y=góra, Z=północ.
- Zero alokacji GC w pętli jazdy. Burst/Jobs tam, gdzie pomiar to uzasadnia.
- Fizyka w stałym kroku, nigdy w `Update()`. Render interpolowany.

## Komendy (PowerShell 7; wszystkie dot-source `scripts/env.ps1`, logi w `artifacts/logs/`)
Platforma główna = Windows (D73, ADR 0260); komendy telefonu niżej jako 🔒 odroczone, ale utrzymywane (Android nadal się kompiluje).
- Doctor (weryfikacja środowiska, exit 0 = zielono): `pwsh scripts/doctor.ps1`
- Konfiguracja projektu jako kod (player settings, tiery URP, scena Boot): `pwsh scripts/setup-project.ps1`
- **Build Windows x64** (ADR 0261): `pwsh scripts/build-windows.ps1 [-Slot] [-Regions d67-full | -RegionsFile Data/build_regions.json [-RegionsAllowMissing]] [-WorldLow] [-Development]` → `artifacts/win/kamion-<ver>-<sha>[-low][-regions][-dev]/Kamion.exe` + `Kamion.exe.sha256` + `build.json` + `Kamion-okno.cmd`; treść PC = High (bez `-WorldLow`); pierwszy build w checkoucie z Library pod Androida = pełny reimport Win64
- Uruchomienie playera z dowodem (zrzut, log, `frametimes.csv`; exit 4 przy wyjątkach/braku zrzutu): `pwsh scripts/build-windows.ps1 -SkipBuild -Run -Scene knyszyn-w [-Tier Low|Medium|High|Ultra] [-Fps 30|60|1000] [-Autopilot route -Speed 50] [-RunSeconds 90 -ShotSeconds 45]` → `artifacts/win/runs/<ts>/` (ADR 0261)
- **Pomiar PC** (ADR 0266; budżety klas min/zalecany/wysoki z D74 w `tools/pcperf/budgets/pc-budgets.json`, wszystko `WORKING_VALUE`; maszyna dewelopera ≠ referencja): `pwsh scripts/pc-metrics.ps1 -Exe artifacts/win/kamion-<ver>-<sha>-regions/Kamion.exe -Scene knyszyn-w -Tier High -Fps 60 -Width 1920 -Height 1080 -DurationSeconds 90 -Class zalecany` (klasa min: `-Tier Low -Fps 30 -Class min`) → `artifacts/pc/<maszyna>/<ts>/` (`frames.csv`, `memory.csv`, `process.csv`, `run.json`, `pc-report.md`; exit 0 w budżecie / 1 poza / 2 pomiar nieważny). Sam parser: `uv run --no-project python tools/pcperf/pc_metrics.py <katalog> --budget tools/pcperf/budgets/pc-budgets.json --class zalecany`. Nie łączyć `-metrics` z `-shot` w jednym przebiegu.
- Paczka dla testerów (ADR 0271, `docs/12`): `uv run --no-project python scripts/package-windows.py <katalog buildu> [--dry-run]` → zip + `.sha256` + `.json`; `--release` kończy się kodem 3, dopóki otwarty bloker licencyjny R-P0-2
- Testy EditMode/PlayMode: `pwsh scripts/test.ps1 [-Platform EditMode|PlayMode] [-BuildTarget Win64|Android]` → `artifacts/tests/*.xml` (`-BuildTarget Win64` w checkoucie z Library pod Windows — bez powrotnego reimportu, ADR 0261)
- Plac testowy + import dźwięku pojazdu z kodu: `pwsh scripts/build-lab.ps1` (WAV: `cd tools/audio; uv run python render_all.py`)
- Kamery kontrolne (visual QA): `pwsh scripts/visual-qa.ps1 -Scene Boot [-Tier Medium]` → `artifacts/visual-qa/<scene>/<id>.png` (GPU wymagane, bez `-nographics`)
- Wejścia batchmode: `Game.Editor.Build.BuildCommands.BuildWindowsPlayer` (`-buildTarget Win64`), `Game.Editor.Build.BuildCommands.BuildAndroidApk`, `Game.Editor.Setup.ProjectSetup.ApplyAll`, `Game.Editor.VisualQA.VisualQaRunner.RenderControlCameras`
- Regeneracja mapy: `uv run tools/worldgen/build_region.py --region <id>` → `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region <id>` → `pwsh scripts/import-region.ps1 -Region <id> [-Build] [-SkipCopy]` (glTFast → `game/Assets/_Generated/World/<id>/` + scena `WorldC`, poza gitem; ADR 0011). Trasa startowa: `uv run --project tools/worldgen python scripts/export-route.py --region <id>`
- Kamery kontrolne świata: `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low|Medium|High -Lighting clear|overcast -OutputDir <dir>` (ADR 0010)
- 🔒 **Telefon (odroczony, D73 — nie blokuje bramek, budżety mobilne zostają jako zabezpieczenie):**
  - Build APK: `pwsh scripts/build-android.ps1` → `artifacts/apk/kamion-<ver>-<sha>.apk` + `.sha256`
  - Build + instalacja + start + logcat: `pwsh scripts/build-android.ps1 -Install -Run [-Serial <s> | -AllDevices] [-LogcatSeconds 60] [-Tier Low|Medium|High|Ultra] [-Fps 30|60] [-SkipBuild] [-Development]`
  - Pomiar na telefonie (CSV klatek, p50/p95/p99, PSS, temp., zrzut ekranu): `pwsh scripts/device-metrics.ps1 [-Launch -DurationSeconds 90] [-Serial <s> | -AllDevices]` → `artifacts/device/<serial>/<ts>/`
  - Telefon musi być odblokowany (skrypty nie wpisują PIN-u; zablokowany = pomiar odrzucony).

## Agenci
Definicje w `.claude/agents/`. Lider = jedyny integrator. Worktree + gałąź na zadanie. Subagenci nie tworzą subagentów. Kontrakt zadania i format raportu: `docs/09`.
- **Tempo i limit (polecenie właściciela, każda sesja):** pracuj na maksa do końca limitu 5-godzinnego. Przy ≥ 85 % limitu nowy agent tylko gdy działa < 2; przy ≥ 95 % żadnych nowych — agenci zapisują WIP (commit + STATUS.md), lider aktualizuje `HANDOVER.md` i pushuje.
- **Ciągły zapis:** każdy agent commituje WIP i dopisuje STATUS.md (z następnym krokiem jako komendą) po każdym kroku; lider aktualizuje górę `HANDOVER.md` (main sha, tabela agentów: worktree, gałąź, STATUS, stan; następne kroki; licznik ADR) po każdym scaleniu/starcie/końcu agenta i pushuje — nowa sesja musi móc kontynuować z samego `HANDOVER.md`. Zasady dla agentów: `docs/owner/AGENT-RULES.md` (wersja w gicie).
- **Druga opinia:** darmowe modele OpenRouter (zgoda właściciela 2026-11-15) do recenzji kodu/ADR — dostęp, lista modeli i zasady: `docs/owner/OPENROUTER-FREE-MODELS.md`.
- **CLI zawsze (właściciel 19.11):** każde zadanie, które da się oddać, zlecaj Antigravity (`agy`, Gemini neon/hydrogen) i Codex CLI (model `gpt-6.2-sol`, duży limit — właściciel 27.11) przez `scripts/cli-jobs/start-job.ps1 -Tool neon|codex`; Mistral zablokowany przez Smart App Control (każde we własnym worktree) — oszczędza limit lidera; w toku stale ≥ 1–2 zlecenia CLI obok własnych agentów, lider przegląda i scala.
$python_line

## Definition of Done (każde zadanie)
Kompiluje się na Windows (i nadal na Androidzie) · testy zielone · brak nowych krytycznych ostrzeżeń · dowód (log/zrzut/telemetria) · budżet wydajności nie pogorszony · review innego agenta · docs/ADR/licencje zaktualizowane · commit.

## Mapa dokumentów
01 wizja · 02 stack/środowisko/MCP · 03 etapy i bramki · 04 fizyka · 05 mapa Białystok i dane · 06 grafika i anti-slop · 07 ciężarówka 3D · 08 audio · 09 agenci i workflow · 10 architektura i DLC · 11 decyzje właściciela
