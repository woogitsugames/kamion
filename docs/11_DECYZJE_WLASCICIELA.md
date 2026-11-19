# 11 — Decyzje właściciela (stan 2026-11-09)

Decyzje podjęte przez właściciela przed startem. Zmiana wymaga ADR i jego zgody.

| # | Temat | Decyzja | Konsekwencje dla sesji |
|---|---|---|---|
| D1 | Silnik | **Unity 6.3 LTS + URP** | Unreal/Godot odrzucone; wracamy do tematu tylko z twardym dowodem z urządzenia |
| D2 | Skala | **Miasta 1:1, trasy między miastami skrócone** | Białystok ulica po ulicy; współczynnik tras ADR-em w Etapie 7 |
| D3 | Urządzenia | **Flagowiec = cel jakości (High/Ultra), Samsung A = minimum (Medium/Low)** | Na razie jest tylko Samsung A (USB debug). Flagowca brak, a budżet zakupów to 0 zł → zgłoś, kiedy brak flagowca zacznie blokować strojenie High; do tego czasu wyniki High oznaczaj jako niezmierzone |
| D4 | Start mapy | **Strefa przemysłowa Białegostoku + wylot na trasę** | Sesja proponuje 2–3 kandydatów po analizie OSM/BDOT, właściciel wybiera i robi zdjęcia |
| D5 | Rozwój mapy | **Najpierw cały Białystok perfekcyjnie, potem obrzeża**, potem Podlasie, Polska, kraje DLC | Dzielnicami, każda przez bramkę jakości |
| D6 | Ciężarówka | **Własna fikcyjna marka**, oryginalne wzornictwo | 3 propozycje nazwy/logo/sylwetki do wyboru |
| D7 | Model 3D | **Robią agenci** (Blender), bez zakupów | Pipeline `docs/07`, pętla renderów kontrolnych, `visual-critic` |
| D8 | Audio | **Darmowe/CC0 + generowane** (AI, synteza); Suno ewentualnie | Suno free = brak praw komercyjnych → `PROTOTYPE_ONLY` |
| D9 | Budżet zakupów | **0 zł** | Nie proponuj zakupów jako rozwiązania domyślnego; jeśli coś jest nie do zrobienia bez wydatku, opisz problem, alternatywy i koszt — decyzja właściciela |
| D10 | Sterowanie v1 | **Kierownica dotykowa + pedały, gyro** | Gamepad i kierownica USB: architektura gotowa, implementacja później |
| D11 | Repo | **Prywatne GitHub** + LFS | Uważaj na limity LFS; surowe geodane poza gitem |
| D12 | Jakość wizualna | **Zero AI slop, nie jak typowa gra truck z Google Play** | `docs/06` jest wiążący; bramka wizualna blokuje merge |
| D13 | Agenci | **Do 10 agentów Opus** | `docs/09` |
| D14 | Platformy | **Android najpierw, iOS później** z tego samego projektu | Kod platformowo neutralny od dnia 1 |

## Otwarte (zdecyduj z właścicielem w odpowiednim momencie, nie teraz)
- Nazwa gry i marki ciężarówki (propozycje sesji w torze A2).
- Model biznesowy (premium / free + DLC) — przed Etapem 8.
- Współczynnik skali tras — Etap 7.
- Zakup lub pożyczenie flagowca — gdy zacznie blokować.
- Opinia prawna dot. ODbL/derived database — przed publikacją.

## Decyzje z 2026-11-09 (sesja 1)
| # | Temat | Decyzja |
|---|---|---|
| D15 | Obszar startowy (D4) | **Kandydat C**: Kwadrat Park → ul. gen. Andersa → Rondo Putry → DK8/DK19 Al. Tysiąclecia (`docs/map-decisions.md`) |
| D16 | Koncepcja ciężarówki (D6) | **Koncepcja B** (aero) jako baza |
| D17 | Marka (robocza) | **TRAKT** — przed publikacją sprawdzenie znaków towarowych (EUIPO/UPRP) |
| D18 | Repo | **Publiczne** zostaje (zmiana względem D11) |
| D19 | Wykończenie kabiny | **Koniak** (trim), badge TRAKT na piaście |
| D20 | Zegary | **Tylko ekran 12,3"** (bez tarcz analogowych) |
| D21 | Audio (demo) | Kierunek zaakceptowany („brzmi jak ciężarówka”) |
| D22 | Build Unity w CI | Później; na razie build lokalny |
| D23 | Wygląd nieba/ekspozycji | **„Jak zdjęcie z telefonu”** — jaśniejsze niebo i obraz, łagodniejszy kontrast (zamiast ekspozycji światłomierzowej) |

