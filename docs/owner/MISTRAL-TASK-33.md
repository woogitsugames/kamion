# Mistral — jedno duże zadanie M33 (s16, 2026-11-12)

Jedna sesja, praca na kilka godzin. Wklej cały blok.

Dlaczego tak: w rundach 2–4 krótkie zadania wracały z błędami, których dało się uniknąć — testy, które przechodziły też na starym kodzie (#16), wnioski niezgodne z cytowanym źródłem (#17), gałąź na starym main przywracająca usunięty kod (#18), kod C# Unity, którego nie dało się skompilować (#19). To zadanie jest w całości uruchamialne w Twoim środowisku (Python + .NET 8, bez Unity) i ma obowiązkową weryfikację przed oddaniem.

```
Repo woogitsugames/kamion (realistyczny mobilny symulator ciężarówki; fizyka pojazdu w C#, testowana BEZ Unity przez tools/physics-runner na .NET 8). Pracuj na gałęzi mistral/33-physics-validation-coverage od NAJNOWSZEGO origin/main. To jedno duże zadanie na kilka godzin — staranność ważniejsza niż tempo.

CEL: pakiet walidacyjny fizyki (docs/04_*.md §6, 15 punktów) ma być pokryty scenariuszami runnera z wartościami oczekiwanymi ze źródłem — i masz to udowodnić uruchomieniem.

NAJPIERW PRZECZYTAJ: CLAUDE.md, docs/04_*.md (całość, zwłaszcza §5 i §6), docs/VEHICLE_REFERENCE_DATA.md, docs/reports/AUDIT-PHYSICS-SOURCES-2026-11-12-mistral.md, docs/reports/PHYSICS-SOURCES-2-2026-11-12-mistral.md, docs/reports/REVIEW-2026-11-12-s15-mistral-r3.md (co poszło źle w #16 i #17 — nie powtarzaj), tools/physics-runner/Sim/{Scenario,ScenarioRunner,Metrics,Suites}.cs, tests/physics/scenarios/*.json (75 plików), tests/physics/scenarios_expected_fail/, tests/physics/test_scenario_strictness.py, game/Assets/_Project/Vehicle/Physics/Definitions/Data/*.json.

ŚRODOWISKO: zainstaluj .NET 8 SDK, jeśli go nie ma. Komendy:
- dotnet test tools/physics-runner/PhysicsRunner.sln -c Release
- dotnet run -c Release --project tools/physics-runner/Runner   (pełny pakiet; zapisz wynik: liczba scenariuszy, checków, porażek)
- testy Python w tests/physics (uv / pytest — sprawdź jak są uruchamiane w repo)
Uruchom je NA STARCIE (baseline) i zapisz liczby.

ZADANIE:
1. Macierz pokrycia: dla każdego z 15 punktów §6 — które scenariusze go pokrywają, jakie checki (metryka, próg, tolerancja), skąd próg (źródło / WORKING_VALUE / brak). Zapisz jako docs/reports/PHYSICS-COVERAGE-2026-11-13-mistral.md.
2. Luki: punkty bez scenariusza lub z checkiem, który niczego nie sprawdza (np. próg tak szeroki, że przejdzie każdy wynik; metryka niezależna od testowanej cechy). Dla każdej luki dodaj scenariusz(e) JSON + checki w formacie istniejących scenariuszy; jeśli runner nie ma potrzebnej metryki — dodaj ją w tools/physics-runner/Sim/Metrics.cs (z testem jednostkowym w tools/physics-runner/Tests).
3. Wartości oczekiwane: każda ze źródłem pierwotnym (regulamin EKG ONZ R13/R13-H na EUR-Lex z numerem punktu, przepisy PL na isap.sejm.gov.pl ze stroną, Gillespie/Pacejka/Bosch z rozdziałem/stroną, karta producenta klasy pojazdu); cytat ≤ 25 słów + link. Brak źródła = WORKING_VALUE z uzasadnieniem fizycznym (rachunek w raporcie). NIE wyciągaj wniosków, których cytat nie zawiera (to był błąd #17).
4. Jeśli nowy check PADA, bo fizyka daje zły wynik — NIE poprawiaj kodu fizyki w game/Assets/**. Przenieś scenariusz do tests/physics/scenarios_expected_fail/ z expectedFailMetrics i opisz w raporcie (wartość zmierzona vs oczekiwana, podejrzana przyczyna z plikiem:linią). Lider i właściciel decydują o zmianie fizyki.
5. Punkty §6, których nie da się sprawdzić bez Unity/telefonu (np. 13 floating origin, 12 obciążenie CPU, feel) — wypisz wprost jako „poza runnerem” z propozycją testu PlayMode (tylko opis, bez kodu Unity).

NIE ZMIENIAJ: game/Assets/** (żadnego kodu Unity ani fizyki), Data/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS, .asmdef. Zakaz Google Maps/Street View/Earth/3D Tiles. Nie zmyślaj liczb.

WERYFIKACJA PRZED ODDANIEM (obowiązkowa, opisz każdy punkt w PR z dowodem):
A. Niezależny przegląd: jeśli możesz uruchomić subagentów albo drugą sesję/model — zleć im OSOBNO (bez Twoich wniosków, tylko pliki i źródła): (a) sprawdzenie każdego cytatu i liczby w raporcie z otwartym źródłem, (b) przegląd kodu i scenariuszy pod kątem checków, które niczego nie sprawdzają, (c) próbę „złamania” Twoich testów. Popraw wszystko, co znajdą, i wklej ich ustalenia do PR. Jeśli nie możesz uruchomić subagentów — zrób trzy osobne przebiegi (a), (b), (c) sam, każdy od zera, z listą sprawdzonych pozycji.
B. Test mutacyjny: dla KAŻDEGO nowego checku pokaż, że pada, gdy zepsujesz testowaną cechę (np. tymczasowo wyłącz ABS, zmień masę, μ, retarder w JSON scenariusza/definicji w lokalnej kopii — NIE commituj mutacji). Tabela: check → mutacja → wynik (musi być FAIL). Check, który nie pada na mutacji, usuń albo popraw.
C. Pełne uruchomienie po zmianach: dotnet test (wszystkie zielone), Runner (liczby przed/po: scenariusze, checki, porażki = 0 poza expected_fail), testy Python w tests/physics. Wklej końcowe liczby.
D. Tuż przed PR: git fetch && git rebase origin/main (albo merge), ponów C. Sprawdź git diff --stat origin/main — tylko dozwolone ścieżki; żadnego przywrócenia usuniętego kodu.
E. Lista kontrolna w opisie PR: A–D z dowodami (liczby, ścieżki, fragmenty logów).

ODDANIE: git push gałęzi, jeden PR do main (nie draft), raport po polsku w opisie PR (macierz pokrycia skrótem, nowe scenariusze, expected_fail z przyczynami, lista A–E). NIE pushuj na main, NIE scalaj. Po utworzeniu PR NIE śledź go — nie czekaj na CI, recenzję ani komentarze. Napisz „M33 gotowe, PR #<numer>” i zakończ sesję.
```
