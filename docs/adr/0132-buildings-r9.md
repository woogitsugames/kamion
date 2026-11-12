# ADR 0132: Zabudowa r9 — posesje jednorodzinne bliżej zdjęć (drzewa z koron ortofoto, krzewy przy płotach, żywopłot o zaokrąglonym przekroju, drzewka i krzewy jako bryły, artefakty płotu / skrzynki, wiek działek, ramki LOD1)

Status: propozycja (world-builder, gałąź `buildings-r9`, z main `f8b85fa2`), 2026-11-12. Kontynuacja ADR 0124; odpowiedź na
`docs/reports/visual/REVIEW-2026-11-12-s12-0124.md` (P1-a…e, P2-c/d/e). Referencje: `docs/refs/posesje-bialystok.md`
(Mapillary CC BY-SA, Commons — oglądane, żaden piksel nie wchodzi do tekstur). Nic z telefonu. LICZBY: sekcja „Liczby” —
wszystko, czego nie zmierzono w silniku, jest oznaczone.

## Decyzja
1. **Wysoka zieleń z danych — korony z ortofotomapy** (`streetscape/plot_canopy.py` → `Data/Regions/<id>/plot_canopy.json`, w gicie).
   BDOT10k nie ma drzew ogrodowych, NMPT / „Modele 3D drzew” nie są w pipeline; mozaika GUGiK 0,25 m (lot letni) pokazuje każdą
   koronę. Ortofoto pozostaje referencją (docs/05 §3): powstają z niej wyłącznie POZYCJE i PROMIENIE koron, żaden piksel nie
   trafia do gry. Metoda: roślinność = chromatyczność zieleni; korona = roślinność SZORSTKA (odchylenie jasności w oknie
   2,25 m) i niezbyt jasna — łąka i podlewany trawnik są równie zielone, ale gładkie; korony = maksima transformaty odległości
   maski (środek + promień 0,7–6,5 m), zachłannie od największej; iglaste = ciemne i niebieskawe. Tylko ≤ 45 m od domu
   jednorodzinnego, poza lasami BDOT i obrysami budynków. Progi: WORKING_VALUE strojone na oko na nakładkach
   (`artifacts/buildings-r9/canopy/*.jpg`); znane braki: drzewa o szarej, mało nasyconej koronie bywają pominięte.
2. **Korona → roślina** (`plots.build`): promień ≥ 2,3 m → **instancja istniejącego prototypu drzewa** (`tree_birch / linden /
   maple / pine / alder`, wybór z hasza — gatunku z RGB nie da się odczytać; wysokość 3,6 r + 3 m w zakresie gatunku):
   wiatr, LOD-y i impostor jak każde drzewo regionu, **zero nowych materiałów i prototypów**; 1,25–2,3 m → drzewko w kicie
   (promień korony = promień z ortofoto); < 1,25 m → krzew; iglaste → świerk / tuja kitu. Pień odsuwany od domu (≥ 1,8 m),
   podjazdu i linii płotu (do 2,4 m), inaczej korona jest pomijana. Pas przed płotem (≤ 6 m od frontu, poza działkami):
   tylko duże korony liściaste, ≥ 0,8 m od śladu drogi i ≥ 3 m od jezdni. Drzewo bliżej niż 2,5 m od drzewa, które region
   już tam ma (BDOT / OSM), odpada. Bez produktu `plot_canopy.json` działa reguła udziałów z ADR 0124 (duże drzewo też
   jako instancja).
3. **Krzewy zarastające płot**: reguła wg wieku działki (old 2–4, prl 1–3, new 0–1), krzew 0,3–0,55 m za linią płotu,
   wyższy od płotu o 0,25–1,15 m, łącznie ≤ 1/3 długości przęsła, nie na froncie z żywopłotem.
4. **Krzew i drzewko jako bryła** (P1-e, P1-a): ciemny rdzeń (kopuła z rzędu liści żywopłotu, głęboko we własnym cieniu) +
   karty gałązek leżące NA powierzchni korony, zachodzące na siebie dookoła, + „namiot” dwóch kart nad środkiem; drzewko ma
   pień rozwidlony na trzy konary i dwa piętra kart. Koniec dwóch / trzech skrzyżowanych kart. Krzew ≤ 36 trójkątów (było 4),
   drzewko ≤ 80 (było 14).
