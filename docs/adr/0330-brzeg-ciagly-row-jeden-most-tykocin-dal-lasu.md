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

## Wyniki
(uzupełnione po rundach — patrz niżej / STATUS.md)

## Otwarte
- Pomiar wysokości pomostu nad wodą (`UNVERIFIED`; zdjęcia sugerują ~0,5 m niżej niż model).
- Perspektywa powietrzna wypiekana dla presetu clear; pochmurny / zmierzch dodają swoją mgłę sceny, ale kolor
  wypieczony się nie zmienia. Właściwe rozwiązanie: dodatkowa głębokość optyczna z wierzchołka w shaderze
  (`Kamion/Vegetation`, `Kamion/World Surface` — poza własnością world-buildera, rendering-perf).
- Skarpa tylna rowu nadal wraca do wysokości krawędzi jezdni (xsec), nawet gdy teren za nią niższy (nasyp) — lepiej
  kończyć ją na terenie (zmiana `roads/network.side_profile` + meshing, osobne zadanie).
