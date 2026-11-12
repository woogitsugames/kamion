# Stan furniture r3

Runda2 zamknięta5d7ff5c9, artifacts skopiowane do main:1908 plików,4,249GB,
robocopy exit1. Ta sama lokalizacja worktree, gałąźgpt-furniture-r3 z r2.
Scalono main889201d5 do tej gałęzi, bez merge do main/push.
Konfliktujące generatedJSON/GLB orazprops_meta przyjęto z main do regeneracji.
materials.py iLICENSES zachowują oba addytywne dopiski; fabrykaPBR połączyła się
bez konfliktu. Kod r2 nie wymaga ponownych zmian do rozpoczęcia baseline.

Zakresr3:przystanki,wiaty,kosze,słupki według Mapillary, bez barier drogowych.
Referencje przygotowane w artifacts/furniture-r2/24h/bus-reference-preview,
shortlista zawiera autorów/licencje/hashe. Czerwona wiata przy5802408812
potwierdzona zdjęciami2018 i2024; druga przyFabryceDywanów widoczna w2019.
Brak tagu shelter/bin nie dowodzi braku obiektu; brak widoczności zdjęcia również.

NASTĘPNY KROK:przygotować baseline po merge (cachePBR jeżeli nieaktualny,
build_world w heavyOwner gpt-furniture-r3, import/rendery w UnityOwnergpt-furniture),
potem poprawić największe udokumentowane odstępstwo wiaty. WIP po każdym kroku.

2026-11-12T11:01:04.0365756+01:00: przygotowano helpery r3 z identyfikatorem artefaktówr3 i właścicielemheavy bieżącej gałęzi. Przed baseline sprawdzeniecachePBR:nieaktualnychplikówMedium=0. Baseline kolejnoPBR,world,snapshot,import,220 kadrówclear/overcast. Brak nowych zmian geometrii przed baseline.

2026-11-12T11:02:26.9638208+01:00: korekta pipeline:cachePBRMedium aktualny(0stale), więc wycofano wyłącznie własny oczekujący etapPBR przed rozpoczęciem (PID68624/72788/49776, brak dzieci pracyPython). Nie przebudowywać bez potrzeby. Baseline wznowiony odworld; żaden generator nie był przerwany. Sloty cudzych właścicieli nietknięte.

2026-11-12T11:03:05.7729976+01:00: oprava usunięcia etapuPBR:poprzednia zamiana tekstowa nie pasowała do końców linii. Ponownie zatrzymano tylko własne procesy oczekujące, bez pracyPython, usunięto obie linie etapupbr i jawnie sprawdzono ich brak. Właściwe wznowienie odworld następuje teraz.

2026-11-12T11:04:47.8512498+01:00: przygotowano mały helper kamer wiat z wygenerowanych instancji, uruchamiany po zakończeniu world przed importem baseline. Cztery kadry(front/corner dla dwóch potwierdzonych referencjami przystanków) są WORKING_VALUE, nie dopasowaniem zdjęcia. Zachowuje55 dotychczasowych kamer; docelowo59×4=236 baseline. Nie uruchamiano helpera na starych instancjach przed przebudową świata.

2026-11-12T11:06:14.7676534+01:00: obejrzano crop450px referencji2024:potwierdzony czerwony szkielet,szkło i profil dachu; zapisano OBSERVATIONS z ograniczeniami metrycznymi i zakazem globalnego kolorowania wszystkichwiat. Prototyp produkcyjny nadal niezmieniony; czekamy baseline po merge.

2026-11-12T11:09:20.2467484+01:00: dodatkowa referencjaWodociągi983799980108126 obejrzana≤960, odrzucona jako dowód rodziny wiaty z powodu niewystarczającej widoczności. Bez rozszerzania zmian na wszystkie przystanki. Baselineworld nadal oczekuje w heavy; proces65664 potwierdzony.

2026-11-12T11:19:06.9450335+01:00: heavy world before; sukces=True; slot gpt-furniture-r3 zwolniony. NASTĘPNY KROK: sprawdzić log i kontynuować walidację rundy.

