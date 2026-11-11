# life r1 — pakiet do niezależnej recenzji
Gałąź: gpt-life-r1; zweryfikowany kod i wyniki: c63ac88fd13e61693fd0aff5cc8bbf63c3984fc6 (kolejne commity wyłącznie dokumentują przekazanie).
Selektywnie przeniesiono R4 osobówek: korektę Pearl, koła 22-segmentowe, nalot od progu/nadkoli/tyłu, podział hash 10/35/35/20 oraz warianty tablic ze wspólnego atlasu.
Porównanie: kanoniczny main 5f2aa277 po regeneracji i kandydat po regeneracji; po 368 PNG (92 kamery × Low/High × clear/overcast), High na WorldC_High.
Wszystkie 368 rekordów CPU: maksymalna zmiana draws świata, instancji i sumy = 0; maksymalna zmiana łącznych tris = 0%. Po 59 kontroli trasy na warunek, bez przekroczeń.
Zakres sumy draws: Low −24…0, High −40…0; trisK: Low −2…0, High −3…0. Są to szacunki CPU przed batchingiem, bez pomiaru GPU/A16.
Obejrzano 28 plansz before/after: review/<warunek>/page-*.jpg lub PNG. Pary materiałowe ≤960 px: refs/photo-render-black.jpg oraz photo-render-white.jpg; źródła w refs/provenance.json.
Zdjęcia materiałowe mają inną lokalizację/pogodę i nie są kalibracją albedo ani dopasowaniem geodezyjnym 1:1. Kadry r10b_black_45 i częściowo g_current_black_lod_20/45 nie dowodzą jakości LOD.
Autor: brak dawnych oderwanych plam w połowie drzwi; kurz nadal zbyt gładki i subtelny. Czerń clear szarawa, felgi płaskie, białe panele zbyt jednolite. Wygląd PARTIAL, niezależna recenzja wymagana.
Testy: ukierunkowane 50 passed; EditMode 274/274, 0 failed/skip; końcowy GIS 543 passed, 1 xfailed w 718,81 s (exit 0), manifest bez zmian.
Importer: 54 podsiatki tablic LOD0/1 z remapem lokalnych narożników; stan materiału identyczny po czterech seriach. Nie dowodzi to unikalności całej floty ani czasu GPU.
Nie używano telefonów, nie scalano do main i nie pushowano. Wcześniejsza porażka nieaktualnego fidelity_qa zachowana w initial-gis.log; po regeneracji test i finał GIS zielone.
Konflikty prawdopodobne: WorldPBR.shader (tylko CARPAINT), WorldPbrMaterials/InstanceImporter/RegionImporter, streetscape/export.py/materials.py, sets_facade.py/materials_spec.json. Zachować zmiany innych dziedzin.
Integracja przez lidera: niezależny visual-critic → git merge gpt-life-r1; konflikty generatów rozwiązać wersją main, potem regeneracja materiałów/props/world/fidelity w heavy, import i testy Unity ze slotem.
Status roli: po nowym poleceniu S11 wykryto już aktywnego lidera Claude. Pakiet r1 przekazywany; start r2 lub przejęcie integracji czeka na wyjaśnienie podziału.
