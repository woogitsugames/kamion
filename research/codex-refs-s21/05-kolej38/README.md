# 05 — Linia38: elektryfikacja i stan zastany kontra projekt — WIP

Stan bieżący:15 rekordów —6 dokumentacyjnych,4 danychOSM,1orto,2 lokalne fotografie stacji oraz2link-only kadry1przejazdu DW671 z2019. KategoriaB jest udokumentowana dla km29+522 w obwieszczeniu2025; przypisanie do konkretnych fotografii i stan wyposażenia2026 nadalUNVERIFIED. Źródłowe3kV DC uzupełniono z dwóch dokumentówPKP, nie wyłącznie z OSM.

W gicie tylko odnośniki, własne parafrazy i dozwolone miniatury. BinariaPKP oraz ich rendery poza gitem.

## Ustalenia

05-D01/02: SOURCED [PKP PLK, Id12, stan07.09.2026, tabela6,s123 drukowana = strona121 PDF]. Sprawdzono pełny render strony i kontekst sąsiednich wierszy37/39/40. Elektryfikacja jest cechą istniejącego odcinka. Sam Id12 nie podaje napięcia; uzupełnienie3kV DC ma osobną podstawę w traction-parameters-round5 poniżej. W korytarzu Knyszyna nie przyjmować pełnej dwutorowości tylko z planów inwestycji.

05-D03: SOURCED [PKP PLK,15.09.2026, Więcej Rail Baltiki]. Docelowy drugi tor i zastępowanie przejazdów to zakres modernizacji, nie potwierdzenie wykonania w listopadzie2026.

## Luki

Kategorie konkretnych przejazdów A–D, aktualne urządzenia i rogatki, znakiG-3/G-4, materiał nawierzchni, rozstaw i typ słupów oraz wizualny stan podsypki — dla stanu2026 UNVERIFIED; historyczne kadry urządzeń2019 opisano oddzielnie. Stan energetyczny odcinka podczas robót i zamknięcia ruchu nie wynikają z ewidencyjnej cechy „zelektryfikowana”.

## Odczyt i ograniczenia

StarszyURL Id12 z lutego2025 zwraca404; aktualny odnaleziono przez oficjalny katalog instrukcji PKP. Lokalny transfer aktualnegoPDF był krótszy niż nagłówekContent-Length; zapisano bajty poza gitem, Poppler ostrzegł o strukturzeXRef, ale wyrenderował czytelną pełną stronę123. Ta strona została obejrzana; nie poświadczono integralności całegoPDF. Serwer web odczytał dokument255stron i ten sam wiersz. `data/source-read.json` rejestruje tę sytuację. Pojedyncze zapytanie Overpass o tagi linii38 zwróciło406, bez powtarzania i bez wnioskowania z braku odpowiedzi.

## Reguły kategorii i znaków

`regulations.csv`: 7 wpisów z §6, §80 i §81 rozporządzenia MI z09.07.2025, Dz.U.2025poz.1105. Pełne strony3,19,20 obejrzane osobno. ELI przy odczycie15.11.2026 oznacza akt jako obowiązujący, wejście27.08.2025; metadane w `data/eli-2025-1105-status.json`. Według ELI zastąpił m.in. rozporządzenie2015poz.1744 i jego wymienione zmiany. Reguły w tabeli nie przypisują kategorii konkretnym przejazdom. Brak geometrycznych wymiarów samych znaków i rogatek.

## Historyczny kadr stacji

05-P01: ponownie obejrzana fotografia K1-P32 z2013r. SOURCED [obraz, link w manifeście] — poprzeczna brama kratowa sieci trakcyjnej, ukośne wsporniki, podwieszenia i przewody, latarnie peronowe, ciemne podkłady i miejscowa roślinność w torowisku. Typ podkładów i uziarnienie podsypki UNVERIFIED. To 1 miniatura istniejącego kadru,0 nowych pobrań zdjęć; nie jest kadrem przejazdu ani potwierdzeniem wyglądu stacji po modernizacji2026.

## OSM — punkty dalszego poszukiwania, nie inwentaryzacja

05-O01…O03 zachowują identyfikatory trzech węzłów przejazdowych blisko korytarza z istniejącego zapytania K1. Ich tagi nie zawierają wystarczających danych do A–D; brak tagu rogatki nie dowodzi braku rogatki. 05-O04 rozdziela tagi istniejącego napięcia i proposed na moście. Dane, identyfikatory, czasy edycji i hash źródła w `data/osm-crossing-and-voltage-evidence.json`. To ponowne wykorzystanie otwartych danych K1, bez nowego zapytaniaOverpass i bez nowych fotografii. Napięcie3000V jest SOURCED jako tag OSM; niezależną podstawę zarządcy uzupełniono później w traction-parameters-round5. Tego tagu nie przepisano jako urzędowego pola. Proponowane25000V nie są dowodem wykonania.

