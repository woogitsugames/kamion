# Audyt GC — alokacje na zarządzanej stercie w pętli jazdy (2026-11-12, mistral)

Zakres: statyczny przegląd całego C# w `game/Assets/_Project/**` bez `Editor/` i `Tests/` (165 plików, ~28 tys. linii).
Szukane: alokacje w metodach wołanych co klatkę / co krok fizyki (`Update`, `LateUpdate`, `FixedUpdate`, callbacki Input/UI wołane ciągle) i w metodach przez nie wywoływanych.
Baza: `main` @ `e0328ea4`. Metoda: mapowanie wszystkich `Update/LateUpdate/FixedUpdate/OnGUI/OnRenderObject` + ścieżek wywołań, grep wzorców (`new` na typach referencyjnych, LINQ, string concat/format/interpolacja, boxing, `ToString`, `ToArray/ToList`, `GetComponent*` w pętli, `Physics.*All` bez NonAlloc, `Camera.main` w pętli, `StartCoroutine` co klatkę, string-klucze shaderowe w pętli), potem czytanie ciał metod.

## Znaleziska (od najgorszych)

### 1. `UI/Driving/DrivingHud.cs:706` — etykieta gyro alokuje co klatkę w trybie gyro — PEWNE (warunkowe)
- **Metoda:** `RefreshNow()` ← `Update()` (co klatka, 30–60 Hz).
- **Problem:** warunek `Time.unscaledTime >= m_NextTelemetry` (linia 705), ale `m_NextTelemetry` jest przesuwane tylko w gałęzi `TelemetryVisible` (linia 709). Gdy gyro jest włączone, a telemetria ukryta, oba bloki mają `m_NextTelemetry` zamrożone w przeszłości → linia 706 wykonuje się **każdej klatki**: `float.ToString("F1")` + 3-częściowa konkatenacja stringów.
- **Alokacja:** ~2 obiekty string (~64–96 B) na klatkę; przy 60 fps ≈ 4–6 KB/s wyłącznie z tego wiersza.
- **Poprawka:**
```csharp
if (gyro && m_Ctx.Gyro != null && Time.unscaledTime >= m_NextTelemetry)
{
    m_NextTelemetry = Time.unscaledTime + 0.2f;   // throttle also for the gyro label
    m_GyroLabel.text = "Gyro: " + m_Ctx.Gyro.RelativeTiltDeg.ToString("F1", CultureInfo.InvariantCulture) + "°"
        + (m_Ctx.Gyro.HasSensor ? "" : "  (brak czujnika)");
}
```
(albo wspólny throttle: przesuń `m_NextTelemetry` przed oba bloki i użyj jednego `if` łączonego warunkiem `gyro || TelemetryVisible`.)

### 2. `UI/Driving/DrivingHud.cs:710` (+ `:812`) — `BuildTelemetry()` co 0,2 s, ~1–2 KB stringa — PRAWDOPODOBNE
- **Metoda:** `RefreshNow()` ← `Update()`, throttle 0,2 s (5 Hz), tylko gdy `TelemetryVisible`.
- **Alokacje:** `sb.ToString()` w `BuildTelemetry()` (linia ~874) — jeden string ~1–2 KB na wywołanie; dodatkowo boxing enuma w `sb.Append(m.Amt.State)` (linia 812, `StringBuilder.Append(object)`).
- **Poprawka:** cache ostatniego stringa i przypisanie tylko przy zmianie; `Append((int)m.Amt.State)`:
```csharp
var s = BuildTelemetry();
if (!ReferenceEquals(s, m_LastTelemetry)) { m_LastTelemetry = s; m_Telemetry.text = s; }
// and in BuildTelemetry: .Append((int)m.Amt.State)
```

### 3. `UI/Diagnostics/DiagnosticsOverlay.cs:193–195, 227` — overlay diagnostyczny co 0,5 s — PRAWDOPODOBNE
- **Metoda:** `RefreshNow()` ← `Update()` (`RefreshInterval = 0.5f`), gdy panel widoczny.
- **Alokacje:** `sb.ToString()` (~1 KB, linia 227) + 3 konkatenacje/interpolacje etykiet przycisków (linie 193–195: `$"Cel: {targetFps} FPS"`, `"Jakość: " + QualityTiers.Current`, …) na każde odświeżenie (2 Hz).
- **Poprawka:** cache'ować etykiety (zmieniają się rzadko) i porównywać przed przypisaniem; body zostawić jako `sb.ToString()` tylko przy zmianie zawartości.

### 4. `UI/CabDisplays/CabScreens.cs:242` — `new DriverInput` w każdym ticu `LateUpdate`, gdy brak pojazdu — WĄTPLIWE (niski wpływ)
- **Metoda:** `Sample()` ← `Refresh()` ← `LateUpdate()` (cluster 20–30 Hz, nav 5–10 Hz, din).
- **Alokacja:** gdy `vehicle == null || model == null` (ekrany bez podpiętego pojazdu — boot/QA) alokowany jest nowy obiekt `DriverInput` przy każdym odświeżeniu ekranu. Podczas jazdy `vehicle.Input` jest zwracane bez alokacji.
- **Poprawka:** statyczny/instancyjny fallback:
```csharp
static readonly DriverInput s_ParkedInput = new DriverInput { ParkingBrake = true, Selector = GearSelector.Drive };
DriverInput input = vehicle != null && model != null ? vehicle.Input : s_ParkedInput;
```

