# STATUS — agent spawn-flip (build #9: dk65-07 bez startu, dk65-06 wywrotka)

- [22:40] Bug 1 przyczyna: trasa dk65-07 zapisana na col_terrain 0.4–0.8 m POD col_asphalt (importer: 2 pierwsze punkty poza kaflem → y=0 → reguła „najbliżej poprzedniego” wybrała najniższą warstwę). Dowód: colprobe na World_dk65-07_High.unity (s=90: asphalt 14.946, terrain 14.191 = route y). Poprawka: RouteGround (Pick/FillMissing), importer RouteHeight, SpawnSafety.Pose/RoadY (wysokość jezdni). Testy EditMode RouteGroundTests.
- Bug 2: dk65-06 trasa OK (route y = top asphalt), wywrotka odtworzona BEZ streamingu (route autopilot, route_s 340). Telemetria w toku.
- NASTĘPNY KROK: pwsh scripts/test.ps1 -Platform EditMode (filtr RouteGroundTests) po zwolnieniu slotu Unity; analiza telemetrii dk65-06.
