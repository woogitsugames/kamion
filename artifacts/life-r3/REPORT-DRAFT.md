# Life r3 — felgi, czerń i tył osobówek — PARTIAL
Gałąź gpt-life-r3; źródła C: 9c7c8c53 (A 846c446e, B 5fb5f28b); stan końcowych testów: DO UZUPEŁNIENIA.
Main 14ccbaf1 dołączono wyłącznie do własnej gałęzi; autor nie scala do main, nie pushuje ani nie używa telefonów.
Fazy ramion felg LOD0 zastępują płaskie czoła; istniejącej beczki/piasty nie przypisuje się tej rundzie.
81 siatek aut: maksima LOD0/1/2 4170/854/90, dawne limity bez zmian; cała biblioteka +960 tris, grupy bez zmian.
Tylko czarny lakier: opt-in flake_lift 0,08→0,025; 28 natywnych materiałów sprawdzonych, reszta pliku czerni i pozostałe materiały identyczne.
C poszerza monotoniczny osad tyłu od rzeczywistego progu, bez nowej tekstury/przebiegu; D odrzucono po oględzinach.
192 raw, geometria poza osobówkami, kolizje i kontakt bez zmian; build bez fallback=True, SHA źródeł/GLB zamrożone do testów.
Baseline/C: 123 kamery × 4 warunki = 492 pary, w tym wszystkie 59 kamer trasy na warunek; identyczne pozy i projekcja.
Maks. tris trasy Low +0,067613%, High +0,155216%; wszystkie kamery Low +0,323992%, High +0,164056%.
Draws świata +0 i instancji +0 osobno; brak pominiętych kamer/przekroczeń. To estymaty CPU przed batching, nie pomiar GPU/A16.
GPU C Direct3D12: 1005 instancji, poziomy CPU/GPU 99/366/331/209 zgodne; 81 LOD, maks. błąd opacity 0,00004215; tablice bez zmian.
Nowe ROI drzwi/asfalt clear: baseline 0,9703/0,9769 → C 0,9236/0,9308 (Low/High); overcast C 0,6706/0,6902. To display RGB, nie albedo.
Testy: EditMode 323/323; końcowy GIS DO UZUPEŁNIENIA. Pierwszy GIS 639 passed, 1 xfailed, 1 failed: wyłącznie stare fidelity po merge main; log zachowany, raport odtworzony kanonicznie bez zmiany testu/kodu dróg.
Obejrzano wszystkie 164 strony before/C przez 28 przeglądów oraz osobne detale; autor nie stwierdził regresji układu świata, niezależny odbiór należy do lidera.
Pary ≤960 px: [czerń](refs/sbs-black-c.jpg), [tył](refs/sbs-tail-c.jpg); źródła/licencje i różnice miejsca, modelu, światła: refs/REFERENCES.md.
PARTIAL: tył nadal za gładki i za czysty, czerń clear nadal zbyt szara; brak pomiaru A16, fotorealistycznego PASS i gwarancji unikalności tablic całej floty.
Konflikty: life_cars, CARPAINT oraz addytywna flaga w materials.py/WorldPbrMaterials.cs; zachować inne domeny i odtworzyć generaty. ADR 0089; następna r4: diagnostyka LOD/kół placowych, potem palety.
