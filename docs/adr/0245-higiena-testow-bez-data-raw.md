# ADR 0245 — Higiena testów bez Data/raw: hashe wejść raportu fidelity, strumień losowy runa leśnego, wskaźniki LFS
Status: Proposed (agent G3, chmura G, s21, gałąź `tests-hygiene-0245`), 2026-11-15. Scala lider.
Kontynuacja ADR 0075 (raport fidelity dróg), 0173 (determinizm generatora, lokalność edycji), 0187 (ściana lasu, run, płaszcz).
Zadanie: `docs/owner/CLOUD-G-PROMPT-S21.md` G3.

## Kontekst
Trzy testy padały w chmurze (bez Data/raw, bez Unity) i według HANDOVER s21 także na main. Odtworzone na `origin/main`
830b077b (`uv run --project tools/worldgen python -m pytest <test> -x -q`); przyczyny są różne:

| test | przyczyna (ustalona) | rodzaj |
|---|---|---|
| `tests/gis/test_road_fidelity.py::test_report_not_stale` | `fidelity_qa.json` C zapisał hash `tools/worldgen/roads/tunnels.py` = `e3b0c442…b855`, czyli SHA-256 **pustego pliku**. `fidelity/run.py` hashował `glob("roads/*.py")`, więc pusty, nieśledzony plik WIP z nie scalonej gałęzi 0211 w lokalnym main wszedł do zacommitowanego raportu. W czystym checkoucie pliku nie ma → test zgłaszał stale. Raportu nie da się odświeżyć w chmurze (wymaga ortofoto z Data/raw). | błąd narzędzia (zbiór wejść zależny od stanu dysku) |
| `tools/worldgen/tests/test_determinism_0173.py::test_vegetation_local_edit_stays_local` | `vegetation.place` (ADR 0187) filtrował kandydatów runa (`:floor`) testem „≤ 45 m od drogi” **przed** losowaniem atrybutów. Nowy krawężnik/plac zmieniał liczbę losowań, więc przesuwał strumień płaszcza (`:edge`) losowanego zaraz potem: płaszcz zmieniał się w całym lesie (na danych testu 154 → 161 drzew, w tym daleko od edycji). Dokładnie ten wzorzec ADR 0173 usunął w `emit`. Drugi, mniejszy błąd: przy siatce bez żadnego zablokowanego węzła `scipy.ndimage.distance_transform_edt` mierzy odległość do fantomowego punktu poza rogiem siatki, więc run pojawiał się w jednym rogu lasu „przy nieistniejącej drodze”. | **prawdziwy błąd generatora** (od scalenia 0187, `aa76c671`) |
| `tests/gis/test_forest_0187.py::test_edge_texture_has_wall_and_mantle_rows` | `art-source/world/vegetation/forest_edge_*.png` są w LFS; checkout bez LFS daje plik‑wskaźnik i `PIL.UnidentifiedImageError`. Po `git lfs pull` test przechodzi (sprawdzone). | środowisko (checkout bez LFS) |

Pełny pakiet na `origin/main` 830b077b w chmurze (checkout bez LFS) dał **6 failed**, 1419 passed, 68 skipped,
5 xfailed. Poza trzema powyżej:

