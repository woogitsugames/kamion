# SBS — priorytety odstępstw od zdjęć, r3

Aktualizacja: 12.11.2026 około 02:43, gałąź gpt-sbs-r3. Baza main 9874d98c, merge 31988772. Jest to ranking wejściowy z recenzji i obejrzanych dowodów ADR 0125, przed własnym renderem nowego świata r3. Nie należy czytać go jako nowego wyniku bramki ani dowodu, że stare braki nadal występują po scaleniach. Po renderach każda pozycja otrzyma potwierdzenie albo zmianę statusu.

Kryterium D51: rozpoznanie miejsca przez kierowcę znającego trasę. Niebo, ekspozycja, odcień trawy i kosmetyka materiałów nie blokują same w sobie. Nie szeregujemy świata według błędu histogramu. Metryki r2 są porównywalne tylko dla trzech Low-clear i nie zastępują oceny układu.

## Kolejność sprawdzenia i napraw rozpoznawalności

| Kolejność | Problem i kadry | Właściciel | Co już wiadomo | Najbliższy dowód rozstrzygający |
|---|---|---|---|---|
| 1 | Pozy G3-B: 275528, 837235, 328135, 297817, 180137, 494288 | sbs | Recenzja 0125 wskazuje pozę jako główny bloker; sześć par po 0125 obejrzano. Nowy portal istnieje. | Na nowej bazie warianty pozy, zgodność portalu i drugiej trwałej kotwicy; C do niezależnego przeglądu. |
| 2 | Wysepka, D-3/D-6, przejście i kostka: A320326 | Claude — węzły 0123; furniture tylko znaki | 0125 zgłasza stale: jezdnia zajmuje obszar wysepki. Nie leczyć tego przesuwaniem samego znaku. | Świeży kadr A320326 oraz geometria nosa względem ortofoto. |
| 3 | Pierzeja handlowo-usługowa: B150280, B297817, częściowo B328135 | Claude — zabudowa 0126 | Na r2 są hale i blok, brak charakterystycznej czerwonej pierzei; nie jest to całkowicie pusty teren. Prace 0126 nie są dowodem efektu na naszej bazie. | Ten sam kadr po potwierdzeniu pozy i integracji zabudowy; bryły, kolor dominujący i rytm, bez marek. |
| 4 | Podpory przy rondzie: A201270 i A139889 | Claude — wiadukty/węzły 0123 | R1/r2 mają pusty prześwit; lider zgłosił filary w gałęzi 0123, nie wolno zakładać ich braku po przyszłym merge. | Dwa świeże kadry na faktycznie scalonym świecie, w tym najbliższa podpora. |
| 5 | Czytelność ekranów i słupa WN: B367829, B494288, B180137 | furniture / Claude 0125; sbs osobno poza | Obiekty istnieją po 0125. Lewy ekran B494288 usunięty; problemem pozostaje sylwetka i ciągłość prawego, a nie rzekomy brak obu. | Low-overcast i Low-clear; po potwierdzeniu pozy porównać masywność słupów, dolny pas i płaszczyznę szkła. |
| 6 | LOD kratownicowej bramownicy: B837235, B381800, B297817 | Claude — oznakowanie/portal | Recenzja 0125: z daleka pełna szara rama zamiast czytelnej kratownicy; bliska geometria jest. | Te same dystanse w Low i High, osobne draws instancji, bez awansu kadru na podstawie samego zbliżenia. |
| 7 | Nos wyspy/szewron: B381800, B837235; znak C-9 A177786 | Claude — geometria węzłów; furniture — znak; sbs — poza | Możliwy snap szewronu do niewłaściwego nosa; A177786 ma także niepewną odległość kamery. | Co najmniej dwie kotwice; sprawdzić osobno geometrię nosa i pozę, nie przesuwać obu naraz. |
| 8 | Nasyp/bariera łuku: A281855/A397016/A177786/A178689/A201270/A139889 | Claude — węzły/teren | Historyczna recenzja wskazuje kostkę zamiast kruszywa i brak szyny. W 0123 trwają poprawki; stan nowego renderu oczekuje. | Prześwit pod mostem i łuk w świeżej parze, bez sugerowania zmian tekstur jako zamknięcia geometrii. |
| 9 | Drzewa i panorama: B297817; A454716/A303305/A320215 | vegetation / edge | R1/r2: brak rytmu dużych drzew, las zamiast bloków. R1 domen scalone, wymagają sprawdzenia wspólnego stanu. | Sylwetki w tych samych kadrach, po kalibracji B297817. |
| 10 | Koniec świata: DK8 i wyloty; klin tła A294859/A303305 clear | edge + light | Recenzje batch1/batch2 wskazują bariery końca mapy i odsłonięty szary klin po nowych chmurach. Klin to artefakt geometrii, nie sam kolor nieba. | Nowy wspólny Low-clear i High-clear; widocznego klina nie używać jako zaliczonego dowodu clear. |

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

Do czasu nowych renderów r3 wszystkie stwierdzenia o obecnej bazie mają status oczekuje potwierdzenia. Nowa poza unieważnia porównywalność trendu; każda nowa ocena D51 wymaga związania z SHA zdjęcia i renderu. C nie są usuwane z historii, ale nie liczą się jako zaliczone pary.
