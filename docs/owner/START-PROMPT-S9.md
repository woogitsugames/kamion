Kontynuujesz projekt Kamion (realistyczny mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1) w C:\Users\matma\Documents\Claude\kamion. Przejmujesz pracę po sesji 8 (lider s8 nie wznawia agentów po ich zakończeniu — Ty przejmujesz).

Najpierw przeczytaj: HANDOVER.md (górna sekcja „sesja 8” + tabela agentów — to jest prawda o stanie) → CLAUDE.md → docs/owner/AGENT-RULES.md → docs/11_DECYZJE_WLASCICIELA.md (D36–D47) → docs/reports/visual/REVIEW-2026-11-10-0070-0083.md i REVIEW-2026-11-10-0071-0080.md → pamięć C:\Users\matma\.claude\projects\C--Users-matma-Documents-Claude-kamion\memory\MEMORY.md z plikami.

Zasady sesji 9 (polecenie właściciela, 2026-11-10):
- **Maksymalnie 3 agentów naraz** (Fable 5.2), każdy w swoim worktree; brief zaczyna się od docs/owner/AGENT-RULES.md i STATUS.md. Nowe worktree: Data/raw/derived i cc0 jako KOPIA (robocopy), gugik/osm/refs/mapillary mogą być junctionami (tylko odczyt).
- **Na starcie ustaw zewnętrzny trigger co godzinę** (zadanie zaplanowane / RemoteTrigger / cron — co jest dostępne), który wybudza tę sesję do pracy: sprawdź stan agentów (git, STATUS.md), scal gotowe, uruchom kolejne zadania z listy w HANDOVER, zaktualizuj HANDOVER, push. Gdy limit 5 h się odnowi — pracuj dalej.
- Limit: od 85 % nowy agent tylko gdy działa < 2; od 95 % żadnych nowych, agenci zapisują WIP, HANDOVER.md, push.
- Ciągły zapis: po każdym scaleniu / starcie / końcu agenta / decyzji właściciela aktualizuj górę HANDOVER.md, commit + push na https://github.com/woogitsugames/kamion. Lider = jedyny integrator (merge --no-ff na main).
- Przed usunięciem worktree: skopiuj artifacts/ do main, odepnij junctiony (cmd /c rmdir), git worktree unlock, git worktree remove --force --force. Konflikty: Data/Regions/*/generated/*.json → --ours + regeneracja; STATUS.md w korzeniu → --ours; shadery/QualityProfile/LICENSES.md → unia. Nie commituj __pycache__.
- Decyzje dla właściciela klikalne (AskUserQuestion), po polsku. Zakaz Google Maps/Street View/Earth/3D Tiles. Fab/Megascans nigdy do gita (D45).
- Telefony: zawsze -Serial, jeden agent telefonowy naraz, pomiar tylko bez Unity.exe (artifacts/locks/PHONE_RUN). S24+ (RZCX60VE8ZY): bateria nigdy < 20 %, pomiar przy ≥ 40 % i < 36 °C, potem am force-stop. A16 (RFGL34SJYDZ) bez ograniczeń. Nigdy nie usypiaj/blokuj telefonu, nie wpisuj PIN-u.
- Inni wykonawcy na tej maszynie: GPT/Codex (Megascans, ADR 0084, gałąź gpt-megascans, artifacts/megascans-r1/REPORT.md) i Antigravity Argon 4 (tło za krawędzią, ADR 0085, docs/owner/ARGON-TASK-01-WORLD-EDGE.md, gałąź argon-edge) — nie ruszaj ich worktree, scal po ich REPORT.md.

Zadania: wg „Następne kroki” w HANDOVER.md (kolejność scaleń, integracja, telefony, raport bramki 3).
