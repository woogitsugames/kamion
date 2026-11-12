# ADR 0123: Węzły r6 — bariery: cień poręczy, ocynk jako metal, brudna kapa i krawężnik pomostu, bariera 0,42 m, rzędy filarów z pomiaru, latarnie między pomostami

Status: przyjęty (world-builder, gałąź `junctions-r6`), 2026-11-11. Wynika z `docs/reports/visual/REVIEW-2026-11-11-s10-0117.md`
(„Lista problemów (r6)”, pkt 4 bramki 3). Powiązane: ADR 0117 (bariery r5), 0110, 0067 (wiadukt hero), 0105 (spód DK8 — nietknięty),
0022 (zestawy PBR), 0060 (`sky_occ`). Dowody: `artifacts/junctions-r6/` (STATUS.md, `renders_m0_*` = main 3540bbdf zregenerowany w tym
worktree, `renders_b*_*`, `renders_t*_*` = iteracja materiału, `ortho/`, `refs/`, `logs/`, `scripts/`).

## Kontekst (co zmierzono przed zmianą)
1. **Szachownica na kapie** (`r4_deck_bz_eye2`, Low clear): rzuca ją poręcz assetu hero (alfa-testowany quad z 6 prętami), nie bariera —
   po wyłączeniu cienia samej bariery (iteracja t1) wzór został. Flaga na materiale nie wystarcza: walidacja materiałów URP przy
   ładowaniu z powrotem włącza pass `ShadowCaster` nieprzezroczystego Lit (`BaseShaderGUI`, `castShadows = IsOpaque`), co wyszło w b2.
2. **Ocynk**: `barrier_steel` 0,13 / metal 0. Luminancja sRGB względem asfaltu w tych samych kadrach (`scripts/lum.py`, `lum_set.sh`):
   zdjęcia — taśma 1,47 (454716650857984, pochmurno), 1,53 w słońcu / 0,58 w cieniu (2948595898752384, słońce); render m0 — 1,36
   (Low clear), 1,18 (High overcast), 0,61–0,66 w cieniu. Kadr `r4_link_bz_a/b` nie nadaje się do porównania tonu „w słońcu”: na
   zdjęciu słońce jest za kamerą, w renderze kamera patrzy pod słońce (taśma w cieniu własnym) — światło to domena GPT.
3. **Kapa**: zdjęcia 1,48 (pochmurno) i 1,43–1,56 (słońce) × asfalt, krawężnik 1,40 / 1,35; render m0 1,64 (Low clear) / 1,77 (High
   overcast). Recenzja podaje 1,2 dla ciemniejszego pasa płyty — przyjęty cel 1,2–1,5.
4. **Odległość bariery**: w wyeksportowanym świecie m0 (`scripts/xsec_glb.py`, przekrój E 490 N −675): lico krawężnika → lico taśmy
   0,65 m, oś linii krawędziowej → lico 1,02 m, → stopy słupków 1,37 m. Metoda recenzji (wiersz obrazu) czyta te 1,37 m jako 1,69 m,
   a na zdjęciu 1,47 m — czyli zdjęcie ma barierę ~0,25–0,3 m bliżej; deklaracja „0,70 m” z 0117 była zgodna z siatką, różnica
   z recenzją to perspektywa pomiaru na wysokości słupków.
5. **RING-B, „2 propy na fartuchu”**: to dwie latarnie `lamp_12m` reguły jednokierunkowej stojące NA pomostach (z 145,84 / 145,95;
   pierścień ~140 m) — przywrócone w 0117. Analiza swept path jest 2D i czytała je jako słupy na fartuchu. Ortofoto 0,08 m
   (`ortho/ringb_apron.jpg`, `via_w.jpg`): latarnie wiaduktu są dwuramienne i stoją w szczelinie między pomostami co ~32 m; na
   zewnętrznych kapach ich nie ma (zdjęcia z pomostu 454716650857984 i 2948595898752384 pokazują to samo).
6. **Filary**: reguła „rozpiętość 25 m” dawała rząd w środku wyspy i rzędy 31–33 m od środka (za jezdnią ronda). Zdjęcie
   177786140912399 (ze wschodniego punktu pierścienia): filar stoi na wyspie tuż za jej krawężnikiem, z taśmą W między nim a
   pierścieniem; następny rząd ~35 m dalej (stosunek wysokości filarów w kadrze ~8).
7. **Murek `r2_fork_link_eye`**: 4 trójkąty kołnierza `c:w1101181473…:L:7` na stacjach, gdzie pas trawy zaczyna się / kończy
   (zmiana rodziny profilu RURAL → URBAN przy s 596, obniżony krawężnik przy s 610): kołnierz 0,5 m stał goły 0,5–0,7 m nad łącznicą.
