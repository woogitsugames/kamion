# ADR 0281 — Przyspieszenie `build_world` bez zmiany bajtów wyjścia (K1a, K1b, K1c, K2, K4a, K4b, K5)

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

WYNIKI_TU

## Czego nie wdrożono i dlaczego
- **K1e (jedno `pipeline.build` zamiast dwóch, ponowne użycie sieci z pass 1).** Zysk ok. 30 s chmury (pass 2:
  `assign_sides` ×2 + `build_junctions` + plan dróg rowerowych). Wymaga `deepcopy` sieci i skrzyżowań przed profilami;
  identyczność zależy od braku porównań po tożsamości obiektów i ukrytych mutacji w całym łańcuchu (także rondo
  kompaktowe, kolej, woda — nieobecne w C), więc biegiem na jednym kaflu jej nie udowodnię. Do tego przebudowa wnętrza
  `pipeline.build`, w którym równolegle pracuje D27 (`effective_graph`). Odłożone.
- **K1d (wektoryzacja `on_arm`/`arm_plane`/`blend`).** Inna kolejność działań float → jednorazowa zmiana bajtów. Poza
  zakresem „bez zmiany wyniku”.
- **K2b (unia per część).** Inny porządek wierzchołków wielokąta → zmiany działek/płotów. Poza zakresem.
- **K3 (plan działek: `obs` w oknie, `cut` przycięty w `layout`).** `plan()` decyduje o marginesach przez porównania pól
  `rect.intersection(obs).area` (remisy, próg 1e-3) i tnie działkę `difference(obs.buffer(0.01)).simplify(0.3)`;
  `simplify` zależy od punktu startowego pierścienia, a pola od kolejności sumowania — wielokąt `obs` złożony z mniejszej
  liczby części daje te same krawędzie, ale inne pierścienie. Identyczności nie da się wykazać → zgodnie ze zleceniem
  pominięte; zalecane jako osobne zadanie z akceptacją lidera i oględzinami (kamery z działkami, `compare_world.py`).
  Na C plan działek to teraz ok. 30 % czasu builda (największa pozycja po tej zmianie); na kleeberga 63 %.

## Konsekwencje
- Wynik `build_world` bajtowo ten sam na C (wyżej) — przebudowa world3 u lidera nie zmienia kafli z powodu tego ADR.
- Pliki wspólne z innymi agentami tej rundy: `roads/pipeline.py` (nowy parametr `collision=True` + 2 warunki; D27
  zmienia `effective_graph` w tym samym pliku), `roads/build_world.py` (1 wiersz: wywołanie pass 1), `roads/network.py`
  (`assign_sides`, `Chain.crossfall_z`). `streetscape/paved.py`, `streetscape/export.py` — tylko D26.
- Nowe ryzyko: kod, który zmodyfikuje `chain.e` w miejscu po pierwszym `crossfall_z`, dostanie `ValueError`
  (świadomie głośno). `road_footprint_polygon` może zwrócić ten sam obiekt wielokąta wielu wywołującym — geometrie
  shapely są niezmienne, `shapely.prepare` nie zmienia wyników.
