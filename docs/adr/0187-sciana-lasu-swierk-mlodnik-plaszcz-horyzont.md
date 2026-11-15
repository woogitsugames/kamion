# ADR 0187 — ściana lasu: świerk, młodnik, płaszcz skraju, runo, linia horyzontu (dojlidy, industrial-c)

Status: PROPOSED na gałęzi `forest-0187` (2026-11-15, s20); nie scalone. Baza: `origin/main` (`857de20df`). Telefon: NIE mierzony (lider). Recenzja `visual-critic`: do wykonania przez lidera.
Źródła: `docs/reports/REVIEW-2026-11-13-s19-0179.md` (route-2 kadry 2–5, P11-056 horyzont), `docs/reports/REVIEW-2026-11-13-s20-0170.md` (P1-1 palisada, P2-3 „kępy liści na gołym pniu”), `docs/reports/REVIEW-2026-11-14-s20-cloud-m68.md` (M68: opisy taksacyjne BDL Nadl. Dojlidy i lasy gminne + NMPT 2023 − NMT dla kafelka Krywlany/Dojlidy i ROD), ADR 0170, docs/06 §2.

## Problem

1. Wnętrze lasu z drogi (route-2 kadry 2, 4): proste pnie z oderwanymi kulami liści, pusta „hala”. Przyczyna: podszyt,
   pas skraju i samosiew to **dojrzałe modele przeskalowane w dół** (sosna 19 m → 4 m = goły słupek z kępką), krzak miał
   liście od 25 % długości pędu, brzoza liście tylko na końcach konarów; podszyt 1 roślina / 60 m².
2. Skraj lasu (kadry 3, 5): pionowa krawędź jak dekoracja — jeden rząd „skraju”, a z daleka jedna pionowa ściana HLOD z
   teksturą samych pni (recenzja 0170 P1-1: palisada z płaskim wierzchem).
3. Horyzont P11-056: zamiast ciemnej ciągłej linii drzew — sadzonki-patyki na tle nieba i białe bryły far-field. Linia
   drzew na zdjęciu to ogrody działkowe (ROD) i lasek na północ od łąki: nie ma ich w BDOT10k OT_PTLZ_A, więc generator
   zostawiał trawę.
4. Biblioteka nie miała świerka (bory sosnowo-świerkowe Puszczy Knyszyńskiej / okolic Krywlan).

## Decyzja

1. **Biblioteka drzew** (`tools/blender/world/make_trees.py`, podgląd `preview_trees.py`): nowe prototypy
   `tree_spruce_0..2` (0, 1 = pokrój drzewostanowy, korona od ~0,36–0,46 H; 2 = gałęzie do ziemi: podrost, skraj),
   `tree_pineyoung_0..1` (młodnik sosnowy), `tree_birchyoung_0..1`, `tree_floor_0..1` (runo: borówka / paproć / nalot,
   bez impostora). Jedyna nowa tekstura: `leaves_spruce.png` (`leaf_textures.spruce_spray`); pozostałe materiały
   istniejące. Krzak: pędy mniej rozchylone, liście od 10 % pędu + ulistniony środek. Brzoza: liście wzdłuż konarów od
   6 % + zwisające gałązki. Konary sosny: `bark_pine` zamiast `bark_twig` (−1 materiał na sosnę w LOD0 / LOD1).
   Impostory młodych drzew w połowie rozdzielczości (768 × 192).
