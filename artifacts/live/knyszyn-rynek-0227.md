# Knyszyn Rynek 0227

- 2026-11-15 18:02 +01:00 — Utworzono worktree z origin/main; scalono origin/summer-led-0216 bez konfliktów.
- NASTĘPNY KROK: `git push -u origin knyszyn-rynek-0227`
- 2026-11-15 18:04 +01:00 — Obejrzano zdjęcia dzienne; fontanna ma dysze w posadzce, kostka układana łukami. Kopiowanie danych i Library trwa; źródła tylko do odczytu przez junction, derived lokalny.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/copy.done; pwsh scripts/import-region.ps1 -Region knyszyn`
- 2026-11-15 18:05 +01:00 — Wstępna tabela referencji zapisana w artifacts/knyszyn-rynek-0227/AUDYT.md; wykryta rozbieżność wymiaru fontanny K1 vs istniejący override. Baseline nadal oczekuje na kopię Library.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/copy.done; pwsh scripts/unity-slot.ps1 -Acquire -Owner knyszyn-rynek-0227`
- 2026-11-15 18:06 +01:00 — Lokalna kopia danych i Library gotowa; import przygotowawczy w toku. Skopiowane GLB mogą być starsze niż scalony LED — przed baseline przebudować knyszyn i ponownie zaimportować.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/import-before.done; pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner knyszyn-rynek-0227`
- 2026-11-15 18:07 +01:00 — Przygotowano i uruchomiono sekwencyjny baseline: po imporcie przygotowawczym build_world, ponowny import oraz Low/High × clear/dusk; status w baseline.done, log baseline.log.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/baseline.done; Get-Content artifacts/knyszyn-rynek-0227/baseline.log -Tail 30`
- 2026-11-15 18:09 +01:00 — Audyt kodu: kolejność authored paved_area prawdopodobnie usuwa płytę fontanny pod placem; weryfikacja na baseline oczekuje na render. Import nadal buduje brakujące materiały.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/baseline.done; Get-Content artifacts/knyszyn-rynek-0227/import-before.log -Tail 20`
- 2026-11-15 18:14 +01:00 — Przerwano własną regenerację materiałów przed Unity, skopiowano gotowe PNG z main po sprawdzeniu identyczności źródeł generatora; wznowiono import i baseline.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/baseline.done; Get-Content artifacts/knyszyn-rynek-0227/baseline2.log -Tail 30`
- 2026-11-15 18:16 +01:00 — Import przygotowawczy OK (64 chunków, Low+High); build_world oczekuje w kolejce heavy. Cofnięto efekt uboczny M_Sky.mat.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/baseline2.log -Tail 30; Get-Content artifacts/knyszyn-rynek-0227/baseline.done`
- 2026-11-15 18:18 +01:00 — Orto K1: fontanna jest w zachodnim parku, a istniejący override na placu wschodnim; pozycja różni się o około 93 m (oszacowanie do weryfikacji). Build nadal czeka na slot heavy.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/baseline2.log -Tail 30; Get-Content artifacts/knyszyn-rynek-0227/baseline.done`
- 2026-11-15 18:23 +01:00 — Inwentaryzacja budynków w promieniu 85 m od fontanny zapisana z ID BDOT i wysokościami GUGiK; build baseline trwa.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/baseline2.log -Tail 30; Get-Content artifacts/knyszyn-rynek-0227/baseline.done`
- 2026-11-15 18:36 +01:00 — Przeczytano owner feedback z origin/main: priorytet skwer liściasty, kościół, urząd, czerwona kostka, pierzeje; targowica osobno, zdjęcie | render dla każdego kadru. Stary raport roślinności: override parku 49 drzew. Merge main po zakończeniu trwającego baseline.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/baseline2.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/baseline.done`
- 2026-11-15 18:42 +01:00 — Baseline 4 wariantów ukończony; merge origin/main bez konfliktów. OSM marketplace ~1 km na N od starej kamery: sprawdzamy orto przed lokalizacją. #97 nie w main, orto 2025 sprzed nowego ronda.
- NASTĘPNY KROK: `uv run --project tools/worldgen python -m pytest tests/gis/test_knyszyn_park_0227.py -q` (po implementacji parkowej)
- 2026-11-15 18:45 +01:00 — Iteracja r1: wyłączono regułę lasu dla poligonu parku, dodano trawnik/punkty lip, alejki, płytę fontanny i 6 szacunkowych kamer zdjęć 3–8. Test syntetyczny 1 passed. Uruchomiono build→import→4 rendery r1.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1.done; Get-Content artifacts/knyszyn-rynek-0227/r1.log -Tail 25`
- 2026-11-15 18:46 +01:00 — Baseline: 51 kamer na wariant; max drawsEst Low 429, High 760 (statystyki edytora). Gotowy niezależny generator kościoła, testy 3 passed; integracja po r1. R1 czeka w kolejce heavy.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r1.done`
- 2026-11-15 18:48 +01:00 — Generatory kościoła i urzędu przygotowane w osobnych modułach, każdy 3 testy passed; wymagają integracji i porównania renderów. R1 nadal oczekuje slotu heavy.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r1.done`
- 2026-11-15 18:51 +01:00 — Testy test_region_knyszyn_0204 + test_knyszyn_park_0227: 14 passed. Przygotowano lokalny generator zestawień zdjęcie/render (bez zdjęć w Git); r1 nadal czeka na slot heavy.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r1.done`
- 2026-11-15 18:53 +01:00 — R1 uzyskało slot heavy i przebudowuje region. Moduł obelisku/monumentu/ławek/latarni przygotowany, 3 testy passed; sylwetka króla PROXY_NOT_APPROVED, orzeł i emisja latarni otwarte.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r1.done`
- 2026-11-15 18:56 +01:00 — R1 build trwa; materiał kostki granitowej nie ma lokalnego skanu, road_sett to proceduralne WORKING_VALUE do próby. Generator par 3–8 gotowy; kamery 1/2 i 9–11 mają orientacyjne pozycje do r2.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r1.done`
- 2026-11-15 19:00 +01:00 — Niezależny przegląd: docelowy poligon jest wyłączony z forest/HLOD i maski leśnej, bez wymuszenia piasku; 18 punktów drzew poza nowymi alejkami. Położenie fontanny zgodne z dopasowaniem orto na poziomie ESTIMATED.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r1.done`
- 2026-11-15 19:08 +01:00 — Review wykrył odstające okna/portyk i dachy landmarków; urząd poprawiony i testy 4 passed, kościół poprawiany. R1 nie korzysta jeszcze z tych modułów.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r1.done`
- 2026-11-15 19:09 +01:00 — UWAGA: proces r1 build_world PID 35844 ma 53 wątki Wait/Suspended, CPU ~10 s nie rośnie; przyczyna nieustalona, nie wznawiam wymuszeniem na współdzielonej maszynie. Slot heavy nadal zajęty przez nas.
- NASTĘPNY KROK: `Get-Process -Id 35844 | Select-Object CPU,Responding; Get-Process -Id 35844 | ForEach-Object { $_.Threads | Group-Object ThreadState,WaitReason }`
- 2026-11-15 19:13 +01:00 — Wstrzymany proces r1 (53/53 wątków Suspended, wiele innych Pythonów także) zakończono wyłącznie własny; wrapper zapisał spodziewany błąd i zwolnił własny slot heavy. R1 nie powstało. Plan korekt: artifacts/knyszyn-rynek-0227/R2-PLAN.md.
- NASTĘPNY KROK: `Get-Process python | ForEach-Object { $_.Threads | Group-Object ThreadState,WaitReason }; Remove-Item artifacts/knyszyn-rynek-0227/r1.done; pwsh -File artifacts/knyszyn-rynek-0227/r1.ps1` (po ustąpieniu masowego wstrzymania, w tle)
- 2026-11-15 19:16 +01:00 — Po zatrzymaniu r1 wpięto poprawione moduły kościoła, urzędu i props do stage; poprawiono obrys placu i kamery 1–11. Testy modułów: 13 passed; brak renderu po integracji. Inne procesy pozostają Suspended.
- NASTĘPNY KROK: `Remove-Item artifacts/knyszyn-rynek-0227/r1.done; pwsh -File artifacts/knyszyn-rynek-0227/r1.ps1` (po ustąpieniu masowego wstrzymania, uruchomić w tle)
- 2026-11-15 19:21 +01:00 — Korekta props: 8 ławek i 5 latarni przechodzi kontrolę odległości, dodane kolizje; test 4 passed. Wznowiono r1 przez kolejkę (r1-retry.log), obserwować czy nowy proces nie zostanie wstrzymany.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1-retry.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r1.done`
- 2026-11-15 19:25 +01:00 — Ponowiony r1 także wstrzymany 53/53 wątków po ~3 s CPU; zakończono wyłącznie własny proces i zwolniono własny slot. Wpięto suchą fontannę (dysze i obwódka; strumienie OPEN). 17 testów modułów passed.
- NASTĘPNY KROK: `Remove-Item artifacts/knyszyn-rynek-0227/r1.done; pwsh -File artifacts/knyszyn-rynek-0227/r1.ps1` (w tle, po ustaleniu przyczyny wstrzymywania procesów)
- 2026-11-15 19:27 +01:00 — Testy kierunkowe regionu i wszystkich nowych modułów po integracji: 30 passed. R1 nadal nie ma po dwukrotnym wstrzymaniu procesów systemowych; nie uruchamiam pętli prób.
- NASTĘPNY KROK: `Remove-Item artifacts/knyszyn-rynek-0227/r1.done; pwsh -File artifacts/knyszyn-rynek-0227/r1.ps1` (w tle po ustąpieniu wstrzymywania)
- 2026-11-15 19:28 +01:00 — OS zgłasza 3.8 GiB wolnej pamięci fizycznej (63,7 GiB całość), wiele procesów nadal Suspended; możliwa presja RAM, przyczyna niepotwierdzona. Nie wznawiam siłą cudzych procesów.
- NASTĘPNY KROK: `Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory; Get-Process python | ForEach-Object { $_.Threads | Group-Object ThreadState,WaitReason }`
- 2026-11-15 19:31 +01:00 — Wolny RAM 0.8 GiB; powtórne uruchomienie r1 zostało wstrzymane jak inne procesy, własny slot zwolniony. Dalszy ciężki build/Unity czeka na poprawę zasobów; kod i testy WIP wypchnięte.
- NASTĘPNY KROK: `Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory; Get-Process python | ForEach-Object { $_.Threads | Group-Object ThreadState,WaitReason }`
- 2026-11-15 20:05 +01:00 — Na polecenie właściciela wznowiono r1 po sprawdzeniu zasobów: RAM 29,43 GiB, C: 501,77 GiB; log r1-resume.log.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1-resume.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r1.done`
- 2026-11-15 20:09 +01:00 — R1 ponownie wstrzymano mimo ~26 GiB wolnego RAM; wznowiono wyłącznie dwa procesy należące do r1 (NtResumeProcess zwrócił 0), potwierdzono wzrost CPU i pracujący wątek. Przyczyna wstrzymywania pozostaje nieustalona.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1-resume.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r1.done`
- 2026-11-15 20:13 +01:00 — Uzupełniono audyt 11 kadrów właściciela, z rozróżnieniem brakujących renderów i niepewności; generator r1 nadal pracuje.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1-resume.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r1.done`
- 2026-11-15 20:16 +01:00 — Plan czterech korekt barw dachów wg orto w roof-plan.md, ESTIMATED; brak obsługi roof_material w generatorze. R1 w trakcie przebudowy.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1-resume.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r1.done`
- 2026-11-15 20:21 +01:00 — Audyt wierzby: brak prototypu dorosłej w bibliotece; potrzebne LOD/impostor i poprawka losowania wariantu points_en. R1 w trakcie. Szczegóły w AUDYT.md.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1-resume.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r1.done`
- 2026-11-15 20:22 +01:00 — R1 przeszedł generację budynków (3 hero assets) i nawierzchni; proces nadal pracuje, przywrócony bez ingerencji w cudze procesy.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1-resume.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r1.done`
- 2026-11-15 20:24 +01:00 — Build_world r1 OK (958,4 s); import Unity w toku, slot unity zajęty wyłącznie przez r1.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1-resume.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r1.done`
- 2026-11-15 20:24 +01:00 — QA generatora r1: kościół, urząd, props i fontanna applied; park_replacement bez stale; 15/18 authored drzew przyjętych, 3 odrzucone przez maskę, do oceny i korekty w r2. Strumienie OPEN.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r1-resume.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r1.done`
- 2026-11-15 20:29 +01:00 — R1: build/import/4 rendery OK; 11 lokalnych par High clear gotowych. Ocena wizualna FAIL; Low max drawsEst 429→440, High 760→774; 15/18 drzew. R2: płaskie ścieżki, lepszy urząd/drzewa, redukcja draw calls.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/AUDYT.md -Tail 15; uv run --project tools/worldgen python artifacts/knyszyn-rynek-0227/budget-r1.py`
- 2026-11-15 20:33 +01:00 — R2 WIP: park_flush + dopasowanie terenu, 4 szacowane kolory dachów, 2 lipy kit zamiast instancji; testy kierunkowe zielone. Urząd i sylwetka króla poprawiane osobno. R1 FAIL wizualnie/budżet Low.
- NASTĘPNY KROK: `uv run --project tools/worldgen python -m pytest tests/gis/test_knyszyn_*_0227.py -q` (po zakończeniu prac agentów), potem build r2
- 2026-11-15 20:38 +01:00 — R2 uruchomione: park_flush, 4 barwy dachów, 2 lipy kit, poprawione kamery, urząd i pomnik oraz ograniczenie materiałów Low. Testy kierunkowe 25 passed; RAM 23,7 GiB, C: 472,7 GiB.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r2.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r2.done`
- 2026-11-15 20:41 +01:00 — R2 build trwa. Audyt fontanny: istniejący WorldWater jest nieprzezroczysty i nie obsługuje pionowych strumieni; sucha fontanna pozostaje OPEN. Analiza ewentualnego shadera i ścieżki importu trwa.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r2.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r2.done`
- 2026-11-15 20:44 +01:00 — W TYPOPLOGIA.md (TYPOLOGIA.md) zapisano 25 brył w promieniu 85 m: typ, wysokość i źródło, dach/fasada z poziomem pewności; r2 nadal buduje.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r2.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r2.done`
- 2026-11-15 20:47 +01:00 — Budżet r1 z instancjami: Low max suma drawsEst 500→493, ale na części wspólnych kamer wzrost do +12; warunek bez pogorszenia nadal FAIL. Narzędzie budget-compare.py obejmuje osobne instancje.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r2.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r2.done`
- 2026-11-15 20:52 +01:00 — Wierzba: opt-in generator i 3 testy, uruchomione izolowane studium Blender z osobnym slotem; bez integracji do świata. R2 nadal buduje.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/willow-study.done; Get-Content artifacts/knyszyn-rynek-0227/r2.done`
- 2026-11-15 20:54 +01:00 — Willow lookdev: pierwszy uruchomiony bake po poprawce ścieżek OK technicznie, ale wizualnie FAIL (pionowe kępy zamiast płaczącej korony); nie włączono do gry. Agent poprawia generator. R2 nadal w toku.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r2.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r2.done`
- 2026-11-15 20:55 +01:00 — Build_world r2 OK (992,7 s), import Unity w toku. Willow study r1 FAIL i nie wchodzi do r2.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r2.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r2.done`

- 2026-11-15 21:03 +01:00 — R2: build/import i cztery warianty renderów OK; wizualnie FAIL (m.in. kamery 02/07, zieleń, pomnik i suche dysze). Low: max drawsEst z instancjami 500→486, ale wspólne kadry do +6; High max 1 256 983 tris. Scalono origin/main b5dca11f, generator wymaga przebudowy.
- NASTĘPNY KROK: `pwsh artifacts/knyszyn-rynek-0227/r3.ps1`


- 2026-11-15 21:06 +01:00 — Uruchomiono r3 po scaleniu main: poprawione kamery 02/07, próba placu pomnika i materiałów Low. Wierzba r3 FAIL wizualnie, nie jest w grze; trwa r4. Test pomnika 6 passed.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r3.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r3.done`


