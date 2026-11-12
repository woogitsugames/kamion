# Próba B po odrzuceniu A

A zostaje zachowany w snapshot-candidate-a, probe-a, porównaniach i ocenie krytyka; nie jest wersją zaakceptowaną. Nie wykonywać pełnej macierzy ani końcowego GIS dla A jako udanej zmiany.

Najpierw ustalić liczbę istniejących wewnętrznych wierzchołków cap i ich rozstaw w czterech prawdziwych obrysach. Eksperyment ograniczyć do berberysu przez dane SPECIES. Sprawdzić niewielki relief na istniejących wierzchołkach góry: skala roślin, ciągłość brzegu i boków, żadnego nowego trójkąta, żadnej zmiany pozostałych gatunków. Amplituda to WORKING_VALUE do oglądania, nie pomiar zdjęcia. Zachować gęstą masę i uniknąć dawnych dużych zaokrąglonych „kiełbas”. Warstwa wewnętrzna ma pozostać niżej od rzeczywiście triangulowanego shell; test nie może opierać się jedynie na globalnej wysokości.

Nie zmieniać tekstur A ani innych materiałów w tym samym eksperymencie. Zachować jawny wariant referencyjny bez reliefu do porównania geometrii, budżetu i pozostałych rodzin. Testy celowane przez heavy, potem World i dekodowanie kolizji w tym samym slocie; lekką migawkę i porównania stdlib wykonać poza heavy. Bez powtórki materiałów. Potem import i nowy tag probe-b, te same kamery i warunki. Pełna macierz oraz końcowy GIS/EditMode dopiero po obiecującej próbie i niezależnej ocenie. Nie zmieniać plików roads, stage, override, importerów, WorldInstances ani make_trees.

## Korekta po pomiarze obrysów

cap-study-a.json ujawnił, że wszystkie osiem obrysów cap jest samoprzecinających. Dlatego _delaunay_fill poprawnie odmawia, a awaryjne ear_clip daje wyłącznie punkty brzegu i krawędzie długości 16–20 m. Brak wewnętrznych punktów oznacza też brak przewidzianych w istniejącym kodzie pędów na górze. Przesuwanie samych wysokości nie usuwa tej przyczyny.

B najpierw naprawi w posiadanym plantings.py sposób tworzenia ringów berberysu: prawidłowe obrysy odsunięte od footprint, spójna kolejność punktów między warstwami, bez samoprzecięć. Nie zmieniać helpera roads ani danych obrysu. Pozwolić istniejącemu _fill(0.6) utworzyć przewidziane wewnętrzne punkty; potem ocenić dotychczasowy relief i pędy, zanim dojdą nowe pola wysokości. Zachować wariant referencyjny A i inne gatunki bez zmian. Deklaracja „zero nowych trójkątów” z pierwszego planu zostaje wycofana na podstawie nowych dowodów: wymaganiem właściciela jest +0 draws i ≤+2% tris na wszystkich kamerach Low. Ewentualny koszt przywróconej poprawnej triangulacji musi być jawnie zmierzony, a nie ukryty jako brak zmiany budżetu.

## B — formalna porażka loftu i następna poprawka

Sekwencja 73347 otrzymała heavy i zakończyła się 8 failed, 19 passed w 4,16 s. Wszystkie osiem nowych przypadków wykazało skrzyżowane quady pasa. World nie uruchomiono; slot został zwolniony. Poprawne osobne capy nie wystarczają. Lekka diagnostyka znalazła 5/8/8/6 niepoprawnych quadów w E1/E2/A/C oraz niewielkie naruszenia zagnieżdżenia kolejnych przekrojów. Nie osłabiać testów, żeby uznać ten loft za poprawny.

Krytyk zaleca kolejną poprawkę w tej rundzie: niezależne dokładne offsety z zachowaniem narożników i segmentowaniem długości, bez wymogu identycznej liczby punktów. Na początek bez bulge XY wyłącznie w nowej ścieżce; zachować wysokości i istniejące pędy. Między zagnieżdżonymi obrysami triangulować rzeczywisty annulus z otworem lokalnym Shapely CDT. Nie zmieniać roads, nie usuwać trójkątów według samego centroidu, nie używać buffer(0) ani nie wybierać największego fragmentu. Wysokości granic przypisać przed triangulacją i odzyskać dokładne granice. UV mierzyć po rzeczywistym obwodzie; rozdzielić szew w trójkątach, bez rozciągania ostatniego odcinka.

Nowa reprezentacja pasów wymaga dostosowania testu do faktycznych trójkątów zamiast indeksowanych quadów: poprawność całego annulus, zgodność sumy pól i union, brak wyjścia poza pas i nakładania, odzyskane obie granice, dodatnie pola, zgodne normalne i brak szczelin. Nadal wymagane core wewnątrz shell w XY i rzeczywisty prześwit Z. Nie ma jeszcze tej poprawki w produkcji; aktualny B jest odrzucony przed World.
