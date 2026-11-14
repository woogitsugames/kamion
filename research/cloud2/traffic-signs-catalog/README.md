# R1: katalog znaków pionowych A/B/C/D/F/T (cloud2, s20)

**Data:** 2026-11-14 · **Gałąź:** `research/cloud2-traffic-signs-catalog` · **Wykonawca:** agent R1 (Claude)
**Wiersze:** `manifest.csv` 297 (SOURCED 287, ESTIMATED 8, UNVERIFIED 2) · `catalog.csv` 265 znaków · `sizes.csv` 130
**Obejrzane:** 11 aktów (PDF, 8 czytanych merytorycznie) i około 50 rastrów stron (tabele-obrazy, rysunki konstrukcyjne, barwne wzory), w tym 14 ponownie w samokontroli.
**Samokontrola** (seed 20261114, 20 %): manifest 60/60 PASS, katalog 51/53 PASS, 2 FAIL poprawione (B-23, F-12) oraz 4 korekty poza próbą. Szczegóły w `audit_20_percent.json`.

## 1. Który akt jest o czym (weryfikacja ISAP/ELI)

| Akt | Tytuł (skrót) | Co zawiera dla znaków pionowych |
|---|---|---|
| **Dz.U. 2019 poz. 2310** | obwieszczenie MI i MSWiA z 31.10.2019. Tekst jednolity **rozporządzenia w sprawie znaków i sygnałów drogowych** (MI i MSWiA, 31.07.2002) | **Znaczenie** znaków (§), **spis kodów i nazw** (zał., PDF s. 29–40), **barwne wzory** (PDF s. 41–50). Wymiarów, barw liczbowych i zasad montażu tu nie ma. |
| **Dz.U. 2019 poz. 2311** | obwieszczenie MI z 9.09.2019. Tekst jednolity **rozporządzenia MI z 3.07.2003 w sprawie szczegółowych warunków technicznych dla znaków i sygnałów drogowych oraz urządzeń BRD i warunków ich umieszczania na drogach** | **Zał. 1 = znaki pionowe**: grupy wielkości, wymiary, barwy CIE i β, odblask, folie, liternictwo, montaż, opisy szczegółowe, rysunki konstrukcyjne (rozdz. 9). Zał. 2 obejmuje znaki poziome, zał. 3 sygnały, a zał. 4 urządzenia BRD (§ 1, PDF s. 5). |

Oba akty były **nowelizowane po 2019 r.**, a nowelizacje zmieniają liczby, których używamy:
- 2311: Dz.U. 2021 poz. 438, **2021 poz. 2066**, **2022 poz. 2377**, **2026 poz. 132**. Tabela wysokości 1.11 ma dziś brzmienie z 2022 poz. 2377. Wysokość D-42 zmieniono z 530 na **600 mm**.
- 2310: Dz.U. 2021 poz. 433 (nazwa B-19), 2021 poz. 2065 (D-23b, D-23c, D-34b, F-14d–f), 2022 poz. 2372 (wzór D-39), 2026 poz. 133 (F-23, F-24).

Strony podajemy jako numer strony pliku PDF. W 2310 i 2311 cz. 1 jest on równy numerowi strony Dziennika Ustaw. Wewnętrzna numeracja załącznika („– 4 –”) to strona Dz.U. minus 5.

## 2. Metoda
1. Pobranie PDF z API ELI (`fetch.py`, sha256), potem `pdftotext -layout` z markerami stron (`tools/pdf_to_pages.py`).
2. Spis znaków: parser listy z 2310 (`tools/parse_list_2310.py`) i ręcznie wpisane nowelizacje. Mapowanie na rysunki opisu i rysunki konstrukcyjne 2311: `tools/parse_fig9.py` oraz ręczne uzupełnienia (C-1/C-3/C-9/C-10 kopiowane z C-5, F-3a/b, T-30a–i, znaki z nowelizacji).
3. Tabele, które w PDF są obrazem (1.2, 1.5, 1.6, 1.8, 1.9, 5.1, 9.7.1 oraz rysunki), przepisano z rastra strony (110–300 dpi) **po obejrzeniu**. Tabele z warstwą tekstową (1.1, 1.3, 1.4, 2.1, 3.1, 4.1) porównano z rastrem.
4. Barwy znaków: akt **nie opisuje słownie** barwy każdego znaku. Kolumny barw w `catalog.csv` to więc odczyt wizualny barwnego wzoru 2310 (status ESTIMATED, strona w kolumnie `wzór_barwny_strona`). Wyjątki opisane słownie w 2311 (T-34, B-24, D-18) mają status SOURCED.
4a. Barwy B-24 i D-18: SOURCED dotyczy tylko elementu z cytatu (szary symbol, biały symbol pojazdu); pozostałe barwy są ESTIMATED (`status_barw`).
5. Generatory: `tools/build_catalog.py`, `tools/build_manifest.py`. Kontrola barw generatora gry: `tools/check_generator_colors.py`. Samokontrola: `tools/audit_sample.py`.

