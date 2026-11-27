# ADR 0349 — Ulica wiejska na DW671: chodniki przy krawężniku czytane z ortofoto (village-street-s24)

Status: Proposed, 2026-11-25 (agent village-street-s24).
Powiązane: ADR 0237 D38 (chodniki domyślne w Knyszynie, opt-in), 0272 (pobocza jako dane), 0301 (pasy z ortofoto →
generowane nadpisania), 0305 r3 (zmierzona szerokość chodnika), 0306 / D94 (poszerzenie pasa dla rozgrywki), 0231 (pierścień
kafli DW671), krytyk build #8 (`artifacts/critic-s24-build8/CRITIC.md`, pkt 10 i ocena elewacji, klatka t2590).

## Kontekst
Krytyk build #8: „ulica 3-pasowa jak aleja przy domach jednorodzinnych (t2590) — za szeroka, bez chodnika po lewej”.

Miejsce klatki z `player.log` nagrania (`[NAV]`, t logu = t nagrania + ~10 s wg `sync.json`): kafel `dw671-tykocin-03`,
E 205 / N −600 (Krypno Wielkie), krawędź grafu `w1111506762:1873962490-2125744109`, 49 km/h, kurs ~202°.

Co generator zbudował w tym miejscu (odczyt z `roads.pipeline.build`):

| element | wartość | źródło |
|---|---|---|
| jezdnia | 7,5 m (2 × 3,5 m + 2 × 0,25 m opaski) | BDOT10k `SZEROKOSCNAWIERZCHNI` 7,0 m + D94 2 × 0,25 m |
| krawędzie | krawężnik 0,13 m po obu stronach | reguła: brak `maxspeed` w OSM → 50 km/h → ulica |
| za krawężnikiem | 1,0 m trawy po obu stronach, **brak chodnika** | OSM bez `sidewalk=*` i bez `footway` przy drodze |

Co pokazuje ortofoto GUGiK 0,25 m kafla (`ortho_0p25m.tif`, 163 ważne stacje co 10 m na 1,9 km ulicy):

| wielkość | mediana | q10–q90 |
|---|---|---|
| pas utwardzony razem | 12,12 m | 9,9–13,9 m |
| od linii środkowej w lewo | 6,38 m | 5,9–7,4 m |
| od linii środkowej w prawo | 5,75 m | 3,4–6,5 m (cienie drzew) |

Profil poprzeczny (mediana 62 stacji krawędzi z klatki, wyrównany do linii środkowej): ciemniejszy asfalt od −3,6 do
+3,6 m (7,2 m ± 0,3 m, czyli BDOT 7,0 m się zgadza), jasna linia krawężnika, po lewej jasna kostka do +6,6 m, po prawej
ciemniejszy chodnik do −5,6 m. Na kaflach bez wsi (01, 02, 05–09) pas utwardzony ma medianę 6,5–7,25 m przy BDOT
6,5–7,5 m — szerokości jezdni z BDOT10k są więc poprawne w granicach dokładności odczytu.

**Przyczyna** nie leży w szerokości jezdni ani w sklejaniu pasów skrętu, tylko w przekroju poza jezdnią:
1. OSM (pbf 2026-11-08) na DW671 przez Krypno ma tylko `highway`, `surface`, `lanes`, `ref`; chodników nie ma w danych,
   a reguła chodników domyślnych (ADR 0237 D38) jest włączona tylko w kaflach Knyszyna.
2. W Krypnie Kościelnym (way 145989268) nadpisanie `dw671-ground-shoulder` — wpisane dla ciągłości na szwie, z adnotacją
   „nie zmierzone na ortofoto tego kafla” — ciągnęło przez wieś pobocze gruntowe i linie krawędziowe.
3. Do tego jezdnia jest o 0,5 m szersza niż w terenie przez D94 (decyzja właściciela, zostaje).

Goła jezdnia 7,5 m między krawężnikami z trawą czyta się z kabiny jak aleja; w terenie te same 7 m obramowują chodniki
i ogrodzenia tuż za nimi.