5. **Żywopłot** (P1-b): przekrój zaokrąglony (stopa węższa od barków, barki zaokrąglone do linii grzbietu — bez półki
   wystającej poza boki), stacje co 1,28 m z wędrującą wysokością (fala ±6 cm + ±5 cm), grubością (±12 %) i osią (±5 cm),
   zwężone końce z zaślepką, liście w skali 1 : 1 (bok w dwóch pasmach v — rząd atlasu ma 1,5 m i nie kafelkuje w pionie),
   pędy nad grzbietem (postrzępiony górny pas rzędu na pionowej karcie).
6. **Okluzja własna rośliny** w `Kamion/World PlotKit`: długość wektora normalnej liści w COLOR_0 (1 = oświetlona skóra,
   ~0,4 = stopa żywopłotu, ~0,26 = rdzeń korony) mnoży albedo. Wstecznie zgodne (dotychczasowe normalne mają długość 1).
7. **Artefakty** (P1-d): odcinek płotu bocznego / tylnego krótszy niż 3,2 m, który jednym końcem nie łączy się z niczym
   (inny odcinek, słupek bramy, ściana / krawędź drogi, istniejące ogrodzenie), nie jest budowany (`r16_drive_3`); front
   zostaje zamknięty do narożnika. Skrzynka na listy 24 × 32 × 9 cm na słupku 12 × 12 cm z daszkiem, nigdy w kolorze ramy
   ogrodzenia (`r16_drive_0`: czarna skrzynka na czarnym słupku 10 cm na tle czarnych lameli).
8. **„Wiata” (P1-c) nie istnieje**: kadr z recenzji (`r16_door_3`) to kamera stojąca WEWNĄTRZ domu — daszek nad drzwiami,
   ościeża okien, okap i grunt pod budynkiem widziane od środka przez ściany z cullingiem tylnych ścian. Generator nie stawia
   wiat na działkach. Poprawka dotyczy kamer (`cams_r16.py`: żadna kamera przeglądowa w obrysie budynku + 0,6 m); wiaty jako
   nowego obiektu nie dodano (poza zakresem rundy).
9. **Wiek działek** (P2-e): na starszych działkach bez garażu podjazd to **dwa pasy pod koła z trawą między nimi** (old 60 %,
   prl 25 %; ten sam materiał kostki — bez nowego draw); tint starzenia old 0,80 → 0,72 (± 0,16), przechył słupków 3° → 4,5°.
   Spłowiałych tynków domów NIE zrobiono (materiały ścian są wspólne dla chunka; osobny odcień = nowy draw).
10. **Otwory LOD1 domów** (P2-d): ramka 7 cm wokół ciemnej szyby, w tej samej płaszczyźnie (4 quady, bez nakładania — bez
    z-fightingu), w jasnym materiale, który LOD1 danego chunka już rysuje i który nie jest ścianą tego domu
    (`plaster_white` → `plaster_light` → `downpipe`).
11. **Zjazd nie szerszy od bramy** (P2-c): płyta zjazdu ma szerokość otworu bramy (3,5 / 4,0 m) — trapez w `r16_drive_0/3`
    wynika ze skosu drogi względem bramy i z dojścia od furtki przyległego do zjazdu; bez zmiany w tej rundzie.
12. **r2 (po obejrzeniu r1)**: instancje drzew ogrodowych — 4 gatunki × JEDEN wariant modelu (`INST_VARIANT`; r1: 5 × 3,
    każdy prototyp × LOD w kadrze to 1–3 instancjonowane draw — najgorsza kamera Low +19); grupa brama + furtka bliżej
    niż 0,9 m od narożnika frontu jest dosuwana do narożnika (słupek bramy = słupek narożny; `r16_drive_3`), chyba że
    stanęłaby wtedy w zasięgu ogrodzenia sąsiada o współliniowym froncie (`_Near.parallel` skasowałby bramę — wykryte testem
    r7); ramka LOD1 12 cm i tylko tam, gdzie KAŻDA komórka chunka dotknięta przez dom ma już ten materiał (r1: +1 submesh).
