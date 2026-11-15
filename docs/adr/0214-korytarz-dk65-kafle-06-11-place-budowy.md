# ADR 0214 — korytarz DK65: kafle `dk65-06` … `dk65-11` z grubsza (stara DK65, place budowy S19 obok)
Status: Proposed (agent world-builder, s20, gałąź `dk65-tiles2-0214`), 2026-11-15. Do scalenia przez lidera.
Powiązane: D63, D64, **D65** (`docs/11`), ADR 0203 (plan trasy A, siatka 2048 m), 0204 (knyszyn-s: przekrój DK65,
plac budowy), 0205/0207 (wzorzec kafla korytarza, linie krawędziowe przez override), 0209 (pin roku NMT), 0212
(linie krawędziowe DK65 w Knyszynie, gałąź niescalona), brief `docs/owner/S20-REGION-RING-BRIEF.md` (DROGI NAJPIERW).

## Kontekst
Plan 0203 (wariant A) prowadzi od ronda za Dobrzyniewem Dużym (koniec `dk65-05`, km 16,56) starą DK65 przez las,
Kozińce i Szaciły do szwu z `knyszyn-s` (km 24,83). D65 p.4: na odcinku budowy S19 (km 16,7–25) jazda starą DK65,
bez objazdu, place budowy obok; p.6: nowa jezdnia DK65 (OSM `primary` ref 65 od ronda na SE) nieotwarta.

## Decyzja (wspólna)
1. **Regiony** w `tools/worldgen/regions.py` (siatka planu 0203, x0 776971, y0 595199, 2048 m):

   | kafel | i,j | bbox EPSG:2180 | km trasy A | trasa w kaflu | powiat |
   |---|---|---|---|---|---|
   | `dk65-06` | −5,4 | 766731,603391–768779,605439 | 16,56–18,26 | 1702 m | 2002 |
   | `dk65-07` | −6,4 | 764683,603391–766731,605439 | 18,26–19,13 | 866 m | 2002 |
   | `dk65-08` | −6,5 | 764683,605439–766731,607487 | 19,13–21,49 | 2355 m | 2002 |
   | `dk65-09` | −7,5 | 762635,605439–764683,607487 | 21,49–21,84 | 352 m | 2002 |
   | `dk65-10` | −7,6 | 762635,607487–764683,609535 | 21,84–24,45 | 2615 m | 2002 |
   | `dk65-11` | −7,7 | 762635,609535–764683,611583 | 24,45–24,83 | 378 m | **2008** |

   `route_endpoints.json`: punkty planu przyciągnięte do krawędzi; szew S = koniec `dk65-05` (767660,9; 603391),
   szew W = start `knyszyn-s` (762635; 609811). Powiat (jeden kod na region): udział pokrycia BDOT10k (warstwy
   `OT_PT*_A`) w kaflu — 10: 62 % 2002 / 32 % 2008, 11: 25 % / 75 %. W `dk65-10` trasa przechodzi do powiatu 2008
   na km 23,67 → ~780 m trasy (km 23,67–24,45) bez budynków/pokrycia BDOT 2008 (LoD1 z 2002 nie sięga) — do backlogu
   (wieloma powiatami na region).
2. **Źródła** (`ingest.py`): NMT 2025 1 m, ortofoto 2024-05-27 0,25 m RGB (nowe arkusze), BDOT10k / LoD1 2024 /
   LoD2 2017 powiatów 2002 i 2008 (już były). **`dk65-11` przypięty do NMT 2022** (`sources.authored.json`, wzorzec
   0209): z NMT 2025 szew z `knyszyn-s` (NMT 2022) różnił się o mediana 0,07 / p95 0,64 / **max 2,70 m** (nasypy S19
   z 2025 tylko w jednym nalocie); po pinie 0,000 m, a zmiana roku przechodzi na szew 10/11: mediana 0,05, p95 0,16,
   max 0,48 m (`tools/seam_dz.py`). Pozostałe szwy 05/06…09/10: 0,000 m.
3. **Przekrój z ortofoto** (`tools/axis_offset.py`: profile jasności co 10 m, para pików linii krawędziowych 5,9–7,4 m,
   mediana na 50 m; `strip_zoom.py` ręcznie): stara DK65 (208187096, 27718745) — asfalt 7,1–7,5 m, linie krawędziowe
   6,25–6,75 m od siebie (0,25 m; na 0,1 m 2025 w `knyszyn-s` 6,7–6,8 m) → **ten sam zestaw co `knyszyn-s` po 0212**:
   2 × 3,4 m + 2 × 0,35 m = 7,5 m, `edge_lines: both` (wpis `dk65-carriageway-width` skopiowany dosłownie z gałęzi
   0212; dla 208187096 i łącznika 1151531610 wpis `dk65-old-xsec` z tym samym `set`). Na ortofoto 2024 linie
   krawędziowe są przerywane (P-7a); kadry właściciela z 2026 (20260727_073424, 073802, 20260728_104740) pokazują
   ciągłe → ciągłe (P-7b). **Oś OSM = środek jezdni** (±0,4 m): punkty `route_start.json` leżą na osi prawego pasa
   (+1,7 m), a zmierzony środek wychodzi +1,25…+2,0 m od nich — bez `center_offset` (to samo na 0,1 m 2025 w
   `knyszyn-s`). Ełcka (1560819273, 1448265994, wlot ronda): **6,9 m** + linie (D65 p.5).
