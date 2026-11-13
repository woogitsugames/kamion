# 0183 — Słupki biało-czerwone z łańcuchem (prototyp mebla ulicznego + override `chain_bollards`)

Status: kandydat (gałąź `bollards-0183`), nie scalone. Data: 2026-11-13.

## Problem
Agent 0179 (Dojlidy) znalazł na zdjęciu właściciela P11-063 (ul. Mickiewicza przy Kuronia) rząd biało-czerwonych
słupków blokujących połączonych dwoma łańcuchami. Biblioteka mebli (`street_props.glb`) ma tylko szary `bollard`
Ø0,12 m i żółte U-12a / U-5a; OSM i BDOT10k nie opisują takich rzędów (`barrier=bollard` najbliżej 87 m — audyt
Mistral p9, M50-056), więc reguła generatora nie ma z czego ich postawić.

## Decyzja
1. **Nowy moduł** `tools/worldgen/streetscape/chain_bollards.py` (bez zmian w `plot_kit.py` i `furniture.py`).
   Wpięcia jednowierszowe: `props.build_all` (prototypy), `export.textures` (atlas), `stage.py` (po `lamp_rows`,
   czyli po przejściach czyszczących jezdnię — rząd jest autorski), `materials.py` (blok addytywny na końcu).
2. **Dwa prototypy, jeden materiał** `chain_bollard` (jeden atlas alfa 256 × 512 px, kolory w teksturze):
   - `bollard_rw_chain` — słupek w początku układu + oba łańcuchy jednego przęsła wzdłuż lokalnego +x (słupek
     końcowy przęsła to następna instancja);
   - `bollard_rw` — sam słupek (zamyka rząd; rzędy `chain: false`).
   LOD0: słupek 10-kątny z kopułką, 4 ucha, każdy łańcuch jako dwie skrzyżowane karty alfa z teksturą ogniw
   (ogniwa na płask / bokiem na przemian, druga karta przesunięta o jedno ogniwo). LOD1: słupek 5-kątny, każdy
   łańcuch = jedna nieprzezroczysta taśma 12 mm (bez alfa-testu ogniw, żeby łańcuch nie znikał w mipmapach).
   Kolizja: jedno niskie pudło na przęsło.
   **Układ atlasu (r2).** Render r1 pokazał czerwone ogniwa blado-różowe w Unity (w Blenderze czerwone). Przyczyna:
   import świata to ASTC 6×6 + trilinear (`InstanceImporter.ImportTexture`), a granica czerwone|białe ogniwa leżała na
   u = 160 px — w środku bloku 6×6 (160/6 niecałkowite) i tuż przy krawędzi karty, więc koder bloków i próbki
   bilinearne mipów ≥ 2 mieszały biel z czerwienią. r2: każda granica kolorów na wielokrotności 24 px (całe bloki
   4/6/8/12), kolumna ogniw 32 px ma po bokach 8 px przezroczystego marginesu w kolorze własnej farby (1 teksel mipa 3),
   czerwony i biały slot stykają się na u = 192 px (krawędź teksela każdego mipa do 64 px), a taśmy LOD1 mają stały
   UV w litej łacie 24 × 48 px (zero śladu filtra przez granicę). Układ (px): słupek 0–120, stal 120–144 (wiersze 0–48
   łata czerwona, 48–96 biała), ogniwa czerwone 144–192, białe 192–240, 240–256 rezerwa (biel, α 0). Zużycie farby
   na koronach ogniw 0,6 → 0,4 (na zdjęciu łańcuch czyta się jako ciemnoczerwony). Test
   `test_atlas_r2_no_red_white_bleed` pilnuje wyrównania i koloru kolumny czerwonej w mipach 0–4. Polityka LOD/cull = domyślna małych mebli (`InstanceImporter.Policy`:
   30 / 120 m × lodBias) — bez zmian w C#.
3. **Wymiary** (stałe w module, każda z opisem źródła):
   | wielkość | wartość | źródło |
   |---|---|---|
   | wysokość słupka | 0,80 m | U-12c 0,6–0,8 m, biało-czerwone: `research/mistral/p9-furniture-3/manifest.csv` wiersz M50-043 (cytuje Dz.U. 2019 poz. 2311, zał. 4, s. 847; aktu nie czytałem ponownie). P11-063 pasuje do górnej granicy (słupek 75 px przy f ≈ 1230 px → 13,1 m; krawężnik na ortofoto 13,5–15 m od pozycji zdjęcia). 0,90 m pasuje równie dobrze — WORKING_VALUE |
   | średnica | Ø60,3 mm | WORKING_VALUE: rura słupków U-12a ze standardu ZDM (G5-010); na zdjęciu 5–7 % wysokości |
   | przęsło | 1,60 m | WORKING_VALUE = 2,0 × wysokość; P11-063: 3 przęsła = 5,9 wysokości słupka (niezależnie od ogniskowej ±10 %) |
   | pasy od ziemi | biały 22 %, czerwony 21 %, biały 25 %, czerwony 21 %, biały 11 % | P11-063 (kadr 4×: 60/60/70/60/30 px z 280) |
   | ucha łańcuchów | 0,94 i 0,46 wysokości | P11-063, WORKING_VALUE |
   | zwis łańcucha | 0,18 i 0,16 wysokości (krzywa łańcuchowa) | P11-063 (50 i 45 px z 280), WORKING_VALUE |
   | łańcuch (r3) | tworzywo, drut 8 mm, podziałka 42 mm, szer. 30 mm; taśma LOD1 22 mm | szerokość pozorna z P11-063: 2–3 px przy ~13 m, f ≈ 1230 px (ASSUMED) → 0,021–0,032 m; materiał i ogniwa UNVERIFIED (r1/r2: stal 6 mm, 24 mm — w r2 łańcuchy znikały od ~10 m, na zdjęciu czytają się jak liny) |
   | malowanie łańcucha | odcinki czerwone i białe ~pół przęsła, niezgrane ze słupkami | P11-063, jeden stały wzór na przęsło — WORKING_VALUE |
