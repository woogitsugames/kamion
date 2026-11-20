# D95 — Knyszyn, rondo-fix-cli (2026-11-20)

Stan: WIP; bez Unity, bez push. Nie stanowi wizualnego PASS.

## Kontynuacja — kontekst szwu w statycznym QA

Poprzednie trzy runnery nie dożyły przydziału heavy (brak procesów oraz plików exit). Wznowiono je jednym
runnerem `artifacts/logs/d95-resume-run.ps1`, który serializuje build knyszyn → combo → pełny retest.
Nie usuwano aktywnych slotów regen-wave ani nie zwiększano limitu puli.

Przyczyna zapory z krytyki: `VisualQaRunner.RenderTier` otwierał tylko pojedynczą scenę, więc WorldEdge
pokazywał zamknięcie i prosty stub z ogólnym materiałem asfaltu, zamiast rzeczywistej kontynuacji w knyszyn-w.
QA Knyszyna ładuje teraz rzeczywistą scenę `knyszyn-w` tego samego tieru (bez generowania sąsiada), ustawia
ją przez `TilePlacement` i otwiera szew tym samym `RefreshEdgesAround` co player, po przygotowaniu kolizji.
Usuwane są zapory obu stron oraz nakładające się aprony/stuby i tło. Brak zaimportowanego sąsiada przerywa
render z błędem — nie powstaje pozornie poprawny obraz nad pustką. Dodano regresję EditMode sprawdzającą
obie zapory, oba stuby i położenie sąsiada; jej uruchomienie oraz kompilacja Unity pozostają odroczone.
Player PC uruchomiony w Knyszynie bez argumentu `-stream` teraz automatycznie włącza streaming, żeby rzeczywista
droga zastąpiła stub także w zwykłym przejeździe. Jawne `-stream 0` i EnabledOverride zachowują pierwszeństwo;
telefony oraz inne sceny zachowują poprzednią regułę. Nadal trzeba mieć scenę sąsiada w buildzie; zapory otwierają
się dopiero po gotowości kafla i kolizji. Samodzielna scena z jawnym wyłączeniem streamingu kończy mapę zaporą.
Nie jest to dowód wizualnego usunięcia szwu; stan po starcie i przejazd wymagają playera.
Helper wydzielono do `WorldNeighbourQa.cs`. Sprawdzono kompilatorem Roslyn (bez edytora): całe lokalne
Game.World, nowy helper QA i zmieniony plik testu EditMode — exit0 dla wszystkich trzech; referencje z cache
main. Pełny stary kod Game.Editor ma niezgodności z tym cache (CabViewQa/forceReverse/CameraModeOverride),
więc kompilacja helpera nie jest deklaracją pełnego buildu. `dotnet test tools/spawn-runner/Tests/Tests.csproj`:
43/43 PASS (w tym 8 przypadków domyślnego streamingu Knyszyna i pierwszeństwa jawnych ustawień).
Nowy scenowy test EditMode nie został wykonany, zgodnie z zakazem Unity.

Zachowane promienie, szerokość pierścienia i fartuch D94. Zachodnie ramię ma dwa pasy z zachowaniem 11,75 m asfaltu po D94 (11,25 m + 2 × 0,25 m zamiast 11,00 m + 3 × 0,25 m).

Przyczyny i poprawki:
- `Data/Regions/knyszyn/roads.graph.json`: way 1478765548 ma OSM lanes=3; lokalny override D95 ustawia dwa pasy bez zwężenia asfaltu.
- `game/Assets/_Project/World/Import/WorldPbrMaterials.cs:378`: asphalt_worn automatycznie włącza _CRACKS. Nowa nawierzchnia ronda otrzymuje asphalt_sma_fresh.
- `tools/worldgen/roads/meshing.py:1496`: większość materiałów ramion wybierała materiał płyty; dla ronda kompaktowego materiał pochodzi teraz z pierścienia. Źródło falistych smug wymaga jeszcze potwierdzenia renderem; nie wykluczono udziału _ROADWEAR/UV1.
- `tools/worldgen/roads/compact_roundabout.py:562`: wysepki pochodzą ze szczeliny między pasami. Krótkie rozdziały E/W dawały głównie azyle; wydłużenie carriageway_split daje główne soczewki 15,89 / 17,53 m (płaska geometria testowa), z przejściem i krawężnikiem z istniejącego plan_islands.
- `tools/worldgen/roads/build_world.py`: lokalne przyciemnienie opaski (0,42 → 0,35) i wzmocnienie fug; kostka paving_20x10_grey była już przypisana. Próg 4 cm, spadek i kolizja bez zmian.
- Cztery zespoły A-7/C-12 i sześć lamp łukowych 9 m przez gate3_landmarks. Pozycje i wysokość WORKING_VALUE, do sprawdzenia na kamerach 09/10/11; nie są pomiarem fotogrametrycznym.

