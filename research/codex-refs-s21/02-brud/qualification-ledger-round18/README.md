# Jawny rejestr kwalifikacji M61 — A/B/C, obieg18

**Rozpoznana dolna granica:5 odrębnych kadrów treściowych A (z ograniczeniami poniżej),1 kadr B. Nie jest to dokładny globalny wynik projektu.** Cała unia P18+s21 pozostaje częściowo audytowana. Spośród88 rekordów P18 indywidualnie obejrzano dotąd45;43 to NOT_REVIEWED. Nie wypełniamy ich zerem i nie przejmujemy bez oglądu dawnych statusówSOURCED/OK.

Ta runda tworzy wyłącznie rejestr istniejących dowodów: **0 nowych fotografii,0 pobrań,0 żądańHTTP,0 nowych oglądówUI**. Nie zamyka20/12/6/6, nie zmienia progów i nie edytuje P18, parenta ani poprzednich obiegów. CSV jest katalogiem statusów, nie arkuszem prognoz; liczby podsumowania są policzone z jego wierszy, nie ręcznie przyjęte z wiadomości koordynatora.

## Definicje bez obniżania wymagań

| Rejestr | Wymóg | Co nie wystarcza |
|---|---|---|
| A |≥20 ŁĄCZNIE:rzeczywiste podwójne tylne drzwi potwierdzonej naczepy z widocznym brudem | Sama rdza, grafika, niepewna powłoka, brud progu bez drzwi, solówka; nie dodano doA progu1000px ani warunku ruchu |
| B |≥12 NOWYCH względem pierwotnegoM61:treśćA +≥1000px wysokości DRZWI w źródle +ruch/zaraz po trasie | Wysokość całego zdjęcia1000px, upscaling, powiększona miniatura, nowe pobranie/crop, deklaracja rozmiaru bez oglądu; stary kadrA nie staje się nowymB |
| C-zima-A i C-Europa-A |≥6 zimowych i≥6 z europejskich dróg w całości | Sam miesiąc/datowanie, adres sprzedawcy lub śnieg na nieczytelnym boku bezA |
| C-zima-B i C-Europa-B |FIX pkt8:„w tym”≥6 zimowych i≥6 europejskich W PODZBIORZE nowychB | Mały nowy zimowy kadrA niespełniającyB nie zwiększa zimowegoB; stareA nie uzupełnia nowegoB |

SOURCED [wymagania]:polecenie użytkownika; docs/owner/MISTRAL-FIXES-12.md,M61-FIX pkt8/9 iKRYTERIA; docs/reports/REVIEW-2026-11-14-s20-mistral-m61.md,kryterium3 i poprawka8. Śnieg/kolor biały nie identyfikują soli ani składu chemicznego.

## Pięć odrębnych źródeł A

| Źródło / aliasy | A | B | C i ograniczenia |
|---|---|---|---|
| P18-158 =02-009/CR7-A02, Knight |PASS_CONTENT; typ semi-trailer wprost u autora, film/wycierki na czerwonych panelach |NOT_NEW_BASELINE; także drzwi native ESTIMATED740–800px |USA źródłowo, zimowe otoczenie niepotwierdzone; brak przyrostuC |
| P18-182 =CR6-001/02-CR6-001, Western Express |PASS_CONTENT po oglądzie koordynatora pełnego oryginału i wycinków |PASS_NEW_GE1000_TRAFFIC:drzwi ESTIMATED1400–1500px, źródłowo i wizualnie ruch drogowy |USA, brak potwierdzonej zimy. To JEDNO zdjęcie, mimo P18 iCR6 |
| P18-183 =CR7-A01/02-CR7-A01, Premier |PASS_CONTENT:lokalny szarobrunatny film lewego pola |FAIL_GE1000_AVAILABLE:root ESTIMATED900–950px, obieg13 bliski910–970; oba<1000 |USA, brak potwierdzonej zimy; nie podciągamy do1000 |
| EUR15-A01, Krone OLX1110839344 |PASS_LIMITED_CONTENT_PEER:lekki MIEJSCOWY film/smugi, nie jednolity brud całych pól; pełny1/8 potwierdza naczepę na podporach z3osiami |FAIL:bitmapa539×700, same drzwi mniejsze; zaraz po trasieUNVERIFIED |Brak zimowego kontekstu. Przybiernów to lokalizacja oferty, nie dowód europejskiej drogi. Peer niezależny, ale jawnie NIEŚLEPY |
| WW17-A01, RoadTour |PASS_CONTENT_SOURCE_DEPENDENT_PEER:2skrzydła i dolny film/smugi; typ semi-truck i Photo deklarowane przez publikatora |FAIL_GE1000_AVAILABLE:exactCDN1290×1364, drzwi ESTIMATED780–850px |C-zima-A:1 z ograniczeniem źródłowego podpisu lodu i obserwacji. KrajUNVERIFIED, Europa niepotwierdzona. EXIF/ekspozycja vs klatka filmuUNVERIFIED; zafarb/optyczne zamglenie nie są mapą brudu |

Pierwsze3 są potwierdzonym rdzeniem treściowym; Krone ma ograniczoną lekką treść, RoadTour warunkową proweniencję źródłową. W ledgerze pięć ma różne statusyPASS, aby nie zgubić jakości dowodu. **A5 zawiera oba jawne ograniczenia; bez tych dwóch kategorii rdzeń wynosi3.** Nie prezentować5 jako pięciu równie silnych zdjęć do masek brudu.

