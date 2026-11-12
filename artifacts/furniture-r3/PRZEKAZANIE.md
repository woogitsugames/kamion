# Przekazanie sesji 8 — furniture

Stan na 12 listopada 2026 r. Praca kończona na wyraźne polecenie właściciela z powodu limitu tygodniowego. **Runda 3 jest otwarta i niegotowa do integracji. Nie ma końcowego REPORT.md.** Nie uruchamiać automatycznie kolejnej rundy.

Repozytorium: `C:\Users\matma\Documents\Claude\kamion`. Własny worktree: `.claude/worktrees/gpt-furniture`, bieżąca gałąź: `gpt-furniture-r3`. WIP i STATUS są zapisywane w Git. Nie wykonano push, scalenia do main ani operacji na telefonie. Dziedzina obejmuje meble, znaki i latarnie; bariery, drogi oraz Kwadrat pozostają poza zakresem.

## Bezpieczne zatrzymanie

W `artifacts/furniture-r3/24h/STOP_REQUESTED` zapisano polecenie zatrzymania. Własne helpery `unity-step.ps1` i `heavy-step.ps1` sprawdzają je przed pobraniem slotu i startem nowego procesu. Kod 75 oznacza świadome zatrzymanie na polecenie właściciela, a nie nieudaną próbę Unity.

W chwili polecenia działał generator after3, rodzic PowerShell PID 68124, dziecko uv PID 80828. Pozwolono mu dokończyć pracę oraz sekwencyjne audyty w już zajętym heavy. Nie ubijano generatora ani Unity. Końcowy potwierdzony wynik i stan procesów są dopisane na końcu tego pliku.

## Zamknięte rundy

- **R1, `gpt-furniture-r1`:** podmurówka i siatka ogrodzenia, betonowy słup oraz rdza tyłu znaku. Kod `7adbe982`, zamknięcie `6b48088b`. REPORT i artifacts skopiowane do main. 220 kadrów: draws +0. Z dokładności zaokrąglonych liczników udowodniono limit tris dla 102/110 Low; pozostałych 8 nie przedstawiano jako udowodnione. EditMode 268; znane niepowodzenia GIS/fizyki opisano w raporcie.
- **R2, `gpt-furniture-r2`:** deterministyczne zużycie znaków, uchwyty, odblask zależny od rzeczywistego stanu świateł ciężarówki. Kod/produkty `52668015`, zamknięcie `5d7ff5c9`. 330 par obejrzanych, wszystkie delty DrawEst +0; 165 dokładnych Low, maksymalny wzrost tris 0,18997983%. EditMode 340/340, physics/gate3 48/48. GIS 644 passed, 1 xfailed, 1 failed z dwoma nieaktualnymi hashami ówczesnej bazy. Odblask bez modelu zasłaniania i kalibracji fotometrycznej. REPORT i artifacts w main.

## R3: co zmieniono

Baza po połączeniu main `889201d5`: checkpoint `162214c3`. ADR wspólny dla rund: `docs/adr/0120-furniture-24h.md`. Dokument roboczy: `artifacts/furniture-r3/24h/PACKET.md`.

Na podstawie Mapillary powstała czerwona wiata `bus_shelter_red_0120`: płytko łukowy zamknięty dach, pięć podpór bez środkowego słupka wejścia, cztery przeszklenia i siedzisko. Przypisanie wyłącznie do potwierdzonych węzłów OSM 5802408812 oraz 5802408814. Pozostałe przystanki i kosze zachowują dotychczasowe rodziny. Pozycje, yaw, wysokości, seedy i liczność instancji mają być zachowane. **Kolizja pozostaje pierwotnym pełnym boksem; wizualne wejście nie oznacza fizycznego przejścia.** Wymiary i kolor to wartości robocze, bez pomiaru fotogrametrycznego.

Referencje: Mapillary 1911352299378570, 214816220453640, 5726790167361670. Autorzy/licencje, hashe oryginałów i wycinka są w `24h/reference/provenance.json`. Nie korzystano z Google Maps/Street View/Earth/3D Tiles.

