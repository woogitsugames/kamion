# Life r5 — palety i drobne życie placów

Krok 1 (12.11.2026 około 13:52): r4 przekazana (9f87ed61; kod i końcowe testy 56021edf/f39e0316), REPORT skopiowany ostatni do main artifacts/life-r4, kopia sprawdzona. Utworzono gpt-life-r5 i dołączono aktualne main 3cdd6da4 wyłącznie do własnej gałęzi. Generaty/GLB/props_meta z main, do kanonicznej regeneracji. LICENSES z main zawiera już identyczny wpis life r3 i nowszy pełny opis kabiny oraz nowe pozostałe licencje; nie zdublowano starej tabeli kabiny. Właściwe zmiany produkcji life r4 zachowane. Uaktualniono tylko historyczny docstring ciągnika 1.5→1.7 k przed nowym baseline.

Cel r5: zaległy backlog istniejących stosów palet. LOD0 obecnie pełne pudełka, LOD1 jeden pełny blok. Najpierw aktualne dane instancji i czytelne kamery/baseline, potem konstrukcja desek/klocków i prześwitów według otwartych zdjęć oraz wymiarów. Nie dodawać fikcyjnego rozmieszczenia, logo lub pieczęci, nie zmieniać dróg, budynków, Kwadratu ani innych dziedzin. Dalszy backlog lakieru/kurzu/cienia z recenzji batch C pozostaje otwarty po paletach.

Oryginalny termin doby około 12.11.2026 21:31 Warszawa. Jedyny integrator main: lider Claude (S11→S12 i jego handoff). Nie przejmować roli lidera, triggera/watchdoga/Fable. Bez merge do main, push i telefonów. Każde Unity przez gpt-life, ciężki Python przez heavy gpt-life-r5; StaleHours 1000000 i respektowanie rezerwacji/PHONE_RUN. WIP + STATUS po krokach, REPORT i kopia na koniec, następna runda od razu.

Następny krok: zakończyć merge, przygotować aktualne źródła/fixture i helpery rundy, kanoniczny World/fidelity (materiały tylko jeśli wejścia się zmieniły), kamery rzeczywistych palet, import i baseline czterech warunków. Nie używać kadrów starego main z r4 do budżetu r5.

Krok 2: odświeżono raw CC0, źródła CC0/Megascans i natywne Truck/Trailer z main; źródła fixture przed/po kopiowaniu oraz wszystkie kopie zgodne SHA. Nie kopiowano świata z aktywnego main. Następny krok: baseline-gen.ps1 pod jednym heavy.

Krok 2: odświeżono dozwolone raw CC0/Megascans i stabilne fixture Truck/Trailer (pre/post źródeł i kopii SHA zgodne). Wszystkie 151 map Medium nadal identyczne z końcowym r4, git diff generatora materiałów/spec względem 71477fbd pusty; build_all niepotrzebny dla tego baseline. Następny krok: baseline World → fidelity → test pojedynczy → source-proof/kamery, jeden heavy gpt-life-r5.
