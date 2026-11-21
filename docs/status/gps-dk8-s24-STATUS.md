# STATUS gps-dk8-s24 — build #3 P2 GPS „zawróć” na al. Tysiąclecia + RegionSelectTests d67-full

- Przyczyna (log `artifacts/full-build-3-s24/logs/win-run-20261121-140003.log` l. 51, 60, 70, 125, 130, 134, 149, 210):
  1. Autopilot jedzie trasą kontrolną C (`route_start.json`: zajezdnia -> DK8/DK19 na północ) + link `after_route`
     `c-dk8-to-maczka`, który zawraca przez przejazd w pasie dzielącym (-821, 861) i wraca na południe do szwu Maczka.
     GPS (odcinek 1 tripu tykocin) skręca na zachód na węźle DK8/DK19 (~(-540, 50)); po minięciu węzła na północ cel jest
     za ciężarówką, więc „zawróć” jest poprawne (reroute 3: +1,5 km = objazd linku). To wada danych linku, nie planera.
  2. Błąd planera (naprawiony): reroute z węzła skrzyżowania — wszystkie krawędzie 0 m, remis wygrywała jednokierunkowa
     odnoga ~63° od kursu (re-plan z (81, -454) startował na niej i planował fałszywe zawracanie). `RoutePlanner` start snap:
     ponowny snap do krawędzi zgodnej z kursem także gdy krawędź jest „obok kursu” (cos < 0,5), nie tylko „pod prąd”.
- Testy: nav-runner `NavTripDk8MaczkaTests` (3 + 1 skip = wada linku), EditMode `NavRoutingTests.Tysiaclecia_TripLeg1Reroute_*`
  (nieuruchomiony — robi lider), `RegionSelectTests.ShippedCatalog_D67Full_IsEveryCatalogRegion` (54 = cały katalog).
  nav-runner całość: 77 pass, 1 skip, 23 fail = 22 Golden_MatchesPlanner + 1 NavVoice — identyczne przed i po zmianie
  (golden nieodświeżone po przebudowie C 61c521c2c, różnice 2-7 m).
- NASTĘPNY KROK (lider): `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64`; link `c-dk8-to-maczka` przenieść na
  `replaces_route` od startu C + obsługa podmiany trasy kafla startowego w `WorldStreamer` (world-builder), potem un-skip
  `ControlPath_ForTripTykocin_HasNoUTurnAndNoDetour`.
