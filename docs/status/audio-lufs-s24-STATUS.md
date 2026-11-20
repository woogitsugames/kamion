# audio-lufs-s24 — STATUS (D92: kabina −18 LUFS)

Worktree `.claude/worktrees/audio-lufs-s24`, gałąź `audio-lufs-s24`. ADR 0312 (0311 zajęty przez embankment-cli).

## Kroki
- [x] Build „przed” (main 83226d958, `-noWorld`, Truck z win-build) → `artifacts/win/before-83226d958/`
- [x] Pomiar przed (DrivingLab 40 t, kabina): EL straight050 −23,1 / circle50 −26,3 / razem −25,1 LUFS, TP −9,5; synth −22,8 / −24,7 / −24,2, TP −8,3
- [x] Kod: `Game.Core.CabinLoudness` (EL +7,1 dB, synth +6,2 dB), `Game.Core.BusLimiter` (look-ahead, −1,5 dBFS), `Game.Gameplay.CabinBusFilter`; przechwyt po gainie
- [x] Build „po” f8176c049 + pomiar: EL razem −17,9 LUFS, TP −3,0 (OK); synth razem −16,5 (poza ±1 — sprawdzam powtarzalność, A/B `-audio_cab_gain_db 0`)
- [x] EditMode: 1475, 1 fail (RegionSelectTests — katalog regionów, niezwiązany z audio); nowe 13 testów zielone
- [ ] Powtarzalność synth, ewentualna korekta, straight80 (TP/limiter), chase (zewnątrz bez zmian), ADR 0312, raport

## Następny krok
```
pwsh tools/audio/lufs_runs.ps1 -Exe artifacts/win/after-f8176c049/Kamion.exe -OutDir artifacts/audio-lufs-s24/ab -Label g0 -Sets synth -Scenarios circle,straight -GainDb 0
```
