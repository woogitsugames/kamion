# Integracja 2026-11-15 — druga wspólna przebudowa C i Dojlid (c-regen2-s23), ETAP 1: przygotowanie

Gałąź `c-regen2-s23` z main `7e044ac0a`. Etap 1 = scalenia, lekkie testy, skrypty etapu 2. **Nic ciężkiego nie było
uruchamiane**: bez Unity, bez `build_world` / `build_region`, bez pełnego pytest. `generated/` C i Dojlid = main.

## Decyzje dla lidera przed etapem 2
1. **#123 typology-0238 nie jest scalony** (werdykt FIX, head bez zmian od recenzji). Wspólna przebudowa nie obejmie
   typologii, więc po poprawkach #123 będzie potrzebna kolejna przebudowa C i Dojlid — albo lider zleca 3 poprawki P1
   (niżej) w tej gałęzi przed etapem 2.
2. **#119 tests-hygiene-0245 nie jest w main** (`git merge-base --is-ancestor origin/tests-hygiene-0245 origin/main` = 1).
   Recenzja każe scalić go przed przebudową C, bo zmienia strumień losowy płaszcza lasu. Nie było go w zadaniu — nie
   scalony. Jeśli wejdzie po etapie 2, las C zmieni się przy następnej przebudowie.
3. **„Before” z main wymaga świeżej budowy.** W main `Data/raw/derived/bialystok-industrial-c` (glb 15.11 16:54) i scena
   `_Generated/.../WorldC.unity` (16:59) są starsze niż zacommitowane `generated/` (regeneracja c-regen-s22 20:48–21:15
   odbyła się w usuniętym worktree). `10-before.ps1` domyślnie buduje i importuje stan main (ok. 55 min); tańsza opcja
   `-Mode Reuse` bierze rendery `artifacts/c-regen-s22/after` (ten sam stan świata, ale bez Low overcast i kamer G3,
   sprzed spawn-fix 0262).

## PR → sha → werdykt → scalenie → testy
Wszystkie heady = sha z recenzji (0 nowych commitów do przejrzenia). Żaden z 7 PR nie zmienia `ProjectSettings/`,
`Packages/`, asmdef, scen, prefabów ani `generated/` (lista plików względem merge-base sprawdzona dla każdego).
#110 zmienia assety tierów `QualityProfile.asset` i `URP_Low.asset` (migracja `revision 240`) — `setup-project` robi lider.

| PR | gałąź | head = recenzja | werdykt | w gałęzi | merge commit | testy po scaleniu (ten worktree) |
|---|---|---|---|---|---|---|
| #109 | fences-0239 | `684f9b5c4` tak | SCAL | tak | `9c8ab51a0` | `test_dojbld_0185`, `test_furniture_0120`, `test_furniture_r1`: 33 passed (uruchomione na drzewie po scaleniu #110) |
| #110 | shadows-0240 | `79830f024` tak | SCAL | tak | `3d4144f9e` + fix `68c3c0740` | `thin_shadow_audit.py --check`: exit 1 → po poprawce exit 0 (155 prototypów, 48 thin, 0 niezgodności) |
| #111 | gpu-ab-0241 | `df5acb73b` tak | SCAL | tak | `72ce5ed05` | `tools/perf/tests`: 61 passed |
| #123 | typology-0238 | `243b3065b` tak | **FIX** | **nie** | — | — |
| #124 | signs-c-0236 | `174826435` tak | SCAL | tak | `f8095bf20` | 6 plików (0236, gate3_landmarks, g3b_lowread, g3b_r2, furniture_0162, budget_0221): 70 passed, 1 skipped (oczekiwany do przebudowy); `test_streetscape.py` (na końcowym drzewie): 58 passed, 1 skipped (instancje świata niezbudowane w worktree) |
| #125 | kerbs-0237 | `7ab4dc2d8` tak | SCAL warunkowo | tak | `71c4e83bf` + hak `4ee4f646a` | `-k "pavements or cycleways or fab_details or yard_wear or plots or paved or bus_stop or cc0"`: 88 passed, 1 skipped (447 s) |
| #122 | dojlidy-0242 | `4e845e768` tak | SCAL | tak | `f06f372bd` | zestaw końcowy — patrz niżej |

