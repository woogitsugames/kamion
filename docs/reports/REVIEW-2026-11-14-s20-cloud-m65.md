# Przegląd M65 cloud (C65, drogi dla rowerów z czerwonego asfaltu: trasa C i Dojlidy) — s20, 2026-11-14

**Werdykt: SCAL z erratą.** Inwentarz OSM, przejazdy, szerokości z ortofoto i rozbieżności OSM↔obraz są kompletne i dają się sprawdzić. Główny wniosek sprawdziłem na P11-001, P11-056 i ortofoto: **w Dojlidach DDR są szare (ciepła szarość), czerwone są tylko część pól przejazdów, a w regionie C czerwonobrązowa DDR występuje wyłącznie w rejonie ronda Putry**. Ten wniosek zmienia gałąź `ddr-0188` (§5). Trzy progi liczby kadrów nie są spełnione (§1). Brakujące kadry nie zmieniają jednak żadnej liczby, którą przejmie gra, a lokalne kadry P11 z repo (`research/_incoming/mistral-p11-dojlidy-photos-v2/`) mogą je uzupełnić bez udziału autora. Dlatego erratą, a nie FIX.

- PR #70, gałąź `origin/research/cloud-p22-red-bike-paths` @ `a91a05bb5`. Diff `origin/main...` ma 29 plików, wszystkie w `research/cloud/p22-red-bike-paths/`.
- Manifest ma 241 wierszy: 93 odcinki, 92 przejazdy (w tym 38 wjazdów), 21 wierszy nawierzchni, 35 kadrów. Kolumny bloku M65 są kompletne, doszły `url_pliku` i `sha256`. Są też `overpass-result.json` (1,41 MB) i `overpass-query.ql`.
- Nic nie scalono, nic nie scommitowano, PR bez komentarza. Ten raport nie jest scommitowany.

## 1. Kryteria M65 punkt po punkcie

| # | Wymóg (MISTRAL-TASKS-10 §M65) | Wynik | Dowód recenzenta |
|---|---|---|---|
| 1 | Inwentarz z Overpass (data, zapytanie), tagi, długości, końce, jezdnia równoległa, rozdzielenie | **TAK** | Sumy w README: C 9888,1 m (7734,2 w kaflu), Dojlidy 13252,8 m (8120,4). OSM API 0.6 ponownie dla way 212811563, 238234011, 285876996, 538810153: tagi zgodne z manifestem |
| 1 | Który odcinek jest na zdjęciu (P11-001, P11-056), zgodność colour/surface | **TAK** | C65-240 (P11-001 → way 212811563, 2,2 m od osi) i C65-241 (P11-056 → 538810153 / przejazd C65-144). Obejrzałem oba (§2) |
| 2 | Szerokości DDR, chodnika, zieleni, krawężnik, skosy | **CZĘŚCIOWO** | Szerokości ESTIMATED z ortofoto 5 cm (linijka 1 m, ±0,3 m) dla 49 przekrojów. Krawężnik i skosy UNVERIFIED (uczciwie). Dokumenty: wytyczne ZDM (min. 2,0 / 1,5 m — sprawdziłem w PDF) |
| 3 | ≥ 10 przejazdów (pozycja, way, szerokość, czerwień, wyspa, znaki, sygnalizacja); wjazdy | **TAK** | 54 przecięcia z jezdniami (44 z odczytem) i 12 wjazdów obejrzanych. Pozycje węzłów 5825973689, 2163381064, 2895147443 zgodne z OSM API. Znaki C-13/C-16/D-6a są UNVERIFIED poza rondem pod estakadą |
| 4 | Wygląd czerwonej nawierzchni (opis, RAL tylko ze źródła), faktura, stan, granica | **CZĘŚCIOWO** | RAL 3020 dla przejazdów (wytyczne ZDM — sprawdzone). RAL masy DDR: UNVERIFIED (poprawnie). Faktura, zima i plamy: UNVERIFIED |
| 5 | ≥ 20 obejrzanych kadrów: ≥ 10 C, ≥ 10 Dojlidy, po ≥ 5 z przejazdem | **NIE w całości** | 17 kadrów ulicznych (15 z C, w tym 4 kontekstowe > 25 m lub z estakady) + **2 z Dojlid** (wymagane 10) + 3 pewne z przejazdem (wymagane 5). Autor zastępuje to 17 wycinkami ortofoto. Powód: Commons odpowiadał 429, a Panoramax i KartaView mają w Dojlidach 0 zdjęć |
| — | Kryteria akceptacji: suma długości, ≥ 10 przejazdów, tabela szerokości z metodą, lista rozbieżności OSM↔zdjęcie | **TAK** | README §2, §4, §3 i §7 (44 wiersze rozbieżności + 3 ogólne) |
| — | Kadry: opis „co widać”, pozycja, kierunek z API, przypisanie ≤ 25 m | **TAK** | Panoramax i KartaView mają kierunek z API. Commons ma UNVERIFIED albo z geometrii. Kadry > 25 m są jawnie oznaczone „kontekstowe” |
| — | Samokontrola ≥ 20 %, seed | **TAK** | `random.Random(20261114).sample(ids, 48)` odtwarza listę z audytu na **239** wierszach. C65-240/241 dopisano po audycie, więc nie są w próbie. Wynik: 38 PASS, 10 poprawek (szerokości przejazdów przeliczone profilem jasności) |
| — | Licencje, zakaz Google | **TAK** | Panoramax i KartaView: CC BY-SA 4.0 jako referencja. Commons: CC0. GUGiK, BIP i ELI: dane i dokumenty urzędowe. Google nie było używane |
| — | fetch.py, sha256 | **TAK** | `python -I fetch.py --skip-pdf` u mnie: **133/133 OK**, 39 768 640 B. Dla C65-240/241 sha256 dotyczy miniatur 1600 px z `thumb.php`, nie oryginałów (README §9 to mówi) |

