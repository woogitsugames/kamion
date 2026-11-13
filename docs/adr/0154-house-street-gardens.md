# ADR 0154 — zieleń ulic domów

Status: WIP — iteracja A spełnia budżet, wizualnie PARTIAL; trwa korekta B. Gałąź `gpt-s16-r2`.
Baza: r1 `eb718b7f8` + `origin/main` `5cca3a2f5`, merge `250f9e7b9`.

## Problem i źródła

ADR 0132 pozostawia D51 PARTIAL: pozycje koron z ortofoto są dostępne, ale korony prototypów są cienkie i rzadkie. W istniejącym planie jest 99 posesji, 479 m żywopłotów oraz 116 drzew ogrodowych po deduplikacji. Nie należy dodawać drzew do każdego nowego trawnika tylko dla uzyskania gęstego kadru.
Zdjęcia P07/P08/P10/P12/P14/P17 z repo pokazują różne typy ulic: stare domy z koronami nad dachami, żywopłoty za płotem i nowsze posesje z mniejszą ilością zieleni. SHA256, autorzy i licencje są w `artifacts/gpt-s16-r2/reference-provenance.json`. Zdjęcia są wyłącznie referencją; ich piksele nie trafiają do gry.
Repo dokumentuje brak zdjęć bocznych ulic regionu. Zestaw sześciu ulic — Skidelska, Racławicka, Grodzieńska, Wileńska, Olsztyńska, Michała Motoszko — ma prawdziwe osie OSM i fronty posesji, ale pary ze zdjęciem są **typologiczne**, nie zgodne lokalizacją lub pozą. Kamery, FOV i wysokość są WORKING_VALUE. Nie użyto Google.

## Rozwiązanie

`vegetation.garden_canopies` zachowuje liczbę, pozycje, prototypy, warianty i tier drzew. Poszerza istniejące korony liściaste high: klon/lipa ×1,35, brzoza ×1,20, sosny bez zmiany. To WORKING_VALUE z typologii P07/P08/P12, nie pomiar wymiarów konkretnego drzewa. Iteracja A używała LoD1 pierwszego domu +3,5 m; nie uwzględniała wyższej kalenicy ani pozostałych domów grupy. Po recenzji B odczytuje maksymalny Z istniejącej geometrii pobliskich domów (do 25 m od pnia), a wysokość korony odnosi do tego poziomu +4,5 m. Margines i limity dojrzałych drzew (brzoza 23 m, lipa 24 m, klon 22 m) są WORKING_VALUE z proporcji zdjęć. Nie zmienia pozycji pni ani nie skraca istniejących wyższych drzew. Geometria domów pozostaje tylko źródłem odczytu.
Importer addytywnie odczytuje jawne `garden_canopy_width` wyłącznie dla drzew high. Skaluje oba poziome osie istniejącej macierzy; wysokość, początek, pochylenie, yaw i kompaktowy TRS są zachowane. Brak pola, zła wartość lub rekord nie-high daje dokładnie starą macierz. Istniejący shader obsługuje transformację normalnych oraz billboard po obu osiach poziomych; nie dodano shadera, materiału lub przebiegu.
`plantings.front_gardens` uzupełnia część dotychczas nieobsadzonych, przeziernych frontów. Czyta helpery `plots.py` bez edycji tego pliku. Korzysta z istniejącego `plot_kit` i warstw `plots`/`plots_low`, zachowuje bramy, furtki, podjazdy, dojścia i domy jako keepouty. Kandydat odpada, jeśli tworzyłby nową grupę chunk/layer/material lub rozszerzał jej dotychczasowe obwiednie.
Dodatkowa proporcja frontów 0,70 wśród kandydatów, odsunięcie 0,80 m, grubość 0,65 m oraz wysokość płotu +0,20…0,45 m (1,2…2,0 m) są WORKING_VALUE. Globalny limit nowej geometrii Low wynosi 3600 tris; rzeczywisty limit kadru +2% jest osobno sprawdzany na każdej kamerze. Istniejące hedges OSM/BDOT nadal obsługuje dotychczasowa ścieżka; nowych frontów nie przedstawia się jako zinwentaryzowanych nasadzeń.
Dwa wywołania w `stage.py` podłączają nowe funkcje. Nie edytowano dróg, overrides, modeli domów, płotów, bram ani ich kolizji. Własne pliki robocze szkiców/prototypu usunięto po przeniesieniu kodu do źródeł i testów.

## Weryfikacja

Baseline generator 597,2 s bez fallback, import Low/High, 90 kamer × clear/overcast × Low/High. Autor obejrzał 12 ujęć ulic i lokalne arkusze zdjęć. Każdy stan ma te same kamery. 2151 chronionych węzłów, 32 grupy posesji i rekordy instancji nie-high zapisano do porównania semantycznych hashy, bez dodatkowej kopii całego świata.
7 nowych testów GIS przechodzi: brama pozostaje otwarta, stare części niezmienione, bufory deterministyczne, limit geometrii twardy, brak nowej grupy rendererów, niezmienione Low/las i brak skracania dojrzałych drzew. Celowany EditMode transformacji: 8/8. Dodano test integracji danych z natywnym WorldInstanceSet; czeka na import B. Wykryty w nim błąd dostępu do prywatnego Compact poprawiono na kontrolę publicznych tablic zapisu.
Otwarte: generator after, audyt chronionych buforów i materiałów, render/oględziny wszystkich par, Low draws +0 i tris ≤+2%, niezależna recenzja, pełny GIS/EditMode. SceneStats to estymata CPU z tris uciętymi do tysięcy, nie pomiar GPU. Telefon, ASTC i przejazd pozostają u lidera.

## Iteracja wizualna i powtórzenie baseline

A: 19 posesji, 34 odcinki, 257,37 m, +3580 tris na każdy wariant kitu; 104 korony poszerzone. Audyt: 2151 chronionych węzłów, 125450 rekordów nie-high, 6 bibliotek/atlasów i 458 materiałów natywnych identycznych; 32 grupy plots zachowane. Wszystkie 90 kamer Low mają delta draws 0, konserwatywny przyrost tris maks. +1,667%. Recenzent mimo tego dał PARTIAL, ponieważ poprawa czytelności ulic w pierwotnych szerokich kadrach była mała; zachowano `iteration-a/`.
B: 12 kadrów dobrano z prawdziwych osi ulic w odległości 28–45 m od istniejących koron, FOV 50; grupy domów bez pełnej bramy też są uwzględnione. Nie traktuje się zmiany kadru jako poprawy produktu. Nowe before/after mają te same pozycje. Powtórzono generator z `KAMION_GARDENS_0154=0` (domyślnie funkcja jest włączona), aby odtworzyć bazę bez nowych frontów i zmian koron. Audyt potwierdził zgodność z pierwszą bazą chronionych siatek, grup/tris posesji oraz wszystkich rekordów Low i drzew ogrodowych. Nie tworzono dodatkowej kopii całego świata.
Diagnostyka VQA addytywnie raportuje `trisExact` oraz `trianglesExact`, bez zmiany renderu. Końcowe +2% będzie liczone na dokładnych całkowitych liczbach CPU, nie różnicy zaokrąglonych tysięcy. Nadal nie jest to pomiar GPU ani telefonu.
