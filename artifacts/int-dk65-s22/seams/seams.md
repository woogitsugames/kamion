## Szwy — podsumowanie

| para | szew | dróg | na trasie | FAIL | UWAGA |
|---|---|---|---|---|---|
| dk65-01 / dk65-02 | y = 597247 | 13 | 1 | 0 | 0 |
| dk65-02 / dk65-03 | x = 768779 | 2 | 1 | 0 | 0 |
| dk65-03 / dk65-04 | y = 599295 | 3 | 1 | 0 | 0 |
| dk65-04 / dk65-05 | y = 601343 | 8 | 1 | 0 | 5 |
| dk65-05 / dk65-06 | y = 603391 | 3 | 1 | 0 | 0 |
| dk65-06 / dk65-07 | x = 766731 | 2 | 1 | 0 | 0 |
| dk65-07 / dk65-08 | y = 605439 | 1 | 1 | 0 | 0 |
| dk65-08 / dk65-09 | x = 764683 | 3 | 1 | 0 | 0 |
| dk65-09 / dk65-10 | y = 607487 | 1 | 1 | 0 | 0 |
| dk65-10 / dk65-11 | y = 609535 | 1 | 1 | 0 | 0 |
| dk65-11 / knyszyn-s | x = 762635 | 1 | 1 | 2 | 0 |

## FAIL

| para | droga / id | parametr | lewa | prawa | Δ | wynik | źródło |
|---|---|---|---|---|---|---|---|
| dk65-04 / dk65-05 | w176274699 residential | pobocze P | krawężnik | krawężnik + chodnik 2.00 | — | UWAGA | derived:network (assign_sides, 1. przebieg) — dk65-05: oś biegnie wzdłuż szwu (/cos/ = 0.07) |
| dk65-04 / dk65-05 | w176274699 residential | położenie osi na szwie [m] | (768247.66, 601343.00) | (768248.24, 601343.00) | 0.584 | UWAGA | derived:network — dk65-05: oś biegnie wzdłuż szwu (/cos/ = 0.07) |
| dk65-04 / dk65-05 | w244403508 tertiary | droga po drugiej stronie | c:w1428963539:840039845-839428386 | — | — | UWAGA | derived:network — droga urywa się na szwie (brak końca łańcucha po prawej stronie w ±5 m); dk65-04: oś biegnie wzdłuż szwu (/cos/ = 0.08) |
| dk65-04 / dk65-05 | w1024956363 tertiary | pobocze P | krawężnik + chodnik 2.00 | krawężnik | — | UWAGA | derived:network (assign_sides, 1. przebieg) — dk65-05: łańcuch 8.2 m (< 15 m, kikut przy węźle) |
| dk65-04 / dk65-05 | w1024956363 tertiary | pobocze L | krawężnik + chodnik 2.00 | krawężnik | — | UWAGA | derived:network (assign_sides, 1. przebieg) — dk65-05: łańcuch 8.2 m (< 15 m, kikut przy węźle) |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | pasy × szer. pasa [m] | 2 × 3.10 | 2 × 3.55 | — | FAIL | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | szer. jezdni ostatni build [m] | 6.6 | 7.5 | 0.9 | FAIL | generated:roads_qa |

## Drogi trasy — wszystkie parametry

