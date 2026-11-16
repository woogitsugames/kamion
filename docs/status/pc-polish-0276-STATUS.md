# STATUS pc-polish-0276 (H10, ADR 0276) — chmura H r3
Gałąź `pc-polish-0276` (baza origin/main `639da4e54`). Bez Unity / Windows / GPU.

- [16.11] (a) `MenuOverlayLayout` (Game.Controls, czysta) + `MenuOverlayBoard`; `BootMenu` w bloku przesuwanym w pionie,
  `DiagnosticsOverlay` pozycjonowany z wyniku. Test EditMode `MenuOverlayLayoutTests` (dotnet z atrapą: 38/38 razem z BuildInfoTests),
  PlayMode `MenuOverlayUiTests` napisany.
- [16.11] (b) `scripts/postbuild-windows.py`: manifest sha256 `Kamion_Data` → `build-id.json` obok exe (12 hex), `BuildInfo.IdentityLabel`
  w menu / „Informacje” / nakładce, `[BOOT] … content=`; `package-windows.py`: nazwa `…[-regions]-<hash>-win64.zip`, weryfikacja.
- [16.11] (c) `build-windows.ps1`: `Kamion-<region>.cmd` z logu buildu + `Kamion-okno.cmd`, `-Package`, symbole Burst do
  `artifacts/win/symbols/`, normalizacja `-Regions`. Do zipu tylko `Kamion-okno.cmd`.
- [16.11] (d) P2: tabela w ADR 0276. pytest `tests/dist` 27 passed, `tools/pcperf` 27 passed; pwsh 7.4.6 parse OK.
- NASTĘPNY KROK (lider, Windows): `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 -Filter "Game.Tests.MenuOverlayLayoutTests;Game.Tests.BuildInfoTests"`
  potem `pwsh scripts/build-windows.ps1 -Slot -Regions d67-full` i zrzut menu z `Kamion-okno.cmd`.
