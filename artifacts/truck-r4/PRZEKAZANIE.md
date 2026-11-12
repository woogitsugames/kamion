# Przekazanie — GPT truck, sesja 6

Stan zapisany 12 listopada 2026 około 16:24 CET. Praca wstrzymana na polecenie właściciela z powodu limitu tygodniowego. Nie rozpoczynać kolejnych rund bez wznowienia przez właściciela. Nie zabijano procesów.

## Repozytorium i zapis

- Repo główne: `C:\Users\matma\Documents\Claude\kamion`.
- Worktree: `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-truck`.
- Bieżąca gałąź: `gpt-truck-r4`. Ostatni commit kodu kandydata: `ff37848cb79effe800af405c10810c1ccf91ba53`; kolejne commity mogą dotyczyć przekazania i samoczynnego zakończenia przygotowania.
- R4 zaczęła się od r3 i merge main `f8b85fa231bd34935d8a2f5a6dc30ea5879e9be1`, merge `07bbd7c1db38dca8d3ed002261eec7bb3b696619`. Nie scalano do main i nie pushowano.
- Wszystkie źródła są zapisane w commitach WIP. Artefakty, cache i logi pozostają na dysku w `artifacts/truck-r1`…`truck-r4`. Dużych kopii eksportów i logów nie dodawać do Git.

## Uruchomione zadanie — najpierw sprawdź to

W chwili zapisu nadal działał **istniejący** `artifacts/truck-r4/prepare-baseline.ps1`: generator świata pod slotem heavy. Materiały ukończył wcześniej w 526 s, bez `fallback=True`.

- Proces nadrzędny pwsh PID **54020**, uruchomiony 13:34:24; jego potomkowie przy odczycie: uv **78320**, python **40584**, python **79792**. Stan i czasy utworzenia zapisano w `artifacts/truck-r4/STOP-PROCESS-STATE.json`. PID może później zostać użyty ponownie, więc sprawdzaj także ścieżkę i czas procesu.
- Sesja narzędzia w tym czacie: **69474**. Nie jest przenośna między kontami; w nowej sesji użyj procesów systemowych i logów.
- Konsola: `artifacts/truck-r4/prepare-retry-console.log`.
- Generator świata: `artifacts/truck-r4/baseline-world.log` (wyjście może być buforowane).
- Skrypt **sam zwalnia heavy w finally**, zapisuje WIP/STATUS i następnie może uzupełnić brakującą warstwę materiału oraz wykonać import Unity pod osobnym slotem. Po tym kończy działanie. Nie uruchamia baseline-captures ani kandydata koła.
- Nie zwalniaj ręcznie slotu działającego generatora. Nie uruchamiaj drugiej kopii przygotowania ani Blendera z tym samym Owner.

Sprawdzenie bez ingerencji:

```powershell
Get-Process -Id 54020,78320,40584,79792 -ErrorAction SilentlyContinue
Get-Content artifacts/truck-r4/prepare-retry-console.log -Tail 25
Get-Content artifacts/truck-r4/STATUS.md -Tail 12
git status --short
```

Przekazanie powstaje, gdy zadanie jeszcze działa. Końcowy wynik procesu i późniejsze commity odczytaj z aktualnego STATUS/logów w worktree, nie z samej kopii tego dokumentu. Nie restartuj zadania wyłącznie dlatego, że log chwilowo się nie zmienia.

## Ukończone rundy

**R1:** poprawka mgły premultiplied w `FragFast`, lokalna kompresja luminancji DRL; clipping lewej lampy High-overcast 1214→0 pikseli RGB≥254. EditMode 266/266, APK poprawny. Lakier, dach i mleczność szyby pozostają otwarte. Raport: `main/artifacts/truck-r1/REPORT.md`.

**R2:** czytelniejsza kratka stopnia przez mniejszą retencję proceduralnego brudu na górnych powierzchniach metalu. Odrzucone zacieki/plastik/krótszy rozbryzg wycofane. EditMode 300/300, APK poprawny. GIS 575 passed / 1 failed / 1 xfailed; ograniczenie porównania po odtworzeniu starego manifestu opisuje `artifacts/truck-r2/GIS-VALIDATION-CORRECTION.md`. Raport: `main/artifacts/truck-r2/REPORT.md`.

