# P18 — jak NAPRAWDĘ brudzi się tył naczepy (firanka 13,6 m, drzwi dwuskrzydłowe)

**Gałąź:** `research/mistral-p18-trailer-soiling` (z najnowszego `origin/main` @ b67b949d, 2026-11-13)
**Autor badania:** Vibe (Mistral), paczka M61/P18
**Data:** 2026-11-13 (init), aktualizacja kadrów: 2026-11-14

Badanie dla naczepy fikcyjnej BEZ MARKI: firanka 13,6 m, dwuskrzydłowe tylne drzwi (biała blacha/sklejka w ramie), belka RUPD, lampy zespolone, taśmy odblaskowe. Cel: materiał referencyjny, jak realnie wygląda zabrudzenie tyłu naczep na polskich drogach — mechanizm, strefy, barwa i faktura (lato/zima), kadr referencyjny dla artysty.

**Zdjęcia NIE są w repo:** katalog `files/` jest ignorowany (`.gitignore`); archiwum **`mistral-p18-trailer-soiling-files.zip`** dostarczono poza git — nazwa, rozmiar i sha256 w opisie PR.

**Status:** BADANIE KOMPLETNE (2026-11-14) — sekcje 1-6 kompletne; **21 zakwalifikowanych kadrów tylnych drzwi** (cel ≥20 osiągnięty), 44 kandydatów odrzuconych z uzasadnieniami; audyt powtarzalności 20% (§4.1, `audit_20_percent.json`).

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

**Stan: 21/20 zakwalifikowanych kadrów tylnych drzwi (cel osiągnięty)** — P18-104, P18-105, P18-107, P18-108, P18-109, P18-111, P18-118, P18-121, P18-133, P18-136, P18-137, P18-138, P18-139, P18-140, P18-153, P18-154, P18-155, P18-156, P18-157, P18-158, P18-159; dodatkowo **44 kandydatów przeanalizowanych i odrzuconych** (pełne wiersze z uzasadnieniem w `manifest.csv`, P18-101…P18-168). Cztery kadry zakwalifikowano po powtórnej weryfikacji (recheck) wprost na tylnych drzwiach (P18-104, P18-111, P18-121; potwierdzenie P18-133). Sezony: zima 6, lato 9, wiosna 5, jesień 1.

### 3.1 Zakwalifikowane kadry (pełne dane: `manifest.csv`)

