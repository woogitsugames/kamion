# 02 — Brud tylnych drzwi naczepy — WIP

Cel: ≥ 20 kadrów brudnych dwuskrzydłowych drzwi naczep, w tym ≥ 6 zimowych i ≥ 6 europejskich. **Kryteria niespełnione: 0 / 0 / 0 kwalifikowanych.** W manifeście 8 lokalnych i obejrzanych kadrów oraz 2 link-only (jeden pomocniczy i jeden nowy pozytywny jakościowo): 3 odrzucone, 1 wzorzec czysty, 1 rdza/wiek, 1 zimowy kontekst klapy solówki oraz 1 link-only małego zabrudzenia; dodatkowo 2 znane pozytywne wzorce P18 ponownie wykorzystane. Dodatkowy screening obejmuje 8 nowych obejrzanych oryginałów (w tym ten 1 kadr rdzy), zapisanych poza gitem; 7 pozostałych odrzucono bez kopiowania miniatur do gita. Nie są dowodem rozkładu brudu. Liczby powyżej to zliczenie wierszy manifestu.

## Wynik przeglądu

- 02-001: SOURCED [obraz, link w manifeście] — zimowy zestaw widoczny z boku, bez widoku tylnych drzwi.
- 02-002: SOURCED [obraz] — załadunek skrzyni od góry; brak widoku tylnych drzwi.
- 02-003: SOURCED [obraz] — solówka ze zbiornikiem; nie jest naczepą ze skrzynią.
- 02-004: SOURCED [obraz] — czyste drzwi, poza statystyką osadu. To znany projektowi kadr P18-107, ponownie obejrzany; nie jest nowym materiałem M61-FIX. Osobno obejrzano wycinek lewej lampy z oryginału; E-numer nieczytelny. Nie kwalifikuje się także jako nowy dowód homologacji.

## Luki

UNVERIFIED: wysokość i intensywność filmu brudnego, położenie i liczba smug, udziały stref, rozkład zimowej soli. Ze zdjęcia śniegu nie wnioskujemy o chemicznym składzie osadu. Nie wyliczono statystyk brudu z odrzuconych kadrów. Poszukiwania trwają.

Openverse API zwróciło HTTP 403 dla pojedynczego zapytania `dirty truck rear`, bez prób obejścia. Commons API zadziałało ponownie; pobrania oryginałów rozdzielono 12 sekundami. Oryginały i metadane poza gitem w `Data/raw/refs/codex-s21/02-brud`. Miniatury ≤ 800 px; licencje i autorzy per kadr w manifeście. Kadry tylko do referencji, nie tekstury.

## Screening dodatkowy 15.11

`screening-2026-11-15.csv`: 8 nowych oryginałów obejrzanych osobno (kandydaci raw5/6/7/8/11/12/13/14). Kadr kontenera 02-005 osobno także na wycinku dolnej części drzwi. Rdzawe plamki rozpoczynają się przy dolnej krawędzi paneli i obrzeżu ramy, a długie cienkie rdzawe ślady przy szczelinie i krawędziach. Brud drogowy/rozbryzg UNVERIFIED, więc nie zwiększa mianownika. Łączna wysokość drzwi na oryginale około 1400 px (ESTIMATED z pełnego kadru), lecz sama duża rozdzielczość nie zmienia kwalifikacji.

Kandydaci9/10 nie pobrani (PD poza filtrem bieżącej serii); kandydat15 Line of trucks zwrócił HTTP429: nie pobrano, nie obejrzano, bez retry. Przerwano pobieranie z Commons. **Nowe kwalifikowane brudne drzwi:0; europejskie0; zimowe0.** Kolejny obieg powinien przejść na inne źródła lub szukać konkretnych tylnych widoków floty z licencją CC. Odrzucenia nie są podstawą statystyki rozkładu brudu.

## Flickr CC — kolejny obieg

Publiczny search Flickr HTTP200 z filtrem licencji 4 (BY) / 5 (BY-SA) / 9 (CC0): cztery zapytania, po 25 metadanych wyników. Czterech wybranych kandydatów nie udało się pobrać (HTTP403). Po zgłoszonym 429 dla static hostu przerwano dalsze próby. Jedną publiczną fotostronę sprawdzono w Chrome przez CUA: metadane i CC BY 2.0 były widoczne, ale właściwy obraz pozostał czarny na zrzucie także po zamknięciu cookies. **Żaden z tych kandydatów nie jest obejrzanym kadrem ani wpisem manifestu zdjęć; wzrost liczników 0.** Log metadanych i testu w `flickr-screening-2026-11-15.json`. Nie zapisano HTML zawierającego zbędne dane runtime ani nie użyto logowania/CAPTCHA.

