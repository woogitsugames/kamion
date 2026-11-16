# ADR 0218 — rondo DK65×DW671 (Knyszyn): tor śladu zestawu 16,5 m i przejezdna opaska jako dane (`truck_apron`)
Status: Proposed (agent C2, chmura, s21, gałąź `roundabout-0218`), 2026-11-15. Do scalenia przez lidera.
Powiązane: D65 p.2 (rondo jak OSM), ADR 0123 (`apron: asphalt`), 0204 (region `knyszyn`), 0212, K1
(`research/dk65-knyszyn-refs/README.md` §b), `art-source/truck/dims.json`, `docs/VEHICLE_REFERENCE_DATA.md`.

## Kontekst
K1: rondo w Knyszynie (OSM way 1426801304) ma **średnicę osi ~17,6 m** (SOURCED, geometria OSM; r osi 8,61–8,98 m,
średnia 8,79 m — policzone ponownie z `Data/Regions/knyszyn/roads.graph.json`), 4 wloty jednopasowe. Średnica
zewnętrzna, szerokość jezdni, wyspa — **UNVERIFIED** (ortofoto 2025-05-27 jest sprzed budowy). Pytanie: czy ciągnik
siodłowy z naczepą 13,6 m przejedzie i czy generator umie zbudować przejezdny pierścień wewnętrzny (opaskę).

## 1. Stan generatora (przed zmianą, odwołania do `tools/worldgen/roads/`)
- **Opaska już istnieje, ale stała.** Każdy pierścień ronda (`junction=roundabout|circular`, `network.py:108`) ma po
  stronie wyspy rodzinę profilu `ISLAND` (`network.py:1053–1055`): opaska z kostki `apron_sett` o szerokości
  `S.ROUNDABOUT_APRON_W = 2,0 m` (`standards.py:131`, WORKING_VALUE) z krawężnikiem najazdowym
  `S.KERB_HEIGHT_APRON = 0,04 m` (`standards.py:86`), spadek 2 % ku jezdni, za nią krawężnik wyspy 0,13 m + 0,15 m
  (profil: `network.py` `side_profile`, gałąź `kind == ISLAND`, l. 1205 n.). Jedyny override: `apron: asphalt`
  (ADR 0123) — te same 2 m, ale asfalt bez progu. **Szerokości/wysokości nie dało się ustawić** per rondo.
- Wyspa = to, co wewnątrz krawężnika wyspy: brak wypełnienia, teren/trawa (`gores.py:8` — środek ronda jest wyspą
  z definicji). Opaska jest powierzchnią przejezdną dla QA (`consistency.py:39` `DRIVABLE` zawiera `apron`,
  `consistency.py:66`), kolizja jako `collision_paving` (`meshing.py:380`).
- Jezdnia pierścienia: 1 pas → `S.SINGLE_LANE_DEFAULT = 4,0 m` albo szerokość BDOT10k przycięta do 3,5–5,5 m
  (`network.py:116–121`); w Knyszynie dwie krawędzie mają BDOT10k 4,0 m — z 2008 r., sprzed ronda. Wygładzenie osi
  pierścienia σ = 1,5 m (`network.py:449`); po nim oś generatora ma r 8,44–8,91 m w 8 łańcuchach.
- Wloty: promienie łuków przy pierścieniu ≤ 12 m (`junctions.py:134–144`), węzeł oznaczony `j.roundabout`
  (`junctions.py:374`). `aprons.py` to inna rzecz: `paved_apron` = przemalowanie wielokąta jezdni na kostkę (ADR 0100),
  bez progu i bez związku z pierścieniem. `pipeline.py` nie ma osobnego kroku dla rond.
- **Knyszyn dziś (wynik generatora, sprawdzone w pamięci na grafie z gita):** jezdnia 4,0 m, krawędź zewnętrzna
  r 10,44–10,91 m (Ø ~21,6 m), opaska 2,0 m, lico krawężnika wyspy r 4,44–4,91 m.

