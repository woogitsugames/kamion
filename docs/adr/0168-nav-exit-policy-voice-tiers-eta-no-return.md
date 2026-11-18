# ADR 0168 — Navigation: roundabout exit counting, three voice tiers, ETA at 1 Hz, no-return zone

Status: Accepted (merged to main 2026-11-13, `668b027b7`; status updated 2026-11-16); originally: implemented on branch `nav-0168` (2026-11-13, s17); not merged. Tests: nav-runner (xUnit) and Unity EditMode;
phone NOT measured (the change is CPU-light and allocation-free, see "Evidence").
Source: open points of the Mistral r6 review of the GPS (exit numbering, repeated announcements, ETA cost, GC proof)
and the dead-end audit of ADR 0169 (`tools/worldgen/navgraph/dead_ends.py`).

## Decisions

1. **Roundabout exit number** (`ExitCountPolicy`, `RoutePlanner.HasExit`). Only roads that can legally be driven
   OUT of the ring count; a one-way entry never counts. Default `AnyMotorVehicle`: exits closed to this truck
   (hgv=no / access=no, B-5, weight / axle / height / length limits below the combination, hgv=destination) still
   count, because the driver counts the exits he sees. `ThisTruck` (skip them) is kept as an option. On the region's
   rings no exit is closed to the truck, so both policies give the golden numbers (checked on every golden route).
2. **Voice: at most three announcements per manoeuvre** (`NavVoiceDriver`): far (2 km / 1 km / 500 m), near
   (300 / 200 / 100 m), now (reaction + braking distance, min 30 m). Triggers scale with speed (far = 45 s lead,
   near = 15 s lead, WORKING_VALUE). Only the closest due tier is said; tiers only go forward, so distance drift
   (GPS-like jitter, stopping, reversing a few metres) and the guidance flipping back to a passed manoeuvre never
   repeat a sentence. A new route starts over.
3. **ETA at 1 Hz** (`RouteTracker.EtaPeriodS = 1`): `NavEta` is O(route points); it is recomputed once per second
   and immediately on a new route, the displayed value is held in between.
4. **Zero GC proof in nav-runner**: `GcAllocCounter` (Unity `Recorder` shim, thread-static) asserts that tracker +
   voice driver allocate nothing over a whole golden drive.
5. **No-return zone (ADR 0169 proposal 1, without changing the generated file).** At load `RouteGraph` computes
   (Kosaraju SCC -> forward / backward closure of the largest component) the nodes that can be driven to but have
   no directed way back, restricted to those that lead to a boundary node (the outbound one-way carriageways cut by
   the tile, ending at the closure 60 m before the edge). Region `bialystok-industrial-c`: **30 edges, 26 nodes,
   2730 m** - exactly the audit numbers. Effects:
   - destination snap (`Snap(mainComponentOnly)`), `NearestMainNode`, `MainNameAt` skip the zone like off-reach;
   - `NavigationService.SetPin` treats a tap there like an off-reach tap: the pin goes to the nearest road outside
     the zone and the HUD shows `GoalOffReach` ("Cel poza zasięgiem mapy - pinezka na najbliższym węźle");
   - the planner never expands an edge of the zone, unless the truck already stands in it (it can still drive on
     to a goal ahead); a goal snapped there by the fallback gives `NoPath`.
   A one-way spur inside the map with no boundary at its end is NOT in the zone (integration r5 decision kept:
   such a spur stays a valid destination). Computed, not a file flag: no regeneration, no format change; when the
   generator writes a "no return" bit later, the runtime rule can be dropped.

## Golden routes changed (reviewed diff)

Re-recorded with `dotnet run -c Release --project tools/nav-runner/Runner -- --write-golden`; only two pairs differ,
both because their goal lay in the no-return zone (the western Andersa NW / Maczka W carriageway is outbound to the
closure; the opposite carriageway is an entry-only, off-reach part):
- G02 Kombatantow -> Andersa NW: goal (-457.95, -55.97) -> (-320, -162), before the point of no return (-340, -149).
  Same manoeuvres up to the roundabout (exit 4); 3785.1 -> 3608.8 m. `NoTruckMedian_ForcesRoundaboutDetour` still
  holds with the new goal.
