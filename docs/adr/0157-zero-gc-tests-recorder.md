# ADR 0157: Testy zero-GC oparte na `Profiling.Recorder("GC.Alloc")`

- **Status:** Zaakceptowano (2026-11-12)
- **Kontekst:** `docs/reports/REVIEW-2026-11-12-s15-mistral-r3.md`, `REVIEW-2026-11-13-s16-mistral-r4.md`, `REVIEW-2026-11-13-s16-mistral-r5.md`

## Context

Część testów regresji „zero alokacji GC” w `game/Assets/_Project/Tests/` używała `System.GC.GetAllocatedBytesForCurrentThread()`. W edytorze Unity pod Mono metoda ta zwraca `0` nawet przy jawnej alokacji (zmierzone w teście próbnym: `GetAllocatedBytesDelta=0` dla `new byte[64]`), przez co testy przechodziły zawsze i nie chroniły przed regresjami GC.

Test próbny (`Recorder.Get("GC.Alloc").sampleBlockCount`, filtrowany na bieżący wątek) wykazał, że licznik `Recorder("GC.Alloc")` działa identycznie w **EditMode** i **PlayMode**:
- EditMode: `isValid=True, noop=0, one64B=1, tenLists=20, GetAllocatedBytesDelta=0` (`artifacts/tests/editmode-20261112-233424.xml`)
- PlayMode: `isValid=True, noop=0, one64B=1, tenLists=20, GetAllocatedBytesDelta=0` (`artifacts/tests/playmode-20261112-233446.xml`)

Dzięki temu testy EditMode nie musiały być przenoszone do PlayMode.

## Decision

1. **Wspólny helper `GcAllocCounter`** w `game/Assets/_Project/Tests/PlayMode/GcAllocCounter.cs`:
   - `GcAllocCounter.Count(Action)` — mierzy `Recorder.Get("GC.Alloc").sampleBlockCount` na bieżącym wątku.
   - `GcAllocCounter.AssertZero(Action measured, Action warmup = null, int baselineSamples = 0, string message = null)` — wykonuje rozgrzewkę (JIT/cache), sprawdza żywotność licznika alokacją kontrolną `new byte[64]` (`> 0`), mierzy `measured` i wymaga `0` próbek `GC.Alloc` netto.
2. **Referencja `Game.Tests.PlayMode` w `Game.Tests.EditMode.asmdef`**:
   - Jednorazowa, jednoliniowa zmiana w `game/Assets/_Project/Tests/EditMode/Game.Tests.EditMode.asmdef`, aby oba zestawy testów korzystały z jednej klasy `GcAllocCounter` bez duplikacji i bez przenoszenia kodu testowego do `Game.Core`.
3. **Przepisane testy (9 plików z `GetAllocatedBytesForCurrentThread` + 2 pliki z lokalną kopią `CountAllocs`)**:
   - EditMode: `NavRoutingTests.cs` (`ZeroGc_LaneGuidanceInDrivingLoop`, `ZeroGc_PlanAndTrack`), `ControlInputLoggerTests.cs` (`Recording_AllocatesNoManagedMemory_InSteadyDrivingWithInputChanges`), `FurnitureRetroSourceAllocTests.cs` (`CompleteRigDoesNotAllocate`, `IncompleteRigWithUnchangedHierarchyDoesNotRescan`, `NoTruckSteadyStateDoesNotAllocate`), `MirrorCostTests.cs` (`StepDue_DoesNotAllocate`), `MirrorRefreshScheduleTests.cs` (`Step_DoesNotAllocate`), `OrientationPhoneTests.cs` (`Step_ZeroGcPerFrame`).
   - PlayMode: `NavHudTests.cs` (`MiniMap_RefreshAndGuidance_ZeroGc`, `LaneBar_DrawsZeroGc`), `ElevenLabsFxAudioTests.cs` (`DrivingLab_AudioUpdate_DoesNotAllocate`), `TyreScrubTests.cs` (`TightTurn10kmh_Scrubs_DoesNotSqueal_NoGc`), oraz deduplikacja w `HudTextAllocTests.cs` i `WorldInstancesRenderGcTests.cs`.
