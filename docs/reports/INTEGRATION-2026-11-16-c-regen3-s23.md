# Integracja 2026-11-16 — trzecia wspólna przebudowa C i Dojlid (c-regen3-s23)

Gałąź `c-regen3-s23` z `origin/main` `8900a203a`. Pakiet: #123 (typologia, ADR 0238), #119 (higiena testów, ADR 0245),
#93 (rondo Putry, ADR 0226 + 0198), P1 z recenzji shadera płotu. Jedna przebudowa `bialystok-industrial-c` i
`bialystok-dojlidy`. Narzędzia: `artifacts/c-regen3-s23/tools/` (kopie c-regen2 z poprawkami), statusy `exit=` per krok.

## Werdykt: gotowe do scalenia — TAK
Budżet C High poniżej 2 M, determinizm potwierdzony, EditMode bez nowych błędów, pytest — patrz tabela.
Zastrzeżenia do decyzji lidera są w sekcji „Otwarte”; najważniejsze: brak `visual-critic` i jedno przejście dla
pieszych mniej w C (węzeł OSM 2882674807).

## Scalenia (osobne merge commity, `STATUS.md` = main)
| PR | gałąź | merge | konflikty |
|---|---|---|---|
| #123 | `origin/typology-fix-s23` `91490b0fe` | `1244ac0a3` | brak |
| #119 | `origin/tests-hygiene-0245` `63bd4a20d` | `9a8cbb874` | brak |
| #93 | `origin/putry-ring-0198b-rebased` `852389efe` | `d43bd5e19` | `network.py`, `build_world.py` |

- `network.py`: wersja main w całości (ma już `_truck_apron`, pętlę w `assign_sides`, `compact`, `construction`).
  Kod 8 = `apron_paving_light` (D75, triage), nie `sidewalk_paving` z PR.
- `build_world.py`: `on_ground_road = HB.keepout(w.hf, mask)` z PR zamiast lokalnej funkcji (ta sama logika, wspólna
  z `qa/check_piers_vs_roads.py`); blok `keep_tunnel_cut` z PR odrzucony — main usunął go w ADR 0211.
- `junctions.py`, `overrides.yaml` C (192 wpisy, 0 zduplikowanych id), `hero_bridge.py`: scalone automatycznie, przejrzane.
- `tests/gis/test_putry_ring_0226.py:79` oczekiwał `sidewalk_paving` dla kodu 8 → poprawiony na `apron_paving_light`
  (commit `fix(tests): 0226`); plik 16/16.

## P1 recenzji `REVIEW-2026-11-16-s23-code-fence-mesh-forward.md`
- `InstanceImporter.UsableShaderOrNull(Shader)` + `FenceShaderOrNull()` (`Shader.Find` + `ShaderUtil.ShaderHasError`,
  ostrzeżenie w logu); użyte w `RegionImporter.LitMaterial` i `InstanceImporter.ImportTexture`. Tylko kod edytora
  (`Game.World.Import.Editor`), bez zmian asmdef.
- Test EditMode `FenceShaderFallbackTests` (5 przypadków, przez refleksję): brak shadera → null; shader płotu → ten sam
  obiekt; shader z błędem składni → null, tekstura zachowuje mipy z pokryciem, materiał zostaje na URP Lit; oba
  importery szukają shadera tylko przez pomocnik. Wynik: 5/5.
- ADR 0239 pkt O-6. Nadal UNVERIFIED (P2 recenzji): czy `ShaderHasError` widzi błąd wariantu jeszcze nieskompilowanego;
  dlatego `vqa.ps1` przeszukuje logi renderów pod kątem błędów shadera (tu: 0 trafień).

