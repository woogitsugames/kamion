# ADR 0279 — audyt oznakowania generatora wg Dz.U. 2019 poz. 2311 (zał. 1 i 2), 2310 i 2025/1105
Status: Proposed (agent D21, chmura D r6, gałąź `signs-audit-0279`), 2026-11-16. Do scalenia przez lidera.
Raport z pełną tabelą i listą zadań dla lidera: `docs/reports/SIGNS-AUDIT-2026-11-16.md`.
Powiązane: ADR 0236 (znaki E, `sign_norms.py`), 0268 (dojazdy do przejazdów), 0217 (urządzenia przejazdów), research R1
(`research/cloud2/traffic-signs-catalog`).

## Źródła (przeczytane 2026-11-16, PDF z API ELI; strony = strona pliku PDF)
| Akt | Plik | sha256 | Zakres użyty |
|---|---|---|---|
| Dz.U. 2019 poz. 2311 (t.j. rozp. MI z 3.07.2003), zał. 1 | `D20192311-c1.pdf` (typ O) | `f94925ec…b550543` | tab. 1.1 s. 9, 1.11, pkt 2.1.2 s. 50, 2.2.8 s. 64, 2.2.10–2.2.11 s. 66–73 (tab. 2.2), 3.2.19–3.2.21 s. 123–126, 4.2.12 s. 170, 5.2.1 s. 185–186, 5.2.6 s. 198–199, 5.2.48 s. 244–245, rys. 9.8.1–9.8.9 s. 507–511 |
| ten sam akt, zał. 2–4 | `D20192311-c2.pdf` (typ **I**, 28 MB; plik typu O pod tą nazwą = c1) | `8abcce24…dfc5d5c4` | strona PDF k = strona Dz.U. 525 + k: tab. 2.1 s. 532, rys. 2.2.1.1–2.2.1.12 s. 533–541, pkt 4.2.1–4.2.5 s. 567–573 |
| Nowelizacje 2311 po t.j. | 2021 poz. 438, 2021 poz. 2066, **2022 poz. 2377** (tab. 1.11), **2026 poz. 132** (A-8 pkt 2.2.9, A-16 pkt 2.2.18) | — | API ELI 2026-11-16: brak nowszego tekstu jednolitego |
| Dz.U. 2019 poz. 2310 (znaki i sygnały, znaczenie) | `D20192310.pdf` | — | § 3 ust. 2, § 6, § 78 (przez ADR 0268); nowelizacje 2021/433, 2021/2065, 2022/2372, 2026/133 |
| Dz.U. 2025 poz. 1105 (przejazdy kolejowo-drogowe) | `text.pdf` | `c3caeb070b48…` | **§ 77 ust. 2** (sygnalizator ≥ 5 m od skrajnej szyny), § 79–81 |

## Decyzja
1. Liczby rozporządzenia dla znaków A–D i G oraz zasad umieszczania trafiają do `streetscape/sign_norms.py`
   (sekcja „ADR 0279”): wymiary wg grup (tab. 1.1), dobór grupy (pkt 1.2.1), wysokości montażu (tab. 1.11 w brzmieniu
   2022/2377, w tym E-1/E-2 poza obszarem zabudowanym 1,00 m, **G-1 1,00 m na ulicach / 0,50 m na innych drogach**),
   odległości znaków ostrzegawczych (pkt 2.1.2 + zalecenia wg v), A-7/B-20/C-12/D-6, tab. 2.2 (G-1), wymiary G-1/G-2/G-3,
   odległości urządzeń przejazdu od szyny (pkt 2.2.11, 1105 § 77 ust. 2). Każda stała ma tabelę/punkt i stronę.
2. Poprawione liczby katalogu (zmiana wyglądu po następnej regeneracji lidera, bez wpływu na liczbę trójkątów):
   - `signs.RECT["G-2"]` 0,35 × 0,50 m (WORKING_VALUE z wzoru barwnego) → **0,44 × 0,60 m** (rys. 9.8.7); tekstura G-2
     376 × 512 px (proporcja 440:600); G-1 0,30 × 1,00 m potwierdzone (rys. 9.8.1) — SOURCED;
   - `rail.SIGN_ARM_L/W` G-3/G-4 1,20 × 0,20 m → **1,40 × 0,15 m**, kąt 50° potwierdzony (rys. 9.8.8–9.8.9);
   - `roads/standards.py`: `DASH["P-6"]` 4,0/2,0 m (rys. 2.2.1.12), `P6_MIN_LEN` 50/100 m, `P1A/P1B_MIN_LEN`,
     `P4_LINE_GAP` 0,12 m (rys. 2.2.1.10 — generator zgodny), `P10_WIDTH_MIN_BUILT_UP` 2,5 / `P10_WIDTH_MAX` 16 m,
     **`P14_BEFORE_OVERHEAD_SIGNAL` 8,0 m** (pkt 4.2.5), komentarz tab. 1.11 (2,20 m także nad chodnikiem).
