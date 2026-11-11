# ADR 0100: Węzły r3 — P-21 jako analityczne czworokąty, nawierzchnie autorskie, oznakowanie Putry N / MA-010 / rozdział wsch.

Status: przyjęty (world-builder, junctions-r3), 2026-11-11. Wynika z `docs/reports/visual/REVIEW-2026-11-11-s10-0095.md`
(„Lista poprawek na węzły r3”). Powiązane: ADR 0077, 0086 (kontrakt `_Tint` — nietknięty), 0093, 0095. Dowody:
`artifacts/junctions-r3/` (REPORT.md, zones*/ = ortofoto | ortofoto + kwadraty P-21, trace/ = wycinki z siatką 1 m,
plan_*/ = ortofoto | generator, renders_*/ = kamery kontrolne Unity).

## Kontekst
- **P-21 połamany (P0-1).** `through_lines.paint_zones` sumował obramowanie i pasy w jeden wielokąt shapely, ciął go
  `constrained_delaunay` z segmentacją 1,5 m i drapował tylko w narożnikach trójkątów. Długie trójkąty nad wypukłą
  (spadek poprzeczny) jezdnią i nad nakładającymi się łatami/taśmami chowały się pod asfalt między narożnikami
  (zmierzone b0: do 2,6 cm pod powierzchnią przy uniesieniu farby 6 mm) — z góry i z oczu: fragmenty, „Z”, same ramki.
  Ten sam błąd (siatka 1 m) dawał ciemne plamki w belkach zebr autorskich (`painted_crossing`).
- Dodatkowo kąty i obrysy pól nie zgadzały się z ortofoto: oś `chevron_axis` przy s 1440 leżała na jednej krawędzi pola
  (wszystkie pasy po jednej stronie), wielokąt nosa s 1440 1–1,5 m na SW od malowania, pasmo s 1440 to na ortofoto pasy
  równoległe pod ~29° do osi wiszące na jednej linii obramowania (recenzja nazwała je jodełką), jodełka DK8 ma wierzchołki
  do nosa (generator rysował odwrotnie) i sięga E −806, a w małych polach przy n10015785253 rozstaw pasów to ~0,5 m.
- **Putry N, MA-010 (P0-2):** łaty przejazdu przez pas dzielący i dolny pierścień bez linii (pary „na wprost” krzyżują się
  = skrzyżowanie, generator nic nie maluje). Plac przy przejeździe Putry N to kostka, generator kładł asfalt.
- **Rozdział jezdni wsch. (P1-2/P1-3):** główna (2 pasy) i łącznica (OSM `lanes=3`) startują z jednego węzła
  n1832975577 jako jedna łata 14,9 m z jedną linią przebiegającą ukośnie przez całą jezdnię.
- **Materiały (P1-5..P1-8):** murki 0,6 m wzdłuż pasa dzielącego DK8, szwy łat, smugi na pasie betonu.

## Decyzja
1. **`roads/p21_hatch.py` — P-21 analitycznie.** Każdy pas = pudełko ∩ wielokąt pola zredukowane do czworokąta między
   dwiema liniami krawędzi pasa (części < 0,35 m na którejkolwiek krawędzi = fragment przy wierzchołku, odrzucany).
   Obramowanie = 1 czworokąt na krawędź wielokąta, wewnętrzne narożniki fazowane (mitre ≤ 3 × szerokość). Jeden kąt na
   pole: `chevron_axis` (łamana; pasy lustrzane, `chevron_apex: tip|nose` z ortofoto) albo `axis` + `stripe_rel_deg`;
   `stripe_az_deg` (bezwzględny) dalej czytany. `stripe_w_m`, `stripe_gap_m` per pole (odczyt z ortofoto), `border_edges`
   — które krawędzie mają linię obramowania. Test `tests/gis/test_p21_hatch.py`: każdy pas i każdy odcinek obramowania
   to wypukły czworokąt, boki pasa równoległe (< 0,5°), kierunek pasa = kierunek jego pola (< 0,5°), pasy się nie
   nakładają, nie wychodzą poza pole; jodełka symetryczna względem osi.
