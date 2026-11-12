# AUDIT-MARKINGS-PL-2026-11-12-mistral — audyt oznakowania poziomego i geometrii dróg (zadanie M10), rewizja zweryfikowana ze źródeł pierwotnych (zadanie 18)

- Gałąź: `mistral/18-markings-verify` (od `main`). Ta rewizja zastępuje pierwotną wersję raportu z PR #13:
  każdy status „ZGODNE” został ponownie sprawdzony **wyłącznie w źródle pierwotnym** (ISAP/ELI), bez serwisów wtórnych.
- Zakres: stałe i reguły w `tools/worldgen/roads` (głównie `standards.py`, użycie w `markings.py`,
  `through_lines.py`, `junctions.py`, `network.py`, `profile.py`, `gores.py`, `p21_hatch.py`, `authored_paint.py`).
- Źródła pierwotne odczytane 2026-11-12 przez API Sejmu (`api.sejm.gov.pl/eli/...`, ten sam backend co isap.sejm.gov.pl):
  - **[ZNAKI-Z2]** załącznik nr 2 do rozporządzenia MI z 3.07.2003 r. — tekst jednolity **Dz.U. 2019 poz. 2311**
    (WDU20190002311, status **„obowiązujący”**, ostatnia zmiana 2026-04-15; nowelizacje m.in. Dz.U. 2021 poz. 438,
    Dz.U. 2021 poz. 2066, Dz.U. 2022 poz. 2377, Dz.U. 2026 poz. 132). Załącznik nr 2 = strony Dz.U. **526–906**
    (PDF `D2019000231102.pdf`); numery stron w tabelach to strony Dziennika Ustaw poz. 2311. Tekst załącznika nr 2
    w części 5 był zmieniony przez Dz.U. 2021 poz. 2066 — czytany tekst jednolity zawiera już te zmiany.
    **[Poprawka lidera s15]** To zdanie jest błędne: tekst jednolity Dz.U. 2019 poz. 2311 (obwieszczenie z 9.09.2019)
    NIE zawiera nowelizacji późniejszych (ELI: „Nowelizacje po tekście jednolitym”: Dz.U. 2021 poz. 438, 2021 poz. 2066,
    2022 poz. 2377, 2026 poz. 132). Statusy poniżej opierają się na tekście z 2019 r.; zmiany z lat 2021–2026 w zał. nr 2
    są niesprawdzone (UNVERIFIED). Lider sprawdził wyrywkowo w PDF `dziennikustaw.gov.pl/D2019000231102.pdf`:
    pkt 5.2.7.1 / Tabela 5.3 (P-21a 0,24/0,39 m, P-21b 0,60/0,98 m) na str. Dz.U. 587 i 589 oraz „nie może być większa
    niż 16,0 m” (P-10) na str. 567 — zgodne z cytatami raportu.
  - **[PTB2022]** rozporządzenie MI z 24.06.2022 r. w sprawie przepisów techniczno-budowlanych dotyczących dróg
    publicznych — **Dz.U. 2022 poz. 1518** (status „obowiązujący”, zmienione m.in. Dz.U. 2025 poz. 1352), tekst HTML z ELI.
- Statusy: **ZGODNE** (zweryfikowane z treścią przepisu w źródle pierwotnym), **NIEZGODNE** (kod różni się od przepisu),
  **BRAK W PRZEPISACH** (przepis nie reguluje wartości — wybór projektowy/WORKING_VALUE).

## 0. Sprostowanie zdania o „uchyleniu w 2022 r.” (wątpliwość recenzji)

Pierwotny raport pisał, że rozporządzenie z 2003 r. zostało „uchylone dopiero 2022 r.”. **To nieprawda.**
Sprawdzone w ELI/ISAP 2026-11-12:

- rozporządzenie MI z 3.07.2003 r. (tekst jednolity **Dz.U. 2019 poz. 2311**) ma status **„obowiązujący”** —
  nie zostało uchylone; nadal obowiązuje z późn. zm. (ostatnia: Dz.U. 2026 poz. 132, zmiana 2026-04-15);
- aktem uchylonym z dniem **2022-09-21** przez PTB2022 (Dz.U. 2022 poz. 1518) było rozporządzenie z 1999 r.
  o warunkach technicznych dla dróg (tekst jednolity **Dz.U. 2016 poz. 124**, status w ELI: „uznany za uchylony”).

