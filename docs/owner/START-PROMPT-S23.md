# Prompt startowy — sesja 23 (wklej do nowej sesji Claude Code w C:\Users\matma\Documents\Claude\kamion)

```
Kontynuujesz projekt Kamion (realistyczny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1 → DK65 → Knyszyn) w C:\Users\matma\Documents\Claude\kamion. Jesteś liderem i jedynym integratorem main. Repo: https://github.com/woogitsugames/kamion. Komunikacja po polsku. Godziny z zegara systemowego (Get-Date) — w s22 część wpisów HANDOVER ma +1 h.

NAJWAŻNIEJSZE ZMIANY s22 (15.11):
- D73 / ADR 0260: WINDOWS JEST PLATFORMĄ GŁÓWNĄ, telefon później; silnik zostaje Unity 6 URP (właściciel odrzucił Unreal). CLAUDE.md zasada 2 = „Build jest prawdą” (build Windows + liczby).
- D74: wymagania PC jak ETS2/ATS — min i5-6400 / GTX 660 / 8 GB → Low 1080p 30 fps; zalecane i5-9600 / GTX 1660 / 12 GB → High 1080p 60 fps (FPS = WORKING_VALUE). D72: limit APK 10 GB (drugorzędne).
- Build Windows działa (ADR 0261, scripts/build-windows.ps1; worktree win-build-0261 trzyma Library Win64 29 GB — buduj PC stamtąd, nie przełączaj main z Androida). Exe: artifacts/win/kamion-0.1.0-4ee3e02626-regions/Kamion.exe (Kamion-knyszyn.cmd).
- BŁĄD GŁÓWNY: we WSZYSTKICH regionach start jest zablokowany (z tyłu koniec drogi, z przodu zapory betonowe; raz spawn w zaporze → naczepa wyrzucona) — naprawia spawn-fix-0262 (ADR 0262). Po scaleniu: reimport regionów + rebuild Windows i APK.

PRZECZYTAJ NAJPIERW:
- HANDOVER.md: blok „SESJA 22” — wpisy chronologicznie, najnowsze tuż nad linią „Ostatni przydzielony ADR” (s22: 0273; zakresy: 0262 spawn-fix, 0263–0267 chmura H r1, 0268 znaki przejazdów, 0269–0271 chmura H r2, 0272–0273 chmura D r4);
- CLAUDE.md, docs/owner/AGENT-RULES.md, docs/owner/S20-AGENT-PREAMBLE.md, docs/owner/S20-PR-REVIEW-BRIEF.md;
- docs/11_DECYZJE_WLASCICIELA.md (D63–D74);
- artifacts/live/*.md (stan każdego agenta z NASTĘPNYM KROKIEM; kopie w main, oryginały w worktree).

ZASADY WŁAŚCICIELA:
- najwyżej 5 lokalnych agentów naraz; nowi na Fable, recenzje/krytycy na Opusie; agentom ZAWSZE każ uruchamiać długie kroki w tle i od razu kończyć turę (watchdog 10 min), obrazy oglądać po kilka; po każdym kroku commit WIP + push + live;
- nie zabijaj działających procesów; skończonych agentów nie wznawiaj bez zgody właściciela; martwych przejmuj nowymi w tym samym worktree TYLKO za zgodą (AskUserQuestion);
- crony: :07 (ZIP-y w Downloads), :17 (agenci, dysk, kolejka, HANDOVER+push), :47 (PR-y) — najpierw CronList;
- decyzje właściciela zawsze klikalne (AskUserQuestion), obrazy najpierw (SendUserFile);
- telefony (drugorzędne po D73): A16 = RFGL34SJYDZ; S24+ (RZCX60VE8ZY) bateria ≥ 40 %, przerwij < 30 %; adb pada, gdy w worktree startuje Unity — instaluj APK, gdy żaden Unity nie działa, z artifacts/locks/PHONE_RUN;
- zakazy: Google Maps/Street View/Earth/3D Tiles; marki i logo w grze; zdjęcia właściciela tylko jako referencja;
- sprzątanie worktree: najpierw robocopy artifacts do main, odpiąć junctions Data/raw ([System.IO.Directory]::Delete na każdym ReparsePoint w <wt>\Data\raw), potem git worktree remove --force; NIE usuwaj win-build-0261 (Library Win64);
- ciągły zapis: po każdym scaleniu/starcie/końcu agenta aktualizuj HANDOVER i push.

STAN NA KONIEC s22 (15.11 ok. 22:3x czasu systemowego), main ≈ a8ecc9f49+:
- SCALONE w s22: #121 recenzje s21, #126 D71, budget-fix-s21 (0221, C stretch_04 1 986 314), fix-pr80-s21 (#80 + Ełcka 6,6 m, generated dk65-02..06), tunnel-0211, audio render_all+build-lab, win-build-0261 (0261), rail-fix-s21 (0217, zastępuje #96), dk65-r4-s21 (0233, szwy K1 6,2 m — WYMAGA przebudowy knyszyn-s), #127 licencje, #128 recenzje s22. Zamknięty #82.
- LOKALNI AGENCI (sesja s22 może zostać ubita — wtedy ich procesy w tle mogą żyć dalej; agentów NIE ma po restarcie, przejęcie tylko za zgodą właściciela):
  - c-regen-s22 (worktree .claude/worktrees/c-regen-s22): jedna regeneracja C + Dojlidy z #95 far_field i #120 lato/LED; budżet OK (C bez zmian, Dojlidy mniej); import/VQA/pytest DONE; zostało: oględziny before/after, merge main, odświeżenie fidelity C, raport → scalić (zamyka #95 i #120);
  - spawn-fix-0262: test startów 21 regionów + naprawa wspólnej przyczyny + bezpiecznik OverlapBox; rendery startów w toku;
  - rail-dk65-s22: #102 rebase + P0 (jeden rail_crossing, ValueError tykocin, G-2), znaki przejazdów D71 (ADR 0268), poprawki krytyka 0217 (krawężnik przez przejazd P0, słupki biało-czerwone); generated dk65-01..04 commituje DOPIERO po scaleniu int-dk65-s22;
  - int-dk65-s22: #98 + #97 + #101 + przebudowa knyszyn-s/knyszyn/dk65-01..05 + seams.py.
  Raporty/następne kroki: artifacts/live/<nazwa>.md.
- CHMURY: D runda 4 (D11 przekrój dróg zamiejskich 0272 — asfalt 8,6 vs 6,5–7,1 m, pobocze gruntowe DW671; D12 FIX #112+#114 0273; D13 recenzje PR chmury H); H runda 2 (H6 rebase #129–#133 na main po 0261, H7 tiery PC 0269, H8 menu ustawień PC 0270, H9 dystrybucja PC 0271). Prompty: docs/owner/CLOUD-D4-PROMPT-S22.md, CLOUD-H2-PROMPT-S22.md.
- CODEX: knyszyn-rynek-0227 (Rynek, targowica z 4 wiatami naprzeciw Jagiellońskiej 50, OSM way 704368699; r5), codex-refs-s21 (PR #100, gotowe NIE).
- OTWARTE PR do scalenia wg recenzji (docs/reports/REVIEW-2026-11-15-s22-code-SUMMARY.md): SCAL #109 #110 #111 #113 #115 #116 (część mobilnych → niższy priorytet po D73), FIX #112 #114 (chmura D12), część B #117–#125 (C: #123/#124/#125 + #122 Dojlidy → kolejna wspólna przebudowa C po c-regen), #93 (rebase na osobnej gałęzi — force-push odrzucony; po c-regen), #129–#133 (chmura H po rebase), #100, #92, #85, #79.
- Test APK d67-full z s22: artifacts/apk/kamion-0.1.0-52188a91f8-dirty-regions.apk (1 821 MB) — tylko do oglądania (zablokowane starty).
- Krytyk wizualny 0217: FAIL (docs/reports/REVIEW-2026-11-15-s22-0217-visual.md) — w rękach rail-dk65-s22.

PIERWSZE KROKI:
1. CronList → załóż crony :07/:17/:47.
2. Sprawdź artifacts/live/*.md, git worktree list, statusy w tle; zbierz raporty; scal gotowe (kolejność: c-regen-s22 → spawn-fix-0262 → int-dk65-s22 → rail-dk65-s22).
3. ListAgents / zapytaj właściciela (AskUserQuestion) o przejęcie martwych worktree nowymi agentami.
4. Po spawn-fix: reimport regionów, rebuild Windows (`pwsh scripts/build-windows.ps1 ...` z worktree win-build-0261 po merge main) i daj właścicielowi exe do jazdy po Knyszynie.
5. Przejrzyj PR chmur D/H, scal SCAL, FIX odeślij.
```
