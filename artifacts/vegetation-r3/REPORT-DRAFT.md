To szkic, nie raport zamkniętej rundy. Końcowa walidacja przywrócenia jest w toku.

Gałąź gpt-vegetation-r3, baza po merge main 49de5a4e. Runda badała brak dużych koron G3-B, bloker B8 D51. Nie dostarcza zaakceptowanej zmiany produkcyjnej; vegetation.py i testy przywrócono do stanu r1. Patch B oraz wszystkie próby zachowano jako odrzucone dowody.

Na lokalnym ortofoto GUGiK 2024 potwierdzono obszar czterech koron. Pin źródła 19d7c3ca5d2192b1d0367c8d039e41aa60221927755b45c6a6763e933d96258b. Odczytane punkty są środkami koron, nie pomierzonymi pniami. Niepewność około 3 m, wysokości 12,5–15 m i zastępcze gatunki były WORKING_VALUE. Fotografia zsolt z 2017-07-29, CC BY-SA 4.0, potwierdza charakter zieleni, lecz poza klasy B wymaga obecnie korekty przez sesję SBS.

Odczytane korony leżą w pasie przed JRG2. Nie potwierdzono ich tożsamości z drzewami pasa dzielącego wskazanymi w B8. Źródłowe potwierdzenie tych koron nie dowodzi więc poprawnego wyboru obiektów dla konkretnego blokera. Po korekcie pozy SBS trzeba ponownie zidentyfikować docelowe nasadzenia; odrzuconych punktów nie traktować jako gotowych danych B8.

Wariant A przeszedł blocked dla dwóch z czterech punktów i dodał dwa drzewa. W próbie B/120 Low-overcast wywołania instancji wzrosły 205 do 209, łączne 665 do 669. Został odrzucony. Ablacja po usunięciu dodatków dała ponownie 205 wywołań instancji i obraz identyczny z baseline, więc przyrost kosztu nie pochodził z samego importu.

B1 zastępował pobliski syntetyczny samosiew, zachowując prototyp, wariant i komórkę 64 m. Pełny producent zamienił tylko jedną brzozę; trzy punkty odłożono, liczba rekordów nie wzrosła. W próbie Low koszt wyniósł nadal 460 wywołań statycznych i 205 instancji oraz raportowane 547 tys. i 28 tys. trójkątów. Brak zmiany kosztu nie zamknął celu wizualnego. Obraz różnił się 5307 pikselami, ale żaden nie leżał w stałym obszarze koron. B1 również odrzucono.

Oddzielna diagnostyka klonu zmieniła tylko h z 8 do 13,8 m w wejściu renderera. Nie jest pełnym wynikiem producenta B2. Powiększyła rzadką sylwetkę i odseparowane skupiska liści zamiast odtworzyć gęstą koronę. Koszt jednej kamery pozostał ten sam, zmieniło się 11 565 pikseli. Próba odrzucona.

Niezależny krytyk potwierdził odrzucenie wszystkich prób oraz otwarty stan B8. VISUAL-CRITIC-A.md i VISUAL-CRITIC-B.md rozróżniają pełny producent od diagnostyki wejścia. Arkusze do 960 px: rejected-comparison.jpg, probe-b-sheet.jpg, B1-difference.png. Źródła, daty i licencje w photo-references.json; fotografia nie trafia do gry.

Baseline obejmuje 368 obrazów: 268 kamer kontrolnych z r1 B, ponownie użytych po zgodności pinów źródeł i 130 GLB, oraz 100 świeżych obrazów 25 póz B w Low/High clear/overcast. Obejrzano wszystkie 16 świeżych arkuszy. Nie wykonano pełnej macierzy after dla odrzuconych kandydatów i nie ogłasza się ich zgodności budżetowej na wszystkich kamerach. all-camera-costs.csv raportuje wszystkie kamery baseline i jawnie oznaczone próby, z osobnymi wywołaniami statycznymi i instancji. trisK ma całkowitą precyzję, nie jest pomiarem GPU.

Testy celowane eksperymentów: A 16/16, B 22/22. Końcowy pełny GIS: 525 passed, 1 xfailed, 1 failed w 1390,34 s, z wstrzymaniem przez watchdog w tym czasie. Jedyną porażką jest test_road_fidelity.py::test_report_not_stale. Dowód względem bazy 49de5a4e potwierdza nieaktualność raportu dla siedmiu źródeł już w bazie i ich brak zmian po normalizacji końców linii. Raport drogowy pozostaje niezmieniony; nie regenerowano cudzej dziedziny. To jawna porażka testu, nie zielony GIS.

Po testach ponownie potwierdzono zgodność 130 GLB, 64 plików instancji i siedmiu pinów źródeł z baseline. Megascans: 15 dostępnych zasobów, fallback false; eksperymentalne QA ortofoto nieobecne. Import przywróconego świata zakończył się kodem 0. EditMode i kontrola probe wymagają jeszcze uzupełnienia.

Nie zmieniano dróg, landmarków, overrides.yaml ani runtime importera. Nie używano telefonów, nie scalano do main i nie pushowano. Każdy ciężki generator i GIS przechodzi przez heavy, Unity przez osobny slot. Po zamknięciu wspólne skutki uboczne generatora trzeba przywrócić z HEAD; migawki pozostają w artefaktach.

Następna runda po merge main zajmie się berberysem zgodnie z nowym feedbackiem lidera. Źródło bliskie: rzeczywiste zdjęcie Rakoon z 2020-11-02, CC0, wskazane w docs/REFERENCES.md. B8, rytm Putry, sosny, tuje, źródłowe pobocza, Pietrasze i sezonowość pozostają otwarte. GPU A16 i ruch są UNVERIFIED.