| id | Sezon | Strefy najbrudniejsze | Kształt brudu | Zacieki/skrzydło | Krycie | Kolor | Licencja / status |
|---|---|---|---|---|---|---|---|
| P18-104 (MB 1850 + naczepa, FULDA) | zima (styczeń) | próg → belka RUPD → dół drzwi | rozbryzg kropel + zacieki | b.d. | średnie | szaro-czarniawy | CC0 / OK |
| P18-105 (MB 1850 SV2 + naczepa, FULDA) | zima (styczeń) | próg → belka → dół drzwi → uszczelka → rygle | rozbryzg + pionowe zacieki od zawiasów (~30% wys. drzwi) | 3 | średnie | szary | CC0 / OK |
| P18-107 (naczepa BANEX, PL→GR) | lato | próg → belka → dół drzwi | rozbryzg kropel | brak | słabe | szary | CC BY-SA 4.0 / REFERENCJA |
| P18-108 (drobiówka PL, KRONE) | jesień | próg → belka → dół drzwi → rygiel → uszczelka | rozbryzg + zacieki od zawiasów i krawędzi dachu (~30%) | 3 | średnie | szaro-czarny | CC BY-SA 4.0 / REFERENCJA |
| P18-109 (Volvo FH420 + naczepa) | lato | próg → belka → dół drzwi → uszczelka → rygle | rozbryzg kropel | brak | średnie | szary | CC BY-SA 4.0 / REFERENCJA |
| P18-111 (tył naczepy, Berlin) | zima (grudzień, błoto pośniegowe) | próg → dół drzwi (dolna połowa) | rozbryzg + pionowe zacieki od progu (~20% wys. drzwi) | 3 | średnie | szary | CC BY-SA 4.0 / REFERENCJA |
| P18-118 (chłodnia + TrailerTail, drzwi otwarte) | zima (grudzień, błoto pośniegowe) | próg → belka → dół drzwi | rozbryzg kropel | brak | średnie | szary | CC BY-SA 3.0 / REFERENCJA |
| P18-121 (tył naczepy Schmitz, A419) | zima (styczeń, błoto pośniegowe) | dół drzwi → belka → próg | rozbryzg — poziome smugi i plamy | brak | słabe | brązowy | CC BY-SA 2.0 / REFERENCJA |
| P18-133 (chłodnia Chereau) | wiosna (kwiecień) | próg → belka → dół drzwi | rozbryzg kropel | brak | słabe | szary | CC BY-SA 4.0 / REFERENCJA |
| P18-136 (PRIME Inc., LoLo Pass, śnieg) | zima (styczeń) | próg → belka → dół drzwi → uszczelka → rygle | rozbryzgi kropel | niepoliczalne | nie określone (wizja) | szary (pośniegowy) | CC BY 2.0 / OK |
| P18-137 (Burundi, droga gruntowa) | wiosna (marzec) | cała powierzchnia drzwi (od górnej krawędzi) → próg → belka → uszczelka → rygle | rozbryzg + pionowe zacieki (~50% wys. drzwi) | 2 | nie określone (wizja) | ciemnoszary | CC BY 2.0 / OK |
| P18-138 (SEINO, Burundi, droga gruntowa) | wiosna (marzec) | próg → belka → dół drzwi → uszczelka → rygle | rozbryzgi kropel | niepoliczalne | nie określone (wizja) | brązowy (błoto) | CC BY 2.0 / OK |
| P18-139 (Liège, BE) | wiosna (maj) | dół drzwi → próg → belka → uszczelka → rygle | rozbryzg + pionowe zacieki (~30-40% wys. drzwi) | 2-3 | nie określone (wizja) | czarny | CC BY-SA 3.0 / REFERENCJA |
| P18-140 (Karakoram Highway) | lato (sierpień) | próg → belka → dół drzwi → uszczelka → rygle | rozbryzg + pionowe zacieki (~30-40% wys. drzwi) | 2-3 | nie określone (wizja) | szary | CC BY-SA 3.0 / REFERENCJA |
| P18-153 (Knight Transportation, USA) | lato (lipiec) | dół drzwi (rozbryzgi do ~10-20% wys.) | rozbryzgi kropel | 0 | brak/słabe | maroon (barwa naczepy) | CC BY-SA 4.0 / REFERENCJA |
| P18-154 (chłodnia insulated, USA) | lato (lipiec) | dół drzwi → próg → belka → uszczelka | rozbryzg + pionowe zacieki (~30-40% wys. drzwi) | 2-3 | średnie | szary na srebrnej folii | CC BY-SA 4.0 / REFERENCJA |
| P18-155 (JP Carrera, naczepa biało-czerwona) | lato (sierpień) | próg → belka → dół drzwi → uszczelka → rygle | rozbryzgi kropel | 0 | słabe | brak wyraźnego (jasne tło) | CC BY 4.0 / OK |
| P18-156 (Britannia/Lanes — przypadek minimalny) | wiosna (marzec) | dół drzwi (lekko) | brak (lekki osad) | 0 | słabe | brak wyraźnego | CC BY-SA 4.0 / REFERENCJA |
| P18-157 (Kögel, Dnipro, UA) | lato (17 sierpnia, rok nieznany) | dół drzwi → próg | rozbryzg + pionowe zacieki (~20-30% wys. drzwi) | 2-3 | średnie | szary | CC BY-SA 4.0 / REFERENCJA |
| P18-158 (EFS Global, UK) | lato (lipiec) | próg → belka → dół drzwi | rozbryzgi kropel | 0 | średnie | szary | CC BY-SA 4.0 / REFERENCJA |
| P18-159 (DeliXL, BE, ugrzęznięcie) | lato (czerwiec) | dół drzwi → próg → uszczelka | rozbryzg + pionowe zacieki (~50% wys. drzwi) | 2-3 | średnie | szary | CC BY 2.0 / OK |

