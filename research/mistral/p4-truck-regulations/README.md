# M44 — P4: Regulacje wpływające na wygląd ciężarówki i widok z kabiny

**Repo:** `woogitsugames/kamion` · **Gałąź:** `research/mistral-p4-truck-regulations`
**Data badań:** 2026-11-13 · **Zespół pojazdu:** fikcyjny ciągnik siodłowy 4×2 (kat. N3) + naczepa firanka 13,6 m, 3 osie (kat. O4), zestaw 5-osiowy

## Cel

Zebranie wymaganych przepisów, które determinują **wygląd zewnętrzny ciężarówki i widok z kabiny** dla realistycznego symulatora: światła i odblaski (R48), oznakowanie odblaskowe i tablice tylne (R104, R70), lusterka (R46), osłony przeciwwjazdowe (R58, R73), wymiary i masy (96/53/WE + 2015/719), polskie wymogi wyposażenia i tablic (rozporządzenia Dz.U. 2024 poz. 502 i 1709) oraz sekcja tablic spotykanych w PL (obowiązek vs zwyczaj).

## Metoda

1. **Źródła wyłącznie urzędowe:** UNECE (pełne teksty regulaminów), EUR-Lex/Publikacje UE (Cellar), Dziennik Ustaw (dziennikustaw.gov.pl). Zakaz Google Maps/Street View/Earth/3D Tiles zachowany — nie użyto.
2. **Pozyskanie:** oficjalne PDF-y pobrane 2026-11-13 (EUR-Lex bezpośrednio lub przez Cellar — `publications.europa.eu/resource/celex/...` z `Accept: application/pdf`, `Accept-Language: pol`; dokumenty UNECE przez web.archive.org, ponieważ unece.org zwraca 403 dla klientów automatycznych; Dz.U. bezpośrednio z dziennikustaw.gov.pl).
3. **Ekstrakcja tekstu:** własny parser PDF (parser obiektów PDF + lekser strumienia treści z mapami ToUnicode, bez zależności zewnętrznych). Dla oryginału 96/53/WE z 1996 r. (skan Dz.U. WE) — OCR i sklejony tekst; spacje w cytatach odtworzone, co odnotowano w uwagach wierszy.
4. **Weryfikacja:** każda liczba w `manifest.csv` ma cytat ≤ 25 słów + numer punktu + URL. Status: SOURCED / ESTIMATED / UNVERIFIED. Żadnych źródeł wtórnych (blogi/fora) do potwierdzania przepisów.
5. **Samokontrola:** deterministyczna próba losowa 25 % wierszy (seed jawny: 20261113) z ponowną weryfikacją cytatu wobec pełnego tekstu źródła, limitu 25 słów i aktualności aktu — wynik w `audit_20_percent.json`. **Dodatkowo wykonano pełną weryfikację wszystkich 171 wierszy: 0 niezgodności.** Wcześniejsze iteracje audytu wyłapały 6 niezgodności (m.in. błędne brzmienie pkt 2.2.2 lit. a dyrektywy 96/53/WE, „nienapędzane"/„nienapędowe", twarda spacja w § 2 zał. 10 WT) — wszystkie poprawione przed oddaniem.
6. Środowisko wykonawcze ulegało resetom; po każdym resecie odtwarzano stan z zarchiwizowanych PDF-ów i ponawiano pełną weryfikację.

## Ustalenia — podsumowanie