4. **Rondo za Dobrzyniewem (km 16,66)**: OSM (edycje 2026-10) ma pełne rondo z czterema wlotami; ortofoto 2024-05-27
   pokazuje w tym miejscu skrzyżowanie T i piaszczystą platformę budowy (`dk65-06/ortho/rondo_graph*.jpg`). Trasa A
   (wybór właściciela) idzie przez rondo → zostaje wg OSM (stan bieżący). **Ramię SE = nowa jezdnia DK65**
   (1557884361/62, 1151531608/13) wycięte z grafu (`graph_filter.authored.json`, D65 p.6) i zamienione w plac budowy;
   rondo ma 3 wloty (Ełcka, stara DK65 NW, droga budowy NE).
5. **Place budowy S19 — nowy etap generatora** `tools/worldgen/streetscape/construction_site.py` (override
   `kind: construction_site`; bez override region nie zmienia się — test `test_construction_site_noop_without_override`):
   osie OSM `highway=construction` (kopiowane do override z id drogi i datą edycji przez
   `tools/worldgen/qa/construction_sites.py`, więc plac przeżywa reimport i późniejsze edycje OSM; osie wychodzą poza
   kafel o pół szerokości + 10 m, oba kafle szwu dostają tę samą krawędź) buforowane wg klasy (S19 30 m — jak
   `knyszyn-s`; łącznice 12, drogi główne/zbiorcze 10, pozostałe 7, nieotwarta jezdnia 10 m), minus 4 m od każdej
   zbudowanej jezdni. Na placu: **piasek** w kolorze terenu (kanał A masek gruntu — ten sam co nieużytki / wycinki
   0163; bez lasu i bez komórek HLOD lasu), **hałdy** (wydłużone, zaokrąglone, 1,2–3,2 m, ~1,2/ha, ziarno = id
   override; w heightfieldzie terenu → przychodzą z siatką terenu, jej LOD i kolizją, 0 dodatkowych draw calli; nie
   bliżej krawędzi kafla niż ich półdługość + 2 m), **płot tymczasowy** (siatka ocynk, stopy betonowe, przęsła 3,5 m ×
   2,0 m) na ~20 % krawędzi placu zwróconej do drogi (≤ 45 m), odcinkami 25–70 m. Platforma 0 m: NMT 2025 ma już
   nasypy 2025. Wszystkie wymiary WORKING_VALUE (kadry właściciela, bez pomiaru). Maszyny, znaki tymczasowe, żółte
   oznakowanie — nie.
6. **Latarnie**: stara DK65 poza Knyszynem bez latarń (`rural-roads-unlit` z `knyszyn-s` dosłownie dla 27718745,
   `dk65-old-unlit` dla 208187096 / 1151531610): brak słupów i ich cieni na ortofoto, brak lamp na 10 kadrach
   właściciela. Pytanie: lampy w Kozińcach na DK65 (D65 p.8 — jeśli są, to białe LED).
7. **Kamery** (4–9 na kafel, `control_cameras_place.authored.json`): widoki z góry 140×249 m przy szwach, rondzie,
   przecięciach z osiami S19, sparowane z ortofoto; widoki kierowcy 2,5 m wzdłuż i pod prąd.

<!-- KAFLE -->

## Budżet
<!-- BUDZET -->

## Walidacja
<!-- WALIDACJA -->

## Otwarte
<!-- OTWARTE -->

## Odtworzenie
```
uv run --project tools/worldgen tools/worldgen/ingest.py --region dk65-NN          # NN = 06..11
uv run --project tools/worldgen tools/worldgen/build_region.py --region dk65-NN
uv run --project tools/worldgen python tools/worldgen/qa/construction_sites.py --region dk65-NN [--ways …]   # tylko przy zmianie OSM
pwsh artifacts/dk65-tiles2-0214/tools/chain.ps1 -Tiles dk65-NN -Tag r2           # build_world --context + export-route + import + vqa Low
uv run --project tools/worldgen python artifacts/dk65-tiles2-0214/tools/pair.py dk65-NN r2
```