8. **`p0_kerb_merge_eye`**: `_join_free_ends` (0117) przeciągał koniec bariery pomostu łącznicy (c:w240542867 R, naturalnie N 76,4–77,5)
   o ~2,5 m na barierę pomostu DK8 — stąd zygzak, słupek bez belki i koniec belki w powietrzu. Ortofoto: separator ma DWIE szyny
   (N 76,6–76,9 i N 75,0–74,5), każda wchodzi w barierę swojego pomostu.
9. **Nos mediany Putry N**: „czarna szczelina” = brak jakiejkolwiek powierzchni w E −556…−553,5, N 130–133,5 (pas trawy strony
   z krawężnikiem i niskie pobocze strony wschodniej nie stykają się; teren 0,15–0,2 m pod koroną krawężnika).

## Decyzja
1. **Cień poręczy**: manifest `viaduct_steel.cast_shadows: false` → `InstanceImporter` zapisuje indeksy takich submeshy w
   `WorldInstanceSet.noShadowMaterials`, `WorldInstances.Flush` rysuje je z `ShadowCastingMode.Off` (wszystkie tiery; pręty 12 mm
   rzucają w rzeczywistości włosowe cienie, które zakrywa bariera). Bariera: `barrier_steel.shadow_low: false` → `_LowNoShadow` w
   Kamion/World PBR (pass ShadowCaster, wierzchołki zapadają się, gdy nie ma `_KAMION_WORLD_DETAIL`, czyli tylko Low): mapa cieni Low
   nie rozdziela dwóch belek odległych o 0,2 m.
2. **Ocynk jako metal**: zestaw `barrier_galv` dostaje maskę metalu w MaskMap.r (cynk 1, film drogowy / zacieki / rdza 0) i
   roughness 0,56 (było 0,62); `barrier_steel`: albedo 0,50, `set_metal` 0,9 (nowy klucz manifestu → `_MetallicScale`), `sky_occ`
   [0, 0,25] (odbicie przy horyzoncie przytłumione: lico belki odbija jezdnię, nie niebo). Wartości dobrane iteracją na
   wygenerowanym `.mat` (b2 / t1 / t2 w STATUS.md), WORKING_VALUE — bez karty szarości.
3. **Kapa i krawężnik pomostu, bez nowego draw calla**: wierzch kapy niesie film drogowy w COLOR_0.r (`standards.CAP_GRIME`,
   `meshing._emit_strip`), `bridge_concrete.vertex_grime` [0,165, 0,158, 0,145, 0,3] → `_VERTEX_GRIME` w Kamion/World PBR (grime
   zachowuje 40 % kontrastu zestawu, więc spoiny prefabrykatów bledną razem z nim). Krawężniki pomostów są eksportowane jako
   `bridge_kerb` (ten sam zestaw `kerb_concrete_1m`, albedo 0,19) — zmiana nazwy dopiero w `build_world.assemble`, więc reguły QA /
   fidelity oparte na `curb_concrete` widzą je bez zmian; siatka `bridge` miała prymityw `curb_concrete` dokładnie dla tych trójkątów.
4. **Bariera 0,42 m za licem krawężnika** na wąskiej kapie (`BRIDGE_BARRIER_FACE_M` 0,70 → 0,42; na kapach 1,5 m bez zmian).
5. **Latarnie między pomostami**: `bridge_style.lamps: {side: median, spacing_m: 32, anchor_en}` → `furniture.bridge_median_lamps`
   usuwa latarnie reguły stojące na tych pomostach i stawia pary `lamp_12m` „plecami do siebie” na wewnętrznej krawędzi kapy pierwszego
   pomostu (bez nowego prototypu). `swept_path_gate3.py` pomija propy stojące > 4,5 m nad jezdnią pod nimi (`props_overhead_skipped`
   w summary.json).
6. **Rzędy filarów z pomiaru**: `hero_bridge` override `pier_lines_en` (punkt każdego rzędu) zamiast reguły rozpiętości; dla
   Bieżeństwa rzędy 14 m po obu stronach środka ronda (kolumny ~2 m za krawężnikiem wyspy, WORKING_VALUE ±2 m), bez rzędu w środku;
   cztery skrajne rzędy zostają na stacjach reguły (brak zdjęcia, z którego da się je odczytać). `pier_guardrails` liczy fartuch
   (`apron_sett`) jako jezdnię — bariera staje za krawężnikiem wyspy, jak na zdjęciu.
