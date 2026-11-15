# REVIEW 2026-11-14 — `dojgreen-0186` (ADR 0186 — Dojlidy: zieleń i skrzyżowanie kadru `P11-063`)

Recenzent: visual-critic (nie autor), tylko odczyt. Kryterium nadrzędne D51: rozpoznawalność > materiały.

Materiał:
- **Runda `B-r4` (aktualna re-weryfikacja, `2026-11-15`)**: gałąź `dojgreen-0186` HEAD `da3640105` (poprawki `bb07398ee` z `2026-11-14 22:17:40` po scaleniu `origin/main` z `e668a9588` w `ba050b034`), worktree `.claude/worktrees/dojgreen-0186`; porównania `sbs-P11-063-{Low,High}.jpg`, `sbs-B-r4-{Low,High}.jpg`, `B-r4/{Low,High}/photo-P11-063.png` (1920×1080), `B-r4/zoom-{thicket,trees}-{Low,High}.jpg`, `B-r4/sbs-P11-{001,056,094}-{Low,High}.jpg`, `B-r4/Low/route-s1370.png`, logi i `stats.txt` z `B-r4/`.
- **Runda `B-r3` (poprzednia recenzja, `2026-11-14`)**: HEAD `5a26ff4fd`, `artifacts/dojgreen-0186/B-r3/`, porównania `A-r1`, `B-r1`, `B-r2`, `artifacts/dojind-0196/sbs-r4/` oraz referencja `research/_incoming/mistral-p11-dojlidy-photos/files/P11-{001,056,063,094}.jpg` (w worktree katalog `mistral-p11-dojlidy-photos-v2` nie występuje na dysku; lewa połowa SBS zawiera zdjęcia referencyjne).

Współrzędne pikseli:
- `sbs-P11-*-{Low,High}.jpg` i `sbs-B-r4-{Low,High}.jpg` (`1920×540`): lewa połowa `x=0..959` zdjęcie referencyjne, prawa połowa `x=960..1919` render (`y=0..539`).
- `photo-P11-063.png` i `route-s1370.png` (`1920×1080`): pełna rozdzielczość renderu (w SBS przeskalowane do `x_sbs = 960 + x/2`, `y_sbs = y/2`).

**Brak zrzutu z telefonu** — `docs/06 §5 pkt 2` niespełniony; dla zmiany danych regionu akceptowalne do scalenia, przed bramką wymagane.

---

## Werdykt (B-r4): SCAL

Wszystkie trzy blokujące problemy **P1** z zakresu ADR `0186` (P1-1 trójkątne „namioty” na `thicket`, P1-2 czarne poziome pasy samozacienienia na `thicket` High, P1-3 powtarzalne drzewa „na patyku” z białym szwem `"X"` na Low i kantem karty na High) oraz regresja znikających ogrodzeń panelowych Low (`e668a9588`) zostały **naprawione lub zredukowane do poziomu P2**.

Rozpoznawalność kadru `P11-063` spełnia próg **P** (`D51`), przyrost pamięci wynosi jedynie `+0.6 MB` `WORLD_MEMORY` (`0` nowych tekstur), a `drawsEst` na Low (`279`) pozostaje o `44` niższe od `dojind-0196 r4` (`323`). Brak **P0** i **P1** blokujących scalenie.