## 1. Oznakowanie poziome — [ZNAKI-Z2] (Dz.U. 2019 poz. 2311, załącznik nr 2, str. Dz.U. 526–906)

| Stała (plik:linia) | Wartość w kodzie | Źródło pierwotne (str. Dz.U. = pkt/rys.) | Wartość z rozporządzenia | Status |
|---|---|---|---|---|
| `standards.py:162` `LINE_W_NARROW` | 0,12 m | rys. 2.2.1.1 (str. 532), 2.2.1.2 (str. 533): szerokość linii 0,12 m; pkt 2.2.2 (str. 545): P-7c/P-7d 0,12 m | 0,12 m | ZGODNE |
| `standards.py:163` `LINE_W_WIDE` | 0,24 m | pkt 2.2.2 (str. 545): „Linie P-7a i P-7b o szerokości 0,24 m”; rys. 2.2.2.2 (str. 546): 0,24 m | 0,24 m | ZGODNE |
| `standards.py:166` `DASH["P-1a"]` | (4,0 m, 8,0 m) | pkt 2.2.1.1 (str. 533): P-1a „na drogach o dopuszczalnej prędkości **powyżej 70 km/h**”, min długość 120 m; rys. 2.2.1.1 (str. 532): kreska 4,00 m, przerwa 8,00 m (0,04 m²/mb = 0,12×4/12) | kreska 4 m / przerwa 8 m; próg > 70 km/h | ZGODNE |
| `standards.py:167` `DASH["P-1b"]` | (2,0 m, 4,0 m) | pkt 2.2.1.2 (str. 533): P-1b „na drogach o dopuszczalnej prędkości **do 70 km/h**”, min długość 50 m; rys. 2.2.1.2 (str. 533): kreska 2,00 m, przerwa 4,00 m | kreska 2 m / przerwa 4 m; próg ≤ 70 km/h | ZGODNE |
| `standards.py:168` `DASH["P-1d"]` | (1,0 m, 1,0 m) | pkt 2.2.1.4 (str. 535); rys. 2.2.1.4 (str. 535): 0,06 m²/mb = 0,12×1/2 → kreska 1 m / przerwa 1 m | kreska 1 m / przerwa 1 m | ZGODNE |
| `standards.py:169` `DASH["P-7a"]` | (1,0 m, 1,0 m) | rys. 2.2.2.2 (str. 546): szerokość 0,24 m, kreska 1,00 m, przerwa 1,00 m | kreska 1 m / przerwa 1 m | ZGODNE (było UNVERIFIED — teraz zweryfikowane) |
| `standards.py:171` `P2A_MIN_LEN` | 20,0 m | pkt 2.2.1.6 (str. 536): „Długość linii pojedynczej ciągłej – wąskiej powinna wynosić co najmniej 20 m.” | ≥ 20 m | ZGODNE |
| `standards.py:189` `SEGREGATION_MIN_CARRIAGEWAY` | 5,80 m | pkt 2.2.1 (str. 531): „Na jezdniach dwukierunkowych o szerokości jezdni mniejszej niż 5,80 m linii segregacyjnych nie stosuje się.” | < 5,80 m → zakaz linii segregacyjnych | ZGODNE |
| `standards.py:185-186` `ARROW_SHORT`/`ARROW_LONG` | dł. 5,00 / 7,50 m, główka 2,05 m, szer. główki 0,75 m, trzonek 0,15 m | rys. 3.2.1.2 a)/b) (str. 553): a) 500 cm, b) 750 cm; główka 205 cm, szer. 75 cm, trzonek 15 cm; pkt 3.2.1 (str. 550): „długie – na drogach o dopuszczalnej prędkości **powyżej 70 km/h**, krótkie – do 70 km/h” | krótka 5,0 m / długa 7,5 m; główka 2,05 m, 0,75 m; trzonek 0,15 m; progi 70 km/h | ZGODNE |
| `standards.py:187` `ARROW_SPACING` | 15 m (≤70 km/h) / 30 m (>70 km/h) | pkt 3.2.1 (str. 550): „15 m (wyjątkowo 20 m) na drogach o dopuszczalnej prędkości do 70 km/h, 30 m (wyjątkowo 40 m) na pozostałych drogach” | 15 m / 30 m | ZGODNE |
| `standards.py:172-175` `P10_STRIPE`/`P10_GAP`/`P10_EDGE_MAX`/`P10_WIDTH` | pasy 0,50 m, przerwy 0,50 m, ≤0,50 m od krawędzi, s = 4,0 m | rys. 4.2.1.1 (str. 567): paski 0,5 m, przerwy 0,5 m, „max. 0,5 m” od krawędzi; pkt 4.2.1 (str. 567): „Szerokość przejścia dla pieszych s wynosi 4,0 m… w obszarze zabudowanym… nie mniejsza niż 2,5 m… **Szerokość przejścia nie może być większa niż 16,0 m**” | s = 4,0 m (min 2,5 m w zabudowie, **max 16,0 m**), pasy/przerwy 0,5 m, ≤0,5 m od krawędzi | ZGODNE (wątpliwość recenzji „max 16 m” — **potwierdzona**) |
| `standards.py:176` `P12_W` | 0,50 m | rys. 4.2.3.1 (str. 571): szerokość linii 0,5 m (0,5 m²/mb) | 0,5 m | ZGODNE |
| `standards.py:179` `P11_SQUARE`/`P11_GAP`/`P11_CLEAR` | 0,40 / 0,40 / 2,0 m | rys. 4.2.2.1 (str. 569): **kwadrat 0,5 m, odstęp 0,5 m**; pkt 4.2.2 (str. 569): „dwie linie przerywane… szerokość przejazdu nie mniejsza niż 1,8 m (jednokierunkowy) / 3,0 m (dwukierunkowy)” | kwadrat 0,5 m / odstęp 0,5 m; szer. min 1,8/3,0 m | **NIEZGODNE** (kod 0,40/0,40; xfail w `tests/gis/test_markings_pl_verify.py`) |
| `standards.py:181` `P13_BASE`/`P13_GAP`/`P13_H` | 0,50 / 0,25 / 0,70 m | rys. 4.2.4.1 (str. 572): podstawa 0,50 m, **wysokość 0,70 m**, odstęp 0,25 m | 0,50 / 0,25 / 0,70 m | ZGODNE (wątpliwość recenzji „0,70 m” — **potwierdzona**) |
| `standards.py:182` `P14_LEN`/`P14_GAP`/`P14_DEPTH` | 0,75 / 0,25 / 0,50 m | rys. 4.2.5.1 (str. 573): prostokąty 0,75 m, odstęp 0,25 m, głębokość 0,5 m | 0,75 / 0,25 / 0,50 m | ZGODNE |
| `standards.py:183-184` `P14_BEFORE_SIGNAL`/`P14_BEFORE_CROSSING` | 2,0 m / 2,0 m | pkt 4.2.5 (str. 573): „co najmniej 2,0 m przed sygnalizatorami znajdującymi się obok jezdni… 8,0 m przed sygnalizatorami znajdującymi się nad jezdnią… 2,0 m przed przejściami dla pieszych” | ≥ 2,0 m (obok jezdni i przed przejściem); 8,0 m nad jezdnią | ZGODNE |
| `standards.py:188` `MARKING_LIFT` | 0,006 m | — | wyniesienie farby nie jest regulowane | BRAK W PRZEPISACH (WORKING_VALUE) |
| `p21_hatch.py:28-30` `STRIPE_W_M`/`STRIPE_GAP_M`/`BORDER_W_M` | 0,5 / 1,0 / 0,24 m | pkt **5.2.7.1** (str. 587; pierwotny raport błędnie cytował „pkt 5.2.1”): „Szerokość linii wewnętrznych oraz odstęp między nimi… wynoszą odpowiednio: **0,24 m z odstępem 0,39 m** – do 70 km/h (P-21a), **0,60 m z odstępem 0,98 m** – pozostałe drogi (P-21b)”; obwiednia = linia P-7b 0,24 m | liniowanie 0,24/0,39 (P-21a) lub 0,60/0,98 (P-21b); obramowanie 0,24 m | **NIEZGODNE** dla kreski/przerwy (kod 0,5/1,0; xfail w `tests/gis/test_markings_pl_verify.py`); obramowanie 0,24 m ZGODNE |
| `markings.py:221-223,570` `FRAGMENT_MIN_M`/`OVERLAP_INSET_M`/`OVERLAP_DZ_M`/`P10_NODE_CLEAR_M` | 2,0 / 0,25 / 1,0 / 3,0 m | — | reguły wewnętrzne generatora | BRAK W PRZEPISACH (WORKING_VALUE) |
| `standards.py:180` `P8_MIN_LANE_W` | 2,5 m | — (ADR 0093; przepis nie zabrania strzałki w wąskim pasie) | brak wymogu | BRAK W PRZEPISACH (WORKING_VALUE) |

