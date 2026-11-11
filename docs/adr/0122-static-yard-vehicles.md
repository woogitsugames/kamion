# ADR 0122 — statyczne pojazdy placowe

Status: r2 w toku; żaden kandydat nie został jeszcze odebrany wizualnie ani scalony do main.

## Runda life r2

Punktem wyjścia jest gpt-life-r1 z dołączonym main 765145c5 w worktree gpt-life. Zakres obejmuje wyłącznie statyczne naczepy i ciągniki oraz ich obecność na placach. Lider Claude S11 jest jedynym integratorem main. Nie zmieniamy rozmieszczenia dróg, budynków, barier ani profili jakości.

Referencje: istniejące lokalne fotografie Krone Tautliner (Jk20301, CC BY-SA 4.0) i WieltonCurtainSider (Cekay, CC0), ze źródłami i ograniczeniami w artifacts/life-r1/refs/YARD-REFERENCES.md. Fotografie potwierdzają trzy oddzielne koła po każdej stronie naczepy, przerwy między nimi, widoczne felgi i zróżnicowanie powierzchni. Logo i oznaczeń handlowych nie przenosimy do gry. Zdjęcia są referencją bryły, nie skalibrowanym pomiarem albedo ani zgodnością miejsca.

Obecny LOD1 naczepy zastępuje trzy koła jednym długim graniastosłupem na stronę. Preflight modelu curtain: 220 trójkątów, 6 grup materiałowych, z tego 24 trójkąty opon; LOD0: 1102 trójkąty, 15 grup. Ciągniki mają osobne koła, ale dalszy LOD pomija widoczne czoła kół. Te miejsca sprawdzimy na zamrożonych kamerach rzeczywistych instancji, obok wszystkich odziedziczonych kontroli trasy.

Kryterium wyboru: poprawa sylwetki i powierzchni na renderze Low/High, clear/overcast względem baseline i zdjęć; bez nowych grup materiałowych/draws na Low, trójkąty na kamerach trasy najwyżej +2%. Zmiany nie mogą przesuwać obrysu kolizji, osi ani punktu podparcia kół. Koszt geometrii prototypu oraz pełny budżet kamer będą raportowane osobno. Limity szacunkowe pojedynczego prototypu nie zastępują pomiaru trasy.

Stan dowodów: skrypt wyboru rzeczywistych instancji i dopisania kamer jest uruchomiony pod kolejką heavy. Baseline renderów r2 oraz pomiary kandydata pozostają do wykonania. Materiały i geometria produkcyjna r2 jeszcze bez zmian. Pełny GIS dopiero na końcu rundy; podczas poprawek pojedyncze pliki testów. Wszystkie zadania ciężkie mają slot heavy gpt-life-r2, każde Unity slot gpt-life.
