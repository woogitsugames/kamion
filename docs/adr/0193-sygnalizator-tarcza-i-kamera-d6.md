# ADR 0193 — Sygnalizator S-1: tarcza kontrastowa, warianty głowic, kamera P11-094 (D-6)

Status: PROPOSED (agent world-builder, s20, gałąź `sigplate-0193`), 2026-11-14. Do scalenia przez lidera.

## Kontekst
Review 0179 (P2): sygnalizator ma dużą białą prostokątną tarczę za komorą, większą od komory; D-6 dominuje pierwszy plan P11-094.
Przyczyna tarczy (zmierzona na siatce, nie zgadnięta): `props.signal_head` miał obudowę 0,36 x 0,26 x 1,04 m, trzy soczewki Ø0,30 rozstawione co 0,34 m (zajmowały 1,0 m,
czyli wystawały poza obudowę), czarną tarczę 0,66 x 1,36 m ZA obudową (y -0,14) i „obwódkę" jako osobny box 0,72 x 1,42 m, grubość 4 mm, szary 0,7 ZA tarczą.
Od tyłu głowicy (kamera 063 stoi za wysięgnikiem) najbliższą płaszczyzną był ten szary box, czyli jednolity jasny prostokąt większy niż głowica. Dodatkowo
soczewki miały normalne -y (winding), czyli od strony kierowcy odcinane przez back-face culling.