## 2. Geometria drogi — [PTB2022] Dz.U. 2022 poz. 1518 (numery paragrafów zweryfikowane w tekście ELI)

| Stała (plik:linia) | Wartość w kodzie | Przepis (zweryfikowany) | Status |
|---|---|---|---|
| `standards.py:36-39` `LANE_WIDTH` | A (3,75/3,50), S (3,50/3,25), GP (3,50/3,25), G (3,50/3,00), Z (3,00/2,75), L (2,75/2,50), D (2,50/2,25) | § 17 ust. 1 pkt 1-7 (standardowo / w trudnych warunkach; G: „3,25 lub 3,00”) — wartości zgodne | ZGODNE |
| `standards.py:41` `SINGLE_LANE_MIN` | 3,50 m | § 17 ust. 3: „na jezdni z jednym pasem ruchu… nie mniejsza niż 3,50 m” | ZGODNE |
| `standards.py:49` `EDGE_STRIP` | A/S 0,75, GP 0,50, G 0,25, Z/L/D 0 | § 23 ust. 7: opaska zewnętrzna 0,75 m (min 0,50 w trudnych) GP, 0,50 G/Z; § 23 ust. 4: na ulicy z wyniesionym krawężnikiem „dopuszcza się inne rozwiązania” opasek | ZGODNE (GP 0,50 = wariant trudnych warunków; G 0,25 i 0 na krawężnikowej = dopuszczone ust. 4) |
| `standards.py:96` `SHOULDER_W` | A/S/GP/G 1,25, Z 1,00, L/D 0,75 m | § 23 ust. 10 pkt 1-5: pobocze gruntowe 1,25 (przy pasie awaryjnym / klasa G), 1,00 (Z), 0,75 (L/D) | ZGODNE |
| `standards.py:97` `PAVED_SHOULDER` | 1,00 m | § 23 ust. 6 dotyczy pasa awaryjnego (A/S); pobocze utwardzone nie ma sztywnego minimum | BRAK W PRZEPISACH (WORKING_VALUE) |
| `standards.py:67` `CROSSFALL` | 0,02 | § 18: wymóg wynikowy („skuteczne odwodnienie”); § 20 ust. 3: pochylenie ukośne 0,7–12% | BRAK W PRZEPISACH (2% = praktyka; WORKING_VALUE) |
| `standards.py:68-71` `CROSSFALL_CURVE`/`CURVE_R` | 0,025 / R<400 m | przechyłka wynikowa (§ 20) | BRAK W PRZEPISACH (WORKING_VALUE) |
| `standards.py:75-76` `KERB_HEIGHT`/`KERB_TOP_W` | 0,13 m / 0,15 m | § 89 ust. 2 pkt 1: krawężnik „o wysokości wynoszącej co najmniej 0,12 m” (próg bariery); wysokość krawężnika sama w sobie nie jest narzucona | ZGODNE (0,13 ≥ 0,12) |
| `standards.py:84` `KERB_HEIGHT_APRON` | 0,04 m | krawężnik najazdowy — brak wymogu wysokości | BRAK W PRZEPISACH (WORKING_VALUE) |
| `standards.py:87-88` `SIDEWALK_W`/`SIDEWALK_CROSSFALL` | 2,00 m / 0,02 | § 29 ust. 1: chodnik ≥ 1,80 m; § 33: pochylenie drogi dla pieszych ≤ 2% (chodnika ≤ 3% w trudnych) | ZGODNE |
| `standards.py:112` `CURB_RADIUS` | A/S 20, GP 15, G 12, Z 10, L/D 8 m | § 58: skrzyżowania projektuje się m.in. pod kątem przejazdu pojazdu miarodajnego — bez tabeli promieni | BRAK W PRZEPISACH (WORKING_VALUE) |
| `standards.py:126-127` `ROUNDABOUT_APRON_W`/`ROUNDABOUT_CROSSFALL` | 2,0 m / 0,02 | geometria ronda wynika z danych OSM; § 59-60 wynikowe | BRAK W PRZEPISACH (WORKING_VALUE) |
| `standards.py:141-142` `CLEARANCE_BY_CLASS`/`BRIDGE_CLEARANCE` | A/S 5,00 m, pozostałe 4,50 m | § 80 ust. 1 pkt 1-2: „Wysokość skrajni… 5,00 m – klasy A lub S; 4,50 m – klasy GP, G, Z, L lub D” | ZGODNE |
| `standards.py:52-57` `MAX_GRADE_BY_VP`/`MAX_GRADE_RAMP`/`MAX_GRADE_SERVICE` | wg Vp: 4/5%…10/12%; łącznice ≤ 7%; serwisowe 12% | § 20 ust. 2: tabela wg prędkości projektowej (130/140→4%, 110/120→5%, 90/100→6%, 70/80→7%, 60→8%, 50→9%, 30/40→10%; trudne +1-2%) — zgodne; § 62 ust. 2: łącznica WA ≤ 6%, WB/WC ≤ 7% (kod stosuje 7% dla wszystkich `_link` — dopuszczalne dla WB/WC; WA miałoby 6%) | ZGODNE (z uwagą o WA ≤ 6%) |
| `standards.py:63` `VCURVE_MIN_R` | 150–2000 m wg klasy | § 20 ust. 1: załamania niwelety wyokrągla się krzywymi — bez tabeli | BRAK W PRZEPISACH (WORKING_VALUE) |
| `standards.py:101-108` `SHOULDER_CROSSFALL`/rowy/nasypy | 6% / 0,60 m / 1:1,5 | § 24-25 wynikowe („skuteczne odwodnienie”) | BRAK W PRZEPISACH (WORKING_VALUE) |