## Materiały zimowego utrzymania — dane dokumentacyjne

02-D01 (GDDKiA, 02.11.2026): SOURCED [pełny HTML, sekcja planu sezonu 2026/2027] — w skali kraju wymieniono sól drogową, chlorek wapnia i materiały uszorstniające. To kontekst krajowy, bez potwierdzenia składu mieszaniny stosowanej na DK65.

02-D02 (Oddział Białystok, 20.01.2026): SOURCED [pełny tekst jednostronicowej odpowiedzi przetargowej, pkt 1] — uziarnienie piasku 1–2 mm dla dostawy ZUD sezonu 2026. Lokalna kopia i wizualny zrzut PDF nie powstały (timeout); wartość pochodzi z pełnego odczytu tekstowego, nie z obrazu.

**Dawka g/m² na DK65, procent NaCl w dostawie lokalnej, aktualny standard ZUD dawnego odcinka po otwarciu S19 oraz skład i rozkład osadu na drzwiach pozostają UNVERIFIED.** Wielkość ziarna na jezdni nie oznacza tej samej wielkości cząstek przyklejonych do naczepy. Nie wyprowadzono odsetka soli, wysokości filmu, koloru ani smużenia z danych o utrzymaniu drogi. Dwa wiersze dokumentacyjne nie zwiększają liczby kadrów.

## Tabela dawek — odczyt archiwalny oczekuje obrazu

`data/zud2006-table2-PENDING-VISUAL.csv` to robocza transkrypcja tekstowa tablicy 2 z **2006**, s. 36–37. Nie jest wersją 2017 ani aktualnym przepisem. Kod A oznacza prewencję gołoledzi/lodowicy/szronu; B — zapobieganie przywieraniu śniegu; C — likwidację śliskości/cienkich pozostałości po pługu. Wszystkie dawki dotyczą jezdni, g/m².

**NIEGOTOWE do użycia jako pełna tabela**: tekst pominął wiersz A dla −3…−6°C; ten wiersz ma UNVERIFIED. Nie uzupełniono go z innej wersji. PDF 2017, lokalne pobranie 2006 i obraz stron były niedostępne (timeout/blank). Szczegóły w `data/zud-table-access-check.json`. Roboczego pliku nie traktować jako zamknięcia luki dawek ani jako wejścia generatora. Nie ma lokalnego snapshotu PDF/SHA.

## Zimowe kadry stock — obejrzany podgląd, wyłącznie link-only

02-006: SOURCED [fotostrona Getty 2208838382 i obejrzany obraz] — Bośnia i Hercegowina, autor MASTER, kolekcja Moment, widoczna etykieta Non-AI. Data zdjęcia UNVERIFIED; 07.06.2025 to upload. Podgląd pokazuje słabe zabrudzenie jasnych dwuskrzydłowych drzwi: rozproszony szarobeżowy film i cienkie pionowe ślady. Na belce poniżej drzwi zabrudzenie jest mocniejsze. Brak wiarygodnej identyfikacji soli, błota pośniegowego lub składu chemicznego; zimowy kontekst wspierają tytuł oraz białe drzewa. Fizyczna wysokość stref i kierunek geograficzny UNVERIFIED.

Obejrzano osobno także trzy kadry tej serii (log `getty-screening-2026-11-15.json`): dwa powtarzają czerwony zestaw, trzeci pokazuje inny pojazd zbyt daleko do rozkładu osadu. Nie zwiększają liczników. **Kryterium brudnych drzwi >=1000 px na zweryfikowanym obrazie pozostaje niespełnione**: podgląd 02-006 ma drzwi około 320 px wysokości (ESTIMATED); deklarowane 8636 × 5760 dotyczy niedostępnego oryginału, a nie obejrzanej rozdzielczości drzwi. Delta ścisłych kryteriów: 0 / 0 / 0. Link-only obejrzane pomocnicze: 1. Materiałów komercyjnych ani zrzutów obrazu nie pobrano; tylko URL i własny opis. Royalty-free nie oznacza CC ani otrzymanej licencji.


### Kontrola publicznego zoomu Getty