3. Zmiany logiki generatora (pliki zablokowane: `rail_approach.py`, kafle; lub zmiana reguł) **nie są** w tej gałęzi —
   lista P1/P2/P3 z plik:linia i proponowanym diffem w raporcie, do decyzji lidera. Najważniejsze P1: sygnalizatory
   i G-3 przejazdów ~3,6 m od skrajnej szyny (wymagane ≥ 5 m), P-14 na wlotach z sygnalizacją przy maszcie zamiast
   ≥ 2,0/8,0 m przed nim, P-13 zamiast P-12 przy B-20, brak D-42/D-43, brak A-7 + T-1 (v > 60), brak A-8 na rondzie
   zamiejskim bez E-1, znaki z OSM `traffic_sign=maxspeed` (17 węzłów) i B-5/B-18 (5 węzłów) pomijane, G-1 0,50 m.

## Konsekwencje
- Budżet: zero nowych prototypów i materiałów; G-2 i krzyż G-3 większe (te same trójkąty). Kamery C bez zmian
  (w regionie C brak przejazdów kolejowych i G-2).
- Testy: `tests/gis/test_signs_audit_0279.py` (8 testów na zmienione liczby, w tym zgodność `rail_approach` z tab. 2.2).
- Kod nie był uruchamiany w Unity; regeneracja `generated/*` — lider (jedna przebudowa).

## P1 — wdrożenie (D25, chmura D r7, gałąź `signs-p1-s23`, 2026-11-16)
Status: Proposed. Baza: PR #147 (`signs-audit-0279`, scalona do tej gałęzi). Źródła sprawdzone ponownie w PDF z API ELI
(sha256 jak wyżej; dodatkowo Dz.U. 2026 poz. 132 `text.pdf` sha256 `6b62d655…c3a6`, Prawo o ruchu drogowym t.j.
Dz.U. 2024 poz. 1251 `text.pdf` sha256 `de6c1f33…fccb`). Strony = strony Dz.U. (= strony pliku c1).

| # | Zmiana | Przepis (dosłownie sprawdzony) | Kod |
|---|---|---|---|
| 1 | Sygnalizator, G-3/G-4, dzwon ≥ 5 m od skrajnej szyny (odległość prostopadła do krawędzi główki szyny), rogatka ≥ 5 m od osi toru po osi drogi, sygnalizator przed rogatką; było ≈ 3,55 m | Dz.U. 2025 poz. 1105 **§ 77 ust. 2 pkt 1** („nie może wynosić mniej niż: 1) 5 m – dla przejazdu kolejowo-drogowego”), § 77 ust. 1 („bezpośrednio przed rogatką”), **§ 54 ust. 1** (rogatka, 5 m po osi drogi); Dz.U. 2019 poz. 2311 zał. 1 **pkt 2.2.11, s. 73** (G-3/G-4 „nie bliżej niż 5 m od skrajnej szyny”, bliżej tylko za zgodą zarządu kolei) | `rail.device_stations`, `rail_approach.device_line_m` (P-14 przejazdu, słupki U-1a, A-9/A-10 liczą się od niej) |
| 2 | P-14 na wlocie z sygnalizacją ≥ 2,0 m przed głowicą obok jezdni, ≥ 8,0 m przed głowicą nad jezdnią (wysięgnik); było trim + 0,6 m = przy maszcie (trim + 1,0) | zał. 2 **pkt 4.2.5, s. 573** (odległości mierzone od zewnętrznej krawędzi linii do płaszczyzny czołowej sygnalizatora) | `standards.p14_before_signal_d`, `signal_overhead` (wspólne z `furniture.signals`) |
| 3 | P-12 (linia ciągła 0,50 m) zamiast P-13 na wlocie z B-20 | zał. 2 **pkt 4.2.3, s. 571–572**; zał. 1 **pkt 3.2.21, s. 126** (B-20 na nawierzchni bitumicznej uzupełnia się linią P-12) | `junctions.Junction.stop` (ten sam test 25 m co `furniture.junction_signs`), `markings.approach_line_kind` |
| 4 | OSM: `traffic_sign=maxspeed`+`maxspeed` → B-33; `PL:B-5` → B-5; `PL:B-18[t]` / `maxweight` węzła → B-18 z wartością; `city_limit` → D-42 (+ D-43 w tym samym przekroju dla kierunku przeciwnego) | B-18: zał. 1 **pkt 3.2.19, s. 123** „Na znaku podaje się wartość wynikającą z rzeczywistej nośności” → B-18 bez liczby nie istnieje: **pomijany**, wpis `osm_signs.needs_value` w QA (nie zmyślamy tonażu); B-5 pkt 3.2.6 s. 109; D-43 pkt 5.2.49 s. 245 | `signs_route.parse_traffic_sign(v, tags)`, `signs.is_known/rect_size`, lica B-5, B-18_n, D-42/43, A-8, T-1; `sources.KEEP_TAGS` += `maxweight`, `traffic_sign:direction` |
| 5a | D-42/D-43 z reguły danych, gdy brak znaku OSM w promieniu 300 m: stacje drogi (GP/G/Z) w ≤ 60 m od BDOT10k OT_PTZB_A mieszkaniowej (jednorodzinna/wielorodzinna/zagrodowa) albo z krawężnikiem/chodnikiem = obszar; luka < 300 m bez pary; izolowany odcinek < 100 m nie jest obszarem | zał. 1 **pkt 5.2.48.1–5.2.48.2, s. 244–245** (300 m SOURCED; zabudowa mieszkaniowa, „początek chodnika”; nie handlowo-usługowa); 1200 × 700 mm | `streetscape/built_up.py` (`runs`, `boundaries`, `rule_signs`); 60 m / 100 m / klasy = WORKING_VALUE; granica ESTIMATED |
| 5b | A-7 + T-1 („150 m”) 150–300 m przed skrzyżowaniem na wlocie podporządkowanym (A-7), A-7 + tabliczka „Stop … m” przed B-20, gdy v_dop > 60 km/h (v z OSM, inaczej art. 20 PoRD: 50 w obszarze, 90 poza) | zał. 1 **pkt 2.2.8, s. 64**, **pkt 3.2.21, s. 126**, T-1 pkt 2.1.3 s. 50 (do 10 m), tabliczka h = 250 mm (Tabela 9.7.1, s. 487; szerokość WORKING_VALUE) | `built_up.advance_signs` (z `j.minor_signs` zapisanych przez `junction_signs`) |
| 5c | A-8 przed każdym rondem (także kompaktowym `compact_roundabout`), chyba że jest E-1 albo rondo w obszarze zabudowanym i widoczne; brak danych widoczności → widoczność przyjmowana tylko przy v ≤ 50 (UNVERIFIED); odległość: dolna granica zalecanej (pkt 2.1.2) | zał. 1 pkt 2.2.9 w brzmieniu **Dz.U. 2026 poz. 132** | `signs_route._a8`, `built_up.needs_a8` |

