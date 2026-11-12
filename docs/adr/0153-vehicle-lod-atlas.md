# ADR 0153 — LOD1/LOD2 aut

Status: WIP, gpt-s16-r1. Baza: origin/main 421f1b4fb (12.11.2026).

## Problem i granice

ADR 0136 r2 raportuje GPU p95 A16 Low 34,0 ms przy celu 33,3 ms. To wynik
lidera, nie pomiar tej gałęzi. Flota ma już uproszczoną geometrię, ale osobne
materiały szyb, lamp, gumy, felg i tablic utrzymują wiele zgłoszeń rysowania.
LOD0, kolizje, contact shadows, rozmieszczenie oraz lakier pozostają bez zmian.

## Rozwiązanie

Osobny lakier / główne poszycie plus wspólny atlas detali: najwyżej dwie
podsiatki w odległych LOD. Atlas BaseColor + MaskMap zachowuje wartości
koloru liniowego oraz efektywną metaliczność i gładkość bazowych materiałów. Tablice
pozostają fikcyjne; ich atlas jest odtwarzany istniejącym generatorem.
Nowy materiał ma jawny opt-in `vehicle_lod_atlas`, używa istniejącego shadera
World PBR i jego przebiegów. Bez nowego przebiegu na Low. Modyfikacje wspólnej
fabryki materiałów są addytywne, chronione tym polem danych.

Pojazdy placowe mają już mały LOD1 (276–316 trójkątów). Ich LOD2 współdzieli
ten sam natywny mesh i materiały, zamiast usuwać osobne koła/podpory. Nowe
extras zawierają trzy pasma i jawny alias. Importer obsługuje je wyłącznie za
`vehicle_lod_atlas`; stare gałęzie polityki pozostają bez zmian. Szacunek Python
w chronionym `roads/build_world.py` nadal używa LOD1 placowych daleko; ponieważ
alias ma identyczną liczbę trójkątów, nie zaniża z tego powodu budżetu geometrii.
Progi 40/100/300 m dla placowych są WORKING_VALUE do weryfikacji w edytorze;
osobówki zachowują 25/85/300 m, floor LOD0 16 m i cull Low 150 m.

Generator: `tools/worldgen/streetscape/vehicle_lod_atlas.py`. Łączenie zachowuje
pozycje, normalne i trójkąty, a główny materiał także komplet swoich atrybutów.
Parametry materiałów odziedziczono z repo (WORKING_VALUE tam, gdzie nie mają
źródła). Wzór grilla chłodni ma osobny prostokąt 1,68 × 0,78 m w atlasie,
60 mm okresu i smoothness 0,45, jak `WorldPbrMaterials.Stripes(louvre_slats)`.
Atlas korzysta z mipów, źródłowy shader z pochodnych; różnica wymaga oględzin.
Metal ≤ 0,5 w bazowym `LookDevAssets.WorldMaterial` wybiera World Surface,
który jest dielektrykiem. Atlas zachowuje efektywne metal=0 w tych komórkach,
a nie uruchamia ignorowanego wcześniej M.metal. Zachowanie nominalnych parametrów
nie jest dowodem identycznego wyglądu pod innym shaderem.

Walidator tablic rozróżnia jawnie oznaczony atlasowy LOD1 od starego LOD1
z osobną tablicą. LOD0 zawsze wymaga pełnych, poprawnych natywnych rogów UV0/UV1.
Nowy test importu wymaga nadal shadera World Car Plate i aktywnego remapu LOD0.
Adaptacja nie zmienia rygorów starych bibliotek ani ich 54 tablic.

## Weryfikacja dotychczasowa

8/8 testów `tests/gis/test_vehicle_lod_atlas.py`: niezmienność geometrii
i normalnych sześciu rodzin/prototypów, dwie podsiatki oraz liniowe parametry
atlasu oraz wzór żaluzji. Z deposition/yard: 37 passed. Baseline ma 114 kamer
× Low/High × clear/overcast. Wariant A: 420 chronionych węzłów GLB oraz 68
dalekich LOD bez błędów audytu, 14 nowych aliasów poprawnych; kod atlasu został
potem poprawiony po niezależnym preflight, trwa regeneracja B. Render after, dobór progów z edytora,
pełne GIS, EditMode oraz niezależna recenzja pozostają otwarte.

## Pomiary i przyjęcie

Raport każdej kamery Low/High, clear/overcast będzie zawierał osobno draws
sceny i instancji, trójkąty oraz dostępne liczniki batchy. SceneStats to estymata
CPU przed SRP batching; nie należy jej podpisywać jako pomiaru GPU lub telefonu.
Brak widocznego przełączenia wymaga oględzin PNG i porównań blisko progów.
Pomiar na A16 i scalenie do main należą do lidera.
