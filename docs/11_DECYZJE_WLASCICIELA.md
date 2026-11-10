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
