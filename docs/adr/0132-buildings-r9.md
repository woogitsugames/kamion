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
- Po scaleniu main i wyłączeniu ramek (r3): patrz `artifacts/buildings-r9/STATUS.md` (krok 7) i `r3/budget_low.txt`.
- Telefon: NIE mierzone (UNVERIFIED). Koszt GPU instancji drzew ogrodowych na A16 Low nieznany.

## Samokrytyka (D51 — rozpoznawalność, nie polerka)
- Względem zdjęć (`pairs_r2/sheet_ref.jpg`): ulice domów na zdjęciach toną w koronach wyższych od dachów i w gęstych
  krzewach; u nas korony są na właściwych miejscach (ortofoto), ale prototypy drzew regionu są rzadkie i cienkie — ulica
  nadal czyta się jako „nowe osiedle z kilkoma drzewami”. Ocena własna D51: PARTIAL (lepiej niż 0124, nie „jak na zdjęciu”).
- `r16_drive_3`: skośny panel ściany bocznej przy bramie nadal widoczny (brama stoi teraz w narożniku, panel to płot sąsiada).
- Low: drzewka i tuje to skrzyżowane karty — z bliska widać konstrukcję; brak krzewów i bylin.
- Progi koron strojone na oko; gatunek losowy; brak wiaty (pkt 8) i spłowiałych tynków (pkt 9).
