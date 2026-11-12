# Liczniki trasy r4 i granice porównania

Odczytano wszystkie 168 rekordów: 42 kamery × Low/High × clear/overcast. Każdy rekord obejmuje draws statyczne i instancji osobno, a suma zawiera oba składniki. Roster kamer i stanów jest kompletny. Plik kamer ma identyczne SHA w r2, r3 i r4. Źródła logów i ich SHA zapisano w counters-completed.json; pełne tabele są w counters oraz counters-vs-r2, w JSON i CSV.

| Baza porównania | Tier | Wzrost draws | Trójkąty ponad +2% | Zakres zmiany draws | Zakres zmiany trójkątów |
|---|---|---:|---:|---:|---:|
| r3 | Low | 0/84 | 0/84 | 0 | 0…+9 tys. |
| r3 | High | 0/84 | 0/84 | 0 | +1…+19 tys. |
| r2 | Low | 38/84 | 34/84 | −17…+29 | +2…+13 tys. |
| r2 | High | 48/84 | 26/84 | −33…+49 | +5…+21 tys. |

Względem r3 nowy przyrost liczników mieści się w warunku draws +0 i tris ≤+2%. Nie oznacza to odzyskania wcześniejszego budżetu: skumulowane przekroczenia Low względem r2 wzrosły z 22/84 do 34/84 dla trójkątów. Draws przekracza dawną bazę nadal w 38/84 przypadkach. Nie zerujemy porównania po każdej rundzie, aby ukryć ten przyrost.

Najwyższa suma draws Low wynosi 810 = 445 statycznych + 365 instancji, w A454716 Low-clear. High osiąga 1376 = 945 + 431 w A320215 High-overcast. To estymaty edytora przed batchingiem, a liczby trójkątów są zaokrąglone do tysięcy. Nie służą do pomiaru małych zmian poniżej tej rozdzielczości. Obejmują także kamery C, żeby ich pominięcie nie zaniżyło kosztu; C nadal nie są zaliczanymi parami bramki.

Świat i runtime pochodzą z różnych zintegrowanych baz main. To porównanie kosztu całej sceny, nie izolowany koszt narzędzia SBS ani konkretnej dziedziny. Nie mierzono GPU, p95 klatki ani telefonu A16. Wynik telefonu i całego budżetu pozostaje UNVERIFIED; brak nowego przekroczenia względem r3 nie nadaje mu PASS.

Parsowanie objęło tylko 40 388 bajtów bieżących logów tekstowych i historyczne logi tej samej wielkości. Nie dekodowano obrazów ani siatek i nie uruchamiano generatora lub pytest. Ciężki test core w tym czasie nadal miał swój odrębny bilet FIFO.