## 3. Odpowiedzi na wątpliwości recenzji (wszystkie zweryfikowane w źródle pierwotnym)

1. **P-10 max 16 m** — ZGODNE: pkt 4.2.1, Dz.U. 2019 poz. 2311, str. 567: „Szerokość przejścia nie może być większa niż 16,0 m.”
2. **P-13 wysokość 0,70 m** — ZGODNE: rys. 4.2.4.1, str. 572: podstawa 0,50 m, wysokość 0,70 m, odstęp 0,25 m.
3. **Progi 70 km/h dla P-1a/P-1b/P-8** — ZGODNE: pkt 2.2.1.1 „powyżej 70 km/h” / pkt 2.2.1.2 „do 70 km/h” (str. 533); pkt 3.2.1: strzałki długie „powyżej 70 km/h”, krótkie „do 70 km/h” (str. 550).
4. **Numery paragrafów PTB2022** — ZGODNE: § 17, § 18, § 20, § 23, § 29, § 33, § 58, § 62, § 80, § 89 istnieją w Dz.U. 2022 poz. 1518 i mają cytowane treści (z uwagą: § 62 ust. 2 rozróżnia łącznice WA ≤ 6% i WB/WC ≤ 7%).
5. **„Uchylenie w 2022 r.”** — NIEPRAWDA dla rozporządzenia o znakach: Dz.U. 2019 poz. 2311 ma status „obowiązujący”; uchylone w 2022 r. (z dniem 2022-09-21) było rozporządzenie z 1999 r. o warunkach technicznych dla dróg (t.j. Dz.U. 2016 poz. 124, status „uznany za uchylony”), zastąpione przez PTB2022. Sekcja 0.