13. **Kit posesji dla Low / Medium (sesja 13, polecenie lidera: A16 Low nie mieści się w GPU, zieleń nie może go pogorszyć)**:
    `Kit.low` — każda część kitu jest wspólna, tylko-High albo tylko-Low; generator pisze drugą warstwę `plots_low`, która w
    `chunk_*.low.glb` trafia pod węzeł `plots` (High GLB bez zmian; importer i scena bez zmian — ta sama nazwa węzła, ten sam
    materiał, ten sam jeden draw na chunk). W Low: ogrodzenia, bramy, żywopłot, świerki, kosze 1 : 1; tuje w rzędach
    `thuja_lite` (rdzeń 4-boczny + jedna karta sylwetki, 14 trójkątów zamiast 39); tuje pojedyncze 2 karty (4);
    drzewka `fruit_tree_lite` (pień z dwóch pasków + 3 karty korony, 10 zamiast 65); krzewy ogrodowe, krzewy zarastające
    płot i byliny — tylko High. Wysokość i obrys roślin lite = pełnych (ten sam hasz), więc sylwetka ulicy z kabiny jest ta
    sama; z bliska na Low widać skrzyżowane karty (świadomy koszt).
14. **Instancje dużych drzew ogrodowych są wspólne dla Low i High** (jeden `WorldInstanceSet`; filtr per tier wymagałby
    zmian w `World/Import/InstanceImporter` i `World/Runtime/WorldInstances` — poza własnością tej gałęzi). Koszt na Low
    zmierzony niżej (kamery trasy i kabiny: −2…+3 draw; dwie kamery uliczek domów: +10 / +14). Decyzja lidera, czy to
    akceptowalne; tańsze warianty: próg `plots.INST_R_M` w górę albo pole „tylko High” w instancji (importer).
15. **Ramki otworów LOD1 (pkt 10) WYŁĄCZONE** (`buildings_mesh.LOD1_HOUSE_FRAME_M = 0.0`; 0.12 włącza): r2 zmierzył
    +31 432 trójkąty w wariancie Low regionu (najgorsza kamera uliczki +29 k, 0 draw), a A16 Low nie mieści się w budżecie
    GPU. Wizualnie ramki poprawiają domy na Low (`r2/sheet_low_a.jpg` vs `base/sheet_low_a.jpg`) — do włączenia, gdy Low
    odzyska zapas.
16. **r4 — budżet High, decyzja lidera B** (`plots.NEAR_FRONT_M = 12`): pełne bryły roślin (krzew, drzewko, tuja) tylko
    ≤ 12 m od frontu działki — tam, skąd patrzy kierowca; głębiej w działce wersje lite wspólne z Low (krzew daleki: 2 karty,
    tylko High). Odchudzone rdzenie (1 pas), drzewko ~48 trójkątów, tuja w rzędzie 16, stacje żywopłotu co 1,92 m (było
    1,28 m). Rekordy instancji drzew ogrodowych mają pole `"tier": "high"` (importer ignoruje nieznane pola — bez zmiany
    zachowania do czasu filtra per tier z sekcji niżej). `INST_R_M` 2,3 m bez zmian.
17. **Drzewa ogrodowe nie są rysowane na Low (r4b, decyzja lidera: +26 draw instancjonowanych na Low nieakceptowalne, A16 Low
    brakuje ~0,7 ms — ADR 0136; zgoda lidera na zmianę importera)**. Rekord instancji z `"tier": "high"` →
    `WorldInstanceSet.Run.highOnly`; `WorldInstances.Render` pomija takie runy, gdy aktywny profil to **Low**
    (`WorldInstances.DrawsHighOnly`). Medium i wyżej oraz narzędzia bez zastosowanego profilu rysują je: Medium ma inny
    budżet niż A16 Low i bez tych drzew ulice domów nie mają żadnej wysokiej zieleni — koszt na Medium NIE zmierzony
    na telefonie (UNVERIFIED, WORKING_VALUE; przełącznik to jedna linia w `DrawsHighOnly`). Żeby Low rysował dokładnie to,
    co bez tych drzew, instancje high-only mają własne komórki (`InstanceImporter.HighOnlyCellKey`, bit 51 — rozłączne
    z komórkami zwykłymi i Fab) i są zapisywane za macierzami zwykłymi (ten sam mechanizm co detale Fab,
    `LegacyStorageOrder`): te same obrysy komórek, runy i indeksy przerzedzania lasu. Instancja high-only nie dostaje
    collidera (kolizja nie może zależeć od profilu). Brak pola `tier` = wszystkie profile (zgodne wstecz, stare assety:
    `highOnly = false`). Test EditMode `HighOnlyInstanceTests` (5 testów). Na Low ulice domów zostają z zielenią kitu
    (żywopłot, świerki, tuje i drzewka lite) — świadomy koszt.