## 3. Wyniki dla generatora znaków

### 3.1 Wymiary tarcz [mm] (2311 tab. 1.1 s. 9, tab. 2.1 s. 49, tab. 3.1 s. 97, tab. 4.1 s. 157, tab. 5.1 s. 178)

| Grupa | A trójkąt: bok b / R / r / obrzeże s / moduł a | B koło: d / obrzeże s / obwódka uchyl. g / pas p / a | C koło: d / obwódka g / a | D: podstawa l / wysokość h / białe pole s / b / c / g / r |
|---|---|---|---|---|
| wielkie W | 1200 / 72 / 32 / 40 / 120 | 1000 / 100 / 10 / 150 / 100 | 1000 / 10 / 100 | 1200 / 1200+300n / 880 / 160 / 300n+160 / 12 / 30 |
| duże D | 1050 / 63 / 28 / 35 / 105 | 900 / 90 / 9 / 135 / 90 | 900 / 9 / 90 | 900 / 900+225n / 660 / 120 / 225n+120 / 9 / 30 |
| średnie S | 900 / 54 / 24 / 30 / 90 | 800 / 80 / 8 / 120 / 80 | 800 / 8 / 80 | 600 / 600+150n / 440 / 80 / 150n+80 / 6 / 30 |
| małe M | 750 / 45 / 20 / 25 / 75 | 600 / 60 / 6 / 90 / 60 | 600 / 6 / 60 | 600 / 600+150n / 440 / 80 / 150n+80 / 6 / 30 |
| mini MI | 600 / 36 / 16 / 20 / 60 | 400 / 40 / 4 / 60 / 40 | 400 / 4 / 40 | 400 / 400+100n / 300 / 50 / 100n+50 / 4 / 30 |

n = 0, 1, 2. Dla D-1 i D-2 obwódka g = l/50, dla D-42–D-47 g = l/60. Kratka białego pola s1 = s/8.

Kształty i wyjątki:
- **A-7**: trójkąt odwrócony, tylko w grupach D i S (R1-041).
- **B-20**: ośmiokąt, tylko D i S. Wymiar d to średnica koła wpisanego (R1-063). Białe obrzeże ma szerokość a/3 (rys. 9.2.28 s. 385). Na drogach z grupą M stosuje się B-20 w grupie S.
- Ukośny pas znaków uchylających: 68°, szerokość p z tab. 3.1. B-42 ma pas a/2 (s. 397).
- **B-39**: 900×1300. **B-40, B-43, B-44**: 900×900 (R30, obwódka 10, znak wewnętrzny Ø600, cyfry 270). **C-17**: 900×1200 (s. 395–398, 404).
- **D-1**: romb (kwadrat z przekątną poziomą), bok l z tab. 5.1. Przy powtórzeniach wzdłuż drogi bok wynosi **400** (s. 185).
- **D-19/D-20**: **620×300** (pkt 5.2.19 s. 227; Dz.U. 2022 poz. 2377 s. 2). Rys. 9.4.27 podaje 600 jako wymiar wewnątrz obwódki 10 (poprawka po recenzji). **D-42/D-43**: 1200×700. Na jednojezdniowych drogach powiatowych i gminnych dopuszcza się 1200×**600** (Dz.U. 2022 poz. 2377 s. 4).
- F nie ma tabeli. Wymiary podaje każdy rysunek, np. F-12 600×750, F-13 wys. 400 (korpus 650 + grot 200), F-22 1400×1960 (s. 481, 487).
- **Tabliczki T** (tab. 9.7.1 s. 487), w kolejności wielkie i duże / średnie i małe: wysokość tabliczki h = **350 / 250**, wysokość cyfr d = **162 / 132**, grubość kreski gr = 27 / 22, promień naroża r = 30, odstęp obwódki c = 10. Szerokość tabliczki zależy od napisu.

