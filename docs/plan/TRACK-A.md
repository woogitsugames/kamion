# Tor A — ciężarówka premium: plan i brief (A1)

Właściciel toru: `truck-artist`. Ocena wizualna: `visual-critic` + akceptacja właściciela. Szczegóły pipeline’u: `docs/07`, skill `blender-hero-asset`.

## Status kroków

| Krok | Opis | Stan |
|---|---|---|
| A1 | Brief, wymiary klasy, punkt oczu, lista zdjęć | **gotowe (ten plik + `art-source/truck/dims.json`)** — wartości `WORKING_VALUE` do potwierdzenia zdjęciami |
| A2 | 3 koncepcje sylwetki + 3 marki | **gotowe do wyboru** → `docs/reports/visual/truck-A2/README.md` |
| A3 | Blockout w skali wybranej koncepcji, kabina, oczy kierowcy, widoczność | czeka na wybór właściciela |
| A4 | high-poly zewnętrza | po A3 |
| A5 | Wnętrze kabiny (neutralne markowo: wspólna bryła, zmienne tylko znak na piaście i kolor wstawek) | **pierwsza pełna wersja do oceny** → §8 i `docs/reports/visual/truck-A5/README.md` |
| A5 → A6 | Poprawki wnętrza po recenzji krytyka (#4, #5, #10, #11, #12, #15) | **zrobione, do ponownej oceny** → `docs/reports/visual/truck-A6/README.md` |
| A6 | Wnętrze game-ready: LOD0/1/2, czyszczenie ukrytych ścian, 5 zestawów + atlas naklejek, mapa otoczenia kabiny, FBX + manifest | **zrobione** → §9 |
| A7–A8 | Import do Unity (prefab, shader „Kamion/CabInterior”, ekrany/lusterka, zrzuty z telefonu), naczepa | później (A7: lider / agent Unity) |

## 1. Klasa pojazdu
Nowoczesny europejski ciągnik siodłowy **4×2**, kabina nad silnikiem (cab-over), **wysoka kabina sypialna** long-haul, kierownica po lewej. Fikcyjna marka (D6), oryginalne wzornictwo — inspiracja klasą, nie modelem.

## 2. Wymiary robocze
Źródło prawdy: `art-source/truck/dims.json` (każda wartość ma status `SOURCED` / `DERIVED` / `WORKING_VALUE` i źródło). Skrypt koncepcji czyta wartości z tego pliku. Kolumna „zmierzone” = bryła z Blendera zmierzona automatycznie (`docs/reports/visual/truck-A2/koncepcja-*_wymiary.json`).

| Parametr | Wartość | Status / źródło | Zmierzone A / B / C |
|---|---|---|---|
| Szerokość maks. (prawo) | 2,55 m | SOURCED — Dyrektywa 96/53/WE zał. I 1.2 | nadwozie 2,540 / 2,540 / 2,546 ✔ |
| Wysokość maks. (prawo) | 4,00 m | SOURCED — 96/53/WE zał. I 1.3 | — |
| Długość zestawu maks. | 16,50 m | SOURCED — 96/53/WE zał. I 1.1 | — |
| Sworzeń → tył naczepy / promień przodu naczepy | 12,00 m / 2,04 m | SOURCED — 96/53/WE zał. I 1.6 | — |
| Wysokość całkowita (wysoka kabina) | 3,95 m | WORKING_VALUE | 3,95 / 3,95 / 3,95 |
| Szerokość kabiny | 2,49 m | WORKING_VALUE | — |
| Rozstaw osi | 3,70 m | WORKING_VALUE (brief: 3,6–3,8) | 3,70 |
| Zwis przedni | 1,45 m (B: 1,52) | WORKING_VALUE | 1,52 / 1,53 / 1,57 (z lusterkiem kl. VI) |
| Zwis tylny | 0,80 m (+ lampy) | WORKING_VALUE | 0,855 z lampami |
| Długość całkowita | 5,95 m (rama) | DERIVED | 6,07 / 6,08 / 6,13 (z lusterkiem przednim i lampami) |
| Opona | 315/80 R22.5 | brief | — |
| Średnica opony | 1,0755 m | DERIVED — 22,5″·25,4 + 2·0,80·315 mm | 1,0755 |
| Promień statyczny pod obciążeniem | 0,50 m | WORKING_VALUE — sprawdzić w karcie ETRTO producenta | — |
| Rozstaw kół przód / tył (środki bliźniaków) | 2,04 / 1,82 m | WORKING_VALUE | — |
| Rozstaw kół bliźniaczych | 0,34 m | WORKING_VALUE | — |
| Koło: rozstaw śrub | 10 × PCD 335 mm | WORKING_VALUE (ISO 4107 — zweryfikować tekst normy) | — |
| Wysokość siodła | 1,15 m | WORKING_VALUE (brief: 1,10–1,15; naczepy mega ~0,95 poza zakresem) | 1,15 |
| Wysunięcie siodła przed oś tylną | 0,55 m | WORKING_VALUE — finalnie z obliczeń nacisków (vehicle-physics) | — |
| Szerokość ramy (zewn.) / góra ramy | 0,85 m / 0,97 m | WORKING_VALUE / DERIVED | — |
| Dolna krawędź kabiny | 1,15 m | WORKING_VALUE | — |
| Podłoga kabiny | 1,40 m | WORKING_VALUE | — |
| Lusterka (od lusterka do lusterka) | ~3,1 m | WORKING_VALUE; lusterka nie wliczają się do 2,55 m | 3,09 / 3,06 / 3,13 |

**Do uzgodnienia:** `docs/VEHICLE_REFERENCE_DATA.md` należy do `vehicle-physics`. Wymiary geometryczne z `dims.json` powinny tam trafić (lider/vehicle-physics), żeby fizyka i grafika używały tych samych liczb.

## 3. Punkt oczu kierowcy (eye-point)
`(x, y, z) = (−0,55; +0,45; 2,50) m` w układzie blockoutu (początek = podłoże pod środkiem osi przedniej, przód = +Y, strona kierowcy = −X). Unity: Y=góra, Z=przód — mapowanie przy eksporcie (A3+).
- z: R-point fotela ~1,87 m (WORKING_VALUE) + 0,635 m (przesunięcie punktów ocznych nad R-point wg UNECE R46 — SOURCED).
- y: ~0,9 m za dolną krawędzią szyby (WORKING_VALUE).
- **Niepewność:** dokładny układ drzwi / stopni / fotela względem osi przedniej (w koncepcjach: stopnie za kołem, drzwi nad tylną połową koła) — potwierdzić na zdjęciach (lista niżej, pozycje oznaczone ★).

## 4. Zdjęcia referencyjne do zrobienia (MOP / parking TIR)
Pochmurny dzień, bez tablic i osób. Dowolna nowoczesna ciężarówka 4×2 z wysoką kabiną; logo nieistotne (i tak go nie przenosimy). Przy ujęciach wymiarowych połóż/przyłóż **kartkę A4 albo miarkę** dla skali.

**Zewnątrz**
- [ ] ★ bok lewy i prawy, prostopadle, z daleka (cała ciężarówka w kadrze, aparat na wysokości ~1,5 m)
- [ ] przód prostopadle, tył prostopadle
- [ ] ¾ z czterech rogów
- [ ] ★ okolica koła przedniego: nadkole, stopnie, dolna krawędź drzwi (z miarką przy stopniu)
- [ ] podwozie z boku: rama, zbiornik paliwa i AdBlue, skrzynka akumulatorów, tłumik/SCR, zbiorniki powietrza
- [ ] siodło z góry/z boku, przewody spiralne do naczepy, tylne błotniki i lampy
- [ ] koło z bliska: bieżnik, opis na boku opony (rozmiar), felga i nakrętki
- [ ] reflektory, kierunkowskazy, lampy obrysowe z bliska
- [ ] lusterka (główne, szerokokątne, przednie) i ich mocowania
- [ ] osłona przeciwsłoneczna, wycieraczki, uszczelki szyby, szczeliny paneli
- [ ] tylna ściana kabiny (uchwyty, panele, deflektory boczne)

**Kabina**
- [ ] ★ widok z fotela kierowcy na wprost (oczy w normalnej pozycji) + w lewo i w prawo
- [ ] ★ widok w lusterkach z fotela (oba boki)
- [ ] deska rozdzielcza z bliska — sekcjami (zegary, środek, panel pasażera)
- [ ] kierownica, dźwignie przy kolumnie, pedały
- [ ] fotel kierowcy (ze szwami), fotel pasażera, leżanka
- [ ] podsufitka, schowki, półki, nawiewy, rolety
- [ ] ★ jeśli się da: wysokość fotela / podłogi kabiny od ziemi (miarka)

Wgraj do `art-source/truck/refs/` (podfoldery `ext/`, `cab/`) — tylko jako referencje, nie tekstury (`docs/07` §1).

## 5. Marki (3 propozycje, oryginalne)
Pliki: `art-source/truck/brand/{trakt,bielik,narew}.svg` (generator `tools/blender/truck/make_logos.py`, litery z kresek geometrycznych, bez fontów).

| Marka | Znaczenie | Znak | Ryzyka do sprawdzenia |
|---|---|---|---|
| **TRAKT** | staropolskie „droga, gościniec” | droga w perspektywie tworzy nóżkę litery T | słowo pospolite, używane w nazwach firm (np. serwis Trakt.tv) — sprawdzić EUIPO/UPRP w klasie 12 i 28/41 |
| **BIELIK** | orzeł bielik, ptak bagien Podlasia | jedno zamaszyste skrzydło z trzech piór (celowo nie podwójny szewron) | „Bielik” to też polska nazwa samolotu M-346 w Siłach Powietrznych — skojarzenie wojskowe |
| **NAREW** | rzeka płynąca obok Białegostoku | pierścień przecięty meandrem rzeki | „Narew” to też nazwa polskiego programu obrony przeciwlotniczej — skojarzenie wojskowe |

Wszystkie trzy wymagają przed decyzją wyszukania w bazach znaków towarowych (EUIPO eSearch, UPRP) — **nie zrobione** (brak zgody na zewnętrzne zapytania w tym zadaniu). Żadna nazwa ani znak nie nawiązuje do Volvo, Scania, MAN, DAF, Mercedes-Benz, Iveco, Renault, Jelcz, Star.

## 6. Odtworzenie (wszystko skryptami)
```
blender -b --factory-startup --python tools/blender/truck/concepts.py -- --concept A --out docs/reports/visual/truck-A2
blender -b --factory-startup --python tools/blender/truck/concepts.py -- --concept B --out docs/reports/visual/truck-A2
blender -b --factory-startup --python tools/blender/truck/concepts.py -- --concept C --out docs/reports/visual/truck-A2
uv run --no-project --with pillow python tools/blender/truck/contact_sheet.py docs/reports/visual/truck-A2
uv run --no-project --with pillow python tools/blender/truck/make_logos.py --preview docs/reports/visual/truck-A2/logotypy.png
```
Opcja `--blend <ścieżka>` zapisuje scenę do podglądu (np. do `artifacts/`, poza gitem). Czas: ~25 s na koncepcję (Cycles CPU, 96 próbek, 1600×900).

## 7. Następny krok (A3, po wyborze)
Wybrana koncepcja (+ ewentualne mieszanki: np. kabina z B, front z C) → blockout w skali z wnętrzem kabiny (fotel, kierownica, deska jako bryły), eye-point jako empty, test widoczności przez szybę i w lusterkach, korekta wymiarów po zdjęciach właściciela, rendery kontrolne + `visual-critic`.

## 8. A5 — wnętrze kabiny (właściciel: `truck-artist`)
Raport z renderami, tabelą ergonomii, budżetami i pytaniami: `docs/reports/visual/truck-A5/README.md`.

**Zasada neutralności marki:** jedna bryła wnętrza dla A/B/C. Parametry zależne od marki: `--badge none|trakt|bielik|narew` (znak na piaście, z SVG w `art-source/truck/brand/`), `--trim grafit|piasek|koniak|lupek` (wstawki deski, drzwi, środki foteli). Pochylenie szyby `--rake` (A/C ≈ 3–5°, B ≈ 19°) przesuwa szybę, słupki i schowek nad szybą; dla B słupek A i szyba boczna wymagają dopracowania w A3.

**Ergonomia (skrót, pełna tabela w raporcie):** oczy (−0,55; 0,45; 2,50) z `dims.json`; punkt H 0,635 m niżej (UNECE R46, SOURCED), 0,465 m nad płaską podłogą; kierownica Ø 470 mm, 38° od poziomu, środek (−0,55; 0,875; 2,12); wysokość stojąca 2,22 m; ekran zegarów 12,3″ pod kapturem ustawionym nad linią wzroku oko → górna krawędź ekranu; konsola środkowa 22° do kierowcy; bez pedału sprzęgła (AMT); hamulec postojowy jako dźwignia zaworu pneumatycznego na desce. Wszystko poza R46 i wymiarami z przepisów = `WORKING_VALUE` do potwierdzenia zdjęciem „z fotela kierowcy” (§4 ★).

**Budżety (zmierzone / plan):** 83 490 trójkątów łącznie ze skorupą, szybami i lusterkami (cel High 60–90 tys.); LOD Medium ~40 tys., Low ~20 tys. (plan w raporcie). Tekstury: High ≈ 12,5 MB, Medium ≈ 2,7 MB, Low ≈ 0,8 MB (ASTC + mipmapy). Jeden atlas AO 2048 na całą kabinę (warstwa UV `Bake`), tekstury kafelkowane w metrach (warstwa `UVMap`).

**Odtworzenie:**
```
uv run --no-project --with pillow --with numpy python tools/blender/truck/interior/make_textures.py
blender -b --factory-startup --python tools/blender/truck/interior/build_interior.py -- --out docs/reports/visual/truck-A5 --samples 512 --stats docs/reports/visual/truck-A5/stats.json
python tools/blender/truck/interior/variants.py --out docs/reports/visual/truck-A5
blender -b --factory-startup --python tools/blender/truck/interior/bake_ao.py
```
Duże mapy kafelkowane i atlas AO są generowane (pomijane w git przez `art-source/truck/interior/.gitignore`); w repo są tylko skrypty i małe grafiki (ekrany, symbole, maski).

**Następne kroki wnętrza:** zdjęcia właściciela → korekta wartości WORKING_VALUE; wybór koloru wstawek i stylu zegarów; A6: usunięcie ukrytych ścian, scalenie 49 materiałów do ~6 atlasów, LOD1/LOD2, wypalenie szwów/drobnych kształtów do normalnych na Medium/Low; A7: import do Unity, ekrany sterowane z fizyki, lusterka jako render texture, zrzuty z A16.

## 9. A6 — wnętrze gotowe do importu (właściciel: `truck-artist`)
Raport, rendery Cycles i URP-like, porównania przed/po: `docs/reports/visual/truck-A6/README.md`.

- **Widoczność zegarów:** okrągłe zegary usunięte, ekran 12,3″ (ciśnienie I/II, paliwo, AdBlue, jedna prędkość) w „wannie” deski. Test `tools/blender/truck/interior/sightline_test.py` (exit 1 przy zasłonięciu) = PASS dla LOD0, LOD2 i szyby 19° (B).
- **Eksport:** `art-source/truck/interior/export/SM_CabInterior_LOD{0,1,2}.fbx` (LOD0 poza gitem, > 5 MB, generowany) + `cab_interior_manifest.json` (obiekty, trójkąty, materiały, tekstury per profil, kontrakt shadera, punkty, osie animacji, osie Unity). Trójkąty: 78 381 / 37 767 / 21 574.
- **Układ:** początek = `CAB_MOUNT_REF` = graybox `CabPivot` (Unity pojazdu (0; 1,15; 3,925)); Blender (x, y, z) → Unity (x, z, y); FBX `axis_forward=Z, axis_up=Y`, bake space transform. Walidacja: `check_export.py` (PASS); kontrola po stronie Unity — położenie `EYE_POINT` = (−0,55; 1,35; 0,225) lokalnie.
- **Oświetlenie:** mapa `T_Cab_AO_LODn` = światło otoczenia kabiny (białe niebo + odbicia, Cycles 4096 spp, odszumione w obrębie wysp); w URP mnoży światło pośrednie (rozproszone i odbicia). Przy niskim słońcu URP-like pokazuje bardzo ciemne wnętrze — decyzja o „fill”/sondzie kabiny należy do `rendering-perf`.
- **Odtworzenie:** komendy w raporcie A6 (§ „Jak odtworzyć”).
