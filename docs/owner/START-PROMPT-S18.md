# Prompt startowy — sesja 18 (przejęcie po s17)

Kontynuujesz projekt Kamion (realistyczny mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1) w `C:\Users\matma\Documents\Claude\kamion`. Jesteś liderem i jedynym integratorem main. Repo: https://github.com/woogitsugames/kamion.

**Najpierw przeczytaj:** `HANDOVER.md` — górny blok „STOP S17” (kolejność pracy, gałęzie gotowe i w toku), potem `artifacts/live/*.md` agentów w toku, `CLAUDE.md`, `docs/owner/AGENT-RULES.md`, `docs/11_DECYZJE_WLASCICIELA.md` (do D62).

**Na starcie:** `get_usage` (resetsAt w UTC; lokalnie UTC+1); CronCreate :17 (limit, dysk, cleanup, live → scalenia → worktree → HANDOVER → push), :47 (PR-y Mistrala: FIX → krótki ponowny przegląd z obejrzeniem obrazów → scal; nowe → pełny przegląd), :07 (ZIP-y w Downloads, przekazania GPT); `(Get-PSDrive C).Free`; `adb devices -l`; `git worktree list`.

**Zasady (skrót):** do 10 agentów w dzień, Fable do geometrii (właściciel: nie oszczędzać; przy końcu limitu przełącza konto); każdy agent zapisuje WIP + push gałęzi + live po KAŻDYM kroku; lider HANDOVER po każdym zdarzeniu; ≥ 85 % limitu nowy agent tylko gdy działa < 2; ≥ 95 % WIP + HANDOVER + push. Przed usunięciem worktree odłącz WSZYSTKIE junctiony pod `<wt>/Data` (także całe `Data/raw`). APK do bramki tylko z czystego drzewa. Pomiary telefonu z ręcznym `artifacts/locks/PHONE_RUN`. Zakaz Google Maps/Street View/Earth.

**Ostatni przydzielony ADR: 0179.**
