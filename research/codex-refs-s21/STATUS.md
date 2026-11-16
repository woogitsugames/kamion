# Status codex-refs-s21

Stan danych po 3a5be2b2a, 16.11.2026. Cel ciągły aktywny; research/codex-refs-s21 → PR100 → main, bez scalania. Czasy zapisów live w Brukseli.

| Pakiet | Rekordy głównego manifestu | Ograniczenia |
|---|---:|---|
| 01 lampy | 64 | Nie 64 homologowanych tylnych lamp. |
| 02 brud | 29 | 27 kadrów (14 lokalnych, 13 link-only) + 2 dokumenty, również odrzucenia/AUX. |
| 03 Knyszyn | 44 | Historyczne kadry i dane; zdjęcia właściciela wyłącznie opis tekstowy. |
| 04 DK65 | 31 | Projekt, ortofoto i przepisy mają oddzielne daty i zakresy. |
| 05 kolej 38 | 22 | Mapowanie lokalnego przejazdu do ID/kilometrażu nadal otwarte. |
| 06 pierścień | 40 | Różne miasta i daty, bez łączenia w stan 2026. |
| 07 Białystok/Dojlidy | 22 | Geometria i dokumenty; lokalne B-5/B-18/wyjątki nadal niepotwierdzone. |

M59: rozpoznana dolna granica 5 tylnych PASS (EuropointII, EuropointIII dwa odrębne kadry, EcopointII klosz, RA38 ScaniaE2) + 1 warunkowy UP4-03. W grupie PASS ON i zmierzch/noc nadal 0. RC39 ma E2, ale niejednoznaczny łańcuch zastosowania i drugi plik SUPPORT; nie dodaje unconditional PASS. Nie wymagamy pełnego numeru, pięciu rodzin ani kompletnej obudowy jako dodatkowych warunków nieobecnych w FIX. EMC 10R nie zastępuje fotometrii.

Tablicowe: 10 samodzielnych kadrów 5 reprezentowanych fizycznych urządzeń (SIM, Proplast, Hella HP36, Vignal EPP96 i EPP98 HP37), plus 5 detali SUPPORT. W HP37 dokładne OE i wspólna rodzina serwisowa mają różną siłę dowodu zastosowania; nie oznacza to 5 udowodnionych demontaży ciężarowych ani 5 czytelnych E. Regpoint pozostaje warunkowy. Progi 15 tylnych / 4 ON / 3 zmierzch-noc / 5 tablicowych wymagają dalszej recenzji zakresu.

M61: A≥20 łącznie; B≥12 NOWYCH z drzwiami ≥1000px i ruchem/zaraz po trasie. Dolna granica A11 z ograniczeniami: Knight158, Western182, Premier183, Krone lekki film, RoadTour source-dependent, AutoReview39, RI49, UR54, UR55 miejscowe smugi, RG57 Tonar i FR60-003 lekki dolny nalot S.KO. B1 Western, raz z aliasem CR6. Zimowe A2: RoadTour source-dependent i RI49 z rzeczywiście widocznym śniegiem. Europejska droga A1: RI49, A1 Nowa Wieś w Polsce. Zimowe/Europa B0 potwierdzonych w rozpoznanym podzbiorze, nie globalne zera. RI49: 1201×904px cały obraz, drzwi ESTIMATED 500–560px; B_FAIL_GEOMETRY. Skład chemiczny osadu UNVERIFIED. Wszystkie progi 20/12/6/6 nadal otwarte.

Audyt P18: indeks R47 ma 88/88 ID z istniejącymi odsyłaczami i zgodnymi ID; 87 znormalizowanych URL. Zawiera aliasy i render, więc nie 88 fotografii ani kwalifikacji. Walidacja odsyłaczy nie jest nowym oglądem wszystkich starych zdjęć. R41 zachowuje kwarantannę błędnie nazwanych lokalnych154/159, bez przypisywania im licencji bieżących źródeł.

Knyszyn: MF15 dwa nowe historyczne widoki Rynku: ciemne listwy ławki, łukowe metalowe podparcia, latarnia z szerokim daszkiem, wachlarzowy bruk i fasada z dwoma poziomami otworów. Publikacja 30.06.2020 nie ustala ekspozycji; bez nowych wymiarów, RAL, formalnej liczby kondygnacji i adresu z samego kadru. Prywatne zdjęcia nadal bez kopii.

