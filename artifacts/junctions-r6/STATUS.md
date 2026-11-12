# STATUS — junctions-r6 (ADR 0123: węzły r6, zamknięcie pkt 4 bramki 3 „bariery”; wg REVIEW-2026-11-11-s10-0117 „Lista na r6”)

Gałąź `junctions-r6` (z main 3540bbdf). Dowody: `artifacts/junctions-r6/` (renders_<tag>_<tier>_<światło>, logs, scripts, ortho, refs).

- krok 0 (baseline m0 = main 3540bbdf zregenerowany w tym worktree: build_world 21:22–21:30, import 21:44): `renders_m0_low_clear/`,
  `renders_m0_high_overcast/` (102 kamery, `stats.txt`); Low overcast / High clear w kolejce do slotu Unity.
  Uwaga: import m0 skompilował już importer z uśpionymi dodatkami r6 (`cast_shadows`, `vertex_grime`, `set_metal` — bez kluczy w manifeście
  m0 nic nie zmieniają); zestawy PBR m0 zbudowane ze starego `sets_facade.py`.
- krok 1 (kod, build b1 zrobiony 21:56 bez pkt d–f): 
  a) cień poręczy: manifest `viaduct_steel.cast_shadows: false` → `RegionImporter.CreateMaterial` wyłącza pass ShadowCaster;
  b) ocynk: `barrier_galv` MaskMap.r = maska metalu (cynk 1, brud/rdza 0), rough 0,56; `barrier_steel` 0,50 / metal → `set_metal` 0,9
     (WORKING, do kalibracji w kadrze); c) kapa: `bridge_concrete.vertex_grime` + COLOR_0.r na wierzchu kapy (`_VERTEX_GRIME` w
     Kamion/World PBR, bez nowego materiału / draw calla), lico bariery 0,70 → 0,42 m za licem krawężnika (pomiar w GLB: `xsec_glb.py`);
  d) `p0_kerb_merge_eye`: koniec bariery POMOSTU nie jest już dociągany do sąsiedniej (zygzak 2,5 m), druga szyna separatora
     `dk8-ramp-split-barrier-n` wg ortofoto, szyny autorskie nie deduplikują się nawzajem;
  e) nos Putry N: kołnierz z kostki na całą szerokość końca mediany + cięcie pasów trawy na obrysie wyspy (`gores._clip_tris`);
  f) murek `r2_fork_link_eye`: kołnierz betonowy na styku „pas trawy / brak pasa” → skarpa z trawy (w siatce terenu);
  g) RING-B: „2 propy na fartuchu” = latarnie `lamp_12m` na POMOŚCIE (z 145,84 / 145,95; rondo ~140) — analiza 2D; ortofoto: latarnie
     dwuramienne stoją między pomostami → `bridge_style.lamps: median` (`furniture.bridge_median_lamps`), a `swept_path_gate3.py`
     pomija propy > 4,5 m nad jezdnią; h) filary Bieżeństwa: rzędy z pomiaru (`pier_lines_en`: rząd przy każdej krawędzi wyspy,
     bez rzędu w środku), bariera przy filarze liczy fartuch jako jezdnię (stoi za krawężnikiem wyspy).
  NASTĘPNY KROK: `bash artifacts/junctions-r6/scripts/loop.sh b2` (po zakończeniu renderów m0) → `bash artifacts/junctions-r6/scripts/imp.sh b2`
  → `python artifacts/junctions-r6/scripts/stats_cmp.py artifacts/junctions-r6/renders_m0_low_clear/stats.txt artifacts/junctions-r6/renders_b2_low_clear/stats.txt`