Niezmienione dane kafli (w tym knyszyn). Lider przy world3: przebudowa `streetscape_sources` (build_region — nowe
`maxweight`), potem build_world; render `rail-x0-*` (dw671), `junctions_cameras` (C), kamery DK65.

### Wpływ na kafle przy world3 (pomiar: stage znaków na prawdziwych danych kafli, wysokość płaska, bez Data/raw)
| Kafel | Nowe znaki pionowe | Linie |
|---|---|---|
| bialystok-dojlidy | B-5 ×3, B-33 z `traffic_sign=maxspeed` ×7 | P-12 ×2 (zamiast P-13), P-14 ×15 przesunięte |
| bialystok-kleeberga | B-33 ×4 | P-14 ×14 przesunięte |
| bialystok-industrial-c (C) | **0** (A-8: 5 wlotów z E-1, 2 zabudowane ≤ 50 / za krótkie) | P-14 ×27 przesunięte (ta sama liczba trójkątów) |
| bialystok-maczka / knyszynska | 0 (knyszynska: para reguły wygaszona przez OSM `city_name` w 265 m) | P-12 ×8 / ×2, P-14 ×18 |
| knyszyn | A-8 ×1 (DK65, OSM 90 km/h, 250 m), B-33 ×4; B-18 ×2 pominięte (`needs_value`, w bieżącym OSM `maxweight` 10 i 15 t — wejdą po przebudowie `streetscape_sources`) | P-12 ×6 |
| knyszyn-w / dk65-01 | B-33 ×1 / ×1 | knyszyn-w P-12 ×2 |
| dk65-02, dw671-tykocin-01 | D-42 + D-43 ×1 (reguła) | — |
| dk65-04 | D-42 + D-43 (OSM `city_limit`, Dobrzyniewo Duże) | — |
| dk65-08 | D-42 + D-43 ×3 (reguła) | dk65-06 P-12 ×1 |
| knyszyn-s | D-42 + D-43 ×2 (reguła) | — |
| dw671-tykocin-01 + kafle z przejazdami (dk65-01…04) | sygnalizatory / G-3 / rogatki odsunięte (≈ +1,6–2,9 m), U-1a i P-14 przejazdu za nimi; DW671: 23 z 24 słupków U-1a (ostatni w wylocie drogi bocznej) | — |
Razem ≈ 35 nowych zestawów (15 słupków reguł + ~20 z OSM). Budżet: zestaw = słupek 30 tris + tarcza 60–176 tris
(LoD0); +1 materiał/draw na nowy kod w kaflu (instancjonowanie). Region C: 0 nowych znaków, P-14 przesunięte
(trójkąty bez zmian) → budżet C neutralny (stretch_04 bez zmian). A-7 + T-1: reguła działa (testy), ale na kaflach
0 wystąpień — drogi podporządkowane mają krawężniki z generatora (= zabudowa → 50 km/h) i brak OSM `maxspeed` > 60.
