# WORLDGEN-PERF 2026-11-16 — gdzie idą minuty `build_world` (D22, s23)

Gałąź `worldgen-perf-s23` (baza `origin/main` `e2578ab78`; drugi pomiar na `9d8f1f589`). Tylko analiza: **zero zmian
w generatorze**, bez ADR. Nowe: profiler etapów `tools/worldgen/qa/profile_build_world.py` + test
`tools/worldgen/tests/test_profile_build_world.py`.

## 1. Wynik: PARTIAL

Pomiar funkcji (cProfile) zrobiony w chmurze na prawdziwym kaflu C z **syntetycznym NMT** (bez `Data/raw`, bez LFS —
landmarki STALE, far field pominięty). Brak pomiaru na maszynie lidera z prawdziwym NMT — plan w §7.

## 2. Liczby referencyjne (cytaty)

| kafel | czas `build_world` | źródło |
|---|---|---|
| C | 8,7 min | `HANDOVER.md:50` |
| C | 9 min 47 s (Dojlidy 7 min 21 s) | `docs/reports/INTEGRATION-2026-11-15-c-regen2-s23.md:180` |
| C | 605 s | `docs/adr/0173-world-determinism-between-builds.md` (Measurements 1) |
| C | 7,8 min | `HANDOVER.md:425` |
| Dojlidy | 441 s | `HANDOVER.md:452` |
| dk65-0x | ok. 6 min/kafel | `HANDOVER.md:252` |
| dw671-tykocin-01 | 174 s | `docs/reports/VERIFY-2026-11-15-qa-tools-0219.md:12` |
| **bialystok-kleeberga** (ADR 0206, 815 działek) | **2 900 s (48 min)**, w tym `plots planned` 1 822 s | log lidera `artifacts/bialystok-dk65-t2-0206/build_world.log` (15.11) |

Logi lidera z czasami etapów (`[world t s]`, różnice między liniami): `artifacts/putry-andersa/logs/build-world-5.log`
(C, 583 s), `artifacts/vegetation-r3/final-world.log` (C, 456 s), log kleeberga j.w.

| etap (linia logu) | C 583 s (putry-andersa) | C 456 s (vegetation-r3) | kleeberga 2 900 s |
|---|---|---|---|
| pass 1 (`pipeline.build` nr 1 + raster pomostów) | 64 | 71 | 74 |
| plan działek (`plots planned`) | **154** | **110** | **1 822** |
| pass 2 (`pipeline.build` nr 2, do `kerb drops applied`) | 73 | 61 | 70 |
| `paved` (od `buildings`) | 89 | 85 | 272 |
| `furniture` | 23 | 16 | 73 |
| `garden fronts` | — | — | 451 |
| `exported` (biblioteka propsów + GLB) | 48 | 29 | 41 |

## 3. Pomiar w chmurze (zmierzone)

Komenda (jednorazowy worktree, potem usunięty):
`uv run --project tools/worldgen python tools/worldgen/qa/profile_build_world.py --region bialystok-industrial-c
--nmt wave --skip-far-field --out-root <scratch>/world --prof <scratch>/bw.prof --json <scratch>/stages.json
--i-know-generated-is-dirtied`. Wynik: **1 148,8 s z cProfile** (4 vCPU, równolegle drugi bieg); bieg bez cProfile
(`--nmt flat`) doszedł do `road chunks` w 848 s, potem padł na braku miejsca na dysku przy zapisie GLB. Chmura jest
ok. 1,6× wolniejsza od maszyny lidera (848 s vs 519 s do `road chunks` w logu putry-andersa) — dlatego niżej podaję
**udział %**; czas u lidera = udział × 522–587 s (ESTIMATED).

| etap (zagnieżdżone liczą się też w rodzicu) | wywołań | s (chmura) | udział |
|---|---|---|---|
| `streetscape.stage.run` | 1 | 384,2 | 33,4 % |
| `roads.pipeline.build` (pass 1 + pass 2) | 2 | 327,8 | 28,5 % |
| `streetscape.stage.plan_plots` | 1 | 232,7 | 20,3 % |
| `streetscape.paved.road_footprint_polygon` | 5 | 191,1 | 16,6 % |
| `roads.meshing.build_patch` | 820 | 151,8 | 13,2 % |
| `streetscape.plots.region_plan` | 1 | 147,9 | 12,9 % |
| `streetscape.paved.build_meshes` | 2 | 103,4 | 9,0 % |
| `streetscape.export.export` (biblioteka propsów/znaków/tekstur) | 1 | 91,0 | 7,9 % |
| `streetscape.plots.plan` | 1 | 87,1 | 7,6 % |
| `roads.network.assign_sides` | 4 | 86,5 | 7,5 % |
| `streetscape.plots.layout` | 387 | 54,7 | 4,8 % |
| `streetscape.buildings_mesh.build` | 1 | 38,5 | 3,4 % |
| pętla GLB (bez `export.export`; `exported` − 91 s) | 64×2 | ok. 19 | 1,7 % |

