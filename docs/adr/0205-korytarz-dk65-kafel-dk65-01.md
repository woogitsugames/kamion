# ADR 0205 — korytarz Białystok → Knyszyn: pierwszy kafel poza miastem `dk65-01` i kolejność następnych
Status: Proposed (agent world-builder, s20, gałąź `dk65-corridor-0205`), 2026-11-15. Do scalenia przez lidera.
Powiązane: D63, D64 (`docs/11`), ADR 0203 (plan trasy i 17 kafli, gałąź `bialystok-dk65-0203`), ADR 0204 (Knyszyn),
ADR 0166/0174 (potok i import regionu ≠ C), brief `docs/owner/S20-REGION-RING-BRIEF.md`.

## Kontekst
Plan 0203 dzieli trasę A (stara droga przez Fasty i Dobrzyniewo Duże, bez S19) na kafle siatki 2048 m. Korytarz 0205
to kafle `dk65-01` … `dk65-11`. ADR 0203 zostawiał wybór pierwszego kafla agentowi 0205 (`dk65-11` albo `dk65-06`);
polecenie lidera: pierwszy kafel **poza granicą miasta, kolejny po kaflach miejskich** → `dk65-01`.

## Decyzja
1. **Kafel `dk65-01`**: siatka (−4,0), EPSG:2180 [768779, 595199, 770827, 597247], origin (769803, 596223), powiat
   2002 (gm. Dobrzyniewo Duże; cały kafel leży na zachód od granicy miasta x ≈ 772066). Trasa A km 8,76–9,39:
   Szosa Knyszyńska przecina narożnik NE — wejście (770827, 597006,8) na szwie z `bialystok-knyszynska`, wyjście
   (770244,6, 597247) na szwie z `dk65-02`; 632 m (`route_start.json`), 70 km/h, 2 pasy, `maxaxleload=10`.
2. **Wspólna zmiana OSM**: cherry-pick `7ce3fe325` z `knyszyn-0204` (bbox wyciągu + bbox w kluczu cache) — ten sam
   commit co 0204, bez drugiej wersji.
3. **Źródła**: OSM `podlaskie-261108`; NMT 2025 (4 arkusze), ortofoto 2024 0,25 m RGB (4 arkusze), BDOT10k, LoD1
   2024 i LoD2 2017 powiatu **2002** (nowe pobrania, 462 MB, manifesty w `Data/SourceManifests`). Ortofoto i NMT
   są z lat 2024/2025; w tym kaflu nie ma robót, więc nie ma konfliktu dat.
4. **Budowa ekspresówki: w tym kaflu nie występuje.** Zapytanie `highway=construction|proposed` w bbox + 600 m
   zwraca tylko 3 podjazdy `construction` 500 m na południe od kafla. W kaflu jest natomiast **otwarta** S19/S8
   (węzeł Białystok Zachód: motorway 4,1 km, łącznice 2,7 km, 9 pomostów) — 1,1 km od trasy, wygenerowana z reguł bez
   szlifu. Place budowy, oznakowanie tymczasowe i kadry właściciela z DK65 dotyczą km 16,7–25 (`dk65-06` … `-11`);
   tu nic nie zostało dodane ani zmyślone. Zdjęcia właściciela nie były kopiowane ani użyte jako tekstury.
5. **Przekrój Szosy Knyszyńskiej z ortofoto** (pasek wyprostowany wzdłuż `route_start.json`, 0,25 m/px, odczyt
   ±0,3 m; `artifacts/dk65-corridor-0205/ortho/route_strip.jpg`, `route_zoom_s200.jpg`): asfalt 6,1 m (BDOT10k
   6,0 m; generator przycinał klasę G do 6,5 m), linia środkowa przerywana na osi OSM (±0,3 m), **ciągłe linie
   krawędziowe po obu stronach**, pobocza nieutwardzone ~1,5 m (SW) i ~1,2 m (NE), bez krawężników i chodnika.
   `overrides.yaml`: `width: 6.0` na odcinku głównym (468 m), `edge_lines: both` na 5 krawędziach trasy.
6. **Zmiana generatora** (`roads/markings.py`, `standards.py`): linie krawędziowe na drodze klasy < GP wyłącznie przez
   override `edge_lines`; szerokość 0,12 m, oś 0,20 m od krawędzi (`EDGE_LINE_INSET_MINOR`, WORKING_VALUE; rodzaj
   znaku P-7 dla tej drogi UNVERIFIED). Bez override wynik jest taki sam jak przed zmianą.
7. **Kamery**: 3 z `cameras_generic` (trasa) + 7 authored (`control_cameras_place.authored.json`): 4 widoki z góry
   (szew wschodni, środek, skrzyżowanie ze Św. Franciszka z Asyżu + pętla autobusowa, szew północny) sparowane
   z wycinkami ortofoto, 2 w kierunku Białegostoku, 1 dojazd do skrzyżowania.