## 2. Co obejrzałem sam (16 obrazów)

- **Kadry:**
  - Lokalne P11-012 i P11-097 (Kuronia, CC0, poza paczką; sprawdzałem, czy kadry P11 mogą uzupełnić lukę). Na obu DDR to szary asfalt z białą osią przerywaną, krawędzią i parą P-23. Chodnik z kostki leży między jezdnią a DDR.
  - P11-001 = C65-240: cały kadr i wycinek DDR (lokalna kopia 1600 px). Dodatkowo zmierzyłem średni kolor: DDR (109, 104, 101) wobec jezdni (87, 87, 88) i chodnika (129, 123, 113).
  - P11-056 = C65-241: cały kadr i wycinek przejazdu.
  - C65-208 (Panoramax): cały kadr i dwa wycinki 3× znaków.
  - C65-212 (Panoramax).
- **Ortofoto 5 cm:**
  - C65-076: Kuronia, przekrój.
  - C65-017: DDR czerwonobrązowa w C.
  - C65-144: przejazd czerwony z kadru P11-056.
  - C65-135/229 (x16): skrzyżowanie Mickiewicza/Kuronia/Dywizjonu 303 z P11-063.
  - C65-170: wjazd przy P11-001.
  - C65-226 (x04): rondo pod estakadą.
- **Zgodność z opisami:** wszystko się zgadza. Szczegóły:
  - **P11-001:** DDR to ciemny, ciepłoszary asfalt, nieco cieplejszy od jezdni (R−B ≈ +8 przy jezdni ±0), z białą przerywaną osią i ciągłą krawędzią. **Nie jest czerwona.** Opis C65-240 „lekko brunatnofioletowy odcień” jest trafny. Chodnik z kostki leży bliżej jezdni, DDR dalej od niej.
  - **x16 (skrzyżowanie P11-063):** wszystkie przejazdy mają tylko białe kwadraty P-11 przy zebrach, czerwieni nie ma. DDR dojazdowe są szare.
  - **C65-017 i C65-226:** wyraźnie czerwonobrązowa (bordowa) DDR z P-23 i osią. Na x04 przejazdy przez jezdnie mają jaskrawoczerwone pola, czyli inny odcień niż DDR.
  - **C65-170:** DDR urywa się na jasnym zjeździe do bramy, bez czerwieni.
  - **C65-208:** znaki D-6b (pieszy + rower) są na obu wycinkach.

## 3. Liczby sprawdzone u źródła (7)

Szerokości z przekrojów ortofoto (README §3) nie mierzyłem ponownie.

