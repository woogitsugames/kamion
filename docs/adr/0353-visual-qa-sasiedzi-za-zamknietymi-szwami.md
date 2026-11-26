# ADR 0353 — visual-qa: prawdziwi sąsiedzi za zamkniętymi szwami kafla (szlaban w osi drogi tylko w zrzutach)

Status: Proposed, 2026-11-26 (agent world-edge-s24). Numer do potwierdzenia przez lidera (równoległe ADR).
Powiązane: ADR 0141 / 0169 (zamknięcia krawędzi, jedno źródło), 0273 (streaming kafli, szwy), D95 (szlaban kafla przy
rondzie Knyszyn = błąd), raport krytyka `artifacts/critic-s24-wave11/CRITIC.md` pkt 5.

## Kontekst
Krytyk fali 11: czerwono-biały szlaban w osi drogi na końcu widoku w prawie każdym kadrze osiowym
(`artifacts/regen-wave-11-s24/vqa/dw671-tykocin-03/High-clear/route-s2035.png` i in.).

1. **Co to jest.** `WorldEdgeBuilder` stawia jedno `Closure_*` (bariery + tablice U-20 + collider) na każdej drodze, która
   przecina krawędź kafla, `ClosureSetbackM` = 60 m w głąb (ADR 0169; `world_edge.authored.json` może skrócić do 8 m).
   Dane: graf dróg kafla (`ReadExits`), strona przecięcia `exitSide`. Każdy kafel ma zamknięcia na wszystkich swoich
   krawędziach — także tych, za którymi stoi następny kafel trasy.
2. **Gra.** `WorldStreamer.RefreshEdges` ukrywa zamknięcie, gdy oba kafle szwu są Ready (`EdgeClosureRules.SeamReady`).
   Przejazd Białystok → Tykocin na PC (`win-build/artifacts/win/runs/20261124-122130/player.log`, High, GTX 1070):
   sąsiad Ready przy pojeździe **377–384 m** od kafla (load 535–566 ms, aktywacja 403–447 ms), więc szlaban (60 m w głąb)
   znika ok. **320 m przed nim**. Klatka `shot_t0160.png` (~465 m przed szlabanem Maczka) — szlabanu nie widać. Na
   zewnętrznej krawędzi świata (brak sąsiada w `tile_graph.json`) szlaban zostaje — to zamierzone (ADR 0082/0169).
3. **visual-qa** otwiera jedną scenę kafla. Sąsiedzi były ładowane (`WorldNeighbourQa`, `-qaNeighbours`) tylko dla kafli
   z `needsNeighbourContext` (dziś knyszyn), a `scripts/visual-qa.ps1` nie przekazywał tej flagi. Kamera `route-s2035`
   w dw671-tykocin-03 stoi ~155 m przed szwem S; za szwem jest dw671-tykocin-04 (w grafie) → w grze szew byłby otwarty.
   Szlaban w kadrach osiowych to artefakt zrzutu pojedynczego kafla, nie granica obszaru gry.

## Decyzja
1. `WorldNeighbourQa`: domyślnie `-qaNeighbours auto`. Ładowani są sąsiedzi krawędziowi (N/E/S/W, nie narożni) po tych
   stronach, na których kafel zamyka co najmniej jedną drogę (strona z `Closure.exitSide`, fallback jak w streamerze:
   `EdgeSides.ClosureSide`), **oraz** każdy sąsiad z grafu (także narożny), którego prostokąt leży w promieniu ładowania
   streamingu (`StreamingSettings.BaseLoadRadiusM` = 400 m) od którejkolwiek kamery kontrolnej — gra miałaby go wtedy
   w pamięci (przykład: `truck-34` przy spawnie 247 m od narożnego dw671-tykocin-01; bez niego szlaban szwu 02/01
   zostawał na końcu widoku). Wybór w czystej funkcji `EdgeClosureRules.QaNeighbourIds` (2 testy EditMode). Sąsiad
   niezaimportowany w danym tierze → ostrzeżenie i szew zostaje zamknięty (jak w buildzie bez tego kafla); brak sąsiada
   w grafie (granica świata) → zamknięty. Ładowanie jak dotąd: scena `_Tile` addytywnie, `AdoptVisualQaTile` (gotowanie
   kolizji, `RefreshEdgesAround`) — ta sama logika szwów co w grze.
