# ADR 0059: szyby TRAKT — film wycieraczek od zewnętrznej strony, szyba drzwi we własnej przestrzeni, dalsza szyba z zewnątrz (r7 N-16, N-3, N-8, D31)

Status: przyjęty (rendering-perf), 2026-11-10. Źródło: `docs/reports/visual/REVIEW-2026-11-10-r7.md` §10–§14 (pkt 4 i 8),
`REVIEW-2026-11-10-r8.md` §8 (nowa miara N-16). Uzupełnia ADR 0045, 0048, 0056. Dowody: `artifacts/glass-r8/`
(edytor, WorldC, Low/High × overcast/lowsun/dusk; telefon NIE mierzony).

## Przyczyny (zmierzone, nie zgadywane)
1. **N-16 (stożek i prążki przy lowsun) to nie ADR 0056.** Ten sam wzór jest w klatkach sprzed capture
   (`owner/modern-front/r7-maskbar/before`, 14:23; ADR 0056 wszedł o 15:25). Kształt = brzegi pól wycieraczek
   (stożek między polami) i łuki piór (okres 1,5 cm = 8–12 px na 2340 px). `Kamion/Truck Glass` oświetlał film drogowy
   normalną **ściany, którą widać**: od środka to normalna wewnętrzna, więc niskie słońce ZA kabiną świeciło na film
   widziany z fotela. Łuki dodatkowo modulowały transmisję (ok. 1 %), stąd prążki także na asfalcie i trawie (r8).
2. **N-3 (szyba drzwi jak matowa folia).** Test „wewnętrzna/zewnętrzna ściana” używa `_CabCentreOS` w przestrzeni
   obiektu szyby. Szyba drzwi jest dzieckiem `DOOR_L/R` (inny pivot); wartość z przedniej szyby (0; 1; −0,6) wypadała
   w płaszczyźnie szyby drzwi, więc wewnętrzna ściana była cieniowana jak ZEWNĘTRZNA: odbicie capture, mgiełka koloru
   szkła i `_ExteriorTransmission` 0,42 w pasie 1,6–3,2 m nad drogą (to „mleczny pas u góry” i „półprzezroczysty budynek”).
   Filmu wycieraczek na drzwiach nie było (test z−okna wyklucza drzwi; sprawdzone na bounds obiektów).
3. **N-8 (prostokąt w szybie)** = przeciwległa szyba drzwi widziana na wylot przez pustą kabinę (render maski
   `GLASS_DoorR` = magenta dokładnie na prostokącie, `n8_truck34_before_after_mask.jpg`). Nie sonda/box (od ADR 0056
   nie ma sondy).
4. **N-17 (przepał deflektora High)** nie zależy od capture: `rq_envcap=0` daje te same 4,1 % pikseli ≥ 99 %
   (Low 0 %). To lakier + krzywa tonalna High — poza szkłem, otwarte (lakier/look).

## Decyzja
- Film drogowy na **zewnętrznej** powierzchni: ambient i słońce z normalną zewnętrzną (`nOut`), słońce tylko gdy pada
  na zewnętrzną stronę, z funkcją fazową Henyeya-Greensteina g = 0,5 (względem izotropowej, max 4): olśnienie tylko pod
  słońce, jak w prawdziwej kabinie. Łuki piór nie zmieniają transmisji ani nie rozpraszają nieba; są tylko składnikiem
  olśnienia pod słońce. SH liczony raz (na `nOut`; składnik koloru szkła istnieje tylko na ścianie zewnętrznej, gdzie
  `nOut = n`).
- `TruckAssetBuilder`: materiały **MI_Ext_DoorGlassL/R** (kopia MI_Ext_Glass, `_Wiper` 0, absorpcja 0,12 — szyba boczna
  hartowana, Tv ok. 0,80, WORKING_VALUE; UE przednie boczne ≥ 0,70) z `_CabCentreOS` przeliczonym do przestrzeni każdej
  szyby drzwi (log buildu: L (1,25; 0,55; −1,57), R (−1,25; 0,55; −1,56)). Sloty w `TruckVisualRig` przez nazwę, jak
  dotąd. `-extTrans` (tylko eksperyment) zmienia `_ExteriorTransmission` bliższej szyby.
- Widok z zewnątrz: `CabInteriorLighting` ustawia globalne `_KamionCamOutside` (1 = kamera widoku poza kabiną,
  0 = w kabinie lub brak komponentu). Wewnętrzna ściana szyby widziana z zewnątrz to dalsza szyba na drodze przez kabinę;
  jej transmisja × `_SeeThroughClutter` 0,35 (fotel pasażera, zagłówek, słupek B, firanka zasłaniają ok. 2/3 —
  WORKING_VALUE). Bliższa szyba bez zmian (0,42, ADR 0048 r6).
- Przetestowano i **odrzucono** podniesienie `_ExteriorTransmission` (sweep 0,42 / 0,7 / 1,0, `artifacts/glass-r8/et*`):
  σ szyby rośnie tylko przez prostokąt N-8 (ov: 3,6 → 3,9 → 4,1 Low; lowsun do 9,1), a widok „akwarium” wraca.

