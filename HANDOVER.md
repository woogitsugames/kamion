# HANDOVER — kamion (TRUCK SIM PL), stan 2026-11-09 wieczór

Dla nowej sesji Claude Code na tym samym komputerze (`C:\Users\matma\Documents\Claude\kamion`). Przeczytaj w kolejności: ten plik → `CLAUDE.md` → `docs/STATUS.md` → `docs/11_DECYZJE_WLASCICIELA.md` → `docs/reports/visual/REVIEW-2026-11-09-r2.md`.

## Polecenia właściciela (stałe)
- Pracuj autonomicznie (tryb bypass). Do 10 agentów naraz: **Opus** do ciężkiej pracy i **całej grafiki/modeli** (ma być pięknie i realistycznie), **Sonnet** do średnich zadań, **Haiku** do prostych.
- Regularnie push na https://github.com/woogitsugames/kamion (publiczne — darmowe Actions) i scalaj na `main`. Regularnie sprzątaj lokalne worktree/artefakty.
- Decyzje dla właściciela zadawaj **w formie klikalnej** (AskUserQuestion). Komunikacja po polsku.
- **Zakaz Google Street View / Maps / Earth** (ADR 0002) — także jako podgląd. Referencje: Wikimedia Commons (licencje w `docs/REFERENCES.md`), obrazy AI właściciela tylko jako nastrój.

## Decyzje właściciela (szczegóły: docs/11)
Obszar startowy **C** (Kwadrat Park → Andersa → Rondo Putry → DK8/DK19) · ciężarówka **koncepcja B, marka TRAKT** · wnętrze **koniak**, zegary tylko ekran 12,3" · repo publiczne · audio OK · wygląd **„jak zdjęcie z telefonu”** (D23) · build Unity w CI później.

## Gdzie jesteśmy
- **Etap 0**: zamknięty (tag `v0.0-gate0`). **Etap 1–2** (fizyka ciągnika + naczepa 40 t, pneumatyka, ABS, retarder, sprzęganie, DrivingLab, audio silnika): działa w edytorze i na telefonach; brak oceny „feelingu” przez właściciela (`docs/reports/GATE-1-draft.md`, `GATE-2-draft.md`).
- **Świat C**: generator (Python, `tools/worldgen`) → GLB → Unity (glTFast, scena `WorldC`/`WorldC_High`). v2 w grze; v3 w toku (patrz niżej).
- **Ciężarówka TRAKT**: zewnętrze A4 r3 + wnętrze A6 r3 (koniak) w Blenderze, scalone; **jeszcze nie w Unity** (w grze wciąż graybox).
- **Telefony** (USB, stale): A16 `RFGL34SJYDZ` (Low, słaby), S24+ `RZCX60VE8ZY` (High). Skrypty wymagają `-Serial`. A16 bywa zablokowany PIN-em — sprawdzaj `isKeyguardShowing`. Pomiary: `docs/reports/device/DEVICE-RUN-2026-11-09.md` (30 FPS wszędzie; las DK8 na A16 Medium 17 FPS; APK Low ~122 MB, cel świata ≤ 60 MB).
- Recenzja wizualna r2: wszystkie obszary FAIL (wnętrze ~7/10, zewnętrze ~5/10, świat ~5/10). Bramka wymaga klatek z URP/telefonu.

## Prace przerwane końcem sesji (do dokończenia)
| Zadanie | Gdzie | Co zrobić |
|---|---|---|
| Świat v3 (fasady, auta/naczepy na placach, asfalt, brama Kwadrat Parku, drzewa, wiadukty wg zdjęć CC0) | worktree `.claude/worktrees/agent-a8cc4186e1bfe4593`, gałąź `worktree-agent-a8cc4186e1bfe4593` (kopia: `origin/wip/agent-a8cc4186e1bfe4593`) | przejrzyj, dokończ wg brief w REVIEW r2 (#4,#5,#9,#10,#12) + zdjęcia `Data/photos/nowe`, scal na main |
| TRAKT zewnętrze A6 (części do rigu, LOD, atlasy, wspólna szyba `glass_interface.json`, manifest) | worktree `.claude/worktrees/agent-a20dfdd09953c707e`, gałąź `worktree-agent-a20dfdd09953c707e` (kopia: `origin/wip/agent-a20dfdd09953c707e`) | dokończ, potem wnętrze dopasuj do `glass_interface.json`, scal |
| Wygląd D23 + wydajność A16 (kolizje liczone w runtime, auto-Low na A16, profil GPU lasu DK8, szarpnięcie 40 t na s≈604 m) | **bezpośrednio na `main`** (ostatni commit `2e34e6d`; niezacommitowane: `game/ProjectSettings/QualitySettings.asset`) | sprawdź diff, dokończ zadania 2–6 z tego briefu, pomiary na obu telefonach |

## Następne kroki (kolejność)
1. Dokończ trzy prace powyżej i scal.
2. **A7**: import TRAKT (zewnętrze + wnętrze) do Unity zamiast grayboxa; oświetlenie kabiny przy niskim słońcu (REVIEW r2 #6); klatki z A16/S24+.
3. Recenzja wizualna r3 (agent `visual-critic`, Opus) z porównaniem do zdjęć CC0 z `Data/photos/nowe`.
4. Bramka Etapu 3 (próbka jakości 300–500 m: brama Kwadrat Parku → Rondo Putry) + test „feelingu” właściciela na telefonie.

## Narzędzia (zainstalowane)
Unity 6000.3.28f1 (licencja: `scripts/env.ps1` kopiuje ją z magazynu MSIX Unity Hub), Unity CLI (winget `Unity.CLI`; `unity pipeline install` jeszcze nie uruchomione w projekcie), plugin Unity (skille `unity:*`), Context7 MCP (`.mcp.json`), Blender 4.2.9 + Blender MCP, .NET SDK 10 user-local (`%LOCALAPPDATA%\Microsoft\dotnet`), uv/Python, ImageMagick, scrcpy, adb. CI: `.github/workflows/ci.yml` (fizyka + GIS) zielone. Research narzędzi: `docs/TOOLING_RESEARCH.md`.

## Sprawy otwarte u właściciela
- Usunąć ręcznie `C:\docs` (agenci zapisali tam pliki przez względną ścieżkę; blokada bezpieczeństwa).
- Zdjęcia bramy/ramp Kwadrat Parku i Andersa — właściciel nie zrobi; używamy Commons + danych GUGiK (ortofoto).
- Wyłączenie blokady ekranu na A16 (ułatwia pomiary bez właściciela).
- Test jazdy na telefonie (checklisty w GATE-1/2-draft).

## Pamięć sesji
`C:\Users\matma\.claude\projects\C--Users-matma-Documents-Claude-kamion\memory\` (MEMORY.md + pliki) — ładowana automatycznie.
