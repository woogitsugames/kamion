# audio-lufs-s24 — STATUS (D92: kabina −18 LUFS)

Worktree `.claude/worktrees/audio-lufs-s24`, gałąź `audio-lufs-s24`. ADR 0311 (do potwierdzenia przez lidera).

## Kroki
- [x] Worktree + Library; build „przed” (main 83226d958, `-noWorld`, kod gry = main) → `artifacts/win/before-83226d958/` (lokalnie, poza gitem)
- [x] `tools/audio/lufs_calibrate.py` + test, `tools/audio/lufs_runs.ps1` (przebiegi DrivingLab straight050 / circle50, EL + synth)
- [ ] Pomiar „przed”
- [ ] Kod: `Game.Core.CabinLoudness` + `Game.Gameplay.CabinBusFilter` (gain szyny słuchacza w kabinie), kalibracja
- [ ] Build „po” + pomiar „po”, testy EditMode, ADR 0311, raport

## Następny krok
```
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner audio-lufs-s24
pwsh tools/audio/lufs_runs.ps1 -Exe artifacts/win/before-83226d958/Kamion.exe -OutDir artifacts/audio-lufs-s24/before -Label before
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner audio-lufs-s24
```
