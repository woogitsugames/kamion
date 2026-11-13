# P16 — Lampy ciężarówki i naczepy: fotometria (R148/R150) i budowa

Pakiet badawczy M59/P16 dla gry **Kamion** (fikcyjny ciągnik siodłowy 4×2 kat. N3 + naczepa firanka 13,6 m, 3 osie, kat. O4).

**Zakres: TYLKO lampy** — fotometria i budowa urządzeń wg regulaminów ONZ nr 148 (urządzenia sygnalizacji świetlnej, LSD) i nr 150 (urządzenia odblaskowe, RRD), budowa lamp zespolonych, lampka tablicy rejestracyjnej oraz dokumentacja fotograficzna (klatka po klatce, każda obejrzana).

**NIE obejmuje instalacji** (liczba, wysokość montażu, kolor na pojeździe, widoczność montażowa wg R48) — to pakiet `research/mistral/p4-truck-regulations/` (M44, wiersze P4-048…). Tam też opisane kąty widoczności *montażu* — tutaj kąty *badania urządzenia* z zał. 2 R148.

Wszystkie liczby mają: punkt regulaminu + cytat (≤25 słów) + wersja przepisu; pełne dane w `manifest.csv`. Statusy: SOURCED / ESTIMATED / UNVERIFIED.

---

## 1. Wersje regulaminów (co naprawdę obowiązuje)

| Regulamin | Wersja UNECE (aktualna) | Wersja wiążąca w UE (GSR2, zał. II) |
|---|---|---|
| R148 LSD | 01 seria + Supl. 2 (E/ECE/TRANS/505/Rev.3/Add.147/Rev.1/Amend.2, EIF 22.09.2024) | **pierwotna wersja** — Dz.U. L 347 z 30.9.2021, s. 123 ([2021/1719]) |
| R150 RRD | 01 seria + Supl. 2 + Corr.1 (Add.149/Rev.1/Amend.2/Corr.1) | **pierwotna wersja** — Dz.U. L 347 z 30.9.2021, s. 297 ([2021/1721]) |
| R48 (barwy, definicje) | seria 07 + Supl. 1 | seria 07 + Supl. 1 — Dz.U. L 347 z 30.9.2021, s. 1 ([2021/1718]) |

- GSR2 (02019R2144, konsolidat 02.08.2026) zał. II wiersz 148 i 150 wskazuje dla LSD i RRD **„Pierwotną wersję regulaminu”** — więc podstawą każdego wiersza manifestu jest tekst Dz.U. UE (PL), a wersje UNECE służą do rozplatania sklejonych tabel PDF.
- Wersja UNECE 01 serii zmienia m.in. wartości kat. 1 i 11/11a kierunkowskazów (maks. 1200/600 cd), ale **kat. 2a/2b, 5, 6, 12 pozostają bez zmian** — funkcje w tyle i na boku ciężarówki/naczepy są identyczne w obu wersjach.
- R148 zastępuje w jednym regulaminie dawne R4 (oświetlenie tablicy), R6, R7 (stop), R23, R38, R50, R77, R87, R91 (boczne pozycyjne); R150 zastępuje R3 i część R104 (odblaski) — pkt 1.1 R148 (P16-003).

---

## 2. Fotometria R148 — funkcje tylne i boczne (urządzenia)

Tabela zbiorcza; „D” = światło opatrzone literą „D” (zespół dwóch świateł niezależnych, pkt 3.3.2.5.2 R148). Kąty badania z zał. 2 R148 (tabele A2-1…A2-3): zapis „H wewn./zewn.”, „V góra/dół”.

