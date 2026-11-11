# STATUS — junctions-r5 (ADR 0117: węzły r5, priorytet bariery; wg REVIEW-2026-11-11-s10-0110 „Lista na r5”)

Gałąź `junctions-r5` (z main 60705006). Dowody: `artifacts/junctions-r5/` (renders_<tag>_<tier>_<światło>, logs, scripts, pairs = zdjęcie | render).

- krok 0: baseline b0 = main 60705006 (świat z kopii main, bez regeneracji): kamery węzłów Low clear + High overcast
  (`renders_b0_low_clear/`, `renders_b0_high_overcast/`, `stats.txt` w każdym). Library + zestawy PBR skopiowane z main.
- krok 1 (kod, przed buildem b1): `furniture.guardrail` przepisany — taśma W 310 × 83 mm jako 6 płaskich faset z własnymi
  wierzchołkami (twarde krawędzie), słupki C 100 × 55 z przekładką 0,10 m za belką (belka na licu słupka), na pomoście słupki
  C 120 × 64 na stopkach co 2 m + górna belka skrzynkowa (góra 0,98 m), słupki gruntowe co 4 m; materiał `barrier_steel`:
  0,55 / metal 0,9 → 0,25 / metal 0 + nowy zestaw `barrier_galv` (4,0 × 0,5 m, UV wzdłuż belki / rozwinięcie profilu:
  styk z śrubami, brud na fasetach „do góry”, zacieki, rdza). Pomost Bieżeństwa: `bridge_style.cap_w` 1,0 m (było 1,5),
  lico belki 0,70 m za licem krawężnika; poręcz z poziomymi prętami wraca do assetu hero (`rail_h_m` 1,10, tekstura
  `viaduct_steel.png` — pręty zamiast szczebelków). Reguła `pier_guardrails`: bariera W przy filarze ≤ 4 m od krawędzi jezdni.
  Testy `tests/gis/test_junctions_r4.py` (bariery): 3 passed.
  NASTĘPNY KROK: `bash artifacts/junctions-r5/scripts/fast.sh b1` → `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c`
  → `bash artifacts/junctions-r5/scripts/qa.sh b1 Low clear` → obejrzeć `r4_deck_bz_eye`, `r4_link_bz_a`, `r4_pier_bz`.
- krok 2 (b1, sha poniżej): build b1 + import + rendery `renders_b1_low_clear/`, `renders_b1_high_overcast/` — OBEJRZANE: profil W,
  słupki C, górna belka i poręcz z prętami czytelne (`r4_deck_bz_eye`, `r4_link_bz_a`), kapa 1,0 m; ALE `barrier_steel` 0,25 nadal
  za jasny w kadrze (belka sRGB ~185 przy asfalcie 60; zdjęcie 454716: belka 74–102 przy asfalcie 63) → następna wartość ~0,11.
  keytests b1: 125 passed. `guardrails_m` b1: bridge 2916, structure 603, pier 0 (reguła po łańcuchach nie łapała ronda).
  Po b1 (kod, jeszcze NIE zbudowane): `pier_guardrails` przepisane na obrys asfaltu (test offline: 3 biegi, 58,5 m przy filarach
  hero 2,7–4,1 m od jezdni). Ustalenia: (a) `_Generated` skopiowane z main było importem SPRZED 0110 → `renders_b0_*` to nie jest
  uczciwe „przed”; prawdziwy baseline = świat main f260ab36: `bash artifacts/junctions-r5/scripts/baseline.sh m0` (W TOKU — na czas
  działania podmienia `Data/raw/derived/.../world`, `generated/world_manifest.json`, `route_start.json`, asset wiaduktu i
  `viaduct_steel.png` na wersje main, kopie w `artifacts/junctions-r5/_swap/` i `world_cur`; jeśli przerwane: przywrócić ręcznie
  wg końcówki skryptu albo po prostu przebudować `fast.sh`). (b) latarnia `p0_lamp_putry_eye`: w b1 nadal brak — do wyjaśnienia
  (`support_adjustments` na main = 20, nie 28→50; `props_off_carriageway.moved` 48→49). (c) pasmo jodełki wsch.: ortofoto 50 px/m
  (`junctions-r4/trace/e_split_band.jpg`) = klin 1,1 m (E −830,6) → 3,1 m (E −806,2), NIE stałe 2,5 m — geometrii nie zmieniam.
  (d) `p0_kerb_merge_eye`: bieg łańcucha `c:w1101181473…:L` i `authored:dk8-ramp-split-barrier` spotykają się przy E −765 z różnym
  offsetem (jeden z terminalem w ziemię, drugi ucięty) — plan: biegi autorskie pierwsze, ucięty koniec dociągany do sąsiedniego
  biegu (bez terminala), górna belka zawsze schodzi na końcu.
  NASTĘPNY KROK: poczekać na `baseline.sh m0` (log `logs/m0_*`), potem: `barrier_steel` color → ~0.11 w `tools/worldgen/roads/build_world.py`,
  łączenie biegów w `furniture._dedup_guardrail`, nos Putry N (wielokąt elipsy w overrides `putry-n-median-nose`), murek
  `r2_fork_link_eye`; `bash artifacts/junctions-r5/scripts/fast.sh b2 && bash artifacts/junctions-r5/scripts/imp.sh b2` →
  `python artifacts/junctions-r5/scripts/stats_cmp.py artifacts/junctions-r5/renders_m0_low_clear/stats.txt artifacts/junctions-r5/renders_b2_low_clear/stats.txt`
