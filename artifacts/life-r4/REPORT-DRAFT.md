# Life r4 — przestrzenne felgi placowe — PARTIAL
Gałąź gpt-life-r4; geometria 954aca26, generacja 6c6f426e, wybór/limity d653d9a3; końcowa walidacja DO UZUPEŁNIENIA.
Main 8b74c2c5 dołączono wyłącznie do własnej gałęzi. Autor nie scala do main, nie pushuje i nie używa telefonu.
Płaski fan LOD0 zastąpiono miską, piastą i zagłębieniami wentylacyjnymi; istniejące rim/tyre, bez nowego materiału, mapy, keywordu lub przebiegu.
Audyt rzeczywistego GLB: 471 węzłów, 28 zmienionych podsiatek wyłącznie przy kołach LOD0; bieżnik, kolizje/contact, LOD1, pozostałe obiekty i 192 raw bez zmian.
LOD0 plandeka 1102→1942, chłodnia 1192→2032, ciągnik 766→1550; LOD1 nadal 316/290/286. Biblioteka łącznie +11424 tris, nie jest to koszt klatki.
Baseline materiały 909 s / World 489,9 s; World A2 528,5 s, bez fallback=True; 15 gotowych Fab/Megascans i 151 map Medium sprawdzonych.
Before/after-a2: po 131 kamer × 4 warunki = 524 PNG/rekordy; wszystkie 59 kamer trasy na warunek, identyczne pozy/rotacje/projekcja i zgodność z legacy loggerem.
Trasa Low maks. +0,365808608% tris (r10_block_5), High +0,585729008% (g3a-rondo-bie-approach); limit +2% bez zmiany.
Wszystkie kamery Low +3,496473727% (yard_tractor_white_side8), High +2,639701583% (yard_tractor_blue_rear34). Draws świata +0 i instancji +0 osobno wszędzie.
To estymaty CPU przed SRP batching. Czas GPU/A16 UNVERIFIED. Po pomiarach lokalne sufity LOD0: naczepy 1200→2200, ciągniki 1500→1700; kontenery, LOD1 i limity ramki bez zmiany.
Wszystkie 408 materiałów native identyczne z baseline. EditMode zmienił SrcBlend w dwóch nieużywanych cache car_dirt; przywrócono dokładne SHA, zachowano pierwotny guard exit 1 i udokumentowano cleanup.
Testy: nowe felgi 9/9, kontrakt pojazdów 12/12, streetscape 59/59, world_v31 20/20; NUnit EditMode 340/340, 0 skipped. Pełny GIS DO UZUPEŁNIENIA.
Rzeczywista diagnostyka potwierdza LOD0 w 13 kadrach na Low i High; nie zmieniono wspólnego progu. Dwa wcześniejsze błędy zamknięcia High zachowane; późniejszy przebieg 0 ze zgodnymi licznikami.
Obejrzano 32 pary nowych detali w czterech warunkach oraz SBS. [Konstrukcja](refs/sbs-yard-rim-a2.jpg) i [detal koła](refs/sbs-wheel-detail-a2.jpg), oba 960×360; źródło/licencja i crop/SHA: refs/REFERENCES.md.
Zdjęcia mają inne miejsce, model, światło i skalę, bez kalibracji albedo/GPS. Felga czytelniejsza, lecz śruby, zużycie i okrągłość pozostają uproszczone; kadr podpór chłodni z błędną krawędzią terenu nie służy jako dowód ich detalu.
Nie zmieniono rozmieszczenia, kabin, plandek ani osobówek; ich wcześniejsze ograniczenia nadal PARTIAL. Osprzęt podwozia już istnieje, nie dodawano go ponownie. Niezależny odbiór i telefon należą do lidera.
Konflikty: life_props.py, trzy oczekiwania własnych prototypów w test_streetscape/test_world_v31, nowy test felg i generaty. Zachować inne domeny, odtworzyć bibliotekę. ADR 0122; następna r5 — zaległe palety.
