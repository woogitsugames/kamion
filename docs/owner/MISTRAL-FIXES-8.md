# Poprawki do PR-ów Mistrala r8 (s17, 2026-11-13)

Każdy blok wklej do NOWEJ sesji Mistrala (sesja, która zrobiła PR, już go nie śledzi). Przeglądy: `docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p11-p12.md`.

---

## M47-FIX — PR #39 (zdjęcia Dojlidy/Krywlany): opisy kadrów niezgodne z treścią

```
Repo woogitsugames/kamion. Popraw istniejący PR #39 (gałąź research/mistral-p11-dojlidy-photos) — dopisz commity do TEJ gałęzi, nie twórz nowego PR. Najpierw `git fetch && git rebase origin/main`.
Przegląd (docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p11-p12.md w origin/main — przeczytaj) wykazał: w próbie 12 obejrzanych JPG 6 jest opisanych błędnie. P11-090, P11-091, P11-092 to zdjęcia zabawkowego robota, nie hal przy Kuronia — USUŃ z manifestu (status REJECTED z powodem) i z ZIP. P11-084 to tablica z planem osiedla, P11-094 to hala Rosti (nie brama browaru). Kolumna punkt_opis i lista „15 najlepszych kadrów” w README powstały BEZ oglądania zdjęć — to niedopuszczalne.
ZADANIE: (1) OBEJRZYJ KAŻDY z 143 JPG (model wizyjny) i popraw punkt_opis tak, by opisywał to, co faktycznie widać (obiekt, kierunek, czy to poziom kierowcy); kadry nieprzydatne (wnętrza, zabawki, makiety, dokumenty) → REJECTED z powodem. (2) Kolumna w_kaflu_0166: kafel bialystok-dojlidy EPSG:2180 [779019, 589055, 781067, 591103] — przelicz WGS84→EPSG:2180 (pyproj) i oznacz każdy wiersz true/false; podaj w README ile w kaflu. (3) Nową listę 15 najlepszych kadrów do kamer kontrolnych wybierz WYŁĄCZNIE spośród obejrzanych, w kaflu, z poziomu jezdni. (4) Samokontrola: losuj 20 % z seedem, dla każdego wklej w README jedno zdanie „co widać” — zgodne z manifestem.
Nowy ZIP: mistral-p11-dojlidy-photos-files-v2.zip (bez odrzuconych). W PR komentarz z SUROWYM wyjściem `git diff --stat origin/main` i licznikami (SOURCED/REJECTED, w kaflu). NIE scalaj. Na końcu „M47-FIX gotowe” i koniec.
```

## M48-FIX — PR #40 (landmarki Dojlidy/Krywlany): drobne poprawki przed scaleniem

```
Repo woogitsugames/kamion. Popraw istniejący PR #40 (gałąź research/mistral-p12-dojlidy-landmarks) — commity do TEJ gałęzi. Najpierw `git fetch && git rebase origin/main`.
Przegląd (docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p11-p12.md w origin/main): dane OSM i wysokości zgodne (22/22, 13/14) — dobrze. Do poprawy:
(1) flagi „poza kaflem” liczone względem własnego kafla P12 — przelicz względem kafla bialystok-dojlidy EPSG:2180 [779019, 589055, 781067, 591103] (np. BISON i Odlewnia SĄ w kaflu; hangar Aeroklubu way 304300294 ~360 m na zachód — poza);
(2) wszystkie 5 linków `File:` do zdjęć Commons prowadzi do nieistniejących stron — popraw na rzeczywiste tytuły plików (curid, autorzy i licencje są poprawne — weź tytuł z API po curid);
(3) znak A-11a to „próg zwalniający”, nie „przystanek na żądanie” — popraw;
(4) Art-Glas i Zintronic mają tę samą współrzędną bramy — ustal osobne bramy z OSM (barrier=gate / entrance) albo oznacz UNVERIFIED;
(5) katalog tools/ i ~1,5 MB data/*.json: zostaw w data/ tylko pliki potrzebne do odtworzenia tabeli (landmarks.json, landmark-colors.json, matched-with-roads.json); surowe zrzuty OSM (osm-*.json, area-geom.json) usuń z gałęzi i opisz w README, jak je odtworzyć (zapytanie Overpass); tools/ przenieś do research/mistral/p12-dojlidy-landmarks/tools/ (już tam? — sprawdź `git diff --stat origin/main`), nic poza tym katalogiem.
W PR komentarz z SUROWYM wyjściem `git diff --stat origin/main` i listą zmian 1–5. NIE scalaj. Na końcu „M48-FIX gotowe” i koniec.
```

## M46-FIX — PR #43 (luki zdjęć trasy P1): kadry przypisane do złych ulic