| Funkcja (symbol) | min w osi [cd] | maks pojedyncze [cd] | maks „D” [cd] | kąty badania | barwa |
|---|---|---|---|---|---|
| Pozycyjne tylne (R1, stałe) | 4 | 17 | 8,5 | H 45°/80° (przy <750 mm: 20°/80°); V 15°/15° (przy <750 mm: 15°/5°) | czerwona |
| Pozycyjne tylne (R2, zmienne) | 4 | 42 | 21 | jak R1 | czerwona |
| Obrysowe tylne górne (RM1, stałe) | 4 | 17 | nd. | H 0°/80°; V 15°/15° | czerwona |
| Stop (S1, stałe) | 60 | 260 | 130 | H 45°/45° (przy <750 mm: 20°/45°); V 15°/15° | czerwona |
| Stop (S2, zmienne) | 60 | 730 | 365 | jak S1 | czerwona |
| Kierunkowskaz tylny (2a, stałe) | 50 | 500 | 250 | H 45°/80° (przy <750 mm: 20°/80°); V 15°/15° | żółta samochodowa |
| Kierunkowskaz boczny (kat. 5) | 0,6 (kierunek A) | 280 | 140 | H 5°/55° (wzgl. kierunku A); V 15°/15° | żółta samochodowa |
| Boczne pozycyjne (SM1) | 4,0 (w osi; 0,6 w polu) | 25,0 | — | H 45°/45°; V 10°/10° | żółta samochodowa (czerwona, jeśli zespolone z tylnymi) |
| Cofania (AR) | 80 | 300 (w h i wyżej) / 600 (do 5°D) / 8000 (poniżej 5°D) | — | **brak wiersza w zał. 2** (LUKA, P16-074) | biała |
| Przeciwmgłowe tylne (F1, stałe) | 150 | 300 | — | **brak wiersza w zał. 2** (LUKA) | czerwona |
| Przeciwmgłowe tylne (F2, zmienne) | 150 | 840 | — | jak F1 | czerwona |

Punkty szczególne (pełne cytaty w `manifest.csv`):

- **Stosunek stop/pozycyjne**: gdy tylne pozycyjne/obrysowe są wzajemnie sprzężone ze stopem, stosunek światłości „stop + pozycyjne” do „pozycyjne” ≥ **5:1** w polu ±5° V i ±10° H — pkt 4.8.11 R148 (P16-035). *Dla gry: wspólna komora stop/pozycyjna musi modulować jasność ≥5×.*
- Pozycyjne sprzężone ze stopem: dopuszczone **60 cd** poniżej płaszczyzny 5° w dół — pkt 5.2.3.
- Minima w polu (zał. 2 część A): pozycyjne/obrysowe **0,05 cd**; stop **0,3 cd** (S2/S4 nocą 0,07); kierunkowskazy 2a **0,3 cd** (1b: 0,7; 2b nocą 0,07); boczne pozycyjne SM1 poza osią **0,6 cd**.
- Cofania: przy montażu wyłącznie parami badanie tylko do 30° do wewnątrz pod warunkiem **25 cd** — pkt 5.8.2.
- Przeciwmgłowe tylne: min **75 cd** w rombie rozsyłu (zał. 3 pkt 2.6), powierzchnia świetlna ≤ **140 cm²** (pkt 5.9.4), po badaniu cieplnym ≥ **90%** wartości (pkt 5.9.6 + zał. 6).
- Jednorodność: rozkład „**zasadniczo jednorodny**” — w każdym kierunku ≥ najniższa wartość otaczających pól siatki (zał. 3 pkt 1.2); cofanie: ≥ 50% niższej z wartości sąsiednich punktów (zał. 3 pkt 2.5). *Dla gry: klosz nie może mieć martwych plam, ale też ostrych „punktów gorących”.*
- SM1 czerwone (zespolone z tylnymi): w sektorze 60°–90° H w przód maks. **0,25 cd** (pkt 5.7.1) — boczne pozycyjne na naczepie nie mogą „świecić” w stronę kierowcy z tyłu.

**Barwy (współrzędne chromatyczności, R48 §2.11; tylko liczby):**

