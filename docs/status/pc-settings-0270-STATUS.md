# STATUS pc-settings-0270 (H8, ADR 0270)

- [15.11] Model/JSON/migracje (`Core/Settings`), runtime + panel (`UI/Settings`), kanały głośności (EngineAudio/AmbientAudio/ClusterChime przez `AudioMixLevels`), przycisk „Ekran, grafika, dźwięk” w BootMenu (poza telefonami), stosowanie przy starcie w GameBootstrap.
- [15.11] Testy `Tests/EditMode/PcSettingsTests.cs` 27/27 poza Unity (dotnet 8 + NUnit 3 + atrapa Mathf/JsonUtility; log `artifacts/pc-settings-0270/dotnet-test.log`, 0 ostrzeżeń). W Unity NIEuruchomione, kompilacja UI/Gameplay/Audio w Unity NIEsprawdzona.
- ADR `docs/adr/0270-menu-ustawien-pc.md`.
- NASTĘPNY KROK (lider, Windows): `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64` → potem `pwsh scripts/build-windows.ps1 -Slot -Regions knyszyn-w -Run` i ręcznie: menu → „Ekran, grafika, dźwięk” → zmiana trybu okna → odliczanie 15 s → powrót; zrzut panelu do visual-qa.
