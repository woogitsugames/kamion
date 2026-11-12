# AUDIT-MARKINGS-PL-2026-11-12-mistral — audyt stałych oznakowania poziomego i geometrii dróg (zadanie M10)

- Gałąź: `mistral/10-markings-pl` (od `main`), raport: ten plik. Świat NIE był regenerowany (regeneruje lider).
- Zakres: stałe i reguły w `tools/worldgen/roads` (głównie `standards.py`, użycie w `markings.py`,
  `through_lines.py`, `junctions.py`, `network.py`, `profile.py`, `gores.py`, `p21_hatch.py`, `authored_paint.py`).
- Przepisy zestawione (stan prawny odczytany 2026-11-12 przez ISAP/ELI i teksty jednolite):
  - **[ZNAKI-Z2]** załącznik nr 2 „Szczegółowe warunki techniczne dla znaków drogowych poziomych i warunki ich
    umieszczania na drogach” do rozporządzenia MI z 3.07.2003 r. — tekst jednolity **Dz.U. 2019 poz. 2311**
    (z późn. zm.; rozporządzenie uchylone dopiero 2022 r., ale zał. nr 2 obowiązuje nadal z późn. zm.,
    m.in. Dz.U. 2026 poz. 132).
  - **[WT]** „warunki techniczne, jakim powinny odpowiadać drogi publiczne i ich usytuowanie” — rozp. MTiGM
    z 2.03.1999 r. (Dz.U. 1999 nr 43 poz. 430), tekst jednolity **Dz.U. 2016 poz. 124** (obwieszczenie MIiB
    z 23.12.2015 r.). **Uwaga:** rozporządzenie z 1999 r. zostało uchylone i zastąpione przez
    **[PTB2022]** rozporządzenie MI z 24.06.2022 r. w sprawie przepisów techniczno-budowlanych dotyczących
    dróg publicznych (**Dz.U. 2022 poz. 1518**, obowiązuje od 21.09.2022) — to aktualny „tekst w ISAP”;
    repo już go cytuje w `standards.py`, audyt poniżej podaje obie wersje tam, gdzie wartości się różnią.
- Statusy: **ZGODNE** (zweryfikowane z treścią przepisu), **ZGODNE-Z-CYTATEM** (repo cytuje pkt/rysunek,
  wartość zgodna), **WORKING_VALUE** (przepis daje swobodę/wymóg wynikowy — wybór projektowy, tak oznaczone
  w repo), **UNVERIFIED** (nie udało się jednoznacznie zweryfikować), **ROZBIEŻNOŚĆ**.

## 1. Oznakowanie poziome — [ZNAKI-Z2] (Dz.U. 2019 poz. 2311, zał. nr 2)

