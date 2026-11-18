# ADR 0246 — zrzuty z telefonu dla póz par zdjęciowych bramki 3 (automat)
Status: Proposed (chmura G, agent G4, gałąź `g3-poses-0246`), 2026-11-15. Do weryfikacji i scalenia przez lidera.
Uzupełnienie 2026-11-16 (s23, FIX PR #116): po D73 / ADR 0260 dowodem bramki są kadry z **playera Windows** — patrz sekcja
„Windows (D73)”. Tryb telefonu (`-Serial`) zostaje bez zmian zachowania, jako **odroczony**.
Powiązane: BACKLOG B-111, `docs/reports/GATE-3.md` (checklista kamer, pkt 2: „brak zrzutów A16 dla 42 póz par
zdjęciowych”), ADR 0010 (kamery kontrolne świata), ADR 0103/0160/0172 (pozy par SBS), ADR 0044 r9 (`ViewCameraResolver`),
`scripts/sbs-gate3.ps1` (pary z edytora), `scripts/gate3-run.ps1` (kamery kontrolne na telefonie).

## Kontekst
Pary zdjęciowe trasy C są renderowane tylko w edytorze (`sbs-gate3.ps1` → `visual-qa.ps1 -Gate3 sbs_cameras.json`,
1280 px × proporcja zdjęcia, Low/High × overcast/clear). Telefon (zasada 2) ma zrzuty kamer kontrolnych G3-A/G3-B
(`gate3-run.ps1`, `qacam`/`qacam_set=gate3`: pełny ekran przez `screencap`, jedno uruchomienie aplikacji na kamerę), ale
nie póz par. Kamery par nie są w scenie ani w `gate3_cameras.json`, więc istniejąca ścieżka ich nie widzi.

## Liczba póz: 42 (zgodna z checklistą)
Źródło: `Data/Regions/bialystok-industrial-c/sbs_cameras.json` — 42 kamery `photo_match` (G3-A 22, G3-B 20; pewność
pozy B 27, C 15), każda z wpisem w `sbs_references.json` (zdjęcie 2048×1536 ×28, 2048×1152 ×10, 1280×720 ×2,
3840×2160 ×2). To ten sam zestaw, który ocenił krytyk s16b (`REVIEW-2026-11-13-s16b-final.md`: 42 = 27 R + 15 P;
G3-A 22, G3-B 20). Historia pliku jest spłaszczona w scaleniu `cae0c95f`, więc tożsamość id 1:1 z s16b jest
**UNVERIFIED** (liczby po segmentach się zgadzają). `sbs_pose_probes.json` (144 sondy) to warianty robocze póz, nie pary.

## Decyzja
1. **Jeden plik póz z danych, nie ręcznie.** `python scripts/g3_poses.py export` łączy `sbs_cameras.json`
   (pozycja/look-at E,N,U, FOV pionowy, `seat`) z `sbs_references.json` (rozmiar zdjęcia, atrybucja, ścieżka zdjęcia
   porównawczego) w `Data/Regions/<region>/g3_poses.json` (schema `kamion/g3-poses/1`, źródło każdej pozy:
   plik + indeks + `pose_reason`, sha256 wejść). Gra czyta bajtowo identyczną kopię
   `game/Assets/_Project/Gameplay/Resources/g3_poses.json` (~52 KB w każdym APK). `g3_poses.py check` i pytest
   `tests/gate3/test_g3_poses.py` pilnują aktualności i równości póz z kamerami.
2. **Tryb w grze bez zmian sceny i prefabów.** `Game.Gameplay.G3PoseRunner` zaczepia się przez
   `RuntimeInitializeOnLoadMethod`; działa tylko gdy `-e g3pose 1` **i** `Debug.isDebugBuild` (Development APK);
   wydanie z argumentem loguje `[G3POSE] REFUSED ...` i `DONE captured=0`. Po załadowaniu sceny z `WorldRegionRoot`
   (`-e scene WorldC`) czeka `g3pose_warmup_s` (8 s), potem dla każdej pozy:
   - kamera poza ekranem w pozie liczonej tą samą funkcją co pary z edytora (`WorldRegionRoot.LocalToUnity` +
     `Gate3Cameras.ComputePose`; wszystkie 42 mają `seat=file`, więc bez osadzania na drodze), ustawienia kamery z tieru
     (`CaptureCameraTier.Apply` → `QualityProfileApplier.Apply` bez wolumenu i tekstur), far = min(1400, tier);
   - render do `RenderTexture` w rozdzielczości × `renderScale` tieru z MSAA tieru, potem dwuliniowo do 1280 × proporcja
     zdjęcia — tak jak `VisualQaRunner.RenderToPixels` w edytorze (porównanie telefon/edytor 1:1 rozmiarem);
   - „streaming ustabilizowany” (`G3PoseSettle`): ≥ 20 klatek, ≥ 1,5 s w pozie i 5 kolejnych klatek bez oczekujących
     ładowań mipów (`Texture.streamingTextureLoadingCount + streamingTexturePendingLoadCount`, gdy mip streaming
     aktywny); po 20 s zrzut i tak, z flagą `settled=timeout`. WorldC to jedna scena bez strumieniowania kafli w kodzie
     gry (brak `LoadSceneAsync`/Addressables w `game/Assets/_Project`), więc mipy to jedyne asynchroniczne ładowanie;
     jeśli płynne kafle (F2/0235) dodadzą strumieniowanie, jego licznik trzeba dodać do `PendingTextureLoads`;
   - PNG do `persistentDataPath/g3poses/<run>/NN_<id>_<oświetlenie>.png` + `manifest.json` (pozycja/kierunek w Unity,
     rozmiary, klatki, czas, flaga timeout); logcat `[G3POSE] BEGIN/SHOT/FAIL/DONE`.
   Widok gracza, HUD i pojazd zostają bez zmian (kamera nie rysuje na ekran, więc HUD nie trafia do kadru).
   Wszystkie czasy powyżej to **WORKING_VALUE**, nie pomiar.
3. **Czysta logika testowalna** (`G3PoseSet` parser/walidacja/filtr, `G3PoseArgs`, `G3PoseCapture` nazwy/rozmiary/linie
   logu, `G3PoseSettle`) nie używa API Unity poza `JsonUtility` pod `#if UNITY_5_3_OR_NEWER`. Ten sam plik NUnit
   `Tests/EditMode/G3PoseTests.cs` działa jako test EditMode (istniejący asmdef `Game.Tests.EditMode`, bez zmian) i jako
   test .NET `tests/g3poses/G3PoseTests.csproj` (wzorzec tools/about-runner, ADR 0150).
4. **Skrypt lidera** `scripts/g3-poses.ps1` (dot-source `env.ps1`): `-Serial`, opcjonalnie `-Build` (Development APK
   przez `build-android.ps1 -Development -Install`) albo `-Apk <dev.apk>`; `isKeyguardShowing=false` i ekran Awake
   przed instalacją, przed każdym przebiegiem, co 5 s w trakcie i po (blokada = odrzucenie, exit 5; tylko
   `KEYCODE_WAKEUP`, nigdy SLEEP/POWER, bez PIN-u); temperatura baterii przed przebiegiem (> `-MaxBatteryC` 40 °C
   = odmowa, exit 7; próg WORKING_VALUE); jeden przebieg na oświetlenie (domyślnie overcast i clear jak pary
   z edytora); czekanie na `DONE run=<id>`; `adb pull` do `artifacts/gate3/poses/<serial>/<ts>/<oświetlenie>/`;
   kontrola liczby PNG i duplikatów MD5; zestawienie z fotografią (`magick`, lewa = zdjęcie z atrybucją, prawa = telefon)
   do `sbs/<oświetlenie>/`; brak ImageMagick lub zdjęcia = jasny komunikat, klatki zostają. Zdjęcia są poza gitem:
   `-RefDir` albo ścieżki z `sbs_references.json` w głównej kopii repo. Wynik `g3poses-result.json` (APK sha256,
   urządzenie, temperatura/thermal przed i po, linie `[BOOT]`, statusy).

## Konsekwencje
- Punkt 2 checklisty bramki 3 może zostać domknięty jednym poleceniem lidera; ocena kadrów nadal należy do
  `visual-critic` (skrypt nie wydaje werdyktu).
- Development APK: renderuje tak samo jak wydanie (te same shadery i ustawienia tieru), ale nie jest APK zaliczenia
  bramki; w raporcie podawać sha APK. Pomiaru wydajności tym trybem się nie robi (dodatkowy render RT co klatkę).
- Per-view stan CPU (`StreetLamps`, `CabInteriorLighting` przez `ViewCameraResolver`) dalej śledzi kamerę gracza, nie
  kamerę pozy; dla dziennych overcast/clear bez znaczenia, dla `dusk` latarnie przy pozie mogą być niepełne — nie
  używać trybu do nocnych par bez rozszerzenia.
- Nowy plik w `Game.Rendering` (`CaptureCameraTier.cs`) — bo `Game.Gameplay` nie referencjonuje URP, a asmdef się nie
  zmienia.

## Windows (D73) — `scripts/g3-poses.ps1 -Exe <Kamion.exe>`
**Wariant: jeden proces na oświetlenie, wszystkie pozy w istniejącym runnerze** (nie „exe na pozę”). Uzasadnienie:
- runner już czyta argumenty na desktopie: `G3PoseArgs.Parse(platform.GetLaunchArgument)`, a
  `DefaultPlatformServices.GetLaunchArgument` szuka `-klucz wartość` w `Environment.GetCommandLineArgs()` — te same klucze
  co intent extras (`-scene WorldC -tier High -lighting overcast -g3pose 1 -g3pose_run <id> ...`);
- „exe na pozę” (`-scene` + `-shot` + `-quit_t`, `DesktopAutoShot`) dałoby zrzut **ekranu** (z HUD-em, w rozdzielczości
  okna, z kamery gracza — pozy kamery argumentem ustawić się nie da) i 84 ładowania WorldC; runner renderuje poza
  ekranem w 1280 px × proporcja zdjęcia, tą samą funkcją pozy co pary z edytora, bez HUD-u.

Zmiany w C# (tylko pliki tego PR, bez `ProjectSettings/`, asmdef):
- `g3pose_dir <folder>` — tylko desktop (`G3PoseCapture.ResolveOutputDir`, na platformach mobilnych ignorowany): PNG +
  `manifest.json` trafiają wprost do katalogu wyniku, bez zgadywania `%USERPROFILE%\AppData\LocalLow\woogitsugames\Kamion`
  (domyślnie dalej `persistentDataPath/g3poses/<run>`);
- `g3pose_quit 1` — `Application.Quit` po linii DONE (kod 0 = czysto, 1 = błędy, 2 = odmowa poza Development);
- `Application.runInBackground = true` na czas przebiegu (w `ProjectSettings` jest 0: okno bez fokusu wstrzymałoby
  render i regułę „ustabilizowane”) — tylko gdy tryb uzbrojony, czyli Development + `g3pose 1`.

Skrypt (bez adb, bez Unity; zestaw parametrów `-Exe` wyklucza `-Serial`/`-Build`/`-Apk`): na każde oświetlenie
(domyślnie overcast, clear) uruchamia `Kamion.exe -screen-fullscreen 0 -screen-width 1600 -screen-height 900 -logFile
<root>/Player-<światło>.log -scene WorldC -tier <Tier> -g3pose 1 -g3pose_run <ts>-<światło> -g3pose_width 1280 -lighting
<światło> -g3pose_dir <root>/<światło> -g3pose_quit 1 [-fps N] [-g3pose_only ...]`; `<root>` =
`artifacts/g3-poses/win/<ts>/`, układ jak w trybie telefonu (`<światło>/NN_<id>_<światło>.png` + `manifest.json`,
`sbs/<światło>/*.jpg`, `g3poses-result.json`). Tier domyślnie **High** (D74, klasa „zalecany”); okno 1600×900 jak
launchery ADR 0261 — rozmiar okna nie wpływa na kadr (render poza ekranem). Czeka na `[G3POSE] DONE` w logu, po
`-TimeoutSeconds` (900 s, WORKING_VALUE) zabija proces (TIMEOUT); gracza, który nie zamknął się 20 s po DONE, zamyka sam.
Linia poleceń i werdykt pochodzą z `scripts/g3_poses.py` (`winargs`, `verify`): exit 6, gdy brakuje PNG / PNG nie jest
PNG-iem / dwa kadry identyczne (MD5) / brak lub niespójny manifest / brak DONE / linia FAIL lub REFUSED / wyjątek lub
crash w `Player.log` (`\w*Exception`, `Crash!!!`, `Shader error`) / kod wyjścia gracza ≠ 0 / TIMEOUT.
`-DryRun` drukuje plan i linie poleceń bez exe i bez Windows.

P2 z recenzji s22 (`REVIEW-2026-11-15-s22-code-116.md`):
1. `CaptureCameraTier.Apply` — poprawiony opis: to pełne `QualityProfileApplier.Apply` (volume/tekstury = null), więc
   ustawia też `Current`, słowa kluczowe, nadpisania potoku i zdarzenie `Applied`; wolno wołać tylko z bieżącym tierem
   (runner tak robi — idempotentne). Wydzielenie `ApplyCamera` w `QualityProfileApplier` (plik spoza PR) — nie zrobione.
2. `Resources/g3_poses.json` w buildzie Release (~52 KB, ścieżki zdjęć referencyjnych, bez samych zdjęć) —
   **zaakceptowane na razie**; wykluczenie wymaga zmiany `BuildCommands` (spoza PR). Do decyzji lidera przed wydaniem.
3. Indeks `docs/adr/README.md` — wiersz 0246 dodany.
4. `-Lighting dusk` — skrypt odmawia (exit 2) w obu trybach; `g3_poses.py winargs` też.

**Uruchomione w chmurze (Linux, 2026-11-16):** pytest `tests/gate3/test_g3_poses.py` 19/19 — w tym 6 testów
uruchamiających `g3-poses.ps1 -Exe` w PowerShell 7.4.6 przeciwko **atrapie gracza** (`tests/gate3/fake_g3_player.py`:
pisze PNG/manifest/log jak runner; ścieżki: 42×2 kadry OK, brak PNG, wyjątek w logu, odmowa, TIMEOUT, `-DryRun` bez exe,
wykluczenie `-Exe`/`-Serial`); `dotnet test tests/g3poses` 17/17; parser PowerShell: 0 błędów.
**NIEuruchomione:** kompilacja C# w Unity, EditMode, build playera Windows, prawdziwy `Kamion.exe` (start procesu
i cytowanie argumentów na Windows, `-logFile`, `runInBackground`, tier High z nakładką PC, czasy rozgrzewki — **UNVERIFIED**).

