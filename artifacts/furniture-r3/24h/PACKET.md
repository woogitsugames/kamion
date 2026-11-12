# Pakiet furniture r3 — stan przed pełną walidacją

Gałąź `gpt-furniture-r3`, jeden worktree sesji. Merge main: `889201d5`, baseline po merge: `162214c3`. Kod kandydata po poprawce dachu: `973a50be6bb0965f397bb21d9d75fcd8ae8ca56c`. Późniejsze commity zapisują diagnostykę i dowody. Nie scalano do main ani nie pushowano.

## Zakres i pochodzenie

Nowy `bus_shelter_red_0120` jest wybierany wyłącznie dla OSM 5802408812 i 5802408814. Pozostałe wiaty zachowują generic. Źródła, pozycje, yaw, wysokości, kolejność wyboru i kotwice Fab pozostawiono bez zmian. Nie zmieniono barier, dróg, chodników, budynków, koszy ani słupków. Brak tagu lub widoczności na zdjęciu nie był podstawą do usuwania obiektów.

Zdjęcia Mapillary: 1911352299378570 (kino, 2024-07-26), 214816220453640 (czadzik, 2018-07-21), 5726790167361670 (grobin, 2019-10-20), CC BY-SA 4.0. Autorzy, adresy stron, licencje i hashe oryginałów: [reference/provenance.json](reference/provenance.json). Oryginały pozostają w istniejącym źródle tylko do odczytu. Trzy SHA256 sprawdzono ponownie z aktualnymi plikami. Hash wycinka jest osobny; crop 450 × 430 px z x=1180, y=880 nie generuje nowych pikseli. Bliskość zdjęcia ani pora UTC nie dowodzą widoczności obiektu.

Model ma czerwoną ramę, płytko wygięty zamknięty dach, pięć podpór bez środkowego słupka wejścia, cztery przeszklone pola i lżejsze podpory ławki. Dach/ramę, szkło i istniejące drewno podzielono na trzy sloty. Low ma dwa segmenty dachu, High cztery. Długości podpór dopasowano do rzeczywistej spodniej powierzchni segmentów. Wymiary zastanego obrysu, barwa, alpha, roughness i krzywizna są WORKING_VALUE, a nie pomiarami lokalnej wiaty.

Kolizja jest identycznym zastanym pełnym prostopadłościanem generic. Wizualnie otwarte wejście nie oznacza przechodniej kolizji. Nie zmieniono globalnych `steel_painted` i `shelter_glass`. Wspólny `materials.py` otrzymał wyłącznie dwa identyfikatory własnego wariantu; istniejąca obsługa przezroczystości importera pozostała bez zmian. Brak nowego shadera, światła, przebiegu lub pola QualityProfile w r3.

## Baza i generator

Baseline obejmuje 236 PNG: po 59 kamer Low/High × clear/overcast. Plik kamer dodaje 11 własnych wpisów; renderer dodaje 48 kontroli sceny. Nie wolno utożsamiać tych 11 wpisów z pełnym zasięgiem. Dodatkowe `before-side` ma osiem obrazów drugiego narożnika, osobno od budżetu. Dokładne bazowe liczniki CPU Low: 118, ze zgodnością runner/frozen/floors oraz proof SHA256 w `exact-before`.

Po bazie generator `after1` trwał 546,9 s, wyeksportował 64 GLB, 479 MiB High i 150 MiB Low. W logu brak `fallback=True`. `world-context-after1.json` zapisuje rzeczywisty HEAD i czas startu procesu. Nie powtarzano aktualnego cache PBR. Każdy generator i skan GLB pobiera slot `heavy`; każdy Unity pobiera slot `gpt-furniture`, a zwalnia go w finally. Pełny GIS dopiero na końcu rundy.

Audyt [instances-after.json](instances-after.json): 64 niezmienione znormalizowane multizbiory instancji, 23 wiaty, dokładnie dwa wybrane czerwone warianty. Wszystkie pola instancji poza tymi dwiema nazwami prototypu identyczne z bazą. Porównanie zachowuje duplikaty, lecz nie wymaga kolejności wierszy, którą eksporter sortuje według prototypu. To dowód metadanych, nie geometrii ani liczby widocznych instancji w kamerze.

Kontrola chronionej geometrii zakończona: 6833 payloady przed i 6833 po, zero różnic w `protected-geometry-comparison.json`. Skan GLB działał w slocie heavy. To osobny dowód eksportowanej geometrii, niezależny od audytu JSON; zakres wykluczeń mebli jest jawny w `snapshot_geometry.py`.

## Wczesna kontrola wizualna — zakres ograniczony

Wczesny import: OK, 64 chunki, korytarz 41. Dane mesh/instancji/kolizji Low 120,8 MB i High 262,9 MB, bez zmiany zaokrąglonych sum względem bazy. To nie pomiar PSS. Dodatkowe cztery kamery Low-clear w `early-after1` nie zastępują standardowych 236 obrazów.

Root i niezależny furniture_review obejrzeli 4/4 podglądy 960 px: front i narożnik obu wiat. Brak widocznego blokera, szczeliny dachu lub rażącego sortowania. Poprawa przejrzystości, czerwonej ramy i ławki; pozostają słaby odczyt powierzchni dachu od frontu i niemal niewidoczne szyby. Nie wzmacniać alpha przed High. [Obserwacje i cztery liczniki](preview-early-after1/OBSERVATIONS.md), [niezależna recenzja](preview-early-after1/REVIEW.md).

W tych czterech kamerach mesh/cienie DrawEst +0, instancje Anders −1, Factory 0. Liczba renderowanych instancji Factory wzrosła o jeden; przyczyny nie ustalono osobno. Zaokrąglone trisK nie dowodzą dokładnego przyrostu. Kamera jest diagnostyczna WORKING_VALUE, bez dopasowania do zdjęcia. Ocena nie obejmuje High, overcast, przeciwnego narożnika, ruchu ani urządzenia.

## Kontrole nadal wymagane przed zamknięciem

Pełne 236 renderów i wszystkie kamery, dokładne 118 Low po zmianie, osiem obrazów `after-side`, draws mesh/instancji osobno, Low tris ≤+2%, analiza i niezależna ocena całej serii: OCZEKUJĄCE. Trzy sloty prototypu ani cztery udane kadry nie dowodzą budżetu sceny.

Własny `test_furniture_shelters_0120.py`: 10 passed w 0,27 s w slocie heavy. Sprawdza jawny wybór rodziny, niezmienną kolizję, otwartą geometrię wejścia, kontakt podpór z dachem, wysokość, sloty i LOD. Nie zastępuje pomiaru sceny. Końcowy pełny GIS, physics/gate3 i EditMode: OCZEKUJĄCE; wyników r2 nie przeniesiono jako wyników r3.

Po pełnej ocenie trzeba uzupełnić ten pakiet i ADR 0120, zapisać końcowy REPORT po polsku, skopiować artifacts r3 do main przez robocopy, następnie rozpocząć r4 z aktualnym main w tym samym worktree. Telefon, adb, pomiary urządzenia/GPU/PSS pozostają poza tą sesją.
