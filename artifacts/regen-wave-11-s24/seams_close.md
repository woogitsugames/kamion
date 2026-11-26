## Szwy — podsumowanie

| para | szew | dróg | na trasie | FAIL | UWAGA | PRZEJŚCIE |
|---|---|---|---|---|---|---|
| bialystok-industrial-c / bialystok-maczka | x = 776971 | 7 | 1 | 0 | 0 | 6 |
| bialystok-kleeberga / bialystok-maczka | x = 774923 | 23 | 1 | 0 | 0 | 8 |
| bialystok-kleeberga / bialystok-knyszynska | x = 772875 | 13 | 1 | 0 | 0 | 12 |
| bialystok-knyszynska / dk65-01 | x = 770827 | 6 | 1 | 0 | 0 | 0 |
| dk65-01 / dk65-02 | y = 597247 | 13 | 1 | 0 | 0 | 0 |
| dk65-02 / dk65-03 | x = 768779 | 2 | 1 | 0 | 0 | 0 |
| dk65-03 / dk65-04 | y = 599295 | 3 | 1 | 0 | 0 | 0 |
| dk65-04 / dk65-05 | y = 601343 | 8 | 1 | 0 | 4 | 1 |
| dk65-05 / dk65-06 | y = 603391 | 3 | 1 | 0 | 0 | 1 |
| dk65-06 / dk65-07 | x = 766731 | 2 | 1 | 0 | 0 | 0 |
| dk65-07 / dk65-08 | y = 605439 | 1 | 1 | 0 | 0 | 0 |
| dk65-08 / dk65-09 | x = 764683 | 3 | 1 | 0 | 0 | 0 |
| dk65-09 / dk65-10 | y = 607487 | 1 | 1 | 0 | 0 | 0 |
| dk65-10 / dk65-11 | y = 609535 | 1 | 1 | 0 | 0 | 0 |
| dk65-11 / knyszyn-s | x = 762635 | 1 | 1 | 0 | 0 | 1 |
| knyszyn-s / knyszyn | y = 611583 | 1 | 1 | 0 | 0 | 0 |
| knyszyn-s / dw671-tykocin-01 | x = 760587 | 1 | 0 | 0 | 0 | 2 |
| knyszyn / knyszyn-w | x = 760587 | 10 | 1 | 0 | 0 | 0 |
| knyszyn-w / dk65-monki-01 | y = 613631 | 2 | 1 | 0 | 0 | 0 |
| knyszyn-w / dw671-tykocin-01 | y = 611583 | 2 | 1 | 0 | 0 | 0 |

## FAIL / UWAGA / PRZEJŚCIE

