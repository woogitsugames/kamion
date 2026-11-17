# STATUS full-build-s23 (worktree .claude/worktrees/win-build-s23 na gałęzi `build/win-s23` — NIE scalać do main; main merguj DO niej. Poprawki skryptów/parsera: gałąź `full-build-s23` (cherry-pick + push). Baza origin/main 0fd0e048a)

- [17.11 07:58] Worktree + kopia Library z pc-visual-s23 (8,1 GB, Win64 — setup 48 s, „Targeting platform: Win64”), _Generated/cc0/megascans z main, junctiony Data/raw/*. Brakujące nieśledzone art-source (wnętrze kabiny LOD0 itd., 1 GB) dokopiowane z main.
- [08:01] Parser pc_metrics: tolerancja progu frame_ms przy limicie FPS (ee1c5ee69, 53/53 testów).
- [08:15] setup (diff ProjectSettings: defaultScreen 1600x900, resizableWindow 1, QualitySettings m_CurrentQuality 1 → artifacts/full-build-s23/projectsettings-after-setup.diff), PcTiers, naczepa, WorldTruckInstaller OK.
- Kanarek: import knyszyn-s (tile/High) → potem 38 pozostałych (check-build-scenes: 39/39 bez kafli, 18 pierścienia bez scen).
- Dodatkowo (lider): menu_bg.png (D87), StartClearanceTests bialystok-industrial-c, schodkowe cienie w kabinie Win64.
- NASTĘPNY KROK: `pwsh -File artifacts/full-build-s23/chain.ps1 -StartAt 2 -Skip knyszyn-s` (stan: artifacts/full-build-s23/chain.status → CHAIN_DONE)
- [08:41] Merge origin/main (cabin-pc) do build/win-s23; setup/assety ponownie OK; import 39 regionów trwa (~2 min/region, Unity Win64). Cienie kabiny: worktree eksperymentalny .claude/worktrees/shadow-s23 (gałąź full-build-s23), odtworzone w DrivingLab -Pc High (schodki ~1 cm); test cascade4SplitX 0.067→0.02.
- NASTĘPNY KROK: czekaj na CHAIN_DONE w artifacts/full-build-s23/chain.status, potem `pwsh scripts/build-windows.ps1 -Slot -Regions d67-full`