| test | przyczyna | co zrobione |
|---|---|---|
| `tests/gate3/test_gate3_meta.py::test_evidence_apk_info_legacy_and_dirty` | `scripts/gate3_evidence.py` brał nazwę APK przez `Path(...).name`; ścieżka z wyniku zapisanego na Windows (`C:\x\apk\kamion-…apk`) na Linuksie nie dzieli się na `\` → brak sha | `PureWindowsPath(...).name` (dzieli `\` i `/`) |
| `tests/physics/test_scenario_strictness.py::test_generator_reproduces_committed_scenarios` | ADR 0165 (podatny kontakt nadwozia) zmienił zacommitowany `kerb_step_27cm_42kmh_comb.json` (kontakt nadwozia włączony + check `max_body_penetration_m ≤ 0,05`), ale nie generator, który dalej pisał `overrides.bodyContact=false` z ADR 0158 | generator emituje dokładnie scenariusz zacommitowany (dodany check, bez override); JSON bez zmian |
| `tests/gis/test_world_v31.py::test_frame_budget_with_forest_hlod` | stretch_04 C > 2 M trójkątów High (ADR 0221, budget-fix-s21) | **nie ruszane** (zakaz: budżet 0221; limitu nie podnoszę) |

Lider zgłaszał też padanie dwóch ostatnich „na main” lokalnie. Pierwszy pada wszędzie (błąd generatora). Drugiego
lokalnie z pełnym LFS nie odtworzyłem (brak dostępu); jeśli dalej pada u lidera z prawdziwym PNG, to inny powód
niż tu opisany — komunikat asercji (`mix`, wartość) wskaże który.

## Decyzja
1. **Wejścia raportu fidelity w jednym module** `tools/worldgen/fidelity/inputs.py`, używanym przez pisarza
   (`fidelity/run.py`) i test:
   - hash CRLF‑normalizowany (jak dotąd);
   - kod generatora = moduły `tools/worldgen/roads/*.py` **śledzone przez git** (`git ls-files`; bez gita — wszystkie
     na dysku), więc nieśledzony plik WIP nie trafia do raportu i nie unieważnia go;
   - moduł zapisany z hashem pustego pliku, którego nie ma, = bez zmian (pusty moduł nie wnosi kodu);
   - **zaostrzenie:** śledzony moduł, którego raport nie zna, = stale (dotąd nowy plik generatora nie unieważniał raportu).
   Hashe nie zależą od Data/raw (tylko graf/overrides/trasa regionu i kod w gicie). Testy reguł na drzewie tymczasowym
   (`test_stale_check_rules`, `test_stale_check_ignores_untracked_modules`, `test_report_lists_every_tracked_generator_module`).
   Zacommitowanego `fidelity_qa.json` NIE edytowałem ręcznie (to byłaby fałszywa proweniencja); wpis `tunnels.py`
   z hashem pustego pliku zostaje i jest poprawnie uznany za równoważny brakowi.
2. **Run leśny losuje atrybuty dla wszystkich kandydatów**, a test „blisko drogi” odrzuca dopiero potem (`emit(..., keep=)` — po scaleniu z main ta sama maska co szpalery ADR 0222,
   ta sama zasada co zablokowane komórki w ADR 0173). Siatka bez zablokowanego węzła → odległość do drogi = ∞ (brak runa).
3. **Test lokalności** sprawdza to, co miał, plus jawną regułę runa z ADR 0187: drzewa wszystkich warstw poza
   promieniem przerzedzania identyczne; run obecny w obu przebiegach identyczny; nowy run tylko w promieniu
   `FLOOR_ROAD_M` (+1,5 m siatki) od edycji; żaden run nie znika daleko od edycji. Siatka ma drogę w obu przebiegach
   (e 100..102), żeby porównanie runa nie było puste. Sprawdzone, że stary generator test oblewa (drzewa poza runem
   1043 → 1055, czyli płaszcz rośnie przez przesunięty strumień).
4. **Tekstura brzegu lasu:** `require_lfs()` z `tests/gis/conftest.py` (istniejący helper) → `pytest.skip` z powodem
   „git-lfs pointer”, nie fail. Z pobranym LFS test działa bez zmian.

Żaden limit budżetu ani próg testu nie został podniesiony.

**Wynik (chmura, bez Data/raw, checkout bez LFS, `uv run --project tools/worldgen python -m pytest tests tools/worldgen/tests -q`):**
przed (main 830b077b) 6 failed / 1419 passed / 68 skipped / 5 xfailed → po 1 failed / 1426 passed / 69 skipped /
5 xfailed (+3 nowe testy reguł staleness, +1 skip LFS tekstury brzegu). Jedyny fail: budżet stretch_04 (0221).
Z pobranym LFS (`git lfs pull --include="art-source/world/vegetation/forest_edge_*.png"`) test tekstury przechodzi.

## Konsekwencje
- **Zmiana wyjścia generatora (punkt 2):** przy następnej regeneracji regionów z lasami BDOT (C, Dojlidy, DK65, Knyszyn
  i inne) zmienią się drzewa płaszcza `:edge` (pozycje, gatunki, wysokości, liczba — inny strumień) i atrybuty runa
  `:floor`; pozostałe warstwy bez zmian. Zacommitowane `generated/*` są do tej pory spójne z poprzednim generatorem,
  dopóki lider nie przebuduje. Liczba trójkątów stretch_04 (C, ADR 0221) może drgnąć o szum losowy płaszcza —
  **zmierzyć** po przebudowie; nie zgaduję kierunku. Regionu knyszyn (0227) nie dotykałem.
- **Zakres regeneracji (FIX po recenzji s22, P2):** zmiana strumienia płaszcza = **regeneracja wszystkich regionów z
  lasami BDOT (`OT_PTLZ_A`) przy ich następnej przebudowie**; do tego czasu `generated/*` w gicie opisuje poprzedni
  generator. Lista z zacommitowanych `Data/Regions/<id>/generated/streetscape_qa.json` (`vegetation.forest_mantle` /
  `forest_floor`, stan main `639da4e54`): `bialystok-industrial-c` (13 317 / 14 450), `bialystok-dojlidy`
  (11 128 / 16 526), `bialystok-kleeberga` (3 804 / 11 885), `dk65-01` … `dk65-11` (980…15 569 / 1 842…25 829),
  `dw671-tykocin-01` (1 538 / 844), `knyszyn-s` (4 694 / 3 282), `knyszyn-w` (1 377 / 23), `knyszyn` (1 088 / 147).
  `bialystok-knyszynska`, `bialystok-maczka` i `dk65-monki-01` mają las (`forest_hlod.forest_trees` 12 462 / 84 129 /
  95 724), ale ich raport jest sprzed ADR 0187 (brak pól `forest_mantle`/`forest_floor`) — przy następnej przebudowie
  dostaną płaszcz i run już z nowego strumienia. Kafle pierścienia ADR 0231 będą budowane od razu nowym generatorem.
- **Kolejność:** scalić **przed** jedyną przebudową C, żeby `mesh_budget.frame_estimate` objął tę zmianę. Po
  przebudowie C porównać `trees_lod*` i `forest_hlod` kamery stretch_04 przed/po (przed, main `639da4e54`, `streetscape_qa.json`:
  stretch_04 `tris_high` 1 985 807, `forest_hlod` 30 033, `trees_lod1` 420, `trees_lod2` 6 670). Kierunek zmiany UNVERIFIED (szum losowy, nie nowe obiekty: liczba kandydatów `:floor`
  i maska bez zmian; liczba `:edge` może drgnąć, bo inne pozycje trafiają w inne komórki `blocked`).
- **Determinizm po scaleniu z main (0222 + 0245 w jednym `emit(keep=)`):** sprawdzony na danych syntetycznych
  (`test_vegetation_with_floor_identical_across_processes`: las z drogą, run i płaszcz aktywne, dwa świeże
  interpretery z różnym `PYTHONHASHSEED` = ten sam SHA-256 wyniku; `test_treerows_0222` bez zmian zielony).
  Na realnych C/Dojlidach **nie sprawdzony w chmurze** — `build_world` wymaga `Data/raw` (BDOT, NMT); lider:
  dwa przebiegi + `compare_world.py` (komendy niżej).
- Po scaleniu 0211 (`roads/tunnels.py` śledzony) raport C stanie się stale z prawdziwego powodu → przebudować
  `fidelity/run.py` lokalnie (Data/raw).
- Uzasadnione `UNVERIFIED`: wpływ punktu 2 na liczbę drzew/trójkątów w realnych regionach (nie ma Data/raw w chmurze).

## Komendy dla lidera
```
uv run --project tools/worldgen python -m pytest tests tools/worldgen/tests -q
uv run --project tools/worldgen python -m pytest tests/gis/test_road_fidelity.py tests/gis/test_forest_0187.py tools/worldgen/tests/test_determinism_0173.py -q
# po scaleniu 0211 albo zmianie generatora dróg (Data/raw):
uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c
# regeneracja świata (punkt 2) po naprawie budżetu 0221, potem pomiar stretch_04 i porównanie:
uv run tools/worldgen/build_region.py --region bialystok-industrial-c
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c
uv run --project tools/worldgen python tools/worldgen/qa/compare_world.py <stary_out> <nowy_out>   # oczekiwane różnice tylko w :edge i :floor
# determinizm (C, potem to samo dla bialystok-dojlidy): kopia wyniku, drugi przebieg, porównanie (oczekiwane: brak różnic)
Copy-Item -Recurse Data/raw/derived/bialystok-industrial-c/world artifacts/tests-hygiene-0245/world_run1
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c
uv run --project tools/worldgen python tools/worldgen/qa/compare_world.py artifacts/tests-hygiene-0245/world_run1 Data/raw/derived/bialystok-industrial-c/world
```
