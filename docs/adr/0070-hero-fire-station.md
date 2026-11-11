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
   `build_world.instance_ends`, tabela `HERO_LOD_ENDS`, trzymane w parze). Stan r5: LOD0 **8 864** trójkątów (budżet
   zadania ≤ 15 000), LOD1 **2 720** (bez ościeży, rur, słupków, powłoki tuj; tuje z próbki atlasu `thuja_far`),
   LOD2 **164** (bryły + dachy + okna szczytu). Cztery materiały. Liczby z `logs/build_world_r5.log`.
5. **Unity**: `InstanceImporter` czyta biblioteki `art-source/world/landmarks/*/*.glb` (ten sam mechanizm co ADR 0067;
   hunk identyczny, żeby scalenie z gałęzią wiaduktu było trywialne).
6. **Kamery QA** (`build_world.cameras`, gdy istnieje spec): `fire_station_route` (oko kierowcy 60 m przed), `fire_station_abeam`
   (na wysokości), `fire_station_ref7197` (kadr zdjęcia CC0 z drugiej strony Andersa), `fire_station_above`.

## Czego nie wiemy (WORKING_VALUE, do weryfikacji na miejscu)
Elewacje od podwórza (NE, NW), tylne bramy wozowni, ściana SE hali, elewacje budynku gospodarczego, dokładna linia
ogrodzenia (±3 m) i położenie bramy, liczba tuj; przesunięcie układu wysokości LoD2 (KRON86) względem EVRF2007 przyjęte
+0,17 m. Albedo szkła hali i odcień napisu dobrane do jednego pochmurnego zdjęcia (7197).

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

## Wynik (rundy r3–r5, 2026-11-10)
- **r3**: dach nasycony (chalk 0,02), okna szczytu z prawdziwą głębią (ościeże 0,20 m, opaska, szprosy) przemierzone na
  zdjęciu 7197, rynny, lampy, ogrodzenie na linii OSM way 258562003 + `hero_building.fence_cut` (generyczny płot wycięty).
- **r4**: tynk równiejszy, okna łukowe 3 pola + szare szkło, biały ślemię w oknie okrągłym, „998” 0,6 m, 4 kratki pod
  okapem, tuje LOD1/2 z próbki atlasu (na Low były czarne).
- **r4b**: przęsła płotu jednościenne (zdublowana lustrzana ściana przy Cull Off dawała blade pręty 141,146,161);
  pomiar po poprawce na High overcast: pręty 69,79,94 (ciemnoniebieskie). Obróbka szczytu 0,22 m, napis karmazynowy.
- **r5** (po `git merge main`, obok hero depot ADR 0071): albedo szkła hali ×2. Pomiar szyby (surowy PNG, High overcast):
  104 → 115 sRGB przy ścianie ok. 180; na zdjęciu szkło jest bliżej ściany (0,45–1,0 × liniowo), u nas ok. 0,37 ×.
- **LOD**: 8 864 / 2 720 / 164 trójkątów, końce 150 / 450 / 20000 m × lodBias.
- **Koszt kadru** (`unity/r5/*/stats.txt`, szacunek edytora przed SRP batchingiem, NIE pomiar z telefonu):
  `fire-station-route` High 516 tys. trójkątów / 350 drawów, Low 209 tys. / 205; `fire-station-ref7197` High 424 tys. /
  138, Low 364 tys. / 132. Wpływ na FPS na telefonie: `UNVERIFIED` (brak przebiegu na urządzeniu w tej gałęzi).

- **r6** (po recenzji `docs/reports/visual/REVIEW-2026-11-10-0070-0083.md`, P0 nr 1 + P1 nr 2–7; łatka
  `artifacts/firestation-r9/scripts/r6_patch.py`): albedo tynku 0,47/0,545/0,65 → 0,185/0,26/0,365. Pomiar w kadrze
  `fire-station-ref7197` High overcast (JPG, prostokąt tynku szczytu): **103/119/135 i 105/121/137 sRGB** przy celu ze
  zdjęcia 7197 110/126/145 (±10: spełnione; r5: 170/178/188). Szum izotropowy tynku ÷3 (zostają zacieki i strefa
  rozbryzgu). Dach: B −35 % liniowo, szorstkość 0,48; pomiar 83/102/138 i 94/112/145 (cel 84/112/153). Okna skrzydła:
  rama PCV 10 cm, szprosy 6 cm, trzy stany szkła (roleta / firana / ciemne wnętrze) z gradientem nieba; szkło szczytu
  z wypalonym gradientem (ciemniejszy dół). Płot granatowy (albedo 0,022/0,032/0,075). Tuje: trzy pokroje, rozrzut
  odstępu ±25 %, wysokość 2,2–5,4 m; trzy świerki (dwa przed prawym oknem łukowym, jeden przed skrzydłem; r6b:
  gładki stożek 12-boczny po tym, jak pierwsza wersja wyszła kanciasta).