- G21 Skidelska -> Maczka: goal moved to the link from Andersa NW (-361.45, -118.74); 3496.7 -> 3123.8 m.
Tests that used the old Andersa NW point (`NavRoutingTests`, `RoundaboutExitTests`, `Nav0168Tests`) use the new one.

## Evidence

- nav-runner: 84 -> **94/94** (`artifacts/nav-0168/navrunner-3.log`; +2 no-return tests on top of the 8 ADR 0168 tests).
- Unity EditMode (worktree, 6000.3.28f1): **507/510 passed**, 1 skipped, 2 failed = the known main failures
  `CarPaintMaterialTests.DepositionChannel_*` (not touched here); `Nav0168Tests` 10/10, `NavRoutingTests` 15/15
  (`artifacts/nav-0168/editmode-20261113-120925.xml`).
- Unity PlayMode, filtered `NavReachabilityServiceTests;NavHudTests`: **9/9** incl. the new
  `Synthetic_SetPin_NoReturnTap_SnapsOutOfTheZone` (`artifacts/nav-0168/playmode-20261113-121332.xml`). The full
  PlayMode suite was not run.
- Mutation test (nav-runner, `artifacts/nav-0168/mutation.txt`): 6/6 mutants killed - planner entering the zone,
  snap ignoring the zone, zone without the boundary rule, voice tier repeat, ETA every frame, default policy
  ThisTruck.

## Risks / open

1. Far / near lead times, the 30 m minimum and the 40 m tier gap are WORKING_VALUES; not tuned in the cab.
2. A truck that drives past a point of no return in free driving gets no warning (ADR 0169 proposal 2: HUD warning;
   proposal 3: median crossover before the closure - road generator). Not done here.
3. The no-return rule depends on node boundary flags (bit0). Graph files without them have no zone (old behaviour).
4. `GoalOffReach` text says "poza zasięgiem mapy"; for the zone it is correct in effect (the road leaves the map) but
   a dedicated text could be clearer - owner's call.

## Dopisek s23 (D31): złote trasy po c-regen3 (#93, rondo Putry z ortofoto)

CI `nav` na main: G04/G05/G29 ~2 m krótsze niż wzorzec (tolerancja 2,0 m). Ustalone z geometrii w gicie, nie na ślepo:
- `bialystok-industrial-c_route.bytes` przed (`be35fbc36^`) i po (`be35fbc36`, c-regen3): węzły, długości OSM (koszt A*),
  flagi, zakazy — bez zmian; zmieniła się geometria JEDNEJ krawędzi: 157 = `w180144451:2629251364-4075461271` (pierścień S
  ronda Putry), przez override `putry-ring-s-placement` z ADR 0226 (MA-010: oś 2,9 m w lewo na całej długości →
  profil 1,2 m na zachodnim końcu, ~0,2 m w środku). Promień pierścienia praktycznie bez zmian (dopasowanie okręgu do
  4 krawędzi pierścienia: R 32,10 → 32,22 m) — skrócenie NIE pochodzi z Δr × kąt.
- `RoutePath.Length` sumuje odcinki narysowanej trasy, łącznie ze skokiem z końca poprzedniej krawędzi (węzeł OSM 293)
  na początek osi jezdni krawędzi 157. Skok = przesunięcie osi na zachodnim końcu: 2,900 → 1,196 m (Δ −1,704).
  Rzut celu „Putry” (-555,6; -10,18) na oś 157: 22,973 → 22,690 m od początku (Δ −0,283; cel 2,87 → 1,20 m od osi).
  Długość osi 157: 46,020 → 46,093 m (Δ +0,073); koniec osi (węzeł 394) bez zmian.