DK65: TC17 dwa nowe 800px ortofragmenty GUGiK, układy koron przy K1 km18 i20. Skala mapowa 0,3m/px, nie GSD ani dokładność pomiaru. Wybrana korona do krawędzi asfaltu około 12±4m ESTIMATED; nie rozstaw pni/skrajnia/gatunek. TP18 legenda i plan S19 z03.2022 pokazują symbole zieleni, lecz 0 potwierdzonych numerowanych drzew i gatunków; plan nie jest stanem powykonawczym2026. Fasty objazd2025 i rondo Krynice pozostają odrębnymi lokalizacjami.

Kolej: 3kVDC wynika z zestawienia PLK i regulaminu, nie samych przewodów na zdjęciu. Dwa kadry Starosielce2020 PLK link-only BY-NC-ND pokazują tory/podsypkę/peron/sieć; nie lokalny przejazd w Knyszynie. Rozbiórka29+522 kat.B i projekt wiaduktu29+394 nie są automatycznie jednym miejscem ani mapowaniem DW671.

Białystok: BR14 dwa Mapillary Batorego dzień/noc z2019, tylko przeglądarka i OSM. Brak czytelnej osi w kadrze nie jest dowodem formalnej organizacji ruchu. Dane UM o pracach2026 osobno. Art20 PoRD ze snapshotu04.11.2026: ciężki zestaw 50 w zabudowie, 20 w strefie zamieszkania, poza zabudową80 na wymienionych klasach i70 na pozostałych; bez przypisywania lokalnych limitów z ogólnej reguły. §27 B33>50 w zabudowie nie podnosi limitu ciężkiego zestawu.

Normy UNECE mają datowane wersje i konkretne paragrafy w pakietach. R148 UE2021: minimum kat.5 0,6cd; maksimum single11a1000,11b/11c1200cd z warunkami. Nie deklarujemy z tego pełnej aktualności2026. R48 pakiet skuteczny26.09.2025 nie rozstrzyga homologacji starego pojazdu. Odblask CIL mcd/lx i emisja cd pozostają rozdzielone.

Losowy audyt lamp ze snapshotu60 (bieżący główny ma64): [R46](01-lampy/qualification-audit-round46/README.md), seed2026111602, 12/60 rekordów =20%,13 obrazów,0zastępstw i0NOT_REVIEWED. CO WIDAĆ i wartość sprawdzone równolegle,12PASS_WITH_LIMITS bez nowych sprzeczności. To nie audyt pozostałych48, czterech dodanych później ani wszystkich licencji/zastosowań. Cztery nowe przednie kadry R51/52 mają osobny celowany ogląd root. Snapshot skopiowano po pierwszych oglądach, ale z hashem zgodnym z zapisanym przed oglądami; kolejność jawna. Stary audyt10/49 pozostaje osobny. R42 wcześniej skorygowano kolor/kształt makra etykiety, które odziedziczyły opis całej lampy.

R43: oficjalny tekst ECE/TRANS/WP.29/2018/159/Rev.1 z03.01.2019, wskazany na okładce R1502020, pobrany zUN. Root i agent niezależnie obejrzeli bitmapę tabeli5/§5.2.3.1: α20′ →450/200/150, α1°30′ →12/8/8mcd/lx przy kolumnachV/H0/0,±10/0,±5/±20. Nie podmieniono dowodu bitmapy2020 ani nie ogłoszono aktualności2026. To odblask, nie emisja cd.

FB19: dwa nowe kadry Fast z27.06.2020, picturehoover, agent i root w publicznym UI Mapillary/OSM. Jeden czerwonołososiowy zjazd, ziarniste pobocze i trawiaste obniżenie.0potwierdzonych przystanków. K1km10.417/dk65-02 dotyczy punktu selekcji, nie udowodnionej pozycji obu kamer. Bez geometrii przepustu, materiału i wymiarów z domysłu. Główny04=29.

Najnowszy brud: UR54-001 wyraźniejszy film prawego skrzydła; UR55-004 A_PASS_LIMITED_LOCAL tylko krótkie smugi na czerwonym prawym panelu pod odblaskiem, reszta przeważnie czysta. A11 z wcześniejszymi ograniczeniami; B1, zimaA2 iEuropa-drogaA1 bez dalszego przyrostu. R56 trzy ekspozycje dwóch chłodni pozostająPENDING, a obraz myjni nie ma pary drzwi. Nie liczono światła/rdzy/napraw/cienia jako brudu drogowego.

