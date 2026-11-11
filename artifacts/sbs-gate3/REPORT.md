# Strumień J / ADR 0103 — REPORT
Wynik: DONE — narzędzie i 160 arkuszy gotowe do recenzji lidera; bramka 3 NIEZALICZONA.
Gałąź gpt-sbs-gate3; kod/kamery 9bfdf2b4; baza main 9e6e9fde; bieżący sha: git rev-parse HEAD.
Dostarczono 40 unikalnych zdjęć (20/G3), 40 kamer sbs-*, 160 renderów i 160 arkuszy Low/High × clear/overcast.
Kod tools/refs/sbs_gate3.py; wrapper scripts/sbs-gate3.ps1; nowe Data/Regions/bialystok-industrial-c/sbs_*.json; inne kamery/świat bez zmian.
27 fisheye + 13 perspective wyprostowane z publicznych intrinsics; GPS -> EPSG:2180, zbieżność południków, zgodny FOV, jawne authored_overrides.
Po przeglądzie skorygowano 27 pozycji/poz od r0, w tym 8 wysokości pomostów, 1 odsunięcie od bariery i 1 błędny kurs SfM; niepewność pozostaje WORKING_VALUE.
Końcowy pełny GIS 380 passed/1 znany xfailed (601.07 s, pytest-final.log; w tym SBS 10/10); refs 51/51, EditMode 226/226 (tests/*.xml).
Metryki: histogram 32-bin, jasność, osobne stosunki powierzchni i jasności niebo/asfalt, jawne maski lub opisane heurystyki, hashe źródeł/renderów.
Dowody finalne: sheets/{Low,High}-{clear,overcast}/*.png + metrics.json; renders/*/stats-*.txt; SUMMARY.json; audit-final.log.
Obejrzano kontakty wszystkich 160 par i wybrane pełne PNG w 4 stanach; VISUAL-REVIEW.md = samokrytyka, nie niezależna recenzja.
Przed/po: r0/ (pełna pierwsza macierz), r1-adjustment-before/, probe-sheet-*.jpg; korekty r2/r3 tylko dla poz o udowodnionej zmianie.
Po korektach G3-A s=343.026–436.716 m (max 29.303 m od trasy), G3-B 0–485.862 m (max 33.732 m); brak pierwszych ~300 m G3-A.
Low: regular drawsEst 188–486, trisK 155–556 (estymaty CPU przed SRP, instancing osobno); brak zmian runtime, brak nowego pomiaru GPU.
Otwarte: niezależny review, dokładność GPS/oka/roll, poligony do ścisłej fotometrii, zdjęcia/akceptacja właściciela; różnice świata opisane, nie poprawiane.
ADR docs/adr/0103-gate3-side-by-side.md; licencja/autor/URL/SHA256 każdego zdjęcia: docs/refs/sbs-gate3-attribution.md + LICENSES/REFERENCES.
Przewidywane konflikty: tylko addytywne sekcje docs/LICENSES.md i docs/REFERENCES.md; nie dotykano cudzych strumieni.
Odtworzenie: uv run --project tools/refs python tools/refs/sbs_gate3.py prepare; pwsh scripts/sbs-gate3.ps1 -EditMode (respektuje PHONE_RUN).
Lider: review REPORT/VISUAL-REVIEW/PNG, potem git merge gpt-sbs-gate3; artefakty kopiowane do głównego artifacts/sbs-gate3 bez commitu na main.
Nie scalano ani nie pushowano main/gałęzi; brak adb/telefonów, efekty uboczne Unity cofnięte.