2026-11-12T11:20:39.6922644+01:00: world baseline zakończony510,1s,64GLB,479MiBHigh/150MiBLow, brakfallback=True. Geometrysnapshot czeka naheavy. Mały helperJSON przygotował59 kamer, w tym4zbliżenia wiat; pochodzenie/hash instancji zapisano. Pozycje i powiązanie najbliższego źródła nadalWORKING_VALUE do obejrzenia renderów.

2026-11-12T11:20:55.9543893+01:00: doprecyzowanie liczbykamer:plik zawiera11 własnych wpisów(7z r2+4wiaty); oczekiwane59 obejmuje również kamery sceny, musi zostać potwierdzone logiem renderera. Źródła przystanków mają odległość1,06m i1,59m od wybranych instancji. Nie traktować11 wpisów jako pełnej liczby kadrów ani59 jako już wyrenderowanych.

2026-11-12T11:22:46.0832558+01:00: heavy geometry before; sukces=True; slot gpt-furniture-r3 zwolniony. NASTĘPNY KROK: sprawdzić log i kontynuować walidację rundy.

2026-11-12T11:24:14.6230225+01:00: Unity import before Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T11:24:48.1357883+01:00: Unity render before Low clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T11:25:15.0764235+01:00: Unity render before Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T11:25:59.7451223+01:00: Unity render before High clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T11:26:17.3199219+01:00: import baselineOK,6833payloady przed zmianą zapisane. Low-clear iLow-overcast po59PNG. Obejrzano4zbliżeniaLow-clear(front/corner obu wiat):potwierdzony płaski dach, ciemne nieprzezroczyste panele i osadzenie na trawie obok chodnika. Zlecono niezależną ocenę tych4widoków i referencji450px; nie zmieniać cudzej nawierzchni/budynków. Highbaseline trwa. Modelr3 nadal niezmieniony.

2026-11-12T11:26:32.5077208+01:00: Unity render before High overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T11:27:10.3131906+01:00: baseline kompletny:236PNG,po59Low/High×clear/overcast,statystyki powiązaneSHA256. Zapisano manifest/props/QA przed zmianąr3 i własne produkty generatora. Efekty uboczne raportówfar-field/wiaduktu przywrócono. Obejrzano4zbliżeniaLowclear; niezależny przegląd w toku. NASTĘPNY KROK:korekta potwierdzonych rodzin wiat, z osobną oceną osadzenia i pełnym budżetem kamer.

2026-11-12T11:27:33.7948057+01:00: niezależny przegląd4/4 zbliżeń potwierdzaP1:skrzyniowy odczyt, szkło/rama i dach;P2:ciężki front/ławka. Czerwony wariant tylko w2potwierdzonych lokalizacjach, bez wymyślonej platformy. Budżet wymaga pomiaru. NASTĘPNY KROK:implementacja własnego wariantu wiaty po kompletnym baseline162214c3.

2026-11-12T11:31:09.8364952+01:00: kandydat1:własny czerwony prototyp tylko dlaOSM5802408812/5802408814,przejrzyste panele,łukowy zamknięty dach,5podpór bez środkowego słupa wejścia i2nogi ławki. Rama/dach mają wspólny slot; kolizja i pozycje zachowane. Generic21wiat bez zmian; zachowano kotwicefab/litter i seedźródeł. Nowe3sloty prototypu nie dowodządraws+0 po podzialeinstancji:pełny pomiar236kadrów wymagany. Dodano pojedynczy plik testów geometrii/kolizji/wyboru źródeł, do uruchomienia w heavy.

2026-11-12T11:33:13.3973994+01:00: przygotowano serialny candidate.ps1:czeka na terminalny testPID20900 i10PASS,zanim pozyskaheavy do world; następniegeometry,import i236kadrów. Równoległe ciężkie zadania tego samego właściciela wykluczone. ADR zachowuje otwartybudżet i ograniczenie starejkolizji. NASTĘPNY KROK:wyniktestów/kodreview, potemgenerator.

