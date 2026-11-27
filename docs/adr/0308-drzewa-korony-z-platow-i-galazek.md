# ADR 0308 — Drzewa bez „brokułów”: korony z płatów na konarach, atlasy gałązek, topola, drzewa ogrodowe z biblioteki (trees-s24)

Status: Proposed, 2026-11-19 (agent trees-s24; numer zarezerwowany przez lidera).
Powiązane: ADR 0012 (instancing drzew), 0015 / 0023 (HLOD lasu, impostory z normalną), 0088 (igły sosny, okna koron),
0132 / 0163 (drzewa ogrodowe z ortofoto: instancje → karty zestawu działek), 0170 / 0187 (ściana lasu, świerk, młodnik),
0222 (szpalery DK65), 0227 (studium lipy i wierzby w Knyszynie), D73 / ADR 0260 (Windows platformą główną).
Referencje (tylko oglądanie, poza gitem i buildem): Mapillary `Data/raw/mapillary/{knyszyn,knyszyn-dk65-b19,dw671-tykocin-01}`
(CC BY-SA 4.0), Wikimedia Commons `Data/raw/refs/commons-trees/` (CC0 / CC BY-SA, `manifest.jsonl`; Puszcza Knyszyńska —
rez. Wielki Las, pokrój klonu). Żadnych źródeł Google.

## Kontekst

Właściciel (s24): drzewa przydrożne i lasy wyglądają jak „brokuły”. Render „przed” (`artifacts/trees-s24/vqa-before-*`,
High, pogodnie) pokazał trzy niezależne przyczyny:

1. **Drzewa biblioteki** (`make_trees.py`: lipa, klon, brzoza, olsza — szpalery DK65, kępy przydrożne, las liściasty).
   Generator wieszał ~15 kart 1 × 1 m w promieniu 0,3 m od każdej z ~50 krótkich gałązek: korona była garścią gęstych kul
   na gołych konarach z niebem pomiędzy. Tekstury kart (`leaf_textures.foliage`) to okrągłe pompony płaskich krążków.
2. **Drzewa ogrodowe Knyszyna** (3243 szt., ADR 0163): na każdym poziomie treści skrzyżowane karty całej korony
   z gradientem okluzji — z ulicy kula z ciemnym krzyżem w środku.
3. **Świerk** (ADR 0187): konary jednego okółka wychodziły na tej samej wysokości, poziomo, z poziomą kartą —
   widziany z jezdni od dołu był stosem ząbkowanych talerzy.

## Decyzja

### 1. Atlasy gałązek (`tools/worldgen/streetscape/leaf_sprays.py`)
`leaves_{linden,maple,birch,alder,poplar}.png` to atlas 2 × 2 (1024 px) czterech różnych gałązek: oś z odgałęzieniami,
liście naprzemianlegle z blaszką gatunku (sercowata lipa, pięcioklapowy klon, rombowa brzoza, wcięta olsza, deltoidalna
topola), blaszka w dwóch tonach wzdłuż nerwu, ciemniejsze liście pod spodem. Podstawa gałązki leży na środku dolnej
krawędzi komórki, żaden liść nie jest przycięty brzegiem komórki, kolor pod przezroczystością = średni kolor liści (bez
czarnej obwódki w mipach). Brzoza: komórki 0–1 wzniesione gałązki, 2–3 zwisające witki. Rysunek proceduralny (numpy + PIL),
bez zdjęć i skanów. Kolory bazowe bez zmian (przygaszone zielenie, `docs/06`). Długości blaszek i wymiar karty
(`CARD_M`) to `WORKING_VALUE`.

### 2. Korona z płatów (`make_trees.grow_crown`, tabela `CROWN`)
Obwiednia korony na gatunek (promień po wysokości + nieregularność po azymucie, inna na wariant), konary szkieletowe
kończące się na obwiedni, rozgałęzienia; każdy koniec gałęzi to **płat** — karty-gałązki po jego zewnętrznej stronie,
podstawą do gałęzi, 14 % kart między płatem a pniem (brak prześwitu na wylot). Miejsca obwiedni bez płata dostają płat na
cienkiej gałązce od najbliższego konaru. Normalne cieniowania = mieszanka kierunku od środka korony i od środka płata
(bryłowatość bez ciemnego rdzenia). Okna `crown_opening` (ADR 0088) nie są wycinane — przerwy między płatami są
naturalnymi prześwitami. LOD1 jak dotąd: podzbiór kart LOD0 × 1,4 (`reuse_leaf_lod`), impostor 6 widoków.
Nowy gatunek **topola** (`tree_poplar_{0,1}`, 24 m; tylko szpalery / nadpisania — nie wchodzi do mieszanek BDOT).
Sosna: pełniejsze kępy igieł (karty 0,95 → 1,2 m, +1 karta na kępę). Świerk: każdy konar ma własny opad, wysokość
i obrót wokół osi. Stary generator liściastych zostaje pod `--legacy-crowns` (rendery porównawcze).
Wszystkie proporcje (`CROWN`) to `WORKING_VALUE` odczytane z referencji, nie dane dendrometryczne.

