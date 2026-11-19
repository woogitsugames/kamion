## Szwy — podsumowanie

| para | szew | dróg | na trasie | FAIL | UWAGA |
|---|---|---|---|---|---|
| bialystok-industrial-c / bialystok-wygoda | x = 779019 | 4 | 0 | 0 | 1 |
| bialystok-wygoda / bialystok-bojary | y = 595199 | 23 | 0 | 2 | 8 |
| bialystok-bojary / bialystok-mickiewicza | y = 593151 | 14 | 0 | 2 | 2 |
| bialystok-mickiewicza / bialystok-dojlidy | y = 591103 | 16 | 0 | 2 | 3 |

## FAIL

| para | droga / id | parametr | lewa | prawa | Δ | wynik | źródło |
|---|---|---|---|---|---|---|---|
| bialystok-industrial-c / bialystok-wygoda | w231796720 residential | pobocze L | krawężnik + chodnik 2.00 | krawężnik | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-industrial-c: łańcuch 11.8 m (< 15 m, kikut przy węźle) |
| bialystok-wygoda / bialystok-bojary | w177912087 trunk_link | pobocze L | krawężnik + chodnik 2.00 | krawężnik | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-bojary: łańcuch 6.7 m (< 15 m, kikut przy węźle) |
| bialystok-wygoda / bialystok-bojary | w177912090 trunk_link | szerokość jezdni [m] | 4.5 | 5 | 0.5 | UWAGA | derived:network — bialystok-bojary: łańcuch 4.2 m (< 15 m, kikut przy węźle) |
| bialystok-wygoda / bialystok-bojary | w177912090 trunk_link | pasy × szer. pasa [m] | 1 × 4.50 | 1 × 5.00 | — | UWAGA | derived:network — bialystok-bojary: łańcuch 4.2 m (< 15 m, kikut przy węźle) |
| bialystok-wygoda / bialystok-bojary | w177912090 trunk_link | pobocze P | krawężnik + chodnik 2.00 | krawężnik | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-bojary: łańcuch 4.2 m (< 15 m, kikut przy węźle) |
| bialystok-wygoda / bialystok-bojary | w188440103 tertiary | szerokość jezdni [m] | 6.4 | 6 | -0.4 | FAIL | derived:network |
| bialystok-wygoda / bialystok-bojary | w188440103 tertiary | pasy × szer. pasa [m] | 2 × 3.20 | 2 × 3.00 | — | FAIL | derived:network |
| bialystok-wygoda / bialystok-bojary | w264219602 tertiary | szerokość jezdni [m] | 9.75 | 9 | -0.75 | UWAGA | derived:network — bialystok-bojary: łańcuch 14.8 m (< 15 m, kikut przy węźle) |
| bialystok-wygoda / bialystok-bojary | w264219602 tertiary | pasy × szer. pasa [m] | 3 × 3.25 | 3 × 3.00 | — | UWAGA | derived:network — bialystok-bojary: łańcuch 14.8 m (< 15 m, kikut przy węźle) |
| bialystok-wygoda / bialystok-bojary | w278213208 trunk | pobocze P | wiejski: utw. 1,00 + żwir 0,75 + rów | krawężnik | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-wygoda: oś biegnie wzdłuż szwu (/cos/ = 0.48); bialystok-bojary: oś biegnie wzdłuż szwu (/cos/ = 0.48) |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk | pobocze L | pas dzielący wiejski | wiejski: utw. 1,00 + żwir 0,75 + rów | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-wygoda: oś biegnie wzdłuż szwu (/cos/ = 0.47); bialystok-bojary: oś biegnie wzdłuż szwu (/cos/ = 0.47) |
| bialystok-bojary / bialystok-mickiewicza | w57104758 residential | pobocze P | krawężnik + chodnik 2.00 | krawężnik | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-bojary: łańcuch 6.2 m (< 15 m, kikut przy węźle) |
| bialystok-bojary / bialystok-mickiewicza | w57104758 residential | pobocze L | krawężnik + chodnik 2.00 | krawężnik | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-bojary: łańcuch 6.2 m (< 15 m, kikut przy węźle) |
| bialystok-bojary / bialystok-mickiewicza | w375934008 service | pobocze P | krawężnik (płasko) | krawężnik | — | FAIL | derived:network (assign_sides, 1. przebieg) |
| bialystok-bojary / bialystok-mickiewicza | w375934008 service | pobocze L | krawężnik | krawężnik (płasko) | — | FAIL | derived:network (assign_sides, 1. przebieg) |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk | pobocze L | wiejski: utw. 1,00 + żwir 0,75 + rów | krawężnik | — | FAIL | derived:network (assign_sides, 1. przebieg) |
| bialystok-mickiewicza / bialystok-dojlidy | w552379027 residential | szerokość jezdni [m] | 6 | 5.5 | -0.5 | UWAGA | derived:network — bialystok-mickiewicza: łańcuch 2.8 m (< 15 m, kikut przy węźle) |
| bialystok-mickiewicza / bialystok-dojlidy | w552379027 residential | pasy × szer. pasa [m] | 2 × 3.00 | 2 × 2.75 | — | UWAGA | derived:network — bialystok-mickiewicza: łańcuch 2.8 m (< 15 m, kikut przy węźle) |
| bialystok-mickiewicza / bialystok-dojlidy | w616184922 tertiary | pobocze P | krawężnik | krawężnik + chodnik 2.00 | — | FAIL | derived:network (assign_sides, 1. przebieg) |
| bialystok-mickiewicza / bialystok-dojlidy | w1525885356 service | pobocze L | krawężnik (płasko) | krawężnik | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-mickiewicza: łańcuch 10.8 m (< 15 m, kikut przy węźle) |

## Drogi trasy — wszystkie parametry

| para | droga / id | parametr | lewa | prawa | Δ | wynik | źródło |
|---|---|---|---|---|---|---|---|