| Stała (plik:linia) | Wartość w repo | Przepis (pkt/rys.) | Status |
|---|---|---|---|
| `standards.py:162` `LINE_W_NARROW` | 0,12 m | pkt 2.2.1: linie podziału pasów wąskie 0,12 m (rys. 2.2.1.1/2.2.1.2/2.2.1.6) | ZGODNE-Z-CYTATEM |
| `standards.py:163` `LINE_W_WIDE` | 0,24 m | rys. 2.2.1.7 (P-2b); pkt 2.2.2 + rys. 2.2.2.2: P-7a/P-7b szerokie 0,24 m (A/S, twarde pobocze/opaska, szlaki międzynarodowe, dwujezdniowe); wąskie P-7c/P-7d 0,12 m | ZGODNE |
| `standards.py:165-170` `DASH["P-1a"]` | (4,0 m, 8,0 m) | rys. 2.2.1.1: P-1a (V > 70 km/h) kreska 4 m, przerwa 8 m | ZGODNE (potwierdzone wtórnie: info-car.pl podaje 4 m/8 m dla dróg poza zabudowanym) |
| `standards.py:166` `DASH["P-1b"]` | (2,0 m, 4,0 m) | rys. 2.2.1.2: P-1b (V ≤ 70 km/h) kreska 2 m, przerwa 4 m; min długość linii 50 m | ZGODNE |
| `standards.py:167` `DASH["P-1d"]` | (1,0 m, 1,0 m) | rys. 2.2.1.4: P-1d „prowadząca wąska” na skrzyżowaniach | ZGODNE-Z-CYTATEM |
| `standards.py:168` `DASH["P-7a"]` | (1,0 m, 1,0 m) | rys. 2.2.2.2: P-7a przerywana szeroka — wymiar kreski/przerwy z rysunku | UNVERIFIED (rysunek nieodczytany jednoznacznie; repo przyjmuje 1/1 m) |
| `standards.py:171` `P2A_MIN_LEN` | 20,0 m | pkt 2.2.1.6: linia pojedyncza ciągła wąska (P-2a) co najmniej 20 m | ZGODNE |
| `standards.py:189` `SEGREGATION_MIN_CARRIAGEWAY` | 5,80 m | pkt 2.2.1: na jezdniach dwukierunkowych węższych niż 5,80 m nie wyznacza się linii podziału | ZGODNE-Z-CYTATEM |
| `standards.py:185-186` `ARROW_SHORT`/`ARROW_LONG` | dł. 5,00 m / 7,50 m, główka 2,05 m, szer. główki 0,75 m, trzonek 0,15 m | rys. 3.2.1.2 a)/b): P-8 krótka 5 m, długa 7,5 m (długa przy V > 70 km/h) | ZGODNE (długości potwierdzone wtórnie: termoznak P-8a L=5000 mm; „długie strzałki powyżej 70 km/h”) |
| `standards.py:187` `ARROW_SPACING` | 15 m (≤70 km/h) / 30 m (>70 km/h) | pkt 3.2.1: odstępy między strzałkami | ZGODNE-Z-CYTATEM |
| `standards.py:172-175` `P10_STRIPE`/`P10_GAP`/`P10_EDGE_MAX`/`P10_WIDTH` | pasy 0,50 m, przerwy 0,50 m, ≤0,5 m od krawędzi, szerokość s = 4,0 m | pkt 4.2.1 + rys. 4.2.1.1: P-10 s = 4,0 m (w obszarze zabudowanym min 2,5 m, max 16,0 m), pasy 0,5 m / przerwy 0,5 m | ZGODNE |
| `standards.py:176` `P12_W` | 0,50 m | rys. 4.2.3.1: P-12 linia zatrzymania STOP szerokość 0,50 m | ZGODNE |
| `standards.py:179` `P11_SQUARE`/`P11_GAP`/`P11_CLEAR` | 0,40 / 0,40 / 2,0 m | pkt 4.2.2: P-11 dwa rzędy kwadratów; szerokość przejazdu min 1,8 m (jednokierunkowy) / 3,0 m (dwukierunkowy) | UNVERIFIED (tak oznaczone w repo: odczyt z ortofoto, nie z przepisu) |
| `standards.py:181` `P13_BASE`/`P13_GAP`/`P13_H` | 0,50 / 0,25 / 0,70 m | rys. 4.2.4.1: P-13 trójkąty podstawa 0,50 m, wysokość 0,70 m, odstęp 0,25 m | ZGODNE |
| `standards.py:182` `P14_LEN`/`P14_GAP`/`P14_DEPTH` | 0,75 / 0,25 / 0,50 m | rys. 4.2.5.1: P-14 prostokąty 0,75 × 0,50 m, odstęp 0,25 m | ZGODNE |
| `standards.py:183-184` `P14_BEFORE_SIGNAL`/`P14_BEFORE_CROSSING` | 2,0 m / 2,0 m | pkt 4.2.5: P-14 co najmniej 2,0 m przed sygnalizatorem obok jezdni (nad jezdnią 8,0 m) i przed P-10/P-11 | ZGODNE |
| `standards.py:188` `MARKING_LIFT` | 0,006 m | brak w przepisie (wyniesienie farby nad nawierzchnią) | WORKING_VALUE |
| `through_lines.py:39-41`, `gores.py:49-51`, `p21_hatch.py:28-32` `P21_STRIPE_W_M`/`P21_STRIPE_GAP_M`/`P21_BORDER_W_M` | 0,5 m / 1,0 m / 0,24 m | pkt 5.2.1 (P-21 powierzchnia wyłączona) — wymiar z rysunku; repo odczytało z ortofoto 0,08 m | WORKING_VALUE |
| `markings.py:220-222` `FRAGMENT_MIN_M`/`OVERLAP_INSET_M`/`OVERLAP_DZ_M`, `markings.py:573-575` `P10_NODE_CLEAR_M` itp. | 2,0 / 0,25 / 1,0 / 3,0 m … | brak w przepisie (reguły wewnętrzne generatora) | WORKING_VALUE |
| `standards.py:180` `P8_MIN_LANE_W` | 2,5 m | ADR 0093 (brak strzałki w pasie węższym niż 2,5 m) | WORKING_VALUE |

