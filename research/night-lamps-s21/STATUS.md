# STATUS — K69 nocne latarnie (gałąź research/night-lamps-s21)

## 2026-11-15 ~10:30 UTC — WIP 1
- Narzędzia, OSM API (Overpass niedostępny), dokumenty ZDM znalezione.

## 2026-11-15 ~12:30 UTC — gotowe do PR
- manifest 84 wiersze (odcinek 22, oprawa 28, kadr 20, barwa 14); 16 ulic OSM z ≥ 10 parami; 4+1 typów opraw; 20 nocnych kadrów (a–f); CCT 4000/5700 K z warunków ZDM dla 7 ulic.
- audyt 17/84: 14 PASS, 3 FIX.
- Luki: brak nocnych kadrów LED z trasy C; h montażu UNVERIFIED; Commons 429.

Następny krok (jeśli kontynuacja): `python3 -I tools/commons_fetch960.py "$PWD/tools" <outdir> <lista.tsv>` dla pozostałych kandydatów nocnych (lista z `tools/commons_cats_html.py`), potem `python3 -I gen_frames.py && python3 -I build_manifest.py`.