Kontrola śledzonych referencji po3a5be2b2a:520 poprawnychJSON,93rastry≤800px,0plików>5MB; główneID unikalne,93lokalne ścieżki istnieją po poprawnym rozdzieleniu pól wieloplikowych. Zakres diff wobec7f830369c wyłącznie research/codex-refs-s21 i docs/LICENSES.md. Duże/raw pozaGit; prywatne zdjęcia bez kopii; media/firmy wyłącznie link-onlyARR. Commons ograniczony pojedynczy obieg; Flickr nowe pobraniaSTOP po429. BezUnity/adb/kodu gry.

Najnowszy odbiór 16.11.2026 około06:07Bruksela:

- R51 Scania E1/4147 oraz R52 MAN/ZKW E12/112029: po2kadry jednego przedniego urządzenia, root niezależnie obejrzał makra1:1 i pełne przody. Nie zwiększają tylnego15; ON/noc niepotwierdzone. Główny01=64.
- R48 R148: obejrzane bitmapy oficjalnych UN Am5 i Rev1Am2. Minimum kat.5 w obu6·10^-1=0,6cd; stary dodatni wykładnik Am5 był błędem ekstrakcji. Maksimum single11a-c wydrukowano120cd w Am5 i1200cd w Rev1Am2: rzeczywista różnica dokumentów, przyczyna prawna i aktualność2026 nieustalone. Nie przyjęto120 jako aktualnej nastawy. Cztery aktywne wiersze porównania skorygowane, kopia starego zapisu zachowana; D600cd to oddzielna kolumna.
- R57 Tonar mocny film prawie całych obu skrzydeł; R60 S.KO348842 lekki ziarnisty nalot dolnych pól. Korozja zamków osobno. A11 z ograniczeniami/B1, zimaA2 iEuropa-drogaA1. R60 ma źródłowy podpis obwodu twerskiego i scenę drogową, geograficzny podzbiór oczekuje źródła; nie użyto regionu rejestracji. R59 trzy kadry bez awansu. Główny02=29.
- KR18 dom Klattów przy Kościelnej6: dwa pełniejsze widoki bryły Joanny Kotyńskiej-Stetkiewicz, stan2015, NID NCND wyłącznie linki. NID/UM: parterowy, pierwotnie częściowo mieszkalne poddasze, dach dwuspadowy, ganek4słupowy, po3okna przy wejściu i7osi tyłu. Tekstowe dane osobno od fotografii; formalny obecny stan kondygnacji i metryka UNVERIFIED. EM17 dwa nowe detale elewacji/przyziemia,0nowych potwierdzonych budynków. Główny03=44.
- KS20 dwa Mapillary27.06.2020 podejścia do Knyszyna: ziarniste pobocze, trawiaste obniżenie, drzewa i słupy. K1km24.6/dk65-11 to punkt selekcji, nie pewny GPS kamery. Bez gatunków/rozstawów/wymiarów. Główny04=31.
- R15 kolej: agent i root obejrzeli strony1/113 urzędowego sprawozdania. Druk112,tabela36lp1 potwierdza zakończony nowy przejazd kat.B ze światłem i dźwiękiem Knyszyn–Krypno, stan31.12.2011. 9,01km/7m to cały projekt drogi. Brak LK38/ID/km i aktualnego stanu2026. Główny05=22,0nowych zdjęć.
- R13 region: dwa nowe widoki jednego zespołu Bernardynów,Tykocin Klasztorna1, Katarzyna Niedźwiecka,listopad2025. Root oba obejrzał. Pełny widoczny obrys dachów, dziedziniec, długa elewacja, lukarny, podziały i grunt. NCND tylko linki; formalne kondygnacje, wymiary, materiały i2026 UNVERIFIED. Główny06=40.

Po3a5be2b2a lokalny HEAD równy zdalnej gałęzi;520 śledzonychJSON poprawnych,93rastry≤800px,0plików>5MB. GłówneID unikalne. Nowe robocze child R61/R18 poza tym snapshotem. Zakres diff tylko research/licencje.

Gotowe do scalenia po recenzji lidera: NIE. Cel aktywny. Następne: zimowe tyłyR61, tylne lampyR53 i rondo Pamięci BieżeństwaR18. Live zapisano06:02:51Bruksela, następny około07:03.
