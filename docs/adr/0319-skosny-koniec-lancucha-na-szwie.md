# ADR 0319 — Skośny koniec łańcucha drogi na szwie kafla

Status: Proposed (seam-knw-s24, 2026-11-21). Powiązane: 0224 (seams.py), 0233 (seam_section), 0275 (seam_taper),
0306 (D94), 0274 / D95 (rondo Knyszyn).

## Kontekst
Łańcuch drogi przecięty krawędzią kafla (węzeł grafu `boundary`) kończył się w `meshing.build_ribbon` przekrojem
prostopadłym do osi. Droga przecinająca szew skośnie (Tykocka/DW671 w1478765548 41°, DK65 w232511646 ~66° na szwie
knyszyn | knyszyn-w, x = 760587) zostawiała w każdym kaflu trójkąt gołego terenu po jednej stronie osi, a po drugiej
wypychała asfalt na teren sąsiada, który go przykrywał: trójkąty trawy, schodkowy próg i urwany chodnik
(vqa-wave5 rings-w-arm-top). Pomiar GLB przed: przy x = szew ∓ 0,3 m knyszyn-w miał asfalt N 611956,5–611964,85,
knyszyn 611964,2–611972,5 — dwie połówki jezdni zamiast całości. seams.py tego nie widział (porównuje przekrój
na osi, nie kształt końca siatki).

## Decyzja
1. `network._seam_dir`: węzeł `boundary` leżący na krawędzi bbox grafu (±0,05 m, nie narożnik) dostaje `seam_u`
   — wektor wzdłuż tej krawędzi.
2. `meshing.seam_shear`: kierunki przekroju rzędu stacji N' = N + f(s)·k·T, k = (u·T)/(u·N); na końcu f = 1, więc
   rząd leży na linii szwu, a N'·N = 1 — szerokości mierzone prostopadle do osi bez zmian; oba kafle kładą każde
   przesunięcie boczne w tym samym punkcie wspólnej krawędzi. Rampa liniowa długości
   max(1,15 × (hw + zasięg pobocza) × |k|, 4 m), ograniczona długością łańcucha (połową, gdy oba końce na szwie),
   żeby rząd nie wyprzedził sąsiedniego (brak zawiniętych trójkątów). |k| > 2,5 (cięcie bardziej skośne niż 68°)
   — bez zmian. Wysokość rzędu = wysokość stacji (crossfall_z), czyli ta sama, którą sąsiad daje na szwie.
   Te same N trafiają do pasów bocznych (krawężnik, chodnik, pobocze, rów) i do siatki kolizji.
3. Wartości 1,15 / 4 m / 2,5 to WORKING_VALUE geometryczne, nie pomiar.

## Konsekwencje
Dotyczy wszystkich kafli przy następnej przebudowie (każdy skośny szew). Znaczniki (markings) nadal kończą się
prostopadle przy punkcie osi; leżą na asfalcie, bo asfalt obu kafli pokrywa teraz pełny pas szwu.
Overrides (authored, przeżywają reimport): knyszyn-w w1478765548 2 pasy / 11,25 m / asphalt_new (jak D95 w knyszyn);
knyszyn center_offset 0,25 dla 300808749 i 98072226 (to samo przesunięcie D94 co w knyszyn-w).
