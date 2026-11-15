# STATUS — gamepad-0264 (H2, ADR 0264: pad i klawiatura „pełne”, rebinding)

Gałąź `gamepad-0264` od `origin/main` ae372b19c. Agent w chmurze (bez Unity/pwsh). Kod: `game/Assets/_Project/{Input,Gameplay,UI}`, testy `Tests/EditMode/PadKeyboardInputTests.cs`.

## Kroki
- [x] 1. Czysta logika: `PadSteeringMath` (martwa strefa+saturacja, ekspo, amplituda od prędkości z a_lat, limit prędkości skrętu, rampy klawiatury), `PadSteerFilter`, `KeyboardAxisRamp`, `PadKeyboardFeel` + `Resources/Controls/pad_keyboard_feel.json` (WORKING_VALUE), `InputBindingsStore` (plik `input_bindings.json`, schemat 1, migracja v0, zapis atomowy), `DrivingActionCatalog` (stabilne nazwy akcji, domyślne przypisania, JSON assetu ze stabilnymi id), `DrivingActions` (asset Input System z JSON, nadpisania, interaktywny rebinding), `GamepadDriverInput`, `KeyboardBindingsDriverInput`, `ViewCommands`, `DriverInputMixer.InsertBefore`, `PcInputBridge` (Gameplay, auto-instalacja po załadowaniu sceny), `InputBindingsPanel` (UI) + wiersz w `ControlSettingsPanel`.
  - Testy .NET (harness w scratchpadzie, shim Mathf): **18/18 PASS** (dotnet 8.0.428, NUnit 3.14). 3 testy tylko-Unity (GC, JSON z Resources, round-trip Input System) — NIEuruchomione.
- [ ] 2. ADR 0264 + PR.

## Następny krok (komenda dla lidera)
`pwsh scripts/test.ps1 -Platform EditMode` (filtr: `PadKeyboardInputTests`), potem build Windows i jazda z padem.