- krok 3 (b3, po resecie limitu): baseline `m0` = świat main f260ab36 zaimportowany w tym worktree (`renders_m0_*`). b3 (łączenie biegów,
  latarnie nie kasowane pod barierami, ocynk 0,11, cięcia trójkątów, nos Putry N): Low clear vs m0 na 102 kamerach: draws −12…+0,
  tris max +1,0 % (`python artifacts/junctions-r5/scripts/stats_cmp.py artifacts/junctions-r5/renders_m0_low_clear/stats.txt artifacts/junctions-r5/renders_b3_low_clear/stats.txt`).
  Swept G3-A −0,10 / −1,12, G3-B −0,14 (= main); fidelity p50 0,36 / p95 2,304 (= main). Latarnia w `p0_lamp_putry_eye` wróciła.
  OBEJRZANE pary `pairs_b3/photo_*` (zdjęcie | render): bariera pomostu ciemna, matowa, W czytelne, kapa wąska. NIE naprawione w b3:
  `p0_kerb_merge_eye` (nadal plątanina biegów po lewej), bariera przy filarze (reguła dała 0 m — dedup z istniejącymi biegami),
  murek `r2_fork_link_eye`.
  NASTĘPNY KROK: `uv run --project tools/worldgen python artifacts/junctions-r5/scripts/dbg_rails.py -765,76,20 560,-715,40` →
  poprawka łączenia → `bash artifacts/junctions-r5/scripts/cycle2.sh b4` → `bash artifacts/junctions-r5/scripts/pairs.sh b4`
- krok 4 (b4): wolne końce biegów dochodzą do sąsiedniego biegu (8), `pier_guardrails` dedup tylko z biegami naziemnymi (132 m przy
  6 filarach), ocynk 0,13, parametry poręczy hero w override (spec 0105 bez zmiany parametrów), Unity przez `unity-slot.ps1`.
  NASTĘPNY KROK (gdyby przerwało): `uv run --project tools/worldgen python -m pytest tests/gis tests/physics tests/gate3 -q`,
  `robocopy artifacts\junctions-r5 C:\Users\matma\Documents\Claude\kamion\artifacts\junctions-r5 /E`.

## RAPORT KOŃCOWY (ADR 0117, gałąź `junctions-r5`; sha kodu i danych: commit `feat(junctions-r5): ADR 0117 …`, ten plik w tym samym lub następnym commicie)

Wynik: **PARTIAL** — priorytet (bariery: profil, materiał, odległość na pomoście) zrobiony i porównany ze zdjęciami w tym samym kadrze;
z listy regresji: latarnia zrobiona, biegi przy E −782 / filar / nos częściowo, murek nie, pasmo jodełki nie zmienione świadomie
(pomiar przeczy recenzji). Brak telefonu i oceny `visual-critic` (dla lidera).

