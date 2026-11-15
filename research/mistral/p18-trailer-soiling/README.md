# P18 — jak NAPRAWDĘ brudzi się tył naczepy (firanka 13,6 m, drzwi dwuskrzydłowe)

**Gałąź:** `research/mistral-p18-trailer-soiling-fix-s21` (poprawka do `research/mistral-p18-trailer-soiling`, PR #58)
**Autor badania:** Vibe (Mistral), paczka M61/P18 — część literaturowa i wybór 75 kandydatów; **M61-FIX s21 (Claude, 2026-11-15):** wszystkie kadry obejrzane ponownie i opisane od nowa, 13 nowych kadrów, §3–8 przepisane, dopiski w §1–2.
**Data:** 2026-11-13/14 (M61), 2026-11-15 (M61-FIX s21)

Badanie dla naczepy fikcyjnej BEZ MARKI: firanka 13,6 m, dwuskrzydłowe tylne drzwi (biała blacha/sklejka w ramie), belka przeciwwjazdowa, lampy zespolone, taśmy odblaskowe. Cel: materiał referencyjny, jak realnie wygląda zabrudzenie tyłu naczep — mechanizm, strefy, barwa i faktura, kadry referencyjne dla artysty.

**Zdjęcia NIE są w repo:** katalog `files/` jest ignorowany; archiwum **`mistral-p18-trailer-soiling-files-v2.zip`** poza gitem — nazwa, rozmiar i sha256 w opisie PR.

**Status po M61-FIX s21:** kadry z drzwiami dwuskrzydłowymi i brudem drogowym: **15** (17 z poziomem „ślad”) — kryterium ≥ 20 **niespełnione**; zimowe 3 (≥ 6 niespełnione); europejskie 3 pewne, 5–6 z zastrzeżeniami. Szczegóły i powody: §3.2 i §6. Statystyka §4 liczona tylko na tej klasie.

---

## 1. Mechanizm (literatura)

### 1.1 Skąd bierze się brud na tylnych drzwiach

Tył naczepy jest brudzony niemal wyłącznie **samozabrudzeniem (self-soiling)**: wodą z filmu na jezdni, rozbryzgiwaną przez **koła zestawu** (głównie tylne koła naczepy), która w postaci sprayu jest wciągana w **worek recyrkulacyjny za naczepą** i osadza się na powierzchni tylnej. Woda niesie zawiesinę: pył drogowy, TRWP (cząstki zużycia opony i nawierzchni), zimą sól i piasek z posiółki.

Kluczowe mechanizmy wg literatury (pełne cytaty w `manifest.csv` i `sources.md`):

- **Koła tylne dominują**: „The rear tyres are seen to be the dominant source, with front wheel spray… only making small relative contributions" (SAE 2014-01-0610, symulacja SUV walidowana w tunelu klimatycznym; DOI 10.4271/2014-01-0610). Dla naczepy analogicznie: koła tandemu naczepy są tuż pod progiem tylnym.
- **Wyrzut wody z opony** działa czterema mechanizmami wg Weira: „bow wave, side splash wave, tread pickup and capillary adhesion" (JWEIA 2019, DOI 10.1016/j.jweia.2018.11.024, abstrakt; klasyfikacja za Weir et al. 1978, badania HGV).
- **Transport na tył**: za bryłą tylną powstają „strong large-scale recirculating vortices… [that] advect the spray and deposit" (JWEIA 2017, DOI 10.1016/j.jweia.2017.05.007 wg indeksu; fragment abstraktu) — dlatego film brudu pojawia się na powierzchni drzwi, nie tylko na krawędziach.
- **Balistyka vs. entrainment**: „Large particles are found to take on a ballistic trajectory and penetrate the wake", „small particles… are less likely to become entrained into the wake" (SAE 2016-01-1604, Windsor body; DOI 10.4271/2016-01-1604, open access). **Uwaga (M61-FIX):** abstrakt mówi tylko o torze balistycznym dużych cząstek i o tym, że małe rzadziej są porywane w ślad; NIE mówi, gdzie się osadzają. Zdanie „duże krople trafiają próg i belkę, drobny aerozol osiada głównie nisko” to **ekstrapolacja autora paczki (ESTIMATED)**. Że próg i dolna rama są najbrudniejsze, wynika z kadrów (§4), nie z tego źródła.
- **Prędkość i mokra nawierzchnia**: warunkiem sprayu jest film wody na jezdni; program FHWA (Weir, Strange, Heffley 1978, FHWA-RD-79-84) charakteryzował „truck splash and spray generation and propagation" w testach simulatorowych, tunelowych i full-scale — zdanie „intensywność rośnie z prędkością i grubością filmu wody” jest **wnioskiem autora paczki (ESTIMATED)**, nie ma go w abstrakcie. Na suchej nawierzchni tył brudzi się głównie drobinowym pyłem w wirze (wolno, jednorodnie).
- **Osłony anty-spray** (dyrektywa 91/226/EWG dla N2/N3/O2-O4) ograniczają lateralny rozbryzg kół, ale **nie osłaniają powierzchni tylnej naczepy** — tył drzwi pozostaje w pełni eksponowany (przywołane, patrz sources.md §2).

### 1.2 Tabela: strefa → intensywność względna → źródło → status

| Strefa tyłu | Intensywność względna | Źródło | Status |
|---|---|---|---|
| **Próg dolny (probelka / dolna listwa drzwi)** | **NAJWYŻSZA** — bezpośrednia strefa zasięgu balistycznego sprayu kół naczepy (duże krople, piasek zimą) | SAE 2014-01-0610 (tylne koła dominują); SAE 2016-01-1604 (czynniki balistyczne) | Udokumentowane pośrednio (SUV/Windsor; ekstrapolacja geometrii na naczepę) |
| **Belka RUPD (pod progiem)** | **NAJWYŻSZA** — najbliżej jezdni, w zasięgu splash i filmu wody; maluje się pierwsza i najmocniej | jw. + spływ z błotników kół | Ekstrapolacja z literatury; potwierdzenie kadrów — patrz §3-4 |
| **Lampy zespolone (nad progiem)** | **WYSOKA** — w strefie filmu dolnego; zabrudzenie degraduje światło i kamery | Gaylard 2019 („can compromise… sensor performance") | Udokumentowane dla lamp/kamer |
| **Dolna część drzwi (od progu do ~40-50% wysokości)** | **WYSOKA, malejąca z wysokością** — film jednolity z aerozolu recyrkulacyjnego | JWEIA 2017 (wiry advectują spray); SAE 2016 (drobne entrained) | Udokumentowane jakościowo; liczby z kadrów — patrz §4 (ESTIMATED) |
| **Górna połowa drzwi** | **NISKA wg literatury; kadry s21 temu przeczą** — po dłuższej trasie film jest na całej wysokości (9/13 kadrów, §4) | SAE 2016 (małe cząstki mniej entrained) | Udokumentowane pośrednio |
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

**Kontekst, nie dane o osadzie na pojeździe (M61-FIX):** próbki z Viana do Castelo w Portugalii — pył drogowy to „primarily composed of quartz, but also of muscovite, albite, kaolinite, microcline, Fe-enstatite, graphite and amorphous content" (IJERPH 2020, DOI 10.3390/ijerph17051563) — z tego składu NIE wyprowadzam barwy osadu na naczepie w Polsce; barwa z kadrów: §4. TRWP: praca „Shades of grey" (Frontiers 2023, DOI 10.3389/fenvs.2023.1258922).

**Wartości liczbowe z literatury:** brak dostępnych otwartych danych o albedo/CIELAB/Munsell letniego osadu drogowego na pojeździe (luka — patrz §6). Nie podajemy tu żadnych liczb.

### 2.2 Zima (sól + pośniegowe błoto)

**Opis słowny (autor M61, z opisu chemii soli — NIE z kadrów; kadry s21 nie potwierdzają białego osadu na drzwiach naczep, §4):**
- **Świeże zabrudzenie (mokra jazda po solonej jezdni):** ciemnoszare do oliwkowo-brązowego „błota pośniegowego" — mieszanina roztworu soli, czarnego topniejącego śniegu przydrożnego i pyłu; na białej blasze wygląda jak brudnosszary, półprzezroczysty film z wyraźnymi kropkami (rozbryzg) na dole.
- **Po wyschnięciu:** matowy, jasnoszary do **białego** nalot krystalicznego residuum solnego (linie i „wymyte" pasy tam, gdzie woda spływała), miejscami z ciemniejszym rdzawym nalotem przy elementach stalowych (zardzewiałe śruby, zawiasy, belka) — sól przyspiesza korozję.
- **Silny mróz (poniżej ok. -7°C):** sól przestaje działać; zabrudzenie bardziej mineralne, szorstkie (piasek/posiółka), mniej filmowe.

**Podstawy liczbowe (tylko ze źródeł):**
- Sól drogowa w Polsce: „chlorek sodu (NaCl) o czystości min. 90% (najczęściej 94-97%)", gatunki DA/DR, antyzbrylacz 20-50 ppm; skuteczna do -7°C (eutektyk -21,1°C) — surowceprzemyslowe.pl (źródło branżowe, orientacyjne; P18-014/017).
- Mieszanki sól-piasek w PL: 20/80 (chodniki) do 100% soli (drogi krajowe GDDKiA) — im niższa klasa drogi, tym jaśniejszy/szorstki osad piaskowy (P18-015).
- Dawki soli: 10-40 g/m² zależnie od temperatury (P18-016).
- Kontekst, nie dane o osadzie na pojeździe (śnieg wokół Finse w Norwegii): redukcja albedo śniegu „reached up to 0.13, 0.21, and 0.25 for red algal blooms, mineral dust, and dark particles respectively" (The Cryosphere 2025, DOI 10.5194/tc-19-1527-2025; P18-018).
- „Of the de-icing agent spread by the Hokkaido Regional Development Bureau, 99% is chloride-based" — i poniżej ok. -8°C stosuje się piasek/posiółkę (Infra Intelligence; P18-019).

### 2.3 Implikacja artystyczna (barwa/faktura, lato vs zima)

- **Lato:** spójny, jednolity film w dolnej połowie + mało zacieków; kolor szaro-beżowy z oliwkowym odcieniem; mikro-drobinki (szum) zamiast plam.
- **Zima (HIPOTEZA, UNVERIFIED na kadrach naczep — patrz §4 i §6 pkt 2):** mocniejszy kontrast — ciemnoszaro-oliwkowy film + **białe residuum solne** (po wyschnięciu) w strefach spływu + rdzawe przybłyski na elementach stalowych + szorstki piasek w dolnej strefie; zacieki liczniejsze i dłuższe (częste cykle mokro/sucho z solą).

---

## 3. Kadry — oglądane i opisane (stan po M61-FIX s21, 2026-11-15)

**Metoda s21.** Każdy z 31 kadrów „zakwalifikowanych” przez M61 pobrałem ponownie z Commons (standardowe miniatury ≤ 1920 px, zapis ≤ 1600 px) i **obejrzałem osobno**; opisy w `manifest.csv` napisałem od nowa z obrazu, bez narzędzia wizyjnego i bez szablonu. Dla 121, 143 i 105 obejrzałem też wycinki. Do tego 13 nowych kadrów (P18-176…188) z Commons i z Flickr (znalezione przez Openverse), każdy obejrzany osobno. Klasa kadru jest w kolumnie `parametr`. W `uwagi` każdego kadru: rozdzielczość drzwi w px i „wycinek obejrzany: tak/nie”.

Ograniczenie: Commons odpowiadał HTTP 429 na oryginały i niestandardowe szerokości; miniatury 3840 px dla 143 i 105 nie pobrały się (2 próby), więc te dwa wycinki są interpolowane z 1600 px.

### 3.1 Klasy kadrów (44 kadry niebędące zwykłym odrzutem M61)

| Klasa | n | Kadry |
|---|---|---|
| **Drzwi dwuskrzydłowe + brud drogowy** | **15** | 108, 118, 121, 136, 137, 140, 143, 158, **176, 177, 178, 179, 182, 183, 184** |
| Drzwi dwuskrzydłowe + brud drogowy, poziom „ślad” (lekki reżim flotowy) | 2 | 109, 155 |
| Prawie czyste / nieoceniany detal | 1 | 133 |
| Wzorzec CZYSTY (poza statystyką brudu) | 3 | 107, 162, 166 |
| Rdza/wiek (poza statystyką brudu drogowego) | 4 wiersze = 3 pojazdy | 139 (+153 ten sam pojazd, nie liczony), 149, 174 |
| Brud drzwi nieoceniany | 4 | 104, 105 (eksponat, ciemna grafika), 164 (260 px), **186** (ok. 150 px, śnieżyca) |
| Drzwi rolowane (poza statystyką drzwi dwuskrzydłowych) | 3 | 150, **180**, **188** |
| Kontekst (typ drzwi nierozstrzygalny albo furgon) | 3 | **181**, **185**, **187** |
| ODRZUCONE w s21: brak dwuskrzydłowych drzwi tylnych | 9 | 111, 138, 142, 156, 160, 167, 169, 171, 172 |

Pogrubione = nowe kadry s21. Ponad recenzję s20 odrzuciłem trzy kadry, których recenzent nie pobrał: **142** (widok boczny, płaszczyzny drzwi nie widać), **156** (tylna ściana kabiny ciągnika), **169** (platforma z ładunkiem).

### 3.2 Kryteria M61-FIX — wynik uczciwy

| Kryterium | Wynik |
|---|---|
| ≥ 20 kadrów z drzwiami dwuskrzydłowymi i brudem drogowym | **NIE: 15** (17 z poziomem „ślad”) |
| ≥ 6 zimowych | **NIE: 3** (118, 121, 176); 177 to przedwiośnie (kwiecień, roztopy) |
| ≥ 6 europejskich | **NIE/GRANICZNIE: 3 pewne** (108 PL, 121 UK, 176 UK-ESTIMATED) + 177 (Rosja, Public Domain Mark) + 178 (kraj UNVERIFIED) = 5; z poziomem „ślad” (109, Francja) 6 |
| ≥ 12 nowych kadrów drzwi dwuskrzydłowych z brudem | **NIE: 7** nowych w tej klasie (+ 6 nowych pomocniczych: 2 rolety, 3 konteksty, 1 nieoceniany) |
| 0 szablonowych opisów | TAK (opisy pisane pojedynczo z obrazu) |
| Statystyka bez kadrów czystych / bez drzwi | TAK (§4) |

Dlaczego nie ma więcej: przejrzałem arkusze stykowe ok. 1 700 miniatur (Openverse: 5 serii zapytań po polsku, niemiecku, angielsku, francusku, rosyjsku, norwesku; Commons: kategorie tylnych widoków i naczep wg krajów, wyszukiwanie po tytułach, pliki autora serii z Kalifornii; Panoramax: zimowe sekwencje z Polski). Otwarte zdjęcia ciężarówek to prawie wyłącznie ujęcia z przodu i z boku; tył brudnej naczepy fotografuje się głównie wtedy, gdy ktoś napisał coś palcem w brudzie. Panoramax w Polsce zimą: w próbce sekwencji drogi lokalne bez ciężarówek w kadrze. Mapillary i KartaView nie były przeszukiwane pod tym kątem (brak wyszukiwania po treści) — to pozostaje luką.

### 3.3 Kandydaci odrzuceni przez M61 (P18-101…175, 44 wiersze)

Bez zmian w treści; 6 z nich trafiło do próby audytu s21 (§7). Powody odrzucenia są w `manifest.csv` (widok boczny, cysterna, platforma, sam ciągnik itd.).

## 4. Zestawienie liczbowe z kadrów (nowy mianownik)

Cechy każdego kadru odczytane ręcznie z obrazu są w `stats_frames.csv`; liczby poniżej to dosłowne wyjście `python stats.py` (2026-11-15). „n/o” = cechy nie da się ocenić w tym kadrze (poza kadrem, zasłonięte, odblask) i nie wchodzi do mianownika. Wszystkie wartości są **ESTIMATED** (ocena wzrokowa, bez pomiaru pikselowego).

| Cecha | Brud drogowy, n = 15 | Z poziomem „ślad”, n = 17 |
|---|---|---|
| Próg / dolna rama brudne | 13/13 (n/o 2) | 15/15 (n/o 2) |
| Belka przeciwwjazdowa / zderzak brudne | 10/11 (n/o 4) | 11/13 (n/o 4) |
| Klosze lamp wyraźnie przybrudzone | 2/12 (n/o 3) — 108, 177 | 2/13 (n/o 4) |
| Film na CAŁEJ wysokości drzwi | 9/13 (n/o 2) | 9/15 (n/o 2) |
| Wycierki / napisy palcem | 5/14 (n/o 1) — 137, 158, 176, 177, 179 | 5/16 (n/o 1) |
| Zacieki na skrzydło | mediana 0; zakres 0–10; ≥ 1 zaciek w 6/15 | mediana 0; ≥ 1 zaciek w 6/17 |
| Zimowe (XII–II) | 3 | 3 |
| Europa | 5 (3 pewne + Rosja/PDM + kraj UNVERIFIED) | 6 |

**Skąd startują zacieki** (6 kadrów z zaciekami): spod zawiasów i okuć rygli — 108 (rdzawe), 183, 184; od krawędzi skrzydła — 121; w dolnym pasie pod naklejkami i przy szczelinie — 178; na całej szerokości jako drobne smużenie po spływającej wodzie — 182. Długich, równych pasów przez całe drzwi nie ma w żadnym kadrze.

**Dwa reżimy filmu** (zgodnie z obserwacją recenzji s20, teraz na większej próbie):
- film na całej wysokości (9 kadrów: 108, 121, 136, 158, 176, 177, 179, 182, 183) — pojazdy po dłuższej jeździe; w 4 z nich są napisy palcem albo wycierki (158, 176, 177, 179);
- tylko dolny pas, ok. 10–33 % wysokości (4 kadry: 118, 137, 143, 184) oraz poziom „ślad” (109, 155).

**Kolor (słownie):** szary lub jasnoszary — 9/15 (118, 121, 136, 140, 143, 182, 183, 184 oraz białawoszary 137); szarobrązowy / szarobrunatny / beżowoszary — 6/15 (108, 158, 176, 177, 178, 179). Barwy ciepłe pojawiają się przy grubym filmie błotnym i pyle (176 zima w mieście, 177 roztopy na drodze z błotnistym poboczem), szarość przy cienkim filmie na białej lub jasnej blasze. Na 143 (pomarańczowe drzwi) i 158 (czerwone) barwy osadu nie da się pewnie oddzielić od lakieru.

**Sezon:** zima 3, przedwiośnie/wiosna 2, lato i koniec lata 8, jesień 2.

**Biały osad solny (pytanie recenzji s20).** W żadnym z 15 kadrów klasy głównej nie widać białego residuum: trzy kadry zimowe (118, 121, 176) mają osad szary lub szarobrunatny. Białawy, zaschnięty nalot z wymytymi ścieżkami kropel pokazuje tylko kadr pomocniczy **185** (tylne drzwi furgonu, styczeń; że to sól — ESTIMATED), a białawe zacieki możliwe są na 181 (typ drzwi nieustalony). Teza §2.2 o „białym osadzie po wyschnięciu” **nie ma potwierdzenia na drzwiach naczepy** — patrz §6.

**Kategorie osobne (poza powyższymi liczbami):**
- wzorzec czysty: 107, 162, 166 (nowe albo umyte pojazdy);
- rdza/wiek: 139 (=153), 149, 174 — rdzawe zacieki spod zawiasów i przerdzewiała dolna rama na starych pojazdach; to nie jest spray drogowy;
- rolety: 150, 180, 188 — 180 potwierdza film na całej powierzchni i napisy palcem także na rolecie.

## 5. Pięć najlepszych kadrów dla artysty

1. **P18-182** (Commons, CC BY-SA 4.0, lato) — białe drzwi, ok. 1000 px wysokości: szary film na całej wysokości z gęstym drobnym pionowym smużeniem, ciemniej przy ryglach i zawiasach, szary próg. Najlepszy wzór „po długiej trasie” na białej blasze.
2. **P18-121** (Commons/geograph, CC BY-SA 2.0, styczeń, Anglia) — zimowy, biała chłodnia: cienki szary film na całej wysokości, ciemniejsze ślady przy prawej krawędzi, ciemna dolna rama, ochlapana belka.
3. **P18-176** (Flickr, CC BY-SA 2.0, grudzień, UK-ESTIMATED) — zimowy gruby film szarobrunatny z napisem palcem i roztartą plamą przy uchwycie; wzór dla krycia „mocne”.
4. **P18-158** (Commons, CC BY-SA 4.0, lato) — pył na całej wysokości, napis palcem na górnej połowie, ciemne wycierki przy uchwytach rygli.
5. **P18-178** (Flickr, CC BY 2.0, wiosna; kraj UNVERIFIED) — zbliżenie dolnego pasa: plamy i krótkie zacieki nad dolną listwą, czystsza listwa z nitami, belka z odbojami. Jedyny kadr z detalem progu w dużej skali i licencją CC BY.

Uzupełniająco: P18-177 (film błotny na całych drzwiach, zachlapane lampy — ale licencja Public Domain Mark, do decyzji lidera), P18-185 (białawy nalot z wymytymi ścieżkami — furgon), P18-107/166 (wzorzec czysty). **Nie polecam** już P18-105 ani P18-111 (były w „top 5” M61): 105 to eksponat bez widocznego brudu drzwi, 111 to winda załadowcza.

## 6. Luki i ograniczenia

1. **Kryteria liczbowe niespełnione**: 15 (17) zamiast ≥ 20 kadrów, 3 zimowe zamiast ≥ 6, 3 pewne europejskie (5–6 z zastrzeżeniami) zamiast ≥ 6. Z Polski jest nadal jeden kadr z brudem (108) i jeden czysty (107). Brak zimowego kadru z PL/DE/CZ/LT z drzwiami w rozdzielczości pozwalającej ocenić brud (186 — Niemcy, śnieżyca — ma ok. 150 px).
2. **Biały osad solny na drzwiach naczepy — brak kadru** (tylko furgon 185 i niepewny 181). Zdania §2.2–2.3 o białym residuum traktować jako hipotezę z opisu chemii soli, nie jako obserwację: **UNVERIFIED**.
3. **Barwa osadu**: nadal brak liczb CIELAB/albedo; z kadrów wynika tylko „szary przy cienkim filmie, szarobrunatny przy grubym” (ESTIMATED, n = 15, różne aparaty i światło — bez wartości RGB).
4. **Rozkład z wysokością**: brak liczb z literatury (bez zmian). Z kadrów: film na całej wysokości w 9/13 ocenialnych — „górna połowa czysta” z wersji M61 jest **nieprawdziwa** dla pojazdów po trasie.
5. **Literatura (M61-FIX pkt 10)**: P18-002 („trafiają próg i belkę”) i P18-005 („rośnie z prędkością i grubością filmu”) to ekstrapolacje autora → ESTIMATED; P18-012 (pył z Portugalii) i P18-018 (śnieg w Norwegii) to kontekst, nie dane o osadzie na pojeździe. §1 i §2 czytać z tym zastrzeżeniem (dopiski w tekście). Audyt s21: cytatu P18-004 nie dało się dziś sprawdzić (Crossref bez abstraktu), link P18-021 zwraca 403 klientowi automatycznemu — oba UNVERIFIED w dniu audytu.
6. **Licencje nowych kadrów**: Flickr 5 × CC BY 2.0 i 4 × CC BY-SA 2.0 (sprawdzone na stronie zdjęcia: kod licencji 4 = BY, 5 = BY-SA), 3 × Commons CC BY-SA 4.0, **1 × Public Domain Mark (P18-177)** — poza listą CC0/BY/BY-SA, zostawiony jako referencja z jawnym oznaczeniem. Wszystkie BY-SA = referencja, nie tekstura.
7. **Kraje ESTIMATED/UNVERIFIED**: 176 (UK z adresu „.co.uk”), 178 (brak danych), 179/180 (USA z kontekstu), 185 (brak), 186 (Niemcy z tytułu), 187 (UK z kontekstu).
8. **Bias próbki**: 8 z 15 kadrów to Kalifornia latem i jesienią (sucho, pył), w większości jeden autor; kadry „z napisem palcem” są nadreprezentowane, bo właśnie takie tyły ludzie fotografują. Odsetków z §4 nie przenosić wprost na polską zimę.
9. **Rozdzielczość**: 143 (ok. 330 px drzwi), 177 (480 px), 176/179 (540–560 px) — poniżej wymaganego 1000 px; ≥ 800 px mają 108, 118, 136, 137, 182, 183, 184.
10. **Daty**: 166 i 172 mają w opisie pliku inne daty niż w EXIF; przyjęto EXIF (odczyt własny z API Commons). Czas EXIF kadru 181 (00:29) jest niewiarygodny — pora dnia UNVERIFIED.

## 7. Samokontrola 20 % (s21)

Seed jawny: `sorted(random.Random(20261115).sample(sorted(ids), 22))` po wszystkich 109 wierszach → 22 wiersze (20,2 %): 4 literatura, 18 kadrów. Każdy kadr z próby, którego obraz dało się pobrać, obejrzany ponownie w dniu audytu osobnym wywołaniem i porównany z wierszem. Wynik i poprawki: `audit_20_percent.json`.

## 8. Pliki

Zdjęcia nie są w repo (`files/` w `.gitignore`). ZIP **`mistral-p18-trailer-soiling-files-v2.zip`**: 44 pliki `P18-NNN.jpg` (31 starych + 13 nowych), JPG ≤ 1600 px; nazwa, rozmiar i sha256 w opisie PR; kopia u lidera w `research/_incoming/`.