## Przebieg (czytane z `exit=`)
| krok | wynik | czas |
|---|---|---|
| before | Reuse `artifacts/c-regen2-s23/after` (Low overcast, High clear, G3 Low clear) | sekundy |
| `build_region` C / Dojlidy | exit 0; nowy pickle warstw OSM (klucz z `roof:shape`), 643 / 415 budynków w kaflu (Dojlidy: liczba z baseline, nie z logu) | 24 s / 8 s |
| `build_world` C ×2 | exit 0, exit 0 | 9 min 49 s, 10 min 1 s |
| `build_world` Dojlidy ×2 | exit 0, exit 0 | 7 min 45 s, 7 min 19 s |
| determinizm (#119) | `compare_world.py` przebieg 1 vs 2: exit 0 w obu regionach; `generated/` (bez fidelity): 0 różnic w SHA-256 | |
| fidelity, export-route, audyt lamp | exit 0 w obu regionach | |
| katalog regionów `--check`, audyt cieni | exit 0, exit 0 | |
| budżet (`30-budget.py`) | exit 0, GREEN | |
| EditMode | 965: 962 passed, 2 failed (oba znane `CarPaintMaterialTests.DepositionChannel_*`), 1 skipped; 0 nowych | 3 min |
| import C / Dojlidy | exit 0 / exit 0 (`IMPORT_RESULT: OK`, 64 chunki każdy) | 10 min / 9 min 44 s |
| VQA after (5 komórek) | exit 0 ×5; 0 linii błędów shadera w logach | 2 min 23 s |
| pełny pytest (1. przebieg) | `tests/gis`: 1878 passed, **1 failed**, 3 skipped, 2 xfailed; `tools/perf/tests` 61 passed | 20 min 2 s |
| pełny pytest (2. przebieg, drzewo końcowe z OD-005) | PYTEST2_PLACEHOLDER | |

Before = Reuse jest uzasadnione tym, że `generated/` C i Dojlid w main różniło się od scalenia c-regen2 (`e4fad6868`)
tylko `fidelity_qa.json`, a sceny `_Generated` w main są z 15.11 16:59 (sprzed c-regen2) — świeże before wymagałoby
budowy i importu obu regionów (ok. 55 min wg c-regen2).

## Budżet (zmierzone, `artifacts/c-regen3-s23/regen/budget.log`)
| | przed (main) | po | zapas / limit |
|---|---|---|---|
| C `stretch_04` High (`frame_estimate`) | 1 985 807 | **1 985 460** (−347) | 14 540 do 2 M |
| C `stretch_04` Low | 938 274 | 937 764 (−510) | |
| C `route_onramp_andersa_above` High | 1 966 411 | 1 962 387 (−4 024) | |
| C największy wzrost High | | `dk8_dk19_exit` +12 001 (1 454 076; drzewa LOD0 +7 508, LOD1 +4 540) | |
| C największy wzrost Low | | `dk8_dk19_exit` +0,70 % | próg +2 % |
| C materiały `stretch_04` High | 155 | 149 | |
| Dojlidy max High (`photo_P11-063`) | 1 768 010 | 1 767 786 (−224) | 232 214 |
| Dojlidy: wszystkie 17 kamer | | High ≤ 0, Low ≤ +8 trójkątów | |
| far_field Low C / Dojlidy | 25 389 / 23 907 | bez zmian | ≤ 30 000 |
| materiały manifestu | 336 | 340 | |
| edytor `stretch-04` High / Low (`trisExact`) | 1 067 394 / 312 956 | 1 066 977 / 312 609 | drawsEst 1085 → 1075 / 463 → 455 |

Rozbicie `stretch_04` High: budynki −1 473, drogi −1 633, props +2 815, drzewa LOD2 −28, furniture −28.
Szacunek z raportu FIX #123 (−697) dotyczył tylko budynków bez `BASE_M`; zmierzone budynki −1 473.

## `pytest-after-regen exit=1` — analiza
3 testy `test_typology_0238.py` padły po przebudowie: `test_authored_and_untouched_buildings_are_bit_identical` (C i
Dojlidy; bloki z wielkiej płyty, np. 11 380 → 11 282 trójkątów) i `test_triangle_budget_is_not_above_the_baseline`
(Dojlidy, `kuronia2_front` +4 High). Przed przebudową ten sam plik przechodził 22/22.
- Przyczyna: baseline był policzony kodem sprzed #123 na danych sprzed `build_region`. `BASE_M` 1,5 (część #123, działa
  w `buildings.py`) zmienił wysokości w `buildings.geojson`, więc test porównywał kod #123 na nowych danych z kodem
  starym na starych danych. Raport FIX #123 to przewidział („wpływ UNVERIFIED, zmierzyć po przebudowie”).