### Liczby przed / po („przed” = main f260ab36, świat main zaimportowany w tym worktree: `renders_m0_*`; „po” = b4)
| miara | przed | po |
|---|---|---|
| profil taśmy W | 5 punktów, wspólne wierzchołki (cieniowanie „rura”), fale 5 cm | 310 × 83 mm, 7 punktów, 6 płaskich faset (twarde krawędzie) |
| słupki | prostopadłościan 10 × 5 cm co 2 m pod belką | C 100 × 55 + przekładka 0,10 m, belka na licu; grunt co 4 m, pomost C 120 × 64 na stopce co 2 m |
| `barrier_steel` | 0,55 / rough 0,45 / metal 0,9, bez tekstury | 0,13 / 0,65 / metal 0 + zestaw `barrier_galv` (styk, śruby, brud, zacieki, rdza) |
| ton belki w kadrze `r4_deck_bz_eye` | najjaśniejszy obiekt dołu kadru (b1 z albedo 0,25: sRGB ~185 przy asfalcie 60) | ciemniejsza od kapy, jak na zdjęciu (belka 74–102 przy asfalcie 63); ocena z par, bez karty szarości (WORKING_VALUE) |
| lico krawężnika → lico belki, pomost Bieżeństwa (z kodu) | 1,12 m (recenzent z kadru: ~1,35) | 0,70 m (zdjęcie ~0,7 ± 0,2) |
| kapa pomostu Bieżeństwa (za krawężnikiem) | 1,50 m | 1,00 m (pomost 11,3 → 10,3 m; jezdnia, dźwigar, filary bez zmian) |
| poręcz na krawędzi pomostu Bieżeństwa | brak (0110 usunęło szczebelkową) | 6 poziomych prętów + płaskownik, w assecie hero (LOD-y) |
| `guardrails_m` | bridge 2916, median 1133, embankment 482, structure 529, authored 36 | bridge 2916, median 1133, embankment 482, structure 603, authored 36, pier 132 |
| połączenia biegów (`joined_ends` / `joined_free_ends`) | — | 5 / 8 |
| latarnia na kapie w `p0_lamp_putry_eye` | brak | jest (lamp_12m 165 → 166; `poles_under_decks` 2 → 3) |
| Low clear, 102 kamery: draws | — | −12…+0 (żadna kamera na plusie) |
| Low clear, 102 kamery: tris | — | max +1,1 % (`g3a-eye-s0262`, `stretch-03`); `r2_kerb_merge_main_eye` −13,4 % |
| High overcast: draws / tris max | — | +0 / +1,0 % |
| swept path, opony: G3-A wide / lane, G3-B, RING-B v25 / v15 | −0,10 / −1,12, −0,14, +1,61 / +1,75 m | bez zmian |
| swept path, prześwit do propów: G3-A / G3-B | 0,69–0,70 / 0,86–0,88 m | bez zmian |
| swept path, prześwit do propów: RING-B v15 / v25 | 1,88 / 2,28 m | **1,31 / 1,79 m** — mniej o ~0,5 m (już w b3, przed barierami przy filarach); przyczyna nie zmierzona (UNVERIFIED: nowe 74 m `structure` przy rondzie po zwężeniu pomostu albo latarnie przywrócone na kapach) |
| fidelity krawędzi p50 / p95 | 0,36 / 2,304 m | 0,36 / 2,304 m |
| road_consistency / ściany terenu | 65 / 4 (max 0,345) | 65 / 4 (max 0,345) |
| konstrukcja 0105 (DK8) | — | `deck_before_sha256` = `deck_after_sha256`, `deck_barriers_unchanged` = true (oba pomosty) |

Budżet: draws ≤ +3 spełnione na wszystkich 102 kamerach (max +0), tris ≤ +2 % spełnione (max +1,1 %). Pomiar tylko z edytora.
Stan pośredni b1 (pełne fasety z obu stron, słupki dwustronne): tris +2…+6,5 % — stąd cięcia (tył blachy 2 fasety, półki
jednostronne, Douglas–Peucker 2 cm). `renders_b0_*` to import sprzed 0110 skopiowany z main — NIE jest bazą porównania.

### Pary zdjęcie | render (≤ 960 px, ta sama poza; `pairs_b4/`)
`photo_r4_deck_bz_eye_{low_clear,high_overcast}.jpg` (454716650857984), `photo_r4_deck_bz_eye2_*` (2948595898752384),
`photo_r4_link_bz_a_*` (500263111404933), `photo_r4_link_bz_b_*` (1259231227807789), `photo_r4_pier_bz_*` (177786140912399).
Przed | po (main | b4, Low clear): `ba_p0_kerb_merge_eye.jpg`, `ba_p0_lamp_putry_eye.jpg`, `ba_r2_fork_link_eye.jpg`,
`ba_r2_kerb_merge_main_eye.jpg`, `ba_r4_putry_nose_eye.jpg`, `ba_eye_putry_n.jpg`, `ba_r3_e_split_eye.jpg`, `ba_stretch-04.jpg`,
`ba_stretch-01.jpg`, `ba_g3b-eye-s1482.jpg`, `ba_p0_lamp_w1101181473_eye.jpg`, `ba_r4_*`. Obejrzane (Read): pary `photo_*` b1 / b3 / b4,
wycinki natywne pomostu, łącznicy, `p0_kerb_merge_eye`, `r4_pier_bz`, arkusze `ba_*`.

