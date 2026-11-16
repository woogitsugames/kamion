# 07 — Białystok trasa C / Dojlidy: referencje i luki — WIP

Stan ewidencji głównej na 16.11.2026: **18 rekordów** (SOURCED: lokalny `manifest.csv`). Rekordy obejmują także dokumenty, AUX i odrzucenia; nie są licznikiem zaakceptowanych fotografii. Bieżące kwalifikacje i ograniczenia: [STATUS](../STATUS.md). Starsze opisy poniżej są datowanymi etapami pracy.

Wcześniejszy etap:15rekordów głównego manifestu. Są dokumenty, znany kadr ronda,2historyczneMapillary i3nowe link-only fotografieUM. Liczba rekordów nie jest liczbą zdjęć ani kwalifikacji. Poniższe starsze sekcje zachowują historię poprzednich przeglądów; bieżące dodatki wostatnichsekcjach.

Cel: uzupełnić backlog S21 źródłami, nie zmieniając generatorów. W pierwszym przeglądzie historycznym: **0 kadrów pobranych, 0 kadrów link-only**, 4 wiersze dokumentacyjne (3 fakty z jednego komunikatu + 1 kontrola publicznych metadanych). To nie jest pakiet zdjęciowy. Nie pobrano ani nie opisano zdjęć z galerii miejskiej.

## B-040 — ruch ciężarowy w Dojlidach

SOURCED [07-D01…D03, komunikat UM/ZDM z 19.11.2025, linki w manifeście]. Źródło rozróżnia zapowiedziane ograniczenie tonażu od już zmienionego układu pasów. Nie dowodzi zakończenia całego wdrożenia ani wyjątków dla dostaw. **Nie zamyka B-040** i nie wystarcza do odblokowania zleceń KAN/BIAFORM. Aktualny stan 2026, symbole znaków B-5/B-18 oraz tabliczki wyjątków pozostają UNVERIFIED.

## B-131 — dane osi dróg miejskich

SOURCED [07-D04, oba endpointy, pola w data/]: usługa jest publiczna, lecz brak wypełnionej informacji licencyjnej. To ponowna kontrola konkretnego datasetu Drogi osie, nie audyt wszystkich danych miasta. **LEGAL_REVIEW_REQUIRED pozostaje**. Nie pobrano geometrii i nie przypisano CC BY do usługi.

## Kolejka dalszego researchu z BACKLOG-S21

- B-123: Batorego, Brzeska/Buska, Maczka zimą, rondo Bieżeństwa z oka kierowcy, osiedlowe ulice i stan tablic 2025–2026 — brak nowego zweryfikowanego kadru w tej rundzie.
- B-132 / B-043…047 / B-056…057: Kuronia 3, Kuronia 2 i Rosti — elewacje, wysokości i bramy wymagają nowych widoków; istniejące proporcje z kadrów nie są pomiarami metrycznymi.
- B-119: licencje KartaView/Panoramax/Mapillary wymagają osobnej kontroli warunków źródła; tej rundy nie użyto tych kadrów.
- B-120: końcówki barier i aktualne źródła prawne to osobny etap; brak nowych liczb w tym przeglądzie.

Źródło identyfikatorów: `docs/owner/BACKLOG-S21.md` z bieżącego worktree. Nie oznaczono żadnej luki jako zamkniętej bez dowodu. Dokumenty mają oznaczoną datę, obrazów nie zastępują opisem tekstowym.

## B-123 — kontrola istniejącego ronda Bieżeństwa

07-P01: ponownie obejrzany G3-028 = P1-004, bez pobrania i duplikowania obrazu. SOURCED [obraz]: niskie brązowawe krzewy, trawa, jezdnia, pas czerwonego gzymsu i walcowe słupy estakady. Pokrywy śnieżnej nie rozpoznano; etykieta sezon=śnieg w P1-004 jest błędna dla tego obrazu. Zapisano erratę w data/rondo-biezenstwa-recheck.json bez zmiany cudzych manifestów. To znany boczny widok, nie nowy dojazd z oka kierowcy, więc B-123 pozostaje otwarte. Łącznie5 wierszy:4 dokumentacyjne i1 ponownie obejrzany kadr; nowych zdjęć0.

## B-040 — raport za2025 potwierdza raportowane wdrożenie