cProfile, najdroższe funkcje (tottime): `shapely.union_all` 4 107 wywołań 231 s; `buffer` 511 596 wywołań 103 s;
GEOS `difference` 12 897 wywołań 64 s; `roads/geom.py:90 project` 1 876 253 wywołań 92 s cum (906 220 z
`meshing.py:814 on_arm`); `np.nan_to_num` 713 919 wywołań 59 s cum (pełna siatka 2049² w `paved.py:284`, `:371`,
plus 701 378 razy w `network.py:238 crossfall_z`); kodowanie PNG 28 s; `export.textures()` **3 razy** (57 s).

## 4. Pięć największych kosztów i propozycje

Koszty rozłączne, ok. 76 % czasu kafla C. „Zysk” = sekundy chmury (udział); u lidera ×0,6 (ESTIMATED).

**K1. Dwa pełne `pipeline.build` — 328 s (28,5 %).** `build_world.py:832` i `:865`. Pass 1 potrzebuje tylko
pomostów, obrysu dróg do działek i przejazdów kolejowych; liczy też siatki kolizji (`coarse=True`,
`pipeline.py:147`, `:151`), a sieć/boki/skrzyżowania/gores są niezależne od NMT. Wewnątrz: `build_patch` 152 s
(`meshing.py:849 blend` → `:814 on_arm` → `geom.py:90 project`, skalarne pętle Pythona), `assign_sides` 86 s
(`network.py:1068/1107/1114` `STRtree.query(q.buffer(r))` per stacja), `crossfall_z` (`network.py:238`
`nan_to_num(self.e)` przy każdym wywołaniu).
- (a) pass 1 bez siatek `coarse` (flaga w `pipeline.build`): ok. 40 s (3,5 %); ryzyko niskie (pass 1 nie czyta
  warstwy `collision`), bajty wyjścia identyczne — do potwierdzenia `compare_world.py`.
- (b) `query(shapely.box(x-r, y-r, x+r, y+r))` zamiast `query(Point.buffer(r))` (to samo bbox → ten sam zbiór
  kandydatów; mikrotest: 19,6 → 7,6 µs/zapytanie, wynik identyczny dla 20 000 zapytań): 20–40 s (ESTIMATED);
  ryzyko zerowe.
- (c) `crossfall_z`: `nan_to_num(self.e)` / `isnan` raz na łańcuch (cache): ok. 13 s; ryzyko zerowe.
- (d) wektoryzacja `on_arm`/`arm_plane`/`blend` (`project` dla tablicy punktów): 60–90 s (ESTIMATED); ryzyko
  średnie (kolejność działań float → możliwa jednorazowa zmiana bajtów, nie determinizm).
- (e) ponowne użycie sieci z pass 1 (deepcopy po `assign_sides(trims=True)`/`build_junctions`/`GO.plan`): ok. 65 s
  (ESTIMATED); ryzyko średnie (ukryta mutacja `net`).
- Pliki zablokowane (`pipeline`, `network`, `meshing`, `build_world`) → zadanie dla lidera.

**K2. `road_footprint_polygon` ×5 — 191 s (16,6 %), ok. 38 s na wywołanie.** `paved.py:184-196`
(`union_all` setek tysięcy trójkątów z `grid_size=0.01`). Wywołania: `stage.py:63` i `:65` (pass 1, działki),
`stage.py:91`, `:143` (CY.paint) i `:286` — dwa ostatnie dają **identyczny** wynik (ta sama lista `road_parts`).
- (a) memoizacja po skrócie SHA-256 trójkątów (lub po prostu `carriage` raz w `stage.run`): −1 wywołanie pewne
  (38 s, 3,3 %), −3 jeśli obrys xy z pass 1 = pass 2 (UNVERIFIED; kerb drops zmieniają wysokość, nie rzut?) → do
  114 s (10 %); ryzyko zerowe (ten sam wynik).
- (b) union najpierw per część (wstęga/łata), potem `union_all` części: 2–4× szybciej (ESTIMATED); ryzyko średnie
  (inna kolejność wierzchołków → drobne zmiany działek/płotów).

