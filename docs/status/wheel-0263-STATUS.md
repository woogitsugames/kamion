# STATUS — wheel-0263 (H1, ADR 0263: kierownica, pedały, H-shifter, FFB na PC)

Gałąź `wheel-0263` (z `origin/main`). Agent w chmurze: bez Unity, bez pwsh. Nie scalać bez weryfikacji lidera w Unity.

## Zrobione
- 15.11: warstwa wejścia kierownicy PC w `game/Assets/_Project/Input/` (Game.Controls, bez zmian asmdef):
  `WheelAxis.cs` (kalibracja osi, pedały odwrócone/łączone, martwe strefy, `AxisCalibrator`, `AutoSteer`/`AutoPedal`),
  `WheelSteeringMap.cs` (zakres 270–900°, `ScaledToLock`/`OneToOne`, soft-lock), `HShifterMapper.cs` (H + zakres, łopatki, zbocza),
  `ForceFeedback.cs` (`IForceFeedbackSink`, Null/Recording, `ForceFeedbackModel` z `AligningTorqueTotal`), `WheelDeviceProfile.cs` + `Resources/Controls/wheel_profiles.json` (7 profili, VID/PID ze źródeł),
  `WheelSettings.cs` (PlayerPrefs `controls.wheel`, schemat 1, migracja), `HidWheelDriverInput.cs` (Input System HID), `PcWheel.cs`.
- `DriverIntent`: nowe pola `DirectSteer`, `Clutch`, `TargetGear`; `DriverInputMixer` je przenosi. `DrivingLabBootstrap`: źródło kierownicy po klawiaturze, `DirectSteer` → `Column.SnapTo`, krok FFB w `FixedUpdate`, stop przy pauzie/fokusie/zniszczeniu.
- Testy EditMode: `PcWheelInputTests` (30), `ForceFeedbackModelTests` (12), `PcWheelDataTests` (7, Unity-only: JSON, migracje, zero GC).
- **Uruchomione poza Unity**: 42/42 zielone (`dotnet test`, .NET 8.0.428, NUnit 3.14, atrapa `UnityEngine.Vector3/Mathf`) — PcWheelInputTests + ForceFeedbackModelTests.
- Dokumenty: `docs/adr/0263-kierownica-pedaly-ffb.md` (badanie FFB ze źródłami, propozycja backendu SDL3 → WGI → HIDO), `docs/compat/wheels.md`.

## NIEuruchomione
- Unity EditMode (wszystkie 3 pliki testów w Unity), kompilacja w Unity plików z Input System (`HidWheelDriverInput`, `WheelSettings`, `PcWheel`, bootstrap), build Windows, test na kierownicy.

## Następny krok (lider, Windows)
`pwsh scripts/test.ps1 -Platform EditMode` → sprawdź `artifacts/tests/*.xml` (filtry: `PcWheelInputTests`, `ForceFeedbackModelTests`, `PcWheelDataTests`), potem `pwsh scripts/test.ps1 -Platform PlayMode` (regresja dotyk/klawiatura) i jazda z kierownicą (Input Debugger → popraw ścieżki w `wheel_profiles.json`).
