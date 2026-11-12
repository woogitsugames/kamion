# Pakiet furniture r2 — stan roboczy przed zamknięciem

Gałąź: gpt-furniture-r2. Kontynuacja r1, następnie merge main 522361aa do tej
gałęzi. Bez merge do main, push, telefonu i zmian barier drogowych. Ostateczny
SHA kodu i zasobów zostanie wskazany w REPORT po końcowych kontrolach.

## Zakres zmiany

Lica znaków mają deterministyczne, miejscowe zużycie: osad przy dolnej krawędzi,
drobne uszkodzenia brzegu oraz łagodniejsze blaknięcie czerwieni. Siła zero
zachowuje wejście; alfa i RGB poza pokryciem znaku pozostają zachowane.
Low otrzymało dwa dystanse mocujące w istniejącym materiale plate_back.
Mocowania High i kolizje nie są zmieniane przez tę poprawkę.

Nowy Kamion/Furniture Sign zachowuje bufor UnityPerMaterial i funkcje URP Lit.
Liczba zadeklarowanych przebiegów wynosi 9 przed i po; pozostałe osiem jest
używane przez UsePass. Własny Forward dodaje odpowiedź kierunkową przed mgłą.
Nie tworzy światła URP, tekstury ani dodatkowego przebiegu. Istniejący slot
_EmissionColor zawiera liniowy współczynnik zwrotu; zwykła emisja jest wyłączona.
Domyślne kontrakty _Tint i _Tile pozostają bez zmian.

Flaga danych plate_back.furniture_sign_fronts w materials.py uruchamia
addytywną rejestrację w WorldPbrMaterials.cs. Źródłem listy jest rzeczywiste
props_meta.json: 36 lic w bibliotece, 35 przypisanych materiałów potwierdzonych
odczytem sceny. Znaki fasadowe są wykluczone, cudze jawne definicje zachowane.
Bez flagi fabryka zachowuje oryginalny Lit, teksturę i GUID materiału.
Nie zmieniano ogólnego importera, asmdef ani QualityProfile.

FurnitureRetroSource odczytuje istniejący TruckLights, VehicleBody i cztery
autorskie sockety mijania/drogowych. Nie zmienia tych komponentów ani scen gry.
Brak aktywnej pary wyłącza odpowiedź. W ustalonym stanie nie tworzy tablic;
po zmianie sceny ma krótkie ponawianie wyszukania brakującego riggu.

## Dowody obrazowe i ograniczenia

before oraz after: po 55 kamer dla Low/High i clear/overcast/dusk, razem
330 wariantów każdej strony. Wcześniejsze obrazy po zmianie zachowano
w iteration1; bieżący after uwzględnia korektę ekspozycji, asymetrii wiązki
i wyszukiwania socketów. Arkusze compare wymagają jeszcze wykonania w heavy.

exact-before i exact-after: po 165 kamer Low. Każdy validation.json potwierdza
zgodność liczb z zaokrąglonym runnerem i zamrożonymi stats.txt; dowody wiążą
SHA256 obu wejść. Skan wszystkich liczników jest w frame-budget.json/csv
oraz frame-coverage.json. Statystyki są estymacjami CPU, nie pomiarem GPU.

night-rig/after3: po 24 PNG Low i High, odległości 25/50/100 m, dwa kąty
widzenia oraz cztery tryby: odpowiedź materiału wyłączona, mijania, drogowe,
komponent źródła wyłączony. Każdy przypadek ma source-evidence.json z czterema
rzeczywistymi próbkami przed kamerą. Wyłączenie komponentu nie jest dowodem
na osobny przełącznik w UI kierowcy. Własna kopia sceny i callback editorowy
utrzymują tryb podczas przeładowania; nie publikują sztucznych pozycji świateł.

Manualne EV100=5, gain800, siła drogowych, odcięcia i zasięg150 m są
WORKING_VALUE. Model słońca kończy się na -8 stopniach, dusk ma -5.
Nie dowiedziono pełnej nocy ani kalibracji lokalnej folii. Nie ma okluzji
ścieżki reflektor–znak. Używany renderer Low/High jest Forward; wariant
GBuffer nie otrzymał odpowiedzi. Brak dowodu Vulkan/APK, strippingu,
GPUp95, PSS, działania podczas jazdy i na telefonie.

Niezależny przegląd night-preview/REVIEW-after3.md obejmuje tylko cztery
podglądy25 m z tieru Low; low/high w nazwach oznaczają tryb reflektorów.
Potwierdzono miejscową reakcję bez oczywistego halo. Realizm siły i praktyczna
czytelność pozostały niepotwierdzone. Przegląd wszystkich kamer jeszcze trwa.

