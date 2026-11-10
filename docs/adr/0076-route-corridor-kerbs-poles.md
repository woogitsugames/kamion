# ADR 0076: Korytarz trasy P0 — krawężniki i słupy na jezdni, włączenia łącznic na osiach OSM

Status: przyjęty (world-builder, roads-p0-r10), 2026-11-11. Zgłoszenia właściciela P0 z filmu 2026-11-10
(„krawężnik w poprzek pasa wyrzuca ciężarówkę”, „latarnia stoi na środku pasa na wiadukcie”, garb na włączeniu),
audyt `artifacts/map-audit-r9/BUGS.md` MA-001 / MA-002 / MA-012. Zależy od ADR 0074 (spójność nawierzchni) i
ADR 0075 (wierność względem OSM / ortofoto). Dowody: `artifacts/roads-p0-r10/`.

## Kontekst
- `test_route_corridor` na czystym buildzie: 64 stacje z przeszkodą / 9 uskoków. Bisekcja: `network.align_forks`
  (ADR 0074) przesuwa łącznicę Andersa → Rondo Putry (w606396463) o 3,25 m pod prawy pas, a `scripts/export-route.py`
  prowadził trasę po surowej osi OSM, czyli 0,45 m za krawężnikiem łącznicy.
- MA-001 / MA-002 (Andersa, włączenie z Ronda Bieżeństwa) i MA-012 (włączenie z Ronda Putry): OSM zbiega oś łącznicy
  do osi jezdni głównej w jednym węźle, więc dwie wygenerowane jezdnie nachodzą na siebie 15–45 m przed węzłem. Każda
  miała własny krawężnik, pobocze i profil wysokości: krawężnik 12–15 cm w poprzek pasa sąsiada (collider kół w
  Unity), łata skrzyżowania 45 m rozpięta między profilami różniącymi się o 1,0–1,9 m (garb).
- Latarnie drogi pod wiaduktem przebijały pomost; latarnia jednej jezdni stała na pasie sąsiedniej.

## Decyzja
1. **Trasa = pas wygenerowanej jezdni** (`roads/route.py`, `pipeline.build_network` wspólne z generatorem): środek
   prawego pasa po wszystkich przesunięciach; na stykach bez skrętu zmiana pasa (smoothstep, 12 × przesunięcie,
   ≥ 20 m) **na jezdni o większej liczbie pasów** (przy równej — na szerszej), na skrętach przycięcie i zaokrąglenie
   Béziera (4 m / 10 m). Zmiana pasa „przed węzłem” na jednopasowej gałęzi włączenia prowadziła prawe koła przez nos
   krawężnika j:n3341716400 (4 uskoki przy s = 618 m) — stąd reguła liczby pasów.