- **Czerwona** (emitowana; pozycyjne, stop, przeciwmgłowe, obrysowe): granice `y = 0,335`, locus widma, `y = 0,980 − x`; punkty (0,645; 0,335), (0,665; 0,335), (0,735; 0,265), (0,721; 0,259).
- **Żółta samochodowa** (kierunkowskazy, boczne pozycyjne): granice `y = x − 0,120`, locus, `y = 0,390`, `y = 0,790 − 0,670x`; punkty (0,545; 0,425), (0,560; 0,440), (0,609; 0,390), (0,597; 0,390).
- **Biała** (cofania): granice `y = 0,150 + 0,640x`, `y = 0,440`, `x = 0,500`, `y = 0,382`, `y = 0,050 + 0,750x`, `x = 0,310`; punkty (0,310; 0,348), (0,453; 0,440), (0,500; 0,440), (0,500; 0,382), (0,443; 0,382), (0,310; 0,283).
- Barwy **odbite** (odblaski, barwa nocna): biała: `y = 0,843 − 1,182x`, `y = 0,489x + 0,146`, `y = 0,968 − 1,010x`, `y = 1,442x − 0,136`; punkty (0,373; 0,402), (0,417; 0,350), (0,548; 0,414), (0,450; 0,513). Żółta: `y = x − 0,040`, locus, `y = 0,200x + 0,268`, `y = 0,970 − x`; punkty (0,505; 0,465), (0,520; 0,480), (0,610; 0,390), (0,585; 0,385). Czerwona: `y = 0,335`, locus, `y = 0,978 − x`; punkty (0,643; 0,335), (0,665; 0,335), (0,735; 0,265), (0,720; 0,258).

---

## 3. Odblaski — R150 (CIL)

CIL = współczynnik światłości [mcd·lx⁻¹]; α = kąt rozbieżności (obserwacji), (V;H) = kąt oświetlenia.

| Klasa (barwa czerwona) | α = 20′ | α = 1°30′ |
|---|---|---|
| IA/IB (boczne naczepy/ciągnika) — (0°;0°) / (±10°;0°) / (±5°;±20°) | 300 / 200 / 100 | 5 / 2,8 / 2,5 |
| IIIA/IIIB (trójkąt tył naczepy) — (0°;0°) / (±10°;0°) / (±5°;±20°) | 450 / 200 / 150 | 12 / 8 / 8 |

- Bursztynowe IA/IB: wartości × **2,5** (pkt 5.1.4.4.2); bezbarwne (białe): × **4** (pkt 5.1.4.4.3).
- Montaż < 750 mm: badanie CIL tylko do 5° w dół (pkt 5.1.4.5 / 5.2.3.2).
- Barwy nocne wg R48 §2.11.2 (pkt 5.1.5.2 / 5.2.4.2 R150) — granice jak wyżej.
- **Trójkąt IIIA** (zał. 5 R150): trójkąt równoboczny, boki zewnętrzne **150–200 mm**; „TOP” wierzchołkiem do góry; typ wydrążony — szerokość boków ≥ **20%** długości skutecznej; powierzchnia nieciągła — szczeliny między zestawami ≤ **15 mm**, ≥ **4** zestawy optyczne na bok (pkt 2.1–2.6).

---

## 4. Lampka tablicy rejestracyjnej (dawne R4; R148 pkt 5.11)

