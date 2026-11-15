# ADR 0208: kafel `bialystok-knyszynska` (−3,0, dwa powiaty) i mur z balustradą na pasie niskiego pomostu (maczka)

Status: PROPOSED (2026-11-15, agent `bialystok-t3-0208`, gałąź `bialystok-t3-0208`)

## Kontekst
- D64: trasa ciężarówki Białystok → Knyszyn (wariant A, ADR 0203). Kafle miasta: `bialystok-maczka` (0203),
  `bialystok-kleeberga` (0206), i ostatni — **`bialystok-knyszynska`**, siatka (−3,0), km 5,80–8,76: koniec
  Kleeberga, łącznica, rondo Pamięci Męczeństwa Kresowian (pod wiaduktem), Szosa Ełcka, granica miasta, Szosa
  Knyszyńska. Dalej korytarz `dk65-01` (0205). D63: najpierw przejezdnie i z grubsza.
- Kafel leży w dwóch powiatach: Białystok 2061 (31 %) i białostocki 2002; `Region.teryt_powiat` był jednym kodem.
- ADR 0203 „Otwarte 1”: w `bialystok-maczka` (E 919–926, N 30–31) mur oporowy BDOT10k stał na dodanym pasie
  jezdni przy końcu niskiego pomostu (`furniture_in_lane` na trasie).

## Decyzja
1. **Region** `bialystok-knyszynska`: bbox 770827,595199 – 772875,597247, origin 771851,596223. Nowe pole
   `Region.teryt_powiat_extra` (tu `("2002",)`), właściwość `powiaty`; `build_region`, `ingest`,
   `streetscape/sources.py` i `build_world.preview_trees` czytają BDOT10k / LoD1 / LoD2 każdego powiatu (obiekty z
   obu paczek scalane po id). Puste pole = wynik bajt w bajt jak wcześniej (14 pozostałych regionów).
   `far_field.py`, `lod2_extract.py` (2061 na sztywno) i `water.py` (jeden powiat) — bez zmian, patrz „Otwarte”.
2. **Dane**: 438 węzłów, 461 krawędzi, 1061 budynków (LoD1 900), NMT 2022, ortofoto 2024 0,25 m.
   Trasa kontrolna `route_start.json`: 2961 m, od szwu z kleeberga (772875; 595511,6) do szwu z dk65-01
   (770827; 597006,8).
3. **Drogi kontra ortofoto** (`junction_checks.authored.json`, 9 punktów, `tools/worldgen/qa/junction_topview.py`):
   przebieg osi, łącznica zjazdowa, rondo pod wiaduktem (pierścień r = 23,7 m, 4 wloty), rozdzielone jezdnie
   Szosy Ełckiej przy rondzie, skrzyżowania boczne i łuk Szosy Knyszyńskiej zgodne topologicznie z ortofoto.
   Różnice — „Otwarte”.
4. **Szwy** (overrides po stronie tego kafla; plików sąsiadów nie ruszam):
   - **W, `dk65-01`** (x = 770827): 6 dróg, te same `osm_way` / klasa / pasy / kierunek. Way 234919333 (Szosa
     Knyszyńska): override `width 6.0 + edge_lines both` jak w dk65-01 (BDOT tu 6,5 m, tam 6,0 m).
   - **E, `bialystok-kleeberga`** (x = 772875): 13 dróg, topologia zgodna. BDOT10k dopasowuje szerokość do
     krawędzi grafu, a krawędź kafla tnie drogi na krawędzie różnej długości — stąd trzy rozbieżności. Sprawdzone
     na ortofoto (paski wyprostowane 0,0625 m/px, `seam-e/strip_*.jpg`):

     | way | tu (BDOT) | kleeberga | ortofoto | override (krawędź przy szwie) |
     |---|---|---|---|---|
     | 561326924 `trunk_link`, 29 m do węzła 2504239797 | 7,5 | 6,0 | **jeden pas 3,4 m przylegający do jezdni** (krawężnik → 1. linia przerywana), dalej 3,9 + ~3 m do bariery; brak zieleni między nimi | 6,0 (`confidence: low`) |
     | 222579345 `service` | brak | 6,0 | plac firmy, asfalt ~12 m, bez krawędzi jezdni | 6,0 (WORKING_VALUE) |
     | 224161424 `service` (y = 596184,5) | 3,0 | 4,0 | plac manewrowy, bez krawędzi jezdni | 4,0 (WORKING_VALUE) |

     Żadna z wartości BDOT dla 561326924 nie jest prawdziwym przekrojem: to trzeci pas jezdni głównej, nie osobna
     jezdnia. 6,0 daje ciągłą krawędź na szwie; właściwy układ wymaga jednej poprawki w obu kaflach („Otwarte 1”).
5. **Mur na pasie pomostu** (`tools/worldgen/streetscape/furniture.py`, zmiana wspólnego kodu):
   `DeckKeepout` — mur / płot wycinany z trójkątów jezdni warstwy `bridge`, gdy jego góra wchodzi w okno QA
   (> nawierzchnia − 0,3 m). `fences()` dostaje `decks` z `streetscape/stage.py`.
   r1 pokazał, że pierwsza wersja nie działała: wycięła 2 m, `furniture_in_lane` zostało 2. Pomiar z chunków GLB:
   mur 128,98–130,54, jezdnia pomostu 131,31–131,88, **balustrada na murze do 131,64**. Mur był pod jezdnią —
   w pas wystawała balustrada, a `_retaining_top` liczył sam mur. Teraz: góra muru + `RAILING_H` (1,10 m).
   Mur pod wysokim pomostem (prześwit większy niż balustrada) zostaje.

## Budżet
<!-- BUDGET -->

## Walidacja
<!-- VALIDATION -->

## Otwarte
<!-- OPEN -->
