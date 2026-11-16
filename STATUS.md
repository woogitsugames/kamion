# STATUS stream-desktop-s23 (D44)
- Zrobione: `StreamingContentChoice` (czysta logika treść/budżet per platforma+tier), hak `TryInstallFromLaunch` używa jej + log `[STREAM] content …` ze źródłem tieru; testy EditMode `StreamingContentChoiceTests` 23/23 pod .NET 8.
- NASTĘPNY KROK (lider): `pwsh scripts/test.ps1 -Platform EditMode -Filter 'Game.Tests.StreamingContentChoiceTests;Game.Tests.WorldStreamingPolicyTests;Game.Tests.WorldStreamerHook0273Tests'`
