# Pilna korekta po recenzji s12, przed zamknięciem r3

Źródło: docs/reports/visual/REVIEW-2026-11-12-s12-gpt-batch-a.md, sekcja2,
oraz docs/owner/GPT-FEEDBACK-S10.md sekcja s12 (09:53), odczytane z main.
Lider scalił r2 po ręcznej unii materials.py. Ocena PARTIAL; nie jest to PASS fotografii.
P1: fazy filarów mają tę samą musztardową farbę, nie goły szary beton;
pigment r2 poszedł zbyt mocno w brąz. P2: ciemny równoległobok w połowie wysokości.
Rura pod krawędzią pomostu nadal wymaga sprawdzenia widoczności i położenia.

Aktualna kolejka r3 uzyskała slot tuż przed próbą anulowania oczekiwania.
Kontrola tożsamości nie pozwoliła zatrzymać nieistniejącego już waitera58232;
żadnego procesu nie zatrzymano. Jednostki EC15 PASS/1 deselected, generator działa.
Nie zmieniać jego źródeł podczas przebiegu. Najpierw zachować izolowany wynik EC,
potem kolejny wariant r3 z korektą P1/P2 pod własnym heavy.

Plan korekty: unpainted_chamfers=false, pigment wraca do roboczego
[0.46,0.40,0.17] sprzed brązowej korekty r2, paint_blobs=false.
Zachować brak schodów, teksturę stopy i miękkie zacieki, bez wymiarów pomostów/ekranów.
Dodać pojedynczy test domyślnego pełnego malowania faz i braku abstrakcyjnej plamy.
Opcjonalny test API gołych faz zostaje jako kontrola zachowania interfejsu,
ale produkcyjna konfiguracja nie będzie tego włączać.

Source hero_bridge.py: w _apply_underdeck (około575) paint_blobs emituje
bridge_soffit :paint_WORKING_VALUE, jeden ukośny quad przy z~ground+0.85 m,
dla co trzeciego filara. To kandydat na zgłoszony równoległobok; sprawdzić render,
nie nazywać diagnozy potwierdzoną przed porównaniem PNG.
Rura collector/downpipe jest już emitowana (około585); nie dodawać drugiej w ciemno.

Audyt EC pierwszego wariantu: wszystkie128 meshy chunków powinny być identyczne.
Po korekcie filarów nie powtarzać tej deklaracji: porównać wszystkie niezmieniane
prymitywy poza materiałami podpomostu, deck V/T/UV/COL, roads_qa i wszystkie
instancje poza dwoma EC. Raport końcowy jasno rozdzieli dowody obu wariantów.

Parametry modelu EC pochodzą z otwartego zdjęcia Commons CC BY3.0 i OSM oraz
faktów technicznych ENEA. Fotografia wykonawcy EMKA nie jest otwartą referencją
D43 ani materiałem do dystrybucji; używać wyłącznie tekstowej informacji H120m.
Przy kolejnej edycji konfiguracji doprecyzować pole źródła, bez twierdzenia o licencji zdjęcia.