## Decyzje z 2026-11-10
| # | Temat | Decyzja |
|---|---|---|
| D24 | Rozmiar świata w APK (E6) | Na razie **bez Play Asset Delivery**; limit podniesiony: świat (Low/Medium) w APK **≤ 110 MB** (WORKING_VALUE dla regionu startowego; zmierzone 94,4 MB górnej granicy po ADR 0025). Wracamy do tematu przy kolejnym regionie |
| D25 | Test jazdy właściciela | **Po raporcie bramki 3** — APK ze wszystkimi poprawkami, instrukcja `docs/owner/FEEL-TEST.md` |
| D26 | Modele 3D | Agenci modeli (truck-artist, Blender) na **Fable 5.2**; shadery/światło/świat na Opus |
| D27 | Balans bieli przy niskim słońcu | **„Jak w telefonie” 0,5** w `LP_LowSun` (ADR 0043 opcja c); pozostałe presety bez adaptacji |
| D28 | Kabina TRAKT | **Nowy nowoczesny front** (wariant `modern`, Fable 5.2): czarna maska „T”, wąskie LED w narożnikach, zderzak jedną bryłą, czapa dachu ze spojlerem, lekka wypukłość czoła R 10 m; zdjęcia prasowe właściciela tylko jako wzór stylu, bez cech cudzej marki |
| D29 | Pochylenie przodu | **1,5°** w widoku z boku (zamiast 7°), przód w jednej płaszczyźnie |
| D30 | Próg połysku lakieru ciężarówki (r6 E1, r7) | Refleks na płaskich drzwiach **4–10 pkt** (Volvo FH na zdjęciu 5–8; ≥ 15 odrzucony jako nieosiągalny) **+ nowy wymóg**: refleks na krzywiźnie (narożnik kabiny, deflektor dachu) **≥ 10 pkt High / ≥ 6 pkt Low** |
| D31 | Szyba ciężarówki z zewnątrz (r6 E2, r7) | p50 jasności **33–45 %** (Fresnel; ≥ 60 % odrzucony) **+ wymóg treści odbicia σ ≥ 8** (r7: 4,5 = FAIL, do poprawy) |
| D32 | Szyby aut osobowych (r7) | Prostopadle **≤ 32 % pochmurno / ≤ 26 % słońce**, kąt ostry / prostopadły **≥ 1,3×** (wg zdjęcia CC0 7197); model nieba ADR 0010 bez zmian |
| D33 | Kierownica przy niskim słońcu (do D27) | Próg **względny**: R−B ≤ 6 % i nasycenie ≤ nasycenia białej powierzchni w tym samym świetle (zamiast sat ≤ 15 %); WB 0,5 bez zmian |
| D34 | Korekta D31 (po naprawie capture odbić, ADR 0056) | Szyba z zewnątrz p50 **23–45 %** (dolna granica wg zdjęcia Volvo FH; 33 % zakładało odbicie samego nieba); σ ≥ 8 zostaje celem |
| D35 | Korekta D30 — gdzie mierzyć krzywiznę | Refleks ≥ 10 pkt High / ≥ 6 pkt Low mierzony na **deflektorze dachu**; narożnik kabiny tylko przy niskim słońcu / słońcu (pionowa ściana poniżej kamery odbija ziemię) |
| D36 | S24+ High nie trzyma 60 kl./s (r8: 43–47 kl./s, p95 33,4 ms) | Dolny próg dynamicznej skali renderu na High **0,70** (zamiast 0,80); A/B na S24+ przed zamknięciem (szacunek GPU 12–15 ms UNVERIFIED) |
| D37 | Jasność farby/zebry (r8: zebra 233 sRGB) | Próg **względny**: farba/asfalt **1,7–2,3** w słońcu; **≤ 235 sRGB** w słońcu, **≤ 217** przy pochmurnym (zastępuje twarde ≤ 217) |
| D38 | Wyprane kolory przy słońcu (r8: trawa sat 28 vs 33–58 na zdjęciach) | Podnieść nasycenie **albedo trawy do 35–40** (materiał, bez zmian post-procesu) |
| D39 | Panel deweloperski w APK | **Zostaje widoczny** — na razie grają tylko właściciel i lider |
| D40 | Skany CC0 (zmiana ADR 0010) | **Zgoda**: skany CC0 z Poly Haven i ambientCG jako baza materiałów świata (licencja każdego zasobu sprawdzana i wpisana do `docs/LICENSES.md`); generatory dalej robią rozkład, zużycie i warianty |
| D41 | Zdjęcia trasy startowej | Właściciel **zrobi własne zdjęcia** trasy (Kwadrat Park → Andersa → Rondo Putry → DK8) wg listy ujęć od lidera — do tekstur fasad i dopasowania kadrów |
| D42 | Źródła referencji ulicznych | **Mapillary** (CC BY-SA 4.0) dozwolone jako referencja i do dopasowania kadrów — z atrybucją autorów w `docs/LICENSES.md`; Google Maps/Street View/Earth nadal zakazane (także zrzuty z Gemini) |
| D43 | Zmiana D41 — zdjęcia trasy | Właściciel **nie zrobi** własnych zdjęć. Referencje zbiera lider/agenci z otwartych źródeł: Mapillary (D42), KartaView, Panoramax, Wikimedia Commons, Openverse (CC), GUGiK (ortofotomapa, LoD2, NMT), otwarte dane Miasta Białystok; licencja każdego zasobu sprawdzana; Google nadal zakazany |
| D44 | Korekta D31/D34 — treść odbicia szyby TRAKT | σ ≥ 8 mierzone tylko przy **niskim słońcu / słońcu**; przy pochmurnym wymóg **σ ≥ 0,7 × σ kadru bez szyby** (ADR 0059: σ ≥ 8 przy overcast nieosiągalne — sam kadr bez szyby ma 5,0–5,5) |
| D45 | Fab (rozszerzenie D40), 2026-11-10 s6 | **Zgoda**: z Fab wolno brać **Megascans** (Fab Standard License, bez atrybucji) i pozycje z **potwierdzoną CC BY** (atrybucja w grze i `docs/LICENSES.md`). Pliki Fab Standard leżą **poza publicznym repo** (`Data/raw/fab/`, `_Generated/`); w gicie tylko manifest + wpis licencji; test, że nic z Fab nie jest śledzone. Pobiera właściciel na swoim koncie Epic (darmowe Megascans do 12.11). Megaplants (tylko Unreal) nie; Patch nie. Raport: `docs/reports/FAB-PATCH-LICENSE-2026-11-10.md` |
| D46 | Ogranicznik na zjeździe, 2026-11-10 s8 | **Dopuszczać ~94 km/h jak w realu**: ogranicznik 90 km/h nie hamuje, na zjeździe zestaw może się rozpędzić do ~94 km/h, potem retarder (`driveline.overrunBrakeOffsetKmh = 4` zostaje; ADR 0082) |
| D47 | Naczepa i ciągnik TRAKT, 2026-11-10 s8 | Firanka naczepy **bez pasa** (wariant B, rendery `artifacts/truck-ext-r10/owner-band/`); **osłony boczne ciągnika zostają** (ADR 0083) |
| D48 | Tynk remizy JRG2 (0086), 2026-11-11 s10 | Właściciel po obejrzeniu zdjęcia 7197 i renderów przed/po (`artifacts/tint-gamma-r1/owner-remiza/`): **zostaje cel 110/126/145 ±10** (overcast), mimo uwagi krytyka o zimnym balansie bieli (`REVIEW-2026-11-11-s10-0086.md` P1-1) |
| D49 | Profil A16 dla bramki 3, 2026-11-11 s10 | **A16 (Mali-G57) oficjalnie Low** — bramka 3 mierzona na A16 w Low (Medium 21,7 FPS, ADR 0106); Medium/High stroimy na S24+ |
| D50 | Skala renderu Low, 2026-11-11 s10 | **Bez obniżania do 70 %** — najpierw druga runda wydajności (las HLOD, korony, impostory, prewarm shaderów, skok CPU G3-A t≈55 s) |
| D51 | Priorytet bramki 3, 2026-11-11 s10 | **Rozpoznawalność trasy > dopracowanie materiałów.** Bramka 3 ma potwierdzić, że kierowca rozpozna drogę: układ jezdni, pasy, skrzyżowania i ronda, wiadukty, oznakowanie i bramownice, charakterystyczne budynki i obiekty, ich położenie i proporcje — „z grubsza podobne” do zdjęć. Kolor nieba/ekspozycja, odcień trawy, tekstury i drobne zużycie (dziury, łaty) dopracujemy później; nie blokują bramki 3 |
| D52 | Kolejność UI na składanym ekranie, 2026-11-12 s12 | **Pełne dopasowanie HUD do Folda (~1:1) po bramce 3**; teraz tylko kierownica dotykowa i orientacja (ADR 0135) |
| D53 | Domyślny ładunek, 2026-11-12 s12 | **Na starcie gry naczepa ładowna 24 t** (zestaw ~40 t), nie pusta — realistyczne przyspieszanie i zmiany biegów (ADR 0134) |
| D54 | Inne pojazdy, 2026-11-12 s15 | **Później** (po ciężarówce): samochody osobowe, autobusy miejskie, autokary itp. jako pojazdy grywalne — „mamy mapę, szkoda się ograniczać”. Teraz bez zmiany zakresu (jedna ciężarówka perfekcyjnie), ale: (1) architektura pojazdu zostaje danymi (`*.vehicle.json`, ADR fizyki), nic nie zakłada „tylko ciągnik + naczepa” na sztywno; (2) **odrzucone ujęcia ElevenLabs nie są kasowane** (`art-source/audio/elevenlabs/`, 348 WAV, licencja Pro komercyjna) — kandydaci dla innych pojazdów (pneumatyka, hamulce, retarder, sprężarka, drzwi, opony → autobus/autokar; diesel ciężarowy → autokar); (3) modele aut ruchu AI z etapu 5 projektować tak, by mogły zostać pojazdami grywalnymi |
| D55 | Kierowanie po r2/r3, 2026-11-12 s15 | Test właściciela na Foldzie (APK `e364975f12`): **„jest spoko, już lepiej się jeździ”** (ADR 0149, 0151) |
| D56 | Windows, 2026-11-12 s15 | **Później pełna wersja na Windows z obsługą kierownic** (force feedback, pedały, skrzynia H; klawiatura/pad), wyższe profile jakości na PC, HUD pod monitor. Kolejność: najpierw bramka 3 na telefonach. Od teraz nie wiązać kodu na sztywno z dotykiem/mobile (wejście przez warstwę sterowania, profile jakości jako dane) |
| D57 | Bramka 3, 2026-11-13 s16 | **PASS — właściciel rozpoznaje miejsca** w pakiecie 12 par zdjęcie\|render (`artifacts/owner-package-s16`; krytyk 27 R / 15 P / 0 N z 42; A16 Low G3-A i G3-B 30 FPS, p95 33,4 ms, kamery 57/57 i 46/46, APK `3ffbf13881`). Poprawki 0161–0163 jako dopracowanie |
| D58 | Krawężnik 27 cm (ADR 0158), 2026-11-13 s16 | **Podatny (tłumiony) kontakt nadwozia z ziemią** zamiast sztywnego; limity szarpnięcia zostają |
| D59 | Przegub naczepy F1 (ADR 0158), 2026-11-13 s16 | **Miękki ogranicznik bez zmian, tolerancja nadmiaru ≤ 3,5°** |
| D60 | Następny region, 2026-11-13 s16 | **Dojlidy / Krywlany** (najsilniejsze skupisko celów ciężarówek wg G2) |
| D61 | Mistral, 2026-11-13 s16 | **Runda 7 tak** — długie sesje, w PR surowe wyjście komend zamiast tabel |

