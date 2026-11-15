# ADR 0213 — woda w dk65-03 (ciągłość na szwie), kolor tafli wg ortofoto, pas trzciny i krzewów na brzegach
Status: Proposed (agent world-builder, s20, gałąź `water2-0213`), 2026-11-15. Do scalenia przez lidera.
Powiązane: ADR 0210 (etap wody, otwarte p. 1, 2, 4, 5), ADR 0132 (korony z ortofoto, `plot_canopy`), ADR 0124
(Kamion/World PlotKit), ADR 0173 (determinizm), docs/06 §6 (budżety).

## Kontekst
ADR 0210 włączył wodę tylko w `dk65-02`. Otwarte: (1) tafla z góry za ciemna / za szara względem ortofoto, na Low
z bliska prawie czarna; (2) brzegi „czyste” — równa linia skoszonej trawy, na ortofoto pas szuwarów i krzewów;
(4) Supraśl płynie dalej przez `dk65-03`; (5) decyzja o C (Biała).

## Decyzja
1. **`dk65-03`: `Region.water = True`** (`regions.py`, `build_region` → `generated/water_sources.json`: BDOT10k
   OT_PTWP_A Supraśl 54 778 m², 9 stawów; OSM 9 obszarów, 1 `intermittent` pominięty; 2 osie SWRS). Kamery:
   `top_water_seam`, `top_water_mid`, `water_bank_mid`, `water_close_bank`, `water_oblique_east`; w `dk65-02`
   dodane `water_deck_west` (z mostu na zachód, ku szwowi) i `top_water_seam_w`.
2. **Szew poziomu (reguła symetryczna)** — `water.Plan._seam_levels`: każdy kafel liczył poziom z własnych stacji
   (mediana okna i bieżące minimum w dół rzeki zaczynają się na jego końcu osi), więc na wspólnej krawędzi
   02|03 różnica wynosiła ~3 cm (02: 110,163–110,193 m, 03: 110,132–110,160 m, zmierzone na wierzchołkach tafli
   GLB, `artifacts/water2-0213/tools/seam.py`). Wspólna kolumna NMT jest identyczna w obu kaflach, więc dla każdego
   przecięcia wody z krawędzią kafla poziom = 30. percentyl NMT na węzłach przecięcia, dokładnie na krawędzi,
   z liniowym zanikiem korekty na `SEAM_BLEND_M` = 120 m w głąb. Oba kafle liczą tę samą wartość z tych samych
   danych — bez zależności między kaflami.
3. **Kolor / jasność tafli** — pomiar (`tools/water_rgb.py`: maska wody BDOT/OSM zerodowana 3 m, bez 14 m wokół
   mostów; kamera z góry 150 m, ten sam ślad co wycinek ortofoto 2024-05-27):
   | ujęcie | ortofoto mediana sRGB | woda/łąka (lum. lin.) | render 0210 Low | render 0210 High |
   |---|---|---|---|---|
   | dk65-02 `top_bridge` | 44/50/54 | 0,41 | 30/32/32 (0,09) | 35/38/39 |
   | dk65-03 `top_water_seam` | 46/50/54 | 0,31 | 31/33/32 | 37/39/39 |
   | dk65-03 `top_water_mid` | 52/53/57 | 0,40 | 31/33/32 (0,06) | 36/39/39 (0,08) |
   Rozkład (render z czarną tonią): odbicie + mgła dają 27/29/30 — **ciało wody wnosiło prawie nic**: shader
   oświetlał toń `0,55·sin(h)·słońce`, ~13× słabiej niż grunt obok. Zmiany (`WorldWater.shader`):
   - toń oświetlona jak grunt: `body·(SH + słońce·N·L·cień)`; albedo toni (WORKING_VALUE, dopasowane do ortofoto)
     `water.color` 0,120/0,120/0,115 (głęboko), `shallow` 0,150/0,145/0,115 (przy brzegu); niebieski odcień wody na
     ortofoto jest częściowo zamgleniem nalotu (ta sama dominanta na łące) — toń neutralno-ciepła, błękit daje odbicie;
   - **odbicie dalekiego brzegu**: promień odbity poniżej `bank_horizon` (sin 0,10) trafia w trzcinę / zarośla
     przeciwległego brzegu, nie w niebo — `env` mieszany do `bank_tint` (0,050/0,065/0,035 × SH + 0,3 słońca);
     jedna interpolacja, oba tiery;
   - Low: usunięta szeroka plama połysku (płaska normalna dawała sztuczną smugę światła), zostaje mała tarcza
     słońca; `reflect_low` 0,55 → 0,70. **Koszt Low bez zmian**: nadal jedno pobranie sondy, bez tekstur, bez
     szumu (−1 pow o niskim wykładniku, +1 smoothstep + lerp);
   - High bez zmian strukturalnych (2 oktawy zmarszczek, ostra sonda, glint) + odbicie brzegu;
   - `RegionImporter.WaterMaterial` zapisuje **wszystkie** parametry z manifestu (`flow_cycle_s`, `ripple_m`,
     `ripple_slope`, `smoothness`, `bank_tint`, `bank_horizon`; brak klucza = domyślna wartość shadera) — materiał
     z 0210 miał nieaktualne 1,6 m / 0,10 zamiast 2,4 m / 0,05.
