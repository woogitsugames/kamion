# 06 — Pierścień regionów: Mońki, Tykocin, DW671 — WIP

Cel: rozpoznawalny układ miejsc i planowane zmiany, z rozróżnieniem projektu od stanu wykonanego. Nowy materiał: **2 ortofoto GUGiK + 2 komunikaty tekstowe link-only**, 0 nowych fotografii ulicznych. Każdy ortokadr obejrzany osobno. Wycinki obejmują 400×400m, oryginały1600×1600px przy0.25m/px poza gitem; miniatury800×800. Pełne bbox/URL/SHA i zapytania skorowidza w `data/wms-overviews.json`. Źródło środka to węzeł miejscowości OSM, nie deklarowany geometryczny środek rynku.

## Tykocin

SOURCED [obraz06-001, link w manifeście]: wydłużony plac, zielone pola po bokach środkowej posadzki, drobne obrysy budynków w pierzei z czerwono-brązowymi dachami; duża budowla sakralna przy wschodnim końcu. Na północ rzeka i most kratowy. Przed budowlą widoczne łukowe/zakrzywione przedpole — nie zastępować go zwykłym prostokątnym parkingiem. Wysokości budynków i liczby kondygnacji UNVERIFIED z tego obrazu.

SOURCED [lokalny OSM2026-11-08, `data/osm-selected-roads.json`]: DW671 biegnie po Placu Stefana Czarnieckiego (way630270655, tag surface=sett, lane_markings=no), następnie Złotą (99877202), a w stronę mostu Puchalskiego (631895410/96941956/96942026). Dane OSM są tagami, nie pomiarem materiału nawierzchni ani dowodem aktualnego oznakowania.

**Flaga dla planowania ciężarówki:** way96942026 (most) ma w OSM `maxheight=3.7`, `maxweight:hgv=12 ton`, `maxspeed=40`. SOURCED wyłącznie jako wartości tagów OSM; obowiązywanie prawne, aktualne znaki i prześwit rzeczywisty **UNVERIFIED**. Nie ustawiać twardych ograniczeń prawnych z samej mapy.

SOURCED [skorowidz GUGiK, XML]: w punkcie środka najnowszy znaleziony arkusz2025-05-27, piksel0.1m; zapytanie2026 bez obiektów. WMS HighResolution nie jest przypięty do daty; nie gwarantuje jednolitej daty całego400m wycinka.

## Mońki

SOURCED [obraz06-002]: kwartały drobnej zabudowy na zielonych działkach, w części kadru większe wydłużone i prostokątne bryły, parkingi i zebry. Przebieg ulic z ukośną główną osią kadru, bez podstaw do opisu całego miasta jako samej niskiej pierzei rynkowej. Typy funkcjonalne budynków i kondygnacje UNVERIFIED z samego orto.

SOURCED [OSM snapshot]: w wybranym otoczeniu m.in. Juliusza Słowackiego way98071718 (tertiary, asphalt, lit=yes), Białostocka/DK65 way98072613 (primary, lanes=2, asphalt), Kolejowa way631046413. Oświetlenie oznacza tag, nie zinwentaryzowany typ opraw.

SOURCED [06-D02, UM17.09.2026]: podpisanie umowy finansowania przebudowy skweru Czesława Gartycha przy Al.Niepodległości. Brak dowodu ukończenia, planu mebli i dzisiejszego wyglądu po przebudowie — UNVERIFIED. Nie modelować ukończonego nowego skweru tylko na podstawie tego komunikatu.

SOURCED [skorowidz, XML]: w środku wycinka najnowszy znaleziony arkusz2025-07-02, piksel0.05m; starsze2025-05-27 mają0.25m. Zapytanie2026 puste. Obraz żądano0.25m/px; WMS może składać różne arkusze, nie gwarantuje jednej daty całego kadru.

## DW671 Knyszyn–Krypno

SOURCED [06-D01, UM03.07.2026](https://www.knyszyn.pl/asp/podpisanie-umowy-na-opracowanie-dokumentacji-projektowej-rozbudowe-drogi-wojewodzkiej-nr-671-w-zakresie-budowy-drogi-dla,239,artykul,1,6670): podpisano umowę **na dokumentację** drogi pieszo-rowerowej, planowany zakres km~47+800…53+600, długość~5.8km; dowiązanie do **projektowanego** wiaduktu DW671×LK38. Plan ukończenia dokumentacji13.11.2027. To nie protokół odbioru infrastruktury. Zrealizowanie ciągu i wiaduktu w2026 UNVERIFIED.

## Metoda i luki

`data/osm-source.json` ma SHA lokalnego PBF, licencję i metodę selekcji. Zachowano255 pełnych wayów wybranych po sąsiedztwie wierzchołków i ref671 — to nie zamknięty wycinek, nie licznik dróg w mieście i nie obliczenie długości DW671. Pochodna baza OSM: © OpenStreetMap contributors, ODbL1.0. Dane GUGiK osobno, nie łączono ich w bazie geometrycznej.

Brak zdjęć ulicznych aktualnych fasad, charakterystycznych obiektów z poziomu kierowcy oraz zweryfikowanych rond. Nie identyfikowano materiałów/RAL i gatunków drzew z kolorów ortofoto. Brak potwierdzenia obecnego stanu ograniczeń mostu w Tykocinie. Nie pobierano modeli Drzewa3D. Oficjalna strona turystyczna UM Tykocin zwracała timeout; treść znalezioną w indeksie wykluczono z wniosków SOURCED.
