# P18 — jak NAPRAWDĘ brudzi się tył naczepy (firanka 13,6 m, drzwi dwuskrzydłowe)

**Gałąź:** `research/mistral-p18-trailer-soiling` (z najnowszego `origin/main` @ b67b949d, 2026-11-13)
**Autor badania:** Vibe (Mistral), paczka M61/P18
**Data:** 2026-11-13

Badanie dla naczepy fikcyjnej BEZ MARKI: firanka 13,6 m, dwuskrzydłowe tylne drzwi (biała blacha/sklejka w ramie), belka RUPD, lampy zespolone, taśmy odblaskowe. Cel: materiał referencyjny, jak realnie wygląda zabrudzenie tyłu naczep na polskich drogach — mechanizm, strefy, barwa i faktura (lato/zima), kadr referencyjny dla artysty.

**Zdjęcia NIE są w repo:** katalog `files/` jest ignorowany (`.gitignore`); archiwum **`mistral-p18-trailer-soiling-files.zip`** dostarczono poza git — nazwa, rozmiar i sha256 w opisie PR.

**Status (2026-11-13):** sekcje 1-2 (literatura) kompletne; sekcje 3-5 wypełnione pierwszą iteracją analizy kadrów (24 kandydatów, 17 kwalifikujących, 4 zimowe); cel ≥20 kadrów — pozostało dołóżenie ≥3 kadrów w kolejnej iteracji (budżet analizy obrazów).

---

## 1. Mechanizm (literatura)

### 1.1 Skąd bierze się brud na tylnych drzwiach

Tył naczepy jest brudzony niemal wyłącznie **samozabrudzeniem (self-soiling)**: wodą z filmu na jezdni, rozbryzgiwaną przez **koła zestawu** (głównie tylne koła naczepy), która w postaci sprayu jest wciągana w **worek recyrkulacyjny za naczepą** i osadza się na powierzchni tylnej. Woda niesie zawiesinę: pył drogowy, TRWP (cząstki zużycia opony i nawierzchni), zimą sól i piasek z posiółki.

Kluczowe mechanizmy wg literatury (pełne cytaty w `manifest.csv` i `sources.md`):

- **Koła tylne dominują**: „The rear tyres are seen to be the dominant source, with front wheel spray… only making small relative contributions" (SAE 2014-01-0610, symulacja SUV walidowana w tunelu klimatycznym; DOI 10.4271/2014-01-0610). Dla naczepy analogicznie: koła tandemu naczepy są tuż pod progiem tylnym.
- **Wyrzut wody z opony** działa czterema mechanizmami wg Weira: „bow wave, side splash wave, tread pickup and capillary adhesion" (JWEIA 2019, DOI 10.1016/j.jweia.2018.11.024, abstrakt; klasyfikacja za Weir et al. 1978, badania HGV).
- **Transport na tył**: za bryłą tylną powstają „strong large-scale recirculating vortices… [that] advect the spray and deposit" (JWEIA 2017, DOI 10.1016/j.jweia.2017.05.007 wg indeksu; fragment abstraktu) — dlatego film brudu pojawia się na powierzchni drzwi, nie tylko na krawędziach.
- **Balistyka vs. entrainment**: „Large particles are found to take on a ballistic trajectory and penetrate the wake", „small particles… are less likely to become entrained into the wake" (SAE 2016-01-1604, Windsor body; DOI 10.4271/2016-01-1604, open access). Duże krople (błoto, piasek) lecą nisko i daleko — trafiają próg i belkę; drobny aerozol wnosi się w wir, ale osadza się głównie w dolnej części powierzchni tylnej.
- **Prędkość i mokra nawierzchnia**: warunkiem sprayu jest film wody na jezdni; program FHWA (Weir, Strange, Heffley 1978, FHWA-RD-79-84) charakteryzował „truck splash and spray generation and propagation" w testach simulatorowych, tunelowych i full-scale — intensywność rośnie z prędkością i grubością filmu wody. Na suchej nawierzchni tył brudzi się głównie drobinowym pyłem w wirze (wolno, jednorodnie).
- **Osłony anty-spray** (dyrektywa 91/226/EWG dla N2/N3/O2-O4) ograniczają lateralny rozbryzg kół, ale **nie osłaniają powierzchni tylnej naczepy** — tył drzwi pozostaje w pełni eksponowany (przywołane, patrz sources.md §2).

