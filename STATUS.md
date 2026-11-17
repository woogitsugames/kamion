# STATUS full-build-s23 (worktree .claude/worktrees/win-build-s23 na gałęzi `build/win-s23` — NIE scalać do main; main merguj DO niej. Poprawki skryptów/parsera: gałąź `full-build-s23` (cherry-pick + push). Baza origin/main 0fd0e048a)

- [17.11 07:58] Worktree + kopia Library z pc-visual-s23 (8,1 GB, Win64 — setup 48 s, „Targeting platform: Win64”), _Generated/cc0/megascans z main, junctiony Data/raw/*. Brakujące nieśledzone art-source (wnętrze kabiny LOD0 itd., 1 GB) dokopiowane z main.
- [08:01] Parser pc_metrics: tolerancja progu frame_ms przy limicie FPS (ee1c5ee69, 53/53 testów).
- [08:15] setup (diff ProjectSettings: defaultScreen 1600x900, resizableWindow 1, QualitySettings m_CurrentQuality 1 → artifacts/full-build-s23/projectsettings-after-setup.diff), PcTiers, naczepa, WorldTruckInstaller OK.
- Kanarek: import knyszyn-s (tile/High) → potem 38 pozostałych (check-build-scenes: 39/39 bez kafli, 18 pierścienia bez scen).
- Dodatkowo (lider): menu_bg.png (D87), StartClearanceTests bialystok-industrial-c, schodkowe cienie w kabinie Win64.
- NASTĘPNY KROK: `pwsh -File artifacts/full-build-s23/chain.ps1 -StartAt 2 -Skip knyszyn-s` (stan: artifacts/full-build-s23/chain.status → CHAIN_DONE)

- [09:50] P1-1 schodkowe czarne bloki w kabinie Win64: PRZYCZYNA = atlas AO kabiny w automatycznym formacie Standalone BC1 (Android ma ASTC), shader mapuje AO przez smoothstep(0.04,0.28) → bloki 4x4. Poprawka: TruckAssetBuilder override Standalone BC4 dla *_AO* + PC High/Ultra pierwsza kaskada 3 m (krawędź twardego cienia słońca). EditMode 20/20 (filtr TruckTextureStandaloneFormat|PcTier). Dowód: artifacts/full-build-s23/shadow/cab-dash-crops-base-bc4-bc4casc.jpg (edytor DrivingLab -Pc High clear). Commit 89505bd00.
- NASTĘPNY KROK: build w win-build-s23 (post.ps1 → POST_DONE), potem zrzut kabiny z playera przed (exe e28533ca31) / po.
