# ADR 0246 — zrzuty z telefonu dla póz par zdjęciowych bramki 3 (automat)
Status: Proposed (chmura G, agent G4, gałąź `g3-poses-0246`), 2026-11-15. Do weryfikacji i scalenia przez lidera.
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

## Weryfikacja (stan w chmurze, bez Unity i telefonu)
- `dotnet test tests/g3poses/G3PoseTests.csproj`: 16/16 zielone.
- `uv run --project tools/worldgen --with pytest pytest tests/gate3 -q`: 24/25; jedyny FAIL
  `test_gate3_meta.py::test_evidence_apk_info_legacy_and_dirty` dotyczy niezmienionego `gate3_evidence.py`.
- `pwsh` 7.4: parsowanie skryptu OK; `-DryRun` (plan, 42 pozy, filtr, exit 2 dla pustego filtra) OK.
- **NIEuruchomione:** kompilacja w Unity, EditMode w Unity, build Development APK, przebieg na A16.

## Komendy dla lidera
```
pwsh scripts/test.ps1 -Platform EditMode                                    # G3PoseTests + reszta
pwsh scripts/g3-poses.ps1 -Serial RFGL34SJYDZ -Build -Only 1-2 -Lighting overcast   # dymny test 2 póz
pwsh scripts/g3-poses.ps1 -Serial RFGL34SJYDZ -RefDir <folder ze zdjęciami>         # zainstalowany dev APK, 42 × overcast+clear
```