7. **Murek**: kołnierz na styku „pas trawy / brak pasa” jest skarpą z trawy 1 : `VERGE_SKIRT_SLOPE` (src `…:vg` → w siatce terenu).
8. **`p0_kerb_merge_eye`**: koniec bariery pomostu nie jest dociągany do innych szyn; szyny autorskie nie deduplikują się nawzajem;
   druga szyna separatora `dk8-ramp-split-barrier-n` wg ortofoto, do końca wygenerowanej wyspy (E −756).
9. **Nos Putry N**: kołnierz z kostki na całą szerokość końca mediany do N 134; pasy trawy są CIĘTE na obrysie wyspy / wypełnienia
   (`gores._clip_tris`) zamiast kasowania całych trójkątów dotykających strefy.

10. **Rondo Bieżeństwa bez fartucha z kostki** (b4, REVIEW s11 SBS D51 B7): override `biezenstwa-ring-no-apron` (`apron: asphalt`) —
    pas fartucha reguły (2,0 m) zostaje w tym samym obrysie, ale jako asfalt w poziomie jezdni; krawężnik wyspy bez zmian. Ortofoto
    0,08 m (`plan_b3/ringb.jpg`) i zdjęcia 1398898753813071 / 201270605169291 / 2818555625124739: jezdnia dochodzi do krawężnika wyspy.
11. **Szyny separatora DK8 do barier pomostów** (b4): `dk8-ramp-split-barrier` / `-n` przedłużone do początku barier swoich pomostów,
    nowy klucz autorskiej szyny `free_ends: [bool, bool]` (koniec, który ma zostać w miejscu zamiast dociągać się do sąsiedniej szyny).
12. **Nasyp z kruszywa na wyspie ronda** (b6, D51 B7): `plantings` — klucz wyspy `mound: {setback_m, slope, max_m}`; `ring-centre`:
    płaski pas 1,6 m za krawężnikiem (bariera stoi na nim), potem 1:5 do 0,7 m (WORKING_VALUE, odczyt ze zdjęć, bez pomiaru) —
    zasłania stopy filarów z kamery na wysokości dachu auta, jak na zdjęciach.

## Otwarte / niezrobione (uczciwie)
1. **Telefon** — brak (agent nie używa adb). Budżet tylko z edytora.
2. **Filar w kadrze `r4_pier_bz`** — nadal go nie ma: bariera przy wyspie jest w kadrze, ale żeby filar wszedł w kadr tak jak na
   zdjęciu, kolumny musiałyby stać ~3,5–4 m od osi pomostu (asset: ±1,3 m pod wąską skrzynką). To przebudowa spodu wiaduktu
   (`hero_bridge.py` / `make_viaduct.py`, domena GPT „pod pomostem”). Kształt filara (owalny, jeden szeroki) także.
3. **Taśma W w cieniu przy czystym niebie** zostaje jaśniejsza niż na zdjęciu (0,58): sonda odbić to samo niebo, bez okluzji przez
   jezdnię; `sky_occ` tłumi to tylko częściowo. Ton „w słońcu od dołu” (`r4_link_bz_a/b`) nieporównywalny — inny azymut słońca.
4. **`p0_kerb_merge_eye`** — częściowo: zygzak usunięty, ale między końcem wyspy (E −756) a początkiem pomostu łącznicy (E −750)
   brakuje ~6 m szyny (wygenerowany grunt leży tam niżej niż wyspa i pomost), a pomosty stykają się zamiast mieć 2,3 m szczeliny.
5. **Nos Putry N** — częściowo: szczelina zamknięta, ale od północy widać lico krawężnika wyspy 0,15–0,2 m nad niskim poboczem
   strony wschodniej (mediana jest w połowie krawężnikowa, w połowie „rural”); czubek nadal ~3 m za daleko na południe.
6. Znak C-9 reguły `roundabout_island` na środku kadru `r4_pier_bz` (E 573,7 N −714,4) — domena znaków (GPT), nie ruszony.
7. Czerwony gzyms, aliasing prętów poręczy, tył taśmy „deska” (P2-2…P2-4 recenzji) — nie ruszone.
8. Baseline m0 dla Low overcast / High clear nie powstał (kolejka slotów Unity) — te dwa zestawy są tylko „po”.