## Nowe orto przejazdu 038 010 194

05-O05: GUGiK WMS,700×700px, samodzielnie obejrzany. SOURCED [obraz i data/crossing-ortho-review.json]: pojedynczy tor, jasne prostokątne pasy/panele w obrębie szyn, powtarzalne podkłady, szarobrązowy pas podsypki. Nie identyfikowano materiału paneli ani rodzaju kamienia. Kategoria A–D, rogatki, sygnalizatory i krzyże UNVERIFIED — drobne obiekty z góry nie pozwalają rozstrzygnąć wyposażenia. Data zdjęcia UNVERIFIED: WMS bez parametru czasu, nie zapytano jeszcze o arkusz. Kierunek góry to północ geograficzna. To1 nowy pobrany kadr; oryginał poza gitem, kopia referencyjna700px w files.

Uzupełnienie datowania05-O05: SOURCED [WFS Skorowidze2025, pola akt_data/godlo/piksel, pełny URL w JSON] — pokrywający środek arkusz N-34-107-A-c-3-4 ma datę2025-05-25 i piksel0,1m. Zapytanie2026 zwraca gml:null missing. Jest to data arkusza, bez gwarancji przypięcia czasu bieżącego WMS. Nie jest potwierdzeniem stanu listopad2026.

## Kolejny kadr naziemny stacji — ground-round2

05-GR2-03: nowy względemK1 URL Henryka Borawskiego, CC BY-SA3.0,2013-10-29; indywidualnie obejrzany przez agenta i koordynatora. Płyty peronu/przejścia, szyny, podkłady, pas podsypki z roślinnością oraz podwieszenia sieci. Fragment czerwono-białego urządzenia przy brzegu kadru nie potwierdza rogatki drogowej. Nie wykazano przejazduDW671 ani kategoriiA–D. P34duplikat i podobnydoP32 odłożone w dzienniku, bez nowych kopii. Manifest główny ma10 rekordów, nowa miniatura800px.


Mapillary-crossings-round3: sprawdzono3istniejące punktyK1/OSM w publicznymUI z OSM; bez widocznej sekwencji przez tor na bocznych drogach w wybranych widokach, w trzecim takżeAllcaptures. 0 nowo obejrzanych kadrów przejazdu, 0pobrań, bez określenia wyposażenia lub kategoriiA–D. Sąsiedni mały podgląd nie jest pełnymi oględzinami. Nie jest to dowód braku przejazdów ani zdjęć w całym regionie. Main10rekordów bez zmian.


Knyszyn-crossing-round4:2 nowe osobno obejrzane kadry1przejazdu DW671 na północ od stacji, grobin,02.09.2019, MapillaryCCBY-SA4.0 według oficjalnej pomocy. 0pobrań. Widać rzeczywiste przecięcie szyn z jezdnią i prostokątne panele oraz przednie pary soczewek/daszki, czerwono-białe słupy i podniesione ramiona z pomarańczowym napędem. NapisS2 tylko odczyt urządzenia, nie kategoria. A–D, materiał paneli, pełna liczba ramion, G-3/G-4, identyfikatorPLK, emisja/napięcie i aktualność2026 UNVERIFIED. Główny manifest12rekordów.


## Typ sieci i oficjalna podstawa3kV DC — traction-parameters-round5

SOURCED [załącznik2.12, „Załącznik2.12dane”!A351:F351]: linia38, torN, km4,298–98,598, literalny typYzC120-2C. N oznacza tor nieparzysty, nie liczbę torów. Daty nagłówka odrębne: wydruk08.10.2026 i stan25.10.2026. Brak pola napięcia w tym arkuszu.

SOURCED [Regulamin sieci2025/2026v45, aktualizacja12.11.2026,2.3.9ust.1,6,s24]: zelektryfikowane liniePLK są zasilane3kV DC, parametry sieci określa załącznik2.12. **Wniosek z dwóch dokumentów:3000V DC dla wskazanego elektryfikowanego odcinka linii38**, nie pomiar i nie stan chwilowego załączenia podczas robót. Oba odczyty, komórki i render strony potwierdził niezależny agent. Nie rozszerzono tego wiersza na całą linię38.

