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
