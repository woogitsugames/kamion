# Zlecenia dla dwóch sesji Claude Code w CHMURZE (do 5 agentów Opus/Fable każda), s20, 15.11

Obie sesje mają dostęp tylko do GitHuba (woogitsugames/kamion): bez Unity, bez telefonów i bez Data/raw. Lokalna maszyna należy do lidera i jego 4 agentów. Gałęzie Argona (0194, 0188, 0187, 0189) zostają na później, u lidera.

Stan prac innych modeli, sprawdzony 15.11 ok. 10:00:
- **Sesja kodu:** 0197 i 0198 nie zostały oddane.
- **GPT Chrome:** G3 ma 3 wiersze, M67, M69 i M64 nie zostały zaczęte.
- **Mistral:** M63 jest w połowie, poprawki M57, M59, M60 i M61 nie zostały oddane.
- **Chmura #2:** R2, R4, R6 i R9 to szkice.
- **Fizyka:** 0201 stoi.

---

## SESJA A: KOD I DANE bez Unity. Wklej:
```
Repo GitHub woogitsugames/kamion (Kamion: mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1). Jesteś w chmurze: NIE masz Unity, telefonów ani Data/raw. Masz do 5 agentów (Fable do geometrii i danych, Opus do kodu i świateł). Każdy agent robi jedno zadanie na swojej gałęzi. Subagenci nie tworzą subagentów. Lider (inna sesja, lokalna) jest jedynym integratorem main. On zbuduje świat, wyrenderuje i scali. Ty NIE scalasz.

NAJPIERW przeczytaj: CLAUDE.md, docs/owner/AGENT-RULES.md, docs/04 (fizyka), docs/06, HANDOVER.md (blok „SESJA 20”, najnowsze wpisy na dole bloku), docs/11_DECYZJE_WLASCICIELA.md (D63–D65).

Uruchamiasz tylko to, co działa bez Unity:
- .NET: tools/physics-runner (dotnet test / dotnet run);
- czysty Python: `uv run --project tools/worldgen python -m pytest tests/gis -k <wybrane>`. Część testów wymaga Data/raw; te pomiń i wypisz w raporcie.
Każdy krok wymagający Unity albo build_world (BuildBatch, build_world, import-region, visual-qa, EditMode) wpisz do raportu jako DOKŁADNĄ komendę dla lidera.

A1 fizyka R3 (kontynuacja gałęzi truckdata-0201, ADR 0201). Przeczytaj artifacts/live/truckdata-0201.md na tej gałęzi i ostatnie commity:
  - rozdzielony promień toczny 0,524 m i promień geometryczny;
  - naciski osi;
  - usunięte marki z JSON.
  Zrób baseline i porównanie runnera (`dotnet run -c Release --project tools/physics-runner/Runner -- --out artifacts/truckdata-0201/<tag>`) przed i po zmianie. Scenariusze docs/04 §6: 0–80, droga hamowania (bramka: solo 0–80 13,66 s, hamowanie 35,85 m; 40 t 47,79 s i 40,72 m na A16). Każda zmiana liczby musi mieć źródło. Testy .NET zielone.
A2 lights-0197 (nowa gałąź). Pełna treść: docs/owner/CODE-SESSION-PROMPT-S20.md, ZADANIE A:
  - STOP:pozycyjne ≥ 5:1 po limiterze ADR 0178;
  - rozdzielenie TAIL_BRAKE naczepy;
  - bursztyn (1, 0.22, 0) z testem obszaru chromatyczności R48;
  - tablica ≥ 2,5 cd/m².
  Napisz kod i testy EditMode (lider je uruchomi). Logikę liczb (limiter, stosunek, chromatyczność) wydziel tak, żeby dało się ją sprawdzić czystym testem .NET albo Pythonem.
A3 piers-0198 (nowa gałąź). Pełna treść: CODE-SESSION-PROMPT-S20.md, ZADANIE B:
  - dodaj `pier_lines_en` w Data/Regions/bialystok-industrial-c/viaduct_underdeck.json dla estakady A ronda Putry;
  - zostaw pusty `BLOCKED_COLS` dla tych rzędów;
  - popraw sprzeczne komentarze.
  Stacje: WORKING_VALUE z research/mistral/p13-andersa-viaducts/ i wycinków c027/c022. Kolumny nie mogą stać na jezdni: sprawdź na geometrii dróg w Data/Regions/bialystok-industrial-c (geojson w gicie).
A4 DK65 według D65 (nowa gałąź dk65-d65-data). Same dane i nadpisania w Data/Regions/dk65-01…05:
  (a) ul. Ełcka ma ok. 6,9 m szerokości (D65). Znajdź jej way w danych regionów i dodaj nadpisanie szerokości tak, jak robią to istniejące `dk65-carriageway-width` (wzoruj się na ADR 0205 i 0212).
  (b) nowa jezdnia w dk65-05 nie jest otwarta, więc ma być placem budowy: bez ruchu i bez oznakowania poziomego. Zaproponuj schemat nadpisania (np. `construction: true`) i obsłuż go w tools/worldgen (roads/markings) z testami jednostkowymi bez Data/raw.
  NIE dotykaj dk65-06…11, knyszyn* ani bialystok-* (pracują tam agenci lidera).
A5 marki i licencje (nowa gałąź brand-fixes-s21). Popraw w kodzie i danych przypadki z docs/reports/BRAND-SWEEP-S20.md, które lądują w buildzie albo na ekranie (neutralne nazwy). Pomiń pliki pojazdu, które zmienia A1. Dodaj ekran „Informacje” z atrybucjami według docs/owner/ATTRIBUTION-SCREEN-DRAFT.md i docs/reports/LICENSES-AUDIT-S20.md: dane jako plik tekstowy w Resources oraz prosty widok UI. Bez zmian w ProjectSettings/, Packages/ i asmdef.

ZASADY: commit i push po każdym kroku; nie zmyślaj liczb (źródło albo WORKING_VALUE); nie zmieniaj ProjectSettings/, Packages/, asmdef ani wspólnych scen; stopka commitów zgodna z modelem. Na koniec każdego zadania otwórz PR (nie draft) z raportem do 20 linii po polsku:
- co zmienione;
- testy uruchomione i ich wynik;
- testy NIEuruchomione;
- DOKŁADNE komendy dla lidera (build, import, visual-qa, EditMode);
- co otwarte;
- „Gotowe do scalenia po weryfikacji lidera: TAK/NIE”.
NIE scalaj. Na końcu krótkie podsumowanie z numerami PR.
```

