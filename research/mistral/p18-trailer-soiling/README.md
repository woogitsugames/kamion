# P18 — jak NAPRAWDĘ brudzi się tył naczepy (firanka 13,6 m, drzwi dwuskrzydłowe)

**Gałąź:** `research/mistral-p18-trailer-soiling` (z najnowszego `origin/main` @ b67b949d, 2026-11-13)
**Autor badania:** Vibe (Mistral), paczka M61/P18
**Data:** 2026-11-13 (init), aktualizacja kadrów: 2026-11-14

Badanie dla naczepy fikcyjnej BEZ MARKI: firanka 13,6 m, dwuskrzydłowe tylne drzwi (biała blacha/sklejka w ramie), belka RUPD, lampy zespolone, taśmy odblaskowe. Cel: materiał referencyjny, jak realnie wygląda zabrudzenie tyłu naczep na polskich drogach — mechanizm, strefy, barwa i faktura (lato/zima), kadr referencyjny dla artysty.

**Zdjęcia NIE są w repo:** katalog `files/` jest ignorowany (`.gitignore`); archiwum **`mistral-p18-trailer-soiling-files.zip`** dostarczono poza git — nazwa, rozmiar i sha256 w opisie PR.

**Status:** UKOŃCZONE dla puli kadrów — 20/20 zakwalifikowanych kadrów tylnych drzwi (cel osiągnięty 2026-11-14); dalsze kadry opcjonalnie w kolejnych iteracjach. Sekcje 1-6 kompletne.

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

**Stan: 20/20 zakwalifikowanych kadrów tylnych drzwi** (P18-104, P18-105, P18-107, P18-108, P18-109, P18-111, P18-118, P18-121, P18-133, P18-136, P18-137, P18-138, P18-139, P18-140, P18-142, P18-143, P18-149, P18-150, P18-153, P18-155); łącznie przeanalizowano 55 kandydatów, odrzucono 35 (pełne wiersze z uzasadnieniem w `manifest.csv`, P18-101…P18-154). Pięć kadrów zakwalifikowano po powtórnej weryfikacji (recheck) wprost na tylnych drzwiach (P18-104, P18-111, P18-121, P18-139/153 — para kadrów jednego pojazdu).

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
| P18-136 (naczepa Amazon Prime) | nieoznaczony (sierpień wg daty) | próg → lampy | rozbryzg kropel (<10% wys. drzwi) | brak | słabe | szary | CC BY-SA 4.0 / REFERENCJA |
| P18-137 (naczepa Coca-Cola) | lato/wczesna jesień (nieoznaczony) | dół drzwi → lampy → uszczelka/rygle | pionowe zacieki od góry (~50-70% wys. drzwi) | 2-3 | średnie | szary/czarniawy | CC BY-SA 4.0 / REFERENCJA |
| P18-138 (naczepa kontenerowa) | zima (wg wizji; patrz uwagi) | próg → belka → lampy → dół drzwi | rozbryzg kropel (~20-30% wys. drzwi) | brak | średnie | ciemnoszary/czarny | CC BY-SA 4.0 / REFERENCJA |
| P18-139 (naczepa ICR, kadr wycięty) | nieoznaczony (maj wg daty) | próg → belka → dół drzwi → rygle → uszczelka | liczne pionowe zacieki od góry (~70-80% wys. drzwi) | liczne (>3) | średnie | ciemnobrązowy | CC BY-SA 4.0 / REFERENCJA |
| P18-140 (chłodnia, tył) | lato | dół drzwi → próg | rozbryzg kropel (~10-15% wys. drzwi) | brak | słabe | szary | CC BY-SA 4.0 / REFERENCJA |
| P18-142 (naczepa, widok ukośny 1/4) | lato | dół drzwi → próg → belka | rozbryzg kropel (~10-15% wys. drzwi) | brak | słabe | szary/brązowawy | CC BY 2.0 / OK |
| P18-143 (naczepa Schneider National) | lato | dół drzwi → próg → belka | rozbryzg kropel (~10-15% wys. drzwi) | brak | średnie | szaro-czarny | CC BY 3.0 / OK |
| P18-149 (naczepa Old NAVAJO) | nieoznaczony (lipiec wg daty) | próg → belka → lampy → dół drzwi | rozbryzg + liczne zacieki od góry (~50-70% wys. drzwi) | liczne (>3) | średnie | rdzawo-brązowy | CC BY-SA 4.0 / REFERENCJA |
| P18-150 (naczepa Ralphs) | nieoznaczony (sierpień wg daty) | próg → belka → lampy → dół drzwi | rozbryzg kropel | brak | średnie | szary | CC BY-SA 4.0 / REFERENCJA |
| P18-153 (naczepa ICR, drzwi + stopnie) | nieoznaczony (maj wg daty) | próg → belka → lampy → dół drzwi → rygle → uszczelka → stopnie | pionowe zacieki od góry (~50-70% wys. drzwi) | kilka (>3) | średnie | ciemnobrązowy | CC BY-SA 4.0 / REFERENCJA |
| P18-155 (naczepa Legend Transportation) | nieoznaczony (sierpień wg daty) | próg → belka → dół drzwi | rozbryzg kropel | brak | słabe | szary | CC BY-SA 4.0 / REFERENCJA |

