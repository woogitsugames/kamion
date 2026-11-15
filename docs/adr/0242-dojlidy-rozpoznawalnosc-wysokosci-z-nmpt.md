# ADR 0242 — Dojlidy: rozpoznawalność — wysokości brył z NMPT, okładzina kasetowa K3, otwory hal na gruncie

Status: Proposed (agent world-builder, s21, chmura D runda 2, gałąź `dojlidy-0242`), 2026-11-15. Do scalenia przez lidera.
Poprzednicy: ADR 0179, 0185, 0196, 0202. Podstawa: `docs/reports/REVIEW-2026-11-14-s20-0185.md`, `…-0196.md`, `…-0183.md`,
`docs/owner/BACKLOG-S21.md` (B-040…B-061). Zakres: tylko region `bialystok-dojlidy` (dane + reguły opt-in).
Nie ruszane: las Krywlany (0187), brama szpitala (0189), DDR (0188), chodniki/krawężniki (0237), typologia ogólna (0238),
płoty i `mipMapsPreserveCoverage` (F6).

## Kontekst
Recenzje 0185 i 0196 zostawiły otwarte P1, których nie dało się rozstrzygnąć ze zdjęć: wysokość hali północnej zakładu przy
Kuronia (16,9 m ze zdjęcia przeciw 18,92 m z LoD1; 14 pasów paneli w renderze przeciw 16 na zdjęciu), hierarchia wysokości
zakładu Kuronia 2 (hala nad frontem), okładzina K3 w złej orientacji, drzwi hali 1,2–1,7 m nad gruntem, zacieki na nowej hali.
W chmurze nie ma `Data/raw` ani zdjęć, jest za to publiczny WCS GUGiK z numerycznym modelem pokrycia terenu.

## Decyzja
1. **Wysokości z NMPT 0,5 m** (GUGiK, WCS `PZGIK/NMPT/GRID1/WCS/DigitalSurfaceModel`, pokrycie `DSM_PL-EVRF2007-NH`, pobrane
   2026-11-15; data nalotu komórek nie jest podana przez usługę — UNVERIFIED; dokładność przyjęta ±0,2 m). Pomiar odtwarza
   `tools/worldgen/qa/dsm_roof_levels.py` (siatki nie ma w gicie). Poziom dachu = `ground_z_evrf2007` + `height_m`
   (reguła `lod1_base_datum` z 0185).

   | Bryła | Było (źródło) | NMPT (EVRF2007) | Jest |
   |---|---|---|---|
   | hala północna zakładu (BDOT 2BE4B431-BC59) | 16,9 m (zdjęcie P11-094, poza z EXIF) | dach 171,04–171,16 przy ścianie N; baza LoD1 152,06 → 19,0 m | LoD1 18,92 m (nadpisanie wycofane) |
   | jej skrzydło zachodnie | 12,2 m (proporcja ze zdjęcia) | 165,25 (p5–p95 165,05–165,66) | 13,2 m nad 152,06 |
   | blok biurowy Kuronia 3 | 14,0 m nad medianą terenu | dach 169,46; teren przy ścianie S 153,9–154,1 | 15,4 m nad 154,0 |
   | hala Kuronia 2 (BDOT 941cfc23) | LoD1 12,72 m (168,89) | dach dwuspadowy: okap od Kuronia 168,07, od SE 168,57, kalenica 170,1 | 11,9 m nad 156,17 (okap od ulicy) |
   | front Kuronia 2: blok narożny i drugi blok | 9,0 m nad medianą | dach 167,45–167,5; próbka attyki 168,04, maks. 168,75 | 9,9 m nad 158,1 (dach + 0,5 m attyki, WORKING_VALUE) |
   | front Kuronia 2: wnęka i skrzydło biurowe | 7,2 m | 167,33–167,52 (cały front na jednym poziomie) | 9,35 m nad 158,1 |
   | przybudówka wzdłuż Kuronia | 7,2 m, 2 kondygnacje | 162,35–162,56 | 5,35 m nad 157,1, 1 kondygnacja |

   Skutki: (a) hala północna ma znów 18,92 m — 16 pasów × 1,15 m + cokół 0,5 m = 18,9 m, czyli moduł `hall_wall_smooth`
   i liczba pasów ze zdjęcia zgadzają się (druga hipoteza recenzji 0185 P1-2); (b) ściana hali Kuronia 2 kończy się 0,07 m
   nad blokami frontu zamiast ok. 2,4 m (P1 recenzji 0196); (c) przybudówka od Kuronia jest najniższa.
   Rzędy okien frontu Kuronia 2 przeskalowane proporcjonalnie (×9,35/7,2) — proporcje ze zdjęcia, UNVERIFIED.
