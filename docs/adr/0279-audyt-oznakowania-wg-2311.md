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