## 2. Tor śladu — model i dane pojazdu
Model kinematyczny niskiej prędkości (bez poślizgu, < ~20 km/h), `tools/worldgen/roads/swept_path.py`:
środek osi przedniej ciągnika jedzie po zadanej ścieżce; oś tylna ciągnika = traktrysa o długości L1; sworzeń
`c` przed osią tylną; oś naczepy = traktrysa sworznia o długości L2. Śledzone krawędzie wszystkich opon i narożniki
nadwozia; wynik = obwiednia promieni wokół środka ronda. Stan ustalony (sprawdzenie w teście):

    R1 = promień osi tylnej ciągnika,  Rf = √(R1² + L1²)          (oś przednia)
    Rk = √(R1² + c²)                                               (sworzeń)
    R2 = √(Rk² − L2²)  (istnieje dla Rk > L2)                      (oś naczepy)
    opona wewn. naczepy = R2 − (rozstaw/2 + szer. opony/2);  kąt skrętu δ = atan(L1 / R1)

| parametr | wartość | źródło / status |
|---|---|---|
| L1 rozstaw osi ciągnika | 3,70 m | dims.json `wheelbase_m`, `tractor_4x2_generic.vehicle.json` — WORKING_VALUE |
| c sworzeń przed osią tylną | 0,68 m | dims.json `fifth_wheel_lead_m` — WORKING_VALUE |
| zwis przedni / tylny ciągnika | 1,45 / 0,80 m | dims.json — WORKING_VALUE |
| szerokość kabiny | 2,49 m | dims.json — WORKING_VALUE |
| rozstaw kół przód / opona | 2,04 m / 0,315 m | dims.json — WORKING_VALUE / DERIVED (315/80 R22.5) |
| bliźniaki napędu: krawędź zewn. | 2,48 m | dims.json `rear_track_m` — WORKING_VALUE |
| sworzeń → tył naczepy / przód | 12,00 / 1,60 m | 96/53/WE zał. I 1.6 — SOURCED / DERIVED |
| osie naczepy od sworznia | 6,39 · 7,70 · 9,01 m, nieskrętne | `curtainsider_tridem_13_6.trailer.json` — WORKING_VALUE |
| L2 efektywny (tridem) | 7,70 m (oś środkowa) | ESTIMATED; czułość L2 = 8,0 m poniżej |
| rozstaw kół naczepy / opona | 2,04 m / 0,385 m | trailer.json / DERIVED (385/65 R22.5) |
| szerokość naczepy | 2,55 m | 96/53/WE zał. I 1.2 — SOURCED (limit) |
| długość zestawu | 16,47 m | dims.json `artic_length_m` — DERIVED (≤ 16,50 SOURCED); test zgodności |
| maks. kąt skrętu kół | 40° | vehicle.json `maxRoadWheelAngleDeg` — WORKING_VALUE |

Założenia jazdy (WORKING_VALUE): zewnętrzna opona przednia 0,50 m od krawężnika zewnętrznego; pas wlotu/wylotu
1,75 m w prawo od osi ramienia; promienie ścieżki osi przedniej na wlocie / wylocie 12 / 14 m; prześwit opony do lica
krawężnika wyspy `ISLAND_CLEARANCE = 0,25 m`. Kąty manewrów z namiarów ramion z grafu (środek ronda,
E = 0°): Obozowa S −61°, Tykocka E 37°, Obozowa N 113°, Tykocka W −139°. Z Białegostoku (wlot Obozowa S):
**do Rynku = w prawo 98°** (Tykocka E), na wprost 174°, w lewo 282°; **powrót Rynek → Białystok = wlot Tykocka E,
wylot Obozowa S = 262°**; zawracanie 360°.

## 3. Wyniki (pełna tabela: `artifacts/roundabout-0218/swept_path_table.txt`, komenda w §7)
Min. promień opony (zawsze wewnętrzna opona naczepy, poza „w prawo”, gdzie decyduje tył ciągnika na łukach
wlotu/wylotu), r zewn. przedniej opony = R_zewn − 0,5 m, narożnik kabiny wychodzi max **0,08 m** poza krawężnik
zewnętrzny (nad krawężnikiem, wysokość zderzaka > 0,13 m — dopuszczalne; słupki/znaki na krawędzi trzeba trzymać ≥ 0,5 m).

