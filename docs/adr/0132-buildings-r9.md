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
    zmierzony niżej; jeśli lider uzna go za za duży: `plots.INST_ON = False` NIE istnieje — decyzja do podjęcia w importerze
    (pole `hi` w instancji) albo przez próg `INST_R_M`.

WORKING_VALUE: wszystkie progi, udziały i wymiary powyżej.
