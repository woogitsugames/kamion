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
## Wynik r2

Końcowy świat: 1226,0 s, w tym obserwowana pauza watchdog 769 s; nie jest to
benchmark CPU. Bez fallback=True. Usunięto 69 stopni oraz zastąpione geometryczne
zacieki, łącznie -906 tris. Oba spec.decks i deck SHA są identyczne z własnym
świeżym baseline; roads_qa także. Payload runoff ma maks. v=16,034, nie wchodzi
w zarezerwowane zakresy UV dla innych trybów.

Obejrzano 32 arkusze wszystkich 232 par (58 kamer, Low/High, clear/overcast),
natywne wycinki i pary z fotografią. 116 PNG identycznych pikselowo. We wszystkich
116 porównaniach Low maks. delta mesh draws=0 i instance draws=0; szacowana suma
tris od -0,4202% do 0%. W ROI ochry Low-overcast 84/79/47 -> 85/71/41 sRGB,
sd Y 3,377 -> 4,880; u dołu Y 63,114 -> 54,746. To pomiary obrazu, nie reflektancji.
W clear inne oświetlenie nie daje tego samego stosunku dół/góra. Zacieki są delikatne.

Pojedynczy plik: 14/14 PASS, 0,29 s. Pełny GIS: 585 passed, 1 xfailed, 983,56 s.
EditMode: 295/295 PASS. Physics/gate3: 47 passed, 1 failed, 295,69 s; znany
test_generator_reproduces_committed_scenarios różni top_speed_flat_comb.json.
Wejścia tej porażki nie zostały zmienione względem początku rundy (2c3939b2).
Cache 64 High GLB + 64 Low GLB + 64 instancje, manifest i własne źródła są zgodne
przed i po testach. Walidacja była wstrzymywana przez globalny watchdog.

Stan: gotowe do recenzji w zakresie r2, z jawną znaną porażką physics poza dziedziną.
Nie ma pomiaru GPU A16 ani niezależnej akceptacji bramki 3. Poza fotografii,
wymiary konstrukcyjne, rozbieżne ekrany, spód i wygląd oczepów pozostają otwarte.
Nie zmieniono dróg, kapy, ekranów, barier, shaderów ani QualityProfile. World Surface
i World PBR mają ten sam zestaw UniversalForward / ShadowCaster / DepthOnly.
