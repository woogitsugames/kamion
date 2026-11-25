# ADR 0341 — Szyba z kabiny: odbicie deski z „oka lustrzanego”, maska brudu i łuki wycieraczek

Status: Proposed (rendering-perf, windscreen-s24, 2026-11-24; numer nadany przez lidera). Źródło: krytyk
`artifacts/critic-s24-build5/CRITIC.md` pkt 6 (P1 „szyba i kabina sterylne”: brak refleksu deski, kurzu, śladów
wycieraczek), docs/06 §4 („szyby kabiny: krople, wycieraczki z maską, lekki brud, odbicia deski”). Uzupełnia ADR 0045,
0048, 0059 (film tylko z zewnątrz od s24 #11), 0106 (szybka ścieżka Low). Wartości wyglądu `WORKING_VALUE` (brak
fotometrii szyby i legalnych zdjęć kabiny w repo).

## Kontekst
Od przejazdu s24 #11 (commit 86cdde386) analityczny film drogowy poza polami wycieraczek jest wyłączony w widoku z
kabiny, bo szerokie gładkie pola czytały się z fotela jak „słupy dymu”. Od środka zostały: absorpcja, Fresnel i
**jednolite** analityczne wnętrze (deska albedo 0,035 w dolnej półsferze odbitego promienia, podsufitka w górnej) —
w praktyce niewidoczne. Szyba z fotela wyglądała jak powietrze.

## Decyzja
Dwie tanie warstwy na przedniej szybie (`Kamion/Truck Glass`, materiał `MI_Ext_Glass`; szyby drzwi bez zmian):

1. **Odbicie kabiny z oka lustrzanego** (`_CabReflection`, tylko pełna ścieżka = PC Medium–Ultra; szybka ścieżka
   Low/Medium mobile zostaje przy analitycznym wnętrzu).
   - Wypiekane w Blenderze (`tools/blender/truck/interior/bake_windscreen_reflection.py`, Cycles, ~10 s): panorama
     equirect 1024×512 wnętrza (LOD1, bez szyb, luster i ekranów; tylne ściany i wszystko przed płaszczyzną szyby
     przezroczyste) z punktu **E' = oko kierowcy odbite w płaszczyźnie szyby** (EYE_POINT (−0,55; 1,35; 0,225) →
     E' (−0,55; 1,398; 2,053) w układzie kabiny; płaszczyzna wewnętrznej strony szyby z `glass_interface.json`, pochylenie
     1,5°). Dla płaskiego lustra promień odbity w punkcie P biegnie dalej po prostej E' → P, więc jedno pobranie panoramy
     kierunkiem R daje **dokładne** odbicie dla oka kierowcy i paralaksę rzędu centymetrów dla innej głowy / kamery
     kontrolnej. Szyba jest płaska w strefie kierowcy (korona R 10 m).
   - Panorama przechowuje „albedo × AO” (kolor wierzchołków liniowo × atlas AO uv1 × (1 + 1,5 zużycie) — formuła
     `shader_contract` kabiny), nie oświetlenie. Shader przelicza ją co piksel: `A × (SH(góra)·(1 − _CabEnclosure) +
     _CabFill + słońce na desce)`; słońce tylko dla kierunków deski (R w dół), gdy słońce jest przed kabiną i nad
     horyzontem, × transmitancja szyby `_CabFill.w` (`CabInteriorLighting`). Pora dnia i kurs pojazdu działają bez
     ponownego wypieku. Wynik × Fresnel jednej powierzchni F1 (jak dotąd; bez „ducha” z drugiej powierzchni).
   - **Dlaczego nie sonda odbić / render czasu rzeczywistego:** sonda z projekcją pudełkową ma krawędź pudła na
     podłodze kabiny, a deska leży 0,6 m nad nią tuż przy szybie — błąd projekcji największy dokładnie tam, gdzie odbicie
     ma być widać; render kostki w grze to dodatkowa kamera URP (6 ścian, cienie, ~100 k trójkątów wnętrza) i własna
     warstwa (TagManager = ProjectSettings). Wypiek z oka lustrzanego jest dokładny dla kierowcy, kosztuje 1 próbkę +
     ~40 ALU i 0,5 MB (1024², BC1 z mipami).
