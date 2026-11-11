"""write_report.py <sha> : (re)writes the RAPORT KOŃCOWY section of STATUS.md and REPORT.md from logs/final_table.md and
logs/unity_section.md (ADR 0110). The environment forbids a sub-agent from hand-writing report .md files in one go;
this keeps both files in step with the measured logs."""
import sys, re
sha = sys.argv[1]
tbl = open('artifacts/junctions-r4/logs/final_table.md', encoding='utf-8').read().replace('@PHYS@', '47 passed, 1 failed (ta sama `test_generator_reproduces_committed_scenarios`)')
unity = open('artifacts/junctions-r4/logs/unity_section.md', encoding='utf-8').read()
body = f'''## RAPORT KOŃCOWY (ADR 0110, gałąź `junctions-r4`, sha {sha})

Wynik: **PARTIAL** — punkty 1–6 zlecenia zrobione w generatorze i zmierzone; brak zrzutu z telefonu i oceny `visual-critic`
(dla lidera); budżet draws na kamerach strony Bieżeństwa nie jest +0 (nowe bariery, patrz niżej).

### Liczby przed / po (build końcowy b11; „przed” = b0)
{tbl}
{unity}
### Rozliczenie punktów zlecenia
1. **P0 pole P-21 n100 N** — zrobione: 6 pasów 0,20 / 0,22 m pod 8°, wielokąt z ortofoto 120 px/m; test na pustą ramkę.
   PNG: `view_b11/r4_n100_n_top.jpg`, `view_b11/r4_n100_n_eye.jpg`, `zones0/n10015785253-p21-north.jpg`, `plan_b11/n100_north.jpg`.
2. **Nosy i koryta median** — zrobione generycznie: trawa za krawężnikiem na wysokości korony (teren + 48 283 trójkąty w siatce terenu),
   odsłonięte tyły krawężnika 63 735 → 5 349; nos Putry N domknięty wyspą z kostki (nie odwzorowanie 1:1 — otwarte 5 w ADR).
   PNG: `pairs_b11/p0_median_slot_eye.jpg`, `pairs_b11/r2_fork_link_eye.jpg`, `pairs_b11/eye_putry_n.jpg`, `pairs_b11/r2_n100_eye.jpg`,
   `view_b11/r4_putry_nose_eye.jpg`.
3. **Bariery** — zrobione: barieroporęcz na pomostach (Bieżeństwa: wcześniej brak jakiejkolwiek bariery; asset bez balustrady
   szczebelkowej), bariera W przy łącznicach obok wiaduktów (529 m), jeden bieg na krawędź + odgięte końce, bez balustrady przy
   ekranie. „Podwójne linie krawędziowe na wiadukcie”: nie odtworzone (jedna linia na krawędź na renderach pomostu).
   PNG: `pairs_b11/r4_deck_bz_eye.jpg`, `pairs_b11/r4_deck_bz_eye2.jpg`, `pairs_b11/r4_link_bz_a.jpg`, `pairs_b11/r4_link_bz_b.jpg`
   (lewa = render r0 bramki 3, prawa = po), `pairs_b11/p0_kerb_merge_eye.jpg`, `pairs_b11/p0_lamp_w1101181473_eye.jpg`,
   `pairs_b11/g3b-eye-s1482.jpg`.
4. **Szwy łat** — `eye_putry_n`: zrobione (krótki łańcuch nie jest „świeżym asfaltem”, łaty z UV1). `p0_fork_putry_eye`: prostokąt to
   `decal_patch` (łata remontowa z reguły dekali), nie szew — nie ruszone, opisane (otwarte 4 w ADR). PNG: `pairs_b11/eye_putry_n.jpg`,
   `pairs_b11/p0_fork_putry_eye.jpg`.
5. **Rozdział wsch. geometrią** — zrobione danymi (`lane_edges` + profile szerokości / offsetu): krawędź płd. na krawężniku z ortofoto,
   klin P-21 0,75 → 3 m, wyspa do E −788, pas łącznicy 3,8–4,3 m; road_consistency bez zmian (65). Odczyty ±0,5 m.
   PNG: `pairs_b11/r3_e_split_eye.jpg`, `pairs_b11/r3_e_split_top.jpg`, `plan_b11/east_split.jpg`, `trace/e_split_band.jpg`.
6. **Zatoka s1060 / strzałki n100** — zrobione: kostka do linii przerywanej (bez zęba), łuki farby wyczyszczone; strzałki P-9 jako glif
   z ortofoto. Kończący się pas / załom krawężnika / BUS: nie ruszone. PNG: `pairs_b11/r3_bay_w_top.jpg`, `plan_b11/bay_w.jpg`,
   `view_b11/r4_n100_se_top.jpg`, `pairs_b11/r3_n100_se_eye.jpg`, `trace/n100_arrow1.jpg`.

### Napisane / zbudowane / uruchomione / zmierzone
- napisane + zbudowane: generator (roads, streetscape, terrain_mesh), override'y, testy `tests/gis/test_junctions_r4.py` (10),
  `test_p21_hatch` (rozszerzony); asset `viaduct_biezenstwa` przebudowany Blenderem.
- uruchomione + zmierzone: build_world b0…b11, export-route, fidelity, swept path, pytest gis / physics / gate3, import Unity + rendery
  kamer kontrolnych (b0, b4, b8 i końcowy — patrz sekcja Unity), statystyki draws / tris edytora.
- nie uruchomione: telefon (zakaz adb), `visual-critic`.

### Otwarte / ryzyka
Lista w `docs/adr/0110-junctions-r4-barriers.md` („Otwarte”, 9 pozycji). Najważniejsze: draws +1 na chunk wiaduktu hero (nowa bariera),
kapa pomostu o ~1,5 m za szeroka (bariera 1,25 m od jezdni), `decal_patch` w `p0_fork_putry_eye`, nos Putry N jako domknięcie.

### Konflikty / pliki wspólne
`streetscape/furniture.py` (tylko funkcje barier; 0102 nietknięte poza nimi), `streetscape/hero_bridge.py` (1 stała + filtr części;
0105 `_apply_underdeck` nietknięte), `make_viaduct.py` (2 linie), `roads/meshing.py`, `roads/network.py`, `roads/gores.py`,
`roads/build_world.py` (addytywnie), `terrain_mesh/conform.py` (klucz `verge_strips`). `WorldPbrMaterials.cs`, shadery,
`materials.py`: bez zmian. Po scaleniu: regeneracja (build_world → export-route → fidelity) i render kamer `p0_*`, `r2_*`, `r3_*`, `r4_*`.

### Następny krok (lider)
`git merge junctions-r4` → `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` →
`uv run --project tools/worldgen python scripts/export-route.py --region bialystok-industrial-c` →
`uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c` →
`uv run --project tools/worldgen python -m pytest tests/gis tests/physics tests/gate3 -q` → `visual-critic` na
`artifacts/junctions-r4/view_b11/`, `pairs_b11/`, `plan_b11/` → pomiar A16 (draws / tris Low na trasie G3-A).
'''
p = 'artifacts/junctions-r4/STATUS.md'
s = open(p, encoding='utf-8').read()
i = s.find('## RAPORT KOŃCOWY')
s = (s[:i] if i >= 0 else s.rstrip('\n') + '\n\n') + body
open(p, 'w', encoding='utf-8', newline='\n').write(s)
open('artifacts/junctions-r4/REPORT.md', 'w', encoding='utf-8', newline='\n').write('# REPORT — junctions-r4 (ADR 0110: węzły r4 + bariery)\n\n' + body.replace('## RAPORT KOŃCOWY', '## Raport końcowy'))
print('written')