| R zewn. (jezdnia) | manewr | łuk na pierścieniu | max δ | max przegub | min r opony | potrzebna opaska* |
|---|---|---|---|---|---|---|
| 10,80 (4,0 m) = **generator dziś** | w prawo 98° | 14° | 16,7° | 21,8° | 7,93 | 0 |
| | na wprost 174° | 90° | 22,9° | 27,0° | 5,41 | 1,64 m |
| | w lewo 262° | 178° | 23,9° | 47,7° | 3,63 | 3,42 m |
| | zawracanie | 276° | 23,9° | 56,1° | 2,78 | 4,27 m |
| 11,30 (5,0 m) = **propozycja** | w prawo 98° | 17° | 16,8° | 21,2° | 8,37 | 0 |
| | na wprost 174° | 93° | 21,9° | 27,5° | 5,89 | 0,66 m |
| | w lewo 262° | 181° | 22,6° | 45,7° | 4,31 | 2,24 m |
| | w lewo 282° | 201° | 22,6° | 47,6° | 4,12 | 2,43 m |
| | zawracanie | 279° | 22,6° | 52,1° | 3,65 | 2,90 m |
| 11,80 (6,0 m) | w lewo 262° / zawracanie | | | | 4,99 / 4,48 | 1,06 / 1,57 m |
| 13,00 (6,0 m), Ø 26 | w lewo 262° / zawracanie | | | | 6,58 / 6,31 | 0,67 / 0,94 m |

\* opaska = (R_zewn − jezdnia) − (min r opony − 0,25 m). Stan ustalony (koło bez końca) dla R_zewn 10,8:
R1 = 8,34 m, δ = 23,9°, R2 = 3,28 m, opona wewn. naczepy r 2,06 m (zgodne z symulacją, która przy 276° łuku
zbliża się do tej granicy: 2,78 m). Czułość (R_zewn 11,3, 262°, min r 4,31 m): L2 = 8,0 m → 4,08; margines 0,3 / 0,8 m
→ 4,59 / 3,91; promienie wlot/wylot 10/12 / 15/18 m → 4,29 / 4,36. Kąt skrętu < 40° we wszystkich przypadkach.

**Odpowiedź: TAK tylko z przejezdną opaską.** Bez opaski (jezdnia do lica wyspy) przy Ø osi 17,6 m zestaw **nie
przejedzie** na wprost (potrzeba jezdni ≥ 5,6 m od krawężnika zewn.: 10,8 − 5,41 + 0,25), a w lewo i przy zawracaniu
potrzebny pas 7–8 m, czyli prawie cała powierzchnia wewnątrz ronda. **Generator dziś** (opaska 2,0 m): w prawo
(trasa do Rynku) i na wprost — TAK (prześwit 0,61 m na wprost); **w lewo (powrót do Białegostoku) i zawracanie — NIE**,
opona naczepy wchodzi ~1,2 m (262°) / ~2 m (360°) za lico krawężnika wyspy.

## 4. Wytyczne (rondo małe / jednopasowe)
Obowiązują „Wzorce i standardy rekomendowane przez MI”: **WR-D-31-3 „Projektowanie skrzyżowań typu rondo”, wersja 01,
obowiązuje od 2022-11-30** (nazwa i data z wyników wyszukiwania; PDF niedostępny — 404, 2026-11-15). Liczby poniżej
**tylko z cytatu wtórnego** (inzynierbudownictwa.pl, „Ronda turbinowe jako alternatywa dla rond jedno- i dwupasowych”):
minirondo Ø zewn. 14–25 m; rondo jednopasowe Ø 22–65 m; „szerokość jezdni wraz z pierścieniem powinna mieścić się
w granicach od 6,0 do 8,5 m”; pierścień przejezdny = „dodatkowa powierzchnia do poruszania się po rondzie pojazdów
wielkogabarytowych”. Szerokość i wysokość samego pierścienia, pojazd miarodajny i wymagania dla obwiedni —
**UNVERIFIED** (do sprawdzenia w oryginale WR-D-31-3). Starsze „Wytyczne projektowania skrzyżowań drogowych cz. II —
Ronda” (GDDKiA 2001) — nie otwierano, UNVERIFIED.

