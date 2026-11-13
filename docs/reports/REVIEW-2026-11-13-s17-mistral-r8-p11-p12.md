# Przegląd paczek Mistral r8: P11 (M47, PR #39) i P12 (M48, PR #40) — s17, 2026-11-13

## NASTĘPNY KROK (dla sesji przejmującej)

**Przegląd ZAKOŃCZONY** (s17): P11 — PRZYJĘTA CZĘŚCIOWO (§2), P12 — PRZYJĘTA z zastrzeżeniami (§3). Dla lidera: (1) przekazać §4 agentowi 0166 — pilne: hangar L10 jest poza kaflem, BISON/Odlewnia w kaflu; (2) poprawki do PR #39/#40 przekazać Mistralowi (listy na końcu §2 i §3); (3) scalenie wg §5. Nic nie scalono, nic nie skomentowano, nic nie scommitowano. Skrypty pomocnicze (scratch s17, `python -I`): `inv.py` (EPSG:2180 + kafel + próba), `osmchk.py` (OSM API dla próby), `lod.py` (wysokości vs `buildings.geojson` 0166), `jpgdim.py` (wymiary JPG / zgodność z manifestem).

## 1. Metoda

Wg `REVIEW-2026-11-13-s16-research-pack-02.md` §1. Metadane czytane przez `git show origin/research/<gałąź>:…` (main nie przełączany), skrypty własne w scratchu, `python -I`; nic z ZIP/PR nie uruchamiano. Kafel referencyjny = `bialystok-dojlidy` z worktree 0166 (`region.yaml`): EPSG:2180 **[779019, 589055, 781067, 591103]**. Przeliczenie WGS84→EPSG:2180 własną implementacją TM (GRS80, λ0=19°, k0=0,9993, FE 500 000, FN −5 300 000) — zgodne co do 0,1 m z narożnikami podanymi w README P11. Zakaz Google zachowany.

## 2. P11 — zdjęcia referencyjne Dojlidy/Krywlany (M47, PR #39) — **PRZYJĘTA CZĘŚCIOWO (jako referencja; opisy kadrów do poprawy)**

**Formalnie:** PR zmienia wyłącznie `research/mistral/p11-dojlidy-photos/` (5 plików: README, manifest, sources, audit, .gitignore `files/`) — zgodne z opisem. Manifest 154 wiersze (143 SOURCED, 8 ODRZUCONE, 3 UNVERIFIED Panoramax), 143 JPG w `_incoming` = dokładnie 143 wiersze SOURCED (0 braków, 0 nadmiarowych), wszystkie JPEG, max bok 1600 px. SHA ZIP nie sprawdzony (mamy rozpakowane pliki).

**Licencje (manifest):**

| licencja | wiersze | status w projekcie |
|---|---|---|
| CC0 | 124 | użyteczne (wszystkie SOURCED CC0 to seria „Rakoon”) |
| CC BY-SA 4.0 / 3.0 / 3.0 pl | 10 / 8 / 4 | **tylko referencja** (zasada przeglądu) |
| CC BY 3.0 pl / 3.0 / 2.0 | 3 / 2 / 1 | referencja z atrybucją |
| CC BY-NC-SA 2.0 | 2 | odrzucone (P11-153/154, poprawnie oznaczone jako tylko link) |

Uwaga: sources.md podaje 7 / 6 / 4 / 2 / 2 dla SOURCED — liczby z manifestu (wszystkie wiersze) są wyższe, bo obejmują wiersze ODRZUCONE; brak sprzeczności istotnej.

