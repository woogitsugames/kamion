# ADR 0070: Straż pożarna JRG nr 2 przy Andersa jako obiekt hero (override `hero_building`)

Status: przyjęty (world-builder / artysta obiektów świata), 2026-11-10. Wzorzec: ADR 0067 (hero wiadukt, override
`hero_bridge`). Powiązane: ADR 0011/0012 (import, instancje), ADR 0022 (zestawy PBR), ADR 0065/0066 (referencje otwarte).

## Kontekst
Trasa startowa (Kwadrat Park → Andersa → Rondo Putry → DK8/DK19) mija remizę Państwowej Straży Pożarnej. Generator
budynków rysował ją jak każdy inny obrys BDOT10k: bryła o wysokości LoD1 z regułową elewacją. To obiekt, który kierowca
rozpoznaje (łukowy szczyt z napisem, niebieskie dachy, bramy wozowni), więc zasługuje na model autorski.

## Który obiekt
`tools/worldgen/streetscape/find_fire_station.py` (OSM `amenity=fire_station` / `building=fire_station`, odległość od
polilinii trasy): w kaflu jest dokładnie jedna remiza, **JRG nr 2, ul. Gen. Andersa 46** — OSM way 211035271, BDOT
`bdot:2BE4B431-C784-1BF0-E053-CC2BA8C0D140` (funkcja „straż pożarna”, 1317,7 m²) i budynek gospodarczy na tej samej
posesji `bdot:2BE4B431-C7B4-1BF0-E053-CC2BA8C0D140` (245,2 m²). Elewacja frontowa stoi 52,2 m w prawo od osi trasy na
stacji ok. 1335 m (z 2401 m). Następna remiza (JRG 1, Warszawska 3) leży 1,76 km od trasy, poza kaflem.

## Źródła (tylko otwarte)
| Co | Źródło | Licencja | Użycie |
|---|---|---|---|
| rzut | BDOT10k (obrysy), ortofoto GUGiK 0,25 m (2024) | dane GUGiK | wymiary bloków, linia ogrodzenia |
| wysokości | GUGiK LoD2 2017, płaszczyzny dachów (`art-source/world/landmarks/fire_station_jrg2/lod2_roofs.json`, `tools/worldgen/streetscape/lod2_extract.py`) | CC BY 4.0 | okapy, kalenice, wieża, łuk hali |
| elewacje | Wikimedia Commons, kategoria „Fire station JRG 2 Białystok (Andersa Street)”: `7197 May 2021 in Białystok.jpg`, `20240626 103137 June 2024 in Białystok.jpg` (Rakoon) | CC0 | referencja główna (kadr, kolory, układ szczytu) |
| elewacje | Mapillary 767523907280643, 171742518208129 (richlv), 471355742447021 (strudel), 2934972690092373 (grobin); KartaView kv993066550 | CC BY-SA 4.0 | tylko wzór (bramy wozowni, wieża, dachy); żaden piksel nie trafia do tekstur |
| materiały | Poly Haven: Painted Plaster Wall (Amal Kumar), Brick Wall 006 (Jan Burghardt), Concrete Wall 008 (Charlotte Baglioni, Dario Barresi) | CC0 | detal albedo (górnoprzepust), relief, szorstkość atlasu |

Google Maps / Street View / Earth: nieużyte. Napis „PAŃSTWOWA STRAŻ POŻARNA” i „998” to nazwa służby i numer alarmowy
widoczne na elewacji (krój DejaVu Sans Bold); **bez logo PSP, herbu, znaku słuchawki**.

## Decyzja
1. **Override `kind: hero_building`** w `Data/Regions/<id>/overrides.yaml`: `osm_way`, `buildings: [id BDOT…]`, `asset`.
   Moduł `tools/worldgen/streetscape/hero_building.py`:
   - `plan()` (przed siatkami budynków) pisze **spec** `Data/Regions/<id>/generated/landmarks/<asset>.spec.json` =
     autorskie wymiary (`art-source/world/landmarks/<asset>/dims.json`, każda liczba ze źródłem albo `WORKING_VALUE`)
     + obrysy BDOT + poziom posadzki (mediana NMT pod obrysem + 0,12 m) + wysokości terenu pod każdym przęsłem
     ogrodzenia, bramą, tujami i masztami. Sprawdza sha256 specu w `<asset>_meta.json`; asset nieaktualny → Blender
     (`KAMION_BLENDER` / PATH) albo zostaje bryła generyczna i wpis `stale` w `streetscape_qa.json → hero_buildings`.
   - `buildings_mesh.build` dla budynków celu emituje wyłącznie pryzmę kolizji (budynek zostaje w masce: nawierzchnie,
     teren i drzewa dalej go omijają); `apply()` dodaje jedną instancję `landmark_<asset>` (LOD0/1/2), kolizję
     ogrodzenia i liczby trójkątów do budżetu kadru; `keepout()` blokuje sadzenie drzew na linii płotu i tuj.
