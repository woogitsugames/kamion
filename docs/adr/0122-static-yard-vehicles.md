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