Pierwszy pomiar ujawnił, że nowa rodzina dostawała fallback widoczności 30/120 m, zamiast 60/300 m rodziny bazowej. Własny `FurnitureShelterPolicySave.cs` addytywnie dziedziczy politykę rodziny podczas zapisu Instances.asset. Nie zmieniano importera ani `tools/worldgen/roads/*`. **Pythonowy estymator roads nadal nie zna nowej rodziny; jego cache nie stanowi dowodu rzeczywistej widoczności.**

Iteracja 2 przy prawidłowym 60/300 m przekroczyła budżet **Low +3 draws** na `g3b-eye-s1482` w obu światłach. Jej wynik nie jest PASS. Dlatego kandydat 3 scala nieprzezroczyste części obu rodzin w jeden slot palety, zachowując szkło oddzielnie. UV0.x wybiera jedną z czterech dotychczasowych receptur. Addytywny keyword `_FURNITURE_SHELTER_PALETTE` w WorldSurface zachowuje ich linearne RGB, smoothness i skyDown, bez nowych tekstur i przebiegów. Factory opt-in tylko przez dane `shelter_opaque_0120`. Nie obniżano cull ani geometrii w celu ukrycia kosztu.

Źródła: własne `streetscape/{props,furniture,fab_details}.py`, addytywne `materials.py`, `WorldSurface.shader`, `WorldPbrMaterials.cs` oraz własny hook edytora i testy. Zamrożone SHA siedmiu plików produktu są w `24h/candidate3-source-fingerprint.json`; po teście GPU nie zmieniano ich. Istotne commity kandydata: `a171cef8`, `078e01d2`, `eb6871ec`; dowód 18 testów GPU `83e6b036`.

## Co rzeczywiście sprawdzono

- Własne testy polityki: 7/7, w tym zapis/wyładowanie/ponowny odczyt assetu. Audyt 196 prototypów: zmiana wyłącznie końców LOD nowej rodziny do polityki bazowej.
- Kandydat 3: **18/18 testów materiału/GPU**, 0 skipped. Odczyty RGB/smoothness dla czterech receptur Low/High oraz skyDown .5/.5/.5/0, opt-out, factory i 3 przebiegi. To próby kontraktu wejściowego, nie pełne oświetlenie sceny, APK ani czas GPU.
- Kandydat 3: **14/14 focused GIS**, 0,55 s, w wymaganym heavy. Zachowanie trójkątów/normali po scaleniu, wejście, dach/podpory, kolizja i selekcja danych. Log: `24h/pytest-shelters-candidate3.log`.
- Poprzednie generatory: 64 chunki, brak fallback Megascans. Chronione payloady geometrii 6833 → 6833 bez zmian; 64 JSON instancji, 23 wiaty, dokładnie 2 zmiany rodziny. Aktualny wynik after3 patrz dopisek końcowy.
- Obejrzano wybrane ujęcia i osiem narożników poprzednich iteracji, także niezależnie; nie stwierdzono tam blokującego mlecznego szkła ani przerwy dachu. **Nie zastępuje to oceny kandydata 3.**
- Audyt wejść końcowych testów względem właściwej bazy r3: 23/23 raw hashe fidelity zgodne, wszystkie wejścia niezmienione. Nie wolno automatycznie przypisywać r3 porażki fidelity z r2. To audyt hashy, nie pełny pytest.

## Czego jeszcze nie ukończono

**Nie ma dowodu końcowego budżetu kandydata 3.** W chwili polecenia nie wykonano jego normalnego importu, 236 renderów trasy, 118 dokładnych pomiarów Low ani 8 ujęć narożników. Katalogi `after`/`exact-after` i metryki w korzeniu `24h` dotyczą iteracji 1; `after2`/`exact-after2` oraz `iteration2` dotyczą iteracji 2. Nie przedstawiać ich jako wyników after3.

Nie wykonano pełnego końcowego GIS, physics/gate3 ani pełnego EditMode dla finalnego r3. Nie wykonano telefonu, APK, pomiaru czasu GPU/PSS ani niezależnej kalibracji fotograficznej.

