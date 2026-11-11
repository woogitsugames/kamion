# ADR 0117: Węzły r5 — bariery: profil W, słupki C z przekładką, ocynk zmatowiały, kapa pomostu Bieżeństwa 1,0 m, łączenie biegów

Status: przyjęty (world-builder, gałąź `junctions-r5`), 2026-11-11. Wynika z `docs/reports/visual/REVIEW-2026-11-11-s10-0110.md`
(„Lista na r5”, pkt 4 bramki 3). Powiązane: ADR 0110 (bariery r4), 0067 (wiadukt hero), 0105 (konstrukcja pod pomostem DK8 —
nietknięta), 0102 (meble uliczne), 0022 (zestawy PBR). Dowody: `artifacts/junctions-r5/` (STATUS.md, `renders_m0_*` = main
f260ab36, `renders_b*_*`, `pairs_*` = zdjęcie | render, `logs/`, `scripts/`).

## Kontekst
1. **Taśma W jak rura, belka „na” słupkach** (P1-1): profil 5 punktów o wspólnych wierzchołkach — eksporter wygładza normalne w
   obrębie części, więc fałdy cieniowały się jak walec; słupek = prostopadłościan 10 × 5 cm pod belką.
2. **Biały płotek** (P1-2): `barrier_steel` 0,55 / metal 0,9 bez tekstury odbijał niebo — najjaśniejszy obiekt kadru.
3. **Kapa jak chodnik** (P1-3): kapa 1,5 m, lico belki 1,12 m za licem krawężnika (zdjęcie Mapillary 454716650857984: ~0,7 m).
4. **Krzyżujące się biegi, koniec w powietrzu** (P1-6, `p0_kerb_merge_eye`): bieg reguły (`c:w1101181473…:L`) i bieg autorski
   `dk8-ramp-split-barrier` spotykały się przy E −765 z różnym offsetem; dedup ucinał drugi w powietrzu, pierwszy 2 m dalej
   schodził terminalem w ziemię.
5. **Latarnie na kapach** (P1-4): zmierzone — na main (f260ab36) `poles_under_decks` = 2, latarni na kapie w `p0_lamp_putry_eye`
   nie ma (`renders_m0_*`); w b1 tej gałęzi `clear_under_decks` usunął 30 słupów: od 0110 bariery pomostów leżą w warstwie
   `bridge`, a ich górne belki 0,7–1,1 m nad kapą były czytane jako „pomost nad słupem”. Licznik `support_adjustments` z recenzji
   (28 → 50) nie zgadza się z plikami: przed 0110 klucza nie było, na main jest 20 pozycji (11 × lamp_12m), w tym żadna na pomoście.
6. **Brak bariery przy filarze** (P1-7): reguła `structure` działa po łańcuchach; filar przy rondzie stoi przy płycie
   skrzyżowania / pierścieniu.

## Decyzja
1. **Profil W** (`furniture.W_PROFILE`, `guardrail`): 310 × 83 mm, 7 punktów, 6 płaskich faset, każda z własnymi wierzchołkami
   (twarde krawędzie); tył blachy 2 fasety; lico belki tam, gdzie było (0,133 m przed linią słupków → kolizja i prześwity bez
   zmian); kolizja = lico. Położenie fałd WORKING_VALUE.
2. **Słupki**: C 100 × 55 (środnik w poprzek drogi), przekładka 0,10 m między półką a doliną belki — belka wisi na licu słupka,
   słupek kończy się 3 cm pod górną krawędzią; na gruncie co 4,0 m (`GUARDRAIL_POST_SPACING_GROUND`, klasa SP-05/4; zdjęcia:
   2–4 m „na oko”, WORKING_VALUE); na pomoście C 120 × 64 na stopce, co 2,0 m.
3. **Bariera pomostu** (`tall`): taśma W (góra 0,75 m) + górna belka skrzynkowa 100 × 80 (góra 0,98 m, `BRIDGE_BARRIER_H`), na
   końcach schodząca za taśmę W; bez pochwytu i płaskownika z 0110. Wzór: Mapillary 454716650857984 (niska taśma W + druga
   belka na krótkich, ciężkich słupkach ze stopkami; za nią osobna poręcz z poziomymi linkami).
4. **Poręcz na krawędzi pomostu Bieżeństwa** wraca do assetu hero (`set: {rail_h_m: 1.10, rail_inset_m: 0.08}` w override
   `andersa-viaduct-biezenstwa-hero`; `DEFAULTS` bez zmian, żeby spec 0105 się nie zmienił): jeden alfa-testowany
   quad na przęsło, tekstura `viaduct_steel.png` — 6 poziomych prętów + górny płaskownik zamiast szczebelków (Mapillary
   500263111404933, 1259231227807789 od dołu). Ma LOD-y assetu, materiał `viaduct_steel` już był w assecie.