### 5. `UI/CabDisplays/NavLayout.cs:298` — `Abbreviate()` alokuje przy każdej nowej nazwie ulicy — WĄTPLIWE (ograniczone)
- **Metoda:** `Draw()` nav (5–10 Hz) → linie 237, 365.
- **Alokacja:** łańcuch `Replace` (3 stringi przejściowe + wynik) przy **pierwszym** wystąpieniu każdej nazwy; dalej cache `s_AbbrevCache`. Liczba unikalnych nazw na trasie jest skończona, więc alokacje ustają po przejechaniu odcinka — ale nawigacja po nowym mieście generuje serię alokacji.
- **Poprawka:** opcjonalnie — ręczna zamiana prefiksów na `TextBuffer` bez alokacji, albo zostawić (cache działa).

## Sprawdzone ścieżki — BEZ alokacji GC (dla kompletności)
- **Fizyka (co FixedUpdate, 100 Hz):** `VehicleBody.Tick` (`Vehicle/Runtime/VehicleBody.cs:153`) — `ChassisState` to struct, `CombinationModel.Step`/`VehicleModel.Step` nie alokują (`new` tylko w konstruktorach); `UnityGroundQuery.Raycast` używa pojedynczego `Physics.Raycast(..., out RaycastHit)` (bez alokacji tablicy), cache `Dictionary<Collider, SurfaceProps>` bez boxingu; `DepotBarrier.Sense` używa `Physics.OverlapBoxNonAlloc`; `WorldSafetyNet.Check` pojedynczy raycast, throttlowany.
- **Input co klatkę:** `DriverInputMixer.Sample` — scratch array `DriverIntent[]`, iteracja po indeksach; `ControlInputLogger.Observe` — ring buffer `Entry[]`, flush batchowany; `GyroSteering.Sample`, `PathFollowerDriverInput.Sample`, `AutopilotDriverInput`, `TouchSteeringWheel`, `TouchControls` (callbacki pointerów) — bez alokacji.
- **Render/visuals co klatkę:** `CameraRig` (FixedUpdate/LateUpdate), `VehicleVisuals`/`TrailerVisuals` (Capture + interpolacja w LateUpdate), `TruckVisualRig`/`TrailerVisualRig.Apply` (wywoływane z `Update` tylko przy zmianie tieru), `TruckLights.Refresh` (hash-gate, tekstura 16 px), `ContactShadowCaster.Refresh` (listy czyszczone i używane ponownie; `Mesh.SetVertices(List)` kopiuje do natywnego bufora — brak GC), `RenderTextureMirror.Schedule` (zadeklarowane "No allocation"), `ReversingCamera.LateUpdate`, `VehicleReflectionCapture.LateUpdate`, `CabInteriorLighting.RefreshForView`, `StreetLamps.LateUpdate` (throttle 0,25 s, tablice statyczne), `QualityProfileApplier.LateUpdate` (tylko przy zmianie jakości), `ExtraViewCostMonitor`/`AdaptiveFrameDriver.Update`.
- **HUD/UI:** `DrivingHud.RefreshNow` poza pozycjami 1–2 — cache stringów (`k_SpeedStrings`, `k_AirStrings`, `k_CruiseStrings`), porównania `ReferenceEquals` przed przypisaniem; `UiViewport.Refresh` — bez alokacji przy braku zmiany; `TouchWidgets` LateUpdate; `BootMenu.Update`, `ControlSettingsPanel.Update` (rebuild tylko przy zmianie ekranu).
- **Telemetria:** `DiagnosticsSampler.Update` — `FrameTimingManager` do preallocated `FrameTiming[1]`, ring `m_Pending*`, flushy CSV/summary throttlowane (2 s / 5 s), `CsvRecorder` buforuje w `char[]` + `double[]`; `FrameTimeStats` ring + scratch.
- **Audio:** `EngineAudio.Update`, `TruckAudioController.Update`, `AmbientAudio.Update`, `EngineLayerGrid.Tick`, `PerspectiveLoop.Set` — bez alokacji (one-shoty tylko na eventach).
- **Brak wzorców:** LINQ poza `World/Import` i `Rendering/Editor` (tylko inicjalizacja/editor); brak `Physics.*All` bez NonAlloc w pętli; brak `StartCoroutine` w pętli; brak string-kluczy `Animator`/`SetFloat("...")` w pętli (wszystkie `Shader.PropertyToID`); brak `Dictionary<enum, …>` (boxing); `Camera.main` tylko w `ViewCameraResolver.Resolve` (koszt CPU tag-lookup, nie GC; udokumentowane ADR 0044 r9).

## Podsumowanie (po polsku)
Rdzeń pętli jazdy — fizyka w `FixedUpdate`, wizualy z interpolacją, input, audio i kamery — jest czysty: zero alokacji GC na klatkę/krok, co potwierdza tezę projektu. Znalezione alokacje siedzą wyłącznie w warstwie UI/diagnostyki i wszystkie oprócz jednej są throttlowane:
1. Najważniejsza: etykieta gyro w HUD (`DrivingHud.cs:706`) alokuje dwa stringi **każdej klatki**, gdy gyro jest aktywne, bo throttle `m_NextTelemetry` jest przesuwany tylko w gałęzi telemetrii — poprawka to jedna linia.
2. `BuildTelemetry()` (5 Hz) i overlay diagnostyczny (2 Hz) alokują ~1–2 KB stringów na odświeżenie — akceptowalne, ale tanio można dodać cache ostatniej wartości; dodatkowo boxing enuma `AmtState` w `StringBuilder.Append`.
3. `CabScreens.Sample` alokuje `DriverInput` tylko gdy ekrany nie mają podpiętego pojazdu; `NavLayout.Abbreviate` alokuje tylko przy pierwszej wystąpieniu nazwy ulicy (cache działa).
Nie znaleziono: LINQ, `ToArray/ToList`, `Physics.*All` bez NonAlloc, `StartCoroutine` w pętli, boxingu enumów w słownikach ani string-kluczy shaderowych w pętli jazdy.