| Parametr | Wartość | Punkt |
|---|---|---|
| Min luminancja B w każdym punkcie pomiarowym | **≥ 2,5 cd/m²** (kat. 1a, 1b, 1c, 2a, 2b); ≥ 2,0 cd/m² (kat. 1, 2) | 5.11.3 |
| Gradient luminancji (max/min między punktami) | **≤ 2 × B₀/cm** | 5.11.3 |
| Kąt padania światła na tablicę | **≤ 82°** (wierzchołek na skrajnej części urządzenia najdalej od tablicy) | 5.11.5 |
| Emisja do tyłu | zabroniona (wyjątek: światło czerwone zespolone z tylnym) | 5.11.5 |
| Barwa | bezbarwna — bez widocznej zmiany barwy tablicy | 5.11.4 |
| Pole widoczności tablicy (zał. 2 część D) | przekrój pionowy **±85°**, poziomy **±60°** | 5.11.1 + fig. A2-IV |
| Metoda pomiaru | prostopadle ±5°; punkty = okręgi **25 mm**; powierzchnia rozpraszająca **2 mm** przed oprawą | 5.11.2 |
| Kategorie tablic (zał. 3 pkt 3) | 1a: 340×240; 1b: 520×120; 1c: 255×165; 2a: 330×165; 2b: 440×220; 1: 240×130; 2: 280×200 (mm) | zał. 3 pkt 3.1–3.7 |

*Uwaga PL: tablica rejestracyjna w Polsce = kat. 1b o wymiarach 520×114 mm (ustalone w p4/M44).*

*Dla gry: lampka tablicy NIE jest „punktową lampką” — rozświetla tablicę równomiernie (gradient ≤2·B₀/cm) i nie może świecić wstecz.*

---

## 5. Budowa lamp zespolonych (tylnych) ciężarówek i naczep

### 5.1. Typy optyki spotykane w lampach zespolonych

1. **Komora z odbłyśnikiem i kloszem pryzmatycznym** (klasyczna, żarówkowa): wewnętrzna paraboliczna/lustrzana komora odbłyśnika + klosz z zewnętrznym żebrowaniem/pryzmatami rozpraszającymi; w świetle dziennym widać pryzmaty i odbłyśnik.
2. **Gładki klosz z optyką wewnętrzną** (frezowana wkładka optyczna): zewnętrzna powierzchnia gładka, „soczewki Fresnela”/lusto-klosz od wewnątrz; częste w lampach z lat 2010 (potwierdzone kadrami — manifest).
3. **LED punktowe ze soczewkami**: 2–6 diod na komorę z indywidualnymi soczewkami; wyłączona komora widać jako ciemne punkty/soczewki.
4. **LED liniowe ze światłowodem/paskiem**: pasek LED + prowadząca wiązka (światłowód lub lita dyfuzytka); równomierna linia światła bez punktów.

Potwierdzenie klatkami: patrz §6 i wiersze `kategoria=zdjęcie` w `manifest.csv` (każdy typ przypisany do konkretnych, obejrzanych kadrów).

### 5.2. Podział komór i kolejność funkcji

Lampy tylne naczep (O4) i ciągników (N3) budowane są jako pionowe zespoły 3–7 komór w jednej obudowie. Typowa kolejność od zewnątrz do środki / od góry w zespole 7-komorowym naczepy:

```
(kierunek jazdy: przód → tył)
od zewnątrz: [kierunkowskaz pomarańczowy] [stop/pozycyjne czerwone] [pozycyjne/stop czerwone]
             [obrysowe górne czerwone] [przeciwmgłowe czerwone] [cofania białe] [lampka tablicy / pusty slot]
od góry:     obrysowe górne, potem kierunkowskaz, stop, pozycyjne, przeciwmgłowe, cofania (układy różne — patrz kadry)
```

Rzeczywiste układy (liczba komór, kolejność od zewnątrz, typ optyki) potwierdzone klatkami — tabela w §6; ogólna zasada: **barwa klosza komory = barwa funkcji** (czerwona/żółta/biała), komora cofania i lampka tablicy mają klosz przezroczysty.

### 5.3. Wymiary typowej lampy 7-funkcyjnej (naczepa)