2. **K3 — okładzina kasetowa** `cladding_cassette_grey`: istniejący zestaw `sandwich_smooth` (pasy 1,15 m), `panel_m`
   3,5 × 1,15 m (WORKING_VALUE; recenzja: fugi poziome „ok. 1 m”, styki „ok. 3–4 m”), kolor jak `cladding_vertical_grey`.
   Bez nowej tekstury. Klucz `storeys_fixed` (opt-in na bryle): trzy kondygnacje po 4,72 m mimo limitu 4,6 m reguły;
   parapety 0,19 / 0,50 / 0,81 wysokości ściany jak w 0185.
3. **Zacieki per materiał**: klucz manifestu `runoff_strength` (mnożnik `_RunoffStrength` w `WorldPbrMaterials`);
   `hall_wall_smooth` 0,25, `cladding_cassette_grey` 0,5 (WORKING_VALUE z recenzji 0185 P1-4; hala na zdjęciu jest czysta).
4. **Otwory hal na gruncie** — reguła `building_rules: hall_openings_at_ground` (opt-in na region): próg drzwi osobowych
   = teren pod drzwiami + 0,15 m, bram i drzwi wjazdowych + 0,02 m (najwyższy z trzech punktów, więc nigdy pod ziemią),
   zamiast mediany terenu całego obrysu. Schodków nie dodaję (różnica po zmianie ≤ 0,16 m).
5. **Bramy hali północnej** 5,9 × 6,6 m (było 4,5 × 5,0): 85 px bramy / 245 px ściany (pomiar z 0196) × 18,9 m; recenzja
   czyta 0,40 → 7,5 m. UNVERIFIED do zdjęcia z miarą.
6. **Front Kuronia 2**: rama bloków w `plaster_accent_grey` (0,20) zamiast `hall_flashing` (0,045) — na zdjęciu blok jest
   ok. 1,8× jaśniejszy od hali (recenzja 0196, liniowo), teraz 2,5× (WORKING_VALUE; materiał już rysowany przez te bryły);
   ciemny parter na wszystkich krawędziach (`min_len_m: 0`) — znikają jasne pionowe pasy.

## Region C i pozostałe regiony
Nowe klucze są opt-in; test `test_new_rules_are_opt_in_and_no_other_region_uses_them`. Porównanie różnicowe generatora
budynków (kod `origin/main` przeciw gałęzi, syntetyczny pochyły teren, skrót SHA-256 wszystkich siatek): region C 644 budynki,
1 018 710 trójkątów — skrót identyczny; `knyszyn` 1903 budynki — identyczny. Słownik `materials` manifestu każdego regionu
dostaje przy następnej regeneracji trzy nieużywane wpisy i klucz `runoff_strength` (jak przy 0185); żaden chunk C ich nie rysuje.

## Budżet (szacunek, bez Unity)
Ten sam przebieg różnicowy dla Dojlid: warstwa LOD0 457 719 → 456 981 trójkątów (−738), LOD1 54 233 → 54 089 (−144), liczba
materiałów warstw 48 / 56 bez zmian → draws ±0 w każdej kamerze; kamery Dojlid z recenzji (Low: P11-001 341 draws / 471 tys.,
kuronia2_front 207 / 348 tys., P11-094 199 / 293 tys., P11-063 279 / 339 tys.) nie rosną. Zestaw `cladding_vertical` przestaje
być używany w regionie (High 2,49 MB ASTC wg `materials_spec.json`) — czy importer go wtedy pomija, UNVERIFIED.

