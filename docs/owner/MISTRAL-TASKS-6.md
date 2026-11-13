# Zadania dla Mistral — runda 6 (s16, 2026-11-13): 5 długich sesji

Repo `woogitsugames/kamion`. **5 sesji, każda dostaje jeden blok (skopiuj całość).** Model: Mistral Large 4. Każde zadanie jest pomyślane na wiele godzin pracy: zakres główny + lista rozszerzeń, którą sesja robi po kolei, aż skończy jej się czas. Wzór jakości: M33 (PR #32) — weryfikacja A–E przed oddaniem.

Środowisko jak w rundach 2–5: GitHub, Python (uv), .NET 8 — bez Unity, telefonów i `Data/raw`; LFS widoczne tylko jako wskaźniki. **CI na main ma teraz 2 znane czerwone testy** (`test_every_gate3_sign_is_placed`, `test_report_not_stale`) — czekają na regenerację świata przez lidera; nie naprawiaj ich i nie traktuj jako swojej regresji.

**Wspólne zasady (są w każdym prompcie):** patrz bloki.

---

## M34 — fizyka: odporność numeryczna, determinizm, soak, fuzz

```
Repo woogitsugames/kamion (fizyka ciężarówki w C#, testowana BEZ Unity przez tools/physics-runner na .NET 8). Gałąź mistral/34-physics-robustness od NAJNOWSZEGO origin/main. Zadanie na wiele godzin — rzetelność ważniejsza niż tempo. Możesz i powinieneś używać subagentów (jeśli je masz) do równoległej pracy i do niezależnej weryfikacji.

CEL: udowodnić liczbami, że symulacja jest stabilna numerycznie i deterministyczna (docs/04_*.md §6 pkt 12 i 14), i wyłapać przypadki, w których nie jest.
PRZECZYTAJ: CLAUDE.md, docs/04_*.md, docs/reports/PHYSICS-COVERAGE-2026-11-13-mistral.md (M33), tools/physics-runner/Sim/*.cs (zwłaszcza DtSweep/SubstepSweep, Metrics, ScenarioRunner), tests/physics/scenarios*/, game/Assets/_Project/Vehicle/Physics/** (tylko do czytania).
ZAKRES GŁÓWNY:
1. Soak: tryb runnera „soak” — 30 min czasu symulacji (jazda w pętli po łuku i prostej, zmiany gazu/hamulca/biegu wg skryptu), metryki: dryf energii (kinetyczna+potencjalna vs praca sił), dryf pozycji przy postoju, maks. błąd więzów przegubu/siodła, NaN/Inf, oscylacje (widmo prędkości kątowej kabiny). Progi jako WORKING_VALUE z rachunkiem.
2. Determinizm: ten sam scenariusz 2× → identyczne wyniki bit w bit (lub udokumentowana przyczyna różnic); ten sam scenariusz przy fixedDeltaTime 1/50, 1/60, 1/100, 1/120 i substepach → różnice metryk w tolerancjach (tabela).
3. Fuzz (property-based): losowe, ale powtarzalne (seed) sekwencje wejść kierowcy (kierownica, gaz, hamulec, biegi, retarder, hamulec postojowy, gyro/dotyk z TouchDriver) na różnych nawierzchniach i nachyleniach; niezmienniki: brak NaN, brak „teleportacji” (skok pozycji > v·dt·k), siły opon w granicach μ·Fz z zapasem, kąt przegubu w ogranicznikach, brak ujemnego ciśnienia powietrza. Każde złamanie → minimalny scenariusz odtwarzający (shrinking) zapisany w tests/physics/scenarios_expected_fail/ z opisem.
4. NIE poprawiaj kodu fizyki w game/Assets/** — tylko raport z plikiem:linią podejrzanej przyczyny (decyduje lider i właściciel).
ROZSZERZENIA (po kolei, ile zdążysz): (a) profil czasu CPU kroku fizyki w runnerze (µs/krok, p50/p99) dla 1/2/4 substepów; (b) wrażliwość na środek masy ładunku (§6 pkt 7) siatką 5×5 położeń; (c) skrajne masy (pusty 15 t … 44 t) × nawierzchnie; (d) krawężniki/koleiny/progi z fuzzem wysokości i prędkości (§6 pkt 11).
NIE ZMIENIAJ: game/Assets/**, Data/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS, .asmdef. Nie zmyślaj liczb; źródła pierwotne z cytatem ≤ 25 słów i stroną, inaczej WORKING_VALUE z rachunkiem.
WERYFIKACJA PRZED ODDANIEM (obowiązkowa, z dowodami w PR): A. niezależny przegląd — subagenci (bez Twoich wniosków) sprawdzają: (a) liczby i źródła, (b) czy każdy check coś sprawdza, (c) próbują złamać testy; bez subagentów: 3 osobne przebiegi od zera. B. test mutacyjny każdego nowego checku (mutacja lokalna, niecommitowana → musi być FAIL; tabela). C. pełne uruchomienie: dotnet test tools/physics-runner/PhysicsRunner.sln -c Release, dotnet run -c Release --project tools/physics-runner/Runner, testy tests/physics — liczby przed/po. D. tuż przed PR: git fetch && git rebase origin/main, ponów C, git diff --stat origin/main tylko dozwolone ścieżki. E. lista A–D w opisie PR.
CIĄGŁY ZAPIS: commit + push gałęzi co ok. godzinę (sesja może zostać przerwana). Raport docs/reports/PHYSICS-ROBUSTNESS-2026-11-13-mistral.md.
ODDANIE: jeden PR do main (nie draft), raport po polsku w opisie. NIE pushuj na main, NIE scalaj. Po utworzeniu PR NIE śledź go (CI, recenzja, komentarze) — napisz „M34 gotowe, PR #<numer>” i zakończ sesję.
```

## M35 — nawigacja bez Unity: nav-runner, trasy wzorcowe, numer zjazdu z ronda, logika komunikatów głosowych

```
Repo woogitsugames/kamion (Unity 6 C#; nawigacja w game/Assets/_Project/Core/Navigation/*.cs). Gałąź mistral/35-nav-runner — od origin/mistral-r5-int, jeśli istnieje (zawiera M27/M28), inaczej od origin/main (napisz od czego). Zadanie na wiele godzin; rzetelność ważniejsza niż tempo. Możesz i powinieneś używać subagentów do równoległej pracy i niezależnej weryfikacji.

PROBLEM: kod nawigacji C# testujecie dotąd „w głowie”, bo nie macie Unity — stąd błędy kompilacji w r4 (#21, #22). Rozwiązanie: tak jak tools/physics-runner kompiluje kod fizyki z game/Assets bez Unity (Compile Include + Sim/UnityShim.cs), zbuduj tools/nav-runner.
PRZECZYTAJ: CLAUDE.md, docs/adr/0150-map-minimap-gps.md, docs/reports/REVIEW-2026-11-13-s16-mistral-r4.md, tools/physics-runner/** (wzór), game/Assets/_Project/Core/Navigation/*.cs, tools/worldgen/navgraph/**, game/Assets/_Project/Tests/EditMode/Nav*Tests.cs, docs/owner/ELEVENLABS-GPS-VOICE.md.
ZAKRES GŁÓWNY:
1. tools/nav-runner (.NET 8): projekt kompilujący Core/Navigation/*.cs z game/Assets (Compile Include, bez kopiowania) + minimalny shim UnityEngine (Vector2, Mathf, Debug, Resources→czytanie pliku) — shim tylko dla użytych API; czyta game/Assets/_Project/UI/Resources/CabDisplay/Nav/<region>_route.bytes. Testy xUnit/NUnit. Dodaj job do .github/workflows/ci.yml (lfs: false).
2. Przenieś/zdubluj logikę testów EditMode Nav* tak, aby te same przypadki szły w nav-runnerze (EditMode zostaje).
3. Trasy wzorcowe (golden): ≥ 30 par start→cel w regionie (z nazwami ulic), dla każdej zapisany oczekiwany ciąg manewrów i długość; test porównuje. Uzasadnij każdą parę (np. omija zakaz skrętu X, rondo Putry, limit ciężarówki). Źródło prawdy = dane OSM w grafie, nie Google (zakaz).
4. Numer zjazdu z ronda dla Maneuver.Roundabout (liczenie wylotów w kierunku ruchu, tylko wyloty dostępne dla pojazdu), wystawiony w stanie nawigacji bez alokacji GC; testy na rondach regionu (Putry, Pamięci Bieżeństwa).
5. Logika wyboru komunikatu głosowego (bez plików audio): czysta funkcja (manewr, odległość, prędkość, pasy, nazwa ulicy, następny manewr) → lista ID zdań z docs/owner/ELEVENLABS-GPS-VOICE.md (np. GPS_B04 #1 + GPS_B12 #10); progi odległości zależne od prędkości (WORKING_VALUE z rachunkiem: czas na reakcję i hamowanie ciężarówki); kolejka bez powtórzeń; zero alokacji. Testy na trasach wzorcowych.
ROZSZERZENIA (po kolei): (a) ETA z limitów prędkości OSM i profilu ciężarówki (80/70/50 km/h wg przepisów PL — źródło ISAP); (b) wykrywanie zjechania z trasy i przeliczanie — testy scenariuszowe na nav-runnerze; (c) raport jakości grafu: krawędzie bez nazwy, podejrzane zakazy, ronda bez oneway.
NIE ZMIENIAJ: Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS, .asmdef, plików .bytes (lider regeneruje). Zmiany w game/Assets/_Project/Core/Navigation dozwolone — muszą kompilować się w nav-runnerze; dla Unity-only API zostaw #if UNITY_5_3_OR_NEWER tylko jeśli konieczne i opisz. Zakaz Google Maps/Street View/Earth/3D Tiles. Nie zmyślaj.
WERYFIKACJA PRZED ODDANIEM (obowiązkowa, z dowodami w PR): A. niezależny przegląd subagentami (kod, trasy wzorcowe vs dane, próba złamania testów) albo 3 osobne przebiegi od zera. B. test mutacyjny każdego nowego testu (np. odwróć oneway, wyłącz zakaz skrętu, przesuń próg — musi być FAIL; tabela). C. pełne uruchomienie nav-runnera, physics-runnera i pytest navgraph — liczby. D. tuż przed PR rebase na źródło gałęzi + origin/main, ponów C, diff tylko dozwolone ścieżki. E. lista A–D w opisie PR.
CIĄGŁY ZAPIS: commit + push gałęzi co ok. godzinę. Raport docs/reports/NAV-RUNNER-2026-11-13-mistral.md.
ODDANIE: jeden PR do main (nie draft), raport po polsku. NIE pushuj na main, NIE scalaj. Po utworzeniu PR NIE śledź go — napisz „M35 gotowe, PR #<numer>” i zakończ sesję.
```

## M36 — przepisy drogowe → parametry generatora (PTB 2022 + zał. 1–4 Dz.U. 2019 poz. 2311)

```
Repo woogitsugames/kamion (świat Białegostoku generowany z OSM; parametry dróg w tools/worldgen/roads/standards.py). Gałąź mistral/36-road-standards-audit od NAJNOWSZEGO origin/main. Zadanie na wiele godzin; rzetelność ważniejsza niż tempo. Możesz i powinieneś używać subagentów do równoległego czytania źródeł i niezależnej weryfikacji.

CEL: każdy parametr geometrii i wyposażenia drogi w generatorze ma źródło pierwotne albo uczciwe WORKING_VALUE — i testy pilnują zgodności.
PRZECZYTAJ: CLAUDE.md (zasady 3, 8), docs/05_*.md, tools/worldgen/roads/standards.py (nagłówek ze źródłami), docs/reports/AUDIT-SIGNS-PL-*.md, AUDIT-MARKINGS-PL-*.md, REVIEW-2026-11-12-s15-mistral-r3.md, REVIEW-2026-11-13-s16-mistral-r4.md (co poszło źle: wniosek ponad cytat; romb — przekątna vs bok).
ZAKRES GŁÓWNY:
1. Inwentarz: każda stała liczbowa w tools/worldgen/roads/*.py i tools/worldgen/streetscape/{signs,signs_route,furniture,props}.py, która opisuje rzeczywisty obiekt drogowy (szerokości pasów i poboczy wg klasy drogi i prędkości projektowej, krawężniki, promienie, pochylenia, skrajnia, wysokości i odległości znaków od krawędzi, bariery i ich wysokości, latarnie, oznakowanie poziome, wysepki, azyle). Tabela: plik:linia, nazwa, wartość, jednostka, obecny status/źródło.
2. Dla każdej: źródło pierwotne — Dz.U. 2022 poz. 1518 (PTB 2022, ze zmianą Dz.U. 2025 poz. 1352), Dz.U. 2019 poz. 2311 z załącznikami i zmianami (2021 poz. 438, 2021 poz. 2066, 2022 poz. 2377, 2026 poz. 132 — sprawdź każdą w ISAP/ELI), normy PN-EN tylko jeśli publicznie dostępne fragmenty. Cytat ≤ 25 słów, strona PDF, paragraf/tabela/rysunek, dla jakiej klasy drogi i grupy wielkości. Wartości z OSM dla naszego regionu (klasy dróg) czytaj z danych w repo.
3. Niezgodności: popraw stałą z komentarzem-źródłem TYLKO gdy przepis jest jednoznaczny; inaczej opisz i zostaw. Każda zmiana → test pytest (marker unit) z cytatem w docstringu.
4. Wskaż przypadki, gdzie przepis daje przedział, a generator bierze jedną wartość — zaproponuj regułę wyboru (np. wg prędkości z OSM) jako osobny punkt, bez wdrażania.
ROZSZERZENIA (po kolei): (a) sygnalizacja świetlna (zał. 3) — wymiary, wysokości, odległości; (b) urządzenia BRD (zał. 4) — bariery, ekrany, słupki prowadzące U-1a/U-1b, pachołki; (c) przejścia dla pieszych i przejazdy rowerowe — szerokości i odległości; (d) drogi ekspresowe S8/DK8 w regionie — parametry węzłów (łącznice, pasy wyłączania/włączania: długości).
NIE ZMIENIAJ: Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS, .asmdef, game/Assets/**. NIE regeneruj świata (lider). Źródła wtórne (blogi, fora, kalkulatory) nie potwierdzają przepisów. Zakaz Google Maps/Street View/Earth/3D Tiles. Nie wyciągaj wniosków, których cytat nie zawiera.
WERYFIKACJA PRZED ODDANIEM (obowiązkowa, z dowodami w PR): A. niezależny przegląd — subagenci sprawdzają ≥ 30 % cytatów z otwartym PDF (losowo, lista), drugi subagent szuka pomyłek interpretacji (wymiar zewnętrzny vs wewnętrzny, przekątna vs bok, grupa wielkości, klasa drogi); bez subagentów: 3 przebiegi od zera. B. test mutacyjny każdego nowego testu (tabela, FAIL). C. uv run --project tools/worldgen pytest tests/gis -q -m unit + pełne tests/gis (znane 2 czerwone na main — patrz wyżej) — liczby przed/po. D. tuż przed PR rebase na origin/main, ponów C, diff tylko dozwolone ścieżki. E. lista A–D w opisie PR.
CIĄGŁY ZAPIS: commit + push gałęzi co ok. godzinę. Raport docs/reports/ROAD-STANDARDS-2026-11-13-mistral.md (tabela parametrów ze statusem SOURCED/DERIVED/WORKING_VALUE).
ODDANIE: jeden PR do main (nie draft), raport po polsku. NIE pushuj na main, NIE scalaj. Po utworzeniu PR NIE śledź go — napisz „M36 gotowe, PR #<numer>” i zakończ sesję.
```

## M37 — walidator świata: kontrola jakości na danych `generated` (bramka 3)

```
Repo woogitsugames/kamion (świat Białegostoku z OSM/GUGiK; wynik generatora w Data/Regions/<region>/generated/*.json — w gicie, tylko do odczytu; *.glb przez LFS są dla Ciebie wskaźnikami). Gałąź mistral/37-world-validator od NAJNOWSZEGO origin/main. Zadanie na wiele godzin; rzetelność ważniejsza niż tempo. Możesz i powinieneś używać subagentów do równoległej pracy i niezależnej weryfikacji.

CEL: automatyczny raport jakości świata, który znajduje błędy widoczne dla kierowcy, zanim zobaczy je właściciel — z pozycją (E/N w metrach regionu) i id obiektu, żeby lider mógł zrobić z nich kamery kontrolne.
PRZECZYTAJ: CLAUDE.md, docs/05_*.md, docs/06_*.md, docs/11_DECYZJE_WLASCICIELA.md (D51), tools/worldgen/roads/consistency.py i fidelity/ (istniejące kontrole — nie dubluj), tools/worldgen/qa_report.py, ADR 0141, 0144, 0146 (sekcje Open — tam są znane błędy, sprawdź, czy walidator je łapie).
ZAKRES GŁÓWNY (każda kontrola = funkcja + test na danych syntetycznych + przebieg na danych regionu z liczbami):
1. Nachodzenie obiektów: znaki/latarnie/słupy/drzewa/budynki w jezdni lub na krawężniku (odległość od krawędzi < skrajnia), obiekty w sobie nawzajem, drzewa w budynkach.
2. Ciągłość: krawężniki, chodniki, ogrodzenia i bariery z przerwami < X m (podejrzane szczeliny) i podwójne (równoległe < 0,5 m) — z wyłączeniem końców barier na pomostach (M29 już to robi).
3. Teren: skoki wysokości jezdnia–teren–chodnik > WORKING_VALUE, „ściany terenu” (terrain walls), jezdnia zakopana/unosząca się.
4. Znaki: orientacja (lico w stronę ruchu, którego dotyczy), wysokość dolnej krawędzi, znaki zasłonięte przez drzewa/latarnie w osi widzenia kierowcy na dystansie rozpoznania (geometria 2D/2,5D).
5. Raport HTML/MD z tabelą: kategoria, liczba, top 20 z pozycją E/N, id, link do kafla; plik JSON do automatycznego tworzenia kamer kontrolnych (format: pozycja, kierunek, opis).
ROZSZERZENIA (po kolei): (a) ocena „trasy G3” (route_start.json): tylko obiekty widoczne z kabiny ±60 m od trasy, ranking ważności; (b) porównanie z poprzednim przebiegiem (diff liczb między gałęziami); (c) kontrola zabudowy: budynki bez dachu/ścian, przenikanie z drogą, wysokość vs piętra z BDOT/OSM.
NIE ZMIENIAJ: generatorów (tools/worldgen/roads/*, streetscape/*.py) — tylko nowy moduł walidatora (np. tools/worldgen/validate/) + testy; Data/**, *.glb, *_meta.json, game/**, .gitattributes, LFS. Progi bez źródła = WORKING_VALUE z uzasadnieniem. Zakaz Google Maps/Street View/Earth/3D Tiles.
WERYFIKACJA PRZED ODDANIEM (obowiązkowa, z dowodami w PR): A. niezależny przegląd — subagent bierze ≥ 20 losowych znalezisk i sprawdza w danych, czy to prawdziwy błąd (precyzja w %), drugi sprawdza znane błędy z ADR Open (czułość: które łapie, które nie); bez subagentów: 2 przebiegi od zera. B. test mutacyjny każdej kontroli (wstrzyknij błąd w kopię danych testowych → musi być wykryty). C. uv run --project tools/worldgen pytest tests/gis -q (znane 2 czerwone na main) — liczby, czas działania walidatora na regionie. D. tuż przed PR rebase na origin/main, ponów C, diff tylko dozwolone ścieżki. E. lista A–D w opisie PR.
CIĄGŁY ZAPIS: commit + push gałęzi co ok. godzinę. Raport docs/reports/WORLD-VALIDATOR-2026-11-13-mistral.md.
ODDANIE: jeden PR do main (nie draft), raport po polsku. NIE pushuj na main, NIE scalaj. Po utworzeniu PR NIE śledź go — napisz „M37 gotowe, PR #<numer>” i zakończ sesję.
```

## M38 — analiza pomiarów z telefonu: płynność, naprzemienne klatki, termika

```
Repo woogitsugames/kamion (mobilny symulator; pomiary z telefonów: scripts/device-metrics.ps1 i artifacts/fold-flicker/fold-run.ps1 zapisują CSV klatek, PSS, temperatury, logi kamery). Gałąź mistral/38-device-metrics-analysis od NAJNOWSZEGO origin/main. Zadanie na wiele godzin; rzetelność ważniejsza niż tempo. Możesz i powinieneś używać subagentów do równoległej pracy i niezależnej weryfikacji.

CEL: jedno narzędzie Python, które z surowych plików pomiaru daje powtarzalny raport bramki wydajności — tak, żeby liczby w ADR były zawsze liczone tak samo.
PRZECZYTAJ: CLAUDE.md (zasada 2: telefon jest prawdą; zasada 3), scripts/device-metrics.ps1, scripts/build-android.ps1 (część logcat), artifacts/fold-flicker/fold-run.ps1 i ADR 0152 (wykrycie naprzemiennych klatek, „okna do 100 %”), ADR 0136 (A16 Low: GPU p95), wszystkie przykładowe CSV/logi pomiarów, które są w gicie (git ls-files 'artifacts/**' — sprawdź, co jest; dużych plików LFS nie masz).
ZAKRES GŁÓWNY:
1. tools/perf/ (uv, pyproject): parser formatów CSV/logów z repo (opisz każdy format i wersję; nieznane kolumny → błąd z komunikatem).
2. Metryki: FPS średni, czasy klatek p50/p95/p99/max, GPU p95 (jeśli jest), frame pacing (odchylenie od celu 33,3/16,7 ms), procent klatek > 1,5× celu, „janky frames”, naprzemienność klatek (wzór z ADR 0152 — zdefiniuj formalnie i przetestuj), trend termiczny i moment throttlingu, PSS min/max/trend (wyciek?), okna przesuwne (np. 10 s) z najgorszym oknem.
3. Porównanie przebiegów (przed/po, telefon A vs B) z testem istotności lub co najmniej przedziałem ufności (bootstrap) — żeby „brak regresji” był liczbą, nie wrażeniem; opisz metodę i założenia.
4. Raport MD + wykresy PNG (matplotlib), wejście = katalog pomiaru z artifacts/device/<serial>/<ts>/.
5. Testy pytest na syntetycznych danych o znanych własnościach (np. wygenerowana naprzemienność 15,6 % musi dać 15,6 %; throttling w 120. s musi zostać wykryty).
ROZSZERZENIA (po kolei): (a) CLI do wywołania z PowerShell po pomiarze (podaj gotową linię do wpięcia w device-metrics.ps1 jako propozycję — bez zmiany skryptu); (b) zbiorcze zestawienie wszystkich pomiarów w repo w jedną tabelę (historia bramek); (c) wykrywanie pomiarów do odrzucenia (telefon zablokowany, ekran wyłączony, bateria < progu, temperatura startowa > 36 °C) z logów.
NIE ZMIENIAJ: scripts/*.ps1, game/**, Data/**, *.glb, *_meta.json, .gitattributes, LFS. Nie zmyślaj liczb.
WERYFIKACJA PRZED ODDANIEM (obowiązkowa, z dowodami w PR): A. niezależny przegląd — subagent przelicza ręcznie (numpy w osobnym skrypcie) metryki dla ≥ 3 prawdziwych plików z repo i porównuje z narzędziem; drugi szuka błędów definicji (percentyle, okna, jednostki ms/µs/ns, klatki pominięte); bez subagentów: 2 przebiegi od zera. B. test mutacyjny każdej metryki (zepsuj definicję → test FAIL; tabela). C. pytest — liczby. D. tuż przed PR rebase na origin/main, ponów C, diff tylko dozwolone ścieżki. E. lista A–D w opisie PR.
CIĄGŁY ZAPIS: commit + push gałęzi co ok. godzinę. Raport docs/reports/DEVICE-METRICS-TOOL-2026-11-13-mistral.md.
ODDANIE: jeden PR do main (nie draft), raport po polsku. NIE pushuj na main, NIE scalaj. Po utworzeniu PR NIE śledź go — napisz „M38 gotowe, PR #<numer>” i zakończ sesję.
```
