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

## M49-FIX — PR #46 (bramy Dojlidy/Krywlany): PZZ, EC, RS16

```
Repo woogitsugames/kamion. Popraw istniejący PR #46 (gałąź research/mistral-p6-dojlidy-gates) — commity do TEJ gałęzi, nie nowy PR. Najpierw `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p6-dojlidy-gates/.
Przegląd (docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p6p8p9p5.md w origin/main — przeczytaj): pomiary bram G03–G08, G11, G13, G14 i ustalenia org. ruchu potwierdzone w próbie. Do poprawy:
(1) G10 PZZ (M49-010, M49-024): way 248109974 to `service=parking_aisle`, a na ortofoto jego koniec to pusty piaszczysty plac przy biurowcu — to NIE jest wjazd na teren PZZ. Znajdź rzeczywistą bramę drogową PZZ (OSM: barrier=gate/lift_gate na granicy landuse way 339398420 i highway; ortofoto) albo oznacz UNVERIFIED; usuń wartości 11 m / 8,3 m, jeśli nie dotyczą bramy.
(2) G12 EC (M49-012, M49-026): node 3954799626 ma access=no i leży ~400 m od celu P6 — teza „brama dla ciężarówek” wymaga źródła (strona Enea Ciepło: dostawy/wjazd, BIP, ortofoto z widocznymi śladami ciężarówek/wagą). Dołącz do ZIP wycinek ortofoto obejmujący tę bramę (obecny M49-G12.jpg ma bbox P6 i bramy nie pokazuje). Bez źródła: status UNVERIFIED.
(3) RS16 (M49-029): PFU 2020 mówi „oddalona jest od stałego punktu kontroli… ok. 1295m” i „obsługuje ruch… na kierunku do Miasta”. Mierzyłeś od skrzyżowania ze Stoczni Gdańskiej i wpisałeś „kier. Zabłudów” — popraw: pas wjazdowy do miasta; punkt odniesienia = stały punkt kontroli (ustal jego położenie: PFU 2015 „parking przy DK 19”); pobierz/odczytaj „załącznik nr 5” PFU (mapa lokalizacji) z BIP. Status ESTIMATED, dopóki nie ma mapy.
(4) M49-031: cytat TVP3 jest nieweryfikowalny (strona pokazuje tylko tytuł) — cytuj tylko tytuł; datę wejścia w życie oznacz „styczeń 2026 wg tytułu TVP3; komunikat 19.11.2025 daty nie podaje”.
(5) M49-035: Karpińskiego to highway=unclassified (nie tertiary).
(6) Do ZIP dołącz wycinki narożników R-* użyte do promieni (bez nich promieni nie da się sprawdzić).
W PR komentarz z SUROWYM wyjściem `git diff --stat origin/main` i listą zmian 1–6. NIE scalaj. Na końcu „M49-FIX gotowe” i koniec.
```

## M54-FIX — PR #44 (ograniczenia ciężarówek): opisy kadrów i rozmiar zdjęć

```
Repo woogitsugames/kamion. Popraw istniejący PR #44 (gałąź research/mistral-p8-restrictions-3) — commity do TEJ gałęzi, nie nowy PR. Najpierw `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p8-restrictions-3/.
Przegląd (docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p6p8p9p5.md w origin/main): dane OSM (historie tagów), S19 (komunikat MI) i e-TOLL potwierdzone. Do poprawy:
(1) M54-008: tysiac_412f2d02 pokazuje jazdę PO wiadukcie Al. Tysiąclecia (droga nad linią nr 6, bridge=yes layer=1) — nic nie ma nad jezdnią. Przepisz opis; dopisz wniosek „Al. Tysiąclecia nad linią 6: brak ograniczenia skrajni (droga na obiekcie)”.
(2) M54-007: na 6ded8ec0 widać B-26 (zakaz wyprzedzania przez samochody ciężarowe) i B-33 70, nie B-19 — popraw.
(3) OBEJRZYJ wszystkie 40 kadrów (także 10 kadrów S8/Choroszcz, M54-006 — nieprzeanalizowane) i dla każdego zapisz w nowym pliku photos.csv: id, plik, odległość, azymut kamery (z EXIF/sekwencji; Panoramax API daje `view:azimuth`/heading — `az: null` w Twoich metadanych oznacza, że nie pobrano), co widać (1 zdanie), czy obiekt badany jest w kadrze.
(4) Zdjęcia w ZIP mają 2048×1536 — zmniejsz do ≤ 1600 px (nowy ZIP mistral-p8-restrictions-3-files-v2.zip).
(5) README „Ograniczenia” pkt 4: `pdftotext -layout` wyciąga tekst z list MF (sprawdzone) — usuń tezę o nieekstraktowalności i potwierdź M54-025/026 własnym odczytem (cytaty z numerami stron).
(6) Samokontrola: nowe losowanie z seedem obejmujące zgodność opisu kadru z obrazem (nie tylko HTTP/API).
W PR komentarz z SUROWYM wyjściem `git diff --stat origin/main` i listą zmian 1–6. NIE scalaj. Na końcu „M54-FIX gotowe” i koniec.
```

## M50-FIX — PR #45 (meble uliczne): kadry „VERIFIED_WIZJA” niezgodne z obrazem

```
Repo woogitsugames/kamion. Popraw istniejący PR #45 (gałąź research/mistral-p9-furniture-3) — commity do TEJ gałęzi, nie nowy PR. Najpierw `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p9-furniture-3/.
Przegląd (docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p6p8p9p5.md w origin/main): dokumenty (OPZ ZMK, Glasdon, Dz.U. 2019/2311) potwierdzone 1:1 — dobra robota. Zdjęcia NIE: na kadrach 5062587, 1326673477, 1326673829 (hydranty) nie ma hydrantu; 219381941 (U-5a), 1326673805 (żerdź), 993066622 (bariera U-12), 219382225 (szafka) — obiektu nie widać; kadr 1326673717 (ławka) nie jest w ZIP.
ZADANIE:
(1) OBEJRZYJ każdy kadr z wierszy VERIFIED_WIZJA i NOT_FOUND (model wizyjny, po jednym kadrze na wywołanie — jeśli masz limit, rozłóż na kilka tur i commituj po każdej). Dla każdego zapisz w uwagach jedno zdanie „co widać” i pozycję obiektu w kadrze (lewo/środek/prawo, przybliżona odległość). Kadry bez obiektu → NOT_FOUND.
(2) Dla 11 typów znajdź prawdziwe kadry z jezdni (≥ 2 na typ): KartaView — sąsiednie klatki tych samych sekwencji co 5–10 m, kamera skierowana na obiekt (|azymut kamery − azymut do obiektu| ≤ 30°, odległość ≤ 25 m); Panoramax (`view:azimuth`, 23 kadry w kaflu — sprawdź je). Obiekt potwierdzaj z węzłem OSM (emergency=fire_hydrant, barrier=bollard, power=pole, man_made=street_cabinet, amenity=bench/waste_basket/bicycle_parking).
(3) Dołącz do ZIP wszystkie kadry z manifestu (brakuje m.in. 1326673717).
(4) Samokontrola: nowe losowanie 20 % z seedem — dla wierszy zdjęciowych wklej „co widać” i porównaj z kolumną obiekt; dla dokumentów cytat ze strony.
Nowy ZIP: mistral-p9-furniture-3-files-v2.zip. W PR komentarz z SUROWYM wyjściem `git diff --stat origin/main` i licznikami (VERIFIED_WIZJA/NOT_FOUND per typ). NIE scalaj. Na końcu „M50-FIX gotowe” i koniec.
```

## M55-FIX — PR #47 (audio): drobne poprawki przed scaleniem

```
Repo woogitsugames/kamion. Popraw istniejący PR #47 (gałąź research/mistral-p5-audio-3) — commity do TEJ gałęzi. Najpierw `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p5-audio-3/.
Przegląd (docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p6p8p9p5.md w origin/main): licencje, długości (ffprobe 13/13) i opisy autorów potwierdzone; wyniki negatywne dobrze udokumentowane. Popraw:
(1) README/manifest: podglądy MP3 Freesound mają ~175–190 kb/s (VBR), nie „128 kbps” — podaj zmierzony bitrate.
(2) Kolumna atrybucja/uwagi: dla 5 plików Commons CC BY-SA dopisz „tylko referencja — ShareAlike, nie do buildu gry”; dla M55-003 (CC BY 4.0) gotowy tekst atrybucji.
(3) M55-002 (Volvo B8R): wypisz znaczniki czasu 3–5 zmian biegów słyszalnych w nagraniu (mm:ss) i czy słychać przerwę momentu — to jedyny kandydat na AMT.
W PR komentarz z SUROWYM wyjściem `git diff --stat origin/main`. NIE scalaj. Na końcu „M55-FIX gotowe” i koniec.
```

## M52-FIX — PR #48 (nawierzchnie): wymiary P-* z rysunków odczytane błędnie

```
Repo woogitsugames/kamion. Popraw istniejący PR #48 (gałąź research/mistral-p2-surfaces-2) — commity do TEJ gałęzi, nie nowy PR. Najpierw `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p2-surfaces-2/.
Przegląd (docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p6p8p9p5.md w origin/main): wytyczne ZDM 2025 i wymogi (płytki, wyspy) potwierdzone. Zadanie 1 ma błąd metody: podpis pod rysunkiem („0,20 m²/mb”, „0,24 m²/mb”, „0,32 m²/mb”, „0,08 m²/mb”) to ZUŻYCIE FARBY na metr bieżący, nie wymiar. Na rys. 2.2.1.8 (P-3a), 2.2.1.11 (P-5), 2.2.1.12 (P-6) są etykiety „4,00” (kreska) i „2,00” (przerwa) — pominięte, a w ich miejsce podano ESTIMATED z pikseli (2,0–2,4/0,56; 1,77/0,91).
ZADANIE:
(1) Wyrenderuj strony Dz.U. (np. PyMuPDF, 150 dpi) i OBEJRZYJ każdy rysunek P-2a…P-25; przepisz tabelę: każda etykieta wymiarowa z tym, czego dotyczy (szerokość linii / odstęp / kreska / przerwa), osobno kolumna „zużycie m²/mb” (lub m²/szt.). Usuń wszystkie ESTIMATED z pikseli tam, gdzie rysunek ma etykietę.
(2) Ponownie zinterpretuj P-3b („0,18”), P-12 („0,5”), P-13 („0,2825”), P-14 („0,375”) — czy to m²/mb / m², czy wymiar; dla P-12/P-13/P-14 podaj wymiary z etykiet i tekstu (s. 571–573).
(3) Jaroszówka: 24 kadry są z estakady Andersa nad rondem Pamięci Bieżeństwa (bariery mostowe) — opisz je tak; dla ronda (ring pod estakadą) i chodników/krawężników przy nim znajdź kadry z poziomu ringu (KartaView/Panoramax, inne sekwencje) albo wynik negatywny z liczbą sprawdzonych kadrów.
(4) Usuń kolumnę kolor_srgb liczoną z dolnych 45 % kadru (maska auta, różne kamery) albo oznacz „niewiarygodne”; zad. 4 (czerwony asfalt) — oceń przez obejrzenie kadrów, nie progiem RGB.
(5) Dodaj .gitignore (files/, *.zip) w katalogu.
(6) Samokontrola: losuj 20 % z seedem; dla wierszy z rysunków wklej odczyt etykiety, dla kadrów — „co widać”.
W PR komentarz z SUROWYM wyjściem `git diff --stat origin/main` i listą zmian 1–6. NIE scalaj. Na końcu „M52-FIX gotowe” i koniec.
```

## M51-FIX — PR #49 (zieleń osiedla): korony odbite N–S, kadry przypisane do złych ulic

```
Repo woogitsugames/kamion. Popraw istniejący PR #49 (gałąź research/mistral-p10-greenery-3) — commity do TEJ gałęzi, nie nowy PR. Najpierw `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p10-greenery-3/.
Przegląd (docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p10.md w origin/main — przeczytaj): część BIP rzetelna; korony i zdjęcia NIE.
ZADANIE:
(1) KORONY: crowns.geojson jest odbity lustrzanie północ–południe w każdym kaflu 1024 m (wiersz 0 obrazu to PÓŁNOC kafla: N = n0 + 1024 − wiersz·0,25). Napraw detect_crowns.py, wygeneruj ponownie i sprawdź: nałóż korony na ortofoto w 3 oknach 300×300 m (PNG do ZIP) i podaj % środków na zieleni (ExG > 0,06) — musi być > 80 %. Usuń górny limit r ≤ 6,5 m albo dodaj osobną warstwę „zwarta zieleń” (poligony masek > 6,5 m: las, skarpy, rzędy drzew) — dziś zadrzewiona skarpa przy Al. Tysiąclecia ginie. Odfiltruj nie-roślinność (zielone dachy/autobusy: kształt, wysokość jasności). Podaj datę ortofoto z metadanych WMS/GetFeatureInfo, nie z pamięci. Przelicz comparison_p10.json po poprawce.
(2) ZDJĘCIA: reguła przypisania — kadr należy do ulicy X tylko gdy geotag ≤ 25 m od osi X ORAZ (gdy jest azymut) kamera patrzy wzdłuż X (|Δ| ≤ 30°). Azymutu NIE wolno wyznaczać „w stronę osi ulicy” (to zakłada tezę) — Commons bez GPSImgDirection = kierunek UNVERIFIED albo ustalony z treści (np. widoczny drogowskaz/budynek, opisz jak). Przelicz 18 kadrów: dziś są z Al. Tysiąclecia/Motoszko/Sokólskiej (np. M51-118 — wiata „Sokólska / Al. Tysiąclecia”, M51-117 > 400 m od Łańcuckiej). Przypisz je do prawdziwych ulic (mogą zostać jako referencja zieleni alei), a dla Skidelskiej/Wileńskiej/Łańcuckiej podaj uczciwie liczbę kadrów z wnętrza ulicy (dziś 0).
(3) ŻYWOPŁOTY: OBEJRZYJ każdy kadr (po jednym na wywołanie; przy limicie rozłóż na tury i commituj po każdej). Dla każdego odcinka: jedno zdanie „co widać”, strona kadru, gatunek/typ, wysokość ESTIMATED z odniesieniem. Usuń odcinki, których nie widać (przegląd: M51-201, 207, 211, 213, 214, 217 — brak żywopłotu lub to ekran/barierka). M51-117 i M51-216 to ten sam plik z różnymi ulicami — ujednolić. Próg ≥ 20 odcinków tylko z obejrzanych kadrów.
(4) KartaView: licencja w repo = CC BY-SA 4.0 (referencja, nie tekstura) — ujednolić.
(5) Samokontrola: nowe losowanie 20 % z seedem; dla kadrów — „co widać” + ulica z OSM + odległość do osi; dla koron — % trafień w zieleń w 3 oknach.
Nowy ZIP: mistral-p10-greenery-3-files-v2.zip (wszystkie JPG + PNG nakładek). W PR komentarz z SUROWYM wyjściem `git diff --stat origin/main` i licznikami. NIE scalaj. Na końcu „M51-FIX gotowe” i koniec.
```
