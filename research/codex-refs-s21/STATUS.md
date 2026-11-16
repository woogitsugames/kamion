# Status referencji codex-refs-s21

Stan po `f9dbf2b94`, 16.11.2026. Cel ciągły wstrzymany na prośbę użytkownika; nieukończony. Gałąź `research/codex-refs-s21`, [PR100](https://github.com/woogitsugames/kamion/pull/100), bez scalania.

| Pakiet | Rekordy głównego manifestu | Co oznacza liczba |
|---|---:|---|
| 01 lampy | 65 | Także przednie, pomocnicze i niekwalifikowane referencje. |
| 02 brud | 36 | 34 kadry: 14 lokalnych i 20 link-only, oraz 2 dokumenty. |
| 03 Knyszyn | 59 | Różne daty; zdjęcia właściciela wyłącznie jako obserwacje tekstowe. |
| 04 DK65 | 42 | Zdjęcia, ortofoto, dokumenty i jeden rekord BDL. |
| 05 kolej 38 | 25 | Dokumenty i kadry nie tworzą automatycznie mapowania lokalnego przejazdu. |
| 06 pierścień | 52 | Różne miasta, daty i stopnie identyfikacji obiektów. |
| 07 Białystok/Dojlidy | 30 | Także historyczne odniesienia i powtórne oglądy. |

SOURCED: lokalne główne manifesty. Liczby nie oznaczają spełnienia progów FIX. Wierszy podkatalogów nie sumujemy z głównymi jako nowych ekspozycji.

## Lampy i fotometria

M59: rozpoznana dolna granica **5 tylnych PASS i 1 warunkowy UP4-03**. W grupie PASS nadal ON0 i zmierzch/noc0. RC39 pozostaje warunkowy po R57: wiele OE w ofercie nie ustala dokładnej części. Nie dodajemy wymogu dowiedzionego demontażu, pełnego numeru E lub pięciu rodzin, których FIX nie żąda. EMC10R nie zastępuje aprobaty fotometrycznej. R51 Scania E1/4147 i R52 MAN/ZKW E12/112029 to rzeczywiste makra przednie; root obejrzał także całe przody. Nie zwiększają tylnego15.

Tablicowe: 10 samodzielnych kadrów 5 reprezentowanych fizycznych urządzeń oraz 5 detali SUPPORT. Dowody zastosowania OE mają różną siłę; nie jest to pięć udowodnionych demontaży ciężarowych ani pięć czytelnych E. Regpoint warunkowy. R54 to rzeczywista emisja o zmierzchu na pokazowym ciągniku HELLA, z zastrzeżeniem konfiguracji producenta i nieczytelnym E; kontekst zachowany, grupa kwalifikowanych4ON bez przyrostu. Progi15/4/3/5 otwarte.

R148: R48 potwierdził na bitmapach minimum kat.5 jako0,6cd w obu wersjach. Starsze maksimum single11a/b/c rzeczywiście wydrukowano120cd, późniejsze1200cd. R50 potwierdził także druk120 w autentycznym projekcie2022/92 oraz brak zmiany tych komórek w§142 raportu1166. **R55 rozstrzygnął przyczynę źródłowo:** GRE/2023/14, II.Justification pkt3, wskazuje błąd konwersji zapisu naukowego; WP29/2024/23 zawiera poprawkę1200cd. Dwa niezależne oglądy. Starsza kolumna120 pozostaje zapisem rzeczywistego druku, nie nastawą generatora. D600cd to osobna kolumna. Nie ogłoszono pełnej aktualności2026 ani zastosowania11a/b/c do dowolnej części ze zdjęcia.

R150 R43: autentyczny tekst2019, tabela5/§5.2.3.1, niezależne odczyty450/200/150 oraz12/8/8mcd/lx dla wskazanych kątów; to odblask CIL, nie emisja cd. R58 dodał sześć norm R7 z publikacji UE2014: minima polowe, punkty siatki35%/70%, apertura i warunki pomiaru. Root obejrzał strony10/27/28. Osobna siatkaS3, procenty minimum osiowego i warunki niskiego montażu są zachowane; bez pełnego audytu prawa2026.

Losowy audyt lamp R46: snapshot60, próbka12/60=20%,13 obrazów,0 zastępstw i0 NOT_REVIEWED. Nie jest audytem bieżących65. Nowe makra R51/52 i kontekst R54 mają dodatkowy celowany ogląd root. R42 wcześniej skorygowano kolory/kształt makra, które odziedziczyło cechy całej lampy. Kolejność kopiowania snapshotu i zgodny hash są jawne wR46.

## Brud tylnych drzwi

**A17 z ograniczeniami/B1.** A: Knight158, Western182, Premier183, KroneEUR15 lekki film, RoadTourWW17 source-dependent, AutoReview39, RI49, UR54, UR55 miejscowe smugi, RG57 Tonar, FR60-003 dolny nalot S.KO, R64 Wabash miejscowe dolne smugi i R65 Facchini ograniczony film, R71 zimowy S.KO oraz dwa R69 z lokalnymi dolnymi smugami. B: Western, alias CR6 liczony raz. Wysokość≥1000px dotyczy B; nie jest dodatkową bramką A.

Zimowe A3: RoadTour source-dependent, RI49 i R71 z widocznym śniegiem. R71 ma podpis miejsca obwód omski, nie moskiewski region rejestracji; Europy nie zwiększa. Europejska droga A2: RI49 w Polsce oraz FR60-003. R70 łączy podpis miejsca fotografii w obwodzie twerskim, widoczną scenę drogową i oficjalny opis geograficzny regionu. To jawny wniosek z dwóch źródeł o kontynencie, nie członkostwie wUE ani GPS. Zimowe/europejskie B0 w rozpoznanym podzbiorze, nie globalne twierdzenie o braku. Progi20/12/6/6 nadal otwarte.

R64 ma duże drzwi1320–1450px ESTIMATED, ale brak dowodu ruchu/zaraz po trasie nie pozwala awansować B. R65 ma obraz627×470 i drzwi320–370px ESTIMATED. Rdza, powłoka, odbicie i cień pozostają odrębne od osadu. Chemia soli z fotografii UNVERIFIED. R61 Nofima ogranicza wyłącznie niepewny typ konkretnego pojazdu, nie samo ucięcie góry. R68 to datowany historyczny kontekst materiałów ZUD GDDKiA z2009/2021, bez dawki DK65 i bez przypisywania chemii drzwi.

R63: snapshot11 przyjętych źródeł sprzed R64/R65, zapisany i zahaszowany przed losowaniem. `random.Random(20261115).sample(sorted(ids),3)` dał FR60-003/Knight009/UR54-001. Agent ponownie obejrzał3/3, bez podmian; root odtworzył hash i losowanie. To samokontrola, nie ślepa recenzja ani losowa próba obecnych16. Indeks P18 R47 ma88/88ID i87URL, z aliasami i renderem; nie88 kwalifikowanych fotografii. Kwarantanna154/159 zachowana.

## Świat

R22/23: jeden ID CityGML porównany w LoD1 i LoD2; własny wykres, nie nowe zdjęcie. Dach obu modeli ma źródło2016, 7,5 m to measuredHeight LoD1, nie kalenica. Dokładny klucz CityGML→BDOT potwierdzony niezależnie przez root; publiczny punkt PRG Rynek1 jest wewnątrz obrysów według analizy agenta. Brak urzędowego pola łączącego adres z budynkiem: adres→model nadal ESTIMATED przestrzennie, formalny join UNVERIFIED.

R18 kolej: sześć norm nawierzchni/niwelety z osobnym oglądem stron8/9/47. 35mm oznacza sumaryczny przyrost żłobków, nie ich podstawową szerokość. Limity8%/3%/20m zachowują warunki/wyjątki i nie stanowią pomiarów Knyszyna.

R16 region: dwa nowe kadry jednego zamku w Tykocinie: sylweta od gruntu i z góry. Bliższy obwód niski względem dalszego korpusu; bez daty ekspozycji, formalnych kondygnacji, metrów i stanu2026. Link-only ARR.

Knyszyn: R19 dwa pełne widoki lamusa z2020, sześć podpór, dach/podcień/przyziemie. KR18 dwa widoki jednego domu Klattów, stan2015; tekstowe cechy NID/UM oddzielone od zdjęć. R21 dwa kadry z Gońca nr11(203), listopad2021, s7, Anna Aneta Molska: pompa na podwyższonym kwadratowym cokole z kratką oraz biały/bordowy słup bez takiego cokołu. Root obejrzał oba przy200% w natywnym PDF. To inna ekspozycja znanego słupa, nie drugi egzemplarz. Piksele źródłowe, GPS, metryka i dokładna ekspozycja nieustalone. Rynek3/4 NID to katalog bez fotografii, nie nowe dachy.

DK65: R25 dwa nowe kadry żółtej farby na jezdni, podpisy27/26.08.2026: odcinki przerywane/zygzak i cienka ciągła krawędź. Root oba obejrzał. To coś innego niż żółte obrzeża tablic R21. Lokalny kilometr galerii nie jest kilometrażem krajowym ani GPS; nie deklarujemy listopadowej organizacji ruchu. R22 jedna wiata w Knyszynie i oddzielny plac, nie dwa przystanki; wcięcie zatoki i relacja do obecnej DK65 nieustalone. KS20/FB19 mają pobocza, zjazd i drzewa bez gatunków/rozstawów z domysłu.

BDL R23/24: punkt w lesie przy istniejącym TC17-02 zwrócił rekord pozaPGL. SO=sosna zwyczajna potwierdzone słownikiem TAKSATOR s20. Surowe species_age100,a_year2017,part_cd5 nie uprawniają do wieku109lat ani udziału50%; odpowiednie powiązania/jednostki nadal UNVERIFIED. Nie odnosić rekordu do każdego drzewa przy drodze. TC17 pomiar wybranej korony do asfaltu około12±4m ESTIMATED nie jest rozstawem pni lub skrajnią. Skala0,3m/px nie jest GSD ani dokładnością orto.

Kolej: R15 urzędowy budżet potwierdza wykonany kat.B ze światłem i dźwiękiem Knyszyn–Krypno, stan31.12.2011; bez ID/km i aktualnego stanu2026. Normy R16 rozdzielają gałęzie kwalifikacjiA–D i warunki przejściowe; gałąźD20km/h nie znosi wspólnego limitu torów. Rozbiórka29+522 i wiadukt29+394 to odrębne dowody. R17 nie znalazł nowego urzędowego powiązania DW671. 3kVDC wynika z PLK, nie z samych przewodów na zdjęciu.

Region: Bernardyni w Tykocinie to jeden kompleks w dwóch kadrach2025, NCND tylko linki. Panorama Moniek AUX nie potwierdza pewnej nazwy centralnej bryły. Ełcka2017 daje dwie nowe ekspozycje uliczne z zasłoniętymi/uciętymi dachami, nie pełne bryły. Białystok: dolne rondo Bieżeństwa dzień/noc oraz dwa kadry Kuronia2017; styki cokołu/trawy/chodnika i dojazdy, bez parametrów lub stanu2026.

## Kontrola i następny krok

Kontrola po f415174f8: **600 poprawnych śledzonych JSON,95 rastrów≤800px,96 istniejących lokalnych ścieżek głównych manifestów,0plików>5MB**. Główne ID unikalne. Zakres diff wobec7f830369c wyłącznie research/codex-refs-s21 i docs/LICENSES.md. Legalne raw pozaGit; media/firmy wyłącznie link-onlyARR; NCND tylko linki; zdjęcia właściciela bez kopii. Bez Unity/adb/kodu gry.

Commons: dwa ograniczone pojedyncze API200, bez nowych obrazów; Flickr nowe pobraniaSTOP. Jedno zawieszone własne git-HTTPS przerwano po weryfikacji procesu; ponowny push zakończył się poprawnie, bez dotykania innych sesji. Ostatni live zapisano08:29:29Bruksela, następny zwykły około09:30.

Gotowe do scalenia po recenzji lidera: **NIE**. R69/R71 brudu, R18 nawierzchni, R22/23 modeli i R16 zamku odebrane. R59 klosz Krone to negatywny odczyt, bez nowej referencji. Następne: nowe fizyczne E na tylnych lampach, sąsiednia bryła Rynku i elewacje przemysłowe Białegostoku. Wyniki robocze nie zwiększają liczników przed odbiorem.

Aktualizacja16.11.2026 po f415174f8: R6 dodaje pięć warunków testu z publikacji2010 (root s1/8/9/23), nie rytm drogowy. R75 HCT: nowy mocny brud+śnieg, lecz A_PENDING_TYPE_ONLY (sprzęg/wózek niepewny), więc A16/B1/zimaA3/EuropaA2 bez wzrostu. R72/73 negatywne oglądy, R74 Nofima nadal tylko typ UNVERIFIED. R26 orto dk65-09 pokazuje pasy i korony, nie potwierdza rowu/przepustu/zjazdu; data nalotu nieznana. PLK R19 opisuje mechanizm wyszukania, bez nowego lokalnego ID. Region R17 to zwykły wlot2017 z czerwonymi poręczami, nie udowodnione rondo. Brzeska R20 pozostaje luką po ograniczonym UI. Goniec3/2020 R24 ma1 AUX robót fontanny, bez finalnych dysz/krat i bez awansu głównego manifestu.

## Odbiór 16.11.2026, 08:19 Bruksela

SOURCED [główne manifesty i kontrola snapshot0e408fbba]: 65/35/55/40/25/48/30 rekordów kolejno01–07. 628 poprawnych śledzonych JSON,97 rastrów≤800px,98 istniejących lokalnych ścieżek w głównych manifestach,0 braków/duplikatów głównychID/plików>5MB. Zakres diff wyłącznie katalog referencji i docs/LICENSES.md. Ta kontrola plików nie zastępuje recenzji wizualnej.

03 R25: drugi ID Rynek2, LoD1 measuredHeight5,98m SOURCED i zakresLoD2 7,62m ESTIMATED to różne metryki; źródłoALS2016, nie porównanie kolejnych przebudów. Formalny join adresowy UNVERIFIED. R26: nowa ekspozycja znanego domu Kościelna6, HenrykBorawski11.06.2012, CC BY-SA3.0. Root obejrzał oryginał i miniaturę800×600; oryginał4000×3000 pozaGit,0 nowych obiektów.

05 R20: pięć norm i jeden dokumentG2/G3/G4, root s72/73/510/511. 440/600 to cały znakG2;360 nie jest pełną szerokością. 1400 biegnie wzdłuż ramieniaG3, nie poziomej szerokościX. Jednostki rysunku UNVERIFIED, bez domyślnego mm. R21: jeden historyczny obraz PLK Ełk, SzymonGrochowski, publikacja10.12.2021; tory/podsypka/kratownice, root obejrzał. Bez dowodu zasilenia, napięcia, lokalnego przejazdu lub stanu2026.

06 R18: dwa nowe ujęcia jednego alumnatuTykocin, stan2016 według podpisów NID, NCND3.0PL wyłącznie linki. Pierwszy AUX obejmuje odległy niski budynek po lewej kościoła, drugi pokazuje długą elewację i zaokrągloną część. Root oba obejrzał; bez metrów/GPS/stanu2026.

07 R22/R23: po dwa indywidualnie obejrzane kadry Bravilor i Rosti, ARR wyłącznie linki, root4/4. **Konflikt źródłowy:** główne teksty obu realizacji Unibep powtarzają Myśliwską18 i dostęp odKuronia. Nie określono przyczyny powtórzenia ani wspólnej parceli. Niezależne strony operatorów wskazują BravilorJackaKuronia2 oraz RostiMyśliwska18; cytowane dokładne sekcje w source-conflict.json. CzytelneBRAVILOR i numer18 to odrębne dowody wizualne; formalny join doP11/B-044 pozostaje UNVERIFIED. Żebrowania biuraRosti nie przenosić na główną halę.

Negatywne kontrole: Pegas nie daje czytelnego fizycznegoE; DEKRA ma śnieg, ale brak zamkniętej pary drzwi i pewnego filmu; EłckaR28 nie daje pewnej wiaty/D-15/zatoki. 0 nowegoPASS/A/B/AUX z tych kontroli. A16/B1/zimaA3/Europa-roadA2 oraz lampy5PASS+1warunkowy/ON0/noc0 bez zmian. Cel aktywny, trzej agenci pracują nad kolejnymi lukami. Gotowe do scalenia po recenzji lidera: NIE.

## Odbiór po9337c8251, 16.11.2026

Bieżące główne manifesty01–07:65/35/56/41/25/50/30 rekordów. R27Knyszyn:1 nowy kadr donicy z szerokich poziomych desek i łukowego bruku, publikacja21.07.2022, dół ucięty;0nowych dokumentów. Root obejrzał, ARRlink-only.

06SIMR19:1nowy nazwany budynekMońkiKościelna41 i1kadr link-only, root obejrzał. Formalne3kondygnacje ztekstu gminy; dach zasłonięty. Datawydarzenia23.10.2026/publikacji26.10.2026 oddzielona od ekspozycjiUNVERIFIED. 06R19: nowy tekstGDDKiA27.02.2026 o przebudowieDK65/DW671Knyszyn na rondo, jezdnia7→12m, pobocza0,75m; zakres prac, nie odbiór,12mnieśrednica.

04KontraktR29: odrębny komunikat04.07.2025 podaje NOWĄ jezdnię o zakresie szerokości7–12,2m,ponad400m zadania i obustronne pobocza0,75m. Nie przepisano tego jako stare7→nowe12,2. Zachowano datowaną różnicę wobec komunikatu2026,bez tezy o sprzeczności/zmianieprojektu/różnychkontraktach. Normalizacja terminu styczeńprzyszłegoroku→styczeń2026 jest wnioskiem kalendarzowym, wykonanieUNVERIFIED. 0obejrzanych fotografii obu komunikatów po timeoutach. Root przyjął odczyt2025agenta; jego własny niezależny odczyt2025też timeout, co jawne wroot-receipt.json.

04ZatokiR29: istniejący dokument04-TI9-D01 pogłębiony o4wiersze: peron20m,zatoka3m,skosy1:8/1:4,sztywna nawierzchnia/rezerwa wiaty, osobno rampa chodnika8%. Root obejrzałPDF44/druk45. ProjektS19przyDK65/DZ1, brak dokładnego join do przystanku i wykonania2026.0nowychPDF/dokumentów/fotografii z tej analizy.

Negatywne01R61/R62/LC7 i zimowe02media nie zwiększająPASS/ON/nocy/A/B/zimy/Europy. 05R22 nie łączy drogowego47+800–53+600 z kilometremLK38;29+522 i historycznaB2011 nadal osobno. Dodatkowy oglądPDF9 normznaków daje mm wyłącznie dla tabeliA–D, nie rozstrzyga rysunkówG. 07R24bramaszpitala:0nowychkadrów po ograniczonymUI,nieglobalnybrakpokrycia.03R28 PRG to mały ekstrakt2punktów1/2,niepełnyPRGmiasta. Nowy rozszerzony odczyt jest w toku,0modeli przed odbiorem.

Kontrola przyrostowaJSON i głównychID/formatówCSV poprawna; pełny audyt plików0e408fbba pozostaje datowanym snapshotem. Live08:29:29, kolejny zwykły około09:30Bruksela. Cel aktywny, PR100 bez scalania; Gotowe do scalenia po recenzji lidera: NIE.

## Odbiór po f9dbf2b94 — nowe bryły i A17

Aktualne główne manifesty01–07:65/36/58/42/25/51/30. Kontrola snapshotf9dbf2b94:661poprawnychśledzonychJSON,99rastrów≤800px,100istniejących lokalnych ścieżek głównych manifestów,0duplikatówgłównychID/braków/plików>5MB/błędówzakresu. To kontrola plików, nie zastępstwo recenzji wizualnej.

M61: **A17/B1, zimaA3, europejska drogaA2**. Nowy02-AFF-001 FruehaufZM53290 ma zamkniętą parę jasnych drzwi z drobnymi pionowymi smugami, root obejrzał exact1200×900. Rama/platforma i brunatne ślady na metalu osobno; nie skład soli. Całyobraz900pxwyklucza1000pxdrzwiB, trasa i ekspozycjaUNVERIFIED. Ablis to adres oferty, nie położenieaparatu. Główny02:34kadry14lokalnych/20link-only+2dokumenty. Inne nowe kontrole TrafiHCT i ClassTrucksUM52126 bez awansu.

03R29/R30: dwie nowe analizy różnychbrył3066 i2D30 przy publicznych punktachPRGRynek3/4. Jedno małe GetFeature300×300m zwróciło51/51pkt,60127B,0nowychZIP; drugi model bezHTTP. Root obejrzał obiefigury800×480 oraz niezależnie odczytałkluczeCityGML/BDOT i rekordyPRG. Adres→bryła ESTIMATEDprzestrzennie, formalnyjoinUNVERIFIED. LoD1measuredHeight6,77m/7,79m SOURCED; zakresyZLoD2 8,10m/9,68m ESTIMATED. Nie rzeczywisteprzedziały tolerancji wysokości;obieźródłoALS2016, wersjeLoD2liter2018/LoD1 2023, różne pionoweCRS. Brak wnisków o przebudowie/materiałach/kondygnacjach/stanie2026. Własnefigury i atrybucje dodane, źródła sharedro.

04R30:1nowy kadr rowu z wodą/skarpami/krawężnikami i dojazdem, podpis24.08.2026/kmokoło0+400lokalny. Rootobejrzał; brak widocznego przepustu, metrów lub GPS.06R20:1nowy kadr ścieżkiTykocin,MonikaKalicka, publikacja30.07.2022; bruk/obrzeża/oprawazpanelem/podporydrzew,bez funkcjipanelu/gatunków/metryki/mostu. Rootobejrzał. Oba ARRlink-only,0kopii.

R4: wskazana uprzednio P4-001 to R48; brak potwierdzonej lokalnejbitmapyR4 wsprawdzonymzakresie. Nie dodano nowych norm bez oglądu. Ograniczony pojedynczy searchUNECE nie dał nowegopełnegoźródła, nie ponawiano blokowanychendpointów. Trzej agenci pracują dalej nad brudnymi tyłami, Dojlidami i relacją kościół–ogrodzenie–ulica. Live08:29:29, następny zwykły około09:30Bruksela. Gotowe do scalenia po recenzji lidera:NIE.

R31odebrany16.11.2026: główny03=59. Nowa ekspozycja znanegokościoła, NIDstan2015, NCNDwyłącznielink, relacja mur–brama–chodnik–krawężnik–jezdnia, rootpeer. Cokółsamychścian zasłonięty.0nowychbudynków/metryki/headinguznazwyelewacji. WciążA17/B1i pozostałemanifestybezprzyrostu.

Ostatni odbiór16.11.2026 przed wyhamowaniem:06R21MEDIATEKA1nowaekspozycjaPARTIAL,pobrane0/link-only1. MEDIATEKA/4czytelne;dół/bokiucięte,auta zasłaniajągrunt.0nowychodrębnychbudynków i beznawierzchni. Rootobejrzał. Główny06=52;pozostałelicznikibezzmiany. Szczegóływznowienia wWZNOWIENIE.md.

## Wyhamowanie na prośbę użytkownika

2026-11-16T08:59:26+01:00 Bruksela. Odebrano wszystkie rozpoczęte pakiety. Dalsze rundy wstrzymane; cel nieukończony, progi pozostają otwarte. Stan i kolejka wznowienia: [WZNOWIENIE.md](WZNOWIENIE.md). Końcowa kontrola snapshot043ec4128:JSON670,rastry99≤800px,lokalneścieżki100,0błędów/plików>5MB. Główne manifesty65/36/59/42/25/52/30. Brak aktywnych agentów badawczych i rezerwacjiChrome. PR100bezscalania.