2. **Włączenia / rozwidlenia z przyrostem pasów zostają na osiach OSM** (`network.abreast_forks`,
   `ABREAST_PUSH = False`). Wersja r1 układała gałęzie obok siebie („abreast”: przesunięcie łącznicy o 1,2–9,1 m na
   15–120 m, poszerzenie jezdni pojedynczej). Sprawdzenie na ortofoto GUGiK 2024 (sekcja niżej) wykazało, że to
   gorzej niż oś OSM, więc przesunięcie wyłączono. Funkcja tylko wiąże gałąź nachodzącą na sąsiada
   (`meta["abreast_of"]`, lista `roads_qa.json → summary.fork_abreast`, 6 par), a jedną nawierzchnię dają:
   - `profile.build_profiles` krok 1b (gałąź naziemna bierze wysokość krawędzi sąsiada) oraz **nowe wiązanie nasypu**:
     jezdnia na nasypie (OSM `layer ≥ 1`, bez obiektu) przejmuje wysokość łącznicy, która się w nią włącza
     (`adjacent_targets(..., skip = c.bridge, min_dot = 0,7)`). Zjazd z wiaduktu Putry był 1,0 m nad łącznicą 30 m
     przed węzłem; teraz krawędzie różnią się o ≤ 0,1 m na odcinku wspólnym (21 m), 0,6 m dopiero na początku klina.
   - `meshing.cull_sides_on_carriageway`: krawężnik / chodnik / pobocze jednego elementu leżące na jezdni drugiego
     (to samo kryterium co kontrola `kerb_on_carriageway`: jezdnia pod trójkątem i w pierścieniu 0,30 m) są usuwane
     z renderu i kolizji (1297 trójkątów krawężnika, 134 poboczy w 158 częściach).
   - drugi przebieg `assign_sides(trims=True)`: krawędź dotykająca innej jezdni (szczelina < 0,5 m) jest „flush”
     (`MAT_FLUSH_ROAD`: asfalt, bez krawężnika), a pasek asfaltu **sięga sąsiedniej jezdni** (szerokość = szczelina,
     ≤ 1,5 m); to samo dla narożników łat (`meshing._corner_gaps`). Wcześniej dwa paski po 0,15 m zostawiały szczelinę
     0,3–0,9 m do terenu 0,5 m niżej (j:n10015785253, `terrain_walls` 2 pkt → 0). Pasek narożnika pochyla się na krawędź
     sąsiada (`_corner_gaps` zwraca też różnicę wysokości; `side_profile` dla flush: `h` = wznios zewnętrznej krawędzi),
     ale tylko gdy różnica ≤ `CORNER_FILL_DZ_M` 0,15 m — łącznice 0,4–0,5 m obok jezdni głównej (j:n1883469484)
     zachowują krawężnik.
   - `meshing.PatchHeight.arm_plane`: punkt obok przyciętej części ramienia bierze wysokość z jego krawędzi, a nie
     z płaszczyzny przekroju końcowego niesionej 15–40 m po zmiennym spadku.
   - `profile.shifted_end_heights` (krok 1c): koniec łańcucha odsunięty od węzła przez `align_forks` startuje z
     nawierzchni jezdni, którą opuszcza (było 0,11 m nad nią: rampa 0,2 m / 3 m pod prawymi kołami, s = 1408 m).
3. **Słupy** (`streetscape/furniture.py`): `clear_under_decks` (słup, którego trzon przebiłby pomost nad nim, znika z
   całym osprzętem), `clear_level_carriageways` (podstawa na jezdni na swoim poziomie, także na pomoście). Kryterium
   właściciela: latarnia tylko na krawędzi pomostu / w pasie dzielącym — `artifacts/roads-p0-r10/scripts/check_poles.py`: 1124 obiekty na gruncie (700 latarni),
   0 na jezdni, 0 przez pomost.
4. **Kontrole** (`roads/consistency.py`): nowe rodzaje `kerb_on_carriageway`, `prop_through_deck`; w
   `test_road_consistency.RATCHET` oba = 0, pozostałe obniżone do stanu zmierzonego.

## Ortofoto: „abreast” czy oś OSM? (decyzja lidera 2026-11-10)
Nakładki `artifacts/roads-p0-r10/abreast_ortho/abreast_<węzeł>.jpg` (8 węzłów, okno 120 m; żółty = abreast, cyjan =
ta sama jezdnia na osi OSM, magenta = oś OSM; `_h32` = okno 64 m na ortofoto 0,08 m) i pomiar
`abreast_vs_ortho.json` (`scripts/abreast_vs_ortho.py`: taśmy jezdni obu wariantów na arkuszu 0,25 m z 2024-05-27,
okno ± 70 m wokół węzła):

| miara (suma 8 okien) | abreast | oś OSM |
|---|---|---|
| powierzchnia jezdni | 43 401 m² | 39 395 m² |
| jezdnia na zieleni (ExG > 0,06) | 639 m² | 493 m² |
| jezdnia na „nie-drodze” (model koloru nawierzchni) | 6 409 m² | 5 968 m² |

Bliżej zdjęcia: oś OSM w 7 oknach, abreast w 1 (n1847317043, różnica 2 m²). Na Andersa zach. (n1832975577,
n1832991672, n1847317043) żółte krawędzie leżą 5–9 m poza jezdnią, na trawniku i chodniku; przy Rondzie Bieżeństwa
(n3341716402, `_h32`) rzeczywisty krawężnik północny biegnie po cyjanie, żółty 1,5–2 m dalej na trawie; przy Rondzie
Putry (n1847044938, `_h32`) abreast trafia w krawężnik pasa włączenia za węzłem (~40 m), ale przed węzłem wchodzi
2–3 m na pobocze i drogę rowerową. Okna trzech węzłów przy Rondzie Bieżeństwa nakładają się (ten sam obszar liczony
trzykrotnie). Wniosek: **NIE** — rzeczywiste pasy włączeń leżą tam, gdzie rysuje je OSM; jezdnie nachodzą na siebie
i są jedną nawierzchnią. Zgodne z wymaganiem właściciela („drogi jak w OSM, żeby mieszkaniec wiedział, jak jechać”):
kolejność i położenie pasów pochodzą z OSM. Provenance `abreast` i osobna metryka względem ortofoto nie są potrzebne,
bo żaden odcinek nie jest już przesuwany.

