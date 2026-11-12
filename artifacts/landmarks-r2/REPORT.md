Gałąź gpt-landmarks-r2; zweryfikowany checkpoint 73170057, baza main 2c3939b2.
Usunięto 69 stopni czterech niepotwierdzonych biegów schodów; stary spec nie może ich ponownie włączyć.
Filary mają cieplejszą ochrę, szare fazy oraz brud przy stopie i zacieki sterowane własnymi flagami danych.
Generator: o 906 trójkątów mniej. Geometria pomostów i roads_qa są identyczne z baseline.
Obejrzano 232 pary przed/po na 32 arkuszach: Low/High, clear/overcast, po 58 kamer; 116 obrazów identycznych pikselowo.
Low, wszystkie 116 par: maksymalna delta mesh draws 0 i instance draws 0; suma tris od -0,4202% do 0%. To estymacja sceny, nie pomiar GPU.
Stały ROI ochry Low-overcast: RGB 84/79/47 → 85/71/41; odchylenie Y 3,377 → 4,880. Y przy stopie 63,114 → 54,746; clear ma inne oświetlenie.
Para zdjęcie/render ≤960 px: review/photo-after-weather/Low-overcast-dk8-ref7204.jpg; analogiczna High-overcast w tym samym katalogu.
Zdjęcie Rakoon 7204, CC0, źródło i kadrowanie w metadanych. Poza kamery pozostaje UNVERIFIED; nie jest pomiarem konstrukcyjnym.
Testy: 14 celowanych PASS; pełny GIS 585 PASS i 1 XFAIL; EditMode 295/295 PASS.
Physics/gate3: 47 PASS i znana porażka test_generator_reproduces_committed_scenarios dla top_speed_flat_comb.json.
Cztery wejścia tej porażki są identyczne z bazą; dowód w known-physics-failure-proof.json. Nie zmieniano fizyki.
Wszystkie 192 pliki runtime zgodne z manifestem przed i po testach; cache i źródła nie zmieniły się po renderze.
Generator końcowy trwał 1226 s, w tym obserwowana pauza watchdoga 769 s; wynik nie jest benchmarkiem CPU.
materials.py rozszerzono addytywnie za flagami podpomostu. Bez zmian shaderów i QualityProfile; oba istniejące shadery mają te same trzy przebiegi.
Otwarte: delikatne zacieki i zbyt czyste głowice/spód, wymiary robocze, niepewna poza, rozbieżność ekranów należących do Claude, koszt GPU A16 bez pomiaru.
Konflikty: hero_bridge.py tylko pod pomostem, materials.py unia addytywna; wygenerowany konflikt przy merge przyjęto z main i odtworzono generatorem.
ADR 0119 i SELF_REVIEW opisują ograniczenia. Bez scalenia do main, pushu i telefonu; następna runda dotyczy kominów.