2. **Rozmieszczenie i dane M68** (`streetscape/vegetation.py`, `Data/Regions/bialystok-dojlidy/overrides.yaml`):
   - `MIX` bazowy regionu: iglasty = sosna 0,64 / świerk 0,20 / brzoza 0,10 / inne 0,06; mieszany = sosna 0,36 / świerk 0,14 / brzoza 0,24 / olsza 0,10 / klon 0,08 / lipa 0,08 (WORKING_VALUE dla regionu C).
   - **3 nadpisania `kind: forest_stand` w kafelku `bialystok-dojlidy` wg BDL + NMPT 2023 (M68 §6)**:
     - `dojlidy-ptlz-149a-conifer` (`1260e10f-a825-11ef-9e0c-1866da21c735`, BDOT `las/iglasty`): `height_m: [24.0, 29.0]`, `mix: {pine: 0.65, birch: 0.20, spruce: 0.07, linden: 0.05, alder: 0.03}`, `emergent: {share: 0.03, height_m: [29.0, 32.0]}`.
     - `dojlidy-ptlz-152a-mixed` (`12617d4f-a825-11ef-b23a-1866da21c735`, BDOT `las/liściasty` — w BDL 50–70% sosna): `height_m: [20.0, 28.0]`, `mix: {pine: 0.55, birch: 0.25, linden: 0.10, spruce: 0.05, alder: 0.05}` (`linden` zastępczo za dąb), `emergent: {share: 0.03, height_m: [29.0, 32.0]}`.
     - `dojlidy-ptlz-151a-mickiewicza` (`1ac1a146-d200-4920-9fd4-9ac2b70023a0`, BDOT `zagajnik/mieszany` — w BDL 85–99 l., H 27–29 m): `height_m: [22.0, 29.0]`, `mix: {pine: 0.65, birch: 0.20, spruce: 0.10, linden: 0.05}`, `emergent: {share: 0.03, height_m: [29.0, 32.0]}`; w `vegetation.py` jawne `height_m` w `forest_stand` NIE jest mnożone przez `0.7` dla `zagajnik`, a `young_edge: {width_m: 8.0, height_m: [4.0, 11.0], facing: NE}` zachowuje pas młodnika od ul. Mickiewicza.
   - **Podszyt `UNDERSTOREY`** (1 roślina / ~30 m²): `shrub: 0.55`, `birchyoung: 0.20`, `spruce: 0.15` (1,5–8 m), `maple: 0.10` (`pineyoung: 0` w podszycie zgodnie z BDL; w liściastym bez iglastych).
   - **Częściowy płaszcz skraju `MANTLE`**: zewnętrzny pas krzewów `[0, +4 m]` (`3,0–5,0 m`) włączany deterministycznym hashem odcinka 18 m na `18%` krawędzi (`15–20%`), wewnętrzny pas młodnika `[-5, 0 m]` na `58%` krawędzi (`50–65%`; `100%` w `young_edge`), pas podokapowy `[-11, -5 m]`. Samosiew (`OT_PTNZ_A` / `OT_PTTR_A`): `pineyoung` / `birchyoung` / krzak `1,5–6,5 m`. Runo `tree_floor` tylko ≤ 45 m od drogi / placu i tylko `tier: high`.
3. **HLOD** (`streetscape/forest_hlod.py`, wypiek w `make_trees.bake_forest`): tekstura krawędzi 1024 × 512 bez zmiany rozmiaru, nowy układ: v 0–0,75 = obraz ściany (48 × 24 m; modulacja kopuł ±9 % co 12–16 m, wnętrze 0,93 wysokości frontu), v 0,75–1 = pas płaszcza (48 × 8 m) zapisany do góry nogami (v = 1 to linia gruntu). Zewnętrzna ściana-spódnica (`SKIRT_OFF_M = 3.5 m`) generowana hashem przestrzennym 18 m na `18%` zewnętrznych odcinków krawędzi (w tym samym prymitywie i materiale, +0 draws), a na ostrych narożnikach krawędzi zewnętrznej wysokość ściany opada (`CORNER_DROP = 0.80`). `far_field.add_curtain1`: v wierzchu = `v_main`.
4. **Nowy rodzaj `authored_overrides`: `kind: tree_stand`** — zadrzewienie spoza `OT_PTLZ_A` (`polygons_en`, `height_m`, `emergent`, `mix`, `spacing_m`, `category`, `mantle`). W `bialystok-dojlidy/overrides.yaml` wg pomiarów NMPT 2023 (M68): `allotment-gardens-north-of-krywlany` (`4,0–10,0 m`, `emergent: {share: 0.02, height_m: [14.0, 17.0]}`), `wood-north-west-of-the-meadow` (`8,0–19,0 m`), `wood-north-of-krywlany-skatepark` (`6,5–11,5 m`, `spacing_m: 6.0` — domyka horyzont `photo_P11-056`).
5. **Licencja BDL** (`docs/LICENSES.md`): dopisano atrybucję Banku Danych o Lasach (BULiGL/PGL LP, opisy taksacyjne Nadl. Dojlidy PUL 2017–2026 i lasy gminne stan 2023, pozyskano 2026-11-14).
6. `InstanceImporter.Policy`: `tree_floor` LOD 25 / 90 m (bez impostora).

