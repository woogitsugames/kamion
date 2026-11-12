# Przekazanie sesji life — 12 listopada 2026

Praca została wstrzymana na prośbę właściciela z powodu kończącego się limitu tygodniowego. Nie wznawiać samoczynnie pętli 24 h. Nie ubijano procesów, nie scalano do main i nie pushowano. Jedynym integratorem pozostaje Claude.

## Repo i gałąź

- Repo main: C:\Users\matma\Documents\Claude\kamion.
- Własny worktree: C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-life.
- Bieżąca gałąź: gpt-life-r5, baza main dołączona w tej rundzie: 3cdd6da4, merge d2cabd7d.
- Ostatni commit przed zapisaniem przekazania: 045d0207. Dalsze commity wyłącznie zapisują to przekazanie i naturalne zakończenie tła; aktualny SHA: git log -1.
- Sprawdzono 12.11 około 16:24: gpt-life-r4 jest już przodkiem main (main w tym odczycie 165c419c). R4 została zintegrowana przez lidera; ja nie wykonywałem scalenia do main.

## Zakończone rundy

R1–R3 są przekazane i scalone. R4 również jest scalona; jej pełny REPORT i dowody znajdują się w main artifacts/life-r4. R4 dodała przestrzenne wnętrza felg statycznych ciągników/naczep. Wynik: GIS 709 passed / 1 xfailed, EditMode 340/340; maksymalny wzrost trójkątów na trasie Low +0,36581%, High +0,58573%, world draws i instance draws oddzielnie +0. Większy wzrost w kamerach inspekcyjnych ujawniono w REPORT. Ocena wizualna PARTIAL, bez pomiaru A16. Dwa nieużywane materiały cache po EditMode przywrócono dokładnie, z zachowaniem surowych logów oraz pełnym ponownym sprawdzeniem 408 ówczesnych materiałów. Szczegóły i ograniczenia są w raporcie r4.

## R5: wykonane, ale jeszcze bez wdrożenia palet

Celem r5 są istniejące wygenerowane stosy palet, obecnie pełne pudełka. Produkcja palet NIE została zmieniona. Plik pallet-candidate.py jest wyłącznie niezaaplikowanym szkicem w artefaktach. Nie scalać r5 jako gotowej poprawy wyglądu palet.

- Przygotowano worktree/fixture i zweryfikowano 151 niezmienionych map Medium. Nie powtarzano niepotrzebnego build_all.
- Kanoniczny World zakończył się bez fallback=True, 758,4 s; commit ba42063c. Fidelity i pojedynczy test: 9 passed, 1 xfailed. Baseline complete/0: 4447672c, baseline-gen-result.json.
- Source-proof: 192 pliki danych, 0 rozbieżności, 15 gotowych źródeł Fab/Megascans, 151 map. Nie dodano ich binariów do gita.
- Wybrano cztery rzeczywiście istniejące instancje w wygenerowanym świecie: stosy 4/8/12/16. Po pięć ujęć oraz dwa kontrolne kadry kontenera/kosza: 22 nowe kamery, packet 105, razem z kontrolami sceny 153. To nie jest dowód fizycznego rozmieszczenia na zdjęciach Mapillary.
- Świeży import Low+High / Medium zakończył się IMPORT_RESULT OK. Zapis: e768c41c, prepared-import-20261112-154301.log. Data w nazwie logu pochodzi z oczekiwania na slot, nie z rzeczywistej godziny startu Unity.
- Pierwszy capture zatrzymał mój błędny próg minimum 400 materiałów w płaskim katalogu. Surowy błąd zachowano: post-baseline-result.json i post-baseline-console.log. To nie był błąd Unity ani testów.
- Poprawka wymaga obecności wszystkich 298 niekolizyjnych definicji manifestu. W katalogu głównym jest 335 .mat, a łącznie z Proto 444. Zachowano oddzielne dokładne kopie baseline-native (335) i baseline-native-full (444), z manifestami SHA. Post-candidate porównuje wszystkie 444.

## Stan zadań w chwili przekazania

Po poprawce uruchomiono raz resume-baseline-capture.ps1. Proces pwsh 72932, sesja narzędzia 78185. To już uruchomiony batch czterech warunków; pozostawiono go do naturalnego zakończenia. Low-clear miał VISUALQA_RESULT OK rendered=153; około 16:24 trwał Low-overcast. Pozostałych wyników nie deklaruję z góry.

STOP-REQUESTED.json blokuje następny etap diagnose-lod.ps1 przed uruchomieniem Unity. Po całym capture i walidacji rodzic dojdzie do tej blokady i może zapisać phase=native-lod / exit=1. Jeżeli istnieje STOP-DRAINED.json, oznacza to zamierzone zatrzymanie na polecenie właściciela, nie wykonaną diagnostykę. Każdy inny błąd trzeba przeczytać w logu, nie uznać automatycznie za STOP.

Lekki finish-stop-handoff.ps1 czeka na proces 72932, niczego nie zabija i nie uruchamia Unity/Pythona. Po jego zakończeniu zapisze DRAIN-RESULT.json, dopisze stan do tego pliku oraz STATUS/REPORT, wykona commit WIP i uzupełni main artifacts/life-r5, kopiując REPORT ostatni. Szczegóły późniejszego stanu należy sprawdzić w DRAIN-RESULT.json i finish-stop-console.log. Jeśli tych wyników jeszcze nie ma, batch nadal trwa lub skrypt kończący wymaga sprawdzenia.

