# Audyt oznakowania generatora — 2026-11-16 (D21, ADR 0279)
Gałąź `signs-audit-0279`. Źródła, wydania i sha256: ADR 0279. Skróty: **Z1** = Dz.U. 2019 poz. 2311 zał. 1
(`D20192311-c1.pdf`, strona PDF), **Z2** = zał. 2 (plik ELI typu I, strona Dz.U. = PDF + 525), **2310** = Dz.U. 2019
poz. 2310, **1105** = Dz.U. 2025 poz. 1105, **2377** = Dz.U. 2022 poz. 2377 (tab. 1.11), **132** = Dz.U. 2026 poz. 132.
Brak nowszego tekstu jednolitego 2311/2310 (API ELI 2026-11-16). Priorytety: **P1** decyzje kierowcy / bezpieczeństwo
jazdy ciężarówką, **P2** realizm, **P3** kosmetyka. „gen.” = generator w `main` (b. tej gałęzi).

## 1. Tabela zgodności: znaki pionowe
| Typ | Gen.? (gdzie) | Wymiar / grupa | Wys. montażu (dolna krawędź) | Od krawędzi jezdni | Od miejsca niebezpiecznego / skrzyżowania | Zgodność |
|---|---|---|---|---|---|---|
| A-7 (podporządk.) | tak, reguła `furniture.py:760` + OSM | 900 mm (S), Z1 tab. 1.1 s. 9 ✓ | 2,00 / 2,20 chodnik ✓ (2377) | kraw. 0,15 + 0,75 = 0,90 m ✓ (0,5–2,0) | 3 m za łatą skrzyżowania ✓ (≤ 25 / ≤ 50 m, Z1 s. 64) | **brak A-7 + T-1 150–300 m przy v > 60 (Z1 s. 64) — P1** |
| B-20 | tak, `furniture.py:760` (węzeł `highway=stop`) | ośmiokąt Ø800 wpis. ✓ | ✓ | ✓ | ≤ 25 m ✓ | brak A-7 + „Stop” 150–300 m przy v > 60 (Z1 s. 126) P1; **P-13 zamiast P-12** (tab. 2) P1 |
| A-7 + C-12 (rondo) | tak, `furniture.py:748` | 900 / 800 ✓ | ✓ | ✓ | 3 m, ≤ 25 m ✓ (Z1 s. 170) | zgodne |
| A-8 (rondo) | **nie** | — | — | — | 150–300 / ≤ 100 m | wymagany, gdy brak E-1 i rondo poza obszarem zabud. / słabo widoczne (132 pkt 2.2.9). Rondo kompaktowe Knyszyn (DK65) nie dostaje E-1 (`signs_route.py:46` R ≥ 18 m) → **P1** |
| E-1 przed rondem | tak (R ≥ 18 m, GP/G) | ADR 0236 ✓ | 2,00 ✓ (poza zabud. dopuszcz. 1,00) | ✓ | 80 m (≤ 100 m w mieście ✓; poza miastem 150–300 m) | zgodne w C; zamiejskie — P2 |
| D-1 | tak, `furniture.py:762` każde skrzyżowanie | romb bok 600 ✓; powtórzenia 400 mm (Z1 s. 185) gen. 600 — P3 | ✓ | ✓ | — | **poza obszarem zabud. D-1 tylko z T-6a; zamiast niego A-6a–e 150–300 m** (Z1 s. 64, 185) — P2 |
| A-6a–e | **nie** | 900 | 2,00 | | 150–300 m (v > 60) | P2 (ostrzeżenie kierowcy drogi głównej DK65) |
| B-33 | tak, reguła 30 m za skrzyżowaniem gdy v ≠ 50 (`furniture.py:779`) + OSM `PL:B-33[n]` | Ø800 ✓ | ✓ | ✓ | — | **17 węzłów OSM `traffic_sign=maxspeed` + `maxspeed=n` pomijanych** (`signs_route.py:85`; dojlidy 7, kleeberga 4, knyszyn 4, knyszyn-w 1, dk65-01 1) — P1; zmiana limitu w środku łańcucha bez znaku — P2 |
| D-42 / D-43 | **nie** | 1200 × 700 (Z1 s. 244) | 2,00 | | granica obszaru zabud. | **P1** (limit 50 km/h, zakaz B-, wg prawa o ruchu); OSM `traffic_sign=city_name` (knyszynska 1) pomijany |
| D-6 | tak, `furniture.py:830` | kwadrat 600 ✓ | 2,00/2,20 ✓ | ✓ | 0,5 m od krawędzi P-10 ✓ (Z1 s. 198) | brak powtórzenia po lewej na jezdniach jednokierunkowych (Z1 s. 198) — P2 |
| A-16 | **nie** | 900 | | | ≤ 100 / 150–300 | 132: tylko gdy przejście może nie być widoczne — P2 na DK65 zamiejskiej |
| B-5 | **nie w katalogu** (`signs.FACES`, s. 743) | Ø800 | | | | 3 węzły OSM (dojlidy) → `unknown` — **P1** |
| B-18 / B-19 / B-16 | **nie w katalogu**; parser liczb tylko dla B-33 (`signs_route.py:65`) | Ø800 + liczba | | | | B-18 2 węzły OSM (knyszyn) bez wartości w OSM → nie zmyślać tonażu, zdjęcie/`maxweight` — **P1** |
| A-17, A-5, A-11, B-35, B-31, D-5, D-51 | nie w katalogu | | | | | 11 węzłów OSM → `unknown` — P2 |
| A-9 / A-10 | tak, `rail_approach.py` (ADR 0268) | 900 ✓ | ≥ 2,00 nad tablicą/G-1 ✓ (lub 1,50 przy kilku znakach, przyp. 5 tab. 1.11) | RURAL: za poboczem +0,5 ✓ | 150 m (v > 60) ✓ / 100 m ✓ (§ 3 ust. 2 2310; Z1 s. 50) | zgodne; zalecane dla 90 km/h 250–300 m (Z1 s. 50) — P2 |
| G-1a–c | tak | **300 × 1000 ✓** (rys. 9.8.1, s. 507) | gen. 1,00 m wszędzie; **tab. 1.11 przyp. 3: 0,50 m poza ulicami** (DW671, DK65) — P2 | ✓ | tab. 2.2 s. 67: 150/100/50 i 100/66,7/33,3 m ✓ (test) | G-1b/c na wysokości G-1a ✓ (s. 67) |
| G-1d–f (lewe) | tylko jezdnia jednokierunkowa | ✓ | | | | warunek Z1 s. 68: także v > 60 i widoczność < 100 m — P2 (brak danych widoczności) |
| T-SA „Sygnalizacja automatyczna” | tak | 0,90 × 0,36 UNVERIFIED (brak wzoru w 1105 i Z1) | | | pod A-9/A-10, kat. B i C ✓ (1105 § 79 pkt 6) | P3 |
| G-2 | tak | gen. 0,35 × 0,50 → **0,44 × 0,60 poprawione** (rys. 9.8.7 s. 510) | na maszcie pod głowicami ✓ (1105 § 81 ust. 1 pkt 1) | | | kat. D: pod krzyżem ✓ |
| G-3 / G-4 | tak (`rail.py`) | ramię gen. 1,20 × 0,20 → **1,40 × 0,15 poprawione**, kąt 50° ✓ (rys. 9.8.8–9.8.9) | gen. 1,50; G-2 pod krzyżem kończy się ~0,85 m < 1,50 (przyp. 5) — P2 | 1,0 m za jezdnią | **≥ 5 m od skrajnej szyny (Z1 s. 73); gen. ≈ 3,6 m** — P1 | |
| Sygnalizator przejazdu | tak (`rail.py`) | | | | **≥ 5 m od skrajnej szyny (1105 § 77 ust. 2 pkt 1); gen. ≈ 3,6 m** — P1 | |
| B-20 / P-12 przy przejeździe kat. D | nie | | | | | wymaga danych widoczności (1105 § 79 pkt 2) — P2 |
| T-7 | nie (flaga `t7_required`) | | | | | P2 |
| E-2 tablice regułowe | tak `furniture.py:876` | ADR 0236 | zawsze `SIGN_H_MIN` 2,00; na chodniku 2,20 — P3 | ≥ 0,5 ✓ | ≤ 50 m ✓ | |
| ogólne | — | barwa GREEN poza polem tolerancji (R1 §3.3) — P3 | | | odstęp między znakami ≥ 10/20/50 m wg v (pkt 1.5.3) nie sprawdzany (`pl.near` 1,5 m) — P2; tarcza odchylona 5° — P3 | |