| para | droga / id | parametr | lewa | prawa | Δ | wynik | źródło |
|---|---|---|---|---|---|---|---|
| bialystok-industrial-c / bialystok-maczka | w23982184 trunk | szer. jezdni ostatni build [m] | 12.25 | 11.5 | -0.75 | PRZEJŚCIE | generated:roads_qa — szerokości sekcji (nominalne) — różnicę niesie przejście ADR 0275 |
| bialystok-industrial-c / bialystok-maczka | w23982184 trunk | przejście szerokości (ADR 0275) | jezdnia 12.25 → 11.88 m na 37.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.375 m, np. D94) | jezdnia 11.50 → 11.88 m na 37.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.375 m, np. D94) | 0.75 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.750 m); krzywa S 75.0 m, połowa w każdym kaflu |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | szer. jezdni ostatni build [m] | 8.983 | 8.5 | -0.483 | PRZEJŚCIE | generated:roads_qa — szerokości sekcji (nominalne) — różnicę niesie przejście ADR 0275 |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | przejście szerokości (ADR 0275) | jezdnia 8.98 → 8.74 m na 24.2 m; oś do środka między osiami nominalnymi (odsunięcie 0.242 m, np. D94) | jezdnia 8.50 → 8.74 m na 24.2 m; oś do środka między osiami nominalnymi (odsunięcie 0.242 m, np. D94) | 0.484 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.484 m); krzywa S 48.4 m, połowa w każdym kaflu |
| bialystok-industrial-c / bialystok-maczka | w606396469 trunk_link | szer. jezdni ostatni build [m] | 5.616 | 5.5 | -0.116 | PRZEJŚCIE | generated:roads_qa — szerokości sekcji (nominalne) — różnicę niesie przejście ADR 0275 |
| bialystok-industrial-c / bialystok-maczka | w606396469 trunk_link | przejście szerokości (ADR 0275) | jezdnia 5.62 → 5.56 m na 10.0 m; oś do środka między osiami nominalnymi (odsunięcie 0.058 m, np. D94) | jezdnia 5.50 → 5.56 m na 10.0 m; oś do środka między osiami nominalnymi (odsunięcie 0.058 m, np. D94) | 0.116 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.116 m); krzywa S 20.0 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-maczka | w25899481 service | przejście szerokości (ADR 0275) | jezdnia 5.50 → 5.50 m na 12.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | jezdnia 5.50 → 5.50 m na 12.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | 0.25 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.250 m); krzywa S 25.0 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-maczka | w25899482 service | przejście szerokości (ADR 0275) | jezdnia 5.50 → 5.50 m na 25.0 m; oś do środka między osiami nominalnymi (odsunięcie 0.500 m, np. D94) | jezdnia 5.50 → 5.50 m na 25.0 m; oś do środka między osiami nominalnymi (odsunięcie 0.500 m, np. D94) | 0.5 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.500 m); krzywa S 50.0 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-maczka | w25899483 living_street | przejście szerokości (ADR 0275) | jezdnia 5.50 → 5.50 m na 10.0 m; oś do środka między osiami nominalnymi (odsunięcie 0.066 m, np. D94) | jezdnia 5.50 → 5.50 m na 10.0 m; oś do środka między osiami nominalnymi (odsunięcie 0.066 m, np. D94) | 0.066 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.066 m); krzywa S 20.0 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-maczka | w227027524 service | przejście szerokości (ADR 0275) | jezdnia 5.50 → 5.50 m na 5.0 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | jezdnia 5.50 → 5.50 m na 5.0 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | 0.25 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.250 m); krzywa S 9.9 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-maczka | w227027719 trunk_link | przejście szerokości (ADR 0275) | jezdnia 5.75 → 5.75 m na 10.0 m; oś do środka między osiami nominalnymi (odsunięcie 0.125 m, np. D94) | jezdnia 5.75 → 5.75 m na 10.0 m; oś do środka między osiami nominalnymi (odsunięcie 0.125 m, np. D94) | 0.125 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.125 m); krzywa S 20.0 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-maczka | w270494330 residential | przejście szerokości (ADR 0275) | jezdnia 6.50 → 6.50 m na 12.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | jezdnia 6.50 → 6.50 m na 12.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | 0.25 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.250 m); krzywa S 25.0 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-maczka | w305072031 service | przejście szerokości (ADR 0275) | jezdnia 5.75 → 5.75 m na 10.0 m; oś do środka między osiami nominalnymi (odsunięcie 0.125 m, np. D94) | jezdnia 5.75 → 5.75 m na 10.0 m; oś do środka między osiami nominalnymi (odsunięcie 0.125 m, np. D94) | 0.125 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.125 m); krzywa S 20.0 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-maczka | w1193586233 tertiary | przejście szerokości (ADR 0275) | jezdnia 7.50 → 7.50 m na 12.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | jezdnia 7.50 → 7.50 m na 12.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | 0.25 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.250 m); krzywa S 25.0 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-knyszynska | w40329438 residential | przejście szerokości (ADR 0275) | jezdnia 6.50 → 6.50 m na 5.9 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | jezdnia 6.50 → 6.50 m na 5.9 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | 0.25 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.250 m); krzywa S 11.9 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-knyszynska | w76084085 tertiary | przejście szerokości (ADR 0275) | jezdnia 6.00 → 6.00 m na 12.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | jezdnia 6.00 → 6.00 m na 12.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | 0.25 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.250 m); krzywa S 25.0 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-knyszynska | w222579345 service | szer. jezdni ostatni build [m] | 5.5 | 6.5 | 1 | PRZEJŚCIE | generated:roads_qa — szerokości sekcji (nominalne) — różnicę niesie przejście ADR 0275 |
| bialystok-kleeberga / bialystok-knyszynska | w222579345 service | przejście szerokości (ADR 0275) | jezdnia 5.50 → 6.00 m na 25.0 m | jezdnia 6.50 → 6.00 m na 25.0 m | 0.5 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.500 m); krzywa S 50.0 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-knyszynska | w224161424 service | szer. jezdni ostatni build [m] | 5.5 | 4.5 | -1 | PRZEJŚCIE | generated:roads_qa — szerokości sekcji (nominalne) — różnicę niesie przejście ADR 0275 |
| bialystok-kleeberga / bialystok-knyszynska | w224161424 service | przejście szerokości (ADR 0275) | jezdnia 5.50 → 5.00 m na 10.4 m | jezdnia 4.50 → 5.00 m na 10.4 m | 0.5 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.500 m); krzywa S 20.8 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | szer. jezdni ostatni build [m] | 8 | 8.5 | 0.5 | PRZEJŚCIE | generated:roads_qa — szerokości sekcji (nominalne) — różnicę niesie przejście ADR 0275 |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | przejście szerokości (ADR 0275) | jezdnia 8.00 → 8.25 m na 25.0 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | jezdnia 8.50 → 8.25 m na 25.0 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | 0.5 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.500 m); krzywa S 50.0 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-knyszynska | w281813932 residential | przejście szerokości (ADR 0275) | jezdnia 5.50 → 5.50 m na 12.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | jezdnia 5.50 → 5.50 m na 12.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | 0.25 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.250 m); krzywa S 25.0 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-knyszynska | w309094412 service | przejście szerokości (ADR 0275) | jezdnia 5.50 → 5.50 m na 3.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | jezdnia 5.50 → 5.50 m na 3.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | 0.25 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.250 m); krzywa S 7.0 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-knyszynska | w561326924 trunk_link | szer. jezdni ostatni build [m] | 5.75 | 6.25 | 0.5 | PRZEJŚCIE | generated:roads_qa — szerokości sekcji (nominalne) — różnicę niesie przejście ADR 0275 |
| bialystok-kleeberga / bialystok-knyszynska | w561326924 trunk_link | przejście szerokości (ADR 0275) | jezdnia 5.75 → 6.00 m na 12.5 m | jezdnia 6.25 → 6.00 m na 12.5 m | 0.25 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.250 m); krzywa S 25.0 m, połowa w każdym kaflu |
| dk65-04 / dk65-05 | w176274699 residential | linia środkowa | brak | P-1b przerywana (2/4) | — | UWAGA | derived:network — dk65-05: oś biegnie wzdłuż szwu (/cos/ = 0.07) |
| dk65-04 / dk65-05 | w176274699 residential | pobocze P | krawężnik | krawężnik + chodnik 2.00 | — | UWAGA | derived:network (assign_sides, 2. przebieg) — dk65-05: oś biegnie wzdłuż szwu (/cos/ = 0.07) |
| dk65-04 / dk65-05 | w176274699 residential | położenie osi na szwie [m] | (768247.66, 601343.00) | (768248.24, 601343.00) | 0.584 | UWAGA | derived:network — dk65-05: oś biegnie wzdłuż szwu (/cos/ = 0.07) |
| dk65-04 / dk65-05 | w244403508 tertiary | droga po drugiej stronie | c:w1428963539:840039845-839428386 | — | — | UWAGA | derived:network — droga urywa się na szwie (brak końca łańcucha po prawej stronie w ±5 m); dk65-04: oś biegnie wzdłuż szwu (/cos/ = 0.08) |
| dk65-04 / dk65-05 | w249298671 service | przejście szerokości (ADR 0275) | jezdnia 5.50 → 5.50 m na 12.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | jezdnia 5.50 → 5.50 m na 12.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | 0.25 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.250 m); krzywa S 25.0 m, połowa w każdym kaflu |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | przejście szerokości (ADR 0275) | jezdnia 7.10 → 7.10 m na 12.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | jezdnia 7.10 → 7.10 m na 12.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | 0.25 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.250 m); krzywa S 25.0 m, połowa w każdym kaflu |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | przejście szerokości (ADR 0275) | jezdnia 7.10 → 7.10 m na 13.5 m; pobocze L utw./grunt 35/75 → 22/88 cm; pobocze R utw./grunt 35/75 → 22/88 cm | jezdnia 7.10 → 7.10 m na 13.5 m; pobocze L utw./grunt 8/100 → 22/88 cm; pobocze R utw./grunt 8/100 → 22/88 cm | 0.27 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.270 m); krzywa S 27.0 m, połowa w każdym kaflu |
| knyszyn-s / dw671-tykocin-01 | w98071886 unclassified | szer. jezdni ostatni build [m] | 6.2 | 6 | -0.2 | PRZEJŚCIE | generated:roads_qa — szerokości sekcji (nominalne) — różnicę niesie przejście ADR 0275 |
| knyszyn-s / dw671-tykocin-01 | w98071886 unclassified | przejście szerokości (ADR 0275) | jezdnia 6.20 → 6.10 m na 10.0 m | jezdnia 6.00 → 6.10 m na 10.0 m | 0.1 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.100 m); krzywa S 20.0 m, połowa w każdym kaflu |

