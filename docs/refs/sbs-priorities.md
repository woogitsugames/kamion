# SBS — priorytety r4 i historia r3

Nowszy main, odczyt około 14:51: scalono ADR 0130 (abf15f9e), który zmienia sześć spornych póz. [Recenzja tej zmiany](../../artifacts/sbs-r4/review-snapshots/REVIEW-2026-11-12-s12-0130-truck-r3.md) wymaga świeżego renderu czterech stanów na main przed kompozycją i aktualizacją rejestru. Jej G3-B 6/10 RECOGNISABLE (3 słabe) dotyczy innej bazy i części kohorty; nie dodajemy tego wyniku do ocen G3-A z r4. Poniższe obrazy r4 nadal przedstawiają main 0023f39d. Przepis 15 starych prób zastąpiono przed wykonaniem; r5 ma sprawdzić scalone pozy na nowym świecie, z zachowaniem zmian Claude. Kolejny wskazany problem kamery to pitch B150280; portal, ekrany i pomost mają także odrębne problemy świata. Te informacje są priorytetami do nowej weryfikacji, nie dowodami naprawy w obrazach r4.

Stan r4, 12.11 około 13:30: bazą nowej generacji jest main 0023f39d po pakietach A+B+C. Materiały i świat zakończone bez fallbacków, import oraz pełne 168 raw gotowe na HEAD 80159a70. [Niezależny świeży przegląd](../../artifacts/sbs-r4/REVIEW-D51-BASELINE.md) wszystkich 25 par B Low-overcast daje D51 FAIL: 13 rozpoznawalnych, 11 częściowych i 1 nierozpoznawalna. Obejrzano 50 natywnych obrazów; przyszłych arkuszy 960 px jeszcze nie oceniano. Sumy są takie jak w r3, ale oceny dotyczą nowych SHA, a historia r3 i r1 pozostaje w rejestrze. Żadnej pozy C nie awansowano.

[Własny punktowy przegląd](../../artifacts/sbs-r4/FRESH-SPOT-REVIEW.md) A294859/A303305 Low-clear i High-clear potwierdza brak ostrego ukośnego klina nad prawym horyzontem w nowej wspólnej bazie. Pozostaje miękki szary pas dolnego nieba; nie utożsamiać go z dawnym twardym klinem ani blokerem D51. W 303305 nadal nie zgadza się sylwetka bloków po lewej. Ta kontrola obejmuje tylko 4 klatki: 294859 jest C, 303305 jest B.

Aktualizacja około 16:01: [niezależny ogląd pozostałych stanów](../../artifacts/sbs-r4/OTHER-STATES-VISUAL-REVIEW.md) zakończył wszystkie 75/75 B raw i 25/25 zdjęć źródłowych. Łącznie z wcześniejszym Low-overcast obejrzano wszystkie 100 B raw czterech stanów. SHA, ścieżki i roster 75 par ponownie związano z capture/request oraz zachowano dokładne bajty recenzji w ZIP. To nadal baza 80159a70 bez ADR 0130, bez nowej oceny D51 i bez oglądu przyszłych arkuszy. High ujawnia różnice LOD portali, ale nie usuwa rozbieżności projekcji, pierzei i ekranów.

## Aktualne największe odstępstwa z natywnych par r4

| Kolejność | Problem | Dowód i następny krok | Właściciel |
|---|---|---|---|
| 1 | Stacje i projekcja portali: B328135, B275528, B297817; dalej B837235, B494288, B180137 | B328135 nadal nierozpoznawalny na starej bazie. R5: świeży świat i cztery stany po ADR 0130, dwie trwałe kotwice, rozdzielenie pozy od świata. Nie uruchamiać zastąpionego przepisu 15 prób. | sbs; geometria portalu i ekranu pozostaje u właściciela świata |
| 2 | LOD portali B227953/B837235/B297817; B381800 | Ogląd trzech pozostałych stanów potwierdza pełną ramę Low zamiast ażurowej kratownicy High w pierwszych trzech kadrach. B381800 pozostaje pełny także na High. Sprawdzić po integracji 0127, na tych samych dystansach. | Claude — czytelność Low 0127 |
| 3 | Wyspa, chodnik i przejście A320326; U-3 przy B837235 | Świeża para pokazuje trawiastą wyspę zamiast zgodnej relacji chodnika, przejścia i znaków. Nie zamykać problemu samym przesunięciem tarczy. | Claude — geometria węzłów; furniture — lica i słupki; sbs — poza |
| 4 | Pierzeja B150280/B297817, częściowo B328135 | Hale i blok są obecne, lecz nie zastępują charakterystycznej zabudowy usługowej i dominant. Sprawdzić po kalibracji pozy oraz na kolejnej scalonej bazie 0126. | Claude — zabudowa |
| 5 | Najbliższe podpory i łuk A201270/A139889; duży C-9 A177786 | Dalsze filary istnieją. Niezgodna jest relacja najbliższego filara do kamery, łuku i nasypu; rozdzielić stację od geometrii. | Claude — wiadukty i węzły; sbs — poza |
| 6 | Prawy ekran i WN B367829/B494288/B180137 | Ekrany i słup są obecne. Pozostają proporcje, ciągłość i relacja do włączenia. B494288 w obu obrazach skręca w lewo; brak podstaw do dużego yaw. | furniture / Claude; sbs — poza |
| 7 | Panorama bloków A454716/A303305/A320215 i dolne niebo | Panorama nadal niezgodna, ale pomost pozostaje rozpoznawalny. Ostry klin naprawiony w dwóch kontrolowanych kadrach; miękki szary pas to dalsza jakość obrazu, nie samodzielny bloker D51. | edge / vegetation / light |