## Budżet (visual-qa r2, 1920×1080, edytor; A/B nie dotyczy — nowy region)
| | Low | High |
|---|---|---|
| WORLD_MEMORY (import) | 68,2 MB | 165,9 MB |
| draws (est.), kamery z drogi (6) | 92–187 | 123–260 |
| trójkąty, kamery z drogi (6) | 98–167 tys. | 194–337 tys. |
Czas: ingest ~8 min, build_region < 2 min, build_world 257 s, import ~2 min, visual-qa ~25 s na tier. Telefon: nie
mierzono (zadanie bez telefonu) — budżet z `docs/06` §6 do potwierdzenia przez lidera na A16.

## Walidacja
- Graf: 235 węzłów, 229 krawędzi; budynki 460. Spójność nawierzchni: 21 przypadków, na trasie 1 (`lane_blind_end`
  na dojeździe pętli autobusowej, nie na jezdni trasy). Ściany terenu > 0,15 m: 55 (max 1,62 m przy węźle S19 poza
  trasą; przy trasie do 0,70 m = skarpa rowu, `steep_grass`).
- Pary render z góry / ortofoto: `artifacts/dk65-corridor-0205/r2/view/pair-top-*.jpg` — zgodne: przebieg osi,
  skrzyżowanie, pętla, zjazdy NE, droga gruntowa na południe.
- Testy: patrz raport końcowy agenta i `artifacts/dk65-corridor-0205/logs/{pytest-gis,editmode}.log`.
- visual-critic: nie uruchamiany (agent nie tworzy subagentów) — do zrobienia przez lidera na `r2/Low-clear`,
  `r2/High-clear`.

## Otwarte (backlog szlifu `dk65-01`)
1. Tory kolejowe (linia równoległa ~80–150 m na SW od drogi, przejazd 038 010 956 na drodze gruntowej): generator
   nie ma torów.
2. Pętla autobusowa i wlot Św. Franciszka są na ortofoto żwirowe/nieutwardzone, u nas asfalt; szpaler drzew
   i krzewów po stronie SW drogi nieodtworzony; biało-czerwona zapora przy wlocie Św. Franciszka — pochodzenie
   niezbadane (UNVERIFIED).
3. Latarnie po stronie NE postawione regułą — na ortofoto niepotwierdzone (UNVERIFIED).
4. `cameras_generic` tworzy osobną kamerę dla każdego łańcucha ronda bez nazwy (6 kamer jednego ronda przy S19).
5. Węzeł S19/S8: pomosty z interpolacji (`confidence: low`), 5 ramp ze ścianami do 5,0 m, uskok 1,62 m.
6. `Region.teryt_powiat` to nadal jeden kod — rozszerzenie na listę potrzebne dopiero w `dk65-10` (2002 + 2008).
7. Plik `game/Assets/_Project/UI/Resources/CabDisplay/Nav/dk65-01_route.bytes` jest generowany, nie commitowany.

## Kolejne kafle korytarza (do zrobienia, w tej kolejności)
| kafel | i,j | km trasy | uwagi |
|---|---|---|---|
| `dk65-02` (Fasty S) | −4,1 | 9,39–11,80 | 2401 m; most km 10,85–10,94; przejście pod/nad S19 — sprawdzić z ortofoto |
| `dk65-03` | −5,1 | 11,80–12,28 | 484 m; poza pasem ~300 m sam teren |
| `dk65-04` (Fasty N) | −5,2 | 12,28–14,36 | Białostocka/Kościelna, Szkolna |
| `dk65-05` (Dobrzyniewo) | −5,3 | 14,36–16,56 | `proposed` łącznice km 15,8–16,3 |
| `dk65-06` (rondo DK65) | −5,4 | 16,56–18,26 | rondo (767641, 603483); **początek budowy S19 przy drodze** — kadry właściciela |
| `dk65-07` | −6,4 | 18,27–19,13 | budowa wzdłuż drogi |
| `dk65-08` | −6,5 | 19,13–21,49 | budowa wzdłuż drogi |
| `dk65-09` | −7,5 | 21,49–21,84 | 352 m |
| `dk65-10` | −7,6 | 21,84–24,45 | dwa powiaty (2002 + 2008) → lista `teryt_powiat` |
| `dk65-11` | −7,7 | 24,45–24,83 | 376 m; przełożenie DK65 przy km 25, szew z `knyszyn-s` (0204) |
Przed `dk65-06`…`-11` potrzebna odpowiedź właściciela na pytania ADR 0203 (wariant A/B, które miejsca mają objazd).

## Odtworzenie
```
uv run --project tools/worldgen tools/worldgen/ingest.py --region dk65-01
uv run --project tools/worldgen tools/worldgen/build_region.py --region dk65-01
pwsh artifacts/dk65-corridor-0205/tools/full.ps1 -Tag r2     # build_world + export-route + import + visual-qa Low/High
pwsh artifacts/dk65-corridor-0205/tools/post.ps1             # pytest tests/gis
```