Wniosek: Ø osi 17,6 m + jezdnia 5,0 m daje **Ø zewn. ≈ 22,6 m (ESTIMATED)** = dolna granica ronda jednopasowego wg cytatu;
jezdnia + opaska 5,0 + 3,2 = 8,2 m mieści się w 6,0–8,5 m.

## 5. Decyzja
1. **Nowy klucz danych `truck_apron`** w `set` override'u celującego w way pierścienia (`target: {osm_way: …}`), zgodnie
   z istniejącym mechanizmem `overrides.yaml` (stale/applied, przeżywa reimport) — nie osobna sekcja `roundabouts:`:
   ```yaml
   set: {truck_apron: {width_m: 3.2, height_m: 0.04, material: kostka_jasna}}   # kostka|kostka_jasna|beton|asfalt
   ```
   `network._truck_apron` waliduje: `width_m` 0,2–6,0 (FIX s22, było 0,5–6,0), `height_m` 0–0,08 (WORKING_VALUE; wyżej to nie krawężnik
   najazdowy), znany materiał; błąd albo way nie-rondowy → `overrides_stale`, nic się nie zmienia. W `assign_sides` stacje
   pierścienia z tym override dostają szerokość, wysokość progu i kod materiału (5 kostka `apron_sett`, 6 beton
   `road_concrete`, 7 asfalt `road_asphalt`, 8 kostka_jasna `sidewalk_paving` — FIX s22); `side_profile(ISLAND)` używa progu `h` zamiast stałej 0,04. Krawężnik
   wyspy przesuwa się do środka o szerokość opaski → **wyspa mniejsza** (topologia profilu bez zmian, ta sama siatka
   pasów, łączenie z wlotami bez zmian). Kolizja: kostka jak dotąd `collision_paving`, beton/asfalt `collision_asphalt`.
2. **Bez override = zero zmian**: test na syntetycznym rondzie (tablice profilu i wierzchołki identyczne) oraz porównanie
   tablic profilu wszystkich łańcuchów 9 regionów z gita (`bialystok-*`, `dk65-01`, `knyszyn`, `knyszyn-s`,
   `knyszyn-w`): sha256 stary `network.py` (origin/main) == nowy.
3. **Knyszyn — przygotowany, NIE nałożony** (`tools/worldgen/roads/examples/knyszyn-roundabout-apron.yaml`):
   `width: 5.0` (jezdnia pierścienia, ESTIMATED — BDOT 4,0 m jest sprzed ronda) + opaska z jasnej szarej kostki
   (`kostka_jasna`, patrz §5a) **3,2 m**, próg
   0,04 m (WORKING_VALUE). Na kole Ø 22,6 lico wyspy r 3,1 m (Ø ~6,2 m); na pierścieniu generatora r 2,74–3,21 m.
   Najciaśniejszy sektor (krawężnik zewn. r 10,94): zawracanie r 3,03 m = 0,29 m od lica wyspy; każdy z 8 łańcuchów
   sprawdzony w teście (`test_knyszyn_ring_sectors_clear_the_u_turn`). 3,0 m wystarczało na idealnym kole, ale nie
   w najciaśniejszym sektorze (0,09 m) — stąd 3,2 m.
4. Wysokość opaski względem jezdni (próg 4 cm + 2 % spadku → 0,04–0,10 m) i krawężnik wyspy 0,13 m to WORKING_VALUE;
   fizyka najazdu na próg — istniejące testy `KerbStrike*` (PlayMode, lider).

