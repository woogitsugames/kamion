# ADR 0122 — statyczne pojazdy placowe

Status: r2 w toku; żaden kandydat nie został jeszcze odebrany wizualnie ani scalony do main.

## Runda life r2

Punktem wyjścia jest gpt-life-r1 z dołączonym main 765145c5 w worktree gpt-life. Zakres obejmuje wyłącznie statyczne naczepy i ciągniki oraz ich obecność na placach. Lider Claude S11 jest jedynym integratorem main. Nie zmieniamy rozmieszczenia dróg, budynków, barier ani profili jakości.

Referencje: istniejące lokalne fotografie Krone Tautliner (Jk20301, CC BY-SA 4.0) i WieltonCurtainSider (Cekay, CC0), ze źródłami i ograniczeniami w artifacts/life-r1/refs/YARD-REFERENCES.md. Fotografie potwierdzają trzy oddzielne koła po każdej stronie naczepy, przerwy między nimi, widoczne felgi i zróżnicowanie powierzchni. Logo i oznaczeń handlowych nie przenosimy do gry. Zdjęcia są referencją bryły, nie skalibrowanym pomiarem albedo ani zgodnością miejsca.

Obecny LOD1 naczepy zastępuje trzy koła jednym długim graniastosłupem na stronę. Preflight modelu curtain: 220 trójkątów, 6 grup materiałowych, z tego 24 trójkąty opon; LOD0: 1102 trójkąty, 15 grup. Ciągniki mają osobne koła, ale dalszy LOD pomija widoczne czoła kół. Te miejsca sprawdzimy na zamrożonych kamerach rzeczywistych instancji, obok wszystkich odziedziczonych kontroli trasy.

Kryterium wyboru: poprawa sylwetki i powierzchni na renderze Low/High, clear/overcast względem baseline i zdjęć; bez nowych grup materiałowych/draws na Low, trójkąty na kamerach trasy najwyżej +2%. Zmiany nie mogą przesuwać obrysu kolizji, osi ani punktu podparcia kół. Koszt geometrii prototypu oraz pełny budżet kamer będą raportowane osobno. Limity szacunkowe pojedynczego prototypu nie zastępują pomiaru trasy.

Stan dowodów: finalny baseline ma 456 PNG, po 114 kamer Low/High × clear/overcast, z High na WorldC_High. Pierwsze zasłonięte kadry zachowano w before-rejected-v1; komplet v2 w before-v2. Finalne kamery obejmują 20 widoków pięciu rzeczywistych pojazdów i dwa dodatkowe czytelne widoki ciągników z 22 m. Obejrzano wszystkie 20 kadrów placu Low/clear i oba dodatkowe; dwa stare dalekie widoki ciągników nie stanowią dowodu ich LOD. Audyt baseline importuje zamrożone baseline-life_props.py. Regresje test_yard_vehicle_lod.py: 5 passed. Regeneracja kandydata jest w toku; import, AFTER i pełny budżet kamer pozostają do wykonania. Pełny GIS dopiero na końcu rundy; podczas poprawek pojedyncze pliki testów. Wszystkie zadania ciężkie mają slot heavy gpt-life-r2, każde Unity slot gpt-life.

## Wynik audytu kandydata r2

Baseline i kandydat przeszły audyt pod heavy. LOD1: firanka 220→316 trójkątów (6→6 grup), box 180→276 (5→5), chłodnia 194→290 (7→7), ciągnik 254→286 (7→7). Wszystkie hashe siatek kolizji oraz zestawy materiałów obu LOD są identyczne. LOD0 nie otrzymał nowej geometrii. Opony LOD1 naczepy miały 0,12 m przerwy nad gruntem, ciągnika około 0,0683 m; kandydat ma 0 m. Audyt potwierdza trzy rozdzielone osie po obu stronach naczepy oraz UV plandeki wewnątrz kafla 2,7 m.

