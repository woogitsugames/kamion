# Zlecenie dla sesji Claude Code w CHMURZE „D” — runda 3 (s22, 15.11 wieczór)

Wklej:
```
Repo GitHub woogitsugames/kamion (Kamion: mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1). Jesteś w chmurze: NIE masz Unity, telefonów ani Data/raw. Masz do 5 agentów (możesz używać Fable); każdy robi jedno zadanie. Subagenci nie tworzą subagentów. Lider (sesja lokalna) jest jedynym integratorem main: zbuduje świat, wyrenderuje, zmierzy i scali. Ty NIE scalasz.

NAJPIERW przeczytaj: CLAUDE.md, docs/owner/AGENT-RULES.md, docs/owner/S20-PR-REVIEW-BRIEF.md, HANDOVER.md (wpisy „SESJA 22” tuż nad linią „Ostatni przydzielony ADR”), docs/11_DECYZJE_WLASCICIELA.md (D63–D70), docs/owner/KNYSZYN-OWNER-FEEDBACK-S21.md, docs/reports/REVIEW-2026-11-15-s21-code-SUMMARY.md i raporty REVIEW-2026-11-15-s21-code-<nr>.md.

Uruchamiasz tylko czysty Python: `uv run --project tools/worldgen python -m pytest tests/gis -k <wybrane>`. Testy wymagające Data/raw pomiń i wypisz. Wszystko, co wymaga build_world, Unity albo renderu, wpisz jako DOKŁADNĄ komendę dla lidera. Nie regeneruj generated/* (lider zrobi jedną przebudowę).

NIE dotykaj (lokalni agenci w toku): budżetu i generatora dróg C / stretch_04 (budget-fix-s21, ADR 0221), tunelu (0211), kafli dk65-06…11 i knyszyn-s (dk65-r4-s21, 0233), dk65-02…05 i Ełckiej (fix-pr80-s21), torowiska i przejazdów (rail-fix-s21 wchodzi zamiast #96; #102 dostanie rebase później). Nowe ADR, jeśli potrzebne: od 0247.

D6 FIX #98 (gałąź dk65-k1-0220, push na nią): wg REVIEW-…-code-98: `markings.py:276-279` — kreska przedłuża się do końca łańcucha przy dziurze; ADR 0220 nadal mówi 6,9 m → 6,6 m wg D66. Test regresji na danych syntetycznych. Komentarz w PR.
D7 FIX #93 + #97 (gałęzie putry-ring-0198b i roundabout-0218): wg REVIEW-…-code-93 i -97: usuń STATUS.md i raport z gałęzi #93; `apron_width` (#93) i `truck_apron` (#97) zapisują to samo pole — jeden mechanizm, opisz kolejność scalania; w #97 materiał opaski ronda Knyszyn ma być jasną kostką/betonem (zdjęcia właściciela opisane w KNYSZYN-OWNER-FEEDBACK-S21.md), nie brązowy. Rebase #93 na origin/main. Komentarze w obu PR.
D8 FIX #101 (gałąź treerows-0222): P2 `tree_rows.py:372` — częściowo przejęta linia BDOT zostaje bez drzew; napraw + test. Komentarz w PR.
D9 Recenzje kodu nowych PR (bez kodu; raporty docs/reports/REVIEW-2026-11-15-s22-code-<nr>.md + SUMMARY na gałęzi reviews-code-s22, PR z samymi raportami): #109, #110, #111, #112, #113, #114, #115, #116, #117, #118, #119, #120, #122, #123, #124, #125 — wg S20-PR-REVIEW-BRIEF: poprawność, testy, budżet (draws/tris), konflikty między PR (szczególnie #120/#123/#124/#125 — wszystkie zmieniają region C; #112/#114 — paczki i streaming), werdykt SCAL / FIX / ZAMKNIJ, kolejność scalania. Werdykt także jako `gh pr comment`. Podziel PR między 2 agentów.
D10 Audyt licencji (gałąź licenses-cloud2-s22): wg REVIEW-…-code-103 P1 — 142 pliki `research/cloud2/*` bez wpisu w docs/LICENSES.md, audyt czerwony. Uzupełnij wpisy (źródło, licencja, autor; bez zgadywania — nieznane = `UNVERIFIED` + lista do usunięcia), uruchom audyt licencji, PR.

ZASADY: commit i push po każdym kroku; nie zmyślaj liczb (źródło, ESTIMATED albo WORKING_VALUE); bez ProjectSettings/, Packages/, asmdef i wspólnych scen; bez Google Maps, Street View, Earth i 3D Tiles; bez marek i logo; nagłówki HTTP bez nazwy projektu. Na koniec każdego zadania PR (nie draft) albo push na istniejący PR + raport do 20 linii po polsku: co zmienione; testy uruchomione i wynik; testy NIEuruchomione; DOKŁADNE komendy dla lidera; co otwarte; „Gotowe do scalenia po weryfikacji lidera: TAK/NIE”. NIE scalaj. Na końcu podsumowanie z numerami PR.
```