- krok 2 (b2, 22:04–22:33; build + import + rendery Low clear / High overcast, 102 kamery; `renders_b2_*`):
  budżet vs m0 (`stats_cmp.py`): Low clear max **+0 draws**, tris max +0,7 %; High overcast +0 / +0,8 %. Fidelity p50 0,36 / p95 2,304 (= main).
  Kluczowe testy (`test_junctions_r4, test_hero_bridge, test_gores, test_streetscape, test_world_roads, test_lane_edges`): 110 passed.
  Swept b2: NIE zmierzony (rc 127, pusty log — powtórzyć). Swept m0 = main (RING-B prop 1,31 / 1,79).
  Zmierzone w GLB (`xsec_glb.py 490 -674.6 -0.906 0.424 9 1.2 144 152`): lico krawężnika → lico taśmy 0,65 → ~0,45 m; oś linii
  krawędziowej → lico 1,02 → ~0,85 m. Murek `r2_fork_link_eye`: zniknął (`walls_at.py -350,-136,9`: brak `…:L:7`), jest skarpa z trawy.
  RING-B: latarnie z pomostu przeniesione między pomosty (10 podwójnych, 15 usuniętych), przy wyspie zostają 2 instancje (jedna para).
  Filary: rzędy przy krawędziach wyspy, `guardrails_m.pier` 132 → 172 m; w `r4_pier_bz` bariera jest w kadrze (lewy dół), filara nadal nie
  ma (stoi poza kadrem — żeby wszedł, kolumny musiałyby stać ~3,5–4 m od osi pomostu = przebudowa spodu wiaduktu, domena GPT).
  Luminancja sRGB / asfalt (`lum_set.sh`; zdjęcia: taśma 1,47 pochm. / 1,53 słońce / 0,58 cień; kapa 1,48 / 1,43–1,56; krawężnik 1,40 / 1,35):
  m0 taśma 1,36 (Low clear) / 1,18 (High overcast), kapa 1,64 / 1,77; b2 (metal 0,9) taśma 1,43–1,48 / 1,51–1,64, w cieniu 0,98 (za jasno).
  USTALENIA: (1) szachownica na kapie = cień PORĘCZY assetu (nie bariery); URP przy walidacji materiału Lit z powrotem włącza pass
  ShadowCaster, więc flaga idzie do `WorldInstanceSet.noShadowMaterials` (InstanceImporter / WorldInstances) — KOD JEST, jeszcze NIE
  zaimportowane ani obejrzane; (2) taśma: dodane `shadow_low: false` (`_LowNoShadow`, bariera nie rzuca cienia na Low) — do oceny po
  imporcie, czy potrzebne; (3) krawężnik pomostu jaśniejszy od kapy → eksport jako `bridge_kerb` (0,19; bez nowego draw calla) — kod jest,
  niezbudowane; (4) `p0_kerb_merge_eye`: szyna N skrócona do końca wyspy (E −756), bo nad niższym gruntem nurkowała; nadal bałagan przy
  początku pomostu łącznicy — CZĘŚCIOWO; (5) nos Putry N: kołnierz zamyka czarną szczelinę, ale od północy widać lico krawężnika wyspy
  ~0,15–0,2 m nad niższym poboczem — CZĘŚCIOWO. Iteracja materiału na .mat bez importu: `sub.sh t1` (sky_occ 0,65: taśma 1,27 / 1,1 — za
  ciemno), `sub.sh t2` (metal 0,7, sky_occ 0,35) w toku. Wartości docelowe przenieść do `build_world.MATERIALS["barrier_steel"]`
  (`set_metal`, `sky_occ: [0, y]`) i `bridge_concrete.vertex_grime` (teraz 0,135 w kodzie; t1 = 0,165).
  Brak: rendery m0 Low overcast / High clear (kolejka slotów Unity zagłodziła je 26 min — porzucone), swept b2, pełny pytest, EditMode /
  PlayMode, ADR 0123, pary zdjęcie | render.
  NASTĘPNY KROK: wpisać wartości z t2 do `tools/worldgen/roads/build_world.py`, potem
  `bash artifacts/junctions-r6/scripts/build.sh b3 && bash artifacts/junctions-r6/scripts/imp.sh b3 && bash artifacts/junctions-r6/scripts/post.sh b3 full`
  → `python artifacts/junctions-r6/scripts/stats_cmp.py artifacts/junctions-r6/renders_m0_low_clear/stats.txt artifacts/junctions-r6/renders_b3_low_clear/stats.txt`
  → `bash artifacts/junctions-r6/scripts/lum_set.sh b3` → obejrzeć `r4_deck_bz_eye2` (szachownica), `p0_kerb_merge_eye`, `r4_putry_nose_eye`.
- krok 3 (22:39, w toku): wartości z iteracji wpisane do `build_world.py` (`barrier_steel` 0,50 / `set_metal` 0,9 / `sky_occ` [0, 0,25];
  `vertex_grime` 0,165; t1 kapa / asfalt 1,35 Low clear, 1,46–1,50 High overcast; krawężnik 1,53–1,63 → stąd `bridge_kerb` 0,19),
  ADR 0123 szkic (`docs/adr/0123-junctions-r6-barriers.md`), build b3 + import + 4 zestawy renderów uruchomione jednym poleceniem
  (`logs/b3_all.out`). Polecenie właściciela: po tej operacji STOP.
  NASTĘPNY KROK (gdyby przerwało w trakcie): `bash artifacts/junctions-r6/scripts/build.sh b3 && bash artifacts/junctions-r6/scripts/imp.sh b3`