## D62 — 0162: +10 draws na dojeździe do ronda Putry od Al. Tysiąclecia przyjęte (2026-11-13, s17)
Kamera `g3b-rondo-putry-approach` 421 → 431 wywołań (Low, ok. +2 %) przez 3 rzeczywiste konstrukcje oznakowania z 2024 (5 tablic; portal P005–P008, E-1 P009, VMS P010). Pozostałe kamery −10…+3. Przyjęte bez wtapiania tablic w siatkę bramownicy; weryfikacja pomiarem A16 po wspólnej regeneracji świata.

## D63 — Najpierw z grubsza, potem detale (2026-11-14, s20)
Właściciel: „nie możesz z grubsza zrobić a potem detale? W takim tempie to nic nie zrobimy”. Nowe regiony (od obwodnicy S8/DK8/DK19) powstają najpierw w wersji przejezdnej z danych (drogi, teren, zabudowa LoD1, podstawowe oznakowanie z OSM, roślinność z generatora, kamery kontrolne, trasa jazdy), bez dopracowywania punktów do bramki; szlif detali w osobnych, późniejszych rundach. Limit lokalnych agentów pozostaje 4 (decyzja z tego samego dnia). Zasady jakości (docs/06, CLAUDE.md) obowiązują przy szlifie; wersja „z grubsza” musi być przejezdna, bez błędów krytycznych (dziury, latające obiekty, crash) i zmierzona na A16.

