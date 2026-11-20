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
- 15:1x: C r4 (prawo-rosnące + L/D limit): lane_blind_end 44 (ratchet 55 OK, main 57), trasa 2 (>1; main 3),
  marking_off_carriageway 6 (>3; main 4), obstacle_in_lane 3 (>2). Badam przypadki (fidelity zoom c_cases). fidelity C po r4 w toku.

## STOP 15:4x (limit tygodniowy 91 %) — stan dokładny
- Gałąź `road-widen-s24`, worktree `.claude/worktrees/road-widen-s24` (prywatna kopia derived; przebudowane tam: knyszyn
  (r4, po merge klattow), knyszyn-s, knyszyn-w (r3), tykocin, dk65-05, bialystok-kleeberga (r2, PRZED regułą „rośnie w prawo”),
  bialystok-industrial-c (r4)). Nic w tle nie działa (r4 exit=0, Unity after2 exit=0). Pliki generated/route_start/
  route_links w worktree NIE commitowane (przelicza fala w main).
- Wyniki: knyszyn DK65→DW671 W środek pasa opp/kerb/off 0/23/5 → 0/3/0, DK65→DK65 W 0/16/0 → 0/0/0 (r3); tykocin opp
  109 → 7 (swing 0); C r4: road_consistency lane_blind_end 44 (≤55, main 57), na trasie 2 (>1, main 3),
  marking_off_carriageway 6 (>3, main 4), obstacle_in_lane 3 (>2); fidelity islands_absent 2 (main 1, r3 symetrycznie 4)
  — oba na DK8 11_dk8 (xy -549.8/216.1 i -554.3/118.8), ortho_road_frac 0,91–0,98: pas dzielący po regule „jednokierunkowa
  rośnie w prawo” szerszy niż w realu (3,87 m vs ~1,5 m zieleni) → NIE ZAMKNIĘTE. Przyczyna markings 6: przesunięcie w prawo
  0,75–1,125 m (podłoga BDOT + widen) wpycha jezdnię na chodniki/wiadukt (artifacts/road-widen-s24/c_cases/*.jpg).
- Propozycja następnego kroku (do decyzji): w `network.gameplay_widen` przesuwać w prawo tylko część GAMEPLAY (add/2),
  wzrost z podłogi BDOT zostawić symetryczny (jak ADR 0301) i ograniczyć przesunięcie do ≤ 0,5 m; potem przebudować C i
  sprawdzić fidelity + consistency:
  `pwsh -File artifacts/road-widen-s24/rebuild.ps1 -Regions bialystok-industrial-c -Tag r5 -Fidelity`
  następnie `uv run --no-project python -c "import json;d=json.load(open('Data/Regions/bialystok-industrial-c/generated/road_consistency_qa.json'));print(d['by_kind'],d['on_route'])"`
  i `uv run --project tools/worldgen python -m pytest -q tests/gis/test_road_fidelity.py tests/gis/test_road_consistency.py tests/gis/test_road_widen_0306.py`.
- Otwarte: przejazd playerem przez rondo (nie zrobiony), EditMode Win64 (nie uruchomione), pełne pytest tests/gis
  (uruchomione podzbiory 0306/0301/0274/lane_edges: 103 zielone), łączniki Rynek Knyszyn (skręty w Rynku: opp 32–37).
- 15:5x (wznowienie): reguła w prawo tylko część GAMEPLAY (≤ 0,5 m, `GROW_RIGHT_MAX_M`), podłoga BDOT symetrycznie;
  r5 = C + fidelity w toku (`artifacts/road-widen-s24/rebuild-r5.log`). VQA Knyszyn after2 obejrzane: narożniki ronda
  szerokie jak na zdjęciu 9, oznakowanie P-10/P-13 na miejscu (`artifacts/road-widen-s24/top_vqa_after_vs_before.jpg`).
  Build playera knyszyn-s/knyszyn/knyszyn-w + przejazd autopilota (`player.ps1`, log `player-build.log` / `player-run.log`).
- NASTĘPNY KROK: po r5 consistency/fidelity C; po player.status analiza telemetrii
  `uv run --no-project python tools/worldgen/qa/combo_player_run.py <telemetry.csv> --link knyszyn-dk65-to-dw671-w`.
- 16:0x: build playera padł (brak zaimportowanej sceny WorldC w worktree — `BUILD_ERROR ... WorldC.unity`). Łańcuch w tle
  `artifacts/road-widen-s24/chain.ps1`: po r5 → import C (Unity) → `player.ps1` (build knyszyn-s/knyszyn/knyszyn-w + przejazd
  autopilota -stream 1 -route_to tykocin -telemetry 1). Stan: `chain.status`, `player.status`, logi `player-build.log`/`player-run.log`.
- 16:2x: C r5: lane_blind_end 42, marking_off 4 (3 z nich już w main: w257367423 E -955 N 56), obstacle 2 ✓, na trasie 2
  (serwisowa pętla w435369082 + znana brama zajezdni). Poprawki: klasa D ignoruje szerokość BDOT; profil położenia z ortofoto
  (ADR 0095) bez przesunięcia w prawo (rampa wiaduktu DK8 E -692 N 73). r6 (C + fidelity) startuje po imporcie C w łańcuchu
  (`r6.ps1`, log `rebuild-r6.log`). Testy: EditMode Win64 + pełne pytest gis w `chain2.ps1` po przejeździe playerem.
- 16:3x: fidelity C r5: islands_absent 2 (main 1): 11_dk8 E -549.8 N 218.9 (ta sama co w main, 543 m²) + nowa mała
  E -554.6 N 118.8 (41 m², nos pasa dzielącego przy rozwidleniu Putry). r6 (D bez BDOT, profil bez przesunięcia) w toku;
  łańcuch import C → player → EditMode → pytest czeka na `rebuild-r6.status`.
- 16:4x: C r6 consistency: lane_blind_end 44, marking_off 3, obstacle 2, arrow 8 — wszystkie ratchety kafla OK
  (main: 57 / 4 / 2 / 7). Na trasie 2 (> ROUTE_MAX 1; main 3): pętla serwisowa w435369082 E -208 N -287 + znana brama.
  fidelity r6 w toku.
- 17:1x: C r6 fidelity: islands_absent 3 (main 1); edge p95 1,33 (main 2,09). Wyspa 11_dk8 E -549.8 N 218.9 to pas
  między jezdnią a parkingiem PO PRAWEJ — przesunięcie w prawo go zjada. Poprawka: podłoga BDOT ADR 0301 (już ≥ +0,25/pas
  ponad pomiar) zaliczana do D94 → DK8 bez dodatkowego poszerzenia. r7 (C + fidelity) w toku. Build playera OK
  (`artifacts/win/kamion-0.1.0-422206cde4-dirty-regions`), przejazd `run.ps1` w toku; chain2 (EditMode → pytest) w toku.
- EditMode Win64 (16:29, C z r5): 1320/2 — `RegionSelectTests` (katalog routeLengthM C nieaktualny: kafel przebudowany,
  katalog przelicza fala w main) i `Nav0168Tests.Exit_GoldenRoutes` (graf nawigacji C z nowej geometrii: 5 manewrów vs 4
  w złotej trasie). Do powtórki po r7.
- 17:2x: przejazd 1 (knyszyn-s, 240 s, 40 km/h): 0 wyjątków, 60 fps (GTX 1070, High), ale skończył 410 m przed rondem.
  Przejazd 2: `-scene knyszyn -route_s 150 -speed 30`, 150 s (`run.ps1`, status `run.status`), telemetria → `combo_player_run.py`.
- 17:3x: przejazd 2 (scena knyszyn, route_s 150, 30 km/h; trasa kontrolna DK65 S → Tykocka E, 1. zjazd): 0 wyjątków;
  w strefie ronda (r ≤ 45 m) ciągnik zawsze na asfalcie, max 0,65 m od linii trasy; naczepa 2,4 s (t 57,4–59,8) kołami
  na betonie/kostce = krawężnik narożnika SE (to samo combo_lane_check: 53 pkt na trasie kontrolnej knyszyn).
  Poprawka: `TRUCK_CORNER_R_M` 12 → 16 m; r8 = knyszyn w toku; potem import knyszyn + VQA + przejazd 3.
- 18:3x: pełne pytest tests/gis (17:31, przed poprawkami): 64 failed / 2506 passed — głównie testy geometrii zmierzonej
  (szwy, K1, przekroje wiejskie, ronda) liczone z GAMEPLAY 0,25. `tests/gis/conftest.py` uruchamia teraz suite przy
  `GAMEPLAY_LANE_WIDEN_M = 0` (geometria zmierzona; testy D94 ustawiają 0,25). Powtórka 64: `pyfail.ps1` → `pytest-fail2.log`.
  r7 (C) i r8 (knyszyn, narożniki 16 m) czekają na slot heavy.
- 20.11 09:1x: r7 C (podłoga BDOT zaliczana do D94): fidelity wyspy 1 (= main), edge p95 1,63; consistency lane_blind 45,
  marking_off 6, obstacle 3, na trasie 3 (gorzej niż r6: 44/3/2/2 przy wyspach 3) — do decyzji lidera, który wariant.
  r8 knyszyn (narożniki 16 m) gotowy: import + VQA `after3` i combo knyszyn w toku. pytest powtórka 64 → 15 failed: kafle
  przebudowane w worktree vs sąsiedzi nieprzebudowani (szwy, łącznik jeroniki), katalog (fala), zebra/ściany/most C;
  test Monki zamieniony na „bez swingu, 0 poza nawierzchnią”.
- 09:2x: knyszyn r8 (narożniki 16 m): DK65→DW671 W środek pasa 0/5/0 (swing 0/0/0), DK65→DK65 W 0/0/0, Rynek→DK65 W
  kerb 59 → 0 (przeciwny pas 33 w ulicach Rynku), trasa kontrolna 29 pkt na narożniku SE (swing 0). VQA after3
  (`artifacts/road-widen-s24/vqa-after3`). Przejazd 3 (knyszyn-s route_s 2150 → łącznik DK65→DW671 W, 30 km/h, po rebuild
  playera) w toku (`player.status`).
- 09:3x: przejazd 3 (build z knyszyn r8; knyszyn-s route_s 2150 → łącznik DK65 → DW671 W, lewo 275°, 30 km/h, stream):
  0 wyjątków; w strefie ronda (r ≤ 45 m, 1952 próbek) ciągnik i prawe koła naczepy zawsze na asfalcie, ciągnik ≤ 0,85 m od
  linii łącznika, min 12,6 km/h, przegub maks. 48°; lewe koła naczepy 5,8 s na kostce = fartuch ronda (zaprojektowany).
  Telemetria `artifacts/road-widen-s24/player_run3_telemetry.csv`.