## Budżet (edytor, baza i `after2` z tego samego worktree; `artifacts/forest-0187/compare2-*.tsv`)

| Zestaw (kamery) | `draws` (baza → po) | `instanced draws` | `trisK` (baza → po) | Najgorszy kadr Δ tris |
|---|---|---|---|---|
| `bialystok-dojlidy` Low (47) | 5959 → 6048 | 2361 → 2625 | 10 234 → 10 385 (+1,48 %) | `edge-north` (+109,75 %) |
| `bialystok-dojlidy` High (47) | 11 384 → 11 533 | 4283 → 4647 | 22 314 → 22 554 (+1,08 %) | `edge-north` (+114,56 %) |
| `bialystok-industrial-c` Low route (129) | 21 338 → 21 338 (max Δ 0) | 11 608 → 11 522 | 22 696 → 22 724 (+0,12 %) | `edge-north` (+2,28 %) |
| `bialystok-industrial-c` High route (129) | 35 880 → 35 880 (max Δ 0) | 22 326 → 22 415 | 52 830 → 52 932 (+0,19 %) | `edge-north` (+9,02 %) |

## Walidacja

- `uv run --project tools/worldgen python -m pytest tests/gis/test_forest_0187.py tests/gis/test_world_v34.py -q`: **33 passed**.
- `uv run --project tools/worldgen python -m pytest tests/gis -q`: **1162 passed, 2 xfailed, 1 failed** (`tests/gis/test_dojbld_0185.py::test_fence_mesh_mips_do_not_preserve_coverage` — niezwiązany z `forest-0187`, stan na `origin/main`).
- Unity `EditMode`: **581 total, 580 passed, 0 failed, 1 skipped** (`Skipped:Ignored`).
- Przegląd wizualny `artifacts/forest-0187/pairs2/`: `photo-P11-056` (horyzont domknięty w 100 % bez białych prześwitów), `route-s0761` i `forest_wall_meadow` (drzewostany 20–29 m + emergenty do 32 m), `forest_edge_near` i `forest_interior_mixed` (pnie sosny w dolnej 1/4–1/3 na niezasłoniętych odcinkach, podszyt bez `pineyoung`, krzewy na ~18 % krawędzi), `krywlany-runway`, `g3a_eye_s0262`, `g3b_eye_s1482`, `edge-north` (C).

## Otwarte / WORKING_VALUE

- Udział emergentów (`0.03` w K1, `0.02` w ROD) oraz zastąpienie dębu lipą (`linden`) w `12617d4f` i `1ac1a146`: WORKING_VALUE.
- Ogrody działkowe: obrysy ±15 m z ortofoto; brak altan i ogrodzeń działek; drzewa owocowe zastępuje klon / lipa; pierścień 3 ROD poza arkuszem NMPT 3-2 (potrzebny arkusz 3-4).
- `far_field._corridor_taper` ma stałe osi dróg regionu C także dla innych regionów (nie ruszane).
- Recenzja 0170 P1-2 (świerk kitu ogrodowego 2–3 m od kamery: szew osi, karta nie sięga gruntu) i P2-1/2 (tuja) — poza tym ADR (atlas `plot_kit`), nadal otwarte. Topola wystająca w pasie 6BC0 (`emergent`): UNVERIFIED, nie dodana.
- Telefon (A16 Low): nie mierzony.