**Bbox:** P11 przyjęła własny kafel WGS84 53,096–53,114 / 23,176–23,206 (≈ X 779 361–781 485, Y 589 335–591 453), przesunięty ~400 m na wschód względem kafla 0166. **Tylko 80/154 wierszy leży w kaflu 0166** (70 poza, 4 bez współrzędnych). Poza kaflem 0166 są m.in.: **cały browar Dojlidy** (X ≈ 781 140–781 300), **rondo Hasbacha** (X 781 057–781 097 — na samej granicy, wloty wschodnie poza), pałac Hasbacha/Lubomirskich, cmentarz i cerkiew Proroka Eliasza, Dojlidy Górne, Grabowa, rondo Meyera (Y ≈ 592 070–592 105, ~1 km na północ), rondo Wünschego (X ≈ 778 800). Dla 0166 w kaflu zostają: Kuronia (zach./środek), Mickiewicza, Wiewiórcza, Myśliwska, Karpińskiego, Borsucza, Kormoranów, Niedźwiedzia, Żurawia, Modzelewskiego, Hake, Dywizjonu 303 (fragment), Sąd/Archiwum/Starostwo/USK Żurawia.

**Próba (seed 11113, 31/154 = 20 %):** P11-001, 008, 021, 023, 025, 026, 027, 032, 043, 044, 050, 054, 057, 064, 070, 079, 082, 083, 085, 086, 088, 091, 103, 104, 108, 110, 115, 121, 136, 140, 143.
- **Metadane Commons (API `imageinfo|coordinates`, na żywo): 31/31 zgodne** — współrzędne co do 1e-6°, data EXIF, licencja i autor jak w manifeście (P11-082: czas 13:54:38 vs nazwa pliku 135456 — trywialne).
- **Treść kadrów (obejrzano 13 JPG: 001, 032, 056, 063, 064, 084, 091, 092, 094, 121, 129, 142 + kontekst):** zgodne z opisem 6 (001 Kuronia — dobry kadr wzdłuż jezdni ze strefą SSSE i latarniami dwuramiennymi; 032 Myśliwska — wjazd na posesję przy jezdni, jesień; 056 Dywizjonu 303 — skrzyżowanie z tabliczką ulicy, pole/łąka, ogrodzenia lotniska nie widać → częściowo; 121 browar — ceglany budynek administracyjny, kominów brak → częściowo; 129 brama USK Żurawia 14 ze szlabanem — zgodne; 142 pałac Lubomirskich — zgodne). **Błędne 6:**
  - **P11-090/091/092 — zdjęcia zabawkowego robota edukacyjnego na biurku** (pliki „Photon_przód/tyłem”, „Robot_na_głowie”), opisane jako „hala zakładu przy ul. Kuronia” → **odrzucić** (to nie są widoki drogi; mają też na sobie znak towarowy).
  - P11-084 „rondo Hasbacha — wlot od DK19” = tablica „Plan osiedla Dojlidy” pod drzewami (nie widać ronda).
  - P11-094 „Browar Dojlidy — brama od Kuronia” = hala produkcyjna innego zakładu SSSE (szara hala z dużym szyldem firmy) przy jezdni — przydatny kadr hali, zły opis.
  - P11-063 „skrzyżowanie z Dywizjonu 303 — narożnik Sądu” = skrzyżowanie w SSSE z halą zakładu po prawej, sądu brak.
  - P11-064 „skrzyżowanie z Karpińskiego — wjazd do SSSE” = furtka ROD „Ekologiczny”, Mickiewicza 106a.
  → **≈ 45 % obejrzanych opisów nie odpowiada treści.** README sam przyznaje, że nabór szedł „bez podglądu zawartości” — opisy powstały z nazwy pliku i pozycji GPS. Pozycje i licencje są rzetelne; **opisy `punkt_opis` i lista „15 najlepszych kadrów” są niewiarygodne** (z 15 kadrów listy obejrzałem 8: błędne 084, 094, 063, 092; częściowe 121, 056; trafne 142, 129).
- `kierunek_deg` = UNVERIFIED we wszystkich (uczciwie zadeklarowane); poziom kamery pieszy ~1,6 m (uczciwie zadeklarowane). Pojazd w P11-057 („tow truck”) — opis neutralny, OK.