Kolejność scalenia: #109 → #110 → #111 → #124 → #125 → #122 (każdy `--no-ff`, `STATUS.md` = main). #93 nie włączony.

**Zestaw końcowy na `f06f372bd`** (16 plików testów wszystkich scalonych PR + sąsiednich 0216/0221):
**192 passed, 3 skipped, 0 failed** (48 s). Skipy oczekiwane do etapu 2: `test_gate3_landmarks.py:143` (świat nieprzebudowany z ADR 0236),
`test_yard_wear.py:217` (świat niezbudowany w tym worktree), `test_dojind_0196.py:90` (tekstury PBR niewygenerowane w tym worktree).
Regresji brak; znane czerwone testy main (forest_0187, road_fidelity, world_v31) nie były w zestawie — pełny pytest to krok 4 etapu 2.
`python scripts/export-region-catalog.py --check`: exit 0. `overrides.yaml` po scaleniach: C 190 wpisów, Dojlidy 47,
YAML poprawny, 0 zduplikowanych id (jak w recenzji).

### Rozwiązane konflikty
- `STATUS.md` w każdym z 6 scaleń → wersja main.
- `docs/PERFORMANCE_BUDGETS.md` (#109 × #111) → obie sekcje (ADR 0239, potem ADR 0241).
- `overrides.yaml` C i Dojlid (#125 × blok 0216b z main) → suma bloków.
- Automatyczne, przejrzane: `RegionImporter.cs` (#109 × #110: `_LowNoShadow`/`IsThinMaterial` l. 308 i shader siatki
  l. 462 — jak w recenzji), `RenderOverrides.cs` (#110 × #111: `ThinShadows` + `GpuAbOverrides`, `CurrentRevision = 240`),
  `WorldPbrMaterials.cs` (#125 `BlockPavingElementSize` × #122 `RunoffStrengthScale` — różne miejsca),
  `test_dojbld_0185.py` (#109 × #122), `stage.py`, `materials.py`, `furniture.py`, `props.py`.

### Poprawki w gałęzi integracyjnej (osobne commity)
1. `68c3c0740` — **konflikt logiczny #110 × #120** (nie było go w recenzji): `thin_shadow_audit.py --check` zwracał
   exit 1 z niezgodnością `lamp_old_concrete_led_9m`. To prototyp dodany do main przez 0216b po napisaniu #110; ten sam
   słup co `lamp_old_concrete_9m`, który jest już wyjątkiem rodzinnym. Dopisany do `FAMILY_EXCEPTIONS` (tylko audyt
   Pythona; reguła C# łapie go prefiksem `lamp_`).
2. `4ee4f646a` — **hak `build_world` z #125** (warunek recenzji P1-L). `git apply --check` łatki
   `docs/adr/0237-build-world-hook.patch` nie przeszedł: hunk 3 stracił kontekst po scaleniu tunelu 0211 do main.
   Trzy hunki nałożone ręcznie w miejscu autora (po logu `hero bridges`, przed `TN.build`). Bez haka chodniki
   zostałyby szarą kostką, a czerwony pas w Dojlidach trafiłby do `overrides_stale`.

### Co blokuje #123 (do wklejenia autorowi)
- **P1** `tests/gis/test_typology_0238.py:305` ma wpisane `2022535`; `streetscape_qa.json` w main ma dla `stretch_04`
  1 986 314 → test pada. Zastąpić porównaniem z wartością z QA.
- **P1** baseline `tests/gis/data/typology_0238_baseline_bialystok-dojlidy.json` policzony przed #122 → przeliczyć
  harness'em na tej gałęzi (zawiera #122).
- **P1** konflikt `buildings_mesh.py:storey_plan` z #122 (potwierdzony `git merge-tree` na tej gałęzi; do tego
  `docs/LICENSES.md` i `STATUS.md`): zostawić `storeys_fixed` z #122, usunąć jego linię `lo, hi = …`.

## Konflikty logiczne między PR-ami — wynik lektury
- **#125 × #124:** `stage.py` (+5 i +1 linia) w różnych miejscach; krawężniki zmieniają wysokości istniejących stacji,
  znaki stoją na pozycjach z overrides. Odsunięcie tablicy `max(1.2, wm/2 + 0.5)` (#124) względem obniżonego
  krawężnika jest niesprawdzone — do obejrzenia na renderze (`route_putry_entry_signs`, `driver_andersa_to_putry`).
- **#125 × budget-fix 0221:** decymacja obrzeży obejmuje nowe materiały `EDGED`; `test_budget_0221` zielony.
- **#125 × tunel 0211:** hak działa przed `TN.build`. W regionie z tunelem części chodnika przycięte przez tunel mogą
  stracić `export_mat` — UNVERIFIED, nie dotyczy C ani Dojlid (bez tunelu), dotyczy Kleeberga przy jej przebudowie.
- **Hak #125 jest opt-in:** `PVM.run` zwraca `{"enabled": false}`, gdy region nie ma override `pavement_rules`
  (`pavements.py:369`). Reguły mają tylko C i Dojlidy, więc inne kafle (DK65, Knyszyn) budują się jak dotąd.
- **#109 × #110:** siatka płotu nie rzuca cienia przez #109, słupki przez #110; obie reguły działają dopiero po reimporcie.
- **#124 × #110:** #124 zmienia prototypy bramownic i tablic → audyt cieni powtórzyć po przebudowie (krok w `20-regen.ps1`).

## Ryzyka dla budżetu C < 2 M High (stan: `stretch_04` 1 986 314, zapas 13 686)
Liczby per PR to szacunki z recenzji (ESTIMATED), nie pomiar; `30-budget.py` policzy je po przebudowie.
1. **Brak kompensacji z #123.** Recenzja liczyła sumę ≈ 1 985 397 z #123 (−693). Bez niego: `stretch_04` ≈ 1 986 090
   (tylko #124 −224), `route_onramp_andersa_above` ≈ 1 966 437. Limit zachowany, zapas ok. 13,9 tys.
2. **Low rośnie bez #123:** słupki E-15 z #124 dają +40/+48 Low na 3 kamerach (ESTIMATED), dużo poniżej progu +2 %.
3. **`fire_station_abeam` +448 High** (#124) — kamera ma 1 170 958, bez ryzyka.
4. **#125 = 0 trójkątów z konstrukcji** (`pavements.run` przerywa build przy różnicy). Ryzyko jest w drawach: +1…3
   submeshe na kafel (`sidewalk_paving_red`, `sidewalk_slabs`, `path_asphalt`); `stretch_04` ma 153 materiały High.
5. **#122 nie zmienia C** (autor: SHA-256 siatek identyczne); Dojlidy LOD0 −738 (zapas Dojlid 231 972).
6. **Późniejsze scalenie #123** doda wpływ `BASE_M` 1,5 po `build_region` (liczba kondygnacji → pasy okien) — UNVERIFIED,
   zmierzyć wtedy osobno; przy zapasie 13,7 tys. to największe ryzyko przekroczenia 2 M.
7. **Późniejsze scalenie #119** zmieni las (UNVERIFIED, wg recenzji szum).
8. **Tekstury #125:** +2,49 MB ASTC High (`paving_20x10_tint`), behaton 1024 × 1264 NPOT (+0,58 MB) — pamięć, nie
   trójkąty; do zmierzenia na telefonie (poza zakresem).
9. `far_field` nie wchodzi do `frame_estimate`; limit testu Low ≤ 30 000 (C 25 389, Dojlidy 23 907) — żaden PR go nie dotyka.
10. `frame_estimate` to szacunek generatora; trójkąty edytora (`stats.txt`) porównać w parach before/after.

## Etap 2 — komendy (NIE uruchomione)
Skrypty: `artifacts/c-regen2-s23/tools/` (w gicie na gałęzi). Każdy pisze `<krok> exit=<kod> try=<n> <czas>` do pliku
statusu; kod −1073741502 jest ponawiany do 3 razy; znacznik `.done` nie jest dowodem — czytać `exit=`.
Bramki między krokami: 20/40/50/60 przerywają pracę, gdy worktree nie jest na gałęzi `c-regen2-s23`; `20-regen.ps1` nie
pisze `regen.done`, gdy `build_world` albo budżet nie mają `exit=0`; `40-unity.ps1` czyta te linie z `regen.status`
(`-Force` = lider świadomie akceptuje czerwony budżet). Ponowienie działa też, gdy kod −1073741502 jest tylko w logu
(`import-region.ps1` i `visual-qa.ps1` zwracają wtedy 1). Helpery sprawdzone testem na sucho w katalogu tymczasowym.
**W trakcie `10-before.ps1` (tryb Fresh) nie commitować i nie pisać live w worktree** — drzewo stoi na sha main, a
skrypty i plik live (śledzone tylko na gałęzi) na ten czas znikają z dysku; krok czeka na slot jeszcze na gałęzi.
Uruchamianie odłączone (wzór), po kolei, każdy następny po `DONE` poprzedniego:

```powershell
$t = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\c-regen2-s23\artifacts\c-regen2-s23\tools'
Start-Process pwsh -WindowStyle Hidden -ArgumentList '-NoProfile','-File',"$t\00-prep.ps1"
Start-Process pwsh -WindowStyle Hidden -ArgumentList '-NoProfile','-File',"$t\10-before.ps1"            # albo: ,'-Mode','Reuse'
Start-Process pwsh -WindowStyle Hidden -ArgumentList '-NoProfile','-File',"$t\20-regen.ps1"
Start-Process pwsh -WindowStyle Hidden -ArgumentList '-NoProfile','-File',"$t\40-unity.ps1"
Start-Process pwsh -WindowStyle Hidden -ArgumentList '-NoProfile','-File',"$t\50-pytest.ps1"
```

| krok | skrypt | slot | co robi | status | czas |
|---|---|---|---|---|---|
| 0 | `00-prep.ps1` | — | robocopy z main: całe `Data/raw/derived` (14,5 GB; w korzeniu leżą cache warstw `*.pkl`), `game/Assets/_Generated` (13,3 GB), `game/Library`; kontrola junctions i megascans | `prep/prep.status` | UNVERIFIED (kopiowanie ponad 30 GB) |
| 1 | `10-before.ps1` | heavy, potem unity | checkout bazy main (detached) → `build_world` C + Dojlidy → import → macierz VQA → powrót na gałąź | `before/before.status`, `before/vqa.status` | ok. 55 min WORKING_VALUE (20 + 23 + rendery; czasy s22) |
| 2 | `20-regen.ps1` | heavy | `build_region` → `build_world` → `fidelity` → `export-route` → audyt lamp, C potem Dojlidy; cofnięcie `manifest_sha256` w `region.yaml`; katalog regionów; audyt cieni; `30-budget.py` | `regen/regen.status` | 27 min w s22 (C: 12 s + 12 min + 4 min 22 s; Dojlidy: 7 s + 8 min + 2 min 18 s) |
| 3 | `40-unity.ps1` | unity | EditMode (bramka kompilacji, werdykt z XML) → import C → import Dojlidy → macierz VQA after | `unity/unity.status`, `after/vqa.status` | EditMode 2 min, import C 13 min, Dojlidy 10 min (s22) + rendery |
| 4 | `50-pytest.ps1` | heavy | pełny `pytest tests/gis` + `tools/perf/tests` | `regen/pytest.status` | 32 min w s22 |
| 5 | `60-postmerge.ps1` | heavy | tylko gdy main zmienił kod świata: `build_world` + `fidelity` × 2, budżet, wybrane pytest | `postmerge/postmerge.status` | 23 min w s22 |
| — | `70-ab.ps1 -Region <id> -Cell Low-clear [-Cameras a,b]` | — | pary before\|after JPG + RMSE + `stats.txt` | `view/ab_*.jpg` | sekundy |

Macierz VQA (`vqa.ps1`): oba regiony × Low clear / Low dusk / Low overcast / High clear / High dusk (pełne zestawy
kamer kontrolnych) + C Low clear z `-Gate3` i kamerami `g3a_eye_s0412, g3b_eye_s1682, g3a_eye_s0212, g3b_eye_s1282,
g3b_eye_s1482`; po przebudowie dodatkowo te same kamery z `-Rq 'rq_thinshadow=1,rq_shadowbias=1,rq_shadownormal=1'`
(A/B ADR 0240 na jednym imporcie). 8 komórek trwało w s22 3,5–4,7 min; tu 11–12 komórek (czas WORKING_VALUE ok. 6–8 min).
Nazwy kamer sprawdzone w `control_cameras.json` / `gate3_cameras.json`. Kamery `r10_fence_*` z opisu #109 nie istnieją —
płot oglądać na `kwadrat_park_gate` i `truck-at-gate`.

Import sam zbuduje tekstury PBR: `import-region.ps1` uruchamia `cc0_fetch.py` i pełny `build_all.py`, gdy brakuje
plików albo `_src/*.py` jest nowsze od PNG. Tu jest to zamierzone (#125 dodaje zestawy `paving_20x10_tint`,
`sidewalk_slab_35` i zmienia behaton); wg nagłówka skryptu ok. 4 min (UNVERIFIED). `cc0_fetch.py` pobiera skany CC0
(sieć).

### Kontrole po kroku 2 (robi `30-budget.py`, exit 1 = czerwono)
`tris_high < 2 000 000` na każdej kamerze · Low ≤ +2 % · `far_field` Low ≤ 30 000 · `pavements.tris_in == tris_out` ·
raport `pavements` obecny (hak zadziałał) · `furniture.gate3_landmarks.stale` puste · `diagrams_replaced` obecne w C
(wtedy `test_every_gate3_sign_is_placed` wykona się, nie skip). Wypisuje też `pavements.overrides_stale` (pas czerwonej
kostki P11-063 ma `confidence: low`), `crossing_kerb`, rodziny lamp, liczbę materiałów manifestu.
Skrypt sprawdzony na obecnych danych: delty 0 na 23 + 17 kamerach, czerwony na trzech brakach oczekiwanych przed przebudową.

### Do commita po etapie 2
`Data/Regions/{C,Dojlidy}/generated/**`, `route_start.json`, `art-source/world/props/props_meta.json` +
`street_props.glb` (#124 zmienia prototypy), manifesty far_field, ewentualnie `region_catalog.json`. Bez
`region.yaml` (CRLF), bez efektów ubocznych Unity. Dowody: `robocopy artifacts\c-regen2-s23 <main>\artifacts\c-regen2-s23 /E`
przed usunięciem worktree; junctions odpiąć `cmd /c rmdir`.

### Kroki tylko dla lidera
- `pwsh scripts/setup-project.ps1` po scaleniu (#110): oczekiwany brak diffu `QualityProfile.asset` / `URP_Low.asset`.
- Oględziny par i `visual-critic` (rendery etapu 2), ocena kratownicy LOD1 na Low (#124 P1-L), acne przy biasie 0,4/0,3 (#110).
- APK i pomiar A16 (cienie, płot, A/B GPU, PSS po teksturach #125) — bez telefonu w tym zadaniu.

## Otwarte (P2 z recenzji, nie ruszane)
- #111: wariant `thinshadow-on` w `gpu-ab-variants.json`; ujednolicenie kamer A/B z #110.
- #124: zawęzić skip `test_gate3_landmarks.py:142` do 4 nowych E-15 (po przebudowie skip znika sam).
- #125: plik `docs/adr/0237-build-world-hook.patch` został w repo (ADR 0237 l. 86 się do niego odwołuje) — po tej
  gałęzi jest zbędny; próg `test_yard_wear.py:38`; NPOT behatonu.
- #109: przejście `DepthNormals` (SSAO Ultra); log mipów `fence_mesh.png`.
- #122: data nalotu NMPT, bramy 5,9 × 6,6 m — do oceny na `photo_P11-094`.
- Lekkie testy z `-k` na całym `tests/gis` trwają tu ok. 7,5 min (kolekcja 1650 testów) — w etapie 2 podawać pliki.

---

# ETAP 2 — wykonany (16.11, łańcuch lidera `stage2-chain.ps1`, potem poprawki i ponowne rendery)

Gałąź `c-regen2-s23` zawiera main `6e6fe972f` (merge `4129c4297`; z main przyszły tylko dokumenty, `rail_bed.png`
i 3 pliki C# spawn-fix r2 — zero kodu świata, więc `60-postmerge.ps1` nie był potrzebny). #123 i #119 nadal poza gałęzią.

## Przebieg (wszystkie kroki z `exit=` w plikach statusu)
| krok | wynik | czas |
|---|---|---|
| `00-prep` | exit 0 po poprawce lidera (`$derived` jako tablica; commit `ae761cca4`) | 1 min 38 s |
| `10-before -Mode Reuse` | rendery `c-regen-s22/after` jako before (bez Low overcast i kamer G3) | sekundy |
| `20-regen` | 13 kroków exit 0; `build_world` C 9 min 47 s, Dojlidy 7 min 21 s; budżet exit 0; audyt cieni exit 0; `region.yaml` Dojlid cofnięty (tylko `manifest_sha256`) | 24 min 46 s |
| `40-unity` | EditMode 788: 785 passed, 2 failed (oba znane `CarPaintMaterialTests.DepositionChannel_*`), 1 skipped; import C exit 0 (12 min 18 s), Dojlidy exit 0 (9 min 54 s); 12 komórek VQA exit 0 | 30 min |
| `50-pytest` (1. przebieg) | 1650 passed, **3 failed**, 3 skipped, 2 xfailed (985 s); `tools/perf/tests` exit 0 | 16,5 min |
| ponowne rendery po poprawce shadera | 12 komórek exit 0, 0 błędów shadera w logach | 5 min 16 s |
| `50-pytest` (2. przebieg, po poprawkach i merge main) | **1653 passed, 0 failed**, 3 skipped, 2 xfailed; `tools/perf/tests` 61 passed | 17 min 26 s |
| `45-editmode` (po poprawce shadera i merge main) | 788: 786 passed, **1 failed** (`StreetLampOpticsTests.SodiumTint_HasTheLedLuminance`), 1 skipped; oba testy CarPaint tym razem zielone | 2 min 28 s |

Nowe testy EditMode z PR-ów (pierwsza kompilacja tego C#): `FenceMeshCoverageTests` 23/23, `ThinShadowCasterTests` 57/57,
`GpuAbOverridesTests` 19/19, `LightPostPolicyTests` 12/12, `WorldPbr*` 19/19. Efekty uboczne Unity: brak diffu w
`game/Assets/_Project/Rendering` i `ProjectSettings` po przebiegu (`unity/unity-side-effects.diffstat.txt` pusty).

## Budżet (zmierzone, `regen/budget.log`)
| | przed | po | zapas / limit |
|---|---|---|---|
| C `stretch_04` High (`frame_estimate`) | 1 986 314 | **1 985 807** (−507) | 14 193 do 2 M |
| C `stretch_04` Low | 938 349 | 938 274 (−75) | |
| C `route_onramp_andersa_above` High | 1 966 981 | 1 966 411 (−570) | |
| C największy wzrost Low | | `stretch_03` +282 (+0,05 %) | próg +2 % |
| C materiały `stretch_04` High | 153 | 155 | budżet draws 800 |
| Dojlidy max High (`photo_P11-063`) | 1 768 028 | 1 768 010 | 231 990 |
| Dojlidy największy wzrost | | `route_s1675` +270 High, +0,07 % Low (`route_s1980`) | |
| far_field Low C / Dojlidy | 25 389 / 23 907 | bez zmian | ≤ 30 000 |
| materiały manifestu (oba regiony) | 331 | 336 | |
| edytor `stretch-04` High / Low (`trisExact`) | 1 067 263 / 312 831 | 1 067 394 / 312 956 | draws 1085 / 463 bez zmian |

- Spadek w C to kategoria `props` (bramownice i tablice z #124: `stretch_04` −772, `g3b_eye_s1482` −2 128).
- **Niezgodność z szacunkiem recenzji #125 („0 trójkątów”):** `roads` +4…+178 i `terrain` do +174 na kamerę w C
  (`stretch_04` +159 / +106). `pavements.tris_in == tris_out` (C 15 979, przemianowanie materiału nic nie dodaje), więc
  przyrost pochodzi z obniżeń krawężników na przejściach (`plots.crossing_kerb`: C 25 obniżonych z 90 przejść, Dojlidy
  16 z 85) — przyczyna wskazana z rozkładu kategorii, nie zmierzona osobno. Skala: poniżej 0,02 % kadru.
- `pavements`: C `path_asphalt` 240 m², kostka 24 460 m², 0 nieaktualnych override; Dojlidy czerwony pas
  `mickiewicza-kuronia-red-block-strip` zastosowany (64,6 m², 32 trójkąty), 0 nieaktualnych.
- `gate3_landmarks.stale` puste w obu regionach; `diagrams_replaced` w C: regułowa E-1 `E-1_79161` zastąpiona przez
  portal p40 (8,4 m).
- Cienie Low (#110), ten sam import, A/B przełącznikami (`stats.txt`): `g3a_eye_s0412` 19 → 5 drawów casterów
  (3 230 → 2 596 trójkątów), `g3b_eye_s1482` 12 → 1 (2 272 → 28), `g3b_eye_s1282` 10 → 3, `g3b_eye_s1682` 20 → 14.

## Błędy znalezione przez przebudowę i poprawione w gałęzi
1. **P0 — płot z siatki renderował się na magenta** (#109, commit `a2a5dfa64`). `FenceMeshForward.hlsl` wołał
   `IsAlphaToMaskAvailable()`, a URP 17 deklaruje tę funkcję tylko pod `_ALPHATEST_ON`, którego ten pass celowo nie
   kompiluje (28 błędów „undeclared identifier” w logach VQA; EditMode tego nie łapie, bo testy czytają plik, nie
   kompilują shadera). Zastąpione globalem `_AlphaToMaskAvailable != 0.0`. Pierwsze rendery zostały jako dowód w
   `artifacts/c-regen2-s23/after-r1-magenta/`; `after/` to rendery po poprawce.
2. **3 testy czerwone po przebudowie C** (#124, commit `6a337b125`) — wszystkie to testy niedostosowane do stanu po
   przebudowie, nie błędy generatora:
   - `test_direction_signs_0236.py:304` — `KeyError`: prototypy bramownic w bibliotece zmieniły nazwy
     (`sign_gantry_14_61_b6` → `14_62_b6`, `sign_cantilever_L8_86` → `L8_72`); test porównuje teraz z biblioteką w gicie.
   - `test_streetscape.py:290` — zestaw landmarków nie znał nowej bramownicy `andersa-putry-e1-advance-gantry`.
   - `test_world_v34.py:139` — żadne rondo trasy nie miało już regułowej E-1; test uznaje E-1 przejętą przez
     bramownicę z `diagrams_replaced`. Otwarte: `route_checks` w generatorze nadal nie liczy tablic na bramownicach.
3. Trzy „znane czerwone” testy main (forest_0187, road_fidelity, world_v31) w tym worktree **przeszły**.
   Skipy: 2 × `test_dk65_seam_knyszyn_0233` (GLB dk65-11 starsze niż overrides — inny region), 1 × 0236 (oczekiwany).

## Oględziny before | after (pary w `artifacts/c-regen2-s23/view/`)
Obejrzane przeze mnie; **bez `visual-critic` i bez porównania ze zdjęciami właściciela** — to zostaje dla lidera.
- **Płoty #109** (`kwadrat-park-gate`, `kuronia2-front`, `photo-P11-001`, Low i High): po poprawce shadera siatka jest
  równą, drobną kratą zamiast porwanych poziomych kresek. Na Low z bliska widać ziarno szumu (kropkowanie) — do oceny
  w ruchu. Palisada i słupki bez zmian.
- **Cienie Low #110** (`g3a_eye_s0412`, A/B na jednym imporcie): znikają porwane plamy cienia głowic latarni na
  jezdni; cień wiaduktu i bariery zostaje. Na `route-putry-entry-signs` nie ma już cieni masztów sygnalizacji.
  Acne na ścianach hal przy biasie 0,4/0,3 nie zauważyłem na obejrzanych kadrach (nie mierzone).
- **Drogowskazy #124** (`g3b-eye-s1482`): wysięgnik p37 ma teraz E-1 ze schematem skrzyżowania 4,6 × 1,85 m zamiast
  listy 5 wierszy 4,6 × 3,3 m. **Na Low napisy są z tej odległości nieczytelne** (wcześniej czytelne). Zgodne ze
  źródłem R2-081, ale to ryzyko dla rozpoznawalności G3b — do oceny krytyka. Kratownica LOD1 nadal czyta się jako kratownica.
- **Krawężniki / chodniki #125**: na obejrzanych kadrach (`route-putry-entry-signs`, `photo-P11-063`) nie widzę różnicy
  nawierzchni ani obniżeń; czerwony pas P11-063 potwierdzony tylko w QA (`overrides_applied`), nie wzrokiem.
- **Dojlidy #122** (`kuronia2-front`, `photo-P11-001`): K3 wyższy, szara okładzina kasetowa z pasami okien zamiast
  ciemnej attyki; hala przy Kuronia wyższa (18,92 m). Brak dziur i brakujących obiektów.
- Zastrzeżenie do par: before pochodzi z s22 (inna pozycja startu ciężarówki po spawn-fix 0262 wpływa na `truck-at-gate`).

## Do commita weszło
`generated/` C i Dojlid, manifesty far_field, `props_meta.json`, `street_props.glb`, tablice znaków (4 nowe PNG).
Cofnięte jako efekty uboczne: `materials_spec.json` (inne `png_bytes` lokalnego kodera PNG), `build_manifest.json`
Dojlid (hash `region.yaml` z CRLF), `viaduct_putry_underdeck.spec.json` (same końce linii).

## Gotowość
**Gotowe do scalenia: TAK pod względem kodu, testów i budżetu** (pytest 1653/0, budżet zielony, katalog regionów
`--check` 0, drzewo czyste). Zastrzeżenia, o których decyduje lider:
1. **EditMode po imporcie: 1 fail** `StreetLampOpticsTests.SodiumTint_HasTheLedLuminance` (oczekiwane 0,93694, jest
   0,94206). W pierwszym przebiegu (przed importem regionów w tym worktree) ten sam test przeszedł, a gałąź nie zmienia
   kodu latarni. Test porównuje ze stałym kolorem LED, a `StreetLamps.SetLedColour` zmienia stan statyczny — wygląda
   na zależność od profilu oświetlenia 0216b / kolejności testów (hipoteza, niesprawdzona na czystym main).
2. **Bez `visual-critic` i bez zestawienia ze zdjęciami właściciela.** Do oceny przede wszystkim czytelność E-1 na
   wysięgniku p37 na Low (#124) i ziarno siatki płotu na Low (#109).
3. Before = rendery s22 (tryb Reuse): brak pary dla Low overcast i kamer G3; cienie #110 porównane przełącznikami.
4. `setup-project` (#110), APK i pomiar A16 — kroki lidera, niewykonane.
5. #123 (FIX) i #119 nie weszły — następna przebudowa C zmieni budynki (`BASE_M` 1,5) i las; zapas `stretch_04` to 14 193.