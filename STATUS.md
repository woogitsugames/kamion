# STATUS road-widen-s24 (D94, ADR 0306)

- Krok 1: `standards.GAMEPLAY_LANE_WIDEN_M = 0.25` (GAMEPLAY_WIDEN, nie pomiar), `network.gameplay_widen` po wszystkich
  overrides w `network.load`; `compact_roundabout.specs`: `lane_w_m` + delta. maczka: każda sekcja +0,25 m/pas (dev 0,0).
- NASTĘPNY KROK: narzędzie toru zestawu `tools/worldgen/qa/combo_lane_check.py` + raport przed.
- Krok 2: `qa/combo_lane_check.py` (tor zestawu: oś przednia na środku pasa + opcjonalnie najlepszy „swing” kierowcy w
  obrębie własnego pasa; klasy opposite/kerb/apron/off_hard, szwy pomijane) + `qa/combo_topview.py` (rzut z góry).
  Przed (main, widen 0, wszystkie korytarze, bez swing): opp 324, kerb 1782, apron 378, off_hard 792 (w tym artefakty szwów).
- NASTĘPNY KROK: `uv run --project tools/worldgen python tools/worldgen/qa/combo_lane_check.py --widen 0 --swing --out artifacts/road-widen-s24/before/combo_swing.json`
- Krok 3/4 (WIP): reguły w generatorze: `network.curve_widen` (pasy dwukierunkowe GP/G/Z na łukach R<200 m, offtrack
  zestawu, ≤1 m/pas), `compact_roundabout.TRUCK_ENTRY_R_MIN_M 12 / TRUCK_EXIT_R_MIN_M 15`, ring +0,25, `lane_w_m` +0,25.
  knyszyn przebudowany r1 (przed scaleniem main z ADR 0304); main scalony (a464ac123) — kafle trzeba przebudować ponownie.
- NASTĘPNY KROK: `pwsh -File artifacts/road-widen-s24/rebuild.ps1 -Regions knyszyn,bialystok-kleeberga,dk65-05,tykocin -Tag r2`
- 11:5x: testy 0274/0301 na geometrii zmierzonej (`GAMEPLAY_LANE_WIDEN_M=0` wyłącza wszystkie reguły D94), 101 zielonych.
  r2 (knyszyn, tykocin, dk65-05, kleeberga, po merge main) w toku. Zlecenie lidera: fantomowa wyspa C (11_dk8, xy -549.8/218.9,
  między jezdniami trunk w197904074 | w266084696, ortho_road_frac 0,654 ≥ 0,6) — analiza w toku (fidelity zoom).
- NASTĘPNY KROK: po r2 `combo_lane_check --swing` na 4 kaflach; import Win64 + VQA (`pwsh -File artifacts/road-widen-s24/unity.ps1 -Tag after -Import knyszyn`).
- 12:2x: knyszyn po r2: DK65→DW671 W środek pasa kerb 23→15, off 5→0; ze swingiem 0→11 (krawężnik narożnika SE przy wlocie
  z płd. — narożniki zamykane NOSE_R_M 4 m). Dodane `TRUCK_CORNER_R_M 12` (kształt jak zdjęcie drona 9). Kolejka:
  r2 (tykocin, dk65-05, kleeberga) → r3 (knyszyn, knyszyn-s, knyszyn-w) → r4 (C + fidelity). Unity: import knyszyn r2 + VQA (`unity-after`).
- NASTĘPNY KROK: po r3 `combo_lane_check --swing --tiles knyszyn,...`, import r3 knyszyn + VQA (`unity.ps1 -Tag after2 -Import knyszyn,knyszyn-s,knyszyn-w`).
- 13:2x: r2 gotowe (knyszyn r2, tykocin, dk65-05, kleeberga), VQA tykocin High OK (artifacts/road-widen-s24/vqa-tykocin).
  Przed (main, widen 0, 7 kafli) środek pasa opp 205 / kerb 1620 / off 357; ze swingiem opp 11 / kerb 557 / off 84.
  r3 (knyszyn+narożniki 12 m, knyszyn-s, knyszyn-w) czeka na slot heavy; potem r4 (C + fidelity → fantomowa wyspa).
- NASTĘPNY KROK: wynik `after/r2tiles_swing.json`; po r3 import knyszyn + VQA.
- 13:3x: kleeberga po: 0/0/0 (przed 663 kerb / 347 off — klasyfikator poprawiony: poziom jezdni pod pojazdem, wiadukt nad trasą
  nie jest jej nawierzchnią). tykocin opp 7 (przed 109), ze swingiem 0. r3 = C + knyszyn + knyszyn-s + knyszyn-w + fidelity
  (CI lidera: wyspa fantomowa 11_dk8 + lane_blind_end 57 > 55 w C — sprawdzę po przebudowie).
- NASTĘPNY KROK: po r3: `road_consistency_qa.json` C (lane_blind_end ≤ 55), fidelity islands 0; combo after na 7 kaflach.
- 13:5x: PRZED (main, poprawiony klasyfikator, 7 kafli + łączniki Knyszyna): środek pasa opp 205 / kerb 166 / off 29;
  ze swingiem opp 11 / kerb 129 / off 12 (`artifacts/road-widen-s24/before/final_swing.json`). r3 buduje C (13:52).
- 14:1x: C z r3 (stary limit L/D): lane_blind_end 49 (≤ 55 OK), ale na trasie 3 (> ROUTE_MAX 1; w main też 3 — dwa nowe po
  ADR 0301 na drogach serwisowych/strefie zamieszkania: BDOT 6,5 m → pas 3,25 przy limicie 3,50). Poprawka: L/D maks.
  std+0,25 (`standards.LANE_WIDTH_MAX`), testy 0301 zaktualizowane. r4 = C ponownie + fidelity (czeka na r3).
- NASTĘPNY KROK: po r4 sprawdzić `road_consistency_qa.json` (on_route ≤ 1, tile ≤ 55) i `fidelity_qa.json` (wyspy 0).
- 14:2x: merge main (klattow-s24, ADR 0305) dee1788db; r4 = C + knyszyn (po merge) + fidelity, czeka na r3.
- 14:5x: C z r3 (symetryczne poszerzenie): fidelity islands_absent 4 (DK8 11_dk8 ×3, Putry) — pas dzielący zjadany.
  Reguła: jezdnia jednokierunkowa rośnie w prawo (lewa krawędź jak zmierzona), także wzrost z podłogi BDOT (ADR 0301);
  DK8 przy wyspie: szczelina 2,62 → 3,87 m. Knyszyn r3: DK65→DW671 W środek pasa 0/3/0 (przed 0/23/5), DK65→DK65 W 0/0/0
  (przed 0/16/0); rzut z góry `artifacts/road-widen-s24/top/`. Usunięty autorski swing rynek→dk65-w.
  r4 = C + knyszyn (po merge klattow) + fidelity.
- NASTĘPNY KROK: po r4: fidelity C islands 0, road_consistency C (≤55, trasa ≤1); import knyszyn + VQA; testy gis.