Otwarte:
- Zapora i widoczny szew: `world_edge.authored.json:13` przesuwa jedynie zaporę 12 m od krawędzi. `WorldEdgeBuilder.cs:90` buduje domknięcie i prosty stub poza kaflem. Brak poprawki tej części; ukrycie samej zapory nie zszywa drogi z knyszyn-w. Wymaga rozwiązania ciągłości sceny/streamingu, bez przebudowy sąsiada w tym zadaniu.
- Brak renderu po zmianach, zgodnie z zakazem uruchamiania Unity. Sprawdzić asfalt (spękania i UV1), bryłę wysepek, fugi i cień opaski, pozycje/duplikaty lamp, orientację i widoczność znaków.

Walidacja w toku. Pierwszy przebieg: 105 passed, 3 failed; stare oczekiwania długości/liczby wysepek i stara trasa przecinająca wydłużoną wysepkę. Trasa zregenerowana, oczekiwania zaktualizowane oraz dodane regresje długości soczewek, liczby pasów i świeżego materiału płyty.

Lokalne siatki skopiowane z main dają historyczne DK65→DW671 W 0/23/5 oraz DK65→DK65 W 0/16/0 (swing w obu przypadkach 0/0/0). To NIE jest baseline G3: ADR 0306 podaje 0/5/0 (swing 0/0/0) oraz 0/0/0. Wymagana bramka pozostaje G3/D95, nie starsze siatki.

## Wyniki pierwszej pełnej przebudowy i pomiaru

- `d95-build.log`: exit 0, 1164,7 s; 64 GLB, High 548 MiB / Low 233 MiB; road_consistency 3 lane_blind_end / 5 obstacle_in_lane, na trasie 0.
- `d95-tests-final.log`: 142 passed, 2 skipped, 2 failed (200,97 s). Poprawiono pominięty feeder 1426600413 oraz historyczny limit obrysu z wyłączonym D94 (zachowanie 11,75 m przy zmianie liczby pasów wymaga bazy większej o 0,25 m). Ponowny test w kolejce; nie uznawać za zielony przed wynikiem.
- `d95-combo-after.json`: całość exit 1 przez istniejące łączniki z Rynku; łącznie opposite/kerb/off_hard 68/30/0, ze swingiem 4/77/0.

| Przejazd | G3 (ADR 0306) | po D95 r1 | po D95 r1 swing |
|---|---|---|---|
| DK65 → DW671 W | 0/5/0 | 0/17/0 | 0/0/0 |
| DK65 → DK65 W | 0/0/0 | 0/0/0 | 0/0/0 |

Kolejność: opposite / kerb / off_hard. DW671 spełnia wymagane 0 przeciwnego pasa i wariant ze swingiem pozostaje 0/0/0, lecz tor środkiem pasa pogarsza kerb 5→17. **Nie potwierdzono pełnego braku pogorszenia toru.**

Pierwszy eksport przyjął wszystkie 6 lamp, ale odrzucił 4 authored zespoły znaków `along not found` (wchłonięte feedery); zwykła reguła nadal wykrywa A-7/C-12 na trasie, dalej od pierścienia. Poprawiono wpisy na jawne at_en/bearing. Druga przebudowa jest w kolejce heavy, wynik i ewentualne duplikaty znaków trzeba sprawdzić.

### Korekta toru łącznika (po r1)
Optymalizator r1 znalazł ruch 0,75 m w prawo, half_m=35, near EPSG:2180 [760608, 611987,39], który daje 0/0/0 bez przeciwnego pasa. Zapisano go jako `swing` w `Data/Streaming/route_links.yaml` i zregenerowano wyłącznie łączniki Knyszyna. To korekta authored trasy, nie zwężenie wysepek ani zmiana progów QA. Osobny pomiar gotowego łącznika oczekuje w heavy (`d95-combo-final.*`); wynik optymalizatora nie zastępuje tego pomiaru.

## Stan przekazania — 15:08, zablokowane pulą heavy
Wszystkie trzy sloty zajęte przez regen-wave-2-s24 A/B/C. W tle pozostają uprawnione zadania wyłącznie dla Knyszyna:
- `artifacts/logs/d95-signs-run.ps1`: drugi build z poprawionymi współrzędnymi znaków i brakującym świeżym feederem; log `d95-build-signs.log`, kod `d95-build-signs.exit`.
- `artifacts/logs/d95-retest-run.ps1`: ponowny moduł 0274 po korektach; log `d95-retest.log`, kod `d95-retest.exit`.
- `artifacts/logs/d95-final-combo-run.ps1`: gotowy authored łącznik DW671, bez ponownego szukania potrzebnej korekty; log `d95-combo-final.log`, kod `d95-combo-final.exit`.
Każdy runner zwalnia swój slot przez finally. Nie uruchamia Unity ani innego kafla. Nie wolno uznać testów za PASS na podstawie samego ustawienia w kolejce. Drugi build zmieni pliki wygenerowane po commicie WIP; wymagają późniejszego przeglądu i commitu.

Przyczyny / najważniejsze miejsca zmian: overrides.yaml:1048 (świeży asfalt), :1054 (dwa pasy bez zwężenia D94), :1060 (wysepki), :1075 (znaki), :1111 (lampy); meshing.py:1502 (materiał płyty), build_world.py:1233 (lokalna opaska). Źródło zapory/stuba: WorldEdgeBuilder.cs:90 oraz world_edge.authored.json:13. Finalnie nadal WIP: zapora/szew niewykonane, finalna walidacja w kolejce, brak renderu po zmianach.
