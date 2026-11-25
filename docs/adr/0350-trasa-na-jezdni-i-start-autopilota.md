# ADR 0350 — Wysokość trasy z jezdni (nie z terenu pod nią) i start autopilota trasy z punktu spawnu (spawn-flip-s24)

Status: Proposed, 2026-11-25 (agent spawn-flip-s24). Numer do potwierdzenia przez lidera (równoległe ADR).
Powiązane: ADR 0262 / 0277 (sieć bezpieczeństwa startu, brak wolnego miejsca), 0235 (streaming, wymiana trasy na trip),
0229 (log startu regionu). Zgłoszenie: build #9 (`artifacts/full-build-9-s24/pcm-b9-dk65-07.log`,
`artifacts/regen-wave-10-s24/vqa/cmp-dk65-06-drive.jpg`), oba błędy także w buildzie #8.

## Kontekst
**1. `-scene dk65-07` nie startuje** — `[START] no free place for the combination: route_s 90.0, zone 85.0-837.4 m, searched
200 m ahead and 200 m back (103 places) (collider 'col_asphalt')`. Blokerem jest sama jezdnia. Pomiar na scenie buildu #9
(parser kolizji `colprobe.py`, `artifacts/spawn-flip-s24/`): w punkcie startu (XZ 973.29, 381.56) col_asphalt 14.946 m,
col_terrain 14.191 m, zapisana wysokość trasy 14.191 m. Trasa leżała na terenie **pod** nawierzchnią (nasyp 0.4–0.83 m), a pudło
sprawdzania startu zaczyna się 0.5 m nad trasą → każde z 103 miejsc „zajęte” przez asfalt.
Przyczyna w imporcie (`WorldSceneBuilder`, wysokości trasy z raycastów kolizji): dwa pierwsze punkty trasy leżą poza kaflem
(x = 1025 > 1024) → brak trafienia → y = 0, a reguła wiaduktów „trafienie najbliższe wysokości poprzedniego punktu” wybrała od
trzeciego punktu NAJNIŻSZĄ warstwę (teren) i trzymała się jej do końca. Skan 53 scen High buildu #9:
**21 kafli ma trasę > 0.3 m pod jezdnią** (`route-vs-road-b9.txt`; np. knyszyn-w 992/995 punktów, max 0.76 m; dk65-monki-02
max 1.48 m). Tylko dk65-07 przekroczył 0.5 m akurat w całej strefie startu. Test `StartClearanceTests.ImportedScene_*` tego
nie widział: sceny są zapisane z wyłączonymi MeshColliderami chunków (odroczone gotowanie, `WorldCollisionCooker`), więc test
nie widział ani jezdni, ani terenu.

**2. dk65-06: autopilot trasy przewraca zestaw** — odtworzone na buildzie #9 również BEZ streamingu i `route_to`
(`-scene dk65-06 -autopilot route -speed 50 -telemetry 1`, `dk65-06-b9-drive.csv`): start z punktu spawnu sceny (route_s 340,
katalog), `route_s` follower'a utknął na 102.06 m, skręt kół stały 0.46°, prędkość ~11 km/h, prawe przednie koło zjeżdża z
asfaltu t = 12 s (surface 0 → 5), przechył −8° t = 17 s, −32° t = 19 s, −84° t = 22 s (wywrotka w rowie, ~(−265.7; −761.0) w
układzie dk65-06, ~260 m od południowej krawędzi kafla — nie na szwie dk65-06/07). Trasa dk65-06 jest poprawna (wysokości
= col_asphalt, skan). Przyczyna: `StartRouteDriver` wołał `SeekTo` tylko przy argumencie `route_s`; dla startu z punktu spawnu
follower zaczynał od 0 m, jego okno 20 segmentów zatrzymało się w lokalnym minimum odległości (102 m), a pure pursuit celował
~240 m dalej → prawie zerowy skręt; zestaw pojechał prosto z łuku. Nie kolizja, nie collider na szwie, nie spawn w powietrzu.

## Decyzja
1. `Game.World.RouteGround` (czyste reguły, wspólne dla importu i gry): brak trafienia = nieznane (NaN, nigdy 0); przy znanej
   wysokości sąsiada wygrywa NAJWYŻSZA powierzchnia w oknie ±1.5 m (jezdnia nad terenem; pomost wiaduktu ≥ 4.5 m wyżej i droga
   pod mostem zostają poza oknem); bez odniesienia — najwyższa; nieznane punkty z sąsiadów (`FillMissing`). Okno 1.5 m =
   `WORKING_VALUE`.
2. Import (`WorldSceneBuilder.RouteHeight`): wysokości trasy tylko z MeshColliderów kafla (jezdnie, krawężniki, mosty, teren);
   pudła propów, zamknięcia i szlabany to przeszkody, nie grunt. Działa po reimporcie kafla.
3. Gra (`SpawnSafety.Pose` / `RoadY`): pudło startu stoi na nawierzchni pod punktem trasy (raycast non-alloc w oknie wokół
   zapisanej wysokości, tylko MeshCollider, bez kolizji samego zestawu) — ten sam grunt, na którym spawn stawia koła
   (`RouteSpawnPose`). Naprawia sceny już zaimportowane, bez reimportu; przeszkoda-pudło (bela, słupek, zamknięcie) nadal
   blokuje start.
4. Autopilot trasy: `SeekRouteDriverToStart` — follower startuje z `route_s`, a bez niego z punktu spawnu sceny
   (`NearestRouteS`), przed wymianą trasy na trip nawigacji. `PathFollowerDriverInput`: gdy okno 20 segmentów nie ma nic bliżej
   niż 12 m (`LostDistanceM`, `WORKING_VALUE`), szuka na reszcie ścieżki — tylko w przód (trasa mijająca samą siebie nie cofa).
5. `StartClearanceTests.ImportedScene_*` otwierają scenę z włączoną kolizją chunków (jak player po `WorldCollisionCooker`).

Fizyka bez zmian: kolizje zestawu, opony, przegub — nietknięte; nic nie jest maskowane.

## Dowody
- EditMode: `RouteGroundTests` (9, w tym na prawdziwej scenie dk65-07: 90 punktów trasy z reguły importera leży na col_asphalt
  ±0.02 m; stara trasa do 0.83 m pod nią), `PathFollowerStartTests` (3), `StartClearanceTests` z kolizją: **dk65-07 czerwony
  na starym `SpawnSafety`** (ten sam komunikat co player: `90.0 -> 90.0 (collider 'col_asphalt')`, NoSpace), **zielony po
  poprawce**; dk65-06 zielony; WorldStreamerHook0273/RouteLinks zielone. PlayMode `StartSafetyTests` + `RouteSpawnTests` 10/10.
- Telemetria wywrotki i zrzut: `artifacts/spawn-flip-s24/`.

## Konsekwencje / ryzyka
- Gra naprawiona dopiero w nowym buildzie; trasy w scenach — po reimporcie kafli (21 kafli z trasą pod jezdnią).
- Siatka-przeszkoda (MeshCollider) na środku pasa w oknie 1.5 m byłaby wzięta za grunt — dziś przeszkody na jezdni to pudła.
- Re-akwizycja follower'a w przód może przeskoczyć na późniejszy odcinek trasy przechodzący < 12 m od zestawu, gdy ten zjedzie
  z trasy > 12 m (tylko w trybie pomiarowym autopilota).
- Respawn (`Spawn` z HUD) przy włączonym autopilocie nie przewija follower'a wstecz (bez zmian; poza zakresem).