### Rozliczenie listy r5 z recenzji 0110
| id | punkt | stan | uwagi |
|---|---|---|---|
| P0-1 | telefon A16 | **nie** | agent nie używa adb |
| P1-1 | profil W, belka na licu, słupek C | **zrobione** | `photo_r4_deck_bz_eye_*`, `photo_r4_link_bz_*`; z tyłu (kadr łącznicy) blacha ma 2 fasety — fałdy tylko od strony jezdni |
| P1-2 | ocynk zmatowiały, poręcz z prętami | **zrobione** (albedo WORKING_VALUE, bez karty szarości) | na tierze Low tekstura zestawu jest blokowa z bliska (`r4_link_bz_a`) |
| P1-3 | kapa / odległość bariery | **zrobione** (0,70 m; kapa 1,0 m) | materiał kapy (`bridge_concrete`, jasny) i czerwony gzyms bez zmian |
| P1-4 | latarnia `p0_lamp_putry_eye` | **zrobione** | w tej gałęzi przyczyną był `clear_under_decks` + bariery w warstwie `bridge` (b1: 30 słupów usuniętych); licznik 28 → 50 z recenzji nie znajduje potwierdzenia w plikach (main: 20 przesunięć, przed 0110 klucza nie było); dlaczego latarni nie ma na samym main (tam `poles_under_decks` = 2) — nie zmierzyłem; po zmianach latarnia stoi |
| P1-5 | samotny murek `r2_fork_link_eye` | **nie** | zdiagnozowany (ADR „Otwarte” 2): odsłonięty tylny kołnierz krawężnika DK8 nad łącznicą |
| P1-6 | krzyżujące się biegi `p0_kerb_merge_eye` | **częściowo** | bieg schodzący w ziemię zniknął, biegi łączą się; przy początku pomostu łącznicy nadal krótki słupek / koniec belki |
| P1-7 | bariera przy filarze | **częściowo** | reguła `pier_guardrails`: 132 m przy 6 filarach; w kadrze `r4_pier_bz` nadal brak (filar z reguły stoi tam 13,7 m od jezdni); otoczaki — nie |
| P1-8 | pasmo jodełki wsch. | **nie zmienione, świadomie** | ortofoto 50 px/m: klin 1,1 → 3,1 m (nie stałe 2,5 m); separator betonowy i urwana linia krawędziowa: nie |
| P1-9 | nos Putry N | **częściowo** | gładka półelipsa z szarej kostki; geometria łaty nie przebudowana, z oczu różnica mała |
| P2-1…P2-7 | gzyms, lico krawężnika, bariera przy murze s1482, plac, decal, latarnie dwuramienne | **nie** | P2-7 (budżet per kamera): pełna tabela = `stats_cmp.py renders_m0_low_clear/stats.txt renders_b4_low_clear/stats.txt` |
| pkt 4 zlecenia | separator s1440, wzór „W” trawy, MA-010 | **nie** | nie starczyło czasu |

### Napisane / zbudowane / uruchomione / zmierzone
- napisane: `furniture.guardrail` (+ `_rail_posts`, `_join_free_ends`, `pier_guardrails`), zestaw `barrier_galv`, `bridge_cap_w`, tekstura
  poręczy, testy (`test_junctions_r4.py`: 3 przepisane / nowe; `test_hero_bridge.py`: szerokość pomostu 10,0–10,6 m), ADR 0117.
- zbudowane: build_world b1, b3, b4 (asset wiaduktu przebudowany Blenderem), import Unity m0 / b1 / b3 / b4.
- uruchomione + zmierzone: export-route, fidelity, swept path, kamery Low clear + High overcast (102), EditMode 261/261, PlayMode 3/3
  (`WorldCRouteTests|WorldCBarrierTests`), pytest — wyniki w linii „TESTY” niżej.
- nie uruchomione: telefon, `visual-critic`, kamery Low overcast i High clear (zlecenie: Low/High × clear/overcast — zrobione 2 z 4).

### Konflikty / pliki wspólne
`roads/build_world.py` (wpis `barrier_steel` + 4 linie po `HB.apply`), `materials_spec.json` (+1 zestaw), `sets_facade.py` (+1 funkcja),
`streetscape/furniture.py` (bariery, `clear_under_decks`, `lamps`), `streetscape/hero_bridge.py` (`pier_points`), `roads/meshing.py`
(`bridge_cap_w`), `roads/network.py`, `roads/profile.py`, `roads/standards.py`, `overrides.yaml` (3 wpisy). `game/`, `materials.py`,
shadery, `WorldPbrMaterials.cs`, `plots.py` / zabudowa: bez zmian. Uwaga dla lidera: `import-region.ps1` za każdym razem przebudowuje
wszystkie zestawy PBR (~7 min; „2 older than _src”) — obejście: `touch` na PNG w `art-source/world/materials`.

### Następny krok (lider)
`git merge junctions-r5` → build_world → export-route → fidelity → pytest → `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c`
→ `visual-critic` na `artifacts/junctions-r5/pairs_b4/` (pary zdjęcie | render) → pomiar A16.

TESTY (b4): `pytest tests/gis` 487 passed / 1 xfailed; `pytest tests/physics tests/gate3` 47 passed / 1 failed (znana 0082: `test_generator_reproduces_committed_scenarios`); EditMode 261/261; PlayMode 3/3.