2. **Maska brudu** (`_GrimeMask`, obie ścieżki), `tools/rendering/windscreen_grime.py` (numpy, ziarno 341), 2048×1024
   w płaszczyźnie xy obiektu szyby (`_GrimeRect`, 1 teksel = 1,27 mm): R kurz rozpraszający (brzeg szyby i uszczelka,
   strzępiasty pas na granicy pola pióra, nakrapianie poza polami), G łuki zużytego pióra w polach wycieraczek,
   B owady (rdzeń 1–3 mm, ogon w górę od opływu; w polach rozmazane wzdłuż łuku). Geometria pól = kontrakt materiału
   (`_WiperPivotA/B`, `_WiperSweep`; sprawdzone w kadrze `truck-front` z zaparkowanymi piórami). **Tylko wysokie
   częstotliwości** (mm–cm), bez szerokich gładkich pól (lekcja s24 #11) i bez linii nawrotu pióra (pionowa linia na
   niebie, ADR 0080 r11). Pokrycie (próg 0,1): łącznie 3,9 % szyby (kurz 3,4 %, łuki 0,35 %, owady 0,2 %) — w paśmie
   3–6 % z krytyka.
   - Cieniowanie (`DirtShade`): kurz = `R × (SH × 0,10 + olśnienie × 0,30)`, łuki = `G × olśnienie × faza × 0,08`
     (węższy płat, widoczne tylko pod słońce), owady = ciemne ciała, przepuszczają `1 − 0,65 B`; olśnienie = słońce na
     zewnętrznej powierzchni × faza Henyeya-Greensteina g 0,5 (ADR 0059). W świetle rozproszonym warstwa jest ledwo
     widoczna, pod niskie słońce świeci jak prawdziwy brud. Kurz podnosi szorstkość odbicia (+0,2 R).
3. **Przełącznik jakości:** `QualityProfile.TierSettings.windscreenLayersOff` (odwrócony, żeby stare profile miały
   warstwy; `PcTierTable` / `PcGraphicsTiers` przenoszą pole; wszystkie tiery włączone) → globalne
   `_KamionWindscreenOff`; nadpisanie pomiarowe `rq_wslayers=0|1`. Diagnostyka `rq_glassdbg=2` (odbicie ×8) i `=3`
   (maska RGB) bez `rq_ab`.
4. **Wycieraczki:** geometria zaparkowanych piór istnieje (A6.1, `body.py wipers()`, pióra 16 mm nad dolnym nadrukiem).
   Z punktu oczu (`cab-driver`) widać je jako wąski ciemny pasek tuż nad krawędzią deski (pomiar niżej) — bez zmian.

## Zmierzone
(edytor, DrivingLab, 2340×1080, tiery PC `-Pc` High i Low, kamery `cab-driver` i `cab-dash`; przed = main 6605f50,
po = ta gałąź; `tools/rendering/windscreen_measure.py`, liczby `artifacts/windscreen-s24/compare3/measure.txt`)

- **Czytelność drogi zachowana:** kontrast wysokich częstotliwości drogi przez dolną szybę (σ górnoprzepustowe, okno 7 px)
  ×1,00–1,01 we wszystkich 12 kadrach; średnia luma drogi −0,2…+0,1 pkt %. Bez mlecznej zasłony: mediana światła
  dodanego na szybie 0,00 (clear, overcast, lowsun).
- **Brud widać tam, gdzie w kabinie:** clear/overcast — p99 światła dodanego 0,00–0,13 % (pojedyncze owady na tle nieba,
  σ nieba ×1,01–1,21); lowsun pod słońce — p95 0,36–0,43 %, p99 1,5–2,3 % (łuki piór, kurz przy prawym słupku, owady),
  cienkie łuki widoczne w wycinku 1:1 (`after3/lowsun_driver_crop_1to1.jpg`), bez linii nawrotu i bez „słupów”.
  Trzy rundy strojenia (pokrycie 5,6 → 5,1 → 4,1 → 3,9 %): usunięta linia nawrotu, osłabione łuki (G 0,12 → 0,08 w
  shaderze) i grzbiet granicy pola (0,15 → 0,08), przerzedzone owady w górnym klinie między polami (w overcast czytały
  się jak kropkowana kolumna).
