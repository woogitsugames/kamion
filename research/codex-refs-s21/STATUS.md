# Status referencji codex-refs-s21

Stan po `5f245675d`, 16.11.2026, około 07:06 w Brukseli. Cel ciągły pozostaje aktywny. Gałąź `research/codex-refs-s21`, [PR100](https://github.com/woogitsugames/kamion/pull/100), bez scalania.

| Pakiet | Rekordy głównego manifestu | Co oznacza liczba |
|---|---:|---|
| 01 lampy | 65 | Także przednie, pomocnicze i niekwalifikowane referencje. |
| 02 brud | 31 | 29 kadrów: 14 lokalnych i 15 link-only, oraz 2 dokumenty. |
| 03 Knyszyn | 48 | Różne daty; zdjęcia właściciela wyłącznie jako obserwacje tekstowe. |
| 04 DK65 | 39 | Zdjęcia, ortofoto, dokumenty i jeden rekord BDL. |
| 05 kolej 38 | 22 | Dokumenty i kadry nie tworzą automatycznie mapowania lokalnego przejazdu. |
| 06 pierścień | 43 | Różne miasta, daty i stopnie identyfikacji obiektów. |
| 07 Białystok/Dojlidy | 26 | Także historyczne odniesienia i powtórne oglądy. |

SOURCED: lokalne główne manifesty. Liczby nie oznaczają spełnienia progów FIX. Wierszy podkatalogów nie sumujemy z głównymi jako nowych ekspozycji.

## Lampy i fotometria

M59: rozpoznana dolna granica **5 tylnych PASS i 1 warunkowy UP4-03**. W grupie PASS nadal ON0 i zmierzch/noc0. RC39 pozostaje warunkowy po R57: wiele OE w ofercie nie ustala dokładnej części. Nie dodajemy wymogu dowiedzionego demontażu, pełnego numeru E lub pięciu rodzin, których FIX nie żąda. EMC10R nie zastępuje aprobaty fotometrycznej. R51 Scania E1/4147 i R52 MAN/ZKW E12/112029 to rzeczywiste makra przednie; root obejrzał także całe przody. Nie zwiększają tylnego15.

Tablicowe: 10 samodzielnych kadrów 5 reprezentowanych fizycznych urządzeń oraz 5 detali SUPPORT. Dowody zastosowania OE mają różną siłę; nie jest to pięć udowodnionych demontaży ciężarowych ani pięć czytelnych E. Regpoint warunkowy. R54 to rzeczywista emisja o zmierzchu na pokazowym ciągniku HELLA, z zastrzeżeniem konfiguracji producenta i nieczytelnym E; kontekst zachowany, grupa kwalifikowanych4ON bez przyrostu. Progi15/4/3/5 otwarte.

R148: R48 potwierdził na bitmapach minimum kat.5 jako0,6cd w obu wersjach. Starsze maksimum single11a/b/c rzeczywiście wydrukowano120cd, późniejsze1200cd. R50 potwierdził także druk120 w autentycznym projekcie2022/92 oraz brak zmiany tych komórek w§142 raportu1166. **R55 rozstrzygnął przyczynę źródłowo:** GRE/2023/14, II.Justification pkt3, wskazuje błąd konwersji zapisu naukowego; WP29/2024/23 zawiera poprawkę1200cd. Dwa niezależne oglądy. Starsza kolumna120 pozostaje zapisem rzeczywistego druku, nie nastawą generatora. D600cd to osobna kolumna. Nie ogłoszono pełnej aktualności2026 ani zastosowania11a/b/c do dowolnej części ze zdjęcia.

R150 R43: autentyczny tekst2019, tabela5/§5.2.3.1, niezależne odczyty450/200/150 oraz12/8/8mcd/lx dla wskazanych kątów; to odblask CIL, nie emisja cd. R58 dodał sześć norm R7 z publikacji UE2014: minima polowe, punkty siatki35%/70%, apertura i warunki pomiaru. Root obejrzał strony10/27/28. Osobna siatkaS3, procenty minimum osiowego i warunki niskiego montażu są zachowane; bez pełnego audytu prawa2026.

Losowy audyt lamp R46: snapshot60, próbka12/60=20%,13 obrazów,0 zastępstw i0 NOT_REVIEWED. Nie jest audytem bieżących65. Nowe makra R51/52 i kontekst R54 mają dodatkowy celowany ogląd root. R42 wcześniej skorygowano kolory/kształt makra, które odziedziczyło cechy całej lampy. Kolejność kopiowania snapshotu i zgodny hash są jawne wR46.

## Brud tylnych drzwi

**A13 z ograniczeniami/B1.** A: Knight158, Western182, Premier183, KroneEUR15 lekki film, RoadTourWW17 source-dependent, AutoReview39, RI49, UR54, UR55 miejscowe smugi, RG57 Tonar, FR60-003 dolny nalot S.KO, R64 Wabash miejscowe dolne smugi i R65 Facchini ograniczony film. B: Western, alias CR6 liczony raz. Wysokość≥1000px dotyczy B; nie jest dodatkową bramką A.

Zimowe A2: RoadTour source-dependent i RI49 z widocznym śniegiem. Europejska droga A2: RI49 w Polsce oraz FR60-003. R70 łączy podpis miejsca fotografii w obwodzie twerskim, widoczną scenę drogową i oficjalny opis geograficzny regionu. To jawny wniosek z dwóch źródeł o kontynencie, nie członkostwie wUE ani GPS. Zimowe/europejskie B0 w rozpoznanym podzbiorze, nie globalne twierdzenie o braku. Progi20/12/6/6 nadal otwarte.

R64 ma duże drzwi1320–1450px ESTIMATED, ale brak dowodu ruchu/zaraz po trasie nie pozwala awansować B. R65 ma obraz627×470 i drzwi320–370px ESTIMATED. Rdza, powłoka, odbicie i cień pozostają odrębne od osadu. Chemia soli z fotografii UNVERIFIED. R61 Nofima ogranicza wyłącznie niepewny typ konkretnego pojazdu, nie samo ucięcie góry. R68 to datowany historyczny kontekst materiałów ZUD GDDKiA z2009/2021, bez dawki DK65 i bez przypisywania chemii drzwi.

R63: snapshot11 przyjętych źródeł sprzed R64/R65, zapisany i zahaszowany przed losowaniem. `random.Random(20261115).sample(sorted(ids),3)` dał FR60-003/Knight009/UR54-001. Agent ponownie obejrzał3/3, bez podmian; root odtworzył hash i losowanie. To samokontrola, nie ślepa recenzja ani losowa próba obecnych13. Indeks P18 R47 ma88/88ID i87URL, z aliasami i renderem; nie88 kwalifikowanych fotografii. Kwarantanna154/159 zachowana.

## Świat

Knyszyn: R19 dwa pełne widoki lamusa z2020, sześć podpór, dach/podcień/przyziemie. KR18 dwa widoki jednego domu Klattów, stan2015; tekstowe cechy NID/UM oddzielone od zdjęć. R21 dwa kadry z Gońca nr11(203), listopad2021, s7, Anna Aneta Molska: pompa na podwyższonym kwadratowym cokole z kratką oraz biały/bordowy słup bez takiego cokołu. Root obejrzał oba przy200% w natywnym PDF. To inna ekspozycja znanego słupa, nie drugi egzemplarz. Piksele źródłowe, GPS, metryka i dokładna ekspozycja nieustalone. Rynek3/4 NID to katalog bez fotografii, nie nowe dachy.

DK65: R25 dwa nowe kadry żółtej farby na jezdni, podpisy27/26.08.2026: odcinki przerywane/zygzak i cienka ciągła krawędź. Root oba obejrzał. To coś innego niż żółte obrzeża tablic R21. Lokalny kilometr galerii nie jest kilometrażem krajowym ani GPS; nie deklarujemy listopadowej organizacji ruchu. R22 jedna wiata w Knyszynie i oddzielny plac, nie dwa przystanki; wcięcie zatoki i relacja do obecnej DK65 nieustalone. KS20/FB19 mają pobocza, zjazd i drzewa bez gatunków/rozstawów z domysłu.

BDL R23/24: punkt w lesie przy istniejącym TC17-02 zwrócił rekord pozaPGL. SO=sosna zwyczajna potwierdzone słownikiem TAKSATOR s20. Surowe species_age100,a_year2017,part_cd5 nie uprawniają do wieku109lat ani udziału50%; odpowiednie powiązania/jednostki nadal UNVERIFIED. Nie odnosić rekordu do każdego drzewa przy drodze. TC17 pomiar wybranej korony do asfaltu około12±4m ESTIMATED nie jest rozstawem pni lub skrajnią. Skala0,3m/px nie jest GSD ani dokładnością orto.

Kolej: R15 urzędowy budżet potwierdza wykonany kat.B ze światłem i dźwiękiem Knyszyn–Krypno, stan31.12.2011; bez ID/km i aktualnego stanu2026. Normy R16 rozdzielają gałęzie kwalifikacjiA–D i warunki przejściowe; gałąźD20km/h nie znosi wspólnego limitu torów. Rozbiórka29+522 i wiadukt29+394 to odrębne dowody. R17 nie znalazł nowego urzędowego powiązania DW671. 3kVDC wynika z PLK, nie z samych przewodów na zdjęciu.

Region: Bernardyni w Tykocinie to jeden kompleks w dwóch kadrach2025, NCND tylko linki. Panorama Moniek AUX nie potwierdza pewnej nazwy centralnej bryły. Ełcka2017 daje dwie nowe ekspozycje uliczne z zasłoniętymi/uciętymi dachami, nie pełne bryły. Białystok: dolne rondo Bieżeństwa dzień/noc oraz dwa kadry Kuronia2017; styki cokołu/trawy/chodnika i dojazdy, bez parametrów lub stanu2026.

## Kontrola i następny krok

Po5f245675d: **570 poprawnych śledzonych JSON,93 rastry≤800px,93 istniejące lokalne ścieżki głównych manifestów,0plików>5MB**. Główne ID unikalne. Zakres diff wobec7f830369c wyłącznie research/codex-refs-s21 i docs/LICENSES.md. Legalne raw pozaGit; media/firmy wyłącznie link-onlyARR; NCND tylko linki; zdjęcia właściciela bez kopii. Bez Unity/adb/kodu gry.

Commons: dwa ograniczone pojedyncze API200, bez nowych obrazów; Flickr nowe pobraniaSTOP. Jedno zawieszone własne git-HTTPS przerwano po weryfikacji procesu; ponowny push zakończył się poprawnie, bez dotykania innych sesji. Live zapisano07:04:54Bruksela, następny około08:05.

Gotowe do scalenia po recenzji lidera: **NIE**. Następne odbiory: R69 brudu, R18 nawierzchni przejazdu i R22 LoD; następnie zimowe europejskie tyły R71. Wyniki robocze nie zwiększają liczników przed odbiorem.
