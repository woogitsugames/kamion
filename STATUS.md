# STATUS — crash-diag-s23 (crash D3D12 887a0001 + crash przy zamykaniu, 16.11)
- Krok 1 (dowody): 4 crashe 16.11 w `%LOCALAPPDATA%\Temp\woogitsugames\Kamion\Crashes`. Symbolizacja RVA z PDB Unity 6000.3.28f1 (llvm-symbolizer z NDK):
  - 15:25 D3D12, tryb **exclusive** 3440x1440, Ultra, cap 144: `D3D12SwapChain::Present` -> `CheckDeviceStatus` (887a0001), VRAM 1,4/11,7 GB (nie OOM); brak TDR w dzienniku System.
  - 08:25 / 15:30 / 17:24 (D3D12 i **D3D11**): przy zamykaniu, ten sam RVA 0xA567E2 = `win::NewInput::Activate(bool)` po zamknięciu Input System -> niezależny od API.
- NASTĘPNY KROK: odtworzenie (exe int-stream a920cfb35b): `pwsh scripts/crash-repro.ps1` (do napisania) — macierz D3D12/D3D11 × borderless/exclusive × wyjście.
