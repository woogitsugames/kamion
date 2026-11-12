# Zadania dla Mistral Vibe Code — runda 2 (s13, 2026-11-12)

Repo: `woogitsugames/kamion`. **10 sesji, każda dostaje jeden blok poniżej (skopiuj całość).** Każda sesja startuje w czystym środowisku z dostępem do GitHub. Nie ma plików lokalnych, Unity, telefonów ani danych `Data/raw`. Pliki LFS są widoczne tylko jako wskaźniki tekstowe. Zadania dotyczą więc kodu .NET/Python, CI, testów, danych tekstowych i dokumentacji.

Runda 1 (PR #1–#5) jest w recenzji u lidera. Zadania M6, M7, M8 i M14 opierają się na jej raportach, które leżą na gałęziach PR-ów. Dlatego te sesje czytają raport z gałęzi `mistral/...`, a swoją gałąź zakładają od `main`.

**Wspólne zasady (wklejone w każdy prompt):** gałąź `mistral/<nr>-<nazwa>` od `main`, na końcu PR do `main`, raport po polsku w opisie PR. Nie pushujesz na `main` i nie scalasz (scala tylko lider). Nie zmieniasz `Data/**/generated/**`, `*.glb`, `*_meta.json`, `game/ProjectSettings/**`, `game/Packages/**`, `.gitattributes` ani ustawień LFS. Nie zmyślasz: każda liczba jest zmierzona, zacytowana ze źródła albo oznaczona `UNVERIFIED`. Zakaz Google Maps, Street View, Earth i 3D Tiles. Bez cudzych marek i logo.

---

## M6 — poprawki alokacji GC z audytu M2 (tylko pewne, bez zmiany zachowania)

```
Repo woogitsugames/kamion (Unity 6 C#, mobilny symulator ciężarówki). Pracuj na gałęzi mistral/6-gc-fixes od main, na końcu PR do main. NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS. Raport po polsku w opisie PR. Nie zmyślaj liczb.

Wejście: raport docs/reports/AUDIT-GC-2026-11-12-mistral.md z gałęzi mistral/2-gc-audit (git fetch origin mistral/2-gc-audit; git show origin/mistral/2-gc-audit:docs/reports/AUDIT-GC-2026-11-12-mistral.md).
Zadanie: wprowadź poprawki TYLKO dla znalezisk o pewności "pewne" w pętli jazdy (Update/LateUpdate/FixedUpdate i to, co wołają) w game/Assets/_Project/** (bez Editor/ i Tests/). Typowe: cache GetComponent/Camera.main w Awake, NonAlloc zamiast *All, StringBuilder/cache stringów dla HUD (aktualizuj tekst tylko przy zmianie wartości), Shader.PropertyToID/Animator.StringToHash w polach statycznych, usunięcie LINQ/lambd z przechwyceniem z pętli, comparer dla Dictionary z kluczem enum.
Twarde zasady: zachowanie gry bez zmian (te same wartości, ta sama kolejność); bez zmian w publicznych API używanych przez testy; nie ruszaj fizyki numerycznie. Nie masz Unity, więc kompilację sprawdzasz ręcznie: tylko API Unity 6, które już występują w repo, i `using` jak w sąsiednich plikach. Każda zmiana = osobny commit z odwołaniem do pozycji raportu.
Opis PR: tabela pozycja raportu → plik:linia → zmiana → ryzyko, plus lista pozycji świadomie pominiętych (z powodem).
```

## M7 — błędy fizyki wykryte testami M5 (naprawa w rdzeniu współdzielonym)

```
Repo woogitsugames/kamion. Projekt .NET tools/physics-runner/PhysicsRunner.sln (xUnit; rdzeń fizyki współdzielony z grą). Pracuj na gałęzi mistral/7-physics-bugfix od main, na końcu PR do main. NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS. Raport po polsku. Nie zmyślaj liczb.

Wejście: PR z gałęzi mistral/5-physics-tests (git fetch origin mistral/5-physics-tests) — testy oznaczone Skip z opisem błędu w kodzie produkcyjnym fizyki.
Zadanie: dla każdego takiego błędu: (1) potwierdź go minimalnym testem (wejście, oczekiwane vs otrzymane, dlaczego oczekiwane jest fizycznie poprawne, ze źródłem lub rachunkiem); (2) jeśli to prawdziwy błąd, napraw go najmniejszą zmianą w rdzeniu i zdejmij Skip; (3) uruchom pełne dotnet test oraz dotnet run --project tools/physics-runner/Runner (scenariusze walidacyjne) w CI swojej gałęzi. Jeśli naprawa zmienia wynik scenariusza/goldena — NIE aktualizuj goldenów; opisz w PR, który scenariusz i o ile się zmienił (lider zdecyduje). Jeśli „błąd” okazał się złym oczekiwaniem testu — popraw test i wyjaśnij.
Opis PR: tabela błąd → przyczyna (plik:linia) → poprawka → wpływ na scenariusze.
```

## M8 — propozycja korekt parametrów pojazdu z audytu źródeł M4 (bez zmiany danych gry)

```
Repo woogitsugames/kamion (realistyczny ciągnik siodłowy 4x2 + naczepa; decyzja właściciela D53: domyślny ładunek 24 t). Pracuj na gałęzi mistral/8-physics-params od main, na końcu PR do main, który dodaje TYLKO docs/proposals/PHYSICS-PARAMS-2026-11-12-mistral.md i ewentualnie tools/physics-runner/** (nowe scenariusze/testy porównawcze). NIE zmieniaj JSON-ów pojazdu ani kodu fizyki gry. NIE pushuj na main, NIE scalaj. Raport po polsku. Nie zmyślaj liczb.

Wejście: docs/reports/AUDIT-PHYSICS-SOURCES-2026-11-12-mistral.md z gałęzi mistral/4-physics-sources.
Zadanie: dla każdej pozycji ROZBIEŻNE i BRAK ŹRÓDŁA z top 10 raportu przygotuj propozycję: obecna wartość (plik:klucz), proponowana wartość albo zakres, źródło (link + cytat ≤ 15 słów lub tabela/strona), pewność, przewidywany wpływ na jazdę (przyspieszenie 0–50/0–80 km/h przy 24 t i 40 t, zmiany biegów, droga hamowania z 50/80 km/h, kołysanie kabiny). Jeśli to możliwe, policz wpływ w runnerze .NET: dodaj scenariusz porównawczy, który uruchamia model z obecnymi i proponowanymi parametrami (parametry jako dane testu, nie zmiana plików produkcyjnych), i wklej wyniki z CI. Priorytet: realizm wg źródeł, nie „lepszy feeling”.
```

## M9 — znaki drogowe pionowe: zgodność z polskim rozporządzeniem

```
Repo woogitsugames/kamion (Białystok 1:1; znaki generowane z danych/kodu w tools/worldgen i art-source/world/signs). Pracuj na gałęzi mistral/9-signs-pl od main, na końcu PR do main. NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS. Raport po polsku. Nie zmyślaj liczb. Zakaz Google Maps/Street View.

Zadanie: znajdź w repo definicje znaków pionowych (kody np. A-7, A-30, B-20, C-12, D-1, D-3, D-6, U-4a, E-…, T-…; wymiary, kolory, folie, wysokość montażu, odległość od krawędzi jezdni, czcionka tablic kierunkowych). Zestaw z polskimi przepisami: rozporządzenie w sprawie znaków i sygnałów drogowych oraz „szczegółowe warunki techniczne dla znaków i sygnałów drogowych” (Dz.U. 2019 poz. 2310/2311 wraz z załącznikami, ISAP) — wielkości znaków (mała/średnia/duża/wielka wg kategorii drogi), barwy, wysokość dolnej krawędzi, odległość od jezdni, kroje pisma tablic E. Wynik: (1) raport docs/reports/AUDIT-SIGNS-PL-2026-11-12-mistral.md: tabela znak → wartość w repo (plik:linia) → wartość z przepisu (paragraf/załącznik, strona) → status; (2) test pytest w tests/gis/ sprawdzający dane znaków wobec tabeli wymagań (jeśli test potrzebuje plików generated/LFS, ma się pomijać przez pytest.skip przy wskaźniku LFS — helper z tests/gis/conftest.py jeśli istnieje); (3) poprawki tylko w danych źródłowych znaków (nie w generated), gdy rozbieżność jest jednoznaczna.
```

## M10 — oznakowanie poziome i geometria pasów: zgodność z warunkami technicznymi

```
Repo woogitsugames/kamion (Białystok 1:1; drogi generowane w tools/worldgen/roads). Pracuj na gałęzi mistral/10-markings-pl od main, na końcu PR do main. NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS. Raport po polsku. Nie zmyślaj liczb. Zakaz Google Maps/Street View.

Zadanie: znajdź w generatorze stałe i reguły: szerokości pasów wg klasy drogi, szerokości linii P-1/P-2/P-3/P-4 itd., długości kresek i przerw, linie krawędziowe, strzałki P-8, przejścia P-10, linie zatrzymania P-12/P-13/P-14, promienie łuków na skrzyżowaniach i rondach, szerokość opasek, wysokość krawężników, pochylenia poprzeczne. Zestaw z przepisami: warunki techniczne dla dróg publicznych (rozporządzenie z 2015 r., Dz.U. 2016 poz. 124 z późn. zm. / aktualny tekst w ISAP) oraz szczegółowe warunki techniczne oznakowania poziomego (Dz.U. 2019 poz. 2311, zał. nr 2). Wynik: raport docs/reports/AUDIT-MARKINGS-PL-2026-11-12-mistral.md (stała w repo plik:linia → wartość z przepisu z paragrafem → status), testy jednostkowe czystych funkcji generatora (bez Data/raw) pilnujące wartości przepisowych oraz poprawki stałych tylko przy jednoznacznej rozbieżności (każda osobnym commitem z cytatem przepisu). Nie regeneruj świata — zrobi to lider.
```

## M11 — testy jednostkowe narzędzi audio (sygnały syntetyczne)

```
Repo woogitsugames/kamion. Narzędzia audio Python: tools/audio/ (m.in. el_prepare.py, el_verify.py, el_analyze.py, el_sweepcut.py, el_regen01.py, render_all.py; uruchamiane `cd tools/audio; uv run python ...`). Pracuj na gałęzi mistral/11-audio-tests od main, na końcu PR do main. NIE pushuj na main, NIE scalaj. Nie zmieniaj plików WAV/OGG ani LFS. Raport po polsku.

Zadanie: dodaj testy pytest (tools/audio/tests/) dla funkcji analizy i przetwarzania na sygnałach syntetycznych generowanych w teście (bez plików z repo): detekcja f0/rzędów zapłonu → RPM dla znanego sygnału harmonicznego (np. 6-cylindrowy 4-suwowy: rząd 3 → f = RPM/60*3), stabilność przy szumie, wykrywanie klipów, punkty zapętlenia (ciągłość fazy/poziomu na złączu), przestrajanie (resampling) zachowujące długość/wysokość zgodnie z teorią, cięcie sweepu na siatkę RPM, deterministyczność. Uruchom w CI swojej gałęzi (dodaj krok do .github/workflows/ci.yml tylko jeśli nie spowalnia >2 min; inaczej osobny job). Błędy znalezione testami: NIE poprawiaj produkcji — Skip z opisem i lista w PR (plik:linia, wejście, oczekiwane vs otrzymane).
```

## M12 — testy jednostkowe czystych funkcji generatora świata

```
Repo woogitsugames/kamion. Generator świata Python: tools/worldgen/** (uv run --project tools/worldgen pytest tests/gis). Pracuj na gałęzi mistral/12-worldgen-unit od main, na końcu PR do main. NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, .gitattributes, LFS. Raport po polsku.

Zadanie: większość testów tests/gis wymaga danych Data/raw lub plików LFS (w CI są pomijane). Dodaj szybkie testy jednostkowe dla funkcji czystych, które da się wywołać na małych danych syntetycznych: transformacje CRS (EPSG:2180 ↔ lokalne X=wschód, Z=północ, 1 unit = 1 m), offsetowanie polilinii jezdni i łuki, triangulacja/ekstruzja, łączenie odcinków na skrzyżowaniach, generowanie krawężników/barier wzdłuż krzywej, hash/seed deterministyczny rozmieszczenia obiektów, chunkowanie. Właściwości: brak samoprzecięć dla prostych przypadków, zachowanie długości/szerokości w tolerancji, symetria, deterministyczność, brak NaN. Testy mają przechodzić w CI bez Data/raw (dodaj marker, np. @pytest.mark.unit, i krok CI uruchamiający je). Błędy produkcji: Skip z opisem + lista w PR, nie poprawiaj.
```

## M13 — jakość skryptów: ruff + PSScriptAnalyzer w CI (raportowo)

```
Repo woogitsugames/kamion. Skrypty: scripts/*.ps1 (PowerShell 7, Windows), tools/**/*.py (uv). Pracuj na gałęzi mistral/13-lint od main, na końcu PR do main. NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**, *.glb, *_meta.json, game/**, .gitattributes, LFS. Raport po polsku.

Zadanie: (1) dodaj do CI job „lint” NIEBLOKUJĄCY (continue-on-error: true): ruff check dla tools/ i tests/ (konfiguracja w pyproject/ruff.toml z rozsądnym zestawem reguł: błędy, nieużywane importy, niezdefiniowane nazwy, porównania z None, bare except) oraz PSScriptAnalyzer dla scripts/*.ps1 (runner windows-latest lub pwsh na ubuntu). (2) Napraw tylko oczywiste i bezpieczne znaleziska: nieużywane importy/zmienne, niezdefiniowane nazwy (prawdziwe błędy!), porównania == None, w PowerShell: nieużywane zmienne, $null po lewej w porównaniach. Każda poprawka bez zmiany zachowania. (3) W opisie PR: liczba znalezisk przed/po per reguła, lista prawdziwych błędów (np. niezdefiniowana nazwa na ścieżce, która się wykonuje) z plik:linia — te najważniejsze.
```

## M14 — rejestr licencji: uzupełnienie brakujących wpisów z audytu M3

```
Repo woogitsugames/kamion. Rejestr docs/LICENSES.md (każdy zasób w repo musi mieć wpis; zasada projektu). Pracuj na gałęzi mistral/14-licenses od main, na końcu PR do main, który zmienia TYLKO docs/LICENSES.md i dodaje raport docs/reports/AUDIT-LICENSES-2026-11-12-mistral.md. NIE pushuj na main, NIE scalaj. Raport po polsku. Nie zgaduj licencji.

Wejście: docs/reports/AUDIT-DOCS-2026-11-12-mistral.md z gałęzi mistral/3-docs-consistency (lista zasobów bez wpisu).
Zadanie: dla każdego zasobu bez wpisu ustal pochodzenie: (a) z historii git (git log --follow, komunikaty commitów, ADR-y, pliki *_SOURCE*, manifesty w art-source/**, pliki .json/.txt obok zasobu), (b) ze strony źródła, jeśli nazwa wskazuje znane repozytorium CC0/CC-BY (Poly Haven, ambientCG, Wikimedia Commons, Freesound, OpenGameArt) — link do konkretnej strony zasobu + licencja ze strony. Jeśli zasób jest wygenerowany przez kod repo (generator), wpisz to z odwołaniem do skryptu. Jeśli nie da się ustalić — NIE dopisuj licencji, tylko wpisz do raportu jako „DO USTALENIA PRZEZ WŁAŚCICIELA” z tym, co wiadomo. Zachowaj format istniejących wpisów, bez BOM, bez duplikatów.
```

## M15 — pokrycie scenariuszy walidacji fizyki z docs/04 §6

```
Repo woogitsugames/kamion. Fizyka: docs/04_FIZYKA.md (§6 scenariusze walidacyjne), docs/PHYSICS_VALIDATION.md (jeśli jest), runner .NET tools/physics-runner (Runner + xUnit, goldeny). Pracuj na gałęzi mistral/15-physics-scenarios od main, na końcu PR do main. NIE pushuj na main, NIE scalaj. NIE zmieniaj istniejących goldenów ani kodu produkcyjnego fizyki. Raport po polsku. Nie zmyślaj liczb.

Zadanie: (1) zrób macierz: każdy scenariusz z docs/04 §6 (i wymagania z tolerancjami) → czy runner go ma (nazwa scenariusza, plik), czy ma tolerancje, czy ma golden, czy CI go uruchamia. (2) Dopisz brakujące scenariusze jako NOWE scenariusze/testy (np. ruszanie pod górę 24 t i 40 t, hamowanie awaryjne z 80 km/h na suchej/mokrej, zjazd z retarderem bez przegrzania hamulców, łuk 50 km/h z naczepą — kąt przegubu i przechył, zmiana pasa, slalom, stała prędkość na wzniesieniu bez „huntingu” biegów) z tolerancjami zaczerpniętymi z docs (albo oznaczonymi UNVERIFIED, jeśli docs ich nie podają). (3) Uruchom w CI swojej gałęzi; nowe scenariusze, które nie przechodzą, oznacz jako oczekiwane porażki z opisem (nie stroisz fizyki). Opis PR: macierz pokrycia przed/po + lista niespełnionych wymagań z liczbami.
```
