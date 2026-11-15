# Prompt startowy sesji 22 (lider lokalny)

Wklej:
```
Kontynuujesz projekt Kamion (mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1 → DK65 → Knyszyn) w C:\Users\matma\Documents\Claude\kamion. Jesteś liderem i jedynym integratorem main. Repo: https://github.com/woogitsugames/kamion. Komunikacja po polsku. Godziny podawaj z zegara systemowego (= czas Brukseli; w s20/s21 część wpisów była przesunięta o +1–2 h).

PRZECZYTAJ NAJPIERW:
- HANDOVER.md: bloki „SESJA 20” i „SESJA 21” — wpisy chronologicznie, najnowsze tuż nad linią „Ostatni przydzielony ADR”;
- CLAUDE.md, docs/owner/AGENT-RULES.md, docs/owner/S20-AGENT-PREAMBLE.md, docs/owner/S20-PR-REVIEW-BRIEF.md;
- docs/11_DECYZJE_WLASCICIELA.md (D63–D70);
- docs/owner/KNYSZYN-OWNER-FEEDBACK-S21.md (zdjęcia właściciela z Knyszyna; pliki lokalnie w Data/raw/refs/owner-knyszyn-2026-11-15/, poza gitem);
- artifacts/live/*.md (stan każdego agenta z NASTĘPNYM KROKIEM).

ZASADY WŁAŚCICIELA:
- najwyżej 5 lokalnych agentów naraz; nowi na Fable, recenzje na Opusie; agentom ZAWSZE każ uruchamiać długie kroki w tle i od razu kończyć turę (watchdog 10 min);
- nie zabijaj działających; skończonych nie wznawiaj bez zgody właściciela; martwych agentów przejmuj nowymi w tym samym worktree TYLKO za zgodą;
- crony: :07 (ZIP-y w Downloads), :17 (agenci, dysk, kolejka, HANDOVER+push), :47 (PR-y) — najpierw CronList;
- decyzje właściciela zawsze klikalne (AskUserQuestion), obrazy najpierw (SendUserFile);
- telefony: A16 = RFGL34SJYDZ; S24+ (RZCX60VE8ZY) bateria ≥ 40 % na start, przerwij < 30 %; nie uruchamiaj Unity w batchu podczas pomiaru na telefonie (zabija adb);
- zakazy: Google Maps/Street View/Earth/3D Tiles; marki i logo w grze; zdjęcia właściciela tylko jako referencja (nie do gita, nie tekstury);
- ciągły zapis: po każdym scaleniu/starcie/końcu agenta aktualizuj górę HANDOVER i push.

STAN NA KONIEC s21 (15.11 ok. 19:1x):
- main ma scalone w s21: #90 naciski 0201b, 0216 lato + białe LED Knyszyn, research #62/#64/#65/#66/#99 + recenzje #105, #103 licencje 0230, #104 wybór regionu w buildzie 0229, #108 stan bramek, #107 audio 0232 (właściciel wybrał B; trzeba render_all.py → build-lab.ps1 przed APK).
- Lokalni agenci s21 (gałęzie i live w artifacts/live/): budget-fix-s21 (0221, budżet tris High C stretch_04 2,02 M → < 2 M; BLOKUJE APK i bramkę), tunnel-0211 (r5), verify-cloud-c (FIX #80 Ełcka 6,6 m + jeden mechanizm placu budowy dk65-05/06 na gałęzi fix-pr80-s21; #82), rail-fix-s21 (#96 FIX 2–5 + importer z fix-pr95-96-s21), dk65-r4-s21 (przebudowa dk65-06…11 r4 + szew 10/11↔knyszyn-s). Jeśli nie żyją — zapytaj właściciela o przejęcie.
- Inne sesje właściciela (raportują PR-ami / plikami live): Codex knyszyn-rynek-0227 (Rynek wg zdjęć; park zamiast lasu sosnowego), Codex codex-refs-s21 (referencje, PR #100), Antigravity (sprzątanie C:, raport docs/reports/CLEANUP-2026-11-15-s21.md), chmura D runda 2 (F1–F10, ADR 0234–0242), chmura E (0228 jackknife, 0231 pierścień — jeszcze nieoddane), chmura G (0243–0246 + lato C/D), chmura recenzji kodu (raporty REVIEW-2026-11-15-s21-code-*, gałąź reviews-code-s21).
- Otwarte PR do weryfikacji lokalnej (build świata + VQA, potem scalenie wg raportów recenzji z chmury): #98 → #106 (szwy) → #80 (fix-pr80-s21), #95 (razem z regeneracją far_field C), #96 + #102 (tory), #101 szpalery, #97 rondo Knyszyn, #93 + #82 Putry, #109 płoty Low, #110 cienie Low, #79 światła (rendery), #92 M59-FIX (FIX), #85.
- D67: następny APK z korytarzem (≤ 2 GB) — buduj z `-Regions` (#104) po scaleniu budget-fix; potem gate3 A16 + zrzuty Argona 0187/0188/0189 + knyszyn Low dusk/night. D68: lato także w C i Dojlidach (dane z chmury G5), regeneracja C+D razem z budżetem.

PIERWSZE KROKI:
1. CronList → załóż crony :07/:17/:47.
2. Sprawdź artifacts/live/*.md i gałęzie; zbierz raporty skończonych agentów; scal gotowe (budget-fix-s21 najpierw).
3. ListAgents / zapytaj właściciela o przejęcia martwych worktree.
4. Przejrzyj nowe PR (chmury D/E/G, recenzje kodu), scal SCAL, FIX odeślij.
5. Kolejność integracji: budget-fix C → regeneracja C (+far_field #95, + lato C/D) → EditMode → render_all audio + build-lab → APK z korytarzem → A16.
Ostatni przydzielony ADR: sprawdź linię w HANDOVER (na koniec s21: 0246).
```