### 1. Światła — Regulamin EKG ONZ nr 48 (seria poprawek 07 + Suplement 1, Dz.U. UE L 347 z 30.9.2021)
- Rama homologacyjna: rozporządzenie ramowe (UE) 2019/2144 (GSR2, wersja skonsolidowana 07.07.2024) czyni R48 (D15), R46 (B13), R58 (A12), R73 (A13) obowiązkowymi dla M/N/O.
- **Kierunkowskazy:** układ A dla ciągnika: 2 przednie (kat. 1/1a/1b wg odległości 40/20 mm od światła mijania), 2 tylne (2a/2b) **+ 2 dodatkowe obowiązkowe dla N3**; boczne kat. 6; **N3 >9 m: dodatkowo 3× kat. 5 na stronę**. Naczepa (układ B): 2 tylne + 2 dodatkowe, **3× kat. 5/stronę — chyba że ≥3 obrysowe boczne żółte migające w fazie** (wyjątek istotny dla naczep z migającymi obrysami).
- Częstotliwość 90±30/min; wszystkie światła: ≤400 mm od krawędzi zewnętrznej; odstęp wewnętrzny ≥600 mm (400 mm przy szer. <1300 mm).
- **Pozycyjne:** przednie 2 (przyczepy szer. >1600 mm; przyczepy ≤150 mm od krawędzi!), tylne 2 (+2 dopuszczalne gdy brak tylnych obrysowych górnych).
- **Obrysowe górne:** obowiązkowe >2,10 m szerokości: 2+2; białe z przodu, czerwone z tyłu; przednie ciągnika — nie niżej niż górna krawędź szyby przedniej.
- **Obrysowe boczne (SM1):** obowiązkowe >6 m; odstępy ≤3 m (wyj. 4 m); pierwsze ≤3 m od przodu, ostatnie ≤1 m od tyłu.
- **Odblaski:** przednie — obowiązkowe w przyczepach (2× IA/IB, ≤150 mm od krawędzi); tylne — nietrójkątne w pojazdach silnikowych (IA/IB), **trójkątne IIIA/IIIB obowiązkowe w przyczepach, zakazane w pojazdach silnikowych**; boczne — obowiązkowe >6 m (wszystkie przyczepy), odstępy ≤3 m.
- **Oznakowanie konturowe (6.21):** tył — pełne dla O3/O4 oraz N2 >7,5 t i N3 **z wyłączeniem ciągników siodłowych**; bok — częściowe >6 m (te samo wyłączenie). Nasz ciągnik siodłowy **nie wymaga** oznakowania konturowego; naczepa **tak**: tył ≥70 % szerokości, ≤600 mm od krańców, 250–1500 mm (wyj. 2500), górne ≤400 mm od górnej krawędzi, przerwy ≤50 %, >200 mm od świateł stopu, elementy ≥60 mm; tylne tablice R70 (seria 01) mogą być liczone jako kontur (6.21.7.4).
- Pełna tabela poniżej.

### 2. Oznakowanie odblaskowe i tablice tylne — R104, R70
- **R104 (pierwotna wersja):** materiał kl. C (kontur/pasy), kl. D (<2 m² powierzchni odblaskowej) / E (≥2 m²) dla grafik; fotometria kl. C wg zał. 7 tab. 1 (m.in. żółty R′ 300/450/120, biały 130/200/60, czerwony 75/90/30 przy β=0/5/30°); znak „TOP" co 0,5 m na pasach.
- **R70 (seria 01):** klasa 1 — pojazdy ciężkie (czerwone pasy fluorescencyjne na przemian z żółtymi odblaskowymi), klasa 2 — przyczepy/naczepy (czerwone obrzeże + żółte tło). Zakres: N3 **z wyłączeniem ciągników siodłowych**; O1–O3 >8,0 m; **wszystkie O4**. Wymiary (zał. 12): długość zestawu 1130–2300 mm, szerokość 140 ±10 mm (ciągniki/ciężarowe) / 200 +30/−5 mm (przyczepy i naczepy); „TOP" u góry; klasy oznaczane RF/RR. Montaż (zał. 15 — wytyczne): dolna ≥250, górna ≤2100 mm; ±5°; widoczność 30°/15°; 1, 2 lub 4 tablice. **W PL obowiązek montażu wynika wprost z § 42 WT + zał. 10** (R70 definiuje wygląd tablic).

