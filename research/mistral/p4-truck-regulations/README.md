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
5. **Samokontrola:** deterministyczna próba losowa 25 % wierszy (seed jawny: 20261113) z ponowną weryfikacją cytatu wobec pełnego tekstu źródła, limitu 25 słów i aktualności aktu — wynik w `audit_20_percent.json`. **Korekta po przeglądzie s17 (2026-11-13):** pierwotna deklaracja pełnej weryfikacji 171 wierszy (0 niezgodności) była zawyżona — przegląd zewnętrzny (próba 35 wierszy, seed 4417) wykazał odrzucony cytat w P4-134 („22,5 t/oś” — wartość nieobecna w 96/53/WE) i błędny numer punktu w P4-133 (3.4.2 zamiast 3.4.1); obie pozycje poprawiono w tej rewizji (patrz sekcja „Korekty po przeglądzie s17”). Wcześniejsze iteracje audytu wyłapały 6 niezgodności (m.in. błędne brzmienie pkt 2.2.2 lit. a dyrektywy 96/53/WE, „nienapędzane"/„nienapędowe", twarda spacja w § 2 zał. 10 WT) — wszystkie poprawione przed oddaniem.
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
- **R104 (wersja pierwotna regulaminu; Rev.2/Add.103/Rev.1, 2010 — korekta etykiety po przeglądzie s17; zał. II GSR2 przywołuje „pierwotną wersję regulaminu”, nie serię poprawek):** materiał kl. C (kontur/pasy), kl. D (<2 m² powierzchni odblaskowej) / E (≥2 m²) dla grafik; fotometria kl. C wg zał. 7 tab. 1 (m.in. żółty R′ 300/450/120, biały 130/200/60, czerwony 75/90/30 przy β=0/5/30°); znak „TOP" co 0,5 m na pasach — **tylko na materiale nieomnirotacyjnym (pkt 4.1.2; korekta po przeglądzie s17 — wcześniej warunek pominięto)**.
- **R70 (seria 01):** klasa 1 — pojazdy ciężkie (czerwone pasy fluorescencyjne na przemian z żółtymi odblaskowymi), klasa 2 — przyczepy/naczepy (czerwone obrzeże + żółte tło). Zakres: N3 **z wyłączeniem ciągników siodłowych**; O1–O3 >8,0 m; **wszystkie O4**. Wymiary (zał. 12): długość zestawu 1130–2300 mm, szerokość 140 ±10 mm (ciągniki/ciężarowe) / 200 +30/−5 mm (przyczepy i naczepy); „TOP" u góry; klasy oznaczane RF/RR. Montaż (zał. 15 — wytyczne): dolna ≥250, górna ≤2100 mm; ±5°; widoczność 30°/15°; 1, 2 lub 4 tablice. **W PL obowiązek montażu wynika wprost z § 42 WT + zał. 10** (R70 definiuje wygląd tablic).

