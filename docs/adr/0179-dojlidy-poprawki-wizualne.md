# ADR 0179 — Dojlidy/Krywlany: poprawki wizualne po pierwszym imporcie (landmarki, lotnisko, kamery foto)
Status: Proposed (agent world-builder, s18 + s19, gałąź `dojlidy-vis-0179`), 2026-11-13. Do scalenia przez lidera.
Poprzednik: ADR 0174 (import regionu `bialystok-dojlidy`, kamery foto), ADR 0166 (dane regionu), recenzja
`REVIEW-2026-11-13-s17-0174` (1R/4P/2N).

## Kontekst
Pierwszy import Dojlid (ADR 0174) dał kadry, których nie dało się pomylić ze zdjęciami CC0 P11
(`research/_incoming/mistral-p11-dojlidy-photos-v2/files`): lotnisko Krywlany było 54 ha betonowego placu
z ciężarówkami, łąka lotniska zarośnięta samosiejkami, hala przy Kuronia 3 bez wysokiego bloku (BDOT10k rysuje
całość jednym obrysem o wysokości LoD1 6,01 m), parking sądu pełen aut w miejscu pasa krzewów (P11-063), ślady opon
doków wychodziły na jezdnię Kuronii, kamera P11-094 patrzyła w ścianę zamiast w narożnik hali. Zakres: tylko region
`bialystok-dojlidy`; region C musi zostać bajt w bajt.

## Decyzja
1. **Nowe rodzaje `authored_overrides` (opt-in; region bez takiego wpisu nie zmienia wyniku):**
   - `kind: building_part` (`buildings_mesh.building_parts`) — osobna bryła wycięta z obrysu BDOT (`cut_from`),
     własna wysokość / kondygnacje / `set`; każdy kawałek rozciętego gospodarza zostaje budynkiem.
   - `kind: open_ground` (`vegetation`) — poligony, w których drzewa reguł (samosiejki BDOT PTTR/PTNZ, rzędy) są
     usuwane po generacji (strumienie losowe cech nietknięte, ADR 0173); drzewa `tree_groups` zostają.
   - `kind: life_rules` / `tyre_scrub_off_roads: true` (`life.tyre_scrub`) — ślady opon doków kończą się przed
     jezdnią publiczną.
   - `set: {hall_bands: false}` (s19) — hala w jednym kolorze okładziny, bez losowanego cokołu / pasa pod dachem.
   - `pitch_deg` w `control_cameras_photo.authored.json` (s19, domyślnie 0) — pochylenie kamery foto w górę;
     zdjęcia z telefonu są pochylone, a pozioma kamera ucinała halę 19 m z 42 m.
   - `lamp_rows.json` regionu + `tools/worldgen/qa/median_lamp_row.py` — rząd latarni dwuramiennych w pasie
     rozdziału, wyłącza latarnie reguły na tej ulicy.
2. **`paved.py`: BDOT KUKO „lotnisko lub lądowisko” nie jest nawierzchnią** (`KUKO_NOT_A_SURFACE`). Region C nie ma
   takiego obiektu (7 stacji paliw + 2 parkingi).
3. **Dane Dojlid** (`Data/Regions/bialystok-dojlidy/overrides.yaml`, 11 wpisów, każdy z `reason`/`confidence`/
   `verify`; bez napisów i marek):
   - Kuronia 3: wysoki blok = zachodnie skrzydło obrysu BDOT (na zachód od E 372,2; 1126 m²), **14 m
     WORKING_VALUE ±1,5 m**, 4 kondygnacje, okna pasmowe. s18 narysował tylko pasek dachu 8×37 m z wysokością 19 m
     z cienia — pierwszy render s19 pokazał płytę frontem do kamery zamiast bryły z dwiema ścianami; namiary
     z kadru P11-001 (narożnik 75,7° = wierzchołek BDOT 75,6°; koniec ściany południowej 83° = pasek dachu 83,2°)
     wskazują skrzydło. Wysokość: naczepa 4,0 m przy doku = 155 px wobec 555 px ściany → 14,3 m; z kąta 13 m.
   - Kuronia 3 hala: `hall_wall_white`; Kuronia 2: jasna ściana z grafitowym pasem pod dachem (bez liternictwa).
   - Rosti (hala północna, LoD1 18,92 m): `hall_wall_white` + `hall_bands: false` (było: kość słoniowa + czerwony
     pas — losowanie).
   - P11-063: podwójny rząd krzewów (2 linie ±1,3 m od osi z ortofoto) na pasie `unpaved_area`, kępa drzew na
     narożniku, `no_parking` w rzędzie parkingu sądu przy ulicy.
   - Krywlany: pas 09R/27L jako `paved_area` (obrys z ortofoto 2024, 30 m × ~1005 m + płyta do zawracania),
     `open_ground` (68 ha: lotnisko + łąka na N od Dywizjonu 303).
   - 31 punktów latarni Y `lamp_double_10m` w pasie rozdziału Kuronii co 35 m (WORKING_VALUE, pozycje niemierzone).
   - Kamery: `photo_P11-094` azymut 209° → 244° (namiar na narożnik NE hali + przesunięcie z piksela); `pitch_deg`
     001: 2,5 · 063: 10 · 056: 6 · 094: 8 (z wysokości horyzontu w kadrze, WORKING_VALUE ±2°).