## Pliki wspólne (addytywnie)
- `game/`: `Environment/Shaders/WorldPBR.shader` (`_VERTEX_GRIME`, `_LowNoShadow`), `World/Import/RegionImporter.cs` (klucze manifestu
  `vertex_grime`, `set_metal`, `shadow_low`), `WorldPbrMaterials.cs` (COLOR_0 dla `vertex_grime`), `InstanceImporter.cs`,
  `World/Runtime/WorldInstanceSet.cs` (+`noShadowMaterials`), `WorldInstances.cs` (1 wyrażenie w `Flush`).
- `tools/worldgen/roads/`: `build_world.py` (materiały, zmiana nazwy w `assemble`), `meshing.py`, `standards.py`, `gores.py`.
- `tools/worldgen/streetscape/`: `furniture.py` (bariery + `bridge_median_lamps`), `hero_bridge.py` (`pier_lines_en`), `materials.py`
  (1 klucz), `stage.py` (1 wywołanie). `tests/physics/swept_path_gate3.py` (filtr propów nad jezdnią).
- `art-source/world/materials/_src/sets_facade.py` (`barrier_galv`: maska metalu), `materials_spec.json`, asset `viaduct_biezenstwa`.
- `overrides.yaml`: `bridge_style.lamps`, `hero_bridge.pier_lines_en`, `dk8-ramp-split-barrier-n`, wielokąt `putry-n-median-nose`.

## Wynik
Buildy: m0 = main 3540bbdf (baza), b3 = pkt 1–9, b4/b5 = pkt 10–11 (+ scalenie main s11), b6 = pkt 12, **b7 = b6 po scaleniu main
bedc52d1 (s13)** — stan do scalenia. Dowody: `artifacts/junctions-r6/` (`renders_b7_*` 4 zestawy × 102 kamery, `renders_b7sbs_low_overcast`,
`pairs_b7/` 24, `pairs_b7sbs/` 20 par zdjęcie | render, `view/b7_{photo,ba}_sheet.jpg`, `logs/b7_*`, `swept_b7/`).

| miara | wynik |
|---|---|
| EditMode / PlayMode (`WorldCRouteTests|WorldCBarrierTests`) | b7: **403/403**, **3/3** (b6: 317/317, 3/3) |
| pytest `tests/gis tests/physics tests/gate3` | b6: 666 passed, 1 xfailed; b7: B7_PYTEST |
| fidelity krawędzi p50 / p95 | b6: 0,36 / 2,304 (= main); b7: B7_FID |
| swept path (min opona / prop) | b6: G3-A lane −1,12 / 0,70, wide −0,10 / 0,69; G3-B −0,14 / 0,86–0,88; RING-B +1,75 / 2,41 (v15), +1,61 / 2,28 (v25) — opony = main, RING-B prop 1,31 → 2,41 / 1,79 → 2,28; b7: B7_SWEPT |
| budżet Low clear, 102 kamery (drawsEst edytora, bez telefonu) | b3 vs m0 +0 draws / tris ≤ +0,7 %; b6 vs b5 **+0 / +0,0 %**; b7 vs b6 max +4 draws, tris ≤ +3,7 % (treść scalona z main, nie ta gałąź) |
| szachownica cienia na kapie (`r4_deck_bz_eye2`) | nie ma (b3…b7 obejrzane) |
| taśma / asfalt (sRGB), pomost: Low clear / High overcast | m0 1,36 / 1,18 → b3 1,38–1,41 / 1,30–1,45 (zdjęcia 1,53 / 1,47) |
| kapa / asfalt | m0 1,64 / 1,77 → b3 1,35 / 1,46–1,49 (zdjęcia 1,43–1,56 / 1,48) |
| lico krawężnika → lico taśmy (GLB) | 0,65 → ~0,45 m |
| `guardrails_m.pier` | 132 → 172 m |
| latarnie na pomostach Bieżeństwa | 15 pojedynczych na kapach → 10 podwójnych między pomostami |

**Kryterium D51 (czy kierowca rozpozna węzeł): TAK** — w parach SBS (2818555625124739, 201270605169291, 1398898753813071,
178689077481862) układ jest ten sam co na zdjęciach: wiadukt z czerwonym gzymsem i poręczą, rząd filarów przy krawędzi wyspy, asfalt
do krawężnika wyspy, taśma W za krawężnikiem, nasyp z kruszywa, tabliczka z nazwą ronda, wieżowiec w tle. Różnice, które zostają
(polerka wg D51, nie rozpoznawalność): kruszywo szarsze i ciemniejsze niż na zdjęciu, filary prostokątne zamiast owalnych z szerokim
czerwonym pasem, spód pomostu ciemniejszy, C-9 reguły na osi kadru `r4_pier_bz`. Niezależna ocena `visual-critic` — po stronie lidera
(agent nie tworzy subagentów).