Typu sieci nie przeliczano z kodu na wysokość/rozstaw słupów. Parametr prędkości kolumnyG dotyczy jazdy z jednym pracującym odbierakiem i nie jest prędkością każdego pociągu. OryginalnyXLSX123617B ma pełne poprawneCRC; oba binaria/hash/render poza gitem. 2nowe rekordy dokumentacyjne,0zdjęć.

## Pierwszy urzędowy punkt kategorii — obieg6

[ObwieszczenieWojewody18.11.2025](crossing-category-source-round6/README.md), publiczneUMMońki, powołana decyzja13.11.2025. SOURCED[s3/17pkt5]:przejazdLK38kmistn29+522(kat.B) w wykazie planowanych rozbiórek. SOURCED[s2/17pkt4lit.b]:projektowanywiaduktkm29+394, odrębna konstrukcja/miara. Trzy skany obejrzane przez agenta i koordynatora. Nie przypisano doDW671/fotografii2019/IDPLK bez źródłowego mapowania; nie dowodzi wykonania ani obecnego statusu2026. G3/G4 i wyposażenie UNVERIFIED. 0nowychfotografii, PDF/rendery wyłącznie pozaGit. Wskazane na s3sieciLPN15kV nie są napięciem trakcyjnym.

## Mapowanie punktu — obieg7 bez potwierdzenia

[Celowana kontrola](crossing-location-round7/README.md):brak poszukiwanego punktu w zapisanymK1;1Overpass406 i1OSMAPI429, po429STOPbezretry/hostwariantów. Nie uzyskano węzła,ref ani topologiiDW671;nie przypisano hipotezy038029522 jako odczytanegoIDPLK. Główny manifest nadal15rekordów. Dowódkat.Bzobwieszczenia pozostaje wyłącznieprzy swoimkm29+522. Nie stwierdzono braku przejazdu wOSM/terenie.

## Galerie modernizacji — obieg8 bez nowej lokalnej fotografii

[Modernisation-photos-round8](modernisation-photos-round8/README.md):sprawdzono znane komunikaty/projekt i jeden kandydat banku zdjęćPKP osobiście obejrzany. Fotografia pokazuje podpisywanie dokumentów przy stole; szerokie tagiFasty/Knyszyn nie są lokalizacją fotograficzną toru ani przejazdu. Odrzucono, nie opisano jej jako podsypki/słupów.0nowych kwalifikowanych kadrów/0pobrań,0zmiany głównego15. Podpisy konferencji/plansz i brak pewnego punktu nie dowodzą nieistnienia zdjęć wcałym archiwum. LicencjaBY-NC-ND odrzuconego źródła nie jest otwartą licencją gry; pozostały tylko własne uwagi i odsyłacze.


## Historyczny budynek Fasty — runda9

[fasty-ground-round9](fasty-ground-round9/README.md):2osobno obejrzane kadry1budynku, MaliniakCCBYSA2.5 iHenrykBorawskiCCBYSA3.0. Pierwsza data2006-06-04 to upload, ekspozycjaUNVERIFIED; druga26.07.2013. Podcień/ławka/schody/falisty dach/tablica informacyjna;0widocznych przejazdów/szyn/podsypki. Materiał dachu i stan2026nieustalone.1małyoryginał+1podgląd pozaGit,2miniatury≤800px. Główny05ma17rekordów.


## Komunikaty wykonawców — runda10

[contractor-ground-round10](contractor-ground-round10/README.md):3pełne teksty komunikatów INTOP/Unibep/PUW,0kandydatów zdjęciowych z pewnym podpisemFasty/Knyszyn,0obrazów obejrzanych/pobranych. Umowa/wybór oferty/pozwolenie i data publikacji nie lokalizują ilustracji ani nie dowodzą wykonania lub uruchomienia infrastruktury. Ograniczony przegląd, bez globalnego wniosku o nieistnieniu zdjęć. Główny17bez zmian.


## Dalszy trop mapowania — runda11

[crossing-document-map-round11](crossing-document-map-round11/README.md):odczytano wyłącznie nagłówek publicznego dokumentu RDOŚ, docelowa strona nie załadowała się wweb ani przy pojedynczym zwykłym otwarciu wChrome. Jeden download skończył się timeoutem bez pliku, bez dalszych pobrań i wariantów hosta. Fragment indeksu wymienia kilka dróg/obiektów, lecz nie dowodzi relacjiDW671→29+522. Nie przyjęto mapowania ani nowego materiału do generatora; zakres odcinka2od25+204 jest właściwy do dalszej weryfikacji29km.0mediów/0pobrań zachowanych/0OSM-Overpass/Commons. Główny17 bez zmian; PENDING nie oznacza braku dokumentów.
