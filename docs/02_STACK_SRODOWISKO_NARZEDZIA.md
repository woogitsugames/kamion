# 02 — Stack, środowisko, MCP i skille

Wszystkie wersje **zweryfikuj w oficjalnych źródłach w dniu instalacji**. Liczby wersji w tym dokumencie to stan researchu z 9.11.2026, nie polecenie.

> **D73 / ADR 0260 (15.11.2026): platformą główną jest Windows Standalone x64** (ten sam projekt Unity 6000.3 URP; Unreal odrzucony). Android (potem iOS) = wersja późniejsza i lżejsza. Pozycje czysto mobilne oznaczone 🔒 „odroczone (D73)” — zostają utrzymywane (Android nadal się kompiluje), a budżety mobilne obowiązują jako zabezpieczenie danych wspólnych (`docs/03`). Wymagania sprzętowe gry: D74 (klasy min/zalecany wg ETS2/ATS, `WORKING_VALUE`).

## 1. Stack gry

| Warstwa | Wybór | Uwagi |
|---|---|---|
| Silnik | Unity 6.3 LTS (najnowszy patch), potem zamrożenie | Unity Personal — sprawdź aktualny próg przychodu |
| Render | URP (Forward+), linear color space; **Windows: Direct3D 12** (log playera `[BOOT] api='Direct3D 12'`, ADR 0261); 🔒 Android: Vulkan | Bez HDRP. 🔒 GLES tylko jeśli macierz urządzeń wymusi. Tiery PC Low/Medium/High/Ultra + „auto” (ADR 0269) |
| Kod | C#, asmdef per moduł; **Windows x64: backend Mono** (ADR 0261), IL2CPP dopiero po pomiarze A/B przed pierwszym wydaniem (ADR 0271); 🔒 Android: IL2CPP, ARM64 | Burst/Jobs/Mathematics dla fizyki i generacji |
| Fizyka | **Własny solver pojazdu** + PhysX jako kolizje/ciała | `docs/04`. WheelCollider tylko jako punkt odniesienia w testach |
| Wejście | Input System (nowy), za warstwą `IDriverInput` (D56) | **PC: klawiatura + pad** (ADR 0261, przypisania ADR 0264), kierownica/pedały z FFB (ADR 0263), HUD pod monitor (ADR 0265), menu ustawień PC (ADR 0270); 🔒 telefon: dotyk + gyro |
| Treść/DLC | Addressables; regiony przez `-Regions` w buildzie (ADR 0229) | `docs/10`. **PC: paczka zip, itch.io najpierw, Steam po decyzji właściciela** (ADR 0271, `docs/12`). 🔒 Play Asset Delivery dla Google Play |
| Audio | FMOD for Unity (sprawdź warunki darmowej licencji indie) albo Unity Audio + własny mikser | `docs/08` |
| Testy | Unity Test Framework (EditMode/PlayMode), pytest dla narzędzi | |
| Profilowanie | **PC:** `scripts/pc-metrics.ps1` + `tools/pcperf` (ADR 0266: klatki, CPU/GPU, draw calls, RAM/VRAM procesu, `nvidia-smi`), Unity Profiler, Memory Profiler, Frame Debugger, RenderDoc. 🔒 Telefon: Android GPU Inspector, Arm Performance Studio (Samsung A zwykle ma Mali), Snapdragon Profiler (Adreno), `scripts/device-metrics.ps1` | Dowód bramki = player Windows, nie edytor (`docs/03`) |
| 3D | Blender (LTS) — headless `bpy` + MCP | `docs/07` |
| GIS | Python 3.12 (venv/uv), GDAL/PROJ, pyosmium, osmium-tool, shapely, pyproj, rasterio, geopandas, numpy, scipy, networkx, lxml (CityGML), laspy/PDAL (LiDAR); QGIS LTR + wtyczka „Pobieracz danych GUGiK” | `docs/05` |
| Tekstury | Własne generatory (Python/numpy, Blender nodes), astcenc, ImageMagick | `docs/06` |
| Audio tools | ffmpeg, sox, Audacity (ręczny odsłuch właściciela) | `docs/08` |