2. `-qaNeighbours none` (`visual-qa.ps1 -Neighbours none`) = sam kafel: QA samych zamknięć (kamery `edge-*`) i
   porównania ze starymi zrzutami. Jawna lista (`-Neighbours a,b`) zachowuje stare, ścisłe zachowanie (brak importu = błąd).
3. Nie ukrywamy zamknięć „na ślepo” nad pustką (zasada D95) i nie ruszamy logiki gry ani danych świata.

## Konsekwencje
- Kamery osiowe pokazują to, co kierowca: drogę ciągnącą się w następny kafel. Kamery `edge-*` na szwach wewnętrznych
  pokazują otwarty szew (stan gry); zamknięcia ogląda się przebiegiem `-Neighbours none`.
- Koszt QA: do 8 dodatkowych scen `_Tile` (w praktyce 2–3; dw671-tykocin-03: 3) w edytorze (High ~0,5–0,8 GB pamięci świata każda, ESTIMATED z tile_graph)
  i dłuższy przebieg (otwarcie + gotowanie kolizji). Wymaga zaimportowanych sąsiadów w tym samym tierze; bez nich wynik
  jak dotąd (z ostrzeżeniem w logu).
- Statystyki `stats.txt` (draws/tris) obejmują teraz także geometrię sąsiadów widoczną w kadrze — porównując z falami
  sprzed tej zmiany, użyć `-Neighbours none`.

## Dowody
`artifacts/world-edge-s24/` (main): `none/` (sam kafel) vs `auto/` (02, 04, 01), High clear 1920x1080, Win64, ta sama
sesja i kamery; `cmp-*.jpg` (góra none, dół auto), `zoom-route-s2035.png`, logi visual-qa. route-s2035 i truck-34:
szlaban zniknął, droga ciągnie się w sąsiedni kafel. Szew 03/04 (route-s2035, edge-south): bez szczeliny, schodka,
przerwy oznakowania i różnicy koloru (visual-critic, przebieg r1: szew 9/10; FAIL r1 za truck-34 → naprawione regułą
promienia kamer w r2, `auto-r1/` = stan r1).

## Ujawnione przy okazji (stan gry, nie skutek tej zmiany)
- **Horyzont za załadowanymi kaflami jest pusty** (`auto/edge-north.png`, `edge-east.png`, daleki plan `truck-34`):
  `EdgeSides.FarSectorMayShow` chowa sektor dalekiego planu kafla w każdym kierunku, w którym graf ma sąsiada, także
  narożnego (03: E, S, NE, SW → wszystkie cztery sektory). W grze daje to szarą mgłę nad polami tam, gdzie dalszy kafel nie
  jest wczytany. Zrzuty pojedynczego kafla pokazywały tu fałszywie pełną ścianę lasu i słupy WN. Do osobnego zadania:
  daleki plan jako pierścień za ostatnim wczytanym kaflem (ADR 0085 / 0308), nie per kafel bieżący.
- `stats.txt` „instanced (props+trees)” czyta statyczne `WorldInstances.Last` — przy kilku kaflach to licznik ostatnio
  renderowanego komponentu (często sąsiada), więc w `auto` wygląda na zero. Telemetria, nie render; do poprawy razem z
  sumowaniem po wszystkich `WorldInstances`.

## Otwarte
- W grze szlaban szwu jest widoczny w kadrze, dopóki sąsiad nie jest Ready: na PC dalej niż ~320 m przed szlabanem
  (kilka pikseli przy FOV 55°), na telefonie dłużej (load UNVERIFIED). Za ciężarówką szew zamyka się, gdy stary kafel
  zaczyna się wyładowywać (> 700 m z tyłu, promień 400 + histereza 300 m). Możliwa poprawka w grze (osobny ADR):
  renderer zamknięcia ukryty, gdy sąsiad jest w drodze (Loading/Activating) i pojazd > ~250 m od szlabanu; collider zostaje.
  Nie wdrożone — wymaga pomiaru, czy w ogóle jest zauważalne.