### Pozostałe uwagi po scaleniu (nieblokujące / P2 i higiena repozytorium)
1. **Backlog P2 (`0186`)**: drobne ciemne cętki samozacienienia na ścianie `thicket` w High (`dark<30%: 9.1%` vs `0.2%` Low), nieco zbyt żywy ceglany odcień `berberis_red` względem ciemnego bordo ze zdjęcia `P11-063.jpg` oraz dwie drobne gałązki u dołu korony `ash` widoczne w zbliżeniu High.
2. **Higiena testów i Region C po scaleniu do `main`**:
   - Pliki `artifacts/dojgreen-0186/pytest-gis.log` (`14.11.2026 19:03:44`) i `editmode.log` (`14.11.2026 19:05:43`) w worktree pochodzą jeszcze z rundy `B-r3` (sprzed merge'a `ba050b034` o `21:34` i poprawki `bb07398ee` o `22:17:40`, choć `bb07398ee` nie dotykało plików C#, a ADR 0186 odnotowuje `13 passed` dla testów celowanych `test_dojgreen_0186.py` i `test_dojlidy_0179.py` oraz świeże `B-r4/build_world.log`, `import.log`, `vqa-Low.log`, `vqa-High.log` z `22:17–22:32`). Po scaleniu do `main` uruchomić pełny `EditMode` + `pytest tests/gis` oraz zregenerować `bialystok-industrial-c/generated/fidelity_qa.json` (nieaktualne po wcześniejszej zmianie `tools/worldgen/roads/junctions.py`).
3. **Bramka (`docs/06 §5 pkt 2`)**: wykonać zrzut z telefonu (Samsung Galaxy A16) dla kadru `photo_P11-063` przed bramką.

---

## Re-weryfikacja B-r4 (`da3640105` / `bb07398ee` + merge `ba050b034`)

### Status wcześniejszych problemów P1 i regresji bazy

| Pozycja z `B-r3` | Status w `B-r4` | Dowód wizualny i liczbowy |
|---|---|---|
| **P1-1** — Trójkątne „namioty” i proste kanty na grzbiecie `thicket` | **NAPRAWIONE** | `B-r4/{Low,High}/photo-P11-063.png`, `B-r4/zoom-thicket-{Low,High}.jpg`: ostrosłup przy `x ≈ 350–465` i długie ukośne krawędzie całkowicie zniknęły; szpaler `T1–T31` tworzy łagodnie pofalowaną, zaokrągloną linię kopuł (`2.1–2.75 m`, skok `≤ 0.25 m`, `ring_step=0.45`, `fill=(1.2, 0.75)`, `local_top=True`, `dome=0.24`). Dodatkowo podniesione do `14–15 m` lewe drzewo z `kuronia-north-park-skyline-trees` wyłania się teraz wyraźnie ponad grzbiet (`x ≈ 240–290, y ≈ 600–655`, częściowa poprawa dawnego P2). |
| **P1-2** — Czarne poziome pasy cienia na `thicket` w High | **POPRAWIONE → P2** | `B-r4/High/photo-P11-063.png`, `B-r4/zoom-thicket-High.jpg`: zniknęło ~15 długich czarnych poziomych cięć po redukcji kart pędów (`sprig=0.70`, `top_sprigs=0.40`, `side_share=0.18`). W czysto wewnętrznym wycinku krzewów (`x=220..580, y=718..765`, `0%` nieba) udział pikseli ciemnych (`mean < 30`) spadł z `12.8%` (`B-r3 High`, `RGB=(40.0, 49.3, 29.3)`) do `9.1%` (`B-r4 High`, `RGB=(42.5, 52.6, 31.1)`). Pozostają drobne ciemne cętki/plamki na High wobec jaśniejszego Low (`RGB=(65.2, 75.1, 53.1)`, `dark<30%: 0.2%`) — poziom **P2**. |
| **P1-3** — Drzewa narożne „na patyku”, biały szew `"X"` (Low) i kant karty (High) | **NAPRAWIONE** | `B-r4/{Low,High}/photo-P11-063.png`, `B-r4/zoom-trees-{Low,High}.jpg`: trzy identyczne `6.0–6.5 m` „lizaki” po lewej zastąpiły osadzone przy ziemi krzewy i niskie formy (`berberis_red` `2.8 m` wpasowany u styku z `thicket`, `shrub` `4.2 m`, `fruit` `5.2 m` z koroną od `0.34–0.42 m`). Dwa wysokie `ash` (`9.2 m` i `10.5 m`) mają ażurowe, wielopłatowe korony bez białych cięć `"X"` na Low i bez pionowego paska karty na High. Wewnętrzne zróżnicowanie korony (`x=1180..1300, y=520..640`) wzrosło z `std=(6.7, 9.6, 6.0)` Low / `(8.3, 12.6, 7.0)` High w `B-r3` do `std=(30.9, 26.9, 35.6)` Low / `(33.4, 29.6, 37.6)` High — bardzo blisko zdjęcia `P11-063.jpg` (`std=(31.4, 36.3, 44.0)`). |
| **P1 (baza)** — Zanik płotów panelowych Low (sprzed `e668a9588`) | **NAPRAWIONE** | Merge `ba050b034` pobrał `e668a9588`. W `B-r4/sbs-P11-094-Low.jpg` (`x=960..1919`), `B-r4/sbs-P11-001-Low.jpg`, `B-r4/Low/route-s1370.png` i w tle `B-r4/Low/photo-P11-063.png` wszystkie przęsła panelowe na Low są pełne i czytelne bez znikania z dystansu. |

### Oceny `B-r4` (1–10)

| Kryterium | Ocena `B-r3` → `B-r4` | Uzasadnienie (`B-r4`) |
|---|---|---|
| Rozpoznawalność `P11-063` (D51) | `7` → **8 / 10** | Spójna sylwetka narożnika: miękka ściana krzewów, bordowy akcent `berberis_red`, stopniowana zieleń schodząca do gruntu i ażurowe wysokie drzewa narożne plus wyraźna korona parkowa w tle po lewej. |
| Zieleń `0186` — krzewy `thicket` | `5` → **7.5 / 10** | Gładki, naturalny profil grzbietu bez trójkątnych szczytów i bez czarnych poziomych pasów; jedynie drobna cętkowatość cienia własnego na High (`P2`). |
| Zieleń `0186` — drzewa i krzewy narożne | `5.5` → **8 / 10** | Zniknął efekt makiety „na patyku” i artefakty `"X"` / kant karty; otwarcie korony (`std ~30–38`) zbliża się do prawdziwego liściastego ujęcia ze zdjęcia. |
| Brak regresji na `001`/`056`/`094`/`s1370` | `7.5` → **9 / 10** | Płoty na Low naprawione po `e668a9588`; brak regresji na `001`, `094`, `route-s1370` (`056` Low MAD `0.642` względem `B-r3`). |
| Budżet Low / High i `WORLD_MEMORY` | `9.5` → **9.5 / 10** | `P11-063` Low: `279` draws / `339 096` tris (`+7 281` vs `B-r3`, nadal `-44` draws i `-3 714` tris vs `dojind-0196 r4`); High: `461` draws / `753 627` tris (`+7 281` vs `B-r3`); `WORLD_MEMORY`: `+0.6 MB` Low/High (`98.8` / `214.1 MB`), `0` nowych tekstur. |

### Budżet, pamięć i logi `B-r4` (różnice względem `B-r3`)
- **`B-r4/{Low,High}/stats.txt`**:
  - Low `photo-P11-063`: `objects=49`, `drawsEst=279` (`shadowDrawsEst=6`), `trisK=339`, `trisExact=339096` (`instanced`: `116` draws / `198` inst. / `173` cells / `38` HLOD / `20775` trisExact); pozostałe kadry `001`/`056`/`094`/`s1370` co do trójkąta identyczne z `B-r3`.
  - High `photo-P11-063`: `objects=86`, `drawsEst=461` (`shadowDrawsEst=138`), `trisK=753`, `trisExact=753627` (`instanced`: `208` / `492` / `277` / `86` / `92231`); `photo-P11-094`: `trisExact=878031` (`+7 281` vs `B-r3`); pozostałe kadry `001`/`056`/`s1370` identyczne z `B-r3`.
- **`WORLD_MEMORY` (`B-r4/import.log`)**:
  - Low: `98.2 MB → 98.8 MB` (`+0.6 MB`; `render_meshes 65.2 MB`, `furniture 7,8 → 8,4`).
  - High: `213.5 MB → 214.1 MB` (`+0.6 MB`; `render_meshes 180.5 MB`, `furniture 7,8 → 8,4`, `plots 2,8 → 2,9`).
  - Build (`B-r4/build_world.log`, `409.2 s`): `plantings.tris = 27363`, `authored_trees = 8` (`tris_low=100`, `tris_high=300`, `skipped={}`).
- **Logi Unity/VQA `B-r4`**: `import.log` (`22:31:30`), `vqa-Low.log` (`22:31:51`, `VISUALQA_RESULT: OK rendered=5`, znany exit code `-1073741819` po zapisie 5 PNG wg ADR 0083), `vqa-High.log` (`22:32:06`, `VISUALQA_RESULT: OK rendered=5`).
- **Uwaga dot. logów testów w worktree**: `pytest-gis.log` (`14.11.2026 19:03:44`) i `editmode.log` (`14.11.2026 19:05:43`) pochodzą jeszcze sprzed `ba050b034` (`21:34:00`) i `bb07398ee` (`22:17:40`); ADR 0186 poświadcza dodatkowo `13 passed` dla celowanego `pytest tests/gis/test_dojgreen_0186.py tests/gis/test_dojlidy_0179.py -q`.

---

## Historia rundy `B-r3` — Werdykt archiwalny: SCAL warunkowo (przed poprawkami `B-r4`)

Skok jakościowy na `P11-063` względem `A-r1` / `REVIEW-2026-11-13-s19-0179` (`N/P`) jest wyraźny: kadr z kamery `[-67.0, 393.5]` (`heading 100°`, `pitch 8°`) trafia z masztem `gate3_signal` przy prawej krawędzi, zniknęły fałszywe sygnalizatory z `n3541204205`, usunięto nagą sosnę z lewej krawędzi za wiatą, mur krzewów `thicket` całkowicie zasłania parking (brak prześwitujących aut), pojawiło się 5 wysokich drzew narożnych, a budżet Low/High oraz przyrost pamięci (`+0.5 MB` `WORLD_MEMORY`, `0` nowych tekstur) są wzorowe.

Nie jest to jednak czyste `SCAL`: silnie kanciaste trójkątne szczyty na grzbiecie `thicket`, czarne poziome pasy samozacienienia na krzewach w High, trzy powtarzalne „lizaki/jajka na patyku” z białymi szwami `X` na Low w grupie drzew narożnych oraz nieaktualna baza `origin/main` (`3bd6e16d4`, sprzed rewertu `e668a9588` przywracającego mipmapy ogrodzeń `fence_` i z nieaktualnym QA Regionu C) blokują ocenę `R` i wymagają warunków przed/po scaleniu.

Warunki scalenia (lider):
1. Przy scalaniu do `main` zachować rewert `e668a9588` w `game/Assets/_Project/World/Import/InstanceImporter.cs` (`ti.mipMapsPreserveCoverage = alpha;`, **nie** brać starszego stanu `3bd6e16d4` z gałęzi, który gubi ogrodzenia panelowe w `B-r3` Low), po czym zregenerować VQA Dojlidy oraz artefakty Regionu C (`fidelity_qa.json` nieaktualne po zmianie `tools/worldgen/roads/junctions.py` na gałęzi).
2. Zapisać w backlogu (lub poprawić przed bramką) usterki **P1** z zakresu `0186`: wygładzenie górnej sylwetki `thicket` (usunięcie trójkątnych ostrosłupów siatki), ograniczenie czarnego samozacienienia liściastych gałązek `thicket` w High oraz zróżnicowanie trzech małych drzew narożnych i likwidacja białych szwów `X` na kartach `kit` w Low.
3. Wykonać zrzut z telefonu (Samsung Galaxy A16) dla kadru `photo_P11-063` przed bramką (`docs/06 §5 pkt 2`).

---

### Oceny `B-r3` (1–10, archiwalne)

| Kryterium | Ocena | Uzasadnienie |
|---|---|---|
| Rozpoznawalność `P11-063` (D51) | **7 / 10** | Sylwetka narożnika Kuronia/Mickiewicza i pozycja prawego masztu `gate3_signal` od razu czytelne; zniknęły fałszywe sygnalizatory z wyspy i nagie sosny na lewej krawędzi; blokuje sztuczny profil krzewów i drzew „na patyku”. |
| Zieleń `0186` — krzewy `thicket` | **5 / 10** | Dobrze domyka tło (zero aut za ścianą) i trzyma skalę 2–3 m oraz brak lewitacji, ale ostre geometryczne trójkąty na grzbiecie oraz ciemne poziome plamy na High psują naturalność. |
| Zieleń `0186` — drzewa narożne | **5.5 / 10** | Skala `9.2–10.5 m` dwóch głównych drzew pasuje do kadru (duży postęp wobec samotnej sadzonki z `A-r1`), ale gęste jednorodne bryły, białe szwy `X` na Low i trio identycznych owali po lewej dają wrażenie makiety. |
| Brak regresji na `001`/`056`/`094`/`s1370` | **7.5 / 10** | Sama logika `0186` jest lokalna dla rejonu `P11-063` (`056` bez zmian); widoczny zanik płotów w `094`/`001`/`s1370` Low wynika wyłącznie ze starszej bazy `3bd6e16d4` przed `e668a9588`. |
| Budżet Low / High i `WORLD_MEMORY` | **9.5 / 10** | `P11-063` Low: `279` draws (`-44` vs `dojind-0196 r4`), `331.8k` tris; High: `461` draws, `746.3k` tris; `WORLD_MEMORY`: `+0.5 MB` na obu tierach. |

---

### Problemy wykryte w `B-r3` (archiwalne — przed poprawkami `B-r4`)

### 1. Zakres ADR 0186 (`P11-063` — zieleń i skrzyżowanie narożne)

**P1 — Trójkątne szczyty siatki („namioty”) i geometryczne krawędzie na grzbiecie `thicket`**
- Gdzie: `B-r3/Low/photo-P11-063.png` i `B-r3/High/photo-P11-063.png` w pasie `x ≈ 20–650, y ≈ 610–675` (`sbs-P11-063-{Low,High}.jpg` `x ≈ 970–1285, y ≈ 305–340`); najwyraźniejszy ostry ostrosłup przy `x ≈ 350–465, y ≈ 615–665` (`sbs` `x ≈ 1135–1192, y ≈ 307–332`) oraz długie proste ukośne krawędzie przy `x ≈ 10–350, y ≈ 635–665` i `x ≈ 540–640, y ≈ 625–655`. Na Low w szparach prześwituje także fasetowany zielony stożek bazowy.
- Przyczyna w kodzie (`tools/worldgen/streetscape/plantings.py` i `Data/Regions/bialystok-dojlidy/overrides.yaml`): profil `thicket` ma zgrubną siatkę (`ring_step=0.7`, `fill=(2.0, 1.1)`, `dome=0.50`, `local_top=False` — środek korony brany z mediany zamiast lokalnego sąsiedztwa), co przy gwałtownych skokach wysokości kolejnych płatów w `mickiewicza-kuronia-shrub-band` (`T5=2.3 → T6=3.0 → T7=3.2 → T9=2.1 → T10=2.0 → T11=3.1`) wyciąga ostre pojedyncze wierzchołki nad linię nieba. Na zdjęciu `P11-063.jpg` ściana krzewów ma miękką, drobnolistną, pofalowaną koronę bez wielokątnych zębów.

**P1 — Ciemne, niemal czarne poziome pasy samozacienienia na `thicket` w High**
- Gdzie: `B-r3/High/photo-P11-063.png` `x ≈ 30–890, y ≈ 670–750` (`sbs-P11-063-High.jpg` `x ≈ 975–1405, y ≈ 335–375`).
- Obserwacja i liczby: na ścianie krzewów w High pojawia się ok. 15 bardzo ciemnych poziomych smug (odstających od jasności Low i zdjęcia). Średnia jasność wycinka `x=150–650, y=690–770` spada na High do `RGB=(44.2, 52.7, 35.4)` wobec `RGB=(64.9, 73.6, 55.3)` na Low i `RGB=(60.7, 64.1, 50.7)` na zdjęciu `P11-063.jpg` (`y=720–810`). Na High nakładające się karty `hedge_sprig_hornbeam` (`sprig_wh=((0.60, 1.20), (0.55, 1.05))`, `top_sprigs=0.8`) rzucają mocne cienie na bryłę bazową i sąsiednie karty.

**P1 — Drzewa narożne (`mickiewicza-kuronia-corner-trees`) jak makiety „na patyku”, z białym szwem `X` na Low i pionowym pasem na High**
- Gdzie: `B-r3/Low/photo-P11-063.png` i `B-r3/High/photo-P11-063.png` w strefie `x ≈ 855–1340, y ≈ 475–720`.
- Szczegóły:
  - Trzy niższe drzewa po lewej (`x ≈ 855–1070`, lokalizacje `-13.2/386.3`, `-3.2/378.8`, `0.6/381.0`, wysokości `6.0–6.5 m`, `crown_base 1.32–1.43 m`) wyglądają jak trzy niemal bliźniacze, symetryczne owale na prostych gołych pniach. W `P11-063.jpg` (`x ≈ 405–465/960`) w tym miejscu rosną niższe, szerokie krzewy sięgające niemal do ziemi (w tym wyraźny ciemnopurpurowy/czerwony krzew po lewej).
  - Dwa duże drzewa narożne (`x ≈ 1085–1340`, `10.5 m` i `9.2 m`) są zbyt jednorodnie zbite i ciemne w środku korony (`x=1180–1300, y=520–640`: odchylenie standardowe jasności/barwy `std=(6.7, 9.6, 6.0)` Low i `std=(8.3, 12.6, 7.0)` High wobec `std=(31.4, 36.3, 44.0)` na zdjęciu, gdzie przez ażurową koronę wielopniowego drzewa wyraźnie prześwituje niebo i gałęzie).
  - **Artefakt krzyżujących się kart na Low**: wyraźne jasnoszare/białe przecięcia `X` i pionowe linie szwów w koronach (`x ≈ 925–950, y ≈ 595–640`; `x ≈ 1030–1055, y ≈ 600–650`; `x ≈ 1235–1250, y ≈ 525–660`).
  - **Artefakt na High**: wąski pionowy pas jasnych/ciemnych liści przecinający środek przedniego dużego drzewa (`x ≈ 1255–1275, y ≈ 500–670`) z karty ustawionej niemal krawędzią do kamery.

**P2 — `kuronia-north-park-skyline-trees` praktycznie niewidoczne za grzbietem krzewów w `P11-063`**
- Gdzie: strefa za `thicket` przy `x ≈ 230–275` w `High/photo-P11-063.png` (prześwituje jedynie ~15 px rozmycia ponad grzbietem).
- Przyczyna: trzy drzewa tła (`(153.0, 453.0, h=12.0)`, `(168.0, 459.0, h=13.5)`, `(178.0, 462.0, h=12.5)`) stoją na terenie `z ≈ 154.53 m` (~4.4 m niżej niż grunt pod kamerą `z ≈ 158.9 m`, oko kamery `z ≈ 160.51 m`) w odległości `228–254 m`. Rzutowanie z pozycji kamery daje wierzchołki w `x ≈ 249–264/1920, y_top ≈ 702–710` wobec osi krzewu `T11` na `~48–52 m` (`h=3.1 m`, `y_top ≈ 714`), więc przy obecnym ukształtowaniu terenu i wysokości `3.0–3.2 m` krzewów prawie nie widać koron parkowych ani dalekich latarni znad ściany zieleni (widocznych w `P11-063.jpg`).

**Co działa dobrze w zakresie `0186`:**
- **Kamera i maszt `gate3_signal`**: kalibracja (`[-67.0, 393.5]`, `heading 100°`, `pitch 8°`) dokładnie trafia geometrią skrzyżowania; maszt `gate3_signal` (`-35.5, 368.0`) stoi przy prawej krawędzi (`x ≈ 1777/1920`, `sbs` `x ≈ 1848/1920`, na zdjęciu `x ≈ 887/960` = `1774/1920`), bez dawnego „masztu na środku drogi” z `A-r1`.
- **Usunięcie fałszywych sygnalizatorów z `n3541204205`** (`mickiewicza-u-turn-not-signalised`): pas rozdziału na wprost i lewy brzeg drogi są wolne od błędnych sygnalizatorów.
- **Usunięcie nagiej sosny z lewej krawędzi** (`mickiewicza-kuronia-shrub-strip-no-rule-trees`): w `B-r3` za wiatą przystankową (`x ≈ 0–200/1920`) nie ma już wysokiego nagiego pnia obecnego w `B-r1`/`B-r2`.
- **Szczelność `thicket`**: ściana krzewów (`31` płatów `T1–T31`) całkowicie zasłania zaparkowane samochody i gruntowo przylega do chodnika bez lewitacji.

---

### 2. Regresja bazy gałęzi względem aktualnego `origin/main` (poza kodem 0186)

**P1 — Wyłączone `mipMapsPreserveCoverage` dla `fence_*` w `B-r3` Low (stan przed `e668a9588`)**
- Gdzie: `sbs-P11-094-Low.jpg` (`x ≈ 960–1919, y ≈ 320–360`), `sbs-P11-001-Low.jpg` (`x ≈ 1150–1350`), `B-r3/Low/route-s1370.png` (`x ≈ 1450–1920`).
- Obserwacja: na renderach Low przęsła ogrodzeń panelowych w odległości >10 m znikają (zostają same słupki lub cienkie strzępy). Gałąź `dojgreen-0186` nie zmieniała `game/Assets/_Project/World/Import/InstanceImporter.cs` (`git diff 3bd6e16d4..HEAD -- game/Assets/_Project/World/Import/InstanceImporter.cs` jest puste), ale jej merge `c07b8ebdc` pobrał `origin/main` na `3bd6e16d4` — chwilę przed commitem `e668a9588`, który na `origin/main` wycofał wyłączenie mipmap dla `fence_`. Ponadto porównanie pamięci `A-main` (`lead-s20/import-dojlidy.log`, po `e668a9588`) i `B-r3` pochodzi przez to z lekko różnych rewizji `main`.

**Stale QA w Regionie C (`pytest-gis.log`)**: zmiana w `tools/worldgen/roads/junctions.py` na gałęzi unieważniła wyprowadzony raport `fidelity_qa.json` w `bialystok-industrial-c` (szczegóły poniżej w sekcji testów).

---

### 3. Poza zakresem ADR 0186 (przypisane do innych zadań — nie blokuje `0186`)

- **Czerwona wiata przystankowa za drzewami narożnymi (`osm_node 9103141028`, `local_en [35.77, 364.11]`)**: widoczna w `photo-P11-063.png` przy `x ≈ 1150–1260, y ≈ 670–715` między pniami drzew narożnych (stan sprzed `0186`, obecna już w `A-r1` i `dojind-0196 r4`); na zdjęciu `P11-063.jpg` w tym narożniku stoi niska biało-szara szafka sterownicza (`x ≈ 670/960`), a przystanek jest poza prawą/lewą częścią tego narożnika.
- **Słupki łańcuchowe (`0183` + `0188`)**: stoją na dalszym chodniku wzdłuż ul. Kuronia (`x ≈ 1060–1350, y ≈ 690–720`) zamiast przy krawędzi wyspy na pierwszym planie — w ADR `0183` celowo wstrzymane do czasu poprawy nawierzchni DDR (`0188`).
- **Brak czerwonego asfaltu DDR i oznakowania (`0188`)**: na pierwszym planie nadal szary chodnik bez wydzielonej czerwonej ścieżki rowerowej oraz brak znaków D-6 / C-13 / A-7 przy przejściu.
- **Niebo / HDR / tył oprawy sygnalizatora `gate3_signal` (`0193`)** oraz **detale budynków przy Kuronia 2/3 (`0196`) i łaty asfaltu (`0194`)**: widoczne w `route-s1370` i `sbs-P11-094`, odziedziczone po poprzednich przeglądach.
- **Daleki horyzont (`0187`)**: pusta linia horyzontu na dalszym planie ponad dachami w `P11-063` i `route-s1370`.

---

### Regresje w `B-r3` na pozostałych kadrach (`001`, `056`, `094`, `route-s1370`)

- **`P11-056`** (`sbs-P11-056-Low.jpg`, `sbs-P11-056-High.jpg`): brak jakichkolwiek zmian i regresji (średnia różnica bezwzględna względem `dojind-0196 r4` wynosi `0.2`).
- **`P11-001` i `P11-094`** (`sbs-P11-001-{Low,High}.jpg`, `sbs-P11-094-{Low,High}.jpg`): drzewa i zieleń ADR `0186` nie pogarszają tych ujęć; jedyna zauważalna zmiana na Low to wspomniane zanikanie siatki płotów (`fence_`) ze starszej bazy przed `e668a9588` (w High płoty wyświetlają się poprawnie).
- **`route-s1370`** (`B-r3/{Low,High}/route-s1370.png`): brak regresji ze strony `0186`; poza znikającym ogrodzeniem po prawej na Low (`x ≈ 1450–1920`), pozostałe niedoskonałości budynków przy Kuronia i nieba pochodzą spoza `0186`.

---

### Liczby, budżet i testy `B-r3` (archiwalne)

### Budżet renderu (`artifacts/dojgreen-0186/B-r3/{Low,High}/stats.txt`, `overcast`)

- **Low** (`msaa=2`, `renderScale=0.75`):
  - `photo-P11-001`: `objects=51`, `drawsEst=342`, `shadowDrawsEst=109`, `trisK=464` (`trisExact=464422`), `instanced`: `53` draws / `40` inst. / `9k` tris (`9296` exact) / `154` cells / `10` HLOD
  - `photo-P11-056`: `objects=34`, `drawsEst=125`, `shadowDrawsEst=3`, `trisK=159` (`trisExact=159725`), `instanced`: `35` draws / `34` inst. / `2k` tris (`2037` exact) / `89` cells / `9` HLOD
  - `photo-P11-063`: `objects=49`, `drawsEst=279` (**`-44`** vs `dojind-0196 r4`: `323`; vs `A-r1`: `262`), `shadowDrawsEst=6`, `trisK=331` (`trisExact=331815` vs `342810` w `0196 r4` i `305631` w `A-r1`), `instanced`: `116` draws / `198` inst. / `20k` tris (`20775` exact) / `173` cells / `38` HLOD — mieści się w hipotezie Low `docs/06 §6` (`≤ 300–400` draws, `≤ 400–600k` tris).
  - `photo-P11-094`: `objects=43`, `drawsEst=202`, `shadowDrawsEst=45`, `trisK=293` (`trisExact=293717`), `instanced`: `92` draws / `69` inst. / `17k` tris (`17032` exact) / `163` cells / `47` HLOD
  - `route-s1370`: `objects=44`, `drawsEst=334`, `shadowDrawsEst=74`, `trisK=271` (`trisExact=271259`), `instanced`: `69` draws / `60` inst. / `11k` tris (`11184` exact) / `200` cells / `26` HLOD
- **High** (`msaa=2`, `renderScale=1`):
  - `photo-P11-001`: `objects=76`, `drawsEst=457`, `shadowDrawsEst=363`, `trisK=701` (`trisExact=701948`), `instanced`: `139` draws / `361` inst. / `33038` exact
  - `photo-P11-056`: `objects=58`, `drawsEst=210`, `shadowDrawsEst=18`, `trisK=291` (`trisExact=291582`), `instanced`: `108` draws / `218` inst. / `9719` exact
  - `photo-P11-063`: `objects=86`, `drawsEst=461`, `shadowDrawsEst=138`, `trisK=746` (`trisExact=746346`), `instanced`: `208` draws / `492` inst. / `277` cells / `86` HLOD / `92231` exact — mieści się w hipotezie High `docs/06 §6` (`≤ 700–1000` draws, `≤ 1.5–2M` tris).
  - `photo-P11-094`: `objects=169`, `drawsEst=513`, `shadowDrawsEst=195`, `trisK=870` (`trisExact=870750`), `instanced`: `190` draws / `387` inst. / `469` cells / `215` HLOD / `68646` exact
  - `route-s1370`: `objects=76`, `drawsEst=489`, `shadowDrawsEst=360`, `trisK=623` (`trisExact=623318`), `instanced`: `153` draws / `429` inst. / `44534` exact

### `WORLD_MEMORY` (`B-r3/import.log` vs `lead-s20/import-dojlidy.log`)

- **Low**: `98.2 MB → 98.7 MB` (**`+0.5 MB`**): `render_meshes 64.5 → 65.1 MB`, `instances 18.2 MB` (b/z), `collision_src 15.5 MB` (b/z); zmiana kategorii: `furniture 7,8 → 8,3` (`+0.5 MB`).
- **High**: `213.5 MB → 214.0 MB` (**`+0.5 MB`**): `render_meshes 179.8 → 180.3 MB`, `instances 18.2 MB` (b/z), `collision_src 15.5 MB` (b/z); zmiana kategorii: `furniture 7,8 → 8,3` (`+0.5 MB`), `plots 2,8 → 2,9` (`+0.1 MB`).
- QA generatora (`streetscape_qa.json`): `authored_trees`: `trees=8`, `tris_high=320`, `tris_low=160`, `skipped={}`.

### Testy automatyczne (`artifacts/dojgreen-0186/`)

- **`editmode.log`**: `581 total, 580 passed, 0 failed, 1 skipped (Skipped:Ignored)`.
- **`pytest-gis.log`**: `1155 passed, 2 xfailed, 3 failed` (`1248.77s`). Wszystkie 3 porażki dotyczą Regionu C (`bialystok-industrial-c`, nieaktualny build po zmianie `tools/worldgen/roads/junctions.py`):
  - `tests/gis/test_p1_0161.py::test_ring_mast_survives_the_carriageway_clearing`
  - `tests/gis/test_road_fidelity.py::test_report_not_stale` (`['tools/worldgen/roads/build_world.py', 'tools/worldgen/roads/junctions.py']`)
  - `tests/gis/test_world_v31.py::test_forest_trees_reference_their_cell`