## D64 — Kierunek rozbudowy: Białystok → droga do Knyszyna → Knyszyn (2026-11-14, s20)
Właściciel: „chcę rozbudować Białystok, a potem drogę do Knyszyna i sam Knyszyn, bo to moje miasto”. Kolejność regionów (wg D63: najpierw z grubsza, potem detale): (1) rozbudowa Białegostoku kaflami w stronę wylotu na Knyszyn (łączenie z obecnymi regionami C i Dojlidy), (2) korytarz drogowy Białystok → Knyszyn (trasę wybrać z OSM — najkrótsza sensowna dla ciężarówki; uzasadnić w ADR), (3) Knyszyn (miasto) — z grubsza, potem szczególnie staranny szlif (miasto właściciela: zdjęcia od właściciela mile widziane). Obwodnica S8/DK8 spada na później, chyba że leży na trasie.
D64 uzupełnienie (2026-11-14): na razie trasa **zwykłą drogą (krajówka/wojewódzka), nie ekspresówką**. W rejonie Knyszyna trwa budowa drogi ekspresowej — uważać: dane (OSM `highway=construction`/`proposed`, objazdy, ortofoto starsze niż budowa, NMT sprzed robót) mogą się wykluczać. Odtwarzamy stan BIEŻĄCY przejezdny dla ciężarówki (drogi otwarte, objazdy z OSM), plac budowy jako uproszczona strefa (ogrodzenie, ziemia, sprzęt bez marek) oznaczona WORKING_VALUE; rozbieżności źródeł opisać w ADR i zapytać właściciela (może zrobić zdjęcia).
D63/D64 uzupełnienie (2026-11-14 23:1x): w wersji „z grubsza” PRIORYTETEM jest **wierność sieci drogowej**: te same drogi co w rzeczywistości (OSM + ortofoto), te same układy pasów, skrzyżowania, ronda, wloty, zjazdy, przejazdy, pierwszeństwo/oznakowanie wynikające z układu; budynki, roślinność i podobieństwo detali — później.