WORKING_VALUE: wszystkie progi, udziały i wymiary powyżej.

## Liczby (zmierzone; edytor = oszacowanie `visual-qa` przed SRP batchingiem, NIE telefon)
- Dane: `plot_canopy.json` 3500 koron ≤ 45 m od domów (2070 drzew, 426 iglastych, pokrycie 19,8 %). Działki 99: instancje
  drzew 117 na 60 działkach (brzoza 38, klon 36, lipa 31, sosna 12; h 11,3–17,5 m; 34 w pasie przed płotem), drzewka kitu 193,
  świerki 53, tuje 521, krzewy 163 + 108 zarastających płot + 213 z reguły, żywopłot 479 m, bramy 43, furtki 132, podjazdy
  „dwa pasy” 11, odcinki płotu usunięte 4, płot w strefie drzwi 0.
- Kit posesji (trójkąty regionu): ADR 0124 52 406 → High 94 172 (płot 20,6 k, bramy 11,9 k, tuje w rzędach 17,2 k, drzewka
  12,5 k, żywopłot 9,3 k, krzewy 17,0 k, tuje pojedyncze 3,2 k, byliny 1,2 k, świerki 0,7 k, kosze 0,6 k) / **Low 51 508**
  (tuje w rzędach 6,2 k, drzewka 1,9 k, tuje pojedyncze 0,3 k; krzewy i byliny 0).
- Region r2 (przed scaleniem main, kod `e553c32a2`): High 4070 submeshy / 14,293 mln; Low 3052 submeshy / 4,604 mln
  (main z integracji e: 3052 / 4,572 mln; różnica Low = +31,4 k ramki LOD1 — potem wyłączone, −0,9 k kit, +0,6 k grunt działek).
- Kamery kontrolne Low overcast, 67 kamer, r2 vs import main z 14:03 (`artifacts/buildings-r9/r2/budget_low.txt`):
  draw MeshRenderer 18 265 → 18 265 (**+0**), cienie 4623 → 4622, draw instancjonowane 18 673 → 18 696 (+23; najgorsze
  `r10_shed_2` 176 → 190, `r10_house_2` 105 → 115, pozostałe −2…+4), instancje +81 (najw. +18), trójkąty siatek +258 k w sumie
  (najw. +29 k — ramki LOD1, wyłączone w r3), trójkąty instancji +10 k w sumie (najw. +6 k).
- **r3 (po scaleniu main `b2f86cb7c`, ramki LOD1 wyłączone; kod `3d992ddb2` + poprawka determinizmu)**: `build_world` exit 0
  (497 s), region High 4070 submeshy / 14 272 032 trójkąty, **Low 3050 / 4 582 476**; kit posesji High 94 172 / **Low 51 508**
  (0124: 52 406); instancje drzew ogrodowych 117 (34 w pasie przed płotem). Import 776 s, 0 `error CS` / `Shader error`.
  EditMode **407 / 407**. Fidelity exit 0. Pytest gis: **819 passed, 3 failed, 1 xfailed** — (1) `test_determinism`
  (iteracja po `set` w kodzie ramek LOD1) — POPRAWIONE (`sorted`, wynik bez zmian, test zielony); (2) i (3) budżet
  trójkątów kadru HIGH — patrz „Otwarte: budżet High”.
