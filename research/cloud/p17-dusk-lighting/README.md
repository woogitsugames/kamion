# M60 — zmierzch w mieście: niebo, luminancja, oświetlenie ulic trasy, zapalone okna (cloud p17)

Stan: 2026-11-14. Źródła wyłącznie otwarte (D43). Bez Google/Bing/Apple/Yandex/Mapillary. Dane mają służyć **kalibracji** tego,
co gra już ma (ADR 0182, 0191, 0192) — patrz sekcja „Do porównania z ADR 0191/0192”.

Pliki: `manifest.csv` (87 wierszy C60-001…087), `sources.md`, `audit_20_percent.json`, `sun.py` (obliczenie astronomiczne),
`ortho_lamp_spacing.csv` (pozycje słupów z ortofoto), `build_manifest.py` + `frames_meta.json` (odtworzenie manifestu),
`fetch.py` (pobranie 24 kadrów do `files/` + sha256), `tools/` (pas ortofoto, rozstaw z OSM, zapytanie Overpass).

Statusy: SOURCED (cytat + URL), SOURCED_SECONDARY (źródło wtórne — nie potwierdza pomiaru samodzielnie), ESTIMATED (pomiar/szacunek
z jawną metodą), VERIFIED_WIZJA (opis obejrzanego kadru), ANALOG (inne miasto/obiekt), UNVERIFIED (brak), REJECTED.

## 1. Niebo i otoczenie o zmierzchu

| Wysokość Słońca | Wielkość | Wartość | Warunki | Źródło (wiersz) | Status |
|---|---|---|---|---|---|
| 0° | E poziome | 759 lx / 355 lx | bezchmurnie; dwie konwencje | Schlyter (C60-001) / Fotios 2024 za Muneerem (C60-008) | wtórne / SOURCED |
| −3° | E poziome | 79,1 lx | jw. | Schlyter (C60-002) | wtórne |
| −4° | E poziome | 29,9 lx | jw. | C60-003 | wtórne |
| −5° | E poziome | 10,4 lx | jw. | C60-004 | wtórne |
| **−6°** | E poziome | **3,41 lx / 4,3 lx** | koniec zm. cywilnego | C60-005 / C60-009 | wtórne / SOURCED |
| −7° | E poziome | 1,09 lx | | C60-006 | wtórne |
| −8° | E poziome | 0,348 lx | | C60-007 | wtórne |
| −18° | E poziome | 0,001 lx | koniec zm. astronomicznego | C60-010 | SOURCED |
| −4…−8° | E poziome, pochmurnie | — | | C60-011 | **UNVERIFIED** |
| −5 / −6 / −7 / −8° | L zenitu (pasmo V) | 2,0 / 0,52 / 0,15 / 0,048 cd/m² | bezchmurnie, Paranal 2635 m; nizina ok. +30 % jaśniej | Patat i in. 2006 (C60-012…016) | ESTIMATED (przeliczenie z mag/arcsec²) |
| ok. −3° (15 min po zachodzie) | L przy horyzoncie | ~1 cd/m² | bezchmurnie | Schlyter (C60-017) | wtórne, rząd wielkości |
| ok. −5° (30 min po zachodzie) | L przy horyzoncie | ~0,1 cd/m² | bezchmurnie | C60-018 | wtórne, rząd wielkości |
| 0° | L przy horyzoncie | ~10 cd/m² | pochmurnie | C60-019 | wtórne |
| −3…−8° | L horyzontu: strona Słońca vs przeciwna | — | | C60-020 | **UNVERIFIED** |
| zmierzch | barwa oświetlenia | najbardziej niebieska ok. −12° (wieś), ok. −6° (miasto); w mieście przesunięta ku czerwieni | pomiar spektralny | Spitschan i in. 2016 (C60-021, 022) | SOURCED (jakościowo) |
| ≤ −8° | niebo nad miastem | dominuje światło sztuczne (łuna) | Filadelfia | C60-023 | SOURCED |
| −6° | CCT horyzont vs zenit | — | | C60-024 | **UNVERIFIED** |

Spadek E na stopień wg tabeli Schlytera: −3→−4°: ×0,38; −4→−5°: ×0,35; −5→−6°: ×0,33; −6→−7°: ×0,32; −7→−8°: ×0,32.