## 5a. FIX s22 (recenzja `docs/reports/REVIEW-2026-11-15-s21-code-97.md` FIX 1–2, `-93.md` FIX 2)
1. **Materiał opaski Knyszyna: jasna szara kostka, nie brązowa.** Właściciel (3 zdjęcia z drona, 9–11.webp, lokalnie
   w `Data/raw/refs/owner-knyszyn-2026-11-15/`; opis w `docs/owner/KNYSZYN-OWNER-FEEDBACK-S21.md`, „Rondo DK65 ×
   Tykocka”): „Wyspa środkowa okrągła, dwustrefowa: zewnętrzny pierścień przejezdny z jasnej kostki/betonu (opaska
   dla naczep, wyraźnie jaśniejsza od asfaltu), wewnątrz okrąg z piaskiem/żwirem i małymi nasadzeniami (krzewy,
   kamienie), bez drzew i bez rzeźby.” Dotychczasowe `material: kostka` = `apron_sett`, albedo [0,27, 0,24, 0,21]
   (ciepły brąz, bez zestawu tekstur). Nowy kod 8 `kostka_jasna` (`paving`) = **istniejący materiał biblioteki
   `sidewalk_paving`**: albedo [0,26, 0,255, 0,245] (neutralna szarość, 3,2× jaśniejsza od `road_asphalt` 0,08),
   zestaw tekstur `paving_20x10_grey` — bez nowego materiału i bez nowych tekstur. Świadomie nie `road_concrete` /
   `road_paving`: materiały klasy jezdni (`CULL_CARRIAGEWAY`, `consistency.CARRIAGEWAY`) — próg 4 cm opaski
   zostałby wycięty jako „krawężnik na jezdni” (`meshing.cull_sides_on_carriageway`), a `road_concrete` wymaga UV1
   wzdłuż osi. `sidewalk_paving` ma tę samą klasę kolizji co `apron_sett` (`collision_paving`). Skutek uboczny:
   `consistency.py` klasyfikuje tę opaskę jako `sidewalk` (nie `apron`) — pas ruchu pierścienia (5,0 m, 1 pas) na
   nią nie wchodzi; lider sprawdza `road_consistency_qa.json` po przebudowie (UNVERIFIED w chmurze). Wartości 5,0 /
   3,2 / 0,04 m bez zmian — nadal ESTIMATED / WORKING_VALUE do pomiaru na zdjęciach 9–11.
