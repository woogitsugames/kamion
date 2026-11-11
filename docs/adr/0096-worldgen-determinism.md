# ADR 0096: Determinizm generatora świata — wynik nie może zależeć od PYTHONHASHSEED

Status: przyjęty (geo-worldgen, determinism), 2026-11-11. Wynika z `artifacts/integration-s9/REPORT.md` („Inne ustalenia”):
ten sam kod dał w worktree integracji inny świat niż zacommitowany na main w `95f49598`. Zasada projektu nr 7:
„wszystko jako kod/dane, odtwarzalne”. Dowody: `artifacts/determinism/`.

## Kontekst (zmierzone)
- Dwa kolejne przebiegi `build_world.py --region bialystok-industrial-c` w jednym worktree, ten sam kod (`0889cae1`),
  te same wejścia: przebieg 1 = stan `c6588194` (1526 stanowisk, 908 aut, kerb_tris 84 705), przebieg 2 = stan
  `95f49598` (1500 / 900 / 84 942). Różne 5 plików `generated/*.json` i GLB kafli
  (`run1/*.sha256`, `run2/*.sha256`, `run1_vs_run2_generated.diff`).
- Nie była to więc różnica środowisk (kopia `Data/raw/derived`, `Data/photos`, Fab), tylko niedeterminizm procesu.
- Sam etap dróg (`roads.pipeline.build`) pod `PYTHONHASHSEED` 0–9 dawał trzy różne siatki: seedy 0, 1, 2, 3, 8 →
  `56ee7520…` (12 168 części), 4, 5, 6, 7 → `2aea2300…` (12 166), 9 → `0b6f08d8…` (12 168); `probe_seed*.json`.
  Różniły się paski boczne naroży skrzyżowań (`j:n…:cornerN`, do 8 naroży) i jeden pasek łańcucha
  (`c:w537184112:…:R`): ten sam pasek raz `curb_concrete`, raz `sidewalk_paving` (render i kolizja).

## Przyczyna
`tools/worldgen/roads/meshing.py`, `_emit_strip`:

```python
mat = max(set(mats), key=mats.count)
```

Materiał wiersza profilu to materiał większości stacji paska. Przy remisie (np. pasek z 2 stacji: jedna „krawężnik”,
druga „chodnik”) `max` zwraca pierwszy element w kolejności iteracji zbioru, a kolejność zbioru stringów wynika z
hasha `str`, który Python losuje dla każdego procesu. Materiał paska decyduje dalej o tym, co wycina
`cull_sides_on_carriageway` (krawężnik: pierścień 8 punktów, chodnik: 3 wierzchołki), a przez to o obrysie dróg,
węzłach konformowania terenu (505 400 / 505 404), wolnej powierzchni placów, liczbie stanowisk i aut, ściankach terenu.

Dlaczego testy tego nie złapały: `test_export_is_deterministic` czytał `world_manifest.json` PO buildzie w procesie
testu, który ten plik nadpisuje — porównywał build z samym sobą.

## Decyzja
1. `meshing.py`: `mat = max(dict.fromkeys(mats), key=mats.count)` — większość, a przy remisie materiał napotkany
   pierwszy wzdłuż paska (kolejność stacji jest geometrią, nie hashem). Jedna linia + komentarz.
2. `consistency.py`: `sorted(...)` na dwóch pętlach po zbiorach (`li_key`, `turns & set(has)`) — kolejność przypadków QA.
3. Reguła: w generatorze kolejność nigdy nie pochodzi ze zbioru; `sorted(set(...))` albo `dict.fromkeys(...)`.
4. Testy (`tests/gis/test_determinism.py`):
   - `test_road_stage_independent_of_hash_seed` — etap dróg w trzech procesach z `PYTHONHASHSEED` 0 / 4 / 9 (seedy,
     które przed poprawką dawały trzy różne wyniki) daje jeden hash (`tools/worldgen/qa/determinism.py`);
   - `test_strip_material_tie_is_first_along_the_strip` — reguła remisu;
   - `test_no_order_taken_from_a_set_in_the_generator` — skan źródeł `roads/`, `streetscape/`, `terrain_mesh/` na
     `max|min|next|list|tuple|enumerate(set(` i `for … in set(`.
   - `test_world_roads.py::test_export_is_deterministic` czyta manifest PRZED buildem (inny proces, inny seed).
     Skutek: po zmianie generatora bez regeneracji regionu test jest czerwony — najpierw `build_world.py`, potem testy.