### 3.2 Którą grupę wielkości stosować (2311 pkt 1.2.1, s. 7–8)

| Grupa | Gdzie |
|---|---|
| W | autostrady, przy jezdniach głównych |
| D | drogi ekspresowe (jezdnie główne); dwujezdniowe poza obszarem zabudowanym; dwujezdniowe w obszarze zabudowanym o v_dop > 60 km/h |
| S | łącznice A/S; dwujezdniowe w obszarze zabudowanym o v_dop ≤ 60 km/h; **jednojezdniowe drogi krajowe i wojewódzkie**; powiatowe (bez drogowskazów tablicowych) |
| M | drogi gminne; drogowskazy tablicowe na drogach powiatowych |
| MI | słupki przeszkodowe; obszar zabudowany przy braku miejsca; strefa zamieszkania i strefa 30; drogi dla rowerów i pieszych |

Dodatkowo: przy robotach drogowych stosuje się grupę o jedną wyższą, a na autostradach W. A-7 i B-20 mają tę samą grupę co znaki drogi z pierwszeństwem, ale co najmniej S. C-9, C-10 i C-11 mogą być w grupie niższej.

Dla Białegostoku w grze: ulice dwujezdniowe ≤ 60 km/h i drogi krajowe jednojezdniowe → **S** (A 900, B/C 800, D 600). Drogi gminne → **M** (A 750, B/C 600). S8 → **D** (A 1050, B/C 900, D 900).

### 3.3 Barwy (2311 tab. 1.3 i 1.4, s. 11)

Pomiar: geometria 45°/0°, obserwator 2°, iluminant D65. Narożniki pól tolerancji podano w CIE 1931 (x;y).

| Barwa | narożnik 1 | 2 | 3 | 4 | β min. folia typu 1 / typu 2 | sRGB pochodne (ESTIMATED) |
|---|---|---|---|---|---|---|
| biała | 0,355;0,355 | 0,305;0,305 | 0,285;0,325 | 0,335;0,375 | 0,35 / 0,27 | #A1A099 |
| żółta | 0,545;0,454 | 0,487;0,423 | 0,427;0,483 | 0,465;0,534 | 0,27 / 0,16 | #B58700 |
| czerwona | 0,735;0,265 | 0,674;0,236 | 0,569;0,341 | 0,655;0,345 | 0,05 / 0,03 | #90000D |
| zielona | 0,007;0,703 | 0,248;0,409 | 0,177;0,362 | 0,026;0,399 | 0,04 / 0,03 | #004930 |
| niebieska | 0,078;0,171 | 0,150;0,220 | 0,210;0,160 | 0,137;0,038 | 0,01 / 0,01 | #001C3F |
| pomarańczowa | 0,610;0,390 | 0,535;0,375 | 0,506;0,404 | 0,570;0,429 | 0,15 / 0,14 | #B05000 |
| brązowa | 0,455;0,397 | 0,523;0,429 | 0,479;0,373 | 0,558;0,394 | 0,03 / 0,03 | #4C260C |
| szara | 0,350;0,360 | 0,300;0,310 | 0,285;0,325 | 0,335;0,375 | 0,12 / 0,12 | #60625C |
| szara (powłoka kryjąca) | 0,305;0,315 | 0,350;0,360 | 0,340;0,370 | 0,295;0,325 | 0,08–0,10 | – |
| czarna (powłoka kryjąca) | 0,300;0,270 | 0,385;0,335 | 0,345;0,395 | 0,360;0,310 | ≤ 0,02 | – |

„sRGB pochodne” policzono ze środka ciężkości pola i Y = β_min folii typu 1. Jest to **dolna granica jasności**: prawdziwe folie są jaśniejsze, więc tych wartości nie należy kopiować do tekstur. **Zielona #004930 (R1-181) leży poza polem tolerancji**: centroid pola jest poza gamą sRGB i konwersja go przycięła.

**RAL:** akt nie podaje odpowiedników RAL. **PN-EN 12899-1:** norma niedostępna otwarcie (UNVERIFIED).