- 2026-11-15 21:09 +01:00 — R3 build trwa po scaleniu main; przegląd statyczny scalenia nie wykazał utraty zmian. Wierzba r3 FAIL, r4 wypalona i czeka na przegląd. Targowica: lokalizacja UNVERIFIED, pytanie o współrzędne zadane właścicielowi.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r3.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r3.done`


- 2026-11-15 21:15 +01:00 — Build R3 aktywny; proces 26128 zwiększa CPU, import i rendery czekają. Wierzba r4 FAIL, nie integrowana. Przegląd pierzei: urząd i skrzydło kultury zidentyfikowane w BDOT, drewniany dom nie ma pewnego ID. C ponad 300 GiB.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r3.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r3.done`


- 2026-11-15 21:24 +01:00 — R3 build_world zakończony, import Unity w toku (kontrola 13 assets, 65 plików, 0 problemów). Równolegle przygotowanie kolejnej próby koron lip oraz wejść urzędu, bez zmian bieżącego buildu.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r3.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r3.done`


- 2026-11-15 21:28 +01:00 — R3 wszystkie 4 warianty OK, 62 kadry/wariant, pary 01–11 lokalnie. Wizualnie FAIL: 02 za blisko, 07 poza osią, plac pomnika przenika. Low nadal FAIL: wspólna kamera +6 draws i +1644 tris; High max 1 229 621 tris (<2 mln). Przygotowano wejścia urzędu i próbę koron, wymagają r4.
- NASTĘPNY KROK: `pwsh artifacts/knyszyn-rynek-0227/r4.ps1`


- 2026-11-15 21:28 +01:00 — R4 wystartowała: plac pomnika przez park_flush, wejścia i lukarny urzędu, 2 próbne korony lip, korekta kamer 02/07. Każda zmiana wymaga renderu i ponownego budżetu.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r4.log -Tail 20; Get-Content artifacts/knyszyn-rynek-0227/r4.done`