2026-11-12T11:35:04.5700246+01:00: naprawiono zgłoszoną przezreviewera szczelinę dach–podpory; wysokości słupków interpolują spód dachuLow/High, bez nowychtris/slotów. Wierzch ograniczono do zastanego2,60m zamiast2,69m. Regresja jest w istniejącym teście geometrii(liczbaprób10). Test nadal oczekiwał w heavy przed poprawką. Ryzyka mlecznego szkła/sortowania pozostają do renderu; budżet niepotwierdzony.

2026-11-12T11:37:39.1635784+01:00: przygotowano dokładne liczniki bazoweLow(clear/overcast) i porównywarkę czterech wariantówr3. Własny lokalnyPAUSE_UNITY blokuje przyszły import/renderkandydata na czas dwóch prób; nie dotyka slotów/markerów innych właścicieli. Każda próba pobieraUnityOwnergpt-furniture i zwalnia wfinally. Liczniki sąCPU, nieGPU. TestPython nadal w kolejceheavy.

2026-11-12T11:38:08.3595509+01:00: preflight licznika zatrzymał próbę przed Unity:tekstowe kopiowanie dodało końcowy newline doC#, więc hash różnił się od własnego istniejącego diagnostyka r2. Skopiowano źródło bajtowo i potwierdzono zgodnośćSHA256 z celem; kod bez zmian. Zachowano log nieudanej kontroli. Ponowne uruchomienie tej samej próby jest teraz bezpieczne; marker własny odtworzony.

2026-11-12T11:38:35.8684391+01:00: dokładny licznik CPU before Low clear; sukces=True, slot Unity zwolniony. NASTĘPNY KROK: pozostałe warianty i porównanie przed/po, bez deklaracji czasu GPU.

2026-11-12T11:39:00.7749909+01:00: dokładny licznik CPU before Low overcast; sukces=True, slot Unity zwolniony. NASTĘPNY KROK: pozostałe warianty i porównanie przed/po, bez deklaracji czasu GPU.

2026-11-12T11:39:23.1284410+01:00: dokładne liczniki bazowe Low zakończone: 118 kadrów, po 59 clear i overcast. Wszystkie runner/frozen/floors zgodne; proof SHA256 zapisane. Własny PAUSE_UNITY usunięty w finally, slot Unity zwolniony. Test pliku shelters nadal czeka na heavy i rezerwację gpt-sbs-r3. NASTĘPNY KROK: wynik 10 prób, generator kandydata i porównanie z bazą, bez powtarzania tych dwóch udanych prób Unity.

2026-11-12T11:56:18.0780855+01:00: szybka kontrola diff --check względem baseline 162214c3 zakończyła się kodem 0. Zmienione źródła produktu ograniczają się do props.py, furniture.py, fab_details.py, addytywnego materials.py oraz własnego pliku testów. Nie zmieniono roads, overrides, barier ani plików Claude. Nie zastępuje to oczekujących testów i pomiarów renderu.

2026-11-12T11:56:36.7394836+01:00: heavy focused candidate1; sukces=True; slot gpt-furniture-r3 zwolniony. NASTĘPNY KROK: sprawdzić log i kontynuować walidację rundy.

2026-11-12T11:56:58.8857809+01:00: pojedynczy plik test_furniture_shelters_0120.py: 10 passed w 0,27 s. Weryfikuje zakres wyboru źródeł, niezmienną kolizję, przejście, połączenie słupków z dachem oraz sloty prototypu. Nie dowodzi budżetu sceny. Slot testów zwolniony; generator after1 czeka w aktualnej kolejce heavy (queue ahead=7), bez omijania kolejności. NASTĘPNY KROK: generator, geometry, import i 236 renderów; kod kandydata zamrożony.

2026-11-12T11:58:19.0427891+01:00: przygotowano osobne dwa kadry przeciwnego narożnika wiat do kontroli szkła. Ich plik kamer i katalogi before-side/after-side nie zmieniają 59 kamer ani dokładnych liczników budżetowych. Własny side-render omija wyłącznie swój lokalny marker harmonogramu; nadal pobiera ten sam wymagany slot Unity. Przyszły import kandydata czeka do zakończenia tej osobnej próby bazowej.