2. **Jeden mechanizm z ADR 0226 (#93, rondo Putry).** #93 miał osobne pole `apron_width` (`EdgeSection.apron_w`)
   zapisujące tę samą szerokość strony ISLAND. Zostaje **jeden klucz `truck_apron`, jedno pole
   `EdgeSection.truck_apron`, jedna funkcja `network._truck_apron`**; `apron_width` nie istnieje. Postać
   `{width_m}` (bez `material` i `height_m`) = tylko położenie krawężnika wyspy, nawierzchnia i próg z reguły albo z
   `apron: asphalt` (ADR 0123) — tak zapisane jest rondo Putry (`{apron: asphalt, truck_apron: {width_m: 0.4}}`).
   Z `material` / `height_m` = opaska z własną nawierzchnią i progiem (Knyszyn). Zakres szerokości wspólny 0,2–6,0 m
   (dół z ADR 0226: poniżej pas dałby zdegenerowane trójkąty; góra z tego ADR). Nieznane klucze w słowniku →
   `overrides_stale`. Bloki mechanizmu w `network.py` są na obu gałęziach bajt w bajt takie same, więc drugi scalany
   PR nie ma w nich konfliktu. Kolejność: **#93, potem #97** (jak w recenzji); przy odwrotnej nic do poprawiania.

## 5b. D75 (właściciel, 2026-11-15 s22) — nowy jasny materiał opaski, przejezdność przed wiernością
Zastępuje §5a pkt 1 w części „istniejący materiał `sidewalk_paving`”.
1. **Materiał.** Kod 8 `kostka_jasna` = **nowy materiał `apron_paving_light`** (`build_world.MATERIALS`): faktura
   kostki 20×10 z wygenerowanego zestawu `paving_20x10_grey` (ADR 0022; **bez nowej tekstury**, więc bez wpisu w
   `docs/LICENSES.md`), albedo **[0,42, 0,42, 0,415] WORKING_VALUE**, szorstkość 0,85, powierzchnia fizyczna
   `paving_stones` (jak chodnik). Silnik (`WorldPbrMaterials`, materiał per nazwa z manifestu) barwi zestaw mnożnikiem
   luminancja materiału / średnia zestawu = 0,42 / 0,26 ≈ 1,6 (zakres importera 0,4–2,5) — ten sam mechanizm, którym
   `bridge_kerb` przyciemnia `kerb_concrete_1m`. Chodnik (`sidewalk_paving` 0,26, odrzucony przez właściciela jako
   ≈ brąz) zostaje bez zmian. Kontrast w grze: opaska / asfalt = 0,42 / 0,081 ≈ 5,2; opaska / chodnik ≈ 1,6.
   Zdjęcie 9 (JPEG po tone-mappingu, więc tylko dolne ograniczenie): opaska / asfalt pierścienia 2,1–2,4 w luminancji
   liniowej (ESTIMATED). 0,42 nie jest pomiarem albedo — do korekty po ocenie renderu `rondo_dk65_top`.
2. **Klasa materiału.** `apron_paving_light` jest wszędzie tam, gdzie `apron_sett`: kolizja `collision_paving`,
   `consistency.py` → `apron` (nie `sidewalk`, jak było w §5a), `WELD`, `conform.WALL_SKIP_MATS`, pionowa ścianka
   progu → `curb_concrete`, `fidelity.CARRIAGEWAY_MATS`, bariery przy filarach (`furniture.pier_guardrails`),
   `tests/physics/swept_path_gate3.py` (kategoria `apron`). Nie jest materiałem jezdni (`road_*`) — próg 4 cm nie
   jest wycinany jako „krawężnik na jezdni”.
3. **Wymiary.** Właściciel: przejezdność przed wiernością zdjęciu — zostaje asfalt pierścienia **5,0 m** + opaska
   **3,2 m** (zawracanie zestawu 16,5 m, §3), choć na zdjęciu 9 jest ok. 3,1 + 2,4 m (ESTIMATED, skala z Ø zewn.
   22,6 m).
4. Testy: `tests/gis/test_truck_apron_0218.py` (23 passed) — m.in. opaska > 1,4× jaśniejsza od chodnika i > 4× od
   asfaltu, neutralna szarość, zestaw `paving_20x10_grey`.

## 5c. Rondo kompaktowe jako jedno skrzyżowanie (int-dk65-s22, 2026-11-16; D75)
**Problem (render knyszyn r1, pierwszy render PR #97).** Pierścień way 1426801304 ma 8 węzłów na obwodzie 54 m (oś
R 8,65 m; krawędzie 1,6–11,6 m), bo każde z 4 ramion rozdziela się na jednokierunkowy wlot i wylot. Generator
sklejał rondo w 4 klastry {węzeł wylotu, węzeł wlotu, węzeł rozdziału}; łańcuch pierścienia między wylotem a wlotem
jednego ramienia wchodził do klastra oboma końcami → 4 samoprzecinające się płyty, opaska w 8 klinach, wyspa =
czworokąt trawy (`artifacts/int-dk65-s22/rondo-proto/r1_junction_patches_selfintersecting.png`). To nie parametr.

**Decyzja.** Nowy tryb w osobnym module `tools/worldgen/roads/compact_roundabout.py`, włączany WYŁĄCZNIE jawnym
kluczem na way pierścienia: `set: {compact_roundabout: {closing_r_m, splitter_w_m, splitter_gap_m, lane_w_m,
lane_clear_m, island_fill}}` (pole `EdgeSection.compact`; zły słownik albo way niebędący pierścieniem →
`overrides_stale`). Bez klucza kod nie jest wykonywany — pozostałe regiony bez zmian.
1. **Jeden klaster** (`junctions.build_junctions`): węzły pierścienia + węzły rozdziału jezdni jednokierunkowych
   (łańcuch jednokierunkowy ≤ 60 m z jednym końcem na pierścieniu); pierścień i te jezdnie są wchłonięte (bez
   wstęg), ramiona skrzyżowania = drogi odchodzące z węzłów rozdziału.
2. **Obrys płyty** = koło R_zewn (oś dopasowana + szer. pierścienia / 2) ∪ jezdnie jednokierunkowe (oś ± hw) ∪
   końcówki ramion, domknięte morfologicznie promieniem `closing_r_m` (wyokrąglenia wylot → następny wlot). Odcinki
   obrysu między ramionami to narożniki skrzyżowania (`Corner.kind = "fillet"` z jawną łamaną i normalnymi
   `Corner.out`), więc krawężniki / chodniki / pobocza ramion biegną po nich zwykłymi `build_corner_strips`.
   Odrzucony wariant: 4 ramiona dwukierunkowe + wyokrąglenia R 12 — środek→krawężnik 9,56 m (< 11,3), krawędzie
   pasów do 3,18 m poza asfaltem.
3. **Wyspa środkowa**: opaska jako pełny pierścień (`meshing._emit_strip` z profilem ISLAND: próg, 2 % spadku,
   materiał z `truck_apron`), krawężnik wyspy, wnętrze = nowy materiał `island_sand` (piasek / drobny żwir, albedo
   [0,30 0,265 0,21] WORKING_VALUE, zestaw `gravel_compacted`; wyraźnie ciemniejszy od opaski — uwaga lidera do r2).
   Asfalt płyty pod wyspą jest przycięty na okręgu progu i obniżony o 0,25 m (ślad terenu i kolizja zostają, nic
   nie przebija przez opaskę na pochylonym terenie).
4. **Wysepki dzielące**: to, co zostaje między wlotem a wylotem jednego ramienia po zostawieniu pasa `lane_w_m`
   wzdłuż zewnętrznego krawężnika i `lane_clear_m` od osi jezdni, najwyżej `splitter_w_m` wokół linii środkowej,
   od `splitter_gap_m` za krawędzią pierścienia do zwężenia < 0,6 m; kerbowane wyspy `gores.Island`
   (`sidewalk_paving`), min. 3 m².
5. **Materiał opaski**: `apron_paving_light` dostał `ground_grime` (kałuże wilgoci prawie wyłączone) — domyślne
   ustawienie importera dla zestawów kostki dawało szare plamy na jasnej opasce (r2).

**Knyszyn (dane, `Data/Regions/knyszyn/overrides.yaml`).** `knyszyn-roundabout-compact`: closing_r_m 6,0,
splitter_w_m 3,6, lane_w_m 4,0 (WORKING_VALUE wg zdjęcia 9); `knyszyn-roundabout-dk65-feeders-width`: jezdnie
jednokierunkowe DK65 4,5 m zamiast 6,0 m z BDOT10k (zdjęcie 9: ~4,2 m, ESTIMATED). Wynik `pipeline.build`: środek
−987,29 / −610,73, asfalt pierścienia 5,00 m (r 6,15–11,15), opaska 3,2 m (próg 0,04), wyspa r 2,95, 4 wysepki
(33,7 / 20,5 / 8,6 / 13,0 m²), `overrides_stale` puste.

**Testy.** `tests/gis/test_compact_roundabout_0218.py` (9): bez klucza bez zmian; jeden klaster, obrys prosty
(bez samoprzecięć), asfalt pierścienia ≥ autorskiej szerokości, pasy jezdni w obrysie, normalne narożników; 4 wąskie
wysepki poza pasami; pełny pierścień opaski (promienie, próg, spadek), wyspa, asfalt nie przebija; klucz błędny /
nie na pierścieniu = stale; klucz tylko w kaflu knyszyn.

**Otwarte (lider zaakceptował geometrię r3 do scalenia, 2026-11-16; dopracowanie w osobnym zadaniu).**
Punkty (a)–(d) podjęte w **ADR 0274** (tryb krawężnikowy, rozdział DK65, siatka wyspy i nasadzenia, P-13 / P-10 przy
pierścieniu); wymiary nadal WORKING_VALUE — ortofoto GUGiK 2025-05-27 jest sprzed budowy ronda.
- (a) Szerokie płaty asfaltu między ramionami (wyokrąglenia wylot → wlot z domknięcia 6 m; na zdjęciu 9 ciaśniej).
- (b) Wysepka na wlocie S krótka (~8 m): OSM rozdziela jezdnie 17 m przed pierścieniem; długa wysepka z azylem ze
  zdjęcia 9 wymaga override poszerzenia jezdni DK65 przed rondem.
- (c) Brak nasadzeń i kamieni na wyspie (zdjęcie 9: niskie krzewy, kamienie); góra wyspy ma promieniste cieniowanie
  wachlarza trójkątów (render r3 z góry).
- (d) Linie P-13 / przejścia stoją na końcach ramion dwukierunkowych (przy węźle rozdziału), nie przy pierścieniu.
- (e) Tor śladu zestawu (§3) dla pierścienia 5,0 + 3,2 m obowiązuje, ale przejazd przez wloty z wysepkami 12 cm
  nie był jechany (PlayMode / właściciel); `tests/physics/swept_path_gate3.py` nie uruchamiany na nowej geometrii.
- (f) Trasa startowa knyszyn wyeksportowana ponownie po zmianie: przesunięcie ≤ 0,02 m (eksport idzie po osiach
  łańcuchów, nie po płycie); 1,9–2,0 m od wysepek E / S.

## 6. Otwarte
- Zdjęcia właściciela już są (15.11; §5a): potwierdzają 4 wloty jednopasowe, wyspę dwustrefową i jasną opaskę.
  Nadal niezmierzone: szerokość jezdni i opaski, Ø wyspy, wysokość progu — lider skaluje na zdjęciach 9–11
  (szerokość pasa wlotu albo długość samochodu jako skala), poprawia override i ponownie liczy `swept_path`.
- Wyspa wewnętrzna: wg właściciela piasek/żwir + niskie krzewy i kamienie, bez drzew — generator zostawia teren/trawę
  (następne zadanie; krzewy i kamienie ≥ 0,5 m od lica krawężnika wyspy, bo nadwozie naczepy wchodzi nad wyspę).
  Sprawdzić na kamerze z góry, że na wyspie nie ma drzew.
- Wlot południowy DK65: długa wysepka dzieląca z azylem (opis właściciela) nie jest modelowana — obowiązkowa kamera
  i przejazd A16 „w prawo” (Białystok → Rynek) przy tej wysepce.
- Wloty: łuki krawężników i wysepki rozdzielające (w prawo 98° decyduje tył ciągnika na łuku wlotu/wylotu,
  min r 7,93–8,37 m od środka) — tor śladu względem narożników wlotów nie liczony; sprawdzić na kamerach kontrolnych.
- WR-D-31-3 w oryginale (pierścień przejezdny: szerokość, wysokość, pojazd miarodajny).
- Ramiona jednokierunkowe 6,0 m (BDOT) przy wysepkach — poza zakresem.

## 7. Komendy (lider)
```powershell
# testy (czysty Python)
uv run --project tools/worldgen python -m pytest tests/gis -k "0218 or knyszyn" -q
uv run --project tools/worldgen python tools/worldgen/roads/swept_path.py          # tabela §3
# test_road_fidelity::test_report_not_stale: hash network.py w fidelity_qa.json (zachowanie bez zmian - regresja §5.2)
uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c
# nałożenie override na region knyszyn (dopisuje wpis do listy overrides:)
$s = Get-Content tools/worldgen/roads/examples/knyszyn-roundabout-apron.yaml -Raw -Encoding utf8
Add-Content Data/Regions/knyszyn/overrides.yaml -Value ("`n" + $s.Substring($s.IndexOf('  - id:')).TrimEnd()) -Encoding utf8
# przebudowa (wymaga Data/raw)
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region knyszyn
uv run --project tools/worldgen python scripts/export-route.py --region knyszyn
pwsh scripts/import-region.ps1 -Region knyszyn -Build
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Medium -Lighting clear -OutputDir artifacts/visual-qa/knyszyn-0218
```
Po przebudowie: `Data/Regions/knyszyn/generated/roads_qa.json` — `knyszyn-roundabout-truck-apron` w `applied`, nie w
`stale`; `road_consistency_qa.json` bez nowych błędów; kamera `roundabout_*_above` dla ronda — opaska z jasnej szarej kostki
(zestawienie ze zdjęciami właściciela 9–11), wyspa mniejsza, próg 4 cm obecny na całym obwodzie; jazda A16: zawracanie na rondzie bez wjazdu na wyspę.
