# Zlecenia dla dwóch sesji Claude Code (do 5 agentów Opus/Fable każda), s20, 15.11

Przejmują pracę, której inne modele nie oddały. Stan sprawdzony 15.11 ok. 10:00:
- **Argon:** brak raportów `ARGON-S20-*`. Gałęzie stoją od 14.11 wieczorem: 0194, 0188, 0187, 0189 nieskończone, 0193 skończona (KONIEC), 0186 po poprawkach B-r4.
- **Sesja kodu:** 0197 (światła) i 0198 (podpory Putry) nie istnieją, brak gałęzi.
- **GPT Chrome:** G3 ma 3 wiersze z wymaganych ~24, M67, M69 i M64 nie zaczęte.
- **Mistral:** M63 na etapie pośrednim od 13.11. Poprawki M57, M59, M60 i M61 nieoddane (PR #55–#58 bez zmian).
- **Chmura #2:** R2, R4, R6 i R9 to szkice (PR #62, #64, #65, #66).

**Właściciel:** zatrzymaj Argona i GPT, jeśli jeszcze pracują nad tymi zadaniami. Inaczej dwie strony będą pisać na tę samą gałąź.

---

## SESJA 1: LOKALNA (ta sama maszyna: Unity, uv, Blender). Wklej:
```
Pracujesz nad projektem Kamion (mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1). Repo: C:\Users\matma\Documents\Claude\kamion (GitHub woogitsugames/kamion). Lider (inna sesja Claude) jest jedynym integratorem main. Ty NIE scalasz do main. Masz do 5 agentów (Fable do geometrii i modelowania, Opus do renderingu i świateł). Każdy agent robi jedno zadanie w swoim worktree i na swojej gałęzi. Subagenci nie tworzą subagentów.

NAJPIERW przeczytaj: CLAUDE.md, docs/owner/AGENT-RULES.md, docs/owner/S20-AGENT-PREAMBLE.md (worktree, sloty Unity/heavy, PHONE_RUN, ciągły zapis, raport), docs/06, HANDOVER.md (blok „SESJA 20”). Dla zadań B1–B4 także docs/owner/ARGON-PROMPT-S20.md i docs/reports/ARGON-INPUT-S20.md (pierwotne treści zadań).

Zadania B1–B4 to przejęcie nieskończonych gałęzi. Worktree już istnieją w .claude/worktrees/<gałąź>. Pracuj W NICH: najpierw `git pull`, potem `git merge origin/main`, potem przeczytaj artifacts/live/<gałąź>.md (tam jest „NASTĘPNY KROK”).
B1 stains-0194 (ADR 0194, plamy/pasy na płytach skrzyżowań): live mówi, że trzeba przebudować światy D (bialystok-dojlidy) i C (bialystok-industrial-c) w slocie heavy, sprawdzić GLB, ponownie zaimportować Low i High i wyrenderować after3, potem obejrzeć view3 i sbs3. Sprawdź, czy zebra na poboczach (route-s0457, s0761, photo-P11-056) i zygzaki kolein (route-s1370, g3-a-2818555625124739) zniknęły.
B2 ddr-0188 (ADR 0188, czerwone drogi rowerowe M65 i przejazdy P-11): build r4 D i C, import, render Low i High, obejrzenie sbs-r4.
B3 forest-0187 (ADR 0187, ściana lasu Krywlany M68): ostatni stan to „rebake r2 tree library”. Dokończ pętlę wizualną. Raport recenzji: docs/reports/REVIEW-2026-11-14-s20-cloud-m68.md.
B4 hospgate-0189 (ADR 0189, brama i mur szpitala P11-129): `pwsh artifacts/hospgate-0189/regen.ps1 -Tag r2`, potem sbs i poprawki według M62 (docs/reports/REVIEW-2026-11-14-s20-mistral-m62-fix.md).
B5 i B6 to nowe zadania. Pełna treść jest w docs/owner/CODE-SESSION-PROMPT-S20.md (ZADANIE A i ZADANIE B):
B5 lights-0197: światła R148, STOP:pozycyjne ≥ 5:1 po limiterze, bursztyn, tablica ≥ 2,5 cd/m².
B6 piers-0198: podpory estakady A ronda Putry, pier_lines_en.
Kolejność: najpierw 5 agentów na B1, B2, B4, B5 i B6. B3 bierze pierwszy agent, który się zwolni.

ZASADY
- Unity i build_world uruchamiaj tylko przez scripts/unity-slot.ps1 (pool unity lub heavy). Bez adb i telefonów (zakaz właściciela). Długie kroki uruchamiaj w tle i od razu kończ turę. Nie czekaj blokująco dłużej niż 5 minut.
- NIE ruszaj gałęzi i worktree lidera: tunnel-0211, water2-0213, dk65-tiles2-0214, bialystok-t3-0208 oraz wszystkich *-dk65-*, knyszyn-*, water-*.
- Nie zmieniaj ProjectSettings/, Packages/, asmdef ani wspólnych scen. Po każdym uruchomieniu Unity: `git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings`.
- Pętla wizualna jest obowiązkowa: render, obejrzenie PNG, porównanie z referencją (sbs), poprawka. Zielony test to nie dowód wyglądu. Nie zmyślaj liczb: każda wartość ze źródła albo oznaczona WORKING_VALUE.
- Po KAŻDYM kroku: commit, push na gałąź i dopisek w artifacts/live/<gałąź>.md z NASTĘPNYM KROKIEM zapisanym jako komenda.
- Na koniec każdego zadania:
  - dowody kopiujesz robocopy do main artifacts/<gałąź>/;
  - ADR (status PROPOSED) z liczbami;
  - pytest tests/gis przez `uv run --project tools/worldgen python -m pytest tests/gis` oraz EditMode (pwsh scripts/test.ps1 -Platform EditMode);
  - raport do 20 linii w C:\Users\matma\Documents\Claude\kamion\docs\reports\S20B-<gałąź>.md: gałąź i sha, liczby, testy, dowody, co otwarte, „Gotowe do scalenia: TAK/NIE”;
  - live kończysz wpisem „KONIEC”.
- NIE scalaj do main i nie usuwaj worktree. Na końcu krótkie podsumowanie wszystkich zadań.
```

---

## SESJA 2: CHMURA (tylko GitHub, bez maszyny) albo lokalna. Research. Wklej:
```
Repo GitHub woogitsugames/kamion (Kamion: mobilny symulator ciężarówki, Białystok 1:1). Nie masz Unity, telefonów ani Data/raw. Masz do 5 agentów (Opus albo Fable). Lider (inna sesja) jest jedynym integratorem main. Ty pracujesz na gałęziach research/* i otwierasz PR. NIE scalasz.

NAJPIERW przeczytaj: CLAUDE.md (zasada 8: ZAKAZ Google Maps, Street View, Earth i 3D Tiles), docs/owner/AGENT-RULES.md p. 5–6, docs/owner/MISTRAL-TASKS-10.md (część wspólna na górze: format manifestu, licencje, audyt 20 %, kryteria akceptacji obowiązują Cię 1:1) oraz recenzje pokazujące, za co odrzucamy research: docs/reports/REVIEW-2026-11-14-s20-mistral-m62.md, …-m56.md, …-m57.md, …-cloud2-r9.md. Źródła dozwolone: Wikimedia Commons, Panoramax, Mapillary i KartaView (CC BY-SA, z atrybucją), OSM, GUGiK (ortofoto, BDOT10k), Geoportal, BIP i dokumenty GDDKiA, ISAP. Każde zdjęcie OBEJRZYJ przed opisaniem. Opis musi zgadzać się z obrazem. Brak = UNVERIFIED, nie zmyślaj.

Zadania (każde na osobnej gałęzi, PR do main):
K1 (NAJWAŻNIEJSZE, research/dk65-knyszyn-refs): bieżący kierunek gry to DK65 Białystok → Knyszyn i samo miasto Knyszyn (decyzje D64 i D65 w docs/11_DECYZJE_WLASCICIELA.md, brief docs/owner/S20-REGION-RING-BRIEF.md). Zbierz referencje dla kafli dk65-01…11, knyszyn, knyszyn-s i knyszyn-w (siatka w tools/worldgen/regions.py):
  (a) przekrój DK65 co ok. 1 km: liczba pasów, szerokość jezdni, pobocza, linie krawędziowe, rowy, bariery, zatoki autobusowe;
  (b) skrzyżowania i rondo DK65×DW671 w Knyszynie;
  (c) stan budowy S19 przy Knyszynie i wiadukt w Fastach: dokumenty GDDKiA (ZRID, mapy), co jest w budowie, gdzie zwężenia i objazdy;
  (d) ul. Ełcka (ok. 6,9 m);
  (e) latarnie LED na DK65 i w Knyszynie: typ, wysokość, rozstaw;
  (f) Rynek w Knyszynie: nawierzchnia, fontanna, kościół, zabudowa pierzei;
  (g) torowisko wzdłuż DK65 i szpalery drzew.
  Wynik: research/dk65-knyszyn-refs/ z README (liczby z odnośnikami), manifest.csv i sources.md.
K2 (research/gate3-spots-s21): zadanie G3, które nie zostało skończone. Treść: docs/owner/GPT-CHROME-RESEARCH-S20.md p. 1. Stan częściowy: research/_incoming/gpt-s20-gate3-spots/ (STATUS.md pokazuje, co już wiadomo; NIE kopiuj zdjęć stamtąd bez weryfikacji). Wymóg: po 6 obejrzanych kadrów na każdy z 4 punktów.
K3 (research/rooftop-gsm-s21 i research/night-lamps-s21): bloki M67 i M69 z docs/owner/MISTRAL-TASKS-10.md (id wierszy K67-NNN i K69-NNN). Przy M69 w README podaj konkretne liczby do kalibracji (ADR 0191 i 0192).
K4 (research/krywlany-airfield-s21 i research/plant-gates-s21): blok M64 oraz blok M63 z MISTRAL-TASKS-10.md. Częściowy stan M63 jest na gałęzi research/mistral-p20-plant-gates: przejrzyj go i dokończ na NOWEJ gałęzi, nie nadpisuj starej.
K5 (dokończenie chmury #2): szkice R2, R4, R6 i R9 (PR #62, #64, #65, #66). Treść jest w docs/owner/CLOUD2-PROMPT-S20.md (bloki R2, R4, R6, R9 i sekcja „Dokończenie”). Uwagi do R9: docs/reports/REVIEW-2026-11-14-s20-cloud2-r9.md. Pracuj na tych samych gałęziach (push do istniejących PR). Jeśli zostanie czas, poprawki Mistrala M57, M59, M60 i M61 (docs/owner/MISTRAL-FIXES-12.md, PR #56, #55, #57, #58) na nowych gałęziach research/<slug>-fix-s21.

ZASADY: commit i push co ok. godzinę; zdjęcia tylko z licencją pozwalającą na użycie (zapisz licencję i autora); bez marek i logo w opisach do gry; nagłówki HTTP i User-Agent bez nazwy projektu; stopka commitów zgodna z modelem. Na końcu każdego zadania PR (nie draft) z raportem po polsku i SUROWYM wyjściem `git diff --stat origin/main`. NIE scalaj. Na koniec krótkie podsumowanie: numery PR, liczby wierszy i co UNVERIFIED.
```
