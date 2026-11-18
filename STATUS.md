# STATUS screens-s24 (ADR 0293)

- 2026-11-18 B (klin S8, dk65-01): przyczyna = łącznice/pasy wyłączania S8 rysowane w OSM jako osobne drogi 1,4-3,1 m od krawędzi S8; profil z NMT 0,3-1,1 m niżej -> gore "merge" odrzucone (różne wysokości) + `_tight_side` stawiał krawężnik. Poprawka: profile.py 1d (wiązanie profilu do jezdni A/S, węzły pośrednie przesunięte), gores.py reguła `express` (paski przy A/S dowolnej długości, w kawałkach 12 m, hatch P-21), markings maluje P-21 (`net.gore_zones`). Sonda dk65-01: express 77 kawałków 2408 m2 w 6 strefach, 1 kawałek odrzucony (-465,-1016).
- NASTĘPNY KROK: A (ekrany: reguła wyboru stylu `clear`/`solid` z danych) w tools/worldgen/streetscape/furniture.py, potem build_world dk65-01.