## RAPORT KOŃCOWY — przerwane (polecenie właściciela 11.11 ~22:50: stop po bieżącej operacji; ADR 0123, gałąź `junctions-r6`)

Wynik: **PARTIAL, niezweryfikowany do końca.** Build końcowy b3 (22:39–22:49) zaimportowany i wyrenderowany: Low/High × clear/overcast,
102 kamery każdy (`renders_b3_*`). Baza: m0 = main 3540bbdf zregenerowany w tym worktree (`renders_m0_low_clear`, `renders_m0_high_overcast`).

### Liczby (m0 → b3)
| miara | m0 | b3 |
|---|---|---|
| Low clear, 102 kamery (`stats_cmp.py`) | — | draws max **+0**, tris max **+0,7 %** |
| High overcast, 102 kamery | — | draws max +0, tris max +0,6 % |
| Low overcast / High clear | brak bazy (kolejka slotów Unity) | tylko „po” |
| szachownica cienia na kapie, `r4_deck_bz_eye2` Low clear | jest | **nie ma** (obejrzane natywnie) |
| taśma W / asfalt (sRGB, `lum_set.sh`): Low clear / High overcast / Low overcast / High clear | 1,36 / 1,18 / — / — | 1,38–1,41 / 1,30–1,45 / 1,55–1,59 / 1,32–1,34 (zdjęcia: 1,47 pochm., 1,53 słońce) |
| taśma w cieniu (lewa), Low clear | 0,61–0,66 | 0,88–0,91 (zdjęcie 0,58 — **gorzej**, odbicie nieba bez okluzji) |
| kapa / asfalt: Low clear / High overcast / Low overcast / High clear | 1,64 / 1,77 | 1,35 / 1,46–1,49 / 1,54 / 1,20–1,31 (zdjęcia 1,48 i 1,43–1,56; recenzja 1,2) |
| krawężnik pomostu / asfalt | ~1,6 | 1,36–1,43 / 1,19–1,50 / 1,20–1,52 / 1,32–1,39 (zdjęcia 1,40 / 1,35) |
| lico krawężnika → lico taśmy (GLB, b2) | 0,65 m | ~0,45 m (oś linii krawędziowej → lico 1,02 → ~0,85 m) |
| `guardrails_m.pier` | 132 | 172 (b2) |
| latarnie na pomostach Bieżeństwa | 15 pojedynczych na zewn. kapach | 10 podwójnych między pomostami |
| fidelity p50 / p95 | 0,36 / 2,304 | 0,36 / 2,304 (b2; b3 nie liczone) |
| kluczowe testy gis (6 plików) | — | 110 passed (b2; b3 nie uruchomione) |

### Rozliczenie 7 punktów zlecenia
| # | punkt | stan |
|---|---|---|
| 1 | szachownica cienia | **zrobione** — przyczyną była poręcz assetu; flaga w `WorldInstanceSet.noShadowMaterials`, bariera bez cienia na Low (`_LowNoShadow`) |
| 2 | ocynk jako metal, 2 zdjęcia | **częściowo** — ton w słońcu i pochmurno w zakresie zdjęć na pomoście; w cieniu za jasna; z dołu (`r4_link_bz_a`) taśma / trawa 1,4 → 2,3 (zdjęcie 3–4, ale tam słońce za kamerą, w renderze pod słońce); białe refleksy na górnych krawędziach belek (p90 180–208) |
| 3 | kapa ciemniejsza, bariera bliżej | **zrobione** (kapa 1,2–1,54, bariera −0,2 m w siatce); skośny krawężnik — nie |
| 4 | filar `r4_pier_bz` | **częściowo** — rzędy filarów z pomiaru (krawędzie wyspy), bariera przy wyspie w kadrze; filara w kadrze nadal nie ma (wymaga przebudowy spodu wiaduktu, domena GPT) |
| 5 | murek `r2_fork_link_eye` | **zrobione** (b2 obejrzane: skarpa z trawy; `walls_at.py` — brak kołnierza) |
| 6 | słupek / koniec belki `p0_kerb_merge_eye`, nos Putry N | **częściowo** — bariera pomostu łącznicy prosta na swojej kapie, druga szyna separatora; brak ~6 m szyny E −756…−750; nos: szczelina zamknięta (b2), zostaje lico krawężnika wyspy od północy. b3: `p0_kerb_merge_eye` obejrzany, nos w b3 NIE obejrzany |
| 7 | RING-B 2 propy | **zidentyfikowane i przeniesione** — latarnie na pomoście, nie na fartuchu; filtr w `swept_path_gate3.py`. Swept po zmianie **NIE zmierzony** (b2: rc 127, pusty log) |

