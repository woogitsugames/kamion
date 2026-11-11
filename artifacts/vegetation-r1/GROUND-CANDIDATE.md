# Proponowana zmiana materiału (przed wdrożeniem)

W VegetationGround.hlsl dodać wspólną funkcję mieszającą obecne albedo z przygaszoną suchą trawą (liniowo około 0,145/0,125/0,055, WORKING_VALUE), zależnie od B i istniejącego detalu. Zostawić stary DryTint oraz dodać funkcję za istniejącymi flagami _GroundMasks/_GROUNDMASKS. _GroundTint = 0 ma zachować dokładnie stary wynik. Bez dodatkowych sampli, przebiegów i obiektów. Las i odkryte podłoże nadpisują efekt jak dotąd.

W syntheticznym podglądzie 200 m maska pobocza uzyskuje odchylenie 0,257 zamiast 0,032, a trawnika OSM 0,123 zamiast 0,032. To pomiar wyłącznie maski, nie obrazu. Większa amplituda nie jest dowodem realizmu — wymaga sprawdzenia renderów i porównania ze zdjęciami. Plamy są nadal ciągłe i mają kilka metrów; nie dodają drobnego szumu.

Potwierdzono 15 gotowych zasobów Megascans w lokalnym cache (megascans-input-proof.json). Wygenerowanego fallbacku trzeba jeszcze sprawdzić po zakończeniu build_world.
