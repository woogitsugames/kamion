# Runda 2 — robocza notatka do raportu końcowego

Gałąź gpt-asphalt-r2. Baza po merge main 4992c434. Dziedzina: krawężnik i kostka jako materiał, bez geometrii roads i bez materiałów placu Kwadrat. D51: ocena materiału nie blokuje rozpoznawalności trasy w Gate3.

Kandydat dodaje dwa opcjonalne bloki danych. kerb_wear wykorzystuje istniejący Mask.B i makro do brudu spoin i słabego mineralnego nalotu. ground_grime pozwala zachować siłę fug chodnika i osłabić rozległe mokro wyglądające plamy. Nowe parametry są WORKING_VALUE. Materiały bez flag zachowują poprzednie działanie. Brak nowych odczytów tekstur Low, przebiegów, wariantów słów kluczowych i kanałów wierzchołków. Dochodzi gałąź uniform i ALU dla krawężnika; czas GPU A16 pozostaje UNVERIFIED.

Baseline odświeżono po korekcie własnych dwóch kamer do seat=file. Są 82 kamery × Low/High × clear/overcast, razem 328 PNG i 328 snapshotów rzeczywistej rootToWorld. Każda macierz ma 16 elementów. Pełny audyt bazowej geometrii obejmuje 128 GLB i 7315 prymitywów. Import baseline: tekstury ASTC 40 910 657 bajtów, 126 992 instancji, 2674 collidery props. Pozostałe kategorie bajtów w baseline-import.json.

Wybrane zdjęcia Mapillary z 2020-08-15, richlv, CC BY-SA 4.0, mają w obecnych pozach SBS istotną rozbieżność kadru. Zachowano ten dowód. Zdjęcia służą za przykład materiału, nie za kalibrację jasności ani potwierdzenie zgodnej geometrii. Osobne zbliżenie obrzeża pokazuje niski brzeg chodnika; nie dowodzi wysokości krawężnika jezdni.

EditMode: 309/309 passed, zero failed/skipped, exit 0. Reszta walidacji i końcowa ocena wizualna wymagają zakończenia producenta, importu i renderu. Nie przenosić do końcowego raportu jako zakończonych.

Korekta rundy 1: wycofano pomiary kontrastu renderu i ich maski. Narzędzie błędnie odtwarzało anchor z wysokości kamery przesadzanej przez seat=road. Prawidłowa macierz pochodzi teraz z rzeczywistego WorldRegionRoot. Korektę opublikowano robocopy i zweryfikowano SHA 12 plików w main/artifacts/asphalt-r1. Nie odtworzono historycznego pomiaru z obecnych GLB. Obrazy, liczniki, pamięć i wyniki testów r1 pozostają niezależnymi dowodami.