4. **Brzegi: pas szuwarów (trzcina, mozga, turzyce) + krzewy wierzbowe / olchy** — jak ADR 0132 ortofoto jest
   wzorcem, nie teksturą:
   - `streetscape/water_banks.py` (CLI, offline) → `Data/Regions/<id>/water_banks.json` (w gicie, 02: 141 KB,
     03: 81 KB): wzdłuż linii brzegu co 1 m (zapis co 2 m) idzie na zewnątrz i mierzy szerokość pasu „szorstkiej”
     roślinności zielnej (odchylenie luminancji w 2,25 m > 9, zieleń/słoma, nie korona drzewa; łąka koszona jest
     gładka), mediana z 9 próbek, pas ≥ 1,5 m; drogi + 3 m wyłączone. Korony zdrewniałe = ciemna (lum. < 72) część
     maski koron `plot_canopy`, r ≥ 1 m, do 18 m od wody, poza lasami BDOT. Wynik: dk65-02 pas na 7,6 z 10,6 km
     brzegu (72 %), 451 koron; dk65-03 3,4 z 5,6 km (60 %), 879 koron (podglądy `artifacts/water2-0213/banks/`).
   - `streetscape/reeds.py`: **wstęgi wzdłuż brzegu** (nie karty na kępę): rzędy co 1,7 m, rząd 0 w wodzie
     (stopa pod taflą, trzcina 2,3 m ± 25 %), dalsze niższe (1,75 / 1,45 m), zygzak w planie ± 0,28 m, szum
     wysokości, zwężanie na końcach; tekstura `water_reeds` (1024×512, rysowana proceduralnie: łodygi, liście
     Phragmites, wiechy, suche zeszłoroczne źdźbła; kafelkuje w u, 4 m) — materiał `water_reeds` = Kamion/World
     PlotKit (liście oświetlane normalną z COLOR_0, okluzja u stopy). Warstwa `banks` (High: do 3 rzędów, odcinek
     2 m) / `banks_low` (Low/Medium: 2 rzędy, odcinek 4 m), LOD0–LOD1 chunka, bez cieni.
   - Krzewy: korony r < 2,2 m → `tree_shrub` (zarośla wierzbowe 2–4,5 m), większe → `tree_alder` (olsza czarna
     8–16 m) — istniejące prototypy, instancje; ≥ 2,5 m od istniejących drzew, nie na drogach / w wodzie; ziarno
     z sha1 pozycji, dopisane po `VG.place` / HLOD lasu (strumień RNG regionu nietknięty).
5. **C (Biała) — ocena, NIE włączone** (p. Ocena C niżej).

## Ocena włączenia wody w C (`bialystok-industrial-c`)
Sondowanie źródeł (`tools/c_probe.py`, nic nie zapisane do `Data/`): Biała 937–939 m w kaflu, **bez poligonu BDOT**
(tylko oś SWRS `szerokosc` 4 m) i OSM `waterway=river` bez `width`; strumienie OSM ~1,5 km (+ przepusty pominięte);
9 obszarów wody (6 × `reservoir` 104–208 m² = osadniki oczyszczalni, 3 × 97–336 m²).
- **Wpływ na trasę/obraz:** Biała leży ≥ 572 m od trasy startowej C (narożnik SW kafla) — z kabiny prawie
  niewidoczna. Dwa strumienie biegną 10 m i 39 m od trasy: wcięcie koryta przy nasypie (`ROAD_KEEP_M` 2 m) wymaga
  przeglądu na kamerach trasy.
