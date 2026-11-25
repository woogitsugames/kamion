# ADR 0330 — Brzeg na ciągłej odległości, jeden rów na stronę, most w Tykocinie z kabiny, dal lasu z perspektywą powietrzną

Status: Proposed (agent banks2-s24, gałąź `banks2-s24`), 2026-11-24. Do scalenia przez lidera.
Powiązane: ADR 0324 (otwarte: schodkowy brzeg, las w dali), 0210 / 0213 / 0318 (woda), 0321 (podłoga rowu), 0110
(pasy trawy w terenie), 0085 / 0141 / 0219 (tło dali), 0187 (HLOD lasu), 0320 (most kratownicowy), 0117 / 0159
(bariery na pomostach), 0323 (nawierzchnie), 0327 (budżet trójkątów C).

## Kontekst
Po ADR 0324 i buildzie #5 otwarte zostały: (1) z fotela kierowcy na moście w Tykocinie Narwi prawie nie widać,
(2) schodkowa krawędź skarpy przy brzegu Narwi (`bv_bank_n`) i garby / piła za rowem (`bv_side_ditch`), (3) las w dali
jako ciemne, płaskie bryły (`far_field`).

## Decyzja

### 1. Most w Tykocinie — co naprawdę widać z kabiny
Sprawdzenie z referencjami (Commons „Tykocin Most drogowy 01–09”, Zala, CC BY-SA 4.0, tylko referencja; GUGiK
ortofoto 2024 0,25 m):
- Ortofoto: Narew ~55 m szerokości pod przęsłem głównym (S), przęsła północne nad łąką zalewową z trzciną — z mostu
  wodę widać tylko nad przęsłem głównym i drugim, z przodu kabiny (na wprost) jej nie widać (droga wchodzi na brzeg).
- Zdjęcia 04 / 06 (skala: poręcz ~1,1 m): chodnik ~3,5–3,8 m nad wodą (model: jezdnia 4,1–4,5 m, ADR 0318) —
  różnica w granicach niepewności, wysokości pomostu nie zmieniono (`UNVERIFIED`, zmiana niwelety = fizyka / trasa).
- Geometria widoku (oko 2,5 m nad jezdnią, poręcz 1,15 m, ~4,8 m w bok): nad poręczą woda od ~22–25 m w bok, bliżej
  przez szczeble — z kabiny rzekę widać bokiem, nie na wprost. Model to odtwarza (kamery `bv2_cab_main_*`).
- **Różnice z rzeczywistością naprawione:**
  - **Nawierzchnia:** pomost był z kostki granitowej. Przyczyna: `meshing.build_ribbon` brał materiał jezdni z sekcji
    w połowie łańcucha; łańcuch 565 m (ul. Puchalskiego: kostka – most – kostka) miał środek na kostce. Teraz materiał
    per stacja (sekcja każdej stacji) — most asfaltowy jak w OSM (`surface=asphalt`) i na zdjęciu 08. Dotyczy wszystkich
    łańcuchów o mieszanej nawierzchni (więcej prymitywów, te same trójkąty).
  - **Bariera:** na pomoście stała bariera wiaduktów Andersa (W-beam + górna belka skrzynkowa 0,98 m, ADR 0117), na
    zdjęciach 08 / 09 jest pojedynczy W-beam na słupkach C. Nowy klucz `bridge_style: barrier: wbeam`
    (`streetscape/furniture.py`) i `authored_overrides` `tykocin-narew-deck-barrier-0330` w `Data/Regions/tykocin/overrides.yaml`.
  - Balustrada chodnika (szczeble 0,20 m, 1,10 m) i trzcina przy przyczółku N zgodne ze zdjęciami — bez zmian.

