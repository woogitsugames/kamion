# 02 — Stack, środowisko, MCP i skille

Wszystkie wersje **zweryfikuj w oficjalnych źródłach w dniu instalacji**. Liczby wersji w tym dokumencie to stan researchu z 9.11.2026, nie polecenie.

## 1. Stack gry

| Warstwa | Wybór | Uwagi |
|---|---|---|
| Silnik | Unity 6.3 LTS (najnowszy patch), potem zamrożenie | Unity Personal — sprawdź aktualny próg przychodu |
| Render | URP (Forward+), Vulkan, linear color space | Bez HDRP. GLES tylko jeśli macierz urządzeń wymusi |
| Kod | C#, asmdef per moduł, IL2CPP, ARM64 | Burst/Jobs/Mathematics dla fizyki i generacji |
| Fizyka | **Własny solver pojazdu** + PhysX jako kolizje/ciała | `docs/04`. WheelCollider tylko jako punkt odniesienia w testach |
| Wejście | Input System (nowy) | dotyk + gyro w v1; gamepad przygotowany |
| Treść/DLC | Addressables (+ Play Asset Delivery dla Google Play) | `docs/10` |
| Audio | FMOD for Unity (sprawdź warunki darmowej licencji indie) albo Unity Audio + własny mikser | `docs/08` |
| Testy | Unity Test Framework (EditMode/PlayMode), pytest dla narzędzi | |
| Profilowanie | Unity Profiler, Memory Profiler, Frame Debugger, Android GPU Inspector, Arm Performance Studio (Samsung A zwykle ma Mali), RenderDoc, Snapdragon Profiler (na flagowcu z Adreno) | |
| 3D | Blender (LTS) — headless `bpy` + MCP | `docs/07` |
| GIS | Python 3.12 (venv/uv), GDAL/PROJ, pyosmium, osmium-tool, shapely, pyproj, rasterio, geopandas, numpy, scipy, networkx, lxml (CityGML), laspy/PDAL (LiDAR); QGIS LTR + wtyczka „Pobieracz danych GUGiK” | `docs/05` |
| Tekstury | Własne generatory (Python/numpy, Blender nodes), astcenc, ImageMagick | `docs/06` |
| Audio tools | ffmpeg, sox, Audacity (ręczny odsłuch właściciela) | `docs/08` |

## 2. Sprzęt

- **PC**: zapisz realne parametry w audycie. Komfort: 64 GB RAM, GPU z ≥ 12 GB VRAM, NVMe z ≥ 300 GB wolnego (każdy worktree Unity ma własny `Library/`, geodane i źródła 3D są duże).
- **Telefon testowy (codziennie)**: Samsung Galaxy A (model ustal przez `adb shell getprop ro.product.model`; zapisz SoC/GPU/RAM/Android w `docs/DEVICE_MATRIX.md`). To **profil minimum** (Medium/Low).
- **Telefon docelowy jakości**: flagowiec (Snapdragon 8 Elite lub odpowiednik) — profil High/Ultra. Dopóki go nie ma: projektuj budżety High na podstawie dokumentacji i pomiarów z A z zapasem, oznaczaj wyniki High jako „niezmierzone na docelowym urządzeniu”. Zgłoś właścicielowi, kiedy brak flagowca zaczyna blokować postęp.
- **Tablet**: format referencyjny dla UI obok telefonu — testuj układ w emulatorze rozdzielczości, a na urządzeniu, gdy będzie dostępne.

## 3. Manifest instalacji (do zatwierdzenia przez właściciela jedną zgodą)

Instaluj przez **winget** lub oficjalny instalator; sprawdzaj kod wyjścia, PATH, wersję po instalacji. Skrypt idempotentny `scripts/setup-windows.ps1`, weryfikacja `scripts/doctor.ps1`.

**Obowiązkowe**
1. Git for Windows + Git LFS + GitHub CLI (`gh`)
2. Unity Hub + Unity 6.3 LTS z modułami: Android Build Support, Android SDK & NDK Tools, OpenJDK (wersje z Huba, nie losowe), Windows Build Support (IL2CPP)
3. .NET SDK zgodny z narzędziami; VS Code + C# Dev Kit + Unity extension (lub Rider, jeśli właściciel ma)
4. Blender LTS (w PATH jako `blender`)
5. Python 3.12 + `uv` (venv w `tools/.venv`, lockfile)
6. QGIS LTR (+ OSGeo4W/GDAL) i osmium-tool
7. Android platform-tools (`adb`) — z Unity lub osobno, ale **jedna udokumentowana ścieżka SDK**
8. scrcpy (podgląd i nagrywanie ekranu telefonu, zrzuty do visual QA)
9. ffmpeg, ImageMagick, astcenc, 7-Zip
10. Node.js LTS i `uv`/`uvx` (wymagane przez niektóre serwery MCP)

**Profilowanie (gdy potrzebne)**: Android GPU Inspector, Arm Performance Studio, RenderDoc, Snapdragon Profiler.

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
  - `unity-android-build` — build APK, instalacja, logcat, metryki z urządzenia
  - `visual-qa` — kamery kontrolne, porównanie z referencjami, checklista anti-slop
  - `physics-validation` — scenariusze testowe, telemetria CSV, tolerancje, raport
  - `blender-hero-asset` — pipeline modelu: blockout → high → low → bake → LOD → eksport → render kontrolny
  - `geo-worldgen` — pipeline OSM/GUGiK → region pack, raport QA danych
- Skille rozwijaj w trakcie projektu: gdy procedura powtórzy się 3 razy, zrób z niej skill.

### Connectory konta Claude (opcjonalnie)
Jeśli konto właściciela ma podpięte narzędzia do generowania SFX/tekstur (np. ElevenLabs, Magnific), sesja może z nich skorzystać **tylko po sprawdzeniu, że licencja wyniku pozwala na użycie komercyjne**, i z wpisem w `docs/LICENSES.md`. Nie są wymagane.

## 5. Git i repo

- Prywatne repo GitHub, `main` zawsze buduje się na Androida.
- `.gitattributes`: LFS dla fbx, blend, png, tga, psd, exr, tif, wav, ogg, bank, osm.pbf (jeśli w repo).
- **Limity LFS GitHuba są realne** — sprawdź aktualny limit planu właściciela. Surowe geodane (`data/raw/`) i duże wygenerowane pliki trzymaj **poza gitem** z manifestem (URL, data, SHA256) i skryptem pobierania/odtworzenia. Źródła `.blend` ciężarówki — w LFS.
- Nie commituj: `Library/`, `Temp/`, `Builds/`, `artifacts/`, keystore, haseł.
- Conventional commits po angielsku; tagi na bramkach (`v0.0-gate0`, …).