Wspólny wzorzec (20 kadrów): brud koncentryczny **od dołu** (próg, belka RUPD, dół drzwi), rozbryzg kropel jako dominująca faktura; pionowe zacieki startują od zawiasów/krawędzi dachu (lato/jesień, długość 50-80% drzwi — brudzenie stacyjne/otwieranie drzwi) lub od progu (zima, 20-30%); górna połowa drzwi w kadrach drogowych czysta. Kadry zimowe (pośniegowe błoto) dają osad brązowy/ciemnoszary, letnie szary. Zgodne z mechanizmem §1.

### 3.2 Kandydaci odrzuceni (przeanalizowani, z powodów)

P18-101 (naczepa niskoramienna, brak drzwi), P18-102 (recheck: zderzak ciągnika bez naczepy — ale dokumentacja zimowego brudzenia belki RUPD i lamp), P18-103 (tipper bez drzwi), P18-106 (cysterna), P18-110 (concept truck targowy — wzór czystego tyłu), P18-112 (oldtimer), P18-113 (cysterna), P18-114 (bok chłodni), P18-115 (tył poza kadrem), P18-116 (tył kabiny bez naczepy), P18-117 (sam ciągnik, zimowy kontekst), P18-119 (bok kurtynowej — dowód bocznego brudzenia firany: 3 zacieki/skrzydło od góry, ~80% wysokości), P18-120 (bok), P18-122 (drzwi poza kadrem/niewyraźne), P18-123 (front), P18-124 (bok), P18-125 (bok), P18-126 (bok), P18-127 (bok), P18-128 (bok), P18-129 (bok), P18-130 (kontenery, bok), P18-131 (bok, ruch), P18-132 (bok), P18-134 (cysterna), P18-135 (bok), P18-141 (MB 1850 — drzwi poza kadrem, kontekst zimowy), P18-144 (stacja krwiodawstwa — brak drzwi w kadrze), P18-145 (dwie skrzyniówki z burtami — kontekst: zabrudzona tylna lampa), P18-146 (skrzyniówka), P18-147 (Isuzu z otwartą skrzynią), P18-148 (DAF — drzwi poza kadrem), P18-151 (skrzyniówka FedEx), P18-152 (targowy czysty — baseline), P18-154 (ciągnik targowy bez naczepy).

## 4. Zestawienie liczbowe z kadrów

**DANE KOŃCOWE (n=20 zakwalifikowanych; stan na 2026-11-14):**

- **Mediana liczby zacieków na skrzydło: 3** (policzalne zacieki w 7/20 kadrów; w kadrach drogowych zawsze ok. 3 — P18-105, P18-108, P18-111, P18-137; kadry stacyjne/leasowe: liczne (>3) — P18-139, P18-149, P18-153).
- **Odsetek kadrów z brudnym progiem lub dołem drzwi: 20/20 (100%)**; **belka RUPD: 16/20 (80%)**; **lampy wskazane jako brudne: 6/20 (30%)** (P18-136, P18-138, P18-139, P18-149, P18-150, P18-153); **uszczelka/rygle: 6/20**.
- **Krycie: średnie 13/20, słabe 7/20; brak kadrów z pełnym kryciem** (mocno zabrudzone tyły to rzadkość w otwartej fotografii — patrz §6).
- **Barwa (słownie): szary/szaro-czarniawy/ciemnoszary 15/20; brązowy/rdzawo-brązowy/ciemnobrązowy 5/20** (P18-121 pośniegowe, P18-139, P18-149, P18-153 — zabrudzenie długotrwałe/stacyjne); zimowe kadry pośniegowe brązowieją, letnie pozostają szare.
- **Typowa długość zacieków: dwa reżimy.** (a) kadr drogowy zimowy: ~20-30% wysokości drzwi → ESTIMATED ok. 0,5-0,8 m; (b) kadr stacyjny/długotrwały: ~50-80% wysokości drzwi → ESTIMATED ok. 1,3-2,1 m. Metoda: wizja podaje długość w % wysokości drzwi; przyjęto typową wysokość drzwi naczepy **2,65 m** (zakres 2,6-2,7 m); id kadrów: (a) P18-105, P18-108, P18-111; (b) P18-137, P18-139, P18-149, P18-153.
- **Górna granica „filmu dolnego" (jednolitego rozbryzgu): ESTIMATED dolna 1/3 wysokości drzwi** — w 20/20 kadrach film/rozbryzg nie przekracza ~1/3 wysokości drzwi (10-30%); górna połowa czysta; granica w metrach: ok. 0,5-1,0 m nad próg.
- **Sezony: zima 6/20 (P18-104, P18-105, P18-111, P18-118, P18-121, P18-138), lato 6/20 (P18-107, P18-109, P18-140, P18-142, P18-143 + P18-136 wg daty), jesień 1/20, wiosna 1/20, nieoznaczony 6/20** — reprezentacja zimowa wystarczająca do porównania barwy (§2.2).
- **Licencje: OK (CC0/CC BY) 4/20; REFERENCJA (CC BY-SA) 16/20** — żadnego kadru z CC BY nie wolno używać w grze bez atrybucji; wszystkie traktowane jako materiał referencyjny dla artysty.