- 2026-11-15 21:33 +01:00 — R4 build trwa. Pełny pytest GIS uruchomiony w slocie heavy; jego proces potomny build_region był Suspended, wznowiono tylko własne PID 13432 i 68456 zgodnie z dyspozycją użytkownika; ponownie aktywny.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/gis-r4.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/r4.log -Tail 10`


- 2026-11-15 21:40 +01:00 — R4 i pełny GIS w toku (>14%). #97 OPEN, DIRTY, GIS FAILURE; orto GUGiK 2025 pokazuje stan sprzed ronda, warstwa 2026 dla punktu pusta, wymiary nowej wyspy niezweryfikowane.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/gis-r4.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/r4.log -Tail 10`


- 2026-11-15 21:45 +01:00 — R4 build i import OK, Low-clear w toku. Pełny GIS: 1410 passed, 43 skipped, 4 xfailed, 2 failed; kontrakt kamer naprawiony (3 testy passed), raport fidelity regionu C nieaktualny już na main, trwa pełne przeliczenie i test.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r4.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/fidelity-refresh.done`


- 2026-11-15 21:48 +01:00 — R4 4 warianty OK; pary 01–11 lokalnie. Plac ciągły, 07 na alei, ale dach portyku niewidoczny High/Low; naprawa generatora w toku. Low max +6 draws i +1704 tris na wspólnych kamerach; High max 1 229 693 tris. Raport fidelity liczy się po wznowieniu własnych procesów.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/fidelity-refresh.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/fidelity-refresh.done`