## Decyzja
1. **Pomiar jako narzędzie** — `tools/worldgen/qa/ortho_sidewalks.py` (`measure` / `fit`): dla krawędzi dwukierunkowych
   wybranych klas (domyślnie primary/secondary/tertiary, `--ref 671`) profil poprzeczny z lokalnego ortofoto 0,25 m co
   10 m; pas utwardzony = ciągły przebieg komórek szarych (jasność ≥ rdzeń − 32, nasycenie ≤ rdzeń + 8, R−B ≤ rdzeń + 10,
   nie zieleń) przez oś; początek układu = linia środkowa, gdy widoczna. Nadmiar ponad połowę szerokości jezdni z BDOT10k
   ≥ 1,3 m na ≥ 60 % ważnych stacji (≥ 4) krawędzi leżącej w terenie zabudowy BDOT10k (`OT_PTZB_A` + 60 m, jak ADR 0237)
   = chodnik przy krawężniku; szerokość = mediana nadmiaru − 0,15 m (krawężnik), zaokrąglona do 0,25 m, w zakresie
   1,5–3,0 m. Stacje w cieniu (rdzeń pasa ciemniejszy o > 25 od p85 drogi) odpadają. Krótka krawędź dziedziczy wynik
   swojej drogi OSM albo zgodny wynik obu sąsiadów; spójny ciąg (także przez szew, gdy kafle podane razem) dostaje jedną
   szerokość na stronę (mediana ważona). Wszystkie progi: `WORKING_VALUE`.
2. **Wynik jako dane** — `Data/Regions/<kafel>/overrides.ortho_sidewalks.json`, nowy plik w
   `roads.pipeline.GENERATED_OVERRIDES` (ładowany przed `overrides.yaml`, wzorzec ADR 0301). Wpis na krawędź:
   `side_left|right: sidewalk`, `sidewalk_w_left|right` (ADR 0305 r3), `shoulder_left|right: kerb` (ADR 0272). Raport
   liczbowy (bez pikseli) w `docs/reports/village-street-0349/<kafel>.json`; test sprawdza, że raport odtwarza plik.
3. **Krypno (prototyp)**: `dw671-tykocin-03` — 15 krawędzi, chodnik lewy 2,75 m, prawy 2,0 m (strony w kierunku drogi OSM,
   tj. w stronę Tykocina); `dw671-tykocin-04` (kafel kontrolny) — 2 krawędzie, 142 m końca wsi, te same szerokości na
   szwie. Kafle 01, 02, 05–09: 0 wpisów (pliku nie ma).
4. **Nadpisanie ręczne** `dw671-village-kerb` w `overrides.yaml` kafla 03: sześć krawędzi way 145989268 od węzła
   2133817368 wraca do krawężnika i traci linie krawędziowe; 290 m od szwu z kaflem 02 zachowuje pobocze gruntowe
   (ścieżka odsunięta po lewej, szpaler po prawej, krawężnika nie widać). Cel `edge` nadpisania przyjmuje listę krawędzi
   (wszystkie muszą istnieć, inaczej wpis jest `stale`).
5. **Szerokość jezdni bez zmian**: BDOT10k 7,0 m potwierdzone pomiarem; +0,5 m to D94. Zmiana D94 dla ulic z krawężnikiem
   to decyzja właściciela (patrz „Otwarte”).

Przepisy (cytowane za `roads/standards.py`, tekst rozporządzenia nie był w tej sesji czytany ponownie): Dz.U. 2022
poz. 1518 § 17 ust. 1 — pas ruchu klasy G 3,50 m (3,00 m w trudnych warunkach), czyli jezdnia 2-pasowa 6,0–7,0 m;
§ 29 ust. 1 — chodnik nie węższy niż 1,80 m. Zmierzone 2,0 m i 2,75 m mieszczą się w tym.

## Czego nie zmieniono
- generatorów fasad, okien i płotów (zadanie neon-windows-s24); płoty same odsuwają się od obrysu drogi
  (`plots.ROAD_CLEAR_M` 1,5 m), więc szerszy obrys = działki cofnięte o szerokość chodnika;
- rond, skrzyżowań, mostu (`hero_bridge`), kafli miejskich: bez pliku `overrides.ortho_sidewalks.json` wynik jest
  bajt w bajt taki sam (klucz w `sources_sha256` manifestu pojawia się tylko tam, gdzie plik istnieje);
- reguły ADR 0237 (opt-in zostaje; w kaflach z plikiem z ortofoto reguła nie jest potrzebna).

## Dowody
- pomiar: `docs/reports/village-street-0349/*.json`, liczby zbiorcze `artifacts/village-street-s24/report_numbers.py`;
- testy: `tests/gis/test_village_street_0349.py`;
- rendery przed | po: `artifacts/village-street-s24/sbs/` (kamery `artifacts/village-street-s24/cams_<kafel>.json`).

## Ryzyka i ograniczenia
- Ortofoto 0,25 m: dokładność odczytu ok. ±0,4 m (`ESTIMATED`); asfalt i stara kostka mają tę samą jasność, więc
  podział „jezdnia | chodnik” opiera się na szerokości BDOT10k, a nie na widocznym krawężniku.
