# Przegląd PR #67 — R1 traffic-signs-catalog (cloud2) — s20, 2026-11-14

**Werdykt: SCAL z erratą.** Cztery z pięciu P1 recenzji wewnętrznej (`REVIEW.md`) są poprawione w pełni. P1-2 (zielona sRGB) poprawiono tylko częściowo, bo komórka tabeli w README nadal pokazuje `#004930` bez zastrzeżenia. Ta poprawka jest kosmetyczna, a zastrzeżenie stoi akapit niżej i w manifeście. Liczby, które sprawdziłem sam na rastrze PDF, zgadzają się co do cyfry: narożniki pól barw, β, tab. 1.1, tab. 1.11 i D-19 620×300. Na gałęzi nie ma blokera.

- Gałąź `origin/research/cloud2-traffic-signs-catalog` @ `611fb726e` (PR #67, OPEN, nie draft). Ma 6 commitów od main, w tym fix `611fb72` z 17:41 UTC.
- `git diff --stat main...`: 17 plików, wyłącznie w `research/cloud2/traffic-signs-catalog/`. Wszystkie są tekstowe, `.gitignore` = `files/` ✓.
- Nic nie scalono, nic nie scommitowano, PR bez komentarza. Raportu nie scommitowano.

## 1. P1 z REVIEW.md — czy naprawdę poprawione

| P1 | Wymóg | Stan na `611fb72` | Dowód |
|---|---|---|---|
| 1 | D-19/D-20 = 620×300 | **TAK** | Poprawione w R1-111 (cytat 2022/2377 § 1 pkt 1 lit. b), w R1-K134/K135 (`prostokąt poziomy (620×300)`), w `sizes.csv` l.127 („620×300; R30 (600 wewnątrz obwódki)”) i w README l.49 oraz l.113. Zrobiłem własny raster: 2022/2377 s.2 (tekst „długość podstawy 620 mm, wysokość 300 mm”) i 2311 s.420 (rys. 9.4.27: 600 = 20+16×35+20, obwódka 10) ✓ |
| 2 | zielona #004930 poza polem: oznaczyć, w kolumnie dać barwę z pola albo „–” | **CZĘŚCIOWO** | Manifest R1-181: przedmiot „(UWAGA: wynik poza polem tolerancji…)” ✓. README l.84: „Zielona #004930 (R1-181) leży poza polem tolerancji” ✓. **Ale** tabela README l.76 nadal ma w kolumnie sRGB `#004930` bez znacznika, a l.90 nadal uzasadnia błąd uproszczeniem „x = 0,257 > 0,248” (P2-1). Errata E1 |
| 3 | fetch.py: 11/11 aktów | **TAK** | `EXTRA` zawiera D20210433, D20212065, D20260133 (+2020/862, 2021/438, 2022/2372). Uruchomiłem `python -I fetch.py` z pustego `files/`: **11/11 OK, sha256 zgodne, exit 0** |
| 4 | znaczniki czasu z przyszłości | **TAK** | STATUS: 17:12 / 17:18 / 17:23 / 17:26 / 17:29 UTC to dokładnie czasy commitów a4e5bec…b03abb9 (`git log --format=%cI`). Krok 6 „17:4x” pasuje do 611fb72 (17:41). sources.md l.19/23 też mieści się w czasie commitów |
| 5 | B-24 / D-18: SOURCED tylko dla cytowanego elementu | **TAK** | R1-K068 i R1-K131: `status_barw` = „SOURCED (tylko element z cytatu), reszta ESTIMATED” ✓. Obejrzałem 2311 s.155: tekst „symbol barwy szarej odwoływanego zakazu, np. B-24” ✓. Na 2311 s.222 jest „symbol pojazdu barwy białej” ✓ |

Drobne pozostałości: w `audit_20_percent.json` nie dopisano bloku „korekty po recenzji”, o który prosiła recenzja (§ końcowy). P2 w większości pozostały bez zmian; nie sprawdzałem każdego punktu z osobna. README l.90 ma już margines „≤ 0,0007” (część P2-2), ale wciąż przybliżenie „x = 0,257 > 0,248” (P2-1).

## 2. Zielona (0,112,72) a pole tolerancji Dz.U. — mój rachunek

Tab. 1.3 (2311 s.11, raster obejrzany przy 100 dpi) podaje narożniki pola dla barwy zielonej, folia typu 1/2: (0,007;0,703), (0,248;0,409), (0,177;0,362), (0,026;0,399). Minimalne β wynosi 0,04 dla typu 1 i 0,03 dla typu 2. Warunki pomiaru to 45°/0°, D65 i obserwator 2°, więc konwersja z sRGB (biel D65) jest właściwa.

Konwersja sRGB → XYZ (IEC 61966-2-1) i odległość ze znakiem od najbliższej krawędzi pola (ujemna = poza polem):

| sRGB | x | y | Y | margines | wniosek |
|---|---|---|---|---|---|
| **(0,112,72)** `signs.py` GREEN | 0,2569 | 0,4447 | 0,121 | **−0,0295** | **poza polem** (potwierdzam wykonawcę i recenzję) |
| (0,73,48) = #004930 (R1-181) | 0,2536 | 0,4330 | 0,050 | −0,0195 | poza polem (potwierdzam P1-2) |
| (0,84,62) | 0,2469 | 0,4087 | 0,067 | +0,0004 | na granicy pola (narożnik 2) |
| (0,120,90) | 0,2468 | 0,4085 | 0,142 | +0,0002 | na granicy pola (narożnik 2) |
| (0,137,103) | 0,2469 | 0,4090 | 0,189 | +0,0006 | na granicy pola (narożnik 2) |

Marginesy +0,0002…+0,0006 mieszczą się w błędzie zaokrągleń (macierz sRGB z 4 miejscami, 8-bitowe kanały), więc te barwy są „na granicy”, a nie „w polu”.
| (0,100,60) | 0,2605 | 0,4577 | 0,094 | −0,0405 | poza polem |

Wniosek: część wspólna gamy sRGB i pola zielonego to klin przy narożniku 2 (0,248;0,409), o marginesie ≤ 0,0006. **Nie istnieje sRGB w polu**, są tylko punkty na granicy przy narożniku 2. Wybór wartości to więc decyzja projektowa (ADR), a nie poprawka liczbowa.

## 3. Moja kontrola (≥ 10 obrazów, ≥ 5 liczb u źródła)

Raster z PDF-ów pobranych przez `fetch.py` (PyMuPDF), oglądany przy ≤ 960 px, wycinek 3× przy 300 dpi:

| # | Obraz | Co sprawdziłem | Wynik |
|---|---|---|---|
| 1 | 2311 s.11 | tab. 1.3: wszystkie narożniki białej i zielonej, β 0,35/0,27 i 0,04/0,03; tab. 1.4 | ✓ zgodne z README l.76 i manifestem |
| 2 | 2022/2377 s.2 | tab. 1.11 w nowym brzmieniu: A–D, F, G poza obszarem zabudowanym min. 2,00 (1,50⁵), w obszarze 2,00 (2,20⁶); E-1/E-2/E-14 poza obszarem min. 1,00; nad jezdnią 5,00; urządzenia BRD 0,90–1,20; przypisy 1 (F-11 5,00; F-14 0,50) i 3 (G-1) | ✓ R1-238…253. Uwaga: `pdftotext -layout` przesuwa „min. 1,00” do wiersza F, ale raster jednoznacznie przypisuje tę wartość do E-1. Wykonawca ma poprawnie |
| 3 | 2022/2377 s.2 | pkt 5.2.19: D-19 620×300 | ✓ |
| 4 | 2311 s.420 | rys. 9.4.27 i 9.4.29 (600 wewnątrz, obwódka 10, R30, TAXI 210) | ✓ |
| 5 | 2311 s.155 | B-42, B-24 „symbol barwy szarej” | ✓ |
| 6 | 2311 s.222 | D-17, D-18, „symbol pojazdu barwy białej” | ✓ |
| 7 | 2310 s.41 | wzory A-1…A-34: żółte tło, czerwona obwódka, czarne symbole; A-7 odwrócony trójkąt | ✓ z `catalog.csv` (kategoria A) |
| 8 | 2310 s.42 | wzory B-1…B-44: B-24 białe tło, szary symbol, czarny pas; B-39/B-43/B-44 tablice | ✓ R1-K068 |
| 9 | 2310 s.43 | C-1 = pozioma strzałka w prawo, C-2 = strzałka w górę i w prawo; C-17 tablica | ✓ rozstrzygnięcie C-1/C-2 poprawne |
| 10 | 2310 s.44 | wzory D: D-19/D-20 poziome, D-23 z zielonym elementem dystrybutora, D-44 biała tablica z D-18 | ✓ R1-K134/K135, K139, K172 |
| 11 | 2310 s.44, wycinek 3× przy 300 dpi (D-19…D-22) | proporcja D-19 ≈ 2:1, biała obwódka, biały napis | ✓ |

Liczba znaków w `catalog.csv` per kategoria: A 42, B 46, C 21, D 76, F 30, T 50 (razem 265). B i C zgadzają się z tablicami wzorów s.42–43, łącznie z wariantami B-3a, B-13a, C-13a, C-16a. **RAL:** README l.86 uczciwie pisze, że „akt nie podaje odpowiedników RAL”, a PN-EN 12899-1 ma status UNVERIFIED. Luka jest jawna, więc wymóg „CIE/RAL” jest spełniony od strony CIE.

Licencje i zakazy: źródła to wyłącznie api.sejm.gov.pl (ELI). Akty prawne nie podlegają prawu autorskiemu (art. 4 pr. aut.). Wyszukiwanie google|bing|yandex|apple|mapillary w manifest/sources/fetch daje 0 trafień. User-Agent `research-fetch/1.0` jest ogólny ✓.

## 4. Errata (do wklejenia autorowi; nie blokuje scalenia)

```
R1 errata (po scaleniu albo w tej gałęzi):
E1. README l.76 (tabela barw), kolumna „sRGB pochodne” dla zielonej: zamiast „#004930” wpisać
    „– (centroid poza gamą sRGB; #004930 leży poza polem, margines −0,020; barwy w polu tylko przy narożniku 2,
    margines ≤ 0,0006, np. (0,120,90) / (0,137,103))”.
E2. README l.90: zamiast „x = 0,257 > 0,248” napisać „(0,112,72) → x 0,2569, y 0,4447, margines −0,030
    od krawędzi 1–2 [(0,007;0,703)–(0,248;0,409)]”.
E3. audit_20_percent.json: dopisać blok "korekty_po_recenzji" (D-19/D-20, R1-181, B-24, D-18) z id i commitem 611fb72.
E4. P2-2, P2-5, P2-7 z REVIEW.md (G:B 1,31–1,83; R' typ2/typ1 per barwa; errata P11-063/129 „C-1/C-2”).
```

## 5. Wnioski dla gry

1. **`tools/worldgen/streetscape/signs.py:30` `GREEN = (0, 112, 72)` leży poza polem tab. 1.3** (margines −0,030). Używają go tarcze E-dróg (l.161), tablice kierunkowe (l.176, l.222) i l.235. Decyzja należy do lidera i wymaga ADR (następny wolny numer). Opcje:
   - (a) punkt na granicy pola przy narożniku 2, np. (0,120,90), z adnotacją „najbliżej pola w gamie sRGB”;
   - (b) zostawić obecną barwę jako „wizualną” z adnotacją WORKING_VALUE.

   Przed decyzją potrzebne są visual-qa i zdjęcie referencyjne zielonej tablicy z Białegostoku, bo po tonemappingu URP barwa i tak wyjdzie z pola.
2. **D-19/D-20 = 620×300 mm.** Jeśli generator kiedyś doda postój taxi, trzeba użyć 620, nie 600.
3. **Wysokość montażu** (tab. 1.11 w brzmieniu 2022/2377): 2,20 m obowiązuje także „nad chodnikiem”. F poza obszarem zabudowanym ma min. 2,00 (merged cell), a 1,00 dotyczy tylko E-1/E-2/E-14. Zestawienie README l.156 o `tools/worldgen/roads/standards.py` (2,00 / 2,20 / 5,00) jest zgodne. Grep `standards.py` po `1.11|mount|height|2.20` nie znalazł jednak stałej wysokości montażu znaków (są tylko krawężniki, l.75–86), więc to zestawienie jest niezweryfikowane. Wykonawca generatora musi wskazać miejsce stałej przy następnej zmianie znaków.
4. **Wymiary A/B/C/D w grupach W/D/S/M/MI** (README §3.1, tab. 1.1) są SOURCED i nadają się do generatora. Wartości G5-031 i `SIGN_SIZE` są potwierdzone.