Przygotowano sześć hipotez kamery dla zdjęcia 1911352299378570: raw GPS/compass oraz dopasowanie jednego obiektu przy VFOV 45/55/65. Surowa poza nie pasuje do położenia wiaty w zdjęciu. Wariant fit jest częściowo kołowy i nie dowodzi wymiarów. Metadane `photo-camera-evidence.json`; kamery `photo-cameras.json`; helper porównania `compare_photo_pose.py`. Tych dodatkowych renderów również nie uznaje się za wykonane.

## Wznowienie — wyłącznie na nowe polecenie

1. Odczytać końcowy dopisek, `git status`, najnowszy STATUS i logi. Nie uruchamiać duplikatu starego procesu; sprawdzać PID wraz z CommandLine, bo identyfikatory mogą być ponownie użyte. Przeczytać aktualne reguły repo.
2. Usunąć wyłącznie własny `24h/STOP_REQUESTED`, dopiero po nowym poleceniu wznowienia. Nie usuwać cudzych slotów, kolejek ani PHONE_RUN. Każdy heavy: właściciel bieżącej gałęzi; każdy Unity: zgodnie z poleceniem właściciela `gpt-furniture`. Używać managera z main, nie starej kopii worktree. Helpery czekają z PollSeconds 10.
3. Jeśli generator after3 i audyty zakończyły się pomyślnie, **nie trzeba ich powtarzać**: `pwsh artifacts/furniture-r3/24h/unity-step.ps1 -Step import -Phase candidate3`, następnie mały audyt metadanych `uv run --project tools/worldgen python artifacts/furniture-r3/24h/audit_shelter_policy.py after3`.
4. Uruchomić `pwsh artifacts/furniture-r3/24h/candidate2.ps1 -Phase after3`. Nazwa helpera jest historyczna; parametr zapisuje właściwe `after3`, `exact-after3`, `after3-side` i `iteration3`. Powstaje 236 + 118 + 8 kadrów. Sprawdzić wszystkie kamery, osobno mesh/instance/shadow draws; Low draws <= 0 i tris <= +2% z dokładnych liczników. Jeśli nie spełnia — poprawić i powtórzyć pętlę.
5. Cały batch arkuszy: `pwsh artifacts/furniture-r3/24h/heavy-step.ps1 -Step compare -Phase after3`. Obejrzeć wszystkie 40 arkuszy/236 par oraz narożniki, także z niezależną recenzją visual-QA. Obrazy oglądane <=960 px. Wykonać dodatkowe sbs-shelter Low/High i uczciwie przyjąć lub odrzucić hipotezy zdjęcia. Nie zmieniać cudzych dróg/budynków, aby dopasować kadr.
6. Dopiero kończąc rundę: `pwsh artifacts/furniture-r3/24h/final-python-tests.ps1` (sekwencyjny pełny GIS i physics/gate3 w heavy), pełny EditMode przez `unity-step.ps1 -Step editmode`. Zachować faktyczne wyniki i sprawdzić skutki uboczne fixture na manifest, zanim ponownie importuje się region. Helper testów nie uruchomi się przy brakującym budżecie lub aktywnych starych consumers.
7. Aktualizować ADR 0120, STATUS/WIP. Przygotować normalny polski REPORT dopiero z rzeczywistym zakresem i brakami, skopiować artifacts do main robocopy bez /MIR. Bez merge do main i push. Potem ewentualna r4 w tym samym worktree: nowa gałąź od r3 + `git merge main`, konflikty produktów wersja main + regeneracja, kod unia.

Kandydatura r4 jest tylko notatką w `24h/next-round-observations.md`: zakrzywione dwuramienne latarnie z Mapillary 1484379768878742. Przed implementacją ponownie sprawdzić aktualny main, dopasowanie instancji i zakres; nie ruszać `lamp_arc` Kwadratu Claude.

## Końcowy potwierdzony stan

W trakcie przygotowania przekazania oczekiwano wyłącznie na naturalny koniec już uruchomionego generatora i audytów. Wynik zostanie dopisany przed końcową odpowiedzią.
