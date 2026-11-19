# ADR 0302 — GPS: trasa do celu przez wiele kafli streamingu (Białystok → Tykocin / Mońki / S8)

Status: Proposed (agent nav-route-s24, 2026-11-19). Numer nadany przez lidera.
Powiązane: ADR 0150 (GPS, graf tras per region), 0168 (strefa bez powrotu, wyjazdy z kafla), 0283 (ekran nawigacji),
0285 (korytarze i trasy łączące, `-route_to`), 0300 (GPS za streamingiem — problem otwarty: cel porzucany na szwie).

## Kontekst
Po ADR 0300 GPS przełącza się na kafel pod ciężarówką, ale trasa była liczona w grafie jednego kafla: cel spoza kafla był
porzucany przy przejściu szwu, a z mapy nie dało się wyznaczyć trasy dalej niż do krawędzi kafla. Właściciel jeździ
korytarzem Białystok → Knyszyn → Tykocin (28 kafli, ~55 km) z celem z `-route_to` (domyślnie tykocin).

## Decyzja
### Dane — `Gameplay/Resources/Nav/nav_trips.json` (`tools/ui/build_nav_trips.py`)
Generator czyta korytarze `route_links.json` (ADR 0285: lista kafli + złącza na szwach w EPSG:2180, punkty brzegowe grafu)
i `Data/Regions/<id>/route_endpoints.json → end_epsg2180` ostatniego kafla. Cele:
- `tykocin` — korytarz `bialystok-tykocin` (28 kafli), cel = koniec trasy kontrolnej kafla `tykocin` (DW671 na krawędzi S);
- `monki` — ten sam korytarz do `knyszyn`, potem `knyszyn-w` wjazdem DK65 (koniec linku `knyszyn-dk65-to-dk65-w`), cel =
  koniec trasy kontrolnej `knyszyn-w` (DK65 w stronę Moniek, krawędź N);
- `s8` — korytarz `bialystok-s8` (obecne 12 kafli), cel = koniec trasy kontrolnej `s8-05`.
Cel = miejsce, w którym kończy jazdę autopilot trasy (spójnie z `-route_to`); punkt „rynek Tykocina” wymagałby autorskiego
punktu — poza zakresem.

### Planowanie — `UI/Navigation/NavTrip.cs`
Grafy zostają per kafel (format ADR 0150 bez zmian, 0,7 MB w Resources). Podróż = łańcuch odcinków, jeden na kafel:
odcinek i planowany A* w grafie kafla i od wjazdu (złącze z poprzednim kaflem, przesunięte 3 m w głąb kafla, kierunek
w poprzek szwu) do wyjazdu (złącze z następnym, 3 m przed szwem) albo do celu; odcinek kafla pod ciężarówką — od ciężarówki.
Odcinki są sklejane w **jedną `RoutePath` w ramce bieżącego kafla** (każdy przesunięty o różnicę originów): tracker,
ETA (`NavEta`), linia na minimapie i pełnej mapie, ekran kabiny działają bez zmian (komunikaty głosowe czytają tę samą ścieżkę — nie sprawdzane osobno), linia trasy biegnie
przez szew. Nazwy ulic: jedna tablica podróży (deduplikacja napisów), indeksy odcinków przemapowane przy planowaniu.
Manewr „Cel” tylko na końcu ostatniego odcinka.
- **Inkrementalnie:** jeden odcinek na klatkę (`NavigationService.Update` → `StepTrip`); pierwszy — odcinek ciężarówki,
  więc wskazówki są od razu.
- **Zmiana kafla** (`SwitchRegion`): nic nie jest liczone od nowa — złożenie od bieżącego odcinka w ramce nowego kafla
  (`Compose`, kopiowanie tablic), cel i pinezka przeliczone o różnicę originów. Rebase originu niczego nie rusza (ramka =
  korzeń regionu, przesuwany razem z ciężarówką, ADR 0300).
- **Zjazd z trasy:** A* tylko odcinka bieżącego kafla od ciężarówki do jego wyjazdu + złożenie (bez alokacji). Poza
  korytarzem (kafel spoza podróży) trasa zostaje narysowana, bez przeliczania.
- **Wyjazd z kafla:** odcinki kończą się na szwie, czyli na jezdni wylotowej do krawędzi — dla zwykłego GPS to strefa bez
  powrotu (ADR 0168) / poza główną składową (M27). `RoutePlanner.AllowTileExit` (tylko dla odcinków podróży) pozwala
  na cel tam i wjazd w tę strefę.
- **Ograniczenia ciężarówki (znalezisko):** DK65 w kaflach `bialystok-knyszynska`, `dk65-01…10` (bez 03, 09, 11),
  `knyszyn-s` i DW671 w `tykocin` ma w OSM `maxaxleload=10` (t) < 11,5 t naszej ciężarówki — ścisły planer zwraca NoPath
  (objazdu w obrębie kafla nie ma). Odcinek bez legalnej drogi jest planowany drugi raz z
  `RoutePlanner.RelaxTruckLimits` (krawędzie ponad limit dozwolone, zwykły koszt — kara za krawędź spychała trasę na
  boczne drogi: dk65-04 3422 m zamiast 2074 m), oznaczony `Relaxed`; pełna mapa pokazuje „odcinek z ograniczeniem dla
  ciężarówek”, log podaje liczbę takich odcinków. Długości odcinków po tej zmianie = długości tras autopilota
  (knyszynska 2957 m vs 2961 m w ADR 0300, dw671-tykocin-01 2603 m vs 2608 m w ADR 0285).

### Wybór celu
Jak `-route_to` (ADR 0285). Kolejność: argument `-route_to` → ostatni wybór z mapy (PlayerPrefs `nav.trip`, „-” = brak)
→ `WorldStreamer.routeDestination` (domyślnie tykocin). Pełna mapa: przycisk „Cel trasy: Tykocin” (lewy górny róg pod
„Wróć”) przełącza tykocin → monki → s8 → brak; wybór ustawia też cel autopilota (`routeDestination`). Pinezka z mapy
zastępuje podróż; „Wyczyść trasę” kończy podróż i zapamiętuje „brak”. Bez streamingu nic się nie zmienia.

### Liczby i ETA
Pozostała odległość = długość sklejonej trasy od rzutu ciężarówki (tracker); ETA = `NavEta` (limity OSM + profil
ciężarówki PL), ta sama liczba na pełnej mapie i (od teraz) na ekranie kabiny (wcześniej kabina skalowała koszt planera).

## Liczby (zmierzone 2026-11-19)
Do uzupełnienia wynikami testów i przejazdu.

## Konsekwencje / otwarte
- Podróż prowadzi korytarzem z `route_links.json`; trasy alternatywne spoza kafli korytarza nie są szukane (planowanie
  na grafie łączonym = osobne zadanie). Poza korytarzem GPS nie przelicza — tylko pokazuje trasę.
- Limit nacisku osi 10 t na DK65/DW671 z OSM: do weryfikacji (dane / właściciel) — dziś trasa idzie nim z oznaczeniem.
- Cele „miasta” (rynek Tykocina, centrum Moniek) jako autorskie punkty — później.