---

## SESJA B: RESEARCH. Wklej:
```
Repo GitHub woogitsugames/kamion (Kamion: mobilny symulator ciężarówki, Białystok 1:1). Jesteś w chmurze: nie masz Unity, telefonów ani Data/raw. Masz do 5 agentów (Opus albo Fable). Lider (inna sesja) jest jedynym integratorem main. Ty pracujesz na gałęziach research/* i otwierasz PR. NIE scalasz.

NAJPIERW przeczytaj: CLAUDE.md (zasada 8: ZAKAZ Google Maps, Street View, Earth i 3D Tiles), docs/owner/AGENT-RULES.md p. 5–6, docs/owner/MISTRAL-TASKS-10.md (część wspólna na górze: format manifestu, licencje, audyt 20 %, kryteria akceptacji obowiązują Cię 1:1) oraz recenzje pokazujące, za co odrzucamy research: docs/reports/REVIEW-2026-11-14-s20-mistral-m62.md, …-m56.md, …-m57.md, …-cloud2-r9.md. Źródła dozwolone: Wikimedia Commons, Panoramax, Mapillary i KartaView (CC BY-SA, z atrybucją), OSM, GUGiK (ortofoto, BDOT10k), Geoportal, BIP i dokumenty GDDKiA, ISAP. Każde zdjęcie OBEJRZYJ przed opisaniem. Opis musi zgadzać się z obrazem. Brak = UNVERIFIED, nie zmyślaj. Zdjęcia zapisuj w gałęzi (rozsądny rozmiar, np. ≤ 1600 px), z licencją i autorem w manifeście.

Zadania (każde na osobnej gałęzi, PR do main):
K1 (NAJWAŻNIEJSZE, research/dk65-knyszyn-refs): bieżący kierunek gry to DK65 Białystok → Knyszyn i samo miasto Knyszyn (D64 i D65 w docs/11_DECYZJE_WLASCICIELA.md, brief docs/owner/S20-REGION-RING-BRIEF.md, regiony dk65-01…11, knyszyn, knyszyn-s i knyszyn-w w tools/worldgen/regions.py). Zbierz:
  (a) przekrój DK65 co ok. 1 km: pasy, szerokość jezdni, pobocza, linie krawędziowe, rowy, bariery, zatoki autobusowe;
  (b) skrzyżowania i rondo DK65×DW671 w Knyszynie;
  (c) stan budowy S19 przy Knyszynie i wiadukt w Fastach: dokumenty GDDKiA (ZRID, mapy), co w budowie, zwężenia;
  (d) ul. Ełcka (ok. 6,9 m);
  (e) latarnie LED na DK65 i w Knyszynie: typ, wysokość, rozstaw;
  (f) Rynek w Knyszynie: nawierzchnia, fontanna, kościół, pierzeje;
  (g) torowisko wzdłuż DK65 i szpalery drzew.
  Wynik: research/dk65-knyszyn-refs/ z README (liczby z odnośnikami, tabela per kafel), manifest.csv i sources.md.
K2 (research/gate3-spots-s21): zadanie G3 z docs/owner/GPT-CHROME-RESEARCH-S20.md p. 1 (4 punkty problemowe trasy C z bramki 3). Wymóg: po 6 obejrzanych kadrów na punkt. Stan częściowy GPT jest tylko lokalnie i go nie widzisz; zacznij od zera według opisu.
K3 (research/rooftop-gsm-s21 i research/night-lamps-s21): bloki M67 i M69 z docs/owner/MISTRAL-TASKS-10.md (id wierszy K67-NNN i K69-NNN). Przy M69 w README podaj konkretne liczby do kalibracji (ADR 0191 i 0192 w docs/adr).
K4 (research/krywlany-airfield-s21 i research/plant-gates-s21): bloki M64 i M63 z MISTRAL-TASKS-10.md. Częściowy M63 jest na gałęzi research/mistral-p20-plant-gates: przejrzyj go i dokończ na NOWEJ gałęzi.
K5 (dokończenie chmury #2): szkice R2, R4, R6 i R9 (PR #62, #64, #65, #66). Treść w docs/owner/CLOUD2-PROMPT-S20.md (bloki R i sekcja „Dokończenie”), uwagi do R9 w docs/reports/REVIEW-2026-11-14-s20-cloud2-r9.md. Pracuj na tych samych gałęziach (push do istniejących PR). Jeśli zostanie czas, poprawki Mistrala M57, M59, M60 i M61 (docs/owner/MISTRAL-FIXES-12.md, PR #56, #55, #57, #58) na nowych gałęziach research/<slug>-fix-s21.

Kolejność: K1, K5, K2, K3, K4 (5 agentów naraz, po jednym zadaniu).

ZASADY: commit i push co ok. godzinę; bez marek i logo w opisach do gry; nagłówki HTTP i User-Agent bez nazwy projektu; stopka commitów zgodna z modelem. Na końcu każdego zadania PR (nie draft) z raportem po polsku i SUROWYM wyjściem `git diff --stat origin/main`. NIE scalaj. Na koniec krótkie podsumowanie: numery PR, liczby wierszy i co UNVERIFIED.
```
