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
     **Sprzeczność (niska pewność):** jasne piki farby w profilu bocznym (`xsec.json`) leżą ~6,25–7,0 m od siebie
     (02: ~7,0; 04 s 1900: 6,5; 05 s 1400–1750: 6,25), a generator maluje linie klasy G 0,20 m od krawędzi, czyli przy
     7,6 m ~7,2 m od siebie. Albo piki to linie i jest ~0,5–0,8 m asfaltu (opaska) poza linią — wtedy szerokość jest
     dobra, a linia za szeroko — albo krawędź asfaltu odczytana ręcznie obejmuje jasne pobocze i jezdnia ma ~6,7–7,0 m.
     Ortofoto 0,25 m z pasami kół i przechyleniem pojazdów (pojazdy wychodzą o 1,5× za szerokie) nie rozstrzyga tego;
     do potwierdzenia przejazdem / zdjęciem właściciela, potem jedna korekta wpisu `dk65-elcka-xsec` (obejmuje 02–05).
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
- **Most nad Supraślą**: pomost i bariery są, **rzeki brak** — w `tools/worldgen/roads` nie ma etapu wody (grep
  `waterway|water` trafia tylko w `streetscape/buildings_mesh.py`, `export.py` — nie rzeki); dolina = sam teren NMT.
  Największy brak kafla do backlogu (nowy etap generatora, nie override).
- Skrzyżowanie z Dzikowską (węzeł 1197260556): układ osi i wlotu zgodny z ortofoto (`pair-top-dzikowska.jpg`).
- Szew z `dk65-01`: 6,5 m + linie po obu stronach z obu stron szwu (`pair-top-seam-south.jpg`; w kadrze tor
  kolejowy na SW z ortofoto — generator nie ma torów, jak w 0205). Pary `top-elcka`, `top-seam-west`: przebieg zgodny.
- Szwy (pary szwów 02/03/04/05 obejrzane w `artifacts/dk65-tiles-0207/seams-grid.jpg`): punkt wyjścia trasy kafla N =
  punkt wejścia N+1 (< 2 m, test), po drugiej stronie szwu tylko pas kontekstu bez oznakowania.

## Kafel `dk65-03` (Ełcka między Fastami S i N, km 11,80–12,28)
- Graf 54/51, 280 budynków; build_world 663 s (kolejka slotów); ściany terenu 0; spójność 3 × `lane_blind_end`, 0 na
  trasie. Trasa 484 m po jednej krawędzi `w1024956365`; override `dk65-elcka-xsec` (7,6 m + linie) jak w `dk65-02`.
- Pary z góry (szew E, środek, szew N): przebieg prosty zgodny; na ortofoto w środku jest polny wjazd na W
  (s ≈ 240), którego nie ma w OSM ani w świecie. Widok kierowcy: po prawej podniesiony
  krawężnik przy trawie (reguła miejska) — na ortofoto pobocze gruntowe; do backlogu.

## Kafel `dk65-04` (Fasty N, km 12,28–14,36)
- Graf 145/151, 788 budynków; build_world 327 s; ściany terenu > 0,15 m: 52, max 0,69 m; spójność 6 ×
  `lane_blind_end`, 1 na trasie (wlot Szkolnej, węzeł 839428386, 17 m przed skrzyżowaniem, „what: none” — bez wpływu
  na jezdnię trasy).
- Skrzyżowanie Białostocka / Kościelna (węzeł 839431354): czterowlotowe, przejście dla pieszych na N wlocie, parking
  przy kościele NE — układ zgodny z ortofoto (`dk65-04/r2/view/pair-top-koscielna.jpg`); Sosnowa / Klubowa, Szkolna
  i szew S zgodne co do położenia wlotów; przy `top-parking` na ortofoto boczny wjazd na plac na W, w świecie tylko
  równoległa ulica. Ełcka w Fastach N to aleja drzew po obu stronach — generator sadzi drzewa z reguły,
  nie z ortofoto (backlog). Parkujące auta na poboczu przy kościele (s 600–830 na ortofoto) — nieodtworzone.

## Kafel `dk65-05` (Dobrzyniewo Duże, km 14,36–16,56)
- Graf 139/138, 473 budynki; build_world 261 s; ściany terenu > 0,15 m: 13, max 0,67 m; spójność 7 ×
  `lane_blind_end`, 0 na trasie.
- Świerkowa (szew S), Dębowa / Podleśna, Chabrowa i droga bez nazwy s 1686: położenie wlotów zgodne z ortofoto. Przy
  Chabrowej na ortofoto 2024 są **roboty ziemne** (pas S19 / łącznice `proposed` w OSM, km 15,8–16,3); w świecie stan
  OSM: istniejąca droga bez nazwy na E jest asfaltowa, plac budowy nieodtworzony (WORKING_VALUE: brak). Pytanie do
  właściciela razem z `dk65-06`.
- **Nowa jezdnia DK65 w OSM**: 3 krawędzie `primary` ref 65 (`w1151531612`, `w1151531613`, `w1151531608`, 2 × ~1,2 km)
  równolegle na NE od trasy do ronda DK65 — generator zbudował je jako gotowe jezdnie; na ortofoto 2024 w tym miejscu
  są **nasypy piaskowe placu budowy** (`pair-top-seam-north.jpg`). Konflikt dat jak przy S19 — pytanie do właściciela
  (czy ta jezdnia jest już przejezdna).