- 2026-11-15 21:51 +01:00 — EditMode 626 passed, 2 skipped, 0 failed. R5 wystartowała z poprawką dachu portyku: r4 GLB ma materiał i normalne w górę, ale połać nie jest skierowana ku kamerze; nowa geometria wymaga renderu. Fidelity regionu C nadal liczy się.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r5.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/fidelity-refresh.done`


- 2026-11-15 21:57 +01:00 — Właściciel wskazał targowicę: Jagiellońska 50, 19-120 Knyszyn; trwa identyfikacja z danymi. R5 build w toku, fidelity regionu C przeliczony; test 9 passed, 1 xfailed. EditMode 626 passed, 2 skipped.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r5.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/r5.done`


- 2026-11-15 22:01 +01:00 — Targowica: adres GUGiK Jagiellońska 50 (760825.18, 613384.98 EPSG:2180) w budynku BDOT; poligon OSM marketplace way 704368699 24,38 m od punktu po drugiej stronie ulicy, mocny kandydat. Pytanie o potwierdzenie właścicielowi; układ nowych wiat UNVERIFIED. R5 trwa.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r5.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/r5.done`


- 2026-11-15 22:07 +01:00 — Właściciel potwierdził: targowica z 4 wiatami jest na placu po drugiej stronie Jagiellońskiej od nr 50; odpowiada kandydatowi OSM way 704368699. Układ i wymiary wiat nadal ESTIMATED; przygotowanie po R5.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r5.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/r5.done`


