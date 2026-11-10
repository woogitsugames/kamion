# Prompt startowy dla nowej sesji (wklej jako pierwszą wiadomość)

```
Kontynuujesz projekt Kamion (realistyczny mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1) na tym samym komputerze, w katalogu C:\Users\matma\Documents\Claude\kamion. Poprzednia sesja działała na innym koncie Claude.

Najpierw przeczytaj w tej kolejności: HANDOVER.md → CLAUDE.md → docs/11_DECYZJE_WLASCICIELA.md → docs/reports/GATE-3-draft.md → docs/reports/visual/REVIEW-2026-11-10-r6.md → docs/REFERENCES.md. Przeczytaj też pamięć poprzednich sesji: C:\Users\matma\.claude\projects\C--Users-matma-Documents-Claude-kamion\memory\MEMORY.md i pliki, do których prowadzi (jeśli nie załadowała się sama).

Zasady (obowiązują cały czas):
- Działaj autonomicznie (bypass), możesz instalować potrzebne narzędzia. Jakość, nie cena: ma być realistycznie na maksa i pięknie.
- Używaj wielu agentów równolegle (do 10, każdy w swoim worktree). Modele 3D (ciężarówka, naczepa, wnętrze, auta, Blender) — Fable 5.2; grafika/shadery/świat/fizyka — Opus; średnie zadania — Sonnet; proste — Haiku. Zwięzłe raporty, zmniejszaj zrzuty przed oglądaniem.
- Ty jesteś liderem i jedynym integratorem: scalaj na main (--no-ff), regularnie push na https://github.com/woogitsugames/kamion, sprzątaj worktree i artefakty — ale ZANIM usuniesz worktree, skopiuj jego artifacts/ do głównego checkoutu.
- Decyzje dla mnie zadawaj w formie klikalnej. Pisz po polsku. Na koniec większego kroku: commit, push, krótki raport.
- Zakaz Google Street View/Maps/Earth. Referencje: Wikimedia Commons i dane GUGiK/OSM. Moje zdjęcia prasowe tylko jako wzór stylu, bez kopiowania cudzej marki.
- Telefony: zawsze -Serial, sprawdzaj blokadę ekranu i temperaturę, nigdy nie usypiaj ani nie blokuj telefonu, nigdy nie wpisuj PIN-u. S24+ (RZCX60VE8ZY) to mój telefon roboczy (połączenia i SMS): bateria nigdy poniżej 20 %, pomiary tylko przy ≥ 40 % i tylko za moją zgodą, po pomiarze zamknij grę. A16 (RFGL34SJYDZ) bez ograniczeń.

Zadania:
1. Sprawdź stan repo. Jedyna praca w toku to niezweryfikowany WIP drutów WN i zacieków pod attyką (worktree .claude/worktrees/agent-a00eb437b0f666944, kopia origin/wip/wires-streaks) — zweryfikuj renderami i dokończ albo zrób od nowa. Napraw czerwony test tests/gis/test_world_v31.py::test_frame_budget_with_forest_hlod (bez luzowania limitu).
2. Testy wszystkich zestawów na main, nowy build Low na A16 z kadrami gate3 (recenzja r6, P0), potem poprawki z listy r6 w HANDOVER.md i recenzja r7.
3. Przygotuj pomiar S24+ High z nowym buildem (ADR 0046) i zapytaj mnie o zgodę, zanim go uruchomisz.
4. Dokończ raport bramki 3 i przygotuj APK do mojego testu jazdy (docs/owner/FEEL-TEST.md).
5. Potem lista otwartych poprawek z HANDOVER.md (punkt 5).
```
