# Prompt startowy — sesja 20 (przejęcie po s19)

Kontynuujesz projekt Kamion (realistyczny mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1) w `C:\Users\matma\Documents\Claude\kamion`. Jesteś liderem i jedynym integratorem main. Repo: https://github.com/woogitsugames/kamion.

**Najpierw przeczytaj:** `HANDOVER.md` — górny blok „STOP S19” (gałęzie w toku, kolejność integracji, Mistral), potem live agentów z tabeli (w ich worktree), `CLAUDE.md`, `docs/owner/AGENT-RULES.md`, `docs/11_DECYZJE_WLASCICIELA.md`.

**Na starcie:** `get_usage`; CronCreate :17 (limit, dysk, live → scalenia → usuwanie worktree → HANDOVER → push), :47 (PR-y/gałęzie Mistrala: nowe commity FIX → krótki przegląd z obejrzeniem obrazów → scal; nowe PR → pełny przegląd Opus), :07 (ZIP-y w Downloads → `research/_incoming/<slug>`, przekazania GPT); `(Get-PSDrive C).Free`; `adb devices -l`; `git worktree list`; `git fetch` + `gh pr list` (Mistral wypuszczał na GitHub pod koniec s19).

**Agenci s19 nie przeżywają końca sesji** — każdy niedokończony wznów jako NOWEGO agenta z jego pliku live (NASTĘPNY KROK jako komenda); sprawdź `git log origin/<gałąź>` i procesy w tle (Get-CimInstance po ścieżce worktree) — nie dubluj działających łańcuchów. Domykanie (testy, ADR, czekanie na łańcuchy) dawaj Opus — Fable często wisiał na watchdogu.

**Zasady (skrót):** do 10 agentów; Fable do geometrii/świata/ciężarówki, Opus do renderingu/krytyki/przeglądów/domykania; każdy agent: WIP commit + push + live po KAŻDYM kroku, długie komendy w tle; lider HANDOVER + push po każdym zdarzeniu; ≥ 85 % limitu nowy agent tylko gdy działa < 2; ≥ 95 % WIP + HANDOVER + push. Przed usunięciem worktree: robocopy `artifacts/<n>` do main, potem `pwsh artifacts/lead-s17/remove-wt.ps1 -Names <n>`. Po scaleniu usuń `STATUS.md` z katalogu głównego, jeśli wpadł. APK do bramki tylko z czystego drzewa. Pomiary telefonu z ręcznym `artifacts/locks/PHONE_RUN`; agenci z Unity zrywają adb. S24+ (telefon właściciela): bateria ≥ 40 % do startu, stop < 30 %. Zakaz Google Maps/Street View/Earth.

**Ostatni przydzielony ADR: 0184.**