## 2. Tabela zgodności: znaki poziome (Z2)
| Typ | Gen.? | Wymiary | Zasada | Zgodność |
|---|---|---|---|---|
| P-1a / P-1b | tak | 4/8 i 2/4 m × 0,12 ✓ (rys. 2.2.1.1–2, s. 533) | > 70 / ≤ 70 km/h ✓ | zgodne |
| P-4 | tak (≥ 4 pasy; dojazd do przejazdu 50 m) | 0,12 + 0,12 + 0,12 ✓ (rys. 2.2.1.10, s. 540) | 1105 § 79 pkt 4b ✓ | **brak P-6 przed P-4 poza obszarem zabud.** (s. 541: ≥ 100 m przy v > 70) — P2 |
| P-6 | **nie** | 4,0/2,0 × 0,12 (rys. 2.2.1.12) — dodane do `standards.DASH` | przed P-2a/P-3a/P-4 | P2 |
| P-7b | tylko A/S/GP z opaską, inne przez override (`markings.py:199`) | 0,24 / 0,12 ✓ | **drogi krajowe i wojewódzkie: linie krawędziowe na całej długości** (Z2 s. 526) — DW671 tylko overridem | P2 |
| P-10 | tak | 0,5/0,5, s = 4,0 m ✓ (s. 567) | 2,5–16 m dopuszczalne | zgodne |
| P-12 | **nie** przy B-20 (`markings.py:787` daje P-13) | 0,5 ✓ | przy B-20 obowiązkowa na nawierzchni bitumicznej (Z1 s. 126; Z2 s. 571) | **P1** |
| P-13 | tak (rondo, wloty podporządk.) | trójkąty 0,50/0,25/0,70 ✓ | ✓ | zgodne |
| P-14 (sygnalizacja) | tak, `markings.py:805` `d0 = trim + 0,6` | 0,75/0,25 × 0,5 ✓ | **≥ 2,0 m przed sygnalizatorem obok jezdni, ≥ 8,0 m przed nad jezdnią** (s. 573); sygnalizator stoi w `trim + 1,0` (`furniture.py:896`) → linia przy maszcie | **P1** (do potwierdzenia renderem `junctions_cameras`) |
| P-14 (przejazd kolejowy, przejście) | tak | ✓ | 2,0 m ✓ | zgodne (położenie zależy od P1 sygnalizatora) |
| P-11 | tak | 0,5/0,5, 1,8 / 3,0 m ✓ (s. 569) | | zgodne |
| P-8 strzałki | tak | 5,0 / 7,5 m ✓ | 15 / 30 m ✓ | zgodne |

