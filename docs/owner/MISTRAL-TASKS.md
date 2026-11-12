# Zadania dla Mistral Vibe Code (chmura, tylko GitHub) — s12, 2026-11-12

Repo: `woogitsugames/kamion`. Każda sesja dostaje **jeden** prompt poniżej (skopiuj całość bloku). Mistral nie ma plików lokalnych, Unity, telefonów ani danych `Data/raw`, a pliki LFS widzi jako wskaźniki tekstowe (`version https://git-lfs...`). Dlatego zadania dotyczą tylko kodu .NET/Python, CI i dokumentacji.

**Wspólne zasady (są wklejone w każdy prompt):** pracuj na gałęzi `mistral/<nr>-<krótka-nazwa>` od `main`. Na końcu otwórz Pull Request do `main`. **Nigdy nie pushuj na `main` i nie scalaj PR** (scala tylko lider). Nie zmieniaj plików `Data/**/generated/**`, `*.glb`, `*_meta.json` ani `game/ProjectSettings/**`, `game/Packages/**`, `.gitattributes`, ani ustawień LFS. Nie zmyślaj liczb: każda wartość ma być zmierzona, zacytowana ze źródła albo oznaczona `UNVERIFIED`. Zakaz Google Maps, Street View, Earth i 3D Tiles. Raport po polsku w opisie PR.

---

## M1 — CI na zielono (job `gis` pada od rana)

```
Repo woogitsugames/kamion (symulator ciężarówki, Unity + Python + .NET). Pracuj na gałęzi mistral/1-ci-green od main, na końcu otwórz PR do main. NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes ani ustawień LFS.

Problem: workflow .github/workflows/ci.yml, job "gis" (uv run --project tools/worldgen pytest tests/gis -q, checkout z lfs: false) pada na każdym pushu do main. Przykłady z logu: tests/gis/test_hero_depot.py:127 'assert b"vers" == b"glTF"' (plik LFS jest wskaźnikiem, nie GLB), test_hero_bridge.py:47/101, test_hero_building.py:172, test_ec_chimneys.py:162 (porównania SHA plików binarnych), test_road_fidelity.py:51 "fidelity_qa.json is stale".

Zadanie:
1. Uruchom CI (workflow_dispatch na swojej gałęzi) i sklasyfikuj KAŻDĄ porażkę: (a) brak treści LFS w CI (wskaźnik zamiast pliku), (b) prawdziwa niespójność danych/kodu na main (np. nieaktualny fidelity_qa.json po scaleniach), (c) inne.
2. Dla (a): dodaj wspólny helper w testach (np. tests/gis/conftest.py), który wykrywa wskaźnik LFS (plik zaczyna się od "version https://git-lfs.github.com/spec/v1") i robi pytest.skip z jasnym powodem, oraz użyj go we wszystkich takich testach. Lokalnie (z prawdziwymi plikami LFS) testy mają działać bez zmian. NIE włączaj lfs: true w checkout (limit transferu LFS).
3. Dla (b): NIE poprawiaj danych (generuje je lider lokalnie). Wypisz w opisie PR listę z dokładnym komunikatem i plikiem. Test świeżości oznacz w CI jako xfail(strict=False) tylko wtedy, gdy przyczyną jest brak surowych danych w CI; jeśli to prawdziwa niespójność, zostaw porażkę i ją opisz.
4. Job "physics" (dotnet) sprawdź także i raportuj.
Wynik: PR z zielonym CI albo z jasno wypisanymi porażkami typu (b), plus tabela przyczyn w opisie PR, po polsku.
```

## M2 — audyt alokacji GC w pętli jazdy (tylko raport)

```
Repo woogitsugames/kamion (Unity 6 C#, symulator ciężarówki na Androida). Pracuj na gałęzi mistral/2-gc-audit od main, na końcu otwórz PR do main, który dodaje TYLKO plik docs/reports/AUDIT-GC-2026-11-12-mistral.md. NIE zmieniaj kodu C#. NIE pushuj na main, NIE scalaj.

Zasada projektu (CLAUDE.md): zero alokacji GC w pętli jazdy; fizyka w FixedUpdate, render interpolowany.
Zadanie: przejrzyj statycznie cały C# w game/Assets/_Project/** (bez Editor/ i Tests/) i znajdź możliwe alokacje na zarządzanej stercie w metodach wołanych co klatkę lub co krok fizyki: Update, LateUpdate, FixedUpdate, OnGUI, OnRenderObject, callbacki Input/UI wołane ciągle oraz metody, które one wywołują. Szukaj: new na typach referencyjnych, LINQ, string concat/format/interpolacja, boxing (np. enum w Dictionary bez comparera, params object[]), lambdy z przechwyceniem, foreach na nie-List/Array, GetComponent*/FindObject* w pętli, ToString, ToArray/ToList, Physics.*All bez NonAlloc, Camera.main w pętli, coroutine start co klatkę, string jako klucz w Animator/Shader property w pętli.
Dla każdego znaleziska: plik:linia, metoda i jak często jest wołana (ścieżka wywołań), szacowana wielkość alokacji (lub UNVERIFIED), pewność (pewne/prawdopodobne/wątpliwe) i proponowana poprawka (kod w bloku). Posortuj od najgorszych. Na końcu podsumowanie po polsku.
```