### 3. Lusterka — R46 (seria poprawek 04, Dz.U. UE L 237 z 8.8.2014)
Dla ciągnika N3 (tabela obowiązkowych klas — pkt 15.2.1.1.1, wiersz N3; korekta numeracji po przeglądzie s17): klasy II i IV obowiązkowe, V obowiązkowe po stronie pasażera, VI obowiązkowe:
- **kl. II (główne):** 1 po stronie kierowcy + 1 po stronie pasażera. Pole: płaski poziomy fragment drogi szer. ≥5 m, od 30 m za punktami ocznymi po horyzont; dodatkowo fragment szer. >1 m od 4 m za punktami ocznymi.
- **kl. IV (boczne „wide"):** 1+1. Pole: fragment drogi szer. ≥15 m, odcinek 10–25 m za punktami ocznymi; dodatkowo szer. 4,5 m od 1,5 m za punktami ocznymi.
- **kl. V (zbliżeniowe, przód):** 1 po stronie pasażera (obowiązkowe) + 1 opcjonalne po stronie kierowcy — pkt 15.2.1.1.1, wiersz N3 (i N2 >7,5 t), kolumna klasy V: „Obowiązkowe (zob. pkt 15.2.2.7 i 15.2.4.5.5) 1 lusterko po stronie pasażera; Opcjonalne 1 lusterko po stronie kierowcy (oba lusterka zamontowane na wysokości co najmniej 2 m od podłoża)”. Pole: bok kabiny; płaszczyzna 2 m przed nią; 1,75 m za punktami ocznymi; 1 m przed punktami ocznymi (wariant montaż ≥2,4 m: do 3 m przed punktami ocznymi — 15.2.4.5.9).
- **kl. VI (przednie):** 1 lusterko przednie na wysokości ≥2 m. Pole: od najdalszego punktu przodu do 2000 mm przed płaszczyzną przegrody; do 2000 mm na zewnątrz od boku kierowcy; krzywizna przedniej części promień 2000 mm.
- **Urządzenie typu kamera-monitor (CMS):** w tekście opublikowanym w Dz.U. UE (seria 04 + Suplement 1) może zastąpić lusterka kl. V i VI (pkt 15.2.1.1.2). **Korekta po ponownym przeglądzie s17 (errata lidera):** Suplement 2 do serii 04 (E/ECE/324/Rev.1/Add.45/Rev.6, w mocy od 18.06.2016) dopuszcza zastąpienie lusterek **wszystkich klas, w tym II i IV** („optional replacement of mirrors of Classes I to IV by camera-monitor systems”); Suplement 2 nie został opublikowany w Dz.U. UE — stosowanie w UE niepotwierdzone (pewność S). Patrz „Punkty otwarte z przeglądu s17 — wyniki”, punkt (a).
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
- **Naciski osi:** pojedyncza oś nienapędzana 10 t (pkt 3.1); oś napędowa 11,5 t (pkt **3.4.1** — „Oś napędowa pojazdów ... 11,5 tony”; korekta numeru punktu po przeglądzie s17: było 3.4.2); zespół osi trójosiowej naczepy przy dystansach osi 1,3 m < d ≤ 1,4 m: **24 t na zespół osi** (pkt 3.3.2: „1,3 < d ≤ 1,4 — 24 tony”). **Korekta po przeglądzie s17:** usunięto sformułowanie „wyj. do 22,5 t/oś przy 38 t” — takiej wartości nie ma w 96/53/WE; limit dotyczy sumy nacisków na zespół osi, nie pojedynczej osi (tabela dystansów w akcie).
- Nowelizacje 96/53/WE — pełna lista (**korekta po przeglądzie s17**; wcześniejsze sformułowanie „ostatnia nowelizacja 2015/719” było nieprawdziwe): **2002/7/WE**; **(UE) 2015/719** (z sprostowaniem — Dz.U. UE L 277 z 27.10.2022, s. 314); **Decyzja (UE) 2019/984** (art. 10a — homologacja kabin; nie zmienia zał. I); **Rozporządzenie (UE) 2019/1242** (art. 10b + adnotacje do zał. I pkt 2.2 i 2.2.2 — masa maksymalna zespołu **+1 t** dla pojazdów na paliwa alternatywne, **+2 t** dla pojazdów bezemisyjnych). Ostatnia konsolidacja: **14.08.2019** (01996L0053-20190814). **Wpływ na nasz zestaw: 40 t bez zmian** (napęd diesel — dopłaty z 2019/1242 nie mają zastosowania). Dyrektywy 2019/1161 (czyste pojazdy, zmienia 2009/33/WE) i 2022/1393 (poziomy THC w konopiach) — **nie dotyczą** 96/53/WE; sprawdzono pełne teksty obu aktów.
- Tachograf: zakres z rozporządzenia (WE) nr 561/2006 (art. 2 ust. 1 lit. a — przewóz rzeczy przy DMC zespołu >3,5 t); montaż rejestratora wg rozporządzenia (UE) 165/2014 (poza zakresem wyglądu).

### 6. Polska — wyposażenie i tablice
- **Rozporządzenie w sprawie warunków technicznych pojazdów (t.j. Dz.U. 2024 poz. 502 — akt obowiązuje):**
  - § 11 ust. 1: VIN + tabliczka znamionowa wg zał. 4 (pkt 1), trójkąt ostrzegawczy (pkt 13), gaśnica w miejscu łatwo dostępnym (pkt 14), miejsce na tablice rejestracyjne wg zał. 5 (pkt 18).
  - **Apteczka — brak wymogu dla N3/O4** (wymóg tylko dla autobusów § 19–20 i pojazdów nauki jazdy § 43–44); **kliny pod koła — brak w całym akcie** (0 wystąpień; praktyka/ADR, nie obowiązek WT); tachograf w WT tylko dla pojazdów nauki jazdy (§ 43).
  - **Tablice wyróżniające (§ 42 + zał. 10):** OBOWIĄZKOWE z tyłu naczepy >8 m (nasza 13,6 m — tak); samochody ciężarowe DMC >7,5 t **z wyłączeniem ciągnika siodłowego** (nasz ciągnik — nie). Zał. 10: z tyłu, prostopadle i symetrycznie; pasy 45° ±5°, szer. 100 ±2,5 mm, żółty odblaskowy + czerwony fluorescencyjny (poj. samochodowy); naczepa: żółte tło odblaskowe + czerwone obrzeże fluorescencyjne; dolna ≥250, górna ≤2100 mm; ≤400 mm od obrysu; odstęp między tablicami 200–300 mm; wymiary w rysunkach 1–2 (grafika → UNVERIFIED liczbowo; por. R70 zał. 12: 1130–2300 mm).
  - Miejsce tablicy rejestracyjnej (zał. 5 § 2): tylne 520×120 lub 340×240 mm; wysokość dolnej ≥0,30 m, górnej ≤1,20 m (absolutnie ≤2,00 m); pochylenie 5–30° od pionu.
- **Rozporządzenie w sprawie rejestracji i zabezpieczeń pojazdów (Dz.U. 2024 poz. 1709 — akt pierwotny z 8.11.2024, nie tekst jednolity; korekta po przeglądzie s17; zmieniony Dz.U. 2025 poz. 939 (§ 27, 31, 32, zał. 13 — wyróżniki powiatów) i Dz.U. 2026 poz. 891 (§ 2, 6, 7, 18, 19, 20, 21 pkt 1, 22, zał. 13 — pełna lista §§ po korekcie r2) — **żadna z tych zmian nie dotyka zał. 12 (tablice rejestracyjne) ani rysunku 1**):**
  - § 33 ust. 1: pojazd — tablice z przodu i z tyłu; **przyczepy (naczepy) — tylko z tyłu**.
  - Zał. 12: płyta z taśmy aluminiowej 1 mm; kształty wg rysunku 1, odchyłki wymiarów głównych ±1 mm, promień naroży −0,5/+1,5 mm (pkt 2.2). **Wymiary 520×114 mm potwierdzone etykietami wymiarowymi rysunku 1** („520”, „114”; naroża R10, ramka obrzeża 7 mm od krawędzi; dwurzędowa: 305×214 mm) — patrz „Punkty otwarte z przeglądu s17 — wyniki”, punkt (b).
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

- **UNVERIFIED:** liczbowe wymiary tablic wyróżniających z zał. 10 WT rys. 1–2 (grafika; por. wartości R70 zał. 12). Wymiary tablicy rejestracyjnej 520×114 mm z zał. 12 rys. 1 **rozstrzygnięte odczytem etykiet wymiarowych rysunku** (pomiar pikselowy tylko kontrolą) — patrz „Punkty otwarte z przeglądu s17 — wyniki”, punkt (b).
- **OCR (96/53/WE, skan 1996):** spacje w cytatach odtworzone; brzmienie pkt 2.2.2 lit. a potwierdzone paralelnie § 3 ust. 1 pkt 2 WT (Dz.U. 2024 poz. 502). Nie udało się pobrać wersji skonsolidowanej 01996L0053-20190814 (Cellar HTTP 500) — oryginał + 2015/719 wystarczają do pełnej rekonstrukcji brzmienia.
- **ESTIMATED:** brak pozycji ESTIMATED — wszystkie wartości liczbowe pochodzą z aktów prawnych.
- R48 punkt 6.21 (kontur) i R70 zał. 15 — wymagania montażowe „miejsc przewidzianych przez producenta"; dla modelu 3D wystarczą wartości minimalne/maksymalne z manifestu.
- Tachograf cyfrowy: rozporządzenie (UE) 165/2014 + akt wykonawczy (UE) 2016/799 (zał. IC) **nie wskazują miejsca montażu w kabinie** — tylko wymagania dostępności i widoczności dla kierowcy (patrz „Punkty otwarte z przeglądu s17 — wyniki”, punkt (c)); miejsce w modelu 3D = praktyka producentów (ESTIMATED).

## Punkty otwarte z przeglądu s17 — wyniki

Przegląd s17 (`docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p4.md` w main) zostawił trzy punkty otwarte; poniżej wyniki (wszystkie źródła pobrano i sprawdzono 2026-11-13; pełna lista w `sources.md` — „Dokumenty dodane po przeglądzie s17”).

### (a) R46 — czy CMS może zastąpić lusterka klas II i IV (N3)?

**Wynik: TWIERDZĄCY na poziomie regulaminu ONZ — od Suplementu 2 do serii 04 (E/ECE/324/Rev.1/Add.45/Rev.6, wejście w życie 18.06.2016) urządzenie typu kamera-monitor (CMS) może zastąpić lusterka wszystkich klas, w tym II i IV.** Wynik NEGATYWNY rundy 1 był błędny — opierał się wyłącznie na tekście opublikowanym w Dz.U. UE (seria 04 + Suplement 1, 2014) i pomijał suplementy późniejsze. Korekta po ponownym przeglądzie s17 (errata lidera).

- Seria obowiązująca w UE: **04** — potwierdzona w konsolidacie GSR2 z 02.08.2026 (02019R2144), zał. II poz. 46: „Urządzenia widzenia pośredniego i ich instalacja — Seria poprawek 04 — Dz.U. L 237 z 8.8.2014, s. 24”. Rozporządzenie delegowane (UE) 2025/1122 (nowelizacja GSR2) dotyczy regulaminów 25/34/79/100/117/127/152/167/169/171 — **nie R46**.
- Tekst Dz.U. UE L 237 z 8.8.2014 (seria 04 + Suplement 1): pkt 15.2.1.1.2 pozwala zastąpić innym urządzeniem widzenia pośredniego tylko lusterka kl. V (pkt 15.2.4.5) i VI (pkt 15.2.4.6): „Jeżeli pole widzenia lusterka przedniego opisane poniżej w pkt 15.2.4.6 lub lusterka bliskiego zasięgu opisane poniżej w pkt 15.2.4.5 można uzyskać za pomocą innego urządzenia widzenia pośredniego … urządzenie to może być stosowane zamiast wspomnianego lusterka lub lusterek.”
- **Suplement 2 do serii 04** (przygotowany przez grupę IGCMS-II; propozycja ECE/TRANS/WP.29/GRSG/2015/2: „to introduce the optional replacement of mirrors of Classes I to IV by camera-monitor systems”): w wydaniu złożonym E/ECE/324/Rev.1/Add.45/Rev.6 („Supplement 2 to the 04 series of amendments – Date of entry into force: 18 June 2016”) pkt 15.2.1.1.1 przewiduje pola widzenia uzyskane z „minimum number of mandatory mirrors or camera-monitor devices”; wymagania dla „CMS of Classes I to IV” — m.in. pkt 6.2.1.3 („The effectiveness of the CMS of Classes I to IV shall not be adversely affected by magnetic or electrical fields”), pkt 6.2.2 i zał. 12.
- **Status w UE: niepotwierdzony (pewność S).** Suplement 2 nie został opublikowany w Dz.U. UE; zał. II GSR2 przywołuje serię 04 z OJ L 237 z 8.8.2014 (tekst 04 + Suplement 1). Wniosek rundy 1 („dla klas II i IV brak podstawy prawnej”) wycofano.
- Serie 05–07 istnieją na poziomie ONZ (ECE/TRANS/WP.29/GRSG/2025/8 — propozycja serii 07; przyjęcie odnotowane w ECE/TRANS/WP.29/2025/103), ale nie zostały włączone do zał. II GSR2 — w UE bez skutków prawnych.
- Źródła sprawdzone: OJ L 237 z 8.8.2014, s. 24 (CELEX 42014X0808(02)); E/ECE/324/Rev.1/Add.45/Rev.6 (UNECE R046r6e.pdf — pobrano przez web.archive.org, unece.org odrzuca klientów automatycznych); ECE/TRANS/WP.29/GRSG/2015/2; konsolidat GSR2 02.08.2026 (02019R2144 — Cellar); DR (UE) 2025/1122 (CELEX 32025R1122); ECE/TRANS/WP.29/GRSG/2025/8 i ECE/TRANS/WP.29/2025/103 (web.archive.org).
- **Dla modelu:** klasyczne lusterka kl. II i IV — decyzja projektowa; CMS dozwolony przez ONZ od Suplementu 2 do serii 04, ale jego stosowanie w UE nie jest potwierdzone w przepisach UE.

### (b) Rysunek tablicy rejestracyjnej 520×114 mm (rozporządzenie z 8.11.2024, Dz.U. 2024 poz. 1709, zał. 12)

**Wynik: POTWIERDZONY — tablica samochodowa jednorzędowa ma wymiary 520 × 114 mm** (etykiety wymiarowe rysunku 1 zał. 12 — SOURCED; opis metody skorygowany po ponownym przeglądzie s17).

- Tekst (zał. 12 pkt 2.2): „Kształty tablic powinny być zgodne z rysunkiem 1. Wymiary na rysunku podano w mm, maksymalne odchyłki wymiarów głównych (długości i szerokość) wynoszą ±1 mm. Odchyłka promienia zaokrąglenia naroży tablic powinna wynosić od –0,5 do +1,5 mm.”
- **Korekta po ponownym przeglądzie s17:** rysunek 1 **zawiera etykiety wymiarowe „520” i „114”** (pozioma pod tablicą; obrócona 90° przy pionowej linii wymiarowej), a także „R10” (promień naroży) i „7” (odsunięcie ramki obrzeża od krawędzi) — wymiar pochodzi z **odczytu etykiet wymiarowych rysunku** (SOURCED). Pomiar pikselowy osadzonych obrazów rastrowych (obrys tablicy jednorzędowej 1173×257 px przy skali 0,4433 mm/px → 520,1 × 114,0 mm) wykonano **tylko jako kontrolę spójności**; walidacja krzyżowa na tablicy dwurzędowej (etykiety „305”/„214”, skala 0,4446/0,4440 mm/px → 305×214 mm) — zgodność ≤1 %. Dla artysty/modelu 3D: naroża R10, ramka obrzeża 7 mm od krawędzi, tolerancja wymiarów głównych ±1 mm.
- Zmiany aktu (ELI, api.sejm.gov.pl; pełne teksty sprawdzono; lista §§ uzupełniona po ponownym przeglądzie s17): Dz.U. 2025 poz. 939 (w życie 30.07.2025 — § 27, 31, 32, zał. 13: wyróżniki powiatów) i Dz.U. 2026 poz. 891 (w życie 4.07.2026 — **§ 2, 6, 7, 18, 19, 20, 21 pkt 1 uchylony, 22 uchylony, zał. 13**; potwierdzone niezależnym odczytem PDF — § 1 pkt 1–9) — **nie dotykają zał. 12 ani rys. 1** (wymiary, kształty i miejsce montażu tablic bez zmian).
- Źródła sprawdzone: Dz.U. 2024 poz. 1709 (D2024000170901.pdf); Dz.U. 2025 poz. 939; Dz.U. 2026 poz. 891 (dziennikustaw.gov.pl); ELI api.sejm.gov.pl.

### (c) Miejsce montażu tachografu w kabinie (rozporządzenie (UE) 165/2014; akt wykonawczy (UE) 2016/799, zał. IC)

**Wynik: NEGATYWNY — przepis nie wskazuje miejsca montażu w kabinie.** Prawo wymaga tylko dostępności i widoczności dla kierowcy; konkretne miejsce w kabinie to praktyka producentów.

- Zał. IC pkt 5.1, wym. (394): „Urządzenie rejestrujące musi być umieszczone w pojeździe w taki sposób, aby kierowca miał ze swojego siedzenia dostęp do niezbędnych funkcji.”
- Zał. IC, wym. (186): „Ostrzeżenia wizualne muszą być łatwo rozpoznawalne przez użytkownika, znajdować się w polu widzenia kierowcy i być łatwe do odczytania tak w dzień, jak i w nocy.”
- Zał. IC pkt 5.2, wym. (395): tabliczka instalacyjna „dobrze widoczna i łatwo dostępna” na urządzeniu, a gdy to niemożliwe — słupek „B” lub framuga drzwi po stronie kierowcy.
- Cytaty wg tekstu skonsolidowanego PL 02016R0799 (konsolidacja z 21.08.2023, seria 003.002; pobrano z Cellar — publications.europa.eu/resource/celex/02016R0799).
- Źródła sprawdzone: 02016R0799 PL (Cellar, XHTML); rozporządzenie (UE) 165/2014 (CELEX 32014R0165).
- **Dla modelu 3D:** tachograf w typowym miejscu deski rozdzielczej (np. gniazdo DIN) — ESTIMATED (praktyka), nie wymóg prawny.

## Korekty po przeglądzie s17

Zgodnie z §4 przeglądu (`docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p4.md`) naniesiono:

1. **P4-134:** usunięto „22,5 t/oś przy 38 t” (wartość nieobecna w 96/53/WE); właściwy limit dla zespołu osi trójosiowej naczepy przy 1,3 < d ≤ 1,4 m: **24 t na zespół osi** (zał. I pkt 3.3.2: „1,3 < d ≤ 1,4 — 24 tony”).
2. **P4-133 / README §5:** oś napędowa 11,5 t — poprawiony numer punktu **3.4.2 → 3.4.1** („Oś napędowa pojazdów ... 11,5 tony”).
3. **README §5 / P4-137:** pełna lista nowelizacji 96/53/WE (2002/7/WE; 2015/719; Decyzja (UE) 2019/984; Rozporządzenie (UE) 2019/1242 — do +2 t dla pojazdów bezemisyjnych); wpływ na nasz zestaw: **40 t bez zmian** (diesel).
4. **P4-160…167, P4-170 / sources.md:** Dz.U. 2024 poz. 1709 opisany jako **akt pierwotny** z 8.11.2024 (nie t.j.), zmieniony Dz.U. 2025 poz. 939 i Dz.U. 2026 poz. 891 — bez zmian zał. 12.
5. **P4-073–076 / README §2:** etykieta R104: **wersja pierwotna regulaminu** (Rev.2/Add.103/Rev.1, 2010), nie „seria poprawek 01”; znak „TOP” — warunek materiału nieomnirotacyjnego (pkt 4.1.2).
6. **P4-093 / README §3:** lusterko kl. V dla N3 pozostaje w wersji pierwotnej (1 obowiązkowe po stronie pasażera + 1 opcjonalne po stronie kierowcy, montaż ≥2 m) — doprecyzowano punkt tabeli: **15.2.1.1.1, wiersz N3**.

Uwaga numeracyjna: przegląd podaje tabelę jako „15.2.1.1.2”; w pobranym pełnym tekście OJ L 237 z 8.8.2014 (PL) tabela obowiązkowych klas lusterzek to pkt 15.2.1.1.1 (str. L 237/43), a pkt 15.2.1.1.2 (str. L 237/44) zawiera postanowienie o zastępowaniu lusterzek kl. V/VI urządzeniami typu kamera-monitor — użyto numeracji z OJ.

## Korekty po ponownym przeglądzie s17 (runda 2 — errata lidera)

Ponowny przegląd (sekcja „Ponowny przegląd po M44-FIX (s17)” w `docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p4.md`) dał werdykt „NADAL DO POPRAWY” — 1 błąd merytoryczny (punkt a) + 1 drobny (niepełna lista §§ Dz.U. 2026/891); errata lidera: `REVIEW-NOTE.md` (origin/main). Naniesiono:

1. **CMS zamiast klas II/IV (README §3, „Punkty otwarte” (a), uwagi P4-093):** wynik NEGATYWNY rundy 1 był błędny (opierał się tylko na tekście OJ z 2014 r. i pomijał suplementy). **Suplement 2 do serii 04** (E/ECE/324/Rev.1/Add.45/Rev.6, wejście w życie **18.06.2016**; propozycja ECE/TRANS/WP.29/GRSG/2015/2) dopuszcza zastąpienie lusterek **klas I–IV przez CMS, w tym II i IV** (pkt 15.2.1.1.1 wydania złożonego; wymagania „CMS of Classes I to IV” — pkt 6.2.1.3, 6.2.2, zał. 12). Status w UE: **niepotwierdzony** (Suplement 2 nieopublikowany w Dz.U. UE; OJ obejmuje tylko 04 + Suplement 1) — pewność **S**; dla modelu lusterka (decyzja projektowa).
2. **Pełna lista zmian Dz.U. 2026 poz. 891 (README §6, punkt (b), sources.md, wersja_przepisu P4-160–167 i P4-170):** **§ 2, 6, 7, 18, 19, 20, 21 (pkt 1 uchylony), 22 (uchylony), zał. 13** (tabela województw/powiatów — wyróżniki) — runda 1 podawała tylko § 2, 6, 7, 18, 19. **Zał. 12 i rys. 1 bez zmian** — potwierdzone pełnotekstowo (ELI + niezależny odczyt PDF: § 1 pkt 1–9).
3. **Opis metody dla 520×114 mm (punkt (b), P4-162):** wymiar pochodzi z **odczytu etykiet wymiarowych rys. 1** („520”, „114”; dodatkowo „R10” — promień naroży, „7” — odsunięcie ramki obrzeża) — SOURCED; pomiar pikselowy tylko jako kontrola spójności. Dla artysty: naroża R10, ramka 7 mm, tolerancja ±1 mm.
4. **P4-134 (drobiazg):** `warunek` doprecyzowany — zał. I pkt 3.3 („Trzyosiowe przyczepy i naczepy”) dotyczy zespołu trzech osi przyczep i naczep ogółem, nie tylko zestawów z pkt 2.2.2; usunięto zbędny nawias w uwagach.

## Samokontrola (audyt)

- **Seed:** 20261113 · **Populacja:** 171 · **Próba:** 43 (25,1 % ≥ wymagane 20 %)
- **Wynik:** 42 PASS, 0 FAIL, 1 SKIPPED (wiersz weryfikacji negatywnej — bez cytatu; adnotacja w JSON)
- **Metoda:** porównanie znormalizowane (lowercase, bez diakrytyków, tylko znaki alfanumeryczne — eliminuje wpływ twardych spacji U+00A0, łamania wierszy i sklejonego OCR) każdego segmentu cytatu (separator „…") z pełnym tekstem oficjalnego dokumentu; limit ≤25 słów; potwierdzenie aktualności aktu (t.j./seria poprawek przywołana w GSR2 z 07.07.2024).
- **Korekta po przeglądzie s17 (2026-11-13):** pierwotna deklaracja „pełna weryfikacja 171/171 — 0 niezgodności” była **zawyżona** (przegląd: próba 35 wierszy — 32 potwierdzone, 1 odrzucony [P4-134], 2 niesprawdzone [P4-148, P4-168]). Poprawki opisano w polu `korekty_po_przegladzie_s17` w `audit_20_percent.json` i w sekcji „Korekty po przeglądzie s17” w README.
- **Runda 2 (errata lidera, 2026-11-13):** korekty z ponownego przeglądu s17 opisano w polu `ponowny_przeglad_s17_r2` w `audit_20_percent.json` i w sekcji „Korekty po ponownym przeglądzie s17” (źródła r2: R46 Rev.6 — UNECE R046r6e.pdf; Dz.U. 2026 poz. 891 — niezależny odczyt PDF).

## Struktura

```
research/mistral/p4-truck-regulations/
├── README.md            (ten plik)
├── manifest.csv          (171 wierszy, UTF-8, separator „;”)
├── sources.md            (pełna lista źródeł z URL i licencjami)
├── audit_20_percent.json (samokontrola: seed 20261113, 43 pozycje)
```

**PDF-y:** wszystkie cytowane dokumenty pobrano 2026-11-13; binarna publikacja załączników przez dostępny konektor GitHub App nie jest wykonalna (konektor przesyła wyłącznie treść tekstową — pliki binarne uległyby uszkodzeniu), więc w repozytorium znajdują się wyłącznie pliki tekstowe, a każdy PDF jest dostępny pod oficjalnym adresem URL w `sources.md` (dokumenty ≤ 5 MB i > 5 MB jednolicie jako linki).
