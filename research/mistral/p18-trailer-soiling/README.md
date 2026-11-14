# P18 — jak NAPRAWDĘ brudzi się tył naczepy (firanka 13,6 m, drzwi dwuskrzydłowe)

**Gałąź:** `research/mistral-p18-trailer-soiling` (z najnowszego `origin/main` @ b67b949d, 2026-11-13)
**Autor badania:** Vibe (Mistral), paczka M61/P18
**Data:** 2026-11-13 (init), aktualizacja kadrów: 2026-11-14

Badanie dla naczepy fikcyjnej BEZ MARKI: firanka 13,6 m, dwuskrzydłowe tylne drzwi (biała blacha/sklejka w ramie), belka RUPD, lampy zespolone, taśmy odblaskowe. Cel: materiał referencyjny, jak realnie wygląda zabrudzenie tyłu naczep na polskich drogach — mechanizm, strefy, barwa i faktura (lato/zima), kadr referencyjny dla artysty.

**Zdjęcia NIE są w repo:** katalog `files/` jest ignorowany (`.gitignore`); archiwum **`mistral-p18-trailer-soiling-files.zip`** dostarczono poza git — nazwa, rozmiar i sha256 w opisie PR.

**Status:** dokument roboczy — sekcje 1-2 (literatura) kompletne; §3-4 częściowo (5/20 zakwalifikowanych kadrów, dalsze commity); §5 po kompletacji; §6 luki.

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

## 3. Kadry (cel: ≥ 20) — oglądane i opisane

