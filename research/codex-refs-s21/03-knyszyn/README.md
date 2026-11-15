# 03 — Knyszyn: bryły i detale fasad — WIP

Cel: dać sesji rynku rozróżnienia brył, kolorów i detali, które gubią się w ogólnym opisie „1–2 kondygnacje”. Pięć kadrów obejrzano osobno ponownie. To pogłębienie istniejącego K1, **0 nowych pobrań zdjęć**, 5 pomniejszeń lokalnych kopii K1, 0 kadrów link-only. Licencje i autorów ponownie sprawdzono przez Commons API; zapis w `data/licences-commons.json`. Daty 2009/2012/2024, aktualny stan 2026 UNVERIFIED. Miniatury ≤ 800 px. To nie są zdjęcia właściciela.

## Wnioski dla generatora

- 03-001, Rynek 1 (2012): SOURCED [obraz, manifest] — 2 górne okna po prawej stoją w podniesionej części dachu, z nisko schodzącymi połaciami po bokach; z lewej osobna mniejsza część z oknem. Nie wystarczy opisać całości jako prostego pełnego piętra. Pełna konstrukcja/przekrój dachu UNVERIFIED.
- 03-002, UM (2009): SOURCED [obraz] — 2 pełne kondygnacje plus rząd lukarn; głęboka dwupoziomowa loggia, 4 kolumny widoczne w kadrze. Czerwony dach, jasny tynk, żółtobeżowe opaski; kolor fizyczny/RAL UNVERIFIED.
- 03-003, Kościelna 4 (2012): SOURCED [obraz] — parter z szeroką centralną lukarną/balkonem i dużymi połaciami dachu po bokach. Wejście pod 2 łukami, ogrodzenie ceglane z metalowymi przęsłami. Pełny typ i geometria dachu UNVERIFIED poza widocznym kształtem.
- 03-004, kościół (2024): SOURCED [obraz] — jasna fasada, czerwony ostrosłupowy hełm, rozeta, czerwone gzymsy/obróbki; mur przed figurą i czarne dwuramienne latarnie. Bruk układa się w łukowe pasy, nie w regularną prostokątną siatkę.
- 03-005, ceglana fasada przy Rynku (2012): SOURCED [obraz] — 2 pełne poziomy plus okno w szczycie, balkon, podwyższony parter i boczne biegi schodów. Okno w szczycie nie oznacza trzeciego pełnego piętra.

## Luki

Wymiary metryczne i proporcje ortogonalnej elewacji UNVERIFIED: kadry są perspektywiczne. Nie wyprowadzono szerokości z liczby okien ani kondygnacji z wysokości modelu. Budynki 03-001/003 wymagają kontroli bryły z LoD2/ortofoto, szczególnie przed przyjęciem etykiety „dach mansardowy”. Aktualność elewacji/ogrodzeń z 2009/2012 UNVERIFIED. Dzisiejsze pierzeje, DK65 przez miasto i mała architektura wymagają dalszego uzupełnienia. Obrys posadzki fontanny został sprawdzony nowym WMS w 03-006 poniżej; wygląd z poziomu ulicy i układ dysz pozostają UNVERIFIED.


## Uzupełnienie: nowy wycinek GUGiK fontanny (03-006)

**Nowy materiał:** 1 wycinek ortofoto WMS (480×480 px, 48×48 m), pobrany 2026-11-15; 5 wcześniejszych kadrów fasad pozostaje pogłębieniem K1. Żadnych nowych zdjęć ulicznych ani zdjęć właściciela. `data/fountain-wms.json` zawiera pełny URL, bbox EPSG:2180, skalę 0,1 m/px i SHA256. Wycinek obejrzano osobno.

SOURCED [03-006, Geoportal WMS]: w jasnej płaskiej posadzce widoczny kwadratowy ciemny obrys i mały ciemny element przy środku; nie widać strumieni wody ani podniesionej misy. Korony i cienie drzew zasłaniają część otoczenia. Nie określam tego elementu jako kratki odpływowej bez obrazu z ziemi.