### 2. Brzeg wody na ciągłej odległości (`streetscape/water.py`)
Przyczyna schodków: profil brzegu liczony z odległości do **rastra** wody (EDT po węzłach 1 m, `all_touched`): każdy
węzeł był „dnem” (poziom − 0,30 m) albo „brzegiem” (≥ poziom + 0,04 m) — próg 0,3 m szedł po schodkach rastra wzdłuż
skośnego brzegu. Teraz `carve` liczy **odległość ze znakiem do prawdziwego zarysu** (wektor BDOT / OSM, segmenty w
`STRtree`, pas 6 m w wodzie / 12 m na lądzie; zarys z obszaru kafel + 14 m, bez sztucznych krawędzi cięcia) i profil
ciągły w zerze: dno `poziom + 0,04 → poziom − 0,12` na 0,6 m, dalej 1 : 2,9 do głębokości; brzeg `poziom + 0,04 →
+0,18` na 0,5 m, dalej 1 : 3; próg (lip) za 2,5 m opada 1 : 3 zamiast kończyć się uskokiem; zatoki i łachy ADR 0324
wygaszane z odległością (`BAY_REACH_M` 1,4 m, `BAR_REACH_M` 1,5 m). Węzeł tylko „dotknięty” przez zarys jest brzegiem.
Linia wody przecina siatkę 1 m na zarysie, interpolacja trójkątów daje prostą linię. Ta sama odległość zasila maskę
mułu i kolor COL tafli. `WORKING_VALUE`.

### 3. Jeden rów na stronę (`terrain_mesh/conform.py`)
Przekrój `xsec_glb` (knyszyn-w E 120 N 795, kamera `bv_side_ditch`): rów z generatora leży 1–3 m od pobocza, a NMT
(LIDAR) niesie **prawdziwy rów 1–3 m dalej** (0,5–0,9 m głęboki, 4–6 m od krawędzi). Na skośnej siatce 1 m ten drugi
rów rysował się jako rząd garbów / piła za skarpą tylną. Rów generatora reprezentuje ten prawdziwy, więc w pasie
5 m (wygaszanie do 9 m) za węzłami rowu (`soft`, podłoga ≥ 0,25 m pod jezdnią) NMT dostaje zamknięcie szarościowe
5 × 5 m (wypełnia tylko rynny węższe niż 5 m; skarpa nasypu i miedza zostają) + Gauss σ 1 m. Dodatkowo fartuch
(pionowy pas pod zewnętrzną krawędzią pasa, |n.z| < 0,35) nie jest już „podłogą” ADR 0321: ciągnął każdy węzeł przy
koronie rowu o 0,20 m w dół (koryto + odsłonięty fartuch). Test `test_ditch_floor_0321` bez zmian (poke ≤ 5 mm).

### 4. Dal lasu (`streetscape/far_field.py`, `streetscape/forest_hlod.py`)
- **Perspektywa powietrzna:** pierścień 1–4,2 km jest skracany do ≤ ~660 m za granicą kafla, więc mgła sceny
  (`KamionFogTau` po odległości renderu) widziała drzewostan z 3 km jak z ~1 km. Brakujące wygaszenie
  `k = 1 − exp(−β (d_true − d_eff))`, β = 3,912 / 20 km (widzialność presetu clear) jest wypiekane bez zmiany shadera:
  kolor wierzchołków submesh 0 (kopce pod okapem, budynki, kominy) per wierzchołek `lerp(albedo, HAZE_ALBEDO, k)`,
  `HAZE_ALBEDO` liniowe 0,36 / 0,42 / 0,50; kurtyny lasu w pasmach odległości: `forest_edge_<mix>` (< 900 m),
  `_haze1` (900–2000 m, k 0,16), `_haze2` (≥ 2000 m, k 0,37) — 6 tekstur generowanych z wypieczonych
  (`FH.haze_textures`, deterministycznie, `forest_edge_haze.json` trzyma sha źródeł). Mgła sceny działa dalej.
- **Rodzaj drzewostanu:** kurtyny tła brały zawsze `forest_edge_mixed`; teraz `forest_edge_<mix>` wg BDOT (iglasty /
  mieszany / liściasty) — ciemne bory i jaśniejsze liściaste się różnią. Kopce: kolor per mix (+ liściasty) × 0,88–1,14.
- **Sylweta:** wysokość drzewostanu × 0,86–1,12 na drzewostan; fale korony z fazą na drzewostan + wygładzony szum i
  pojedyncze wyższe korony (~7 % wierzchołków +12–26 %); przesunięcie i skala u tekstury na drzewostan (sąsiednie lasy
  nie powtarzają tych samych koron). **Ta sama liczba wierzchołków i trójkątów** (zmieniają się tylko wysokości / UV /
  kolory / materiały); + do 8 prymitywów na sektor (3 mixy × 3 pasma), budżet draw calls D74: 2000 / 4000.