| para | droga / id | parametr | lewa | prawa | Δ | wynik | źródło |
|---|---|---|---|---|---|---|---|
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | szerokość jezdni [m] | 6.5 | 6.5 | 0 | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | pasy × szer. pasa [m] | 2 × 3.00 | 2 × 3.00 | — | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | opaska (edge_strip) [m] | 0.25 | 0.25 | 0 | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | rozstaw linii krawędziowych [m] | 6.2 | 6.2 | 0 | OK | derived:network (authored_override:dk65-k1-edge-line-spacing) |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | linia środkowa | P-1b przerywana (2/4) | P-1b przerywana (2/4) | — | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | pobocze P | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | pobocze L | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | wys. terenu w osi Z [m] | 124.27 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-01) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-02) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | szer. jezdni ostatni build [m] | 6.5 | 6.5 | 0 | OK | generated:roads_qa |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | położenie osi na szwie [m] | (770244.58, 597247.00) | (770244.58, 597247.00) | 0 | OK | derived:network |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | referencja rozstawu linii (lewa) 6.0–6.4 m | 6.2 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 9,0 = 6,2 m, km 10,0 = 6,4 m |
| dk65-01 / dk65-02 | w396566354 secondary (trasa) | referencja rozstawu linii (prawa) 6.0–6.4 m | — | 6.2 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 9,0 = 6,2 m, km 10,0 = 6,4 m |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | szerokość jezdni [m] | 6.6 | 6.6 | 0 | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | pasy × szer. pasa [m] | 2 × 3.05 | 2 × 3.05 | — | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | opaska (edge_strip) [m] | 0.25 | 0.25 | 0 | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | rozstaw linii krawędziowych [m] | 6.2 | 6.2 | 0 | OK | derived:network (authored_override:dk65-k1-edge-line-spacing) |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | linia krawędziowa L | przerywana (dk65-02-k1-dashed-elcka-l) | przerywana (dk65-03-k1-dashed-elcka-l) | — | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | linia krawędziowa P | przerywana (dk65-02-k1-dashed-elcka-p) | przerywana (dk65-03-k1-dashed-elcka-p) | — | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | pobocze P | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | pobocze L | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | wys. terenu w osi Z [m] | 113.96 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-02) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-03) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | szer. jezdni ostatni build [m] | 6.6 | 6.6 | 0 | OK | generated:roads_qa |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | położenie osi na szwie [m] | (768779.00, 598817.91) | (768779.00, 598817.91) | 0 | OK | derived:network |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | referencja rozstawu linii (lewa) 6.0–6.4 m | 6.2 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 11,5 = 6,1 m, km 12,0 = 6,1 m |
| dk65-02 / dk65-03 | w1024956365 secondary (trasa) | referencja rozstawu linii (prawa) 6.0–6.4 m | — | 6.2 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 11,5 = 6,1 m, km 12,0 = 6,1 m |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | szerokość jezdni [m] | 6.6 | 6.6 | 0 | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | pasy × szer. pasa [m] | 2 × 3.05 | 2 × 3.05 | — | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | opaska (edge_strip) [m] | 0.25 | 0.25 | 0 | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | rozstaw linii krawędziowych [m] | 6.2 | 6.2 | 0 | OK | derived:network (authored_override:dk65-k1-edge-line-spacing) |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | linia krawędziowa L | przerywana (dk65-03-k1-dashed-elcka-l) | przerywana (dk65-04-k1-dashed-elcka-l) | — | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | linia krawędziowa P | przerywana (dk65-03-k1-dashed-elcka-p) | przerywana (dk65-04-k1-dashed-elcka-p) | — | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | pobocze P | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | pobocze L | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | wys. terenu w osi Z [m] | 115.36 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-03) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-04) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | szer. jezdni ostatni build [m] | 6.6 | 6.6 | 0 | OK | generated:roads_qa |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | położenie osi na szwie [m] | (768694.97, 599295.00) | (768694.97, 599295.00) | 0 | OK | derived:network |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | referencja rozstawu linii (lewa) 6.0–6.4 m | 6.2 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 12,0 = 6,1 m, km 12,5 = 6,2 m |
| dk65-03 / dk65-04 | w1024956365 secondary (trasa) | referencja rozstawu linii (prawa) 6.0–6.4 m | — | 6.2 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 12,0 = 6,1 m, km 12,5 = 6,2 m |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | szerokość jezdni [m] | 6.6 | 6.6 | 0 | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | pasy × szer. pasa [m] | 2 × 3.05 | 2 × 3.05 | — | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | opaska (edge_strip) [m] | 0.25 | 0.25 | 0 | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | rozstaw linii krawędziowych [m] | 6.2 | 6.2 | 0 | OK | derived:network (authored_override:dk65-k1-edge-line-spacing) |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | pobocze P | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | pobocze L | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | wys. terenu w osi Z [m] | 149.1 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-04) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-05) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | szer. jezdni ostatni build [m] | 6.6 | 6.6 | 0 | OK | generated:roads_qa |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | położenie osi na szwie [m] | (768334.87, 601343.00) | (768334.87, 601343.00) | 0 | OK | derived:network |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | referencja rozstawu linii (lewa) 6.0–6.4 m | 6.2 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 14,0 = 6,2 m, km 14,5 = 6,2 m |
| dk65-04 / dk65-05 | w1024956364 secondary (trasa) | referencja rozstawu linii (prawa) 6.0–6.4 m | — | 6.2 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 14,0 = 6,2 m, km 14,5 = 6,2 m |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | szerokość jezdni [m] | 6.6 | 6.6 | 0 | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | pasy × szer. pasa [m] | 2 × 3.05 | 2 × 3.05 | — | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | opaska (edge_strip) [m] | 0.25 | 0.25 | 0 | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | rozstaw linii krawędziowych [m] | 6.2 | 6.2 | 0 | OK | derived:network (authored_override:dk65-k1-edge-line-spacing) / derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | pobocze P | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | pobocze L | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | oświetlenie | reguła klasy | reguła klasy | — | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | wys. terenu w osi Z [m] | 163.2 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-05) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-06) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | szer. jezdni ostatni build [m] | 6.6 | 6.6 | 0 | OK | generated:roads_qa |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | położenie osi na szwie [m] | (767660.42, 603391.00) | (767660.42, 603391.00) | 0 | OK | derived:network |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | referencja rozstawu linii (lewa) 6.0–6.4 m | 6.2 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 16,0 = 6,2 m, km 17,0 = 6,1 m |
| dk65-05 / dk65-06 | w1560819273 secondary (trasa) | referencja rozstawu linii (prawa) 6.0–6.4 m | — | 6.2 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 16,0 = 6,2 m, km 17,0 = 6,1 m |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | szerokość jezdni [m] | 6.6 | 6.6 | 0 | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | pasy × szer. pasa [m] | 2 × 3.10 | 2 × 3.10 | — | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | opaska (edge_strip) [m] | 0.2 | 0.2 | 0 | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | rozstaw linii krawędziowych [m] | 6.2 | 6.2 | 0 | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | pobocze P | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | pobocze L | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | oświetlenie | brak (override) | brak (override) | — | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | wys. terenu w osi Z [m] | 155.42 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-06) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-07) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | szer. jezdni ostatni build [m] | 6.6 | 6.6 | 0 | OK | generated:roads_qa |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | położenie osi na szwie [m] | (766731.00, 604722.19) | (766731.00, 604722.19) | 0 | OK | derived:network |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | referencja rozstawu linii (lewa) 6.0–6.4 m | 6.2 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 18,0 = 6,0 m, km 19,0 = 6,4 m |
| dk65-06 / dk65-07 | w208187096 primary (trasa) | referencja rozstawu linii (prawa) 6.0–6.4 m | — | 6.2 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 18,0 = 6,0 m, km 19,0 = 6,4 m |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | szerokość jezdni [m] | 6.6 | 6.6 | 0 | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | pasy × szer. pasa [m] | 2 × 3.10 | 2 × 3.10 | — | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | opaska (edge_strip) [m] | 0.2 | 0.2 | 0 | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | rozstaw linii krawędziowych [m] | 6.2 | 6.2 | 0 | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | pobocze P | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | pobocze L | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | oświetlenie | brak (override) | brak (override) | — | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | wys. terenu w osi Z [m] | 147.27 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-07) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-08) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | szer. jezdni ostatni build [m] | 6.6 | 6.6 | 0 | OK | generated:roads_qa |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | położenie osi na szwie [m] | (766246.20, 605439.00) | (766246.20, 605439.00) | 0 | OK | derived:network |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | referencja rozstawu linii (lewa) 6.0–6.4 m | 6.2 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 19,0 = 6,4 m, km 20,0 = 6,0 m |
| dk65-07 / dk65-08 | w27718745 primary (trasa) | referencja rozstawu linii (prawa) 6.0–6.4 m | — | 6.2 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 19,0 = 6,4 m, km 20,0 = 6,0 m |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | szerokość jezdni [m] | 6.6 | 6.6 | 0 | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | pasy × szer. pasa [m] | 2 × 3.10 | 2 × 3.10 | — | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | opaska (edge_strip) [m] | 0.2 | 0.2 | 0 | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | rozstaw linii krawędziowych [m] | 6.2 | 6.2 | 0 | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | pobocze P | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | pobocze L | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | oświetlenie | brak (override) | brak (override) | — | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | wys. terenu w osi Z [m] | 130.28 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-08) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-09) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | szer. jezdni ostatni build [m] | 6.6 | 6.6 | 0 | OK | generated:roads_qa |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | położenie osi na szwie [m] | (764683.00, 607186.77) | (764683.00, 607186.77) | 0 | OK | derived:network |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | referencja rozstawu linii (lewa) 6.0–6.4 m | 6.2 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 21,0 = 6,25 m, km 21,65 = 6,1 m |
| dk65-08 / dk65-09 | w27718745 primary (trasa) | referencja rozstawu linii (prawa) 6.0–6.4 m | — | 6.2 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 21,0 = 6,25 m, km 21,65 = 6,1 m |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | szerokość jezdni [m] | 6.6 | 6.6 | 0 | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | pasy × szer. pasa [m] | 2 × 3.10 | 2 × 3.10 | — | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | opaska (edge_strip) [m] | 0.2 | 0.2 | 0 | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | rozstaw linii krawędziowych [m] | 6.2 | 6.2 | 0 | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | pobocze P | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | pobocze L | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | oświetlenie | brak (override) | brak (override) | — | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | wys. terenu w osi Z [m] | 129.14 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-09) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2025-dk65-10) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2025 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | szer. jezdni ostatni build [m] | 6.6 | 6.6 | 0 | OK | generated:roads_qa |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | położenie osi na szwie [m] | (764498.56, 607487.00) | (764498.56, 607487.00) | 0 | OK | derived:network |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | referencja rozstawu linii (lewa) 6.0–6.4 m | 6.2 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 21,65 = 6,1 m, km 22,0 = 6,1 m |
| dk65-09 / dk65-10 | w27718745 primary (trasa) | referencja rozstawu linii (prawa) 6.0–6.4 m | — | 6.2 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 21,65 = 6,1 m, km 22,0 = 6,1 m |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | szerokość jezdni [m] | 6.6 | 6.6 | 0 | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | pasy × szer. pasa [m] | 2 × 3.10 | 2 × 3.10 | — | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | opaska (edge_strip) [m] | 0.2 | 0.2 | 0 | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | rozstaw linii krawędziowych [m] | 6.2 | 6.2 | 0 | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | pobocze P | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | pobocze L | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | oświetlenie | brak (override) | brak (override) | — | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | wys. terenu w osi Z [m] | 132.87 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2025-dk65-10) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2022-dk65-11) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Różne roczniki NMT (2025 / 2022): możliwy skok terenu ≤ 0,5 m (ADR 0214) |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | szer. jezdni ostatni build [m] | 6.6 | 6.6 | 0 | OK | generated:roads_qa |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | położenie osi na szwie [m] | (762892.90, 609535.00) | (762892.90, 609535.00) | 0 | OK | derived:network |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | referencja rozstawu linii (lewa) 6.0–6.4 m | 6.2 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 24,0 = 6,1 m, km 24,6 = 6,0 m (mediana korytarza 6,2) |
| dk65-10 / dk65-11 | w27718745 primary (trasa) | referencja rozstawu linii (prawa) 6.0–6.4 m | — | 6.2 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 24,0 = 6,1 m, km 24,6 = 6,0 m (mediana korytarza 6,2) |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | szerokość jezdni [m] | 6.6 | 6.6 | 0 | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | pasy × szer. pasa [m] | 2 × 3.10 | 2 × 3.55 | — | FAIL | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | opaska (edge_strip) [m] | 0.2 | 0.2 | 0 | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | rozstaw linii krawędziowych [m] | 6.2 | 6.2 | 0 | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | szer. linii krawędziowej [m] | 0.12 | 0.12 | 0 | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | linia krawędziowa L | ciągła | ciągła | — | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | linia krawędziowa P | ciągła | ciągła | — | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | linia środkowa | P-1a przerywana (4/8) | P-1a przerywana (4/8) | — | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | pobocze P | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | pobocze L | wiejski: utw. 1,00 + żwir 0,75 + rów | wiejski: utw. 1,00 + żwir 0,75 + rów | — | OK | derived:network (assign_sides, 1. przebieg) |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | oświetlenie | brak (override) | brak (override) | — | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | wys. terenu w osi Z [m] | 144.18 | — | — | N/D | graph:z_terrain (NMT gugik-nmt-2022-dk65-11) / brak (z_terrain = null na krawędzi S/E kafla; NMT gugik-nmt-2022-knyszyn-s) — Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. Oba kafle: NMT 2022 - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, wymaga Data/raw) |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | szer. jezdni ostatni build [m] | 6.6 | 7.5 | 0.9 | FAIL | generated:roads_qa |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | położenie osi na szwie [m] | (762635.00, 609811.11) | (762635.00, 609811.11) | 0 | OK | derived:network |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | referencja rozstawu linii (lewa) 6.0–6.4 m | 6.2 | — | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 24,6 = 6,0 m, km 25,0 = 6,1 m |
| dk65-11 / knyszyn-s | w27718745 primary (trasa) | referencja rozstawu linii (prawa) 6.0–6.4 m | — | 6.2 | — | OK | research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel): km 24,6 = 6,0 m, km 25,0 = 6,1 m |