- 2026-11-15 22:11 +01:00 — R5 wszystkie warianty OK, dach portyku widoczny High/Low; kalenica i lukarny nadal niezgodne. Low max +6 draws i +1825 tris na wspólnych kamerach, High max 1 229 814 tris. Pary 01–11 lokalnie. Targowica potwierdzona przez właściciela, prototyp wiat NIEZINTEGROWANY do czasu zdjęć/pozycji.
- NASTĘPNY KROK: `uv run --project tools/worldgen python -m pytest tests/gis -q`


- 2026-11-15 22:12 +01:00 — R6 uruchomiona: niższe lukarny CULTURE na istniejącej połaci, 10 testów modułu passed; dach nadal wymaga poprawy kalenicy. C powyżej progu. Targowica: potwierdzony plac OSM, zdjęcia dronowe potrzebne do położeń wiat.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r6.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/r6.done`


- 2026-11-15 22:18 +01:00 — R6 build trwa, pełny GIS po poprawkach >14% bez wyniku końcowego. EditMode 626 passed/2 skipped. Wiaty targowicy nadal poza światem: czekamy na ścieżkę do zdjęć dronowych potrzebnych do lokalizacji.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/gis-r6.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/r6.log -Tail 10`


- 2026-11-15 22:31 +01:00 — R6 4 warianty OK, lokalne porównania 01–11: lukarny niższe, nadal FAIL; Low +6 draws/+1825 tris na wspólnych kamerach, High max 1 229 814 tris. Pełny GIS po poprawkach w końcowej części (>88%), aktywny.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/gis-r6.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/gis-r6.done`


- 2026-11-15 22:35 +01:00 — GIS rerun: 1419 passed, 31 skipped, 4 xfailed, 11 errors ze wspólnej starej usterki far_field (out_root ignorowany, fallback R16 używa starego schematu). Poprawka i testy kierunkowe w toku; po GIS przywrócono własne efekty uboczne generated regionu C.
- NASTĘPNY KROK: `uv run --project tools/worldgen python -m pytest tests/gis -q`


- 2026-11-15 22:37 +01:00 — Scalono origin/main 114658153 bez konfliktów, R7 uruchomiona (dopracowane lukarny i fix far_field). Raport fidelity C ponownie nieaktualny po zmianach dróg main, trwa pełne przeliczenie. Poprawki kierunkowo 10/11 testów modułów passed; pełny GIS nadal wymagany.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r7.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/fidelity-refresh.done`


