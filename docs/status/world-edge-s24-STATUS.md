# world-edge-s24 — szlaban w osi drogi w zrzutach visual-qa (CRITIC fala 11 pkt 5)

Gałąź: `worktree-agent-a45822541efad5332`, baza `f4b7a47b9`. Dowody: `C:\Users\matma\Documents\Claude\kamion\artifacts\world-edge-s24\`.

## Krok 1 — rozpoznanie (zrobione)
- Szlaban = zamknięcie krawędzi kafla `WorldEdgeBuilder` (ADR 0141/0169): jedno `Closure_*` na każdą drogę przecinającą
  krawędź kafla, `ClosureSetbackM` = 60 m w głąb kafla (`world_edge.authored.json` może skrócić do 8 m). Dane: graf dróg
  kafla (`ReadExits`), strona wyjścia `exitSide`.
- Gra (streaming, ADR 0273): `WorldStreamer.RefreshEdges` ukrywa zamknięcie, gdy oba kafle szwu są Ready
  (`EdgeClosureRules.SeamReady`). Na zewnętrznej krawędzi świata (brak sąsiada w grafie) szlaban zostaje.
- visual-qa ładuje pojedynczy kafel; sąsiedzi tylko przez `WorldNeighbourQa` (`-qaNeighbours`, domyślnie tylko gdy
  `needsNeighbourContext` w tile_graph — dziś knyszyn). `scripts/visual-qa.ps1` nie przekazuje `-qaNeighbours`.
- route_s2035 (dw671-tykocin-03): kamera (94,-878) patrzy na S; szew S (-1024) ~155 m przed kamerą, szlaban (-964) ~95 m;
  za szwem jest dw671-tykocin-04 (w grafie). Szlaban to więc szew wewnętrzny, nie granica świata.
- Decyzje właściciela: D95 (szlaban kafla przy rondzie Knyszyn = błąd do usunięcia); brak decyzji o granicy świata.

## Krok 2 — gra ze streamingiem (z logów, bez nowego uruchomienia)
- Przejazd `win-build/artifacts/win/runs/20261124-122130` (Białystok→Tykocin, PC High): sąsiad Ready przy pojeździe
  377–384 m od kafla, load 535–566 ms + aktywacja ~0,4 s → szlaban (60 m w głąb) znika ~320 m przed nim. Klatka t=160
  (~465 m przed szlabanem) — szlabanu nie widać. Wniosek: w środku trasy w grze szlaban nie stoi w osi; to artefakt
  zrzutów pojedynczego kafla.

## Następny krok
Krok 3: visual-qa domyślnie dociąga sąsiadów, w których stronę patrzą kamery (WorldNeighbourQa), render przed|po.

## Krok 3 — poprawka (kod zrobiony, render w toku)
- `WorldNeighbourQa`: domyślnie `-qaNeighbours auto` (sąsiedzi krawędziowi po stronach z zamknięciami, niezaimportowani
  pomijani z ostrzeżeniem); `none` = sam kafel; lista = ściśle. `EdgeClosureRules.QaNeighbourIds` + test EditMode.
  `scripts/visual-qa.ps1 -Neighbours`. ADR 0353 (Proposed).
- Render A/B (worktree, świeże Library Win64; sceny dw671-tykocin-02/03/04 skopiowane z win-build `_Generated`, poza gitem):
  `pwsh -NoProfile -File artifacts/world-edge-s24/vqa-ab.ps1` (w tle) → `artifacts/world-edge-s24/{none,auto}/`.

## Krok 3 — wynik
- r1 (`auto-r1/`, sąsiedzi 02, 04): route-s2035 bez szlabanu, szew czysty; visual-critic FAIL — truck-34 nadal szlaban
  (szew 02/01 przy narożniku) + pusty horyzont.
- r2 (`auto/`, + reguła promienia ładowania 400 m od kamer → także narożny 01): truck-34 i route-s2035 bez szlabanu.
- Pusty horyzont = stan gry (`FarSectorMayShow` chowa sektory w stronę każdego sąsiada z grafu, także narożnego) —
  ujawniony, nie naprawiany tu (ADR 0353 „Ujawnione”). Statystyka instanced w auto = `WorldInstances.Last` (telemetria).
- EditMode r1: 1439 pass, 4 fail = StartClearance na skopiowanych scenach Low (środowisko); `_Generated` usunięte,
  powtórka → `artifacts/world-edge-s24/editmode2.out`.

## Następny krok
EditMode r3 (`editmode3.out`): 1438 pass, 0 fail, 153 skip. Zadanie gotowe do przeglądu lidera; nie scalać. Kolejne: daleki plan jako pierścień za wczytanymi kaflami (osobne zadanie), suma WorldInstances w stats.txt.