**R3:** zamknięte osie Low ciągnika i naczepy; ciągły atlas opon/rantów bez mostkowania wysp; pełniejsza przednia tarcza Low. Końcowe LOD2: ciągnik 17 690/17 900, naczepa 7 849/8 000. UV-wide przedniego koła Low 47→0. Wszystkie 96 wierszy kamer bez wzrostu draws i trójkątów, instancje osobno. EditMode 326/326. GIS 617 passed / 1 failed / 1 xfailed: tylko nieaktualny fidelity względem overrides.yaml i roads/meshing.py; deterministyczność świata przeszła na świeżych wejściach. APK poprawny, bez telefonu. Ostatni commit r3 `43b39c39`, raport `13ffa2b2`.

R3 przekazana robocopy: 804 pliki, 1 890 363 713 bajtów; REPORT SHA256 `F7298DE38E86368B52F905E0F3B03A3D0E2BF0EDE7C3CBD9AEED5309C4AFEC5E`. Lider scalił ją później sam. Recenzja `docs/reports/visual/REVIEW-2026-11-12-s12-0130-truck-r3.md` potwierdza poprawę i pozostawia P1 zabawkowej felgi.

## R4 — dokładnie co jest gotowe, a co nie

**Nie wygenerowano ani nie zainstalowano nowego wariantu FBX R4. Nie ma jeszcze świeżego baseline ani akceptacji wyglądu R4.** Aktualne kanoniczne FBX pozostają wariantem r3.

Przygotowano wariant źródłowy pod flagą `--regular-front-wheels`, **domyślnie False do walidacji**:

- `tools/blender/truck/exterior/wheel_disc.py`: regularna tarcza z dziesięcioma otworami, zamkniętym tyłem i ścianami. Low 8 segmentów otworu = 680 tris; High 16 = 1000. Cztery warianty mają prawidłową topologię, dodatnią objętość i 91 próbek otworów bez pokrycia.
- `wheel_disc_blender.py`: wspólny układ 14 chartów, rekonstrukcja UV Low z rzeczywistego atlasu High. Źródłowe parametry odtwarzane z przepisu, z kontrolą indeksów/pozycji wierzchołków i kluczy trójkątów. Nie dokłada kanałów runtime. Syntetyczne 42 transformacje, także odbicie i skalowanie niejednorodne, przeszły; zniekształcony chart został odrzucony.
- `chassis.py`: regularna przednia tarcza, bardziej płaski stalowy dekiel o roboczej wysokości 40 mm zamiast 95 mm; metadane profilu przedniej misy.
- `a6_export.py`: zachowanie UV, ochrona regularnej tarczy przed COLLAPSE, przednia misa i dziesięć rzeczywistych nakrętek na koło zachowane w Low, próba przesunięcia budżetu z profili tylnych obręczy. Limit 17 900 nie został podniesiony. Budżet całego wariantu nadal NIEZMIERZONY w Blenderze.

Pliki kontrolne: `art-source/truck/exterior/qa/check_disc_proxy_0115.py`, `check_disc_blender_0115.py`, `estimate_wheel_profile_0115.py`. Pierwszy działa bez Blendera i został uruchomiony. **Native smoke, packer, bake i FBX nowego wariantu jeszcze nie zostały uruchomione.** Diagram `disc-solid-prototype.jpg` jest wykresem topologii, nie renderem gry. Estymaty profili są oznaczone WORKING_VALUE.

Dodatkowo gotowe, na dalszą diagnozę: `prepare_glass_0115.py` i `artifacts/truck-r4/glass-controls.ps1` obejmują pełny shader i `FragFast`, z odczytem rzeczywistych materiałów po renderze. Kompilacja C# i istniejący fixture GlassFastTierTests przeszły 3/3. Kontrole optyczne nie były wykonywane. Wykadrowano referencje bez oznaczeń, z licencjami i SHA.

## Najbliższe kroki po wznowieniu