## 2. Geometria drogi — [WT] Dz.U. 2016 poz. 124 (1999) vs [PTB2022] Dz.U. 2022 poz. 1518 (aktualne)

| Stała (plik:linia) | Wartość w repo | Przepis | Status |
|---|---|---|---|
| `standards.py:36-39` `LANE_WIDTH` | A (3,75/3,50), S (3,50/3,25), GP (3,50/3,25), G (3,50/3,00), Z (3,00/2,75), L (2,75/2,50), D (2,50/2,25) | PTB2022 § 17 ust. 1 pkt 1-7 (standardowo / w trudnych warunkach; G dopuszcza 3,25 lub 3,00) — wartości zgodne; WT 1999 § 15 miało zbliżoną tabelę | ZGODNE |
| `standards.py:41` `SINGLE_LANE_MIN` | 3,50 m | PTB2022 § 17 ust. 3: jezdnia 1-pasowa < 2 pasy, ale ≥ 3,50 m | ZGODNE |
| `standards.py:49` `EDGE_STRIP` | A/S 0,75, GP 0,50, G 0,25, Z/L/D 0 | PTB2022 § 23 ust. 7: opaska zewnętrzna 0,75 m (A/S/GP), w trudnych warunkach ≥ 0,50 m; ust. 4 dopuszcza inne rozwiązania przy krawężnikach | ZGODNE (GP 0,50 = wariant „trudne warunki”; G 0,25 = WORKING_VALUE dopuszczony ust. 4) |
| `standards.py:96` `SHOULDER_W` | A/S/GP/G 1,25, Z 1,00, L/D 0,75 m | PTB2022 § 23 ust. 10 pkt 1-5: pobocze gruntowe 1,25 (przy pasie awaryjnym / klasa G), 1,00 (Z), 0,75 (L/D) — standardowo; w trudnych min 0,50-0,75 | ZGODNE |
| `standards.py:97` `PAVED_SHOULDER` | 1,00 m | pobocze utwardzone — brak sztywnej wartości minimalnej w PTB2022 (cz. pobocza o nawierzchni twardej projektuje się wg potrzeb) | WORKING_VALUE |
| `standards.py:67` `CROSSFALL` | 0,02 | WT 1999 § 17 + tabele: pochylenie poprzeczne jezdni 2% na odcinku prostym; PTB2022 § 18 wymóg wynikowy („skuteczne odwodnienie”) | ZGODNE (2% = wartość tabelaryczna WT 1999, przyjęta w PTB2022 jako praktyka; repo oznacza WORKING_VALUE) |
| `standards.py:68-71` `CROSSFALL_CURVE`/`CURVE_R`/ramy | 0,025 / R<400 m | WT 1999 § 21 tabele przechyłki na łukach; PTB2022 wynikowe | WORKING_VALUE |
| `standards.py:75-76` `KERB_HEIGHT`/`KERB_TOP_W` | 0,13 m / 0,15 m | WT 1999 § 43 ust. 5: krawężnik 6-16 cm ponad jezdnię; PTB2022 § 89 ust. 2 pkt 1: krawężnik ≥ 0,12 m = podniesiony | ZGODNE (0,13 mieści się w 0,06-0,16; WORKING_VALUE w repo) |
| `standards.py:84` `KERB_HEIGHT_APRON` | 0,04 m | krawężnik najazdowy (przejezdny) ronda — przepis nie narzuca wysokości; praktyka 0-5 cm | WORKING_VALUE |
| `standards.py:87-88` `SIDEWALK_W`/`SIDEWALK_CROSSFALL` | 2,00 m / 0,02 | WT 1999 § 43 ust. 2: chodnik przy jezdni ≥ 2,0 m (PTB2022 § 29: droga dla pieszych ≥ 1,80 m w zabudowie); pochylenie w stronę jezdni ≤ 3% (§ 33) | ZGODNE |
| `standards.py:112` `CURB_RADIUS` | A/S 20, GP 15, G 12, Z 10, L/D 8 m | WT 1999 § 73-74: wewnętrzna krawędź pasa skręcających — łuki 10-40 m wg klasy, krzywa koszowa ≥ 9 m; PTB2022 § 58 ust. 3: wynikowo (przejazd pojazdu projektowego) | WORKING_VALUE (L/D 8 m poniżej zakresu tabeli WT 1999, ale PTB2022 nie narzuca tabeli — bez jednoznacznej rozbieżności) |
| `standards.py:126-127` `ROUNDABOUT_APRON_W`/`ROUNDABOUT_CROSSFALL` | 2,0 m / 0,02 | geometria ronda (średnica wyspy, szerokość jezdni) wynika w generatorze z danych OSM, nie ze stałej; PTB2022 rozdział o rondach — wymogi wynikowe | WORKING_VALUE |
| `standards.py:141-142` `CLEARANCE_BY_CLASS`/`BRIDGE_CLEARANCE` | A/S 5,00 m, pozostałe 4,50 m | PTB2022 § 80 ust. 1 pkt 1-2 | ZGODNE |
| `standards.py:52-57` `MAX_GRADE_BY_VP`/`MAX_GRADE_RAMP`/`MAX_GRADE_SERVICE` | wg Vp tabelarycznie; łącznice ≤ 7% | PTB2022 § 20 ust. 2 (tabela wg prędkości projektowej), § 62 ust. 2 (łącznice ≤ 7%) | ZGODNE-Z-CYTATEM |
| `standards.py:63` `VCURVE_MIN_R` | 150-2000 m wg klasy | PTB2022 § 20 ust. 1 wynikowe (krzywe wyokrąglające niweletę) — brak tabeli | WORKING_VALUE |
| `standards.py:101-108` `SHOULDER_CROSSFALL`/rowy/nasypy | 6% / 0,60 m / 1:1,5 itp. | PTB2022 § 24-25 wynikowe („skuteczne odwodnienie”) | WORKING_VALUE |