- Naprawa wg procedury z raportu FIX: baseline przeliczony kodem `origin/main` (`git archive`, bez `typology.py`,
  `subtypes: null`) na danych po przebudowie. Suma harnessu kodem sprzed #123: C 964 112 → 963 856, Dojlidy
  500 537 → 500 683 (LOD0) — to jest sam efekt danych. Po przeliczeniu `test_typology_0238.py` 22/22.
- Rzeczywisty budżet mierzy `frame_estimate` (tabela wyżej): `kuronia2_front` High −12.
- Uwaga do testu (nie zmieniałem): po przebudowie zacommitowany `frame_estimate` zawiera już #123, a test dodaje do
  niego deltę harnessu — szacunek per kamera liczy wtedy efekt #123 dwa razy. Do uporządkowania przez autora #123.

## Zmiany w `generated/` — co skąd
**Z trzech PR-ów:**
- #123: `buildings.subtypes` (C: 67 biurowców, 267 domów, 3 domy drewniane, 120 gospodarczych, 77 hal, **1 kamienica**,
  43 pawilony, 50 bloków; Dojlidy: 0 kamienic, 12 bloków), `pavilion_fronts` 24 / 15, `roofs_other`,
  `facade_signs` 86 → 72 (C) i 78 → 65 (Dojlidy), balkony 3 357 → 3 348.
- #119: Dojlidy `forest_mantle` 11 128 → 11 148, liczby drzew per gatunek ±0,1…2 %; w C zmiany lasu widać w budżecie
  kamer leśnych (`dk8_dk19_exit`).
- #93: `overrides_applied` 123 → 125 (`putry-ring-island-kerb`, `putry-ring-island-nw-corner`), 0 nieaktualnych;
  podpory `guardrails_pier.piers` 58 → 66, `viaduct_putry_underdeck.spec.json`; kamera `putry_above` przesunięta
  o 0,25 m (środek ronda); trasa Nav C (`bialystok-industrial-c_route.bytes`).

**Spoza trzech PR-ów (kod świata w main od c-regen2: 0272, 0222, rondo kompaktowe, kolej):**
- Dojlidy: `roads_qa.json`, `road_consistency_qa.json`, `terrain_walls_qa.json` — 0 różnic. Dryfu z main nie ma.
- C, drogi: wszystkie różnice w `roads_qa.json` dają się przypisać przebudowie pierścienia Putry (łaty skrzyżowań
  polar 147 → 146, delaunay 37 → 38, footprint −242 węzły). Nie znalazłem zmiany, która wskazywałaby na 0272 / 0222 /
  rondo kompaktowe / kolej (C nie ma poboczy zamiejskich, szpalerów z `tree_rows.yaml` ani przejazdu).
- C, wtórne skutki zmiany strumienia losowego i geometrii (nie da się ich przypisać jednemu PR bez przebudowy
  każdego osobno): parking 1 495 → 1 513 zatok, 906 → 913 aut, naczepy na placach 268 → 265, ciągniki 79 → 81, jedna
  latarnia `lamp_10m` mniej (57 → 56), nawierzchnie placów ±1…8 m². Na renderach widać to jako inne naczepy w tych
  samych miejscach (`stretch-03`, `g3a-eye-s0262`).
- **C: jedno przejście P-10 mniej** (63 → 62; `crossings_skipped` zyskało węzeł OSM 2882674807). Położenie
  UNVERIFIED — prawdopodobnie wlot ronda Putry, bo tylko tam zmieniła się geometria dróg. Do sprawdzenia przez autora #93.