Barwa nieba z kadrów (opis słowny, bez RGB): bezchmurnie przy −5,4° (C60-064): horyzont od jaśniejszej strony żółtawo-brzoskwiniowy,
wyżej blady róż-lawenda, górą niebieski — **róż leży nad pasem żółtawym, nie przy samym horyzoncie**. Bezchmurnie przy −4,1° i −5,1°
(C60-076, 087): równy błękit jaśniejszy ku dołowi. Pochmurnie przy −4,9° i −7,9° (C60-086, 071): jednolity ciemny granat, zero ciepłej
poświaty. Noc pod niskimi chmurami (C60-073): pomarańczowobrunatna łuna.

### Zmierzch cywilny w Białymstoku — obliczenie (`python3 sun.py table`)
Formuły NOAA Solar Calculator / Meeus (jawne w `sun.py`, stdlib), 53,1325° N 23,1688° E, elewacja geometryczna, czas urzędowy. ESTIMATED
(obliczenie; dokładność ok. 1 min wg NOAA; selftest: górowanie w przesileniach ±0,1°).

| Data (2026) | Zachód (−0,833°) | Słońce −3° | Koniec zm. cywilnego (−6°) | Słońce −8° | Zachód → −6° | Azymut Słońca przy −6° |
|---|---|---|---|---|---|---|
| 15.01 | 15:40 | 15:58 | 16:21 | 16:35 | 40 min | 243° |
| 15.02 | 16:38 | 16:54 | 17:14 | 17:28 | 36 min | 257° |
| 15.03 | 17:31 | 17:46 | 18:06 | 18:19 | 35 min | 275° |
| 15.04 | 19:27 | 19:43 | 20:04 | 20:19 | 37 min | 295° |
| 15.05 | 20:20 | 20:38 | 21:04 | 21:23 | 44 min | 313° |
| 15.06 | 20:56 | 21:16 | 21:48 | 22:11 | 52 min | 324° |
| 15.07 | 20:47 | 21:06 | 21:34 | 21:56 | 48 min | 319° |
| 15.08 | 19:55 | 20:11 | 20:34 | 20:50 | 39 min | 303° |
| 15.09 | 18:43 | 18:58 | 19:18 | 19:32 | 35 min | 283° |
| 15.10 | 17:32 | 17:47 | 18:07 | 18:20 | 35 min | 264° |
| 15.11 | 15:32 | 15:48 | 16:11 | 16:25 | 39 min | 247° |
| 15.12 | 15:10 | 15:28 | 15:52 | 16:08 | 42 min | 239° |

## 2. Ulice trasy

Klasy wg EN 13201-2:2015 (wartości ze strony streszczającej normę — SOURCED_SECONDARY; M1/M2/M6 potwierdzone w publikacji CC BY i wydruku
DIALux z przetargu; treści normy nie kopiowano): M1 2,0 / M2 1,5 / M3 1,0 / M4 0,75 / M5 0,50 / M6 0,30 cd/m²; Uo 0,40 (M1–M4), 0,35 (M5–M6);
Ul 0,70 / 0,70 / 0,60 / 0,60 / 0,40 / 0,40; fTI 10 / 10 / 15 / 15 / 15 / 20 %. Strefy konfliktowe: C2 20 lx, C3 15 lx, C4 10 lx, C5 7,5 lx, Uo 0,40.

| Ulica | Klasa / L / Uo | Wysokość montażu | Rozstaw słupów | Źródło światła |
|---|---|---|---|---|
| ul. gen. Andersa | UNVERIFIED | UNVERIFIED | **41,6 m** (mediana, n=6; 39,5–43,3) — rząd w pasie dzielącym; rzędy boczne 38,7 i 42 m | LED: ulica w przetargach ZDM 2023 (I) i (II) — C60-037, 040; udzielenie 30.10.2023 (C60-043). Wcześniej sód (ADR 0191: kadry 2019) |
| Al. Tysiąclecia PP | UNVERIFIED | UNVERIFIED | **34,8 m** (n=7; 33,6–36,7), odc. południowy, słupy w pasie dzielącym | LED: przetarg 2023 (I) (C60-038). 10.02.2022 światło żółtopomarańczowe (kadr C60-061) |
| ul. gen. Maczka | UNVERIFIED | UNVERIFIED | **40,4 m** (n=6; 39,5–41,0), pas dzielący | LED: przetarg 2023 (I) (C60-039) |
| rondo Putry | UNVERIFIED (właściwa klasa C) | UNVERIFIED | UNVERIFIED | UNVERIFIED |
| ul. Sokólska | UNVERIFIED | UNVERIFIED | 32,4 m (n=5; 26,3–35,5; z cieni, niska pewność) | UNVERIFIED |
| ul. Wysockiego | UNVERIFIED | UNVERIFIED | nie mierzono | LED: przetargi 2023 (II) i 2024 (I) (C60-041, 042) |
| ul. Kombatantów | UNVERIFIED | UNVERIFIED | 32,6 m (n=3, węzły OSM) | UNVERIFIED |