### 5. Schodki przy trzcinie — prawdziwa przyczyna (`bv_bank_n`)
Teren po (2) jest gładki (LOD0 w `chunk_6_3.glb` sprawdzony węzeł po węźle: spadek ~0,35 m/m bez uskoków), a schodki
na kamerze zostały. Źródło: (a) maska mułu A liczona z rastra wody (`np.where(self.mask, ...)`) i z progiem
(`m2 > 0.3`) — interpolacja po trójkątach 1 m rysowała jasny pas mułu o schodkowych brzegach; teraz z ciągłej
odległości, przejście ≥ 1,5 m, bez progu, płynnie w wartość dna; (b) boki kart trzciny przy stopie prawie pionowe
(stopa 0,35–0,7 szerokości) — rząd kart czytał się jak schody; stopa 0,12–0,30 (kępa z wąskiej nasady), każda stopa
na własnym terenie.

## Wyniki
Rundy: r0 = stan przed (derived = kopia main, kod main `80126cf83`), r1 = 4 kafle (brzeg, rów, dal lasu,
nawierzchnia), r2 = tykocin (bariera, stopy trzciny), r3 = tykocin + dw671-tykocin-01 (maska mułu), r4 = tykocin
(wąska stopa trzciny). Visual-qa High 1920 × 1080 clear + overcast + Low clear, edytor (nie player). Arkusze
przed | po: `artifacts/banks2-s24/sbs/r{1,2,3,4}/`.
- Most: nawierzchnia asfaltowa (było: kostka na całym moście), pojedynczy W-beam (było: W-beam + belka 0,98 m);
  woda widoczna bokiem przez szczeble i nad poręczą (`bv2_cab_main_w`), na wprost — tylko brzeg S (zgodnie z ortofoto).
- Brzeg: hillshade terenu przed / po (`artifacts/banks2-s24/hillshade/`) — schodki rastra zniknęły; na kamerze
  `bv_bank_n` zamiast schodkowej ściany kart — kępy z wąskiej nasady, pas mułu bez schodków (resztkowe ząbki przy
  pojedynczych kępach — do oceny krytyka).
- Rów knyszyn-w: drugi (NMT) rów za rowem generatora wypełniony; garby / piła na `bv_side_ditch` zniknęły (clear i
  overcast).
- Dal lasu: kurtyny w kolorze rodzaju drzewostanu, sylweta nieregularna, pasma ≥ 900 m jaśniejsze i bardziej
  niebieskoszare; bloki lasu wewnątrz kafla (HLOD ADR 0187) bez zmian.
- Budżet kamer (stats.txt edytora, szacunek przed SRP batching): r0 → r1 High 44 kamery: draws 10 301 → 10 759 (+458,
  +3…+24 na kamerę: prymitywy kurtyn per mix × pasmo, podział jezdni wg nawierzchni), trójkąty 28,14 → 28,07 M
  (−0,2 %); Low draws 6 575 → 6 736 (+161), trójkąty −0,4 %. r4 tykocin High +154 draws / −0,1 % trójkątów, Low −1 /
  +0,3 %. Budżety D74 draw calls 4 000 / 2 000 (build #5 p95 1 462 / 775). Pamięć / czas klatki: nie mierzone (lider,
  `pc-metrics.ps1` w buildzie).
- pytest: woda / brzeg / rów 23/23 (`test_water_0210` — bank_colours: wartość dna wg ciągłej odległości), far field /
  las / v34 124/124 (`test_far_field` — materiał kurtyny wg mixu), nawierzchnie / ronda / mosty 177/177, most / bariery /
  szuwary / xsec 128/128, budżet trójkątów (0221, hero_bridge, typology_0238, world_v31) 62/62. Pełny `tests/gis`: STATUS.md.

## Otwarte
- Pomiar wysokości pomostu nad wodą (`UNVERIFIED`; zdjęcia sugerują ~0,5 m niżej niż model).
- Perspektywa powietrzna wypiekana dla presetu clear; pochmurny / zmierzch dodają swoją mgłę sceny, ale kolor
  wypieczony się nie zmienia. Właściwe rozwiązanie: dodatkowa głębokość optyczna z wierzchołka w shaderze
  (`Kamion/Vegetation`, `Kamion/World Surface` — poza własnością world-buildera, rendering-perf).