## Decyzja
1. `props._signal_head(lit, n, d, plate, order)`: tarcza (czarna, margines 90 mm wokół obudowy, WORKING_VALUE) leży PRZED obudową (y 0,085..0,097), obwódka
   retrorefleksyjna żółto-biała (`signal_border` [0,62 0,55 0,20]; kolor UNVERIFIED, zadanie: „biała/żółta") to 4 paski 25 mm tylko na licu, 3 mm nad tarczą
   (bez z-fightingu), od tyłu głowica jest czarna. Obudowa mieści wszystkie soczewki (rozstaw = Ø + 60 mm). Soczewki normalne +y, daszek (góra + 2 policzki, tylko LOD0).
   Środek głowicy = środek obudowy, tył obudowy 85 mm od osi głowicy (słup r ~ 50 mm przy offsecie 0,15 m nie przecina głowicy).
2. Warianty (`SIGNAL_VARIANTS`): `signal_head` (S-1, 3 komory Ø300, jedyny stawiany przez `furniture.signals` / `gate3_landmarks`), `signal_head2` (2 komory),
   `signal_head1` (1 komora), `signal_ped` (2 komory Ø200, typ S-5), `signal_bike` (3 komory Ø200 bez tarczy). Piktogramy (pieszy, rower) NIE modelowane — UNVERIFIED,
   prototypy czekają na authored placement. Materiał `signal_yellow_on` dodany (żółte światło).
3. Kamera `photo_P11-094`: pozycja z GPS Commons (776,6 387,2) stawiała słup D-6 `osm:node/3867824992` w odległości **2,8 m** od obiektywu (nie „2-3 m za blisko": 10 m).
   Na zdjęciu słup stoi ~13 m dalej, x 325/960 (11,6° na lewo od osi, słup 170 px dla ~3 m, f = 753 px). Przecięcie promienia od słupa (azymut 232,4°) z namiarem na narożnik
   hali (224,7°, widziany 20° na lewo) daje (784,3 394,0), azymut 244,5°. Kontrola niezależna: koniec ściany północnej (670,6 389,5) ma teraz namiar 267,7° = x 802 px
   (zdjęcie 800-850, stara pozycja dawała 867). Znak i dane OSM bez zmian (znak stoi w miejscu węzła OSM).

## Budżet (A/B)

### Prototyp (jedna głowica, `art-source/world/props/props_meta.json`)
| | tris LOD0 | tris LOD1 | materiały (draws) |
|---|---|---|---|
| przed (3 komory) | 120 | 84 | 6 |
| po (3 komory) | 188 | 80 | 6 (te same) |

Warianty nieużyte w świecie (`signal_head2_*`: 136/64 tris, 5 mat.; `signal_head1_*`: 84/48, 4 mat.; `signal_ped_*`: 136/64, 5 mat.; `signal_bike_*`: 168/60, 4 mat.) = 0 instancji, 0 kosztu w scenie.
- `bialystok-industrial-c`: 69 głowic (`green` 30, `red` 29, `off` 10) = +4 692 tris LOD0 / -276 tris LOD1 w całym regionie, 0 nowych draw calls.
- `bialystok-dojlidy`: 42 głowice (`green` 29, `red` 13) = +2 856 tris LOD0 / -168 tris LOD1, 0 nowych draw calls.

### Kamery sceny (Low A/B oraz High)
UWAGA: `before-C` istniał tylko dla `Low` (brak zapisanego `before-C High` w repo); `after-C2` i `after-D2` wyrenderowano po scaleniu z `origin/main` na obu tierach (`Low` renderScale=0.75, `High` renderScale=1.0).

| Kamera / scena | drawsEst (before -> after Low / High) | trisExact (before -> after Low / High) | instanced draws (before -> after Low / High) | instanced trisExact (before -> after Low / High) |
|---|---|---|---|---|
| `sig-mast-back` | 104 -> 104 / 104 | 198 095 -> 198 759 / 388 353 | 48 (40 inst.) -> 48 (40 inst.) / 55 (203 inst.) | 2 989 -> 3 193 (+204) / 4 540 |
| `sig-mast-front` | 474 -> 474 / 955 | 560 096 -> 560 963 / 2 539 778 | 114 (99 inst.) -> 113 (99 inst.) / 310 (499 inst.) | 14 093 -> 14 301 (+208) / 42 078 |
| `sig-pole-34` | 487 -> 487 / 784 | 596 890 -> 598 438 / 2 636 222 | 97 (87 inst.) -> 97 (86 inst.) / 181 (412 inst.) | 10 432 -> 10 584 (+152) / 30 428 |
| `sig-pole-front` | 496 -> 496 / 1 013 | 605 599 -> 606 466 / 2 740 800 | 117 (105 inst.) -> 117 (105 inst.) / 297 (496 inst.) | 15 560 -> 15 706 (+146) / 39 823 |
| `sbs-g3-b-182011943700132` (`gate3_signal`) | - -> 203 / 272 | - -> 184 064 / 745 691 | - -> 145 (130 inst.) / 203 (609 inst.) | - -> 36 145 / 51 195 |
| `photo_P11-063` (Dojlidy) | - -> 329 / 601 | - -> 340 146 / 1 702 445 | - -> 121 (249 inst.) / 196 (706 inst.) | - -> 16 938 / 92 509 |
| `photo_P11-094` (Dojlidy) | - -> 202 / 535 | - -> 293 717 / 1 644 693 | - -> 95 (80 inst.) / 187 (396 inst.) | - -> 17 417 / 64 640 |

### `WORLD_MEMORY` (`import-region.ps1`, Low & High vs baseline `origin/main`)
| Region / tier | `render_meshes` | `instances` | `collision_src` | `total` (vs baseline) | `furniture` (vs baseline) |
|---|---|---|---|---|---|
| `bialystok-industrial-c` Low | 83.3 MB | 22.6 MB | 17.1 MB | 123.0 MB (123.0 MB, +0.0) | 8,6 (8,6) |
| `bialystok-industrial-c` High | 226.2 MB | 22.6 MB | 17.1 MB | 265.9 MB (265.9 MB, +0.0) | 8,6 (8,6) |
| `bialystok-dojlidy` Low | 64.5 MB | 18.2 MB | 15.5 MB | 98.2 MB (98.2 MB, +0.0) | 7,8 (7,8) |
| `bialystok-dojlidy` High | 179.8 MB | 18.2 MB | 15.5 MB | 213.5 MB (213.5 MB, +0.0) | 7,8 (7,8) |

## Walidacja
- `uv run --project tools/worldgen python -m pytest tests/gis/test_signal_head_0193.py tests/gis/test_photo_cameras_0174.py tests/gis/test_dojlidy_0179.py tests/gis/test_road_fidelity.py -q` -> **35 passed, 1 xfailed** (w tym `test_signal_head_0193.py`: 17 passed — 5 wariantów x 3 stany + 2; normalne soczewek i obwódki +y, obudowa mieści soczewki, tarcza <= obudowa + 0,2 m, obwódka tylko z przodu i wewnątrz tarczy, odstęp >= 2 mm, tył najdalej -85 mm, tris < 260 / 110, materiały).
- Pełny `uv run --project tools/worldgen python -m pytest tests/gis -q` (`artifacts/sigplate-0193/pytest-gis.log`) -> **1168 passed, 1 failed, 2 xfailed** w 1129.80s (jedyny błąd to `tests/gis/test_dojbld_0185.py::test_fence_mesh_mips_do_not_preserve_coverage`, spowodowany wcześniejszym revertem w `origin/main` `e668a9588` na `InstanceImporter.cs`, niezwiązany z `sigplate-0193`).
- Unity EditMode (`pwsh scripts/test.ps1 -Platform EditMode`, `artifacts/sigplate-0193/editmode.log`) -> **581 total, 580 passed, 0 failed, 1 skipped (Skipped:Ignored)**.
- Wizualna kontrola (arkusz prototypów + rendery sceny Low/High + porównania SBS):
  - Arkusz prototypów: `artifacts/sigplate-0193/{before,after}-heads.png` i `artifacts/sigplate-0193/sbs2/after-heads.jpg` (po naprawie sortowania głębi w `sheet.py` na per-pixel Z-buffer 2x SSAA: wszystkie 5 wariantów czyste, czarna tylna tarcza, zero artefaktów 3/4).
  - Montaże sceny C (2x2) przed/po: `artifacts/sigplate-0193/before-C-sheet.jpg`, `artifacts/sigplate-0193/sbs2/after-C-sheet-Low.jpg`, `artifacts/sigplate-0193/sbs2/after-C-sheet-High.jpg` (czarny tył tarczy na wysięgniku i słupie, kontrastowa obwódka tylko z przodu, czytelne czerwone soczewki i daszki).
  - Brama 3 (`sbs-g3-b-182011943700132`): `artifacts/sigplate-0193/sbs2/gate3-signal-Low.jpg`, `artifacts/sigplate-0193/sbs2/gate3-signal-High.jpg`.
  - Dojlidy SBS vs zdjęcia ref.: `artifacts/sigplate-0193/sbs2/sbs-P11-063-Low.jpg`, `artifacts/sigplate-0193/sbs2/sbs-P11-063-High.jpg` (czarne plecy sygnalizatorów po prawej), `artifacts/sigplate-0193/sbs2/sbs-P11-094-Low.jpg`, `artifacts/sigplate-0193/sbs2/sbs-P11-094-High.jpg` (D-6 w odległości ~13 m zgodny ze skalą na zdjęciu i geometrią narożnika/ściany północnej Rosti).
  - Surowe zrzuty: `artifacts/sigplate-0193/{before-C,after-C2/Low,after-C2/High,after-C2/gate3-Low,after-C2/gate3-High,after-D2/Low,after-D2/High}/`.

## Otwarte
- Kolor obwódki, piktogramy ped/bike, rozmiar Ø200 vs Ø300 w Białymstoku (UNVERIFIED; sprawdzić w Mapillary po zdjęciach z tools/refs).
- Stawianie `signal_ped`/`signal_head2` wg OSM `crossing=traffic_signals` (obecnie pomijane w furniture.py:766): poza zakresem.