2. **Drapowanie bez zanurzeń (`p21_hatch.drape_lift`)**: komórki ≤ 0,35 m wzdłuż czworokąta; w każdej komórce próbka
   powierzchni w środku i środkach krawędzi; narożniki podnoszone o największą nadwyżkę powierzchni nad płaszczyzną farby;
   komórka nad uskokiem > 3 cm odrzucana (liczona). To samo dla `painted_crossing` (belki zebr, kwadraty P-11 jako
   czworokąty) i `painted_arrow` (triangulacja 0,5 m). Raport `painted_zones[].max_lift_m`, test: ≤ 3 cm.
3. **`kind: paved_apron`** (`roads/aprons.py`, na początku `markings.build_markings`): trójkąty jezdni w warstwie `road`
   przycięte analitycznie do wielokąta (shapely, triangulacja kawałków), część wewnątrz dostaje materiał nawierzchni
   (`sett | paving | concrete | asphalt`), z, UV, UV1, COL interpolowane barycentrycznie — powierzchnia nie przesuwa się,
   kolizja (osobna siatka) bez zmian. UV kostki = metry w planie. Test `tests/gis/test_aprons.py` (pole i wysokości).
4. **`kind: guardrail`** (`streetscape/furniture.py`, addytywnie): bariera W na słupkach po łamanej autorskiej na
   wyspach rozdzielających (generator stawia bariery tylko z reguł mostu / pasa dzielącego / nasypu).
5. **Krawężnik pasa dzielącego** (`network.assign_sides`): stacja wiejska przerobiona na miejską medianę z krawężnikiem
   zachowywała głębokość rowu (0,60 m) jako wysokość krawężnika → teraz `KERB_HEIGHT` 0,13 m.
6. **Szwy łat**: materiał łaty skrzyżowania = większość materiałów silnikowych ramion (`standards.surface_material`, z
   udziałem „świeżego” SMA), a nie surowego materiału sekcji — łaty między dwoma ramionami SMA nie są już jaśniejszymi
   prostokątami w poprzek jezdni.
7. **Pas betonu przy krawężniku** (`meshing._emit_strip`): wiersz `curb_concrete` szerszy niż 0,4 m (kod chodnika 0) dostawał
   UV górnej płaszczyzny krawężnika (u wzdłuż, v w poprzek, fugi co 1 m) — smugi w poprzek pasa E −830…−770 N 82; teraz
   UV planu w metrach i materiał `sidewalk_paving` (render b6: sama zmiana UV zostawiała smugi tekstury krawężnika).
8. Override'y z ortofoto (wszystkie z `reason` i wycinkiem w `artifacts/junctions-r3/trace|zones*|plan*`): pola P-21
   (DK8 przód, s1440 nos i pasmo, n10015785253 × 3), Putry N (2 × P-1, 2 × P-7a, P-7b, plac `paved_apron` paving), MA-010
   (P-1 pierścienia, P-1 wlotu ramienia płd.), zatoka s 1060 (2 × `paved_apron` sett na końcach), rozdział wsch.
   (`paint_clear` ukośnej linii, P-1, P-2b, jodełka, wyspa, bariera, P-21 boczne, P-1e), bariera na wyspie E −782,
   n10015785253 SE (4 × `paint_clear` strzałek na wprost, 2 strzałki naprowadzające), s610 (4 pola: kąty 19–20°, gęste),
   s1440 ramp (ukośne −30° od osi zamiast drabiny). Kamery: `r3_*` (6).
9. **Bariery** (`streetscape/furniture._dedup_guardrail`): run bariery w promieniu 1 m od już zbudowanej nie powstaje drugi
   raz (24 m pominięte w regionie).