5. **Materiał** (`build_world.MATERIALS["barrier_steel"]`): 0,13 / rough 0,65 / metal 0 + zestaw `barrier_galv` (nowy,
   `sets_facade.barrier_galv`, 4,0 × 0,5 m, UV0 = metry wzdłuż belki / rozwinięcie profilu, `set_tile`): patyna cynku, styk na
   zakład z 8 śrubami, śruba słupka, kurz na fasetach patrzących w górę, bryzgi przy dolnej krawędzi, zacieki, rzadka rdza.
   Albedo dobrane w kadrze (WORKING_VALUE): zdjęcie 454716 belka sRGB 74–102 przy asfalcie 63; render b1 z 0,25 dawał 185 przy 60; 0,11 (b3) w cieniu schodziło do czerni → 0,13.
   `materials.py`, shadery, `WorldPbrMaterials.cs`: bez zmian (zestaw modulacyjny obsługuje istniejąca ścieżka).
6. **Kapa pomostu Bieżeństwa 1,0 m** (`bridge_style.cap_w`, `meshing.bridge_cap_w`, `network.structure_sides`): tylko ten
   wiadukt; pomost węższy o 0,5 m z każdej strony zewnętrznej, gzyms assetu idzie za krawędzią; jezdnia, dźwigar skrzynkowy,
   filary i konstrukcja 0105 pod DK8 bez zmian (`deck_before_sha256` = `deck_after_sha256` w `hero_bridges.underdeck`).
   Linia słupków: lico belki 0,70 m za licem krawężnika (`BRIDGE_BARRIER_FACE_M`), min. 0,32 m od krawędzi kapy; pozostałe mosty
   (kapa 1,5 m): 0,40 m od krawędzi jak w 0110. Latarnia na wąskiej kapie staje przy krawędzi, za barierą.
7. **Jeden bieg zamiast dwóch** (`_dedup_guardrail`, `_join_free_ends`, `guardrails`): biegi autorskie budowane pierwsze; bieg
   ucięty przez dedup dochodzi łukiem (8 m) do biegu, który go uciął (≤ 4 m), a koniec tamtego traci terminal w ziemię (kolejka
   `lin.rail_queue`); wolny koniec biegu stojący ≤ 4 m od innego biegu na tym samym poziomie (|Δz| < 1 m) też do niego dochodzi
   (nos V / Y jak na ortofoto E −781 N 76,5). Build końcowy: 5 + 8 połączeń.
8. **Latarnie**: `clear_under_decks` nie liczy `barrier_steel` jako pomostu.
9. **Bariera przy filarze** (`pier_guardrails`, po `HB.apply`): filar (kolumny hero + cylindry generyczne) ≤ 4,5 m od obrysu
   asfaltu naziemnego → taśma W 8 m w obie strony + terminale, 0,75 m za krawędzią (bliżej, gdy filar nie zostawia miejsca),
   dedup tylko z biegami naziemnymi (bariery pomostów przechodzą górą — w b3 kasowały wszystko). WORKING rule; pozycje filarów
   hero są z reguły (rozpiętość 25 m), nie z pomiaru. Build końcowy: 132 m przy 6 filarach (3 × Bieżeństwa, 3 × DK8 Putry).
10. **Nos mediany Putry N**: półelipsa 12 odcinków z szarej kostki (była półośmiokątna, beżowa), czubek N 128,8.
11. **Budżet**: półki słupków jednostronne, przekładka = 2 boki, stopka = wierzch, górna belka bez spodu, Douglas–Peucker belek 2 cm.

## Otwarte / niezrobione
1. **Telefon** — brak (agent nie używa adb); budżet tylko z edytora.
2. **Samotny murek `r2_fork_link_eye`** (P1-5): zdiagnozowany, NIE naprawiony — to tylny kołnierz krawężnika `c:w1101181473…:L:7`
   (curb_concrete, z 130,86–132,24, E −353,7…−342,8, N −142…−133,4; stacje s 596–610 łańcucha, bok miejski bez chodnika, `verge`
   0,75–1,0 m). Jezdnia DK8 leży tam 0,45–0,65 m nad łącznicą w173956083 biegnącą tuż obok; pas trawy `:vg` istnieje, ale jest
   zwężony do połowy odstępu i jego skarpa nie sięga terenu łącznicy, więc kołnierz zostaje odsłonięty. Poprawka: skarpa pasa do
   poziomu sąsiedniej jezdni (albo kołnierz w materiale trawy) w `meshing._emit_verge` + test `kerb_rise.py` dla kołnierzy.