- Przewidywanie vs pomiar (C# RoutePlanner, `dotnet test` na obu wersjach `.bytes`):
  dojazd do Putry (G04, G05, G24, G29) −1,704 − 0,283 = **−1,987** / zmierzone −1,986; przejazd przez 157 (G26)
  −1,704 + 0,073 = **−1,631** / −1,631; start w Putry (G36) (46,093 − 22,690) − (46,020 − 22,973) = **+0,356** / +0,355.
  Manewry, numery zjazdów i `costS` (koszt liczony po długościach OSM + rzut) bez zmian.
Wzorce przepisane `--write-golden` (wynik identyczny z ręczną zmianą 6 pól `lengthM`): G04 564,6→562,6, G05 1107,5→1105,5,
G24 791,1→789,1, G26 3001,3→2999,7, G29 1221,9→1219,9, G36 2436,8→2437,2. Tolerancja 2,0 m bez zmian.
Otwarte (bez zmian tutaj): skok węzeł OSM → oś przesuniętej jezdni wlicza się w długość trasy (artefakt ADR 0144 —
oś generowana vs węzły OSM); osobny problem `test_region_file_is_reproducible` — patrz raport PR D31.

## Dopisek s23 (D35): wycinanie osi jezdni z tolerancją 1e-6 m (reprodukowalność `.bytes` między platformami)

Problem (D31): świeży build `bialystok-industrial-c_route.bytes` na Linuksie ≠ plik zatwierdzony z Windows na 8 krawędziach,
różnica = jeden krok próbkowania osi (~0,5 m) na jednym końcu. Przyczyna potwierdzona analizą danych (skrypt diagnostyczny,
nie w repo): `load_carriageway_axes` wycinał zakres krawędzi z gęstej osi łańcucha przez `searchsorted(s, s1*k)`; granica
zakresu jest wierzchołkiem łańcucha, czyli próbką, a `s1*k` trafia w nią z błędem kilku ulp. W regionie C 32 granice leżą
0,9e-15…5,7e-14 m od próbki — WSZYSTKIE to koniec łańcucha (`raw_end * (length / raw_end)` vs `s[-1]`). 8 z nich wypadało
na Linuksie PONIŻEJ ostatniej próbki → próbka (prawdziwy koniec osi) odcięta; dokładnie te 8 krawędzi różniło się od pliku.
Znak błędu zależy od kolejności sumowania długości (platforma/numpy) — na Windows wypadł inaczej (mechanizm potwierdzony,
konkretna przyczyna różnicy sumowania na Windows UNVERIFIED).

Decyzja: `axis_span_slice(s, a, b, eps=AXIS_SPAN_EPS_M=1e-6)` (WORKING_VALUE) — reguła jawna: oba końce WŁĄCZNIE,
bierzemy każdą próbkę z `a − eps ≤ s[i] ≤ b + eps`. Wierzchołek wspólny dwóch krawędzi należy do obu (jak dotąd przy trafieniu
dokładnym). 1e-6 m ≫ szum (1e-14) i ≪ krok 0,5 m. Pozostałe miejsca w `navgraph`: brak innych `searchsorted`/porównań float
na granicach; jedyny próg to Douglas-Peucker `best > 0,05 m` na współrzędnych zaokrąglonych do 1 mm (ryzyko teoretyczne, nie ruszane).

Wynik (Linux, nowy kod vs zatwierdzone pliki): różnią się wyłącznie `pts` krawędzi (węzły, długości OSM, flagi, zakazy, pasy
bez zmian); region C 10 krawędzi, ≤ 0,500 m; pozostałe regiony 0–8 krawędzi, ≤ 0,500 m (dk65-06/08/09/10/11, dk65-monki-01,
knyszyn-s/-w: 0). Podgląd złotych tras (runner w izolowanym katalogu, nowy `.bytes` C): 8/36 par — `lengthM` +0,4…+0,5 m,
`costS` +0,1…+0,2 s (G03 G14 G19 G20 G21 G28 G31 G35); manewry, kąty, numery zjazdów bez zmian.
Testy regresji: `test_axis_span_slice_is_stable_on_float_noise` (syntetyczna oś, zaburzenia ±1e-14…±1e-9),
`test_region_axis_slices_stable_under_perturbation` (wszystkie zakresy regionu C). `test_region_file_is_reproducible` zielony
dopiero po regeneracji `.bytes` u lidera (Windows) nowym kodem.