### 3. Drzewa ogrodowe = instancje biblioteki na High (`plantings.library_instance`)
Na poziomie High (PC) drzewo ogrodowe liściaste o promieniu korony ≥ 1,6 m jest instancją biblioteki (`tier: high`,
LOD0 / LOD1 / impostor): wysokość taka, żeby korona modelu miała promień z ortofoto, w granicach 0,8–1,3 wysokości
z G7 i pułapu gatunku. Jesion → model lipy, kasztanowiec → model klonu (`WORKING_VALUE`: brak własnych modeli).
Poziom Low zachowuje lekkie drzewo z kart (budżety A16, ADR 0163 bez zmian). Drzewa owocowe i iglaki ogrodowe bez zmian.

### 4. Skrajnia jezdni (`vegetation.road_clearance`) — zastąpione przez ADR 0347 (zasięg z siatki, margines 0,5 m, przesunięcie)
Po złożeniu wszystkich drzew kafla (reguły, szpalery, ogrody, brzegi wód): drzewo, którego korona ma podstawę poniżej
4,7 m (`CLEAR_H_M`, `WORKING_VALUE`: skrajnia 4,5 m + 0,2 m) i sięgałaby nad jezdnię dalej niż 0,3 m, jest obniżane
tak, żeby promień korony = odległość pnia od krawędzi jezdni + 0,3 m; gdyby musiało zmaleć poniżej 65 % wysokości —
jest usuwane. Promień korony / H i wysokość pnia / H na gatunek w `vegetation.CROWN_FORM` (te same liczby co
`make_trees.CROWN`). Sosna i świerk drzewostanowy mają koronę powyżej skrajni i zostają.

### 5. „Zielona ściana” na DK65 = tło dali w złym sektorze (`far_field.split_by_sector`) — zgłoszenie właściciela, przegląd przejazdu s24 #1, 2, 4, 5, 6
Przyczyna (potwierdzona danymi, `artifacts/trees-s24/audit_far_sectors.py`, `far_sectors_dk65-07_before_after.png`):
`far_field.py` wstawiał cały drzewostan tła do sektora jego **centroidu**. Las owijający narożnik kafla trafiał np.
do `far_east`, choć jego połowa leżała na północ od kafla — w sąsiednim kaflu, którego otwarty szew chowa tylko
`far_north`. dk65-07: 47 ha lasu rysowane z `far_east` leży w południowych 580 m dk65-08; po zwolnieniu dk65-06 bok E
kafla 07 zamyka się, sektor wraca i kopiec podszytu (płaski, kolor wierzchołków) z kurtynami staje na jezdni kafla 08.
To samo: dk65-11 104 ha, dw671-tykocin-07 35 ha, -08 27 ha, -09 25 ha, industrial-c 14 ha, maczka 6,5 ha.
Poprawka: drzewostan jest cięty po granicach sektorów (`sector_regions` = ten sam podział co `sector_of`), każda część
idzie do sektora, w którym leży. dk65-07 po regeneracji: trójkąty poza własnym sektorem `far_east` 20,3 % → 0 %,
`far_south` 11,9 % → 0 %; koszt +12 % trójkątów tła High (53 508 → 60 137), Low 12 446 → 13 101 (limit 27 000).

### 6. Streamer: obiekty krawędzi pod gotowym kaflem (`EdgeSides`, `WorldStreamer.RefreshEdges`, `WorldEdgeBuilder`)
- Sektor dali i część fartucha chowają się także wtedy, gdy gotowy jest kafel **po przekątnej** (korytarz DK65 idzie
  schodkami 06 → 07 → 08: 06 i 08 nie mają wspólnego boku, więc ich szew nigdy się nie otwierał).