Każdy kadr obejrzany narzędziem wizyjnym (opis „co widać" w kolumnie `opis_co_widać` manifestu); marki widoczne na zdjęciach traktowane wyłącznie jako „marka widoczna, tylko referencja"; CC BY-SA = „referencja, nie tekstura"; NC/ND/płatne stocki = link „tylko referencja, nie pobrano". Zdjęcia wyłącznie z Wikimedia Commons (Openverse/Panoramax/KartaView: patrz §6).

**Stan: 5/20 zakwalifikowanych kadrów tylnych drzwi** (P18-105, P18-107, P18-108, P18-109, P18-118); dodatkowo 15 kandydatów przeanalizowanych i odrzuconych (pełne wiersze z uzasadnieniem w `manifest.csv`, P18-101…P18-120). Dobór kolejnych kadrów trwa — kolejne commity.

### 3.1 Zakwalifikowane kadry (pełne dane: `manifest.csv`)

| id | Sezon | Strefy najbrudniejsze | Kształt brudu | Zacieki/skrzydło | Krycie | Kolor | Licencja / status |
|---|---|---|---|---|---|---|---|
| P18-105 (MB 1850 + naczepa, FULDA) | zima (styczeń) | próg → belka RUPD → dół drzwi → uszczelka → rygle | rozbryzg kropel + pionowe zacieki od zawiasów (~30% wysokości drzwi) | 3 | średnie | szary | CC0 / OK |
| P18-107 (naczepa BANEX, PL→GR) | lato | próg → belka RUPD → dół drzwi | rozbryzg kropel | brak | słabe | szary | CC BY-SA 4.0 / REFERENCJA |
| P18-108 (przewóz drobiu, PL, KRONE) | jesień | próg → belka RUPD → dół drzwi → rygiel → uszczelka | rozbryzg kropel + zacieki od zawiasów i krawędzi dachu (~30%) | 3 | średnie | szaro-czarny | CC BY-SA 4.0 / REFERENCJA |
| P18-109 (Volvo FH420 + naczepa) | lato | próg → belka RUPD → dół drzwi → uszczelka → rygle | rozbryzg kropel | brak | średnie | szary | CC BY-SA 4.0 / REFERENCJA |
| P18-118 (chłodnia + TrailerTail, drzwi otwarte) | zima (grudzień, błoto pośniegowe) | próg → belka RUPD → dół drzwi | rozbryzg kropel | brak | średnie | szary | CC BY-SA 3.0 / REFERENCJA |

Wspólny wzorzec (5 kadrów): brud koncentryczny **od dołu** (próg, belka RUPD, dół drzwi), rozbryzg kropel jako dominująca faktura; pionowe zacieki (3/skrzydło) startują od zawiasów/krawędzi dachu; górna połowa drzwi czysta. Zgodne z mechanizmem §1 (balistyka dużych cząstek nisko, entrainment drobnych nisko-średnio).

### 3.2 Kandydaci odrzuceni (przeanalizowani, z powodów)

P18-101 (naczepa niskoramienna, brak drzwi), P18-102 (kadr z wystawy, drzwi niewyraźne — do ponownej oceny w audycie), P18-103 (tipper bez drzwi), P18-104 (drzwi niewyraźne w 1280 px — do audytu), P18-106 (cysterna), P18-110 (concept truck targowy — przydatny jako wzór czystego tyłu), P18-111 (zimowy tył, ale drzwi niewyraźne wg wizji — do audytu), P18-112 (oldtimer), P18-113 (cysterna), P18-114 (widok boczny), P18-115 (tył poza kadrem), P18-116 (tył kabiny bez naczepy), P18-117 (sam ciągnik, zimowy kontekst), P18-119 (bok kurtynowej — dowód bocznego brudzenia firany: 3 zacieki/skrzydło od góry, ~80% wysokości), P18-120 (bok).

## 4. Zestawienie liczbowe z kadrów

**DANE CZĘŚCIOWE (n=5 zakwalifikowanych; stan na 2026-11-14, uzupełniane po sięgnięciu 20 kadrów):**

- **Mediana liczby zacieków na skrzydło: 3** (obserwacje: 3, 3, brak, brak, brak — zacieki pojawiają się w ~2/5 kadrów; ESTIMATED z opisów wizyjnych, id kadrów: P18-105, P18-108).
- **Odsetek kadrów z brudnym progiem: 5/5 (100%)**; **belką RUPD: 5/5 (100%)**; lampy: 0/5 (w żadnym kadrze lampa nie wskazana jako strefa brudna).
- **Dolna część drzwi brudna: 5/5 (100%)**; uszczelka środkowa/rygle wskazane w 3/5.
- **Typowa długość zacieków: ~30% wysokości drzwi → ESTIMATED ok. 0,8 m** (metoda: wizja podaje długość zacieków w % wysokości drzwi; przyjęto typową wysokość drzwi naczepy **2,65 m** [zakres 2,6-2,7 m]; 0,30 × 2,65 m ≈ 0,80 m; id kadrów: P18-105, P18-108).
- **Górna granica „filmu dolnego" (jednolitego rozbryzgu): dół drzwi, tj. strefa progu/belki + dolna partia skrzydeł** — w 5/5 kadrach film nie przekracza dolnej ~1/3 drzwi; górna połowa czysta. ESTIMATED: film dolny sięga ok. 0,8-1,0 m nad próg (jak wyżej).

Wszystkie liczby z kadrów są **ESTIMATED** (opisy narzędzia wizyjnego na miniaturach 1280 px; proporcje pikselowe przeliczone przez model wizyjny, nie mierzone pikselowo w edytorze); nie są to pomiary.

## 5. Pięć najlepszych kadrów dla artysty

**W TRAKUJE UZUPEŁNIANIA.**

## 6. Luki i ograniczenia

1. **Brak otwartych liczb „pokrycie vs wysokość" dla naczep** — literature dotyczy SUV/Windsor body i ogólnych brył; mapy konturowe nieupublicznione w abstraktach. Więc rozkład wysokościowy liczony ESTIMATED z kadrów (§4).
2. **Brak otwartych danych CIELAB/Munsell/albedo letniego osadu drogowego na pojazdach** — barwa opisana słownie z mineralogii (kwarc/grafit/sadza/TRWP); albedo podane tylko dla śniegu z LAP.
3. **Dane o soli PL z portalu branżowego** (nie recenzowanego) — traktować jako orientacyjne; GDDKiA (gov.pl) zablokowała automatyczny pobór (2026-11-13).
4. **Panoramax: brak danych dla Polski** (bbox Warszawa = 0 wyników); **KartaView: API bez klucza nie zwróciło danych** (2026-11-13) — kadry tylko z Commons/Openverse.
5. **Openverse** — mimo zapytań („lorry rear", „truck rear view" itd.) brak użytecznych kadrów tylnych drzwi naczep (przeważnie zabytki i martwe zapytania; często 504 API).
6. **Ekstrapolacja SUV→naczepa**: mechanizmy fizyczne te same (bryła tylna, spray kół tylnych), ale skala stref (belka RUPD, drzwi 2,6 m) wymaga potwierdzenia kadrów.
