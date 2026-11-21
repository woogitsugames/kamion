# ADR 0318 — Woda: Narew pod mostem w Tykocinie i korytarz DW671
Status: Proposed (agent water-tykocin-s24, gałąź `water-tykocin-s24`), 2026-11-21. Do scalenia przez lidera.
Powiązane: ADR 0210 (etap wody, opt-in per region), ADR 0213 (szew poziomu, kolor tafli, pas trzciny), ADR 0231
(kafle DW671 → Tykocin), ADR 0212 (dw671-tykocin-01), ADR 0204 (Knyszyn), vqa-wave5 WORST2 „tykocin narew bridge no river”.

## Kontekst
Przegląd vqa-wave5 (P1 przed buildem #3): most DW671 na ul. Puchalskiego (OSM way 220328689, 194,4 m) stoi nad łąką.
Etap wody ADR 0210 jest opt-in (`Region.water`) i był włączony tylko w `dk65-02/03`. W kaflu `tykocin` dane są:
BDOT10k OT_PTWP_A 27 obiektów / 159 004 m², OT_SWRS_L 9,8 km (Narew `SZEROKOSC` 48 m), OSM 13 obszarów
(Narew `water=river` 78 445 m², starorzecza `water=oxbow` 32 096 / 4 907 / 3 271 m²), Nereśl, Zajkowska Struga.

## Decyzja
1. `water=True` dla `tykocin` oraz kafli korytarza, w których BDOT/OSM ma istotną wodę (inwentaryzacja
   `water.extract` bez zapisu, 13 kafli):
   | kafel | BDOT PTWP m² | osie (BDOT / OSM) | uwagi |
   |---|---|---|---|
   | tykocin | 159 004 | 9,8 km / Narew 4,1 km, Nereśl, Zajkowska Struga | most DW671 |
   | dw671-tykocin-09 | 24 395 | 3,2 km / Nereśl 2,8 km | szew z tykocin (N) |
   | dw671-tykocin-08 | 32 866 | 5,2 km / kanały 4,6 km | Stara Narew |
   | dw671-tykocin-02 | 8 976 | 2,1 km / Jaskrzanka | szew z -01 |
   | dw671-tykocin-01 | 831 188 | 1,7 km / Jaskrzanka | stawy rybne SW Knyszyna |
   | knyszyn | 23 108 | 2,5 km / Jaskrzanka | Zalew Miejski |
   | knyszyn-s | 87 491 | 1,1 km / Jaskrzanka | stawy |
   Pominięte (tylko drobne stawy ≤ 9 000 m², bez cieków): dw671-tykocin-03/-04/-05/-06/-07, knyszyn-w.
2. Dla każdego włączonego kafla: `build_region` (→ `generated/water_sources.json`, blok `water` w `region.yaml`),
   `streetscape/water_banks.py` (→ `water_banks.json`, pas szuwarów/krzewów z ortofoto 2024 jak ADR 0213),
   `build_world`. Kod etapu bez zmian. `buildings.geojson` / `rail_sources.json` z `build_region` zostawione jak
   na main (build_region dawał dryf niezwiązany z wodą — do osobnego sprawdzenia przez lidera).
3. Kamery: `top_water_bridge`, `water_bank_bridge_se`, `water_oblique_bridge`, `water_boat_under_bridge`
   (`control_cameras_place.authored.json` kafla tykocin).

## Wyniki (zmierzone)
- tykocin: 36 ciał wody, 176 724 węzłów, tafla 182 627 m² / 32 175 tris; dno do 5,44 m pod NMT (krawędzie zarysów na
  skarpach); 48 303 węzłów brzegu obniżonych, 1 061 podniesionych (próg); 0 węzłów wody przy drogach; pas trzciny
  9,1 z 13,0 km brzegu (70 %), 1 055 koron; ściany terenu 0; spójność dróg = main (6 × lane_blind_end, 1 na trasie).
- Most (GLB chunk_5_3, wierzchołki): tafla pod mostem 104,46 m n.p.m. (NMT nad wodą 104,56), spód przęsła
  107,5–107,6 m, jezdnia 108,6–109,0 m → **prześwit pod przęsłem ≈ 3,0–3,1 m**, jezdnia 4,1–4,5 m nad wodą.
  Rzeczywisty prześwit: UNVERIFIED (brak danych; na zdjęciach Commons przęsło nisko nad wodą — zgodne co do rzędu).
- Szwy poziomu (reguła ADR 0213): tykocin N = dw671-tykocin-09 S (105,15 / 104,817 m), knyszyn-s W =
  dw671-tykocin-01 E (113,928 / 113,27 / 114,11 m) — identyczne w obu kaflach.
- Pozostałe kafle: ściany terenu i spójność dróg identyczne z main (porównanie `terrain_walls_qa.json`,
  `road_consistency_qa.json`).

## Budżet
`WORLD_MEMORY` tykocin (import Win64): Low 80,8 → 81,8 MB (water 0,7, banks 0,3), High 173,9 → 180,3 MB
(water 0,7, banks 5,6). Kamery (High 1920×1080 clear, edytor, szac. przed SRP batching; A = vqa-wave5, B = ta gałąź):
most +4…+34 draws, +19…+82 tys. tris (max `tyk_narew_side` 390 → 424, 1011 → 1093 tys.); Rynek/trasa +0…+29 draws,
+0…+56 tys. tris; cienie bez zmian (tafla i trzcina nie rzucają cieni). Tabela: `artifacts/water-tykocin-s24/budget-ab.md`.

## Otwarte
1. **Most w Tykocinie to stalowy most łukowy kratownicowy** (Commons „Tykocin Most drogowy” 01–09; znak B-16 3,7 m
   na dojeździe), generator stawia belkowy most z filarami — osobne zadanie (hero bridge / przekrój mostu).
2. Pas trzciny z góry jako regularne „jodełki” kart (widoczne z kamery 150 m) i trzcina na promenadzie miejskiej
   (S brzeg Narwi w mieście jest utwardzony) — strojenie `water_banks` / wykluczenie ciągów pieszych.
3. Tafla Narwi ciemna i szara z bliska (jak ADR 0213 otwarte) — strojenie po zdjęciu właściciela.
4. `visual-critic` nie uruchamiany (agent nie tworzy subagentów) — do zlecenia przez lidera.
5. Derived kafli zbudowany w prywatnej kopii worktree (`-CopyDerived`) — przed usunięciem worktree skopiować do main.
