# STATUS farfield-low-s24 (CI: test_far_field Low/far_east 10 submeshes)
- krok 1: kurtyny tła = jeden prymityw `forest_edge_mixed_far_atlas` (atlas 9 slotów: conifer/mixed/broadleaf x bez/haze1/haze2), UV v w slocie; usunięte 6 PNG haze. Dotknięte kafle (submeshes>2): bialystok-industrial-c, dk65-07, dw671-tykocin-01, knyszyn-w, tykocin.
- NASTĘPNY KROK: build_world 5 kafli (log artifacts/farfield-low-s24/logs), potem pytest test_far_field + budżetowe.
- krok 2: build_world 5 kafli OK (tykocin, dw671-tykocin-01, dk65-07, knyszyn-w, bialystok-industrial-c): wszystkie sektory High/Low = 2 podsiatki. pytest far_field*/forest/v34/budżet/world_roads/fidelity: 213 passed, 1 xfailed.
- Kafle do main (derived = kopia): te same 5. NASTĘPNY KROK (lider): scalić farfield-low-s24, robocopy derived 5 kafli, import Win64.
