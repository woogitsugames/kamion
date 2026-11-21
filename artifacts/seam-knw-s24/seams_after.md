## Szwy — podsumowanie

| para | szew | dróg | na trasie | FAIL | UWAGA | PRZEJŚCIE |
|---|---|---|---|---|---|---|
| knyszyn / knyszyn-w | x = 760587 | 10 | 1 | 0 | 0 | 0 |

## FAIL / UWAGA / PRZEJŚCIE

| para | droga / id | parametr | lewa | prawa | Δ | wynik | źródło |
|---|---|---|---|---|---|---|---|


## Drogi trasy — wszystkie parametry

| para | droga / id | parametr | lewa | prawa | Δ | wynik | źródło |
|---|---|---|---|---|---|---|---|
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
