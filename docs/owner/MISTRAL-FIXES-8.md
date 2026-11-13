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
