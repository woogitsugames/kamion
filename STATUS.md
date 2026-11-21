# STATUS world-fix2-s24 (gałąź world-fix2-s24, ADR 0321)

- [1] Ząbki na skarpach rowów DK65: przyczyna = teren (węzły "soft" 0,04 m pod trawą rowu) przecina skarpę rowu
  między węzłami siatki 1 m (wklęsłe załamania 1:1,5, dno 0,4 m; przekątna 1,41 m wystaje do 0,24 m).
  Sonda przekroju knyszyn-w (122,787): teren 4 cm pod skarpą tylną. Poprawka: `CF.rasterise_floor` (min
  powierzchni trawy w 4 komórkach wokół węzła) + `conform(..., soft_floor=)` -> żaden węzeł nad floor - 0,04.
  Test syntetyczny tests/gis/test_ditch_floor_0321.py zielony (stara reguła: przebicie > 5 cm, nowa <= 0).
- NASTĘPNY KROK: zadanie 2 (zapora B-1 dk8-wasilkow-01), potem przebudowa kafli.
