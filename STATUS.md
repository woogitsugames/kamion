# STATUS world-fix2-s24 (gałąź world-fix2-s24, ADR 0321)

- [1] Ząbki na skarpach rowów DK65: przyczyna = teren (węzły "soft" 0,04 m pod trawą rowu) przecina skarpę rowu
  między węzłami siatki 1 m (wklęsłe załamania 1:1,5, dno 0,4 m; przekątna 1,41 m wystaje do 0,24 m).
  Sonda przekroju knyszyn-w (122,787): teren 4 cm pod skarpą tylną. Poprawka: `CF.rasterise_floor` (min
  powierzchni trawy w 4 komórkach wokół węzła) + `conform(..., soft_floor=)` -> żaden węzeł nad floor - 0,04.
  Test syntetyczny tests/gis/test_ditch_floor_0321.py zielony (stara reguła: przebicie > 5 cm, nowa <= 0).
- NASTĘPNY KROK: zadanie 2 (zapora B-1 dk8-wasilkow-01), potem przebudowa kafli.
- [2] Zapora B-1 dk8-wasilkow-01: zamknięcie krawędzi drogi w1220009817 (pod wiaduktem DK8) wypadało 60 m od krawędzi
  dokładnie pod pomostem; RoadY brało wysokość pomostu -> rząd stał na DK8 wzdłuż pasa. Poprawka w
  WorldEdgeBuilder.ReadExits: zamknięcie przesuwa się (2 m kroki, najpierw ku krawędzi) aż cały rząd omija pomost
  innej drogi (bridge/layer>=1). Test EditMode WorldEdgeClosureDeckTests (do uruchomienia).
- [3] Szuwary: water_banks.walk_polys (chodniki/ścieżki z osm_context.json, pół szer. + 0,75 m) wyłączone z pasa i z
  keep_out kart (stage.py). Dalej: nieregularne kępy w reeds.py.
- NASTĘPNY KROK: edycja reeds.py (losowe kąty/rozmiary/odstępy kart High, losowy zygzak Low), potem
  `uv run --project tools/worldgen python tools/worldgen/streetscape/water_banks.py --region tykocin`.
- [3b] reeds.py: kępy nieregularne (gęstość kępy 0,55-1, przesunięcie +-0,9/0,5 m, dowolny kąt pary, szer. 0,6-1,15x;
  Low: losowa amplituda zygzaka). Commit 568b45f26.
- [4] Woda: ref Commons Tykocin_Most_drogowy_03 tafla sRGB ~98/115/121 (niebieskoszara, odbicie nieba, kąt mały);
  nasz render tyk_narew_side 62/65/66 (neutralna szarość, ciało 0,12/0,12/0,115). Materiał wody globalny (strojony na
  Supraśl ADR 0213) -> plan: nadpisanie per region `region.yaml water.material` (tykocin: chłodniejsze ciało
  ~0.10/0.125/0.13, shallow zielonkawe), bez zmiany Supraśla.
- [4b] Woda: `regions.py water_material` -> build_region -> region.yaml `water.material` -> build_world
  `region_water_materials` (manifest + GLB). tykocin: color 0.095/0.118/0.128, shallow 0.12/0.135/0.115. Commit 72a48d6c1.
- W TLE: artifacts/world-fix2-s24/rebuild.ps1 (slot heavy; water_banks tykocin + build_world tykocin, knyszyn-w,
  dk65-07, dk8-wasilkow-01), status artifacts/world-fix2-s24/logs/rebuild.status.
- NASTĘPNY KROK po DONE: import-region.ps1 -Region <r> -SkipCopy? (sprawdzić), visual-qa WorldC High, porównanie z vqa-wave5.
