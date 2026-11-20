# audio-lufs-s24 — STATUS (D92: kabina −18 LUFS) — DONE, czeka na scalenie i odsłuch

Worktree `.claude/worktrees/audio-lufs-s24`, gałąź `audio-lufs-s24`. **ADR 0313** (0311 zajęty na main ×2, 0312 = drive-feel-s24).

## Wynik (player Windows, DrivingLab 40 t, kabina, program straight050 + circle50)
- Przed (main 83226d958): EL −25,1 LUFS, synteza −24,2 / −22,8 / −23,4 (rozrzut przebiegów do 1,2 LU), TP ≤ −8,3
- Po (7eadff67d, EL +7,1 dB, synteza +4,8 dB): **EL −17,9, synteza −18,3 LUFS**, TP ≤ −2,9 dBTP
- Kontrole: straight080 kabina −20,8 → −13,7, TP −1,5 (limiter min −0,9 dB); zewnątrz (chase) −28,5 → −28,2 (bez zmian)
- EditMode 1475: 1 fail niezwiązany (RegionSelectTests, katalog regionów); 13 nowych zielone; pytest 5/5

## Następny krok (lider)
```
git -C C:\Users\matma\Documents\Claude\kamion merge --no-ff audio-lufs-s24
pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64
```
Odsłuch właściciela: `artifacts/audio-lufs-s24/final/f1-*/capture.wav` (main).