- **LOD po r6**: **9 944 / 2 828 / 164** trójkątów (`logs/build_world_r6b.log`). Koszt kadru bez zmian w granicach
  szacunku (`unity/r6/*/stats.txt`: route High 516 tys. / Low 209 tys.).
- **Otwarte po r6**: świerki to gładkie stożki (pokrój tui, nie świerka) i dwa stoją na kostce, nie na trawie
  (pozycje `WORKING_VALUE` z jednego zdjęcia — przesunąć); albedo koron (`hedge_thuja`, zestaw wspólny) nierozjaśnione;
  płot z góry nadal zlewa się w pas (teraz ciemny); brak drzew liściastych po lewej; P2 z recenzji (cegła, kratki,
  flaga, budynek gospodarczy, AO okapu w lowsun) nieruszone; światła nie strojono (czeka scalenie r11).

### Samokrytyka wg docs/06 (r5, bez visual-critic)
- Szkło hali nadal ciemniejsze względem ściany niż na zdjęciu; brak firan/odbić (jednolite szare pola).
- Tynk z bliska lekko „chmurkowy” (detal skanu ok. 1 m); na zdjęciu farba jest równa. Z trasy (≥ 45 m) niewidoczne.
- Tuje: jeden kształt w trzech wysokościach, rytm zbyt równy; na zdjęciu są też świerki przed szczytem (brak u nas).
- Płot z góry pod kątem (kamera `above`) zlewa się w pełny niebieski pas (alpha test + mipy); od podwórza nie oglądany z bliska.
- Elewacje podwórza i budynek gospodarczy pozostają `WORKING_VALUE`.

## Dowody
`artifacts/firestation-r9/`: `unity/r6/` (r6b; `r6a/` = pierwsza wersja świerków), `unity/r6/compare_unity_r6.jpg`, `unity/r4b/view/`, `unity/r5/{High,Low}-{overcast,lowsun}/`, `unity/r5/view/`,
`unity/r5/compare_unity_r5.jpg` (zdjęcie 7197 / High / Low), `atlas_base_r5.jpg`, logi `logs/*_r5.log`.
pytest `tests/gis` (r5): 229 passed, 3 failed, 2 xfailed — wszystkie 3 odziedziczone z main (`test_route_corridor` ×2:
P0 z HANDOVER, wiadukt s≈1432–1480; `test_report_not_stale`: `fidelity_qa.json` w wersji main). EditMode (r5): 188,
176 passed, 0 failed, 7 skipped, 5 inconclusive (brak prefabrykatu TRAKT w worktree).
Wcześniejsze: `blender/it{1..6}/`, `unity/r2..r4/`, `plan_overlay.jpg`.
Przegląd `visual-critic`: do zrobienia przez lidera (subagent nie tworzy subagentów).

## r7 — S10 E (2026-11-11; technical validation partly complete, appearance residuals open)

