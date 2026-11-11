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

## r7 — S10 E (2026-11-11, w toku — bramki końcowe PENDING)

- Zamrożona baza `901c427f2bc5cebf9571adc14df3253bbd3bd772`, świeży własny PBR/hero/świat i kanoniczny pojazd przed
  160 prawdziwymi PNG: 40 kamer × Low `WorldC` / High `WorldC_High` × clear / overcast. Baseline192rawSHA i pojazd
  zapisane w `artifacts/firestation-r10/`; bez porównywania starego cache z nową produkcją.
- Dwa świerki przed szczytem przesunięte +4m w osi u, trzeci przed skrzydłem zachowuje środek. Korony: połączony,
  nieregularny rdzeń .55R, niskie gałęzie i wycięte karty z dwoma sprayami ±26° o wspólnej nasadzie. Źródło:
  Poly Haven `fir_tree_01`, CC0, Rob Tuytel / Rico Cilliers, przypięte dwa SHA256 w `conifer_source.json`.
  To krótkoigłowy fir/conifer, **nie zweryfikowany skan Picea ani geometria rzeczywistego świerka JRG2**.
  Źródła repo-relative i pakiet odtworzenia `source-cache/` + `restore_cc0_inputs.py`, bez zależności od strumienia B.
- Trzy nieregularne pokroje tui i zasiane odchylenie odstępów maks.19.50% (limit±25%). Wspólna paleta własnego atlasu
  i lokalnego aliasu `fire_station_thuja_shell`; dotychczasowe globalne kolory/tekstury żywopłotów zachowane.
- LOD **9344 / 2828 / 164**, wcześniej9944 /2828 /164. High3materiały, Low2bez nowego batcha. Karty wykorzystują
  istniejący `fire_station_alpha`, ustawienia importu i zachowania pokrycia alfa bez zmian. Android-target Editor
  importuje rzeczywiste ASTC6×6,1024×512,11mipów: stare litery/płot/brama/998 mają alfa dokładnie zgodną do mip3,
  dalsze poziomy mają jawne różnice progu (letters1pixelmip4/8mip5,fence3/gate1mip5,9983mip6). Native i max1024
  to **ta sama importowana rozdzielczość**, nie niezależne testy. Oglądane kadry ref/route bez oczywistej regresji
  napisu/płotu/flagi/okrągłego obramienia; telefon i migotanie pozostają UNVERIFIED.
- Po dwóch odrzuconych próbach (rzadka korona, potem sam połączony rdzeń) ROOT przyjął bundle2 jako ograniczoną
  poprawę tej iteracji. Korony nadal węższe/kolumnowe względem7197; **nie deklarujemy mocnego dopasowania do zdjęcia**.
  Rzeczywisty kolorystyczny proxy odsłonięcia prawej głowy łuku rośnie Low62.87→99.11%,High54.25→97.81%; całego
  otworu51.45→88.70%,45.16→85.42%. Proxy klasyfikuje zieleń/ciemne piksele w ustalonej masce, ma fałszywe wskazania
  na obramieniu/AA i **nie jest pomiarem widoczności z bufora głębi ani100% szkła**. Dolne tuje nadal przesłaniają otwory.
- D48/A: zachowana baza tynku x1.15 `[.21275,.299,.41975]`. Semantyczny baseline czystego tynku szczytu Low105/123/141,
  High112/131/150; skrzydło/tower nie wymagają rozjaśnienia względem szczytu. To stan zastany zachowany, nie nowa poprawka.
- Oddzielny kandydat fasady: szkło hali/okrągłe `[.102,.108,.117]` z łagodnym gradientem nieba .90+.06, brązowy klinkier
  `[.27,.135,.06]`, miejscowe zacieki pod obróbką .35–1m, gęsty rdzeń7–16cm z miękkim ramieniem. Strefa rozbryzgu przy
  gruncie, kratki i flaga zachowane. Target szkła60–75 sRGB wymaga świeżego renderu — **PENDING**. Wszystkie9map
  Normal/Mask/Var i czyste piksele tynku/dachu/opasek/flagi/okien biura dokładnie zgodne z bazą; aktualizowany manifest
  średniej atlasu utrzymuje mnożnik blisko1 (istniejące zaokrąglenie3cyfry daje1.000743 liniowo).
- Lokalne2widoki: Lowdraws/tris bez zmian, High−1instancedcall/widok i−1ktri z trasy. Pełna końcowa macierz, globalny
  budżet, pełny GIS, EditMode, ocena końcowa i REPORT wciąż **PENDING**. Praca nie jest zakończona.