## Oględziny before | after (`artifacts/c-regen3-s23/view/`, pary `ab_*.jpg` i `v_*.jpg`)
Obejrzane przeze mnie na 10 kadrach; **bez `visual-critic` i bez zestawienia ze zdjęciami właściciela**.
- **Rondo Putry #93** (`putry-above` High, `g3b_rondo_put_above` Low; ortofoto `artifacts/putry-ring-0198b/ortho-overlay-island.jpg`):
  przed — wyspa nieregularna, ze szpicem i szeroką opaską z kostki; po — gładki, wydłużony owal z krawężnikiem,
  kształtem zgodny z obrysem z ortofoto. Różnica względem ortofoto: wnętrze wyspy jest całe trawiaste, na ortofoto
  jest pas żwiru/tłucznia przy krawężniku i trawa w środku.
- **Typologia #123**: budynek ceglany na `photo-P11-129` (Dojlidy) zmienił barwę z czerwonej cegły na ciemniejszy brąz;
  dalekie bloki zmieniły kolory elewacji (`photo-P11-129`, `stretch-03`); pawilon na `truck-at-gate` dostał dach
  dwuspadowy zamiast płaskiego. Hale (`route-s1675`, `photo-P11-094`) i `photo-biezenstwa-ground` bez widocznych zmian.
  Kamienica jest w C jedna i nie ma jej na obejrzanych kadrach — nie oceniona. Front pawilonu na Low z bliska — nie oceniony.
- **Roślinność #119** (`dk8-dk19-exit` High, `truck-at-gate` Low): inny układ drzew płaszcza lasu, ta sama gęstość
  i gatunki; bez dziur.
- **Płoty** (`kwadrat-park-gate`, `photo-P11-094` Low): siatka szara, bez magenty; 0 błędów shadera w logach.
- Pary Low nie są jeden do jednego: after jest wyraźnie ciemniejsze i bardziej kontrastowe (np. `photo-P11-094`),
  do tego ADR 0269 (cienie drzew PC Low). To zmiany renderingu w main po renderach c-regen2, nie tej gałęzi.
- Kamery ciężarówki i kabiny w C różnią się bardziej niż w Dojlidach (RMSE do 0,07 wobec < 0,001) — otoczenie startu
  w C zmieniło się (pawilon, las); pozycja ciężarówki na `truck-at-gate` ta sama.

## Do commita weszło
`generated/` C i Dojlid, `buildings.geojson` + `build_manifest.json` obu regionów, manifesty far_field, trasa Nav C,
baseline 0238 (2 pliki). Cofnięte jako efekty uboczne: `materials_spec.json` (`png_bytes` lokalnego kodera),
hash `region.yaml` w `build_manifest.json` Dojlid (CRLF), `region.yaml` Dojlid (`manifest_sha256`). Po Unity brak
diffu w `Rendering/` i `ProjectSettings/`.

## Otwarte
1. `visual-critic` i porównanie ze zdjęciami właściciela — niewykonane (agent nie tworzy subagentów).
2. Przejście P-10 przy węźle 2882674807 pominięte po #93 — sprawdzić, czy zgodne z terenem.
3. Wyspa Putry bez pasa żwiru z ortofoto (cała trawa).
4. Test budżetu 0238 po przebudowie liczy #123 podwójnie w szacunku per kamera (patrz analiza) — baseline trzeba
   przeliczać po każdej zmianie generatora budynków albo danych.
5. Kamery MA-010 `au_r_s1160` i `ortho_putry` z warunku recenzji #93 nie były renderowane (nie ma ich w zestawie
   kontrolnym VQA); Putry oceniony na `putry-above` i `g3b_rondo_put_above`.
6. Zapas C `stretch_04`: 14 540 trójkątów. `dk8_dk19_exit` urósł o 12 001 High po #119 — przy kolejnych zmianach lasu obserwować.
7. OD-005: wpis `dk8-seam-kerb-od005-c` czeka na przebudowę C (sekcja wyżej).
8. Stary #93 zamknąć jako zastąpiony gałęzią `-rebased` (lider / właściciel).

## Komenda scalenia
```
git -C C:\Users\matma\Documents\Claude\kamion merge --no-ff origin/c-regen3-s23
```
Przed usunięciem worktree: `robocopy` dowodów już wykonane do `artifacts\c-regen3-s23` w main; junctions odpiąć
`cmd /c rmdir`; `Data/raw/derived/_c-regen3-run1` (kopia pierwszego przebiegu, 1,4 GB) usunięta razem z worktree.
