# gpt-s16 r2 — ADR 0154
Gałąź `gpt-s16-r2`; baza r1 `eb718b7f8` + main `5cca3a2f5`, merge `250f9e7b9`. Recenzja statyczna PASS zakresu; GIS jeszcze trwa.
19 posesji, 34 nowe odcinki żywopłotów, 257,37 m; istniejące 479 m → 736,37 m. Wartości wymiarów/selekcji WORKING_VALUE, nie inwentaryzacja OSM.
116 drzew ogrodowych bez zmiany liczby/pozycji/prototypu/tier; 104 szersze korony, 47 wyższych drzew (11,3–20,4 m). High-only nadal pomijane na Low.
Końcowy baseline B 590,4 s; generator B 593,1 s, import i cztery warunki 90 kamer przed/po; bazę odtwarza `KAMION_GARDENS_0154=0`.
Low: delta scene draws 0 na każdej kamerze, instance draws/tris/liczba instancji bez zmian; dokładne łączne tris maks. +0,718622% (limit +2%).
High: delta scene draws 0, tris maks. +0,716331%; najwyższa suma scene+instance tris 1 368 451. Liczby CPU, nie GPU/SRP/telefon.
Każda kamera: `CAMERAS.md`, `camera-counts.json`; oba oświetlenia. Diagnostyka addytywnie zapisuje dokładne całkowite tris.
Audyt: 2151 chronionych węzłów, 125450 rekordów nie-high, 32 grupy posesji i 6 bibliotek/atlasów zachowane; +3580 tris/kit High i Low, zero nowych grup/materiałów.
458/458 materiałów natywnych identycznych SHA256 po cofnięciu 2 ubocznych serializacji Unity (`native-cleanup-ledger.json`).
Sześć ulic: Skidelska, Racławicka, Grodzieńska, Wileńska, Olsztyńska, Michała Motoszko; po dwa pasujące ujęcia przed/po.
Zdjęcia P07/P08/P10/P12/P14/P17 są typologiczne, z innych poz/lokalizacji, CC BY-SA 4.0; pełne hashe i autorzy w `reference-provenance.json`. Bez Google, bez tekstur ze zdjęć.
Dowody ≤960 px: `pairs/` (360), `overviews/` (32), `photo-pairs/` (24); autor obejrzał wszystkie pary i foto, critic wszystkie arkusze oraz zbliżenia.
B po korekcie A: critic PASS lokalnej poprawy frontów/koron, PARTIAL fotograficznego D51/Gate3; pozostały płaskie korony, nagie konary i otwarte trawniki (`REVIEW-VISUAL.md`).
Testy: celowane GIS 7 passed; pełny EditMode 484 passed, 0 failed/skipped (w tym integracja 104 skal). Pełny GIS W TOKU.
Zmiany wspólne tylko addytywne: importer jawnego `garden_canopy_width` dla high i dwa pola dokładnych liczników VQA. Shaderów/przebiegów/profili bez zmian.
Odtworzenie: `baseline-world.ps1 -Stage after`, `import.ps1`, `render.ps1 -Stage after`; skrypty przestrzegają wspólnych slotów i PHONE_RUN. Drogi/domowe modele tylko czytane.
Szkice zastąpione źródłami usunięto; pełne PNG lokalne, kompaktowe dowody w Git. Telefon, ASTC, FPS, termika i popping niezweryfikowane.
Następny krok po GIS: push własnej gałęzi; lider integruje i mierzy urządzenia. Agent rozpoczyna ADR 0155 na `gpt-s16-r3`.