- Fałszywe trafienia: zatoka autobusowa, szeroki utwardzony pas albo plac przy drodze czytają się jak chodnik —
  przed commitem `fit` obejrzeć paski (`--strips`, poza gitem). Sprawdzone okiem: kafle 03 i 04.
- Jedna szerokość na ciąg: lokalne zwężenia / poszerzenia chodnika znikają.
- Wpis generowany `shoulder_<strona>: kerb` wygrywa z ręcznym `shoulder:` (obie strony) tej samej krawędzi, bo klucz
  strony ma pierwszeństwo w `xsec.resolve`; ręczne nadpisanie, które ma wygrać, musi nazwać stronę albo usunąć wpis.
- Krawężnik ↔ pobocze gruntowe zmienia się skokiem na węźle 2133817368 (brak klina przejściowego).

## Otwarte
- D94 na ulicach z krawężnikiem (7,0 → 7,5 m): do decyzji właściciela, czy poszerzenie obowiązuje także tam.
- `tykocin` (5 krawędzi-kandydatów, 489 m) i `knyszyn-w` (1 krawędź) — tylko raport, bez `fit`: kafle mają własne
  nadpisania / regułę D38 i wymagają obejrzenia pasków.
- Wsie bez wykrytych chodników (Zygmunty 06, Morusy 07, Tatary 09): wynik „brak” nie był sprawdzany okiem.
- Inne drogi przez wsie (DK65, drogi powiatowe `tertiary`): narzędzie działa bez `--ref`, nie uruchamiano.

## Dopisek neon-paving-s24 (2026-11-25): zmienność kostki, obniżenia i płytki przy przejściach, zjazdy

Odpowiedź na krytyka wave10-pre §3 (kostka sterylna, brak obniżonego krawężnika i płytek, brak wyróżnienia zjazdów). Wszystko opt-in przez `pavement_rules` (tylko `dw671-tykocin-03`); inne regiony bez zmian w geometrii.
- **Zmienność kostki** (`WorldPBR.shader`, 0 nowych draw calli i keywordów; deterministyczna z E/N w przestrzeni obiektu, zależna od `groundWear`): 3 tony partii co kurs 0,20 m, łaty po wykopach (~30 % komórek 8,5 m), plamy ciemne i jasne, ciemniejsze fugi, rzadkie chwasty przy krawężniku i tylnej krawędzi (UV1). Parametry domyślne dla `sidewalk_paving*`/`sidewalk_slabs` w `WorldPbrMaterials.cs`. Wszystkie wagi WORKING_VALUE (stain_strength obniżone do 0,18 po ocenie renderu).
- **Obniżenie krawężnika** do 2 cm na przejściach (Dz.U. 2016 poz. 124 § 127 ust. 10; Dz.U. 2022 poz. 1518 § 36 ust. 3) plus pas płytek z wypustkami 0,50 m (WORKING_VALUE), proceduralnie w shaderze (płyty 25 cm, kopułki co 5 cm).
- **Zjazdy**: kontrastowa kostka `driveway_paving_red` (stonowana, kolor 0,15/0,094/0,084), szerokość = brama 3-4,5 m (WORKING_VALUE), tylko na chodniku (kerb -> tył nawierzchni drogi), ~35 % bram (hash `drvcross`), reszta = ta sama szara kostka; pierwsza wersja kładła pas od bramy do jezdni (do 10 m) i była zbyt nasycona.
- Ryzyko: `test_world_roads::test_export_is_deterministic` (region C) czerwony także na kodzie main (manifest C nieodświeżony po fields3) — niezwiązany z dopiskiem.

## Dopisek axis-driveway-s24 (27.11): zjazd jako biała smuga i „patyki” w lusterku (krytyk build #10 pkt 7)

**Diagnoza** (`KAMION_QA_DIAG=colorby:material`, kamery w miejscu spawnu buildu #10 `artifacts/axis-driveway-s24/drv_cameras.json`;
`dbg_plan.py`, `glb_probe.py`): zjazd = `M_yard_paving` (apron `plots.paved_items` + nakładka `plots._verge_overlay`),
„patyki” = `M_verge_tufts` (karty `streetscape.verge_flora` w rowie) stojące NA zjeździe. Przyczyny w generatorze:
1. brama w płocie 12–14 m od DK65 (Obozowa), skośna do drogi o 41°: nakładka szła po normalnej bramy po skosie przez
   pobocze i rów, a zasyp rowu (przepust, `apply_drops`) obejmował tylko ±(w/2+0,4) m w miejscu, gdzie skos trafiał
   w asfalt — kostka zawinięta w niezasypanym rowie (pomiar GLB: ścieżka zjazdu 123,79 m przy jezdni 124,29 m);
