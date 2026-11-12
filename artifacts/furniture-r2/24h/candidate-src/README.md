# Źródła kandydata r2

Stan na 2026-11-12 około 03:04: shader, publisher i addytywna fabryka są już
w kodzie gry i mają 13/13 zaliczonych prób EditMode, bez pominięć. Bazowe obrazy
330 wariantów i payloady geometrii zapisano przed aktywacją flagi świata.
Python kandydata jest zmieniony; jego pojedyncze testy i generator czekają
w sekwencji candidate-build.ps1. Same próby GPU nie dowodzą ukończenia rundy
ani wyglądu przy prawdziwym riggu nocą. Produkcyjne C# jest nadrzędnym źródłem
względem wcześniejszego fragmentu FurnitureSignFactory.cs.fragment.

Prototyp zachowuje właściwości, układ UnityPerMaterial i funkcje URP Lit.
Forward ma tę samą funkcję PBR i dodaje zwrot światła przed tą samą mgłą.
Osiem pozostałych przebiegów jest używane z istniejącego URP Lit; liczba
przebiegów wynosi 9 przed i po. Nie powstaje dodatkowe światło ani przebieg.
GBuffer z URP nie zawiera zwrotu; prototyp dotyczy bieżącego renderera Forward,
a zgodność konfiguracji Low/High trzeba sprawdzić przed włączeniem w grze.

Własny keyword `_FURNITURE_RETRO` wymaga jawnej flagi materiału. Użyty istniejący
slot `_EmissionColor` jest współczynnikiem zwrotu, nie emisją: `_EMISSION`
nie jest kompilowany w naszym Forward. Pozostawia to identyczny bufor URP we
wszystkich przebiegach i pozwala porównać keyword off z oryginalnym Lit.
Potrzebny test GPU liniowego współczynnika oraz zgodności obrazu off/original;
nie wolno wnioskować o zgodności wyłącznie z identycznego tekstu funkcji.

Publisher odczytuje istniejący TruckLights i prawdziwe sockety LIGHT_LowBeam_L/R oraz LIGHT_HighBeam_L/R,
zapisane w manifeście ciężarówki. Nie zmienia ciężarówki ani nie zakłada pozycji
reflektorów, gdy ich brak. Brak źródła/socketu, wyłączony komponent lub światła
zerują stan. Nie ma wymyślonego źródła przy kamerze. Geometria światła i oka jest
oddzielna, więc zmiana kamery zmienia kąt obserwacji. Częstotliwość szukania
brakującego riggu jest ograniczona do 1 Hz, bez tablic w ustalonym stanie.

Źródła zasad optycznych, bez stosowania amerykańskich progów do Polski:
- FHWA, opis kątów i zależności jasności: https://highways.dot.gov/safety/other/visibility/workshops-nighttime-visibility-traffic-signs-summary-workshop-findings-7
- 3M, jakościowy opis stożka powrotnego: https://www.3m.com/3M/en_US/road-safety-us/resources/road-transportation-safety-center-blog/full-story/~/road-signs-retroreflectivity/?storyid=328c8880-941b-4adc-a9f9-46a1cd79e637

To własna aproksymacja do oceny, nie tabela fizycznego RA ani konkretna klasa
folii. Siła, szerokość wiązki, kąta powrotu i zasięg 150 m są WORKING_VALUE.
Brakuje cienia rzucanego od reflektora: formuła analityczna nie dowodzi
widoczności od źródła przez przeszkody. Ten limit wymaga jawnej oceny, nie
przemilczenia. Światła uliczne nie wyzwalają tej formuły.

Przed akceptacją: factory/cleanup flagi, UV/alpha, brak zawsze świecącego lica,
source off/missing/disabled, przód/tył, kąt obserwacji i odległość, GPU off/original,
obraz z realnego riggu nocą i dzienny Low/High, wszystkie liczniki kamer oraz
niezależna ocena. Mocowania Low i zużycie tekstury wymagają osobnej oceny obrazu.
Źródło części szkieletu: Unity Technologies ApS, Unity Companion License,
https://unity.com/legal/licenses/unity-companion-license; pliki źródłowe i hashe
w provenance.json. Skrypt odtworzenia: prepare-sign-prototype.ps1.
