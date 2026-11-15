# ADR 0189 — Brama szpitala przy Żurawiej (P11-129): zestaw `masonry_gate`
Status: PROPOSED (runda `r4`, gałąź `hospgate-0189`), 2026-11-15. Do scalenia przez lidera.
Poprzednik: ADR 0179 (P11-129 poza zakresem), `REVIEW-2026-11-13-s19-0179.md` (P11-129 = N, „dla bramki 3 P0”), `REVIEW-2026-11-14-s20-mistral-m62.md` §7, `REVIEW-2026-11-14-s20-mistral-m62-fix.md` (`M62-FIX`).

## Kontekst
Kadr CC0 P11-129 (Rakoon, Commons, 2019-11-10) pokazuje wjazd na teren szpitala od ul. Żurawiej (~16,4 m na E/NE, kierunek wjazdu `~242°` w siatce EPSG:2180). W grze stał tam szlaban reguły, białe ogrodzenie panelowe i pusta bryła portierni oraz dominujący 4-kondygnacyjny szary blok z BDOT10k 2024. OSM ma tylko `barrier=lift_gate` (węzeł `2448457849`) i linię `barrier=fence`; BDOT10k ma obrys portierni (`bdot:8243ac9d`).

Ustalenia z kadru F01 (`P11-129`) i scalonego researchu `M62-FIX` (`research/mistral/p19-hospital-gate/`):
- **Mur**: jasna cegła silikatowa/klinkier, wysokość ~1,85 m + płaska betonowa nakrywa 0,06 m, **jeden** filar końcowy (~2,12 m + czapa, bez daszka); pełny mur ograniczony do odcinka widocznego w F01 (~6,2 m, `WORKING_VALUE` — na F14/F19 dalsze ogrodzenie ma przęsła); **5 poziomych bordowych tablic** w 2 kolumnach (2 po lewej + 3 po prawej przy filarze).
- **Ganek (strona N)**: 2 ceglane filary pod wspólnym zadaszeniem z ciemnej blachy trapezowej na jasnej betonowej belce (spód ~2,65 m); na szerokim filarze wyblakły `B-20 STOP` (0,8 m) i niebieska tablica `WJAZD NA PODSTAWIE`; przed prawym filarem **niebieska tablica izby przyjęć (`IZBA PRZYJĘĆ`) na własnym białym słupku**.
- **Szlaban i znaki**: czerwona obudowa napędu + biało-czerwone ramię z niebieską tabliczką `OPŁATA ZA WJAZD 3 zł`; słupek przy szlabanie z latarenką, `C-2` (strzałka w górę i w prawo = skręt za znakiem) nad `B-33 „20”` i małą tabliczką; znak `B-2` na osobnym słupku w głębi (~24 m za bramą, `WORKING_VALUE`).
- **Tło i zieleń**: niskie 1–2-kondygnacyjne beżowe/kremowe budynki szpitalne w tle + 2 smukłe kominy kotłowni (~13,5 m) zamiast 4-kondygnacyjnego szarego bloku (`bdot:2BE4B431-AAE9` obniżony do 2 kondygnacji beżowych, dodane niskie `building_part` `zurawia-hospital-bg-yellow` i `zurawia-hospital-bg-cream` z `plaster_beige`); gęste kolumnowe iglaki (`thuja`, 8–9,5 m) za lewym murem i w głębi.

## Decyzja
1. Nowy rodzaj `authored_overrides`: **`kind: masonry_gate`** (`tools/worldgen/streetscape/masonry_gate.py`).
   Geometria w układzie bramy: początek `anchor.at_en` `[327.1, 808.4]`, `enter_bearing_deg: 242.0`, `l` = w prawo od wjeżdżającego, `a` = ku ulicy. Elementy: `walls` (linia, filar, opcjonalna płaska nakrywa betonowa, tablice 2+3), `piers`, `canopy`, `platform`, `faces`, `boards`, `posts` (w tym biały słupek tablicy IP i słupek `B-2` w głębi), `boom` (własna czerwona obudowa + biało-czerwone ramię + tabliczka opłaty, zastępujący `lift_gate` OSM), `chimneys`, `conifers` (przekazywane do `plantings.garden_trees` jako kolumnowe `PLT.thuja` bez `strict` limitu wzrostu granic grupy). Mur wycina ogrodzenie reguły (`fence_cut_m: 1.5`).
