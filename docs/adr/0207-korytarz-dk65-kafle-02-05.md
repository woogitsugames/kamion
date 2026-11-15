# ADR 0207 — korytarz DK65: kafle `dk65-02` … `dk65-05` z grubsza (Fasty, Dobrzyniewo Duże)
Status: Proposed (agent world-builder, s20, gałąź `dk65-tiles-0207`), 2026-11-15. Do scalenia przez lidera.
Powiązane: D63, D64 (`docs/11`), ADR 0203 (plan trasy A, siatka 2048 m), ADR 0205 (wzorzec kafla `dk65-01`, linie
krawędziowe przez override), brief `docs/owner/S20-REGION-RING-BRIEF.md` (DROGI NAJPIERW).

## Kontekst
Plan 0203 (wariant A, stara droga) prowadzi z `dk65-01` przez Fasty i Dobrzyniewo Duże do ronda DK65 (km 16,6).
Kafle `dk65-06`+ (km 16,7–25, budowa S19) czekają na odpowiedź właściciela — nie ruszane.

## Decyzja (wspólna dla kafli)
1. **Regiony** dopisane w `tools/worldgen/regions.py` (siatka planu 0203, x0 776971, y0 595199, 2048 m, powiat 2002):

   | kafel | i,j | bbox EPSG:2180 | km trasy A | trasa w kaflu |
   |---|---|---|---|---|
   | `dk65-02` | −4,1 | 768779,597247–770827,599295 | 9,39–11,80 | 2401 m |
   | `dk65-03` | −5,1 | 766731,597247–768779,599295 | 11,80–12,28 | 484 m |
   | `dk65-04` | −5,2 | 766731,599295–768779,601343 | 12,28–14,36 | 2079 m |
   | `dk65-05` | −5,3 | 766731,601343–768779,603391 | 14,36–16,56 | 2202 m |

   `route_endpoints.json` = punkty wejścia/wyjścia planu 0203 przyciągnięte do krawędzi kafla (ciągłość: koniec
   `dk65-01` (770244,6; 597247) ↔ start `dk65-02` (770244,2; 597247), dalej identyczne punkty na szwach).
2. **Źródła** (`ingest.py`): NMT 2025-05-25 1 m, ortofoto 2024-05-27 0,25 m RGB (nowe arkusze, ~1,2 GB łącznie,
   manifesty `Data/SourceManifests/gugik-{nmt-2025,orto-2024-rgb-0p25}-dk65-0N.json`), BDOT10k / LoD1 2024 / LoD2 2017
   powiatu 2002 — te same pliki co `dk65-01` (pominięte, sha zgodne). Bez Drzewa3D.
3. **Przekrój z ortofoto** — narzędzia `artifacts/dk65-tiles-0207/tools/`: `ortho_strip.py` (pasek wyprostowany wzdłuż
   `route_start.json`, ±15 m, 8 px/m; profil boczny `xsec.jpg`), `strip_zoom.py` (24 px/m z linijką 1 m), `mosaic.py`,
   `cams.py` (kamery authored + wycinek ortofoto o tym samym zasięgu), `pair.py` (render z góry | ortofoto).
   Odczyt ręczny ±0,4 m (pasy kół i plamy cienia utrudniają automat — `band()` odrzucony, liczby z odczytu):
   - **Szosa Knyszyńska** (way 396566354, s 0–552 w `dk65-02`): asfalt 6,4–6,6 m → BDOT 6,5 m zostaje (= szew
     z `dk65-01`, override `knyszynska-xsec-e`: tylko linie), **ciągłe linie krawędziowe** po obu stronach.
   - **Fasty S, 50 km/h** (s 554–1458): linie krawędziowe widoczne; szerokość 6,4–7,4 m (wloty i pobocza
     rozmywają krawędź) → BDOT 6,5 m bez zmiany, `confidence: low`.
   - **Ełcka / Studzienna, 90 km/h** (`dk65-02` s 1548+, `dk65-03`, `-04`, `-05`): asfalt 7,2–8,0 m w 5 punktach
     (02 s 1950: 8,0; 04 s 200: 8,0, s 1360: 7,6, s 1960: 7,2; 05 s 1200: 7,8), linie krawędziowe ~7,5 m od siebie.
     BDOT10k 6,0–6,5 m jest tu za wąskie → **override 7,6 m + `edge_lines: both`** (WORKING_VALUE).
   - **Most nad Supraślą** (way 41533342, s 1460–1546): balustrady 10,5 m, jezdnia z opaskami ~9 m → 7,5 m (przejście
     do Ełckiej), `confidence: low`.
   Overrides są **way-level** (`target: {osm_way: […]}`), ten sam wpis `dk65-elcka-xsec` w kaflach 02–05 → bez skoku
   szerokości i urwanych linii na szwach (`tests/gis/test_dk65_seams_0207.py`).