2026-11-12T11:58:51.9886932+01:00: Unity side-render before-side Low clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T11:59:13.6024542+01:00: Unity side-render before-side Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T11:59:34.9064290+01:00: Unity side-render before-side High clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T11:59:56.5097836+01:00: Unity side-render before-side High overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T12:00:34.0683532+01:00: osobna próba before-side kompletna: 8 PNG, po 2 dla Low/High i clear/overcast. Root obejrzał dwa podglądy przeciwnego narożnika (Low-clear Anders i High-overcast Factory), potwierdzając skrzyniowy odczyt starego modelu. Pozostałe 6 plików zapisane, bez deklaracji ich oględzin. Nie zmienia to 236 kadrów budżetowych. Własny marker usunięty, slot Unity zwolniony; generator nadal w kolejce heavy. Po imporcie kandydata odtworzyć side-captures.ps1 -Phase after-side.

2026-11-12T12:12:06.0723008+01:00: zapisano bazę audytu instancji z 64 małych plików JSON: 23 wiaty, 0 nowych czerwonych wariantów. Przed odczytem potwierdzono SHA256 każdego pliku względem zamrożonego baseline. Audyt po generacji ma wykazać wyłącznie zmianę prototypu dwóch wybranych wiat oraz identyczność wszystkich pozostałych danych instancji. To nie jest pomiar geometrii ani budżetu. Generator nadal czeka w kolejce heavy. NASTĘPNY KROK: po generacji uruchomić audit_shelter_instances.py after.

2026-11-12T12:19:39.8641147+01:00: przygotowano post-candidate.ps1, który czeka na rzeczywisty koniec procesu candidate.ps1, odrzuca niekompletne 236 kadrów i nieoczekiwane zmiany instancji, a dopiero potem uruchamia liczniki Low i 8 osobnych kadrów narożników. Nie uruchamia pełnego pytest ani generatora. Każdy krok Unity używa wymaganej blokady. Wynik nadal oczekuje na generator w kolejce heavy.

2026-11-12T12:25:55.6356900+01:00: doprecyzowano audyt JSON: eksporter sortuje instancje według prototypu, więc zmiana nazwy legalnie zmienia kolejność wierszy. Porównywane są pełne multizbiory instancji w każdym chunku, z zachowaniem duplikatów i wszystkich pól; nie ignoruje się pozycji ani innych wartości. Bazę przeliczono wyłącznie po tej zmianie metody i ponownie potwierdzono wszystkie źródłowe SHA256. Generator nadal w kolejce; źródła produktu bez zmian.

2026-11-12T12:30:59.4484674+01:00: generator otrzymał heavy i rozpoczął pracę; zapisano pomocnik preview_shelter_frame.py do pojedynczego interaktywnego podglądu PNG, maksymalnie 3 MP wejścia i 960 px wyjścia, priorytet IDLE. Nie uruchamia batchu ani generatora. Umożliwia obejrzenie szkła od razu po pierwszym renderze, zanim zakończy się cała seria. NASTĘPNY KROK: wynik generatora i kontrola kandydata.

2026-11-12T12:37:32.6545950+01:00: heavy world after1; sukces=True; slot gpt-furniture-r3 zwolniony. NASTĘPNY KROK: sprawdzić log i kontynuować walidację rundy.

2026-11-12T12:39:42.2388754+01:00: generator after1 zakończony w 546,9 s, 64 GLB, bez fallback=True w logu. Audyt JSON: 64 identyczne znormalizowane multizbiory instancji; 23 wiaty, dokładnie dwa wybrane czerwone warianty, pozycje i wszystkie pozostałe pola bez zmian. Przygotowano wczesny podgląd czterech kamer Low-clear podczas kolejki kontroli geometrii. Lokalny marker zatrzyma tylko własny standardowy import; bypass dotyczy wyłącznie tego markera, nigdy slotu maszyny. NASTĘPNY KROK: wczesny import/render i oględziny, potem pełna walidacja.