**K3. Plan działek bez obrysu — ok. 157 s (13,7 %), na kleeberga ok. 1 800 s (63 % kafla).** `plots.py:256-330`
(`plan`): dla każdej grupy domów `unary_union(static + others + laid)` (`:304`), gdzie `static` to bufor obrysu
**całego kafla** + wszystkie przeszkody, `laid` rośnie (O(n²)), `others` = `distance` do wszystkich domów (O(n²));
potem do 60 iteracji × 5 przecięć z tym wielokątem. `layout` (`:509`, `:562`): `line.difference(cut)` /
`cut.distance(...)` z `cut` = suma dróg + budynków całego kafla, 387 wywołań (plus `relayout` w `plan_access`
`:691`, 189 razy).
- Propozycja: `static_u = union_all(static)` raz; per grupa `clip_by_rect(static_u, okno)` + `laid`/`others` z
  STRtree w oknie (okno = `rect(mg)` startowe + 1 m; `rect` tylko maleje); w `layout` przyciąć `cut` do bbox działki
  + 1 m. Zysk C: 100–130 s (9–11 %); kleeberga: 1 822 s → 100–200 s (ESTIMATED, usunięcie członu n²). Ryzyko:
  różnice float w wielokątach działek → jednorazowa zmiana bajtów (determinizm zachowany); weryfikacja
  `compare_world.py` + kamery z działkami.

**K4. `paved.build_meshes` ×2 — 103 s (9 %).** `paved.py:284`: `np.nan_to_num(zgrid, nan=np.nanmean(...))` na pełnej
siatce 2049² **dla każdego obszaru** (748 razy), `paved.py:371` `nan_to_num` dla każdego pierścienia (818 razy);
mikrotest: 85 ms i 30 ms na wywołanie. `paved.py:387`: `shapely.distance(punkty, roads_poly)` do obrysu całego kafla
(22 s).
- (a) wynieść oba `nan_to_num`/`nanmean` przed pętlę (raz na wywołanie `build_meshes`): 45–60 s (4–5 %); bajty
  identyczne, ryzyko zerowe.
- (b) przyciąć `roads_poly` do bbox pierścienia + 0,6 m przed `distance` (`< 0.6` daje ten sam wynik): ok. 20 s;
  ryzyko bardzo niskie.
- Na kleeberga `paved` = 272 s i `garden fronts` 451 s — ten sam wzorzec do sprawdzenia w `plantings.py:814`
  (UNVERIFIED, brak profilu tego kafla).

**K5. Biblioteka propsów `export.export` — 91 s (7,9 %).** `build_world.py:1009` → `export.py:162`. `textures()`
(`export.py:135`) wołane **3 razy** (2× przez `export.glb_materials`, `export.py:151`, raz z `export.py:203`), każde
renderuje i koduje wszystkie PNG od nowa (57 s); kodowanie PNG 28 s; `props.build_all`/`life_props.build_all` 34 s.
Wynik nie zależy od świata kafla (tylko `codes`/`boards` i kod).
- (a) `functools.cache` na `textures()` w procesie: ok. 38 s (3,3 %); ryzyko zerowe.
- (b) cache dyskowy całej biblioteki z kluczem = SHA-256(kody, tablice, pliki `streetscape/*.py`): ok. 90 s przy
  przebudowie bez zmian w propsach; ryzyko: nieaktualny cache, jeśli klucz pominie wejście.

Razem (a) z K1–K5 bez zmian bajtów: ok. 190–270 s chmury ≈ **2–2,7 min z 9 min** u lidera (ESTIMATED). Z
propozycjami zmieniającymi bajty (K1d, K1e, K2b, K3): kolejne 3–4 min na C, rzędu 25–40 min na kleeberga.

## 5. Zrównoleglenie (bez łamania ADR 0173)

- Losowość jest lokalna i ziarnista (`np.random.default_rng(_seed(...))` w `vegetation.py:350/433/438`,
  `construction_site.py:110/189`; brak globalnego `np.random.seed`) — zadania równoległe nie dzielą strumienia.
- **Między kaflami**: osobne procesy `build_world --region` (największy zysk, ograniczenie: RAM i sloty lidera).
- **W kaflu**, niezależne od reszty: `far_field.build_far_field(region_id)` (`build_world.py:1188`, 4–27 s) i
  `export.textures()` mogą ruszyć w osobnym procesie na starcie; pętla 64 kawałków GLB (`build_world.py:1020-1087`,
  ok. 19 s chmury) — `ProcessPoolExecutor` z wynikami składanymi w `sorted(terrain)`, ale na Windows (spawn)
  pikle siatek zjedzą większość zysku (ESTIMATED < 10 s). Pass 1 → plan działek → pass 2 → `stage.run` to łańcuch
  zależności — nie zrównoleglać.
