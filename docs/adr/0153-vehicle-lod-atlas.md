# ADR 0153 — LOD1/LOD2 aut

Status: WIP, gpt-s16-r1. Baza: origin/main 421f1b4fb (12.11.2026).

## Problem i granice

ADR 0136 r2 raportuje GPU p95 A16 Low 34,0 ms przy celu 33,3 ms. To wynik
lidera, nie pomiar tej gałęzi. Flota ma już uproszczoną geometrię, ale osobne
materiały szyb, lamp, gumy, felg i tablic utrzymują wiele zgłoszeń rysowania.
LOD0, kolizje, contact shadows, rozmieszczenie oraz lakier pozostają bez zmian.

## Rozwiązanie w przygotowaniu

Osobny lakier / główne poszycie plus wspólny atlas detali: najwyżej dwie
podsiatki w odległych LOD. Atlas BaseColor + MaskMap zachowuje wartości
koloru liniowego, metaliczności i gładkości z danych materiałów. Tablice
pozostają fikcyjne; ich atlas jest odtwarzany istniejącym generatorem.
Nowy materiał ma jawny opt-in `vehicle_lod_atlas`, używa istniejącego shadera
World PBR i jego przebiegów. Bez nowego przebiegu na Low. Modyfikacje wspólnej
fabryki materiałów będą wyłącznie addytywne, chronione tym polem danych.

Generator: `tools/worldgen/streetscape/vehicle_lod_atlas.py`. Łączenie zachowuje
pozycje, normalne i trójkąty, a główny materiał także komplet swoich atrybutów.
Parametry materiałów odziedziczono z repo (WORKING_VALUE tam, gdzie nie mają
źródła). Szczegóły rastrowe grilla chłodni w atlasie palety wymagają oględzin;
zachowanie koloru nie jest dowodem identycznego wyglądu.

## Weryfikacja dotychczasowa

7/7 testów `tests/gis/test_vehicle_lod_atlas.py`: niezmienność geometrii
i normalnych sześciu rodzin/prototypów, dwie podsiatki oraz liniowe parametry
atlasu. Baseline materiałów/świata jest w toku. Render, dobór progów z edytora,
pełne GIS, EditMode oraz niezależna recenzja pozostają otwarte.

## Pomiary i przyjęcie

Raport każdej kamery Low/High, clear/overcast będzie zawierał osobno draws
sceny i instancji, trójkąty oraz dostępne liczniki batchy. SceneStats to estymata
CPU przed SRP batching; nie należy jej podpisywać jako pomiaru GPU lub telefonu.
Brak widocznego przełączenia wymaga oględzin PNG i porównań blisko progów.
Pomiar na A16 i scalenie do main należą do lidera.