## Ratchety fidelity (`tests/gis/test_road_fidelity.py`)
Raport `fidelity_qa.json` na main był sprzed ADR 0074 (`test_report_not_stale` czerwony na main), więc poniższe to
pierwsze zmierzone wartości generatora 0074; r2 tego ADR żadnej z nich nie zmienia (bieg „bez abreast” poprzedniej
rundy dał te same liczby: `fidelity_no_abreast.json`).

| miara (trasa startowa) | r9 (ADR 0075) | 0076 r1 (abreast) | 0076 r2 = BASELINE | przyczyna zmiany względem r9 |
|---|---|---|---|---|
| oś względem OSM p95 | 0,032 m | 1,745 m | **0,129 m** | `align_forks` (0074): łącznica w606396463 3,25 m od osi, w173956083 zanik do 0; pozostałe krawędzie p95 ≤ 0,11 m |
| krawędź względem ortofoto p95 | 2,04 m | 2,57 m | **2,50 m** | ta sama łącznica jest teraz mierzona (18 stacji, 3,9 m) |
| wysepki nieobecne na ortofoto | 4 | 7 | **6** | (336, −563) 14 m² w esowaniu łącznicy w282244180 i (−366, −119) 373 m² między zjazdem z wiaduktu a łącznicą — oba z przesunięć 0074 |
| pas w wysepkę (błąd generatora) | 3 | 2 | **2** | — |
| zgodność liczby pasów | 25/25 | 25/25 | 25/25 | — |

Cel właściciela (oś p95 ≤ 1,0 m) spełniony; cel lidera dla tej rundy (≤ 0,13 m) spełniony. Tolerancja osi 0,02 → 0,001 m
(metryka jest deterministyczna). Wysepki: przyrost z abreast (7 → 6) usunięty; zejście z 6 do ≤ 4 należy do ADR 0077
(kliny / narożniki skrzyżowań, `junctions.compute_corners` — tu nietknięte).

## Wyniki (build 2026-11-11, `bialystok-industrial-c`)
- `tests/gis/route_corridor.py`: 2394 m, 4789 stacji, **0 uskoków, 0 stacji z przeszkodą**, 0 bez nawierzchni.
- `road_consistency_qa.json`: kafel 145 → **69** (furniture_in_lane 5 → 1, marking_off_carriageway 17 → 3,
  obstacle_in_lane 58 → 2, prop_on_carriageway 1 → 0, kerb_on_carriageway 0, prop_through_deck 0, lane_blind_end 55,
  arrow_no_exit 8); na trasie 2 → 1 (lane_blind_end przy bramie, j:n1882954015).
- Nawierzchnia przy 8 węzłach (`scripts/overlap_dz.py`, siatka 0,5 m, okno ± 40 m, kolizja asfaltu): przy
  n1847044938 (MA-012) komórki odstające > 5 cm od średniej 4 sąsiadów 119 (max 0,238 m) → **0** (max 0,049 m).
- `terrain_walls_qa.json`: kategoria `skirt:j:road_asphalt` 2 → 0; `steep_grass:verge_grass` 4 → 0.

### Runda 3 (build 2026-11-11 00:29, pasek narożnika ze wzniosem) — stan końcowy gałęzi
- `pytest tests/gis`: **222 passed, 2 xfailed**; `route_corridor.py`: 2394 m, 4789 stacji, 0 uskoków, 0 przeszkód.
- `road_consistency_qa.json`: 69 (arrow_no_exit 8, furniture_in_lane 1, lane_blind_end 55, marking_off_carriageway 3,
  obstacle_in_lane 2; kerb_on_carriageway 0, prop_on_carriageway 0, prop_through_deck 0).