**Kontrola barw generatora** `tools/worldgen/streetscape/signs.py` (main 81c9bae) skryptem `tools/check_generator_colors.py`:
- czerwona, żółta, niebieska, biała i szara mieszczą się w polach tolerancji, a Y przekracza β_min.
- **zielona (0,112,72) wychodzi poza pole** (x = 0,257 > 0,248). Pole zielonej folii leży prawie całkowicie poza gamą sRGB. Część wspólna pola i gamy sRGB to wąski pas przy narożniku (0,248; 0,409). Margines wewnątrz pola wynosi tam najwyżej około +0,0007 w x/y, a (0,84,62) i (0,137,103) leżą praktycznie na narożniku. Wierne odtworzenie tej zieleni w sRGB nie jest możliwe. **Wybór barwy (np. narożnik pola albo najbliższy punkt gamy) to decyzja lidera i wymaga ADR.** Dotyczy znaków E oraz F-14d–f.

Odblask (tab. 1.5 i 1.6, s. 12): minimalne R' przy α = 0,2° i β1 = 5° wynosi dla folii typu 1 / typu 2 [cd/(lx·m²)]: biała 70/250, żółta 50/170, czerwona 14,5/45, zielona 9/45, niebieska 4/20, brązowa 1/12, pomarańczowa 25/100. Proporcje te nadają się do nocnej jasności lic w shaderze; folia typu 2 jest około 3,5× jaśniejsza od typu 1.

### 3.4 Folie (2311 tab. 1.2 s. 10; Dz.U. 2021 poz. 2066 s. 1)

| Położenie | A i S | krajowe dwujezdniowe | krajowe jednojezdniowe międzynarodowe | inne krajowe | wojewódzkie | powiatowe i gminne |
|---|---|---|---|---|---|---|
| obok jezdni | typ 2 | typ 2 | typ 2 | typ 1* | typ 1* | typ 1* |
| nad jezdnią | pryzmatyczna | typ 2 | typ 2 | typ 2 | typ 2 | typ 2 |

*Znaki A-7, B-2, B-20, D-6, D-6a i D-6b zawsze na folii typu 2. Przy robotach drogowych typ 2 lub pryzmatyczna. Folia pryzmatyczna musi spełniać co najmniej wymagania typu 2.
Folię fluorescencyjną żółto-zieloną (lub pomarańczową) dopuszcza się na A-10, A-14, A-17, A-30, T-27, D-6, D-6a, D-6b (tło), D-51 i D-51a. Rewers tarczy jest szary. T-34 wykonuje się na folii typu 2.

### 3.5 Liternictwo (2311 pkt 1.4, s. 14–26; pkt 1.4.1 w brzmieniu Dz.U. 2026 poz. 132)
- **Akt nie podaje nazwy kroju.** Litery i cyfry są zdefiniowane rysunkami na siatce „gr” (pkt 1.4.3, s. 21–26). Słowo „Drogowskaz” jako nazwa kroju nie występuje ani w 2310, ani w 2311 (UNVERIFIED).
- Proporcje: d = 6 gr, m = 4 gr, wiersz 8 gr, interlinia 2 gr. Odstęp między literami 1,5 gr (na folii pryzmatycznej 1,8 gr), między wyrazami 4,5 gr, od obwódki co najmniej 2 gr. Szerokości znaków podaje tab. 1.10 (s. 18–19).
- Wysokość liter dużych d [mm] według grupy (tab. 1.8 s. 16): I 42, II 72, III 102, IV 132, V 162, VI 210, VII 282, VIII 348, IX 420.
- Grupy liter według kategorii znaku (tab. 1.9 s. 17), w kolejności W / D / S / M:
  - B (bez B-33 i B-34): VI–III / VI–II / V–II / IV–I.
  - D: V–III / V–II / IV–I / IV, III, I.
  - F: II, I we wszystkich grupach.
  - T: V,IV / V,IV / IV,III / IV,III.
- Napisy na tabliczkach pod znakami zakazu mają wysokość **72 lub 42 mm**, a tabliczka nie może być szersza od znaku (s. 99). Na B-39 napisy mają 102/68 i 72 mm (s. 395), na B-43 cyfry 270 mm, na D-19 (620×300) napis „TAXI” 210 mm.

### 3.6 Montaż (2311 pkt 1.5; tab. 1.11 w brzmieniu Dz.U. 2022 poz. 2377 s. 2)