## Wynik
### Liczby (build b5, 2026-11-11, `bialystok-industrial-c`; „przed” = main 503c89ae / r2 b12)
| miara | przed | po |
|---|---|---|
| P-21: farba pod asfaltem między narożnikami (powierzchnia nad płaszczyzną farby) | do 2,6 cm na polach (b0, komórki 0,5 m bez podniesienia; 11,7 cm na uskoku s1440 ramp), trójkąty CDT 1,5 m — więcej | 0 w próbkach (podniesienie ≤ 3,0 cm, komórki nad uskokiem > 3 cm odrzucone) |
| P-21: pola / pasy (czworokąty) | 12 pól, pasy jako wycinki wielokąta | 14 pól, 301 pasów, każdy czworokąt wypukły, równoległy (test 17/17) |
| farba autorska `painted_line` / `painted_arrow` / `painted_crossing` zbudowana | 8 | 20 / 20 |
| override'y zastosowane / nieaktualne | 69 / 0 | 94 / 0 |
| wzniesienie krawężnika nad jezdnią ≥ 0,25 m (`kerb_rise.py`) | 0,60 m na pasie dzielącym DK8 E −888…−768 i in. (wszystkie pionowe ściany krawężnika 0,25–0,40 m: 52) | 1 (j:n1847317049:corner0, E −983 N 66,5, poza trasą); ściany 0,25–0,40 m: 0 |
| ścianki terenu > 0,15 m (`terrain_walls_qa`) | 3 | 3 (max 0,345 m) |
| fidelity trasy: krawędź jezdni vs ortofoto p50 / p95 | 0,36 / 2,30 m | 0,36 / 2,304 m (bez zmian — geometria jezdni nietknięta) |
| bariery: punkty runów pominięte jako duplikat < 1 m | — | 24 m (bariery autorskie 36 m) |
| `pytest tests/gis` | 356 passed, 1 xfailed (r2) | b3: 387 passed / 1 failed (szwy, naprawione); b4: `test_world_roads` 15/15, testy kluczowe 51/51 |
| swept path G3-A wide / lane, G3-B (min. prześwit opon) | −0,10 / −1,12, −0,14 m | −0,10 / −1,12, −0,14 m (b3, bez zmian); RING-B +1,61 m |
| `pytest tests/physics tests/gate3` | 47 passed, 1 failed (0082) | 47 passed, 1 failed (ta sama znana `test_generator_reproduces_committed_scenarios`) |
| import-region (pamięć świata) | Low 110,0 / High 237,9 MB (r2) | Low 111,5 / High 240,0 MB (b10; markings 2,8 MB, paved 3,2 MB) |
| PlayMode `WorldCRouteTests|WorldCBarrierTests` | 3/3: 40 t max \|dv\|/krok 0,121 m/s (s 361), solo 0,080 | 3/3 (b8): 0,121 m/s (s 361), solo 0,080 m/s — bez zmian |

Kontrola wizualna: rendery 44 kamer `artifacts/junctions-r3/renders_b6_high/`, `renders_b8_high/` (High overcast),
`renders_b8_low/` (Low clear), `renders_b10_high/` (stan końcowy), wycinki ≤ 960 px `view_b6/`, `view_b8/`; plany
ortofoto | generator `plan_b2/`…`plan_b10/`; pola P-21 na ortofoto `zones2/`. Obejrzane: p0_n10015785253_top,
p0_kerb_merge_top (+ wycinek), r3_e_split_eye/top, top_putry_n, eye_putry_n (High i Low), top_ma010, r3_ma010_eye,
r2_n100_eye, r3_n100_se_eye, r2_bay_eye, top_merge, r2_kerb_merge_main_eye, p0_kerb_merge_eye, top_s1440,
r2_fork_link_eye, top_s610.