## 3. Zmienione w tej gałęzi (dane/katalog) — testy `tests/gis/test_signs_audit_0279.py`
`streetscape/sign_norms.py` (nowa sekcja ADR 0279), `streetscape/signs.py` (`RECT` G-1/G-2 z rysunków, tekstura G-2),
`streetscape/rail.py` (`SIGN_ARM_L/W/ANGLE`), `roads/standards.py` (P-6, P1a/P1b min., P-4 odstęp, P-10 zakres,
`P14_BEFORE_OVERHEAD_SIGNAL`, komentarz tab. 1.11). Bez nowych prototypów/materiałów; trójkąty bez zmian.

## 4. Zadania dla lidera (pliki zablokowane / zmiana logiki) — proponowane diffy
**P1**
1. `streetscape/rail.py:79` + `rail.py:879/886/909` — sygnalizator, G-3/G-4, dzwon ≥ 5 m od skrajnej szyny:
   ```diff
   - post = pc - drive * (dtrack + SIGN_SETBACK) + right * (half_road + SIGN_LATERAL)
   + # 1105 § 77 ust. 2 pkt 1 / Z1 s. 73: >= 5 m from the outer rail (outer rail = max offset + gauge/2 + 0.04 m head)
   + d_rail = (max(abs(o) for o in t.offsets) + gauge_m / 2 + 0.04) / sin_t
   + post = pc - drive * max(dtrack + SIGN_SETBACK, d_rail + SN.ROAD_SIGNAL_MIN_FROM_OUTER_RAIL_M / sin_t) + ...
   ```
   (`rail_approach.device_line_m` liczy z tego samego `SIGN_SETBACK` → P-14 i słupki przesuną się same; testy
   `test_rail_approach_0268` z odległościami do aktualizacji.)