## M3 — spójność dokumentacji, ADR i rejestru licencji (raport + poprawki tylko w docs)

```
Repo woogitsugames/kamion. Pracuj na gałęzi mistral/3-docs-consistency od main, na końcu otwórz PR do main. Zmieniaj WYŁĄCZNIE pliki *.md w docs/ (oraz nowy raport). NIE pushuj na main, NIE scalaj.

Zadanie:
1. ADR (docs/adr/NNNN-*.md): sprawdź duplikaty numerów, luki w numeracji, ADR-y bez statusu, odwołania "ADR NNNN" w całym repo (md, py, cs, ps1) wskazujące nieistniejące ADR-y. Wygeneruj docs/adr/README.md jako indeks: numer, tytuł, status, data, link. Zrób to skryptem, który dołączysz jako tools/docs/adr_index.py (Python, bez zależności), żeby dało się go uruchomić ponownie.
2. Linki: znajdź zepsute linki względne w docs/**/*.md oraz w HANDOVER.md i CLAUDE.md. Popraw oczywiste literówki ścieżek, resztę wypisz.
3. Rejestr licencji docs/LICENSES.md: zestaw z zasobami śledzonymi w git (git ls-files: art-source/**, game/Assets/**/*.png|jpg|tga|wav|ogg|mp3|fbx|glb|ttf|otf poza _Generated) i wypisz zasoby, które nie mają wpisu ani nie wynikają jednoznacznie z kodu generatora. Sprawdź też duplikaty wpisów, BOM na początku pliku i brak spacji typu "CC BY-SA2.5". Poprawiaj tylko formatowanie i duplikaty; brakujące wpisy wypisz w raporcie (nie zgaduj licencji).
Raport docs/reports/AUDIT-DOCS-2026-11-12-mistral.md po polsku.
```

## M4 — weryfikacja źródeł danych referencyjnych fizyki (research + raport)

```
Repo woogitsugames/kamion (realistyczny symulator ciągnika siodłowego 4x2 + naczepa, zestaw do 40 t). Pracuj na gałęzi mistral/4-physics-sources od main, na końcu otwórz PR do main, który dodaje TYLKO docs/reports/AUDIT-PHYSICS-SOURCES-2026-11-12-mistral.md. NIE zmieniaj kodu ani danych. NIE pushuj na main, NIE scalaj.

Zadanie: przejdź docs/04_FIZYKA.md, docs/VEHICLE_REFERENCE_DATA.md (jeśli jest na main), docs/PHYSICS_VALIDATION.md oraz pliki JSON pojazdu i skrzyni w repo (wyszukaj masy, momenty, przełożenia, sztywności zawieszenia/kabiny, drogi hamowania, czasy 0–50/0–80 km/h, strategie AMT). Dla każdej liczby zapisz: wartość w repo, źródło podane w repo, czy źródło jest publiczne i potwierdza wartość (link + cytat do 15 słów lub numer strony/tabeli), status: POTWIERDZONE / ROZBIEŻNE (podaj wartość ze źródła) / BRAK ŹRÓDŁA / UNVERIFIED. Szukaj w źródłach otwartych: normy i regulaminy (EKG ONZ R13 hamulce, dyrektywa 96/53/WE masy i wymiary), publikacje SAE/TRB/UMTRI, karty techniczne producentów silników i skrzyń (bez kopiowania marek do gry), materiały uczelniane. Nie używaj forów jako jedynego źródła. Na końcu lista 10 najważniejszych rozbieżności dla realizmu jazdy (przyspieszanie, zmiany biegów, hamowanie, kołysanie kabiny). Po polsku.
```

## M5 — testy jednostkowe runnera fizyki (.NET, bez zmiany zachowania)

```
Repo woogitsugames/kamion. Projekt .NET: tools/physics-runner/PhysicsRunner.sln (xUnit + Runner scenariuszy; CI: dotnet test, dotnet run --project tools/physics-runner/Runner). Pracuj na gałęzi mistral/5-physics-tests od main, na końcu otwórz PR do main. NIE pushuj na main, NIE scalaj. NIE zmieniaj zachowania kodu produkcyjnego fizyki ani plików goldenów; zmieniasz tylko projekty testowe.

Zadanie: zwiększ pokrycie testami jednostkowymi modułów rdzenia fizyki współdzielonych z grą (silnik, skrzynia AMT, sprzęgło, hamulce pneumatyczne, retarder, opony, przegub naczepy — znajdź je w rozwiązaniu). Testy właściwości i przypadki brzegowe, np.: monotoniczność momentu w zakresie obrotów, brak zmiany biegu podczas otwartego sprzęgła, brak oscylacji zmian góra–dół (hunting) przy stałym pedale i stałym nachyleniu, ograniczenia obrotów (jałowy/odcięcie), symetria sił opony lewo/prawo, zachowanie przy dt bardzo małym i maksymalnym, brak NaN/Inf przy skrajnych wejściach, deterministyczność (ten sam wynik przy tych samych wejściach). Uruchom dotnet test w CI swojej gałęzi. Jeśli test ujawni błąd, NIE poprawiaj produkcji — oznacz test Skip z opisem i wypisz błąd w PR (plik:linia, wejście, oczekiwane vs otrzymane). Raport po polsku w opisie PR: liczba nowych testów, pokrycie przed/po (coverlet), znalezione błędy.
```
