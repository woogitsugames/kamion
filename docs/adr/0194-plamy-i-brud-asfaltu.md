# 0194 — Plamy i brud na asfalcie sterowane ruchem (olej, łaty, koleiny na płytach, brud placów)

Status: kandydat (gałąź `stains-0194`), nie scalone. Data: 2026-11-13. Dotyczy: ADR 0019 (decale), 0060 (_GRIME), 0110 (UV1 płyt),
0118 (asphalt_wear / szew łat), 0062/0191 (pule latarni — konflikt opisany niżej).

## Kontekst (REVIEW-2026-11-13-s19-0179, P2)
1. P11-129: plamy na asfalcie to **jasne rozmyte „splaty”** (pomiar przed: plama 91 vs asfalt 66–70 kodu sRGB luma, +34 %).
   Przyczyna (zmierzona na atlasie `oil_stain_alpha`): albedo plamy 0,018 lin. (ciemne, OK), ale Mask.A w rdzeniach 0,43–0,52
   przy płaskiej normalnej decala → przy kącie ślizgowym kierowcy odbija się jasne niebo zachmurzone; asfalt obok ma 0,09.
2. Dojlidy route-after kadr 2 (= kamera `route_s1066`, płyta skrzyżowania Kuronia/Mickiewicza bez linii): gęste ciemne smugi na
   całej szerokości. Przyczyna: `_patch_uv1` (ADR 0110) przenosi współrzędną pasa ramion na płytę, więc koleiny (−42 % albedo w osi
   koleiny przy `wheel_darkening` 0,45) i pas kapania biegną równolegle przez całą płytę, a na płycie nie ma linii, które je porządkują.
3. „Ten sam brud wszędzie”: kałuże/brud `_GRIME` (ADR 0060) mają jeden próg makro na całym placu (chase C), łaty drogowe mają tę
   samą gęstość na każdej klasie drogi i losowe położenie w poprzek jezdni.

## Decyzja
Nowy plik `game/Assets/_Project/Rendering/Shaders/KamionRoadStains.hlsl` (wszystko opt-in, wektor 0 = dokładnie stary wynik):
- **Olej** (`KamionOilStain`, `_OilLook`, dane `decal_oil.oil_look`): gładkość 0,10 (stara plama) … 0,22 (świeży film) zamiast
  ~0,5; gamma pokrycia 0,7 (gęstszy rdzeń, ostrzejszy brzeg). Kratki/włazy Fab (ten sam `_DECAL_ALPHA`) bez zmian.
- **Płyty skrzyżowań** (`KamionPlateWear`): `roads.meshing._patch_uv1` dodaje +20 m (`PLATE_EDGE_FLAG`) do UV1.y wierzchołków
  płyty z danymi pasa; shader zdejmuje flagę i zostawia 35 % kontrastu kolein i 40 % pasa kapania (ruch skręca i się przeplata).
- **Brud placów** (`KamionYardGrimeBias`, `_GrimeTraffic`, dane `grime_traffic` na yard_*): UV1 nawierzchni utwardzonych
  (odl. od krawędzi, odl. od ściany) przesuwa próg kałuż: przy ścianach/dokach (< 18 m) i krawędziach (< 2,5 m) −0,04 (wilgotniej),
  na otwartym środku +0,07 (czyściej). Zero dodatkowych próbek tekstur.
- **Łaty** (`roads.decals`): oczekiwana liczba × klasa drogi (A/S 0,35, GP 0,55, G 0,85, Z 1,0, L 1,2, D 1,3) × strefa wlotu
  (30 m od końca łańcucha przy skrzyżowaniu ×1,8, środek odcinka ×0,75); łaty „w koleinie” i 60 % małych łat w osi koleiny pasa
  (±0,24 szer. pasa, 65 % zewnętrzna). Szew 25 mm i inny odcień/zestaw `asphalt_patch` — bez zmian (ADR 0118), teraz widać je tam,
  gdzie realnie powstają. Wszystkie liczby WORKING_VALUE (porównanie: P11-076 Dywizjonu 303 — prawie bez łat; P11-129 — kilka łat).

### Konflikt z lamppool-0191
0191 zmienia w `WorldPBR.shader` tylko linię oświetlenia (`KamionLampPools(...)` → `KamionLampPoolsLit(...)`, ~l. 986) oraz
`KamionLampPools.hlsl`. 0194 dotyka: include (l. ~108), CBUFFER (`_OilLook, _GrimeTraffic`), Properties (`_GrimeTraffic`, `_OilLook`),
blok `_ROADWEAR` (3 linie), blok `_GRIME` (1 linia), blok `_DECAL_ALPHA` (1 linia). Brak wspólnych linii; przy scaleniu obu
sprawdzić tylko kolejność include w HLSLINCLUDE.

## Budżet
Draws/tris: bez zmian (ten sam zestaw materiałów; łaty: liczba zmieniona, patrz walidacja). ALU: olej +~6, płyta +~4, plac +~10
(tylko materiały z danymi); 0 nowych fetchy, 0 nowych wariantów (bez nowych keywordów).

## Walidacja
TODO (wyniki renderów i testów)

## Otwarte
- Koleiny na nowych drogach (Dywizjonu 303, P11-076: ledwo widoczne) są w renderze wyraźne — `asphalt_wear.wheel_darkening` 0,45 jest
  wspólne dla `road_asphalt`; kandydat: wiek nawierzchni z danych (oddanie drogi) → osobny materiał, decyzja lidera.
- Pomiar na telefonie przy najbliższym APK (koszt ALU szacowany, nie zmierzony).
- Lider: regeneracja `generated/*` regionów C i Dojlidy po scaleniu (gałąź nie commituje generated).