- **Błędy danych do poprawy przed włączeniem:** (a) bez poligonu Plan buforuje oś OSM szerokością domyślną 8 m,
  a BDOT mówi 4 m — trzeba brać `szerokosc` SWRS przed domyślną; (b) osadniki oczyszczalni (`reservoir`, za
  ogrodzeniem `access=no`) to zbiorniki betonowe nad terenem — płaska tafla na p30 NMT byłaby błędna (wyłączyć
  `reservoir` w obrębie `landuse=industrial`/`man_made=wastewater_plant` albo modelować osobno).
- **Determinizm C:** zmienią się wszystkie chunki z wodą (teren LOD0–3 przez wcięcie i maskę min-filtra, kolory
  gruntu, kolizja terenu, tafla, pas trzciny, instancje drzew w wodzie i krzewy), `world_manifest.json`,
  `streetscape_qa.json`, nowe `water_qa.json` / `water_sources.json` / `water_banks.json`; nowa linia bazowa
  determinizmu (ADR 0173 / test `test_determinism`), odświeżenie `fidelity_qa.json` i dowodów bramki 3
  (`gate3_cameras`, ujęcia sbs) — praca lidera, nie agenta.
- **Budżet (szacunek, nie zmierzone):** tafla ~6–10 tys. m² → ~1,5–2,5 tys. trójkątów na cały kafel; pas trzciny
  ~1,5 km brzegu → ~2–3 tys. tris High / ~1 tys. Low; +1 draw (tafla) +1 (trzcina) na chunk z wodą w kadrze.
  Pomijalne wobec budżetu docs/06 §6.
- **Rekomendacja:** nie teraz. Włączyć razem z poprawkami (a)–(b), jedną świadomą zmianą linii bazowej C
  i odświeżeniem fidelity / bramki 3, po decyzji właściciela (Biała z trasy nie jest widoczna — zysk mały).

## Budżet (visual-qa 1920×1080, edytor, szacunek przed SRP batching; telefon NIE mierzony)
A = 0210 r3 (`artifacts/water-0210/dk65-02/r3/*/stats.txt`), B = 0213 r5 (`artifacts/water2-0213/dk65-02/r5`), scena
Low (`World_dk65-02`):
| kamera (Low) | draws A → B | trójkąty A → B |
|---|---|---|
| `top-bridge` | 21 → 23 | 51,3 → 52,0 tys. |
| `drive-bridge-approach` | 32 → 33 | 74,6 → 74,9 tys. |
| `water-bank-west` | 149 → 150 | 159,2 → 159,6 tys. |
| `water-deck-east` | 87 → 89 | 138,3 → 139,1 tys. |
| `water-oblique-bridge` | 31 → 33 | 72,3 → 73,0 tys. |
| `rev-elcka`, `route-s0450` (max trasy), `drive-s19-approach` | bez zmian | bez zmian |
Koszt Low: ≤ +2 draws (materiał `water_reeds` w chunkach z brzegiem), ≤ +0,8 tys. trójkątów na klatkę; shader wody
Low: ta sama liczba pobrań tekstur (1 sonda). Cały kafel: `banks_low` 02: 6,6 tys. tris (max 0,57 tys./chunk),
03: 2,9 tys.; krzewy 02: 270 `tree_shrub` + 34 `tree_alder`, 03: 580 + 93 (instancje istniejących prototypów,
impostory). High (`banks`, karty-namioty r6): patrz Walidacja (liczby r6); **uwaga**: ADR 0210 i r1–r5 tego zadania
renderowały „High” na scenie Low (`World_<id>` z `-Tier High` = shader High, geometria Low); od r6 łańcuch używa
`World_<id>_High`. Sceny High (r5H, cała zawartość High) mają 0,8–1,0 mln tris na kamerach wodnych `dk65-02` — to
głównie istniejąca zawartość High (las, krzewy, teren LOD0), nie woda; pomiar telefonu (flagowiec, profil High) otwarty.