2026-11-12T12:41:12.9344817+01:00: Unity import early-after1 Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T12:41:32.6640117+01:00: Unity side-render early-after1 Low clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T12:41:33.1944102+01:00: wczesny import i 4 diagnostyczne kadry wiat Low-clear; sukces=True. Każdy krok pobierał i zwalniał slot Unity; standardowy pipeline czekał na własny marker. Ten dodatkowy podgląd nie zastępuje 236 kadrów budżetowych ani oczekującej kontroli geometrii. NASTĘPNY KROK: obejrzeć podglądy i kontynuować pełną walidację.

2026-11-12T12:43:43.5226936+01:00: obejrzano cztery wczesne kadry Low-clear obu wiat; szkło przepuszcza tło, z tych stron nie widać szczeliny dachu ani rażącego sortowania. Zapisano OBSERVATIONS z jawnymi ograniczeniami i pełnymi licznikami tych czterech kamer: mesh/cienie +0, instancje draws Anders -1, Factory 0. Factory ma +1 renderowaną instancję; przyczyny nie ustalono, mimo identycznych danych JSON. Nie deklaruje się budżetu całej trasy. Recenzent dostał te same 4 JPG; geometry nadal czeka na heavy. NASTĘPNY KROK: recenzja i pełne 236 kadrów.

2026-11-12T12:44:10.7013622+01:00: niezależny furniture_review obejrzał 4/4 wczesne kadry Low-clear, zdjęcie i dwa kadry baseline. Brak widocznego blokera; potwierdził poprawę ramy, szkła i ławki oraz brak widocznej wcześniejszej szczeliny. Pozostaje słaby odczyt powierzchni dachu od frontu i niemal niewidoczne szyby. Nie wzmacniać szkła bez High. Pełny tekst zapisano w preview-early-after1/REVIEW.md. Nie jest to końcowy PASS ani dowód budżetu. NASTĘPNY KROK: pełna seria i oba narożniki.

2026-11-12T12:48:55.5349559+01:00: zapisano roboczy PACKET.md ze źródłami, zakresem zmian, dowodami i jawnymi pozycjami OCZEKUJĄCE. Zweryfikowano ponownie SHA256 trzech oryginałów Mapillary; metadane i osobny hash wycinka zapisano w reference/provenance.json. Nie przeniesiono wyników testów r2 jako wyników r3. NASTĘPNY KROK: geometria, pełne kadry i końcowe testy.

2026-11-12T12:52:53.7423734+01:00: uzupełniono ADR 0120 o poprawkę kontaktu dachu, test 10/10, audyt instancji i ograniczony przegląd czterech Low-clear. Wskazano wprost oczekującą geometrię, High, drugi narożnik i pełny budżet. NASTĘPNY KROK: dokończenie istniejącego pipeline, bez ponawiania generatora.

2026-11-12T12:57:44.5538523+01:00: heavy geometry after; sukces=True; slot gpt-furniture-r3 zwolniony. NASTĘPNY KROK: sprawdzić log i kontynuować walidację rundy.

2026-11-12T12:58:56.7582574+01:00: skan chronionej geometrii after zakończył się powodzeniem: 6833 przed, 6833 po, changed=[]; slot heavy zwolniony. Standardowy import after1 już działa w wymaganym slocie Unity. Uzupełniono PACKET i ADR o rzeczywisty wynik, bez przenoszenia go na jeszcze niezmierzony budżet. NASTĘPNY KROK: cztery serie 59 kamer, dokładne Low i oba narożniki.

2026-11-12T12:59:13.5324475+01:00: Unity import after1 Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T12:59:39.8523150+01:00: Unity render after Low clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:00:06.5299522+01:00: Unity render after Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:00:36.7639987+01:00: Unity render after High clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:01:08.7835697+01:00: Unity render after High overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:01:10.2625814+01:00: dokonano kontroli kompletności czterech wariantów renderu i audytu instancji po generacji. Logi i JSON zawierają wynik; to nie jest jeszcze przegląd wizualny ani pomiar GPU. NASTĘPNY KROK: dokładne liczniki Low i dodatkowe narożniki szkła.