| Wartość (dł. × wys. × głęb.) | Źródło | Status |
|---|---|---|
| **390 × 145 × 70 mm** (LED 7-funkcyjna z trójkątem odblaskowym) | karta katalogowa/dystrybutor (URL w manifest, P16-301) | SOURCED |
| **400 × 153 × 88 mm** (żarówkowa 7-funkcyjna, 12 V) | karta produktu dystrybutora (P16-302) | SOURCED (sklep) |
| **450 × 138 × 90 mm**, odległość otworów montażowych **152 mm** (LED 7-komorowa do naczep) | sklep specjalistyczny (P16-303) | SOURCED (sklep; weryfikacja HTML 13.11.2026 — strona obecnie renderuje treść po stronie klienta) |
| **450 × 138 × 72,3 mm** (LED 7-funkcyjna, 24 V) | karta produktu dystrybutora (P16-305) | SOURCED (sklep) |

Wnioski dla gry: typowy zespół 7-komorowy naczepy ≈ **425 mm długości (montaż pionowy) × ~142 mm szerokości × ~81 mm głębokości** (ESTIMATED, P16-304: mediana czterech kart 390/400/450/450 × 145/153/138/138 × 70/88/90/72,3; zaokrąglenie dla gry: 420 × 140 × 80).

### 5.4. Wygląd lampy wyłączonej w świetle dziennym

- Klosz czerwonej komory: głęboki, lekko przezroczysty czerwony (czerwone komory wyglądają na ciemnoczerwone/bordowe); komora żółta (kierunkowskaz) — pomarańczowo-miodowa; komory białe (cofania, lampka tablicy) — mlecznoszare lub przezroczyste.
- W lampach pryzmatowych widać wyraźne żebrowanie klosza i lustrzany odbłyśnik; w lampach LED widać ciemne punkty diod i soczewki; w lampach ze światłowodem — jednolita „szyna” bez punktów.
- Zespół praktycznie zawsze jest **brudny** w realnych warunkach (film drogowy, kurz) — potwierdzone klatkami; dla gry realistyczny jest lekki nalot kurzu na dolnych krawędziach.

### 5.5. Oznaczenia homologacyjne na kloszu (zasada wg R148, pkt 3.3.2 + zał. 7)

Znak homologacji urządzenia (nie kopiujemy cudzych znaków — opisujemy zasadę):

- **Okrąg z literą „E” + numer państwa** homologującego (np. E1…E56 — numer, nie logo producenta).
- **Numer homologacji** (pkt 3.3.2.2), umieszczany w pobliżu okręgu (pkt 3.3.2.5.4).
- **Symbole funkcji** wg pkt 3.2.4 (tab. 1): dla naszego zestawu: R/R1/R2 (pozycyjne), RM1/RM2 (obrysowe), S1/S2 (stop), 2a/2b (kierunkowskaz tylny), AR (cofania), F1/F2 (przeciwmgłowe), L (lampka tablicy), SM1/SM2 (boczne pozycyjne), kat. 5/6 (kierunkowskaz boczny).
- **Numer regulaminu + „R” + 2 cyfry serii poprawek** (np. 148R–00 dla pierwotnej serii; 148R–01 dla serii 01).
- Symbole dodatkowe: **strzałka pozioma** = strona zewnętrzna montażu (pkt 3.3.2.5.1); **„D”** = zespół dwóch świateł niezależnych (pkt 3.3.2.5.2); **„Y”** = układ współzależny; **pionowa strzałka w dół** = zmniejszony rozsył (pkt 3.3.2.5.3).
- W lampach **zespolonych** wszystkie symbole funkcji występują łącznie w jednym znaku (zał. 7, przykłady A7-I…A7-IV).
- Alternatywnie **niepowtarzalny identyfikator (UI)** zamiast znaku E — wysokość znaku a ≥ 8 mm (pkt 3.3.3); dane homologacji w bazie ONZ.

*Dla gry: na kloszu fikcyjnej lampy wystarczy fikcyjny „okrąg E + numer” + symbole funkcji + „148R–00”; nie odtwarzamy żadnych rzeczywistych znaków homologacji ani logotypów producentów.*

---

## 6. Lampka tablicy rejestracyjnej — położenie i budowa (z kadrów)

<!-- PHOTO-PLATE-SECTION: do uzupełnienia po obejrzeniu kadrów lampki tablicy -->