## Otwarte
1. **Geometria nie przebudowana tam, gdzie OSM jest daleko od ortofoto**: rozdział jezdni wsch. (jezdnia 2 m za szeroka od
   południa, N 48,8 zamiast 51,6; wyspa tylko do E −788, dalej generator ma pas łącznicy tam, gdzie na ortofoto jest
   wyspa — przedłużenie wpakowałoby wyspę w pas), MA-010 (łata dolnego pierścienia szersza niż pierścień, 1,5–2,5 m
   od ortofoto), n10015785253 jezdnia płd. (kończący się 4. pas i załom krawężnika E −247 N −253 — zrobione tylko
   strzałki), pole `s1440-diverge-p21` (178 komórek poza jezdnią generatora).
2. **P1-7 częściowo**: wysokość krawężnika naprawiona; tekstura „marmurkowa”, moduł 1 m ze spoiną i teren do korony
   (kołnierz 0,5 m widoczny tam, gdzie teren mediany leży niżej) — nie ruszone. Samotny murek przed łącznicą s 1440 —
   nie sprawdzony po zmianie.
3. **P1-9** separator łącznica/dojazd wiaduktu (trawa → kostka z barierą) — nie zrobione (wyspa autorska leży na jezdni,
   tu jest trawa poza jezdnią). **P1-11** zygzak trawy median — obrót / przesunięcie UV pasków trawy hashem nie zmienił
   wzoru na renderze b6 (cofnięte): przyczyna w teksturze / masce shadera (`WorldSurface.shader`, plik wspólny) — nie ruszone. **P1-10** — tylko deduplikacja < 1 m (24 m); „słupek-skrzynka” nie zidentyfikowany; w `p0_kerb_merge_eye`
   nadal krzyżują się balustrada wiaduktu i bariery (odstęp > 1 m, różne systemy).
4. **P2**: P2-1 (skok linii) nie ruszone; P2-2 (podwójne linie na wiadukcie) — `mk_near.py` na b4 pokazuje jedną P-7b
   na krawędź; drugi pas na planie to kapa / krawężnik w kolorze planview — do potwierdzenia na renderze; P2-3 (czerwone
   przejazdy, sygnalizator), P2-4 (filary) — nie ruszone; P2-5 — dodane kamery `r3_*`.
5. Kąty i rozstawy P-21 (35° jodełki, 29° pasma s 1440, 19–20° s 610, pasy 0,25–0,30 m co 0,5–0,85 m) to odczyt z
   ortofoto 0,08 m — WORKING_VALUE; zgodność z rozporządzeniem (Dz.U. 2019 poz. 2311, zał. 2) UNVERIFIED.
6. Ocena `visual-critic` i zrzut z telefonu — dla lidera (agent nie tworzy subagentów i nie używa telefonów).


## Pliki wspólne i przewidywane konflikty
- Nie dotknięte: `WorldPbrMaterials.cs`, `WorldPBR.shader`, `WorldSurface.shader`, `streetscape/materials.py` (kontrakt `_Tint`
  ADR 0086 bez zmian), zabudowa (agent 0097).
- Zmienione addytywnie: `roads/through_lines.py` (`paint_zones` przepisane — konflikt tylko z inną zmianą P-21),
  `roads/authored_paint.py` (`_drape_polygon`), `roads/markings.py` (wywołanie `aprons.apply`), `roads/meshing.py`
  (`_patch_mat`, `_emit_strip` — r2 ostrzegał o konflikcie w `_emit_strip` z main, tu zmiana to 6 linii w gałęzi UV),
  `roads/network.py` (1 linia po regule mediany), `streetscape/furniture.py` (`guardrails`: dedup + bariery autorskie;
  jeśli 0097 zmienia `furniture.py`, konflikt możliwy tylko w `guardrails`).
- `Data/Regions/bialystok-industrial-c/overrides.yaml` (dopisane bloki + zmiany pól P-21) i `junctions_cameras.json` (+6 kamer).
