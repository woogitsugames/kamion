# CLAUDE.md — zasady projektu TRUCK SIM PL

Ten plik jest ładowany na starcie każdej sesji. Trzymaj go aktualnym i krótkim; szczegóły są w `docs/`.

## Projekt w jednym akapicie
Mobilny (Android → iOS) realistyczny symulator ciężarówki z naczepą. Unity 6.3 LTS + URP + C#. Własna fizyka pojazdu. Świat z danych OSM + GUGiK: Białystok 1:1, potem obrzeża, Podlasie, Polska, kraje jako DLC. Jedna fikcyjna ciężarówka zrobiona perfekcyjnie. Budżet zakupów 0 zł. Jakość > tempo.

## Żelazne zasady
1. **Jakość > tempo > zakres.** Nie dodajesz funkcji spoza bieżącego etapu.
2. **Telefon jest prawdą.** Edytor kłamie o mobile GPU. Każda bramka = APK na Samsungu A (`adb`) + liczby. Profil High/Ultra stroimy na flagowcu, gdy będzie dostępny.
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
- Doctor (weryfikacja środowiska, exit 0 = zielono): `pwsh scripts/doctor.ps1`
- Konfiguracja projektu jako kod (player settings, tiery URP, scena Boot): `pwsh scripts/setup-project.ps1`
- Build APK: `pwsh scripts/build-android.ps1` → `artifacts/apk/kamion-<ver>-<sha>.apk` + `.sha256`
- Build + instalacja + start + logcat: `pwsh scripts/build-android.ps1 -Install -Run [-Serial <s> | -AllDevices] [-LogcatSeconds 60] [-Tier Low|Medium|High|Ultra] [-Fps 30|60] [-SkipBuild] [-Development]`
- Pomiar na telefonie (CSV klatek, p50/p95/p99, PSS, temp., zrzut ekranu): `pwsh scripts/device-metrics.ps1 [-Launch -DurationSeconds 90] [-Serial <s> | -AllDevices]` → `artifacts/device/<serial>/<ts>/`
- Testy EditMode/PlayMode: `pwsh scripts/test.ps1 [-Platform EditMode|PlayMode]` → `artifacts/tests/*.xml`
- Plac testowy + import dźwięku pojazdu z kodu: `pwsh scripts/build-lab.ps1` (WAV: `cd tools/audio; uv run python render_all.py`)
- Kamery kontrolne (visual QA): `pwsh scripts/visual-qa.ps1 -Scene Boot [-Tier Medium]` → `artifacts/visual-qa/<scene>/<id>.png` (GPU wymagane, bez `-nographics`)
- Wejścia batchmode: `Game.Editor.Build.BuildCommands.BuildAndroidApk`, `Game.Editor.Setup.ProjectSetup.ApplyAll`, `Game.Editor.VisualQA.VisualQaRunner.RenderControlCameras`
- Telefon musi być odblokowany (skrypty nie wpisują PIN-u; zablokowany = pomiar odrzucony).
- Regeneracja mapy: `uv run tools/worldgen/build_region.py --region <id>` → `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region <id>` → `pwsh scripts/import-region.ps1 -Region <id> [-Build] [-SkipCopy]` (glTFast → `game/Assets/_Generated/World/<id>/` + scena `WorldC`, poza gitem; ADR 0011). Trasa startowa: `uv run --project tools/worldgen python scripts/export-route.py --region <id>`
- Kamery kontrolne świata: `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low|Medium|High -Lighting clear|overcast -OutputDir <dir>` (ADR 0010)

## Agenci
Definicje w `.claude/agents/`. Lider = jedyny integrator. Worktree + gałąź na zadanie. Subagenci nie tworzą subagentów. Kontrakt zadania i format raportu: `docs/09`.

## Definition of Done (każde zadanie)
Kompiluje się na Androidzie · testy zielone · brak nowych krytycznych ostrzeżeń · dowód (log/zrzut/telemetria) · budżet wydajności nie pogorszony · review innego agenta · docs/ADR/licencje zaktualizowane · commit.

## Mapa dokumentów
01 wizja · 02 stack/środowisko/MCP · 03 etapy i bramki · 04 fizyka · 05 mapa Białystok i dane · 06 grafika i anti-slop · 07 ciężarówka 3D · 08 audio · 09 agenci i workflow · 10 architektura i DLC · 11 decyzje właściciela