**Twierdzenia z PR/README:** „tylko `research/mistral/p11-…`” — prawda. „Panoramax 0 w kaflu, KartaView 0” — nie sprawdzono (przyjmuję jako deklarację). „DK65 nie oznakowana w bbox, S19 poza” — zgodne z wiedzą projektu. „Park Centralny” przy DK19 — **błąd nazewniczy** (Park Centralny jest w centrum miasta; tu park pałacowy Lubomirskich / Dojlidy). „Szpital uniwersytecki (Żurawia)” — to oddziały zakaźne USK przy Żurawiej 14 (kadr potwierdza), OK.

**Werdykt P11:** PRZYJĘTA CZĘŚCIOWO — jako galeria referencyjna Commons (pozycje/licencje/daty wiarygodne, CC0 Rakoon dominuje). Odrzucić P11-090, 091, 092. Nie używać `punkt_opis` ani listy 15 kadrów bez obejrzenia; dla 0166 brać tylko 80 wierszy w kaflu.

**Do poprawy w PR #39 (dla Mistrala):** (1) usunąć P11-090/091/092; (2) przejrzeć wzrokowo wszystkie 143 kadry i przepisać `punkt_opis` wg treści (min. 084, 094, 063, 064, 056, 121); (3) dodać kolumnę `w_kaflu_0166` wg bbox EPSG:2180 [779019,589055,781067,591103] (region.yaml jest w gałęzi `region-0166`); (4) listę 15 kadrów ułożyć z obejrzanych kadrów w kaflu 0166; (5) „Park Centralny” → park pałacowy Lubomirskich.

## 3. P12 — landmarki, typologia, wyposażenie, generatory ruchu (M48, PR #40) — **PRZYJĘTA z zastrzeżeniami**

**Formalnie:** PR zmienia wyłącznie `research/mistral/p12-dojlidy-landmarks/` (24 pliki): README, manifest (95 wierszy: 39 landmark, 6 typologia, 33 wyposażenie, 17 generator_ruchu; statusy SOURCED 49 / UNVERIFIED 40 / ESTIMATED 6), sources, audit, `.gitignore` (`files/` + nazwa ZIP), **`tools/` (8 skryptów Python — nie uruchamiano)** i **`data/` (11 JSON, ~1,5 MB: m.in. `road-geom.json` 506 kB, `matched-with-roads.json` 500 kB — wyciągi OSM ODbL / LoD1)**. Kolumny manifestu = dokładnie wg zlecenia. 30 JPG w `_incoming` (25 ortofoto GUGiK 800×800 A01–A26 bez A20, 5 Commons), wszystkie JPEG ≤ 1600 px. SHA ZIP nie sprawdzony.

**Licencje:**

| źródło | wiersze/pliki | status |
|---|---|---|
| OSM ODbL (+ GUGiK otwarte dane) | 35 + 8 wierszy | OK (atrybucja ODbL) |
| OSM + Radio Białystok / strony firm „tylko referencja” | 25 + 12 | OK — tekst informacyjny, nie zasób |
| GUGiK ortofoto (A01–A26) | 25 JPG | OK (otwarte dane) — do lokalizacji/kolorów, nie jako tekstura bez decyzji |
| Commons CC BY-SA 3.0/4.0 (P01–P05) | 5 JPG | **tylko referencja** |

**Bbox:** P12 przyjęła własny kafel EPSG:2180 [778660, 589590, 780660, 591590] (≈ 359 m na zachód i 535 m na północ od 0166). **W kaflu 0166: 62/95 wierszy.** Skutek: flagi `poza_kaflem` są względem złego kafla — **BISON (P12-034, LoD1 8,37 m) i Odlewnia (P12-036, LoD1 13,08 m) LEŻĄ w kaflu 0166**, a **hangar Aeroklubu (P12-004, X 778 655) i maszty (P12-030) — poza nim**. Browar, BIAFORM, BIAWAR, kościół NSM, pałace — poza 0166 (zgodnie z P12).