- Fartuch jest cięty na 8 części (boki + narożniki `Apron_NE/SE/SW/NW`); narożnik znika, gdy otwarty jest któryś z jego
  boków albo gotowy kafel po przekątnej. Sceny ze starego importu (4 części) chowają wtedy cały bok fartucha.
- Widoczność sektorów dali i fartucha liczy się od gotowych sąsiadów niezależnie od stanu samego kafla (`coveredSides`):
  kafel w trakcie aktywacji nie rysuje już swojego tła w kaflu, po którym jedzie ciężarówka. Zamknięcia dróg (kolizja,
  tablice) nadal otwierają się dopiero, gdy oba kafle są gotowe.

## Wyniki (pomiar w edytorze, High, pogodnie, 1920 × 1080; `artifacts/trees-s24/`)

Rundy: „przed” → r1 (korony, atlasy, instancje ogrodowe) → r2 (świerk jako kalenice ze zwisającymi gałązkami, brzoza
z dwoma rodzajami kart, skrajnia, LOD1 odchudzony). Rundy 3 nie użyto. SBS: `artifacts/trees-s24/sbs/*-before-vs-r2.jpg`,
referencja `refs/ref_mly_knyszyn_road.jpg` (Mapillary 525325368849219, CC BY-SA 4.0) w `sbs/ref-vs-game-dk65-inlet-south.jpg`.

| Pomiar (edytor, `compare_stats.py`) | przed | po (r2) |
|---|---|---|
| knyszyn, 66 kamer: draws (szacunek) | 18 390 | 18 452 (+0,3 %) |
| knyszyn: trójkąty sceny | 55,26 M | 54,67 M (−1,1 %; karty koron ogrodowych zniknęły z High) |
| knyszyn: draws instancji / trójkąty instancji | 5 573 / 1,306 M | 5 833 (+4,7 %) / 1,455 M (+11,5 %) |
| knyszyn: najcięższa kamera (`rynek-owner-04`) | — | 536 draws, 1,72 M + 0,03 M instancji |
| dk65-05, 26 kamer: draws / trójkąty sceny | 3 759 / 11,43 M | bez zmian |
| dk65-05: trójkąty instancji | 1,104 M | 1,113 M (+0,8 %) |
| tło dali dk65-07 (High / Low) | 53 508 / 12 446 | 60 137 / 13 101 |

| Model (tris LOD0 / LOD1) | przed | po |
|---|---|---|
| lipa | 3128–3272 / 684–720 | 3272–3354 / 776–822 |
| klon | 2450–2520 / 524–586 | 2916–2996 / 670–688 |
| brzoza | 3380–3534 / 908–970 | 2936–2976 / 690–744 |
| olsza | 4024–4130 / 826–874 | 3098–3122 / 744–810 |
| sosna | 1484–2414 / 780–1306 | 1628–2670 / 838–1408 |
| świerk | 676–900 / 344–364 | 696–904 / 344–364 |
| topola (nowa) | — | 3638–3660 / 850–892 |

Skrajnia w Knyszynie: 5604 drzewa sprawdzone, 36 obniżonych, 4 usunięte. Drzewa ogrodowe: 1770 z 3243 to instancje biblioteki
na High. Czas klatki GPU i pamięć NIE były mierzone (pomiar tylko w buildzie na bezczynnej maszynie — lider, `pc-metrics.ps1`);
liczby wyżej to szacunek draws / trójkątów edytora. Tekstury: 5 atlasów liści 512 → 1024 px (`UNVERIFIED` wpływ na pamięć,
rząd +5 MB po kompresji).

Dowód renderem dla „zielonej ściany” (`sbs/dk65-07-08-seam-far-sectors-before-after.jpg`, `farproof.ps1`): scena samego
dk65-07, kamera na wysokości kabiny 56 m za szwem północnym (strona dk65-08), maska `-Mask far_east` / `far_north`.
Przed: w kadrze na północ od kafla widać geometrię `far_east` (las tła); po regeneracji `far_east` nie ma tam nic —
wszystko, co stoi w obszarze dk65-08, należy do `far_north`, który streamer chowa przy sąsiedzie od północy.