Rozstaw = ESTIMATED z ortofoto GUGiK (metoda i współrzędne: `ortho_lamp_spacing.csv`, `tools/strip.py`). Zakres odcinków objętych wymianą
i daty montażu — UNVERIFIED (pełne teksty ogłoszeń 2023 niedostępne; frazy potwierdzone wyszukiwaniem pełnotekstowym API TED).
Załączanie latarni w Białymstoku (zegar/próg lx) — UNVERIFIED; analog Augustów: 10 min po zachodzie (C60-054). Z kadrów: latarnie
świecą przy Słońcu −3,1° (C60-083), −3,7° (C60-075), −4,1° (C60-076), −5,4° (C60-064); kadru z przedziału 0…−3° z EXIF nie znaleziono.
CCT opraw ZDM — UNVERIFIED (C60-045); analog BPN-T (parking, 2026): 4000 K ± 200 K, ≥ 16,5 klm (C60-046).

## 3. Zapalone okna

Literatura: maks. 50 % okien świecących na osiedlu bloków (Výškovice, pomiar terenowy) i średnia luminancja okna 6 cd/m² (Novak i in.
2025, C60-055…057); światło z mieszkań najsilniejsze na początku nocy i maleje do ok. 04:00 (Bará i in. 2017, C60-059). Polskiego badania
z odsetkiem w funkcji godziny nie znaleziono (C60-060).

Zliczenia z kadrów Białegostoku (ESTIMATED; ręcznie, ±2 okna zapalone, ±10 % mianownika; okna pod ostrym kątem pominięte):

| Wiersz | Budynek | Data, godz. (EXIF), dzień | Słońce | Zapalone / widoczne |
|---|---|---|---|---|
| C60-083 | blok 8-kond. | 2021-09-22 18:41 śr. | −3,1° | 7/110 = 6 % |
| C60-075 | blok 4-kond. | 2020-11-28 15:39 sob. | −3,7° | 8/40 = 20 % |
| C60-076 | blok 5-kond. | 2019-11-10 16:04 niedz. | −4,1° | 9/32 = 28 % |
| C60-077 | blok 5-kond. | 2021-11-19 16:32 pt. | −9,8° | 12/50 = 24 % |
| C60-081 | blok 5-kond. | 2023-01-22 17:37 niedz. | −15,4° | 10/45 = 22 % |
| C60-082 | blok 5-kond. | 2023-01-22 17:38 niedz. | −15,5° | 8/17 = 47 % (zawyżone — ciemne okna niewidoczne) |
| C60-079 | bloki 5-kond. | 2021-12-03 18:35 pt. | −29,2° | 17/62 = 27 % (w części dobrze widocznej 5/32) |
| C60-080 | blok 4-kond. z usługami | 2021-12-04 18:52 sob. | −31,7° | 2/34 = 6 % |
| C60-084 | biurowiec/urząd | 2021-12-16 15:57 czw. | −6,6° | 5/22 = 23 % |
| C60-078 | biurowiec spółdzielni | 2021-11-19 16:32 pt. | −9,8° | 7/21 = 33 % |
| C60-087 | biurowiec przeszklony | 2025-03-12 17:55 śr. | −5,1° | 6/11 = 55 % (pola przeszkleń) |
| C60-085 | biurowiec/urząd | 2022-03-24 18:44 czw. | −9,2° | 1/30 = 3 % |
| C60-086 | pawilony usługowe, piętro | 2023-01-20 16:20 pt. | −4,9° | 2/10 = 20 % |

Wnioski: (a) mieszkania o zmierzchu i wczesnym wieczorem: typowo 20–28 %, rozrzut 6–47 %; nigdzie nie widać 40–50 % na całej elewacji;
(b) przy −3° okna dopiero zaczynają się zapalać (6 %), gdy latarnie już świecą; (c) biura zależą od godziny zegarowej, nie od Słońca:
23–55 % w godzinach pracy, ~3 % o 18:44; (d) okna świecą nierówno — od ciepłej żółci i pomarańczu po zimną biel, pojedyncze czerwone
(zasłona); ciemne okna z jasnymi firanami są szare od latarni, nie czarne; (e) klatki schodowe świecą pionem wąskich okien (C60-079).

