# ADR 0193 — Sygnalizator S-1: tarcza kontrastowa, warianty głowic, kamera P11-094 (D-6)

Status: Proposed (agent world-builder, s20, gałąź `sigplate-0193`), 2026-11-13. Do scalenia przez lidera.

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

## Budżet (A/B, prototyp, jedna głowica)
| | tris LOD0 | tris LOD1 | materiały (draws) |
|---|---|---|---|
| przed (3 komory) | 120 | 84 | 6 |
| po (3 komory) | 188 | 80 | 6 (te same) |
Region C: 68 głowic = +4,6 tys. tris LOD0 w całym regionie, 0 nowych draw calls. Warianty 1/2/ped/bike nieużyte w świecie = 0 kosztu w scenie.

## Walidacja
- `tests/gis/test_signal_head_0193.py` (17 przypadków: 5 wariantów x 3 stany + 2; normalne soczewek i obwódki +y, obudowa mieści soczewki, tarcza <= obudowa + 0,2 m, obwódka tylko z przodu i wewnątrz tarczy, odstęp >= 2 mm, tył najdalej -85 mm, tris < 260 / 110, materiały) + `test_p1_0161`, `test_street_r9`, `test_furniture_r1`.
- Arkusz prototypów przed/po: `artifacts/sigplate-0193/{before,after}-heads.png`; render sceny: patrz raport.

## Otwarte
- Kolor obwódki, piktogramy ped/bike, rozmiar Ø200 vs Ø300 w Białymstoku (UNVERIFIED; sprawdzić w Mapillary po zdjęciach z tools/refs).
- Stawianie `signal_ped`/`signal_head2` wg OSM `crossing=traffic_signals` (obecnie pomijane w furniture.py:766): poza zakresem.
