# ADR 0244 — Audyt pętli jazdy: zero GC i koszt CPU (klatka i krok fizyki)
Status: Proposed (agent G2, chmura G, s21, gałąź `perf-loop-0244`), 2026-11-15. Do weryfikacji przez lidera (Unity + A16).
Zadanie: `docs/owner/CLOUD-G-PROMPT-S21.md` G2; BACKLOG B-098 (HUD dev), B-106 (testy GC.Alloc dla fizyki, audio, kamery).
Kontynuacja: ADR 0131 (zero GC w renderze mebli), 0157 (testy `GC.Alloc` nawigacji), 0068 (koszt przebiegów stałych), 0177 (sensory diagnostyki).

## Kontekst
Pętla jazdy na A16 (Helio G99, 4 GB) ma budżet 33,3 ms przy 30 FPS (docs/PERFORMANCE_BUDGETS.md). Krok fizyki 100 Hz ma już test
`FixedStep_ZeroGcAllocation` / `Combination_FixedStep_ZeroGcAllocation` (PlayMode, 2000 kroków), HUD jazdy, nawigacja, ekrany kabiny,
`WorldInstances.Render` i meble mają testy `GC.Alloc`. Brakowało przeglądu całej reszty kodu wykonywanego co klatkę: diagnostyki
(która działa w KAŻDYM buildzie, także bez flagi deweloperskiej), oświetlenia kabiny i reflektorów, kamer, logów.

Metoda (bez Unity, w chmurze): przegląd wszystkich `Update`/`LateUpdate`/`FixedUpdate`/`beginCameraRendering`/`beginContextRendering`
w `game/Assets/_Project` poza `Editor/` i `Tests/` (47 plików z takimi metodami) i metod, które wywołują; wzorce: LINQ, closures, boxing (`string.Format`,
`params`), `ToString`/konkatenacja/interpolacja, `new` w pętli, `foreach` po interfejsach, `GetComponent`/`Find*`/`Camera.main`,
nazwy właściwości shaderów jako string. Liczby bajtów poniżej to **ESTIMATED** z budowy kodu (rozmiar obiektu Mono ok. 16 B nagłówka +
dane), nie pomiar — pomiar w planie na końcu.

## Decyzja — poprawione bezpieczne przypadki (bez zmiany zachowania gry)