- Kamery kontrolne **Low overcast, 67 kamer, r3 vs baza** (`r3/budget_low.txt`; baza = import main z 14:03, czyli SPRZED
  scalenia `b2f86cb7c` — różnica zawiera też treść main z s13): draw MeshRenderer 18 265 → 18 276 (+11, najw. +2), cienie
  4623 → 4598 (−25), draw instancjonowane 18 673 → 18 859 (+186; najw. `r10_fence_3` +40, `r10_shed_2` +22), instancje +150,
  trójkąty siatek 17 768 k → 17 828 k (+60 k w sumie, najw. kamera +3 k), trójkąty instancji +165 k.
  **Rozdzielenie wkładu** (r2 = ten sam kod posesji PRZED scaleniem main, r3 = PO): r3 − r2 = instancjonowane +163, instancje
  +69, trójkąty instancji +155 k, MeshRenderer +11 — to treść main (między r2 a r3 w tej gałęzi zmieniło się tylko wyłączenie
  ramek: trójkąty siatek −198 k; liczba drzew ogrodowych 117 = 117). **Wkład 0132 na Low = pomiar r2 vs baza: MeshRenderer
  +0, cienie −1, instancjonowane +23 (67 kamer; kamery trasy / kabiny −2…+3; uliczki domów `r10_shed_2` +14,
  `r10_house_2` +10), instancje +81, trójkąty instancji +10 k; trójkąty siatek po wyłączeniu ramek ≈ 0** (kit −0,9 k,
  grunt działek +0,6 k w regionie). Estymata kadru generatora, Low (`streetscape_qa.json`, 23 kamery): −1,7 k…+1,4 k
  trójkątów na kamerę względem main (`stretch_04` 946 528 → 946 920).
- **r4 (decyzja B, po scaleniu main `6d511d49c`; kod `7d675d793`; baza = `base2`, czyli TREŚĆ main `1b002a730` zbudowana
  i zaimportowana w tym samym worktree tego samego dnia — różnica to wyłącznie 0132)**: `build_world` exit 0 (616 s), region
  High 4071 submeshy / 14 239 334 trójkąty, **Low 3051 / 4 580 678**; kit posesji **High 59 867** (r3 94 172; 0124 52 406:
  płot 20,6 k, bramy 11,9 k, żywopłot 6,6 k, tuje w rzędach 6,5 k, drzewka 4,0 k, krzewy 2,9 k + 1,8 k, zarastanie 1,9 k,
  byliny 1,2 k, tuje pojedyncze 1,1 k, świerki 0,7 k, kosze 0,6 k) / **Low 48 884** (r3 51 508). Fidelity exit 0. Import
  601 s, 0 `error CS` / `Shader error`.
- **Estymata kadru HIGH r4** (`r4/streetscape_qa.json`, próg 2 000 000): `stretch_04` **1 995 296** (base2 1 987 612, r3
  2 027 946; zapas 4 704), `route_onramp_andersa_above` **1 986 990** (base2 1 982 699; zapas 13 010). Low: 947 654 /
  852 975 (base2 947 656 / 852 977).
- **Kamery kontrolne Low overcast, 67 kamer, r4 vs base2** (`r4/budget_low.txt`): draw MeshRenderer 18 282 → 18 282 (**+0**),
  cienie 4603 → 4602 (−1), draw instancjonowane 18 859 → 18 885 (**+26**: `r10_shed_2` 187 → 201, `r10_house_2` 106 → 116,
  pozostałe ≤ +3; najlepsze −3), instancje 18 220 → 18 346 (+126), trójkąty siatek 17 823 k → 17 814 k (**−9 k**), trójkąty
  instancji 2190 k → 2202 k (+12 k, najw. kamera +6 k). Cały przyrost to 117 instancji drzew ogrodowych (wspólny
  `WorldInstanceSet`, pkt 14); geometria siatek Low jest lżejsza niż w main.
- **Testy r4**: pytest `tests/gis` **837 passed, 1 xfailed** (1060 s; oba testy budżetu High zielone); EditMode
  **408 / 408** (`artifacts/tests/editmode-20261112-213413.xml`).