- Matched base `901c427f2bc5cebf9571adc14df3253bbd3bd772`: fresh PBR/hero/world and canonical vehicle before 160 baseline PNGs. Final `round2/` contains the same 40 cameras × Low `WorldC` / High `WorldC_High` × clear/overcast, 2340×1080. Both use the existing shared Medium512 material tier. All 20 final full-frame contact sheets were inspected; no exposure matching was applied.
- Two foreground conifers move +4m in authored u; wing tree stays in place. Connected asymmetric .55R core and rooted two-spray alpha cards replace opaque smooth cones. Poly Haven `fir_tree_01`, CC0, Rob Tuytel/Rico Cilliers; two pinned SHA256 values and repo-relative raw paths are in `conifer_source.json`. This is short-needle fir/conifer imagery, **not verified Picea or a scan of JRG2 trees**. Offline inputs and verified `restore_cc0_inputs.py` accompany artifacts; no dependency on B/cache paths.
- Three irregular thuja habits and seeded spacing maximum19.50% (limit±25%). Hero-local core/shell aliases preserve every existing global hedge palette. LOD triangles **9344/2828/164** versus9944/2828/164; High3/Low2 materials, Low plants remain888tri.
- High-only thin-leaf lighting uses a runtime copy of exactly `M_fire_station_thuja_shell` in `WorldInstances`: active quality profile High, existing simpleFoliage/template control, Transmission.25/CrownShade0. Source asset remains URP Lit; Low—including near LOD0—uses original source. Gamma color, texture/ST, Cull, cutoff.5 and A2C retained. Cache tracks the hero policy independently from simpleFoliage. The importer-hook attempt affected Low LOD0 and is explicitly superseded (`round1/`); accepted proof is `round1-runtime/` and `round2/`.
- Actual normal factory reimport is byte-idempotent; bindings prove Low direct Lit / High Vegetation copy and source JSON unchanged. ONE NUnit test passes1/1 and exercises two actual factory imports and Low→High→Low with unchanged simpleFoliage. No global shader, scene or quality settings change.
- Final15paired interior thuja ROIs: overcast Low medianY50=61.65, High66.94, median paired ratio1.0889; clear90.58/92.29, paired ratio.9945. These are selected foliage interiors, not whole-crown radiometric calibration. Source photo7197 has different exposure/weather. No exact every-pixel brightness claim.
- Arch upper-head and whole-opening masks are separate. Color proxy for right head Low62.87→99.11%, High54.25→97.81%; whole opening51.45→88.70% /45.16→85.42%. Dark frames/AA cause classification errors: this is not depth-buffer visibility or100% unobscured glass. Lower thujas remain.
- D48/A plaster-only x1.15 base `[.21275,.299,.41975]` preserved. Actual overcast clean gable Low105/123/141, High112/131/150 meets110/126/145±10. Wing/tower already at least as bright; preserved, not claimed newly fixed. Clean plaster, roof, trim, flag, office pixels and all9 Normal/Mask/Var maps remain exact baseline.
- Hall/round glass `[.0612,.0648,.0702]`, soft sky gradient .90+.06; brown clinker `[.27,.135,.06]`; sparse flashing runoff .35–1m long with7–16cm dense core. Existing splash, vents and flag retained. Updated atlas mean keeps original global linear tint near1 (**1.0003615**, existing3-digit rounding).
- Final clean primary-pane mean sRGB Y: LowOV63.42–66.81 / HighOV70.12–73.24: **60–75 overcast PASS**. Clear Low81.83–89.92 / High88.97–96.76 (round pane near97.87): **clear FAIL**. No further scalar: it would break overcast. Static atlas receives diffuse illumination; a glass-lighting model/common exposure integration needs separate causal evidence, not an unlit fake or extra Low material slot.
- Existing alpha importer/coverage unchanged. Actual Editor Android-target ASTC6×6 readback1024×512,11mips: protected old alpha exactmip0–3; coarse cutoff differences letters1pixelmip4/8mip5,fence3/gate1mip5,9983mip6. Native/max1024 are the SAME imported size. Actual native letters/fence/clock/flag frames show no obvious regression; device/temporal shimmer unverified.
- Full matrix80Low/80High matched: maximum per-view drawEst and ktri delta0 in both tiers; peaks Low968drawEst/487ktri, High1778/2476 unchanged. Some views decrease. These are editor estimates before batching; additional High depth pass GPU/timing cost **UNVERIFIED**, not free.
- Latest-product full GIS **375 passed,1xfail,517.58s**, after graph-only fidelity refresh. All784 pinned products including192raw and canonical vehicle unchanged after suite. Full EditMode **PENDING renewed explicit Unity release** (PHONE hold); targeted runtime NUnit1/1 passed. ROOT reviewed true runtime16-frame gate and approved full160; final review pending.
- Appearance remains bounded: conifers narrower/column-like than7197, repeated card structure, subtle runoff, clear glass outside target. No collective visual-quality PASS. Full evidence and rejected rounds retained in `artifacts/firestation-r10/`; final technical and appearance verdicts are separate.