2. nakładka w obrysie drogi z pass 1 (rów niezasypany, szerszy) trzymała wysokość jezdni — wisiała nad gruntem albo
   fałdowała się z apronem;
3. każdy podjazd był `yard_paving`, choć `region_plan` losuje `plot["surface"]` (żwir dla starych działek) — nieużywane;
4. verge_flora nie znała zjazdów.

**Decyzja** (`streetscape/plots.py`, `streetscape/verge_flora.py`, `roads/build_world.py`; WORKING_VALUE):
- `_perpendicular_crossing`: brama skośna > 12° do normalnej drogi na boku wiejskim → zjazd od wejścia promienia bramy
  w obrys drogi PROSTOPADLE do krawędzi jezdni, zasyp rowu w tym miejscu (knyszyn-w: 9 z 11 zjazdów wiejskich);
- nakładka tylko w obrysie drogi (apron działki przejmuje grunt za nim), narożnik między skośnym apronem a zjazdem
  wypełniony otoczką; poza powierzchnią drogi rampa od jezdni do gruntu na końcu apronu (nigdy pod gruntem);
- `drive_mat`: nawierzchnia podjazdu i zjazdu z ziarna działki (`yard_paving` / `yard_gravel`; knyszyn-w 37 z 86 żwir);
- `_crossing_edging`: boki zjazdu z kostki — obrzeże 8 cm (+3 cm nad kostką) z licem do gruntu (głowica przepustu
  zamiast krawędzi płyty w powietrzu); zjazd żwirowy — skarpa żwiru 1:1,5 do gruntu; bez obrzeża przy asfalcie
  (styk na równo) i na styku z apronem;
- `crossing_keepout` + `verge_flora.build(keepout=)`: brak kart trawy/ziół na zjazdach (knyszyn-w: 103 karty mniej).
- Koszt (VQA High, ta sama scena): drawsEst +1…+6 na kamerę (`yard_gravel` i `curb_concrete` w warstwie `plot_ground`
  kafla), trisK bez zmian (np. drv_cab_spawn 540→546 / 1643k→1643k, dk65-goniadzka 170→171). Build playera
  i pomiar `pc-metrics` NIE wykonane (prototyp w prywatnym derived).
- Testy: `tests/gis/test_driveway_crossing_s24.py` (6), `test_banks_verges_0324::test_verge_flora_keeps_off_driveway_crossings`,
  `test_buildings_r7` (dopuszcza `yard_gravel`); podzbiór tests/gis (plot/drive/verge/seal/patch/pavement/kerb/…) 229/230,
  jedyny czerwony (r7, materiał) poprawiony.
- Dowody: `artifacts/axis-driveway-s24/{before,after,after-overcast,diag-before-material,diag-after-material,sbs}`.
- Otwarte: ocena visual-critic (subagent nie może jej uruchomić — lider); apron skośnej bramy nadal skośny przez trawnik
  przed płotem (geometria działki z BDOT); obniżony krawężnik dotyczy tylko boków miejskich (wiejskie nie mają krawężnika).

## Dopisek codex-patches-edges-s24 — profil styku zjazdu z asfaltem

W przekroju wiejskim generator wydziela przy zjeździe krótki asfaltowy najazd z istniejącego pasa pobocza.
Przy wąskim asfaltowym obrzeżu granica asfalt–żwir przesuwa się do 30 cm od krawędzi pasa ruchu, zależnie od
dostępnej szerokości żwiru. Dodatkowy spadek na końcu asfaltu to 10% szerokości najazdu, ograniczony do 3,5 cm.
Początek asfaltu i zewnętrzna krawędź żwiru zachowują dotychczasową rzędną. W mieście krawężnik przy bramie
schodzi do 2 cm nad ściekiem. Progi i wymiary: WORKING_VALUE.

Siatki renderu i kolizji dostają te same stacje początku i końca najazdu oraz metrowego przejścia. Zjazd na
wiejskim poboczu jest docinany według obrysu asfaltu z finalnej siatki. Wzdłuż styku nakładka zachowuje kilka mm
prześwitu nad poboczem, przechodząc do 2 cm dalej od asfaltu. Generator używa dotychczasowych warstw i materiałów.
