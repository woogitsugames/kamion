# SBS — priorytety odstępstw od zdjęć, r3

Aktualizacja: 12.11.2026 około 10:15, gałąź gpt-sbs-r3. Źródła świata z main 9874d98c; aktualny main 14ccbaf1 dodaje tylko obsługę slotów i integracji. Pełny render 168 raw z HEAD 62d45b92 jest gotowy. Ranking uwzględnia niezależny przegląd wszystkich 25 B Low-overcast (FAIL: 13 rozpoznawalnych, 11 częściowych, 1 nierozpoznawalny) oraz własny przegląd wszystkich 25 B Low-clear. Próby diagnostyczne nadal są C i nie poprawiają formalnego wyniku.

Kryterium D51: rozpoznanie miejsca przez kierowcę znającego trasę. Niebo, ekspozycja, odcień trawy i kosmetyka materiałów nie blokują same w sobie. Nie szeregujemy świata według błędu histogramu. Metryki r2 są porównywalne tylko dla trzech Low-clear i nie zastępują oceny układu.

## Kolejność sprawdzenia i napraw rozpoznawalności

| Kolejność | Problem i kadry | Właściciel | Co już wiadomo | Najbliższy dowód rozstrzygający |
|---|---|---|---|---|
| 1 | Pozy G3-B: 275528, 837235, 328135, 297817, 180137, 494288 | sbs | Recenzja 0125 wskazuje pozę jako główny bloker; sześć par po 0125 obejrzano. Nowy portal istnieje. | Na nowej bazie warianty pozy, zgodność portalu i drugiej trwałej kotwicy; C do niezależnego przeglądu. |
| 2 | Wysepka, D-3/D-6, przejście i kostka: A320326 | Claude — węzły 0123; furniture tylko znaki | Nowe Low-overcast i Low-clear potwierdzają brak zgodnego układu wysepki, chodnika i przejścia. Nie leczyć tego przesuwaniem samego znaku. | Świeży kadr A320326 oraz geometria nosa względem ortofoto. |
| 3 | Pierzeja handlowo-usługowa: B150280, B297817, częściowo B328135 | Claude — zabudowa 0126 | R3 w obu stanach Low pokazuje hale i blok, brak charakterystycznej czerwonej pierzei; nie jest to całkowicie pusty teren. Prace 0126 nie są dowodem efektu na naszej bazie. | Ten sam kadr po potwierdzeniu pozy i integracji zabudowy; bryły, kolor dominujący i rytm, bez marek. |
| 4 | Podpory przy rondzie: A201270 i A139889 | Claude — wiadukty/węzły 0123 | R3 Low-overcast A201270/A139889 nadal pokazuje brak najbliższych podpór. Tablica z nazwą ronda już jest. Nie przenosić tego wyniku na przyszłe scalenie 0123 bez nowego renderu. | Dwa świeże kadry na faktycznie scalonym świecie, w tym najbliższa podpora. |
| 5 | Czytelność ekranów i słupa WN: B367829, B494288, B180137 | furniture / Claude 0125; sbs osobno poza | Obiekty istnieją po 0125. Lewy ekran B494288 usunięty; problemem pozostaje sylwetka i ciągłość prawego, a nie rzekomy brak obu. | Low-overcast i Low-clear; po potwierdzeniu pozy porównać masywność słupów, dolny pas i płaszczyznę szkła. |
| 6 | LOD kratownicowej bramownicy: B837235, B381800, B297817 | Claude — oznakowanie/portal | Recenzja 0125: z daleka pełna szara rama zamiast czytelnej kratownicy; bliska geometria jest. | Te same dystanse w Low i High, osobne draws instancji, bez awansu kadru na podstawie samego zbliżenia. |
| 7 | Nos wyspy/szewron: B381800, B837235; znak C-9 A177786 | Claude — geometria węzłów; furniture — znak; sbs — poza | Możliwy snap szewronu do niewłaściwego nosa; A177786 ma także niepewną odległość kamery. | Co najmniej dwie kotwice; sprawdzić osobno geometrię nosa i pozę, nie przesuwać obu naraz. |
| 8 | Nasyp/bariera łuku: A281855/A397016/A177786/A178689/A201270/A139889 | Claude — węzły/teren | Świeży A139889 Low-overcast potwierdza brak bariery łuku i różny nasyp. Wynik dotyczy naszej bazy main 14ccbaf1, nie niescalonych poprawek 0123. | Prześwit pod mostem i łuk w świeżej parze, bez sugerowania zmian tekstur jako zamknięcia geometrii. |
| 9 | Drzewa i panorama: B297817; A454716/A303305/A320215 | vegetation / edge | R3 A303305 clear w obu tierach nadal ma drzewa zamiast wyraźnej grupy bloków po lewej. Low-clear A454716/A320215 potwierdza różnicę panoramy. W B297817 rytm drzew jest inny, ale najpierw należy rozstrzygnąć pozę. | Sylwetki w tych samych kadrach, po kalibracji B297817. |
| 10 | Koniec świata: DK8 i wyloty; klin tła A294859/A303305 clear | edge + light | Klin nad halami potwierdzony w świeżym A303305 Low-clear i High-clear. Bariery końca mapy nadal opierają się na recenzji batch1 i wymagają nowej kontroli. | Nowy wspólny Low-clear i High-clear; widocznego klina nie używać jako zaliczonego dowodu clear. |