### NIE zrobione / niezweryfikowane
swept path b3; pełny `pytest tests/gis tests/physics tests/gate3`; EditMode / PlayMode (zmieniony shader, importer, `WorldInstances`); pary
zdjęcie | render (`pairs.sh`); przegląd wszystkich 102 kamer b3 (obejrzane: `r4_deck_bz_eye2`, `p0_kerb_merge_eye` b3; reszta tylko b2 / t1);
telefon; `visual-critic`; finalne liczby w ADR 0123 (szkic). Pliki `Data/Regions/…/generated/*` w commicie = stan b3.
Uwaga: pełny pytest uruchomiony bez `KAMION_BLENDER` nadpisuje `generated/world_manifest.json` wersją z generycznymi filarami (asset „stale”).

### NASTĘPNY KROK (sesja 11, z katalogu worktree `.claude/worktrees/junctions-r6`)
1. `bash artifacts/junctions-r6/scripts/post.sh b3 full` (slot heavy: fidelity, swept, pełny pytest; logi `logs/b3_*`)
2. `pwsh C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1 -Acquire -Owner claude-junctions-r6; pwsh scripts/test.ps1 -Platform EditMode; pwsh scripts/test.ps1 -Platform PlayMode -Filter "WorldCRouteTests|WorldCBarrierTests"; pwsh C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1 -Release -Owner claude-junctions-r6; git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings`
3. `bash artifacts/junctions-r6/scripts/pairs.sh b3` → obejrzeć `pairs_b3/photo_*`, `ba_*` (zwł. `r4_putry_nose_eye`, `r4_pier_bz`, `r2_fork_link_eye`, `p0_lamp_putry_eye`)
4. uzupełnić „Wynik” w `docs/adr/0123-junctions-r6-barriers.md`, `robocopy artifacts\junctions-r6 C:\Users\matma\Documents\Claude\kamion\artifacts\junctions-r6 /E /XF *.pkl`, potem `visual-critic`.

## Sesja 11 (kontynuacja)
- s11 krok 1 (23:31): `post.sh b3 full` — fidelity p50 0,36 / p95 2,304 (= main); swept b3 = m0 poza RING-B prop 1,31 → 1,88 (v15) /
  1,79 → 2,28 (v25), opony bez zmian (G3-A lane −1,12, wide −0,10; G3-B −0,14; RING-B +1,75 / +1,61); pytest gis+physics+gate3:
  539 passed, 1 xfailed, 2 failed — `test_report_not_stale` (własna edycja `network.py` w trakcie biegu; powtórzyć po b4) i
  `tests/physics/test_scenario_strictness` (`top_speed_flat_comb.json`, fizyka — gałąź nie dotyka tests/physics; do sprawdzenia na main).
- s11 krok 3a: `pairs.sh b3` (24 pary), arkusze 102 kamer `sheets_b3_960/`, kamery SBS G3-A na b3 (`renders_b3sbs_low_overcast`,
  `pairs_b3sbs/`): B2 recenzji D51 (brak filarów s 351–359) w b3 już jest — rząd filarów przy krawędzi wyspy + bariera w kadrach
  201270 / 1398898 (recenzja oglądała main). B7: fartuch z kostki 2 m wokół wyspy, którego w rzeczywistości nie ma (ortofoto
  `plan_b3/ringb.jpg`) → b4: `apron: asphalt` (override `biezenstwa-ring-no-apron`) + szyna N separatora DK8 do pomostu (N 76,65).
  NASTĘPNY KROK: `bash artifacts/junctions-r6/scripts/build.sh b4 && bash artifacts/junctions-r6/scripts/imp.sh b4 && bash artifacts/junctions-r6/scripts/post.sh b4 full`