## 2. Sprzęt

- **PC dewelopera = maszyna pomiarowa, NIE referencja** (ADR 0260/0261): zapisz realne parametry w audycie (stan s22 wg ADR 0261: Ultra 7 270K Plus, 64 GB RAM, RTX 5070, D3D12 — z ADR 0261). Komfort pracy: 64 GB RAM, GPU z ≥ 12 GB VRAM, NVMe z ≥ 300 GB wolnego (każdy worktree Unity ma własny `Library/`, geodane i źródła 3D są duże). Wynik z tej maszyny jest informacyjny („jest zapas / nie ma zapasu”), nie zalicza klas min/zalecany.
- **Klasy sprzętu gracza (D74, `WORKING_VALUE`)**: min = i5-6400 / Ryzen 3 1200, GTX 660 / RX 460 / Intel HD 630 (2 GB VRAM), 8 GB RAM → Low 1080p 30 fps; zalecany = i5-9600 / Ryzen 5 3600, GTX 1660 / RX 590, 12 GB RAM → High 1080p 60 fps; dysk ≤ 25 GB. Pełna tabela budżetów: `docs/03`, dane: `tools/pcperf/budgets/pc-budgets.json` (ADR 0266). Referencyjny PC dla klas — do wskazania przez właściciela; ryzyko: Intel HD 630 (pomiar Low na iGPU przed obietnicą).
- **Wejście do testów**: klawiatura i pad na maszynie dewelopera; kierownica z FFB — gdy będzie dostępna (ADR 0263; brak sprzętu = `UNVERIFIED`).
- 🔒 **Telefony (odroczone, D73)**: Samsung Galaxy A16 (profil Low, D49) i S24+ (Medium/High) w `docs/DEVICE_MATRIX.md` (model z `adb shell getprop ro.product.model`, SoC/GPU/RAM/Android). Wracają jako obowiązujące przy wersji telefonowej (`docs/03` Etap 9+). Flagowiec i tablet — jak w poprzedniej wersji planu, bez zakupów teraz.

## 3. Manifest instalacji (do zatwierdzenia przez właściciela jedną zgodą)

Instaluj przez **winget** lub oficjalny instalator; sprawdzaj kod wyjścia, PATH, wersję po instalacji. Skrypt idempotentny `scripts/setup-windows.ps1`, weryfikacja `scripts/doctor.ps1`.

**Obowiązkowe**
1. Git for Windows + Git LFS + GitHub CLI (`gh`)
2. Unity Hub + Unity 6.3 LTS z modułami: **Windows Build Support** (`windowsstandalonesupport`, ADR 0260; backend Mono — moduł IL2CPP tylko do pomiaru A/B, ADR 0271), 🔒 Android Build Support, Android SDK & NDK Tools, OpenJDK (wersje z Huba, nie losowe — utrzymywane, bo Android nadal się kompiluje, D73)
3. .NET SDK zgodny z narzędziami; VS Code + C# Dev Kit + Unity extension (lub Rider, jeśli właściciel ma)
4. Blender LTS (w PATH jako `blender`)
5. Python 3.12 + `uv` (venv w `tools/.venv`, lockfile)
6. QGIS LTR (+ OSGeo4W/GDAL) i osmium-tool
7. 🔒 Android platform-tools (`adb`) — z Unity lub osobno, ale **jedna udokumentowana ścieżka SDK** (odroczone, D73)
8. 🔒 scrcpy (podgląd i nagrywanie ekranu telefonu; odroczone, D73 — zrzuty do visual QA bierzemy z playera Windows, `scripts/build-windows.ps1 -Run`)
9. ffmpeg, ImageMagick, astcenc, 7-Zip
10. Node.js LTS i `uv`/`uvx` (wymagane przez niektóre serwery MCP)

**Profilowanie (gdy potrzebne)**: PC — RenderDoc, `nvidia-smi` (sterownik NVIDIA; używa go `scripts/pc-metrics.ps1`, ADR 0266). 🔒 Telefon: Android GPU Inspector, Arm Performance Studio, Snapdragon Profiler.