## Drogi trasy — wszystkie parametry

| para | droga / id | parametr | lewa | prawa | Δ | wynik | źródło |
|---|---|---|---|---|---|---|---|
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | szerokość jezdni [m] | 8.742 | 8.742 | 0 | OK | derived:network |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | pasy × szer. pasa [m] | 2 × 3.87 | 2 × 3.87 | — | OK | derived:network (lanes_follow_width: lokalnie, sekcja 3.99) / derived:network (lanes_follow_width: lokalnie, sekcja 3.75) |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | opaska (edge_strip) [m] | 0.5 | 0.5 | 0 | OK | derived:network |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | rozstaw linii krawędziowych [m] | 7.982 | 7.982 | 0 | OK | derived:network |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | szer. linii krawędziowej [m] | 0.24 | 0.24 | 0 | OK | derived:network |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | linia środkowa | brak | brak | — | OK | derived:network |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | krawędź asfaltu P [m od osi] | 4.371 | 4.371 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | pobocze P | krawężnik (płasko) | krawężnik (płasko) | — | OK | derived:network (assign_sides, 2. przebieg) |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | krawędź asfaltu L [m od osi] | 4.371 | 4.371 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | pobocze L | krawężnik | krawężnik | — | OK | derived:network (assign_sides, 2. przebieg) |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | wys. terenu w osi Z [m] | 130.84 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-bialystok-industrial-c) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-bialystok-maczka) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | szer. jezdni ostatni build [m] | 8.983 | 8.5 | -0.483 | PRZEJŚCIE | generated:roads_qa — szerokości sekcji (nominalne) — różnicę niesie przejście ADR 0275 |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | przejście szerokości (ADR 0275) | jezdnia 8.98 → 8.74 m na 24.2 m; oś do środka między osiami nominalnymi (odsunięcie 0.242 m, np. D94) | jezdnia 8.50 → 8.74 m na 24.2 m; oś do środka między osiami nominalnymi (odsunięcie 0.242 m, np. D94) | 0.484 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.484 m); krzywa S 48.4 m, połowa w każdym kaflu |
| bialystok-industrial-c / bialystok-maczka | w257367422 trunk (trasa) | położenie osi na szwie [m] | (776970.99, 596279.31) | (776970.99, 596279.31) | 0 | OK | derived:network |
| bialystok-kleeberga / bialystok-maczka | w249740774 trunk (trasa) | szerokość jezdni [m] | 8 | 8.006 | 0.006 | OK | derived:network |
| bialystok-kleeberga / bialystok-maczka | w249740774 trunk (trasa) | pasy × szer. pasa [m] | 2 × 3.50 | 2 × 3.50 | — | OK | derived:network |
| bialystok-kleeberga / bialystok-maczka | w249740774 trunk (trasa) | opaska (edge_strip) [m] | 0.5 | 0.5 | 0 | OK | derived:network |
| bialystok-kleeberga / bialystok-maczka | w249740774 trunk (trasa) | rozstaw linii krawędziowych [m] | 7.24 | 7.246 | 0.006 | OK | derived:network |
| bialystok-kleeberga / bialystok-maczka | w249740774 trunk (trasa) | szer. linii krawędziowej [m] | 0.24 | 0.24 | 0 | OK | derived:network |
| bialystok-kleeberga / bialystok-maczka | w249740774 trunk (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| bialystok-kleeberga / bialystok-maczka | w249740774 trunk (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| bialystok-kleeberga / bialystok-maczka | w249740774 trunk (trasa) | linia środkowa | brak | brak | — | OK | derived:network |
| bialystok-kleeberga / bialystok-maczka | w249740774 trunk (trasa) | krawędź asfaltu P [m od osi] | 4 | 4.003 | 0.003 | OK | derived:network (hw + pobocze utwardzone) |
| bialystok-kleeberga / bialystok-maczka | w249740774 trunk (trasa) | pobocze P | krawężnik | krawężnik | — | OK | derived:network (assign_sides, 2. przebieg) |
| bialystok-kleeberga / bialystok-maczka | w249740774 trunk (trasa) | krawędź asfaltu L [m od osi] | 5 | 5.003 | 0.003 | OK | derived:network (hw + pobocze utwardzone) |
| bialystok-kleeberga / bialystok-maczka | w249740774 trunk (trasa) | pobocze L | wiejski: utw. 1,00 + grunt 0,75 + rów | wiejski: utw. 1,00 + grunt 0,75 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| bialystok-kleeberga / bialystok-maczka | w249740774 trunk (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| bialystok-kleeberga / bialystok-maczka | w249740774 trunk (trasa) | wys. terenu w osi Z [m] | — | 123.44 | — | N/D | brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-bialystok-kleeberga) / graph:z_terrain (NMT gugik-nmt-2025-bialystok-maczka) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| bialystok-kleeberga / bialystok-maczka | w249740774 trunk (trasa) | szer. jezdni ostatni build [m] | — | — | — | N/D | generated:roads_qa: łańcuch ma szerokości [8.38, 11.67], żadna ≠ sekcji / generated:roads_qa: łańcuch ma szerokości [8.38, 11.85], żadna ≠ sekcji |
| bialystok-kleeberga / bialystok-maczka | w249740774 trunk (trasa) | położenie osi na szwie [m] | (774923.00, 596185.73) | (774923.00, 596185.73) | 0.003 | OK | derived:network |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | szerokość jezdni [m] | 8.25 | 8.25 | 0 | OK | derived:network |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | pasy × szer. pasa [m] | 2 × 3.63 | 2 × 3.63 | — | OK | derived:network (lanes_follow_width: lokalnie, sekcja 3.50) / derived:network (lanes_follow_width: lokalnie, sekcja 3.75) |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | opaska (edge_strip) [m] | 0.5 | 0.5 | 0 | OK | derived:network |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | rozstaw linii krawędziowych [m] | 7.49 | 7.49 | 0 | OK | derived:network |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | szer. linii krawędziowej [m] | 0.24 | 0.24 | 0 | OK | derived:network |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | linia środkowa | brak | brak | — | OK | derived:network |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | krawędź asfaltu P [m od osi] | 4.125 | 4.125 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | pobocze P | krawężnik (płasko) | krawężnik (płasko) | — | OK | derived:network (assign_sides, 2. przebieg) |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | krawędź asfaltu L [m od osi] | 4.125 | 4.125 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | pobocze L | krawężnik | krawężnik | — | OK | derived:network (assign_sides, 2. przebieg) |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | wys. terenu w osi Z [m] | 126.48 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-bialystok-kleeberga) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2022-bialystok-knyszynska) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Różne roczniki NMT (2025 / 2022): możliwy skok terenu ≤ 0,5 m (ADR 0214) |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | szer. jezdni ostatni build [m] | 8 | 8.5 | 0.5 | PRZEJŚCIE | generated:roads_qa — szerokości sekcji (nominalne) — różnicę niesie przejście ADR 0275 |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | przejście szerokości (ADR 0275) | jezdnia 8.00 → 8.25 m na 25.0 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | jezdnia 8.50 → 8.25 m na 25.0 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | 0.5 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.500 m); krzywa S 50.0 m, połowa w każdym kaflu |
| bialystok-kleeberga / bialystok-knyszynska | w261104557 trunk (trasa) | położenie osi na szwie [m] | (772874.94, 595511.68) | (772874.94, 595511.68) | 0 | OK | derived:network |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | szerokość jezdni [m] | 7.2 | 7.2 | 0 | OK | derived:network |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | pasy × szer. pasa [m] | 2 × 3.35 | 2 × 3.35 | — | OK | derived:network |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | opaska (edge_strip) [m] | 0.25 | 0.25 | 0 | OK | derived:network |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | rozstaw linii krawędziowych [m] | 6.8 | 6.8 | 0 | OK | derived:network |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | linia środkowa | P-1b przerywana (2/4) | P-1b przerywana (2/4) | — | OK | derived:network |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | krawędź asfaltu P [m od osi] | 3.68 | 3.68 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | pobocze P | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | krawędź asfaltu L [m od osi] | 3.68 | 3.68 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | pobocze L | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | wys. terenu w osi Z [m] | 119.66 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2022-bialystok-knyszynska) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-01) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Różne roczniki NMT (2022 / 2025): możliwy skok terenu ≤ 0,5 m (ADR 0214) |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | szer. jezdni ostatni build [m] | 7.2 | 7.2 | 0 | OK | generated:roads_qa |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | położenie osi na szwie [m] | (770827.00, 597006.79) | (770827.00, 597006.79) | 0 | OK | derived:network |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | referencja rozstawu linii (lewa) 6.5–6.9 m | 6.8 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 8,8 = 6,3 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| bialystok-knyszynska / dk65-01 | w234919333 secondary (trasa) | referencja rozstawu linii (prawa) 6.5–6.9 m | — | 6.8 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 8,8 = 6,3 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | szerokość jezdni [m] | 7 | 7 | 0 | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | pasy × szer. pasa [m] | 2 × 3.25 | 2 × 3.25 | — | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | opaska (edge_strip) [m] | 0.25 | 0.25 | 0 | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | rozstaw linii krawędziowych [m] | 6.7 | 6.7 | 0 | OK | derived:network (authored_override:dk65-k1-edge-line-spacing) |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | linia środkowa | P-1b przerywana (2/4) | P-1b przerywana (2/4) | — | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | krawędź asfaltu P [m od osi] | 3.58 | 3.58 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | pobocze P | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | krawędź asfaltu L [m od osi] | 3.58 | 3.58 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | pobocze L | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | wys. terenu w osi Z [m] | 124.27 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-01) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-02) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | szer. jezdni ostatni build [m] | 7 | 7 | 0 | OK | generated:roads_qa |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | położenie osi na szwie [m] | (770244.58, 597247.00) | (770244.58, 597247.00) | 0 | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | referencja rozstawu linii (lewa) 6.5–6.9 m | 6.7 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 9,0 = 6,2 m, km 10,0 = 6,4 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | referencja rozstawu linii (prawa) 6.5–6.9 m | — | 6.7 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 9,0 = 6,2 m, km 10,0 = 6,4 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | szerokość jezdni [m] | 7.1 | 7.1 | 0 | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | pasy × szer. pasa [m] | 2 × 3.30 | 2 × 3.30 | — | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | opaska (edge_strip) [m] | 0.25 | 0.25 | 0 | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | rozstaw linii krawędziowych [m] | 6.7 | 6.7 | 0 | OK | derived:network (authored_override:dk65-k1-edge-line-spacing) |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | linia krawędziowa L | przerywana (dk65-02-k1-dashed-elcka-l) | przerywana (dk65-03-k1-dashed-elcka-l) | — | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | linia krawędziowa P | przerywana (dk65-02-k1-dashed-elcka-p) | przerywana (dk65-03-k1-dashed-elcka-p) | — | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | krawędź asfaltu P [m od osi] | 3.63 | 3.63 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | pobocze P | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | krawędź asfaltu L [m od osi] | 3.63 | 3.63 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | pobocze L | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | wys. terenu w osi Z [m] | 113.96 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-02) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-03) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | szer. jezdni ostatni build [m] | 7.1 | 7.1 | 0 | OK | generated:roads_qa |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | położenie osi na szwie [m] | (768779.00, 598817.91) | (768779.00, 598817.91) | 0 | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | referencja rozstawu linii (lewa) 6.5–6.9 m | 6.7 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 11,5 = 6,1 m, km 12,0 = 6,1 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | referencja rozstawu linii (prawa) 6.5–6.9 m | — | 6.7 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 11,5 = 6,1 m, km 12,0 = 6,1 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | szerokość jezdni [m] | 7.1 | 7.1 | 0 | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | pasy × szer. pasa [m] | 2 × 3.30 | 2 × 3.30 | — | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | opaska (edge_strip) [m] | 0.25 | 0.25 | 0 | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | rozstaw linii krawędziowych [m] | 6.7 | 6.7 | 0 | OK | derived:network (authored_override:dk65-k1-edge-line-spacing) |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | linia krawędziowa L | przerywana (dk65-03-k1-dashed-elcka-l) | przerywana (dk65-04-k1-dashed-elcka-l) | — | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | linia krawędziowa P | przerywana (dk65-03-k1-dashed-elcka-p) | przerywana (dk65-04-k1-dashed-elcka-p) | — | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | krawędź asfaltu P [m od osi] | 3.63 | 3.63 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | pobocze P | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | krawędź asfaltu L [m od osi] | 3.63 | 3.63 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | pobocze L | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | wys. terenu w osi Z [m] | 115.36 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-03) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-04) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | szer. jezdni ostatni build [m] | 7.1 | 7.1 | 0 | OK | generated:roads_qa |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | położenie osi na szwie [m] | (768694.97, 599295.00) | (768694.97, 599295.00) | 0 | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | referencja rozstawu linii (lewa) 6.5–6.9 m | 6.7 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 12,0 = 6,1 m, km 12,5 = 6,2 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | referencja rozstawu linii (prawa) 6.5–6.9 m | — | 6.7 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 12,0 = 6,1 m, km 12,5 = 6,2 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | szerokość jezdni [m] | 7.1 | 7.1 | 0 | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | pasy × szer. pasa [m] | 2 × 3.30 | 2 × 3.30 | — | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | opaska (edge_strip) [m] | 0.25 | 0.25 | 0 | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | rozstaw linii krawędziowych [m] | 6.7 | 6.7 | 0 | OK | derived:network (authored_override:dk65-k1-edge-line-spacing) |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | krawędź asfaltu P [m od osi] | 3.63 | 3.63 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | pobocze P | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | krawędź asfaltu L [m od osi] | 3.63 | 3.63 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | pobocze L | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | wys. terenu w osi Z [m] | 149.1 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-04) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-05) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | szer. jezdni ostatni build [m] | 7.1 | 7.1 | 0 | OK | generated:roads_qa |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | położenie osi na szwie [m] | (768334.87, 601343.00) | (768334.87, 601343.00) | 0 | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | referencja rozstawu linii (lewa) 6.5–6.9 m | 6.7 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 14,0 = 6,2 m, km 14,5 = 6,2 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | referencja rozstawu linii (prawa) 6.5–6.9 m | — | 6.7 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 14,0 = 6,2 m, km 14,5 = 6,2 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | szerokość jezdni [m] | 7.1 | 7.1 | 0 | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | pasy × szer. pasa [m] | 2 × 3.30 | 2 × 3.30 | — | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | opaska (edge_strip) [m] | 0.25 | 0.25 | 0 | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | rozstaw linii krawędziowych [m] | 6.7 | 6.7 | 0 | OK | derived:network (authored_override:dk65-k1-edge-line-spacing) / derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | krawędź asfaltu P [m od osi] | 3.63 | 3.63 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | pobocze P | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | krawędź asfaltu L [m od osi] | 3.63 | 3.63 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | pobocze L | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | wys. terenu w osi Z [m] | 163.2 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-05) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-06) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | szer. jezdni ostatni build [m] | 7.1 | 7.1 | 0 | OK | generated:roads_qa |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | przejście szerokości (ADR 0275) | jezdnia 7.10 → 7.10 m na 12.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | jezdnia 7.10 → 7.10 m na 12.5 m; oś do środka między osiami nominalnymi (odsunięcie 0.250 m, np. D94) | 0.25 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.250 m); krzywa S 25.0 m, połowa w każdym kaflu |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | położenie osi na szwie [m] | (767660.32, 603390.92) | (767660.32, 603390.92) | 0 | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | referencja rozstawu linii (lewa) 6.5–6.9 m | 6.7 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 16,0 = 6,2 m, km 17,0 = 6,1 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | referencja rozstawu linii (prawa) 6.5–6.9 m | — | 6.7 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 16,0 = 6,2 m, km 17,0 = 6,1 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | szerokość jezdni [m] | 7.1 | 7.1 | 0 | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | pasy × szer. pasa [m] | 2 × 3.35 | 2 × 3.35 | — | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | opaska (edge_strip) [m] | 0.2 | 0.2 | 0 | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | rozstaw linii krawędziowych [m] | 6.7 | 6.7 | 0 | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | krawędź asfaltu P [m od osi] | 3.9 | 3.9 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | pobocze P | wiejski: utw. 0,35 + grunt 0,75 + rów | wiejski: utw. 0,35 + grunt 0,75 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | krawędź asfaltu L [m od osi] | 3.9 | 3.9 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | pobocze L | wiejski: utw. 0,35 + grunt 0,75 + rów | wiejski: utw. 0,35 + grunt 0,75 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | oświetlenie | brak (override) | brak (override) | — | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | wys. terenu w osi Z [m] | 155.42 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-06) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-07) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | szer. jezdni ostatni build [m] | 7.1 | 7.1 | 0 | OK | generated:roads_qa |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | położenie osi na szwie [m] | (766731.00, 604722.19) | (766731.00, 604722.19) | 0 | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | referencja rozstawu linii (lewa) 6.5–6.9 m | 6.7 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 18,0 = 6,0 m, km 19,0 = 6,4 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | referencja rozstawu linii (prawa) 6.5–6.9 m | — | 6.7 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 18,0 = 6,0 m, km 19,0 = 6,4 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | szerokość jezdni [m] | 7.1 | 7.1 | 0 | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | pasy × szer. pasa [m] | 2 × 3.35 | 2 × 3.35 | — | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | opaska (edge_strip) [m] | 0.2 | 0.2 | 0 | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | rozstaw linii krawędziowych [m] | 6.7 | 6.7 | 0 | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | krawędź asfaltu P [m od osi] | 3.9 | 3.9 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | pobocze P | wiejski: utw. 0,35 + grunt 0,75 + rów | wiejski: utw. 0,35 + grunt 0,75 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | krawędź asfaltu L [m od osi] | 3.9 | 3.9 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | pobocze L | wiejski: utw. 0,35 + grunt 0,75 + rów | wiejski: utw. 0,35 + grunt 0,75 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | oświetlenie | brak (override) | brak (override) | — | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | wys. terenu w osi Z [m] | 147.27 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-07) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-08) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | szer. jezdni ostatni build [m] | 7.1 | 7.1 | 0 | OK | generated:roads_qa |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | położenie osi na szwie [m] | (766246.20, 605439.00) | (766246.20, 605439.00) | 0 | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | referencja rozstawu linii (lewa) 6.5–6.9 m | 6.7 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 19,0 = 6,4 m, km 20,0 = 6,0 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | referencja rozstawu linii (prawa) 6.5–6.9 m | — | 6.7 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 19,0 = 6,4 m, km 20,0 = 6,0 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | szerokość jezdni [m] | 7.1 | 7.1 | 0 | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | pasy × szer. pasa [m] | 2 × 3.35 | 2 × 3.35 | — | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | opaska (edge_strip) [m] | 0.2 | 0.2 | 0 | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | rozstaw linii krawędziowych [m] | 6.7 | 6.7 | 0 | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | krawędź asfaltu P [m od osi] | 3.9 | 3.9 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | pobocze P | wiejski: utw. 0,35 + grunt 0,75 + rów | wiejski: utw. 0,35 + grunt 0,75 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | krawędź asfaltu L [m od osi] | 3.9 | 3.9 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | pobocze L | wiejski: utw. 0,35 + grunt 0,75 + rów | wiejski: utw. 0,35 + grunt 0,75 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | oświetlenie | brak (override) | brak (override) | — | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | wys. terenu w osi Z [m] | 130.28 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-08) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-09) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | szer. jezdni ostatni build [m] | 7.1 | 7.1 | 0 | OK | generated:roads_qa |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | położenie osi na szwie [m] | (764683.00, 607186.77) | (764683.00, 607186.77) | 0 | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | referencja rozstawu linii (lewa) 6.5–6.9 m | 6.7 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 21,0 = 6,25 m, km 21,65 = 6,1 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | referencja rozstawu linii (prawa) 6.5–6.9 m | — | 6.7 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 21,0 = 6,25 m, km 21,65 = 6,1 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | szerokość jezdni [m] | 7.1 | 7.1 | 0 | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | pasy × szer. pasa [m] | 2 × 3.35 | 2 × 3.35 | — | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | opaska (edge_strip) [m] | 0.2 | 0.2 | 0 | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | rozstaw linii krawędziowych [m] | 6.7 | 6.7 | 0 | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | krawędź asfaltu P [m od osi] | 3.9 | 3.9 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | pobocze P | wiejski: utw. 0,35 + grunt 0,75 + rów | wiejski: utw. 0,35 + grunt 0,75 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | krawędź asfaltu L [m od osi] | 3.9 | 3.9 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | pobocze L | wiejski: utw. 0,35 + grunt 0,75 + rów | wiejski: utw. 0,35 + grunt 0,75 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | oświetlenie | brak (override) | brak (override) | — | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | wys. terenu w osi Z [m] | 129.14 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-09) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-10) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | szer. jezdni ostatni build [m] | 7.1 | 7.1 | 0 | OK | generated:roads_qa |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | położenie osi na szwie [m] | (764498.56, 607487.00) | (764498.56, 607487.00) | 0 | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | referencja rozstawu linii (lewa) 6.5–6.9 m | 6.7 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 21,65 = 6,1 m, km 22,0 = 6,1 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | referencja rozstawu linii (prawa) 6.5–6.9 m | — | 6.7 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 21,65 = 6,1 m, km 22,0 = 6,1 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | szerokość jezdni [m] | 7.1 | 7.1 | 0 | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | pasy × szer. pasa [m] | 2 × 3.35 | 2 × 3.35 | — | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | opaska (edge_strip) [m] | 0.2 | 0.2 | 0 | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | rozstaw linii krawędziowych [m] | 6.7 | 6.7 | 0 | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | krawędź asfaltu P [m od osi] | 3.9 | 3.9 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | pobocze P | wiejski: utw. 0,35 + grunt 0,75 + rów | wiejski: utw. 0,35 + grunt 0,75 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | krawędź asfaltu L [m od osi] | 3.9 | 3.9 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | pobocze L | wiejski: utw. 0,35 + grunt 0,75 + rów | wiejski: utw. 0,35 + grunt 0,75 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | oświetlenie | brak (override) | brak (override) | — | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | wys. terenu w osi Z [m] | 132.87 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-10) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2022-dk65-11) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Różne roczniki NMT (2025 / 2022): możliwy skok terenu ≤ 0,5 m (ADR 0214) |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | szer. jezdni ostatni build [m] | 7.1 | 7.1 | 0 | OK | generated:roads_qa |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | położenie osi na szwie [m] | (762892.90, 609535.00) | (762892.90, 609535.00) | 0 | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | referencja rozstawu linii (lewa) 6.5–6.9 m | 6.7 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 24,0 = 6,1 m, km 24,6 = 6,0 m (mediana korytarza 6,2); ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | referencja rozstawu linii (prawa) 6.5–6.9 m | — | 6.7 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 24,0 = 6,1 m, km 24,6 = 6,0 m (mediana korytarza 6,2); ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | szerokość jezdni [m] | 7.1 | 7.1 | 0 | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | pasy × szer. pasa [m] | 2 × 3.35 | 2 × 3.35 | — | OK | derived:network / derived:network (lanes_follow_width: lokalnie, sekcja 3.80) |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | opaska (edge_strip) [m] | 0.2 | 0.2 | 0 | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | rozstaw linii krawędziowych [m] | 6.7 | 6.7 | 0 | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | krawędź asfaltu P [m od osi] | 3.77 | 3.77 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | pobocze P | wiejski: utw. 0,22 + grunt 0,88 + rów | wiejski: utw. 0,22 + grunt 0,88 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | krawędź asfaltu L [m od osi] | 3.77 | 3.77 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | pobocze L | wiejski: utw. 0,22 + grunt 0,88 + rów | wiejski: utw. 0,22 + grunt 0,88 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | oświetlenie | brak (override) | brak (override) | — | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | wys. terenu w osi Z [m] | 144.18 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2022-dk65-11) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2022-knyszyn-s) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2022 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | szer. jezdni ostatni build [m] | 7.1 | — | — | N/D | generated:roads_qa / generated:roads_qa: sekcja z profilem szerokości (roads_qa niesie maksimum 8.00 m, na szwie 7.10 m) — nieporównywalne |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | przejście szerokości (ADR 0275) | jezdnia 7.10 → 7.10 m na 13.5 m; pobocze L utw./grunt 35/75 → 22/88 cm; pobocze R utw./grunt 35/75 → 22/88 cm | jezdnia 7.10 → 7.10 m na 13.5 m; pobocze L utw./grunt 8/100 → 22/88 cm; pobocze R utw./grunt 8/100 → 22/88 cm | 0.27 | PRZEJŚCIE | derived:seam_taper — przekroje nominalne różnią się (największy skok krawędzi 0.270 m); krzywa S 27.0 m, połowa w każdym kaflu |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | położenie osi na szwie [m] | (762635.00, 609811.11) | (762635.00, 609811.11) | 0 | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | referencja rozstawu linii (lewa) 6.5–6.9 m | 6.7 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 24,6 = 6,0 m, km 25,0 = 6,1 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | referencja rozstawu linii (prawa) 6.5–6.9 m | — | 6.7 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 24,6 = 6,0 m, km 25,0 = 6,1 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | szerokość jezdni [m] | 8 | 8 | 0 | OK | derived:network |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | pasy × szer. pasa [m] | 2 × 3.65 | 2 × 3.65 | — | OK | derived:network |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | opaska (edge_strip) [m] | 0.35 | 0.35 | 0 | OK | derived:network |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | rozstaw linii krawędziowych [m] | 7.3 | 7.3 | 0 | OK | derived:network (authored_override:dk65-edge-line-spacing-0304) |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | krawędź asfaltu P [m od osi] | 4.08 | 4.08 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | pobocze P | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | krawędź asfaltu L [m od osi] | 4.08 | 4.08 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | pobocze L | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | oświetlenie | brak (override) | brak (override) | — | OK | derived:network |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | wys. terenu w osi Z [m] | 116.9 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2022-knyszyn-s) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2022-knyszyn) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2022 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | szer. jezdni ostatni build [m] | 8 | 8 | 0 | OK | generated:roads_qa |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | położenie osi na szwie [m] | (760985.78, 611583.00) | (760985.78, 611583.00) | 0 | OK | derived:network |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | referencja rozstawu linii (lewa) 7.1–7.5 m | 7.3 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 26,0 / 27,0 = 6,8 m (Obozowa); ADR 0212: 6,8 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| knyszyn-s / knyszyn | w286990127 primary (trasa) | referencja rozstawu linii (prawa) 7.1–7.5 m | — | 7.3 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 26,0 / 27,0 = 6,8 m (Obozowa); ADR 0212: 6,8 m; ADR 0306 D94: +0.25 m/pas (2 pasy) |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | szerokość jezdni [m] | 8 | 8 | 0 | OK | derived:network |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | pasy × szer. pasa [m] | 2 × 3.65 | 2 × 3.65 | — | OK | derived:network |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | opaska (edge_strip) [m] | 0.35 | 0.35 | 0 | OK | derived:network |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | rozstaw linii krawędziowych [m] | 7.3 | 7.3 | 0 | OK | derived:network (authored_override:dk65-edge-line-spacing-0304) |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | linia środkowa | P-1b przerywana (2/4) | P-1b przerywana (2/4) | — | OK | derived:network |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | krawędź asfaltu P [m od osi] | 4.08 | 4.08 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | pobocze P | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | krawędź asfaltu L [m od osi] | 4.08 | 4.08 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | pobocze L | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | wys. terenu w osi Z [m] | 123.41 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2022-knyszyn) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2022-knyszyn-w) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2022 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | szer. jezdni ostatni build [m] | 8 | 8 | 0 | OK | generated:roads_qa |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | położenie osi na szwie [m] | (760587.00, 612073.70) | (760587.00, 612073.70) | 0 | OK | derived:network |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | referencja rozstawu linii (lewa) 7.1–7.5 m | 7.3 | — | — | OK | ADR 0212 p.1: DK65 na Mońki 6,8 m linia-linia (ortofoto 0,1 m 2025); ADR 0306 D94: +0.25 m/pas (2 pasy) |
| knyszyn / knyszyn-w | w232511646 primary (trasa) | referencja rozstawu linii (prawa) 7.1–7.5 m | — | 7.3 | — | OK | ADR 0212 p.1: DK65 na Mońki 6,8 m linia-linia (ortofoto 0,1 m 2025); ADR 0306 D94: +0.25 m/pas (2 pasy) |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | szerokość jezdni [m] | 8 | 8 | 0 | OK | derived:network |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | pasy × szer. pasa [m] | 2 × 3.65 | 2 × 3.65 | — | OK | derived:network |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | opaska (edge_strip) [m] | 0.35 | 0.35 | 0 | OK | derived:network |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | rozstaw linii krawędziowych [m] | 7.3 | 7.3 | 0 | OK | derived:network (authored_override:dk65-edge-line-spacing-0304) |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | krawędź asfaltu P [m od osi] | 4.08 | 4.08 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | pobocze P | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | krawędź asfaltu L [m od osi] | 4.08 | 4.08 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | pobocze L | wiejski: utw. 0,08 + grunt 1,00 + rów | wiejski: utw. 0,08 + grunt 1,00 + rów | — | OK | derived:network (assign_sides, 2. przebieg) |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | oświetlenie | brak (override) | brak (override) | — | OK | derived:network |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | wys. terenu w osi Z [m] | 123.42 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2022-knyszyn-w) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2022-dk65-monki-01) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2022 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | szer. jezdni ostatni build [m] | 8 | 8 | 0 | OK | generated:roads_qa |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | położenie osi na szwie [m] | (759428.06, 613631.00) | (759428.06, 613631.00) | 0 | OK | derived:network |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | referencja rozstawu linii (lewa) 7.1–7.5 m | 7.3 | — | — | OK | ADR 0212 p.1: 6,8 m linia-linia (dk65-monki-01, 7 przekrojów); ADR 0306 D94: +0.25 m/pas (2 pasy) |
| knyszyn-w / dk65-monki-01 | w232511647 primary (trasa) | referencja rozstawu linii (prawa) 7.1–7.5 m | — | 7.3 | — | OK | ADR 0212 p.1: 6,8 m linia-linia (dk65-monki-01, 7 przekrojów); ADR 0306 D94: +0.25 m/pas (2 pasy) |
| knyszyn-w / dw671-tykocin-01 | w70329870 secondary (trasa) | szerokość jezdni [m] | 7 | 7 | 0 | OK | derived:network |
| knyszyn-w / dw671-tykocin-01 | w70329870 secondary (trasa) | pasy × szer. pasa [m] | 2 × 3.25 | 2 × 3.25 | — | OK | derived:network |
| knyszyn-w / dw671-tykocin-01 | w70329870 secondary (trasa) | opaska (edge_strip) [m] | 0.25 | 0.25 | 0 | OK | derived:network |
| knyszyn-w / dw671-tykocin-01 | w70329870 secondary (trasa) | rozstaw linii krawędziowych [m] | — | — | — | OK | derived:network |
| knyszyn-w / dw671-tykocin-01 | w70329870 secondary (trasa) | szer. linii krawędziowej [m] | — | — | — | OK | derived:network |
| knyszyn-w / dw671-tykocin-01 | w70329870 secondary (trasa) | linia krawędziowa L | brak | brak | — | OK | derived:network |
| knyszyn-w / dw671-tykocin-01 | w70329870 secondary (trasa) | linia krawędziowa P | brak | brak | — | OK | derived:network |
| knyszyn-w / dw671-tykocin-01 | w70329870 secondary (trasa) | linia środkowa | P-1b przerywana (2/4) | P-1b przerywana (2/4) | — | OK | derived:network |
| knyszyn-w / dw671-tykocin-01 | w70329870 secondary (trasa) | krawędź asfaltu P [m od osi] | 3.5 | 3.5 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| knyszyn-w / dw671-tykocin-01 | w70329870 secondary (trasa) | pobocze P | krawężnik + chodnik 2.00 | krawężnik + chodnik 2.00 | — | OK | derived:network (assign_sides, 2. przebieg) |
| knyszyn-w / dw671-tykocin-01 | w70329870 secondary (trasa) | krawędź asfaltu L [m od osi] | 3.5 | 3.5 | 0 | OK | derived:network (hw + pobocze utwardzone) |
| knyszyn-w / dw671-tykocin-01 | w70329870 secondary (trasa) | pobocze L | krawężnik + chodnik 2.00 | krawężnik + chodnik 2.00 | — | OK | derived:network (assign_sides, 2. przebieg) |
| knyszyn-w / dw671-tykocin-01 | w70329870 secondary (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| knyszyn-w / dw671-tykocin-01 | w70329870 secondary (trasa) | wys. terenu w osi Z [m] | — | 118.28 | — | N/D | brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2022-knyszyn-w) / graph:z_terrain (NMT gugik-nmt-2022-dw671-tykocin-01) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2022 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| knyszyn-w / dw671-tykocin-01 | w70329870 secondary (trasa) | szer. jezdni ostatni build [m] | 7 | 7 | 0 | OK | generated:roads_qa |
| knyszyn-w / dw671-tykocin-01 | w70329870 secondary (trasa) | położenie osi na szwie [m] | (760129.19, 611583.00) | (760129.19, 611583.00) | 0 | OK | derived:network |