- Pary r4 obejrzane: `artifacts/buildings-r9/pairs_r4/sheet_base_hc.jpg` (base2 | r4, High, 8 kamer), `sheet_base_low.jpg`,
  `sheet_low.jpg` (kamery kontrolne Low), `sheet_ref.jpg` (r4 | zdjęcie). Z ulicy r4 nie różni się od r3 (pełne bryły
  ≤ 12 m od frontu); z lotu (`r17_over_0`) w głębi działek widać karty.
- **r4b (pkt 17: drzewa ogrodowe pomijane na Low; ponowny import produktów r4 po scaleniu `origin/main` 41e6fd89f, kod
  `f49e823ad`)**: import 579 s, 0 `error CS` / `Shader error`; EditMode **444 / 444** (w tym 5 × `HighOnlyInstanceTests`;
  `artifacts/tests/editmode-20261112-220907.xml`). Kamery kontrolne Low overcast, 67 kamer:
  (a) **sam filtr** — ten sam import i kod, filtr wyłączony → włączony (`r4b/budget_low_filter_only.txt`): draw MeshRenderer
  +0, cienie +0, trójkąty siatek +0, draw instancjonowane 14 453 → 14 433 (**−20**; `r10_shed_2` −6, `r10_house_2` −5),
  instancje −72, trójkąty instancji −6 k; żadna kamera nie zyskała ani jednego draw.
  (b) r4b vs base2 (`r4b/budget_low.txt`): `r10_house_2` 106 → **107** (+1; r4: 116), `r10_house_1` 148 → 147,
  `r10_fence_2` 205 → 205, `r10_shed_2` 187 → 113; najgorsza kamera sumy MeshRenderer + instancjonowane **+1**. UWAGA: sumy
  tego porównania (MeshRenderer −906, instancjonowane −4426) NIE są zasługą 0132 — base2 renderowano kodem C# sprzed
  scalenia, a `origin/main` wniósł ADR 0136 r2 (cull pojazdów Low 150 m, zmiany `QualityProfile`); czysty wkład 0132 na Low
  po filtrze = (a) odjęte od r4, czyli brak instancji drzew ogrodowych; zostaje kit Low (trójkąty siatek −9 k względem main).
- Pary r4b obejrzane (`pairs_r4b/sheet.jpg`): Low base2 | r4b — bez instancji drzew ogrodowych (`r17_over_0`, `r17_street_0a`),
  kabina bez zmian; Low | High r4b — na High drzewa są.
- Telefon: NIE mierzone (UNVERIFIED). Koszt GPU instancji drzew ogrodowych na A16 Low nieznany.

## Koszt drzew ogrodowych na Low i propozycja filtra per tier (poza własnością gałęzi — tylko propozycja)
- Kontekst: ADR 0136 — drzewa przy drodze kosztują A16 Low 6,6–8,7 ms GPU w oknach z lasem (impostory przycięte
  `ImpostorTrim`), A16 Low jest na granicy 33,3 ms. Każda dodatkowa instancja drzewa na Low wymaga uzasadnienia.
- Co dokłada 0132: **117 instancji** (brzoza 38, klon 36, lipa 31, sosna 12; 4 gatunki × 1 wariant — te same prototypy,
  LOD-y i impostory co drzewa regionu, 0 nowych materiałów), 60 działek, 34 w pasie przed płotem. Wspólne dla Low i High,
  bo region ma jeden `WorldInstanceSet`. Zmierzone w edytorze (Low, 67 kamer): +23 draw instancjonowane, +81 instancji,
  +10 k trójkątów; na kamerach trasy Gate 3 i kabiny −2…+3 draw. Trasa Gate 3 nie przebiega uliczkami domów — drzewa
  ogrodowe są tam tłem (impostor / LOD2). Koszt GPU w ms: UNVERIFIED (brak pomiaru `rq_ab` na A16).
- Uzasadnienie pozostawienia na Low do decyzji lidera: to jedyna wysoka zieleń posesji na Low (krzewy i byliny Low nie ma,
  drzewka i tuje to wersje lite); bez nich ulice domów na Low wracają do stanu z recenzji 0124 (P1-a „brak wysokiej zieleni”).
