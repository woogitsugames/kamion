# ADR 0168 — Navigation: roundabout exit counting, three voice tiers, ETA at 1 Hz, no-return zone

Status: implemented on branch `nav-0168` (2026-11-13, s17); not merged. Tests: nav-runner (xUnit) and Unity EditMode;
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
