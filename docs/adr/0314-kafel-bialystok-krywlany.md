# ADR 0314 — Kafel bialystok-krywlany (ADR 0278 kafel 4): domknięcie trasy C ↔ Dojlidy przez DK19

Status: Proposed (krywlany-s24, 2026-11-20; numer 0314 — następny wolny po 0313 z HANDOVER.md; do przyjęcia przez lidera
przy scaleniu). Powiązane: ADR 0278 (plan mapy, kafel 4 = siatka (0,−3)), 0290 (kafle DK19 i luka krywlany), 0203 (siatka),
0209/0212 (pin NMT), 0285 (trasy łączące), 0275 (szwy), D63 (najpierw przejezdne), D81 (C ↔ Dojlidy), D93 pkt 4.

## Kontekst
ADR 0290 zostawił lukę: Ciołkowskiego DW678 schodzi z mickiewicza na N krawędź Dojlid, przecina ich NW narożnik i wychodzi
na zachód do kafla 4, który nie istniał; trasa Dojlid zaczyna się na ich W krawędzi (Dywizjonu 303). Korytarz
`bialystok-dojlidy-dk19` kończył się na mickiewicza, a krywlany i Dojlidy były w `missing`.

## Decyzja
1. **Kafel 2048 × 2048 m** `bialystok-krywlany`, bbox EPSG:2180 776971, 589055 – 779019, 591103, powiat 2061, NMT 2025
   (pin jak Dojlidy i mickiewicza), ORTO 2024 0,25 m, BDOT10k + LoD1/LoD2 2061, OSM z przypiętego pbf 261108.
   Definicja i pliki authored z generatora `tools/worldgen/qa/krywlany_tile_0278.py` (ta sama ścieżka ciężarówki co
   `qa/dk19_tiles_0278.py`). `overrides.yaml` pusty (rough first, D63).
2. **Trasa kontrolna** = kawałek korytarza w kaflu: od szwu z Dojlidami na Ciołkowskiego (779019, 591055,7) przez rondo
   i Dywizjonu 303 do wejścia trasy Dojlid (779019, 590253), ~1205 m (OSM API 0.6 z 2026-11-16).
3. **Narożnik Dojlid (~87 m Ciołkowskiego, way 279881972)** nie jest częścią żadnej trasy kafla, a mickiewicza i krywlany
   stykają się tylko narożnikiem (streamer otwiera szwy N/E/S/W). Zamiast zmieniać trasę Dojlid (kafel zbudowany) —
   **link** `dojlidy-ciolkowskiego-corner-to-krywlany` w `Data/Streaming/route_links.yaml` (kafel Dojlidy, `head_from`
   koniec trasy mickiewicza, `tail_to` start trasy krywlany). Korytarz: `[C, wygoda, bojary, mickiewicza, dojlidy,
   krywlany, dojlidy]` — Dojlidy dwa razy (najpierw link narożnika, potem ich trasa).
4. **Narzędzia danych**: (a) `gugik_index.get_feature` ponawia zapytanie WFS (5×, przerwa 30·n s) — 20.11 indeks
   mapy.geoportal.gov.pl zrywał połączenia/timeout; (b) `build_region.build_ortho` przyjmuje arkusz ORTO z WKT
   „ETRF2000-PL / CS92” bez kodu EPSG (arkusze N-34-107-C-b-3-1/-3-3 z 2024) jako EPSG:2180 przez WarpedVRT bez
   reprojekcji — sprawdzone: ten sam datum (ETRF2000 Poland, GRS 1980) i parametry TM (lon_0 19, k 0,9993, x_0 500000,
   y_0 −5300000), WKT kończy się AUTHORITY["EPSG","2180"]. Inny CRS nadal kończy się błędem `merge`.

## Zmierzone
- Ingest 2026-11-20: 8 plików, 339 074 329 B (NMT 2025 ×4, ORTO 2024 ×4); BDOT/LoD 2061 już na dysku.
- build_region: 396 węzłów, 455 krawędzi, 700 budynków; teren 141,33–167,01 m EVRF2007, 0 brakujących próbek.
- Szew z Dojlidami (graf): 6/6 węzłów brzegowych, odchyłka 0,0 m.