### 1.2 Tabela: strefa → intensywność względna → źródło → status

| Strefa tyłu | Intensywność względna | Źródło | Status |
|---|---|---|---|
| **Próg dolny (probelka / dolna listwa drzwi)** | **NAJWYŻSZA** — bezpośrednia strefa zasięgu balistycznego sprayu kół naczepy (duże krople, piasek zimą) | SAE 2014-01-0610 (tylne koła dominują); SAE 2016-01-1604 (czynniki balistyczne) | Udokumentowane pośrednio (SUV/Windsor; ekstrapolacja geometrii na naczepę) |
| **Belka RUPD (pod progiem)** | **NAJWYŻSZA** — najbliżej jezdni, w zasięgu splash i filmu wody; maluje się pierwsza i najmocniej | jw. + spływ z błotników kół | Ekstrapolacja z literatury; potwierdzenie kadrów — patrz §3-4 |
| **Lampy zespolone (nad progiem)** | **WYSOKA** — w strefie filmu dolnego; zabrudzenie degraduje światło i kamery | Gaylard 2019 („can compromise… sensor performance") | Udokumentowane dla lamp/kamer |
| **Dolna część drzwi (od progu do ~40-50% wysokości)** | **WYSOKA, malejąca z wysokością** — film jednolity z aerozolu recyrkulacyjnego | JWEIA 2017 (wiry advectują spray); SAE 2016 (drobne entrained) | Udokumentowane jakościowo; liczby z kadrów — patrz §4 (ESTIMATED) |
| **Górna połowa drzwi** | **NISKA** — pojedyncze zacieki z krawędzi dachu/panelu i rygli, brak filmu | SAE 2016 (małe cząstki mniej entrained) | Udokumentowane pośrednio |
| **Uszczelka środkowa / rygle / zawiasy** | **ŚREDNIA** — zacieki startują w punktach zakłócenia przepływu i skroplin (rygle, zawiasy, narożniki); wycieki skoncentrowane na styku skrzydeł | mechanika filmu wody (Gaylard 2019); kształt z kadrów | Kształt: ESTIMATED z kadrów — §3-4 |
| **Klamry/uchwyty/rygle (strefy dotykowe)** | **WYTARTE** — frajerski kontrast: brud wszędzie, ale uchwyty czystsze (używane przez kierowców) | brak w literaturze | ESTIMATED z kadrów — §3 |
| **Taśmy odblaskowe (kontur)** | Brud osiada na nich jak na blasze, ale gdy są wypukłe/wytarte — jaśniejsze pasy | brak w literaturze | ESTIMATED z kadrów |

### 1.3 Rozkład zabrudzenia z wysokością

W literaturze dostępnej otwarcie (abstrakty SAE/JWEIA, rozprawa Gaylarda) **nie znaleziono liczb „% pokrycia vs wysokość nad jezdnią"** dla naczep 13,6 m — schematy pokrycia w publikacjach to mapy konturowe (mocna dolna krawędź, gradient malejący z wysokością). Jakościowo: „The rear surfaces of blunt-ended vehicles… are vulnerable to the build-up of contaminants thrown up from wet road surfaces by their tyres" (Gaylard 2019). Liczbowe oszacowanie górnej granicy „filmu dolnego" dla naczepy — **ESTIMATED z kadrów, patrz §4 (z metodą)**.

### 1.4 Wpływ prędkości i nawierzchni

- **Mokra nawierzchnia + 80-90 km/h** = maksymalne samozabrudzenie tyłu (spray kół + wir). Na suchej nawierzchni tył brudzi się powoli, drobinowo (pył/sadza), równomiernie.
- **Zima (sól/posiółka)**: film wody jest słony — po wyschnięciu zostaje **biały/szary osad krystaliczny + ciemne zabrudzenie mineralne** (patrz §2).
- Brake/wydech nie mają wpływu na tył naczepy (zamontowane na ciągniku).

---

## 2. Barwa i faktura osadów (Polska, lato vs zima)

### 2.1 Lato (pył drogowy)

**Opis słowny:** szaro-beżowy, matowy, drobnoziarnisty nalot; na białej blasze wygląda jak przyciemnienie o odcieniu „kawy z mlekiem po rozcieńczeniu"; w dolnych strefach mocniejszy — szaro-brązowy. TRWP (cząstki zużycia opony i nawierzchni) dodają chłodny, ciemnoszary/grafitowy ton.

**Podstawa:** pył drogowy to „primarily composed of quartz, but also of muscovite, albite, kaolinite, microcline, Fe-enstatite, graphite and amorphous content" (IJERPH 2020, DOI 10.3390/ijerph17051563) — dominacja jasnego kwarcu i minerałów warstwowych tłumaczy beżowo-szarą barwę, a grafit i amorficzne (sadza) — ciemniejsze żyły. TRWP: praca „Shades of grey" (Frontiers 2023, DOI 10.3389/fenvs.2023.1258922).

**Wartości liczbowe z literatury:** brak dostępnych otwartych danych o albedo/CIELAB/Munsell letniego osadu drogowego na pojeździe (luka — patrz §6). Nie podajemy tu żadnych liczb.

### 2.2 Zima (sól + pośniegowe błoto)

**Opis słowny:**
- **Świeże zabrudzenie (mokra jazda po solonej jezdni):** ciemnoszare do oliwkowo-brązowego „błota pośniegowego" — mieszanina roztworu soli, czarnego topniejącego śniegu przydrożnego i pyłu; na białej blasze wygląda jak brudnosszary, półprzezroczysty film z wyraźnymi kropkami (rozbryzg) na dole.
- **Po wyschnięciu:** matowy, jasnoszary do **białego** nalot krystalicznego residuum solnego (linie i „wymyte" pasy tam, gdzie woda spływała), miejscami z ciemniejszym rdzawym nalotem przy elementach stalowych (zardzewiałe śruby, zawiasy, belka) — sól przyspiesza korozję.
- **Silny mróz (poniżej ok. -7°C):** sól przestaje działać; zabrudzenie bardziej mineralne, szorstkie (piasek/posiółka), mniej filmowe.

**Podstawy liczbowe (tylko ze źródeł):**
- Sól drogowa w Polsce: „chlorek sodu (NaCl) o czystości min. 90% (najczęściej 94-97%)", gatunki DA/DR, antyzbrylacz 20-50 ppm; skuteczna do -7°C (eutektyk -21,1°C) — surowceprzemyslowe.pl (źródło branżowe, orientacyjne; P18-014/017).
- Mieszanki sól-piasek w PL: 20/80 (chodniki) do 100% soli (drogi krajowe GDDKiA) — im niższa klasa drogi, tym jaśniejszy/szorstki osad piaskowy (P18-015).
- Dawki soli: 10-40 g/m² zależnie od temperatury (P18-016).
- Zabrudzony śnieg ciemnieje: redukcja albedo „reached up to 0.13, 0.21, and 0.25 for red algal blooms, mineral dust, and dark particles respectively" (The Cryosphere 2025, DOI 10.5194/tc-19-1527-2025; P18-018).
- „Of the de-icing agent spread by the Hokkaido Regional Development Bureau, 99% is chloride-based" — i poniżej ok. -8°C stosuje się piasek/posiółkę (Infra Intelligence; P18-019).

### 2.3 Implikacja artystyczna (barwa/faktura, lato vs zima)

- **Lato:** spójny, jednolity film w dolnej połowie + mało zacieków; kolor szaro-beżowy z oliwkowym odcieniem; mikro-drobinki (szum) zamiast plam.
- **Zima:** mocniejszy kontrast — ciemnoszaro-oliwkowy film + **białe residuum solne** (po wyschnięciu) w strefach spływu + rdzawe przybłyski na elementach stalowych + szorstki piasek w dolnej strefie; zacieki liczniejsze i dłuższe (częste cykle mokro/sucho z solą).

---

## 3. Kadry — obejrzane i opisane (analiza wizyjna, Wikimedia Commons)

**Zbadano 24 kandydatów** (miniatury 1280 px, Commons; każda analiza zapisana lokalnie jako `analysis_P18-1NN.json`; surowe odpowiedzi modelu wizyjnego). Status na 2026-11-13:

- **Kwalifikują się (widoczny tył/drzwi naczepy): 17/24** — P18-101, 102, 103, 104, 107, 108, 109, 110, 111, 112, 116, 117, 118, 119, 120, 121, 122.
  - w tym **zimowe: 4** (P18-112 z widocznym śniegiem, P18-120, P18-121, P18-122) oraz **2 kadry fabrycznie czyste** jako odniesienie kontrastowe (P18-110, P18-111 — MAN Concept/Krone) i 1 niemal czysty (P18-107, BANEX).
- **Odrzucone: 7** (P18-105, 106 — widok boczny; P18-113 — cysterna z góry; P18-114 — brak tyłu; P18-115 — wywrotka; P18-123 — cysterna bok; P18-124 — bok).
- **Uwaga metodologiczna (uczciwie):** budżet narzędzia analizy obrazów (20 wywołań na odpowiedź) wyczerpał się po 24 kadrach; **cel ≥20 kadrów kwalifikujących nie został jeszcze osiągnięty (17/20)**. Przygotowano dodatkowo 12 kandydatów (pobrane miniatury + metadane w stanie badania; m.in. zimowy „Semi truck in the snow Church Avenue Jan 2026", zestawy polskie: Renault T/Orlen Wichrów, Biedronka Białystok, JAS-FBG, Mlekovita, Actros) — do przeanalizowania w kolejnej iteracji.

Wszystkie kadry: **Wikimedia Commons**, licencje CC0/CC BY/CC BY-SA/PD → **status REFERENCJA** (do patrzenia, nie do użycia jako tekstura w grze); marki widoczne na zdjęciach — wyłącznie „marka widoczna, tylko referencja". Zakaz Google Maps/Street View zachowany.

Pełne dane kadrów (strefy, zacieki, krycie, barwa, licencja, autor) — wiersze `kadr` w `manifest.csv` (P18-101…P18-124).

## 4. Zestawienie liczbowe z kadrów (ESTIMATED, z metodą)

Liczby pochodzą wyłącznie z analizy kadrów i są **ESTIMATE**; metoda podana przy każdej. n = 17 kwalifikujących kadrów.

| Parametr | Wartość | n | Metoda |
|---|---|---|---|
| Górna granica „filmu dolnego" — **mediana** | **0,3 wysokości drzwi ≈ 0,78–0,81 m nad jezdnią** (przy drzwiach 2,6–2,7 m) | 11 kadrów z filmem > 0 | ułamek wysokości drzwi widocznej w kadrze (ESTIMATE z analizy wizyjnej); zakres 0,1–0,8 |
| …dla kadrów zimowych — mediana | 0,3 (max **0,8** — kadr P18-112, śnieg) | 4 | jw. |
| Zacieki pionowe na skrzydło — mediana | **lewe: 3, prawe: 2** | 14/12 kadrów z danymi | liczenie wyraźnych pionowych śladów (ESTIMATE); zakres 0–6 |
| Odsetek kadrów z brudnym progiem (ŚREDNIO/MOCNO) | 10/17 ≈ **59%** | 17 | ocena strefy z kadrów |
| Odsetek z brudną belką RUPD (ŚREDNIO/MOCNO) | 14/17 ≈ **82%** | 17 | ocena strefy z kadrów — **belka maluje się najczęściej** (zgodnie z §1.2) |
| Odsetek z brudnymi lampami | 9/17 ≈ **53%** (zawsze tylko LEKKO) | 17 | ocena strefy z kadrów — lampy brudzą się najmniej ze stref dolnych |
| Dolna część drzwi MOCNO zabrudzona | 11/17 ≈ **65%** | 17 | ocena strefy z kadrów |
| Górna połowa drzwi MOCNO | 1/17 ≈ 6% (tylko kadr zimowy P18-112) | 17 | potwierdza gradient z literatury (§1.2–1.3) |
| Stan czysty (film = 0) | 3/17 (2 kadry pojazdów koncepcyjnych/prezentacyjnych + 1 świeżo umyty) | 17 | punkt odniesienia „jak wygląda czysty tył" |

Wnioski: potwierdzono jakościowo rozkład z literatury — **belka RUPD i próg najbrudniejsze (59–82%), film dolny sięga medianie ~0,3 wysokości drzwi (~0,8 m), góra drzwi prawie czysta latem**; zimą film może sięgać 0,8 wysokości (P18-112). Zacieki: typowo 2–3 na skrzydło, częściej na lewym (lewe skrzydło otwierane częściej → starty brud od uchwytów mógł „rozmywać" ślady — hipoteza do weryfikacji).

## 5. Pięć najlepszych kadrów dla artysty

1. **P18-112** (MB 1850, Sinsheim, zima, CC0) — zimowy film na **całych** drzwiach (granica 0,8), śnieg w kadrze: referencja maksymalnego zimowego samozabrudzenia.
2. **P18-101** (LKW-Sattezug Rückseite, PD) — klasyczny film dolny + kropki rozbryzgowe na progu, czyste lampy/taśmy: „typowy dzień po deszczu".
3. **P18-109** (Kögel, Dnipro) — mocny osad + rdza na ryglach/uchwytach: referencja „zapuszczonego" zestawu, strefy dotykowe wytarte kontrastowo.
4. **P18-108** (Schneider) — film 0,2 wysokości drzwi + 3–4 zacieki na skrzydło: „statystyczny" profil letni (najbliższy medianie).
5. **P18-110/111** (MAN Concept/Krone, CC0) — tył fabrycznie czysty: baza pod nakładanie zabrudzenia (odwrotność — co dokładnie jest brudzone).

## 6. Luki i ograniczenia

1. **Brak otwartych liczb „pokrycie vs wysokość" dla naczep** — literature dotyczy SUV/Windsor body i ogólnych brył; mapy konturowe nieupublicznione w abstraktach. Więc rozkład wysokościowy liczony ESTIMATED z kadrów (§4).
2. **Brak otwartych danych CIELAB/Munsell/albedo letniego osadu drogowego na pojazdach** — barwa opisana słownie z mineralogii (kwarc/grafit/sadza/TRWP); albedo podane tylko dla śniegu z LAP.
3. **Dane o soli PL z portalu branżowego** (nie recenzowanego) — traktować jako orientacyjne; GDDKiA (gov.pl) zablokowała automatyczny pobór (2026-11-13).
4. **Panoramax: brak danych dla Polski** (bbox Warszawa = 0 wyników); **KartaView: API bez klucza nie zwróciło danych** (2026-11-13) — kadry tylko z Commons/Openverse.
5. **Openverse** — mimo zapytań („lorry rear", „truck rear view" itd.) brak użytecznych kadrów tylnych drzwi naczep (przeważnie zabytki i martwe zapytania; często 504 API).
6. **Ekstrapolacja SUV→naczepa**: mechanizmy fizyczne te same (bryła tylna, spray kół tylnych), ale skala stref (belka RUPD, drzwi 2,6 m) wymaga potwierdzenia kadrów.
