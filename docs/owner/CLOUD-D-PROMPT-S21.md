# Zlecenie dla sesji Claude Code w CHMURZE „D” (do 5 agentów, Fable dozwolony), s21, 15.11 wieczór

Wklej:
```
Repo GitHub woogitsugames/kamion (Kamion: mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1). Jesteś w chmurze: NIE masz Unity, telefonów ani Data/raw. Masz do 5 agentów (możesz używać Fable); każdy robi jedno zadanie na swojej gałęzi od origin/main. Subagenci nie tworzą subagentów. Lider (sesja lokalna) jest jedynym integratorem main: zbuduje świat, wyrenderuje, zmierzy i scali. Ty NIE scalasz.

NAJPIERW przeczytaj: CLAUDE.md, docs/owner/AGENT-RULES.md, docs/owner/S20-PR-REVIEW-BRIEF.md, docs/05 (mapa i dane), HANDOVER.md (blok „SESJA 20”, najnowsze wpisy na dole), docs/11_DECYZJE_WLASCICIELA.md (D63–D66), research/dk65-knyszyn-refs/README.md (K1) oraz ADR 0205, 0207, 0212, 0214, 0215, 0217, 0220.

Uruchamiasz tylko czysty Python: `uv run --project tools/worldgen python -m pytest tests/gis -k <wybrane>`. Testy wymagające Data/raw pomiń i wypisz w raporcie. Dane regionów (Data/Regions/<id>/*.geojson, overrides.yaml, generated/*.json) są w gicie. Wszystko, co wymaga build_world, Unity albo renderu, wpisz do raportu jako DOKŁADNĄ komendę dla lidera.

NIE dotykaj (lokalni agenci w toku): generatora dróg w regionie C i budżetu trójkątów stretch_04 (budget-fix-s21, ADR 0221), tunelu kleeberga (0211), latarni/nieba knyszyn* i bialystok-knyszynska (0216), Ełckiej i placu budowy dk65-05/06 (FIX PR #80, lokalnie), importera rail_* w Unity i sha256 w qa-tools (FIX #95/#96, lokalnie). Nowe ADR: D1=0222, D2=0223, D3=0224, D4=0225, D5=0226.

D1 szpalery wzdłuż DK65 (gałąź treerows-0222). D65/K1: aleje drzew przy DK65 i drogach dojazdowych do Knyszyna. Sprawdź, co generator roślinności (tools/worldgen/streetscape/vegetation.py, plantings.py) robi dziś z OSM `natural=tree_row` i pojedynczymi `natural=tree` w kaflach dk65-01…11, knyszyn*. Dodaj szpaler jako dane: rytm, gatunek/mieszanka, odsunięcie od krawędzi jezdni zgodne z przepisami (źródło!) i K1, wycięcie przy zjazdach i skrzyżowaniach (trójkąty widoczności). Budżet trójkątów i instancji oszacuj i wpisz do ADR. Testy na danych syntetycznych + na geojsonach kafli z gita.
D2 torowisko wzdłuż DK65 (gałąź rail-dk65-0223). Generator rail-0217 (PR #96, opt-in `Region.rail`) działa dziś tylko w dw671-tykocin-01. Ustal z danych w gicie i z OSM (Overpass, nagłówek bez nazwy projektu), które kafle dk65-* i knyszyn* mają linię kolejową (Białystok–Ełk, nr 38) i przejazdy; przygotuj włączenie rail dla tych kafli (regions.py + overrides), przejazdy z typem zabezpieczenia z OSM (`crossing:barrier`, `crossing:light`), testy. Opisz styk z #96 (gałąź od origin/rail-0217, jeśli nie jest jeszcze w main) i komendy build_world dla lidera.
D3 kontrola szwów DK65 (gałąź seams-0224). Napisz narzędzie tools/worldgen/qa/seams.py: dla par sąsiednich kafli (C/dojlidy→dk65-01→…→dk65-11→knyszyn-s, knyszyn, knyszyn-w, dk65-monki-01, dw671-tykocin-01) porównaj na wspólnej granicy przekrój drogi (szerokość jezdni, linie, pobocza, wysokość osi) z generated/*.json i geojsonów; tolerancja ±0,1 m. Raport tabelą. Szczególnie szew dk65-10/11 ↔ knyszyn-s: musi mieć przekrój K1 (rozstaw linii 6,0–6,4 m, mediana 6,2; ADR 0220). Dla niezgodności zaproponuj override z uzasadnieniem i komendę przebudowy. Test pytest dla narzędzia.
D4 recenzje PR research (bez gałęzi kodu; raporty docs/reports/REVIEW-2026-11-15-s21-cloudD-*.md na gałęzi reviews-0225): #99 (M67 uzupełnienie), #92 (M59-FIX), oraz stare #62, #64, #65, #66 (cloud2 R2/R4/R6/R9), #55, #42 — według S20-PR-REVIEW-BRIEF (obejrzyj kadry, sprawdź licencje i SOURCED vs ESTIMATED, werdykt SCAL / FIX / ZAMKNIJ z listą poprawek). Werdykt także jako `gh pr comment`. Nie scalaj.
D5 kolizja numerów ADR (gałąź od origin/putry-ring-0198b, PR #93): #93 używa ADR 0216, a 0216 ma już summer-led-0216 (latarnie LED Knyszyn). Przenumeruj ADR #93 na 0226 (plik, odwołania w kodzie/testach/docs), push na tę samą gałąź, komentarz w PR. Potem przejrzyj #93 kodowo (wyspa ronda Putry z ortofoto, 2 rzędy podpór) i porównaj z #82 piers-0198 — czy się dublują/konfliktują; raport i komendy dla lidera.

ZASADY: commit i push po każdym kroku; nie zmyślaj liczb (źródło, ESTIMATED albo WORKING_VALUE); bez ProjectSettings/, Packages/, asmdef i wspólnych scen; bez Google Maps, Street View, Earth i 3D Tiles; bez marek i logo; nagłówki HTTP bez nazwy projektu; stopka commitów zgodna z modelem. Na koniec każdego zadania PR (nie draft) z raportem do 20 linii po polsku:
- co zmienione;
- testy uruchomione i ich wynik;
- testy NIEuruchomione;
- DOKŁADNE komendy dla lidera;
- co otwarte;
- „Gotowe do scalenia po weryfikacji lidera: TAK/NIE”.
NIE scalaj. Na końcu podsumowanie z numerami PR.
```