ESTIMATED [własny pomiar 03-006]: cztery ręcznie wskazane narożniki `(91,179), (145,169), (156,223), (102,234)` px; odległości euklidesowe ×0,1 m/px i pole wzorem Gaussa. Widoczny obrys ma około **5,5×5,6 m**, pole około **31 m²**; przyjmuję ostrożnie ±0,4 m dla boków (wybór narożników ±2 px, brak pomiaru terenowego). To wymiary **obrysu na posadzce**, nie potwierdzona długość instalacji/dysz ani rozmiar całego okrągłego placu. K1 podawał ~6,3×5,8 m — tej wartości nie powielam jako własnego pomiaru; różnica może wynikać z wyboru krawędzi. Przed skalowaniem modelu zalecane porównanie obu obrysów.

SOURCED [WFS GUGiK, `data/fountain-sheet-2025.xml`]: arkusz N-34-106-B-b-1-4 ma datę 2025-05-27 i piksel 0,1 m. Zapytanie do skorowidza 2026 dla tego bbox zwróciło pustą kolekcję (`data/fountain-sheet-2026.xml`). WMS nie jest czasowo przypięty do arkusza; przyporządkowanie daty to najnowszy znaleziony arkusz w tych zapytaniach, nie gwarancja serwera WMS.

UNVERIFIED: rzeczywista liczba i układ indywidualnych dysz, wysokość strumieni podczas pracy, rodzaj odpływu, dokładny kolor podświetlenia, stan działający w dniu pobrania. Ortofoto nie potwierdza tych szczegółów. OSM API zwróciło429; nie korzystano z niepobranych geometrii i nie próbowano obejścia.


## Komunikaty UM: chronologia i wyposażenie (2 źródła tekstowe link-only)