Komendy dla lidera (Windows):
```
pwsh scripts/build-windows.ps1 -Development -Slot            # -> artifacts/win/kamion-<ver>-<sha>-dev/Kamion.exe (WorldC w buildzie domyślnym)
pwsh scripts/g3-poses.ps1 -Exe artifacts/win/kamion-<ver>-<sha>-dev/Kamion.exe -Only 1-2 -Lighting overcast   # dymny test 2 póz
pwsh scripts/g3-poses.ps1 -Exe artifacts/win/kamion-<ver>-<sha>-dev/Kamion.exe -RefDir <folder ze zdjęciami>  # 42 × overcast+clear, High
```

## Weryfikacja (stan w chmurze, bez Unity i telefonu)
- `dotnet test tests/g3poses/G3PoseTests.csproj`: 16/16 zielone.
- `uv run --project tools/worldgen --with pytest pytest tests/gate3 -q`: 24/25; jedyny FAIL
  `test_gate3_meta.py::test_evidence_apk_info_legacy_and_dirty` dotyczy niezmienionego `gate3_evidence.py`.
- `pwsh` 7.4: parsowanie skryptu OK; `-DryRun` (plan, 42 pozy, filtr, exit 2 dla pustego filtra) OK.
- **NIEuruchomione:** kompilacja w Unity, EditMode w Unity, build Development APK, przebieg na A16.

## Komendy dla lidera — telefon (odroczone, D73)
```
pwsh scripts/test.ps1 -Platform EditMode                                    # G3PoseTests + reszta
pwsh scripts/g3-poses.ps1 -Serial RFGL34SJYDZ -Build -Only 1-2 -Lighting overcast   # dymny test 2 póz
pwsh scripts/g3-poses.ps1 -Serial RFGL34SJYDZ -RefDir <folder ze zdjęciami>         # zainstalowany dev APK, 42 × overcast+clear
```