Historyczny limit pojedynczej naczepy LOD1 w test_streetscape wynosił 250 trójkątów. Dla sześciu oddzielnych zamkniętych kół przyjęto limit 320 (zmierzony maksymalny koszt 316); nie zmieniamy ograniczenia kamery trasy: draws +0 i łączne trójkąty najwyżej +2%. Nowy limit prototypu nie stanowi odbioru wydajności. Warunkiem przyjęcia pozostaje pełne porównanie 114 kamer × cztery warunki i oględziny AFTER. UV dają warianty istniejącego nalotu, nie pełną symulację brudu ani niezależne tekstury każdej instancji.

## Korekta diagnozy UV (przed drugą iteracją)

Sprawdzenie natywnego M_trailer_curtain_grey wykazało _Tile 4×4 m. Wcześniejsza hipoteza o zawijaniu wysokości 2,75 m przy kaflu 2,7 m była błędna: samo tile_m w specyfikacji nie jest stosowane bez set_tile, atlas lub elementScan. Aktualny kandydat A nadal używa 4 m. Audyt wartości UV nie dowodzi jeszcze fizycznej skali tekstury ani naprawy zawijania. Odpowiedni dowód: tile-baseline-proof.json. Po oględzinach A przewidziany jest osobny, ograniczony opt-in set_tile dla plandek; żadna taka zmiana nie została jeszcze wykonana. Nie zmieniamy globalnej zasady wyboru _Tile.

## Weryfikacja kosztu A i plan materiałów B

Seria AFTER A ma 456 PNG. Wszystkie cztery warunki zachowują liczbę grup/draws; zaokrąglone statystyki przekraczają jednak limit Low w r10_hall_3 (+2,0408%). Nie podnosimy limitu. Opt-in Editor LifeExactStats zapisuje całkowite liczby z natywnego importu, a walidator wymaga zgodności 114 wierszy na warunek z dotychczasowym loggerem. Wszystkie 456 odczytów A przeszły tę kontrolę. Świat zachowuje frustum wspólnego SceneStats po przywróceniu targetu (aspect 4:3); instancje pochodzą z właściwego renderu 2340×1080. To porównanie CPU przed SRP batching, nie pomiar GPU. Prawdziwy baseline dokładny będzie ponownie zaimportowany z biblioteki o SHA c56cbe59b99b61d8cf15c605c6b0b78697c45e76af8bdaea404de7f5602d3cfd; surowy świat i rozmieszczenie pozostają identyczne. Przełączenie biblioteki jest jawnie zapisane w SOURCE-MODE.json i zawsze przywraca źródło kandydata w finally. Przywrócenie GLB nie oznacza przywrócenia natywnych scen bez kolejnego importu.

Obejrzane plansze A: całe 22 widoki placowe Low/clear oraz próbki Low/overcast i High/clear/overcast. Poprawa jest wyraźna na dalszym LOD Low: osobne osie i zamknięte czoła opon zamiast długiego bloku/otworów. LOD0 geometrii nie zmieniono, więc bliskie płaskie felgi i czyste kabiny pozostały. Czerwone plandeki są ciemne, a sam poziomy offset UV nie daje wystarczającej różnorodności. Nie ogłaszamy PASS jakości.

Plan B (jeszcze niewykonany): opt-in danych yard_paint tylko dla sześciu tractor_paint_* z istniejącym car_grime_clean i payloadem UV1 od rzeczywistego dołu kabiny 1,05 m. Istniejący _CARPAINT ma obsłużyć statyczne kabiny bez nowego przebiegu, tekstury ani keywordu; _CarFlake.w=2 wyłączy odtwarzanie historycznego nalotu dachu osobówek, zachowując ich w=1 bez zmiany. Pozostałe materiały nie dostaną tej ścieżki. Dla sześciu plandek set_tile=true włączy rzeczywisty kafel 4,8×2,7 m, zgodnie z globalnym kontraktem _Tile. To addytywne wyjątki w plikach wspólnych zgodne z pkt 10 protokołu; wymagają testu zachowania UV1 w imporcie i natywnego dowodu materiału. Geometrię A pozostawimy tylko jeśli dokładny budżet trasy spełni 2%; inaczej odchudzimy zasłonięte powierzchnie LOD1 i powtórzymy pomiar.