2026-11-12T13:01:35.9669208+01:00: dokładny licznik CPU after Low clear; sukces=True, slot Unity zwolniony. NASTĘPNY KROK: pozostałe warianty i porównanie przed/po, bez deklaracji czasu GPU.

2026-11-12T13:02:03.3222650+01:00: dokładny licznik CPU after Low overcast; sukces=True, slot Unity zwolniony. NASTĘPNY KROK: pozostałe warianty i porównanie przed/po, bez deklaracji czasu GPU.

2026-11-12T13:02:20.1765646+01:00: Unity side-render after-side Low clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:02:41.1165723+01:00: Unity side-render after-side Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:02:49.9214251+01:00: pełne 236 kadrów standardowych gotowe. Wstępne liczniki: mesh i cienie wszędzie +0; na Low brak wzrostu draws instancji; High route-putry-approach ma +3 w obu światłach. Nie ukrywać tej różnicy High w raporcie. Obejrzano pojedyncze narożniki High-clear Anders i High-overcast Factory: bez mlecznej tafli lub rażącego sortowania w tych ujęciach. Dokładne Low i after-side kończy post-candidate. Przygotowano review-sheets.ps1, który czeka na jego koniec i dopiero potem tworzy 40 arkuszy w heavy. NASTĘPNY KROK: pełny przegląd i rzeczywista wartość maksymalnych tris Low.

2026-11-12T13:03:03.7351088+01:00: Unity side-render after-side High clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:03:22.7227178+01:00: Unity side-render after-side High overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:03:23.6017023+01:00: ukończono dokładne liczniki Low, oddzielne rendery narożników after-side i porównanie metryk. To nie dowodzi zgodności wizualnej ani budżetu; wartości trzeba odczytać i obejrzeć kadry. NASTĘPNY KROK: kontrola szkła, analiza wszystkich 236 par oraz niezależna recenzja. Pełny GIS dopiero na końcu rundy.

2026-11-12T13:05:31.0384236+01:00: dokładne 118/118 Low spełnia tris <= +2%; maksimum +0,0330134791%, bez wzrostu draws Low. Post-candidate zakończony poprawnie. Poprawiono zbyt szerokie git add diagnostyki: 118 surowych PNG usunięto wyłącznie z indeksu (--cached), wszystkie pozostają w artifacts do robocopy. Przyszły zapis obejmuje tylko JSON/stats; podglądy do oglądania mają <=960 px. Arkusze czekają w heavy, niezależny recenzent potwierdził dodatkowe 8+2 zbliżenia bez blokera. NASTĘPNY KROK: pełne 236 par i końcowe testy.

2026-11-12T13:06:03.5344448+01:00: root i niezależny recenzent obejrzeli 8/8 przeciwnych narożników oraz dwa zbliżenia High, bez widocznego blokera szkła/geometrii. Zapisano preview-after-side/REVIEW.md oraz budget-summary.json z pełnym zakresem 236 kadrów i 118 dokładnych Low. High +3 na route-putry-approach pozostaje jawnie osobno; limit zadania dotyczy Low. NASTĘPNY KROK: pełne arkusze 236 par, potem końcowe testy.

2026-11-12T13:13:57.0502731+01:00: znaleziono regresję polityki: Instances.asset zapisuje generic [60,300] m, a nowy wariant fallback [30,120] m. Dotychczasowe 118 pomiarów Low opisują ten krótszy zasięg i NIE stanowią końcowego dowodu budżetu poprawnej rodziny. Dodano własny edytorowy FurnitureShelterPolicySave, który podczas zwykłego zapisu wygenerowanego setu dziedziczy wyłącznie nowemu wariantowi politykę i maskę cieni generic. Nie edytowano InstanceImporter ani roads. Dodano 7 testów, w tym rzeczywisty save/reload. Stare 236 kadrów i queued compare pozostają historyczną iteracją 1; nowe rendery dopiero po jej zachowaniu i teście hooka. Estymator roads nadal nie zna nowej rodziny — wymaga jawnego zgłoszenia liderowi, nie edycji zakazanych źródeł. NASTĘPNY KROK: focused EditMode w slocie Unity, import i ponowny pełny pomiar przy właściwym zasięgu.