1. Najpierw ustal naturalny wynik przygotowania 54020. Nie dubluj żywego procesu. Przy błędzie przeczytaj konkretny log; `-SkipMaterials`/`-SkipGenerators` stosuj wyłącznie po potwierdzeniu udanych i nadal świeżych etapów.
2. Po sukcesie przygotowania uruchom `pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/truck-r4/baseline-captures.ps1`. Zapisze aktualne prefaby, fixture, 28 całych kadrów, wszystkie kamery i 12 zbliżeń. Obejrzyj je.
3. Następnie `pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/truck-r4/regenerate-exterior.ps1 -Stage regular-front-v1`. Wrapper wymaga kompletnego baseline, robi backup, bierze heavy, pilnuje źródeł i uruchamia preflight + pełny bake + natywny validator, dwa wątki Blendera. Na Failed nie instalować częściowych plików.
4. Jeśli problem dotyczy tylko budżetu Low, cache nowego pełnego bake może pozwolić na LOD2-only. Wzorzec z r3 trzeba dostosować do r4; **nie uruchamiać go bez zmian**, bo ma ścieżki r3. Odtwórz `C.REGULAR_FRONT_WHEELS` z `manifest.regular_front_wheels`, a mapy i LOD0/1 zachowaj bajtowo.
5. Dopiero po walidatorze: installer pod Unity-slot, test `TruckWheelLodGeometryTests`, te same Low/High clear/overcast, zdjęcie|render ≤960 px i niezależny krytyk. Sprawdź prześwit, regularność otworów, nakrętki, ciemniejszy płaski dekiel i możliwe straty profilu z tyłu. Zobacz `INTEGRATION-PLAN.md`.
6. Po akceptacji włącz domyślnie wariant w C i CLI eksportera, żeby zwykła regeneracja odtwarzała dostarczony model. Potwierdź konfigurację i aktualne SHA. Nie zostawiaj jako ukończonego wariantu wymagającego nieudokumentowanej flagi.
7. Wszystkie kamery i instancje osobno, pełny EditMode, APK bez instalowania, pełny GIS dopiero na końcu rundy pod heavy. Raportuj rzeczywiste błędy, także poza truck. Dane świata zachowaj świeże do GIS.
8. Zapisz ADR 0115 r4, normalny polski REPORT, robocopy artefaktów do main. Nie scalaj do main i nie pushuj. Następną rundę rozpoczynaj dopiero po wznowieniu przez właściciela.

## Ograniczenia i ważne pułapki

- Tylko truck: zewnętrze TRAKT i naczepa. Nie edytuj wnętrza cab, dróg, budynków ani plików Claude.
- Zawsze centralny skrypt `C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1`. Unity Owner `gpt-truck`; heavy Owner bieżącej gałęzi (`gpt-truck-r4`). Bez Priority, bez usuwania cudzych blokad i PHONE_RUN. Pełny GIS tylko na końcu rundy. Biblioteki numeryczne jeden wątek, Blender `--threads 2`.
- Dwa wcześniejsze Acquire skończyły się błędem udostępniania pliku biletu. Obecny wrapper używa PollSeconds 60 i najwyżej trzech ponowień wyłącznie po takim terminalnym błędzie. Nie zmieniano centralnej infrastruktury.
- Nie cofaj world_manifest ani innych wygenerowanych danych przed konsumentami i końcowym GIS. Po generatorze mogą być brudne pliki innych dziedzin; zachowaj patch/surowe pliki i dopiero na końcu przywróć dokładną listę, bez commitowania ich.
- P1 naczepy, kanciastość opony, lakier/dach, mleczność szyby i pełny brud pozostają otwarte. Żaden częściowy test nie oznacza PASS całej grafiki.
- Bieżący feedback lidera wspomina ograniczenie VQA High: zapis R8 przed post. Pomiary obrazu nie są fizycznym HDR ani pomiarem GPU telefonu.
- Nie używano telefonów/adb. Nie używano Google Maps/Street View/Earth. Referencje wyłącznie z dostarczonych zdjęć i repozytoryjnych metadanych, bez przenoszenia logo do gry.

## Ostatnia aktualizacja

Aktualizacja przy zamykaniu sesji: generator świata zakończył się poprawnie, zwolnił heavy i zapisał commit 78a2d19f5. Istniejący skrypt czeka na slot Unity przed importem; nie został przerwany. Wygenerowane pliki innych dziedzin pozostawiono na dysku bez commitowania; ich diff zapisano w generated-at-stop.patch. Nie odtwarzać ich podczas trwającego przygotowania.