## 4. Kadry ulic o zmierzchu i w nocy (13 + 1 odrzucony)

Wszystkie z Białegostoku; **tylko 3 z okolic trasy** (C60-061…063, rejon Al. Tysiąclecia/Kombatantów, 10.02.2022) i 1 przy
ul. Wysockiego (C60-064, parking); 7 z ul. Lipowej i śródmieścia (C60-065…071), 2 z osiedli (C60-072, 073). Nocnych kadrów Andersa,
Maczka, ronda Putry w otwartych źródłach nie znaleziono (Commons: geosearch 9 punktów trasy, 1615 plików; Panoramax: brak sekwencji
o zmierzchu w bbox).

- **Plamy:** na suchych jasnych płytach (C60-065) przejścia są łagodne — jaśniej pod latarnią, ciemniej między, bez krawędzi. Na mokrej
  nawierzchni (C60-061, 067, 069) dominują podłużne smugi odbić skierowane do obserwatora, a nie plamy rozproszone; między smugami ciemno.
  Pojedyncza oprawa LED na osiedlu (C60-072) daje wyraźną plamę o ostrym zaniku w czerń. Przy −5,4° (C60-064) plam jeszcze nie widać.
- **Barwa:** Al. Tysiąclecia w lutym 2022 — żółtopomarańczowa (wygląd sodowy); ul. Lipowa 2020–2022 — pomarańczowa; parkingi i osiedla
  2022–2023 — biała/zimna. Ocena wzrokowa z kadrów telefonu (balans bieli automatyczny) — nie CCT.
- **Halo:** każda świecąca oprawa ma okrągłą poświatę, często z promieniami; rozmiar rośnie z jasnością źródła i wilgocią (C60-066 bardzo
  duże). To efekt obiektywu telefonu — zgodne z kierunkiem ADR 0192, skali nie da się zmierzyć.
- Jasność kadrów nie jest miarą luminancji (automatyka ekspozycji, ISO 160–2000).

## Do porównania z ADR 0191/0192 (i 0182)

