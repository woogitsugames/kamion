# ADR 0285 — trasy łączące korytarza streamingu (Białystok → Knyszyn → Tykocin bez przerw)

Status: Proposed (agent stream-gaps-s23, 2026-11-16). Numer nadaje lider przy scalaniu (0283 zajęty przez HUD/menu #166).
Powiązane: ADR 0235 (streaming kafli), 0273 (jeden model świata), 0231 (pierścień, gałąź world2-s23), 0203/0204/0209/0212
(trasy kontrolne kafli Knyszyna), D63 (najpierw przejezdne), raport integracji `docs/reports/INTEGRATION-2026-11-16-int-stream-s23.md`.

## Kontekst — dlaczego Knyszyn-W i Tykocin „wypadały” z korytarza
Właściciel chce jechać bez przerwy Białystok → Knyszyn → Tykocin (`-scene … -stream 1`, 19 regionów). Ustalenia:
1. **Sąsiedztwo i szwy były w porządku.** `tile_graph.json`: knyszyn | knyszyn-w (bok W, 2048 m), knyszyn-w | dw671-tykocin-01
   (bok S). Streamer otwiera szwy wg sąsiedztwa + dostępności sceny `_Tile`, nie wg portali (portale/korytarze czytają tylko
   testy). DW671 Tykocka przecina szew knyszyn | knyszyn-w w węźle brzegowym (760587,0; 611964,5) i szew knyszyn-w |
   dw671-tykocin-01 w (760129,2; 611583,0) — te same identyfikatory węzłów `Bw…` po obu stronach. Jazda ręczna przechodziła.
2. **Przerwa = trasa autopilota.** `WorldStreamer.ContinueRoute` (int-stream-s23) dokleja trasę startową kafla, gdy zaczyna
   się ≤ 3 m od końca ścieżki. Trasa kontrolna `knyszyn` (ADR 0204) kończy się na **Rynku** (761086, 612403) — ślepy koniec:
   dalsza droga jest za ciężarówką (zawrotka zestawu). Trasa `knyszyn-w` (ADR 0209) zaczyna się na DK65 w stronę Moniek
   (596 m od końca knyszyn), `dw671-tykocin-01` (ADR 0212) na szwie S knyszyn-w (2164 m). Dodatkowo C → Maczka: trasa C
   kończy się na DK8/DK19 ~700 m przed szwem.
3. **Kafel `tykocin` nie istnieje w main.** Łańcuch dw671-tykocin-02…09 + `tykocin` jest na gałęzi pierścienia `world2-s23`
   (ADR 0231; tam graf: `dw671-tykocin-01..tykocin`, 10 kafli, portale gap ≤ 0,04 m). W main korytarz kończy się na
   dw671-tykocin-01 (koniec świata na S, „(-9,6) not built”).
4. **Dojlidy** (`bialystok-dojlidy`, x 779019–781067, y 589055–591103) leżą 1 kolumnę na E i **2 rzędy (4096 m) na S** od C —
   brak wspólnej krawędzi z czymkolwiek; w streamingu nigdy nie są chciane (nie ma sąsiada).

## Decyzja
1. **Trasy łączące jako dane** `Data/Streaming/route_links.yaml` (authored) → generator
   `tools/worldgen/streaming/route_links.py` → `Resources/WorldStreaming/route_links.json` (JsonUtility). Każdy link leży w
   jednym kaflu; linia = środek prawego pasa co 2 m liczona **tym samym kodem co `scripts/export-route.py`**
   (`pipeline.effective_graph` → najkrótsza ścieżka `roadgraph.to_digraph` → `pipeline.build_network` + `roads.route.lane_route`).
   To nie są `authored_overrides` regionów: `route_endpoints.json`, `route_start.json`, `overrides.yaml`, spawn, kamery i katalog
   regionów bez zmian.
2. **`replaces_route`**: link zaczyna się w tym samym punkcie co trasa kontrolna kafla i jest doklejany ZAMIAST niej (Knyszyn:
   DK65 od szwu z knyszyn-s → rondo DK65/DW671 → ramię celu). **`after_route`**: link zaczyna się na końcu trasy kafla (C).
3. **Cel jazdy** `destination` (`any` | `tykocin` | `monki`); argument uruchomienia `-route_to <cel>` (albo `route_to=<cel>`),
   domyślnie **tykocin** (polecenie właściciela). Czytany przez `WorldStreamer.TryInstallFromLaunch` z linii poleceń — bez zmian
   w `DrivingLabBootstrap` / asmdef.
4. **Wygładzenie złączy** (`head_from` / `tail_to`, `BLEND_M = 60 m`, WORKING_VALUE): koniec / początek linku przesunięty liniowo
   na 60 m tak, by trafić dokładnie w punkt sąsiedniej trasy. Potrzebne, bo pasy przy rondzie Knyszyna są jeszcze zwężane
   37 m przed szwem w kaflu knyszyn (lane_route), a w knyszyn-w już nie (skok 2,74 m w poprzek); C → Maczka 1,875 m.
5. **Korytarz jako lista kafli** (`corridors` w yaml): generator utrzymuje prefiks kafli obecnych w `Data/Regions` (main: 19 z 28;
   po scaleniu world2-s23 automatycznie do `tykocin`) i sprawdza każdą parę: sąsiad krawędziowy N/E/S/W + złącze trasy ≤ 2 m.
   Wynik w `route_links.json` (`corridors[].joins`), osobno od `tile_graph.json` (`portals`/`corridors` bez zmian — testy D67).
6. **Runtime** (`RouteLinks.cs`, `WorldStreamer.ContinueRoute` + `FindLinkAt`): co decyzję 0,25 s, bez alokacji — najpierw link
   celu, którego kafel jest Ready, a pierwszy punkt ≤ `routeJoinM` od końca ścieżki; trasa kafla zastąpionego linkiem jest
   pomijana. Log `[STREAM] route continued by link <id> in <kafel> (to <cel>): +N m`.

## Wyniki (main 64e54592e + ta gałąź)
- Linki: C→Maczka 1509 m, knyszyn DK65→DW671 W 618 m, knyszyn DK65→DK65 W 639 m (monki), knyszyn-w DW671 596 m.
- Korytarz `bialystok-tykocin`: 19 kafli (C … knyszyn-s, knyszyn, knyszyn-w, dw671-tykocin-01), 18 złączy, wszystkie
  **gap 0,0 m**, wszystkie boki krawędziowe; brakujące 9 = kafle world2-s23.
- QA szwów linków (`tools/worldgen/streaming/link_seams.py`, siatki chunków GLB): skok wysokości osi ≤ 0,041 m, załamanie osi
  ≤ 0,008°, przesunięcie linii autopilota 0,000 m na wszystkich 4 szwach linków.
- **Znaleziska do właścicieli kafli (nie naprawiane tutaj):** knyszyn-s | knyszyn — asfalt 9,48 m vs 7,64 m 2 m od szwu (skok
  szerokości 1,84 m; world2 / ADR 0275 seam_taper); knyszyn | knyszyn-w na DW671 — linie ±1,75 m po stronie knyszyn, tylko −1,75
  po stronie knyszyn-w (linia urywa się na szwie; int-world3); C | Maczka — linia 2,91 m tylko po stronie Maczka.

## Przejazd w buildzie Windows (exe `kamion-0.1.0-14243bcc83-regions`, 19 regionów, High, 60 fps, RTX 5070 — maszyna dewelopera)
`Kamion.exe -scene knyszyn-s -stream 1 -autopilot route -speed 70 -route_s 1900` (domyślny cel tykocin):
log `[STREAM] route continued by link knyszyn-dk65-to-dw671-w in knyszyn (to tykocin): +618 m` → `… knyszyn-w-dw671 in
knyszyn-w … +596 m` → `route continued into dw671-tykocin-01: +2608 m`; rebase origin ×3 (0,73–1,60 ms), wyładowane knyszyn
i knyszyn-s. Run B: `stream-report.py --gate` **PASS** (loads 3, closed seams 0, resets 0, ładowanie kafla p50 250 / max
677 ms, gotowy przy ≥ 380 m, klatek > 33,3 ms: 6, max 1201 ms = klatka startowa). Run A: zawieszenie playera ok. t = 145 s
(klatka 1849 ms, potem brak logu, kill po 290 s) tuż przed rebase do dw671-tykocin-01 — **nie powtórzyło się** w run B ani C;
podejrzenie: znana niestabilność D3D12 przy równoległym obciążeniu GPU (crash 887a0001, HANDOVER 16.11 15:2x) — UNVERIFIED.
Zrzuty: `artifacts/stream-gaps-s23/shotA-60s.jpg` (DK65 przed Knyszynem), `shotB-95s.jpg` (DW671 Tykocka za rondem, szew
knyszyn | knyszyn-w), `shotC-135s.jpg` (szew knyszyn-w | dw671-tykocin-01).

## Plan dla Dojlid (trzecia przerwa, bez realizacji w tym zadaniu)
Najkrótsze połączenie krawędziowe: 3 nowe kafle siatki 2048 m — (779019, 591103) N Dojlid, (779019, 593151), (779019, 595199)
= sąsiad E kafla C — albo (776971, 593151) jako sąsiad S kafla C zamiast trzeciego. Wybór zależy od drogi łączącej Dojlidy z
trasą C (Andersa / Rondo Putry), której nie zweryfikowałem — **UNVERIFIED**, do ustalenia z OSM przy zleceniu (D63: najpierw
przejezdne). Pierścień ADR 0231 (world2-s23) nie zawiera kafli między C a Dojlidami.

## Konsekwencje / ograniczenia
- Start w samym kaflu knyszyn (`-scene knyszyn`): ścieżką jest trasa kontrolna do Rynku i autopilot staje na Rynku (zastąpić
  można tylko trasę doklejaną). Przejazd do Tykocina autopilotem: start w knyszyn-s albo wcześniej (`-scene knyszyn-s`,
  `-scene bialystok-knyszynska -route_s 2300`). Jazda ręczna — bez ograniczeń.
- Po scaleniu world2-s23 / int-world3 (zmiany sieci dróg Knyszyna) linki trzeba przeliczyć:
  `uv run --project tools/worldgen python tools/worldgen/streaming/route_links.py` (test `test_links_json_fresh` to wymusza).
- Rozwidlenia dalej (Mońki, Jasionówka) — kolejne linki z `destination`; `-route_to monki` już działa do knyszyn-w.

## Testy
- pytest `tests/gis/test_route_links_s23.py` (8: świeżość, korytarz do Tykocina, złącza krawędziowe i zamknięte, BFS grafu,
  kafle w zestawie `d67-full`, linki w kaflu bez skoków, linki przez rondo nie przez Rynek, geometria szwów z GLB).
- EditMode `WorldStreamerRouteLinksTests` (5: dane z Resources przez JsonUtility, złącza na nowych szwach, parsowanie
  `-route_to`, doklejanie linku właściwego celu tylko gdy kafel Ready i tylko raz, polityka przy 90 km/h przez narożnik
  czterech kafli knyszyn-s / knyszyn / knyszyn-w / dw671-tykocin-01 dla Low/Medium × telefon/PC).