Testy: `tests/gis/test_trees_0308.py` 12, `test_far_field.py` +1; pełny `pytest tests/gis`: 2569 passed, 11 failed, 1 skipped,
2 xfailed — wszystkie 11 dotyczą kafli miejskich Białegostoku i katalogów tras (industrial-c, maczka, kleeberga,
knyszynska: `routeLengthM`, ratchety `lane_blind_end` / wysp, `route_links`, determinizm eksportu C), których ta gałąź
nie dotyka (baza gałęzi sprzed przebudowy lidera; nie sprawdzane ponownie na main). EditMode Win64: 1420 / 1318 passed /
1 failed (`RegionSelectTests.ShippedCatalog…`: ten sam nieaktualny `routeLengthM` industrial-c) / 101 skipped.

Zbieżność z gałęzią `farfield-blocks-cli` (Codex, ADR 0311, nie scalona): tam sektor dali w stronę każdego
zarejestrowanego sąsiada (także po przekątnej) jest wyłączony na stałe (`EdgeSides.FarSectorMayShow`). Próbne scalenie:
jeden konflikt tekstowy w `WorldStreamer.RefreshEdges` (linia `farSectors[i].SetActive`) — przy scalaniu wziąć wersję
Codexa dla sektorów dali, a z tej gałęzi zostawić fartuch (`ApronPieceVisible`, `coveredSides`); `far_field.py` łączy się
automatycznie (tam budynki, tu drzewostany). Cięcie drzewostanów po sektorach jest potrzebne także z regułą Codexa:
sektor bez sąsiada (np. `far_east` dk65-11 ze 104 ha lasu leżącego na północ) pozostaje widoczny.

## Konsekwencje i otwarte punkty

- **Po scaleniu trzeba**: zregenerować tło dali każdego kafla (`far_field.py --region <id>`, < 2 min / kafel) i zaimportować
  kafle ponownie (narożniki fartucha, nowe drzewa i tekstury lasu wchodzą przy imporcie; instancje ogrodowe i skrajnia
  dopiero po `build_world`). Bez reimportu działa już reguła streamera (stare sceny chowają cały bok fartucha).
- **Brak potwierdzenia w jeździe**: poprawka „zielonej ściany” jest potwierdzona danymi i testami, nie renderem ze streamingu
  w dk65-08 / industrial-c / dk65-10 / tykocin-06 / -09 — to wymaga buildu z przebudowanymi kaflami.
- Świerk z bliska nadal uproszczony (4 trójkąty na konar, limit 1000 tris z ADR 0187); impostory liściastych na 60–150 m
  bywają rozmyte (256 × 384 px na widok).
- Wierzba (głowiasta) — brak modelu; studium 0227 nietknięte. Topola jest w bibliotece, ale żadne dane jej nie używają
  (gatunki szpalerów DK65 są `UNVERIFIED`).
- Jesion i kasztanowiec ogrodowy używają modeli lipy i klonu.
- Odległości LOD drzew (20 / 60 m × lodBias) są z czasów telefonu; na PC warto je wydłużyć (zakres rendering-perf).
- Low: bez zmian w treści poza nowymi siatkami LOD1 / impostorami biblioteki; nie mierzone na telefonie (D73).

## Dopisek render-artifacts-s24 (2026-11-26): ciemne romby w koronach (krytyk fala 11, P0 #3)
**Przyczyna (dowód).** Drzewa przy ulicy w kaflach z działkami, za małe na instancję biblioteki (r < `LIB_MIN_R_M` 1,6 m;
w kadrze `knyszyn-w/tykocka-dw671-out` 30 z 46 drzew pasa ulicy, np. jesion/klon r 1,25 m), na High są pełnym drzewem zestawu
(`garden_tree(lite=False)`). Ten wariant miał wewnątrz korony ciemny 4-boczny „rdzeń” `PLT._core` (occ 0,26, sides=4) — przez
dziury kart z alfą widać go z ulicy jako ciemny romb o prostych krawędziach (ten sam błąd, który ADR 0170 usunął z wariantu
lite). Dowód offline (`preview_kit.render`, rdzeń pomalowany na magentę): `artifacts/render-artifacts-s24/preview/kit_full_before_core_magenta.jpg`
— magenta dokładnie w miejscu rombów. Nie LOD/impostor/crossfade (instancje biblioteki w kadrze nie mają rombów).