| Parametr gry (ADR / kod) | Wartość w grze | Wartość referencyjna | Jedn. | Źródło (wiersz) | Status ref. | Jak porównać |
|---|---|---|---|---|---|---|
| `SkyModel.CivilTwilightEndLux` (0182; w kodzie „UNVERIFIED from memory”) | 3,4 | 3,41 (Schlyter za Expl. Suppl.); 4,3 (Fotios/Muneer) | lx | C60-005, 009 | wtórne / SOURCED | zgodne z dolną wartością; widełki 3,4–4,3. Test EditMode: E z kopuły przy −6° w tych widełkach |
| `TwilightFactorAt` — spadek na stopień (0182) | ~0,37×/° stałe od 0,5° do −6° | 0,53 (0→−1°), 0,38 (−3→−4°), 0,33 (−5→−6°), 0,32 (−7→−8°) | ×/° | C60-001…007 | wtórne | krzywa referencyjna nie jest log-liniowa: gra za ciemna przy 0…−3°, zbieżna przy −6°. Porównać E(el) w 7 punktach |
| Natężenie z nieba z mgiełką presetu (0182) | 2,87 | brak danych o mgle/zachmurzeniu | lx | C60-011 | UNVERIFIED | — |
| Luminancja zenitu przy −6° (pośrednio `ApplyTwilightChroma`) | nie podano | 0,5 (Paranal) → ok. 0,7 (nizina) | cd/m² | C60-013, 016 | ESTIMATED | odczytać luminancję zenitu LUT przy −6° (cd/m² przed ekspozycją) |
| Luminancja przy horyzoncie przy −3…−5° | nie podano | ~1 → ~0,1 | cd/m² | C60-017, 018 | wtórne (rząd) | stosunek horyzont/zenit w LUT: rząd 1–2× przy −5…−6° |
| Barwa horyzontu (0192 `SuppressTwilightMagenta`; 0192 „koralowy pas” otwarte) | B < G w stronę Słońca | żółtawo-brzoskwiniowy przy horyzoncie, róż/lawenda wyżej, błękit górą; pochmurnie — granat bez ciepła | opis | C60-064, 071, 086 | VERIFIED_WIZJA | zestawić render `route_putry` z kadrem C60-064 (ten sam rząd −5…−6°): pas różu ma być NAD pasem żółtawym |
| Azymut Słońca w `LP_Dusk` (0182) | 300° przy −6° | 295° 15.04; 303° 15.08 | ° | sun.py | ESTIMATED (obliczenie) | preset odpowiada połowie kwietnia / połowie sierpnia; „~40 min po zachodzie” = 37–39 min ✓ |
| Luminancja jezdni pod oprawą (0182: „M3–M5 0,5–1,0”) | 0,5–1,0 | M3 1,0; M4 0,75; M5 0,50 (średnia eksploatacyjna, nie „pod oprawą”) | cd/m² | C60-027…029 | wtórne | wartość normowa to ŚREDNIA z pola; klasa ulic trasy UNVERIFIED |
| Równomierność: min/szczyt 0,49 / 0,44 / 0,46 / 0,20 (0191) | min/max E | Uo = min/średnia L ≥ 0,40 (M1–M4), 0,35 (M5–M6); Ul = min/max wzdłuż osi pasa ≥ 0,60 (M3–M4), 0,40 (M5–M6) | – | C60-025…030 | wtórne | inna definicja: policzyć w `StreetLampOpticsTests` min/średnia i min/max w osi pasa; 0,20 (h 8/S 30) byłoby poniżej każdej klasy M |
| Podłoga nocna `NightFloorLux` (0191 s20) | 1 | brak danych | lx | — | UNVERIFIED | jakościowo: między latarniami nie jest czarno (C60-061, 065) |
| Natężenie I0 / strumień w dół (0191) | 2500 cd / 6,9 klm; oprawa 8–12 klm | analog: oprawa LED ≥ 16,5 klm, 95–150 W (parking BPN-T) | klm | C60-046 | ANALOG | gra w dolnym zakresie; dla GP z rozstawem ~41 m rozważyć większy strumień |
| Rozstaw `standards.LAMP` GP (0191: 36 m przy h 11) | 36 | Andersa 41,6; Maczka 40,4 | m | C60-047, 048 | ESTIMATED (ortofoto) | podmienić rozstaw GP na ~41 m lub override per ulica; przeliczyć „doły” przy S/h ≈ 3,7 |
| Rozstaw G / Z / L (33 / 30 / 30) | 33 / 30 / 30 | Al. Tysiąclecia (odc. płd.) 34,8; Sokólska 32,4; Kombatantów 32,6 | m | C60-049…051 | ESTIMATED | zgodne w granicach ±3 m |
| Układ słupów na ulicach dwujezdniowych | reguła: przy krawędzi | Andersa, Maczka, Tysiąclecia: rząd w pasie dzielącym (Maczka, Tysiąclecia — oprawy na obie strony) | – | C60-047…049 | ESTIMATED | sprawdzić `lamp_double_*` w pasie dzielącym na tych ulicach |
| Wysokość montażu GP (0162/0191) | 11 | brak dla ulic trasy | m | C60-052 | UNVERIFIED | — |
| Sód vs LED per oprawa (0191; „stan dzisiejszy UNVERIFIED”) | DK8 LED | Andersa, Maczka, Al. 1000-lecia, Wysockiego: przetargi LED 2023–2024; do 02.2022 Al. Tysiąclecia żółtopomarańczowa | – | C60-037…043, 061 | SOURCED (przetarg) / WIZJA | „świat współczesny” = LED na trasie ✓; sód zostawić dla śródmieścia (Lipowa pomarańczowa do 12.2022) — stan 2026 UNVERIFIED |
| Barwa LED `k_Led` (1; 0,93; 0,82) | biel ciepła | ZDM: brak; analog 4000 K ± 200 K; kadry: biała/zimna | K | C60-045, 046, 072 | UNVERIFIED / ANALOG | kolor w grze wygląda na ~3000–3500 K; referencja sugeruje neutralną biel 4000 K |
| Włączenie latarni | (wg presetu) | świecą przy −3,1°; analog: 10 min po zachodzie (≈ −1,5…−2,3°) | ° | C60-083, 054 | WIZJA / ANALOG | latarnie mają świecić najpóźniej od ok. −2…−3° |
| Glare K = 0,4, 3° (0192) | WORKING_VALUE | halo obecne przy każdej oprawie; skala niemierzalna | – | C60-061…073 | VERIFIED_WIZJA | ocena wzrokowa obok kadrów C60-061, 065, 072 |
| Luminancja soczewki 2·10⁵ cd/m² | WORKING_VALUE | brak | cd/m² | — | UNVERIFIED | — |
| Udział okien: mieszkania (0192) | 0,40 → 0,50 | 6–28 % o zmierzchu, 22–27 % wieczorem (kadry); maks. 50 % (literatura) | – | C60-075…083, 055 | ESTIMATED / SOURCED | gra ~2× za wysoko o zmierzchu; 0,5 to górna granica, nie typ |
| Włączanie okien 4° → −2° (0192) | pełny udział od −2° | przy −3,1° dopiero 6 %; 20–28 % przy −3,7…−10° | – | C60-083, 075…077 | ESTIMATED | przesunąć rampę na ok. 0° → −8° |
| Udział okien: biura (0192) | 0,65 → 0,15 wg Słońca | 23–55 % w godzinach pracy, 3 % o 18:44 | – | C60-078, 084, 085, 087 | ESTIMATED | uzależnić od godziny zegarowej (zimą zmierzch 16:00 = biura pełne; wiosną 20:00 = puste) |
| Udział: klatki 0,35, hale 0,45 → 0,30 | WORKING_VALUE | klatki: pion świecących okien widoczny w 1 kadrze; hale — brak | – | C60-079 | brak danych | — |
| Luminancja okna (0192) | 15 × ekspozycja | 6 (średnia, bloki, firany) | cd/m² | C60-056 | SOURCED | gra 2,5× jaśniej; reklamy/szyldy ~50 cd/m² (C60-058) |
| CCT okien 2700/3200/4000/4500 K, jasność ×0,55–1,45 | wg klasy | mieszkania: od ciepłej żółci po zimną biel i kolory zasłon; biura: zimna biel | opis | C60-077, 078, 082 | VERIFIED_WIZJA | rozrzut barwy w obrębie mieszkań większy niż jedna CCT na klasę |

