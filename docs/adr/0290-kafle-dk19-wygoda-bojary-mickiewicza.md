# ADR 0290 — Kafle DK19 w Białymstoku: bialystok-wygoda, -bojary, -mickiewicza (D81, dk19-tiles-s23/s24)

Status: Proposed (dk19-tiles-s24, 2026-11-17; numer 0290 — następny wolny po 0289; do przyjęcia przez lidera przy scaleniu).
Powiązane: ADR 0278 (plan rozbudowy mapy, kafle 5–7 = siatka (1,0), (1,−1), (1,−2)), 0203 (siatka kafli), 0275 (przejścia
szerokości na szwach), 0285 (trasy łączące korytarza), 0273 / 0229 / 0234 (WORLD_MEMORY w `tile_graph.json`), 0274 („Czytniki
grafu” — narzędzia `qa/dk19_*.py`), 0289 (P-2a przez szew), D81 (właściciel: trasa C ↔ Dojlidy przez DK19).

## Kontekst
D81: ciężarówka ma dojechać z kafla C (bialystok-industrial-c) do Dojlid przez DK19 (Andersa → Sosabowskiego → Piastowska →
pl. Antonowicza → Branickiego → rondo Meyera → Ciołkowskiego DW678). ADR 0278 definiował tylko trzy pierwsze kafle; trzy
kafle DK19 nie miały wpisów w `regions.py` ani plików authored. Gałąź dk19-tiles-s23 je dodała; przerwana przenosinami na
nowy PC 17.11 (przebudowa bojary/mickiewicza po poprawce szwu Piastowskiej zabita w połowie). dk19-tiles-s24 dokończyła.

## Decyzja
1. **Trzy kafle 2048 × 2048 m** wg siatki ADR 0203, NMT 2025, ORTO 0,25 m (2022/2024), BDOT10k + OSM z przypiętego pbf;
   definicje w `tools/worldgen/regions.py` i `Data/Regions/<id>/{region.yaml,overrides.yaml,sources.authored.json,
   route_endpoints.json,control_cameras_place.authored.json}` (generator `qa/dk19_tiles_0278.py`).
2. **Szerokości jezdni z ortofoto zamiast BDOT 7,0 m** (`qa/ortho_xsec.py` co 40 m + `qa/dk19_xsec_summary.py`): Piastowska
   mediana 8,25 m (13 stacji), Branickiego DK19 8,40 m (16), Ciołkowskiego 8,20 m (37) → override 2 × 3,50 + 2 × 0,50 = 8,00 m
   (WORKING_VALUE w zmierzonym zakresie; `qa/dk19_xsec_overrides.py --write`, `authored_overrides` przeżywają reimport).
3. **Szew bojary | mickiewicza na Piastowskiej** (w440321721): plateau 14,0 m po stronie bojary, ręczny profil usunięty;
   przejście wg ADR 0275 lustrzane po obu stronach — zmierzone po przebudowie s24: jezdnia 9,50 → 9,27 m | 9,04 → 9,27 m na
   11,6 m (`artifacts/dk19-tiles-s24/seams.md`). Ciołkowskiego L na szwie z Dojlidami: override
   `dk19-ciolkowskiego-seam-dojlidy-left-kerb` (krawężnik po obu stronach; Dojlidy bez zmian).
4. **Trasy kontrolne z punktami pośrednimi** (`qa/dk19_route_vias.py`, węzły grafu co ~300 m): wygoda 91 m, bojary 3267 m,
   mickiewicza 3721 m. Wygoda jest kaflem tylko do streamingu (`noStart`, `no_standalone_start` w katalogu — trasa 91 m krótsza
   niż zapas zamknięcia bezpiecznika startu ADR 0277).
5. **Streaming**: łańcuch portali `bialystok-wygoda..bialystok-mickiewicza` w `tile_graph.json`; link `c-andersa-to-wygoda`
   (C → wygoda, 963 m przez rondo Pamięci Bieżeństwa) i korytarz `bialystok-dojlidy-dk19` w `route_links.json` (4 kafle,
   brakujące 2: krywlany + Dojlidy jako kafel korytarza; złącza bez rozjazdu). Link zastępujący trasę kafla startowego nie
   jest instalowany przy starcie C (jak knyszyn, ADR 0285) — jazda ręczna przez szwy działa.