- 2026-11-15 22:54 +01:00 — R7 build OK po scaleniu main, import Unity trwa. Pełny GIS po poprawce far_field kontynuuje >9%. Fidelity po merge przeliczone, 9 passed/1 xfailed; kierunkowo far_field 10 passed, urząd 11 passed.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r7.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/gis-r7.log -Tail 10`


- 2026-11-15 23:11 +01:00 — Pełny GIS po scaleniu i fix far_field: 1472 passed, 33 skipped, 3 xfailed, exit 0 (21:56); przywrócono wyłącznie efekty uboczne testu w generated C. R7: poprawa lukarn w obu profilach, Low nadal +6 draws/+1832 tris na wspólnych kamerach.
- NASTĘPNY KROK: `uv run --project tools/worldgen python artifacts/knyszyn-rynek-0227/budget-compare.py r7`


- 2026-11-15 23:13 +01:00 — R8 uruchomiona: próba 13 pełniejszych lip w dotychczas zaakceptowanych punktach, wysokości z R7; średnice WORKING_VALUE, trzy odrzucone poza próbą. GIS dla stanu R7 1472 passed, 33 skipped, 3 xfailed; test próby 4 passed. Wymagane nowe rendery i budżet.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r8.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/r8.done`


- 2026-11-15 23:38 +01:00 — R8 4 warianty OK, pary 01–11 lokalnie. Lipy lepiej przypominają park, ale widać szwy i częściowo zasłaniają urząd; FAIL naturalności. Low max +5 draws/+1832 tris na wspólnych kamerach, High max 1 230 049 tris. GIS 1472 passed dla R7, R8 po zmianie drzew wymaga końcowego testu.
- NASTĘPNY KROK: `uv run --project tools/worldgen python artifacts/knyszyn-rynek-0227/budget-compare.py r8`