## Luki (co sprawdzono)
- Klasa oświetleniowa, wysokość montażu, CCT i próg załączania dla ulic trasy — brak w otwartych dokumentach (TED API, 5 orzeczeń KIO,
  OPZ BPN-T; strony TED, MDPI, DTIC, AMS, ugr.es zwracały 202/403 lub puste przez proxy).
- Natężenie o zmierzchu pochmurnym, luminancja horyzontu po stronie Słońca i przeciwnej, CCT horyzont/zenit — brak liczb.
- Tabela E(elewacja) pochodzi ze źródła wtórnego (FAQ) — oryginału (Explanatory Supplement) nie otwarto.
- Kadry: brak nocnych zdjęć Andersa/Maczka/Putry; kierunki kadrów UNVERIFIED (brak azymutu w EXIF/API); 7 z 13 kadrów ulicznych
  to śródmieście z iluminacją świąteczną w 4 z nich.
- Pliki: Commons blokował pobieranie oryginałów (HTTP 429, Retry-After 600) — `url_pliku`/`sha256` dotyczą **miniatur 1920 px**
  (to je oglądano); `url_oryginału` i `sha1_oryginału` (z API) są w osobnych kolumnach. KartaView nie sprawdzono.
- Zliczenia okien obciążone: ciemne okna na nieoświetlonych elewacjach są niewidoczne (zawyża odsetek nocą).

## Samokontrola 20 %
Seed `random.Random(20261114).sample(range(87), 18)` → 18 wierszy (10 dokumentowych, 8 z kadrem). Dokumentowe: cytaty odszukane
ponownie w zapisanych tekstach źródeł (6/6 z cytatem — zgodne), linki 8 źródeł: 6× HTTP 200, 1× 301 (przekierowanie), TED 202 (strona za ochroną przed botami —
treść potwierdzona przez API). Kadry: 8 obejrzanych ponownie (w tym wycinki b01 i r09, s08); przeliczono okna b01 (9/32 — bez zmian).
Poprawki po wylosowaniu próby: 0. Przed audytem (autokontrola przy budowie manifestu): C60-071 — elewacja w polu „wartość”
−7,6° → −7,9°; usunięto 6 domysłów lokalizacyjnych z pola „element” (zastąpione „wg współrzędnych/kategorii Commons”);
odrzucono 12 pobranych kadrów (wnętrza, dzień wg EXIF mimo „wieczornej” nazwy pliku, same szyldy). Szczegóły: `audit_20_percent.json`.

## Errata lidera (s20, 2026-11-14)
Patrz `docs/reports/REVIEW-2026-11-14-s20-cloud-m60-compare.md`: przy zachodzie gra jest ZA JASNA (do ×2,3 przy +0,5…−1°), nie za ciemna; stosunek horyzont/zenit 0,05–0,2×; zdjęcia 1920 px.