**Nie instaluj**: Android Studio jako drugiego SDK (tylko jeśli konieczne do profilowania), HDRP, Unreal, przypadkowych NDK/JDK.

## 4. MCP i skille — co realnie pomoże tej sesji

To jest odpowiedź na pytanie „czy trzeba konkretne connectory albo skille?”. Tak — kilka z nich wyraźnie podnosi jakość, bo dają sesji **oczy i ręce** w edytorach, zamiast pracy na ślepo.

### MCP (konfiguracja w `.mcp.json` projektu; zweryfikuj aktualne repozytoria i instrukcje)

| MCP | Po co | Priorytet |
|---|---|---|
| **Unity MCP** (np. „MCP for Unity” CoplayDev/unity-mcp; sprawdź też, czy Unity wydało oficjalny serwer MCP i który jest aktywnie utrzymywany) | Odczyt konsoli, uruchamianie testów, operacje na scenach/prefabach, zrzuty z kamer edytora | **Wysoki** |
| **Blender MCP** (ahujasid/blender-mcp) | Interaktywna praca na scenie Blendera, podgląd viewportu, szybkie iteracje modelu ciężarówki | **Wysoki** (obok skryptów headless) |
| **Context7** (aktualna dokumentacja bibliotek) | Unity 6.3 API, URP, Addressables, Input System — bez halucynacji o starych API | Wysoki |
| GitHub | przez `gh` CLI — osobny MCP niepotrzebny | — |

Zasada: MCP to wygoda, nie zależność. Każda operacja krytyczna (build, generacja mapy, eksport modelu, testy) musi też działać **headless ze skryptu**, żeby była odtwarzalna i dostępna dla subagentów.

### Pluginy/skille Claude Code

- **Superpowers** (obra/superpowers) — dyscyplina pracy: brainstorming → plan → TDD → systematyczne debugowanie → review → subagent-driven development. Zainstaluj zgodnie z aktualną instrukcją repo. Szczególnie przydatne: `writing-plans`, `test-driven-development`, `systematic-debugging`, `verification-before-completion`.
- **Skille projektowe z tej paczki** (`.claude/skills/`):
  - 🔒 `unity-android-build` — build APK, instalacja, logcat, metryki z urządzenia (odroczone, D73). Build i pomiar Windows nie mają jeszcze skilla — komendy w `CLAUDE.md` „Komendy” (ADR 0261/0266/0271)
  - `visual-qa` — kamery kontrolne, porównanie z referencjami, checklista anti-slop
  - `physics-validation` — scenariusze testowe, telemetria CSV, tolerancje, raport
  - `blender-hero-asset` — pipeline modelu: blockout → high → low → bake → LOD → eksport → render kontrolny
  - `geo-worldgen` — pipeline OSM/GUGiK → region pack, raport QA danych
- Skille rozwijaj w trakcie projektu: gdy procedura powtórzy się 3 razy, zrób z niej skill.

### Connectory konta Claude (opcjonalnie)
Jeśli konto właściciela ma podpięte narzędzia do generowania SFX/tekstur (np. ElevenLabs, Magnific), sesja może z nich skorzystać **tylko po sprawdzeniu, że licencja wyniku pozwala na użycie komercyjne**, i z wpisem w `docs/LICENSES.md`. Nie są wymagane.

## 5. Git i repo

- Prywatne repo GitHub, `main` zawsze buduje się jako player Windows x64 (D73, ADR 0260/0261) i nadal kompiluje na Androida (DoD w `CLAUDE.md`).
- `.gitattributes`: LFS dla fbx, blend, png, tga, psd, exr, tif, wav, ogg, bank, osm.pbf (jeśli w repo).
- **Limity LFS GitHuba są realne** — sprawdź aktualny limit planu właściciela. Surowe geodane (`data/raw/`) i duże wygenerowane pliki trzymaj **poza gitem** z manifestem (URL, data, SHA256) i skryptem pobierania/odtworzenia. Źródła `.blend` ciężarówki — w LFS.
- Nie commituj: `Library/`, `Temp/`, `Builds/`, `artifacts/`, keystore, haseł.
- Conventional commits po angielsku; tagi na bramkach (`v0.0-gate0`, …).
