# ADR 0088: Roślinność r2

Status: WIP — pomiary świata i recenzja końcowa w toku.

## Problem

S9 pokazało zwarte ciemne korony DK8, powtarzalną beżową obwódkę trawy i geometryczne żywopłoty. Baseline odtworzono ze źródeł 4f7da66c, następnie zaimportowano; 192 pliki raw odpowiadały manifestowi. Porównanie obejmuje po 59 identycznych kamer dla WorldC/Low i WorldC_High/High, clear/overcast. Materiałowy tier importu obu scen: Medium (512).

## Decyzja

Zachowujemy istniejący kontrakt trzech pasm runtime: geometryczne LOD0 i LOD1 oraz billboard LOD2. Nie dodajemy czwartego pasma ani nie przedstawiamy nieużywanej geometrii jako aktywnego LOD. LOD1 wybiera stabilny, ograniczony liczbowo podzbiór kart LOD0. Prześwity wynikają ze spójnych okien gałęzi, nie losowego usuwania pikseli. Sosna ma głębszą koronę i boczne konary; liściaste ciągłe miejsca osadzenia gałęzi zamiast powtarzanych poziomych pięter. Geometria i liczba submeshy pozostają pod kontrolą metadanych i statystyk świata.

Near bark brzozy/lipy korzysta z istniejącego importera zatwierdzonych Fab: silver-birch-bark, birch-tree-trunk, linden-branch. Nie tworzymy liści ze skanu drewna. Zatwierdzenie Fab i hash źródła pozostają wymagane. Kora sosny pochodzi z pine_bark, Poly Haven CC0, z istniejącego cc0_manifest i kontrolą SHA256; brak źródła zachowuje proceduralny fallback. Publiczne GLB, impostory i HLOD zawierają nasze liście/proceduralną korę liściastych oraz korę i eksperymentalne igły sosny CC0. Fab pozostaje ignorowanym near override, nigdy wejściem do publicznego bake.

Po r2 recenzja wykazała płaskie wyspy kart sosnowych mimo poprawy jasności. W ograniczonej próbie zastępujemy wyłącznie RGBA sosny czystym wycinkiem gałązki z igłami z Poly Haven pine_tree_01 (CC0). Manifest pine_needles_manifest.json przypina SHA256/MD5, crop i autorów. Procesor odrzuca padding/szyszki atlasu, składa3gałązki na512px i zachowuje zmierzoną średnią luminancję pokrytych texeli r2 (0,0638625 liniowo). Nie dodaje trójkątów ani materiałów. Przy braku/podmianie raw wraca proceduralna sosna; pochodne CC0 mogą być publiczne. Akceptacja tej próby wymaga pełnego bake impostor/HLOD i tych samych kamer, nie samego swatcha.

Korekcja canopy scattering dotyczy sosny oraz iglastego/mieszanego HLOD. Nie zmienia światła, ekspozycji, emisji ani globalnego Tint. Bazowe palety liściastych zachowano: zdrowe korony Andersa/Putry są granicami regresji. Wartości lokalnego rozpraszania i otwarć korony są WORKING_VALUE, nie pomiarem parametrów optycznych konkretnego gatunku.

Maska podłoża zachowuje R odległości i G lasu. B zawiera łagodne pole suchszych obszarów w skali 6m, silniejsze poza koszonymi klasami. A różnicuje istniejące klasy odsłoniętego podłoża polem 3,5m. Pola są zakotwiczone we współrzędnych świata, bez szwów chunków. Nie udajemy zinwentaryzowanych ścieżek. Grit przy krawędzi wymaga kontekstu odsłoniętego/dry podłoża i ma zmienną szerokość 8–55cm, zamiast jednolitej obwódki wszystkich trawników. Żywopłoty wykorzystują istniejące siatki/materiały z nierówną górą i przerwami roślin; boki strzyżonego berberysu pozostają proste.

## Pomiar i ograniczenia

vegetation_metrics.py liczy p10/p50 jasności Rec709 na sRGB8 w jawnych ROI po zmniejszeniu do <=960px. Maska odrzuca niebo i brązowe podłoże, ale zatrzymuje piksele <16, aby nie usuwać problematycznej czerni z pomiaru. Te same ROI/maska obowiązują przed i po. Baseline DK8 Low: p10/p50 18,64/31,15, 5,43%<16; High:21,50/34,79,0,86%. Zdrowe Andersa/Putry mają p50 około64–73.

Zdjęcia referencyjne z Mapillary są wyłącznie materiałem QA, nie źródłem tekstur. photo-crown-metrics.json zawiera ścieżki, SHA i ROI; p10 około30–36,p50 47–65. Różne ekspozycje, zachmurzenie, sezon i gatunki wykluczają traktowanie tych wartości jako dokładnego celu kalibracji. Podgląd sylwetek nie dowodzi jakości końcowego oświetlenia ani gęstości z kamery kierowcy. Końcowe statystyki, pomiary po i otwarte ograniczenia: artifacts/vegetation-r2/REPORT.md.