**Poprawka.** Wariant pełny bez `_core`; karty korony ciemnieją ku osi (`occ_mid` 0,58–0,68, wachlarz 4 trójkątów — jak lite+core,
ADR 0170). −6 trójkątów na drzewo (40 → 34 klon/lipa), ta sama liczba draw calli. Low bez zmian (`tris_low` 15 428 = 15 428).
knyszyn-w po regeneracji: drzewa ogrodowe High 19 010 → 18 302 tris; okna budżetu High −1 000…−3 000 tris.
Test: `tests/gis/test_horizon_0170.py::test_full_garden_tree_has_no_dark_core_body`.
Render przed|po (High, pogodnie): `artifacts/render-artifacts-s24/sbs/crop-trees-before-after.jpg` — ostre romby zniknęły, został
miękki cień środka korony bez krawędzi. Inne kafle z działkami dostaną zmianę przy najbliższej regeneracji (lider).

## Dopisek crown-lod-s24 (2026-11-27): stipple na krawędziach koron i „topiąca się” plama (krytyk build #10, TOP 3)
**Diagnoza (pomiar, nie hipoteza).** Widok spawnu `knyszyn-w` z buildu #10 odtworzony (kamera `cab-driver`, edytor High PC,
oraz player build #10 / build gałęzi, `artifacts/crown-lod-s24/`).
- `Kamion/Vegetation` **nie ma** LOD crossfade (zero `LOD_FADE_CROSSFADE`); `WorldInstances` przełączał LOD twardo:
  High `treeCardLodScale` 1,0 → LOD0 < 20 m, LOD1 < 60 m, impostor dalej.
- **Plama = impostor.** A/B `rq_card=1.5` zamienia rozmytą plamę (x ~1010–1170) na ostre karty LOD1: drzewo stoi w 60–90 m,
  a impostor (6 widoków 256 × 384 px, liniowy blend dwóch widoków 60° od siebie = podwójny obraz) zajmuje tam ~190 px.
- **Stipple = alfa-test przerw między liśćmi ~1 px, nie dither.** Player build #10, korona klonu: izolowane piksele nieba
  0,21 % z A2C, 0,93 % bez A2C (`-rq_a2c 0`), 0,96 % przy MSAA 1 → A2C już łagodzi, LOD crossfade nie istnieje, więc to nie
  dither crossfade'u. Próba „snap A2C do pełnych próbek” (gaszenie ordered dither NVIDIA): 0,9 % pikseli zmienionych,
  różnicy nie widać → odrzucona i usunięta. Edytorowe VQA nie odtwarza A2C playera (inne proporcje pikseli) — stipple
  oceniany tylko w playerze.

**Decyzja.**
1. High `treeCardLodScale` 1,0 → **1,5** (karty LOD1 do 90 m; Ultra 1,5 → 2,0, monotoniczność tierów). `WORKING_VALUE`.
2. **Cross-fade LOD1 → impostor** na ostatnich 25 % dystansu LOD1 (High 67,5–90 m; `WorldInstances.TreeFadeBand`):
   w paśmie rysowane są oba LOD drzewa (per instancja), a `Kamion/Vegetation` (`VegCutoff`) podnosi cutoff kart ponad 1
   i obniża cutoff impostora z ponad 1 do własnego — przejście kształtem liści / tekseli (dissolve w teksturze), bez wzoru
   ekranowego i bez skoku. Odległość liczona per instancja w etapie wierzchołków (te same wartości w przebiegu głębi i koloru).
   Przełącznik tieru `treeLodFade` (PC Medium/High/Ultra tak, Low nie; profil mobilny: nie), A/B `rq_lodfade 0|1`.
   Pień LOD1 (kora, nieprzezroczysty) nadal przełącza się twardo na końcu pasma — widoczne słabo, otwarte.
3. **Blend widoków impostora** `smoothstep(0,3; 0,7)` zamiast liniowego: jeden ostry widok dla większości azymutów,
   przejście tylko w środkowych 24° sektora.
4. **Fill zminiaturyzowanych liści** (`VegCutoffFill`): gdzie tekstura liści jest pomniejszona (mip > 1), cutoff spada
   o do 0,3 (`WorldInstances.LeafMipFill`, `WORKING_VALUE`; A/B `rq_leaffill`). Player, korona klonu: piksele mieszane
   (krawędzie przerw) 8,2 % → 4,2 %, izolowane niebo 0,01 % → 0,00 %; duże prześwity zostają. 0,45 zlewało korony w masę.
5. `Vegetation.shader` po ręcznym scaleniu 0352 + 0354: kompiluje się bez błędów; dwa ostrzeżenia fxc z buildu #10
   (`potentially uninitialized variable` w `VegAlpha` i `VegShadow`) usunięte — build gałęzi: 0 ostrzeżeń `Kamion/Vegetation`.