Wspólny wzorzec (21 kadrów): brud koncentryczny **od dołu** (dół drzwi 20/21, próg 19/21, belka RUPD 15/21), rozbryzg kropel jako dominująca faktura (20/21 z rozbryzgiem); pionowe zacieki (2-3/skrzydło) startują od zawiasów/górnej krawędzi (lato/jesień/wiosna) lub od progu (zima); górna połowa drzwi czysta — zacieki sięgają maks. ~50% wysokości drzwi. Kadry zimowe (pośniegowe błoto) dają osad brązowy/szary, letnie szary/ciemnoszary; drogi gruntowe (Burundi) dają skrajne brązowe zabrudzenie błotem. Zgodne z mechanizmem §1.

### 3.2 Kandydaci odrzuceni (przeanalizowani, z powodów)

P18-101 (naczepa niskoramienna, brak drzwi), P18-102 (recheck: zderzak ciągnika bez naczepy — ale dokumentacja zimowego brudzenia belki RUPD i lamp), P18-103 (tipper bez drzwi), P18-106 (cysterna), P18-110 (concept truck targowy — wzór czystego tyłu), P18-112 (oldtimer), P18-113 (cysterna), P18-114 (bok chłodni), P18-115 (tył poza kadrem), P18-116 (tył kabiny bez naczepy), P18-117 (sam ciągnik, zimowy kontekst), P18-119 (bok kurtynowej — dowód bocznego brudzenia firany: 3 zacieki/skrzydło od góry, ~80% wysokości), P18-120 (bok), P18-122 (drzwi poza kadrem/niewyraźne), P18-123 (front), P18-124 (bok), P18-125 (bok), P18-126 (bok), P18-127 (bok), P18-128 (bok), P18-129 (bok), P18-130 (kontenery, bok), P18-131 (bok, ruch), P18-132 (bok), P18-134 (cysterna), P18-135 (bok), P18-141 (tył kabiny Renault, PL, grudzień), P18-142…P18-144 (tyły kabin, zlot Wörth 2006), P18-145/P18-146 (tyły kabin, IAA 2024/2026), P18-147 (tył kabiny MAN TGS), P18-148 (tył kabiny Renault Magnum), P18-149 (cysterna + tył kabiny), P18-150 (tył kabiny Eddie Stobart), P18-151 (tył kabiny GAZ Vepr NEXT), P18-152 (tył kabiny, Indie), P18-160 (bryt brezentowy — brak drzwi, ale potwierdza brud progu/belki), P18-161 (platforma flatbed), P18-162 (tył kabiny Isuzu), P18-163 (cysterna DRAINLINE), P18-164 (kadr ukośny, bok Coop), P18-165 (kadr ukośny, ładunek skrzynie), P18-166 (box bez potwierdzonych dwuskrzydowych drzwi), P18-167 (skrzynia ładunkowa UNITRUNK), P18-168 (tył kabiny z przeładowanym ładunkiem).

## 4. Zestawienie liczbowe z kadrów

**DANE KOŃCOWE (n=21 zakwalifikowanych kadrów tylnych drzwi; stan na 2026-11-14):**

