# buildings-r14 — RAPORT KOŃCOWY (ADR 0107, zabudowa r6 + działki domów)

Gałąź `buildings-r6` (z main `ff400569`), worktree `.claude/worktrees/buildings-r6`. ADR: `docs/adr/0107-buildings-r6-plots.md`.

1. **Wynik: PARTIAL** — P1-e/f/g/h zrobione i zrenderowane; P2-h/i/k/m/n zrobione, P2-j częściowo, P2-l otwarte.
   Bez `visual-critic` i bez telefonu.
2. **Ustalenia / liczby (edytor, base → r3)**
   - Budżet Low, 57 kamer: draws 16695 → 16695 (+0,0 %), suma tris 15256 k → 15297 k (+0,3 %, maks. r10_block_2 +1,6 %),
     kamer > 400 draws 10 → 10. Region High 4028 submeshy / 14,03 → 14,05 mln tris; Low 3009 / 4,497 → 4,499 mln.
   - P1-e: spód balkonu / ściana (`r10_block_4`, ten sam prostokąt) 0,38 → 0,63 High overcast, 0,36 → 0,61 Low (42 → 71 sRGB).
   - P1-f: dwa wąsy od końców parapetu + słaby pas, 40 % okien czystych (nowy addytywny tryb shadera, v ≥ 112).
   - P1-g: schodek i szczelina znikły; 125 małych części dachu to jedna połać (pulpit / przedłużenie), 21 skrzydeł
     zostało dwuspadowych; uskoki zamknięte ścianą. r2 pokazał „żagle” w kolorze dachu na szczycie (wierzchołki na
     linii uskoku brały wyższy dach) — naprawione w r3.
   - P1-h: 97 działek (104 grupy, 270 domów), 4737 instancji z 19 prototypów; `drawsEst` ich nie liczy — górne
     oszacowanie przy domach: 14 prototypów / 17 submeshy na LOD (r1: 21 / 38).
   - Kopia `_Generated` w worktree była importem sprzed r5 — baza zaimportowana na nowo (`base/`), pierwsza próba
     odłożona w `base_stale_import/`.
3. **Zmienione pliki**: `tools/worldgen/streetscape/{plots.py (nowy), roofs.py, buildings_mesh.py, facade_kit.py,
   materials.py (blok na końcu), props.py (+2 linie), stage.py (3 wstawki)}`, `art-source/world/materials/_src/sets_buildings.py`
   (krawędź płyty w facade_far), `game/Assets/_Project/Environment/Shaders/WorldPBR.shader` (wstawka w `_RUNOFF`),
   `tests/gis/test_buildings_r6.py` (nowy, 13), `tests/gis/test_buildings_r5.py`, `docs/adr/0107-buildings-r6-plots.md`.
4. **Dowody**
   - `pytest tests/gis`: 421 passed, 1 xfailed, 1 failed (`test_road_fidelity::test_report_not_stale` — raport fidelity
     nieaktualny względem plików dróg; nie z tej gałęzi) — `r3/pytest_gis.log`.
   - EditMode 241: 234 passed, 7 failed (`WorldPbrTintTests` × 7: kopia shadera testu nie znajduje include
     `VegetationGround.hlsl`; nie sprawdzałem na main) — `r3/editmode.log`.
   - Pary przed/po (góra = base, dół = r3, 960 px): `pairs/*.jpg` (39), kamery dodatkowe `r3/extra/960/*.jpg` (15),
     kontrolne `r3/{High-overcast,Low-overcast,High-clear}/960/`.
   - Liczby: `budget.py`, `underside.py`, `plot_instances.py`, `roof_scan.py`, `r3/chunk_mats.json`, `r3/streetscape_qa.json`.
5. **Napisane / zbudowane / uruchomione / zmierzone**: kod napisany i przetestowany (pytest); świat zbudowany 4× i
   zaimportowany (base, r1, r2, r3); rendery High/Low overcast + High clear; zmierzone tylko w edytorze. Nic z telefonu.
6. **Ryzyka i braki**: działki z reguły (nie EGiB), ogrodzenia bez kolizji, podjazd z płyt-instancji (schodkuje, nie
   przecina chodnika), brak siatki plecionej, cull ogrodzeń 120 m × lodBias, pulpity w materiale dachówki, realny koszt
   instancji na A16 nieznany, P2-l (żółta linia w trawie) bez diagnozy.
7. **Następny krok**: visual-critic na `pairs/` + `r3/extra/960/`; zrzut A16; po scaleniu
   `build_all.py --only facade_far` → `build_world` → `import-region`.

## Rozliczenie recenzji 0097
| # | stan | dowód |
|---|---|---|
| P1-e | zrobione | `pairs/r10_block_4_High-overcast.jpg`, `underside.py` |
| P1-f | zrobione (subtelne) | `pairs/extra_r13_block3_close.jpg` |
| P1-g | zrobione | `pairs/extra_r13_house2_az110.jpg`, `_az200`, `_az20`, `_az290` |
| P1-h | zrobione (reguła, bez kolizji) | `pairs/extra_r13_houses_aerial.jpg`, `r3/extra/960/r14_plot*.jpg`, `pairs/r10_house_2_*.jpg` |
| P2-h | zrobione | pranie pod poręczą, bez czerwieni (`pairs/r10_block_2_*.jpg`) |
| P2-i | zrobione | wyjątki bez maty trzcinowej (`pairs/r10_block_5_*.jpg`) |
| P2-j | częściowo | próg szary; stopień bez zmian |
| P2-k | zrobione | fugi cokołu (`pairs/r10_block_5_High-overcast.jpg`) |
| P2-l | otwarte | linia nadal widoczna w `r3/extra/960/r13_block3_close.jpg` |
| P2-m | zrobione | `r13_house2_az20`, `r13_block1_az180` działają; 15 kamer na stanie końcowym |
| P2-n | zrobione, niezmierzone | dryf tonu dachówki 7 m / 0,16 |

## Konflikty
`stage.py` i `props.py` (wstawki) z `gpt-furniture-r1`; `materials.py` (blok na końcu); `WorldPBR.shader` (blok `_RUNOFF`).
`furniture.py`, `WorldPbrMaterials.cs`, `WorldSurface.shader` bez zmian. Pliki `generated/*.json`, `props_meta.json`,
`materials_spec.json` zmienione przez build — niecommitowane (lider regeneruje po scaleniu).
