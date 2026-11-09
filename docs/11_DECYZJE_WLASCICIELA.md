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