| # | Liczba / cytat | Źródło | Wynik |
|---|---|---|---|
| 1 | P-11: „nie może być mniejsza niż: – 1,8 m … jednokierunkowego, – 3,0 m … dwukierunkowego”, s. 569 | Dz.U. 2019 poz. 2311, `text/I/D20192311-c2.pdf` (pdftotext) | ✓ s. 569 |
| 2 | „zaleca się dodatkowe oznaczenie powierzchni przejazdu barwą czerwoną”, s. 570 | jw. | ✓ |
| 3 | przejazd połączony z przejściem „oznacza się barwą czerwoną”, s. 571 | jw. | ✓ |
| 4 | „Przejazdy rowerowe w kolorze czerwonym - kolor RAL 3020, wykonane z masy …” | wytyczne ZDM, BIP `resource/103311` (pobrane w recenzji, 21 s.) | ✓ |
| 5 | DDR jednokierunkowa min. 1,5 m, dwukierunkowa min. 2,0 m | wytyczne ZDM | ✓ |
| 6 | way 212811563: `path`, `bicycle=designated`, `segregated=yes`, `cycleway:surface=asphalt`, `footway:surface=paving_stones`; way 538810153: `segregated=yes`, `surface=paved` | OSM API 0.6, 2026-11-14 | ✓ |
| 7 | węzeł 5825973689 (C65-144) 53.104500, 23.176802, `crossing=uncontrolled`; 2163381064 (C65-129) 53.105472, 23.185316, `crossing=traffic_signals` | OSM API 0.6 | ✓ |

Przy okazji: wytyczne ZDM podają też „słupki metalowe ogrodzeń segmentowych (w kolorze czerwonym RAL 3020)”, czyli U-12a z czerwonymi słupkami, jak w M58 §4 i w grze.

## 4. Errata (do naniesienia przy scaleniu albo w następnej paczce — nie blokuje)

```
M65-ERRATA (cloud p22), recenzja s20 2026-11-14:
1. README §6 / §9 pkt 1–2: dopisać wprost „kryterium ≥ 10 kadrów z Dojlid: NIE (2); ≥ 5 kadrów z przejazdem: NIE (3 pewne);
   łącznie kadry uliczne 17 + 2 = 19 < 20; zastępczo 17 wycinków ortofoto”. Dziś to jest rozproszone w §6 i §9.
2. Uzupełnienie bez autora (lider/Argon): lokalne kadry CC0 z research/_incoming/mistral-p11-dojlidy-photos-v2/files.
   Manifest p11 opisuje DDR / przejazd / C-13 w 13 kadrach z Dojlid: P11-012, 013, 016, 024, 026, 054, 062, 063, 073,
   075, 078, 079, 097 (+ P11-001, 056, 076). Recenzent obejrzał P11-012 i P11-097: szara DDR, chodnik między jezdnią a DDR
   – zgodnie z wnioskiem M65. P11-076 (= Commons 20200726_082324) ma czerwone pole przejazdu przy rondzie Wünschego.
3. C65-240/241: sha256 dotyczy miniatury 1600 px (thumb.php), nie oryginału – dopisać w kolumnie uwagi (README §9 już mówi).
4. audit_20_percent.json: dopisać, że C65-240/241 dodano po losowaniu (próba z 239 wierszy).
5. README §0 pkt 1 i C65-240: „czy to spłowiała masa barwiona – nierozstrzygnięte” → „dla tekstury: ciepła szarość, nie czerwień;
   tak samo P11-012 i P11-097 (Kuronia)” – sam opis słowny, bez RGB (zasada bloku M65).
```

## 5. Co M65 daje grze — ADR 0188 (Argon, gałąź `ddr-0188`, niescalona)

Kod `ddr-0188` sprawdziłem w gałęzi `origin/ddr-0188` @ `c77df2c86` (stan po ponownym fetch o ~20:15; gałąź się nie zmieniła):
- `tools/worldgen/streetscape/cycleways.py`, `_surface_mat` + `classify`;
- `tools/worldgen/roads/markings.py`, ścieżka P-11 (l. ~498–515 i `_drape_crossing`).