4. **Kamery** (6–10 na kafel): widoki z góry 140×249 m (północ w górę) przy szwach i skrzyżowaniach, sparowane
   z ortofoto (`<kafel>/r2/view/pair-*.jpg`), + 2–3 widoki kierowcy 2,5 m (wzdłuż / pod prąd).

## Kafel `dk65-02` (Fasty S, km 9,39–11,80)
- Graf 99 węzłów / 88 krawędzi, 293 budynki; build_world 141 s; spójność nawierzchni: 4 × `lane_blind_end`, 0 na
  trasie; ściany terenu > 0,15 m: 22, max 0,67 m. Overrides 4/4 zastosowane, 0 stale.
- **S19 nad drogą (s ≈ 930)**: OSM (2025) ma wiadukt S19 (`motorway`, `bridge=viaduct`, `layer=1`, ref S19;65) nad Szosą
  Knyszyńską; **na ortofoto 2024-05-27 wiaduktu nie ma** (pole, polna droga, ziemne roboty na N). Generator odtwarza
  stan OSM (bieżący przejezdny) — wiadukt, nasypy i nowe łącznice serwisowe; układ lokalnych dróg przy S19 różni się
  od ortofoto (stan sprzed oddania). **Pytanie do właściciela**: czy S19 nad DK65 w Fastach jest już oddana (tak jak w
  OSM)? Para: `dk65-02/r2/view/pair-top-s19.jpg`, widok kierowcy `low-drive-s19-approach.jpg`.
- **Most nad Supraślą**: pomost i bariery są, **rzeki brak** (generator nie rysuje wody; dolina = sam teren NMT) —
  największy brak kafla do backlogu.
- Skrzyżowanie z Dzikowską (węzeł 1197260556): układ osi i wlotu zgodny z ortofoto (`pair-top-dzikowska.jpg`).
- Szew z `dk65-01`: 6,5 m + linie po obu stronach z obu stron szwu (`pair-top-seam-south.jpg`).

## Kafel `dk65-03` … `dk65-05`
(uzupełniane po imporcie — sekcje poniżej)

## Budżet (visual-qa, 1920×1080, edytor, szacunek przed SRP batching; A/B nie dotyczy — nowe regiony)
| kafel | WORLD_MEMORY Low / High | draws (est.) kamery z drogi | trójkąty kamery z drogi |
|---|---|---|---|
| `dk65-02` | 59,9 / 139,0 MB | 21–196 | 45–220 tys. |
Odniesienie `docs/06` §6 (hipotezy): Samsung A ≤ 300–400 draws, ≤ 400–600 tys. trójkątów. Telefon: nie mierzono
(zadanie bez telefonu).

## Walidacja
- `tests/gis/test_dk65_seams_0207.py`: szwy 01→02→03→04→05 (ten sam way, ta sama szerokość i linie) + jeden przekrój
  Ełckiej w 02–05.

## Otwarte
1. Rzeka Supraśl pod mostem w `dk65-02` (brak wody w generatorze).
2. S19 w Fastach: zgodność OSM 2025 vs ortofoto 2024 (pytanie wyżej); węzeł i łącznice z reguł, bez szlifu.
3. Oś OSM Ełckiej może być przesunięta ~0,5–1 m względem środka jezdni (odczyt niepewny przez pasy kół) —
   `center_offset` nie ustawiony.
4. Szerokość w Fastach S (6,5 m BDOT) i na moście — niska pewność; do weryfikacji przejazdem właściciela.
5. Na `dk65-05` trasa kończy się 70 m przed rondem DK65 (szew z `dk65-06`, nie budowany) — droga ucięta na krawędzi.
