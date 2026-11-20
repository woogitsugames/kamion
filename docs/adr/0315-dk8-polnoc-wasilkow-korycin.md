# ADR 0315 — korytarz DK8 na północ: Białystok → węzeł Wasilków → w stronę Korycina

Status: Proposed (agent s8-north-s24, 2026-11-20). 0314 = krywlany (scalony), więc 0315 jest wolny.

Powiązane: D93 pkt 4, D95 pkt 4 (następny region po Krywlanach: S8/DK8 dalej, Wasilków/Korycin), D63 (najpierw przejezdne),
ADR 0203 (siatka 2048 m), 0209 (pin NMT), 0285/0292 (linki i korytarze), 0300 (route_obstacles), 0302 (nawigacja).

## Kontekst
Zlecenie: przedłużyć korytarz `bialystok-s8` o kafle na północ „w stronę Wasilkowa/Korycina”.
**Ustalenie z przypiętego pbf (2026-11-08):** S8 kończy się na węźle Białystok Zachód (`dk8-s8-jeroniki`/`dk65-01`).
Ekspresówka na północ od `dk65-02` (S19 Księżyno – Białystok Północ – Wasilków) ma w OSM `highway=construction`
(siatka (−4,2), (−3,2), (−1,3), (0,3)) — nie ma przejezdnej S8/S19 z korytarza S8 do Wasilkowa. Jedyna przejezdna
droga to **DK8 (ref 8;19, Al. Tysiąclecia Państwa Polskiego → Białostocka)**, wychodząca z kafla C przez jego północny
szew; w Wasilkowie (węzeł bezkolizyjny, koniczyna) DK19 odchodzi na wschód (Sokółka), DK8 idzie dalej na
północny zachód (Korycin, Augustów).

## Decyzja
1. **4 kafle w kolumnie i = 0 siatki ADR 0203** (`tools/worldgen/qa/dk8_north_plan.py`, plan
   `docs/reports/map/dk8_north_plan.{json,png}`; wejścia i wyjścia tras = przecięcia jezdni DK8 z krawędziami kafla
   policzone z przypiętego pbf, te same co w build_region):
   `dk8-wasilkow-01` (0,1), `dk8-wasilkow-02` (0,2), `dk8-wasilkow-03` (0,3, węzeł Wasilków),
   `dk8-korycin-01` (0,4, DK8 wychodzi zachodnim szwem do (−1,4)). Powiat wg udziału powierzchni (PRG): 01 = 2002
   (57,8 %) + 2061, pozostałe 2002. Pin NMT 2025 jak C (ADR 0209), łańcuchowo na północ.
2. **Link `c-dk8-north-to-wasilkow`** (kafel C, `replaces_route` jak `c-andersa-to-wygoda`): trasa C kończy się na
   jezdni DK8 w stronę północy ~330 m przed szwem, a w tym punkcie zaczyna się link `any` `c-dk8-to-maczka` (na zachód);
   dla celu `wasilkow` link zastępuje trasę C i jedzie dalej DK8 do wejścia trasy `dk8-wasilkow-01`.
   Korytarz `bialystok-wasilkow` (cel `-route_to wasilkow`), trip nawigacji „Wasilków (DK8)” (`tools/ui/build_nav_trips.py`).
3. **Katalog:** grupa „DK8 Wasilków”, 4 wpisy po S8.
4. **`gugik_index`:** ponawianie zapytań WFS przy zerwanym połączeniu / przekroczeniu czasu (3 próby, 15/45/120 s);
   warstwa, która nie odpowiada po próbach, jest traktowana jak brak warstwy, ale zapisywana w
   `Data/SourceManifests/<kafel>.gugik-availability.json` → `unavailable_layers` (raport, nie cisza). Przyczyna:
   20.11 warstwa `SkorowidzOrtofomapy2026` dla bbox kafli 01/02 zrywała połączenie przy każdej próbie; ortofoto jest
   tylko referencją (docs/05 §3), NMT/BDOT/LoD z tego nie zależą.