## D65 — Odpowiedzi właściciela do tras DK65/Knyszyn (2026-11-15)
1. Trasa Białystok → Knyszyn: **wariant A** (stara droga przez Fasty i Dobrzyniewo Duże). 2. Knyszyn DK65 × DW671: **rondo** (jak OSM). 3. Wiadukt S19 w Fastach: **stoi, otwarty**. 4. Budowa przy DK65 km 16,7–25: **jazda starą DK65, bez objazdu** (place budowy obok). 5. Ełcka/Studzienna: **wąska ~7 m** (zwęzić z 7,6 do ~6,9 m). 6. Nowa jezdnia DK65 w dk65-05: **nieotwarta** — plac budowy, trasa po starej. 7. Domyślna pora roku/światło: **lato** (zmierzch ~21:00, azymut ~300°). 8. Latarnie na trasie DK65/Knyszyn: **białe LED**.

## D66 — Szerokość ul. Ełckiej (2026-11-15)
Właściciel wybrał **6,6 m** szerokości jezdni (`width`) ul. Ełckiej / Studziennej w kaflach dk65-02…05 zamiast 6,9 m z D65. Powód: ortofoto 0,1 m pokazuje asfalt 6,5–7,1 m i linie krawędziowe 6,1–6,4 m od siebie (research K1, weryfikacja PR #80); przy 6,6 m generator rysuje linie ok. 6,2 m od siebie.

## D67 — Korytarz do Knyszyna w APK (2026-11-15, s21)
Właściciel: „dodaj korytarz do następnego APK”. Następny APK (po naprawie budżetu trójkątów C, ADR 0221) zawiera oprócz WorldC sceny regionów korytarza Białystok → DK65 → Knyszyn (Dojlidy, bialystok-knyszynska, dk65-01…11, knyszyn-s, knyszyn; w miarę rozmiaru także knyszyn-w, dk65-monki-01, dw671-tykocin-01, kleeberga, maczka) z wyborem regionu/trasy w menu. Na start bez płynnego przejścia między kaflami. Kod: chmura E, E2 (ADR 0229); lider weryfikuje i mierzy na A16 (rozmiar APK, PSS, gate3 w C bez pogorszenia). Punkt odniesienia: APK z samym C ma 224 MB.
Uzupełnienie (właściciel, 15.11): APK instaluje sam, więc **nie może być duży**. Do korytarza wchodzi tylko tyle regionów, ile mieści się w limicie ≤ 2 GB (właściciel 15.11: instaluje sam, 2 GB akceptowalne), w razie potrzeby sama trasa główna. Docelowo regiony jako osobne paczki do pobrania (podział: osobne zadanie po tym APK).

## D68 — Pora roku i zmierzch (2026-11-15, s21)
Właściciel (decyzje z ADR 0216 §Otwarte): (1) azymut zmierzchu **300°** (ok. 15 sierpnia, −6°) — zostaje obecne LP_Dusk; (2) **lato wszędzie**: letni preset (zmierzch ok. 21:00) także w Białymstoku C i na Dojlidach — przebudowa C i D po scaleniu naprawy budżetu (0221), potem pomiar na telefonie; (3) LED Knyszyna zostaje **4000 K** (WORKING_VALUE, bez nocnego zdjęcia).

## D69 — Drobne potwierdzenia (2026-11-15, s21)
Właściciel: (1) droga **1392B** (dk65-10/11) poza zabudową **bez latarni** — potwierdzone; (2) metryka bramki 3 (B-112): **≤ 12 klatek > 40 ms na przejazd**; (3) weryfikację/recenzję kodu PR robi sesja w chmurze (prompt docs/owner/CLOUD-REVIEW-PROMPT-S21.md), lokalny lider robi budowę świata, rendery i telefon.

## D70 — Sterowanie i lusterka (2026-11-15, s21; B-076)
Właściciel: domyślny zakres kierownicy dotykowej **270°** (900° w ustawieniach); lusterka jako **stałe okienka na ekranie**; feel test bramki 2 (B-075) **później** — po bramce 3.

## D71 — Decyzje po recenzji kodu s21 (2026-11-15, s21; REVIEW-2026-11-15-s21-code-*)
Właściciel: (1) **APK D67** — dodać zestaw regionów **`d67-full`** = obecny `d67` + Dojlidy, Knyszyn-W, Mońki, Tykocin (ESTIMATED do ~1,95 GB; limit 2 GB z D67 mierzyć na buildzie); `d67` zostaje jako lżejszy wariant (PR #104, ADR 0229). (2) **Opaska ronda Knyszyn** (DK65×Tykocka, PR #97, ADR 0218) — **jasna kostka betonowa**: nowy jasny materiał z fakturą kostki zgodny ze zdjęciami S21 (nie ciepły brąz `apron_sett`, nie gładki beton). (3) **Oznakowanie dojazdu do przejazdów kolejowych** (Dz.U. 2025 poz. 1105 § 79: A-9/A-10, G-1a–f, tablica „Sygnalizacja automatyczna”, U-1) — **osobne zadanie teraz**, po scaleniu rail-fix-s21 i #102.

## D72 — Limit rozmiaru APK 10 GB (2026-11-15, s22)
Właściciel: limit rozmiaru APK z regionami podniesiony z 2 GB (D67/D71) do **10 GB**. Uwaga techniczna: pojedynczy plik APK powyżej ~4 GB nie jest obsługiwany przez Androida i format ZIP32 (UNVERIFIED dla Unity 6000.3 — sprawdzić przy buildzie); powyżej tej granicy regiony muszą iść jako osobne paczki (PR #112, ADR 0234) albo asset packs.

## D73 — Windows jako platforma główna, telefon później (2026-11-15, s22)
Właściciel: na telefon „jednak za ciężkie” → **Windows (PC) jest teraz platformą główną**; Android/iOS później jako lżejsza wersja. **Silnik bez zmian: Unity 6 URP** (właściciel wybrał wariant rekomendowany zamiast Unreal 5). Zastępuje kolejność z D56 (PC po bramce 3). D67/D71/D72 (APK z korytarzem, limit rozmiaru) stają się drugorzędne. Budżety i bramki PC: do zdefiniowania (referencyjny PC, FPS, wejście — pytanie do właściciela); do czasu pomiaru WORKING_VALUE. Dotychczasowe budżety mobilne (np. < 2 M tris High) zostają jako zabezpieczenie dla przyszłej wersji telefonowej. ADR 0260.

## D74 — Wymagania sprzętowe PC jak w ETS2/ATS (2026-11-15, s22)
Właściciel: „zobacz wymagania Euro i American Truck Simulator 2 i zrób podobne”. Przyjęte klasy (Windows 10 64-bit; źródło: karta Steam ATS 270880 i serwisy cytujące kartę ETS2 227300, stan 15.11.2026 — ETS2 do potwierdzenia na samej karcie Steam):
- **Minimalne:** Intel Core i5-6400 / AMD Ryzen 3 1200, NVIDIA GTX 660 / AMD RX 460 / Intel HD 630 (2 GB VRAM), 8 GB RAM. Cel: tier Low, 1080p, **30 fps** (WORKING_VALUE).
- **Zalecane:** Intel Core i5-9600 / AMD Ryzen 5 3600, NVIDIA GTX 1660 / AMD RX 590, 12 GB RAM. Cel: tier High, 1080p, **60 fps** (WORKING_VALUE).
- Dysk: jak u nich ≤ 25 GB na grę bazową (WORKING_VALUE).
Progi FPS i dysk to propozycja lidera (SCS nie publikuje FPS) — do potwierdzenia przy pierwszym pomiarze. Ryzyko: Intel HD 630 przy obecnym świecie (do 2 M tris High) — pomiar Low na iGPU konieczny przed obietnicą. Pomiar na maszynie deweloperskiej (RTX 5070) nie zastępuje klas minimalnej/zalecanej. ADR 0260 (uzupełnienie), chmura H zadanie H4 (0266).

## D75 — Rondo Knyszyn: nowy jasny materiał i przejezdność (2026-11-15, s22)
Właściciel: (1) opaska ronda DK65×Tykocka = **nowy jasny materiał kostki betonowej z fakturą** (nie istniejący materiał chodnika, albedo ok. 0,26 ≈ odrzucony brąz); (2) wymiary: **przejezdność przed wiernością** — asfalt pierścienia 5,0 m + opaska 3,2 m (zawracanie zestawu 16,5 m), choć na zdjęciu ok. 3,1 + 2,4 m (ESTIMATED). ADR 0218.

## D76 — Pomiar klas PC: emulacja na maszynie deweloperskiej (2026-11-16, s23, OD-001)
Właściciel: klasy „min” i „zalecany” z D74 mierzymy teraz **emulacją na RTX 5070** (ograniczenie rozdzielczości, tieru i limitu FPS) jako metodą zastępczą; raporty PC mogą zaliczać bramki z adnotacją „emulacja”. Przed publiczną obietnicą wymagań sprzętowych — pomiar na prawdziwym słabszym sprzęcie (iGPU HD 630 / GTX 660 i GTX 1660). ADR 0266.

## D77 — Feel test bramki 2 na exe PC (2026-11-16, s23, OD-002)
Właściciel robi feel test bramki 2 (ruszanie pod górę z 40 t, hamowanie, rondo, cofanie pod rampę) **na najnowszym exe PC z padem/klawiaturą** (`docs/owner/FEEL-TEST.md`); uwagi idą do strojenia 0201b, 0228, 0264. Kierownica z FFB później (nie blokuje bramki 2).

## D78 — Rynek Knyszyn (#139): przejęcie lokalne, +64 draw calls Low przyjęte (2026-11-16, s23, OD-003)
Właściciel: lider przejmuje gałąź `knyszyn-rynek-0227` lokalnie (po zakończeniu pracy Codexa) — sprzątanie artefaktów, poprawki z recenzji `REVIEW-2026-11-16-s23-code-139.md`, przebudowa kafla knyszyn, rendery i budżet; wzrost Low na kamerze `dk65-inlet-south` 240 → 304 draw calls przyjęty (telefon drugorzędny, D73). ADR 0227.

## D79 — Naczepa: rozstaw sworzeń–środek tridemu 7,60 m (2026-11-16, s23, ADR 0280)
Właściciel: skrócić rozstaw sworzeń–środek tridemu naczepy z 7,70 m do **7,60 m**, żeby zestaw mieścił się w pierścieniu skrętu 12,5/5,3 m z dyrektywy 96/53/WE (zał. I pkt 1.5): 7,135 m przy granicy 7,20 m, zapas 6,5 cm (runner fizyki, sesja P r4). Wartość 3 cm poniżej najmniejszej z kart producentów naczep 13,6 m → **WORKING_VALUE** (do potwierdzenia rysunkiem/kartą). Zmiana obejmuje dane naczepy (trailer.json, dims.json), `TrailerAssetBuilder.cs:215`, model Blendera i fizykę — lista w ADR 0280 §5; scenariusz pierścienia skrętu z oczekiwanego błędu na PASS.

## D80 — Pad: warstwa „przytrzymaj Back + przycisk” (2026-11-16, s23)
Właściciel: 6 akcji bez wolnego przycisku pada dostaje warstwę modyfikatora **Back (przytrzymany) + przycisk**; Back przestaje być wstecznym (R) — wsteczny przechodzi na inny przycisk ustalony w implementacji (ADR 0264, propozycja w raporcie sesji P r4 / docs/owner/JAK-GRAC-PC.md). Do oceny w feel teście (D77).

## D81 — Trasa C ↔ Dojlidy przez DK19 Piastowska–Branickiego (2026-11-16, s23)
Właściciel: trasa ciężarówki C ↔ Dojlidy idzie DK19 przez ul. Piastowską, pl. Antonowicza i Branickiego do ronda Meyera, ze skrętem w Ciołkowskiego (za rondem Meyera zakaz 3,5 t). Podstawa: plan UM Białegostoku (2018, 40 t) + OSM bez ograniczeń tonażowych; brak zdjęcia znaków → WORKING_VALUE do potwierdzenia. Nocne 40 km/h na Piastowskiej jako WORKING_VALUE. Kafle bialystok-mickiewicza, -bojary, -wygoda wg ADR 0278. Research: docs/owner/MAP-DECISIONS-2026-11-16.md (a).

## D82 — Kierunek Podlasia: najpierw pętla S8 ↔ DW671 ↔ Tykocin (2026-11-16, s23)
Właściciel: po kaflach Białegostoku z ADR 0278 pierwszym kierunkiem Podlasia jest **pętla S8 ↔ DW671 ↔ Tykocin** (15 kafli: S8 z węzłami i MOP, powrót przez Tykocin–Knyszyn, strefa przemysłowa przy dk65-01); zgoda na S8 mimo D64. Mońki → Grajewo później (kafel Grajewa > 2 M High wymaga redukcji). Research: docs/owner/MAP-DECISIONS-2026-11-16.md (b).

## D83 — Budżety kafli dla PC: pomiar per tier zamiast limitu z telefonu (2026-11-16, s23)
Właściciel: limit 2 mln trójkątów na kamerę High pochodzi z telefonu (A16) i nie jest automatycznie limitem PC. Budżety trójkątów i draw calls ustalamy **pomiarem per tier** (emulacja klas D74 na RTX 5070 wg D76; skalowanie na inne karty tylko z cytowanych porównań, ESTIMATED): Low (GTX 660 / HD 630) ostrożnie, High/Ultra wyżej. Do czasu pomiaru gęste kafle Białegostoku (2,6–3,75 mln) i kafel Grajewa czekają; budżety mobilne zostają jako zabezpieczenie. ADR 0266, 0269, 0278, 0282.

**D79 — korekta (2026-11-16, s23, po raporcie sesji P r5):** brak karty producenta z 7,60 m; najbliższa realna wartość **7,63 m** (7 kart, rozstaw osi 1,31 m) przechodzi pierścień skrętu (zapas ~2,9 cm). Przy 7,60 m wychodziło pełzanie pustej naczepy na 12 % 5,04 mm (> 5 mm), które przechodzi dopiero od ~7,69 m. Właściciel: **7,63 m + uczciwa poprawka modelu hamulca postojowego/tarcia statycznego naczepy** (bez osłabiania testu). Zastępuje 7,60 m.

## D84 — Feel test bramki 2: zaliczony 5/5 + uwagi do PC (2026-11-16, s23)
Właściciel zrobił feel test (D77) na exe `kamion-0.1.0-e28533ca31-regions`, klawiatura, plac testowy (`-scene DrivingLab -trailer 40`): ruszanie pod górę 7 %/12 % — 5, hamowanie — 5, okrąg R50/rondo — 5, cofanie pod rampę — 5 („jak prawdziwe”). **Odczucie jazdy bramki 2 zaliczone** (pad i kierownica FFB nietestowane; geometria naczepy sprzed D79). Uwagi poza próbami: (1) **wnętrze kabiny na PC brzydkie, na telefonie było ładne** — właściciel przyśle zrzuty (do diagnozy: materiały/tekstury/oświetlenie kabiny w tierach PC); (2) **HUD i menu „zbyt AI slop”** — przeprojektować na poziom jakości gier symulacyjnych ciężarówek (styl własny, bez kopiowania cudzego wyglądu, marek i elementów), menu niewygodne w obsłudze; (3) **lusterka za małe / złe**.


## D85 — Kontrolki dotykowe na PC: jednorazowa migracja „zawsze” → „auto” (2026-11-16, s23)
Właściciel (klik): zapis `ui.touchControls = zawsze` na PC bez ekranu dotykowego zmienia się jednorazowo na `auto`, żeby nowy HUD monitora (ADR 0283) był widoczny. Telefon bez zmian. Źródło: raport integracji int-ui-s23 (§ ustawienia).

## D86 — Sceny dk65-03/04 w buildzie dopiero z wersją High (2026-11-16, s23)
Właściciel (klik): najpierw zbudować treść High dla dk65-03 i dk65-04, potem dodać je do EditorBuildSettings każdego buildu. Powód: po #168 jeden kafel tylko-Low przełącza streaming PC na treść Low.

## D87 — Tło menu startowego: zdjęcie z gry (2026-11-16, s23)
Właściciel (klik): menu startowe na tle statycznego zrzutu z gry (np. DK65 o świcie) z przyciemnieniem pod tekstem; bez marek. Zastępuje obecny brak tła (tekst na szachownicy placu — najgorszy element UI wg integracji int-ui-s23).

## D88 — Direct3D 11 domyślnym API grafiki na Windows, D3D12 jako opcja (2026-11-18, s24, ADR 0291)
Właściciel (klik) po pomiarze A/B na GTX 1070 (`artifacts/d3d-ab/`, knyszyn High, autopilot, 2 powtórzenia): bez limitu D3D11 171–190 kl./s vs D3D12 153–157; High 60 obie trzymają 60 (D3D12 r1: 4 klatki > 100 ms); pamięć prywatna D3D11 2,64–2,89 GB vs 3,04–3,27 GB; VRAM 1,76 vs 1,87 GB; 0 crashy przy wyjściu na obu (3 + 3 cykle). Lista API Windows = [Direct3D11, Direct3D12] jako kod (`ProjectSetup`); `-force-d3d12` (launchery `Kamion-d3d12.cmd`, `Kamion-korytarz-d3d12.cmd`) zostaje do porównań; mitygacja D3D12 (pełny ekran wyłączny → bez ramki) bez zmian. Numer D88 nadany przez agenta — do potwierdzenia przez lidera.

## D90 — Kamera z fotela: FOV 70°, pasek HUD ukryty w kabinie (2026-11-18, s24, ADR 0294)
Właściciel (klik) po wariantach `artifacts/cab-view-s24/WARIANTY.md`: domyślne pionowe FOV kamery kabiny 55° → **70°** (wariant B, wzrok 6° w dół, oko bez zmian), kamera QA `cab-driver` tak samo, suwak 45–75° zostaje; zapisane ustawienia z dawnym domyślnym 55° → 70° jednorazowo (jak D85), ręcznie zmienione zostają. Dolny pasek HUD (prędkość, bieg, ciśnienie) **ukryty w widoku z kabiny** (zasłaniał prawdziwe zegary), widoczny w kamerach zewnętrznych. Lusterek bocznych FOV nie pokaże (54–76° od osi) — zostają okienka D70.

## D91 — Most na Narwi w Tykocinie: trasa zostaje, gra ostrzega (2026-11-19, s24)
Właściciel (klik): OSM podaje dla mostu DW671 na Narwi `maxheight=3.7` i `maxweight:hgv=12 t` (edycja 08.2026); zestaw 4 m / 40 t nie powinien przejechać. Decyzja: trasa autopilota i GPS do Rynku w Tykocinie zostaje przez most, ale gra pokazuje ostrzeżenie o ograniczeniu (znaki B-16/B-18 przy moście i komunikat w nawigacji/HUD przed wjazdem). Znaki na zdjęciach nadal UNVERIFIED. Źródło decyzji: ADR 0303 (otwarte), HANDOVER s24.
