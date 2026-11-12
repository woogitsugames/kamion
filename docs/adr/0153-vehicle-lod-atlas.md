# ADR 0153 — LOD1/LOD2 aut

Status: implementacja i statyczna recenzja edytora PASS; końcowy GIS w toku.
Gałąź gpt-s16-r1. Baza: origin/main 421f1b4fb (12.11.2026).

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
Progi 40/100/300 m dla placowych są WORKING_VALUE zweryfikowane w edytorze;
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

## Pomiary w edytorze

Natywny odczyt 72 pozycji potwierdza rzeczywiste pasma. Osobówki Low:
15,9 m LOD0, 16,1 m LOD1, 42,4 m LOD1, 42,6 m LOD2; High: 37,4/37,6
i 127,4/127,6 m. Placowe Low: 19,9/20,1 i 49,9/50,1 m; High: 59,9/60,1
i 149,9/150,1 m. Cull Low nadal 150 m. Przykład hatch: LOD0 14 podsiatek,
4092 tris; LOD1 2 podsiatki, 816 tris; LOD2 2 podsiatki, 86 tris.
Tractor LOD1/2: 2 podsiatki, 286 tris, ten sam natywny mesh i materiały.
`artifacts/gpt-s16-r1/projection-probe.json` jest pomiarem, a nie dowodem widoczności.

114 kamer × 4 warunki = 456 porównań; dodatkowo 40 odsłoniętych pozycji
× 4 = 160. Wszystkie mają osobne statystyki przed/po w `CAMERAS.md` oraz
`clear/CAMERAS.md`. W podstawowym zestawie delta batchy instancji Low wynosi
−312..0, High −395..0; w dodatkowym Low −310..−34, High −381..−97.
Żadna kamera Low nie zwiększa draws ani tris. Liczba instancji i geometria
pozostają identyczne. Cab-dash Low: batche instancji 307 → 190, tris 17k → 17k;
osobne estymaty sceny 388 draws / 344k tris bez zmian.

SceneStats to estymata CPU przed SRP batching. TrisK są ucięte do tysięcy;
dokładną niezmienność geometrii potwierdza osobny audyt GLB. Instanced draws
liczą zgłoszenia batchy instancji, a nie wszystkie przebiegi GPU/SRP.
Nie wyprowadzamy z tych liczb oszczędności milisekund.

## Weryfikacja i ograniczenia

Ostateczny wariant B: 420 chronionych węzłów GLB identycznych buforowo,
68 istniejących odległych LOD z identycznymi trójkątami, 14 nowych aliasów
placowych identycznych z LOD1, zero błędów (`glb-audit.json`). 456 wcześniejszych
materiałów natywnych ma po sprzątnięciu cache identyczny SHA256; dodano tylko
`M_vehicle_lod_details`. Siedem ubocznych zapisów Unity cofnięto z bazowej kopii:
dwa nieużywane stare car_dirt `_SrcBlend` oraz pięć ukrytych `_MainTex` znaków.
Jawne różnice są w `native-cleanup-ledger.json`; nie zmieniono generatora znaków.

8 testów atlasu wraz z deposition/yard: 37 passed. Końcowy EditMode:
452 passed, 0 failed, 0 skipped. Pierwszy pełny GIS wykrył wyłącznie nieaktualny
raport fidelity (926 passed, 3 xfailed, 1 failed); odświeżono go bez edycji
roads/* i jego 9 testów przechodzi z 1 xfail. Pełne powtórzenie GIS trwa;
wynik zostanie dopisany przed push.

Autor obejrzał wszystkie porównania i lokalne zdjęcia konstrukcji aut/kół;
niezależny visual-critic ocenił 456 podstawowych i 160 dodatkowych par:
PASS dla braku nowej widocznej regresji w statycznych obrazach edytora.
Wyszukiwanie dodatkowych pozycji porównuje maskę solo z głębią świata,
ale końcowa recenzja używa zwykłych renderów. Wcześniejsze zasłonięte próby
są odrzucone. SUV przy 127,5 m jest za mały do oceny detali koloru;
można ocenić brak widocznej plamy w całym kadrze. Istniejące przejścia
okrągłych kół w wielokąty oraz cull Low są widoczne także w baseline.

PASS nie obejmuje przejazdu w ruchu, kompresji ASTC ani telefonu. Pomiar GPU
p95 na A16, ocena celu 33,3 ms i scalenie do main należą do lidera.
