# STATUS — gpt-s16 r1
2026-11-12T23:31:56.5941638+01:00
Gałąź: gpt-s16-r1
Zapisano render after/High-overcast; liczby w stats.txt. Oględziny i recenzja pozostają otwarte.
NASTĘPNY KROK: Get-Content artifacts/gpt-s16-r1/STATUS.md
Gotowe do recenzji: NIE

EditMode zakończony: exit 0; szczegóły EDITMODE-STATUS.md i final-editmode.xml.

EditMode:452/452 passed,0skipped. Wszystkie456parPNG i per-kamera count gotowe; Low bez wzrostów. Dodano odczyt natywnych pasm/projekcji w edytorze do pomiaru progów i kadrów; bez pomiaru GPU, bez modyfikacji sceny/profili.

Pełny GIS zakończony: exit 1; szczegóły GIS-STATUS.md oraz final-gis.log.

GIS:926passed,3xfailed,1FAIL(test_report_not_stale) — odświeżenie fidelity w slocie heavy27250, bez zmian roads/*. Recenzja wizualnaPARTIAL: brak nowej regresji w widocznych celach, ale część przejść zasłonięta. Wyszukiwarka dodatkowych kamer sprawdzi statyczne linie widzenia do rzeczywistych instancji, także agregatu chłodni; wynik wymaga oględzin.

Wyszukano40uzupełniającychkamer; każda para progowa18/18niezasłoniętych prób statycznych. Nie oznacza to akceptacji wizualnej. Obejrzano wszystkie456par w20arkuszach author-overviews i lokalny real-cars-contact.jpg; brak nowej zmiany makro, luki widoczności potwierdzone. Start renderów dodatkowych after przed ponownym bazowym importem.

Dodatkowe kamery: after/Low-clear zapisane.

Dodatkowe kamery: after/Low-overcast zapisane.

Dodatkowe kamery: after/High-clear zapisane.

Dodatkowe kamery: after/High-overcast zapisane.

Pierwsze40dodatkowychkamer NIEZALICZONE: statyczne raycasty używały wysokości absolutnych bez scenicznego -anchorZ. Obrazy obejrzano, wykryto zasłonięcia/pozycje pod terenem. Poprawiono wyłącznie narzędzie QA: scenaOffset z WorldInstances, centralne instancje i kamery wewnątrz kafla. Fidelity odświeżone254.3s, potrzebna walidacja testów.

Fidelity po odświeżeniu:9passed,1xfailed; poprzedni FAILstale rozwiązany. Próba usunięcia wyłącznie własnych odrzuconych PNG clear-rejected/after została dwukrotnie odrzucona automatycznie: blocked by policy (brak dalszego uzasadnienia). Nie usunięto plików. DECYZJA: sprzątnięcie tego katalogu pozostaje do ręcznego działania właściciela; nie blokuje dalszej pracy. Drugi wyszukany zestaw40kamer ma18/18prób; wymaga renderu i oględzin.

Dodatkowe kamery: after/Low-clear zapisane.

Dodatkowe kamery: after/Low-overcast zapisane.

Dodatkowe kamery: after/High-clear zapisane.

Dodatkowe kamery: after/High-overcast zapisane.

Kolizje sceny nie pokrywają wszystkich widocznych ścian, dlatego same promienie nie dały pełnej widoczności — druga próba nie jest zaliczona. Nowe40kamer: prześwity z643obrysami budynków i1488obrysami pozostałych pojazdów, wysokość2.5m nad NMT. Sprawdzenie Low-clear przed resztą warunków. Narzędzie nie zmienia geometrii/rozmieszczenia.

Dodatkowe kamery: after/Low-clear zapisane.