- Skarpa tylna rowu nadal wraca do wysokości krawędzi jezdni (xsec), nawet gdy teren za nią niższy (nasyp) — lepiej
  kończyć ją na terenie (zmiana `roads/network.side_profile` + meshing, osobne zadanie).

---

## Dopisek — pas lasu na horyzoncie (`far_field`): prawdziwa głębia optyczna (ADR 0332), atlas v2 i sylweta z CHM (gałąź `neon-farfield-s24`, 2026-11-25)

### Kontekst i przyczyna
Po ADR 0330 i 0339 (sekcja otwartych) z kabiny na horyzoncie nadal widoczna była ciemna, równa wstęga lasu (`far_field`, pierścień 1–4,2 km):
1. **Zbyt mała perspektywa powietrzna w shaderze:** `KamionFogTau` liczył ekstynkcję wyłącznie dla skróconej odległości renderu (`d_eff ≤ 660 m` za krawędzią), zamiast prawdziwej `d_true` (1–4,2 km). Wypieczone w ADR 0330 `HAZE_ALBEDO` w teksturze było mnożone przez oświetlenie — na ścianach odwróconych od słońca (`edge-west`, `edge-south`) dawało to zaledwie sRGB `45–75` (czarna wstęga), a w `Overcast` nie dawało właściwego szarego wygaszenia z warstwy przyziemnej (`hazeGroundFactor = 2,4`).
2. **Tłumienie nieba przez okluzję pni (`vis_B`):** pomiar `forest_edge_{conifer,mixed,broadleaf}_n.png` wykazał średnie `vis_B = 0,135 / 0,159 / 0,204`; przy `VegetationCanopyPolicy` (`_Impostor.y = 0,85`) kurtyny dalekie traciły ~71 % światła kopuły nieba (`SampleSH`), a przy płaskiej normalnej (`z = 0,48`) czytały się jak ciemna pionowa ściana.
3. **Równa wysokość w 2–4 km:** `far_field.py` przycinał bazową wysokość każdego drzewostanu przez `max(..., 8.5)`. Przy skali skrócenia `s_h ≈ 0,39` (2,5–4 km) wszystkie drzewostany (18–21,5 m × `s_h` = 7,0–8,4 m) wpadały w tę podłogę i dostawały jedną płaską wysokość `8,5 m`, bez użycia dostępnych modeli koron (`forest_chm.png`, ADR 0339).

### Decyzja
1. **Prawdziwa głębia optyczna w shaderze (spójna z ADR 0332, bez białego pasa):**
   - `KamionAtmosphere.hlsl`: nowa funkcja `KamionFogTauExtra(pw, viewDepth, extraDist)` — stosuje dokładnie ten sam współczynnik ekstynkcji Koschmiedera i warstwy przyziemnej (`_KamionHaze`) co niebo i teren dla drogi `viewDepth + max(extraDist, 0)`, zostawiając `FarFade` przy `viewDepth` (żeby Low far clip 900–1500 m nie wycinał środka pierścienia). Dla `extraDist == 0` wynik jest identyczny z `KamionFogTau`.
   - `Vegetation.shader` (`_HLOD_EDGE`): czyta `TEXCOORD1.x = d_extra` (`max(d_true - d_eff, 0)` zapisane w `far_field.py` na istniejącym kanale `UV1` z `WorldEdgeBuilder` — **0 B dodatkowej pamięci GPU**, **0 nowych wariantów**, **0 zmian na HLOD wewnątrz kafla**, który nie ma `UV1`).
   - `WorldSurface.shader` (`_FAR_FACADE`): `KamionFarExtraDist(posOS.xz, uv1.x)` wylicza `max(d_true - d_eff, 0)` z odwrotności skrócenia radialnego dla obiektów > 140 m za granicą kafla (i 0 dla obiektów w kaflu oraz `SKYLINE_FLAG_BEYOND`). Usunięto wypiekanie `HAZE_ALBEDO` w `COL` submesh 0 (budynki/kominy nie są podwójnie zamglane ani niebieskie w pochmurny dzień / w nocy).