## Zmierzone (edytor; luma Rec.709 %, przed = HEAD f9143ba, po = ta zmiana)
**N-16, nowa miara r8** (`diff.py`: D = kadr z szybą − T × kadr `-NoGlass` w liniowym, T dopasowane; residuum po
wygładzeniu σ 20 px, piksele szyby bez krawędzi sceny; `added p95−p5` = rozpiętość światła dodanego przez szybę):

| kadr | σ residuum przed → po | p99 \|res\| | dodane p95−p5 |
|---|---|---|---|
| cab-dash High lowsun | 0,85 → **0,42** | 2,83 → 1,15 | 14,0 → **2,6** |
| cab-dash Low lowsun | 0,67 → **0,17** | 2,61 → 0,59 | 13,0 → **1,7** |
| cab-driver High lowsun | 0,60 → **0,35** | 2,10 → 0,98 | 7,5 → 2,0 |
| cab-driver Low lowsun | 0,44 → **0,13** | 1,93 → 0,39 | 7,0 → 1,1 |
| cab-dash High / Low overcast | 0,59 / 0,31 → 0,60 / 0,32 | 1,7 / 1,3 | 5,6 / 4,4 → 6,1 / 4,9 |

Mapy residuum (`n16_residual_before_after.jpg`): przed — koncentryczne łuki i klin, po — tylko krawędzie sceny
(niedopasowanie T przez krzywą tonalną). Wycinek 1:1 `n16_cabdash_lowsun_1to1.jpg`: brak pasów i klina.
Akceptacja r8 (σ różnicy ≤ 1–1,5 po odjęciu gradientu, brak struktury pasmowej): **PASS**.

**N-3** (`cab-left`, trawa za szybą drzwi 250–1150 × 640–790 px, wobec tego samego kadru `-NoGlass`):
sat 14,7 / 28,2 = 0,52 (High ov) → **0,99–1,01**; σ 0,86 → **0,92–0,97** (wszystkie 4 warianty Low/High × ov/lowsun).
Cel ≥ 0,85: **PASS**. (Uwaga: stary przebieg `noglass/` miał jeszcze szybę drzwi — tam „sat 0,67–0,73”; prawidłowa
referencja to `noglass2/`.)

**Szyba z zewnątrz** (`truck-34`, 380–460 × 160–200 @1024, D34/D31): p50 ov High 30,9 → 28,9, Low 29,3 → 26,8 (D34
23–45 PASS); σ ov High 4,23 → 3,64, Low 3,96 → 3,57; lowsun 7,45 → 5,94 / 7,01 → 5,71. **D31 σ ≥ 8: FAIL** i shaderem
nieosiągalne: ten sam obszar BEZ szyby ma σ 5,0–5,5 (ov), a z transmisją 1,0 — 4,1–4,4. Struktura odbicia jest słaba,
bo capture widzi jednolitą halę i niebo (drzewa/latarnie/auta instancjonowane nie wchodzą do capture, ADR 0056), a
wnętrze nie ma kierowcy. Prostokąt N-8: kontrast do sąsiedztwa ov High 6,8 → **4,0**, lowsun 13,9 → 11,8 (słabszy,
nadal widoczny przy lowsun — tak wygląda przeciwległe okno oświetlonej hali).

## Koszt GPU (szacunek; telefon NIE mierzony)
Bez nowych tekstur, przebiegów, draw calli i wariantów. Piksel szyby: +~8 ALU (faza HG: log2/exp2, dot, select),
SH bez zmian (1×). Szyba drzwi: `_Wiper` = 0 pomija gałąź filmu (2× atan2 + smoothstep, ok. 40 ALU), którą wcześniej
liczyła i zerowała — w widoku z kabiny (Low) szyby drzwi to większość pikseli szkła, więc **netto koszt na Low maleje**.
Do potwierdzenia na A16: `device-metrics.ps1` cab-dash/cab-left przed/po.

## Otwarte
- **D31 σ ≥ 8 (ov)**: proponuję zmianę progu (σ ≥ 8 przy lowsun/clear, gdzie po zmianie 5,7–5,9; lub miara na pasie
  odbicia nieba) albo treść: kierowca w kabinie (truck-artist) i tania ścieżka „reflection” w `WorldInstances`
  (world-builder, koszt CPU A8 +4 ms na S24+ przy pełnych instancjach).
- **E7 (obudowy lusterek)**: obudowa to `plastic_satin` (albedo 0,028, roughness 0,36) z atlasu Trim — „chromowy”
  wygląd to odbicie nieba przy szorstkości 0,36 i jasne krawędzie fazek; w szkle lusterka jasny pas to odbicie białej
  ściany własnej kabiny (poprawne). Zmiana wymaga nowego bake'u eksteriera (truck-artist: `mirror_*` → nowy materiał
  „plastic_grain” rough 0,55–0,6); nie ruszałem eksportu, bo równolegle pracuje nad nim Fable (przód TRAKT).
- **N-17** (przepał deflektora High 4 %, niezależny od capture) — lakier/krzywa High, nie szkło.
- Lider po scaleniu: `TruckAssetBuilder.BuildBatch` (nowe materiały drzwi), potem build APK; telefon: N-16 1:1, `cab-left`.
- Test: `TruckDoorGlassTests` (EditMode).