02-006 obejrzano ponownie w zwykłej galerii Zoom: wyrenderowany obraz ma naturalnie 2048 × 1366 px (SOURCED [read-only DOM obrazu galerii]), wyświetlony 1303 × 869 px. Drzwi około 370 px na ekranie i około 580 px w naturalnym podglądzie (ESTIMATED z proporcji, nie pomiar oryginału); nadal poniżej progu 1000 px. Nie powiększano sztucznie miniatury. Dodatkowy kadr 181541451 obejrzany osobno w Zoom odrzucono: jasny prosty tył bez wiarygodnego brudu i bez czytelnej konstrukcji dwuskrzydłowych drzwi.

Łącznie ta seria screeningu obejmuje 5 różnych kadrów, około 3 pojazdów/scen (ESTIMATED z obrazów); trzykrotny czerwony zestaw to jeden pojazd. Ponowny Zoom 02-006 nie jest nowym kadrem. Przyrost kwalifikowanych M61 pozostaje 0. Publiczny PDF gov.pl ze zdjęciem naczepy w zimowym otoczeniu był niedostępny wizualnie (timeout); Shutterstock pokazał Device Check. Nie użyto tych nieobejrzanych kandydatów ani nie obchodzono blokad.


## Lokalny przegląd manifestów i nowy kontekst zimowy

Przejrzano 61 lokalnych manifestów CSV; filtr terminów zimowych i ciężarowych dał 19 wierszy kandydatów (zapis `data/local-winter-manifest-search-2026-11-15.json`). Nie znaleziono lokalnego archiwum fotografii P18 w sprawdzonym głównym katalogu research ani Data/raw; nie zmieniano cudzych danych. Najmocniejszy znany kandydat P18-118 został pobrany ponownie z Commons i obejrzany w oryginale: zamknięte drzwi z prętami są częściowo zasłonięte panelami aerodynamicznymi, dolny pas ma rzadkie szare cętki. To kadr już wykorzystany, więc wzrost liczników nowych zdjęć 0.

Nowy 02-007 (Heavy filthy): SOURCED [opis autora Commons] — Glasgow, 29.01.2010, śnieżyca; CC BY-SA 4.0, Chris McKenna (Thryduulf). Osobno obejrzany oryginał i wycinek pokazują gęsty szarobrązowy film, napis odsłaniający jaśniejszą powierzchnię i ciemne pionowe smugi poniżej. ESTIMATED: ślady spływu głównie w dolnej połowie, sam film niemal na całej widocznej klapie. Fizyczne wysokości i skład białego materiału przy zamknięciu UNVERIFIED. To **solówka z pojedynczą klapą/platformą**, dlatego stanowi tylko jakościowy kontekst zimowego brudu i nie spełnia kryterium dwuskrzydłowych drzwi naczepy. Oryginał 3648 × 2736 poza gitem, miniatury ≤800 px.

Nowy kandydat Old Trailer Abandoned in the Snow (CC BY 2.0, Cindy Shebley) po obejrzeniu miniatury okazał się przyczepą kempingową widzianą z boku — odrzucony, bez miniatury w repo. Wyniki i SHA surowych plików w `data/local-winter-recheck-results-2026-11-15.json`. **Przyrost ścisłych progów M61: 0; nowy pomocniczy kadr zimowy/europejski: 1, jeden pojazd.**


## Kolejny obieg — europejskie naczepy poza zimą

Przegląd kategorii Krone trailers i dwóch celowanych zapytań Commons dał trzy nowe pobrane kadry do osobnego obejrzenia (pełne miniatury, dodatkowo wycinek drzwi Ribnitz). Ribnitz-Damgarten: jasne drzwi z niskimi zamkami i drobnymi kreskami/otarciami; nie rozpoznano filmu drogowego ani mokrych smug. Big white lorry: kabina i bok, brak tylnych drzwi. Altenwerder Damm: podwozie kontenerowe bez skrzyni. Wszystkie odrzucone, delta M61 0. Nie opisano pory jako jesień ani warunków jako mokre bez dowodu. Szczegóły i SHA w `data/europe-autumn-candidates-2026-11-15.json`; surowe pliki kandydatów18–20 poza gitem, bez dodatkowych miniatur w repo. Czwarty wynik 640 × 384 px odrzucono już na metadanych rozdzielczości, bez pobierania i bez opisu nieobejrzanego obrazu.


