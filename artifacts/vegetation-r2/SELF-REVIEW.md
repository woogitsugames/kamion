# Samokrytyka ADR0088 — stan po pełnej macierzy

Obejrzano wszystkie 472 źródłowe kadry przed/po poprzez 40 kontaktów <=960px (59 kamer × Low/High × clear/overcast), dodatkowo pełne kadry DK8, Andersa, Putry i fence1/2 <=960px oraz rzeczywistą galerię LOD. Kontakty służą przeglądowi całej sceny; nie zastępują oceny pojedynczego piksela w natywnej rozdzielczości. Porównanie ma ten sam pojazd i fixture przed/po. Dopiero po zakończeniu macierzy odtworzono canonical fixture pojazdu do testów EditMode; te późniejsze sceny nie są źródłem liczb macierzy.

| Ocena | Miejsce | Dowód / ograniczenie |
|---|---|---|
| PASS | DK8, Low/High overcast | Zamiast zwartej czarnej czapy widać oddzielne konary i niebo między nimi. Las nadal czyta się jako gęsty pas drzew; nie stał się rzędem samotnych patyków. Low p10/p50 18,64/31,15→32,72/43,36; High21,50/34,79→35,86/46,79. <16:5,43→0% /0,86→0,087%. |
| PASS ograniczony | Andersa / Putry | Zachowane pierwotne palety liściastych, brak globalnej zmiany ekspozycji. Overcast p50 Andersa Low67,50→69,29,High73,29→74,58; PutryLow63,99→72,20,High73,49→83,06. Nie widać neonu; zmiana Putry jest większa niż Andersa i należy ją zachować jako punkt kontroli po scaleniu A/C. |
| PASS | Trawa fence1/2, hale, pobocza | Znikła stała jasnobeżowa obwódka trawników. Suchsze miejsca pozostają przy klasach odsłoniętego/niekoszonego gruntu, mają łagodne plamy zamiast jednego pasa przy każdej krawędzi. Brak nowej geometrii lub materiałów. |
| PASS ograniczony | LOD0/1/billboard2 | Galeria faktycznej geometrii pokazuje prześwity także w LOD1; billboard2 jest bake LOD0. Wszystkie18wariantów LOD0/1 mają <= bazowych trójkątów. Nie dodano czwartego pasma runtime. Statyczne kadry nie dowodzą braku temporalnego poppingu podczas jazdy. |
| P2, pozostaje | Lipa / pojedyncze drzewa przy Putry | Korona jest nadal stylizowanym zbiorem skupisk, częściowo jednostronnym. Gałęzie są rozmieszczone mniej piętrowo, lecz nie należy nazywać tego fotorealistycznym rozpoznawalnym pokrojem każdego gatunku. |
| P2, pozostaje | Trawa i żywopłoty z bliska | Brak osobnych źdźbeł w całym terenie; przy małej odległości widać materiał powierzchniowy. Żywopłot nadal używa niskobudżetowej siatki z nierówną górą, nie pełnych liści 3D. Fab boxwood/elderberry zachowują istniejącą sylwetkę skanów. |
| PASS | Budżet | Każde236porównań ma dokładnie0delta draws. Low trisdelta -8..0k,High -8..+1k (max+0,074%). Peak Low1016draw/482ktris iHigh1756draw/2471ktris bez zmiany. To estymata static + rzeczywiste instanced według istniejącego runnera, nie pomiar GPU A16. |

Zdjęcia referencyjne: photo-crown-rois.jpg i photo-crown-metrics.json (jawne ROI, SHA). Korony zdjęć mają p10 około30–36 i p50 47–65; zachmurzenie mieszane, sezon i ekspozycja nie są identyczne z grą. Dane uzasadniają usunięcie dominującej czerni, nie udają dokładnego pomiaru albedo z fotografii. Nie zmieniono globalnego światła, postprocessu, Tint ani skyboxu.

Dodatkowa weryfikacja Fab: właściwe pole raportu to furniture.megascans. Świat ma15 dostępnych zatwierdzonych źródeł,320dodatkowych props,954podmian odpływów; fallback nie jest True. Fab wood działa wyłącznie w near importerze, nie w publicznych bake drzew. Wczesne podejrzenie braku wywołania integracji wynikało z niepełnego wyszukiwania; zostało sprostowane i nie doprowadziło do zmiany kodu.

Recenzja lidera po r2: **P1 pozostaje — sosnowe karty na DK8 czytają się jako płaskie odłączone wyspy**. Liczby jasności i budżet PASS nie oznaczają zatem końcowego wizualnego PASS. Trwa ograniczona próba czystej gałązki z igłami CC0 pine_tree_01 w tym samym materiale/512px/liczbie kart. Near-only próba nie obejmuje jeszcze wymiany starych HLOD/billboardów i nie może sama zamknąć uwagi.

Końcowe GIS/EditMode oraz ponowna niezależna recenzja lidera: w toku. Oceny powyżej dotyczą obejrzanego r2 i zmierzonych statystyk, nie oznaczają jeszcze pełnego DoD.
