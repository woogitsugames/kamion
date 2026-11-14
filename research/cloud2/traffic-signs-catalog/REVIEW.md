# Przegląd R1 traffic-signs-catalog (cloud2, katalog znaków pionowych A/B/C/D/F/T): s20, 2026-11-14

**Werdykt: FIX.** Rdzeń pakietu jest dobry i da się go sprawdzić. Te elementy zgadzają się co do cyfry z rastrem stron PDF:
- tabele 1.1, 2.1, 3.1, 4.1, 5.1 i 9.7.1;
- narożniki pól barw i wartości β (tab. 1.3 i 1.4);
- R' (tab. 1.5 i 1.6);
- grupy wielkości (pkt 1.2.1) i tabela wysokości 1.11 w brzmieniu z Dz.U. 2022 poz. 2377.

Rozstrzygnięcie C-1/C-2 jest poprawne. Erraty do wcześniejszych pakietów potwierdzają się w repo. Seed samokontroli da się odtworzyć. Nie ma błędu, który blokowałby PR (P0). Przed scaleniem trzeba jednak poprawić pięć rzeczy (P1):
1. **D-19/D-20 mają 620×300, a nie 600×300.** Wykonawca wziął wymiar wewnętrzny z rysunku. Wymiar 620 podaje tekst aktu i ta sama nowelizacja 2022/2377, którą pakiet cytuje.
2. „sRGB pochodna” zielonej (#004930, R1-181) **leży poza polem tolerancji**, a README podaje ją w tabeli jako wartość z pola.
3. `fetch.py` pobiera 8 z 11 aktów. Brakuje 2021/433, 2021/2065 i 2026/133, a na nich opiera się część nazw w `catalog.csv`.
4. Znaczniki czasu w STATUS.md i sources.md są z przyszłości: 17:55–19:10 UTC przy commitach 17:12–17:29 UTC.
5. Dla B-24 i D-18 status barw całego wiersza to SOURCED, choć cytat obejmuje tylko jeden element.

Nic nie scommitowano, nic nie scalono.

## 1. Zakres i metoda

- Gałąź `origin/research/cloud2-traffic-signs-catalog` @ `b03abb9` (5 commitów od main). Sprawdziłem w osobnym worktree `--detach`. `git diff --stat origin/main...HEAD` pokazuje 16 plików wyłącznie w `research/cloud2/traffic-signs-catalog/`. Są to pliki tekstowe (największy: manifest.csv, 211 KB). Nie ma binariów, PDF ani rastrów. `.gitignore` = `files/` ✓.
- `python3 -I fetch.py`: 8 PDF pobranych w 56 s, **wszystkie sha256 OK** (exit 0). Trzy akty, których fetch.py nie zna (2021/433, 2021/2065, 2026/133), pobrałem ręcznie z api.sejm.gov.pl. Tekst wyciągnąłem `tools/pdf_to_pages.py` (pdftotext -layout).
- Strony oglądałem jako raster (pdftoppm 80–250 dpi, ≤ 960 px, wycinki), narzędziem Read:
  - 2311 s. 9, 11, 12, 30, 97, 158–159, 178, 395, 398–399, 404, 420, 481, 487;
  - 2310 s. 41–45, 48, 49 (wzory barwne, wycinek D-44/D-45 przy 250 dpi).
- Nowelizacje: przeczytałem tekst 2022/2377 s. 1–4, 2021/2066 (pkt 1.2.2, 1.11, 5.1.1), 2026/132 (spis zmian), 2021/433, 2021/2065, 2022/2372 i 2026/133. Kompletność listy nowelizacji sprawdziłem w API ELI (`/eli/acts/DU/2003/2181` i `/2002/1393`, pole `references`, 2026-11-14 ok. 17:45 UTC). Po t.j. 2019 są tylko 2021/438, 2021/2066, 2022/2377 i 2026/132 dla 2311 oraz 2021/433, 2021/2065, 2022/2372 i 2026/133 dla 2310. **Lista w pakiecie jest kompletna** ✓.
- Barwy policzyłem własnym skryptem (`R1-colour-check.py` obok tej recenzji), niezależnie od `tools/check_generator_colors.py`.

## 2. Kryteria

| Kryterium | Wynik |
|---|---|
| Format: README, manifest (kolumny), sources, fetch.py, audit, STATUS, .gitignore | **CZĘŚCIOWO.** Komplet plików i kolumn jest. fetch.py nie obejmuje 3 aktów użytych w `catalog.csv` (P1-3). |
| fetch.py: sha256 | **TAK** dla 8/8 plików, które pobiera. |
| Seed samokontroli odtwarzalny | **TAK.** `random.Random(20261114).sample(sorted(ids), ceil(0.2n))` daje te same 60 id manifestu (n = 296, bez R1-297) i te same 53 kat_id. Wynik 60/60 + 51/53 zgadza się z JSON. Samokontrola obejmuje ponowne rendery stron (38/60 wpisów manifestu wprost wymienia render). |
| Własna próbka (seed 777) | manifest **30/30 PASS**, catalog **15/15 PASS**, sizes **12/12 PASS** (§3). Poza próbą 1 FAIL: D-19/D-20 (P1-1). |
| Źródła dozwolone i licencje | **TAK.** Tylko ELI/ISAP: akty normatywne, art. 4 pkt 2 pr. aut. Bez Google, Mapillary i Commons (429, nic nie pobrano). Brak marek w opisach do gry. |
| Nowelizacje 2022/2377 i późniejsze uwzględnione | **CZĘŚCIOWO.** Tab. 1.11, pkt 1.3.2, 1.5.2 i D-42/D-43 (600 mm) są ✓. **Pominięta jest zmiana pkt 5.2.19 (D-19 620×300)** z tej samej nowelizacji. Akty zmieniające są przypisane poprawnie (§4). |
| ESTIMATED nie przebrane za SOURCED | **CZĘŚCIOWO.** 262/265 barw w katalogu ma ESTIMATED ✓, a 8 wierszy sRGB pochodnych ESTIMATED z metodą ✓. Nadmiarowe SOURCED mają B-24 i D-18 (P1-5). |
| Erraty sprawdzone w repo | **TAK**, z jedną drobną nieścisłością (P2-7). |
| Użyteczność dla gry | **TAK.** Tabele są gotowe dla generatora (sizes.csv, §3.1–3.6). Luki są jawne. |
| Spójność czasu i opisu pracy | **NIE.** STATUS.md i sources.md zawierają godziny późniejsze niż ostatni commit (P1-4). |

## 3. Próbka recenzenta (seed 777)

Losowanie: `random.Random(777).sample(sorted(kat_id), 15)` dla catalog, `random.Random(777).sample(range(130), 12)` dla sizes i `random.Random(777).sample(sorted(id), 30)` dla manifestu (10 %).

### 3a. catalog.csv (15 wierszy; nazwy sprawdzone w tekście listy 2310 s. 29–40 i nowelizacji, barwy i kształt na rastrze wzoru)

| kat_id | kod | Nazwa | Kształt | Barwy (wzór 2310) | Wynik |
|---|---|---|---|---|---|
| K001 | A-1 | ✓ s. 29 | trójkąt ✓ | żółte / czerwone / czarny ✓ s. 41 | PASS |
| K021 | A-14 | ✓ | ✓ | ✓ s. 41 | PASS |
| K040 | A-32 | ✓ | ✓ | ✓ s. 41 | PASS |
| K054 | B-11 | ✓ | koło ✓ | białe / czerwone / czarny ✓ s. 42 | PASS |
| K059 | B-15 | ✓ | ✓ | ✓ s. 42 | PASS |
| K062 | B-18 | ✓ | ✓ | ✓ s. 42 | PASS |
| K118 | D-6b | ✓ | kwadrat ✓ | niebieskie, biały trójkąt, czarne symbole ✓ s. 44 | PASS |
| K139 | D-23 | ✓ | prostokąt pionowy ✓ | białe pole, czarny dystrybutor + zielony element ✓ | PASS |
| K148 | D-26c | ✓ | ✓ | WC czarne na białym polu ✓ | PASS |
| K171 | D-43 | ✓ | 1200×700 / 600 ✓ (2377 s. 4) | białe, czarna sylweta, czerwony pas ✓ | PASS |
| K173 | D-45 | ✓ (2021/2065 § 1 pkt 10) | prostokąt pionowy ✓ (wycinek 250 dpi) | białe, cienka czarna obwódka, szary symbol, czerwony pas ✓ | PASS |
| K174 | D-46 | ✓ | poziomy ✓ s. 45 | ✓ | PASS |
| K189 | F-3 | ✓ | pionowy ✓ s. 48 | niebieskie / białe ✓ | PASS |
| K200 | F-14a | ✓ (nazwy nie zmieniono w 2021/2065) | pionowy ✓ | białe cyfry i pasy ✓ | PASS |
| K229 | T-8 | ✓ | pionowy ✓ s. 49 | żółte / czarny ✓ | PASS |

### 3b. sizes.csv (12 wierszy)

| Wiersz | Wartość | Źródło (raster/tekst) | Wynik |
|---|---|---|---|
| 10 | A, S, bok 900 | tab. 1.1 s. 9 / tab. 2.1 s. 49 | PASS |
| 19 | A, M, a = 75 | tab. 2.1 s. 49 | PASS |
| 29 | B, W, a = 100 | tab. 3.1 s. 97 (raster) | PASS |
| 30 | B, D, d = 900 | tab. 3.1 | PASS |
| 58 | C, S, a = 80 | tab. 4.1 s. 157 | PASS |
| 69 | D, W, c = 300n+160 | tab. 5.1 s. 178 (raster) | PASS |
| 73 | D, D, l = 900 | tab. 5.1 | PASS |
| 85 | D, S/M, c = 150n+80 | tab. 5.1 | PASS |
| 86 | D, S/M, g = 6 | tab. 5.1 | PASS |
| 94 | D, MI, g = 4 | tab. 5.1 | PASS |
| 99 | T, W/D, h = 350 | tab. 9.7.1 s. 487 (raster 200 dpi) | PASS |
| 114 | T, S/M, l = 49 | tab. 9.7.1 | PASS |

### 3c. manifest.csv (30 wierszy = 10 %)

Kontrola automatyczna (fragment cytatu i liczba na wskazanej stronie) oraz raster tam, gdzie tabela jest obrazem:
- R1-001, 018, 021, 040, 054, 055, 059, 076, 108, 118, 137, 139, 148, 160, 171, 173, 200, 213, 229, 257, 270, 276, 281, 295 i 296: liczba i cytat są na stronie ✓;
- R1-062 (68°): raster s. 97 ✓;
- R1-065 (a/3): s. 385 ✓;
- R1-174 (czarna, tab. 1.4): raster s. 11 ✓, cytat ma przecinki zamiast kropek, ale treść się zgadza;
- R1-189 (żółta, typ 2: 170): raster s. 12 ✓;
- R1-179 (#B58700, ESTIMATED): przeliczone, x = 0,4726, y = 0,4629, Y = 0,272, w polu ✓.

**30/30 PASS.**

Poza próbą sprawdziłem jeszcze:
- rysunki B-39 (s. 395), C-17 (s. 404), F-12 i F-13 (s. 481), kąt tarczy rys. 1.5.5 (s. 30): ✓;
- **D-19/D-20 (s. 420): FAIL** (P1-1).

## 4. Wymiary i nowelizacje (2022/2377 i później)

- **Tab. 1.11:** brzmienie z 2022/2377 § 1 pkt 1 lit. a (PDF s. 2) zgadza się z README §3.6 i R1-238…253, w tym przypis 6) „na chodniku albo nad chodnikiem” → 2,20 ✓. Pierwsza zmiana tabeli (2021/2066) została zastąpiona; README podaje to poprawnie.
- **D-42/D-43:** w t.j. 2311 (s. 244) wysokość dopuszczalna na drogach powiatowych i gminnych wynosi 530 mm. 2022/2377 s. 4 zmienia ją na **600 mm**. R1-109/110 i sizes 128 ✓.
- **D-19/D-20: błąd.** Tekst t.j. 2311 pkt 5.2.19 (PDF s. 227) oraz nowe brzmienie z **2022/2377 § 1 pkt 1 lit. b (PDF s. 2)** mówią: „długość podstawy **620 mm**, wysokość 300 mm”. Rysunek 9.4.27 (s. 420, obejrzany przy 200 dpi) podaje 600 jako wymiar wewnętrzny (20 + 16×35 + 20 = 600) i obwódkę 10 z każdej strony, co razem daje 620.
- **2026/132** nie zmienia tabel 1.1–1.11 ani wymiarów A–D. Zmienia pkt 1.4.1 (cytowany w R1-229 ✓), opisy, część E i rysunki F-23/F-24. **2021/438** zmienia tylko B-19 i E-15 (zgodnie z sources.md).
- **Akty zmieniające wskazano poprawnie:**
  - 2021/433 → nazwa B-19 (§ 1 pkt 1 i 3, tekst ✓);
  - 2021/2065 → D-23b/c, D-34b, F-14d–f;
  - 2022/2372 → D-19/D-20 (§ 53 znaczenie), UNESCO, wzór D-39;
  - 2026/133 → D-23b/c „…lub hybrydowych” (catalog ✓), E-1c, E-2d, E-20a, F-23, F-24.

  Skrót w README §1 przy 2022/2372 („wzór D-39”) jest niepełny, ale sources.md podaje zakres w całości.
- **B-39:** R1-066 podaje 900×1300 z rysunku 9.2.47 (✓ na rastrze). Tekst (opis szczegółowy B-39, PDF s. 153) mówi jednak: „Znaki B-39 mają wymiary jak duże znaki informacyjne”, czyli 900 × (900+225n) = 1125/1350. Rysunek jest przykładem. Patrz P2-4.

## 5. Barwy CIE

- **Narożniki i β:** wszystkie 8 barw z tab. 1.3 i 2 z tab. 1.4 w README §3.3 i manifeście (R1-140…176) są **zgodne z rastrem s. 11** ✓. Warunki pomiaru (45°/0°, 2°, D65) też ✓.
- **Metoda konwersji (recenzent):**
  1. 8-bit sRGB → linearyzacja IEC 61966-2-1: c/12,92 dla c ≤ 0,04045, inaczej ((c+0,055)/1,055)^2,4.
  2. Macierz sRGB (D65) → XYZ: [0,4124564 0,3575761 0,1804375; 0,2126729 0,7151522 0,0721750; 0,0193339 0,1191920 0,9503041].
  3. x = X/(X+Y+Z), y = Y/(X+Y+Z).

  Adaptacja chromatyczna nie jest potrzebna, bo tabela dotyczy iluminantu D65, a sRGB ma biel D65. „W polu” = punkt wewnątrz otoczki wypukłej 4 narożników. Margines liczę jako odległość w xy od najbliższej krawędzi (dodatni = wewnątrz). Skrypt wykonawcy używa 4-cyfrowej macierzy i daje te same wyniki do 3. miejsca.
- **Generator (`signs.py`, GREEN = (0,112,72)):** x = 0,2569, y = 0,4447, Y = 0,121 → **poza polem**. Margines wynosi −0,030; punkt leży na zewnątrz krawędzi 1–2, czyli od (0,007;0,703) do (0,248;0,409). Wniosek wykonawcy jest **poprawny**. Uzasadnienie „x = 0,257 > 0,248” jest uproszczone: przy y = 0,445 krawędź pola ma x ≈ 0,218, więc przekroczenie wynosi około 0,04 (P2-1). Pozostałe 5 barw generatora mieści się w polach, a Y ≥ β_min ✓ (zgodne z pakietem).
- **Alternatywy wykonawcy:** (0,84,62) → x = 0,2469, y = 0,4088, margines **+0,0004**; (0,137,103) → x = 0,2469, y = 0,4090, margines **+0,0006**. Obie **leżą w polu**, ale praktycznie na narożniku 2 (0,248;0,409).
  - Przeszukałem całą gamę sRGB 8-bit. Największy możliwy margines wynosi **+0,0007**, np. (0,190,144); wszystkie barwy w polu mają R ≤ 19.
  - Przecięcie gamy sRGB z polem zielonym to więc wąski klin przy narożniku 2. Twierdzenie pakietu o „wąskim pasie” jest prawdziwe. Przybliżenie „G:B ≈ 4:3” jest za wąskie: przy R = 0 stosunek G:B wynosi 1,31–1,83 (P2-2).
- **sRGB pochodne (README §3.3, R1-178…185):** 7 z 8 wartości leży w polu z marginesem 0,011–0,021 ✓. **Zielona #004930 (R1-181) → x = 0,2536, y = 0,4330, margines −0,020: poza polem.** Centroid zielonego pola (0,1145;0,4682) leży poza gamą sRGB i konwersja go przycięła. README podaje tę wartość bez zastrzeżenia, choć obok zaleca poprawienie GREEN, bo jest poza polem (P1-2).
- **Narożniki brązowej** podane w kolejności 1-2-3-4 tworzą wielokąt samoprzecinający się (kokardę). Test „punkt w wielokącie” w tej kolejności daje fałszywe „NIE” dla #4C260C, który leży w otoczce z marginesem +0,018. `check_generator_colors.py` nie testuje brązowej ani pomarańczowej, więc wyniki pakietu na tym nie cierpią. README przepisuje jednak kolejność z aktu bez uwagi (P2-3).

## 6. C-1 / C-2

Sprawdziłem na rastrze:
- 2311 s. 158: rys. 4.2.1.1 C-1 to strzałka pozioma w prawo.
- 2311 s. 159: rys. 4.2.2.1 C-2 to strzałka w górę zakręcająca w prawo.
- 2311 s. 398: rys. 9.3.1 C-5 z notą „może być wykorzystany do kopiowania znaków C-1, C-3, C-5, C-9 i C-10 po dokonaniu obrotu osi strzałki o 135° i 90° w prawo lub w lewo”.
- 2311 s. 399: rys. 9.3.2 „Konstrukcja znaku C-2 (dla C-4 odbicie lustrzane)”.
- 2310 s. 43: wzory C-1…C-4.
- Dodatkowe potwierdzenie: rys. 9.3.13 (C-17, s. 404) zawiera C-2 w tej samej postaci.

**Rozstrzygnięcie R1-293/294 jest poprawne:** strzałka „w górę i w prawo” to C-2.

## 7. Errata do wcześniejszych pakietów (sprawdzone w repo)

| # | Twierdzenie R1 | Stan w repo | Ocena |
|---|---|---|---|
| 1 | m47-fix2 §3: wiersz 005 „C-2 (strzałka pozioma w prawo)” jest sprzeczny; 129 „strzałka zakrzywiona = C-1” błędne; 063 do sprawdzenia | `docs/reports/REVIEW-2026-11-13-s20-mistral-m47-fix2.md` l. 31, 53, 42: dokładnie takie wpisy ✓. m62 l. 70 „Możliwa errata” ✓ | **TAK.** Nieścisłość: manifest `research/mistral/p11-dojlidy-photos/manifest.csv` P11-129 ma „C-1/C-2”, a nie „C-1”. Poprawka powinna brzmieć „C-1/C-2 → C-2”. P11-005 ma już „C-2”, a P11-063 „C-1/C-2” (P2-7). |
| 2 | wzorzec (a): „A-16 to czerwony trójkąt” jest nieprecyzyjne | l. 60 ✓; wzór 2310 s. 41: żółte tło, czerwone obrzeże ✓ | **TAK** |
| 3 | g5: README l. 61 i S9 „załączniki jako skany / nieprzeszukiwalne”; G5-031 → SOURCED | `research/g5-street-furniture/README.md` l. 61, `sources.md` l. 27, `manifest.csv` G5-031 UNVERIFIED ✓. Zał. 1 ma warstwę tekstową (pdftotext tab. 1.1 ✓) | **TAK** |
| 4 | gptpro/p2-surfaces sources poz. 1: zły tytuł („Rozp. Ministra Transportu z 11.09.2019”) | `research/gptpro/p2-surfaces/sources.md` l. 5 ✓; ELI: obwieszczenie MI z 9.09.2019, t.j. rozp. MI z 3.07.2003 ✓ | **TAK** |
| 5 | gptpro/p8 P8-037: brzmienie B-19 pochodzi z 2021/433, nie z t.j. 2019 (lexlege) | P8-037 cytuje 2310 t.j. i URL lexlege ✓; 2310 s. 30: „nacisku osi większym niż … t” ✓; 2021/433 § 1 pkt 1 lit. a (80 %) i pkt 3 lit. a ✓ | **TAK** |
| 6 | kod gry: `signs_route.py` „Załącznik 1 (A-D) and 4 (E)”; `signs.py` bez 2022/2377 i 2026/132; GREEN poza polem; `standards.py` 2,20 także nad chodnikiem | `signs_route.py` l. 4 ✓, `signs.py` l. 3 i 30 ✓, `standards.py` l. 200 i 216–219 ✓; E jest w zał. 1 cz. 6 (s. 256+) ✓ | **TAK** |

## 8. Odczyty barw z obrazu: status

- `catalog.csv`: 262/265 wierszy ma `status_barw` = ESTIMATED z metodą („odczyt wizualny barwnego wzoru 2310 s. …”) ✓.
- Trzy wiersze SOURCED:
  - **T-34** (s. 291): cytat obejmuje tło, ramkę i symbol ✓.
  - **B-24** (s. 155): cytat potwierdza tylko „symbol barwy szarej”. Tło białe, czarna obwódka i czarny pas to odczyt z obrazu (P1-5).
  - **D-18** (s. 222): cytat potwierdza tylko „symbol pojazdu barwy białej” dla wariantu z symbolem. Niebieskie tło, biała obwódka i główny symbol to odczyt z obrazu (P1-5).
- `manifest.csv`: barwy z obrazu nie trafiły jako SOURCED. Kategoria `barwa_sRGB_pochodna` = ESTIMATED z metodą ✓.
- Kształty D/F/T ESTIMATED z metodą ✓.

## 9. Lista poprawek

### P0 (blokuje PR)
Brak.

### P1 (przed scaleniem)
1. **D-19/D-20 = 620 × 300 mm** (nie 600×300). Poprawić R1-111 (cytat: 2311 pkt 5.2.19 PDF s. 227 oraz Dz.U. 2022 poz. 2377 § 1 pkt 1 lit. b, PDF s. 2: „długość podstawy 620 mm, wysokość 300 mm”), R1-K134, R1-K135 (`kształt`), sizes.csv wiersz „D-19/D-20” i README §3.1. Dopisać uwagę, że rys. 9.4.27 wymiaruje 600 wewnątrz obwódki 10. Przy okazji przejrzeć inne wymiary „z rysunku” (R1-066…068, 081, 113–115) pod kątem wymiar wewnętrzny/zewnętrzny. W mojej kontroli B-39, C-17, F-12 i F-13 są zewnętrzne ✓.
2. **R1-181 / README §3.3: zielona #004930 leży poza polem tolerancji** (x = 0,2536, y = 0,4330, margines −0,020; centroid pola jest poza gamą sRGB i został przycięty). Oznaczyć w README i manifeście „poza polem; centroid poza gamą sRGB”. W kolumnie „sRGB pochodne” dla zielonej podać barwę w polu z jawnym marginesem (np. (0,84,62), +0,0004) albo „–”.
3. **fetch.py** musi pobierać wszystkie akty z `sources.md` i `catalog.csv` (`źródło_nazwy`): dodać do `EXTRA` D20210433, D20212065 i D20260133 z sha256. README „11 PDF” jest dziś nieprawdziwe dla fetch.py (8 PDF). Opcjonalnie dodać wiersze manifestu z tymi aktami (np. nazwa B-19 R1-xxx z 2021/433), bo dziś manifest ich nie cytuje, a README §5 pkt 5 się na nie powołuje.
4. **Znaczniki czasu:** STATUS.md podaje „17:55 / 18:25 / 18:50 / 19:10 UTC”, a sources.md „Commons 429 ok. 18:55 UTC”. Wszystkie commity powstały między 17:12 a 17:29 UTC, a recenzja zaczęła się o 17:30 UTC. Wpisać rzeczywiste godziny (z `git log`) albo usunąć godziny. Wpis o 429 z Commons opisać zgodnie z faktami: kiedy próba się odbyła i jaki był wynik.
5. **B-24 (R1-K068) i D-18 (R1-K131):** `status_barw` = SOURCED obejmuje elementy niecytowane. Zmienić na ESTIMATED z dopiskiem w `źródło_barw` „symbol szary: SOURCED 2311 s. 155; reszta: odczyt wzoru 2310 s. 42” (analogicznie D-18). Ewentualnie rozbić status na pola.

### P2 (sugestie)
1. README §3.3: uzasadnienie „x = 0,257 > 0,248” zastąpić odległością od krawędzi 1–2 (przy y = 0,445 krawędź ma x ≈ 0,218).
2. Alternatywy zielonej mają margines ≤ 0,0006. Cała część wspólna pola z gamą sRGB ma ≤ 0,0007 i leży przy narożniku 2. Zapisać to wprost i zamiast „G:B ≈ 4:3” podać zakres (R ≤ 19, G:B 1,31–1,83). Uwaga dla renderingu: po tonemappingu i w linearnym potoku URP barwa i tak wyjdzie z pola. Decyzja (dokładne pole czy wizualna zgodność) należy do lidera; najlepiej zapisać ją w ADR.
3. README §3.3: przy brązowej (i ogólnie) dodać uwagę, że narożniki z aktu nie są uporządkowane po obwodzie (brązowa 1-2-3-4 tworzy kokardę) i do testów trzeba brać otoczkę wypukłą. Rozszerzyć `check_generator_colors.py` o pomarańczową i brązową.
4. B-39: obok 900×1300 (rys. 9.2.47, przykład) podać regułę tekstową „jak duże znaki informacyjne” = 900 × (900+225n) (opis szczegółowy B-39, PDF s. 153), żeby generator nie przyjął 1300 jako stałej.
5. README §3.3 „folia typu 2 około 3,5× jaśniejsza” dotyczy tylko białej i żółtej (3,6 i 3,4). Dla czerwonej wynosi 3,1, dla zielonej i niebieskiej 5, dla brązowej 12. Podać stosunek dla każdej barwy. Wspomnieć tab. 1.7 (R' w okresie trwałości, pkt 1.3.2 w brzmieniu 2022/2377), dziś pominiętą.
6. README §3.1: w kolumnie D brakuje modułu a (120/90/60/40). Jest w sizes.csv, ale tabela README powinna być z nim spójna.
7. Errata 1: doprecyzować, że w manifeście P11 wiersze 063 i 129 mają „C-1/C-2” (a nie „C-1”), a 005 ma już „C-2”.
8. README §3.6, tab. 1.11: dopisać wiersze E w obszarze zabudowanym (2,00/2,20; min. 1,00 w pasie zieleni lub na poboczu) i duże strzały E (0,70), dla kompletności generatora E.

## 10. Rekomendacja
FIX w tej samej gałęzi: P1-1…P1-5, ponownie `python3 -I fetch.py` (11/11 OK) i dopisanie korekt do `audit_20_percent.json` jako „korekty po recenzji”. Po poprawkach pakiet nadaje się do scalenia. Liczby A/B/C/D/T, barwy CIE, β, R', tab. 1.11 i grupy wielkości można już teraz traktować jako SOURCED dla generatora. Wyjątki: D-19/D-20 oraz zielona sRGB.