- **Odbicie kabiny działa i jest zorientowane poprawnie** (`rq_glassdbg=2`, ×8: deska u dołu szyby, kierownica,
  fotele i tylna ściana lustrzanie, `dbg2/`), ale **przy zatwierdzonej desce jest fizycznie niewidoczne na tle drogi**:
  mediana dodanego światła w pasie nad deską 0,0000 (poniżej 1 kodu sRGB; tło 0,036–0,087 liniowo). Rachunek: deska
  albedo 0,035–0,045 × AO ~0,6, natężenie w kabinie ~0,1–0,2 na jednostkę albedo (eksponowane) × F1 0,045 ⇒ ~0,0001–0,0005,
  czyli 0,2–1 % jasności asfaltu i 1–3 % ciemnego drzewa w cieniu. Tak wygląda prawdziwa czarna deska w dzień: widoczne
  odbicia dają jasne przedmioty (dokumenty, wydruki tachografu, uchwyt telefonu) i deska w słońcu. Nie podbijamy
  wzmocnienia ponad fizykę (docs/06: bez „HDR look”); warstwa zadziała sama, gdy na desce pojawią się jasne elementy
  (ponowny wypiek ~10 s).
- **Wycieraczki:** zaparkowane pióra są w kadrze `cab-driver` — maska `WIPER_L_LOD0;WIPER_R_LOD0` 4306 px (x 847–1673,
  y 790–847 z 1080: wąski ciemny pasek tuż nad krawędzią deski, po obu stronach kierownicy), `cab-dash` 4447 px.
  Geometria bez zmian.
- **Mapowanie maski** sprawdzone w kadrze `truck-front` (`rq_glassdbg=3`): łuki pól zaczynają się na zaparkowanych
  piórach, granice zgodne z geometrią.

## Koszt
- **Pełna ścieżka (PC Medium–Ultra):** +2 próbki (maska 2048×1024 BC1, panorama 1024×512 BC1, razem ~1,9 MB z
  mipami) i ~40 ALU (atan2, asin, 2 × przekształcenie kierunku, SH) na piksel przedniej szyby; bez nowych przebiegów,
  draw calli, wariantów shadera i alokacji. **Szybka ścieżka (Low/Medium mobile):** +1 próbka maski i ~15 ALU.
- Pomiar w edytorze (informacyjnie, `-TimeFrames 300`, `cab-driver` High clear 2340×1080 MSAA 4, karta zgłoszona przez
  Unity: GTX 1070, równolegle pracowały inne procesy Unity): włączone 2,13 / 2,32 / 2,40 ms, wyłączone (`rq_wslayers=0`)
  2,15 / 2,59 / 2,01 ms — różnica median +0,17 ms przy rozrzucie 0,6 ms, czyli **poniżej szumu pomiaru**. Build Windows
  i telefon: **niezmierzone** (`UNVERIFIED`); A/B w playerze: `-Rq rq_wslayers=0` przez `pc-metrics.ps1`.

## Odrzucone / otwarte
- Krople deszczu na szybie — poza zakresem (pogoda/deszcz nie istnieje jeszcze w grze).
- Emisja ekranów w odbiciu nocą (zegary i nawigacja odbite w szybie po zmroku) — panorama ma ekrany wyłączone;
  następny krok: osobny kanał emisji × podświetlenie z `CabInteriorLighting`.
- **Jasne przedmioty na desce** (dokumenty w uchwycie, wydruk tachografu, uchwyt telefonu, jaśniejsza mata na
  desce) — truck-artist; dopiero one dadzą czytelny „refleks deski” z punktu 6 krytyka. Po zmianie wnętrza:
  `blender -b --factory-startup --python tools/blender/truck/interior/bake_windscreen_reflection.py` i przebudowa TRAKT.