## 3. Wynik audytu i decyzje

- **Nie znaleziono jednoznacznej rozbieżności** stałych z przepisami → **nie wprowadzono poprawek stałych**
  (brak osobnych commitów z cytatem przepisu — zgodnie z instrukcją poprawiamy tylko jednoznaczne rozbieżności).
- Pozostałe do zweryfikowania (oznaczone w repo i tu): `DASH["P-7a"]` = 1/1 m (rys. 2.2.2.2),
  wymiary P-11 (`P11_SQUARE`/`P11_GAP`/`P11_CLEAR`, odczyt z ortofoto), szczegóły główki P-8
  (`head_len`/`head_w`/`shaft_w` z rys. 3.2.1.2).
- Uwaga o aktach: Dz.U. 2016 poz. 124 to tekst jednolity WT z 1999 r.; od 21.09.2022 obowiązuje
  PTB2022 (Dz.U. 2022 poz. 1518) — repo już pracuje na PTB2022, co jest aktualnym stanem prawnym.
- Testy jednostkowe (bez `Data/raw`): `tests/gis/test_markings_pl_standards.py` — pilnują wartości
  przepisowych stałych (szerokości pasów § 17, opaska/pobocze § 23, szerokości linii, kreski/przerwy
  P-1, P-2a 20 m, P-10/P-12/P-13/P-14, P-8, 5,80 m, krawężnik 6-16 cm, skrajnia § 80) oraz czystych
  funkcji (`road_class`, `grade_limit`, `clearance_height`, `arrow_glyph`, `lane_layout`).

## 4. Weryfikacja

```
uv run --project tools/worldgen pytest tests/gis/test_markings_pl_standards.py -q
# 26 passed in 0.42s
```

Źródła przepisów odczytane podczas audytu: ISAP/ELI (WDU20190002311, WDU20160000124, WDU20220001518),
teksty jednolite na sip.lex.pl / eli.gov.pl oraz materiały wtórne z wymiarami z rysunków zał. nr 2
(tioman.pl — rys. 4.2.3.1/4.2.4.1/4.2.5.1; kalkulatorxxl.pl — P-7/P-10/P-11/P-14; info-car.pl — P-1a/P-1b;
strefabrd.pl — pkt 4.2.1 P-10; rankomat/znakowo — P-2a 20 m, P-8 długa >70 km/h). Zakaz Google
Maps/Street View zachowany — żadne źródło mapowe nie było używane.