## Tabela punktów (stan na `origin/main` 25924f60b)
| Punkt | Źródło | Status przed | Co zrobione |
|---|---|---|---|
| K3 okładzina w złej orientacji | R 0185 P1-1, B-043 | otwarte | zrobione (pkt 2); szczyt nadal ślepy — zdjęcie właściciela |
| Hala: 14 pasów vs 16, wysokość 16,9 vs LoD1 | R 0185 P1-2, B-044 | otwarte | rozstrzygnięte pomiarem NMPT (pkt 1) |
| Zacieki pod attyką | R 0185 P1-4, B-045 | rytm usunięty w 0196 (`runoff_shuffle`) | siła ×0,25 dla tej hali (pkt 3) |
| Drzwi hali 1,2–1,7 m nad gruntem | R 0185 P1-5, B-046 | otwarte | zrobione (pkt 4), także bramy |
| Kuronia 2: hala nad frontem | R 0196 P1, B-056 | otwarte | zrobione z NMPT (pkt 1) |
| Kuronia 2: bloki ciemniejsze od hali, jasne pasy w parterze | R 0196 P2 | otwarte | zrobione (pkt 6) |
| Bramy za małe | R 0196 P2, B-057 | otwarte | powiększone, UNVERIFIED (pkt 5); obróbka/podjazd otwarte |
| Kuronia 2: okna płaskie | R 0196 P1, B-056 | otwarte | NIE — mechanizm okien `frontage` to typologia ogólna (F5, 0238); odnotowane |
| Kuronia 2: poza kamery `kuronia2_front`, czerwona linia i daszek | R 0196 P2 | otwarte | NIE — bez zdjęcia P11-005 w chmurze; czerwona linia = +1 materiał w kadrze |
| Pas z płotu nieczytelny jako lotnisko | R 0196 P1, B-055 | oznakowanie, „27 L”, zielony płot w 0202 | otwarte: w kaflu i w `osm_context.json` brak rękawa/hangarów (hangar poza kaflem, B-041); wymaga rozszerzenia kafla na E |
| Drzewa narożnika 063 | 0186, B-049 | scalone (recenzja Argona: SCAL) | sprawdzone z NMPT: główne drzewo 7,1–8,3 m nad gruntem przeciw 10,5 m w danych (zdjęcie 10,6 m); model pokrycia zaniża korony liściaste — bez zmiany, UNVERIFIED |
| Czarna obróbka attyki, cokół 0,8–1 m, białe słupki płotu | R 0185 P2 | otwarte | NIE: obróbka = zmiana wspólnego `hall_flashing`; cokół — 16 × 1,15 + 0,5 m potwierdza ok. 0,5 m z 0185; płot = F6 |
| Płot panelowy (mora/zanik), płot i brama K3 | R 0185 P1-3, B-047, B-082 | otwarte | wyłączone (F6) |
| Słupki U-12b: widoczność na Low/A16 | R 0183, B-058/059 | 0202 scalone | tylko telefon — lider |
| Las, brama szpitala, DDR, plamy, tarcze | B-048, B-050, B-052–054, B-060 | scalone (Argon) | wyłączone z zakresu |
| Chodniki, krawężniki, latarnie, wiaty | B-042 | otwarte | wyłączone (F4/F5) |

## Otwarte
- Część południowa obrysu hali północnej ma dach ok. 165 m (NMPT), a w grze 171 m — niewidoczna z Kuronia; do `building_part`.
- Hala Kuronia 2 jako graniastosłup do okapu: szczyt dwuspadowy (kalenica +2 m) nie jest rysowany.
- Zrzuty A16 `kuronia2_front`, `photo_P11-094` (B-109) i ocena `visual-critic` po regeneracji — lider.
- Atrybucja NMPT w `docs/LICENSES.md` (dodana); status prawny jak pozostałe zbiory GUGiK (`LEGAL_REVIEW_REQUIRED`).