Koszt skumulowany nie jest zamknięty: [wszystkie liczniki r4](../../artifacts/sbs-r4/BUDGET-LIMITATIONS.md) pokazują względem r3 draws +0 i tris ≤+2%, lecz względem r2 Low nadal ma 38/84 wzrostów draws i już 34/84 przekroczeń +2% tris (r3: 22/84). To estymaty edytora, bez pomiaru GPU A16. Nie resetować oceny budżetu co rundę.

Kolejne cele z [recenzji pakietu C](../reports/visual/REVIEW-2026-11-12-s12-gpt-batch-c.md): edge — kolor i podział hal południowej panoramy; furniture — profil tyłu tarczy i kontrast obejm; life — odbicie otoczenia na czerni, szum płatków i prostokątny cień pod autem. Szczegółów kabiny i naczep nie oceniać z samych kadrów trasy. SBS ma najpierw sprawdzić sześć scalonych korekt na aktualnym main. Historyczny przepis 15 hipotez C nie został wykonany i pozostaje zastąpiony. Własny ogląd B150280 potwierdza hipotezę pitch jako kolejny osobny temat, bez produkcyjnej korekty i bez leczenia braków pierzei kamerą.

## Historia r3

Aktualizacja: 12.11.2026 około 11:31, gałąź gpt-sbs-r3. Źródła świata renderów z main 9874d98c; baza capture 14ccbaf1 dodaje tylko obsługę slotów i integracji. Main ma już 49a9d332 po pakietach A+B; obrazy r3 nie przedstawiają tej późniejszej bazy. Pełny render 168 raw z HEAD 62d45b92 jest gotowy. Ranking uwzględnia niezależny przegląd wszystkich 25 B Low-overcast (FAIL: 13 rozpoznawalnych, 11 częściowych, 1 nierozpoznawalny) oraz własny przegląd wszystkich 25 B Low-clear. Próby diagnostyczne nadal są C i nie poprawiają formalnego wyniku.

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

Pełna seria r3 powstała około 09:06–09:09 na źródłach ówczesnego main 14ccbaf1. Niezależny recenzent obejrzał wszystkie 25 B Low-overcast, a własny przegląd obejmuje już wszystkie 25 B Low-clear oraz wcześniejsze cztery natywne raw. Wynik formalny nowej bazy: FAIL 13/11/1; nie obejmuje akceptacji nowych prób C. Nowa poza unieważnia porównywalność trendu; każda nowa ocena D51 wymaga związania z SHA zdjęcia i renderu. C nie są usuwane z historii, ale nie liczą się jako zaliczone pary.

[Dokładny zakres świeżego przeglądu czterech klatek](../../artifacts/sbs-r3/FRESH-SPOT-REVIEW.md) i [SHA](../../artifacts/sbs-r3/fresh-spot-inspection.json). Nie jest to nowy pełny werdykt D51.



[Pełny niezależny przegląd bazy r3](../../artifacts/sbs-r3/REVIEW-D51-BASELINE.md) i [własny przegląd 25 Low-clear](../../artifacts/sbs-r3/REVIEW-LOW-CLEAR.md) zastępują częściowy zakres opisany wyżej w historycznym przeglądzie czterech klatek. Ocenę r3 trzeba odczytywać wraz z SHA w rejestrze, nie przenosić jej na inne stany światła.

## Nowsze recenzje s12 — zakres do następnych rund