- Kierowca w odbiciu (brak modelu kierowcy) — górna część szyby odbija pusty fotel i tylną ścianę; przy normalnym
  wzmocnieniu prawie niewidoczne.
- Telefon (szybka ścieżka Low): +1 próbka maski na piksel szyby (~80 % kadru z kabiny na A16) — `UNVERIFIED`, do
  pomiaru `device-metrics.ps1` przed/po z `rq_wslayers`; jeśli > 0,2 ms, wyłączyć warstwy na Low profilem.

## Dopisek glass-sky-s24 (2026-11-25): łuki jak „pęknięcia / linie energetyczne” (krytyk build #8 P0#2)
**Diagnoza.** Klatki 1080p z nagrania build #8 (`artifacts/glass-sky-s24/full/t2480*.jpg`): cienkie białe łuki biegną
nieprzerwanie przez niebo, domy, drzewa i jezdnię — to szyba, nie przewody. Potwierdzone A/B `rq_wslayers=0`
(dw671-tykocin-02, Clear, kurs ~SSW = azymut słońca 200°): łuki, plamki i skośna smuga znikają w całości
(`cmp_t02_clear_ws_on_off.jpg`); maska `rq_glassdbg=3` (`dbg3_crop.jpg`) pokazała dwa źródła: kanał G (10 linii po 0,6–1,2 mm
na pole) i ciągły grzbiet końca pióra w R (σ 4,5 mm, R_OUT + 12 mm) — ten drugi to „skośna smuga” na niebie.
Przyczyna jasności: `d.g × glare × phase × 0,08`, a `glare` ma już fazę, więc łuk świecił z fazą² (≤ 4) × słońce w całym
stożku ~90° od słońca — przy słońcu z przodu (DW671 latem po południu) prawie zawsze.

**Zmiany.**
1. `windscreen_grime.py` G: 3 miękkie pasy smugi na pole (gauss σ 6–14 mm, amplituda 0,10–0,22, łuk 35–80°, przerwy
   z szumu 12 cm) zamiast 10 linii 1 mm; grzbiet końca pióra σ 10 mm, amplituda 0,04 (było 0,08), przerwany na ~połowie
   długości. Pokrycie > 0,1: łącznie 3,8 % (kurz 3,4 %, pasy 0,25 %, owady 0,23 %) — nadal w paśmie 3–6 %.
2. `TruckGlass.shader` `DirtShade`: pasy świecą tylko w stożku ~37° od słońca (`smoothstep(0,80; 1; cosScatter)²`) i są
   ograniczone `≤ 0,6 × amb` (SH zewnętrznej strony jako zastępstwo luminancji tła, którego szyba premultiplied nie czyta);
   olśnienie kurzu ograniczone `≤ 1,2 × amb` (plamki nie iskrzą na niebie). Koszt: +1 smoothstep, 2 min na piksel szyby,
   bez nowych próbek i wariantów.

**Zmierzone** (edytor, `-Pc` High 1920×1080, `cab-driver`; `tools/glassdiff.py`: luma dodana przez warstwy = render −
render `rq_wslayers=0`, okno szyby x 380–1500, y 0–700, poziomy sRGB):

| dw671-tykocin-02 Clear, pod słońce | p95 | p99 | p99,9 | > 8 poziomów |
|---|---|---|---|---|
| przed (main ada09fa1c) | 5,2 | 20,4 | 42,6 | 3,18 % |
| po | 2,2 | 9,2 | 20,1 | 1,25 % |

LowSun prosto w słońce (knyszyn-w, kurs 60°): wachlarz kilkunastu cienkich łuków przez całą szybę → zostają rozmazane owady, kurz przy
krawędziach i jeden miękki pas przy słońcu (`cmp_lowsun.jpg`, `lowsun_after2_crop.jpg`). Overcast: różnica przed/po
średnio 0,04–0,10 poziomu (warstwy w świetle rozproszonym bez zmian). Dowody: `artifacts/glass-sky-s24/`
(`before*/`, `after2/`, `dbg3*/`). Telefon i build Windows: niezmierzone (`UNVERIFIED`).