2. **Chłodniejszy atlas daleki v2 i światło nieba (`forest_hlod.py`, `far_field.py`, `WORKING_VALUE`):**
   - `forest_edge_mixed_far_atlas` (schemat `truck-sim-pl/forest-edge-far-atlas/2`): chłodniejszy cel Rayleigha `HAZE_ALBEDO = (0,20; 0,30; 0,46)` dla pasm `""` / `_haze1` / `_haze2` (`k = 0,08 / 0,24 / 0,40`); w `_n.png` podniesienie `vis_B` ku `1,0` (`0,55 / 0,78 / 0,92`) i wygładzenie normalnych XY (`0,35 / 0,60 / 0,80`). W `Overcast` silna szara mgła z `KamionFogTauExtra` przykrywa chłodny tint naturalnie.
   - Normalne kurtyn `far_field`: gradient w pionie `CURTAIN_NORMAL_UP = (0,65; 1,65)` (jak w ADR 0339 r2 — korony biorą niebieskie światło nieba z góry).
3. **Nieregularna sylweta z `forest_chm.png` i szumu z ziarna (`far_field.py`):**
   - `RingChm`: ładuje `forest_chm.png` wszystkich sąsiednich kafli (spośród 24 kafli trasy z CHM), których bbox przecina pierścień ±4,2 km; w wierzchołkach kurtyn odwraca foreshortening (`unforeshorten_xy`) i pobiera zmierzoną wysokość koron (`max(top, 0,78 * dom) / CHM_WALL_TOP_FRAC[mix]`, ±7 % jittera). Kopiec pod okapem także dopasowuje wysokość do CHM.
   - Poza 24 kaflami CHM: deterministyczny wieloskalowy szum gładki (`_vnoise2`: wydzielenia/wiek ~260 m, kępy ~65 m, korony ~22 m) + ziarno drzewostanu (przestoje ~12 %, wcięcia ~10 %, zakres 0,42–1,48× baza klasy), bez sztucznej podłogi `8,5 m` (zastąpiona `3,5 * s_h`).
   - Topologia, `seg_step` i liczba podsiatek (`≤ 2` na sektor) bez zmian.

### Zmierzone wyniki (prototypy `knyszyn-w` i `dk65-05`, Win64 High PC `1600×900`)
- **Pokrycie CHM w pierścieniu:** `knyszyn-w` 1 536 / 13 294 wierzchołków kurtyn (11,6 %, 7 kafli CHM); `dk65-05` 6 565 / 18 242 wierzchołków kurtyn (36,0 %, 7 kafli CHM).
- **Budżet geometrii i draw calli:**
  - `knyszyn-w` `far_field`: High **93 052 → 93 052** (Δ 0), Low **12 359 → 12 359** (Δ 0), podsiatki **≤ 2 / sektor**.
  - `dk65-05` `far_field`: High **111 935 → 111 935** (Δ 0), Low **15 120 → 15 120** (Δ 0), podsiatki **≤ 2 / sektor**.
  - `stats.txt` (visual-qa High, wszystkie 21 kamer): `drawsEst` i `trisExact` **Δ 0** na każdej kamerze.
- **Pomiar najciemniejszego wiersza pasma horyzontu (sRGB, High Clear przed → po):**
  - `knyszyn-w edge-west`: `[45, 48, 39] → [69, 76, 65]` (Overcast `[70, 72, 70] → [86, 91, 87]`).
  - `knyszyn-w edge-north`: `[74, 77, 54] → [101, 112, 88]` (Overcast `[64, 66, 60] → [82, 87, 79]`).
  - `knyszyn-w edge-south`: `[75, 79, 71] → [91, 97, 94]`.
  - `knyszyn-w dk65-fields-nw`: `[90, 95, 78] → [101, 114, 82]`.
  - `dk65-05 edge-west`: `[58, 62, 55] → [72, 77, 68]`; `edge-east`: `[85, 87, 74] → [96, 100, 87]`.
- **Dowody wizualne (przed | po + crop 1:1):** `artifacts/neon-farfield-s24/sheets/` (`sbs-knyszyn-w-High-{clear,overcast}.jpg`, `sbs-dk65-05-High-{clear,overcast}.jpg`, `crop-1to1-clear.jpg`).
- **Testy:** `test_far_field*` (w tym 3 nowe testy regresyjne `*_0330`) + budżetowe (`test_budget_0221`, `test_typology_0238`, `test_world_v31`, `test_hero_bridge`) — wszystkie zielone.
- **Do zrobienia po scaleniu (lider):** przebudowa `far_field` dla pozostałych kafli (szczególnie 24 kafli z CHM) i reimport, by nowe `UV1` (`d_extra`), normalne i sylwety CHM trafiły do buildu (same shadery `WorldSurface` i `Vegetation` działają wstecznie kompatybilnie także na starych GLB).