4. **Override** `kind: chain_bollards` w `Data/Regions/<id>/overrides.yaml` (przeżywa każdą regenerację):
   `line_epsg2180: [[x, y], ...]` albo `lines: [{line_epsg2180: [...]}, ...]`, opcjonalnie `chain: false`.
   Rząd idzie od pierwszego punktu, słupki dokładnie co 1,60 m (cięciwa) na zadanej linii, także po łuku; ostatni
   słupek może wyjść poza koniec linii o < 0,80 m (siatka przęsła ma jedną długość, instancje skalują tylko oś
   pionową). Przerwa (przejście) = dwa rzędy. Błędny wpis trafia do `stale` w raporcie, nie znika po cichu.
   Raport `streetscape_qa.json → furniture.chain_bollards`: słupki, przęsła, długość, `end_shift_m`, `max_step_m`.
5. **Osadzanie**: prefiks `bollard` → `Placer.seat` jak każdy słupek. Przęsło jest poziome (instancja ma tylko
   obrót wokół pionu), więc na spadku łańcuch trafia w następny słupek o `max_step_m` wyżej/niżej niż ucho —
   raportowane; rzędy stoją na chodnikach (spadki ≤ kilka %), przy > 0,10 m rząd trzeba podzielić.

## Odrzucone
- Jeden prototyp „przęsło z dwoma słupkami” lub odwrócone przęsło jako zakończenie (0 dodatkowych draw): daje
  pokrywającą się geometrię alfa (migotanie) i zdublowane słupki o różnych wysokościach na spadku.
- Łańcuch wypalony w siatce chunku (`Lin`, jak ogrodzenia): brak LOD i instancjonowania, nowy materiał w każdym
  chunku z rzędem.
- Ogniwa jako geometria: ~70 ogniw × 2 łańcuchy na przęsło — poza budżetem dla mebla widzianego z kabiny.

## Blok dla Dojlid (do wklejenia przez 0179 / lidera; nie jest w plikach regionu na tej gałęzi)
Plik gotowy: `artifacts/bollards-0183/overrides.dojlidy.chain_bollards.yaml`.
```yaml
  - id: mickiewicza-kuronia-chain-posts-p11-063
    kind: chain_bollards
    line_epsg2180: [[780011.30, 590461.30], [780016.31, 590451.28]]
    chain: true
    sources: ["research/_incoming/mistral-p11-dojlidy-photos-v2/files/P11-063.jpg", "GUGiK orthophoto 2024 0.25 m"]
    confidence: low
    verify: start / end post on site (+-2 m along the kerb); the further row visible behind (smaller posts) is not placed
```
Podstawa: zdjęcie zrobione z wysepki przystankowej ul. Mickiewicza w stronę wschodnią; 8 słupków stoi tuż za
wschodnim krawężnikiem jezdni w kierunku NW (osm way 691820489 / 258564444), do przejścia przy narożniku Kuronia.
Linia krawężnika z ortofoto GUGiK 2024 (0,25 m): lokalnie E = −33,5 − 0,5 (N − 385), rząd 0,5 m za nią. Początek:
21° w lewo od białej szafki przy (−15,5; 371,0) widzianej z (−46,5; 381,8) — szafka stoi na zdjęciu za słupkami 5–6.
Pozycja kamery `photo_P11-063` (ADR 0174) ma błąd kilku metrów (szafka wypada 13° zamiast 27° od osi kadru), stąd
`confidence: low`. Drugi, dalszy rząd widoczny na zdjęciu (mniejsze słupki) — nieumieszczony, UNVERIFIED.

## Budżet
WYNIKI_BUDZET

## Dowody
WYNIKI_DOWODY

## Otwarte
- Wysokość 0,80 vs 0,90 m i długość przęsła — do pomiaru na miejscu (właściciel) albo z drugiego zdjęcia z obiektem
  o znanym wymiarze.
- Łańcuch: typ i wymiary ogniw UNVERIFIED.
- Kolizja przęsła jest sztywna (ciężarówka nie zerwie łańcucha) — jak wszystkie meble; fizyka zrywania poza zakresem.
- Rozstawienie w Dojlidach i korekta pozy `photo_P11-063` — 0179 / lider.