2. **Generator Blender** `tools/blender/world/landmarks/make_fire_station.py` (headless, deterministyczny, tylko ze
   specu): wozownia (4 bramy segmentowe między filarami z klinkieru, blacharka nadproża i szczytu), skrzydło
   dwukondygnacyjne z dachami z blachy trapezowej wchodzącymi pod wieżę z dachem namiotowym, kominy, maszt, hala z dachem
   łukowym (szczyt: dwa okna łukowe, okno okrągłe, napis, wiatrownica łukowa), budynek gospodarczy z wieżyczką, cokół,
   rury spustowe, daszek od podwórza, ogrodzenie stalowe na podmurówce z odsuniętą bramą przesuwną, rząd tuj (rdzeń +
   powłoka alfa jak żywopłoty z ADR 0049), maszty z flagą. Rama glTF jak `street_props.glb`: (−dE, dU, dN) od kotwicy
   (narożnik W obrysu, poziom posadzki), instancja z `yaw = 0`.
3. **Materiały**: jeden atlas `fire_station` 14 × 14 m (UV0 w metrach; 2048² High = 6,8 mm/teksel, 1024² Medium, 512²
   Low) w `art-source/world/materials/_src/sets_fire_station.py`: pasy okresowe w u (tynk z strefą rozbryzgu u dołu i
   zaciekami pod górną krawędzią, blacha trapezowa okap→kalenica, obróbki, cokół) + elementy (brama, filar, okna,
   drzwi, flaga, stal, papa). Ściany i połacie są cięte na strefy (`bands()`): dół / powtarzalny środek lustrzany / góra,
   więc brud siedzi tam, gdzie siedzi w rzeczywistości, a środek nie kafelkuje widocznie. Drugi materiał
   `fire_station_alpha` (alpha test): przęsła płotu, brama, napisy. Tuje: istniejące `hedge_thuja` + `hedge_shell_thuja`.
4. **LOD i budżet**: `landmark_fire_station*` → końce LOD [150, 450, 20000] m × lodBias (InstanceImporter.Policy i
   `build_world.instance_ends`, trzymane w parze). LOD0 8 240 trójkątów (budżet zadania ≤ 15 000), LOD1 2 950
   (bez ościeży, rur, słupków, powłoki tuj), LOD2 164 (bryły + dachy + okna szczytu). Cztery materiały.
5. **Unity**: `InstanceImporter` czyta biblioteki `art-source/world/landmarks/*/*.glb` (ten sam mechanizm co ADR 0067;
   hunk identyczny, żeby scalenie z gałęzią wiaduktu było trywialne).
6. **Kamery QA** (`build_world.cameras`, gdy istnieje spec): `fire_station_route` (oko kierowcy 60 m przed), `fire_station_abeam`
   (na wysokości), `fire_station_ref7197` (kadr zdjęcia CC0 z drugiej strony Andersa), `fire_station_above`.

## Czego nie wiemy (WORKING_VALUE, do weryfikacji na miejscu)
Elewacje od podwórza (NE, NW), tylne bramy wozowni, ściana SE hali, elewacje budynku gospodarczego, dokładna linia
ogrodzenia (±3 m) i położenie bramy, liczba tuj; przesunięcie układu wysokości LoD2 (KRON86) względem EVRF2007 przyjęte
+0,17 m. Okna szczytu są płaskie (głębia tylko w normal mapie): z trasy (≥ 45 m) nieodróżnialne, z bliska widać.

## Konsekwencje
- Mechanizm jest ogólny: kolejny budynek hero = `dims.json` + generator + wpis w `BLENDER_SCRIPTS`.
- Spec zależy od NMT; zmiana terenu pod posesją unieważnia asset (sha) i wymusza przebudowę w Blenderze — celowo.
- Atlas jest generowany (poza gitem jak inne zestawy PBR); skany CC0 leżą w `Data/raw/cc0/polyhaven/` z kontrolą md5,
  bez sieci zestaw buduje się z szumu (komunikat w logu).
- Testy: `tests/gis/test_hero_building.py`.

## Dodatek: `_Tile` w Kamion/World PBR
`WorldPbrMaterials.Create` wyliczał `tile` z `tile_m` zestawu, ale nigdy nie zapisywał go do materiału: wszystkie zestawy
są próbkowane z domyślnym kaflem shadera 4 m (np. `plaster` 2 m, `brick` 1,04 m, beton 10 m). Dla atlasu to błąd
krytyczny (pierwszy render: atlas powielony co 4 m), więc zestaw z `"atlas": true` w `materials_spec.json` dostaje
`_Tile` = `tile_m`. Pozostałych zestawów ta zmiana nie dotyka: naprawa ogólna zmienia wygląd całego świata i wymaga
osobnej decyzji lidera (dotyczy też atlasu wiaduktu z ADR 0067, który trzeba oznaczyć `atlas`).

## Dowody
`artifacts/firestation-r9/`: `blender/it{1,2,3}/` (3 iteracje, `compare_it3.jpg` obok referencji),
`unity/r2/{High,Low}-{overcast,lowsun}/` (`compare_unity_r2.jpg`), `plan_overlay.jpg` (rzut na ortofoto), logi `logs/`.
pytest `tests/gis`: 173 passed; EditMode: 164 passed, 0 failed (5 inconclusive: brak prefabrykatu TRAKT w worktree).
Przegląd `visual-critic`: do zrobienia przez lidera (subagent nie tworzy subagentów).
