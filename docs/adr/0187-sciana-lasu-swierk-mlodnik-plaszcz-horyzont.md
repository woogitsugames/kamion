# ADR 0187 — ściana lasu: świerk, młodnik, płaszcz skraju, runo, linia horyzontu (dojlidy, industrial-c)

Status: PROPOSED na gałęzi `forest-0187` (2026-11-13, s20); nie scalone. Baza: `horizon-0170` de0ea6df8 + `origin/main`
a4d2a1782 (0170 i 0179 scalone). Telefon: NIE mierzony (lider). Recenzja `visual-critic`: do wykonania przez lidera.
Źródła: `docs/reports/REVIEW-2026-11-13-s19-0179.md` (route-2 kadry 2–5, P11-056 horyzont), `docs/reports/REVIEW-2026-11-13-s20-0170.md`
(P1-1 palisada, P2-3 „kępy liści na gołym pniu”), ADR 0170 („Otwarte”: prototypy biblioteki), docs/06 §2.

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
2. **Rozmieszczenie** (`streetscape/vegetation.py`): `MIX` iglasty = sosna 0,64 / świerk 0,20 / brzoza 0,10 / inne
   0,06; mieszany = sosna 0,36 / świerk 0,14 / brzoza 0,24 / olsza 0,10 / klon 0,08 / lipa 0,08 (WORKING_VALUE).
   Podszyt 1 roślina / ~30 m²: leszczyna 0,38, podrost świerkowy 0,30 (1,5–8 m), brzoza młoda 0,16, sosna młoda 0,16
   (w liściastym bez iglastych). **Płaszcz skraju w 3 pasach** o rosnącej wysokości: 0–4 m na zewnątrz obrysu krzewy i
   nalot 1–3,5 m; 0–5 m do środka młodnik 2,5–9 m; 5–11 m do środka podokap 6–15 m (`MANTLE`). Samosiew
   (OT_PTNZ_A / OT_PTTR_A): te same pozycje, gatunki → `pineyoung` / `birchyoung` / krzak 1,5–6,5 m (koniec „patyków”).
   Runo `tree_floor` tylko ≤ 45 m od drogi / placu i tylko `tier: high` (Low bez zmian liczby instancji).
3. **HLOD** (`streetscape/forest_hlod.py`, wypiek w `make_trees.bake_forest`): tekstura krawędzi 1024 × 512 bez zmiany
   rozmiaru, nowy układ: v 0–0,75 = obraz ściany (48 × 24 m; płaszcz i podszyt zasłaniają pnie, wysokość kopuł
   modulowana ±9 % co 12–16 m, wnętrze 0,93 wysokości frontu), v 0,75–1 = pas płaszcza (48 × 8 m) zapisany do góry
   nogami (v = 1 to linia gruntu), więc oba obrazy stykają się pustym niebem i mipy nie przenoszą kryjących wierszy
   nad las. Przed każdą zewnętrzną ścianą stoi **niższa ściana-spódnica** 3,5 m na zewnątrz z pasem płaszcza — w tym
   samym prymitywie i materiale (+0 draws). Drzewa „okapu” komórki wybierane po roli (gatunek + źródło), nie po h ≥ 8 m.
   `far_field.add_curtain1`: v wierzchu = `v_main`.
4. **Nowy rodzaj `authored_overrides`: `kind: tree_stand`** — zadrzewienie spoza OT_PTLZ_A (`polygons_en`, `height_m`,
   `mix`, `spacing_m`, `category`): siatka okapu + dwa zewnętrzne pasy płaszcza, bez podszytu i runa, maska gruntu bez
   zmian, komórki HLOD jak las; źródło `override:…` (nie kasuje go `open_ground`). W `bialystok-dojlidy/overrides.yaml`:
   `allotment-gardens-north-of-krywlany` (3 pierścienie ROD z ortofoto 2024, ±15 m, drzewa 4–8,5 m) i
   `wood-north-west-of-the-meadow` (10–17 m). Wysokości i udziały: WORKING_VALUE.
5. `InstanceImporter.Policy`: `tree_floor` LOD 25 / 90 m (bez impostora).

## Budżet (edytor, baza i „po” z tego samego worktree; `artifacts/forest-0187/compare-*.tsv`)

@@BUDGET@@

## Walidacja

@@VALIDATION@@

## Otwarte / WORKING_VALUE

- Udziały gatunków, wysokości świerka (14–25 m) i pasów płaszcza: WORKING_VALUE (nie z inwentaryzacji leśnej).
- Ogrody działkowe: obrysy ±15 m z ortofoto; brak altan i ogrodzeń działek; drzewa owocowe zastępuje klon / lipa.
- `far_field._corridor_taper` ma stałe osi dróg regionu C także dla innych regionów (nie ruszane).
- Recenzja 0170 P1-2 (świerk kitu ogrodowego 2–3 m od kamery: szew osi, karta nie sięga gruntu) i P2-1/2 (tuja) — poza
  tym ADR (atlas `plot_kit`), nadal otwarte. Topola wystająca w pasie 6BC0 (`emergent`): UNVERIFIED, nie dodana.
- Telefon (A16 Low): nie mierzony.