- **Propozycja filtra per tier** (zmiana w `World/Import/InstanceImporter` + `World/Runtime/WorldInstances`, właściciel:
  lider / rendering-perf): generator już oznacza te instancje `"src": "<plot>:canopy"`; dopisać w rekordzie pole
  `"tier": "high"` (brak pola = wszystkie tiery); importer zapisuje bit „tylko High” per instancja (albo osobną listę
  komórek, jak `DetailCellKey` dla Fab), runtime pomija te instancje, gdy aktywny profil < High — tak samo, jak dziś wybiera
  gęstość wg profilu, nie wg odległości. Warianty tańsze, bez zmiany importera, w mojej własności: (a) `plots.INST_R_M`
  2,3 → 3,0 m (mniej instancji na wszystkich tierach; korony 2,3–3,0 m stają się drzewkami kitu: High 65 trójkątów, Low 10),
  (b) Low tylko pas przed płotem (34 instancje) — wymaga jednak pola tier. Zalecenie: pole `tier` + pomiar
  `rq_ab off:` drzew ogrodowych na A16 przed decyzją; do tego czasu 117 wspólnych.

## Budżet High — ZAMKNIĘTE w r4 wariantem B (decyzja lidera; historia poniżej, liczby r4 w sekcji „Liczby”)
- `tests/gis/test_hero_bridge.py::test_asset_lods_and_budget` i `tests/gis/test_world_v31.py::test_frame_budget_with_forest_hlod`:
  estymata kadru HIGH ≤ 2 000 000 trójkątów. r3: `stretch_04` **2 027 946** (main 1 986 709), `route_onramp_andersa_above`
  **2 009 629** (main 1 981 768). Przyczyna: kit posesji High 52,4 k → 94,2 k (+41,8 k; krzewy / drzewka jako bryły, tuje,
  żywopłot zaokrąglony — odpowiedź na P1-a/b/e recenzji 0124), a main miał w tych kadrach 13,3 k / 18,2 k zapasu
  (99,3 % / 99,1 % limitu). Estymator liczy kit posesji High bez limitu odległości (`LOD_POLICY["High"]["furn"] = 1e9`,
  klin 120° do 1600 m) — w `stretch_04` wchodzi +40,6 k z 41,8 k całego regionu. Low bez zmian (+0,4 k).
- Nie zmieniałem progu testu (budżet = decyzja lidera; docs/06 §6: High „≤ 1,5–2 mln, hipoteza”, High nie był mierzony na
  telefonie) ani nie ciąłem kitu High (cofnęłoby poprawki, o które prosił krytyk). Warianty:
  (A) lider podnosi próg estymaty High do 2,05 M albo estymator dostaje realny zasięg kitu posesji (np. `furn` High 600 m);
  (B) runda r4 w tej gałęzi: pełne bryły tylko dla roślin ≤ ~12 m od frontu działki, reszta w wersjach lite + odchudzone
  rdzenie (tuja w rzędzie 39 → 24, krzew 36 → 28, drzewko 65 → 50) — szacunek kit High ≈ 63 k (+11 k; mieści się o ~2 k,
  WORKING_VALUE, niepoliczone w silniku), koszt: ~50 min regeneracji + ponowny przegląd, z lotu ptaka widać karty;
  (C) LOD kitu posesji w High (`plots` → geometria `plots_low` powyżej N m) — zmiana `RegionImporter`, poza własnością.

## Samokrytyka (D51 — rozpoznawalność, nie polerka)
- Względem zdjęć (`pairs_r3/sheet_ref.jpg`, `pairs_r2/sheet_ref.jpg`): ulice domów na zdjęciach toną w koronach wyższych od dachów i w gęstych
  krzewach; u nas korony są na właściwych miejscach (ortofoto), ale prototypy drzew regionu są rzadkie i cienkie — ulica
  nadal czyta się jako „nowe osiedle z kilkoma drzewami”. Ocena własna D51: PARTIAL (lepiej niż 0124, nie „jak na zdjęciu”).
- `r16_drive_3`: skośny panel ściany bocznej przy bramie nadal widoczny (brama stoi teraz w narożniku, panel to płot sąsiada).
- Low: drzewka i tuje to skrzyżowane karty — z bliska widać konstrukcję; brak krzewów i bylin.
- Progi koron strojone na oko; gatunek losowy; brak wiaty (pkt 8) i spłowiałych tynków (pkt 9).
