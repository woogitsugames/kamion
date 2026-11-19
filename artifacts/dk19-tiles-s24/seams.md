## Szwy — podsumowanie

| para | szew | dróg | na trasie | FAIL | UWAGA | PRZEJŚCIE |
|---|---|---|---|---|---|---|
| bialystok-industrial-c / bialystok-wygoda | x = 779019 | 4 | 1 | 0 | 1 | 0 |
| bialystok-wygoda / bialystok-bojary | y = 595199 | 23 | 1 | 0 | 6 | 6 |
| bialystok-bojary / bialystok-mickiewicza | y = 593151 | 14 | 1 | 2 | 2 | 1 |
| bialystok-mickiewicza / bialystok-dojlidy | y = 591103 | 16 | 1 | 1 | 1 | 2 |

## FAIL / UWAGA / PRZEJŚCIE

| para | droga / id | parametr | lewa | prawa | Δ | wynik | źródło |
|---|---|---|---|---|---|---|---|
| bialystok-industrial-c / bialystok-wygoda | w231796720 residential | pobocze L | krawężnik + chodnik 2.00 | krawężnik | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-industrial-c: łańcuch 11.8 m (< 15 m, kikut przy węźle) |
| bialystok-wygoda / bialystok-bojary | w177912087 trunk_link | pobocze L | krawężnik + chodnik 2.00 | krawężnik | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-bojary: łańcuch 6.7 m (< 15 m, kikut przy węźle) |
| bialystok-wygoda / bialystok-bojary | w177912090 trunk_link | pobocze P | krawężnik + chodnik 2.00 | krawężnik | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-bojary: łańcuch 4.2 m (< 15 m, kikut przy węźle) |
| bialystok-wygoda / bialystok-bojary | w177912090 trunk_link | szer. jezdni ostatni build [m] | 4.5 | 5 | 0.5 | PRZEJŚCIE | generated:roads_qa — szerokości sekcji (nominalne) — różnicę niesie przejście ADR 0275 |
| bialystok-wygoda / bialystok-bojary | w177912090 trunk_link | przejście szerokości (ADR 0275) | jezdnia 4.50 → 4.75 m na 4.2 m | jezdnia 5.00 → 4.75 m na 4.2 m | 0.25 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.250 m); krzywa S 8.5 m, połowa w każdym kaflu |
| bialystok-wygoda / bialystok-bojary | w188440103 tertiary | szer. jezdni ostatni build [m] | 6.4 | 6 | -0.4 | PRZEJŚCIE | generated:roads_qa — szerokości sekcji (nominalne) — różnicę niesie przejście ADR 0275 |
| bialystok-wygoda / bialystok-bojary | w188440103 tertiary | przejście szerokości (ADR 0275) | jezdnia 6.40 → 6.20 m na 10.0 m | jezdnia 6.00 → 6.20 m na 10.0 m | 0.2 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.200 m); krzywa S 20.0 m, połowa w każdym kaflu |
| bialystok-wygoda / bialystok-bojary | w264219602 tertiary | szer. jezdni ostatni build [m] | 9.75 | 9 | -0.75 | PRZEJŚCIE | generated:roads_qa — szerokości sekcji (nominalne) — różnicę niesie przejście ADR 0275 |
| bialystok-wygoda / bialystok-bojary | w264219602 tertiary | przejście szerokości (ADR 0275) | jezdnia 9.75 → 9.38 m na 14.8 m | jezdnia 9.00 → 9.38 m na 14.8 m | 0.375 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.375 m); krzywa S 29.6 m, połowa w każdym kaflu |
| bialystok-wygoda / bialystok-bojary | w278213208 trunk | krawędź asfaltu P [m od osi] | 6.375 | 5.375 | -1 | UWAGA | derived:network (hw + pobocze utwardzone) — bialystok-wygoda: oś biegnie wzdłuż szwu (/cos/ = 0.48); bialystok-bojary: oś biegnie wzdłuż szwu (/cos/ = 0.48) |
| bialystok-wygoda / bialystok-bojary | w278213208 trunk | pobocze P | wiejski: utw. 1,00 + grunt 0,75 + rów | krawężnik | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-wygoda: oś biegnie wzdłuż szwu (/cos/ = 0.48); bialystok-bojary: oś biegnie wzdłuż szwu (/cos/ = 0.48) |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | krawędź asfaltu L [m od osi] | 5.375 | 6.375 | 1 | UWAGA | derived:network (hw + pobocze utwardzone) — bialystok-wygoda: oś biegnie wzdłuż szwu (/cos/ = 0.47); bialystok-bojary: oś biegnie wzdłuż szwu (/cos/ = 0.47) |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | pobocze L | pas dzielący wiejski | wiejski: utw. 1,00 + grunt 0,75 + rów | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-wygoda: oś biegnie wzdłuż szwu (/cos/ = 0.47); bialystok-bojary: oś biegnie wzdłuż szwu (/cos/ = 0.47) |
| bialystok-bojary / bialystok-mickiewicza | w57104758 residential | pobocze P | krawężnik + chodnik 2.00 | krawężnik | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-bojary: łańcuch 6.2 m (< 15 m, kikut przy węźle) |
| bialystok-bojary / bialystok-mickiewicza | w57104758 residential | pobocze L | krawężnik + chodnik 2.00 | krawężnik | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-bojary: łańcuch 6.2 m (< 15 m, kikut przy węźle) |
| bialystok-bojary / bialystok-mickiewicza | w375934008 service | pobocze P | krawężnik (płasko) | krawężnik | — | FAIL | derived:network (assign_sides, 1. przebieg) |
| bialystok-bojary / bialystok-mickiewicza | w375934008 service | pobocze L | krawężnik | krawężnik (płasko) | — | FAIL | derived:network (assign_sides, 1. przebieg) |
| bialystok-bojary / bialystok-mickiewicza | w440321721 secondary | przejście szerokości (ADR 0275) | jezdnia 9.50 → 9.27 m na 11.6 m | jezdnia 9.04 → 9.27 m na 11.6 m | 0.231 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.231 m); krzywa S 23.1 m, połowa w każdym kaflu |
| bialystok-mickiewicza / bialystok-dojlidy | w552379027 residential | szer. jezdni ostatni build [m] | 6 | 5.5 | -0.5 | PRZEJŚCIE | generated:roads_qa — szerokości sekcji (nominalne) — różnicę niesie przejście ADR 0275 |
| bialystok-mickiewicza / bialystok-dojlidy | w552379027 residential | przejście szerokości (ADR 0275) | jezdnia 6.00 → 5.75 m na 2.8 m | jezdnia 5.50 → 5.75 m na 2.8 m | 0.25 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.250 m); krzywa S 5.5 m, połowa w każdym kaflu |
| bialystok-mickiewicza / bialystok-dojlidy | w616184922 tertiary | pobocze P | krawężnik | krawężnik + chodnik 2.00 | — | FAIL | derived:network (assign_sides, 1. przebieg) |
| bialystok-mickiewicza / bialystok-dojlidy | w1525885356 service | pobocze L | krawężnik (płasko) | krawężnik | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-mickiewicza: łańcuch 10.8 m (< 15 m, kikut przy węźle) |