Stan dziś:
1. Każda DDR asfaltowa, `paved` albo bez tagu dostaje `cycle_asphalt_red`. Na szaro (`path_asphalt`) przechodzi tylko przez tag `colour=grey`, którego w OSM nie ma na żadnym odcinku (C65: `colour` 0/93), albo przez override `kind: cycleway colour: grey`.
2. **Każdy** przejazd P-11 na zbudowanej DDR dostaje czerwone pole (`_emit_p11_ribbon` → `cycle_red`, `_drape_crossing` → `cycle_crossing_red`). Kod nie ma warunku, który by to wyłączał.
3. Kolor `cycle_asphalt_red` [0.238, 0.206, 0.184] skalibrowano na P11-001 („weathered, nearly grey”). Pasuje to do Dojlid, ale nie do bordowej DDR w C.
4. Override Dojlid `id … target {osm_way: [212811563]} cycle_side: away` opisuje P11-001 słowami „the red asphalt cycle track”. Według M65 i według mnie ta DDR nie jest czerwona. Strona `away` jest za to poprawna (M65 t02: jezdnia | zieleń | chodnik | DDR).

Co poprawić (wszystkie wartości ESTIMATED z ortofoto 5 cm wg M65; tam, gdzie to moja interpretacja, oznaczam WORKING_VALUE):

**A. Kolor DDR**
- **Dojlidy → ciepła szarość.** Albo zmienić nazwę i rolę `cycle_asphalt_red` na „asfalt DDR Dojlid” (kolor już pasuje do P11-001), albo dodać override `colour: grey` z ciepłym odcieniem.
  - Z przekrojem ortofoto („szary asfalt”): 180233649, 212811563, 237088754, 285876996, 290656135, 294819728, 538810153, 543330143, 692955707, 692955719.
  - Bez odczytu koloru, szarość wynika z reguły regionu (WORKING_VALUE): 674080173, 674080174, 1534813758.
  - Ciemna, w cieniu drzew, odczyt niepewny: 1534813757.
  - Nieczytelne na ortofoto: 203348234, 614216218.
  - Ciągi pieszo-rowerowe (CPR) jasnoszare, bez linii: 198376011, 212811558, 674080176.
  - Odcinki-przejazdy (tylko białe P-11): 538810152, 671082740, 671082750.
- **C, czerwonobrązowa (bordowa, matowa, ciemniejsza i mniej nasycona niż pole przejazdu):**
  - way 173985179, 177903955, 238234011, 257367441, 282244166, 284396207, 284396209, 591365139, 613145836 (wszystkie z przekrojem);
  - 173956082 jest spłowiała, różowoszara.
  - Potrzebny drugi, bardziej nasycony materiał, bo dzisiejszy `cycle_asphalt_red` to prawie szarość. Kolor WORKING_VALUE z ortofoto x02/x04/C65-017, bez kadru z ziemi: to luka.
- **C, szara (z przekrojem):** 236107938, 344253261, 591358181, 879051665, 946729182, 676746632, 999223585 (oraz 923506577/579 — `segregated=no`, więc 0188 ich nie buduje).
- **C, niepewne (README §9 pkt 7):** 257367436 i 268470393 (cień lasu, możliwy spłowiały barwiony), 741639504 (407 m, Al. Tysiąclecia, `segregated=yes`, „jasnoszara, jednolita”), 946729187, 236110049, 173985180. Bez rozstrzygnięcia nie malować na czerwono, domyślnie szare (WORKING_VALUE).
- **„Czerwona (kostka?)” według M65 — materiał niepewny:**
  - 177948306 ma `surface=paving_stones`, więc 0188 da `cycle_red`.
  - 177895175 i 350559280 nie mają tagu `surface`, więc 0188 da `cycle_asphalt_red`. Kolor czerwony jest OK, czy to kostka — UNVERIFIED.
  - 435369091 ma `segregated=no`, więc 0188 go nie buduje.

**B. Czerwone pola przejazdów: tylko tam, gdzie są.** Potrzebna lista węzłów albo override `crossing_red: false`.
- **Czerwone (25):**
  - Dojlidy: C65-131/132/138/141/142/143/144/145/148, węzły 2895147443, 2895147444, 3889955473, 5775179569, 5775179571, 5810311651, 5825973689, 5906745186, 6505679117.
  - C, z wycinkiem przejazdu: 1748446221, 1882953779, 1882953782, 2441701386, 2641555452, 3032448286, 5940539335, 6337303569, 6942794456, 9224916295.
  - C, czerwień ESTIMATED z wycinka zbiorczego x00/x12 (przypisanie do węzła z położenia, szerokość UNVERIFIED): 3032448284, 8763628068, 9224916298, 6337303579, 6942794457, 6942794461.