## Wyniki (worktree, 2026-11-13)
- `build_world --region bialystok-dojlidy` (build #4, 382 s): beton placów 546 319 → 8 041 m², pas startowy
  30 153 m², 23 latarnie Y postawione (8 punktów pominiętych „carriageway”, 47 latarni reguły usuniętych), ślady opon
  168 → 68 (56 przebiegów uciętych), 1349 drzew usuniętych z łąki, auta 1091 → 1027, `tree_groups` 67 roślin / 7 kęp.
- Import: 64 chunki, Low 97,7 MB / High 213 MB (pomiar importu #3; edytor, nie telefon).
- Iteracje s19: render #1 (build #3) → oględziny 5 par → build #4 + import + render #2 → oględziny. Kadry foto:
  33–55 obiektów, 158–463 tys. trójkątów (szacunek edytora przed batchingiem, `Low-overcast-photo/stats.txt`).

## Wizualnie (Low, overcast, 1920×1080; pary zdjęcie | render w `artifacts/dojlidy-vis-0179/sbs/`)
Obejrzane (agent, Read na JPG) po renderze #1 i #2; ocena `visual-critic` należy do lidera.
| Para | Zgodne | Rozbieżne |
|---|---|---|
| `sbs-P11-001.jpg` Kuronia 3 | wysoki jasnoszary blok po lewej z dwiema ścianami (czołowa + długa wzdłuż ulicy z oknami pasmowymi), budynek biurowy w tle, biała hala z ciemnym pasem po prawej, latarnie Y w pasie rozdziału, horyzont | brama przesuwna, znak „20”, DDR z asfaltu, dok z naczepą; zielone ogrodzenie panelowe wyższe niż na zdjęciu |
| `sbs-P11-063.jpg` Mickiewicza/Kuronia | hala Kuronia 2 z grafitowym pasem po prawej, pas krzewów zamiast pełnego parkingu, sygnalizacja, dużo nieba | krzewy z przerwami (auta prześwitują), kępa drzew na narożniku to młode drzewka (na zdjęciu ~10 m), brak słupków z łańcuchem, biały budynek sądu przy lewej krawędzi kadru (na zdjęciu poza kadrem) |
| `sbs-P11-056.jpg` Dywizjonu 303 | otwarta łąka bez drzew, wlot drogi bocznej z przejściem, latarnie, znak D-6 | brak wysokiej trawy i linii lasu na horyzoncie; pojedyncze samosiejki w tle |
| `sbs-P11-094.jpg` Rosti | narożnik hali po lewej (x ≈ 220/960 wobec 205/960), jasnoszara okładzina w jednym kolorze, ściana do prawej krawędzi, przejście, latarnia | hala ~12 % wyższa w kadrze (LoD1 18,92 m dla całego obrysu), brak bram i tablicy (świadomie), znak D-6 bliżej kamery |
| `sbs-P11-129.jpg` brama szpitala | szlaban | mur, słupy, znaki, zabudowa — nie robione (P2) |

Kamery trasy (`view/route-after.jpg`): blok Kuronia 3 i szara hala Rosti widoczne z jezdni, łąka lotniska otwarta,
brak placu betonowego, brak śladów opon na jezdni Kuronii.

## Testy
- EditMode (`scripts/test.ps1 -Platform EditMode`, 21:32): 518 total, **517 passed, 0 failed**, 1 skipped (Ignored).
- `pytest tests/gis` (pełny, 21:52, 1250 s): **1071 passed, 4 failed, 2 xfailed**; `tests/gis/test_dojlidy_0179.py`
  (7 testów) zielone. Porażki:
  - `test_photo_cameras_0174::test_photo_cameras_generated[bialystok-dojlidy]` — test zakładał poziomą kamerę;
    poprawiony na `pitch_deg` (po poprawce: zielony, uruchomiony osobno).
  - `test_world_roads::test_export_is_deterministic`, `test_world_v31::test_forest_trees_reference_their_cell`,
    `test_road_fidelity::test_report_not_stale` — **nie z 0179**: zacommitowany `generated/*` regionu C w main jest
    starszy niż wejścia (chunk 0_0 w main `8424bb32…`, a build w każdej gałęzi na tej bazie daje `e3ecabed…`:
    dojlidy-vis-0179, p1b-0172, horizon-0170, gates-s19, atlas-0184), `fidelity_qa.json` nieaktualny względem
    `overrides.yaml` / `build_world.py` (wymaga `fidelity/run.py` po scaleniu — `build_world.py` zmienia też 0179).
  - Przebieg s18 (20:37) miał dodatkowo `test_parts_hash_independent_of_pythonhashseed` — podproces 0xC0000142
    po śmierci sesji; w przebiegu s19 zielony.
- Region C bez różnic: build C z pytest (kod 0179) porównany per chunk (sha256, 64 chunki) z gałęziami
  `p1b-0172` (różne 1_3, 1_4, 2_4, 6_6 — `paved`) i `gates-s19` / `tower-0180` (różne 4_5, 6_5, 6_6, 7_5 —
  `buildings`); zbiory rozłączne poza 6_6, gdzie każda z nich zmienia inną warstwę → 0179 nie zmienia żadnego chunku.
  Pliki `generated/*` regionu C przepisane przez pytest zostały cofnięte (`git checkout`), nie są w commicie.

## Otwarte (follow-up)
- **Słupki biało-czerwone z łańcuchem (P11-063, P11-001)** — brak prototypu; nowy prototyp = zmiana wspólnej
  biblioteki ulicy regionu C → osobne zadanie lidera.
- Brama szpitala P11-129 (mur z cegły, słupy, STOP, B-33 „20”, szlaban) — nie robione (P2); kadr `129b` pokazuje tylko
  szlaban reguły.
- P11-001: brama przesuwna i znak „20”/„droga wewnętrzna” przy wjeździe, DDR z czerwonego asfaltu po lewej (w grze
  chodnik z kostki), wysokie ogrodzenie panelowe zasłania dół hali.
- P11-056: wysoka trawa / nieużytek i linia lasu na horyzoncie (far-field) — poza zakresem (D51: układ, nie trawa);
  samosiejki zostają tylko w wycięciu `open_ground` przy ogródkach (E −780…−560, N 300…400).
- Oznakowanie pasa startowego (linie krawędziowe, próg) nie rysowane; płyta lotniska bez dylatacji.
- Wysokość bloku Kuronia 3 (14 m) i liczba kondygnacji — do potwierdzenia zdjęciem właściciela; pozycje latarni Y.
- `generated/world_manifest.json` regionu C w main jest nieaktualny względem wejść (test
  `test_export_is_deterministic` pada w każdym worktree na bazie d515371f5) — lider regeneruje po scaleniu.

## Konsekwencje
- Region C: żaden z nowych rodzajów nie występuje w jego danych (test `test_region_c_has_no_0179_overrides`,
  `test_hall_bands_and_camera_pitch_are_opt_in`); build C kodem 0179 (z pytest) = per chunk identyczny z buildami
  niezależnych gałęzi `tower-0180` / `p1b-0172` poza ich własnymi chunkami (60/64 i 60/64, różnice rozłączne
  z wyjątkiem 6_6, gdzie tower zmienia `buildings`, a p1b `paved`).
- Dane `generated/*` Dojlid są zacommitowane po buildzie #4; GLB poza gitem (ADR 0011).

## Odtworzenie
```
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy
pwsh scripts/import-region.ps1 -Region bialystok-dojlidy
pwsh scripts/visual-qa.ps1 -Scene World_bialystok-dojlidy -Tier Low -Lighting overcast -Width 1920 -Height 1080 `
  -Cameras 'photo_P11-001,photo_P11-063,photo_P11-056,photo_P11-094,photo_P11-129b' -OutputDir artifacts/dojlidy-vis-0179/Low-overcast-photo
bash artifacts/dojlidy-vis-0179/sbs.sh artifacts/dojlidy-vis-0179/Low-overcast-photo
```