**Próba (seed 12113, 19/95 = 20 % + 6 dobranych: 001, 018, 020, 080, 081, 082):**
- **API OSM (way/node .json, na żywo): 16/16 zgodne** — m.in. way 958211700 v2 `aeroway=runway ref=09R/27L length=1350 surface=asphalt`; 303368859 v3 grass 860 m; 304300294 hangar; 484566822 Sąd Rejonowy Mickiewicza 103; 236884780 szpital Żurawia 14 „A”; 210878364 WORD Wiewiórcza 64; 471492581 KAN; 234838499 Masterpress; 513010463 Bravilor; 252332077 Rosti; 674071951 Biawar; 1192357612 Zintronic.
- **Przystanki (OSM `map` bbox ±15 m): 6/6** — nazwy i `shelter=yes/brak` zgodne (P12-050, 055, 061, 065, 066, 068).
- **Wysokości vs LoD1 2024 z danych 0166 (`buildings.geojson`, point-in-polygon): 13/14 identyczne co do 0,01 m** (KAN 15,05; Masterpress 12,17; Bravilor 12,72; Rosti 18,92; BPN-T 18,09; Sąd **24,44**; Archiwum 12,22; WORD 5,27; LO 13,23; dyskont 6,69…). P12-020 szpital 14,85 vs 13,14 w punkcie (P12 bierze sąsiedni pawilon E1 — drobne).
- **Bramy generatorów:** KAN, Masterpress, Bravilor = te same node’y co w P6 (4656499172, 2999986083, 6539179208) co do 1e-7°. Rosti: P12 podaje 53.103204/23.193609, P6 node 6596800253 = 53.103235/23.193238 (~25 m — inna brama zakładu). **Art-Glas i Zintronic mają identyczną „bramę” 53.110652, 23.185712** (= pozycja budynku Zintronic) → błąd dopasowania.
- **Commons P01–P05:** curid, autor i licencja zgodne 5/5 (API po pageid), ale **wszystkie 5 URL-i `File:` w sources.md wskazują nieistniejące pliki** (prawdziwe: „Browar Dojlidy w Białymstoku panorama 1.jpg”, „Browar Dojlidy fasada budynku.jpg”, „Lotnisko na Krywlanach.jpg”, „Sąd Rejonowy w Białymstoku (Mickiewicza 103) 1.jpg”, „Białystok Dojlidy Fabryczne 23, Pałac Hasbacha.jpg”). Atrybucja wymaga poprawy.
- **Obejrzane JPG:** A01 (ortofoto — pas asfaltowy z oznakowaniem progu i strzałkami, pas trawiasty z oznacznikami — zgodne), A08 (duża hala z naświetlami przy Kuronia + ROD — wiarygodne, obiektu nie identyfikuję jednoznacznie), P03 (płyta Krywlany, stary terminal żółty, samoloty, 2011 — zgodne), P04 (Sąd: jasny kamień + przeszklone górne kondygnacje, zima — zgodne).
- **Błąd merytoryczny:** P12-072 „znaki PL:A-11a (przystanek na żądanie)” — **A-11a to „próg zwalniający”**; OSM (node 2999716107: `traffic_calming=bump`, `traffic_sign=PL:A-11a`) jest poprawny, opis zły.
- Twierdzenie o tranzycie > 3,5 t (Kuronia → D303 → Ciołkowskiego od 19–20.11.2025, > 8 t na Mickiewicza) — zgodne z naszym `research/g10-truck-restrictions/` (pkt 1–2).

**Typologia (census 1307 bud., bufor 30 m = 911):** metoda jawna i spójna z LoD1/BDOT; jednorodzinne 80,8 % (h med. 7,4 m), gospodarcze 14,2 %, handel 3,2 %, bloki 1,3 % (h med. 11 m), hale 0,4 % w buforze (29 hal w kaflu). Kolory dachów = ESTIMATED z ortofoto (szare 34 %, grafit 14,6 %, ocynk 14,1 %, czerwone 14,4 %). Uwaga: liczone dla kafla P12, nie 0166 — rząd wielkości przenośny, liczby nie.