Bezpośredni kadr zdjęcie/render używa istniejącej kamery
sbs-g3-b-297817221966185. Referencja: Mapillary, zsolt, 2017-07-29,
CC BY-SA4.0. Rektyfikacja pobrana z main ma SHA zgodne z istniejącą definicją.
Poza ma confidenceB i WORKING_VALUE; zdjęcie jest historyczne, bez prawa
wnioskowania o dokładnej dzisiejszej pozycji i kalibracji fotometrycznej.

## Pomiary i testy potwierdzone

- Wszystkie330 wariantów: DrawEst mesh +0, instancji osobno +0, cieni mesh +0.
- Wszystkie165 dokładnych Low: max tris +0,189979830474662%, limit +2% zachowany.
- Import: Low120,7→120,8 MB, High262,8→262,9 MB danych mesh/instancji/kolizji,
  nie PSS urządzenia. Generator after1:64 chunki,406,8 s; log zachowany.
- Własne pojedyncze Python:17/17,9/9 i10/10; logi pytest-test_furniture*.
- FurnitureSignTests:16/16, w tym rzeczywiste GPU versus Lit, alfa, HDR1/800,
  strony, kąty, dystans, ekspozycja, asymetria, źródła, GUID i rodzina materiałów.
- Końcowe EditMode:340/340,0 failed,0 skipped; XML i log w test-results.
- Chroniona geometria: PENDING, proces czeka na slot heavy. Nie deklarować PASS.
- Pełny GIS i physics/gate3: PENDING, wykonywać przy zamknięciu rundy w heavy.

Porażki wcześniejszych fixture zachowano. Pierwszy shader probe nie ustawiał
aktywnego tagu URP, inny mieszał kąt i odległość; poprawiono warunki próby.
Faktyczne błędy liniowego współczynnika i timingu socketów naprawiono i sprawdzono.
Nie zamieniać samego uruchomienia w PASS ani ukrywać ograniczeń statycznego obrazu.

## Odtworzenie i integracja

unity-step.ps1 zawsze pobiera slot Owner gpt-furniture z main, zwalnia go
w finally i cofa skutki uboczne ustawień Unity. heavy-step.ps1 pobiera heavy
pod aktualną gałęzią. Nigdy nie uruchamiać dwóch jego procesów równolegle
z tym samym właścicielem: ponowne Acquire tylko odświeża istniejący slot.
compare-after-geometry.ps1 dlatego czeka na terminalny proces geometrii.
Żaden helper nie usuwa cudzych slotów ani PHONE_RUN.

Po integracji lider powinien zachować unie flag furniture_plinth_detail i
furniture_sign_fronts w plikach wspólnych, a produkty świata regenerować
po połączeniu zmian. Źródła CC0/Megascans/Fab nie trafiają do gita.
Przyszła r3: referencje przystanków są w bus-reference-preview i shortliście;
bliskość oraz brak tagu nie dowodzą obecności lub braku wiaty/kosza.

Oględziny pary SBS: znacząca rozbieżność układu sceny i brak porównywalnego zbliżenia znaków. Ta para nie dowodzi zgodności lic ani uchwytów ze zdjęciem; zachowano ją z tym ograniczeniem, bez poprawiania wspólnych kamer i cudzych obiektów. Własny kadr diagnostyczny tyłu znaku pokazuje mocowania, ale nie zastępuje dopasowanego zdjęcia.

Przed końcowymi zestawami wykonano wyłącznie mały audyt hashy wejść,
bez uruchamiania pytest ani fidelity/run.py. existing-test-input-audit.json:
23 wejścia raportu i sam raport są niezmienione od bazy r2 po merge main
3fe0c97f, wraz z roboczymi blobami. Dwa rzeczywiste hashe nie odpowiadają
raportowi. Jest to nowy odczyt r2, nie wolno kopiować liczby siedmiu z r1.
Normalizacja LF zmienia także poprawnie pasujące pliki; nie jest naprawą
raportu ani zamiennikiem testu. Trzy wejścia znanej niezgodności scenariusza
physics również zachowały bloby bazy r2. Wyniki pełnych testów nadal PENDING.

Aktualizacja końcowych kontroli:root i niezależny reviewer obejrzeli330/330 par na60 arkuszach≤960px, bez nowego widocznego blokera furniture (compare/REVIEW.md). Chroniona geometria6833→6833,0 różnic (protected-geometry-comparison.json). Wszystkie arkusze powstały jako pojedyncze małe interaktywne przeglądy; zbędny pełny batch anulowano, bez powtórnego dekodowania. KońcoweGIS/physics nadal oczekują na heavy. Kod/zasoby52668015 pozostają bez zmian.