6. **Po scaleniu road-widen (D94, ADR 0306):** wszystkie 4 kafle przebudowane (r2) i zaimportowane (r3, po scaleniu
   też roof-tiles ADR 0316 — dachy/płoty działek w GLB są jeszcze sprzed 0316, odświeży je pełna przebudowa).
   Link C dostał drugie wychylenie 1,0 m / ±30 m przy (777718, 596034) — po przebudowie C 4 punkty opon osi napędowej
   poza nawierzchnią w s 1346–1349 m → 0 / 0.
   Trasa 01 kończy się 0,31 m obok wejścia trasy 02 → link `wasilkow-01-to-02` (jak `s8-03-to-s8-04`: ta sama ścieżka,
   ostatnie BLEND_M m przesunięte na start 02; ślad zestawu 0 / 20559 pkt poza nawierzchnią).
7. **Plan ADR 0278:** komórki (0,1)..(0,4) były już kandydatami planu (`dk8-dk19-pn-01`, `dk8-dk19-jurowce`,
   `dk8-sochonie`, `dk8-woroszyly`); zbudowane pod nazwami tego ADR — `map_plan_0278.built_regions` pomija je jak kafle
   ADR 0288, plan zostaje bez zmian.

## Konsekwencje / otwarte

- Wyjaśnienie `dk8-seam-cli` (20.11): krótka sekcja DK8 pozostaje w dłuższym łańcuchu.
  D94 przesuwa ukośne końce osi o 0,078/0,091 m poza płaszczyznę szwu; filtr 0,05 m w QA
  błędnie zgłaszał urwanie, a filtr sąsiadów generatora stosował taper DK8 tylko po jednej stronie.
  Przynależność do szwu ustalana z granicznego węzła grafu; obustronny taper daje 8,75 m.
  Pozostają jawne 2 FAIL położenia osi po 0,25 m (DK8/serwisowa), bez rozluźnienia progów.
  Korycin: jednopasowa sekcja way 304733170 ma `edge_strip=0`, co wyłączało P-7b; oznakowanie
  A/S/GP działa teraz także bez opaski, w całości na asfalcie. Testy siatki bez Unity/przebudowy;
  szczegóły i zakres regeneracji: `docs/reports/dk8-seam-cli.md`. Poniższe r1/r3 pozostają historią.

- qa.seams 01|02: 2 FAIL „droga urywa się na szwie” (trunk 876126468, service 306912739). W sieci 01 po D94 odcinek
  27,6 m way 876126468 przy szwie nie tworzy osobnego łańcucha (łańcuch w211148033 kończy się na szwie z taperem
  9,0 → 8,5 m); wysokości |dz| ≤ 0,014 m, przesunięcie toru 0,31 m przejmuje link `wasilkow-01-to-02`. Do wyjaśnienia
  w narzędziu szwów lub w regule taperu.
- 03: road_consistency „obstacle none” na trasie s 614–626 m (łańcuch 703487195/239748583, lewe pasy przy łącznicy
  węzła; także w r1) — route_obstacles na siatce nie widzi tam ani przeszkody, ani dziury.
- Na moście DK8 w 01 (way 145631572/3, 3 pasy) krawężnik mostu wchodzi w lewy pas (pas 0, przy pasie dzielącym):
  road_consistency 63 × `bridge_kerb` w pasie 30 m wokół trasy, 5,2–6,6 m od toru ciężarówki (route_obstacles 0) —
  błąd generatora mostów przy wielopasowej jezdni, do osobnego zadania (występuje też w porosly/bojary).
