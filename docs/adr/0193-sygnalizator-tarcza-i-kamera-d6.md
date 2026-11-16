# ADR 0193 — Sygnalizator S-1: tarcza kontrastowa (M66 / Dz.U. rys. 10.28), warianty głowic, kamera P11-094 (D-6)

Status: przyjęty (scalony do main 2026-11-15, `fa857b11b`; status zaktualizowany 2026-11-16); pierwotnie: PROPOSED (agent world-builder, s20, gałąź `sigplate-0193`, runda 3 po M66), 2026-11-14. Do scalenia przez lidera.

## Kontekst
Review 0179 (P2): sygnalizator ma dużą białą prostokątną tarczę za komorą, większą od komory; D-6 dominuje pierwszy plan P11-094.
Przyczyna tarczy (zmierzona na siatce, nie zgadnięta): `props.signal_head` miał obudowę 0,36 x 0,26 x 1,04 m, trzy soczewki Ø0,30 rozstawione co 0,34 m (zajmowały 1,0 m,
czyli wystawały poza obudowę), czarną tarczę 0,66 x 1,36 m ZA obudową (y -0,14) i „obwódkę" jako osobny box 0,72 x 1,42 m, grubość 4 mm, szary 0,7 ZA tarczą.
Od tyłu głowicy (kamera 063 stoi za wysięgnikiem) najbliższą płaszczyzną był ten szary box, czyli jednolity jasny prostokąt większy niż głowica. Dodatkowo
soczewki miały normalne -y (winding), czyli od strony kierowcy odcinane przez back-face culling.

Research M66 (`research/cloud/p23-traffic-signals`, przegląd `docs/reports/REVIEW-2026-11-14-s20-cloud-m66.md` §5, Dz.U. 2019 poz. 2311 zał. 3 pkt 3.3.5.6 s. 715–716, pkt 3.3.2 s. 708–709, pkt 7.2.2 s. 755, rys. 10.28a s. 802, SOURCED):
- Tarcza kontrastowa (ekran kontrastowy) jest integralnym elementem sygnalizatora **tylko nad jezdnią** (15/15 widocznych skrzyżowań w Białymstoku); głowice boczne na masztach/słupkach obok jezdni (0/11) oraz sygnalizatory dla pieszych S-5 nie mają tarczy.
- Wymiary tarczy nad jezdnią dla Ø300 (rys. 10.28a): **850 × 1400 mm** (`0,85 × 1,40 m`), czarna z zaokrąglonymi narożami **R70**, **biała obwódka 40 mm** odsunięta o **20 mm** czarnego marginesu od krawędzi zewnętrznej (żółtawej obwódki nie stwierdzono nigdzie).
- Tarcza leży **za obudową** (na tylnej płaszczyźnie komory), tak że czarna obudowa i daszki wystają przed tarczę w stronę kierowcy (wycinek C66-031).
- Wystająca część daszka ochronnego ≥ 200 mm (zalecenie Dz.U. s. 709; z kadrów 0,21–0,28 m -> `0,22 m` WORKING_VALUE); pochylenie głowic nad jezdnią ku nadjeżdżającym `5–10°` (Dz.U. s. 755 -> `7°` WORKING_VALUE).

## Decyzja
1. **Tarcza kontrastowa tylko na wysięgnikach (`signal_head_*` vs `signal_head_side_*`)**:
   - W `props.SIGNAL_VARIANTS` rozdzielono głowice S-1 3×Ø300 na wariant wysięgnikowy z tarczą `signal_head` (`plate=True`, stawiany na ramionach masztów w `furniture.py:865` i `gate3_landmarks.py:488`) oraz wariant boczny bez tarczy `signal_head_side` (`plate=False`, stawiany na słupach bocznych i masztach przy krawędzi jezdni w `furniture.py:868/874` oraz `gate3_landmarks.py:492`).
   - Sygnalizatory piesze `signal_ped` (typ S-5, 2×Ø200) oraz rowerowe `signal_bike` (3×Ø200) mają `plate=False`. Wszystkie warianty eksportowane są w 4 stanach świecenia `("red", "yellow", "green", "off")`.
