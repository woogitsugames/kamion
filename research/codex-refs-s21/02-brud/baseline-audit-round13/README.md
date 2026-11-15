# M61/P18 — niezależny audyt mianownika, obieg13

**Werdykt: nie używać „1/20 nowych” ani sumy „P18 + CR6” bez deduplikacji.** Wymaganie użytkownika to co najmniej 20 kadrów ŁĄCZNIE. M61-FIX wymaga dodatkowo co najmniej 12 NOWYCH względem pierwotnego M61. Jedno nowe źródło w naszym podzbiorze nie oznacza całego aktualnego stanu projektu.

## Zakres i metoda

Odczytano recenzję 2026-11-14, blok M61-FIX w MISTRAL-FIXES-12 oraz aktualne README/manifest P18. To dane wejściowe, a nie przyjęte wyniki wizualne. Własny ogląd lokalnych pełnych kadrów:108,109,118,121,136,137,140,143,155,158 i WSZYSTKIE176–188. Razem 23 z 88 rekordów kadrowych. Osobno obejrzano istniejące wycinki121/158. Pozostałe 65 = NOT_REVIEWED, nie zero i nie automatyczne odrzucenie.44 pliki JPG są obecnie dostępne w lokalnym katalogu v2; brak nowego pobierania fotografii.

Zapisano jeden publiczny odczyt metadanych 13 konkretnych plików Commons: źródłowe rozmiary, opis autora i licencje w source-metadata-snapshot.json. Dla innych wierszy deklaracje P18 mają osobny status nieweryfikowany; wyjątkiem są Flickr 176/178 sprawdzone na publicznych fotostronach we wcześniejszym round12. candidates.csv zachowuje status P18 jako deklarację oddzielnie od własnego oglądu, rodzaju pojazdu, brudu i progu rozdzielczości.

## Trzy odrębne mianowniki

| Cel | Co liczymy | Ograniczenie |
|---|---|---|
| Użytkownik:≥20 łącznie | Unikalne rzeczywiste kadry brudnych podwójnych tylnych drzwi potwierdzonej naczepy, stare oraz nowe | Solówki/vany wykluczone według aktualnego polecenia; nie sam tytuł lorry/trailer |
| FIX pkt8:≥12 nowych | Nowe względem pierwotnych 75 źródeł M61, spełniające treść i rozdzielczość≥1000 px na wysokość drzwi, ruch/zaraz po trasie | Nowy plik/crop/pobranie/alias nie jest nową fotografią |
| Zima i Europa | Użytkownik/końcowe KRYTERIA:≥6 każdego w całości; FIX pkt8 mówi także „w tym”≥6 każdego w nowych kadrach | Prowadzić licznik całości i licznik podzbioru nowych; nie przenosić do nowych starego kadru121 |

Próg 1000 px w pkt8 dotyczy nowych referencji FIX; nie należy po cichu zamieniać „20 łącznie” w „20 NOWYCH”. Dla ostrzejszej oceny całej bazy można osobno użyć kolumny rozdzielczości, lecz jest to inny filtr. Historyczny M61 dopuszczał szersze słowo skrzynie; aktualne polecenie użytkownika wymaga naczepy i ta kontrola nie zalicza solówek.

## Deduplikacja i chronologia

- SOURCED [aktualny CSV]: 75 pierwotnych rekordów P18-101…175 oraz 13 dopisków 176…188 =88 wierszy. To liczby rekordów, nie zaakceptowanych obrazów.
- SOURCED [normalizacja URL i photoID]: 87 unikalnych kluczy źródła. P18-144 i 159 wskazują TEN SAM plik `Semi-trailer based mobile blood transfusion station (rear view).jpg`. Nieobejrzany w tej rundzie, więc bez kwalifikacji brudu. Recenzja wskazuje też 139/153 jako ten sam pojazd; zachowano tę informację jako cudzy wynik, bez nowego potwierdzenia wizualnego. Zdjęcia a pojazdy to oddzielne liczniki; FIX nakazuje139/153 liczyć raz.
- **P18-182 = CR6-001 Western Express**, jeden photoURL, nie dwa kadry. P18-183 = CR7-A01 Premier. P18-158 =02-009/CR7-A02 Knight. P18-121 =02-008. Całej unii nie wolno obliczać przez sumę liczników pakietów.
- SOURCED [read-only git log, history.json]: P18-182 pojawia się w29ba270e8cced006d41b01e275e26e1455699b94,2026-11-15 14:10:21+01:00. Manifest CR6 w6f34302b10a25939edb54c20ef55173ed0ca49ed,2026-11-15 21:14:52+01:00. Są to czasy commitów w Brukseli/CET, NIE daty pierwszego odkrycia/pobrania. P18 wpis był zacommitowany wcześniej. CR6 jest odrębnie przyjętym pakietem naszej gałęzi, ale po porównaniu z bieżącym P18 nie stanowi kolejnej nowej fotografii dla całego projektu. Brak podstaw do przypisywania pierwszeństwa samym czasem commitu.

## Co potwierdza własny ogląd