- Warunek przyjęcia każdej zmiany: dwa buildy przed/po + `uv run --project tools/worldgen python
  tools/worldgen/qa/compare_world.py <przed> <po>` = identyczne (dla K1a-c, K2a, K4, K5a) albo jawna jednorazowa
  zmiana z oględzinami; `test_determinism_0173.py` + `tests/gis/test_determinism.py` (PYTHONHASHSEED).

## 6. Zmienione pliki

- `tools/worldgen/qa/profile_build_world.py` (nowy): timery ok. 80 funkcji generatora (podmiana atrybutów modułów,
  przywracana na końcu), `--prof` cProfile, `--json` tabela, `--nmt raw|flat|wave`, `--skip-far-field`, blokada
  bez `--i-know-generated-is-dirtied` (build zapisuje `Data/Regions/<id>/generated/*` i
  `art-source/world/landmarks/*` — zmierzone `git status` po biegu).
- `tools/worldgen/tests/test_profile_build_world.py` (nowy, 2 testy).
- ten raport, `STATUS.md`.

## 7. Plan pomiaru dla lidera (prawdziwy kafel)

```
# A: czysty cProfile (zapisuje generated/ jak zwykła regeneracja; na main po regeneracji albo w jednorazowym worktree)
uv run --project tools/worldgen python -m cProfile -o artifacts/perf/bw_c.prof tools/worldgen/roads/build_world.py --region bialystok-industrial-c --no-route-graph
# B: tabela etapów + cProfile, GLB do artifacts (nie do Data/raw/derived)
uv run --project tools/worldgen python tools/worldgen/qa/profile_build_world.py --region bialystok-industrial-c --out-root artifacts/perf/c/world --prof artifacts/perf/c/bw_c.prof --json artifacts/perf/c/stages.json --i-know-generated-is-dirtied
git checkout -- Data/Regions/bialystok-industrial-c/generated art-source/world/landmarks
# to samo dla kafla z wieloma działkami (najgorszy znany przypadek)
uv run --project tools/worldgen python tools/worldgen/qa/profile_build_world.py --region bialystok-kleeberga --out-root artifacts/perf/kl/world --prof artifacts/perf/kl/bw.prof --json artifacts/perf/kl/stages.json --i-know-generated-is-dirtied
```
Czytanie: `uv run --project tools/worldgen python -c "import pstats; pstats.Stats('artifacts/perf/c/bw_c.prof').strip_dirs().sort_stats('cumulative').print_stats(40)"`
(potem `sort_stats('tottime')`; wywołujących: `.print_callers('road_footprint_polygon')`), graficznie
`uvx snakeviz artifacts/perf/c/bw_c.prof`. cProfile dokłada ok. 30–40 % — porównuj udziały, nie sekundy; czas bez
narzutu = linie `[world t s]` zwykłego logu. Oczekiwanie: te same pozycje co w §3; jeśli prawdziwy NMT zmienia
kolejność (conform/`tidy`, ściany terenu), to K1/K4 rosną.

## 8. Dowody, rozróżnienie, ryzyka

- **Zmierzone:** biegi w chmurze (`flat`: etapy do 848 s; `wave`: 1 148,8 s + `bw.prof`, pliki w scratchpad, nie w
  gicie); mikrotesty `nan_to_num` i `query(box)`. **Z logów lidera:** tabela §2. **ESTIMATED:** wszystkie zyski
  i czasy u lidera. **Nie zmierzone:** prawdziwy NMT, far field, landmarki hero (STALE w chmurze), kleeberga.
- Testy: `uv run --project tools/worldgen python -m pytest tools/worldgen/tests/test_profile_build_world.py -q` →
  2 passed. `test_determinism_0173.py`: 4 passed, **1 failed** `test_vegetation_local_edit_stays_local`
  (1160 > 200 and 1437 < 1160) — błąd istniejący na main, plik niezmieniony w tej gałęzi; do zgłoszenia.
- Ryzyko: chmura bez LFS i `Data/raw` — udziały mogą się przesunąć (§7). Dysk chmury był pełny (98–100 %),
  stąd przerwany bieg `flat`.

## 9. Następny krok

Lider: pomiar §7 (C i kleeberga). Potem jedno zadanie „perf bez zmiany bajtów” (K1b, K1c, K2a, K4a, K4b, K5a; pliki
`paved.py`, `export.py`, `stage.py`, `network.py`, `meshing.py`) z `compare_world.py` przed/po = identyczne;
osobno K3 (plan działek) z oględzinami.
