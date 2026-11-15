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

## Tykocin z poziomu ulicy — sierpień2026

06-P01/P02: dwa nowe kadry Krzysztofa Popławskiego, CC BY4.0, indywidualnie obejrzane. Data2026-08-05 z metadanych Commons. Podglądy960px zachowano poza gitem i zmniejszono do≤800px; pełnych oryginałów nie pobrano. SOURCED [obrazy]: biały parterowy dom, czerwony dach, brązowe okiennice, drewniany płot; osobno wąski brukowany przesmyk, pnącza i latarnia z panelem. Liczby kondygnacji dotyczą widocznych elewacji, nie wnętrza/poddasza. Adresy z opisów autora, współrzędne, azymut, wysokości i szerokości UNVERIFIED. Łącznie6 rekordów:2 orto,2 dokumenty,2 fotografie.

## Rondo DW671/DK64 — odrębne nowe orto

06-O03: nowy kadr800px GUGiK, indywidualnie obejrzany. SOURCED [obraz]:4 główne ramiona, trawiasta wyspa z zakrzywionymi niskimi nasadzeniami, jasny pierścień, widoczne zebry przy ramionach północnym/zachodnim. Materiał i przejezdność pierścienia, wymiary, gatunki oraz komplet urządzeń UNVERIFIED. Identyfikacjaref64;671 z istniejących danych OSMway183373470, nie nowej inwentaryzacji prawnej. WMS bez daty przypięcia; data arkusza jeszcze UNVERIFIED. Łącznie7 rekordów:3 orto,2 dokumenty i2 fotografie.

Datowanie06-O03: WFS2025 zwraca arkusz N-34-106-C-b-2-4, akt_data2025-05-27, piksel0,1m; WFS2026 zwraca gml:null missing. SOURCED jako metadane arkusza w punkcie środka, nie gwarancja daty bieżącej mozaiki WMS ani stanu2026.

## Mońki — dwie nowe fasady z poziomu ulicy

monki-ground-round2:2 nowe źródła Henryka Borawskiego, CC BY-SA3.0/4.0,2014/2015. Obie miniatury800×600 obejrzane osobno przez agenta i koordynatora, opisy PASS. Kremowo-ceglana nieregularna bryła z arkadami i czerwonym dachem; osobno niska zabudowa, szeroki wjazd i rowopodobne obniżenie przy jezdni. Adresy z metadanych, nie odczytu numerów. Nie dopasowano dokładnych fasad do DK65, nie ustalono stanu2026 ani pełnych przekrojów. Główny manifest ma9 rekordów.


Tykocin-landmarks-round3:2 nowe kadry2009/2018 (Lollencja BY-SA3.0pl, Ymblanter BY-SA4.0), kościół/pomnik i pierzeja placu. Osobne oględziny koordynatora i niezależny przegląd. Lewa wieża ucięta, wymiary/formalne kondygnacje i aktualność2026 nieustalone. 2 podglądy pobrane, 2 miniatury≤800px, brak pełnych oryginałów. Główny manifest11 rekordów.


Monki-centre-round3:3nowe indywidualnie obejrzane link-onlyMapillary, szurek for Here2017 iroadlifehacks2021. Drewniany szczyt przy Białostockiej, pawilon z witrynami przy Słowackiego oraz dalsza niska pierzeja DK65. Bez kopii/API/tokenów, jawny podkładOSM. Nie są pełną panoramą placu/ronda ani dowodem wykonania skweru2026. Adresy/formalne kondygnacje/GPS kamery/metryka i stan2026UNVERIFIED. Główny manifest14rekordów.

## Synagoga i skwer — obieg4

Aktualny główny manifest:21rekordów. [Synagoga](tykocin-synagogue-round4/README.md):4różne zdjęciaCC, 4podglądy pobrane, 4miniatury≤800,0pełnychoryginałów; dach z poziomym uskokiem, rytm okien, przybudówki i bruk. [Mońki](monki-square-round4/README.md):3zdjęciaCC z2009/2011/2013,3podglądy i3miniatury,0pełnychoryginałów. Widok misy placowej i osobny kwietnik po dawnej fontannie nie tworzą pary przed/po. Wszystkie7miniatur koordynator obejrzał osobno; recenzje przy pakietach. Stan2026, RAL, wymiary i formalne kondygnacje UNVERIFIED. Kolorów2013synagogi nie łączyć w jeden stan z2020/2024.