**Werdykt P12:** PRZYJĘTA z zastrzeżeniami — najlepsza dotąd paczka landmarków pod względem weryfikowalności (OSM 22/22, LoD1 13/14). Zastrzeżenia: zły kafel (flagi `poza_kaflem`), 5 złych URL Commons, opis A-11a, zdublowana brama Art-Glas/Zintronic, elewacje i latarnie UNVERIFIED (uczciwie). `tools/` i `data/` — do decyzji lidera: można scalić (to dane ODbL/GUGiK + kod badawczy, nie runtime), ale `data/*.json` 1,5 MB to duplikat tego, co worldgen 0166 i tak generuje — rekomendacja: scalić bez `data/road-geom.json`, `matched-with-roads.json`, `area-geom.json` (albo przyjąć całość, jeśli lider woli reprodukowalność).

**Do poprawy w PR #40:** (1) przeliczyć `poza_kaflem` wg kafla 0166 [779019,589055,781067,591103]; (2) poprawić 5 URL Commons; (3) P12-072 → „próg zwalniający”; (4) bramy Art-Glas/Zintronic — osobno albo UNVERIFIED; (5) Rosti — podać obie bramy (node 6596800253 i ta z P12).

## 4. Fakty dla agenta 0166 (region `bialystok-dojlidy`)

Wszystko poniżej sprawdzone w tym przeglądzie (OSM API / LoD1 z `buildings.geojson` 0166 / obejrzane JPG). X,Y = EPSG:2180.

**Landmarki w kaflu 0166 (wysokość LoD1 2024):**

| obiekt | OSM | X, Y | h [m] | wygląd (źródło) |
|---|---|---|---|---|
| Sąd Rejonowy, Mickiewicza 103 | way 484566822 | 780 056, 590 576 (53.106828, 23.185689) | **24,44** (najwyższy w kaflu) | jasna okładzina kamienna, przeszklone 2 górne kondygnacje, ciemny cokół (P12-P04, CC BY-SA → ref.) |
| Rosti, Myśliwska 18 | way 252332077 | 780 609, 590 204 | 18,92 | szara hala z płyt warstwowych, 2 bramy segmentowe, dachu nie widać (P11-094 — kadr przy jezdni) |
| BPN-T Inkubator, Żurawia 71 | — | (53.106874, 23.193275) | 18,09 | — |
| KAN, Karpińskiego 5 | way 471492581 | (53.104351, 23.190790) | 15,05 | dach ocynk (ESTIMATED) |
| Odlewnia, Myśliwska 11 | way 315456645 | 780 877, 590 342 | 13,08 | **w kaflu** (P12 mylnie „poza”) |
| LO J. Pawła II, Mickiewicza 95 | way 234838484 | (53.109891, 23.182440) | 13,23 | — |
| Bravilor, Kuronia 2 | way 513010463 | (53.105330, 23.187331) | 12,72 | jasnoszara hala, ciemnografitowe pasy z szyldem (P11-063) |
| Archiwum Państwowe, Mickiewicza 101 | — | (53.107864, 23.184172) | 12,22 | — |
| Masterpress, Kuronia 4 | way 234838499 | (53.105609, 23.191144) | 12,17 | — |
| BISON | way 658448323 | 780 871, 590 256 | 8,37 | **w kaflu** |
| Kontri, Kuronia 3 | — | (53.106752, 23.191379) | 6,01 | jasnoszara hala z pomarańczowym szyldem, brama przesuwna czarna (P11-001) |
| Pas 09R/27L asfalt 1350×30 | way 958211700 | 779 262, 589 869 | 0 | oznakowanie progu/strzałki (P12-A01) |
| Pas 09L/27R trawa 860 m | way 303368859 | w kaflu | 0 | — |
| Stacja 110/15 kV RPZ11 | — | 780 341, 590 181 | 5,15 (budynek) | słupy 110 kV UNVERIFIED |

