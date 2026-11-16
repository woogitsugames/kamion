# ADR 0281 — Przyspieszenie `build_world` bez zmiany bajtów wyjścia (K1a, K1b, K1c, K2, K3a, K4a, K4b, K5)

Status: Proposed (agent geo-worldgen, chmura D r7, zadanie D26, gałąź `worldgen-perf2-0281`), 2026-11-16. Do scalenia
przez lidera. Powiązane: `docs/reports/WORLDGEN-PERF-2026-11-16.md` (D22, PR #149: pomiar i propozycje K1–K5),
ADR 0173 (determinizm między buildami), `tools/worldgen/qa/profile_build_world.py`, `tools/worldgen/qa/compare_world.py`.

## Kontekst
`build_world` kafla C trwa u lidera 7,8–9,8 min, w chmurze 13–15 min (raport D22 §2–3). Raport wskazał pięć kosztów
(K1–K5) i podzielił propozycje na „bez zmiany bajtów” (ryzyko zerowe/niskie) i „zmieniające bajty” (K1d wektoryzacja
`blend`, K1e jedno `pipeline.build`, K2b inna kolejność unii, K3 plan działek). Ten ADR wdraża **tylko** te, dla których
dowód identyczności wyjścia się da, i zapisuje, dlaczego reszta nie weszła.

## Decyzja — co zmienione (pliki, mechanizm, dlaczego wynik jest ten sam)

| # | zmiana | plik | dlaczego bajty te same |
|---|---|---|---|
| K2 | memo `road_footprint_polygon` (klucz = SHA-256 kształtu + bajtów tablicy trójkątów faktycznie unionowanych, ≤ 4 wpisy) | `streetscape/paved.py` | trafienie zwraca wielokąt policzony z bajtowo identycznego wejścia (ta sama funkcja, ten sam GEOS) |
| K4a | `nan_to_num`/`nanmean` siatki 2049² raz na wywołanie `build_meshes` (leniwie), nie dla każdego obszaru (748×) i pierścienia (818×) | `streetscape/paved.py` | `zgrid` nie jest modyfikowany w pętli; ta sama tablica wejściowa → te same wartości |
| K4b | `near_road()`: odległość punktów krawędzi do obrysu dróg przycięta do okna punktów + 1 m (`clip_by_rect`), a odległości w paśmie ±1e-6 m od progu 0,6 m mierzone ponownie na całym wielokącie | `streetscape/paved.py` | każdy punkt obrysu bliższy niż 0,6 m leży w oknie; przycięcie zmienia tylko końce przeciętych krawędzi (błąd ~1e-13 m), więc wynik `< 0,6` może się różnić tylko w paśmie, które jest liczone po staremu |
| K5 | `functools.cache` na proceduralnych PNG `textures()` (2 części, by zachować kolejność kluczy dict); 2 pliki z dysku czytane przy każdym wywołaniu | `streetscape/export.py` | funkcje tekstur nie mają wejścia poza kodem; zwracany jest nowy dict z tymi samymi bajtami w tej samej kolejności |
| K1a | `pipeline.build(..., collision=False)` w pass 1: bez zgrubnych wstęg/łat kolizji (warstwa `collision`) | `roads/pipeline.py`, `roads/build_world.py` | pass 1 czyta tylko warstwy `bridge` (pomosty), `road` (działki, przejazdy kolejowe) i `net`; wstęgi/łaty `coarse` dokładają tylko części `collision` i nie mutują `net`/łańcuchów (przegląd `meshing.build_ribbon/_emit_strip/build_patch`); `cull_sides_on_carriageway`/`drop_kerbs_in_fills` liczą każdą część osobno |
| K1b | `STRtree.query(_qbox(q, r))` zamiast `query(q.buffer(r))` w `assign_sides` (3 miejsca) | `roads/network.py` | `query` porównuje tylko obwiednie; obwiednia bufora punktu GEOS = dokładnie `x∓r, y∓r` (test 100 000 punktów × 3 promienie, bit w bit) → ten sam zbiór kandydatów w tej samej kolejności |
| K1c | `Chain.crossfall_z`: `nan_to_num(e)` i `isnan(e)` raz na tablicę `e` (cache po tożsamości tablicy; tablica źródłowa ustawiana jako tylko-do-odczytu) | `roads/network.py` | `e` jest w kodzie tylko podmieniane (`c.e = ...`), nigdy nie modyfikowane w miejscu; zapis w miejscu po tej zmianie rzuca `ValueError` zamiast zostawić nieaktualny cache |

| K3a | `plots.plan` / `plots.layout`: `getattr(X, "geoms", [X])` liczył `X` (różnicę z obrysem całego kafla) **dwa razy** — domyślny argument `getattr` jest zawsze obliczany; teraz raz | `streetscape/plots.py` | ta sama funkcja GEOS na tych samych argumentach; wynik użyty tak samo |

Testy równoważności: `tools/worldgen/tests/test_perf_0281.py` (każda zmiana osobno: referencja = stary kod/formuła).

## Dowód — ten sam wejściowy kafel przed/po

Wejście: kafel `bialystok-industrial-c`, syntetyczny NMT `flat` (bez `Data/raw`, bez LFS; jak w raporcie D22),
far field pominięty. Komenda (oba worktree, wyjście do scratchpad, po każdym biegu `git checkout -- generated landmarks`
+ `git status` czysty):
```
uv run --project tools/worldgen python tools/worldgen/qa/profile_build_world.py --region bialystok-industrial-c \
    --nmt flat --skip-far-field --out-root <scratch>/<tag>/world --json <scratch>/<tag>/stages.json --i-know-generated-is-dirtied
```
Porównanie: SHA-256 **wszystkich 319 plików** wyjścia — 193 pliki `world/` (GLB kawałków + `instances_*.json` + …),
`props/`, `signs/`, `textures/` biblioteki propsów oraz `Data/Regions/<id>/generated/*` (QA JSON) i
`art-source/world/landmarks/*` skopiowane po biegu.

Biegi (ta sama maszyna chmurowa, 4 vCPU; `main` = `origin/main` `0d91ee7db`, A = K1a-c + K2 + K4 + K5 (`a2ce64bed`),
B = A + K3a (`c7e0cb616`)). `base1` szedł równolegle z moim biegiem przechwytującym dane do mikrotestu, `base2`/`after2`
przy obciążeniu innych agentów (load 2–4), `base3`/`after3`/`afterB*` na spokojnej maszynie (load 1,0) — dlatego podaję
medianę i wszystkie wartości, a przypisanie zysku do zmiany czytać z wiersza jej etapu (timery `profile_build_world`):

**Identyczność: 8/8 biegów (main ×3, A ×3, B ×2) — wszystkie 319 plików wyjścia mają ten sam SHA-256 co `base1`**
(lista `sha256.txt` każdego biegu; `git status` po każdym biegu czysty). Main sam ze sobą też identyczny (ADR 0173).

| zmiana | etap (s, chmura) | main, mediana [biegi] | A | B | identyczność |
|---|---|---|---|---|---|
| K2 | `road_footprint_polygon` (5 wywołań) | 192,3 [198, 192, 179] | 167,6 [168, 168, 157] | 153,8 [158, 150] | tak (sha256 319/319) |
| K4a+K4b | `paved.build_meshes` (2 wywołania) | 107,3 [107, 108, 101] | 5,3 [6, 5, 5] | 5,1 [5, 5] | tak + mikrotest (niżej) |
| K5 | `export.export` | 66,8 [69, 67, 64] | 55,5 [56, 56, 55] | 52,7 [52, 53] | tak + test bajtów PNG |
| K1b | `network.assign_sides` (4) | 51,6 [52, 59, 49] | 50,7 [51, 51, 48] | 43,7 [45, 43] | tak + test obwiedni |
| K1a+K1c | `meshing.build_patch` (820 → 615 wywołań) | 88,3 [88, 101, 87] | 69,6 [70, 76, 66] | 65,0 [66, 64] | tak |
| K1c | `meshing.build_ribbon` | 9,6 [10, 10, 8] | 7,7 [8, 9, 8] | 7,7 [8, 8] | tak |
| K3a | `plots.plan` | 81,8 [82, 93, 81] | 86,7 [90, 85, 87] | 59,2 [61, 58] | tak |
| K3a | `plots.layout` (388, w tym relayout) | 52,0 [52, 56, 51] | 55,4 [55, 53, 58] | 27,8 [29, 27] | tak |
| K3a | `plots.plan_access` | 28,8 [29, 31, 28] | 30,8 [31, 29, 33] | 15,9 [17, 15] | tak |
| — | `stage.plan_plots` | 216,2 [216, 238, 212] | 228,3 [229, 228, 228] | 170,6 [176, 165] | — |
| — | `stage.run` | 358,4 [367, 358, 335] | 229,2 [242, 229, 215] | 203,8 [204, 203] | — |
| — | **`build_world` całość** | **934,8** [935, 964, 884] | 770,9 [778, 771, 737] | **655,6** [664, 647] | **tak** |

Mikrotesty na tym samym wejściu (dane pierwszego wywołania `build_meshes` przechwycone z biegu C, 489 obszarów,
obrys dróg 71 050 wierzchołków; 2 powtórzenia, części siatki porównane tablica po tablicy):
`build_meshes` main 81,8 / 79,1 s → gałąź 3,8 / 2,9 s, 1470 części identycznych; sam K4b (stara odległość vs
`near_road`) 16,1 / 16,6 s → 3,3 / 3,8 s, identyczne; 34 678 punktów: `distance < 0,6` 12,6 / 13,1 s → okno 0,40 /
0,36 s, wynik identyczny (wariant `dwithin` 15,5 s — wolniejszy, odrzucony).

Wniosek: **−29,9 % czasu kafla C** w chmurze (mediana 934,8 → 655,6 s; spokojna maszyna: `base3` 884 s vs B 647–664 s
= −25…−27 %). U lidera (chmura ≈ 1,6× wolniejsza wg D22) ok. 9 → 6,5 min — ESTIMATED, do zmierzenia (§ Komendy).
Uwagi: K1b dał mniej niż szacował raport (−1…−8 s; koszt `assign_sides` to pętla Pythona, nie `buffer`). K2 trafia raz
na build (pass 2 `stage.py:143` = `:286`); obrysy pass 1 i pass 2 różnią się (obniżone krawężniki), więc nie trafiają.
`plan_plots` w A +12 s względem main (bez zmian w tym etapie poza trafieniami memo — niewyjaśnione, w granicach
rozrzutu main 212–238 s); w B −46 s dzięki K3a.

## Komendy (lider, prawdziwy NMT)
```
uv run --project tools/worldgen python -m pytest tools/worldgen/tests/test_perf_0281.py -q
uv run --project tools/worldgen python tools/worldgen/qa/profile_build_world.py --region bialystok-industrial-c --out-root artifacts/perf/c/world --json artifacts/perf/c/stages.json --i-know-generated-is-dirtied
git checkout -- Data/Regions/bialystok-industrial-c/generated art-source/world/landmarks
```
Ten sam bieg na main i na gałęzi + `uv run --project tools/worldgen python tools/worldgen/qa/compare_world.py <main>/world <gałąź>/world`
(oczekiwane: brak różnic) albo zwykła przebudowa world3 (wynik ma być ten sam co bez tego ADR).

## Czego nie wdrożono i dlaczego
- **K1e (jedno `pipeline.build` zamiast dwóch, ponowne użycie sieci z pass 1).** Zysk ok. 30 s chmury (pass 2:
  `assign_sides` ×2 + `build_junctions` + plan dróg rowerowych). Wymaga `deepcopy` sieci i skrzyżowań przed profilami;
  identyczność zależy od braku porównań po tożsamości obiektów i ukrytych mutacji w całym łańcuchu (także rondo
  kompaktowe, kolej, woda — nieobecne w C), więc biegiem na jednym kaflu jej nie udowodnię. Do tego przebudowa wnętrza
  `pipeline.build`, w którym równolegle pracuje D27 (`effective_graph`). Odłożone.
- **K1d (wektoryzacja `on_arm`/`arm_plane`/`blend`).** Inna kolejność działań float → jednorazowa zmiana bajtów. Poza
  zakresem „bez zmiany wyniku”.
- **K2b (unia per część).** Inny porządek wierzchołków wielokąta → zmiany działek/płotów. Poza zakresem.
- **K3b (plan działek: `obs` w oknie, `cut` przycięty w `layout`; K3a — podwójna różnica — weszła).** `plan()` decyduje o marginesach przez porównania pól
  `rect.intersection(obs).area` (remisy, próg 1e-3) i tnie działkę `difference(obs.buffer(0.01)).simplify(0.3)`;
  `simplify` zależy od punktu startowego pierścienia, a pola od kolejności sumowania — wielokąt `obs` złożony z mniejszej
  liczby części daje te same krawędzie, ale inne pierścienie. Identyczności nie da się wykazać → zgodnie ze zleceniem
  pominięte; zalecane jako osobne zadanie z akceptacją lidera i oględzinami (kamery z działkami, `compare_world.py`).
  Na C plan działek to po tej zmianie 26 % czasu builda (największy etap); na kleeberga było 63 %.
- **Determinizm:** `tools/worldgen/tests/test_determinism_0173.py::test_vegetation_local_edit_stays_local` pada na
  main tak samo jak na gałęzi (`1160 > 200 and 1437 < 1160`, plik i `vegetation.py` niezmienione) — błąd istniejący, nie
  maskowany, do osobnego zgłoszenia; pozostałe 4 testy tego pliku zielone.

## Konsekwencje
- Wynik `build_world` bajtowo ten sam na C (wyżej) — przebudowa world3 u lidera nie zmienia kafli z powodu tego ADR.
- Pliki wspólne z innymi agentami tej rundy: `roads/pipeline.py` (nowy parametr `collision=True` + 2 warunki; D27
  zmienia `effective_graph` w tym samym pliku), `roads/build_world.py` (1 wiersz: wywołanie pass 1), `roads/network.py`
  (`assign_sides`, `Chain.crossfall_z`). `streetscape/paved.py`, `streetscape/export.py`, `streetscape/plots.py` — tylko D26
  (D25/D27 ich nie zmieniają wg `git diff origin/main...signs-p1-s23 / effective-graph-s23`; brak nakładających się hunków).
- Nowe ryzyko: kod, który zmodyfikuje `chain.e` w miejscu po pierwszym `crossfall_z`, dostanie `ValueError`
  (świadomie głośno). `road_footprint_polygon` może zwrócić ten sam obiekt wielokąta wielu wywołującym — geometrie
  shapely są niezmienne, `shapely.prepare` nie zmienia wyników.