07-D05/D06: SOURCED [Raport o stanie Miasta Białegostoku za2025, s101; URL w manifeście i data/annual-report-2025-source.json] — w sprawozdaniu działań odnotowano wprowadzenie zakazu dla ciężarówek na Suchowolca (Plażowa–Ciołkowskiego) oraz ograniczenia8ton na Mickiewicza (Kuronia–Ciołkowskiego). To źródło wdrożenia raportowanego za2025, uzupełniające wcześniejszą zapowiedź prasową. Okładkę2025 i pełną stronę101 odczytano tekstowo i obejrzano w renderach; mylący tytuł indeksu2024 nie został użyty. PDF15MB i rendery poza gitem. Rodzaj znaku B-5/B-18, definicja masy, tabliczki wyjątków i stan15.11.2026 UNVERIFIED; B-040 nadal otwarte. Brak nowych fotografii.

## B-131 — miejskie warunki, nadal bez rozstrzygnięcia datasetu

07-D07 i licence-round2/: znaleziono publiczne warunki BIP i zarządzenie973/21. §3 i§6 trzeba oceniać łącznie; prawa pierwotne do konkretnej bazy nie zostały wykazane. Świeże metadane potwierdzają wydawcę miejskiego, ale licenseInfo nadal null, copyrightText pusty. Brak jawnego powiązania warunków z tym itemem, więc LEGAL_REVIEW_REQUIRED pozostaje. Geometrii nie pobierano. Główny manifest teraz8 rekordów.


KartaView-licence-round3: indeks oficjalnej sekcji4 wskazuje BY-SA4.0 fotografii, oddzielnie od MIT kodu; wymagany kredyt w źródle. Bezpośrednia strona dała shell, pełny regulamin nieodczytany. To częściowa kontrola B-119, bez zdjęć i bez zatwierdzenia wcześniejszych klatek. Manifest główny:9 rekordów.


Mapillary-gates-round4:2 nowe, indywidualnie obejrzane link-only obrazy czadzik2018 i zsolt2017. Dojazd Mickiewicza/Karpińskiego z wyspami/kreskowaniem/zieleń oraz rozpoznany szyldem sklepBIAFORM z jasnym pawilonem i żółtą szczeblową bramą. Nadruk20m nie jest pomiarem; małeSTOP na bramie nie zostało zakwalifikowane do kodeksowegoB-20. Nie potwierdzono bramKAN/Rosti, funkcji logistycznej i przejezdności ciężarówki. Danehistoryczne nie domykają B040/B123. Main11rekordów,0pobrań.

## TrasaC — kontrola nowszego materiału, obieg5

[Celowany screening](route-c-signs-round5/README.md):3pobrane i osobno obejrzane podglądyCC0 z2024 odrzucono jako boczne elewacje/parking/zieleń, bez portalu. Żadnych nowych obrazów wGit ani przyjętych kadrów; główny manifest nadal11rekordów. Dwa ograniczone zapytania publicznego katalogu federacyjnegoPanoramax dla2024–15.11.2026 zwróciły features[]; nie dowód braku zdjęć we wszystkich instancjach. B006/B007, treść tablicy675Centrum, liczba paneli/wierszy/wysięgników i wysokość kamery pozostająUNVERIFIED. Nie opisano zdjęć z tytułów.

## Publiczny projekt Alei Tysiąclecia — obieg6

Główny manifest12rekordów. [DokumentBIP](route-c-public-plans-round6/README.md):1nowy opisPAB,0fotografii. PDF9/druk13 iPDF14/druk18 obejrzane przezagenta i koordynatora: projekt2×2,pas3.50m,chodnik2m,DDR3m,mediana2.5–6m;7projektowanych przystanków z zatokami(5Aleja+1Sokólska+1Kombatantów),zatoka3m/peronokoło20m. ZakresWileńska–teren kolejowyPoleska, data2017.07.05 wyłączniezDocumentInfo, nie datarealizacji. Materiał pomaga parametrom projektowym; nie potwierdza stanu wykonanego ani675Centrum/bramownic2024+. PDF11.67MB i rendery pozaGit, wyłącznie własneparafrazy/link.

## Dojlidy — trzy rzeczywiste widoki UM, obieg7