- Szew N z `dk65-06`: droga zamknięta zaporą na krawędzi kafla (70 m przed rondem DK65) — zniknie z `dk65-06`.

## Budżet (visual-qa, 1920×1080, edytor, szacunek przed SRP batching; A/B nie dotyczy — nowe regiony)
| kafel | WORLD_MEMORY Low / High | draws (est.) kamery z drogi | trójkąty kamery z drogi |
|---|---|---|---|
| `dk65-02` | 59,9 / 139,0 MB | Low 21–196 | Low 45–220 tys. |
| `dk65-03` | 50,5 / 131,7 MB | Low 7–78 | Low 26–83 tys. |
| `dk65-04` | 76,1 / 181,5 MB | Low 47–281 | Low 69–177 tys. |
| `dk65-05` | 75,5 / 176,5 MB | Low 26–171, **High 26–455** | Low 89–173 tys., High 90–537 tys. |
High: max na `rev-mid` (455 draws, 436 tys.) i `route-s0157` (423 / 463 tys.) — wieś + las; mieści się w hipotezie flagowca (≤ 700–1000), nie w Samsungu A (High nie jest tierem A).
Czasy: ingest 2–2,5 min/kafel (pobranie ~300 MB), build_region 7–8 s, build_world 141–663 s (z kolejką slotów),
import 9–10 min, visual-qa 20–35 s na tier. High tylko na ostatnim kaflu (zgodnie z zadaniem).Odniesienie `docs/06` §6 (hipotezy): Samsung A ≤ 300–400 draws, ≤ 400–600 tys. trójkątów. Telefon: nie mierzono
(zadanie bez telefonu).

## Walidacja
- `tests/gis/test_dk65_seams_0207.py` 9/9: szwy 01→02→03→04→05 (ten sam way, ta sama szerokość i linie) + jeden
  przekrój Ełckiej w 02–05 + punkty trasy na szwach < 2 m (9 testów); `tests/gis/test_edge_lines_0205.py` 4/4. Overrides: 4 + 1 + 1 + 1 zastosowane, 0 stale.
  Pełny `pytest tests/gis` i EditMode nie uruchamiane (zmiana = dane regionów + test; kod generatora bez zmian).
- Pętla wizualna: pary render z góry | ortofoto `artifacts/dk65-tiles-0207/dk65-0N/r2/view/pair-top-*.jpg` (20 par),
  widoki kierowcy `low-drive-*.jpg`, `low-rev-*.jpg`, `grid-drive*.jpg`; obejrzane wszystkie 20 par (część w siatkach
  `seams-grid.jpg`, `pairs-grid.jpg`) i siatki widoków kierowcy 02 oraz 03/04/05. Krytyk `visual-critic`: nie
  uruchamiany (agent nie tworzy subagentów) — do zlecenia przez lidera.

## Otwarte
1. Rzeka Supraśl pod mostem w `dk65-02` (brak wody w generatorze).
2. S19 w Fastach: zgodność OSM 2025 vs ortofoto 2024 (pytanie wyżej); węzeł i łącznice z reguł, bez szlifu.
3. Szerokość Ełckiej 7,6 m vs rozstaw linii z ortofoto 6,25–7,0 m — patrz sprzeczność w Decyzji p. 3 (najważniejsze).
3a. Oś OSM Ełckiej może być przesunięta ~0,5–1 m względem środka jezdni (odczyt niepewny przez pasy kół) —
   `center_offset` nie ustawiony.
4. Szerokość w Fastach S (6,5 m BDOT) i na moście — niska pewność; do weryfikacji przejazdem właściciela.
5. Krawężnik po prawej na Ełckiej w `dk65-03` (reguła miejska) zamiast pobocza gruntowego; aleje drzew w Fastach N
   i parkujące auta przy kościele nieodtworzone; dekale włazów na jezdni zamiejskiej (jak w 0205, UNVERIFIED).
6. Plac budowy S19 przy Chabrowej i nowa jezdnia DK65 (`primary`, `dk65-05`) — stan OSM bez placu; odpowiedź
   właściciela razem z `dk65-06`.
6a. Kamery: `dk65-03` ma 5 authored (krótki kafel 484 m) + kamery generyczne z trasy; commity nie są ściśle „jeden na
   kafel” (dane 03–05 szły razem, sekcje ADR osobno). `regions.py` będzie w konflikcie z gałęziami 0203/0204/0206
   (dopisy w tym samym miejscu) — przy scaleniu zachować wszystkie wpisy.
7. Na `dk65-05` trasa kończy się 70 m przed rondem DK65 (szew z `dk65-06`, nie budowany) — droga ucięta na krawędzi.

## Odtworzenie
```
uv run --project tools/worldgen tools/worldgen/ingest.py --region dk65-0N          # N = 2..5
uv run --project tools/worldgen tools/worldgen/build_region.py --region dk65-0N
pwsh artifacts/dk65-tiles-0207/tools/chain.ps1 -Tiles dk65-0N -Tag r2 [-High]       # build_world + export-route + import + vqa
uv run --project tools/worldgen python artifacts/dk65-tiles-0207/tools/pair.py dk65-0N r2
```
