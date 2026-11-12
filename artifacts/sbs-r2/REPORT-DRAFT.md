# R2 — wersja robocza, pełny GIS w toku

Gałąź gpt-sbs-r2, worktree .claude/worktrees/gpt-sbs. To jeszcze nie jest końcowy REPORT. Źródła końcowego testu: e386b92996c10ef92022508b8ede0c10c7843863. Pełna seria renderowana na b9b5574e2dd093af3b36b82ff2a84f55643141e3. Po renderach zmieniały się narzędzia raportowania i dokumentacja, a nie kamery ani świat. Main włączono na początku rundy przez merge ce3f1a77.

R2 dodaje wersjonowane metryki kontrastu RMS, zakresu percentylowego i gradientu oraz ręczne próbki nieba/asfaltu z wyłączeniami. Próbka jest kwalifikowana tylko dla konkretnych SHA zdjęcia i renderu, zgodnego światła, klasy A/B i notatki przeglądu. Histogram i luma są diagnostyką obrazu, nie pomiarem albedo. Nie przyznają zaliczenia bramki.

[Raport HTML z historią i trendem](../sbs-gate3/latest/index.html) działa lokalnie, bez zasobów sieciowych. Ma wybór rundy, tieru i światła, osobny widok C, źródła i licencje. Trend odrzuca zmienione zdjęcie, pozę, maski, definicję metryk, rozdzielczość, tier, światło i niesprawdzone próbki. R1 przeliczono tym samym algorytmem v2 z pierwotnych bajtów inputs.zip, w jawnym trybie historical. Oryginalnych dowodów r1 nie nadpisano.

Zachowano 42 zdjęcia: 25 B, 17 C, brak A. R2 ma 168 nowych raw, 100 arkuszy B i 168 dodatkowych arkuszy diagnostycznych. Każdy arkusz ma szerokość 960 px. Wszystkie stany mają komplet 42 capture. Rzeczywiste bajty 64 GLB High i 64 Low zgadzają się z manifestem; oba warianty siatek są identyczne z r1. SHA 143/168 PNG są identyczne z r1; pozostałe różnice nie są dowodem poprawy świata.

Kwalifikacja obejmuje trzy Low-clear. To te same piksele i te same maski w r1/r2: mediana zmiany błędu histogramu, luma asfaltu i kontrastu wynosi 0. Pozostałe trzy stany jawnie nie mają porównywalnych próbek. Różny kierunek słońca i cień w jednej próbce nadal ograniczają interpretację. Nie agregowano pozostałych obrazów jako wiarygodnej fotometrii.

Formalna recenzja D51 nadal dotyczy r1: FAIL, 12 rozpoznawalnych, 11 częściowych, 2 nierozpoznawalne. Raport wiąże ją z oboma SHA; 19/25 nowych par Low-overcast ma te same ocenione piksele. Sześć nowych obrazów obejrzano samodzielnie i niezależnie. Główne braki pozostają. W 180137 są częściowo przezroczyste zielonkawe panele — problemem są ich proporcje, ciągłość i osadzenie, a nie całkowity brak ekranu. Przy 150280 są hale i blok, ale nie ma charakterystycznej pierzei handlowej. Nie zmieniono historycznej recenzji ani nie awansowano klas.

![Brak najbliższej podpory — zdjęcie i render Low-overcast](evidence/sheets/Low-overcast/sbs-g3-a-1398898753813071.png)

![Bramownica w innym położeniu — zdjęcie i render Low-overcast](evidence/sheets/Low-overcast/sbs-g3-b-275528677534382.png)

Źródła, autorzy, daty i licencje są w każdym arkuszu oraz w [migawce referencji](evidence/inputs/sbs_references.json). W drugim przykładzie stacja kamery samochodowej pozostaje niepotwierdzona; nie wyznaczono nowej odległości do bramownicy.

[Pełne liczniki 168 kamer](counters/camera-counters.csv) rozdzielają draws geometrii i instancji. Wszystkie delty Low i High względem r1 wynoszą 0, również dla estymacji trójkątów i cieni. Low max 812 = 445 + 367; High max 1376 = 945 + 431. To estymacje CPU przed batchingiem, nie GPU ani pomiar A16. Nie wykonywano pracy na telefonie.

Walidacja zakończona do tej chwili: generator kod 0, 457 s, bez fallback=True; import 64 chunków Low+High; EditMode 261/261; pojedyncze testy report 25/25, core 40/40, photometry 13/13; fidelity kod 0; audyt integralności kod 0. Pierwszy test raportu wykrył błąd Unicode escaping, poprawiony bez osłabiania regresji. Niezależna kontrola dała PASS narzędzia/kompletności, bez PASS świata. Przegląd własny objął 100/100 B: 25 natywnych Low-clear i 75 na 21 stronach pozostałych stanów. UI sprawdzono w 1280×960 i 390×844; naprawiono przewijanie poziome, konsola bez błędów, przełączniki i historia działają. Pełny GIS: W TOKU, wynik zostanie uzupełniony.

Dodatkowa diagnostyka 182 obejmuje 16 nowych prób, wszystkie obejrzane; niezależny krytyk wskazał 12 jako najlepszą do dalszej pracy, ale zachował C z powodu braku jednoznacznych kotwic. Nie zmieniono produkcyjnej pozy. Dla 326 zapisano potrzebę rozdzielenia roll, pitch i optyki; nie zmieniono C#. Ponowne zapytanie Mapillary wokół pierwszych 300 m zwróciło 20 rekordów przy stacjach 317–365 m i żadnego nowego kandydata do 300 m. Pierwsze 300 m nadal bez zatwierdzonej pary.

Otwarte: kalibracja C i cztery zastrzeżenia B, brak A, brak początku trasy, jedynie trzy próbki fotometryczne i brak pomiaru telefonu. Pliki świata, shaderów i runtime nie są częścią zmiany SBS. Osiem pochodnych plików innych domen pozostaje po generatorze i zostanie przywróconych po końcowym teście. Przewidywane punkty integracji to ADR 0111, rozszerzenia sbs_*.json i narzędzia SBS; nie należy brać pochodnych generatora z tej rundy zamiast aktualnego main.

Dostarczenie do main: JESZCZE NIEWYKONANE. Po końcowym GIS i zapisie REPORT nastąpi robocopy artefaktów r2 oraz latest, bez commitowania na main. Następna runda: nowa gałąź gpt-sbs-r3 od r2, merge aktualnego main i ranking odstępstw w docs/refs/sbs-priorities.md. Cel całej sesji trwa do około 12.11.2026, 21:31 Europe/Warsaw.