- **Bez oznakowania przejazdu** (ani P-11, ani czerwieni): 4391371828, 2274001610 (C); 2999994950 (Dojlidy, UNVERIFIED).
- **Nieobejrzane:** 10 drobnych przecięć w C (uliczki osiedlowe). Domyślnie białe P-11 bez czerwieni (WORKING_VALUE recenzenta: w próbie czerwień występuje głównie na skrzyżowaniach z sygnalizacją na ulicach głównych).
- **Tylko białe:**
  - **całe skrzyżowanie P11-063** (2163381053, 2163381064, 5169862895, 6284342138, oraz 3051047426/7, 5169862896, 6284342139);
  - Karpińskiego 2226186646, Żurawia 2999986094, Myśliwska 3867824994;
  - rondo pod estakadą (1852129028, 2882674810, 1859438371, 2882674819, 1852129061).
  - W tych miejscach DDR jest czerwonobrązowa, a przejazdy białe.
- Kolor pól: **RAL 3020** (wytyczne ZDM, SOURCED). Jest to powłoka na asfalcie jezdni, z wytarciem w śladach kół (C65-100/101/149).

**C. Strona DDR w ciągu `segregated=yes`** (kolumna „układ od jezdni”):
- `away` (chodnik przy jezdni): 212811563 ✓ (już jest), 180233649, 237088754 (w 25 % długości; w 75 % DDR jest przy krawężniku, a chodnik dalej — odcinek do podziału), 1534813757, 344253261, 257367436, 268470393, 591358181, 591365139. (Odcinki `highway=cycleway` bez chodnika w ciągu, np. 284396209 i 177903955, nie potrzebują strony.)
- `road` (domyślnie, DDR przy jezdni): 538810153, 543330143, 236107938, 946729182, 879051665.

**D. Szerokości** (dziś `DDR_W_TWO_WAY` 2,0, `SEG_TOTAL_DEFAULT` 4,0 — WORKING_VALUE z przepisu minimalnego):
- Dojlidy DDR: **2,45–2,8 m** (mediana ~2,65), chodnik obok 1,9–2,55 m.
- C (czerwonobrązowe) DDR: 2,2–3,3 m.
- Proponowane per way z tabeli README §3. Domyślnie DDR 2,6 m i ciąg 4,5–5,0 m (WORKING_VALUE z mediany M65).
- Pas zieleni od krawężnika: 1,9–4,7 m (bywa 0).

**E. Szerokość przejazdu:** `P11_CLEAR_TWO_WAY` 3,0 (Dz.U.) zostaje. Zmierzone mediany to 2,83 m (czerwone) i 2,70 m (białe), czyli około połowa poniżej normy. To informacja, nie zmiana.

**F. Wjazdy do posesji:**
- W Dojlidach DDR **urywa się**: zjazd z kostki lub betonu przechodzi przez nią, P-23 jest po obu stronach, bez czerwieni (C65-168/170/175/177/182).
- W C zdarzają się czerwone prostokąty bez kwadratów (C65-153/157).
- 0188 robi dziś obniżenia krawężnika przy jezdniach. Sprawdzić, czy na drogach `service` nie kładzie czerwieni ani P-11.

**G. P-23:** 1,1 × 2,0 m. Wytyczne ZDM (C65-199) potwierdzają wartość już użytą w 0188 ✓.

**Kontrola po zmianach (render r4/r5 Argona):**
- photo_P11-001: DDR w ciepłej szarości, nie czerwona.
- photo_P11-063: przejazdy białe.
- photo_P11-056: pole czerwone.
- Rondo Putry (C): DDR bordowa, przejazdy białe.

## 6. Dla lidera

- **Scalić PR #70.** Diff dotyczy tylko `research/cloud/p22-red-bike-paths/`. Errata 1–5 nanieść przy scaleniu. Niespełnione progi kadrów są zapisane jawnie i nie zmieniają danych.
- **Przekazać Argonowi (0188) §5 A–G przed scaleniem `ddr-0188`.** Dziś gałąź pomalowałaby na czerwono przejazdy na skrzyżowaniu z kadru P11-063 i nazywa DDR z P11-001 czerwoną. To jest dokładnie to, co M65 obala.
