# ADR 0185 — Dojlidy: budynki po recenzji 0179 (hala zakładu przy Kuronia, blok Kuronia 3, ogrodzenie, poziom LoD1)
Status: Proposed (agent world-builder, s20, gałąź `dojbld-0185`), 2026-11-13. Do scalenia przez lidera.
Poprzednik: ADR 0179, recenzja `docs/reports/REVIEW-2026-11-13-s19-0179.md` (P1 P11-094, P1 P11-001, P2 tło).

## Kontekst
Recenzja 0179: (1) hala północna zakładu przy Kuronia ~12 % za wysoka w kadrze P11-094 i bez niższego segmentu na
prawym końcu, (2) białe ogrodzenie panelowe u podstawy daje morę na Low, (3) okładzina czyta się jak siatka bloczków
i ma rząd małych okienek, których nie ma na zdjęciu, (4) blok Kuronia 3 wygląda jak tynkowany biurowiec z PRL
z czarnymi pasami okien, P2: dodatkowe białe bloki w tle za blokiem — sprawdzić wysokości LoD1.
Zakres: tylko region `bialystok-dojlidy`; region C bajt w bajt. Bramy segmentowe / Bravilor / kamera pasa: ADR 0196;
zieleń: ADR 0186.

## Ustalenia z danych (zmierzone)
- **Poziom odniesienia LoD1.** `measuredHeight` LoD1 2024 to wysokość bryły nad jej dolną ścianą
  (`ground_z_evrf2007`); dla 329 budynków kafla z LoD1 najniższy teren obrysu (NMT 2025) leży medianowo 0,06 m poniżej
  tej podstawy. Generator stawiał budynek na **medianie** terenu obrysu, więc na skarpie dach był za wysoko: mediana
  +0,22 m, p95 +1,42 m, max +3,52 m. Hala zakładu `bdot:2BE4B431-BC59…` +1,83 m (przy narożniku NE ściana 20,5 m
  zamiast 18,7 m = −9 %), budynek badawczy `bdot:2BE4B431-C1A0…` za blokiem Kuronia 3 (18,09 m) +2,69 m, hala
  Kuronia 2 +1,96 m. Same wysokości LoD1 są dobre — to odpowiedź na P2 „tło” i większość „12 %”.
- **Hala zakładu, P11-094.** 16 pasów paneli na ścianie; moduł 1,15 m × 16 = 18,4 m + cokół = wysokość LoD1 (18,92 m
  nad najniższym terenem). Linia dachu ściany północnej schodzi w dół na zachodnim końcu (x 793/960; koniec ściany
  x 870/960) do niższego segmentu w tej samej płaszczyźnie: wysokość 180 px wobec 255 px (0,71). Ortofoto 2024: wysoka
  hala kończy się na prostej równoległej do ściany wschodniej, 11,8 m od narożnika NW + ~2 m przesunięcia radialnego
  krawędzi dachu = 13,8 m (z namiaru w kadrze 15–19 m). Rzędu małych okienek na zdjęciu nie ma (lampy).
- **Ogrodzenie istnieje**: OSM way 702465389 (`barrier=fence`, 819 m wokół zakładu, 8,5 m od ściany północnej) i widać
  je na P11-094 jako cienką siatkę ze słupkami u podnóża skarpy. Mora: tekstura `fence_mesh` miała mipy zachowujące
  pokrycie alfa (`mipMapsPreserveCoverage`) — ~15 % tekseli kryjących na każdej odległości, czyli biała krata tam, gdzie
  piksel jest szerszy niż rozstaw drutów (50 mm).
- **Okładzina**: set `sandwich_ribbed` ma tylko fugi poziome, ale 10 % pionowych zacieków wpieczonych w albedo i był
  próbkowany w domyślnym kaflu 4 m (pasy 0,67 m) — stąd „bloczki”.
- **Blok Kuronia 3, P11-001**: panele pionowe w jasnym srebrnoszarym kolorze; trzy wysokie kondygnacje — parapety pasm
  okien ściany południowej na 0,19 / 0,51 / 0,82 wysokości = 2,7 / 7,2 / 11,5 m z 14 m, pasma ~1,4 m, od ~12 %
  długości; na szczycie zachodnim pionowy pas przeszklenia klatki przy narożniku południowym i małe okna (nie rysowane).

## Decyzja
1. **Generator (opt-in; region bez takich wpisów nie zmienia wyniku)** — `streetscape/buildings_mesh.py`:
   - `kind: building_rules` / `lod1_base_datum: true` — dach na poziomie podstawa LoD1 + wysokość (`roof_height`; nie
     mniej niż 60 % wysokości LoD1; tylko `height_source` LoD1 / authored z podanym `ground_z_evrf2007`).
   - `target_sets`: kilka wpisów `target: {building}` na ten sam budynek = suma `set` w kolejności pliku (było: ostatni
     wpis zastępował poprzednie w całości). Region C nie ma budynku z dwoma wpisami (test). `override:<id>` celuje
     w `building_part`.
   - `set.storeys`, `set.hall_windows: false` (bez losowanego rzędu okienek hali), `ground_z_evrf2007` w `building_part`.
2. **Materiały** (`streetscape/materials.py`, blok addytywny) i sety (`art-source/world/materials/_src/sets_facade.py`):
   - `sandwich_smooth` (kafel 3,45 m = 3 pasy 1,15 m, gładkie lico, fugi cieniowe, bez wpieczonych zacieków) →
     `hall_wall_smooth` z `panel_m: [6.0, 1.15]` (styk pionowy co 6 m i ton na panel — shader ADR 0092), kolor
     `hall_wall_white`.
   - `cladding_vertical` (panele pionowe 1,0 m) → `cladding_vertical_grey` (+ `__far_office` / `__far_ribbon`).
   - Oba sety generowane w 1024 px (High 1024, Medium 512, Low 256): ¼ pamięci zwykłego setu przy tej samej gęstości
     tekseli co `sandwich_ribbed` (kafel 3–3,45 m zamiast 6 m).
3. **Ogrodzenie** (`World/Import/InstanceImporter.cs`): tekstury `fence_*` bez `mipMapsPreserveCoverage` — druty
   cienieją z odległością i znikają tam, gdzie piksel jest szerszy od rozstawu; słupki i cokół zostają (jak na zdjęciu).
   Dotyczy wszystkich regionów (importer, nie dane generowane).
4. **Dane Dojlid** (`overrides.yaml`, 4 nowe bloki, stare nietknięte): `dojlidy-lod1-base-datum`; `rosti-west-wing`
   (`building_part`, 3234 m², 13,4 m nad podstawą LoD1 152,06, WORKING_VALUE ±1 m; granica 13,8 m ±2 m);
   `rosti-hall-cladding` (`hall_wall_smooth`, `hall_windows: false`); `kuronia3-office-block-facades` (`storeys: 3`,
   `cladding_vertical_grey`, `facades`: szczyt W — kolumna okien klatki, długie ściany — pasma 2,3–3,6 m nad
   posadzką kondygnacji od 12 % długości, krótkie — ślepe).
   Hala główna zachowuje id BDOT (`bdot:2BE4B431-BC59…`); jej ściana północna ma teraz 69,6 m od narożnika NE.

## Wyniki
WYNIKI_PLACEHOLDER

## Otwarte
OTWARTE_PLACEHOLDER
