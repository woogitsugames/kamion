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
   niebie, ADR 0080 r11). Pokrycie (próg 0,1): łącznie 5,1 % szyby (kurz 3,8 %, łuki 0,6 %, owady 0,7 %) — w paśmie
   3–6 % z krytyka.
   - Cieniowanie (`DirtShade`): kurz = `R × (SH × 0,10 + olśnienie × 0,30)`, łuki = `G × olśnienie × faza × 0,12`
     (węższy płat, widoczne tylko pod słońce), owady = ciemne ciała, przepuszczają `1 − 0,65 B`; olśnienie = słońce na
     zewnętrznej powierzchni × faza Henyeya-Greensteina g 0,5 (ADR 0059). W świetle rozproszonym warstwa jest ledwo
     widoczna, pod niskie słońce świeci jak prawdziwy brud. Kurz podnosi szorstkość odbicia (+0,2 R).
3. **Przełącznik jakości:** `QualityProfile.TierSettings.windscreenLayersOff` (odwrócony, żeby stare profile miały
   warstwy; `PcTierTable` / `PcGraphicsTiers` przenoszą pole; wszystkie tiery włączone) → globalne
   `_KamionWindscreenOff`; nadpisanie pomiarowe `rq_wslayers=0|1`. Diagnostyka `rq_glassdbg=2` (odbicie ×8) i `=3`
   (maska RGB) bez `rq_ab`.
4. **Wycieraczki:** geometria zaparkowanych piór istnieje (A6.1, `body.py wipers()`, pióra 16 mm nad dolnym nadrukiem).
   Z punktu oczu (`cab-driver`) zasłania je górna krawędź deski — zostawiamy (bez przesuwania geometrii wbrew
   wymiarom); szczegóły w sekcji „Zmierzone”.

## Zmierzone
(edytor, DrivingLab, 2340×1080, tiery PC `-Pc`; przed = main 6605f50, po = ta gałąź; `tools/rendering/windscreen_measure.py`)

TBD

## Koszt
TBD

## Odrzucone / otwarte
- Krople deszczu na szybie — poza zakresem (pogoda/deszcz nie istnieje jeszcze w grze).
- Emisja ekranów w odbiciu nocą (zegary i nawigacja odbite w szybie po zmroku) — panorama ma ekrany wyłączone;
  następny krok: osobny kanał emisji × podświetlenie z `CabInteriorLighting`.
- Kierowca w odbiciu (brak modelu kierowcy) — górna część szyby odbija pusty fotel i tylną ścianę; przy normalnym
  wzmocnieniu prawie niewidoczne.
- Telefon (szybka ścieżka Low): +1 próbka maski na piksel szyby (~80 % kadru z kabiny na A16) — `UNVERIFIED`, do
  pomiaru `device-metrics.ps1` przed/po z `rq_wslayers`; jeśli > 0,2 ms, wyłączyć warstwy na Low profilem.