2. **Jeden prototyp, jeden materiał, jeden atlas 1024 px** na zestaw (`FACE_PX_M = 200.0`, cegła 128 px/m, beton, tablice i lica znaków). Atlas idzie przez rejestr `boards` z kluczem `MG*`; `export.py` nie zmniejsza go do 512 px i nie nakłada wspólnego „weather”, roughness 0,85.
3. Cegła, tablice i tablice informacyjne to własne rysunki (PIL/numpy). Teksty neutralne („SZPITAL / Oddział I”, „WJAZD NA PODSTAWIE…”, „IZBA PRZYJĘĆ”, „OPŁATA ZA WJAZD 3 zł”) — bez nazwy i godła prawdziwej instytucji (CLAUDE.md §8).
4. Dane Dojlid: wpis `zurawia-hospital-gate` + tło (`zurawia-hospital-ward-low`, `zurawia-hospital-bg-yellow`, `zurawia-hospital-bg-cream`) w `Data/Regions/bialystok-dojlidy/overrides.yaml`; kamera `photo_P11-129c`.
5. Region C nie ma takiego wpisu — wynik bez zmian (test na danych).

## Budżet A/B (`r4`, kamera `photo_P11-129c`)
- **Zestaw `masonry_gate` (`zurawia-hospital-gate`)**: `576` trójkątów, `1` materiał (`sign_MG4a8c94b1`), `1` draw call, atlas `1024×1024`, `on_carriageway: []`, `lift_gates_replaced: 1`.
- **Low (`overcast`, msaa=2, renderScale=0.75)**: `objects=58`, `drawsEst=329`, `shadowDrawsEst=38`, `trisExact=440709` (+ instanced: `draws=80`, `instances=64`, `trianglesExact=12158`).
- **High (`overcast`, msaa=2, renderScale=1.0)**: `objects=166`, `drawsEst=621`, `shadowDrawsEst=369`, `trisExact=915806` (+ instanced: `draws=171`, `instances=308`, `trianglesExact=36415`).
- Dowody wizualne (`r4`): `artifacts/hospgate-0189/sbs/sbs-P11-129-Low-overcast-r4.jpg` i `artifacts/hospgate-0189/sbs/sbs-P11-129-High-overcast-r4.jpg` (obejrzane; wszystkie elementy i tło zgodne z `P11-129` i `M62-FIX`, bez magenty).

## Walidacja (`r4`)
- `uv run --project tools/worldgen python -m pytest tests/gis/test_masonry_gate_0189.py -q`: **10/10 passed**.
- `pwsh scripts/test.ps1 -Platform EditMode`: **587 total, 586 passed, 0 failed, 1 skipped (Ignored)**.
- `uv run --project tools/worldgen python -m pytest tests/gis -q`: **1239 passed, 3 skipped, 3 xfailed, 2 failed** (oba niepowodzenia dotyczą wyłącznie przestarzałego `Data/raw/derived/bialystok-industrial-c/world` w tym worktree: `test_ring_mast_survives_the_carriageway_clearing`, `test_forest_trees_reference_their_cell`; wszystkie testy `bialystok-dojlidy` i `masonry_gate` przeszły).

## Otwarte (`WORKING_VALUE` / luki M62-FIX)
- Kryterium `M62` „≥ 12 kadrów bramy z ≥ 3 stron” oraz „≥ 2 niezależne odczyty wymiaru” pozostają niespełnione (w źródłach otwartych istnieje tylko 1 kadr `F01 = P11-129` od ulicy) — do uzupełnienia sesją zdjęciową właściciela (strona wewnętrzna muru/filarów, tył portierni, dalsze ogrodzenie).
- Odległość `B-2` w głębi (~24 m), rozmiary tarcz znaków (800 / 600 mm) i pozycja/wysokość kominów (~13,5 m) — `WORKING_VALUE`.