```
Repo woogitsugames/kamion. Popraw istniejący PR #43 (gałąź research/mistral-p1-route-photos-2) — commity do TEJ gałęzi, nie nowy PR. Najpierw `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p1-route-photos-2/.
Przegląd (docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p1b.md w origin/main — przeczytaj) wykazał: metadane z API są wierne, ale 26 z 33 kadrów „OK” pokazuje inną ulicę niż w manifeście. P1B-017…033 to Al. Tysiąclecia (kamera jedzie arterią i mija wloty Bitwy/Białostoczek/Kombatantów/Sokólskiej/Motoszko/Wileńskiej/Skidelskiej), P1B-001…003 to ul. Andersa przy wlocie Batorego, P1B-010…016 to estakada Andersa NAD rondem Pamięci Bieżeństwa (ringu nie widać). P1B-009 to jezdnia A (ta sama sekwencja 1155711), nie B. Opisy typu „przy nr 2”, „na krawędzi ringu” nie odpowiadają zdjęciom.
ZADANIE:
(1) Reguła przypisania: kadr należy do ulicy X tylko gdy odległość do osi X ≤ 25 m ORAZ |azymut kamery − kierunek odcinka X| (mod 180) ≤ 30°; jeśli bliżej (lub lepiej współliniowa) jest inna ulica — przypisz do niej. Przelicz wszystkie 47 wierszy, dodaj kolumny `os_way_id`, `delta_azymutu_deg`; w README opisz regułę.
(2) Przepisz ulica/punkt_opis po OBEJRZENIU każdego JPG (co faktycznie widać: obiekt, skrzyżowanie, drogowskaz). Kadry z Al. Tysiąclecia/Andersa zostaw jako OK pod prawdziwą nazwą — są cenne (zima 2018, wiadukt kolejowy 1955, estakada nad rondem).
(3) Tabela luk w README i opis PR: luka 4 = 0/9 ulic, Batorego = 0, rondo = 0 slotów z poziomu kierowcy (sloty przedefiniuj wg OSM: ring junction=roundabout jest pod estakadą, wjazdy z łącznic Andersa i z Bitwy Białostockiej). Jeśli znajdziesz prawdziwe kadry dla tych luk (KartaView: inne sekwencje; Panoramax; Commons) — dodaj; jeśli nie — wynik negatywny z liczbą przeszukanych kadrów.
(4) Manifest P1 ISTNIEJE: research/gptpro/p1-route-photos/manifest.csv (origin/main). Usuń duplikaty P1B-034 (=P1-004), P1B-036 (=P1-033), P1B-037 (=P1-052), P1B-042 (=P1-053) albo oznacz DUPLIKAT_P1; popraw README/sources.
(5) Autor P1B-037, 039–042 to Rakoon (Commons API), nie „Hollyfeld” — popraw. P1B-005: silne rozmycie ruchu → jakość 2.
(6) Samokontrola: nowe losowanie 20 % z seedem; dla każdego wylosowanego wklej w audit_20_percent.json jedno zdanie „co widać” + nazwę ulicy z OSM i deltę azymutu — sprawdzaj przypisanie, nie tylko zgodność z API.
Nowy ZIP: mistral-p1-route-photos-2-files-v2.zip. W PR komentarz z SUROWYM wyjściem `git diff --stat origin/main` i licznikami (OK/REFERENCJA/ODRZUCONE/DUPLIKAT). NIE scalaj. Na końcu „M46-FIX gotowe” i koniec.
```

## M44-FIX — PR #41 (przepisy ciężarówki): poprawki przed scaleniem + 3 otwarte punkty

```
Repo woogitsugames/kamion. Popraw istniejący PR #41 (gałąź research/mistral-p4-truck-regulations) — commity do TEJ gałęzi, nie nowy PR. Najpierw `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p4-truck-regulations/.
Przegląd (docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p4.md w origin/main — przeczytaj): próba 35/171 → 32 potwierdzone, 1 odrzucony, 2 niesprawdzone; deklaracja „171/171 bez niezgodności” była zawyżona.
POPRAW: (1) P4-134 „22,5 t/oś” — tego cytatu nie ma w 96/53/WE; właściwa wartość dla osi potrójnej naczepy: 24 t (podaj punkt załącznika I i cytat). (2) README: lista zmian 96/53/WE NIE kończy się na 2015/719 — są też 2019/984 i 2019/1242 (do +2 t dla napędów alternatywnych/bezemisyjnych); opisz wpływ na nasz zestaw (40 t bez zmian). (3) Dz.U. 2024 poz. 1709 to akt pierwotny, nie tekst jednolity; sprawdź zmiany 2025/939 i 2026/891 (ELI Sejmu) i opisz, czy dotykają wymiarów/położenia tablic. (4) Etykieta wersji R104 — popraw zgodnie z przeglądem. (5) Lusterko klasy V dla N3: zostaw swoją wersję (obowiązkowe po stronie pasażera), dopisz punkt tabeli R46 i cytat.
OTWARTE (dodaj sekcję z wynikiem albo negatywnym wynikiem i listą sprawdzonych źródeł): (a) R46 — czy system kamera-monitor (CMS) może zastąpić lusterka klas II i IV dla N3 w UE (seria obowiązująca w UE: 04 — potwierdź); (b) rysunek tablicy rejestracyjnej 520×114 mm (rozporządzenie 8.11.2024 i zmiany) — wymiar z rysunku; (c) miejsce montażu tachografu w kabinie (rozp. 165/2014, wykonawcze 2016/799 zał. IC — tylko wymagania widoczności/dostępu dla kierowcy).
W PR komentarz z SUROWYM wyjściem `git diff --stat origin/main` i listą poprawek 1–5 + a–c. NIE scalaj. Na końcu „M44-FIX gotowe” i koniec.
```