**Poza kaflem 0166 (tylko sylwetka/tło):** hangar Aeroklubu way 304300294 (X 778 655 — **ok. 360 m na zachód od krawędzi; w `landmarks_d51.authored.json` 0166 jest jako L10 — przenieść do tła albo usunąć**), browar Dojlidy (X ≈ 781 140–781 300), BIAFORM (2 kominy), BIAWAR, kościół NSM, pałace Hasbacha/Lubomirskich, rondo Meyera (Y ≈ 592 100). Rondo Hasbacha leży na samej krawędzi wsch. (X 781 057–781 097).

**Generatory ruchu (bramy OSM, potwierdzone):** KAN lift_gate node 4656499172 (53.1034982, 23.1900064, `access=customers`); Masterpress lift_gate 2999986083 (53.1060181, 23.1922411); Bravilor gate 6539179208 (53.1058866, 23.187439); Rosti gate 6596800253 (53.1032347, 23.1932384) + druga ~25 m wg P12 (53.103204, 23.193609). PSS Społem D303 8 (way 1525885366, `building=industrial`) — wjazd UNVERIFIED. Korytarz tranzytu ciężarówek: **Kuronia → Dywizjonu 303 → Ciołkowskiego**; > 8 t zakaz na Mickiewicza (Kuronia–Ciołkowskiego); > 3,5 t zakaz na Suchowolca/Dojlidy Fabryczne (zgodne z g10).

**Wyposażenie (P12, OSM):** 25 przystanków (19 z wiatą — 6/6 próby zgodne z OSM); wiaty stare przeszklone z czerwoną ramą vs nowe antracytowe — który gdzie UNVERIFIED; 14 sygnalizacji; progi zwalniające ze znakiem A-11a; ekrany akustyczne 0; latarnie — brak w OSM; w kadrach Commons przy Kuronia/Karpińskiego/Mickiewicza widać **latarnie dwuramienne (Y) na wysokich masztach stalowych ~10 m (wysokość ESTIMATED z kadru)** oraz słupki biało-czerwone z łańcuchem przy wyspach (P11-001, 063).

**Najlepsze kadry do kamer kontrolnych (obejrzane, w kaflu 0166, CC0 — Rakoon):**
1. **P11-001** (53.106512, 23.189265; VI 2024) — Kuronia wzdłuż jezdni na wschód: hala z pomarańczowym szyldem, brama, DDR, latarnie Y, hala po prawej — **wzorcowy kadr SSSE**.
2. **P11-063** (53.105827, 23.184707; VI 2024) — skrzyżowanie w SSSE, hala z ciemnymi pasami szyldu, słupki z łańcuchem, sygnalizacja.
3. **P11-094** (53.105443, 23.196978; IX 2023) — szara hala zakładu przy jezdni z latarnią Y (to NIE brama browaru).
4. **P11-056** (53.104182, 23.176891; VIII 2023) — skrzyżowanie przy Dywizjonu 303 z tabliczką ulicy, łąka lotniska, nowe latarnie — kadr „pustej” krawędzi lotniska.
5. **P11-129** (53.109464, 23.190654; XI 2019) — brama szpitala Żurawia 14 ze szlabanem, STOP, mur z cegły — zima/późna jesień.
Dodatkowo do porównań lotniczych: **P12-A01** (ortofoto pasów). Kadry P11-084/091/092/064 — **nie używać** (treść inna niż opis).

## 5. Rekomendacja dla lidera

- **PR #39 (P11): nie scalać w obecnej postaci** — najpierw poprawki z §2 (min. usunięcie P11-090/091/092 i przepisanie opisów). Alternatywa, jeśli Mistral nie poprawi: scalić z adnotacją w README „opisy niezweryfikowane wzrokowo — patrz REVIEW s17” i usuniętymi 3 wierszami.
- **PR #40 (P12): można scalić** po poprawkach (1)–(3) z §3 (kafel, URL Commons, A-11a); poprawki (4)–(5) mogą pójść jako errata. Do 0166 przekazać §4 od razu (niezależnie od scalenia).
- Nic nie scalono, nic nie skomentowano na GitHubie, nic nie scommitowano.
