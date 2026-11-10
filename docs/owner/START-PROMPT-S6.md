Kontynuujesz projekt Kamion (realistyczny mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1) w C:\Users\matma\Documents\Claude\kamion. Poprzednia sesja (5) mogła zginąć na limicie; zostali agenci w toku (worktree w .claude/worktrees).

Najpierw przeczytaj: HANDOVER.md (górna sekcja „sesja 5” + tabela agentów — to jest prawda o stanie) → CLAUDE.md (w tym „Tempo i limit” i „Ciągły zapis”) → docs/owner/AGENT-RULES.md → docs/11_DECYZJE_WLASCICIELA.md (D36–D44) → artifacts/map-audit-r9/BUGS.md → docs/reports/visual/REVIEW-2026-11-10-r8.md → docs/reports/GATE-3-draft.md → pamięć C:\Users\matma\.claude\projects\C--Users-matma-Documents-Claude-kamion\memory\MEMORY.md z plikami.

Zasady (cały czas):
- Autonomicznie, wolno instalować narzędzia. Jakość, nie cena: realistycznie na maksa i pięknie.
- Agenci równolegle (do 15, każdy w swoim worktree, brief zaczyna się od przeczytania docs/owner/AGENT-RULES.md). Modele 3D (ciężarówka, naczepa, wnętrze, auta, wiadukt, obiekty charakterystyczne, Blender): Fable 5.2; grafika, shadery, świat, fizyka, feeling: Opus; średnie: Sonnet; proste: Haiku. Numery ADR z góry (ostatni przydzielony: sprawdź HANDOVER.md; w chwili pisania 0075).
- Limit: pracuj na maksa do końca okna 5-godzinnego (sprawdzaj mcp__ccd_session_mgmt__get_usage). Od 85 % nowy agent tylko gdy działa < 2; od 95 % żadnych nowych, każ agentom zapisać WIP, zaktualizuj HANDOVER.md, push.
- Ciągły zapis: po każdym scaleniu / starcie / końcu agenta / zgłoszeniu właściciela aktualizuj górę HANDOVER.md (main sha, tabela agentów: worktree, gałąź, STATUS, stan; następne kroki; licznik ADR), commit + push.
- Ty jesteś liderem i jedynym integratorem: merge --no-ff na main, push na https://github.com/woogitsugames/kamion. Przed usunięciem worktree: skopiuj artifacts/ do main, odepnij junctiony Data/raw (cmd /c rmdir), git worktree unlock, git worktree remove --force --force; sprawdź Data/raw w main. Konflikty: Data/Regions/*/generated/*.json → --ours + regeneracja; shadery, QualityProfile.cs, RenderOverrides.cs, LICENSES.md → unia.
- Decyzje dla mnie w formie klikalnej (AskUserQuestion), po polsku.
- Referencje TYLKO z otwartych źródeł (D43): Mapillary (token w C:\Users\matma\.kamion\secrets.env — nigdy nie wypisuj), KartaView, Panoramax, Commons, Openverse (CC0/BY/BY-SA), GUGiK, OSM, dane Białegostoku, CC0 Poly Haven/ambientCG. Zakaz Google Maps/Street View/Earth/3D Tiles.
- Telefony: zawsze -Serial, tylko $Adb z scripts/env.ps1, jeden agent telefonowy naraz, pomiar tylko bez Unity.exe (blokada artifacts/locks/PHONE_RUN). S24+ (RZCX60VE8ZY): bateria nigdy < 20 %, pomiar przy ≥ 40 % i < 36 °C, po pomiarze am force-stop. A16 (RFGL34SJYDZ) bez ograniczeń. Nigdy nie usypiaj/blokuj telefonu, nie wpisuj PIN-u.

Zadania (kolejność):
1. `git worktree list`, `git log --oneline -15`, STATUS.md każdego agenta z tabeli HANDOVER.md. Niedokończonych dokończ (agent per worktree, ten sam model). Scalaj: 0073 → 0075 → 0070/0071 → 0066. Sprawdź log regeneracji artifacts/logs/s5-main-regen.log.
2. Zgłoszenie właściciela: drogi „dosłownie jak w OSM” (pas ze strzałką wjeżdża w wysepkę, artifacts/owner/bugs/). Audyt: 21 błędów (4 P0: MA-010, MA-001, MA-002, MA-012). Zweryfikuj powtórzonym audytem (kamery artifacts/map-audit-r9/cameras/audit_cameras.json), że P0 = 0, a testy zgodności z OSM/ortofoto (ADR 0075) przechodzą.
3. Fab (fab.com): agent Sonnet sprawdza licencję (bez logowania/pobierania) → klikalne pytanie o rozszerzenie D40.
4. Pełna integracja na main: cc0_fetch → build_region → build_world → import-region, Truck/Trailer BuildBatch, WorldTruckInstaller.InstallBatch, pytest, EditMode (sprawdź 2 inconclusive TruckCabGlassTierTests), PlayMode, physics; czysty build Low + High (+ Ultra, właściciel ma Folda 8 Ultra — instaluje sam z pliku).
5. Telefony: A16 Low gate3 (G3-A, G3-B, kabiny × 3 pory, świat ov), A/B rq_worldgi; S24+ High wg docs/owner/S24-HIGH-RUN.md + A/B ADR 0062/0068/0072 (exteriorToeParity) — cel 60 kl./s.
6. APK do testu jazdy (docs/owner/FEEL-TEST.md); logi `adb logcat -d -s Unity | findstr CONTROLS`.
7. Recenzja r9 (visual-critic, Opus) z kadrami telefonu i montażami; klikalne decyzje: ekspozycja overcast (p10, ADR 0060), D23 biel 0,7 vs przepał dachu N-17 (ADR 0072), wynik audytu mapy.
8. Raport bramki 3 do końca (docs/reports/GATE-3-draft.md) — werdykt do mojej decyzji.