2. `roads/markings.py:787` — przy `highway=stop` (B-20 z `furniture.py:760`) P-12, nie P-13:
   ```diff
   - elif j.give_way or (rank > maxrank and maxrank <= RANK["G"]):
   + elif getattr(j, "stop", False):          # B-20 on this approach (same 25 m test as furniture.junction_signs)
   +     kind = "P-12"                        # Z2 pkt 4.2.3 s. 571: P-12 with B-20, width S.P12_W
   + elif j.give_way or (rank > maxrank and maxrank <= RANK["G"]):
   ```
3. `roads/markings.py:805` — P-14 na wlocie z sygnalizacją: `d0 = max(t + 0.6, sig_d + S.P14_BEFORE_SIGNAL)` gdzie
   `sig_d` = stacja głowicy z `furniture.signals` (`trim + 1,0`), a dla masztu z wysięgnikiem
   `S.P14_BEFORE_OVERHEAD_SIGNAL` (8,0 m). Najpierw render `junctions_cameras` C — czy linia stoi przy maszcie.
4. `streetscape/signs_route.py:85` — `traffic_sign=maxspeed` + `maxspeed=<n>` → `B-33_<n>`; `city_name` → D-42
   (kierunek wjazdu) / D-43; `parse_traffic_sign` z wartością dla `B-18/B-19/B-16/B-5` (`B-18_<t>` jak `B-33_<n>`),
   wartość z węzła lub `maxweight` drogi; bez wartości → `unknown` (nie zmyślać). `signs.FACES`: B-5, B-18_n,
   B-19_n (+1 materiał na kafel z takim znakiem; dojlidy, knyszyn — kafle zablokowane, regeneracja lidera).
5. `furniture.py:756–762` — przy v > 60 na wlocie podporządkowanym dodatkowy słupek A-7 + T-1 („150 m”) w
   `SN.A7_ADVANCE_T1_RANGE_M[0]`; przy B-20 A-7 + tablica „Stop 150 m” (Z1 s. 64, 126). Na DK65 poza obszarem
   zabudowanym na drodze głównej A-6a–e zamiast D-1 (Z1 s. 185).
6. D-42/D-43 — nowa reguła (`granica obszaru zabudowanego` z OSM `traffic_sign=city_name` / `place` + override);
   wymaga wzoru tablicy (nazwa miejscowości, bez marek) — P1 dla prędkości ciężarówki; ADR potrzebny.
7. A-8 przed rondem kompaktowym Knyszyn (`compact_roundabout.py`, zablokowany) gdy brak E-1: 150 m przed (v > 60).
**P2**
8. `rail_approach.py:62` `G1_BOTTOM_Z_M = 1.00` → `SN.g1_bottom_m(street=kind != RURAL)` (0,50 m na DW671/DK65); A-9
   nad G-1 przy kilku znakach na słupku ≥ 1,50 m (przyp. 5) — test `test_plate_stack_and_new_plate_shapes` (stała 1,0).
9. `rail.py:85` `SIGN_BOTTOM_Z` 1,50 → tak, by najniższy znak (G-2 pod krzyżem) miał ≥ 1,50 m: krzyż ≥ 2,15 m.
10. `markings.py:623–636` — P-6 przed P-4 dojazdu do przejazdu poza obszarem zabud. (`S.DASH["P-6"]`, `S.P6_MIN_LEN`).
11. `markings.py:199` — P-7b domyślnie dla dróg krajowych i wojewódzkich (Z2 s. 526), nie tylko klasy GP z opaską.
12. D-6 po lewej stronie jezdni jednokierunkowych (`furniture.py:822–833`); odstęp między znakami
    `SN.sign_spacing_min_m(v)`; A-9 na DW671 przy 90 km/h zalecane 250–300 m (`rail_approach.SIGN_DIST_FAST_M`).
13. Brakujące lica z OSM: A-17, A-5, A-11, B-35, B-31, D-5, D-51 (11 węzłów).
**P3**: D-1 powtarzany 400 mm; E-2 na chodniku 2,20 m (`furniture.py:876`); tarcza 5°; barwa GREEN (R1 §3.3); T-SA wzór.

## 5. Weryfikacja
`uv run --project tools/worldgen python -m pytest tests/gis -k "sign or marking or 0236 or 0279 or rail_approach" -q`
→ 172 passed, 1 skipped, 1 xfailed; `-k "rail or v34 or furniture"` → 198 passed, 3 skipped. Unity / render / telefon:
nie uruchamiane (chmura); `generated/*` nieregenerowane. Pętla wizualna po regeneracji: kamery `rail-x0-*`
(dw671-tykocin-01), `junctions_cameras` (C) — lider.
