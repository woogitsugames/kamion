# Prompt startowy — sesja 19 (przejęcie po s18)

Kontynuujesz projekt Kamion (realistyczny mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1) w `C:\Users\matma\Documents\Claude\kamion`. Jesteś liderem i jedynym integratorem main. Repo: https://github.com/woogitsugames/kamion.

**Najpierw przeczytaj:** `HANDOVER.md` — górny blok „STOP S18” (gałęzie gotowe / w toku, kolejność integracji), potem `artifacts/live/*.md` agentów z tabeli, `CLAUDE.md`, `docs/owner/AGENT-RULES.md`, `docs/11_DECYZJE_WLASCICIELA.md`.

**Na starcie:** `get_usage` (resetsAt w UTC; lokalnie UTC+1); CronCreate :17 (limit, dysk, cleanup, live → scalenia → worktree → HANDOVER → push), :47 (PR-y Mistrala: „…-FIX gotowe” → krótki ponowny przegląd z obejrzeniem obrazów → scal; nowe → pełny przegląd Opus), :07 (ZIP-y w Downloads → `research/_incoming/<slug>`, przekazania GPT); `(Get-PSDrive C).Free`; `adb devices -l`; `git worktree list`.

**Agenci s18 nie przeżywają końca sesji** — każdy niedokończony wznów jako NOWEGO agenta z jego pliku live (tam jest NASTĘPNY KROK jako komenda). Sprawdź `git log origin/<gałąź>` — agent mógł pracować dalej niż live.

**Zasady (skrót):** do 10 agentów; Fable do geometrii/świata/ciężarówki (właściciel: nie oszczędzać), Opus do renderingu/wydajności/krytyki/przeglądów; każdy agent: WIP commit + push gałęzi + live po KAŻDYM kroku, długie komendy w tle (zawieszenia watchdog API 600 s są częste); lider HANDOVER + push po każdym zdarzeniu; ≥ 85 % limitu nowy agent tylko gdy działa < 2; ≥ 95 % WIP + HANDOVER + push. Przed usunięciem worktree: `pwsh artifacts/lead-s17/remove-wt.ps1 -Names <n>` (odłącza junctiony pod Data; najpierw robocopy `artifacts/<n>` do main). Po scaleniu usuń `STATUS.md` z katalogu głównego, jeśli wpadł. APK do bramki tylko z czystego drzewa. Pomiary telefonu z ręcznym `artifacts/locks/PHONE_RUN`; agenci z Unity zrywają adb. Zakaz Google Maps/Street View/Earth.

**Ostatni przydzielony ADR: 0182.**