- s11 krok 2a: EditMode na b3: 261/261 passed (`artifacts/tests/editmode-20261111-233236.xml`). Build b4 (3 iteracje danych): obie szyny
  separatora DK8 dochodzą do barier swoich pomostów (`view/rails_b4.png`; nowy klucz `free_ends` autorskiej szyny), fartuch ronda
  Bieżeństwa = asfalt (xsec: `apron_sett` zniknął, krawężnik wyspy bez zmian), `overrides_stale` puste.
  NASTĘPNY KROK: `bash artifacts/junctions-r6/scripts/b4_all.sh` (import + 4 zestawy + SBS + PlayMode + post full)

## Sesja 12 (wznowienie po restarcie PC 03:44)
- s12 krok 1 (09:13): b4 landmark Bieżeństwa zacommitowany, `git merge main` (743 commity s11) → `85cdd0b6`; konflikty tylko
  `generated/{fidelity_qa,roads_qa,streetscape_qa,world_manifest}.json` → ours + regeneracja; kod scalił się automatycznie.
- s12 krok 2 (12:12–12:21, slot heavy z kolejki FIFO): build **b5** = b4 po scaleniu, build_world rc 0, trasa 2398 m, Megascans
  dostępne (bez fallbacku), `overrides_stale` puste; `gate3_landmarks.stale` = D-3/D-6 `biezenstwa-n-slip` (znany bloker G3-B nr 2,
  brak wysepki — poza zakresem 0123). Commit `31b10c65`.
  NASTĘPNY KROK: `bash artifacts/junctions-r6/scripts/b5_all.sh` (import + 4 zestawy + SBS + PlayMode + EditMode + post full; w toku od 12:23)
  → `bash artifacts/junctions-r6/scripts/pairs.sh b5`
- s12 krok 3 (12:22–13:26, `b5_all.sh`): import b5 rc 0, 4 zestawy renderów + SBS G3-A (`renders_b5_*`, `renders_b5sbs_low_overcast`),
  **EditMode 317/317, PlayMode 3/3** (`WorldCRouteTests|WorldCBarrierTests`), **pytest gis+physics+gate3 666 passed, 1 xfailed**,
  fidelity p50 0,36 / p95 2,304 (= main), swept = b3 (RING-B prop 2,41 / 2,28; G3-A lane −1,12, wide −0,10; G3-B −0,14).
  Budżet b5 vs m0 (stary main 3540bbdf, więc zawiera też scalenia s11): Low clear draws +0 na kamerach z poziomu jezdni, max +10
  (`r3_e_split_top`, kamera z góry 25 → 35), tris ≤ +3,8 % poza nią. Pary: `pairs_b5/` (24), `pairs_b5sbs/` (20, zdjęcie | render SBS;
  `scripts/pairs_sbs.sh`). Obejrzane: B2 — rząd filarów + bariera przy wyspie są w kadrach 201270 / 1398898; B7 — asfalt do krawężnika
  wyspy jest, ale wyspa płaska (na zdjęciach nasyp z kruszywa zasłania stopy filarów); ton kruszywo / asfalt zdjęcie 2,2–2,4, render 2,5–3,4.
- s12 krok 4 (13:40, W TOKU w tle): b6 = nasyp wyspy (`plantings.py` klucz `mound`, override `ring-centre` rim 1,6 m, 1:5, 0,7 m
  WORKING_VALUE); uruchomione `build.sh b6 && b6_all.sh` → log `artifacts/junctions-r6/logs/b6_all.out`.
  NASTĘPNY KROK (gdy `b6_all.out` kończy się „b6_all done”; jeśli przerwane — powtórzyć):
  `bash artifacts/junctions-r6/scripts/build.sh b6 && bash artifacts/junctions-r6/scripts/b6_all.sh`
  → `bash artifacts/junctions-r6/scripts/pairs.sh b6 && bash artifacts/junctions-r6/scripts/pairs_sbs.sh b6` → obejrzeć
  `pairs_b6sbs/photo_{2818555625124739,201270605169291,1398898753813071,178689077481862}.jpg` (nasyp, zakopane znaki / bariera?)
  → uzupełnić „Wynik” w `docs/adr/0123-junctions-r6-barriers.md` → `robocopy artifacts\junctions-r6 C:\Users\matma\Documents\Claude\kamion\artifacts\junctions-r6 /E /XF *.pkl`