- `terrain_walls_qa.json`: 6 → **5** (yard_concrete 4 → 3, max 0,364 → 0,345 m; `skirt:j:road_asphalt` 0).
- `cull_sides_on_carriageway`: 1262 trójkąty krawężnika, 132 poboczy w 151 częściach (było 1297 / 134 / 158).
- `check_poles.py`: 1125 obiektów na gruncie (700 latarni), 0 na jezdni, 0 przez pomost, 0 latarni w |lat| < hw.
- `overlap_dz.py` (`final/overlap_dz_r3.json`): bez zmian względem poprzedniego buildu (n1847044938: 0 komórek > 5 cm,
  max 0,049 m).
- Unity 6000.3.28f1: `import-region` OK (Medium 112,0 MB, High 248,6 MB siatek + instancji + kolizji);
  PlayMode `WorldCRouteTests|WorldCBarrierTests` **3/3** — trasa 2390/2394 m ukończona: zestaw 40 t max |dv|/krok
  0,152 m/s (s = 359 m), solo 0,080 m/s, bez kontaktu nadwozia, max odchyłka poprzeczna 0,75 m; EditMode 176 passed,
  0 failed, 7 skipped (188).
- Kamery (13, Medium, overcast; `renders/*.png`, `renders_1280/*.jpg`) obejrzane i porównane z
  `abreast_ortho/*_h32.jpg`: brak krawężnika w poprzek pasa na włączeniach Andersa (au_f_s0620/0640, p0_ma001_top) i
  z Ronda Putry (au_r_s1380/1400, p0_ma012_top), szczelina przy j:n10015785253 zamknięta asfaltem (nos pasa dzielącego
  kończy się krawężnikiem), latarnie poza jezdnią. Ocena `visual-critic` nie wykonana (agent bez subagentów) — lider.

## Konsekwencje i otwarte
- Jezdnie włączeń nachodzą na siebie w planie (jedna nawierzchnia, dwie siatki): przy Rondzie Bieżeństwa 88 m² z
  różnicą wysokości do 0,145 m w (345, −562) (łącznica w282244180 / j:n1882887385, poza pasem trasy) — do ADR 0077.
- Klin przed węzłem n1847044938 ma spadek poprzeczny do ~10 % (0,6 m na 5,8 m na początku łaty 45 m); to powierzchnia
  wyłączona z ruchu (na zdjęciu malowana), nie pas.
- Szerokości jezdni przy włączeniach nadal pochodzą z liczby pasów OSM (pas włączenia za węzłem n1847044938 kończy
  się ~40 m wcześniej niż na zdjęciu) — to zakres ADR 0075 / 0077 (krawędź p95 2,50 m, cel 0,75 m).
- Kod przesunięcia (`_push_abreast`, poszerzenie) zostaje za flagą `ABREAST_PUSH` do odtworzenia nakładek
  (`scripts/abreast_overlay.py`, `abreast_vs_ortho.py` włączają ją lokalnie); do usunięcia, gdy ADR 0077 zamknie kliny.
- Widoczne na kamerach rundy 3, nienaprawione (zakres ADR 0077 / oznakowanie):
  - łata 45 m przy n1847044938 (p0_ma012_top, au_r_s1380/1400) i jezdnia przy (−782, 77) (p0_kerb_merge_top) to goły
    asfalt bez linii pasów; na ortofoto klin jest powierzchnią wyłączoną z ruchu malowaną w jodełkę (P-21) — brak
    tego oznakowania i ciągłości linii przez łatę;
  - strzałka „prosto + w prawo” na p0_fork_putry_eye leży na linii krawędziowej pasa (pas w klinie węższy od strzałki);
  - nos klina trawy przy włączeniu z Ronda Bieżeństwa (au_f_s0620, E 324 N −575): teren 0,04–0,13 m poniżej jezdni,
    więc lico krawężnika ma tam 0,16–0,25 m (pomiar `scripts/xsec.py`, siatka renderu `terrain_lod0`); poza jezdnią;
  - nakładające się jezdnie serwisowe przy n1882887385 (p0_n1882887385_top): linie krawędziowe jednej jezdni biegną
    przez drugą.
- WORKING_VALUE: `CORNER_FILL_DZ_M` 0,15 m, `FLUSH_FILL_MAX_M` 1,5 m, `ABREAST_TIE_DOT` 0,7, `LANE_CHANGE_RATIO` 12, `JOINT_ROUND_M` 4 / 10 m,
  `CULL_RING_M` 0,30 m, wysokości słupów `standards.GROUND_PROP_H`.