[Doilidy-signs-round7](dojlidy-signs-round7/README.md):3nowe indywidualnie obejrzane kadry galerii UM19.11.2025, MarcinJakowiak;0pobrań/3link-onlyARR. TablicaZmianaorganizacjiruchu/dojazd, wlotrondaMeyera z dwoma pasami/kreskowaniem/zebrami i czerwonymi przejazdami oraz narożnikSuchowolca/Plażowa z czytelnymi nazwamiulic/wysięgnikami. B5/B18 i wyjątki nie zostały odczytane; materiał nie zamykaB040 i nie potwierdza obecnejprzejezdnościHGV. Koordynator ponownie odczytał pełny tekstUM:tranzyt3.5t osobno odMickiewicza8t; wchwili artykułu znaki ciężarowe dopiero planowano w dalszym etapie. Publikacja nie jest ekspozycją ani stanem2026. Oglądy obrazów wykonałagent, kontrola koordynatora wtejrundzie dotyczyła tekstu.

## B123 — ograniczony przegląd zimowych ulic, obieg8

[Winter-streets-round8](winter-streets-round8/README.md):6konkretnych metadanychMaczka,1podglądCCosobnoobejrzany z25.03.2015. Suchaasfaltowa jezdnia/zieleń i bezlistne drzewa, bezśniegu lub czytelnegobłotapośniegowego — nie zakwalifikowano jako zimowy.0nowychkadrów/0rastrówGit,1podgląd tylko raw. Brak dokładnych kategorii ulic nie dowodzi braku zdjęćtychulic. B123pozostajeotwarte; nieopisanoPDF jako fotografii. BezOSM/Overpass/Chrome, bezstwierdzania nieistnienia obrazów. Głównymanifest15bez zmian.


## Identyfikator organizacji ruchu — runda9

[traffic-order-round9](traffic-order-round9/README.md):publiczny tropSOR200/25/S z rejestruumów pozycja2070,s84PDF, potwierdzony tekstowo także przezroot. Publiczne postępowanie176716 ma19nazw/rozmiarów załączników wedługUI; zawartość nieodczytana,0pobranychSOR/0rysunków/0zdjęć. Nie działało zwykłe pobranie, sessionURLsbezutrwalania i bezobejść. B5/B18/wyjątki/stan2026nadalUNVERIFIED. Cel umowy i jej terminy nie są treścią znaku/datą zatwierdzenia. Główny07ma16rekordów.


## Maczka: śnieg historyczny i osobnyAUX — runda10

[winter-streets-round10](winter-streets-round10/README.md):1nowy historyczny kadrDDRMaczka:luty2012wgporównania źródłowego, widocznyśniegprzykrawędzi/mokrepolazpopękanym asfaltem. Prawymarcowykadr kontrolny nie drugi zimowy. Drugi nowyrekordMaczka/Produkcyjna18.11.2022wgpublikacji:ścianaoporowa/bariera/latarnie, śnieg/błotośniegoweUNVERIFIEDprzezszybę, AUX.2link-onlyARR/0pobrań, obaagentosobnoobejrzał;rootodczytartefaktów bezdrugiegooglądu. Batorego/Brzeska/Buska otwarte; stan2012nie2026/chemiasoliUNVERIFIED. Główny07ma18rekordów. CzysteURLwplik_lub_url, lokatorosobnąkolumnąchildi wopisiemain.

## SchematP10/P11 — runda12

[p10-p11-diagram-round12](p10-p11-diagram-round12/README.md): rzeczywiście obejrzany urzędowy rys.4.2.2.3 na stronie16 Dz.U.2026/132. Dwa poziome wymiarowania0,5m i≥3,0m; liczba s i pionowe przerwy wzoru niewyznaczone. Nie zamknięto całegoP11_GAP ani backloguB129. Jeden schemat/zero nowych zdjęć/pobrań; główny18.

## Art20 i zakresB33 — runda13

[speed-law-round13](speed-law-round13/README.md): osobno obejrzane s32–33 urzędowego snapshotuPoRD04.11.2026; limity50/20 oraz80/70 dla zestawu poza zabudowanym z warunkami rodzaju drogi. Rolnicze40 nie jest limitem ciągnika samochodowego. Pełne4 nowelizacje rozporządzenia znakowego sprawdzone dla§27: podwyższającyB33>50 w zabudowanym nie dotyczy ciężkiego zestawu. Bez nadawania limitu konkretnemu kaflowi i bez kompletnego algorytmu znaków. Główny18 bez zmian.