## Walidacja
- Szew 02|03 (`tools/seam.py`, wierzchołki tafli GLB na x = 768 779): przed 110,163–110,193 | 110,132–110,160 m,
  po: **110,179 | 110,179 m**, zasięg wody n −330,5…−306,2 m identyczny. Dno pod taflą na szwie różni się do
  0,25 m (odległość od brzegu `d_in` liczona w kaflu) — niewidoczne pod nieprzezroczystą taflą; brzeg i próg
  identyczne (≤ 3,6 cm).
- Kolor z góry (mediana sRGB tafli, `top_bridge` 02 / `top_water_mid` 03): ortofoto 44/50/54 i 52/53/57; render
  przed (0210) Low 30/32/32 i 31/33/32, High 35/38/39 i 36/39/39; **po: Low 48/49/47 i 49/49/47, High 54/54/52
  i 54/55/52** (jasność jak ortofoto; odcień cieplejszy o ~7 w B — świadomie, patrz Decyzja 3).
- Determinizm (etap wody wyłączony): `build_world` na tej gałęzi dla C i Dojlidy — `world_manifest.json`,
  `far_field_qa.json`, `<id>-far-field.manifest.json` **identyczne** z main (`artifacts/water2-0213/determinism.txt`).
  `fidelity_qa.json` C: odświeżony tylko hash `build_world.py` (wynik C bez zmian).
- `pytest tests/gis`: **1223 passed, 3 xfailed**, 1 odznaczony (`test_road_stage_independent_of_hash_seed`, 3 × pełny
  build C); nowe `tests/gis/test_water_0213.py` 6/6 (szew symetryczny na dwóch syntetycznych kaflach, wstęgi High/Low
  poza keep-out, krzewy i odstęp od drzew, tekstura kafelkuje i jest przycinana, izolacja C/Dojlidy, produkty
  `water_banks.json`); `test_water_0210.py` zaktualizowany (2 regiony z wodą, 3 strażniki w stage).
- EditMode: 587, **586 passed, 0 failed**, 1 skipped (`artifacts/water2-0213/tests/editmode-20261115-092220.xml`).
- Import bez błędów shadera / C#. Pętla wizualna (6 rund, `artifacts/water2-0213/{dk65-02,dk65-03}/r1..r6/view/`,
  strojenie `tune/`): r3 trzcina jak limonkowy żywopłot → r4 kępy z przerwami, ciemniejsza paleta → r4 z bliska
  „płetwy” (wstęga widziana wzdłuż brzegu) → r5 High = skrzyżowane karty (z daleka czyta się jak szuwar, z bliska
  pionowe krawędzie kart) → r6 karty-namioty. Low: tafla już nie czarna (z bliska ciemnoszara z odbiciem nieba).

## Otwarte
1. **Telefon**: brak pomiaru (Low: shader bez dodatkowych pobrań; High: +tris kart trzciny, alpha-test na Mali —
   UNVERIFIED). Zmierzyć na A16 (Low) i flagowcu (High) z kamerą przy moście.
2. Kolor i trzcina strojone tylko na ortofoto (nadir) i renderach — **brak zdjęcia z brzegu Supraśli/Białej**
   (prośba do właściciela: 2–3 zdjęcia z mostu DK65 i z brzegu, lato). Wartości WORKING_VALUE.
3. Trzcina z bliska (< 10 m) nadal widać pojedyncze karty; docelowo LOD0 z kępami krzyżowymi o losowym skręcie
   i tekstura z fotoskanu CC0 (brak w repo).
4. Pas szuwarów z ortofoto jest szeroki (do 24 m), geometria buduje ≤ 4 rzędy (~5,5 m) — reszta pasa to kolor gruntu
   (wysoka trawa 6 m z ADR 0210); poszerzyć maskę `unmown` do szerokości pasu.
5. `tree_shrub` z bliska wygląda jak pochylony krzak-miotła — prototyp wierzby (Salix cinerea) do zrobienia w
   `make_trees.py`.
6. Krawędź kafla bez sąsiada z wodą też dostaje korektę poziomu (02 E: Biała +9 cm na krawędzi, 03 W: +1 cm) —
   nieszkodliwe; po włączeniu wody w `dk65-01` / kaflu na zachód od 03 szew będzie ciągły automatycznie.
7. Sceny „High” w ADR 0210 były renderowane na geometrii Low — dowody 0210 High dotyczą tylko shadera.
8. C — patrz Ocena C (rekomendacja: później, z poprawkami szerokości z SWRS i wykluczeniem osadników).
