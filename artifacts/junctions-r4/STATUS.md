# STATUS — junctions-r4 (ADR 0110: węzły r4 + bariery, wg REVIEW-2026-11-11-s10-0100 i priorytetów bramki 3 pkt 4)

Gałąź `junctions-r4` (z main 7a685901). Dowody: `artifacts/junctions-r4/` (trace = ortofoto z siatką, zones0 = pola P-21,
plan_* = ortofoto | generator, renders_* = kamery Unity, scripts = narzędzia r3 + plan.sh / unity.sh / patch0*.py, logs).

- krok 0: baseline b0 (build + route + fidelity + pytest gis + swept; `logs/b0_*`): fidelity edge p50 0,36 / p95 2,304;
  pytest gis 446 passed / 1 failed (`test_report_not_stale` — źródła zmienione w trakcie buildu b0) / 1 xfailed.
  Kopia świata b0: `Data/raw/derived/bialystok-industrial-c/world_b0` (poza gitem).
- krok 1 (P0, sha 02c2b0a8): pole P-21 północne n10015785253 przerysowane z ortofoto 120 px/m (`trace/n100n.jpg`,
  `zones0/n10015785253-p21-north.jpg`): wielokąt szerszy od wsch. (wierzchołki −216,13/−226,57; −212,21/−223,63; −214,71/−227,54),
  pasy 0,20 / 0,22 m pod 8° (było 0,25/0,25 pod 42° → 1 pas), obramowanie 0,15 m (`border_w_m`), `stripe_min_m` 0,2 → 6 pasów.
  Test `test_p21_hatch`: `stripes_built` ≥ 60 % analitycznych i pokrycie pasami ≥ 15 % pola (roads_qa `stripe_cover`).
- krok 2 (w toku): `_emit_verge` — trawa za krawężnikiem bez chodnika na wysokości korony (1 m; w medianie do 3 m, nigdy za
  połowę odstępu do równoległej jezdni) ze skarpą 1:1,5 zamiast pionowego kołnierza 0,5 m (koryta median, „murki”);
  narożniki / nosy też; `h` stacji wiejskiej w narożniku mieszanym = KERB_HEIGHT (murek 0,6 m n1847317049);
  wyspa `putry-n-median-nose` (kostka, domknięcie tępego końca mediany Putry N).
- krok 3 (w toku): bariery — barieroporęcz na pomostach (słupki 1,10 m, taśma W, płaskownik, pochwyt; 0,40 m od krawędzi kapy),
  bariery pomostu hero nie są już kasowane przy podmianie wstęg, asset wiaduktu bez balustrady szczebelkowej (`rail_h_m` 0),
  balustrada generyczna pominięta przy ekranie, bariera W przy jezdni biegnącej obok wiaduktu / rampy w murach (≤ 8 m, ≥ 1 m
  wyżej), jeden ciągły bieg na krawędź (offset wygładzany 9 m), końce odgięte do gruntu (4 m), dedup gruntowy 2,5 m.
  NASTĘPNY KROK: (po imporcie b0 Unity) `bash artifacts/junctions-r4/scripts/loop.sh b1` → `bash artifacts/junctions-r4/scripts/plan.sh b1`
  → `bash artifacts/junctions-r4/scripts/unity.sh b1 low`