### Dopisek (2026-11-25, `neon-farfield2-s24`): runda 2 — eliminacja stożków, nieregularna podstawa z podszytem, ostrość atlasu 1:1 i impostory skraju (300–1500 m)

Po rozjaśnieniu lasu w rundzie 1 recenzja `artifacts/critic-s24-wave10-pre/CRITIC.md` §2 wskazała cztery wady w `far_field`: (1) stożkowe pagórki (`dk65-05 edge-west` nad magazynem, `knyszyn-w edge-east` z lewej, `edge-west` i `edge-south`), (2) idealnie prostą podstawę ściany (`knyszyn-w edge-north`), (3) rozmazaną, malarską ścianę z diagonalnymi smugami przy 1:1 oraz (4) brak pojedynczych drzew przy skraju w pasie 300–1500 m.

- **Diagnoza stożkowych pagórków (teren vs las):** analiza `BorderElevation` i GLB `far_field` potwierdziła, że daleki teren (apron NMT) jest płaski i zgodny z rzeczywistym NMT Podlasia (`knyszyn-w` 115–139 m, `dk65-05` 122–169 m, brak interpolacji w stożki). Wszystkie stożki pochodziły w 100 % z geometrii lasu w `tools/worldgen/streetscape/far_field.py`:
  1. Funkcje `_corridor_treelines()` i `_corridor_taper()` zakodowane dla `bialystok-industrial-c` (ul. Maczka W + al. Tysiąclecia N) były wstrzykiwane do **każdego** regionu, tworząc identyczne sztuczne pagórki i dolinę „V” przed `edge-west` w `knyszyn-w` i `dk65-05` oraz sztuczną bliską ścianę w `knyszyn-w edge-north`.
  2. Nieograniczone wartości z `RingChm` były dodatkowo mnożone przez `stand_scale × 1,06` (`h` do `38,9 m` w `knyszyn-w` i `43,0 m` w `dk65-05`, np. płat GIS #501 w `knyszyn-w edge-east` z `chm = 39 m`).
  3. Liniowe zwężanie końców kurtyny (`end_taper` do `0,30` na 32 m) + jednowierzchołkowy szum `u_ev` ±28 % dawały stromości `|dz/ds|` do `1,615` (~58°, również źródło diagonalnego ścinania UV) oraz spiczaste podkoronowe kopce (`h_cap` do `10,3 m`, widoczne w `knyszyn-w edge-south`).
- **Zmiany w generatorze (`tools/worldgen/streetscape/far_field.py`):**
  - `_corridor_treelines()` i `_corridor_taper()` ograniczone wyłącznie do `region_id == "bialystok-industrial-c"`.
  - Limity wysokości drzewostanów `FAR_CROWN_CAP_M` (`conifer 25,5 m`, `mixed 24,0 m`, `broadleaf 22,5 m`), niższe bazy `FAR_BASE_H_M` (`20,5 / 19,5 / 18,5 m`), brak ponownego mnożenia zmierzonego CHM przez `stand_scale × 1,06`, bogatsze zróżnicowanie CHM (`max(top, 0.62 * dom)`), usunięcie szpilek `u_ev`.
  - Ograniczenie stromości grzbietu koron `_limit_top_slope` (`|dz_top/ds| ≤ 0,26`, ~14,5°), łagodne wygaszanie końców smoothstep (`0,52` na `≤ 16 m`), spłaszczenie podkoronowego kopca do `h_cap ≤ 2,2 m`, filtr `facing_tile ≥ 0,48`.
  - Proporcjonalne `u_scale` względem lokalnej wysokości kurtyny (`ht_med / 21,0` dla ściany, `ht_med / 8,0` dla podszytu) — brak poziomego rozciągania pni i smug w przestrzeni skróconej.
  - Nieregularny skraj i podstawa na tierze High (0 dodatkowych draw calli): falowanie obrysu `FAR_EDGE_WOBBLE_M = 5,0 m`, łaciata falująca kurtyna podszytu (`v_bot = 1,0 → v_main`, `d_true ≤ 2200 m`) oraz indywidualne dwupłaszczyznowe (`+`, 4 tr/szt.) impostory drzew i krzewów w pasie `d_true ≤ 1500 m` (`add_tree_impostor1`) pakowane do tej samej podsiatki `forest_edge_mixed_far_atlas`. Tier Low pomija podszyt i impostory.
- **Atlas i ostrość 1:1 (`forest_hlod.py`, `InstanceImporter.cs`, `Vegetation.shader`):**
  - `art-source/world/vegetation/forest_edge_mixed_far_atlas.png` (+ `_n.png`, `.json`): powiększony z `1024×2048` do `1024×4096`, `FAR_ATLAS_PAD = 8` px (brak przesiąkania między pasmami do mip 3), 9 pasm kurtyn + 2 wiersze 8 pojedynczych drzew z `impostor_tree_*.png` (`pine_0/1`, `spruce_0/1`, `birch_0`, `alder_0`, `linden_0`, `shrub_0`) z chłodnym zamgleniem Rayleigha (`k = 0,16`, `vis_lift = 0,68`, `nrm_flat = 0,45`).
  - `InstanceImporter.cs`: `anisoLevel = 8`, `TextureImporterMipFilter.KaiserFilter` dla `forest_edge*`, `maxTextureSize = 4096` na PC dla `forest_edge_mixed_far_atlas` (Android zachowuje dotychczasowy limit).
  - `Vegetation.shader` (`_HLOD_EDGE`): niezależna normalizacja `T` i `B` (`invT`, `invB`) zamiast wspólnego `max(|T|, |B|)`, co przywraca pełny pionowy relief normalnych w 11-slotowym atlasie.
- **Zmierzone liczby (przed → po):**
  - Wysokość koron i stromość (`|dz/ds|`): `knyszyn-w` max `h` `38,9 → 24,5 m`, `|dz/ds|` max `1,615 → 0,359` (p95 `0,982 → 0,260`); `dk65-05` max `h` `43,0 → 28,7 m`, `|dz/ds|` max `1,509 → 0,327` (p95 `0,901 → 0,260`).
  - Trójkąty `far_field` (`submeshes = [2, 2, 2, 2]` na obu tierach):
    - `knyszyn-w`: High `93 052 → 104 569` (las `24 364 → 35 932`), Low `12 359 → 11 830` (**−529 tr**).
    - `dk65-05`: High `111 935 → 130 148` (las `33 562 → 51 826`), Low `15 120 → 14 585` (**−535 tr**).
    - `bialystok-industrial-c`: High `169 318 → 188 322`, Low `29 161 → 29 139` (**−22 tr**, budżet `≤ 30 000`).
  - Draw calle (`stats.txt`, PC High `1600×900`): **Δ `drawsEst` = 0** na każdej kamerze `knyszyn-w` (`cab-driver 349`, `dk65-fields-nw 33`, `route-s0994 126`, `edge-west 6`, `edge-north 7`, `edge-south 9`, `edge-east 7`) i `dk65-05` (`cab-driver 396`, `drive-debowa 336`, `drive-north 32`, `edge-east 30`, `edge-south 43`, `edge-west 58`).
- **Dowody wizualne (przed | po + crop 1:1, PC High, clear i overcast):** `artifacts/neon-farfield2-s24/sheets/` (`sbs-knyszyn-w-High-{clear,overcast}.jpg`, `sbs-dk65-05-High-{clear,overcast}.jpg`, `crop-1to1-{clear,overcast}.jpg`).
- **Testy regresyjne i budżetowe:** 4 nowe testy `*_0330_r2` w `tests/gis/test_far_field.py` + pełny zestaw `test_far_field*`, `test_budget_0221`, `test_typology_0238`, `test_world_v31`, `test_hero_bridge` — wszystkie zielone.
- **Do zrobienia po scaleniu (lider):** przebudowa `far_field` dla pozostałych kafli (poza prototypami `knyszyn-w`, `dk65-05` i `bialystok-industrial-c`, które można też skopiować z `Data/raw/derived/` tego worktree) i reimport, by nowy układ 11-slotowy atlasu `1024×4096` oraz geometria bez stożków trafiły na wszystkie kafle (uwaga: zmiana liczby slotów w `forest_edge_mixed_far_atlas.png` z 9 na 11 wymaga przebudowy `far_field.py` na pozostałych kaflach, aby UV starych GLB nie sięgały poza pasmo 0..9).