2. **Wymiary tarczy, obwódki, obudowy, daszków i pochylenia (`props._signal_head`)**:
   - Tarcza kontrastowa `0,85 × 1,40 m` (`ph = 0,425`, `pz = 0,70` dla 3 komór) z zaokrąglonymi narożami `R70` (`0,070 m`) leży na tylnej płaszczyźnie komory (`y = -0,085..-0,075`), **za** czarną obudową komory `280 mm` (`y = -0,080..+0,200`, szer. `0,38 m`, wys. `1,12 m`, rozstaw = Ø + 60 mm). Od tyłu zarówno tarcza, jak i obudowa są czarne (`signal_backplate` / `signal_housing`, 5 mm separacji eliminuje z-fighting).
   - Obwódka (`signal_border`, kolor biały jak `marking_white` `[0,55, 0,55, 0,54]`, SOURCED) to pierścień o szerokości `40 mm` (`0,040 m`) odsunięty o `20 mm` (`0,020 m` czarnego marginesu) od krawędzi zewnętrznej tarczy, umieszczony wyłącznie po stronie czołowej (`y = -0,072`, 3 mm przed licem tarczy, normalne `+y`).
   - Soczewki (normalne `+y`, `y0 = 0,203`) osłonięte są od przodu trzyczęściowymi czarnymi daszkami tunelowymi (góra + 2 policzki, LOD0) o długości `L = 0,22 m` (`y = 0,200..0,420`).
   - Głowice wysięgnikowe (`plate=True`) pochylone są o `7°` w dół w stronę nadjeżdżających (`_tilt_mesh_down`).
