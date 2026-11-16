# WORLDGEN-K3B 2026-11-16 — plan działek w oknie + STRtree (K3b): co się zmienia, ile to daje (D34, s23 r8)

Gałąź `plots-k3b-analysis` (baza `origin/main` `8401944b6`). **Tylko analiza**: generator w gałęzi niezmieniony,
prototyp K3b zrobiony i zmierzony lokalnie (worktree w scratchpad), bez ADR. Kontekst: raport D22
`docs/reports/WORLDGEN-PERF-2026-11-16.md` §4 K3 (PR #149), ADR 0281 (K3a weszło, K3b pominięte, bo „zmienia bajty”).

## 1. Wynik: DONE

**Rekomendacja: WDROŻYĆ Z WARUNKIEM** (§7). Na kaflu C prototyp K3b daje **bajtowo identyczne wyjście**
`build_world` (228/228 plików, SHA-256) przy **planie działek 12× szybszym** (`region_plan` 108,6 → 9,1 s). Na
kleeberga plan działek **16× szybciej** (1 409 → 89,8 s, czyli −22 min z ok. 48 min u lidera, ESTIMATED), a jedyna
różnica to **5 z 815 działek** z dziurą (wycięty sąsiedni dom w środku działki) uproszczoną inaczej — do 0,35 m,
**wyłącznie na wewnętrznych pierścieniach**. Płoty, bramy, furtki, dojazdy, obniżenia krawężników: identyczne
(różnica ≤ 1,1·10⁻¹³ m). Pełny build kleeberga: 19/219 plików inne — 7 kawałków (trawnik `plot_ground` +26 tris,
`road_collision` +10 tris w całym kaflu, 340 węzłów terenu przy tych 5 działkach), build 2 698 → 1 414 s.
Determinizm między procesami i `PYTHONHASHSEED`: zachowany.

## 2. Prototyp (co dokładnie zmienia K3b)

Diff: `docs/reports/k3b/k3b_prototype.diff` (`git apply --check` przechodzi na main; tylko `streetscape/plots.py`,
+35/−11). Trzy niezależne części:

| część | gdzie (main) | było | jest |
|---|---|---|---|
| **OBS** | `plots.py:300-304` (`plan`) | dla każdej grupy domów `unary_union(static + others + laid)`: bufor obrysu dróg całego kafla + wszystkie przeszkody + wszystkie dotąd ułożone działki; `others` = `distance` do **wszystkich** domów | `static_u = union_all(static)` **raz**; per grupa okno = bbox prostokąta startowego `rect(mg)` + 1 m; `clip_by_rect(static_u, okno)` + domy z `STRtree.query(okno)` (ten sam warunek `distance < 40`, ta sama kolejność) + działki z bbox w oknie |
| **HIT** | `plots.py:281` | promień 45 m × 4 kierunki × grupa: `ray.intersection(roads_poly)` (cały kafel) | `ray.intersection(clip_by_rect(roads_poly, bbox promienia + 1 m))` |
| **CUT** | `plots.py:836`, `:845`, `:866`, `:868` → `layout` `:487`, `:510`, `:564` | `layout(plot, cut)` z `cut` = suma dróg + budynków + stref drzwi **całego kafla** (`difference`, `intersects`, `distance` na nim; 3 729 wywołań na kleeberga z `relayout`) | `cut_of(plot)` = `clip_by_rect(cut, bbox działki + 2 m)`, przygotowany, memo na działkę |

Dlaczego to ten sam wynik geometrycznie: marginesy `mg` w pętli `plan` tylko maleją, więc każdy `rect(mg)` i każda
różnica leżą w prostokącie startowym; przeszkoda dalej niż 1 m od niego nie dotyka ani prostokąta, ani `obs.buffer(0.01)`
(najszerszy bufor w `obs`: dom 0,8 m — liczony od domu, a dom z bbox poza oknem jest > 1 m od prostokąta). W `layout`
wszystkie odcinki leżą na krawędziach działki, a `cut.distance(...) < 0.8` pyta o punkty końcowe — margines 2 m.
GEOS `clip_by_rect` zostawia wierzchołki wewnątrz okna bez zmian; nowe wierzchołki tylko na brzegu okna.

## 3. Co dokładnie zmienia się w bajtach

### 3.1 Wynik planu działek (ten sam wejściowy `region_plan`, przechwycony z pass 1)

Wejście: argumenty `region_plan` przechwycone z `build_world` (pass 1, syntetyczny NMT `flat`, bez `Data/raw`) —
`compare_plots.py capture`; potem `run` dla main i K3b w osobnych procesach; `diff` porównuje id i kolejność działek,
WKB obrysów, Hausdorffa, odcinki płotów (końce), bramy, furtki, dojazd (łańcuch/strona), obniżenia krawężników.

| | C (99 działek) | kleeberga (815 działek) |
|---|---|---|
| działki: liczba / id / kolejność | 99 = 99, te same, ta sama | 815 = 815, te same, ta sama |
| obrys WKB identyczny | 98 | 802 |
| obrys różny | 1 (Hausdorff 1,1·10⁻¹³ m) | 13: 8 × ≤ 1,1·10⁻¹³ m, **5 × 0,23–0,35 m** |
| liczba wierzchołków różna | 0 | 0 |
| `lay` (płoty/bramy) identyczne | 97 (2 × końce odcinków ±1,1·10⁻¹³ m) | 800 (15 × ±1,1·10⁻¹³ m) |
| odcinki płotów (liczba / długość sumaryczna) | 583 / 9 642,321 m = | 3 710 / 61 166,473 m = |
| bramy / zmienione | 43 / 0 | 607 / 0 |
| furtki zmienione / dojazdy zmienione | 0 / 0 | 0 / 0 |
| obniżenia krawężników (`drops`) | 43, identyczne bajtowo | 607, identyczne bajtowo |
| `access_stats` (moved/removed) | 11/5 = | 118/54 = |

Pliki: `docs/reports/k3b/c_region_plan_diff.json`, `docs/reports/k3b/kleeberga_region_plan_diff.json`.

Ablacja na C (każda część osobno vs main): HIT — **bajtowo identyczne** (99/99 obrysów, 99/99 `lay`); OBS — 1 obrys
i 1 `lay` ±1,1·10⁻¹³ m; CUT — 1 `lay` ±1,1·10⁻¹³ m. Różnice ostatniego bitu biorą się z innego rozkładu wielokątów
wejściowych w overlay GEOS (inny początek pierścienia), nie z innej geometrii.

### 3.2 Pełny `build_world` kafla C (wszystkie pliki wyjścia)

`profile_build_world.py --nmt flat --skip-far-field`, main (`k3bbase`) ×1 i K3b ×2 (`PYTHONHASHSEED` 0 i 31337),
SHA-256 wszystkich plików: 64 GLB `chunk_*.glb` + 64 `*.low.glb` + JSON-y `world/`, `Data/Regions/<id>/generated/*`
(QA, `streetscape_qa.json`, landmarki spec) i `art-source/world/landmarks/*` skopiowane po biegu = **228 plików**.

**Wynik: 228/228 identycznych (main = K3b bieg 1 = K3b bieg 2).** Różnice 10⁻¹³ m z §3.1 znikają przy zapisie
(float32 w GLB, zaokrąglenia w JSON). Lista SHA main: `docs/reports/k3b/c_sha256_main.txt`. `git status` po każdym
biegu przywrócony do czystego (`git checkout -- generated landmarks`).

### 3.3 Kleeberga — pełny build

Ta sama procedura, main ×1 i K3b ×1 (równolegle, load 3–5; build main trwa 45 min w chmurze, drugiej pary nie
robiłem). **219 plików, 19 różnych** (lista + `compare_world.py`: `docs/reports/k3b/kleeberga_full_build_diff.txt`):

| plik | co się zmieniło |
|---|---|
| `world/chunk_{3_5,4_5,6_5,6_6}.glb` + `.low.glb` | `plot_ground` +10/+3/+10/+3 tris, `road_collision` +4/+1/+2/+1 tris (`world_manifest.json`) |
| `world/chunk_3_7.glb` + `.low.glb` | `road_collision` +2 tris |
| `world/chunk_{3_4,5_0,5_6}.glb` (+ `.low` 3_4, 5_6) | ta sama liczba trójkątów i bajtów — przesunięte wierzchołki terenu |
| `world/terrain_conformed.npy` | **340 węzłów** (z 2049²) w 14 skupiskach, wszystkie przy 5 działkach z §4; max \|Δz\| 0,32 m (krok dopasowania terenu pod nawierzchnię — z płaskim NMT to jedyna wysokość, która może się zmienić) |
| `gen/world_manifest.json` | SHA/bajty/trójkąty powyższych kawałków |
| `gen/streetscape_qa.json` | `mesh_budget.per_chunk[29,37,53,54]` `tris_high_static` +10/+3/+10/+3 (low tak samo); `plots.list[140,425,779].c` (środek działki, 0,1 m) |
| `gen/roads_qa.json` | `summary.footprint_nodes` 986 949 → 986 932 (−17) |

`instances_*.json`, warstwy `plots`/`plots_low` (płoty, bramy, rośliny ogrodów), budynki, drogi: identyczne. Budżet:
+3…+10 tris na kawałek (≤ 0,005 % kawałka), `mesh_budget.frame_estimate` bez zmiany — neutralnie.

## 4. Wpływ na wygląd

- **C:** zero — bajty wyjścia identyczne (§3.2). Budżet kamer (`streetscape_qa.json`, `mesh_budget.frame_estimate`)
  bez zmian, bo plik jest identyczny.
- **Kleeberga:** 5 działek (render `docs/reports/k3b/kleeberga_plot_diffs.png`, mapa własnych danych, matplotlib).
  We wszystkich pięciu zewnętrzny obrys i płoty są identyczne; różnią się **dziury** wycięte wokół domu sąsiedniej
  grupy stojącego wewnątrz działki (`others` = dom + 0,8 m, potem `difference(obs.buffer(0.01)).simplify(0.3)`).
  `simplify` Douglasa-Peuckera na pierścieniu zależy od jego punktu startowego, a ten zależy od tego, z ilu części
  składa się `obs` (cały kafel vs okno). Przykłady (id BDOT skrócone, Hausdorff / zmiana pola):
  `da4c8df1…` 0,35 m / −6,6 m²; `2BE4B431-6834…` 0,29 m / −6,6 m²; `2BE4B431-65F2…` 0,29 m / −4,8 m²;
  `2BE4B431-6919…` 0,26 m / −2,1 m²; `2BE4B431-6F58…` 0,23 m / −1,7 m². Skutek: brzeg trawnika działki
  (`plot_ground`) wokół cudzego domu przesunięty o ≤ 0,35 m; dyskretne decyzje (płot/brama/furtka/dojazd/
  obniżenie krawężnika, styl, wysokość) — **żadna nie zmieniona**; rośliny ogrodów i instancje też identyczne
  (§3.3). Zmienia się tylko trawnik (+26 tris w kaflu) i teren pod nim (340 węzłów, ≤ 0,32 m) w pasie ≤ 0,35 m wokół
  cudzego domu w głębi ogrodu, 25–60 m od ulicy. Z kabiny: oceniam jako niewidoczne (ESTIMATED; potwierdzić
  kamerą tylko jeśli któraś z kamer kontrolnych kleeberga patrzy na te działki — pozycje w `kleeberga_plot_diffs.png`,
  środki działek w układzie kafla: (−85, −1012), (−104, −272), (167, −496), (531, −639), (551, −474) m).

## 5. Determinizm (ADR 0173)

- `region_plan` K3b: C ×3 procesy (`PYTHONHASHSEED` 0, 7, 0 + bieg z ablacją) i kleeberga ×2 (0, 4242) — wyniki
  **bajtowo identyczne** między procesami (pickle bez timerów). Main dla porównania: C ×3, kleeberga ×2 (0, 99) —
  też identyczne.
- Pełny build C K3b ×2 (`PYTHONHASHSEED` 0 i 31337): 228/228 identyczne.
- Brak nowej losowości: `STRtree.query` posortowane po indeksie, kolejność `others` = kolejność domów jak w main;
  `cut_memo` po id działki (słownik, deterministyczny).
- `tools/worldgen/tests/test_determinism_0173.py` + `tests/gis/test_determinism.py` na prototypie: 8 passed,
  1 skipped (te testy nie dotykają planu działek — dowodem są biegi wyżej).

## 6. Zysk czasu (ten sam wejściowy `region_plan`, chmura 4 vCPU, load 2–7 od innych agentów)

| kafel | etap | main [biegi] → mediana | K3b [biegi] → mediana | zysk |
|---|---|---|---|---|
| C | `region_plan` | [108,6; 118,1; 103,5] → **108,6 s** | [9,1; 9,8; 8,5] → **9,1 s** | −99,5 s (12×) |
| C | `plan` | [70,4; 73,7; 70,9] → 70,9 | [2,1; 1,8; 1,8] → 1,8 | −69 s |
| C | `layout` (387) | [33,5; 38,7; 28,9] → 33,5 | [2,0; 2,9; 2,1] → 2,1 | −31 s |
| kleeberga | `region_plan` | [1 430,6; 1 409,4] → **1 420,0 s** | [86,5; 93,2] → **89,8 s** | **−1 330 s (16×)** |
| kleeberga | `plan` | [835,4; 793,4] → 814,4 | [7,3; 7,3] → 7,3 | −807 s |
| kleeberga | `layout` (3 729) | [549,1; 568,3] → 558,7 | [27,7; 30,7] → 29,2 | −530 s |
| kleeberga | `plan_access` (z relayout) | [343,0; 354,8] → 348,9 | [42,7; 46,8] → 44,8 | −304 s |

Pełny build kleeberga (1 bieg każdy, równolegle): main **2 698,1 s** → K3b **1 414,2 s** (−47,6 %);
`stage.plan_plots` 1 756,9 → 192,8 s, `plots.region_plan` 1 642,1 → 80,2 s. `plots.build` 313 → 449 s i `stage.run`
590 → 850 s w K3b to obciążenie (K3b był w tych etapach, gdy main liczył plan działek i szły biegi `normalize`;
K3b nie zmienia `plots.build`) — do potwierdzenia u lidera.

Pełny build C (te same warunki, timery `profile_build_world`): main 851,2 s (1 bieg, load 5–7) vs K3b 614,9 / 617,8 s;
`stage.plan_plots` 217,6 → 86,3 s; `plots.region_plan` 120,9 → 7,7 s. Część różnicy całości to obciążenie maszyny —
**przypisuję K3b tylko zysk z wiersza `region_plan` (≈ −110 s chmury ≈ −70 s u lidera, ESTIMATED ×0,6 wg D22)**.
U lidera kleeberga: `plots planned` 1 822 s (log 15.11) → ok. 100–150 s (ESTIMATED: 1 822 × 89,8/1 420 ≈ 115 s).

Co zostaje po K3b (kleeberga, pełny build K3b, timery): `plots.build` 449 s (rośliny ogrodów / „garden fronts”,
`plots.paved_items` 59 s), `road_footprint_polygon` 178 s (5 wywołań), `pipeline.build` 246 s, `gate_access` 40 s
(pętla po wszystkich łańcuchach sieci na bramę — kandydat na STRtree, ten sam wzorzec). To następne cele (K3c).

## 7. Rekomendacja dla lidera: WDROŻYĆ Z WARUNKIEM

1. Wdrożyć OBS + HIT + CUT jak w `k3b_prototype.diff` (ADR: dopisać sekcję „K3b” do ADR 0281 — runda bez nowych
   numerów). HIT samo jest bajtowo identyczne nawet w `region_plan` i może wejść bez warunku.
2. Warunek: przebudowa C na prawdziwym NMT daje **bajtowo identyczny** wynik (jak w chmurze), a na kleeberga różnice
   ograniczone do działek z dziurami (`compare_plots.py diff`: `gate_changed`, `wicket_count_changed`,
   `access_changed`, `run_count_changed` puste; Hausdorff ≤ 0,35 m tylko w działkach z dziurą) + `compare_world.py`
   z różnicami tylko w kawałkach tych działek (jak §3.3). Jeśli warunek nie przejdzie — zostawić HIT, resztę cofnąć.
3. Wariant odrzucony na teraz: `shapely.normalize(...)` przed `simplify(0.3)` w `plan` (`plots.py:333`). Z nim K3b vs
   main+normalize jest identyczne do 1,1·10⁻¹³ m także na kleeberga (807/815 bajtowo, 8 × 10⁻¹³, 0 > 1 mm) — wynik
   przestaje zależeć od kształtu `obs`. Ale sam `normalize` to jednorazowa zmiana wszystkich kafli: C 40/99 obrysów
   (2 > 1 mm, max 0,18 m), **1 brama przesunięta**; kleeberga 206/815 obrysów (8 > 1 mm, max 0,29 m), +4 m płotów.
   Warto dopiero przy następnej świadomej zmianie planu działek.

### Komendy (prawdziwy NMT, maszyna lidera)

```
# 0. worktree main (A) i worktree z K3b (B): git apply docs/reports/k3b/k3b_prototype.diff w B
# 1. szybkie A/B samego planu działek (przechwycenie zapisuje tylko pickle; nie rusza generated/)
uv run --project tools/worldgen python tools/worldgen/qa/compare_plots.py capture --region bialystok-kleeberga --out artifacts/k3b/rp_kl.pkl
uv run --project tools/worldgen python tools/worldgen/qa/compare_plots.py run --worktree <A> --input artifacts/k3b/rp_kl.pkl --out artifacts/k3b/kl_main.pkl
uv run --project tools/worldgen python tools/worldgen/qa/compare_plots.py run --worktree <B> --input artifacts/k3b/rp_kl.pkl --out artifacts/k3b/kl_k3b.pkl
uv run --project tools/worldgen python tools/worldgen/qa/compare_plots.py diff artifacts/k3b/kl_main.pkl artifacts/k3b/kl_k3b.pkl
# 2. pełny build przed/po (w każdym worktree; potem przywrócić generated/landmarks)
uv run --project tools/worldgen python tools/worldgen/qa/profile_build_world.py --region bialystok-industrial-c --out-root artifacts/perf/k3b-<A|B>/c/world --json artifacts/perf/k3b-<A|B>/c/stages.json --i-know-generated-is-dirtied
git checkout -- Data/Regions/bialystok-industrial-c/generated art-source/world/landmarks
uv run --project tools/worldgen python tools/worldgen/qa/compare_world.py artifacts/perf/k3b-A/c/world artifacts/perf/k3b-B/c/world
# (to samo dla --region bialystok-kleeberga)
# 3. testy
uv run --project tools/worldgen python -m pytest tests/gis/test_buildings_r6.py tests/gis/test_buildings_r7.py tests/gis/test_buildings_r8.py tests/gis/test_buildings_r9.py tests/gis/test_house_greenery_0163.py tests/gis/test_pavements_0237.py tools/worldgen/tests/test_perf_0281.py tools/worldgen/tests/test_determinism_0173.py tools/worldgen/tests/test_compare_plots.py -q
# 4. oględziny (tylko gdy kleeberga różni się bajtami): import + kamery
pwsh scripts/import-region.ps1 -Region bialystok-kleeberga
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting clear -OutputDir artifacts/visual-qa/k3b-kleeberga
```

## 8. Testy do aktualizacji

Żaden. Na prototypie (scratch worktree) zielone: `tests/gis/test_buildings_r6.py`, `_r7`, `_r8`, `_r9`,
`test_house_greenery_0163.py`, `test_pavements_0237.py`, `tools/worldgen/tests/test_perf_0281.py` — **92 passed**
(298 s); `test_determinism_0173.py` + `tests/gis/test_determinism.py` — 8 passed, 1 skipped. Testy porównujące
liczby z `generated/*` kafli nie zmienią się dla C (bajty identyczne); dla kleeberga — tylko jeśli §3.3 pokaże różnice
w QA JSON — pokazał tylko `per_chunk` trójkąty i `plots.list[].c` w `streetscape_qa.json` oraz `footprint_nodes`
w `roads_qa.json`; `grep` w `tests/gis` i `tools/worldgen/tests` nie znajduje asercji na tych polach kleeberga. Przy wdrożeniu dodać test równoważności (jak `test_perf_0281.py`):
`plan()` main-formuła vs okno na syntetycznym kaflu (dom wewnątrz cudzej działki — przypadek z §4) z tolerancją
`simplify`.

## 9. Zmienione pliki (gałąź)

- `tools/worldgen/qa/compare_plots.py` (nowy): `capture` / `run` / `diff` — A/B planu działek na tym samym wejściu.
- `tools/worldgen/tests/test_compare_plots.py` (nowy, 2 testy): `uv run --project tools/worldgen python -m pytest
  tools/worldgen/tests/test_compare_plots.py -q` → 2 passed.
- `docs/reports/k3b/`: `k3b_prototype.diff`, `c_region_plan_diff.json`, `kleeberga_region_plan_diff.json`,
  `c_sha256_main.txt`, `kleeberga_full_build_diff.txt`, `kleeberga_plot_diffs.png`.
- ten raport, `STATUS.md`.

## 10. Rozróżnienie, ryzyka

- **Zmierzone (chmura):** wszystkie liczby §3, §5, §6 (syntetyczny NMT `flat`, far field pominięty, landmarki STALE —
  jak w D22/ADR 0281). **ESTIMATED:** czasy u lidera. **UNVERIFIED:** prawdziwy NMT (plan działek nie czyta NMT
  w pass 1 poza obrysem dróg, ale obrys dróg zależy od profilu — wejście u lidera będzie inne niż w chmurze).
- Ryzyko: okno 1 m / 2 m jest poprawne tylko dopóki `plan` nie poszerza marginesów i `layout` nie pyta o `cut` dalej
  niż 0,8 m od krawędzi działki — przy przyszłych zmianach tych funkcji trzeba pamiętać o oknie (komentarz w kodzie).
- Ryzyko: wynik kleeberga zależy od tolerancji `simplify(0.3)` — kafel z wieloma domami wewnątrz cudzych działek
  może mieć więcej takich dziur (dla C: 0).