## Porównanie dwóch znanych pozytywnych wzorców P18

**02-008 = P18-121; 02-009 = P18-158. Istniejący P18, nie nowy kadr M61-FIX.** Oba pliki odczytano z lokalnego `research/_incoming/claude-p18-trailer-soiling-files-v2-2026-11-15/files`, bez ponownego pobierania. Osobno obejrzano pełne kadry i wycinki drzwi/progu. Poprzednia informacja o nieznalezieniu lokalnego archiwum P18 była zbyt szeroka: wcześniejsze wyszukiwanie pomijało ignorowany katalog `_incoming`; wyszukiwanie z `-uuu` znalazło zdjęcia i ZIP. Nie zmieniano źródłowych plików innych agentów.

| Cecha widoczna | 02-008 / P18-121 | 02-009 / P18-158 |
|---|---|---|
| Drzwi | Jasne, dwa skrzydła i środkowa szczelina | Czerwone, dwa skrzydła, cztery pionowe pręty |
| Film na panelach | Cienki szary, drobno smugowany, wyraźniejszy u góry | Delikatny jaśniejszy nalot na czerwieni |
| Miejscowe ślady | Ciemne pionowe ślady przy prawej zewnętrznej krawędzi, środek/dół | Ciemniejszy napis na prawym skrzydle; wycierki przy prawym uchwycie i tabliczce, słabsze przy lewym uchwycie |
| Próg / belka | Ciemne poplamienie listwy; szarobrunatne nieregularne plamy na białej dolnej belce | Matowy szary próg i wsporniki z gęstym pionowym smużeniem |
| Pułapka interpretacji | Cienkiego filmu nie opisywać jako jednolicie grubej warstwy błota | Ostre cienie prętów i zawiasów nie są smugami brudu |

Obserwacje z obrazu SOURCED [poszczególne URL w manifeście]. Położenie śladów jest jakościowe; wysokość fizyczna i chemiczny skład osadu UNVERIFIED. Udział soli pozostaje UNVERIFIED. Lokalna wysokość drzwi około 500–600 px i 650–700 px (ESTIMATED z obrazów), więc nie spełniają progu 1000 px. Nie powiększano zdjęć sztucznie. Wersja P18-158 ma lokalnie 960 × 1199, choć aktualne metadane źródła deklarują 1093 × 1365; większej wersji nie pobierano.

Licencje zweryfikowane ponownie w Commons: 02-008 Jaggery, CC BY-SA 2.0; 02-009 Eric Polk, CC BY-SA 4.0. Snapshot w `data/reused-p18-source-metadata.json`, niezależne obserwacje i SHA lokalnych wersji w `data/reused-p18-observations-2026-11-15.json`. Miniatury i wycinki repo ≤800 px. **Znane pozytywne wzorce: 2 kadry / 2 pojazdy, w tym 1 zimowy i europejski. Nowe fotografie: 0; wzrost ścisłego M61: 0.** Nie doliczać ich drugi raz do zbioru P18.


## Nowy pozytywny wzorzec z Flickr: 02-010

**NOWE zdjęcie brudnych dwuskrzydłowych drzwi, jakościowo potwierdzone obrazem**, bez dopisywania do progu rozdzielczości M61. Flickr230839170, Harold Hollingsworth, CC BY-SA2.0; obejrzany indywidualnie publiczny podgląd 768 × 1024 px (SOURCED [DOM wyrenderowanego obrazu]). Pełny obraz pokazuje tył skrzyni z dwiema jasnymi drzwiami, dwoma prętami zamków i brudem: górny pas/górna połowa mają nierówny szarobrunatny film i liczne pionowe ciemniejsze ślady. Środek jaśniejszy, dolne obrzeże i okolice zamknięć ciemniej poplamione. Resztki naklejki po prawej nie są plamą brudu. Obserwacje SOURCED [obraz fotostrony w manifeście]; skład chemiczny UNVERIFIED.

Drzwi około550px w podglądzie (ESTIMATED), oryginał wg metadanych ma960 × 1280, nie został pobrany ani obejrzany. Kraj, data wykonania i kalendarzowa zima UNVERIFIED; 01.09.2006 to upload. Widoczne białe płaty w krajobrazie nie uprawniają do przypisania soli ani miesiąca. **Nowe pozytywne jakościowo:1kadr /1pojazd; ścisły wzrost M61>=1000px:0.** Zdjęcie nie występowało w lokalnych manifestach P18; było jedynie w dawnym nieobejrzanym surowym wyniku wyszukiwania. Nie pobrano fotografii, użyto link-only. Metadane tylko fotografii, bez danych runtime, w `data/flickr-230839170-public-metadata.json`; wynik obserwacji w `data/flickr-230839170-observation.json`.