SOURCED [03-D01, UM, 2023-08-25](https://www.knyszyn.pl/asp/i-%E2%99%A5-knyszyn,239,artykul,1,5400): zrewitalizowany rynek dostępny od2020; fontanna podświetlana, nocą świeci kolorowo. W sierpniu2023 dołożono przenośny podświetlany napis „I ♥ KNYSZYN”. To potwierdza istnienie światła, ale nie liczbę reflektorów, moc ani stałą barwę. Pozycja przenośnego napisu w 2026 UNVERIFIED.

SOURCED [03-D02, UM, 2022-07-21](https://www.knyszyn.pl/asp/nasz-wspolny-rynek---apel-do-mieszkancow,239,artykul,1,4982): po rewitalizacji są brukowane alejki, podświetlana fontanna, ławki i stoliki; w sezonie2022 urząd opisuje czerwone pelargonie w donicach. Nie przenosimy gatunku i koloru sezonowych nasadzeń bezwarunkowo do2026.

**Wniosek dla generatora:** fotografie wnętrza parku sprzed2020 nie są dowodem obecnego układu nawierzchni/wyposażenia. Bryły fasad z2009/2012 również wymagają aktualizacji, choć sama data rewitalizacji nie dowodzi ich przebudowy. Źródła tekstowe są odczytane; zdjęć z komunikatów nie pobrano i nie opisano. Łączny nowy materiał w tym uzupełnieniu: 1 ortofoto + 2 dokumenty tekstowe link-only, 0 nowych fotografii ulicznych; 5 poprzednich fotografii to ponowny przegląd K1.


## Nowe kadry link-only: napis i lampy parkowe (03-L01/L02)

Dwa zdjęcia dołączone do komunikatu UM2023-08-25 otwarto **osobno w Chrome i obejrzano**. Licencja fotografii nieustalona: `link-only, all rights reserved`; brak lokalnych plików zdjęć lub screenshotów. Ścieżki i zapis oględzin w `data/link-only-visual-review.json`. Są to **2 nowe kadry link-only**, odrębne od2 źródeł tekstowych D01/D02.

- SOURCED [03-L01, obraz](https://www.knyszyn.pl/asp/pliki/aktualnosci/img_7820.jpg): białe lica liter, czerwone serce, cienkie podpory napisu w trawniku; za nim proste ciemne słupy z jasnymi głowicami pod szerszym daszkiem. Iglaste drzewo po lewej ma sinawy odcień igieł (gatunek UNVERIFIED). Znak B-36 przy ulicy widoczny w prawym tle, aktualne obowiązywanie2026 UNVERIFIED.
- SOURCED [03-L02, obraz](https://www.knyszyn.pl/asp/pliki/aktualnosci/img_7835noc.jpg): nocą litery jasno zielonkawe, serce różowo-czerwone; pod literami zielonkawa poświata na trawie. Świecą2 widoczne głowice parkowe. Technologia źródeł, fotometria i CCT UNVERIFIED.

**Oba kadry pokazują napis, nie fontannę.** Kolory liter nie są dowodem koloru światła w fontannie. Nie wyprowadzono wysokości liter/słupów ani ich rozstawu z perspektywy; brak skali. Stała/programowalna barwa napisu i jego obecne położenie UNVERIFIED. W komunikacie D01 napis jest opisany jako przenośny.


## Fontanna: opis projektu z grudnia 2019 (03-D03)

SOURCED [Nowy Goniec Knyszyński nr 12 (181), grudzień 2019, str. 8](https://www.knyszyn.pl/asp/pliki/download/goniec12.pdf): projekt przewidywał **3 rodzaje dysz**, **4 obiegi wody**, maksymalny strumień **2,5 m** oraz reflektory podświetlenia. Rodzajów nie należy mylić z liczbą pojedynczych dysz. Ten sam opis przewidywał kostkę granitową na alejkach oraz nowe ławki i kosze. Numer i datę odczytano z okładki, całą stronę 8 odczytano z PDF przez pypdf.

Są to **parametry projektowane w 2019**, nie pomiar fontanny ani odbiór wyposażenia. Komunikaty UM z 2022/2023 potwierdzają działającą podświetlaną fontannę, ale nie potwierdzają zgodności liczby obiegów/dysz i wysokości strumieni. Zainstalowana liczba dysz, ich rozmieszczenie, program pracy i maksymalna osiągana wysokość w 2026 pozostają UNVERIFIED. Dokument nie podaje mocy/reflektorów/CCT. Do shadera i modelu używać jako warunkowego punktu odniesienia do weryfikacji, nie dowodu obecnego stanu.

PDF ma 17 069 352 B i pozostaje wyłącznie w `Data/raw/refs/codex-s21/03-knyszyn/goniec12.pdf`. SHA256 i lokalizacja danych w `data/goniec2019-fontanna.json`. W repo tylko parafraza z URL, bez zdjęć ani reprodukcji PDF. Źródło archiwalnej specyfikacji technicznej odrzucono przy błędzie certyfikatu TLS; nie obchodzono zabezpieczeń.


## Wysokości i bryły: pogłębienie lokalnego LoD2 (03-M01)

Nowa analiza bez pobierania danych. Lokalny ZIP: `Data/raw/gugik/lod2-2017-2008/2008_lod2_gml.zip`; SHA zgodny z manifestem źródłowym. GUGiK, CC BY 4.0. Wybrane budynki mają **aktZrodla=2016**, mimo nazwy produktu LoD2-2017. To nie jest pomiar z 2026 r. Obrysy adresowe pochodzą z lokalnego PBF OSM z 2026-11-08 (© OpenStreetMap contributors, ODbL 1.0), a nie z ewidencji gruntów.

Wyniki = **ESTIMATED: obliczenia z historycznej geometrii**. Metoda: dopasowanie wielokątów GroundSurface do obrysu OSM przez pole części wspólnej / pole sumy (IoU); maksymalna wysokość RoofSurface minus mediana wysokości GroundSurface danego modelu. Układ EPSG:2180, wysokości PL-KRON86-NH. Zaokrąglenie do 0,1 m nie oznacza dokładności pomiaru 0,1 m.

| Obiekt wg OSM | OSM way | IoU | Maksymalny dach nad GroundSurface |
|---|---|---|---|
| Rynek 1 — kandydat | 300667350 | 0,67 | ~8,7 m |
| Kościelna 4 | 294345656 | 0,87 | ~7,0 m |
| UM Rynek 39, dwie części LoD2 | 294345008 | 0,88 dla sumy części | ~14,4 m oraz ~15,0 m, osobne poziomy GroundSurface |
| Kościół — kandydat | 294345650 | 0,75 | ~33,4 m |

**Minimum RoofSurface nie jest wysokością okapu:** niskie połacie ganków/przybudówek mogą zaniżać tę wartość. Nie zamieniamy wysokości modelu na liczbę kondygnacji. Różnice obrysów, uproszczenia LoD2 i data źródła wykluczają traktowanie liczb jako inwentaryzacji obecnych fasad. LoD2 nie potwierdza pełnego układu lukarn i podniesionych części dachu widocznych na zdjęciach.

`files/03-roof-plan-analysis.png` obejrzano po wygenerowaniu; poprawiono odstępy etykiet. Kolor oznacza wysokość, a nie kolor pokrycia. Przerywane obrysy pokazują różnice wobec OSM. Pliki `data/lod2-target-candidates.json`, `lod2-target-summary.json` i `osm-target-buildings.json` zachowują identyfikatory, atrybuty, wierzchołki i obliczenia. Wykres i podsumowanie odtwarza `tools/roof_analysis.py` (Python z matplotlib, pyproj i shapely). To analiza referencyjna; kod generatora pozostaje poza zakresem.


## Lokalna kontrola zdjęć właściciela — wyłącznie obserwacje tekstowe

Zgodnie z `docs/owner/OWNER-PHOTOS-KNYSZYN.md` lokalnie obejrzano osobno dwa dzienne kadry fontanny oraz trzy kadry fasady. W repo **nie zapisano żadnego zdjęcia, miniatury, wycinka ani embedu**. Nie przesyłano plików do usług zewnętrznych. Kadr nocny wskazany jako prywatny pominięto. Nie opisano osób i nie użyto ich jako skali. Ślad referencji, ograniczenia i porównanie z projektem zapisano wyłącznie tekstowo w `data/owner-fontanna-observations.json`. Daty z nazw pozostają UNVERIFIED (brak EXIF/GPS).

SOURCED [lokalne kadry OWN-F01/F02]: fontanna ma płaską mokrą posadzkę, najwyższy pionowy strumień w centralnej strefie oraz niższe strumienie i niskie spienione wypływy. Strumienie częściowo się nakładają; **liczby pojedynczych dysz nie da się wiarygodnie policzyć**. Plac otacza szara drobna kostka o nieregularnych licach, układana w łukowe pasy. W tle ławki z brązowymi poziomymi listwami i ciemną konstrukcją, proste ciemne słupy parkowe z jasnymi głowicami/daszkami, trawniki i duże drzewa. Brak potwierdzenia gatunków drzew i rodzaju kamienia z samego kadru.

**Porównanie projektu 2019:** nie stwierdzono podstaw do liczbowej rozbieżności. Trzy rodzaje mechanicznych dysz, cztery obiegi i maksymalny strumień 2,5 m pozostają UNVERIFIED dla rzeczywistej instalacji; różne wysokości lub spienienie strumieni nie dowodzą typów dysz ani obiegów. Nie ustalono działania i barwy reflektorów na podstawie kadrów dziennych. Różnica wobec samego ortofoto: kadry z ziemi potwierdzają działającą w chwili zdjęcia fontannę bez wystającej misy i układ kostki w łuki, czego obraz z góry nie rozstrzygał w szczegółach.

SOURCED [OWN-B01]: osobny kadr pokazuje dwa pełne poziomy okien, poddasze z czerwonymi lukarnami, kremowo-szarą fasadę z poziomymi pasami i czerwonymi rurami spustowymi oraz ogrodzenie budowlane. Adres UNVERIFIED; nie przypisano tej fasady do konkretnego obrysu LoD2.

Niezależna recenzja obliczeń (agent brud,15.11.2026): PASS. Odtworzono SHA źródłowegoZIP, pięć obiektów, wysokości, IoU i zgodność osi; wykres obejrzany także przez koordynatora. Szczegóły w `data/roof-peer-review.json`. Recenzja rachunków nie potwierdza aktualności geometrii ani urzędowej identyfikacji adresowej modeli.

Bieżące działanie instalacji w listopadzie 2026 r. pozostaje UNVERIFIED; obserwacje odnoszą się wyłącznie do chwili wykonania prywatnych kadrów.

Dwa dodatkowe kadry fasady (OWN-B02/B03) potwierdzają zawijanie jasnych poziomych pasów na narożniku, białe ramy z czerwonymi parapetami, ciemny cokół, narożnik między skrzydłami oraz mały daszek pod balkonem. To obserwacje kształtu i kolorów w chwili zdjęcia. Adres, rozstaw pasów, wymiary oraz obecny stan robót pozostają UNVERIFIED; nie przypisano fasady do modelu LoD2 bez lokalizacji.

## Kolejny obieg fasad i ulic — new-round2

Dodano5 rekordów w new-round2/manifest.csv i głównym manifeście (teraz17):3 nowe źródła względem K1, dwa ponowne przeglądy istniejącychK1-P06/P22 bez kopiowania obrazów. Nowe fotografie Henryka Borawskiego, CC BY-SA3.0,2012-06-09: dwie fasady i detal tabliczki42. Koordynator osobno obejrzał wszystkie3 nowe miniatury: zgodność opisów PASS. Nazwy adresów z metadanych nie są niezależnym ustaleniem lokalizacji. Niebieskiej bryły z oknami na różnych wysokościach nie upraszczać do dwóch pełnych kondygnacji. Historyczny wlotDK65 z2009 nie potwierdza obecnego ronda. Nowych współczesnych ujęć trasyDK65 w tej porcji0.

## Gminne źródła2024–2026 — municipal-round3

Cztery nowe dokumenty tekstowe (manifest główny teraz21 wierszy), bez nowych zdjęć. Konkurs otoczeniaUM z2026 dotyczy koncepcji i przyszłej dokumentacji, nie stanowi potwierdzenia wykonania. Rozstrzygnięcie06.05.2026 odczytał też koordynator: ocena29.04,5 prac, dokumentacja dopiero planowana. Informacja gminy o braku posiadanej cyfrowej dokumentacji do modelowania budynku nie jest dowodem nieistnienia geometrii LoD2 GUGiK użytej oddzielnie. Umowa Rynek6 z2024 zapowiada zmiany, bez potwierdzenia odbioru. Regulamin DOCX sprawdzony read-only: brak jawnej publicznej licencji wejściowych fotografiiZIP; archiwum niepobrane i PENDING-VISUAL. Szczegóły municipal-round3/README.md i legal-check.json.

## Rynek6 — wykonana modernizacja i fotografie2025

03/rynek6-round4 zawiera2 dokumenty i2 fotografie link-only. SOURCED [komunikat6381 z27.11.2025]: zakończenie inwestycji12.11.2025; przeprowadzka była jeszcze zapowiadana, dnia otwarcia nie ustalono. Dokument urzędowy opisuje użytkowanie Rynek6 przez bibliotekę według31.12.2025, lecz wymienia teżRynek38; nie stwierdzono wyłączności lokalizacji. Dwa kadry zewnętrzne w Gońcu11(250), listopad2025, s4 obejrzano osobno i niezależnie przez dwóch agentów: kremowo-szara elewacja, schody i balustrady, czerwony dach z lukarnami. Podpis Fot.UrszulaCitkowska dotyczy grupy zdjęć; daty ekspozycji UNVERIFIED. Brak kopii PDF/obrazów. Nie utożsamiono ze starszymi nieustalonymi fasadami.

Fontanna-round5:1 nowy dokument gminny z15.12.2023 o zimowej bombce w miejscu letniej fontanny; fotografii nie oglądano i nie opisano. To nie dowód świecącej wody ani parametrów dysz. Łącznie główny manifest26 rekordów; nowe lokalne rastry w tych dwóch porcjach0.

Dodatkowy historyczny kadr ulicy przy Rynku:04-dk65/mapillary-browser-round2,04M2-002 (picturehoover,27.06.2020, CC BY-SA4.0 wg oficjalnej pomocy). Chodniki, schody, drewniana fasada i przewody, bez odczytu adresu. Nie zdublowano rekordu w manifeście03 ani licznikach; GPS kamery i stan2026 UNVERIFIED.


Mapillary-town-round6: dwa nowe, osobno obejrzane kadry picturehoover z 27.06.2020: Kościelna (zielona bryła ze szczytem, chodnik i łaty asfaltu) oraz Rynek (ceglana poczta, schody, sąsiednia drewniana fasada). Obserwacje i ograniczenia w podkatalogu. SOURCED [manifest i przegląd UI]: główny manifest 28 rekordów; ta porcja 2 link-only, 0 pobrań. Nie potwierdzają stanu 2026, GPS kamery ani formalnej liczby kondygnacji.