### 3. Lusterka — R46 (seria poprawek 04, Dz.U. UE L 237 z 8.8.2014)
Dla ciągnika N3 (tabela 15.2.1) — wszystkie cztery klasy obowiązkowe:
- **kl. II (główne):** 1 po stronie kierowcy + 1 po stronie pasażera. Pole: płaski poziomy fragment drogi szer. ≥5 m, od 30 m za punktami ocznymi po horyzont; dodatkowo fragment szer. >1 m od 4 m za punktami ocznymi.
- **kl. IV (boczne „wide"):** 1+1. Pole: fragment drogi szer. ≥15 m, odcinek 10–25 m za punktami ocznymi; dodatkowo szer. 4,5 m od 1,5 m za punktami ocznymi.
- **kl. V (zbliżeniowe, przód):** 1 po stronie pasażera (obowiązkowe) + opcjonalne po stronie kierowcy; montaż ≥2 m. Pole: bok kabiny; płaszczyzna 2 m przed nią; 1,75 m za punktami ocznymi; 1 m przed punktami ocznymi (wariant montaż ≥2,4 m: do 3 m przed punktami ocznymi — 15.2.4.5.9).
- **kl. VI (przednie):** 1 lusterko przednie na wysokości ≥2 m. Pole: od najdalszego punktu przodu do 2000 mm przed płaszczyzną przegrody; do 2000 mm na zewnątrz od boku kierowcy; krzywizna przedniej części promień 2000 mm.
- Wymiary kl. II: a = 170/(1+1000/r), b = 200 mm (r — promień krzywizny); kl. I: prostokąt 40 mm × „a". Montaż: ≤55° od wzdłużnej płaszczyzny (przez środek lusterka i linię ocznu 65 mm); wystawanie ≤250 mm poza obrys bez lusterek gdy dolna krawędź <2 m.
- Dla naczepy O4 — brak wymogów lusterkowych (R46 dotyczy pojazdów silnikowych).

### 4. Osłony przeciwwjazdowe — R58 (seria 03), R73 (seria 01)
- **R58 (RUPD/RUP — tył):** **części dotyczące pojazdu nie obejmują pojazdów ciągnących zespołów (ciągników siodłowych)** — nasz ciągnik nie wymaga RUP; urządzenie RUPD (poprzeczka ≥120 mm) homologowane wg części I. Dla naczepy O4: prześwit ≤450 mm (zawieszenie pneumatyczne/hydrauliczne/autopoziomujące) lub ≤500 mm (inne); wariant równoważny: kąt natarcia 8° przy ≤550 mm. Przepis o ≤550 mm na całej szerokości (pkt 25.2) **nie dotyczy N3/O4**.
- **R73 (LPD — boki):** nie dotyczy ciągników siodłowych; **dla naczepy O4**: dolna krawędź ≤550 mm; górna ≤350 mm poniżej struktury pojazdu (poziom podłogi lub 950 mm — mniejsza; ≥950 mm gdy struktura >1,3 m); przednia krawędź ≤250 mm za płaszczyzną nóg podporowych (≤2,7 m od sworznia); tylna ≤300 mm przed płaszczyzną boczną opon; główna powierzchnia ≤150 mm w głąb od maksymalnej szerokości; szczeliny ≤25 mm; listwy ≤300 mm od siebie, wysokość ≥100 mm (N3/O4, płaskie); ugięcie ≤30 mm (tylne 250 mm) / ≤150 mm (reszta) przy 1 kN.

### 5. Wymiary i masy — 96/53/WE + Dyrektywa (UE) 2015/719
Nasz zestaw: ciągnik 4×2 + naczepa 3-osie (zespół 5-osiowy):
- **Długość pojazdu przegubowego: 16,50 m** (zał. I pkt 1.1); promienie skrętu 12,50/5,30 m (pkt 1.5); sworzeń–tył naczepy 12,00 m (pkt 1.6, przy oś sworznia ≤1,50 m przed tylną osią).
- **Szerokość: 2,55 m** (pkt 1.2; nadbudówki chłodni 2,60 m — 2015/719); **wysokość: 4,00 m** (pkt 1.3).
- **Masa całkowita zespołu: 40 t** (zał. I pkt 2.2.2 lit. a — „pojazdy silnikowe dwuosiowe z naczepami trzyosiowymi 40 ton"; odpowiednik PL: § 3 ust. 1 pkt 2 WT: zespół ≥5 osi z pojazdem samochodowym jako ciągnącym — 40 t).
- Wyjątki intermodalne (nie dotyczą zwykłego zestawu firankowego): 42 t (2-osie ciągnik + kontenery ≤45 stóp; 2015/719 lit. c; WT § 3 ust. 1 pkt 2 lit. a i c) i 44 t (3-osie ciągnik; 2015/719 lit. d; WT lit. b i d).
- Ciągnik dwuosiowy: 18 t (pkt 2.3.1; od 2015/719 — „inne niż autobusy"; dopłata maks. +1 t dla paliw alternatywnych); naczepa 3-osie: 24 t (pkt 2.1.2; w PL § 3 ust. 1 pkt 1 lit. c dotyczy przyczep „z wyjątkiem naczepy" — masa naczepy limitowana DMC zespołu).
- **Naciski osi:** pojedyncza oś nienapędowa 10 t (pkt 3.1); oś napędowa 11,5 t (pkt 3.4.2); oś trójosiowa naczepy (dystanse 1,3–1,4 m): 24 t na zespół osi, tj. maks. 22,5 t/oś przy zestawie 38 t wg pkt 3.3.2 (tabela dystansów w akcie).
- Ostatnia nowelizacja merytoryczna 96/53/WE: **2015/719** (dyrektywy 2019/1161 — czyste pojazdy, zmienia 2009/33/WE; 2022/1393 — poziomy THC w konopiach — **nie dotyczą** 96/53/WE; sprawdzono pełne teksty obu aktów).
- Tachograf: zakres z rozporządzenia (WE) nr 561/2006 (art. 2 ust. 1 lit. a — przewóz rzeczy przy DMC zespołu >3,5 t); montaż rejestratora wg rozporządzenia (UE) 165/2014 (poza zakresem wyglądu).

### 6. Polska — wyposażenie i tablice
- **Rozporządzenie w sprawie warunków technicznych pojazdów (t.j. Dz.U. 2024 poz. 502 — akt obowiązuje):**
  - § 11 ust. 1: VIN + tabliczka znamionowa wg zał. 4 (pkt 1), trójkąt ostrzegawczy (pkt 13), gaśnica w miejscu łatwo dostępnym (pkt 14), miejsce na tablice rejestracyjne wg zał. 5 (pkt 18).
  - **Apteczka — brak wymogu dla N3/O4** (wymóg tylko dla autobusów § 19–20 i pojazdów nauki jazdy § 43–44); **kliny pod koła — brak w całym akcie** (0 wystąpień; praktyka/ADR, nie obowiązek WT); tachograf w WT tylko dla pojazdów nauki jazdy (§ 43).
  - **Tablice wyróżniające (§ 42 + zał. 10):** OBOWIĄZKOWE z tyłu naczepy >8 m (nasza 13,6 m — tak); samochody ciężarowe DMC >7,5 t **z wyłączeniem ciągnika siodłowego** (nasz ciągnik — nie). Zał. 10: z tyłu, prostopadle i symetrycznie; pasy 45° ±5°, szer. 100 ±2,5 mm, żółty odblaskowy + czerwony fluorescencyjny (poj. samochodowy); naczepa: żółte tło odblaskowe + czerwone obrzeże fluorescencyjne; dolna ≥250, górna ≤2100 mm; ≤400 mm od obrysu; odstęp między tablicami 200–300 mm; wymiary w rysunkach 1–2 (grafika → UNVERIFIED liczbowo; por. R70 zał. 12: 1130–2300 mm).
  - Miejsce tablicy rejestracyjnej (zał. 5 § 2): tylne 520×120 lub 340×240 mm; wysokość dolnej ≥0,30 m, górnej ≤1,20 m (absolutnie ≤2,00 m); pochylenie 5–30° od pionu.
- **Rozporządzenie w sprawie rejestracji i zabezpieczeń pojazdów (t.j. Dz.U. 2024 poz. 1709 — akt obowiązuje):**
  - § 33 ust. 1: pojazd — tablice z przodu i z tyłu; **przyczepy (naczepy) — tylko z tyłu**.
  - Zał. 12: płyta z taśmy aluminiowej 1 mm; kształty wg rysunku 1, odchyłki głównych wymiarów ±1 mm (**wymiary 520×114 mm tylko w rysunku — UNVERIFIED w tekście**).
  - § 28: niebieskie pole z 12 gwiazdkami UE i literami „PL"; § 39: znak „PL" z tyłu nadwozia w ruchu międzynarodowym; § 38 + zał. 15: tarcza prędkości — **tylko autobus albo prędkość indywidualna** (dla N3/O4 brak obowiązku); § 37: numery na burcie — tylko pojazdy samowyładowcze.

### 7. Tablice spotykane w PL — obowiązek vs zwyczaj
| Tablica | Status | Podstawa |
|---|---|---|
| Tylne tablice wyróżniające (żółto-czerwone) na naczepie | **OBOWIĄZKOWE** | § 42 ust. 1 + zał. 10 WT (Dz.U. 2024 poz. 502); wygląd zgodny z R70 kl. 2 (seria 01) |
| Tablice wyróżniające na ciągniku siodłowym | **NIEOBOWIĄZKOWE** | § 42 ust. 1 wyłącza ciągnik siodłowy (DMC >7,5 t) |
| Tablica „DŁUGI POJAZD" | **ZWYCZAJ — brak obowiązku** | 0 wystąpień w t.j. WT; Konwencja Wiedeńska 1968 (tekst 2006, zał. 1–9) nie przewiduje tablicy „long vehicle" (weryfikacja pełnotekstowa) |
| Znak ograniczenia prędkości (tarcza, np. 80 km/h) na naczepie | **ZWYCZAJ/dobrowolna — brak obowiązku** | § 38 rozporządzenia rejestracyjnego: tarcza tylko dla autobusów lub prędkości indywidualnej |
| Tablice odblaskowe ostrzegawcze R70 (kl. 2) | **OBOWIĄZKOWE** (jako tablice wyróżniające) | § 42 WT → zał. 10; R70 seria 01 definiuje tablicę |
| Znak „PL" (owalny) | obowiązkiem warunkowym | § 39 rozporządzenia rejestracyjnego — tylko w ruchu międzynarodowym |

## Tabela R48 — element → liczba → wysokość → odległość od krawędzi → barwa (N3 ciągnik / O4 naczepa)

| Element (punkt R48) | N3 — liczba obowiązkowa | O4 — liczba obowiązkowa | Wysokość nad jezdnią (mm) | Odległość od krawędzi / odstępy (mm) | Barwa |
|---|---|---|---|---|---|
| Kierunkowskazy przednie (6.5) | 2 (kat. 1/1a/1b) | – | 350–1500 (wyj. 2100) | ≤400; odstęp wewn. ≥600 (400 przy szer. <1300) | żółta samochodowa |
| Kierunkowskazy tylne (6.5) | 2 + 2 dodatkowe (N3) | 2 + 2 dodatkowe (O2–O4) | 350–1500 (wyj. 2100) | ≤400; odstęp wewn. ≥600/400 | żółta samochodowa |
| Kierunkowskazy boczne (6.5.3) | kat. 6; przy dł. >9 m dodatkowo 3× kat. 5/stronę | 3× kat. 5/stronę (chyba że ≥3 obrysowe boczne migające w fazie) | 500–1500 (wyj. 2300); ≤1800 od przodu | – | żółta samochodowa |
| Światła stop S1/S2 (6.7) | 2 | 2 | 350–1500 (wyj. 2100) | ≤400; odstęp wewn. ≥600/400 | czerwona |
| Pozycyjne przednie (6.9) | 2 | 2 (obowiązek przy szer. >1600) | 250–1500 (wyj. 2100) | ≤400 (przyczepy ≤150); odstęp ≥600/400 | biała |
| Pozycyjne tylne (6.10) | 2 (+2 dopuszczalne) | 2 (+2 dopuszczalne) | 350–1500 (wyj. 2100) | ≤400 | czerwona |
| Obrysowe górne (6.13; >2,10 m) | 2 przód + 2 tył | 2 przód + 2 tył | poj. siln. przód: nie niżej niż górna krawędź szyby przedniej; przyczepy: maks. możliwa | ≤400 od krawędzi zewn. | biała z przodu, czerwona z tyłu |
| Obrysowe boczne SM1 (6.18; >6 m) | obowiązkowe | obowiązkowe | 250–1500 (wyj. 2100) | odstępy ≤3000 (wyj. 4000); pierwsze ≤3000 od przodu, ostatnie ≤1000 od tyłu | żółta samochodowa |
| Odblaski przednie (6.16) | opcjonalne (poj. silnik.) | 2 — IA/IB (obowiązkowe) | 250–900 (wyj. 1500) | przyczepy ≤150 | taka sama jak światło padające |
| Odblaski tylne (6.14/6.15) | 2 — IA/IB nietrójkątne; trójkątne zakazane | 2 — IIIA/IIIB trójkątne | 250–900 (zespolone ≤1200; wyj. 1500) | ≤400 | czerwona |
| Odblaski boczne IA/IB (6.17; >6 m) | obowiązkowe | obowiązkowe | 250–900 (zespolone ≤1200; wyj. 1500) | odstępy ≤3000; ostatnie ≤1000 od tyłu | żółta samochodowa |
| Oświetlenie tablicy rej. (6.8) | 1 | 1 | – | – | biała |
| Migotanie kierunkowskazów (6.5.9) | 90 ± 30/min | 90 ± 30/min | – | – | – |
| Oznakowanie konturowe (6.21, kl. C wg R104) | TYŁ: N2 >7,5 t i N3 **z wył. ciągników siodłowych**; BOK >6 m — nasz ciągnik: BRAK obowiązku | TYŁ (pełne) + BOK >6 m (częściowe) | dolne 250–1500 (wyj. 2500); górne ≤400 od górnej krawędzi pojazdu | tył ≥70 % szerokości; ≤600 od krańców; przerwy ≤50 %; >200 od świateł stopu; elementy ≥60 mm | materiał kl. C R104; tablice R70 (seria 01) liczone jako kontur |

## Braki / ograniczenia

- **UNVERIFIED:** wymiary tablicy rejestracyjnej 520×114 mm (tylko rysunek w zał. 12 — grafika bez warstwy tekstowej); liczbowe wymiary tablic wyróżniających z zał. 10 WT rys. 1–2 (grafika; por. wartości R70 zał. 12).
- **OCR (96/53/WE, skan 1996):** spacje w cytatach odtworzone; brzmienie pkt 2.2.2 lit. a potwierdzone paralelnie § 3 ust. 1 pkt 2 WT (Dz.U. 2024 poz. 502). Nie udało się pobrać wersji skonsolidowanej 01996L0053-20190814 (Cellar HTTP 500) — oryginał + 2015/719 wystarczają do pełnej rekonstrukcji brzmienia.
- **ESTIMATED:** brak pozycji ESTIMATED — wszystkie wartości liczbowe pochodzą z aktów prawnych.
- R48 punkt 6.21 (kontur) i R70 zał. 15 — wymagania montażowe „miejsc przewidzianych przez producenta"; dla modelu 3D wystarczą wartości minimalne/maksymalne z manifestu.
- Tachograf cyfrowy: wymogi montażowe w rozporządzeniu (UE) 165/2014 (poza zakresem zadania — nie wpływa na wygląd zewnętrzny poza samym urządzeniem w kabinie).

## Samokontrola (audyt)

- **Seed:** 20261113 · **Populacja:** 171 · **Próba:** 43 (25,1 % ≥ wymagane 20 %)
- **Wynik:** 42 PASS, 0 FAIL, 1 SKIPPED (wiersz weryfikacji negatywnej — bez cytatu; adnotacja w JSON)
- **Metoda:** porównanie znormalizowane (lowercase, bez diakrytyków, tylko znaki alfanumeryczne — eliminuje wpływ twardych spacji U+00A0, łamania wierszy i sklejonego OCR) każdego segmentu cytatu (separator „…") z pełnym tekstem oficjalnego dokumentu; limit ≤25 słów; potwierdzenie aktualności aktu (t.j./seria poprawek przywołana w GSR2 z 07.07.2024).
- **Dodatkowo:** pełna weryfikacja wszystkich 171 wierszy — 0 niezgodności. Szczegóły: `audit_20_percent.json`.

## Struktura

```
research/mistral/p4-truck-regulations/
├── README.md            (ten plik)
├── manifest.csv          (171 wierszy, UTF-8, separator „;”)
├── sources.md            (pełna lista źródeł z URL i licencjami)
├── audit_20_percent.json (samokontrola: seed 20261113, 43 pozycje)
```

**PDF-y:** wszystkie cytowane dokumenty pobrano 2026-11-13; binarna publikacja załączników przez dostępny konektor GitHub App nie jest wykonalna (konektor przesyła wyłącznie treść tekstową — pliki binarne uległyby uszkodzeniu), więc w repozytorium znajdują się wyłącznie pliki tekstowe, a każdy PDF jest dostępny pod oficjalnym adresem URL w `sources.md` (dokumenty ≤ 5 MB i > 5 MB jednolicie jako linki).
