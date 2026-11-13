# Prompt startowy — sesja 17 (przejęcie po s16)

Skopiuj całość poniżej do nowej sesji Claude Code (zakładka Code, katalog `C:\Users\matma\Documents\Claude\kamion`).

---

Kontynuujesz projekt Kamion (realistyczny mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1) w `C:\Users\matma\Documents\Claude\kamion`. Przejmujesz pracę po sesji 16, którą zakończył limit 5 h. Jesteś liderem i jedynym integratorem main. Repo: https://github.com/woogitsugames/kamion.

**Najpierw przeczytaj (w tej kolejności):**
1. `HANDOVER.md` — górny blok „KONIEC S16”.
2. `artifacts/live/{p1-0161,furn-0162,veg-0163,phys-0165,region-0166}.md` — stan 5 agentów w toku (sha, NASTĘPNY KROK jako komenda).
3. `CLAUDE.md`, `docs/owner/AGENT-RULES.md`, `docs/11_DECYZJE_WLASCICIELA.md` (**D57: bramka 3 PASS**, D58–D61).
4. `docs/reports/visual/REVIEW-2026-11-13-s16b-final.md` (27 R / 15 P / 0 N; lista P1), `docs/reports/REVIEW-2026-11-13-s16-research-pack-02.md` (przegląd ZIP-ów paczki 2, może być niepełny).

Pamięć: `C:\Users\matma\.claude\projects\C--Users-matma-Documents-Claude-kamion\memory\MEMORY.md`.

**Na starcie:**
1. `get_usage`; CronCreate: **:17** (limit, dysk + `uv run --project tools/worldgen python scripts/cleanup-artifacts.py`, live → scalenia → usunięcie worktree → HANDOVER → push), **:47** (PR-y Mistrala), **:07** (przekazania GPT / ZIP-y w Downloads). Uwaga: `resetsAt` z get_usage jest w UTC — czas lokalny = UTC+1.
2. `(Get-PSDrive C).Free`; `adb devices -l` (A16 RFGL34SJYDZ, S24+ RZCX60VE8ZY — telefon właściciela: bateria ≥ 40 % i < 36 °C, nigdy < 20 %); `git worktree list`; procesy agentów (`Get-CimInstance Win32_Process` z `worktrees\`).
3. Wznów agentów jako NOWYCH (nie SendMessage do starych) z ich plików live, maks. 10 w dzień, 3 w nocy.

**Kolejność pracy s17:**
1. Dokończ i scal: **0161** (P1 kadrów: cm*, D-1, sygnalizatory, 962702, 1259231, 482392, 494288, 339463, horyzont), **0162** (wiaty BKM czerwone, U-12a żółte, latarnie 11 m, tablice G3 2024), **0163** (zieleń ulic domów wg G7), **0165** (podatny kontakt nadwozia D58, F1 ≤ 3,5° D59), **0166** (region Dojlidy/Krywlany D60). Konflikty `generated/*` → przy scaleniu kolejnych gałęzi `--ours`, potem JEDNA regeneracja (wzór: `docs/reports/WORLD-INTEGRATION-2026-11-13-s16b.md`), import w main (`pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` — inaczej APK ma stary świat!), APK, krytyk, A16 (`pwsh scripts/gate3-run.ps1 -Serial RFGL34SJYDZ -Segment A|B -Tier Low -SkipBuild -Apk ...`).
2. **0164** scalony — przy regeneracji graf dostanie `maxaxleload` (89 krawędzi; trasy bez zmian).
3. Mistral r7: zadania `docs/owner/MISTRAL-TASKS-7.md` (M39–M43) — właściciel zleca; integracja PR-ów agentem Opus (wzór raportów r4–r6).
4. Research: paczka 2 — 7 ZIP-ów (P2, P3, P5, P6, P8, P9, P10) w przeglądzie; brak P1, P4, P7 → kolejna paczka dla innego modelu (właściciel zleca). Ustalenia przekazać 0162/0163/0166.
5. S24+ High/30 na końcowym APK (nie zrobione w s16).
6. Głos GPS: `docs/owner/ELEVENLABS-GPS-VOICE.md` — właściciel wybiera głos.

**Zasady (skrót):** do 10 agentów w dzień; ≥ 85 % limitu nowy agent tylko gdy działa < 2; ≥ 95 % WIP + HANDOVER + push. Ciągły zapis (HANDOVER + live po każdym scaleniu/starcie). Przed usunięciem worktree: unlink junctionów `Data/raw/*` (`cmd /c rmdir`). Dowody agentów zewnętrznych (Codex itp.) — NIE do gita (tylko .md/.tsv). Po każdym Unity: `git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings`. Unity zrywa adb — pomiary telefonu tylko z `artifacts/locks/PHONE_RUN`. Decyzje właściciela klikalne (AskUserQuestion), obrazy najpierw (SendUserFile ≤ 960 px). Zakaz Google Maps/Street View/Earth/3D Tiles; Fab/Megascans nigdy w gicie.

**Ostatni przydzielony ADR: 0166.**