W przejrzanym podzbiorze są **co najmniej 3 użyteczne treściowo źródła** potwierdzonej naczepy i lokalnego brudu drzwi:158(Knight),182(WesternExpress),183(Premier). To dolna granica oglądu 23/88, NIE kompletny wynik 3/20 całego projektu. Pierwotny podzbiór zawiera 158; dopiski FIX 182/183. Z tych trzech tylko 182 ma w tej kontroli potwierdzoną wysokość drzwi≥1000 px. Zimowe i europejskie w tej potwierdzonej trójce: 0/0 (źródłowe USA), NIE globalny wynik całych 88.

| Kadr | Treść i typ | Rozdzielczość / kwalifikacja |
|---|---|---|
|121| Film/smugi potwierdzone; naczepa vs solówka/drawbar UNVERIFIED, autor podaje long lorry | Natywne 1600×1493; same drzwi około500–600px. PENDING_TYPE. Zimowa data/styczniowa mokra scena nie identyfikują soli |
|158| Źródłowy semi-trailer; film na czerwonych polach, napis i wycierki; próg szary | Lokalnie 960×1199, drzwi 650–700px. Natywnie 1093×1365 daje około740–800px, NIE1000. PASS_CONTENT; poza nowym filtrem1000 |
|176| Film i dwuskrzydłowość widocznej części tak; krajEngland z UI, ale typ niepotwierdzony | Lokalnie 1024×768, widoczny fragment około520–560px. Render 1600×1200 z round12 nie jest dowodem pełnego oryginału i ma uciętą górę. Maksymalny oryginałUNVERIFIED |
|178| Lokalne zacieki nad dolną listwą i uszkodzone naklejki osobno; autor dirty white lorry | Tylko dolny fragment; większy render 1599×1062 nie pokazuje pełnych drzwi. Typ/kraj/originalUNVERIFIED; nie odrzucać źródła jako nieistniejącego, lecz nie zaliczać do naczep |
|182| Źródłowy semi-trailer w ruchu; lokalny szary film i smugi | Natywnie 1522×2233, drzwi około1400–1500px. Lokalna kopia1091×1600 ma około1000–1050px drzwi. PASS_GE1000; ten sam co CR6 |
|183| Źródłowy semi-trailer w ruchu, lokalny pionowy szary film na lewym polu; niebieski ton prawego osobno | Natywnie 1118×1487; drzwi około910–970px. PASS_CONTENT, poza nowym progiem1000 |

Pozostałe 8 z 10 pierwotnych wytypowanych:108(rdza/zużycie vs film i typ wymagają dalszego dowodu),109/155(śladowe/prawie czyste),118(zasłonięte powierzchnie przez TrailerTail),136(jasna plama/mechanizm niepewny),137(białawe plamy/mechanizm niepewny),140(odbicia na drzwiach, brud progu sam nie wystarcza),143(mały lokalny detal; natywna wysokość blisko 1000px pozostajeUNVERIFIED). Nie skopiowano ocen recenzji jako własnych PASS.

Wszystkie 13 dopisków 176–188 obejrzano.176/177/178/179 mają użyteczny film/wycierki, ale typ naczepy nie jest potwierdzony w dostępnej konstrukcji/opisie.180/181/187 nie mają wymaganej pary pionowych skrzydeł.184 autor opisuje wprost box truck;185 to dostawczy Opel Vivaro.186 to odległy zimowy kontekst kilku pojazdów, nie trzy osobne kadry;188 śnieżny kontekst bez potwierdzonych podwójnych drzwi naczepy.182 i183 jak wyżej. Szczegóły każdego w CSV.

## Rozdzielczość bez pozornych zysków

Wysokość CAŁEGO zdjęcia nie jest wysokością drzwi. Obraz lokalny P18-136 ma 960×1434, a aktualny oryginał Commons 861×1286 — większa kopia nie dowodzi większego źródłowego detalu. Dla143 lokalne 1600px szerokości z drzwiami około330–370px nie przesądza oryginalnych4636×2713: po samej geometrii skali około960–1070px, więc próg bliski i UNVERIFIED bez natywnego oglądu. Nie pobierano ponownie po dawnym 429 i nie interpolowano do kwalifikacji.

Wielkości drzwi w tym raporcie są ESTIMATED z widocznej geometrii, wymiary całych źródeł SOURCED z imageinfo. Natywne metadane Commons nie zastępują oglądu oryginału, zwłaszcza przy granicy 1000px. Flickr pełne oryginały inne niż wyrenderowane obrazy pozostająUNVERIFIED — nie udajemy, że 1024px kopia jest maksimum źródła.

## Dalszy licznik

Nie potwierdzono ukończenia20/12/6/6. Nie ma też podstaw twierdzić, że cały projekt ma dokładnie 1 lub 3 kwalifikowane zdjęcia. Wymagany jest dalszy audyt 65 nieobejrzanych rekordów i rozstrzygnięcie PENDING typ/mechanizm/rozmiar, a dopiero potem statystyka stref. Bieżące 1 nowe przyjęte CR6 to licznik naszego niezależnego podzbioru, którego źródło nakłada się na P18-182.

Całość pracy read-only względem P18, parenta i gry; zapis wyłącznie baseline-audit-round13. Żadnego git commit/push, nowego zdjęcia ani zmiany cudzych manifestów. Pliki: candidates.csv (88 wierszy), audit-summary.json, source-metadata-snapshot.json, history.json, README.md.