3. **Pasmo jodełki rozdziału wsch.** (P1-8): nie zmienione. Pomiar na ortofoto 50 px/m (`artifacts/junctions-r4/trace/e_split_band.jpg`):
   pasmo ma 1,1 m przy E −830,6 i 3,1 m przy E −806,2 — jest klinem, nie stałym pasmem 2,5 m; override ma 0,75 → 2,75 m
   (różnica ≤ 0,35 m, w tolerancji odczytu). Separator betonowy z barierą za E −788 i urwana linia krawędziowa łącznicy: nie ruszone.
4. **Nos Putry N**: nadal domknięcie, nie odwzorowanie (rzeczywisty czubek N 131,7; mediana generatora sięga N 130); z oczu
   różnica względem main jest mała (`pairs_b4/ba_r4_putry_nose_eye.jpg`).
4a. **`p0_kerb_merge_eye`**: częściowo — bieg schodzący w ziemię pod barierą pomostu zniknął, biegi łączą się na wyspie; po lewej
   przy początku pomostu łącznicy nadal stoi krótki słupek / koniec belki obok bariery pomostu.
4b. **`r4_pier_bz`**: w tym kadrze bariery przy filarze nadal nie ma — filar z reguły stoi tam 13,7 m od jezdni (na zdjęciu przy
   krawężniku ronda); reguła zadziałała przy innych filarach.
5. **Łoże z otoczaków przy filarze** (zdjęcie 177786140912399), okrągłe filary — do 0105 / assetu hero.
6. Kapa: materiał `bridge_concrete` bez zmian (kolor / spoiny — runda materiałowa); czerwony gzyms (P2-1, P2-2) bez zmian.
7. Punkt 4 zlecenia (separator s1440, wzór „W” trawy, linie MA-010): nie ruszone.
8. Balustrada generyczna innych mostów (`meshing.build_bridge_extras`) ma UV w metrach świata — tekstura `barrier_galv` jest
   na niej rozciągnięta w pionie (smugi); do poprawy przy okazji.

## Pliki wspólne
- `roads/build_world.py`: wpis `barrier_steel` (wartości + `texture_set`), wywołanie `pier_guardrails` (addytywnie).
- `art-source/world/materials/_src/sets_facade.py` (+`barrier_galv`), `materials_spec.json` (+1 zestaw), `sets_viaduct.railing_texture`,
  `art-source/world/textures/viaduct_steel.png`, asset `viaduct_biezenstwa` przebudowany (spec: `rail_h_m`, węższy pomost).
- `streetscape/furniture.py`: `guardrail*`, `_dedup_guardrail`, `pier_guardrails`, `clear_under_decks` (1 linia), `lamps` (1 warunek).
- `streetscape/hero_bridge.py`: `DEFAULTS` (2 wartości), `pier_points` (nowa). `roads/meshing.py`: `bridge_cap_w`;
  `roads/network.py`, `roads/profile.py`: szerokość kapy z `bridge_cap_w`. `roads/standards.py`: stałe barier.
- `overrides.yaml`: `cap_w` w `andersa-viaduct-biezenstwa-style`, wielokąt `putry-n-median-nose`.
- `game/`: bez zmian.

## Wynik (build końcowy b4 względem main f260ab36 zaimportowanego w tym samym projekcie — `renders_m0_*`)
- Low clear, 102 kamery (`stats.txt`): draws −12…+0 (żadna kamera na plusie), tris max +1,1 % (`g3a-eye-s0262`, `stretch-03`);
  High overcast: draws max +0, tris max +1,0 %. Uwaga: `renders_b0_*` to import sprzed 0110 skopiowany z main — nie jest bazą.
- `guardrails_m`: bridge 2916, median 1133, embankment 482, structure 529 → 603, authored 36, pier 0 → 132.
- latarnie: `poles_under_decks` 2 → 3 (trzecia: latarnia jezdni pod pomostem, prawdziwy przypadek), lamp_12m 165 → 166;
  latarnia na kapie w `p0_lamp_putry_eye` jest (na main jej nie ma).
- swept path G3-A −0,10 / −1,12, G3-B −0,14 (= main); prześwit do propów G3-A 0,69–0,70, G3-B 0,86–0,88 (= main); fidelity
  krawędzi p50 0,36 / p95 2,304 (= main); road_consistency 65 (= main); ściany terenu 4 / 0,345 (= main).
- konstrukcja 0105: `deck_before_sha256` = `deck_after_sha256`, `deck_barriers_unchanged` true dla obu pomostów DK8.
- testy: `pytest tests/gis` 487 passed / 1 xfailed; physics + gate3 47 passed / 1 failed (znana 0082); EditMode 261/261; PlayMode 3/3.
- swept path RING-B, prześwit do propów: 1,88 / 2,28 → 1,31 / 1,79 m (opony bez zmian); przyczyna nie zmierzona (UNVERIFIED).