- 2026-11-15 23:41 +01:00 — R9 uruchomiona: odwracalny wariant 15 koron bez przecięć kart, dwie kamery boczne na 1,7 m; ryzyko płaskości i overdraw OPEN. Testy kierunkowe 5 passed, wygląd i budżet do pomiaru.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r9.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/r9.done`


- 2026-11-16 00:05 +01:00 — R9 FAIL: korony znikają pod kątem, wariant wycofany. R10 uruchomiona: objętościowe korony z istniejącego atlasu, osiem azymutów QA; testy kierunkowe 5 passed. Low koszt korony wyższy w próbie, pomiar całych kamer OPEN.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r10.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/r10.done`


- 2026-11-16 00:14 +01:00 — R10 build aktywny: próba koron objętościowych, osiem azymutów QA. R9 wycofana po FAIL (znikanie krawędziowe), R8 pozostaje punktem odniesienia. GIS 1472 passed dla R7; pełna walidacja nowszych zmian OPEN. Targowica na potwierdzonym placu, układ wiat bez zdjęć OPEN.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r10.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/r10.done`


- 2026-11-16 00:29 +01:00 — Scalono origin/main 2d125e171 bez konfliktów; testy far_field/fidelity 12 passed, 1 xfailed. R11 uruchomiona po wycofaniu FAIL R10; dodatkowo powstaje niezintegrowany prototyp lipy 3D. Układ wiat targowicy nadal bez zdjęć OPEN.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r11.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/r11.done`


- 2026-11-16 00:34 +01:00 — Izolowany prototyp lipy 3D wyeksportowany i obejrzany w 16 kadrach LOD0/LOD1: FAIL, zbyt rzadka wąska korona i wyraźny spadek pokrycia LOD1; nie w grze. Druga próba prototypu w przygotowaniu. R11 build trwa.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r11.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/r11.done`


- 2026-11-16 00:51 +01:00 — R11 cztery warianty OK, High max 1 250 405 tris; Low +63 draws w dk65-inlet-south vs before, lecz kadr R11 zawiera pełną ciężarówkę zamiast szarej atrapy baseline, więc udział far-field nieustalony. R12 start: 2 lipy 3D w lokalnym worldgen, testy kierunkowe 6 passed, pomiar OPEN.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r12.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/r12.done`


- 2026-11-16 01:11 +01:00 — R12: dwie lipy bardziej przestrzenne, ale plamiste; przy tym samym stanie co R11 +2044 tris Low, draws bez zmian. R13 uruchomiona: Low wraca do lekkiej geometrii identycznej z R11, High zachowuje trial 3D; poprawione proxy króla, tarcza i ptak. Ryzyko skoku LOD oraz budżet do oceny.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r13.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/r13.done`


- 2026-11-16 01:17 +01:00 — R13 build aktywny, dwie lipy mają uproszczone Low oraz trial High; król, tarcza i ptak poprawione jako proxy. GIS 1472 passed dotyczył R7; końcowe testy i budżet OPEN. Rozbieżność baseline: ADR 0262 zmienił pozycję ciężarówki, kosztu nie rozdzielono.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/r13.log -Tail 10; Get-Content artifacts/knyszyn-rynek-0227/r13.done`


- 2026-11-16 01:47 +01:00 — GIS R13: 1632 passed, 29 skipped, 3 xfailed, 4 failed; brak instancji Białystok C i stary cache GIS. Cache przebudowany lokalnie schema 12; trwa weryfikacja instancji i testów. R13 Low względem R11 maks. +14 tris, draws bez zmian; względem before budżet Low nadal OPEN.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/cache-c.done; git status -sb` 