Podglądy kategorii Rear views of trucks pozwoliły też odrzucić bez pobierania Big Rigs (cysterna) i LKW-Sattezug Rückseite (niska klapa/platforma; PD-self poza filtrem CC). Nie opisano z nich brudu drzwi.


### Następny obieg Flickr — duży kandydat oczekuje obrazu

Kandydat4433883530 „Dirty”, Bill Stilwell (icathing), ma na publicznej fotostronie datę wykonania17.02.2010 i upload14.03.2010; CC BY-SA2.0 potwierdzono na fotostronie i stronie publicznych rozmiarów. Ta ostatnia deklaruje oryginał3444 × 2584. Obejrzano tylko miniaturę w wynikach, **pełny obraz nie został obejrzany**: hero czarny, original brokenimage i naturalne0 × 0. Jedna próba dokładnego URL oryginału zwróciłaHTTP429; host live.staticflickr.com wstrzymany, bez wariantów/retry. Brak wpisu zdjęcia w manifeście i brak wzrostu liczników. Log `data/flickr-4433883530-access.json`; nie wyprowadzono stref/koloru/rozdzielczości drzwi z tytułu ani z metadanych rozmiaru całego obrazu.

Publiczny search trailer rear był zdominowany przez niepasujące obiekty; wynik van trailer4874408570 wykluczono opisem autora jako przyczepę z fragmentu Dodge Maxivan, bez opisu nieobejrzanego obrazu. Jego selektywne publiczne metadane w `data/flickr-4874408570-public-metadata.json`. Dodatkowy search trailer doors zachowano jako25 metadanych kandydatów w `data/flickr-trailer-doors-candidates.json`, nie jako obejrzane fotografie. Wszystkie te pliki zawierają wyłącznie wybrane dane fotografii; brak danych runtime i uwierzytelniających.


### Niezależna kopia4433883530 i kontrola nowego Commons

Nie znaleziono niezależnej kopii4433883530: wyszukiwarka poID z wyłączeniemFlickr, indeksOpenverse oraz CommonsAPI poID/autorze zwróciły0 pasujących wyników. To wynik wskazanych wyszukiwań, nie dowód nieistnienia kopii; szczegóły w `data/flickr-4433883530-independent-copy-check.json`. Nie ponawiano static hostu Flickr ani OpenverseAPI po wcześniejszym403.

Nowy Commons kandydat Dot Foods Distribution Truck Whitmore Lake Michigan, Dwight Burdette, CC BY3.0, 06.02.2012, oryginał4752 × 3168 obejrzany jako pełny lokalny podgląd i osobny wycinek drzwi/progu. Dwa skrzydła są z pikowanej blachy: regularne jasne/ciemne romby i odbicia nie stanowią dowodu filmu. Wyraźniejsze pionowe szare/szarobrązowe ślady występują na listwie/progu, a dolna rama jest brunatnawo przygaszona. Przy okuciach punktowe rude przebarwienia. Brud na samych panelach pozostaje nierozstrzygnięty, więc odrzucono jako nowy pozytywny wzorzec brudnych drzwi. Nie wnioskowano o soli z lutowej daty. Oryginał6,23MB wyłącznie poza gitem, brak dodatkowych repo miniaturek. Log ze źródłem/licencją/SHA: `data/candidate-23-dotfoods-observation.json`. Delta M61:0; 02-010 pozostaje stabilny.


### Obieg galerii firmowych i medialnych — tylko link-only

W relacji trans.info z08.02.2021 indywidualnie obejrzany główny kadr (podpis Twitter/@GDDKiA_Opole) pokazuje pług i czerwoną kabinę od przodu w opadzie śniegu, bez tylnych drzwi naczepy. Odrzucony. W galerii The Mobile Wash Company kadr opisany jako „Dry van trailer, rear doors” po obejrzeniu pokazał **pojedynczą segmentową roletę i windę**, nie parę skrzydeł. Odrzucony; nie klasyfikowano konstrukcji z altu. Brak nowych pozytywnych kadrów. Oba źródła link-only, all rights reserved; brak zapisu zdjęć/PDF/zrzutów.