Odczytano z main 49a9d332 około 11:31. [Migawka recenzji pakietu A](../../artifacts/sbs-r3/review-snapshots/REVIEW-2026-11-12-s12-gpt-batch-a.md), [pakietu B](../../artifacts/sbs-r3/review-snapshots/REVIEW-2026-11-12-s12-gpt-batch-b.md) i [SHA źródeł](../../artifacts/sbs-r3/review-source-index.json). To uwagi niezależnych recenzji innych rund, nie własny przegląd renderów nowego main. Nie zastępują powyższego wyniku D51 bazy r3.

| Dziedzina | Największy kolejny problem według najnowszego dostępnego dowodu | Granica dowodu |
|---|---|---|
| sbs | Priorytet 297817/328135, potem 275528/837235, 180137 i 494288. Dwie niezależne kotwice, bez strojenia kamery do błędu portalu lub wyspy. | Przeglądy r3 nadal nie akceptują żadnej próby C. Nowe małe próby pitch i B275528 opisane w artefaktach, po odświeżeniu main w r4. |
| vegetation | B8 czeka na pozę SBS; niezależnie można poprawiać berberys przypominający bordowe bale i mierzyć koszt. | R3 vegetation jest produkcyjnym NO-OP; odrzuconych koron nie traktować jako wdrożonej poprawy. Nie oceniać brakujących koron B297817 bez zgodnego kadru. |
| edge | Klin clear i B9 przed dalszym dopracowaniem panoramy; jaskrawe, płaskie pudła LoD1 wymagają okien, kondygnacji i materiału. | Podejrzane bloki B9 leżą wewnątrz regionu: nie dublować ich automatycznie far-fieldem. Aktualna okluzja wymaga nowego wspólnego renderu. |
| landmarks | Fazy filarów w tej samej musztardowej farbie, bez szarego pasa; sprawdzić ciemny równoległobok i odwodnienie. | Usunięcie zmyślonych schodów jest poprawą, nie zamknięciem D51. Brak najbliższej podpory przy rondzie nadal należy do geometrii Claude. |
| light | Po wspólnej kontroli klina: nocne plamy światła na jezdni, emisja głowic, halo i łuna miasta; teren mniej nasycony nocą. | Night r2 wygląda jak przyciemniony dzień. Usunięto niespójne odbicie zachodu, ale nie dowiedziono naprawy dziennego klina. GPU A16 niezmierzone. |
| truck | Lakier z odbiciem nieba i szyba bez mlecznego wyglądu; zużycie progów/błotników i krawędzi stopnia, dalej opony/felgi. | R2 poprawia czytelność kratki stopnia w makro; cały kadr z trasą pozostaje prawie bez zmiany. Nie przypisywać poprawie stopnia zaliczenia lakieru. |
| cab | Osobny skan tworzywa lub usunięcie szerokich fal tłoczenia; wytarcie kontaktowe i pasmo AO. | Ziarno r2 czyta się jak skaj, poprawa poza makro mała. Kwestie licencji i deterministyczności muszą być rozstrzygnięte przez właściciela/lidera, bez edycji tych plików przez SBS. |
| life | Felgi i ciemny bok opony LOD0, osprzęt podwozia naczepy, plandeka z lokalnymi fałdami i pasami. | R2 oddziela trzy koła w LOD1, lecz nadal ma płaskie dyski i gołą ramę. Budżetu trasy nie zastępować wynikiem makro. |
| furniture | Sylwetka słupa WN i ekranów, osadzenie U-3 oraz znaki wobec rzeczywistego nosa wyspy. | Pakiety A+B nie dają nowej recenzji tej dziedziny; podstawą pozostaje wcześniejszy dowód i świeże kadry r3. Geometrii nosa nie naprawiać samym przesunięciem znaku. |
| asphalt | Prostokątne łaty i przetarcia oznakowania jako materiał, po rozwiązaniu blokerów orientacyjnych. | Pakiety A+B nie dają nowej recenzji asfaltu; wcześniejsza ocena pozostaje historyczna. Nie używać niekwalifikowanego histogramu r3 jako albedo. |

Kolejność nadal wynika z rozpoznawalności układu, a dopiero później z materiałów i zużycia. Nowy main trzeba odświeżyć w następnej rundzie SBS. Wspólny wzrost kosztu z bazy r2 do r3 (38/84 Low draws i 22/84 tris ponad 2%) jest jawny w [ograniczeniach budżetu](../../artifacts/sbs-r3/BUDGET-LIMITATIONS.md); nie rozdzielamy go bez pomiaru na poszczególne domeny.



