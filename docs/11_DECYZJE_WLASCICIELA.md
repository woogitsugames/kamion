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