2026-11-12T13:14:35.2057271+01:00: Unity shelter-policy-probe candidate2 Low overcast; sukces=False. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:16:17.3915180+01:00: pierwsza próba focused EditMode zakończyła się błędem kompilacji CS0234: testy nie referencjonują assembly World.Import.Editor. Przeniesiono wyłącznie własny nowy hook do Editor/Furniture w istniejącym Game.Editor, dodano właściwy using Game.World i zachowano GUID pliku oraz folderu. Nie zmieniono cudzych asmdef. Log pierwszej kompilacji zachowano; ponowna próba ma osobną fazę candidate2b. NASTĘPNY KROK: wynik rzeczywistego zapisu/reload polityki.

2026-11-12T13:18:11.1310372+01:00: Unity shelter-policy-probe candidate2b Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:20:41.3141475+01:00: focused FurnitureShelterPolicyTests 7/7 passed, 0 failed/skipped. Test rzeczywistego SaveAssets + unload/reload potwierdził trwałość. Niezależny przegląd kodu nie znalazł blokera dla obecnego importu, wskazał ograniczenia hooka przy zapisie, wymóg obecności generic i nieobsługiwany estymator roads. Zapisano bazę polityk wszystkich prototypów oraz XML/logi. PACKET jawnie wycofuje iterację 1 jako dowód końcowego budżetu. NASTĘPNY KROK: normalny import candidate2 i audyt wszystkich polityk.

2026-11-12T13:22:12.4833337+01:00: Unity import candidate2 Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:24:19.8364948+01:00: normalny import candidate2 OK. Audyt wszystkich 196 prototypów wykazał zmianę wyłącznie bus_shelter_red_0120: LOD/cull [60,300] m jak generic, liczby LOD/instancji i pozostałe polityki bez zmian. Dodano odrębne ścieżki after2, exact-after2, after2-side oraz iteration2, aby nie nadpisać starej serii czy wejść oczekującego porównania. Nowy pipeline używa wyłącznie slotów Unity i małych kontroli metadanych; nie rozpoczyna drugiego heavy z tym samym właścicielem. NASTĘPNY KROK: pełne ponowne pomiary przy właściwym zasięgu.

2026-11-12T13:24:51.0389905+01:00: Unity render after2 Low clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:25:18.7430213+01:00: Unity render after2 Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:25:51.4830627+01:00: Unity render after2 High clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:25:52.7891682+01:00: zapisano niezależny przegląd hooka i ograniczenia kontraktu, pełny log rzeczywistego importu oraz uzupełniony ADR/PACKET. Historia iteracji 1 pozostaje jawnie wycofana jako końcowy budżet. Nowa seria after2 działa w osobnych katalogach; stary queued compare ma niezmienione wejścia i nie koliduje z nowymi metrykami iteration2. NASTĘPNY KROK: odczytać poprawione delty Low i ocenić nową serię.

2026-11-12T13:26:22.0745557+01:00: Unity render after2 High overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:26:49.0226048+01:00: dokładny licznik CPU after2 Low clear; sukces=True, slot Unity zwolniony. NASTĘPNY KROK: pozostałe warianty i porównanie przed/po, bez deklaracji czasu GPU.

2026-11-12T13:27:16.1258692+01:00: dokładny licznik CPU after2 Low overcast; sukces=True, slot Unity zwolniony. NASTĘPNY KROK: pozostałe warianty i porównanie przed/po, bez deklaracji czasu GPU.

2026-11-12T13:27:37.0345914+01:00: Unity side-render after2-side Low clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:27:57.5726759+01:00: Unity side-render after2-side Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-12T13:28:21.0428320+01:00: Unity side-render after2-side High clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.