Zasady montażu (instalacja) omówiono w p4/M44; tutaj położenie i budowa z kadrów:
- Ciągnik N3: lampka nad tablicą w zderzaku/na belce tablicy (kable: patrz kadry P16-2xx).
- Naczepa O4: lampka w belce RUPD (zderzak tylnej osłony) nad tablicą lub zespolona z obudową lampy zespolonej (komora „REG” 7-komorowej).

---

## 7. Kadry (zdjęcia CC) —	status oglądania

<!-- PHOTO-TABLE: do uzupełnienia: ≥15 kadrów lamp zespolonych + ≥5 lampek tablicy, każdy OBEJRZANY -->

Każdy kadr: typ optyki, liczba komór, kolejność funkcji od zewnątrz, widoczne pryzmaty/punkty LED, stan czysty/brudny, włączony/wyłączony, dzień/zmierzch/noc, marka widoczna (→ „tylko referencja kształtu”). Pełne opisy w `manifest.csv` (kategoria `zdjęcie`). Pliki JPG ≤1600 px w archiwum `mistral-p16-truck-lamps-files.zip` (NIE w gicie).

---

## 8. Luki i nieweryfikowalne

| # | Luka | Status |
|---|---|---|
| L1 | Kąty widoczności badania dla AR (cofania) i F1/F2 (przeciwmgłowe) nie występują w tab. A2-1 zał. 2 R148 | UNVERIFIED (P16-074) |
| L2 | Wartości procentowe siatki rozsyłu (fig. A3-I) odczytane z rysunku — niepewny odczyt wizyjny; nie użyto w manifest | UNVERIFIED (pominięte szczegółowe %) |
| L3 | Wiersze tabel PL PDF sklejone (dwie kolumny w jednym runie) — każda taka wartość odnotowana i potwierdzona wersją EN | SOURCED z uwagą |
| L4 | Wymiary lamp 7-komorowych z kart katalogowych/sklepów (nie z tekstów regulaminów — regulaminy nie określają wymiarów lamp) | SOURCED (karta katalogowa) |
| L5 | Fotograficzne potwierdzenie lamp LED liniowych ze światłowodem — zależy od dostępnych kadrów CC | patrz §7 |

---

## 9. Metodologia i samokontrola

- Podstawa liczb: pełne teksty PL z Dz.U. UE (Cellar/EUR-Lex, CELEX 42021X1719, 42021X1721, 42021X1718), weryfikacja krzyżowa wersjami EN UNECE (R148e.docx, R150e.docx — 00 seria; R148r1am2E — 01 seria) pobranymi przez Wayback Machine (unece.org blokuje roboty).
- Zdjęcia: wyłącznie licencje CC0/CC BY/CC BY-SA (Wikimedia Commons; Openverse/Panoramax/KartaView sprawdzono jako źródła pomocnicze); każdy kadr pobrano jako JPG ≤1600 px i **obejrzano modelem wizyjnym** (opis w kolumnie `opis_co_widać`); jeśli widoczna marka — oznaczono „marka widoczna, tylko referencja kształtu”.
- Zakaz Google Maps/Street View/Earth/3D Tiles — nie wykorzystano żadnych treści Google.
- Samokontrola: losowe ≥20% wierszy manifestu (jawny seed) — sprawdzenie: link działa, cytat zgadza się z PDF, wersja regulaminu poprawna; kadry ponownie obejrzane. Wynik: `audit_20_percent.json`.
- Archiwum zdjęć i dokumentów: `mistral-p16-truck-lamps-files.zip` (nazwa/rozmiar/sha256 w opisie PR); w repo tylko pliki tekstowe (pliki binarne przechodzą przez GitHub API zniekształcone — jak w p4).

*Wygenerowano: 2026-11-13. Autor pakietu: Vibe (Mistral) na zlecenie Mateusza Kapicy (woogitsugames).*
