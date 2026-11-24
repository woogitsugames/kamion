# STATUS farfield-low-s24 (CI: test_far_field Low/far_east 10 submeshes)
- krok 1: kurtyny tła = jeden prymityw `forest_edge_mixed_far_atlas` (atlas 9 slotów: conifer/mixed/broadleaf x bez/haze1/haze2), UV v w slocie; usunięte 6 PNG haze. Dotknięte kafle (submeshes>2): bialystok-industrial-c, dk65-07, dw671-tykocin-01, knyszyn-w, tykocin.
- NASTĘPNY KROK: build_world 5 kafli (log artifacts/farfield-low-s24/logs), potem pytest test_far_field + budżetowe.