Dokładne pięć kluczy sprawdzono niezależnie z URL/photoID i istniejącymi plikami dowodów w five-source-dedup-check.json. Przykładowo ID pliku OLXmpwsrr1ixzzq-PL iWix609dc9_bae2413ee20f49e984a094efa83e2f3a różnią się od trzech plikówCommons. Wiersze pełnego obrazu, galerii, miniatury i wycinka nie tworzą kolejnych źródeł.

## Co pozostaje poza A

- P18-121/02-008:brud i para drzwi potwierdzone, lecz autor mówi long lorry; naczepa vs solówka/drawbar UNVERIFIED. Źródłowego semi-trailer w opisie P18-158 nie odbierano ani nie zastąpiono samym obrazem.
- Harold Flickr230839170:film jest widoczny, typ naczepy UNVERIFIED — pozaA.
- Bill Stilwell4433883530:jasna siatka/smugi, mechanizm osad vs powłoka i typUNVERIFIED — pozaA.
- Posti003:typ/Finlandia/śnieg potwierdzone; mechanizm siatkiUNVERIFIED, nie zamieniamy jej w pewny brud. PozaA iC, mimo zimowego kontekstu.
- EVcargo7602388:geometrycznie duży tył prawdziwego articulatedlorry na mokrej drodze; brud versus wycieranie/grafika/powłokaUNVERIFIED. Sam próg geometryczny nie dajeA/B.
- Pozostałe PENDING zachowują indywidualne powody w ledger.csv. NOT_REVIEWED pozostaje nieustalone, a nie odrzucone.

## Dolne granice C

Dla rozpoznanych źródeł: **C-zima-A=1(source-dependent RoadTour), C-Europa-A=0 potwierdzonych, C-zima-B=0 potwierdzonych, C-Europa-B=0 potwierdzonych**. To liczby zaakceptowanych w aktualnym rejestrze, NIE dowód braku innych zimowych/europejskich w nieobejrzanej bazie. Krone nie zwiększaC, a Posti/mały131/śnieżne104–105 nie zwiększająC przez brak treściA. Nie identyfikujemy chemicznej soli z bieli.

## Normalizacja i zakres

ledger.csv zawiera108 jednostek źródłowych/kontrolnych unii manifestów, alias-index.csv128 wierszy aliasów. P18 ma88 rekordów,87 kluczyURL (144/159 wskazują ten sam plik). Dodatkowo139/153 pokazują ten sam ICR i prawdopodobny crop tego samego zdjęcia; zgodnie zFIX liczone raz:86 jednostekP18. Zachowano oba URL i obaID dla odtwarzalności. Nie twierdzimy, że wszystkie108 to odrębne zweryfikowane fotografie:nieobejrzane zdalne źródła mogą mieć dalsze duble, dlatego liczba jednostek jest inwentarzem, nie wynikiemA.

Normalizacja:CommonsFile tytuł odkodowany zpercent/underscore na spacje iUnicodeNFC; Flickr wedługphotoID niezależnie od handle; GettyphotoID; OLXfileID niezależnie od wariantu wielkości; WixmediaID niezależnie od wariantu; pozostałe publiczne ścieżkiCDN bez querytracking. Dwa różne zdjęcia jednego pojazdu co do zasady pozostają osobnymi źródłami, poza jawną regułąFIX139/153. Crop/miniatura tego samego zdjęcia nigdy nie jest kolejnym kadrem.

new_vs_original75 rozróżnia NO(starybaseline), YES_P18_FIX_APPEND176_188(dopiskiP18 względem staregoM61) iNO_CANONICAL_MATCH_IN_ORIGINAL75(dla odrębnych kluczyS21; pełna nowość wizualnaUNVERIFIED). Nie przypisuje pierwszeństwa odkrycia. P18-182 było zacommitowane wcześniej niż naszCR6, ale to czas commitu, nie pierwszego znalezienia; źródłowy history.json pozostaje w obiegu13.

Każdy verdict ma existing_evidence_refs do konkretnegoCSV+ID, źródłowych metadanych, audytu lub peer/koordinatora. Ścieżki są względem02-brud; #ID oznacza identyfikator wiersza, nie numer strony. original/local image paths pozostają osobno. Rejestr nie wymaga nowych kopii fotografii. Summary JSON jest snapshotem policzonym ze statusówCSV; każda późniejsza zmiana werdyktu wymaga ponownego przeliczenia, nie zmiany samych liczb.

manifest.csv ma1wiersz dokumentacyjny koordynatora, ponieważ ta runda nie zbiera nowych kadrów. Artefakty:ledger.csv,alias-index.csv,five-source-dedup-check.json,summary.json,README.md. Bezgit i cudzych edycji. Narzędzie dalszej selekcji, nie zamknięcie progów.

Snapshot23:31 poprzedza włączenieWW17do głównego manifestu23; dodatkowy aliasmainWW17 nie oznacza nowego kluczaWix/zdjęcia. Koordynator sprawdził108unikalnychkluczy oraz5werdyktówA/1B zCSV, bez dopisywania własnych nowych oglądów do audytu.