| Co | Wartość | id |
|---|---|---|
| dolna krawędź znaków A–D, F, G poza obszarem zabudowanym | min. 2,00 m (kilka znaków na jednej konstrukcji bez ruchu pieszego: min. 1,50) | R1-238/239 |
| j.w. w obszarze zabudowanym | min. 2,00 m; **na chodniku albo nad chodnikiem min. 2,20** | R1-240/241 |
| znaki nad jezdnią | min. 5,00 m | R1-246 |
| na urządzeniach BRD lub za nimi | 0,90–1,20 m | R1-247 |
| F-11 / F-14a–f / G-1 | 5,00 / min. 0,50 / 1,00 na ulicach i 0,50 poza nimi | R1-248–250 |
| E-1, E-2, E-14 poza obszarem zabudowanym | min. 1,00 m | R1-242 |
| nad drogą dla rowerów / na drodze dla rowerów | min. 2,50 / min. 1,0 (2,2 przy ruchu pieszym) | R1-252/253 |
| punkt odniesienia wysokości | dolna krawędź znaku. Na ulicach w obszarze zabudowanym liczy się dolna krawędź tabliczki pod znakiem | R1-251 |
| odległość boczna na ulicach | **0,50–2,00 m** od krawędzi jezdni. Krawężnik miejski wlicza się do chodnika | R1-259/262 |
| odległość boczna na drogach z poboczem | min. 0,5 m od krawędzi korony; pobocze gruntowe min. 0,50 od jezdni; pobocze twarde min. 0,50 od krawędzi pobocza; szeroki nasyp maks. 5 m | R1-254–257 |
| pas dzielący / tor tramwajowy / razem z sygnalizatorem | min. 0,50 od opaski / min. 1,95 od osi toru / 0,50–1,00 | R1-258, 260, 263 |
| kąt tarczy | odchylona około **5°** od prostopadłej do osi jezdni, w stronę jezdni. Na łuku w prawo 0–5°, na łuku w lewo 5–10° | R1-264–266 |
| odstęp między kolejnymi znakami | min. 50 m przy v_dop > 90 km/h, 20 m przy > 60 km/h, 10 m na pozostałych | R1-267–269 |
| słupek | 2 lub 3 znaki na słupku. Z A-7 może stać tylko jeden dodatkowy znak. Beton najwyżej 0,15 m nad gruntem | R1-270–272 |
| powtórzenie po lewej stronie (obowiązkowe) | drogi dwujezdniowe z więcej niż jednym pasem: A, B (bez B-35–B-38), G, D-6, D-6a, D-6b | R1-273 |

**Odległość znaków ostrzegawczych od miejsca niebezpiecznego** (pkt 2.1.2, s. 50):
- przy v_dop > 60 km/h: 150–300 m; na pozostałych drogach: do 100 m;
- zalecane: 300 m przy v ≥ 100 km/h, 250–300 m przy 90, 200–250 m przy 80, 150–200 m przy 70, 50–100 m przy v ≤ 60;
- poniżej 50 m tylko wyjątkowo.

Inne odległości:
- **A-7** stoi najdalej 50 m od skrzyżowania przy v > 60 km/h i 25 m na pozostałych drogach. Przy v > 60 poprzedza go A-7 z T-1 w odległości 150–300 m (s. 64).
- **B-20** stoi najdalej 25 m od skrzyżowania w obszarze zabudowanym. Przy v > 60 poprzedza go A-7 z tabliczką „Stop” w odległości 150–300 m (s. 126).
- Znaki C-1…C-12 stoją najdalej 25 m od krawędzi jezdni drogi poprzecznej (s. 158).
- T-1 podaje odległość z dokładnością do 10 m, T-2 długość z dokładnością do 0,5 km.

### 3.7 C-1 czy C-2 (rozstrzygnięcie, R1-293/294)
- **C-1** „nakaz jazdy w prawo przed znakiem”: **strzałka pozioma w prawo**. Pod rys. 9.3.1 (s. 398) akt stwierdza: „Wzór znaku [C-5] … może być wykorzystany do kopiowania znaków C-1, C-3, C-5, C-9 i C-10 po dokonaniu obrotu osi strzałki o 135° i 90°”. Potwierdzają to rys. 4.2.1.1 (s. 158) i wzór 2310 s. 43.
- **C-2** „nakaz jazdy w prawo za znakiem”: **strzałka w górę, zakręcająca w prawo** (rys. 4.2.2.1 s. 159, rys. 9.3.2 s. 399, wzór 2310 s. 43). C-4 jest jej lustrzanym odbiciem.
- Strzałka „w górę i w prawo” oznacza więc **C-2**. Uwaga z REVIEW-2026-11-14-s20-mistral-m62 §„Możliwa errata” jest słuszna. Zestawienie stron: `files/_view/c1c2.png`.

