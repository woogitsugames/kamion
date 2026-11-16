# STATUS — D14 roundabout2-0274 (rondo Knyszyn, ADR 0274)

- [1] Narzędzie `tools/worldgen/qa/roundabout_ortho.py` + `docs/reports/roundabout-0274/knyszyn_ortho_probe.json`.
  WYNIK: ortofoto GUGiK w punkcie ronda = arkusz N-34-106-B-b-1-4 z 2025-05-27 (0,1 m), brak arkusza 2026; na zdjęciu jest
  jeszcze zwykłe skrzyżowanie (`roundabout_visible: false`, środek = asfalt 100 %). Promieni krawężnika ani długości wysepek
  ronda nie da się zmierzyć z ortofoto — wartości zostają ESTIMATED / WORKING_VALUE (zdjęcia 9–11 ma tylko lider).
- NASTĘPNY KROK: obrys z jawnymi promieniami krawężnika + override rozdziału DK65 + poprawki z recenzji D18:
  `uv run --project tools/worldgen python -m pytest tests/gis -k "roundabout or 0218 or 0274 or compact" -q`
