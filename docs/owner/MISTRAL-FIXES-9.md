# Poprawki do PR-ów Mistrala, runda 9 (s18, 2026-11-13)

Każdy blok wklej do NOWEJ sesji Mistrala. Przegląd: `docs/reports/REVIEW-2026-11-13-s18-mistral-fixes-r8.md`.
Wszystkie PR-y tych paczek są już SCALONE. Commity dopisuj do tej samej gałęzi (bez nowego PR). Lider scali je ręcznie.
Gałąź musi się nazywać DOKŁADNIE tak, jak podano w bloku: `research/mistral-…` z myślnikiem. Nazwa ze slashem (`research/mistral/…`) jest błędna.

---

## M52-FIX-3 — P2 nawierzchnie (`research/mistral-p2-surfaces-2`): kadry pod złą ulicą, kadry nadal nieobejrzane

```
Repo woogitsugames/kamion, gałąź research/mistral-p2-surfaces-2 (PR #48 scalony — dopisz commity do tej gałęzi, nie twórz PR). Najpierw `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p2-surfaces-2/.
Przegląd s18 (docs/reports/REVIEW-2026-11-13-s18-mistral-fixes-r8.md): część rysunkowa r2 jest dobra (P-3b 1,00/1,00, P-13 0,50/0,70/0,25, P-12 0,5, P-14 0,75×0,50). Do poprawy:
(1) M52-103, M52-104, M52-105 („Sokólska”, route/sokolska-01…03.jpg) leżą 53.1513–53.1515 N, 23.1544 E w sekwencji 1155711. To jest Al. Tysiąclecia Państwa Polskiego (OSM: ways 536419697 / 946729184 / 999223603 w promieniu 25 m; Sokólskiej brak). Kadr pokazuje dojazd do skrzyżowania z sygnalizacją, w tle stację Circle K i żółty wieżowiec. Ten sam widok jest na cross-tys-07 (M52-090). Popraw `element`/`lokalizacja` na Al. Tysiąclecia. Zastosuj do WSZYSTKICH wierszy kadrów (route/, crossings/) regułę z M46: odległość do osi ≤ 25 m ORAZ |azymut − kierunek odcinka| (mod 180) ≤ 30°. Wpisz do uwag way_id i deltę.
(2) Kadry nadal NIE są obejrzane („nie obejrzano w sesjach FIX”). OBEJRZYJ każdy z 78 kadrów (model wizyjny, po jednym na wywołanie). Przy limicie rozłóż pracę na tury i commituj po każdej. Do uwag wpisz jedno zdanie „co widać” (nawierzchnia, oznakowanie poziome, krawężnik, przejście) i oceń, czy element z kolumny `element` jest w kadrze.
(3) M52-012 / README (P-5): rysunek 2.2.1.11 przedstawia 2 pary linii (to Twój własny pomiar: 4 kanały). Podpis 0,32 m²/mb = 2 × 0,16 jest więc spójny. Usuń „rozbieżność wewnętrzną rozporządzenia” albo podaj inny dowód.
(4) Pomyłki kopiuj-wklej w `uwagi`: M52-006 (wiersz o szerokości linii P-3b) zaczyna się od „przerwa 2,00 m etykieta…”. W M52-014 (przerwa) i M52-015 (kreska) uwagi są zamienione. M52-027 ma dwa sprzeczne zdania („nie zawiera etykiet” i „KOREKTA r2: zawiera”) — zostaw tylko aktualne. Dla P-3b dodaj osobny wiersz „kreska/przerwa 1,00/1,00 m”, tak jak M52-005 dla P-3a.
(5) Samokontrola: nowe losowanie 20 % z jawnym seedem. Dla każdego wylosowanego kadru wpisz „co widać” + ulicę z OSM + deltę azymutu.
W komentarzu PR #48 wklej SUROWE wyjście `git diff --stat origin/main`. NIE scalaj. Na końcu „M52-FIX-3 gotowe” i koniec.
```

## M47-FIX-2 — P11 zdjęcia Dojlidy (`research/mistral-p11-dojlidy-photos`): opisy znaków niezgodne z obrazem

```
Repo woogitsugames/kamion, gałąź research/mistral-p11-dojlidy-photos (PR #39 scalony — dopisz commity do tej gałęzi). Najpierw `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p11-dojlidy-photos/.
Przegląd s18 obejrzał 7 kadrów, które różnią się między ZIP v2 i v2b (002, 057, 072, 107, 120, 143, 144). Obraz jest ten sam (zmieniło się tylko kodowanie). Obiekty główne opisano dobrze 7/7, ale znaki są zmyślone w 3/7:
(1) P11-002: brak „zakazu wjazdu”. Przy hali Masterpress stoi niebieska tablica kierunkowa z symbolem samochodu ciężarowego w kole i tabliczką „12t” (wskazanie drogi dla ciężarówek). Obok jest znak D-1 (droga z pierwszeństwem). Popraw opis. To ważne dla P8/ograniczeń: dopisz w uwagach współrzędne i kierunek.
(2) P11-057: brak „zakazu skrętu w lewo” i „zakrętu”. Jest znak A-30 (inne niebezpieczeństwo, „!”) z tabliczką ze strzałką przesunięcia/objazdu. Popraw.
(3) P11-120: brak „zakazu wjazdu” i „STOP”. Jest znak B-36 (zakaz zatrzymywania się), a za zielonym ogrodzeniem z bramą stoją stosy beczek (kegów). Pole `ulica` = „Jacka Kuronia” przy d = 374,5 m to błąd: przypisz ulicę ≤ 25 m albo wpisz UNVERIFIED. To samo dotyczy P11-143 (d = 145 m) i P11-144 (d = 235 m). Przy P11-143 „taśma ostrzegawcza” to w rzeczywistości szlaban (biało-czerwone ramię).
(4) Ponieważ 3/7 sprawdzonych opisów zawiera nieistniejące znaki: przejrzyj w CAŁYM manifeście każdą wzmiankę o znaku drogowym. Obejrzyj kadr i zostaw tylko znaki, które naprawdę widać, z kodem (A-/B-/C-/D-/F-…). Jeśli kodu nie da się odczytać, napisz „znak nieczytelny”.
(5) Pole `ulica` we wszystkich wierszach z d(poligon drogi) > 25 m zmień na najbliższą ulicę ≤ 25 m albo UNVERIFIED.
W PR #39 komentarz z SUROWYM `git diff --stat origin/main` i liczbą poprawionych opisów znaków. NIE scalaj. Na końcu „M47-FIX-2 gotowe” i koniec.
```

## M54-FIX-2 — P8 ograniczenia (`research/mistral-p8-restrictions-3`): 2 opisy kadrów w photos.csv

```
Repo woogitsugames/kamion, gałąź research/mistral-p8-restrictions-3 (PR #44 scalony — dopisz commit do tej gałęzi). Najpierw `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p8-restrictions-3/.
Plik photos.csv JEST w gicie i nadal zawiera 2 błędne opisy z ponownego przeglądu s17:
(1) s8_0a2121ca: to nie są „znaki ostrzegawcze o nierównościach”. Są to znaki łączenia/zwężenia pasów z tabliczką 100 m. OBEJRZYJ kadr i popraw.
(2) wolukrainy_4ac8cbd1: w kadrze nie ma znaku B-1. Są słupki U-23 i roboty drogowe. OBEJRZYJ kadr i popraw.
Popraw też photos.csv w ZIP (v3). Commit + SUROWY `git diff --stat origin/main` w komentarzu PR #44. Na końcu „M54-FIX-2 gotowe” i koniec.
```

## M49-FIX-2 — P6 bramy (`research/mistral-p6-dojlidy-gates`): drobiazg + zła nazwa gałęzi

```
Repo woogitsugames/kamion. UWAGA: ostatni commit „M49-FIX r8” wypchnąłeś na gałąź research/mistral/p6-dojlidy-gates (ze SLASHEM). Właściwa gałąź to research/mistral-p6-dojlidy-gates (z myślnikiem). Ten sam commit jest już w main, więc nic nie trzeba przenosić. Kolejne commity dawaj tylko na gałąź z myślnikiem.
Gałąź research/mistral-p6-dojlidy-gates: `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p6-dojlidy-gates/.
(1) M49-030 `uwagi` kończą się na „node = wjazd drogowy” oraz „wjazd ciężarowy od ul. Elewatorskiej”. To przeczy M49-010/024, gdzie brama drogowa PZZ jest UNVERIFIED. Zmień na „node = adres rejestrowy (punkt adresowy), NIE brama; brama drogowa PZZ UNVERIFIED — patrz M49-010”.
Commit + SUROWY `git diff --stat origin/main` w komentarzu PR #46. Na końcu „M49-FIX-2 gotowe” i koniec.
```

## M48-FIX-2 (opcjonalne, niski priorytet) — P12 landmarki (`research/mistral-p12-dojlidy-landmarks`)

```
Repo woogitsugames/kamion, gałąź research/mistral-p12-dojlidy-landmarks (PR #40 scalony). Najpierw `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p12-dojlidy-landmarks/.
M48-FIX pkt 5 kazał zostawić w data/ tylko landmarks.json, landmark-colors.json i matched-with-roads.json. Zostały też road-geom.json (551 KB — pochodna OSM), region-summary.json, typologia.json i typologia-colors.json. Możliwe dwie drogi: (a) usuń road-geom.json i dopisz w README, jak go odtworzyć (skrypt z tools/ + zapytanie); (b) uzasadnij w README, której tabeli README każdy z tych 4 plików potrzebuje do odtworzenia.
Liczba flag poza_kaflem = 17 (sprawdzone pyproj: 17/39, 0 niezgodności) — erratę w PR #40 masz poprawną, w plikach niczego nie zmieniaj.
Na końcu „M48-FIX-2 gotowe” i koniec.
```