## 4. NIEZGODNE pozycje kodu (generator NIE zmieniony; testy xfail)

- `standards.py:179` `P11_SQUARE`/`P11_GAP` = 0,40/0,40 m vs rys. 4.2.2.1 (str. 569): kwadrat 0,5 m / odstęp 0,5 m →
  `tests/gis/test_markings_pl_verify.py::test_p11_square_and_gap_vs_rys_4_2_2_1` (xfail strict, marker `unit`).
- `p21_hatch.py:28-29` `STRIPE_W_M`/`STRIPE_GAP_M` = 0,5/1,0 m vs pkt 5.2.7.1 (str. 587): 0,24/0,39 m (P-21a) lub 0,60/0,98 m (P-21b) →
  `tests/gis/test_markings_pl_verify.py::test_p21_hatch_vs_pkt_5_2_7_1` (xfail strict, marker `unit`).

## 5. Weryfikacja

```
uv run --project tools/worldgen pytest tests/gis/test_markings_pl_verify.py -q
# 2 xfailed (strict) in ...
```

Źródła odczytane wyłącznie z ISAP/ELI (api.sejm.gov.pl, isap.sejm.gov.pl, dziennikustaw.gov.pl dla PDF załącznika nr 2);
żadne serwisy wtórne nie zostały użyte do statusów. Zakaz źródeł mapowych (Google Maps/Street View) zachowany.