## Zadania dla dziesięciu dziedzin

| Dziedzina | Największy następny temat z recenzji | Miejsce w kolejce i ograniczenie dowodu |
|---|---|---|
| sbs | Sześć pozy G3-B, kalibracja C i brak zatwierdzonego początku 300 m | Priorytet 1; nie zmieniać świata w celu dopasowania kamery. W r2 API nie dostarczyło nowego kandydata do 300 m. |
| furniture | Sylwetka słupa WN i ekranów na Low; kontrola znaku przy B150280 | Priorytet 5, współpraca z właścicielem 0125; bariery i geometria nosa należą do Claude. |
| edge | Bariery końca mapy, klin far-field, skyline bloków | Priorytety 9–10; po merge light i edge wymagana wspólna kontrola, nie suma oddzielnych zapewnień. |
| vegetation | Rytm drzew Putry i pasa B297817; berberys jako bordowe bale | Drzewa: priorytet 9; kształt krzewów dalej jako jakość obrazu. Nie podmieniać D51 oceną odcienia trawy. |
| light | Klin wspólnie z edge, dalej zmierzch i spójność ekspozycji | Klin: priorytet 10; niebo i ekspozycja same nie blokują D51. Nowe koszty fragmentu wymagają pomiaru lidera na A16. |
| asphalt | Łaty jako prostokątne naklejki, przerywana zebra kontrolna | Jakość obrazu po blokerach układu. Ślady kół r1 poprawione; nie przypisywać samemu SBS wyniku albedo. |
| landmarks | Nierówne tuje i remiza, dalsza czytelność spodu wiaduktu | Kosmetyka remizy po D51. Brak podpory priorytetu 4 należy do Claude, nie do korekty materiału filara. |
| cab | Prawy wide-angle zasłonięty kanałem, kremowa bryła w przednim lusterku | Funkcja usunięcia wnętrza z lusterek r1 zaliczona; wygląd i okluzja nadal częściowe. Nie liczyć widoku głównego jako kosztu RT. |
| truck | Materiały lakieru/szyby z kabiny i nocne moduły lamp | Zmiana r1 wizualnie mała, DRL bez przepału. Brak nowego dowodu telefonu; nie nadawać wyższego miejsca niż brakom orientacyjnym trasy. |
| life | Brud tyłu i felg, samochody za czyste, czerń w słońcu | Oderwane plamy progów r1 naprawione; nie przywracać ich dla większej różnicy pikseli. Życie statyczne nie blokuje D51. |

## Stan dowodów i źródła

- [Formalny pełny D51 r1](../reports/visual/REVIEW-2026-11-11-s11-sbs-r1-D51.md): 25 B Low-overcast, FAIL 12/11/2. To ocena historyczna.
- [Recenzja 0125](../reports/visual/REVIEW-2026-11-12-s11-0125.md): G3-B 2 rozpoznawalne, 7 częściowych, 1 nierozpoznawalny, nadal FAIL. Inna epoka niż r1/r2; nie dodawać tych liczb do starego wyniku G3-A jako nowej pełnej oceny.
- [Recenzja life/vegetation/cab/edge](../reports/visual/REVIEW-2026-11-12-s11-gpt-r1-batch.md) oraz [asphalt/landmarks/light/truck](../reports/visual/REVIEW-2026-11-12-s11-gpt-r1-batch2.md): tematy dla dziedzin, brak pomiaru wspólnego A16.
- [Zamknięty raport SBS r2](../../artifacts/sbs-r2/REPORT.md), [audyt](../../artifacts/sbs-r2/AUDIT.json), [przegląd sześciu par 0125](../../artifacts/sbs-r2/PRE-R3-VISUAL.md), [HTML](../../artifacts/sbs-gate3/latest/index.html).

Pełna seria r3 powstała około 09:06–09:09 na źródłach aktualnego main 14ccbaf1. Niezależny recenzent obejrzał wszystkie 25 B Low-overcast, a własny przegląd obejmuje już wszystkie 25 B Low-clear oraz wcześniejsze cztery natywne raw. Wynik formalny nowej bazy: FAIL 13/11/1; nie obejmuje akceptacji nowych prób C. Nowa poza unieważnia porównywalność trendu; każda nowa ocena D51 wymaga związania z SHA zdjęcia i renderu. C nie są usuwane z historii, ale nie liczą się jako zaliczone pary.

[Dokładny zakres świeżego przeglądu czterech klatek](../../artifacts/sbs-r3/FRESH-SPOT-REVIEW.md) i [SHA](../../artifacts/sbs-r3/fresh-spot-inspection.json). Nie jest to nowy pełny werdykt D51.



[Pełny niezależny przegląd bazy r3](../../artifacts/sbs-r3/REVIEW-D51-BASELINE.md) i [własny przegląd 25 Low-clear](../../artifacts/sbs-r3/REVIEW-LOW-CLEAR.md) zastępują częściowy zakres opisany wyżej w historycznym przeglądzie czterech klatek. Ocenę r3 trzeba odczytywać wraz z SHA w rejestrze, nie przenosić jej na inne stany światła.