Dziennik `data/company-media-screening-2026-11-15.json` rozdziela2 obejrzane odrzucenia od niedostępnych źródeł: GITD timeout, nswiecie403 bez retry, bidcom brak odczytu. Publiczny dokument PKO dotyczył lawety, więc nie przeniesiono jego zimowych fotografii do statystyki drzwi. Kraj i daty konkretnych kadrów pozostają UNVERIFIED tam, gdzie nie ma danych autora; adresu myjni nie użyto jako geotagu fotografii. Zimowe otoczenie nie zostało użyte do identyfikacji soli.


### Obieg nordycki — selekcja bez pobierania oryginałów

Nowy fiński kadr Full-trailer truck on Mäkelänkatu (JIP, CC BY-SA4.0, 25.07.2023, Helsinki) obejrzano indywidualnie w przeglądarce: dwa skrzydła i cztery pręty są widoczne, lecz błyszczące panele nie pokazują czytelnego filmu ani smug brudu. Odrzucono; źródło dodatkowo identyfikuje przyczepę dyszlową. Dwa inne podglądy, Red Star rear view (Szwecja w zapytaniu) oraz Varelevering i Thomas Angells gate, pozostały białe — **nieobejrzane**, bez opisu obrazu i bez retry oryginału. Pierwszy ma cały obraz1300 × 925, więc próg1000px drzwi jest niemożliwy. Kraju drugiego nie wyprowadzono z tytułu.

Siatkę zimowych wyników Finlandii potraktowano wyłącznie jako selekcję; dominujące pługi/wywrotki/załadunek śniegu i frontowe ujęcia nie zostały wpisami manifestu. Szczegóły `data/nordic-screening-results-2026-11-15.json`, metadane wyszukiwania `data/nordic-candidates-2026-11-15.json`. Nowe pobrane obrazy0, nowe kwalifikowane0, nowych miniaturek wGit0. Białych podglądów nie nazwano potwierdzonymHTTP429; mimo to nie próbowano wariantów ani serii oryginałów.

## Korekta typu pojazdu02-010

Audyt data/flickr-230839170-type-audit.json: z tylnego kadru pewne są drzwi skrzyni, koła i belka; brak potwierdzenia sprzęgu/siodła, podpór, kabiny lub całego podwozia. Naczepa vs solówka/drawbar pozostaje UNVERIFIED. Poprawiono wcześniejsze bezwarunkowe określenie naczepa w głównym manifeście i obserwacjach. Wzorzec filmu/smug pozostaje jakościowo użyteczny, ale nie kwalifikuje rodzaju pojazdu do M61; ścisły licznik nadal0.


### Kontrola typu przed pobraniem — nowy obieg Commons

Selekcja metadanych `intitle:trailer intitle:rear filetype:bitmap` zwróciła30 plików, w tym9 znanychP18. Żaden nowy nie przeszedł jednocześnie warunków: jawne semi-trailer w opisie autora, skrzynia z podwójnymi drzwiami, odpowiednia licencja i szansa1000px drzwi. Nowe tytuły dotyczyły m.in. cysterny, przyczep specjalnych, wagonu i pojazdów wystawowych; słowa trailer nie zamieniano automatycznie na naczepę. Dodatkowy opis Groenewegen potwierdzał naczepę, lecz płaską platformę. ICR end doors to znane kadry rdzyP18, bez ponownego zliczania.

Brak nowych pobrań, brak nowych oględzin i brak wzrostu liczników. To wynik selekcji metadanych, nie opis obrazów. Dziennik `data/semitrailer-preselection-result-2026-11-15.json` wskazuje dwa selektywne snapshoty źródłowe. Dwa nieprzydatne pełne zestawy początkowych wyników (główniePDF/niepasujące obrazy) usunięto; ukończonych audytów nie zmieniano.

Dalszy audyt typu istniejących P18: 02-008 autor opisuje tylko jako long lorry, więc naczepa/solówka/drawbar UNVERIFIED. 02-009 autor Commons wprost identyfikuje semi-trailer — typ SOURCED z opisu autora, nie z samego tylnego kadru. Nie wyprowadzono kategorii UE. Dwa pozytywne wzorce rozkładu brudu nie oznaczają dwóch niezależnie potwierdzonych naczep; nowe ścisłe M61 nadal0. Dowód w data/reused-p18-type-audit.json.
