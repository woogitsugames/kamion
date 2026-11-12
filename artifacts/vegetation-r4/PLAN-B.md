# Próba B po odrzuceniu A

A zostaje zachowany w snapshot-candidate-a, probe-a, porównaniach i ocenie krytyka; nie jest wersją zaakceptowaną. Nie wykonywać pełnej macierzy ani końcowego GIS dla A jako udanej zmiany.

Najpierw ustalić liczbę istniejących wewnętrznych wierzchołków cap i ich rozstaw w czterech prawdziwych obrysach. Eksperyment ograniczyć do berberysu przez dane SPECIES. Sprawdzić niewielki relief na istniejących wierzchołkach góry: skala roślin, ciągłość brzegu i boków, żadnego nowego trójkąta, żadnej zmiany pozostałych gatunków. Amplituda to WORKING_VALUE do oglądania, nie pomiar zdjęcia. Zachować gęstą masę i uniknąć dawnych dużych zaokrąglonych „kiełbas”. Warstwa wewnętrzna ma pozostać niżej od rzeczywiście triangulowanego shell; test nie może opierać się jedynie na globalnej wysokości.

Nie zmieniać tekstur A ani innych materiałów w tym samym eksperymencie. Zachować jawny wariant referencyjny bez reliefu do porównania geometrii, budżetu i pozostałych rodzin. Testy celowane przez heavy, potem World i dekodowanie kolizji w tym samym slocie; lekką migawkę i porównania stdlib wykonać poza heavy. Bez powtórki materiałów. Potem import i nowy tag probe-b, te same kamery i warunki. Pełna macierz oraz końcowy GIS/EditMode dopiero po obiecującej próbie i niezależnej ocenie. Nie zmieniać plików roads, stage, override, importerów, WorldInstances ani make_trees.

## Korekta po pomiarze obrysów

cap-study-a.json ujawnił, że wszystkie osiem obrysów cap jest samoprzecinających. Dlatego _delaunay_fill poprawnie odmawia, a awaryjne ear_clip daje wyłącznie punkty brzegu i krawędzie długości 16–20 m. Brak wewnętrznych punktów oznacza też brak przewidzianych w istniejącym kodzie pędów na górze. Przesuwanie samych wysokości nie usuwa tej przyczyny.

B najpierw naprawi w posiadanym plantings.py sposób tworzenia ringów berberysu: prawidłowe obrysy odsunięte od footprint, spójna kolejność punktów między warstwami, bez samoprzecięć. Nie zmieniać helpera roads ani danych obrysu. Pozwolić istniejącemu _fill(0.6) utworzyć przewidziane wewnętrzne punkty; potem ocenić dotychczasowy relief i pędy, zanim dojdą nowe pola wysokości. Zachować wariant referencyjny A i inne gatunki bez zmian. Deklaracja „zero nowych trójkątów” z pierwszego planu zostaje wycofana na podstawie nowych dowodów: wymaganiem właściciela jest +0 draws i ≤+2% tris na wszystkich kamerach Low. Ewentualny koszt przywróconej poprawnej triangulacji musi być jawnie zmierzony, a nie ukryty jako brak zmiany budżetu.
