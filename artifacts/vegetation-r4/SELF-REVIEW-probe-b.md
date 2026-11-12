# Próba B2 — ocena autora

World zakończył się kodem 0 w 534,6 s, import i cztery grupy prób również 0. Autor obejrzał wszystkie osiem arkuszy berberis-review-probe-b: dwa kadry ronda, Low/High clear/overcast, ze zdjęciem Rakoon. Duże ostre załamania góry są ograniczone, a obrys spokojniejszy. Nie powstała widoczna pusta skorupa ani duże otwory na przestrzał. Jednak gładka, prawie jednolita brunatna góra nadal dominuje; drobne listki i pędy skupiają się przy brzegach. Zwykły kadr nadal pokazuje formowaną belkę. B2 nie jest końcową akceptacją realizmu.

Pomiary obejmują 16 wierszy próby, bez pełnej macierzy. Maksymalne delta Low: draws 0, raportowane trisK +0,680272%. Nasadzenia mają 20 347 zamiast 18 402 trójkątów, czyli +1945; procent nasadzeń nie jest procentem kadru. Nie ma pomiaru GPU ani migotania w ruchu.

Sześć z ośmiu kontroli fence_2/remiza jest bajtowo identycznych z baseline. Dwa obrazy High remizy różnią się po sześć pikseli. Autor obejrzał oba arkusze control-diff-High-*.jpg; nie widać zmiany makroskopowej materiałów lub bryły. Położenie różnic i liczby zapisuje probe-b-control-differences.json. Nie nazywamy tych dwóch obrazów identycznymi i nie przypisujemy niepotwierdzonej przyczyny różnic.

Niezmienione są wszystkie 64 pliki instancji, dekodowane wejścia kolizji 64 Low chunków i far field. Jedyną zmianą źródłową jest plantings.py. Testy 33 przypadków przeszły; płaski/nachylony grunt i wspólny podział capów nie są deklaracją pełnej kontroli każdego terenu w scenie. Następny eksperyment musi poprawić pokrywę środka góry, zachowując poprawną topologię B2 i ponownie mierząc koszty.