## Drogi trasy — wszystkie parametry

| para | droga / id | parametr | lewa | prawa | Δ | wynik | źródło |
|---|---|---|---|---|---|---|---|
| bialystok-industrial-c / bialystok-wygoda | w560802662 trunk (trasa) | szerokość jezdni [m] | 10.75 | 10.75 | 0 | OK | derived:network |
| bialystok-industrial-c / bialystok-wygoda | w560802662 trunk (trasa) | pasy × szer. pasa [m] | 3 × 3.25 | 3 × 3.25 | — | OK | derived:network |
| bialystok-industrial-c / bialystok-wygoda | w560802662 trunk (trasa) | opaska (edge_strip) [m] | 0.5 | 0.5 | 0 | OK | derived:network |
| bialystok-industrial-c / bialystok-wygoda | w560802662 trunk (trasa) | rozstaw linii krawędziowych [m] | 9.99 | 9.99 | 0 | OK | derived:network |
| bialystok-industrial-c / bialystok-wygoda | w560802662 trunk (trasa) | szer. linii krawędziowej [m] | 0.24 | 0.24 | 0 | OK | derived:network |
| bialystok-industrial-c / bialystok-wygoda | w560802662 trunk (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| bialystok-industrial-c / bialystok-wygoda | w560802662 trunk (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| bialystok-industrial-c / bialystok-wygoda | w560802662 trunk (trasa) | linia środkowa | brak | brak | — | OK | derived:network |
| bialystok-industrial-c / bialystok-wygoda | w560802662 trunk (trasa) | krawędź asfaltu P [m od osi] | 6.375 | 6.375 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| bialystok-industrial-c / bialystok-wygoda | w560802662 trunk (trasa) | pobocze P | wiejski: utw. 1,00 + grunt 0,75 + rów | wiejski: utw. 1,00 + grunt 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| bialystok-industrial-c / bialystok-wygoda | w560802662 trunk (trasa) | krawędź asfaltu L [m od osi] | 5.375 | 5.375 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| bialystok-industrial-c / bialystok-wygoda | w560802662 trunk (trasa) | pobocze L | krawężnik | krawężnik | — | OK | derived:network (assign_sides, 1. przebieg) |
| bialystok-industrial-c / bialystok-wygoda | w560802662 trunk (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| bialystok-industrial-c / bialystok-wygoda | w560802662 trunk (trasa) | wys. terenu w osi Z [m] | — | 137.86 | — | N/D | brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-bialystok-industrial-c) / graph:z_terrain (NMT gugik-nmt-2025-bialystok-wygoda) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| bialystok-industrial-c / bialystok-wygoda | w560802662 trunk (trasa) | szer. jezdni ostatni build [m] | 10.75 | 10.75 | 0 | OK | generated:roads_qa |
| bialystok-industrial-c / bialystok-wygoda | w560802662 trunk (trasa) | położenie osi na szwie [m] | (779019.00, 595242.45) | (779019.00, 595242.45) | 0 | OK | derived:network |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | szerokość jezdni [m] | 10.75 | 10.75 | 0 | OK | derived:network |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | pasy × szer. pasa [m] | 3 × 3.25 | 3 × 3.25 | — | OK | derived:network |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | opaska (edge_strip) [m] | 0.5 | 0.5 | 0 | OK | derived:network |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | rozstaw linii krawędziowych [m] | 9.99 | 9.99 | 0 | OK | derived:network |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | szer. linii krawędziowej [m] | 0.24 | 0.24 | 0 | OK | derived:network |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | linia środkowa | brak | brak | — | OK | derived:network |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | krawędź asfaltu P [m od osi] | 6.375 | 6.375 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | pobocze P | wiejski: utw. 1,00 + grunt 0,75 + rów | wiejski: utw. 1,00 + grunt 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | krawędź asfaltu L [m od osi] | 5.375 | 6.375 | 1 | UWAGA | derived:network (hw + pobocze utwardzone) — bialystok-wygoda: oś biegnie wzdłuż szwu (/cos/ = 0.47); bialystok-bojary: oś biegnie wzdłuż szwu (/cos/ = 0.47) |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | pobocze L | pas dzielący wiejski | wiejski: utw. 1,00 + grunt 0,75 + rów | — | UWAGA | derived:network (assign_sides, 1. przebieg) — bialystok-wygoda: oś biegnie wzdłuż szwu (/cos/ = 0.47); bialystok-bojary: oś biegnie wzdłuż szwu (/cos/ = 0.47) |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | wys. terenu w osi Z [m] | — | 138.13 | — | N/D | brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-bialystok-wygoda) / graph:z_terrain (NMT gugik-nmt-2025-bialystok-bojary) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | szer. jezdni ostatni build [m] | 10.75 | 10.75 | 0 | OK | generated:roads_qa |
| bialystok-wygoda / bialystok-bojary | w606396456 trunk (trasa) | położenie osi na szwie [m] | (779098.27, 595199.00) | (779098.27, 595199.00) | 0 | OK | derived:network |
| bialystok-bojary / bialystok-mickiewicza | w1329465432 secondary (trasa) | szerokość jezdni [m] | 14 | 14 | 0 | OK | derived:network |
| bialystok-bojary / bialystok-mickiewicza | w1329465432 secondary (trasa) | pasy × szer. pasa [m] | 2 × 6.75 | 2 × 6.75 | — | OK | derived:network |
| bialystok-bojary / bialystok-mickiewicza | w1329465432 secondary (trasa) | opaska (edge_strip) [m] | 0.25 | 0.25 | 0 | OK | derived:network |
| bialystok-bojary / bialystok-mickiewicza | w1329465432 secondary (trasa) | rozstaw linii krawędziowych [m] | — | — | — | OK | derived:network |
| bialystok-bojary / bialystok-mickiewicza | w1329465432 secondary (trasa) | szer. linii krawędziowej [m] | — | — | — | OK | derived:network |
| bialystok-bojary / bialystok-mickiewicza | w1329465432 secondary (trasa) | linia krawędziowa L | brak | brak | — | OK | derived:network |
| bialystok-bojary / bialystok-mickiewicza | w1329465432 secondary (trasa) | linia krawędziowa P | brak | brak | — | OK | derived:network |
| bialystok-bojary / bialystok-mickiewicza | w1329465432 secondary (trasa) | linia środkowa | brak | brak | — | OK | derived:network |
| bialystok-bojary / bialystok-mickiewicza | w1329465432 secondary (trasa) | krawędź asfaltu P [m od osi] | 7 | 7 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| bialystok-bojary / bialystok-mickiewicza | w1329465432 secondary (trasa) | pobocze P | krawężnik | krawężnik | — | OK | derived:network (assign_sides, 1. przebieg) |
| bialystok-bojary / bialystok-mickiewicza | w1329465432 secondary (trasa) | krawędź asfaltu L [m od osi] | 7 | 7 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| bialystok-bojary / bialystok-mickiewicza | w1329465432 secondary (trasa) | pobocze L | krawężnik | krawężnik | — | OK | derived:network (assign_sides, 1. przebieg) |
| bialystok-bojary / bialystok-mickiewicza | w1329465432 secondary (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| bialystok-bojary / bialystok-mickiewicza | w1329465432 secondary (trasa) | wys. terenu w osi Z [m] | — | 133.42 | — | N/D | brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-bialystok-bojary) / graph:z_terrain (NMT gugik-nmt-2025-bialystok-mickiewicza) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| bialystok-bojary / bialystok-mickiewicza | w1329465432 secondary (trasa) | szer. jezdni ostatni build [m] | 14 | 14 | 0 | OK | generated:roads_qa |
| bialystok-bojary / bialystok-mickiewicza | w1329465432 secondary (trasa) | położenie osi na szwie [m] | (780205.63, 593151.00) | (780205.63, 593151.00) | 0 | OK | derived:network |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk (trasa) | szerokość jezdni [m] | 7.5 | 7.5 | 0 | OK | derived:network |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk (trasa) | pasy × szer. pasa [m] | 2 × 3.25 | 2 × 3.25 | — | OK | derived:network |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk (trasa) | opaska (edge_strip) [m] | 0.5 | 0.5 | 0 | OK | derived:network |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk (trasa) | rozstaw linii krawędziowych [m] | 6.74 | 6.74 | 0 | OK | derived:network |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk (trasa) | szer. linii krawędziowej [m] | 0.24 | 0.24 | 0 | OK | derived:network |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk (trasa) | linia środkowa | brak | brak | — | OK | derived:network |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk (trasa) | krawędź asfaltu P [m od osi] | 4.75 | 4.75 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk (trasa) | pobocze P | wiejski: utw. 1,00 + grunt 0,75 + rów | wiejski: utw. 1,00 + grunt 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk (trasa) | krawędź asfaltu L [m od osi] | 3.75 | 3.75 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk (trasa) | pobocze L | krawężnik | krawężnik | — | OK | derived:network (assign_sides, 1. przebieg) |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk (trasa) | wys. terenu w osi Z [m] | — | 144.92 | — | N/D | brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-bialystok-mickiewicza) / graph:z_terrain (NMT gugik-nmt-2025-bialystok-dojlidy) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk (trasa) | szer. jezdni ostatni build [m] | 7.5 | 7.5 | 0 | OK | generated:roads_qa |
| bialystok-mickiewicza / bialystok-dojlidy | w279881972 trunk (trasa) | położenie osi na szwie [m] | (779092.40, 591103.00) | (779092.40, 591103.00) | 0 | OK | derived:network |
