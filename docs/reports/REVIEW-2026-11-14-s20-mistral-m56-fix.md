# Przegląd M56-FIX (P13 estakady Andersa) — s20, 2026-11-14

**Werdykt: SCAL z erratą.** Wszystkie 11 punktów bloku M56-FIX wykonano. Trzy fałszywe SOURCED są poprawione, kierunki Panoramax pochodzą teraz z API, 23/23 kadry mają opis „co widać” napisany z obrazu, a seed 20261114 się odtwarza. Luki zamknięto kadrami CC0 wskazanymi w recenzji. Zostały drobne błędy, które nie blokują scalenia (§4).

- Gałąź `origin/research/mistral-p13-andersa-viaducts` @ `9fdc96f15` (PR #54). Commity FIX: `259f04ba2` (manifest), `dd047ce6e` (README, sources), `52e0131df` (audyt, ZIP) oraz merge `9fdc96f15`.
- `git diff --stat origin/main...` pokazuje 6 plików, wszystkie w `research/mistral/p13-andersa-viaducts/` (+935 linii). Manifest ma 83 wiersze (było 78), id są unikalne.
- Nic nie scalono, nic nie scommitowano, PR bez komentarza. Raport nie jest scommitowany.

## 1. Punkt po punkcie

| # | Wymóg FIX | Wynik | Dowód recenzenta |
|---|---|---|---|
| 1 | 23/23 kadry obejrzane osobno, opis z obrazu | **TAK** | 23 wiersze (015–029, 059–066) mają opis „co widać” i adnotację o pliku. Treść zgadza się z obrazem we wszystkich 16 kadrach, które obejrzałem sam (§2). `NOTATKI_OGLEDZIN.md` ma osobny akapit dla każdego kadru. Doszły 4 kadry bez obiektu (020, 025, 028, 064), co potwierdzam na 020, 025, 028 i 064 |
| 2 | Słupy A prostokątne fazowane z głowicą, ochra | **TAK** | P13-015/016/017/018/019/022/026/034/044 poprawione. Obejrzałem c015, c022 (w połowach, w natywnej rozdzielczości) i pełny kadr 026: płaskie ściany, faza na narożu, jaśniejszy panel na czole, oczep z łożyskiem. Słowo „owalne” zostało tylko w README jako „poprzedni wpis był błędny” i w P13-071 (B, z ADR, UNVERIFIED), co jest poprawne |
| 3 | PFU = Sulika/Sosabowskiego, E1–E19 = ekrany | **TAK** | P13-009 przeniesiono do obiektu „inny odcinek Trasy Generalskiej (nie A)” i oznaczono SOURCED tylko co do istnienia PFU. README §3 ma osobną tabelę, sources D4 ma poprawny tytuł i kontekst. Fraza „Sulika i Maczka” zostaje już tylko jako cytat błędu |
| 4 | B: balustrada, nie ekrany | **TAK** | P13-073 (NE, 20201102_152339) i nowy P13-080 (SW, 20210320_092717/737). Wątek „obserwacji z sesji” usunięty. Na c059, c061, c062 i pełnym 065 widać czerwony gzyms i balustradę z poziomymi prętami, bez paneli |
| 5a | P13-040 SOURCED z 20221203_111814 | **TAK** | Na pełnym kadrze 018 widać ekran na krawędzi bliższej kamerze, a za nim drugi pomost |
| 5b | Strona od pasa dzielącego A | **TAK** | Nowy P13-079 z Panoramax 6fc62548 (ref. BY-SA). Na kadrze widać jasnoszarą/ocynkowaną balustradę z pochwytami, bez ekranu |
| 5c | Połowa SE B: słupy, gzyms, mur, liczenie na 3840 px | **TAK** | P13-061/062/067/076/082. Liczenie jest na wycinku 3840 px. Kadr kończy się przed wyspą ronda, więc wynik to „≥ 4–5 do krawędzi kadru”, a nie liczba do wyspy. Mistral pisze to wprost ✓ |
| 5d | Rzędy A osobno dla jezdni, ESTIMATED | **TAK** | P13-030 (NE) i P13-031 (SW): po ok. 7–9, z opisem zasłonięć |
| 5e | 024/063/066 bez obiektu | **TAK** | Plus 020, 025, 028, 064. Kadry bez obiektu mają status UNVERIFIED i nie są liczone jako kandydaci |
| 5f | P13-060: EC w tle | **TAK** | Poprawione w wierszu i w README §4 |
| 6 | Azymuty Panoramax z API | **TAK** | Sam pobrałem `view:azimuth` dla 7 kadrów: 021 = 268, 023 = 242, 028 = 275, 029 = 274, 020 = 53, 025 = 56, 026 = 100. Wszystkie zgadzają się z manifestem. Dla 019, 022, 024 i 027 opieram się na przeglądzie M56, który sprawdził je z API (zgodne ±0,5°). Uwaga przy każdym kadrze podaje źródło azymutu i błędny EXIF z Ref = M |
| 7 | Etykiety jezdni | **TAK** | Format „NE (ruch na NW; ways …)” / „SW (ruch na SE; …)” dla A i B, zgodny z PBF |
| 8 | OSM rampy vs mosty, Putry, cytaty | **TAK** | README §2: rampy z `layer=1` bez `bridge` oraz rondo Putry (257367424/425/428). P13-046 ma „…posadowionej bezpośrednio”, P13-055 ma cytat UM z [sic] |
| 9 | Przekrój B | **TAK (UNVERIFIED)** | P13-081: spód w cieniu, rozstrzygnięcia brak. Uczciwie, bez zgadywania |
| 10 | ZIP wycinków | **TAK** | `C:\Users\matma\Downloads\m56fix-p13-crops.zip`: **2 686 939 B, sha256 `c3fdca5f…7c9829a`**, zgodne z `files/README.md` i komentarzem PR. Wszystkie 13/13 plików są bajtowo identyczne z `research/_incoming/mistral-p13-andersa-viaducts-fix-crops/` (sha256 każdego pliku). Zestaw zgadza się z README.txt |
| 11 | Samokontrola | **TAK** | `random.Random(20261114).sample(ids, 17)` daje tę samą listę w tej samej kolejności ✓. Próba to 20,5 %, w tym 5 wierszy kadrów (017, 020, 062, 064, 065) i 4 inne wiersze oparte na obrazie. Wynik: 15 zgodnych, 2 niezgodne poprawione (065, 082). Dla dokumentów sprawdzono kontekst (P13-009, 049, 054). Seed oryginalny 20261113 zachowany |
| — | „Nie ruszaj” 001–008, 010–013, 046–054, 056–058 | **TAK** | Diff względem `6f39fc260`: zmieniła się tylko kolumna `jezdnia` (010, 011, 056, 057, zgodnie z pkt 7) oraz P13-046 (uzupełnienie cytatu z pkt 8 i data dostępu). Wartości i statusy bez zmian |

Uwagi procesowe (nie blokują): zamiast `git rebase` Mistral zrobił `git merge origin/main` (dwa razy, bez force-push). Diff i tak jest czysty. Commons pobrano jako miniatury 3840 px, nie oryginał 5520 px (HTTP 429). Do oceny kształtu słupów to wystarcza.

## 2. Co obejrzałem sam (18 obrazów, 16 kadrów)

- **Wycinki z ZIP (11):** c015, c017, c018, c019, c022 (w połowach, natywnie), c023, c027 (w połowach, natywnie), c059, c061, c062, c065. Wszystkie ≤ 960 px na wywołanie.
- **Pełne kadry pobrane ponownie (7):** Panoramax sd 020, 025, 026, 028 oraz Commons 1600 px 018, 064, 065.
- **Zgodność z opisami Mistrala:** wszystkie opisy się zgadzają. Szczegóły warte odnotowania:
  - 065: słupy B mają szeroką jasnoszarą ścianę i węższą ścianę pomalowaną na czerwono, z zaokrąglonymi narożami.
  - 026: balustrada od strony pasa dzielącego jest jasna/ocynkowana, nie ciemna.
  - c023 (widok z boku od NE, pod słońce): jedna szersza przerwa między podporami. Pozostałe przęsła mają regularny rytm.

## 3. Co M56 może teraz poprawić w grze

**P1 — pomost SW (ruch na SE) estakady A: przęsło 94,8 m to artefakt generatora, nie pomiar.**

Stan w grze:
- `generated/landmarks/viaduct_putry_underdeck.spec.json`, łańcuch `c:w173956078` to pomost SW (leży ~14 m na S od łańcucha `c:w1101181473`).
- `s_open` = 246,05–459,30 m, linie podpór co 23,69 m (= 213,25 / 9).
- Generator ustawił 5 rzędów: 269,7 / 293,4 / 388,2 / 411,9 / 435,6. Pominął `pier_lines_skipped: 3` przy s ≈ 317,1 / 340,8 / 364,5, czyli 71 / 95 / 118 m od przyczółka NW.
- Pominięcie robi keep-out `blocked(q)` w `tools/worldgen/streetscape/hero_bridge.py` („True where a column may not stand (carriageway or paved surface underneath)”). Generator nie znalazł wolnego miejsca w zakresie przesunięć ±`pier_shift_max_m`. Nie sprawdzałem, która powierzchnia zablokowała słup.
- Pomost NE (osobny wpis spec, łańcuch `c:w1101181473`) **też nie jest pomiarem**, tylko wynikiem tej samej reguły. Rytm 24,39 m: rząd 327,5 to linia k = 3 przesunięta o +8 m, a linia k = 5 (≈ 368,3) jest pominięta (`pier_lines_skipped: 1`). Dlatego powstały para 16,4 m i przęsło 48,8 m.
- Definicja obiektu: `Data/Regions/bialystok-industrial-c/viaduct_underdeck.json` (`id: dk8-putry-underdeck-0105`, `span_target_m: 25.0`).

Dowód z kadrów:
- P13-031: pomost SW ma ok. 7–9 rzędów.
- **c027** (Panoramax 844e35c7, kamera przy s ≈ 46 m, patrzy na SE): przed kamerą widać 5–6 rzędów bliższego pomostu do autobusu. W grze kamera stałaby przy ostatnim słupie przed dziurą 95 m.
- **c022** (35224dcb, s ≈ 92 m): słup tuż przy kamerze, potem 3–4 rzędy do przyczółka SE. W grze w tym miejscu jest środek przęsła bez podpór.
- Na żadnym kadrze strony SW nie ma przerwy na kilka przęseł. Jedna szersza przerwa jest widoczna tylko w c023, pod słońce, w widoku z boku, przy nakładających się pomostach. Więcej ten kadr nie pozwala powiedzieć.

Działanie (zadanie dla world-builder, nie M56):
1. Dodaj do wpisu Putry w `viaduct_underdeck.json` pole `pier_lines_en` (mechanizm ADR 0123, którego używa już B w ADR 0144), dla obu pomostów. **Zmierzone rzędy omijają keep-out**: stoją tam, gdzie je wpisano, a słupy na nawierzchni trafiają tylko do raportu `BLOCKED_COLS`. Po regeneracji `BLOCKED_COLS` musi być pusty, inaczej słup stanie na pasie ruchu.
2. Z M56 wynika tylko jedno: **7–9 rzędów na każdym pomoście, w regularnym rytmie** (P13-030/031, ESTIMATED). Liczba i stacje rzędów (np. ~8 na pomost, rząd na wyspie ronda) to **WORKING_VALUE recenzenta, nie dane M56**. Zdjęcia dowodzą, że rzędy istnieją, ale nie podają ich stacji. Stacje trzeba dobrać z mapy nawierzchni (wyspa ronda, pasy zieleni) i potwierdzić kadrami.
3. Kamery kontrolne z pozycji c027 i c022 (Panoramax, ref.) oraz 018 (CC0; GPS ±15 m).

**Pozostałe wnioski** (nadal otwarte na main `edb552499`):

| Element | Gra dziś | Po M56-FIX | Działanie |
|---|---|---|---|
| A ekran pomostu SW | `reason`: „southbound deck is assumed symmetric (UNVERIFIED)” | SOURCED, CC0 20221203_111814 (P13-040) | przepisać `reason` w `andersa-viaduct-putry-style` |
| A kształt słupów | `reason`: „yellow-painted round piers” (geometria już fazowana 1,0×1,2, faza 0,25) | prostokątne fazowane z oczepem, jaśniejszy panel na czole (P13-034) | poprawić tekst; panel na czole jako detal materiału (opcjonalnie) |
| A krawędź od pasa dzielącego | `barrier: dark_rails` (ADR 0159; override nie mówi, której krawędzi dotyczy) | od pasa dzielącego jasna/ocynk balustrada z pochwytami, bez ekranu (P13-079, ref.) | sprawdzić, czy krawędź wewnętrzna nie dostaje ciemnej bariery ani ekranu |
| B ekrany | `noise_screen: null` | brak na obu pomostach (P13-073/080, CC0) | ✓ bez zmian |
| B słupy | l. 280 `reason`: „plain grey cylindrical”; `col_shape: stadium` | szare, zaokrąglone narożniki, czerwona węższa ściana/pas (P13-076, 065) | poprawić `reason` (sprzeczny z `stadium`); geometria OK |
| B rzędy | 4 na połowę (ADR 0144) | połowa SE ≥ 4–5 do krawędzi kadru (061), ok. 6 grup (065, z obu pomostów) | zgodne na dolnej granicy, bez zmian |
| B przekrój | „box girders with sloped webs” | UNVERIFIED (P13-081) | bez zmian |
| Bramka 3 | `gate3_reference_map.json`: tylko 7204 i 20201102 | CC0: 20221203_111814 (A, SW), 20210320_092717/092737 (B, połowa SE) | dodać jako kadry porównawcze |

## 4. Errata (do poprawki przy scaleniu albo w następnej paczce — nie blokuje)

1. **Sezon:** P13-034 (2021-05-03) ma „jesień”, a P13-039 (2021-05-03) ma „lato”. Powinno być „wiosna” (tak jak w P13-015/041/043/044).
2. **P13-076 (B, kształt słupa):** „przekrój zaokrąglony” → „prostokątny z zaokrąglonymi narożami, węższa ściana czerwona”. Tak opisuje to sam Mistral w P13-065 i tak widać na c065.
3. **Kolejność ekran/balustrada na zewnętrznej krawędzi A jest opisana niespójnie.** 015/016/018: „ekran, za nim balustrada”. 017/023: „balustrada i za nią ekran”. Nie rozstrzygam tego; ADR 0146 (słupki bariery przed ekranem od strony jezdni) zostaje w mocy. Zgłaszam do ewentualnej weryfikacji.
4. **P13-017:** pozycja z EXIF (5,6 m od osi) przeczy widokowi z kilkudziesięciu metrów. Mistral to odnotował w audycie, ale nie w samym wierszu. Dopisać „pozycja niepewna”.
5. **README §3 (rzędy A):** dopisać, że c023 pokazuje jedną szerszą przerwę między podporami, żeby zdanie „nie widać przęsła ~95 m” nie było czytane jako „przęsła są równe”.

## 5. Dla lidera

- **Scalić PR #54** (squash albo merge; diff dotyczy tylko `research/mistral/p13-andersa-viaducts/`). Errata 1–5 można nanieść przy scaleniu albo zostawić na następną paczkę.
- ZIP: `C:\Users\matma\Downloads\m56fix-p13-crops.zip` (zweryfikowany). Wycinki już rozpakowane w `research/_incoming/mistral-p13-andersa-viaducts-fix-crops/`. ZIP M56 (`de50ff75…`) nadal nie jest w `research/_incoming`.
- Gra: P1 z §3 (podpory pomostu SW Putry przez `pier_lines_en`) oraz cztery poprawki tekstu i referencji z tabeli. Żadna nie jest warunkiem scalenia M56.
- Bloku do `MISTRAL-FIXES-12.md` nie dodaję (werdykt nie jest FIX).
