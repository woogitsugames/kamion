# ADR 0119 — DK8 przy Putry, powierzchnie i geometria pod pomostem

## Runda r2 — 12 listopada 2026, w toku

Sesja 7, gałąź gpt-landmarks-r2. Początek od rundy remizy cb699d74 i merge main
2c3939b2. Konflikt wygenerowanego streetscape_qa przyjęty z main; przed zmianą
powstaje świeży świat i porównanie kamer. Własny worktree pozostaje ten sam.

Zakres obejmuje wyłącznie część pod pomostem w hero_bridge.py i jej konfigurację.
Pomost, kapa, bariery, ekrany, jezdnie i pliki Claude nie są przedmiotem zmian.
Schody mają wymiary WORKING_VALUE i niepotwierdzone połączenie z chodnikiem;
według recenzji HIL przecinają ekran i kończą się na ścianie. Kandydat: jawna
flaga wyłączająca ich generację również przy wczytaniu starego spec.

Referencja: Rakoon, Commons 7204 May 2021 in Białystok, CC0. Pozyskano oryginał
5520×3680, SHA-1 61364bef59ec622ecf0a89e5a4c6e9cf6678504a zgodne z Commons.
Natywne kadry pokazują szare pionowe ścięcia przy ochrowych płaszczyznach filarów.
Rozrzut mieszanych ROI nie jest miarą samego zabrudzenia: wyodrębnione płaszczyzny
mają Y sd około 6,6–10,0, a dużą różnicę jasności daje światło pod pomostem.
Odtworzenie powierzchni ścięć i ocieplenie stosunku R/G należy ocenić na świeżych
renderach, zamiast podnosić szum całej farby. Parametry bez pomiaru pozostają WORKING_VALUE.

Kamery: wszystkie dotychczasowe kontrolne oraz dziesięć własnych kadrów detalu,
skopiowanych i połączonych z wcześniejszych dowodów viaduct-r10, bez zmian kamer
sesji sbs. Low/High, overcast/clear, stała kolejność i rozdzielczość przed/po.
Budżet: draws Low +0, instancje osobno, suma trójkątów najwyżej +2% w każdej kamerze.
Testy pojedynczego pliku w trakcie, pełny GIS na końcu. Python heavy i Unity
mają oddzielne wymagane sloty; nie uruchamia się generatora po cichu z importu.

Baseline wykonany: 58 kamer w każdej z czterech kombinacji, 232 PNG. Świat
415,5 s, bez fallback=True; przygotowanie brakujących map po merge main odbyło się
osobno pod heavy. Import Low+High zakończony OK. Dziesiąta kamera korzysta z GPS
i ogniskowej fotografii 7204. Po próbach 295/305/315 stopni wybrano 295, zachowując
wcześniejsze PNG/statystyki 280 stopni i rejestr podmiany jednej kamery. Poza
pozostaje UNVERIFIED: kierunek, pitch i wysokość oczu są WORKING_VALUE; różnice
ekranów i geometrii drogowej pozostają poza własnością tej sesji.

Wdrożony kandydat: `stairs_enabled=false` w konfiguracji, warunek także na bieżącej
konfiguracji przy emisji starego spec; brak potwierdzonego dojścia nie tworzy biegu.
`unpainted_chamfers=true` rozdziela istniejące 8 trójkątów pionowych faz na istniejący
bridge_concrete; wierzch i szerokie płaszczyzny zachowują pier_yellow. Kolizja
pozostaje jedną pełną bryłą, a domyślne wywołanie _prism nie zmienia zachowania.
Addytywny blok materials.py jest sterowany pier_paint.enabled; liniowy pigment
[0,46;0,34;0,135] jest WORKING_VALUE. Nie dodano materiału, shadera ani przebiegu.

Test ochrony pomostu rozszerzono o UV1 i COL oraz sprzeczne flagi starego spec;
osobny test porównuje komplet kolizji i podział istniejących trójkątów.
Pierwszy podgląd: 20 par detalu, Low mesh/instance draws +0. Usunięto 69 stopni
w czterech biegach, -690 tris; pełne spec.decks obu łańcuchów, deck SHA oraz
roads_qa zachowały treść baseline. Ochra w rozdzielonym ROI Low-overcast ma
85/72/42 sRGB (R/G 1,181). To podzbiór kamer, nie pełne potwierdzenie budżetu.

Po podglądzie dół pozostał zbyt czysty. Druga iteracja dodaje paint_weathering:
istniejącą modulację concrete_precast, splash_h=0,8 m i runoff o skali 0,35
(mapa do 4 m daje około 1,4 m na kolumnie). Własne pomalowane płaszczyzny mają
UV0.y od gruntu i UV1 od głowicy; fazy i kolizja zachowują stare UV. Krótkie
geometryczne zacieki kolumn są zastępowane teksturowymi, nie dublowane. Wspólny
materials.py ma tylko addytywny blok za flagą danych; shaderów nie zmieniono.
Liczba przebiegów pozostaje ta sama, koszt dodatkowych próbek PBR na A16 jest
UNVERIFIED bez telefonu. Wariant wymaga pełnego pomiaru kamer Low i High.

Test pierwszego wariantu nigdy nie uzyskał slotu i został celowo anulowany jako
nieaktualny. Druga iteracja wykona pojedynczy plik i generator kolejno pod jednym
slotem heavy; pełny GIS dopiero po akceptacji renderów na końcu rundy.
Stan: druga iteracja oczekuje heavy. Testy, wygląd weather oraz pełny budżet
pozostają UNVERIFIED do zakończenia walidacji i obejrzenia porównań.
