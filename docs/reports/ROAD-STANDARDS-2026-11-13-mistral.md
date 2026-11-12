# ROAD-STANDARDS-2026-11-13-mistral — audyt M36: parametry geometrii i wyposażenia dróg w generatorze vs źródła pierwotne

Data: 2026-11-13. Gałąź: `mistral/36-road-standards-audit` (od `origin/main` abe711ad). Zakres: stałe liczbowe opisujące
rzeczywiste obiekty drogowe w `tools/worldgen/roads/*.py` i `tools/worldgen/streetscape/{signs,signs_route,furniture,props}.py`.
Cel: każdy parametr ma źródło pierwotne albo uczciwe WORKING_VALUE; testy pilnują zgodności.
Nie zmieniono `Data/**/generated/**`, nie regenerowano świata. Brak źródeł mapowych (Google) i wtórnych jako potwierdzeń.

## 0. Źródła pierwotne i nowelizacje — każda sprawdzona w ISAP/ELI (2026-11-13)

| Akt | Status w ELI | Co zmienia (zweryfikowane) |
|---|---|---|
| **Dz.U. 2022 poz. 1518** (PTB2022, MI 24.06.2022) | obowiązujący; tekst odczytany z `api.sejm.gov.pl/eli/acts/DU/2022/1518/text.html` + `text.pdf` (PDF: § 1–33 w całości) | akt bazowy; § 17, 18, 20, 23, 24, 25, 26, 29, 33 zweryfikowane własnym odczytem; § 62 ust. 2, § 80 ust. 1, § 89 ust. 2 pkt 1 — cytaty z treści aktu (eli.gov.pl/isap + recenzja M18/M25 2026-11-12) |
| **Dz.U. 2025 poz. 1352** (MI 25.09.2025, PDF D20251352.pdf odczytany) | obowiązujący od 2025-10-22 (§ 1 pkt 3 od 2026-10-08) | zmienia PTB2022: m.in. § 17 ust. 5 (szerokość pasa na łuku — wymóg wynikowy, bez tabeli), § 13 ust. 1 pkt 3 (Vp klasy GP: 110 dwujezdniowa / 100 jednojezdniowa), § 20 ust. 2 (redakcyjne), § 23 ust. 10 pkt 5 (usunięcie klauzuli „jeżeli nie zaprojektowano części utwardzonej"), § 34 ust. 2/3 (przejścia dla pieszych a prędkość), § 58, § 78, § 80, § 81, § 83, § 88, § 89, zał. 1–3. **Żadna z wartości używanych w `standards.py` nie ulega zmianie.** |
| **Dz.U. 2019 poz. 2311** (t.j. rozp. MI 3.07.2003 o znakach/sygnałach/urządzeniach BRD) | obowiązujący (changeDate 2026-04-15); załączniki: `D20192311-c1.pdf` (zał. 1), `D20192311-c2.pdf` (zał. 2 = str. Dz.U. 526–906) | akt bazowy dla znaków; tekst jednolity NIE zawiera nowelizacji późniejszych (ELI: „Nowelizacje po tekście jednolitym”) |
| Dz.U. 2021 poz. 438 | obowiązujący | **tylko załącznik nr 1** (część 3 pkt 3.2.20 B-19; część 6 pkt 6.3.1.2/6.3.2.1/6.3.7.x; część 9 pkt 9.5) — zał. 2/3/4 nietknięte. Zamyka otwarty punkt z REVIEW r4. |
| Dz.U. 2021 poz. 2066 | obowiązujący | **tylko załącznik nr 1**, m.in. pkt 1.5.3 **Tabela 1.11** (wysokości znaków: w zabudowanym min 2,00 m, 2,20 m na chodniku; nad jezdnią min 5,00 m; na urządzeniach BRD 0,90–1,20 m) — odczytane własnym przebiegiem. |
| Dz.U. 2022 poz. 2377 | obowiązujący | § 1 „patrz oryginał”; § 2 wskazuje **załącznik nr 1** pkt 5.2.19, 5.2.20, 5.2.48.1, 5.2.49 — zał. 2/3/4 nietknięte. |
| Dz.U. 2026 poz. 132 (PDF D20260132.pdf odczytany) | obowiązujący od 2026-02-19 | zmienia rozp. 2003/2181 w **zał. 1** (E-20a, F-23/F-24, W-7, pkt 6.4.2.1/6.4.2.2 oznakowanie węzłów), **zał. 2** (P-1c, P-1e, P-3a, warunki P-7a/P-7b 0,24 m, rys. 4.2.2.3 P-10+P-11, P-18, P-23/P-26 na drogach dla rowerów) i **zał. 4** (BRD — zasady ogólne). Nie zmienia wymiarów P-1/P-2/P-8/P-10/P-11/P-12/P-13/P-14 używanych w generatorze. |

Wniosek z § 0: używane w kodzie wartości z zał. 2 (P-1a 4/8, P-1b 2/4, P-7a 1/1 szer. 0,24, P-10 4,0 m i pasy 0,5/0,5, P-11 0,5/0,5, P-12 0,5, P-13 0,50/0,25/0,70, P-14 0,75/0,25/0,50, P-2a ≥ 20 m, P-8 5,00/7,50 m i odstępy 15/30 m, pkt 2.2.1 próg 5,80 m) oraz Tabela 1.11 pozostają aktualne po wszystkich czterech nowelizacjach.

## 1. Inwentarz (wybór: stałe opisujące rzeczywiste obiekty drogowe; pełna tabela w duchu AUDIT-MARKINGS-PL)

Statusy: **SOURCED** = cytat z aktu pierwotnego (paragraf/strona), **DERIVED** = wywiedziona jednoznacznie z przepisu, **WORKING_VALUE** = nasz wybór.

| Plik:linia | Nazwa | Wartość | Jedn. | Status / źródło |
|---|---|---|---|---|
| roads/standards.py:38 | `LANE_WIDTH` | A 3,75/3,50; S 3,50/3,25; GP 3,50/3,25; G 3,50/3,00; Z 3,00/2,75; L 2,75/2,50; D 2,50/2,25 | m | SOURCED — PTB2022 § 17 ust. 1 pkt 1–7 (zweryfikowane własnym odczytem 2026-11-13) |
| standards.py:43 | `SINGLE_LANE_MIN` | 3,50 | m | SOURCED — § 17 ust. 3 |
| standards.py:44 | `SINGLE_LANE_DEFAULT` | 4,00 | m | WORKING_VALUE (w przedziale § 17 ust. 3: ≥ 3,50 i < 2 pasy) |
| standards.py:51 | `EDGE_STRIP` | A/S 0,75; GP 0,50; G 0,25; Z/L/D 0 | m | SOURCED dla A/S/GP — § 23 ust. 7 pkt 1 (0,75, min 0,50 trudne) i ust. 8; G 0,25 i 0 na krawężnikowej = dopuszczone § 23 ust. 4 (wer. po Dz.U. 2025/1352) |
| standards.py:54–59 | `MAX_GRADE_BY_VP`, `MAX_GRADE_RAMP`, `MAX_GRADE_SERVICE` | 4/5%…10/12% wg Vp; łącznice 7%; serwisowe 12% | — | SOURCED — § 20 ust. 2 pkt 1–7 (zweryfikowane); § 62 ust. 2 (WA ≤ 6%, WB/WC ≤ 7% — kod bierze 7% dla wszystkich, patrz pkt 4); serwisowe WORKING_VALUE |
| standards.py:65 | `VCURVE_MIN_R` | 150–2000 wg klasy | m | WORKING_VALUE — § 20 ust. 1 wynikowy (bez tabeli) |
| standards.py:69–73 | `CROSSFALL`, `CROSSFALL_CURVE`, `CURVE_R` | 0,02 / 0,025 / 400 | —, m | WORKING_VALUE — § 18 wynikowy; § 20 ust. 3: pochylenie ukośne 0,7–12% (2% i 2,5% w zakresie) |
| standards.py:77–78 | `KERB_HEIGHT`, `KERB_TOP_W` | 0,13 / 0,15 | m | DERIVED/WORKING_VALUE — § 89 ust. 2 pkt 1: krawężnik ≥ 0,12 m (próg bariery); wysokość sama nieuregulowana |
| standards.py:89–90 | `SIDEWALK_W`, `SIDEWALK_CROSSFALL` | 2,00 / 0,02 | m / — | SOURCED — § 29 ust. 1 ≥ 1,80 m; § 33 ≤ 2% (zweryfikowane własnym odczytem) |
| standards.py:101 | `SHOULDER_W` | A/S 1,25; **GP 0,75**; G 1,25; Z 1,00; L/D 0,75 | m | SOURCED — § 23 ust. 10 pkt 1–5 (zweryfikowane); **GP poprawione w M36 z 1,25 → 0,75 (pkt 2: część przyległa do opaski zewnętrznej)** |
| standards.py:102–103 | `PAVED_SHOULDER`, `PAVED_SHOULDER_MEDIAN` | 1,00 / 0,50 | m | WORKING_VALUE w dozwolonym przedziale § 23 ust. 7 pkt 1 (0,75 std, do 1,50 § 23 ust. 9) — patrz pkt 4 |
| standards.py:106–113 | `SHOULDER_CROSSFALL`, rowy, skarpy, `BERM_W` | 6% / 0,60 m / 1:1,5 / 1,0 m | — | WORKING_VALUE — § 24 ust. 3 i § 25 wynikowe |
| standards.py:117–128 | `CURB_RADIUS`, `TAPER_*` i in. węzłowe | 8–20 m; skos 1:10 | m | WORKING_VALUE — § 58 ust. 3/5: tylko przejazd pojazdu miarodajnego |
| standards.py:146–148 | `CLEARANCE_BY_CLASS`, `BRIDGE_CLEARANCE` | A/S 5,00; pozostałe 4,50 | m | SOURCED — § 80 ust. 1 pkt 1–2 |
| standards.py:167–195 | linie P-1/P-2/P-7, P-2a, P-10, P-11, P-12, P-13, P-14, P-8 | 0,12/0,24 m; 4/8, 2/4, 1/1; ≥ 20 m; 4,0 m; 0,5/0,5; 0,5; 0,50/0,25/0,70; 0,75/0,25/0,50; 5,00/7,50 m; 15/30 m; 5,80 m | m | SOURCED — zał. 2 (Dz.U. 2019 poz. 2311) pkt 2.2.1/2.2.2, 3.2.1 + rys. 3.2.1.2, 4.2.1–4.2.5 + rys. (zweryfikowane w M18/M25; niezmienione przez nowelizacje 2021–2026) |
| standards.py:218–220 | `SIGN_H_MIN`, `SIGN_H_SIDEWALK`, `SIGN_H_OVERHEAD` | 2,00 / 2,20 / 5,00 | m | SOURCED — zał. 1 Tabela 1.11 pkt 1.5.3 (brzmienie po Dz.U. 2021 poz. 2066, odczytane 2026-11-13) |
| standards.py:232–235 | `SIGN_SIZE`, `SIGN_LATERAL`, `SIGN_POST_D` | 0,90/0,80/0,60/0,80·sec(π/8)/0,60·√2; 0,75; Ø 60,3 mm | m | SOURCED rozmiary (zał. 1 Tabela 1.1/3.1/5.1, pkt 3.1.1 — romb = przekątna, ośmiokąt = koło wpisane 800 mm); odsunięcie 0,75 m mieści się w 0,50–2,00 m (pkt 1.5.3); słupek WORKING_VALUE katalogowy |
| standards.py:241–246 | `LAMP`, `LAMP_OFFSET` | h 8–12 m, rozstaw 30–36 m | m | WORKING_VALUE (PN-EN 13201-2 nie narzuca geometrii) |
| standards.py:249–253 | `SIGNAL_POLE_H`, `SIGNAL_MAST_H`, `SIGNAL_CANTILEVER_LANES`, `SIGNAL_MAST_BEND_R` | 4,0 / 6,8 / 2 / 1,5 | m | WORKING_VALUE — zał. 3 nieodczytany w całości (patrz rozsz. a) |
| standards.py:256–263, 268–272 | `GUARDRAIL_*`, `BRIDGE_BARRIER_*`, `RAILING_H` | 0,75 m; rozstaw 2,0/4,0 m; odsunięcie 0,60 m; 1,10 m | m | WORKING_VALUE; zgodne z § 89 ust. 2 pkt 1 (bariera ≥ 0,50 m od krawędzi pasa przy krawężniku ≥ 0,12 m) |
| roads/decals.py:85–86 | `GULLY_SPACING_M`, `GULLY_SIZE` | 35 m; 0,50×0,60 m | m | WORKING_VALUE |
| roads/gores.py:39–58 | `GORE_*`, `P21_STRIPE_W_M/GAP_M` | 2,0/4,0 m; 0,5/1,0 m | m | WORKING_VALUE; P-21 kreska/przerwa NIEZGODNE z pkt 5.2.7.1 (0,24/0,39 ≤ 70 km/h; 0,60/0,98 pozostałe) — xfail, patrz pkt 4 |
| roads/markings.py:221–223, 570–572 | `FRAGMENT_MIN_M`, `OVERLAP_*`, `P10_*` | 2,0/0,25/1,0/3,0/0,5/0,06 m | m | WORKING_VALUE (reguły wewnętrzne generatora) |
| roads/network.py:505–509, 625–632, 756–757 | `FORK_*`, `ABREAST_*`, `ALONGSIDE_*` | 40–60 m, 20:1, 0,3–30 m | m | WORKING_VALUE |
| roads/junctions.py:24–25 | `LOOK`, `STEP` | 70 m / 0,5 m | m | WORKING_VALUE |
| roads/profile.py:349–351 | `ABREAST_TIE_DOT`, `SHIFTED_*` | 0,7 / 0,3 / 2,0 | —/m | WORKING_VALUE |
| roads/route.py:31–49 | `LANE_CHANGE_*`, `JOINT_*`, `RING_*` | 12:1, 20–30 m, 8 m, 4–12 m | m | WORKING_VALUE (trasa pojazdu, nie obiekt drogowy) |
| streetscape/signs.py:25–32 | kolory lic znaków | RGB | — | SOURCED Tabela 1.3 (pola CIE 1931) oprócz GREEN — odchylenie udokumentowane w AUDIT-SIGNS-PL |
| streetscape/signs_route.py:38–41 | `DIAGRAM_BEFORE_M`, `EXIT_BOARD_AFTER_M`, `MIN_RING_R_DIAGRAM`, `DIAGRAM_MIN_M` | 80 / 7 / 18 / 40 | m | WORKING_VALUE (zał. 1 pkt 6.3.1/6.4.2 podaje odległości tablic na węzłach A/S: 3000/1500/500/300/200/100 m — region nie ma A/S) |
| streetscape/furniture.py:48–49, 123, 347–348, 432, 1318–1328, 1526–1534, 1564–1565, 1689–1690, 1731, 1775–1776, 2002–2004, 2110–2116, 2229, 2269–2278, 2320–2321 | stałe wyposażenia (siedzenia słupów, W-profile bariery, słupki, ekrany, przewody) | różne | m | WORKING_VALUE (ADR-y/Mapillary jako źródło wizualne, nie przepis) |
| streetscape/props.py:83, 213–214, 226–229, 351, 391, 427–432 | `LAMP_OLD`, słupki znaków, shelter 4,0×1,5×2,5, pylon | różne | m | WORKING_VALUE |

## 2. Niezgodności — co zmieniono, co opisano

**Zmieniono (przepis jednoznaczny):**
1. `standards.py:101` `SHOULDER_W["GP"]` 1,25 → **0,75 m** — PTB2022 § 23 ust. 10 pkt 2: część pobocza gruntowego przyległa do opaski zewnętrznej: standardowo 0,75 m (w trudnych ≥ 0,50 m). 1,25 m to wartość pkt 1, tylko przy pasie awaryjnym (A/S). Zmiana bezpieczna: profil RURAL w `network.py` używa już na stałe `sw = 0.75`; stała była nieużywana w geometrii. Test: `tests/gis/test_road_standards_audit_2026_11_13.py::test_shoulder_w_gp_next_to_opaska` (cytat w docstringu).

**Opisano, nie zmieniono (przepis daje przedział / dwie wartości / brak regulacji):**
- P-21 kreska/przerwa (`gores.py:48-49`, `through_lines.py:39-40`, `p21_hatch.py:28-29` = 0,5/1,0 m) vs pkt 5.2.7.1 zał. 2: 0,24/0,39 (≤ 70 km/h) lub 0,60/0,98 (pozostałe). Xfail strict w `test_markings_pl_verify.py` — decyzja właściciela z r3/r4.
- `MAX_GRADE_RAMP` 7% dla wszystkich `*_link` vs § 62 ust. 2: WA ≤ 6%, WB/WC ≤ 7%.
- `EDGE_STRIP["G"]` 0,25 m vs § 23 ust. 7 pkt 3 (0,50 m) — dopuszczone przez § 23 ust. 4 (ulica z wyniesionym krawężnikiem); miasto = ulice krawężnikowe.
- `PAVED_SHOULDER` 1,00 m vs § 23 ust. 7 pkt 1 (0,75 m standard) — dozwolone § 23 ust. 9 (do 1,50 m).

## 3. Przypadki przedziałów przepisowych — propozycje reguł wyboru (bez wdrażania)

1. **Szerokość pasa (§ 17 ust. 1: standard vs trudne warunki)** — kod bierze standard; BDOT `width` nadpisuje w dozwolonym zakresie (`network.py:100-116`, clamp do [diff, std+0,25]). Propozycja: trudne warunki tylko gdy OSM/BDOT wskazują zwężenie (obecna reguła już to robi przez `width`).
2. **P-21 (pkt 5.2.7.1): dwie wartości wg prędkości** — propozycja: `maxspeed` z OSM ≤ 70 km/h → P-21a 0,24/0,39 m, inaczej P-21b 0,60/0,98 m (region: maxspeed 90 tylko na 3 krawędziach DK8, reszta ≤ 70 → głównie P-21a).
3. **Łącznice (§ 62 ust. 2): WA 6% vs WB/WC 7%** — propozycja: rozróżnić typ łącznicy z geometrii węzła (zjazd z A/S = WA) i stosować 6%; obecnie dane regionu mają max 5,13%, więc bezpieczne.
4. **Opaska zewnętrzna GP (§ 23 ust. 7 pkt 1–2 + ust. 9: 0,75 / 0,50–1,50)** — propozycja: 0,75 m standardowo, 1,50 m tylko przy pasie awaryjnym/węźle; obecnie `PAVED_SHOULDER` 1,00 m.
5. **Przejście dla pieszych P-10 (§ 34 PTB2022: 4,00–16,00 m; na ulicy do 2,50 m; zał. 2 pkt 4.2.1: s = 4,0 m, w zabudowanym ≥ 2,5 m)** — kod bierze 4,0 m; propozycja: 2,5 m na ulicach klasy L/D z ruchem uspokojonym.

## 4. Rozszerzenia

**(a) Sygnalizacja świetlna (zał. 3 do Dz.U. 2019 poz. 2311).** W kodzie tylko WORKING_VALUE (`SIGNAL_POLE_H` 4,0 m, `SIGNAL_MAST_H` 6,8 m, `SIGNAL_CANTILEVER_LANES` 2, `SIGNAL_MAST_BEND_R` 1,5 m; głowica S-1 Ø300 mm w komentarzu). Zał. 3 (tekst jednolity + zmiany 2026/132) definiuje m.in. rozmieszczenie sygnalizatorów na węźle (odległości F-14 300/200/100 m, E-1a 1500/500 m — potwierdzone w Dz.U. 2021/2066 pkt 6.4.2.1/6.4.2.2 i 2026/132). Pełny odczyt zał. 3 (wysokość dolnej krawędzi nad jezdnią, Ø soczewek, odległość od krawędzi) — **otwarte**, oznaczone WORKING_VALUE.
**(b) Urządzenia BRD (zał. 4).** Bariery: § 89 PTB2022 (odległość najbardziej wystającej części bariery od krawędzi pasa ≥ 0,50 m przy krawężniku ≥ 0,12 m) — `GUARDRAIL_OFFSET` 0,60 m zgodne; wysokość W-beam 0,75 m, rozstaw słupków 2,0/4,0 m, ekrany 4,0 m, słupki U-1a/U-1b i pachołki U-14 — WORKING_VALUE (zał. 4 pkt 7.x, nieodczytane w całości; PN-EN 1317 tylko publiczne fragmenty).
**(c) Przejścia dla pieszych / przejazdy rowerowe.** P-10: s = 4,0 m (zał. 2 pkt 4.2.1; PTB2022 § 34: 4,00–16,00 m, na ulicy do 2,50 m) — SOURCED. P-11: kwadraty 0,5/0,5 m, szerokość ≥ 1,8 m (jednokierunkowy) / 3,0 m (dwukierunkowy) — SOURCED (rys. 4.2.2.1, pkt 4.2.2; PTB2022 § 34 ust. 6: 1,80/3,00 m). P-14: ≥ 2,0 m przed sygnalizatorem obok jezdni i przed przejściem, 8,0 m przed sygnalizatorem nad jezdnią (pkt 4.2.5). Uwaga po Dz.U. 2025/1352 § 34 ust. 2/3: przejście bez sygnalizacji tylko przy V ≤ 50 km/h i max jeden pas na kierunek — reguła projektowa, nie modelowana.
**(d) S8/DK8 w regionie.** Dane regionu (`roads.graph.json`): brak `motorway` (S8 poza wycinkiem), DK8/DK19/DK65 = `trunk` → klasa GP, `trunk_link` 31 krawędzi; maxspeed 90 na 3 krawędziach, 70 na 63, 50 na 454. Parametry węzłów: § 13 ust. 1 pkt 3 (po 2025/1352): GP jednojezdniowa Vp 100 (90/80), dwujezdniowa 110; § 62 ust. 2: łącznice WA ≤ 6%, WB/WC ≤ 7%; pasy wyłączania/włączania — § 62 podaje kryterium wynikowe (opóźnienie ≤ 1,5 m/s² na A/S), **bez tabeli długości** → długości w generatorze (TAPER_RATIO 10:1) to WORKING_VALUE; propozycja: liczyć z różnicy prędkości przy a = 1,0–1,5 m/s².

## 5. Weryfikacja A–E (dowody w opisie PR)

- **A. Niezależny przegląd:** bez subagentów — 3 przebiegi od zera: (1) własny odczyt ELI/ISAP 2026-11-13 (PTB2022 § 1–33 z PDF, nowelizacje 2021/438, 2021/2066, 2022/2377, 2026/132, 2025/1352 w całości), (2) krzyżowe porównanie z AUDIT-MARKINGS-PL-2026-11-12 i AUDIT-SIGNS-PL-2026-11-12 (wartości ZGODNE), (3) kontrola pułapek interpretacji: romb = przekątna (0,60·√2, poprawione w r4), ośmiokąt B-20 = koło wpisane 800 mm (płyta 0,80/cos(π/8)), grupa wielkości „średnie”, klasa drogi GP dla trunk. Lista losowa ≥ 30% cytatów: § 17 ust. 1, § 17 ust. 3, § 20 ust. 2, § 23 ust. 7/8/10, § 29 ust. 1, § 33, § 62 ust. 2, § 80 ust. 1, § 89 ust. 2 pkt 1, Tabela 1.11, pkt 2.2.1/2.2.2/3.2.1/4.2.1/4.2.2/4.2.5/5.2.7.1.
- **B. Test mutacyjny:** każdy nowy test w `test_road_standards_audit_2026_11_13.py` zmutowany ręcznie → FAIL (tabela 9/9 FAIL w opisie PR).
- **C. Testy:** przed: `pytest tests/gis -q -m unit` = 76 passed, 1 xfailed; pełne = 2 failed (znane), 876 passed, 45 skipped, 2 xfailed. Po: patrz opis PR.
- **D. Rebase na origin/main przed PR; diff tylko dozwolone ścieżki** (`tools/worldgen/roads/standards.py`, `tests/gis/test_road_standards_audit_2026_11_13.py`, ten raport).
- **E.** Lista A–D w opisie PR.
