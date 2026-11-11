# STATUS — junctions-r3 (ADR 0100: węzły r3 wg REVIEW-2026-11-11-s10-0095)

Gałąź `junctions-r3` (z main 503c89ae). Dowody: `artifacts/junctions-r3/` (zones* = ortofoto | ortofoto + kwadraty P-21; trace = wycinki 1 m;
scripts = narzędzia r2 + zones_plan.py; logs). „Przed” = main b12 z ADR 0095 (b0 tej rundy zbudował się już z nowym kodem P-21).

- krok 1 (P0-1): `roads/p21_hatch.py` — P-21 jako analityczne czworokąty (pas = pudełko ∩ wielokąt → czworokąt między liniami krawędzi
  pasa; fragmenty < 0,35 m odrzucane), obramowanie = 1 czworokąt na krawędź (fazowane narożniki), kąt z jednej osi pola
  (`chevron_axis` + `chevron_apex`, `axis` + `stripe_rel_deg`, `stripe_w_m`/`stripe_gap_m`, `border_edges`), drapowanie komórkami 0,35 m
  z podniesieniem do najwyższej próbki (centroid + środki krawędzi; schodek > 3 cm = komórka odrzucona). Przyczyna połamań:
  długie trójkąty CDT drapowane tylko w narożnikach chowały się pod koroną jezdni (b0: do 2,6 cm pod asfaltem przy lift 6 mm).
  Override'y: DK8 front (jodełka do E −806, wierzchołek do nosa, 35°), s1440 nos (wielokąt przerysowany, oś przez środek), s1440 pasmo
  (równoległe −29° od osi, obramowanie tylko NE), n100 (gęste 0,25/0,25). Test `tests/gis/test_p21_hatch.py` (15).
  NASTĘPNY KROK: `bash artifacts/junctions-r3/scripts/loop.sh b1`
- krok 2 (sha 784b7fc5, 7468bf9c): `roads/aprons.py` (`kind: paved_apron` — analityczne przycięcie trójkątów jezdni do wielokąta,
  z, UV, UV1, COL barycentrycznie; test `tests/gis/test_aprons.py`), `kind: guardrail` (streetscape/furniture.py, bariera autorska),
  zebry / strzałki drapowane komórkami z podniesieniem (`p21_hatch.drape_lift`), UV w metrach dla pasa betonu szerszego niż 0,4 m
  (meshing.KERB_TOP_UV_MAX_W — smugi E −830…−770 N 82), materiał łaty = większość materiałów silnikowych ramion (szwy).
  Override'y: Putry N (2 × P-1 + P-7a × 2 + P-7b przez łatę przejazdu, plac `paved_apron` paving), MA-010 (P-1 pierścienia +
  wlot ramienia płd.), zatoka s 1060 (2 × `paved_apron` sett na „uszach”), rozdział jezdni wsch. E −831…−788 (paint_clear ukośnej
  linii, P-1 N 59,85, P-2b, jodełka do nosa E −805,6, wyspa, bariera, P-21 boczne, P-1e), bariera na wyspie E −782, n100 SE (4 ×
  paint_clear strzałek na wprost, 2 strzałki naprowadzające). Build b1 padł na aprons (np.cross 2D) — naprawione.
  NASTĘPNY KROK: `bash artifacts/junctions-r3/scripts/loop.sh b2`
- krok 3 (sha f3b4ece6 … cbaf26c3): krawężnik mediany — stacje wiejskie przerobione na miejską medianę brały głębokość rowu
  0,60 m jako wysokość krawężnika (DK8 E −888…−768, prawa strona w1101181473): teraz 0,13 m. `kerb_rise.py` (b2): wzniesienia
  krawężnika nad jezdnią ≥ 0,25 m: 1 (j:n1847317049:corner0, 0,6 m — otwarte); wszystkie pionowe ściany 0,25–0,40 m: 52 → 0,
  0,40–0,70 m: 79 630 → 79 009 (reszta = kołnierze pod terenem). b2 fast: plany `plan_b2/` obejrzane (Putry N linie + plac,
  rozdział wsch. jodełka/wyspa/linie, n100 SE strzałki), poprawki: zatoka (współrzędne z planu 8,75 px/m), ukośna linia, ostrze pola.
  W toku: `loop.sh b3` (pełny: pytest gis + swept), potem import Unity + rendery.
  NASTĘPNY KROK: `cat artifacts/junctions-r3/logs/b3_loop.out`; `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c`