- `arrow_no_exit` w 01 i 02: strzałki „slight_right” do zjazdów wychodzących zachodnią krawędzią kolumny (kafle (−1,j)).
- Prawa linia krawędziowa korycin-01 ok. s 480 m niewidoczna na renderze r2 (szerokie pobocze) — sprawdzić po r2.
- DK8 biegnie 150–300 m od zachodniej krawędzi kolumny i = 0: zabudowa i łącznice po zachodniej stronie drogi są
  ucięte krawędzią kafla (w 01 węzeł z ul. do Dziesięcin częściowo w (−1,1)); widok zastępuje far-field. Kafle (−1,j)
  — później, jeśli właściciel uzna to za widoczne (D63).
- Dalszy ciąg do Korycina: kafel (−1,4) i dalej na NW (DK8 w (−1,5), (−2,6..10)).
- S19 Białystok Północ – Wasilków: po oddaniu do ruchu (nowy pbf) — pętla S8 → S19 → Wasilków.

5. **Link C:** pierwsze ~400 m jak `c-andersa-to-wygoda` (rondo Pamięci Bieżeństwa) — bez wychylenia 12 punktów opon
   naczepy poza nawierzchnią (s 364–368 m); użyte to samo `swing` (2,0 m / ±30 m) → 0 / 0.

## Liczby (zmierzone 20.11, worktree s8-north-s24)
| wielkość | wartość | źródło |
|---|---|---|
| trasy kontrolne 01 / 02 / 03 / korycin-01 | 2071,26 / 2125,83 / 2067,86 / 962,59 m | `route_start.json` |
| link c-dk8-north-to-wasilkow | 2755 m | `route_links.json` |
| złącza korytarza bialystok-wasilkow (4 pary) | r1: 0,000–0,007 m; r3 (po D94, z linkiem 01→02): 0,000–0,008 m | `route_links.json` corridors |
| ślad zestawu (ciągnik + naczepa 13,6 m) poza nawierzchnią, link C | 0 / 27359 pkt (przed swing: 12) | `qa/link_swept_check.py` |
| route_obstacles korytarz (5 kafli + link) | colliders 0, visual 0 (no-surface 1 próbka w 02, korycin, linku C) | `artifacts/s8-north-s24/route_obstacles-r1.json` |
| qa.seams C, 01, 02, 03, korycin (4 szwy, 21 dróg) | 0 FAIL | `artifacts/s8-north-s24/seams/seams-r1.md` |
| wysokość na szwach (GLB), drogi trasy (trunk) | \|dz\| ≤ 0,038 m; wszystkie drogi ≤ 0,088 m | `qa/seam_z.py`, `seams/seam_z-r1.json` |
| road_consistency na trasie 01 / 02 / 03 / korycin | 0 / 0 / 0 / 0 (w kaflu: 95 / 20 / 239 / 9) | `generated/road_consistency_qa.json` |
| WORLD_MEMORY High 01 / 02 / 03 / korycin (r3) | 159,0 / 199,3 / 200,5 / 148,7 MB | import Win64 (log import-region) |
| WORLD_MEMORY Low 01 / 02 / 03 / korycin (r3) | 78,7 / 86,6 / 87,6 / 61,2 MB | j.w. → `streaming/tile_graph.py` |
| najgorsze okno 3 kafli + przypięty C | bez zmian: bojary 798,4 / 1940,1 MB (≤ 850 / 2000) | `tile_graph.json` |
| route_obstacles r3 (korytarz + 2 linki) | colliders 0, visual 0 | `route_obstacles-r3.json` |
| qa.seams r3 | 02\|03, 03\|korycin, C\|01: 0 FAIL; 01\|02: 2 FAIL (dopasowanie łańcucha, patrz otwarte) | `seams/seams-r3.md` |
| EditMode Win64 | 1398 pass / 0 FAIL / 107 skip | `artifacts/tests/editmode-20261120-161228.xml` |
| far_field High (trójkąty) 01 / 02 / 03 / korycin | 148 684 / 126 879 / 107 997 / 91 089 | build_world |
| NMT | 2025 na wszystkich 4 kaflach (pin), ortofoto 2024 0,25 m | `Data/SourceManifests/gugik-*` |