- s12 STOP (16:39, polecenie lidera — koniec limitu): zadanie w tle `build.sh b6 && b6_all.sh` DZIAŁA (nie zabite), slot heavy od 14:02;
  log `artifacts/junctions-r6/logs/b6_all.out` (ostatnia linia: "EditMode: 317 total, 317 passed, 0 failed, 0 skipped (Passed) -> C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\junctions-r6\artifacts\tests\editmode-20261112-153012.xml"), szczegóły `logs/b6_{build,import,qa_*,playmode,editmode,fidelity,swept,pytest}.log`.
  b6 NIE obejrzany, ADR 0123 „Wynik” nieuzupełniony (liczby b5 w kroku 3 wyżej), dowody nieskopiowane do main.
  NASTĘPNY KROK: `tail -3 artifacts/junctions-r6/logs/b6_all.out` — jeśli jest „b6_all done”:
  `bash artifacts/junctions-r6/scripts/pairs.sh b6 && bash artifacts/junctions-r6/scripts/pairs_sbs.sh b6` → obejrzeć pary (krok 4) → ADR → robocopy;
  jeśli brak „b6_all done” i proces nie żyje: `bash artifacts/junctions-r6/scripts/build.sh b6 && bash artifacts/junctions-r6/scripts/b6_all.sh`
  (jeśli jest „world ready”, wystarczy samo `b6_all.sh`). Po buildzie zacommitować `Data/Regions/*/generated`, `art-source`.

## Sesja 13 (wznowienie 16:43)
- s13 krok 1 (17:01): żywy łańcuch `b6_all.sh` z s12 dobiegł końca sam („b6_all done 17:01”, nic nie zabite / nie zdublowane):
  **b6** import rc 0, 4 zestawy + SBS, **EditMode 317/317, PlayMode 3/3, pytest gis+physics+gate3 666 passed, 1 xfailed** (16:16 min),
  fidelity p50 0,36 / p95 2,304, swept = b5 (RING-B prop 2,41 / 2,28; G3-A lane −1,12, wide −0,10; G3-B −0,14).
  Budżet b6 vs b5 Low clear 102 kamery: draws max **+0**, tris +0,0 %. Pary `pairs_b6/` (24), `pairs_b6sbs/` (20) obejrzane
  (2818555…, 201270…, 1398898…, 178689…, arkusze `view/b6_{ba,photo}_sheet1.jpg`): nasyp z kruszywa na wyspie jest, bariera i
  tabliczki ronda stoją na nim (niezakopane), filary + czerwony gzyms czytelne — węzeł rozpoznawalny (D51).
  NASTĘPNY KROK: `git merge main` (generated/glb → ours; `WorldPBR.shader` CBUFFER: zostawić obie strony) →
  `bash artifacts/junctions-r6/scripts/build.sh b7 && bash artifacts/junctions-r6/scripts/b7_all.sh`
- s13 krok 2 (17:03): `git merge main` (bedc52d1, 1825 commitów) → `c92cffb5`; konflikty: generated ×4 + `street_props.glb` → ours, `WorldPBR.shader` CBUFFER → obie strony. Uruchomione w tle `build.sh b7 && b7_all.sh` (log `logs/b7_all.out`).
  NASTĘPNY KROK (jeśli przerwane): `bash artifacts/junctions-r6/scripts/build.sh b7 && bash artifacts/junctions-r6/scripts/b7_all.sh` → `pairs.sh b7 && pairs_sbs.sh b7` → ADR „Wynik” → robocopy
- s13 krok 3 (17:25–17:48): build **b7** rc 0 (trasa 2398 m, `overrides_stale` puste, Megascans dostępne), commit `ac0f01d6`; import rc 0 (import-region sam uruchomił build_all 1045 s — w worktree brakowało `asphalt_detail_photo`, skopiowane z main), 4 zestawy renderów; Low clear b7 vs b6: draws max +4, tris ≤ +3,7 % (treść z main). W tle dalej `b7_all.sh` (SBS, PlayMode, EditMode, post full).
  NASTĘPNY KROK: `tail -5 artifacts/junctions-r6/logs/b7_all.out` → po „b7_all done”: `bash artifacts/junctions-r6/scripts/pairs.sh b7 && bash artifacts/junctions-r6/scripts/pairs_sbs.sh b7` → ADR „Wynik” → robocopy. Handover na żywo: `C:\Users\matma\Documents\Claude\kamion\artifacts\live\junctions-r6.md`