## 4. Co już było w repo, a co jest nowe

| Temat | Było | Teraz (R1) |
|---|---|---|
| Wymiary A/B/D w grupie S | G5-031 jako UNVERIFIED („A 0.90 / B 0.80 / D 0.60”, według ADR generatora); stałe `SIGN_SIZE` w `roads/standards.py` z cytatem tab. 1.1 | SOURCED dla wszystkich 5 grup i kategorii A, B, C, D, T (R1-001…138). Wartości G5-031 i generatora są **poprawne**. |
| Wysokości montażu | `standards.py` cytuje tab. 1.11 (2,00 / 2,20 / 5,00) | SOURCED z **aktualnym brzmieniem** (2022 poz. 2377): 2,20 obowiązuje także **nad chodnikiem**. Doszły pozostałe wiersze tabeli. |
| Odległość boczna | `SIGN_LATERAL = 0.75` WORKING_VALUE | SOURCED zakres 0,50–2,00 m na ulicach (R1-259). 0,75 mieści się w zakresie. |
| Barwy | `signs.py` „nominal sRGB, WORKING_VALUE until checked against the regulation's colour table” | Tab. 1.3/1.4 SOURCED i kontrola barw generatora (zielona poza polem). |
| Oznakowanie poziome | gptpro/p2-surfaces (zał. 2) | Nie dublowano. |
| Ograniczenia ciężarówek (B-5, B-16, B-18, B-19) | G10, P8-2, M54 | Nie dublowano; dodano tylko aktualną nazwę B-19 (patrz errata). |

## 5. Errata do wcześniejszych pakietów i plików

1. **docs/reports/REVIEW-2026-11-13-s20-mistral-m47-fix2.md §3**:
   - wiersz **005** ma ocenę „C-2 (strzałka pozioma w prawo)”, co jest wewnętrznie sprzeczne, bo strzałka pozioma to **C-1** (pkt 3.7). Trzeba ponownie obejrzeć kadr P11-005: jeśli strzałka jest pozioma, poprawny kod to C-1.
   - wiersz **129** ma „strzałka zakrzywiona = C-1”, co jest **błędne**: zakrzywiona strzałka (w górę, potem w prawo) to **C-2**. Potwierdza to uwagę z REVIEW m62 i manifest P11-129 należy poprawić na C-2.
   - wiersz **063** („C-2 ✓”) wymaga sprawdzenia kształtu strzałki według tej samej reguły.
   - Zdjęć z Commons nie obejrzałem ponownie (HTTP 429), więc korekta dotyczy definicji, a przypisanie kodu do kadrów musi potwierdzić lider.
2. **Ta sama recenzja, wzorzec (a)**: zdanie „A-16 to czerwony trójkąt” jest nieprecyzyjne. Znaki A mają **żółte** tło i **czerwone obrzeże** (2310 s. 41). Kryterium odróżnienia od D-6 pozostaje bez zmian.
3. **research/g5-street-furniture** (README l. 61, sources S9, G5-031):
   - twierdzenie „załączniki jako skany / tekst nie był przeszukiwalny” jest nieścisłe: zał. 1 do 2311 **ma warstwę tekstową** (tab. 1.1, 2.1, 3.1, 4.1 i opisy dają się wyciągnąć `pdftotext`); obrazami są tylko część tabel i rysunki;
   - G5-031 można zmienić na SOURCED (R1-003, R1-008, R1-015).
4. **research/gptpro/p2-surfaces/sources.md** poz. 1: tytuł „Rozporządzenie Ministra Transportu z 11 września 2019 r. w sprawie szczegółowych warunków technicznych…” jest **błędny**. Dz.U. 2019 poz. 2311 to **obwieszczenie Ministra Infrastruktury z 9 września 2019 r.** ogłaszające tekst jednolity **rozporządzenia Ministra Infrastruktury z 3 lipca 2003 r.** (R1-296).
5. **research/gptpro/p8-truck-restrictions-2** (P8-037, README l. 105): definicja „B-19 = nacisk pojedynczej osi napędowej” jest przypisana do „Dz.U. 2019 poz. 2310 t.j.” przez serwis wtórny (lexlege). W t.j. 2019 nazwa brzmiała „zakaz wjazdu pojazdów o nacisku osi większym niż … t” (2310 s. 30). Obecne brzmienie („nacisku pojedynczej osi napędowej powyżej … t”, a dla grupy osi 80 % masy) pochodzi z **Dz.U. 2021 poz. 433** (§ 1 pkt 1 i 3). Wartość merytoryczna jest dobra, źródło nie.
6. **Kod gry** (tylko do decyzji lidera, kodu nie zmieniałem):
   - `tools/worldgen/streetscape/signs_route.py` (docstring: „Załącznik 1 (A-D) and 4 (E)”): znaki E też są w **zał. 1** (część 6, s. 256+), a zał. 4 dotyczy urządzeń BRD;
   - `signs.py` cytuje nowelizacje tylko do 2021 poz. 2066 (brakuje 2022 poz. 2377 i 2026 poz. 132);
   - barwa `GREEN` leży poza polem tolerancji (pkt 3.3);
   - `standards.py`: wartość 2,20 m dotyczy też znaku nad chodnikiem (2022 poz. 2377).