6. Poprawka narzędzia: `rq_a2c 0` działa w edytorowym VQA (kopie materiałów brały stare `m_LeafA2C`).

**Koszt (edytor, High PC 1920 × 1080, pogodnie, `artifacts/crown-lod-s24/compare-before2-after2.md`).** `drawsEst` obiektów
kafla bez zmian na 8 kamerach; draw calle instancji +0…+11 (cab-driver 96 → 106), trójkąty instancji +3,6k…+17k
(cab-driver 47,3k → 58,7k), trójkąty cieni instancji +3,6k…+17k (karty LOD1 rzucają cień, `treeShadowLodMask` 3).
Czas klatki: patrz `pc-metrics` niżej.

**pc-metrics** (`artifacts/crown-lod-s24/pc/`, GTX 1070 + i5-10400F, maszyna dewelopera ≠ referencja → werdykt INVALID
z definicji; `knyszyn-w` High 1920 × 1080, autopilot trasy 50 km/h, 90 s). Ta sama treść (build gałęzi, A/B parametrami):
| przebieg | GPU p50 / p95 / p99 [ms] | draw calls p50 / p95 | trójkąty p95 |
|---|---|---|---|
| bez klatkowania, stare ustawienia (`rq_card 1, rq_lodfade 0, rq_leaffill 0`) | 6,10 / 8,18 / 8,89 | 1411 / 1703 | 3,78 M |
| bez klatkowania, ta gałąź | 6,07 / 7,99 / 8,66 | 1468 / 1742 | 3,84 M |
| build #10 (baza, inna treść kafla), bez klatkowania | 6,07 / 7,58 / 8,21 | 1410 / 1681 | 3,91 M |
| 60 FPS: build #10 / ta gałąź | 8,69 / 9,89 / 10,37 → 8,91 / 10,03 / 10,50 | 1435 → 1504 | 3,98 → 3,91 M |
Wniosek: koszt GPU zmian w szumie pomiaru (A/B tej samej treści: −0,03…−0,23 ms), draw calle +4 % (+57 p50), pamięć
VRAM 964 = 964 MB. Jedna klatka 15,5 ms w przebiegu gałęzi (p99 8,6 ms) — pojedynczy skok, niepowtórzony w 60 FPS.

## Dopisek impostor-rebake-s24 (2026-11-27): „kolce” koron (krytyk day27 pkt 7) i ostrzejszy impostor
**Diagnoza.** W `route-s0426` (knyszyn-w, High) cienkie ukośne smugi wychodzą z koron klonów 10–30 m od kamery. To karty
liści (kwadrat, kwadratowa komórka UV) widziane prawie krawędzią: cała tekstura kępy ściśnięta w pasek kilku pikseli.
**Decyzja.** `Kamion/Vegetation` `VegCardEdge` (tylko karty, nie impostor / HLOD): anizotropia jakobianu UV w przestrzeni
ekranu, `sqrt(λmin/λmax)` ≈ |cos| kąta patrzenia; poniżej 0,12 cutoff karty > 1 (znika), powyżej 0,3 bez zmian, smoothstep
pomiędzy (`WorldInstances.CardEdgeFade`, global `_KamionCardEdge`, `WORKING_VALUE`; A/B `rq_cardedge=0`). Liczone z samego
UV, więc przebieg głębi (`VegetationDepth`, `DepthOnly`) i koloru odrzucają te same fragmenty; cienie bez zmian. Usuwa
~5 % rzutowanego pola kart (|cos| jednostajny na sferze → ∫₀^0,3 udział ≈ 0,05). Bez nowych draw calli (66 kamer: draw
calle i trójkąty identyczne), koszt ~15 ALU na fragment liścia (pochodne już liczone przez `VegCutoffFill`).
**Wynik** (`artifacts/impostor-rebake-s24/`): kolce znikają w pogodnie i pochmurno (`sbs-zoom/route-s0426-crown-*.jpg`,
`view/z1.png` 200 %), gęstość koron bez widocznej zmiany; zmienione piksele (fuzz 6 %) ≤ 0,08 % kadru na wszystkich kamerach.
Atlas impostorów przebake'owany 4096 × 1024 — ADR 0023, addendum impostor-rebake-s24.
Otwarte: ocena w playerze (A2C/MSAA 4) i przez `visual-critic`; próg 0,12/0,3 z jednej kamery.