| plik:linia (po zmianie) | było | jest | szacunek przed (ESTIMATED) | test |
|---|---|---|---|---|
| `Telemetry/DiagnosticsSampler.cs:269` `FlushCsv` (co 2 s, każdy build) | wiersz `frametimes.csv` przez `StringBuilder.Append(long)` + 5× `float.ToString("F*")` = ok. 6 stringów na klatkę; nagłówek obiecywał 8 kolumn, wiersze miały 6 (`mirror_n`, `ab` z ADR 0068 nigdy nie zapisane — `perfgate` cicho dopełniał pustymi) | `Telemetry/FrameCsvFormat.cs` (czysty C#): wiersz do bufora `char[]` 128 wierszy × 200 znaków, zapis `StreamWriter.Write(char[],int,int)`; zapisuje też `mirror_n` i `ab` (puste, gdy A/B wyłączone, jak opisuje `formats.py`); usunięty `StringBuilder` 64 K znaków | ok. 200 B/klatkę → ~6 KB/s przy 30 FPS, ~12 KB/s przy 60 FPS | `tools/loop-runner` (30 testów .NET: zgodność z `ToString` na 800 000 floatach, 0 B alokacji, nagłówek = kontrakt `perfgate`); EditMode `PerfLoop0244Tests` (zgodność + `GcAllocCounter`) |
| `Rendering/Runtime/Sky/KamionHeadlamps.cs:35` `Resolve` (nocą, przy światłach mijania, co 0,25 s) | `Resources.FindObjectsOfTypeAll<CabInteriorLighting>()` + LINQ `Where(...).ToArray()` z closure przy KAŻDYM sprawdzeniu, także gdy wiązanie było poprawne; `Shader.GetGlobalTexture("_TruckLightState")` po nazwie co klatkę | rejestr włączonych kabin `CabInteriorLighting.Enabled` (OnEnable/OnDisable — `isActiveAndEnabled` jest prawdą dokładnie między nimi), ten sam filtr i te same liczniki (0 / 1 / „found N”); kotwice przez `GetComponentsInChildren(true, list)` tylko przy zmianie wiązania; id właściwości w `static readonly` | tablica + closure + delegat + iteratory ≈ 250 B × 4/s ≈ 1 KB/s nocą + przegląd wszystkich obiektów typu (CPU niezmierzone) | EditMode `HeadlampProjectionTests` (7 istniejących bez zmian + `PeriodicRecheckOfABoundCab_ZeroGcAlloc`), `PerfLoop0244Tests.CabRegistry_TracksEnableAndDisable` |
| `Rendering/Runtime/Truck/CabInteriorLighting.cs:179/197` `Refresh` (LateUpdate) | bez włączonego `EnvironmentLighting` (DrivingLab nie ma rigu nieba — scena bramek 1–2) `FindAnyObjectByType<EnvironmentLighting>()` **co klatkę** | w trybie gry najwyżej 1 wyszukiwanie na `EnvironmentSearchIntervalS` = 1 s (WORKING_VALUE; wzór ADR 0131), znaleziony obiekt trzymany, dopóki żyje; w edytorze (visual QA) jak dotąd przy każdym wywołaniu | 30 przeszukań sceny/s → 1/s (koszt jednego przeszukania niezmierzony; w playerze bez GC) | EditMode `CabEnvironmentFallback_EditModeSearchesEveryCall`; PlayMode `CabEnvironmentThrottleTests` (2) |
| `Rendering/Runtime/Sky/WorldAtmosphere.cs:106` `Push` (co klatkę) | `Shader.SetGlobalFloat("_KamionDimColourDesaturation", …)` — hash nazwy co klatkę | id w `static readonly` | bez GC; ~1 haszowanie stringu/klatkę | (trywialne, bez testu) |
| `Gameplay/DrivingLabBootstrap.cs:701` `UpdateTurnSignals` (Update) | `GetComponent<TruckLights>()` co klatkę, gdy go brak (ciągnik graybox); w edytorze każde puste `GetComponent` alokuje obiekt „fake null” | `TryGetComponent(out m_Lights)` — ten sam wynik, bez alokacji w edytorze | edytor: ~1 obiekt/klatkę; player: tylko wyszukanie komponentu | (trywialne, bez testu) |

Uwaga o tekście CSV: `FrameCsvFormat.AppendFixed` liczy z dokładnej wartości binarnej i remisy (np. 41,5625 przy F3) zaokrągla od zera;
.NET 8 część takich remisów zaokrągla w dół (1,25 % wartości `t_s` w zakresie 0–36 000 s, 0,036 % `frame_ms` 0–2000 ms, 0 % `render_scale`) —
różnica o 1 na ostatniej cyfrze, nic więcej (test). Runtime telefonu (biblioteka klas Mono pod IL2CPP) może drukować float z 7 cyframi
znaczącymi przed zaokrągleniem (reguła .NET Framework) — **UNVERIFIED**; wtedy stare i nowe wiersze różnią się tylko cyframi poza precyzją
floata (`t_s` > 1000 s). Parser `perfgate` i `device-metrics.ps1` czytają liczby, więc to bez znaczenia dla percentyli.

## Pozostałe znaleziska (nie zmienione — opis, priorytet, propozycja)

| plik:linia | problem | szacunek (ESTIMATED) | prio | propozycja |
|---|---|---|---|---|
| `Vehicle/Runtime/UnityGroundQuery.cs:37` ← `Components/WheelGroup.cs:144`, `TrailerModel.cs:250` | 152 pojedyncze `Physics.Raycast` na krok zestawu (10 końców osi × 15 + 2 nogi) = 15 200/s, sekwencyjnie na wątku głównym | 507 promieni/klatkę przy 30 FPS; koszt promienia na A16 NIEZMIERZONY — przy 1–3 µs (założenie, bez źródła) 0,5–1,5 ms/klatkę | P1 (najpierw pomiar) | Profiler A16: jeśli `Physics.Raycast` w `FixedUpdate.PhysicsFixedUpdate`/`VehicleBody.Tick` > 0,5 ms/klatkę → `RaycastCommand.ScheduleBatch` z pozy na początku kroku (promienie zależą tylko od pozy nadwozia i skoku zawieszenia z poprzedniego kroku); wymaga `IGroundQuery.Prefetch` i testu zgodności w `tools/physics-runner` |
| `Telemetry/DiagnosticsSampler.cs:286` `WriteSummary` (co 5 s, każdy build) | `string.Format` z 23 argumentami (tablica `object[]` + boxing ~20 wartości), `QualitySettings.names` (nowa tablica), konkatenacja rozdzielczości, `JsonUtility.ToJson` ~1 KB, `File.WriteAllText` na wątku głównym | ~6–9 KB / 5 s ≈ 1,5 KB/s + synchroniczny zapis pliku na wątku głównym (czas niezmierzony) | P2 | zachować format `[DIAG]` (parsuje go `perfgate`): `StringBuilder` + `FrameCsvFormat.AppendFixed`, nazwa tieru z cache po indeksie, zapis `summary.json` przez istniejący wątek PSS (ADR 0177) |
| `Rendering/Runtime/Truck/ContactShadowCaster.cs:111/238` `Refresh` (LateUpdate, każdy pojazd) | co klatkę: raycast na każdy wierzchołek płyty (ciągnik: 2 sekcje 2×3 i 3×3 wierszy → 21) + koło, przebudowa siatki (`Clear`, `SetVertices`, `SetUVs`×2, `SetTriangles`) i 4× `SetGlobalVectorArray` — także na postoju | ~40–60 promieni/klatkę dla zestawu (z budowy `TruckAssetBuilder.AddContactShadow`; naczepa nie liczona dokładnie) + upload siatki; bez GC (listy reużywane) | P2 | pomijać przebudowę, gdy poza pojazdu i kół zmieniła się o < 1 mm / 0,05° od ostatniej (postój, korki); mierzyć `ContactShadowCaster.LastHits` |
| `UI/Driving/DrivingHud.cs:769` `BuildTelemetry` (5 Hz, tylko panel telemetrii dev) | ~100 `ToString`/`PadLeft`/`PadRight` na odświeżenie | ~20 KB/s przy otwartym panelu | P2 (B-098) | `FrameCsvFormat.AppendFixed` do `char[]` + `Text.text` tylko przy zmianie (już jest porównanie `SbEquals`) |
| `Gameplay/DrivingLabBootstrap.cs:759` `CouplingStatus` ← `DrivingHud.cs:818` (10 Hz, dev + telemetria) | ~10 stringów na odświeżenie | ~5 KB/s przy widocznym panelu | P2 | jw.; klucz zmiany z kwantyzowanych wartości (cm, °) |
| `UI/Diagnostics/DiagnosticsOverlay.cs:222` `RefreshNow` (co 0,5 s, tylko otwarty panel diagnostyki) | `StringBuilder` + `ToString` liczb i końcowy `ToString()` | kilka KB/s przy otwartym panelu | P2 | jw. |
| `Input/ControlInputLogger.cs:157` `TryFlush` | linia `[CONTROLS]` budowana z `ToString` w paczce (komentarz: „allocates only on that frame”) | ~1 linia / kilka s przy sterowaniu | P2 | zostawić (diagnostyka D-sterowania); ewentualnie `AppendFixed` |
| `Camera/CameraRig.cs:181` `FlushPoseLog` | `camlog=1`: `StringBuilder` + `ToString` 12 kolumn × 200 wierszy | tylko z argumentem diagnostycznym | P2 | zostawić |
| `Gameplay/ScreenOrientationPolicy.cs:230` `Diagnostics` (Update) | `Camera.main` + `eulerAngles` co klatkę | bez GC (Unity 6 trzyma `Camera.main` w cache); <1 µs | P2 | `ViewCameraResolver` jak w oświetleniu kabiny, jeśli Profiler pokaże koszt |
| `Gameplay/TruckAudioController.cs:300`, `Audio/EngineAudio.cs:251`, `Audio/AmbientAudio.cs:72` | przegląd wzorców: brak LINQ, `ToString`, `new` w ścieżce co klatkę (alokacje tylko przy budowie warstw i logach zdarzeń) | — | — | **nie zmieniane** (ADR 0232, inne zadanie); potwierdzić Profilerem `GC.Alloc` w `TruckAudioController.Update` (B-106) |
| `Vehicle/Physics/**` (rdzeń) | zero GC potwierdzone testami PlayMode i .NET (`Stage2Tests`, `ValidationTests`, `BodyContactTests`); alokacje tylko przy sprzęganiu (`AxleLoads`, `SetCollisionIgnored`) | rdzeń .NET p50 6,4–6,7 µs/krok (desktop, PHYSICS_VALIDATION §4) | — | Burst/Jobs dla opon **nieuzasadnione** teraz: 10 końców osi × 4 sub-stepy × 100 Hz = 4000 wywołań opony/s; nawet przy 10× wolniejszym IL2CPP na A16 (założenie) ~0,2 ms/klatkę przy 30 FPS. Próg ponownej oceny: `VehicleBody.AverageStepMicros` na A16 > 150 µs |
| `Rendering/Runtime/Sky/StreetLamps.cs:329` `PickNearest` (4 Hz) | O(latarnie × n), n ≤ 9 | znikome | — | bez zmian |
| `Vehicle/Runtime/TruckLights.cs:91` | `SetPixels`/`Apply` tylko przy zmianie stanu (hash) | — | — | bez zmian (dobrze) |
| Streaming świata | w runtime brak streamingu (scena regionu statyczna; płynne kafle = ADR 0235, inne zadanie); `WorldInstances.Render` ma test `GC.Alloc` | — | — | ocenić po 0235 |

## Sprawdzenie: fizyka tylko w stałym kroku, render interpolowany
- `VehicleBody.FixedUpdate` → `Tick` (siły z modelu, `AddForce*`), `TrailerBody` w tym samym kroku (zestaw); `DepotBarrier.FixedUpdate`,
  `WorldSafetyNet.FixedUpdate`, kolumna kierownicy `DrivingLabBootstrap.FixedUpdate` (ADR 0058), `VehicleTelemetryRecorder.FixedUpdate`.
  `Update` czyta tylko wejście kierowcy (gaz/hamulec/biegi do `DriverInput`) — to wejście, nie fizyka. Brak `transform.position +=` dla pojazdu.
- Interpolacja: `Rigidbody.interpolation = Interpolate` dla ciągnika (`VehicleBody.cs:95`), naczepy (`TrailerBody.cs:75`) i szlabanu
  (`DepotBarrier.cs:77`); koła/kabina: `VehicleVisuals`/`TrailerVisuals` zbierają stan w `FixedUpdate` i interpolują w `LateUpdate` tym
  samym współczynnikiem co Rigidbody. Kamera (`CameraRig`) liczy przyspieszenie w `FixedUpdate`, pozę w `LateUpdate` z interpolowanej
  transformacji. Zgodne z CLAUDE.md i docs/04 §1.

## Plan pomiaru dla lidera (A16 `RFGL34SJYDZ`)
1. Testy: `pwsh scripts/test.ps1 -Platform EditMode` (nowe: `PerfLoop0244Tests` ×4, `HeadlampProjectionTests.PeriodicRecheckOfABoundCab_ZeroGcAlloc`;
   istniejące `HeadlampProjectionTests` ×7 muszą zostać zielone), `pwsh scripts/test.ps1 -Platform PlayMode` (nowe `CabEnvironmentThrottleTests` ×2;
   istniejące `*ZeroGc*`). `dotnet test tools/loop-runner/Tests/LoopTests.csproj -c Release`, `dotnet test tools/physics-runner -c Release`.
2. Dwa buildy Development tej samej sceny: main `830b077bf` (A) i `perf-loop-0244` (B): `pwsh scripts/build-android.ps1 -Development -Install -Run -Serial RFGL34SJYDZ`.
3. Profiler (Autoconnect albo `adb forward` + Unity Profiler, moduł CPU → Hierarchy, kolumna „GC Alloc”, i moduł Memory: „GC Allocated In Frame”,
   „GC Allocation In Frame Count”, „GC Used Memory”): 90 s DrivingLab autopilot `circle50` 40 km/h z naczepą 40 t oraz 90 s WorldC trasą nocą
   (światła mijania → ścieżka reflektorów). Zapisać: suma GC Alloc / 60 s (A vs B), liczba klatek z GC Alloc > 0, klatki ze skokiem
   `GC.Collect` (znacznik `GC.Collect` w CPU), czas `CabInteriorLighting.LateUpdate` w DrivingLab, `Physics.Raycast` w `FixedUpdate` (pod decyzję P1).
   Oczekiwanie (ESTIMATED): B bez alokacji w klatkach poza flushem `[DIAG]` co 5 s i panelami dev; A ok. 6 KB/s z `FlushCsv`.
4. Licznik kolekcji bez Profilera: `GC.CollectionCount(0)` przed/po 90 s nie jest dziś logowany — jeśli potrzebny, dopisać pole na KOŃCU linii
   `[DIAG]` dopiero po sprawdzeniu, że `perfgate` toleruje nowy klucz (format v1) — osobna zmiana.
5. Telemetria klatek po zmianie: `pwsh scripts/device-metrics.ps1 -Launch -DurationSeconds 90 -Serial RFGL34SJYDZ` — `frametimes.csv` ma teraz
   wypełnione `mirror_n` (i `ab` przy `rq_ab`); p50/p95/p99 bez pogorszenia względem A.

## Konsekwencje
- Diagnostyka w każdym buildzie przestaje alokować co klatkę; `frametimes.csv` niesie wreszcie kolumny ADR 0068 (koszt luster per klatka).
- Nocą wiązanie reflektorów nie przegląda już wszystkich obiektów typu co 0,25 s.
- DrivingLab (bramki 1–2) nie przeszukuje sceny co klatkę.
- Ryzyko: kod C# skompilowany w chmurze tylko składniowo (Roslyn, C# 9) i w .NET (`FrameCsvFormat`); kompilacja Unity, EditMode, PlayMode
  i pomiar na A16 — lider.
