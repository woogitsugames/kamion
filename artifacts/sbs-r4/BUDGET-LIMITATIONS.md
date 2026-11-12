# Liczniki trasy r4 i granice porównania

Odczytano wszystkie 168 rekordów: 42 kamery × Low/High × clear/overcast. Każdy rekord obejmuje draws statyczne i instancji osobno, a suma zawiera oba składniki. Roster kamer i stanów jest kompletny. Plik kamer ma identyczne SHA w r2, r3 i r4. Źródła logów i ich SHA zapisano w counters-completed.json; pełne tabele są w counters oraz counters-vs-r2, w JSON i CSV.

| Baza porównania | Tier | Wzrost draws | Trójkąty ponad +2% | Zakres zmiany draws | Zakres zmiany trójkątów |
|---|---|---:|---:|---:|---:|
| r3 | Low | 0/84 | 0/84 | 0 | 0…+9 tys. |
| r3 | High | 0/84 | 0/84 | 0 | +1…+19 tys. |
| r2 | Low | 38/84 | 34/84 | −17…+29 | +2…+13 tys. |
| r2 | High | 48/84 | 26/84 | −33…+49 | +5…+21 tys. |

Względem r3 nowy przyrost liczników mieści się w warunku draws +0 i tris ≤+2%. Skumulowane przekroczenia Low względem r2 wzrosły jednak z 22/84 do 34/84 dla trójkątów. Draws przekracza dawną bazę nadal w 38/84 przypadkach. Zestawienie skumulowane zachowuje stałą bazę r2.

Nowe przekroczenia to sześć kamer odcinka G3-B, każda w Low-clear i Low-overcast. Wartości procentowe są przybliżone, obliczone z zaokrąglonych liczników tysiąca trójkątów. [Pełne rekordy i źródłowe powiązanie](new-low-threshold-crossings.json) zachowują także liczby całkowite i sprawdzenie arytmetyki trzech rund.

| Kamera | Przyrost r3→r4 | Skumulowane r3 względem r2 | Skumulowane r4 względem r2 |
|---|---:|---:|---:|
| sbs-g3-b-1528935774382039 | +8 tys. | 0,24% | 2,18% |
| sbs-g3-b-3281350541967811 | +8 tys. | 0,50% | 2,48% |
| sbs-g3-b-381800493259507 | +6 tys. | 1,83% | 3,39% |
| sbs-g3-b-494288258686575 | +3 tys. | 1,65% | 2,64% |
| sbs-g3-b-810896133189484 | +3 tys. | 1,73% | 3,03% |
| sbs-g3-b-962702164479831 | +4 tys. | 0,78% | 2,33% |

Najwyższa suma draws Low wynosi 810 = 445 statycznych + 365 instancji, w A454716 Low-clear. High osiąga 1376 = 945 + 431 w A320215 High-overcast. To estymaty edytora przed batchingiem, a liczby trójkątów są zaokrąglone do tysięcy. Nie służą do pomiaru małych zmian poniżej tej rozdzielczości. Obejmują także kamery C, żeby ich pominięcie nie zaniżyło kosztu; C nadal nie są zaliczanymi parami bramki.

Świat i runtime pochodzą z różnych zintegrowanych baz main. To porównanie kosztu całej sceny, nie izolowany koszt narzędzia SBS ani konkretnej dziedziny. Nie mierzono GPU, p95 klatki ani telefonu A16. Wynik telefonu i całego budżetu pozostaje UNVERIFIED; brak nowego przekroczenia względem r3 nie nadaje mu PASS.

Parsowanie objęło tylko 40 388 bajtów bieżących logów tekstowych i historyczne logi tej samej wielkości. Nie dekodowano obrazów ani siatek i nie uruchamiano generatora lub pytest. Ciężki test core w tym czasie nadal miał swój odrębny bilet FIFO.