3. **Kamera `photo_P11-094`**: pozycja z GPS Commons (776,6 387,2) stawiała słup D-6 `osm:node/3867824992` w odległości **2,8 m** od obiektywu (nie „2-3 m za blisko": 10 m).
   Na zdjęciu słup stoi ~13 m dalej, x 325/960 (11,6° na lewo od osi, słup 170 px dla ~3 m, f = 753 px). Przecięcie promienia od słupa (azymut 232,4°) z namiarem na narożnik
   hali (224,7°, widziany 20° na lewo) daje (784,3 394,0), azymut 244,5°. Kontrola niezależna: koniec ściany północnej (670,6 389,5) ma teraz namiar 267,7° = x 802 px
   (zdjęcie 800-850, stara pozycja dawała 867). Znak i dane OSM bez zmian (znak stoi w miejscu węzła OSM).

## Budżet (A/B)

### Prototyp (jedna głowica, `art-source/world/props/props_meta.json`)
| Prototyp | tris LOD0 | tris LOD1 | materiały (draws) |
|---|---|---|---|
| przed (`signal_head_*`, 3 komory) | 120 | 84 | 6 |
| po — wysięgnik z tarczą R70 (`signal_head_*`) | 264 | 92 | 6 (te same) |
| po — słupek boczny bez tarczy (`signal_head_side_*`) | 168 | 60 | 4 (bez `signal_backplate` i `signal_border`) |

Warianty nieużyte w świecie (`signal_head2_*`: 212/76 tris, 5 mat.; `signal_head1_*`: 160/60, 4 mat.; `signal_ped_*`: 116/44, 3 mat.; `signal_bike_*`: 168/60, 4 mat.) = 0 instancji, 0 kosztu w scenie.
- `bialystok-industrial-c`: 69 głowic = **16 wysięgnikowych** (`signal_head_red` 8, `signal_head_green` 8) + **53 boczne bez tarczy** (`signal_head_side_green` 22, `signal_head_side_red` 21, `signal_head_side_off` 10). Względem stanu przed 0193: +4 848 tris LOD0 / **-1 144 tris LOD1** w całym regionie (względem rundy 2 `after-C2`: **-1 376 tris LOD0 / -868 tris LOD1** dzięki usunięciu tarcz z 53 głowic bocznych).
- `bialystok-dojlidy`: 42 głowice = **13 wysięgnikowych** (`signal_head_green` 9, `signal_head_red` 4) + **29 bocznych bez tarczy** (`signal_head_side_green` 20, `signal_head_side_red` 9). Względem stanu przed 0193: +3 264 tris LOD0 / **-592 tris LOD1** w całym regionie (względem rundy 2 `after-D2`: **-412 tris LOD0 / -424 tris LOD1**).

### Kamery sceny (Low A/B oraz High — `after-C3` / `after-D3`)
UWAGA: `before-C` istniał tylko dla `Low` (brak zapisanego `before-C High` w repo); `after-C3` i `after-D3` wyrenderowano po scaleniu z `origin/main` (`b0d9769fc`) na obu tierach (`Low` renderScale=0.75, `High` renderScale=1.0).

| Kamera / scena | drawsEst (before -> after-C3 Low / High) | trisExact (before -> after-C3 Low / High) | instanced draws (before -> after-C3 Low / High) | instanced trisExact (before -> after-C3 Low / High) |
|---|---|---|---|---|
| `sig-mast-back` | 104 -> 104 / 104 | 198 095 -> 198 759 / 388 353 | 48 (40 inst.) -> 52 (40 inst.) / 59 (203 inst.) | 2 989 -> 3 229 / 4 576 |
| `sig-mast-front` | 474 -> 474 / 955 | 560 096 -> 560 963 / 2 539 778 | 114 (99 inst.) -> 125 (99 inst.) / 320 (499 inst.) | 14 093 -> 14 189 / 41 826 |
| `sig-pole-34` | 487 -> 487 / 784 | 596 890 -> 598 438 / 2 636 222 | 97 (87 inst.) -> 109 (86 inst.) / 187 (411 inst.) | 10 432 -> 10 516 / 30 272 |
| `sig-pole-front` | 496 -> 496 / 1 013 | 605 599 -> 606 466 / 2 740 800 | 117 (105 inst.) -> 129 (105 inst.) / 307 (496 inst.) | 15 560 -> 15 594 / 39 615 |
| `sbs-g3-b-182011943700132` (`gate3_signal`) | - -> 203 / 272 | - -> 184 064 / 745 691 | - -> 147 (130 inst.) / 211 (609 inst.) | - -> 36 073 / 51 315 |
| `photo_P11-063` (Dojlidy) | - -> 329 / 601 | - -> 340 146 / 1 702 445 | - -> 129 (249 inst.) / 204 (706 inst.) | - -> 16 982 / 92 681 |
| `photo_P11-094` (Dojlidy) | - -> 202 / 535 | - -> 293 717 / 1 644 693 | - -> 95 (80 inst.) / 187 (396 inst.) | - -> 17 417 / 64 640 |

### `WORLD_MEMORY` (`import-region.ps1`, Low & High vs baseline `origin/main`)
| Region / tier | `render_meshes` | `instances` | `collision_src` | `total` (vs baseline) | `furniture` (vs baseline) |
|---|---|---|---|---|---|
| `bialystok-industrial-c` Low | 83.3 MB | 22.6 MB | 17.1 MB | 123.1 MB (123.0 MB, +0.1) | 8,6 (8,6) |
| `bialystok-industrial-c` High | 226.2 MB | 22.6 MB | 17.1 MB | 265.9 MB (265.9 MB, +0.0) | 8,6 (8,6) |
| `bialystok-dojlidy` Low | 64.5 MB | 18.2 MB | 15.5 MB | 98.2 MB (98.2 MB, +0.0) | 7,8 (7,8) |
| `bialystok-dojlidy` High | 179.8 MB | 18.2 MB | 15.5 MB | 213.5 MB (213.5 MB, +0.0) | 7,8 (7,8) |

## Walidacja
- `uv run --project tools/worldgen python -m pytest tests/gis/test_signal_head_0193.py tests/gis/test_p1_0161.py tests/gis/test_p1b_0172.py tests/gis/test_photo_cameras_0174.py tests/gis/test_dojlidy_0179.py tests/gis/test_road_fidelity.py -q` -> **62 passed, 1 xfailed** (w tym `test_signal_head_0193.py`: 26 passed — 6 wariantów x 4 stany + 2; pochylenie 7° dla wysięgnikowych i 0° dla bocznych, obudowa 280 mm z daszkami 220 mm wystająca przed tarczę, tarcza `0,85 × 1,40 m` R70 za obudową, biała obwódka 40 mm z marginesem 20 mm w kolorze `marking_white`, `signal_head_side_*` oraz `signal_ped_*` bez tarczy).
- Pełny `uv run --project tools/worldgen python -m pytest tests/gis -q` (`artifacts/sigplate-0193/pytest-gis.log`) -> **1168 passed, 1 failed, 2 xfailed** (jedyny błąd to `tests/gis/test_dojbld_0185.py::test_fence_mesh_mips_do_not_preserve_coverage`, niezwiązany z `sigplate-0193`).
- Unity EditMode (`pwsh scripts/test.ps1 -Platform EditMode`, `artifacts/sigplate-0193/editmode.log`) -> **581 total, 580 passed, 0 failed, 1 skipped (Skipped:Ignored)**.
- Wizualna kontrola (arkusz prototypów + rendery sceny Low/High + porównania SBS w `artifacts/sigplate-0193/sbs3/`):
  - Arkusz prototypów (6 wariantów): `artifacts/sigplate-0193/after-heads.png` i `artifacts/sigplate-0193/sbs3/after-heads.jpg` (`signal_head` z tarczą `0,85 × 1,40 m` R70, białą obwódką 40 mm / marginesem 20 mm za obudową 280 mm, daszkiem 220 mm i pochyleniem 7°; `signal_head_side`, `signal_ped`, `signal_bike` bez tarczy).
  - Montaże sceny C (2x2) przed/po: `artifacts/sigplate-0193/before-C-sheet.jpg`, `artifacts/sigplate-0193/sbs3/after-C-sheet-Low.jpg`, `artifacts/sigplate-0193/sbs3/after-C-sheet-High.jpg` (tarcza kontrastowa z białą obwódką wyłącznie na wysięgniku nad jezdnią, od tyłu czarna; głowica na słupie bocznym bez tarczy).
  - Brama 3 (`sbs-g3-b-182011943700132`, Rondo Putry): `artifacts/sigplate-0193/sbs3/gate3-signal-Low.jpg`, `artifacts/sigplate-0193/sbs3/gate3-signal-High.jpg` (dwie głowice na wysięgniku 8,8 m z tarczą kontrastową i białą obwódką, dwie głowice boczne na maszcie i wyspie bez tarczy).
  - Dojlidy SBS vs zdjęcia ref.: `artifacts/sigplate-0193/sbs3/sbs-P11-063-Low.jpg`, `artifacts/sigplate-0193/sbs3/sbs-P11-063-High.jpg` (głowica na słupku i głowica boczna na maszcie bez tarczy, zgodnie z C66-061 / P11-063; głowica na wysięgniku z czarną tarczą za komorą), `artifacts/sigplate-0193/sbs3/sbs-P11-094-Low.jpg`, `artifacts/sigplate-0193/sbs3/sbs-P11-094-High.jpg` (D-6 w odległości ~13 m zgodny ze skalą na zdjęciu i geometrią narożnika/ściany północnej Rosti).
  - Surowe zrzuty rundy 3: `artifacts/sigplate-0193/{after-C3/Low,after-C3/High,after-C3/gate3-Low,after-C3/gate3-High,after-D3/Low,after-D3/High}/`.

## Otwarte
- Piktogramy ped/bike, tarcze ażurowe/owalne na wybranych skrzyżowaniach (M66 §3–4: 3 ażurowe, 1 owalna ESTIMATED): poza zakresem generycznego prototypu S-1.
- Stawianie `signal_ped`/`signal_head2` wg OSM `crossing=traffic_signals` (obecnie pomijane w `furniture.py`): poza zakresem.