- **Mediana liczby zacieków na skrzydło: 2-3** (policzalne zacieki w 9/21 kadrach; wartości: 3,3,3 (P18-105, P18-108, P18-111), 2 (P18-137), 2-3 (P18-139, P18-140, P18-154, P18-157, P18-159); w 4/21 kadry rozbryzg bez zacieków, w 8/21 niepoliczalne/zamurowane).
- **Odsetek kadrów z brudną strefą: dół drzwi 20/21 (~95%)**; **próg 19/21 (~90%)**; **belka RUPD 15/21 (~71%)**; **uszczelka 8/21 (~38%)**; **rygle 6/21 (~29%)**; **lampy: 0/21** (w żadnym kadrze lampa nie wskazana jako strefa brudna — stoją wyżej filmu dolnego; patrz §5 rekomendacja artystyczna).
- **Krycie: średnie 10/21 (~48%), słabe 5/21, nie określone przez wizję 5/21 (+1 „brak/słabe"), brak kadrów z pełnym kryciem** (mocno zabrudzone tyły to rzadkość w otwartej fotografii — patrz §6).
- **Barwa (słownie): szary dominant ~14/21** (w tym szaro-czarniawy/szaro-czarny/ciemnoszary/czarny), **brązowy 3/21** (pośniegowe i gruntowe błoto: P18-121, P18-138 + barwa naczepy P18-153); zimowe kadry pośniegowe wyraźnie brązowieją, letnie pozostają szare.
- **Typowa długość zacieków: ~20-50% wysokości drzwi → ESTIMATED ok. 0,5-1,3 m** (metoda: wizja podaje długość w % wysokości drzwi; przyjęto typową wysokość drzwi naczepy **2,65 m** [zakres 2,6-2,7 m]; 0,20 × 2,65 ≈ 0,53 m, 0,50 × 2,65 ≈ 1,33 m; id kadrów: P18-105, P18-108, P18-111 (~20-30%), P18-137, P18-159 (~50%), P18-139, P18-140, P18-154 (~30-40%), P18-153 (~10-20%), P18-157 (~20-30%)).
- **Górna granica „filmu dolnego" (jednolitego rozbryzgu): dolna część drzwi** — w 20/21 kadrach film/rozbryzg koncentruje się w dolnej części drzwi (do ~1/3 wysokości); górna połowa czysta. ESTIMATED: film dolny sięga ok. 0,5-0,9 m nad próg (dolna 1/3 drzwi przy 2,65 m ≈ 0,9 m).
- **Sezony qualified: zima 6/21, lato 9/21, wiosna 5/21, jesień 1/21** — reprezentacja zimowa wystarczająca do porównania barwy (§2.2); jesień słabo reprezentowana (luka §6).
- **Licencje: 7/21 status OK** (CC0/CC BY — dopuszczalne jako tekstura: P18-104, P18-105, P18-136, P18-137, P18-138, P18-155, P18-159), **14/21 status REFERENCJA** (CC BY-SA — patrz, nie kopiuj).

Wszystkie liczby z kadrów są **ESTIMATED** (opisy narzędzia wizyjnego na miniaturach 1280 px; proporcje przeliczone przez model wizyjny, nie mierzone pikselowo w edytorze); nie są to pomiary.

### 4.1 Audyt powtarzalności (20% kadrów)

Próba kontrolna: **seed jawny = 20261113**; wybór deterministyczny — **co 5-ty kadr wg id** z listy 21 zakwalifikowanych (posortowanej wg id): P18-109, P18-136, P18-153, P18-158 (4 kadry ≈ 19% ≈ 20%). Każdy kadrowy opis z manifestu porównano z **niezależną, drugą analizą** tego samego pliku (to samo pytanie, to samo narzędzie) — zgodność oceniona polami: strefy, kształt, zacieki, kolor, krycie. Wyniki w `audit_20_percent.json` (z pełnymi opisami obu analiz i zgodnością TRUE/FALSE per pole). Dodatkowo ponownie zweryfikowano 5 cytatów literaturowych z manifestu u źródła (open_url) — wyniki w tym samym pliku.

## 5. Pięć najlepszych kadrów dla artysty

Dobór: kompletność widoku tylnej ściany + siła i czytelność zabrudzenia + wartość wzorcowa (typowy/skrajny przypadek) + jakość licencji (OK = można użyć jako tekstura).

1. **P18-159 (DeliXL, Belgia, lato, CC BY 2.0 / OK)** — najlepszy pojedynczy wzorzec „prawdziwej" jazdy: rozbryzgi na progu + 2-3 wyraźne pionowe zacieki na lewym skrzydle od górnej krawędzi drzwi do ~50% wysokości (ESTIMATED ok. 1,3 m przy drzwiach 2,65 m), uszczelka lekko zabrudzona, belka/lampy/rygle czyste. Biała naczepa = czytelny kontrast brudu. Klimat belgijski ≈ polski. **Do bezpośredniego odmalowania.**
2. **P18-137 (Burundi, droga gruntowa, wiosna, CC BY 2.0 / OK)** — skrajny przypadek: zacieki do ~50% wysokości drzwi + rozbryzgi na wszystkich strefach (próg/belka/dół/uszczelka/rygle), ciemnoszary brud. UWAGA: warunki afrykańskiej drogi gruntowej — nie polska norma, ale wzór „maksimum" zabrudzenia i zasięgu pionowego. **Do kalibracji górnej granicy brudu.**
3. **P18-105 (MB 1850 SV2, zima, CC0 / OK)** — czytelny zimowy wzorzec: rozbryzg kropel na progu/belce/dole drzwi + 3 pionowe zacieki na skrzydło startujące od zawiasów, długość ~30% wysokości drzwi (ESTIMATED ok. 0,8 m); szary osad, krycie średnie. Pojazd zabytkowy, ale geometria drzwi dwuskrzydowych analogiczna. **Zimowy punkt odniesienia.**
4. **P18-154 (chłodnia insulated, USA, lato, CC BY-SA 4.0 / REFERENCJA)** — naczepa chłodnicza (folia srebrna): rozbryzgi drobne + 2-3 zacieki/skrzydło do ~30-40% wysokości, zabrudzone próg/belka/dół/uszczelka, czyste lampy/rygle. Wzorzec „cierpienia" srebrnej folii odblaskowej — brud na folii ma inną czytelność niż na blasze. **Referencja dla naczep chłodniczych.**
5. **P18-121 (Schmitz, A419 UK, zima, CC BY-SA 2.0 / REFERENCJA)** — zimowe błoto pośniegowe: rozbryzg w postaci poziomych smug i plam w dolnej części drzwi, osad **brązowy** (odmiana barwna względem letniego szarego), krycie słabe. Wzorzec barwy zimowej §2.2 na współczesnej naczepie Schmitz (typowa na polskich drogach). **Referencja barwna zimy.**

Dopełnienie kontrastu: **P18-156 (Britannia, wiosna, CC BY-SA 4.0)** — wzorzec „dolnej granicy": pojazd czysty, dół drzwi lekko zabrudzony; przydatny jako stan wyjściowy przed nałożeniem warstw brudu (artysta: od czystego → P18-156 → typowe → P18-159 → skrajne → P18-137).

## 6. Luki i ograniczenia

1. **Brak otwartych liczb „pokrycie vs wysokość" dla naczep** — literatura dotyczy SUV/Windsor body i ogólnych brył; mapy konturowe nieupublicznione w abstraktach. Więc rozkład wysokościowy liczony ESTIMATED z kadrów (§4).
2. **Brak otwartych danych CIELAB/Munsell/albedo letniego osadu drogowego na pojazdach** — barwa opisana słownie z mineralogii (kwarc/grafit/sadza/TRWP); albedo podane tylko dla śniegu z LAP.
3. **Dane o soli PL z portalu branżowego** (nie recenzowanego) — traktować jako orientacyjne; GDDKiA (gov.pl) zablokowała automatyczny pobór (2026-11-13).
4. **Panoramax: brak danych dla Polski** (bbox Warszawa = 0 wyników); **KartaView: API bez klucza nie zwróciło danych** (2026-11-13) — kadry tylko z Commons/Openverse.
5. **Openverse** — mimo zapytań („lorry rear", „truck rear view" itd.) brak użytecznych kadrów tylnych drzwi naczep (przeważnie zabytki i martwe zapytania; często 504 API).
6. **Ekstrapolacja SUV→naczepa**: mechanizmy fizyczne te same (bryła tylna, spray kół tylnych), ale skala stref (belka RUPD, drzwi 2,6 m) wymaga potwierdzenia kadrów.
7. **Ograniczony zasób otwartych kadrów tyłów naczep** (dominanta zbiorów fotograficznych: boki pojazdów i tyły kabin — w tej turze 44 z 65 przeanalizowanych kadrów odrzucono głównie z tego powodu); kwalifikowane tyły dwuskrzydłowe to przeważnie przystanki/zjazdy/złote kadry fotografów pojazdów, nie rutynowa jazda — stąd brak kadrów z pełnym kryciem.
8. **Geografia kadrów**: tylko część kadrów z PL/BE/UK/DE (klimat ≈ polski); pozostałe (USA, Burundi, Karakoram, Ukraina) użyte jako wzorce mechanizmu/barwy z adnotacją w manifestu. Polska reprezentacja: drobiówka KRONE (P18-108), BANEX (P18-107), Renault PL (odrzucony — tył kabiny).
9. **Jesień słabo reprezentowana (1/21)**; kadry rozczyszczane lub z targów (IAA) były czyste/odrzucone — brak otwartych kadrów jesiennych tyłów.
10. **Liczby z kadrów ESTIMATED**: oceny wysokości/faktury daje model wizyjny na miniaturach 1280 px; nie są to pomiary pikselowe (metoda w §4); audyt powtarzalności (§4.1) ogranicza, ale nie eliminuje tej niepewności.