4. **Rozgrzewka w `ControlInputLoggerTests`**:
   - Pierwszy przebieg `RunDrive` alokował `1` próbkę `GC.Alloc` (JIT gałęzi `Observe`/`Event`/`TryFlush`), drugi `0`. Rozgrzewka na osobnej instancji `warm` zachowuje świeży `m_LastAxisT` na mierzonym `log`.

## Tabela mutacji (tymczasowe `new List<int>(1)` w kodzie produkcyjnym → cofnięte)

| Test | Mutacja (plik:metoda) | Wynik (GC.Alloc) |
|---|---|---|
| `NavRoutingTests.ZeroGc_LaneGuidanceInDrivingLoop` | `RoutePlanner.cs:Plan` | **FAIL** (`20`) |
| `NavRoutingTests.ZeroGc_PlanAndTrack` | `RoutePlanner.cs:Plan` | **FAIL** (`20`) |
| `ControlInputLoggerTests.Recording_AllocatesNoManagedMemory_InSteadyDrivingWithInputChanges` | `ControlInputLogger.cs:Observe` | **FAIL** (`3016`) |
| `FurnitureRetroSourceAllocTests.CompleteRigDoesNotAllocate` | `FurnitureRetroSource.cs:BeginCamera` | **FAIL** (`400`) |
| `FurnitureRetroSourceAllocTests.IncompleteRigWithUnchangedHierarchyDoesNotRescan` | `FurnitureRetroSource.cs:BeginCamera` | **FAIL** (`400`) |
| `FurnitureRetroSourceAllocTests.NoTruckSteadyStateDoesNotAllocate` | `FurnitureRetroSource.cs:BeginCamera` | **FAIL** (`400`) |
| `MirrorCostTests.StepDue_DoesNotAllocate` | `MirrorRefreshSchedule.cs:StepDue` | **FAIL** (`2000`) |
| `MirrorRefreshScheduleTests.Step_DoesNotAllocate` | `MirrorRefreshSchedule.cs:Step` | **FAIL** (`2000`) |
| `OrientationPhoneTests.Step_ZeroGcPerFrame` | `ScreenOrientationPolicy.cs:Step` | **FAIL** (`40000`) |
| `NavHudTests.MiniMap_RefreshAndGuidance_ZeroGc` | `MiniMapView.cs:Draw` | **FAIL** (`696`) |
| `NavHudTests.LaneBar_DrawsZeroGc` | `NavDraw.cs:LaneBar` | **FAIL** (`600`) |
| `ElevenLabsFxAudioTests.DrivingLab_AudioUpdate_DoesNotAllocate` | `TruckAudioController.cs:AudioStep` | **FAIL** (`600`) |
| `TyreScrubTests.TightTurn10kmh_Scrubs_DoesNotSqueal_NoGc` | `TruckAudioController.cs:AudioStep` | **FAIL** (`600`) |

## Liczby testów przed / po

- **EditMode przed:** `467 total, 444 passed, 8 failed, 10 skipped` (`artifacts/tests/editmode-20261112-232723.xml`)
- **EditMode po (po merge `origin/main`):** `467 total, 444 passed, 8 failed, 10 skipped` (`artifacts/tests/editmode-20261112-234803.xml`) — te same 8 znanych porażek środowiskowych (`CarPaintMaterialTests.DepositionChannel` ×2, `MirrorPresentationTests` ×2, `TruckDoorCrownTests` ×3, `LightPostPolicyTests` ×1).
- **PlayMode przed:** `151 total, 136 passed, 0 failed, 14 skipped` (`artifacts/tests/playmode-20261112-232825.xml`)
- **PlayMode po (po merge `origin/main`):** `151 total, 136 passed, 0 failed, 14 skipped` (`artifacts/tests/playmode-20261112-234217.xml`).

## Open

- Brak realnych alokacji wykrytych w przepisanych testach po poprawnej rozgrzewce (żaden test nie wymagał `[Ignore]`).
- Testy oparte o `Is.Not.AllocatingGCMemory()` (`CabScreensTests`, `CombinationLabTests`, `VehicleLabTests`) używają tego samego mechanizmu `GC.Alloc` i mają własne kontrole `Is.AllocatingGCMemory()` — pozostawione bez zmian.