Wszystkie liczby z kadrów są **ESTIMATED** (opisy narzędzia wizyjnego na miniaturach 1024-1280 px; proporcje przeliczone przez model wizyjny, nie mierzone pikselowo w edytorze); nie są to pomiary.

## 5. Pięć najlepszych kadrów dla artysty

Dobór: różnorodność reżimów (zima drogowy, zima pośniegowe, lato drogowy, stacyjny) + licencje możliwie najswobodniejsze.

1. **P18-105 (MB 1850 + naczepa, CC0)** — wzorcowy zimowy kadr drogowy: rozbryzg na progu/belce/dole drzwi + 3 pionowe zacieki na skrzydło od zawiasów, ~30% wysokości drzwi (ESTIMATED ~0,8 m), osad szary. Najlepszy „przepis" na tył po mokrej zimowej jeździe.
2. **P18-111 (tył naczepy, Berlin, grudzień, CC BY-SA)** — pośniegowe błoto: rozbryzg + zacieki od progu (~20% wys. drzwi), dolna połowa drzwi brudna; potwierdza zimowy reżim „brud startuje od dołu".
3. **P18-121 (tył naczepy Schmitz, A419, styczeń, CC BY-SA)** — zimowy osad **brązowy** (pośniegowe błoto), poziome smugi i plamy na dole drzwi — kontrast barwny względem szarych kadrów letnich.
4. **P18-143 (naczepa Schneider National, CC BY, lato)** — letni reżim drogowy: jednolity rozbryzg kropel na progu/belce/dole drzwi do ~1/3 wysokości, góra czysta; licencja CC BY pozwala użyć jako referencji tekstury z atrybucją.
5. **P18-153 (naczepa ICR z drzwiami i stopniami, CC BY-SA)** — reżim stacyjny/długotrwały: liczne zacieki 50-70% wysokości, brud także na ryglach, uszczelce, lampach i stopniach; wzór stref dotykowych (stopnie wytarte) i koncentracji brudu w punktach zakłócenia.

Dla artysty: P18-105+P18-111 dają zimę, P18-121 zimę brązową (posiółka), P18-142/143 lato szare, P18-153/139 detale rygli/uszczelki/stopni. Wszystkie miniatury w `files/` (poza git, patrz opis PR).

## 6. Luki i ograniczenia

1. **Brak otwartych liczb „pokrycie vs wysokość" dla naczep** — literature dotyczy SUV/Windsor body i ogólnych brył; mapy konturowe nieupublicznione w abstraktach. Więc rozkład wysokościowy liczony ESTIMATED z kadrów (§4).
2. **Brak otwartych danych CIELAB/Munsell/albedo letniego osadu drogowego na pojazdach** — barwa opisana słownie z mineralogii (kwarc/grafit/sadza/TRWP); albedo podane tylko dla śniegu z LAP.
3. **Dane o soli PL z portalu branżowego** (nie recenzowanego) — traktować jako orientacyjne; GDDKiA (gov.pl) zablokowała automatyczny pobór (2026-11-13).
4. **Panoramax: brak danych dla Polski** (bbox Warszawa = 0 wyników); **KartaView: API bez klucza nie zwróciło danych** (2026-11-13) — kadry tylko z Commons.
5. **Openverse** — mimo zapytań brak użytecznych kadrów tylnych drzwi naczep (przeważnie zabytki i martwe zapytania; często 504 API).
6. **Ekstrapolacja SUV→naczepa**: mechanizmy fizyczne te same (bryła tylna, spray kół tylnych), ale skala stref (belka RUPD, drzwi 2,6 m) wymaga potwierdzenia kadrów — potwierdzone jakościowo w §3-4.
7. **Sezon wg metadanych vs treść kadru**: P18-138 — wizja wskazuje śnieg (zima), metadane pliku sierpień; sezon przyjęto wg treści kadru (oznaczono w manifeście). P18-155 — miniatura 1280px niedostępna (HTTP 429 Wikimedia), analizowano 1024px.
8. **Bias próbki**: 6/20 kadrów letnich/„nieoznaczonych" pochodzi z parkingów wjazdowych/terminali (stan umiarkowany); kadry z silnym brudem (krycie pełne) nie wystąpiły ani razu w 55 kandydatach — w grze krycie „pełne" należy traktować jako stan awaryjny/rzadki.
9. **Audyt wizyjny**: pełne ponowne oglądzenie wizyjne próbki 20% odroczono do następnej iteracji (budżet analyze_image wyczerpany na analizę nowych kadrów); w `audit_20_percent.json` wykonano zastępcze porównanie manifest↔analizy + weryfikację cytatów (patrz plik).