## Dowód
- Etap dróg po poprawce, seed 0 / 4 / 9: jeden hash `81ae1c30…`, 12 166 części (`fix_seed*.json`).
- Pełny `build_world.py` z `PYTHONHASHSEED=4` i `=9` (przed poprawką różne drogi): identyczne SHA-256 wszystkich
  202 plików `Data/raw/derived/<id>/` (GLB High/Low, instancje, teren), 27 plików `Data/Regions/<id>/` i plików
  `art-source/world/{props,vegetation,landmarks}` — `fix_run_seed4/*.sha256` == `fix_run_seed9/*.sha256`.

## Zmiana wyniku (stała; `numbers_before_after.txt`)
| miara | `95f49598` | `c6588194` | po poprawce |
|---|---|---|---|
| stanowiska / auta / vany | 1500 / 900 / 114 | 1526 / 908 / 116 | 1526 / 908 / 116 |
| naczepy na placach / ciągniki solo / zestawy | 276 / 87 / 84 | 268 / 84 / 77 | 268 / 84 / 77 |
| kerb_tris | 84 942 | 84 705 | 84 731 |
| wycięte na jezdni (kerb / side / części) | 4276 / 111 / 439 | 4273 / 115 / 440 | 4275 / 113 / 440 |
| węzły obrysu dróg | 505 400 | 505 404 | 505 404 |
| ścianki terenu > 0,15 m / przypadki spójności | 4 / 65 | 4 / 65 | 4 / 65 |

Wynik po poprawce nie jest żadnym z dwóch poprzednich w siatce dróg (inny wybór przy remisach), a w otoczeniu
(stanowiska, auta, pojazdy na placach) równa się stanowi `c6588194`.

## Izolacja Fab (Megascans, ADR 0084)
Build z produktami Fab skopiowanymi z main (`art-source/world/megascans/_generated`, niecommitowane) vs fallback, ten sam
kod i seed (`fab_run_seed4/` vs `fix_run_seed4/`, `fab_isolation.txt`): `roads_qa`, `road_consistency_qa`,
`terrain_walls_qa`, `control_cameras` — 0 różnic; `streetscape_qa` — 34 liście, z czego 32 pod `furniture/megascans`
(954 podmiany odwodnienia, 320 propów) i 2 w `mesh_budget`. Stanowiska, auta, pojazdy na placach, `yard_drains` (188) i
krawężniki bez zmian: Fab nie przesuwa RNG ani indeksów reszty świata. Różnica „yard_drains 188 → 189,
drainage_replacements 955” w regeneracji main `0207a3be` jest zgodna z drugim stanem hasha (189 było też w `95f49598` bez Fab) — wniosek, nie pomiar na main.
Zacommitowane `generated/*.json` tej gałęzi pochodzą z buildu z aktywnym Fab (jak środowisko main).

## Zmiany w cudzych plikach (agenci 0094 / 0095)
- `tools/worldgen/roads/meshing.py`: 1 linia kodu + 2 linie komentarza w `_emit_strip`.
- `tools/worldgen/roads/consistency.py`: 2 linie (`sorted(...)`).
- `tests/gis/test_world_roads.py`: fixture `world` (+3 linie, klucz `manifest_before`) i `test_export_is_deterministic`.
Bez zmian w `overrides.yaml`, budynkach i pozostałych modułach.

## Otwarte
- Skan źródeł łapie tylko jawne wzorce; zbiór przypisany do zmiennej i iterowany później nie jest wykrywany statycznie —
  pilnuje tego test z trzema seedami (etap dróg) i `test_export_is_deterministic` (cały świat, inny proces).
- Etap otoczenia (streetscape) sprawdzony pełnym buildem tylko dla seedów 4 i 9.