## 6. Luki
- Barwy poszczególnych znaków w `catalog.csv` są **ESTIMATED**: to odczyt barwnych wzorów 2310 przy 110–200 dpi, bo akt nie opisuje ich słownie. Kształt D/F/T (kwadrat albo prostokąt pionowy/poziomy) też jest ESTIMATED tam, gdzie nie ma wymiaru na rysunku.
- Znaczenie symboli z, l, g1, k, d1 w tab. 9.7.1 przyjąłem z rysunku 9.7.1 bez opisu słownego (oznaczone w `uwagi`).
- Wymiary znaków F podano tylko dla F-12, F-13 i F-22. Pozostałe są na rysunkach 9.6.x (strony w `catalog.csv`) i można je przepisać, gdy generator będzie ich potrzebował.
- PN-EN 12899-1 jest niedostępna (UNVERIFIED). Brak też typowej luminancji folii (akt podaje tylko minimum).
- D-23c, T-25c i T-26 nie mają osobnego rysunku konstrukcyjnego. D-39a, D-50, F-2a, T-6d i T-33 nie mają rysunku w opisie szczegółowym (kolumny puste lub UNVERIFIED).
- Kadry P11-005, P11-063 i P11-129 nie zostały ponownie obejrzane (Commons zwracał 429).

## 7. Jak używać w grze
- `sizes.csv` to płaska tabela (znaki, kształt, grupa, parametr, wartość_mm, źródło). Generator wybiera grupę według klasy drogi (pkt 3.2) i bierze bok, średnicę, obrzeże i moduł; geometria piktogramu skaluje się modułem a (siatka 10×10 a).
- `catalog.csv` daje kod, nazwę, kształt, barwy (tło / obrzeże / symbol) i strony rysunków konstrukcyjnych (rys. 9.x) do odtwarzania piktogramów **własnymi prymitywami**, bez kopiowania rastrów z aktu.
- Montaż: wysokość dolnej krawędzi 2,00 m, a na chodniku lub nad nim 2,20 m. Odsunięcie boczne 0,5–2,0 m (generator ma 0,75). Kąt tarczy 5° w stronę jezdni. Kolejne znaki co najmniej 10, 20 lub 50 m zależnie od v_dop. Znaki ostrzegawcze według tabeli z pkt 3.6.
- Barwy: chromatyczność z pola tolerancji (tab. 1.3), jasność ≥ β_min. Noc: stosunek R' typ 2 do typ 1 (pkt 3.3). Barwę zieloną ustala lider w ADR (patrz pkt 3.3; w sRGB nie ma punktu wyraźnie wewnątrz pola).
- Odtworzenie wszystkiego: `python -I fetch.py && python -I tools/pdf_to_pages.py files/D20192310.pdf files/_derived/2310_p.txt && python -I tools/pdf_to_pages.py files/D20192311-c1.pdf files/_derived/2311_p.txt && python -I tools/build_catalog.py files/_derived/2310_p.txt files/_derived/2311_p.txt . && python -I tools/build_manifest.py .`

Rozmiar plików pobieranych przez `fetch.py`: około 55 MB (11 PDF, wszystkie z sources.md; główny plik 2311 cz. 1 ma 39,7 MB).

Recenzja lidera: `REVIEW.md` (FIX, P1 1–5 poprawione na tej gałęzi).

## Errata lidera (s20, 2026-11-14)
Patrz `docs/reports/REVIEW-2026-11-14-s20-cloud2-r1.md` — errata obowiązuje przed użyciem danych.