6. **WORLD_MEMORY** (import Win64 s24, `tile_graph.py`): bojary Low 251,6 / High 620,7 MB, mickiewicza Low 232,1 / High
   557,6 MB, wygoda — patrz „Zmierzone”. Bojary jest najcięższym zmierzonym kaflem, więc `UNKNOWN_MEMORY_MB` /
   `UNKNOWN_MEMORY_HIGH_MB` (reguła „kafel bez pomiaru = najcięższy zmierzony”) rosną z 160,0 / 420,4 do 251,6 / 620,7 MB.

## Zmierzone (s24, nowy PC i5-10400F / GTX 1070)
- build_world --context: bojary 9062 s, mickiewicza 8692 s (exit 0). GLB 64 chunki: bojary High 1046 / Low 420 MiB,
  mickiewicza High 1016 / Low 453 MiB; far_field bojary High 132 326 / Low 30 748 tris, mickiewicza 123 375 / 29 964.
- Ściany terenu > 0,15 m: bojary 20 (max 0,665 m), mickiewicza 6 (max 0,335 m).
- road consistency (na trasie): bojary obstacle_in_lane 47 (what=none), marking_off_carriageway 13, arrow_no_exit 8,
  lane_blind_end 4; mickiewicza 4 / 1 / 8 / 5.
- Szwy (`qa/seams.py`, C | wygoda | bojary | mickiewicza | Dojlidy): 4 szwy, 57 dróg, FAIL 3 — wszystkie poza trasą
  (w375934008 service: krawężnik płaski|zwykły; w616184922 tertiary: chodnik tylko po stronie Dojlid).
- Kamery High overcast (szacunek przed SRP batching): mickiewicza dk19-piastowska-seam-n 1 319 k tris / ~1440 draws,
  pl. Antonowicza 989 k / ~893, Branickiego 991 k / ~956, rondo Meyera 552 k / ~450, Ciołkowskiego 1 161 k / ~876;
  bojary sosabowskiego 1 541 k / ~1203.

## Konsekwencje
- Gęste kafle miejskie DK19 są ~3× cięższe od Dojlid w High (620,7 vs 214,9 MB) — budżet streamingu PC High (ADR 0273)
  trzeba sprawdzić w buildzie z trzema kaflami naraz; budynki High (bojary 279,2 MB) i teren High (201,4 MB) to główne pozycje.
- **Luka: kafel 4 `bialystok-krywlany` nie istnieje.** Ciołkowskiego wchodzi w Dojlidy od N tylko na ~129 m (3 z 379 węzłów
  Dojlid osiągalne) i wychodzi na zachód krawędzią do krywlany (1206 m Dywizjonu 303). Kafle 5–7 łączą C z NW narożnikiem
  Dojlid, ale pełna trasa do sieci Dojlid wymaga kafla 4 — do decyzji lidera / właściciela (ADR 0278).
- `maxspeed:hgv:conditional` (nocne 40 km/h) nie jest atrybutem grafu — WORKING_VALUE tylko w dokumentach.

## Otwarte (z porównania renderów z referencjami Commons / KartaView, `artifacts/dk19-tiles-s24/refs`)
- Rondo Meyera: brak szerokiej opaski z kostki wokół wyspy środkowej (w ref wyraźna); ekrany akustyczne renderują się jako
  ciemne nieprzezroczyste ściany, w ref przezroczyste panele w jasnych ramach.
- Zieleń przy pl. Antonowicza i Piastowskiej rzadsza niż na zdjęciach; las HLOD z bliska wygląda jak płaska ciemna ściana.
- Jasna kwadratowa łata w pasie (bojary route-s2245) — do sprawdzenia źródła decalu.
- `visual-critic` na renderach `vqa/*/view` — nie wykonany przez agenta (do zlecenia przez lidera).