Nie ma innego mojego aktywnego generatora lub pełnego pytest. Baseline heavy zakończył się i zwolnił gpt-life-r5. Aktualne Unity zwalnia własny slot gpt-life w finally, ustawienia Unity są przywracane w tym samym bloku. Nie usuwać cudzych blokad ani PHONE_RUN. Nie przywracać plików ustawień, dopóki własne Unity jeszcze działa.

## Co jest gotowe do wznowienia

- refs: dwa obejrzane zdjęcia CC0 W.carter i PALLET-PREFLIGHT.md. Wymiary EPAL 1200×800×144 mm, 11 desek i 9 klocków; pozostałe proporcje to WORKING_VALUE. Bez logo/stempli w modelu. Zdjęcia są referencją konstrukcji z innego miejsca, nie potwierdzeniem lokalizacji.
- PALLET-DESIGN.md i pallet-candidate.py: LOD0 deski/poprzeczki/klocki, LOD1 uproszczony górny pokład z prawdziwymi wejściami na widły, ta sama grupa pallet_wood i kolizja. Projektowane koszty 204 i 120 trójkątów na warstwę są tylko rachunkiem szkicu, nie pomiarem eksportu ani klatki.
- test_pallet_openings.py: nie zainstalowany w tests i nie uruchomiony. Promienie przez wejścia z obu osi, trafienia i właściwa strona ścian klocków, obrys, kolizja, deterministyczność, brak degeneracji.
- audit-pallet-scope.py: nie uruchomiony na kandydacie. Chroni wszystkie pozostałe węzły GLB, kolizje, materiały/grupy i 192 pliki danych; kandydat ma zmienić wyłącznie osiem LOD czterech pustych stosów.
- candidate-gen.ps1 i post-candidate.ps1: przygotowane, nie uruchomione. Blokada bez BASELINE-INSPECTED.json. Osobny heavy na test/World/audyt, Unity przez slot, później komplet kamer i porównanie pod heavy. Trasa maks. +2% trójkątów, oba rodzaje draws osobno +0. Limity klatki bez zmian.
- Life5PropLodProbe.cs i diagnose-lod.ps1: przygotowana sonda faktycznych buforów natywnego WorldInstances. Osobne flagi od sondy r4, aby nie podwajać dispatch. W r5 jeszcze nie uruchomiona. Far50 ma sprawdzić LOD1 także przy High lodBias 1,5; rzeczywisty LOD nadal UNVERIFIED.

## Kolejność wznowienia po nowym poleceniu właściciela

1. Sprawdzić aktualny STATUS, git status, DRAIN-RESULT oraz czy 72932/Unity jeszcze działają. Nie uruchamiać duplikatu batcha.
2. Obejrzeć surowe wyniki capture/validation. Jeśli cztery warunki zakończyły się poprawnie, NIE powtarzać World/importu/capture tylko dlatego, że kontrolowany STOP ma exit1.
3. Dopiero po wyraźnym wznowieniu usunąć własny STOP-REQUESTED.json; zachować jego kopię/historyczny commit. Uruchomić brakującą diagnostykę LOD, obejrzeć PNG ≤960 px, sprawdzić materiał pallet_wood, teren i widoczność stosów. Nie ma jeszcze BASELINE-INSPECTED.json.
4. Po rzeczywistej ocenie baseline zastosować szkic tylko do pallets_empty w life_props.py, zainstalować test, zapisać WIP i STATUS. Potem candidate-gen / import / cztery warunki / natywny LOD / pełne budżety i foto|render. Nie obniżać limitów ani nie ukrywać kamer inspekcyjnych.
5. Pełny pytest tests/gis i EditMode dopiero po wyborze wariantu. Przed EditMode zachować dokładne własne materiały; surowe błędy zawsze zachowywać. Następnie ADR0122, REPORT, kopia artifacts z REPORT ostatnim. Kolejna runda tylko jeśli właściciel wznowi długą pracę.

Każde Unity: scripts/unity-slot.ps1 -Acquire/-Release -Owner gpt-life. Ciężki Python: -Pool heavy -Owner gpt-life-r5. StaleHours 1000000, żadnego Priority/zmiany limitów/usuwania cudzych blokad. Bez telefonów, adb, push i merge do main. Własność produkcji: life.py, life_cars.py, life_props.py, depot_yard.py oraz _CARPAINT; wspólne flagi wyłącznie addytywnie w zatwierdzonym zakresie.

Otwarte P1 po paletach: czerń clear, szum płatków, czysty tył i prostokąt pod autem. NEXT-R6-PREFLIGHT.md dokumentuje wyłącznie odczyt kodu, nie wykonaną poprawkę. Odbicia dla statycznych aut pochodzą z modelu sky/ground; nie udawać brakujących lokalnych odbić losowymi pasami lub samym obniżeniem albedo. Do rozdzielenia kontakt i podwozie. A16/GPU oraz wygląd r5 pozostają niezweryfikowane.
