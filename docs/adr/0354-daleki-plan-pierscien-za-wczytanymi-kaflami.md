# ADR 0354 — Daleki plan jako pierścień za wczytanymi kaflami (przycinanie na piksel, własność najbliższego kafla)

Status: Proposed, 2026-11-26 (agent horizon-ring-s24). Numer do potwierdzenia przez lidera (równoległe ADR).
Powiązane: ADR 0085 (daleki plan, kompresja ≤ ~660 m za granicą kafla, 4 sektory × ≤ 2 podsiatki), 0308 (sektory
przy gotowych sąsiadach), 0311 (sektory w stronę każdego sąsiada z grafu stale wyłączone; budynki w zarejestrowanych
kaflach wycięte w generatorze), 0330/0339/0351 (las, WN dalekiego planu), 0353 (visual-qa z prawdziwymi sąsiadami —
ujawnił pusty horyzont).

## Kontekst
- `WorldStreamer` wyłączał sektor dalekiego planu kafla w każdym kierunku, w którym graf ma sąsiada, także narożnego
  (`EdgeSides.FarSectorMayShow`, ADR 0311), niezależnie od tego, czy sąsiad jest wczytany. Sektor `far_north` obejmuje
  też narożnik NE (podział `far_field.sector_of`), więc dw671-tykocin-03 (sąsiedzi E, S, NE, SW) tracił wszystkie
  cztery sektory. Na północ od 03 nie ma żadnego kafla — w grze zostawała szara mgła nad polami, bez lasu i linii WN
  (`artifacts/world-edge-s24/auto/edge-north.png`; tu `artifacts/horizon-ring-s24/dw671-tykocin-03/off/edge-north.png`).
  To samo na knyszyn-w `edge-west` (sąsiad narożny NW dk65-monki-02 → `far_west` wyłączony, na zachód nie ma kafla).
- Daleki plan jest skompresowany radialnie do pasa ≤ ~660 m za granicą własnego kafla (ADR 0085). W stronę wczytanego
  sąsiada leżałby na jego prawdziwej geometrii (z-fighting, ściany lasu na drodze), a dwa wczytane kafle rysowałyby
  ten sam narożny obszar dwa razy (każdy w swojej kompresji). Budynki w zarejestrowanych kaflach są wycięte już
  w generatorze (ADR 0311), lasy i WN nie.

## Opcje
| Opcja | Jakość | Koszt | Uwagi |
|---|---|---|---|
| (a) maskowanie całych sektorów względem wczytanych prostokątów (reguła 0308 bez 0311) | narożnik NE ukrywa cały `far_north`; dwa kafle rysują wspólny narożnik podwójnie | 0 | za grube — problem 03 zostaje |
| (a') 8 sektorów (bok + narożnik) z importu | lepiej, ale nadal podwójne narożniki | +do 8 draw/kafel | wymaga reimportu wszystkich kafli |
| (b) HLOD/daleki plan „sąsiadów sąsiadów” | prawdziwa geometria dalej | pamięć + I/O kolejnych scen; Low i tak ucina na 900 m | duża zmiana streamingu |
| **(c) przycinanie na piksel w shaderze + własność najbliższego wczytanego prostokąta** | dokładnie bez nakładania i bez dziur; kontynuacja pasów kafli o wspólnej krawędzi | pętla ≤ 16 prostokątów tylko w pikselach dalekiego planu; brak nowych draw calli; bez reimportu | wybrana |

## Decyzja
1. **Reguła (piksel):** piksel dalekiego planu kafla K w punkcie p (XZ świata) jest pomijany, gdy któryś inny wczytany
   kafel (stan Activating lub Ready — jego geometria jest pokazywana) jest **ściśle bliżej** p niż prostokąt K
   (wewnątrz wczytanego kafla odległość = 0, więc ten przypadek się zawiera). Daleki plan rysuje więc tylko obszar za
   ostatnim wczytanym kaflem, a każdy punkt pierścienia ma jednego właściciela — najbliższy, najmniej skompresowany
   kafel. Dla kafli o wspólnej krawędzi (03|04 na zachód, A|B na północ) kompresja jest prostopadła do tej samej
   linii, więc pasy łączą się bez szwu; dla pary narożnej (03/01) podział biegnie po przekątnej ze wspólnego narożnika.
   Remis (zbiór miary zero) — rysują oba, bez dziury.
2. **Shader:** `Rendering/Shaders/KamionFarRing.hlsl` (`KamionFarRingOwner` w wierzchołku — środek kafla = początek
   obiektu, bo siatki dalekiego planu są w układzie regionu; `KamionFarRingHidden` w pikselu). Globalnie
   `_KamionFarRects[16]` (minX, minZ, maxX, maxZ w przestrzeni świata Unity) i `_KamionFarRectCount`; prostokąt
   właściciela = wczytany prostokąt zawierający jego środek, inaczej środek ± 1024 m (jak `far_field.py`).
   - `Kamion/World Surface`: nowy lokalny keyword `_FAR_RING_CLIP` tylko na klonach `M_far_field_buildings` robionych
     przez streamer (per kafel, `HideFlags.DontSave`, niszczone przy wyładowaniu). Dzięki temu `discard` nie trafia do
     wariantu LOD1 elewacji zwykłych budynków (`_FAR_FACADE`, wczesny test głębi bez zmian). Wariant trzymany w buildzie
     przez `World/Runtime/Streaming/Resources/WorldStreaming/FarRingClipVariants.mat` (shader_feature).
   - `Kamion/Vegetation` `_HLOD_EDGE` (kurtyny lasu dalekiego planu): test w obu przebiegach głębi i w ForwardLit;
     shader już ma `clip` (alpha test), więc brak nowego kosztu early-Z. Krawędzie HLOD lasu w kaflach nie są oznaczone.
   - Znacznik renderera: `MeshRenderer.SetShaderUserValue(0x46415252)` („FARR”, Unity 6.3 renderer user value,
     zgodny z SRP Batcherem). Tylko sektory `FarField_far_*`; `FarSkyline` (ADR 0141) bez zmian.
3. **CPU:** `WorldStreamer.PushFarRects` publikuje prostokąty przy każdej zmianie stanu kafla (Activating, Ready,
   wyładowanie) i przy rebase floating origin — nigdy co klatkę, bez alokacji (bufor 16). Całe sektory, które reguła
   ukrywa wszędzie, są wyłączane (`FarRing.SectorVisible`: siatka 16 × 16, komórka wewnątrz innego wczytanego
   prostokąta albo własność z marginesem 2 × półprzekątna — różnica odległości jest 2-Lipschitz, więc wynik jest
   konserwatywny; test losowy 200 zestawów). Oszczędza to wierzchołki np. pasa E kafla 03 w całości leżącego w 02.
4. **A/B:** `FarRing.Enabled` — `-farRing off` w linii poleceń playera/edytora albo `KAMION_FAR_RING=off` przywraca
   dokładnie stary stan (reguły ADR 0311 + 0308, licznik 0, bez klonów). Funkcje `FarSectorMayShow` /
   `FarSectorVisible` zostają wyłącznie dla tego trybu.
5. Zmiana tylko w runtime: bez regeneracji `far_field.glb`, bez reimportu, bez zmian ProjectSettings. Pliki poza
   własnością świata: dwa shadery w `Rendering/Shaders` (rendering-perf do przeglądu) i drobna poprawka narzędzia QA
   (`WorldNeighbourQa.StartRoot`: kamery `-Gate3` i `-qaTruckPose` liczone względem kafla startowego, nie losowego
   sąsiada — błąd ujawniony przy dowodach tego ADR).

## Dowody (`artifacts/horizon-ring-s24/`, worktree agenta; High clear 1920×1080, Win64, ta sama sesja i sceny)
- `dw671-tykocin-03/{off,on}/` + `cmp-*.jpg` (góra off = stan przed, dół on) z `-Neighbours auto` (02, 04, 01):
  `edge-north` — las na horyzoncie zamiast mgły (10,9 % pikseli zmienionych), `edge-east` — sylwetka lasu za 02
  (0,9 %), `truck-34` — linia lasu za szpalerem (0,35 %); pozostałe kamery osiowe bez zmian.
- `knyszyn-w/{off,on}/` (sąsiedzi dk65-monki-01, knyszyn, dw671-tykocin-01, dk65-monki-02, knyszyn-s): `edge-west`
  — ściana lasu na zachodzie zamiast pustki (11,6 %); 60 pozostałych kamer bez różnicy > 0,16 %.
- `diag-03-r2/` (kamery diagnostyczne `ring-cams-03.json`): `ring-seam-n` — przy narożniku 03/01 na wysokości oczu
  las + kratowe słupy WN na horyzoncie (wcześniej sama mgła); `ring-high-ne` (180 m nad terenem) — bez ścian
  dalekiego planu na terenie 01/02, podział po przekątnej niewidoczny; `ring-high-e` — pas E kafla 03 w obszarze 02
  znika. Low: `diag-03-low/`.
- Liczby (`stats.txt`, szacunek przed SRP Batcherem; trójkąty obejmują geometrię odciętą w pikselu):

| Kamera (03, High) | draws off → on | trisK off → on |
|---|---|---|
| edge-north | 16 → 22 | 70 → 135 |
| edge-east | 154 → 168 | 231 → 355 |
| edge-south | 376 → 388 | 827 → 933 |
| truck-34 | 57 → 69 | 441 → 570 |
| route-s2035 | 385 → 393 | 858 → 932 |

  W budżecie docs/06 §6 (High ≤ 700–1000 draw, ≤ 1,5–2 mln trójkątów); koszt = sektory, które wcześniej były wyłączone
  na stałe. Brak nowych tekstur i materiałów w assetach (1 klon materiału na wczytany kafel, ~kilka kB).
- Testy EditMode: `Tests/EditMode/FarRingTests.cs` (9: brak kafli, sąsiad wczytany, pasy współliniowe bez dublowania,
  para narożna, prostokąt właściciela z listy, cull sektora, cull nigdy nie chowa widocznego piksela, przełącznik,
  przypadek 03 z prawdziwego `tile_graph.json`); stare testy ADR 0311/0308 zostają (tryb A/B). Pełny EditMode Win64:
  **1447 pass, 0 fail, 153 skip** (`artifacts/horizon-ring-s24/editmode-20261127-002815.xml`; skopiowane sceny
  `_Generated` odłożone na czas testów jak w world-edge-s24). Pierwszy przebieg wykrył: include względny łamał testy
  kopiujące `WorldSurface.shader` (FurniturePlinth i in.) → include absolutny; cull sektora za ostrożny na granicach
  kafli → dokładne pokrycie sumą prostokątów w komórce.

## Konsekwencje
- W grze horyzont za ostatnim wczytanym kaflem jest zawsze zamknięty dalekim planem (las, WN, zabudowa spoza
  zarejestrowanych kafli); po wczytaniu sąsiada jego prostokąt przejmuje prawdziwa geometria w tej samej klatce, w której
  zaczyna się aktywacja (stan Activating), a po wyładowaniu daleki plan wraca w tej samej klatce, w której znika korzeń.
  Zmiana w kadrze następuje ≥ ~400 m od kierowcy (promień ładowania) — taki sam „pop” jak samego kafla.
- Daleki plan w stronę jeszcze niewczytanego, zarejestrowanego kafla zawiera las/WN (budynki wycięte, ADR 0311);
  przed wczytaniem drogi tego kafla i tak nie widać (zamknięcie szwu). Na Low (far clip 900 m) daleki plan sąsiada
  zza wczytanego kafla zwykle leży poza płaszczyzną odcięcia — tam horyzont jak dotąd daje mgła.
- Z lotu ptaka (≥ 150 m) skompresowany daleki plan wygląda jak warstwy kart i płaskie bryły (znane z ADR 0085 r2);
  dotyczy tylko kamer diagnostycznych.

## Weryfikacja w buildzie #10 (nie wykonano tutaj)
1. Build Windows z tą gałęzią; przejazd autopilota Białystok → Tykocin z `-Scene knyszyn-w` lub `dw671-tykocin-03`
   (`& ./scripts/build-windows.ps1 -SkipBuild -Run -Scene knyszyn-w -Tier High -Autopilot route -Speed 50
   -RunSeconds 240 -ShotSeconds 120 -ExtraPlayerArgs '-stream','1'`), drugi przebieg z `$env:KAMION_FAR_RING='off'` w tej samej sesji PowerShell
   (zmienna dziedziczona przez player; równoważnie argument playera `-farRing off`) — A/B w tym samym buildzie.
2. W logu: `[STREAM] ready …` bez ostrzeżenia `far ring: more than 16`; brak błędów shadera.
3. Zrzuty z boku trasy (pola dw671): las/WN na horyzoncie w `on`, mgła w `off`; brak ścian lasu na drodze sąsiada przy
   szwie (wjazd w kafel ~400 m po Ready).
4. `pwsh scripts/pc-metrics.ps1 … -Class zalecany -Extra 'stream=1,farRing=on'` vs `'stream=1,farRing=off'`:
   p95 klatki w budżecie; spodziewany koszt GPU niewielki
   (wierzchołki dalekiego planu, pętla ≤ 16 w jego pikselach).

## Otwarte
- `discard` w klonie `_FAR_RING_CLIP` wyłącza wczesny zapis głębi tylko dla dalekiego planu (kilka draw na kafel) —
  pomiar na A16 odroczony (D73).
- Gdyby kiedyś kafle nie były kwadratami 2048 m w osiach, prostokąt właściciela w trybie Unloading spada do ± 1024 m
  (jak `KamionFarExtraDist`); dziś wszystkie kafle grafu spełniają założenie.


## Dopisek (2026-11-27, `far-forest-look-s24`): dowody tego ADR były na nieaktualnym imporcie kafli
- Sceny w worktree `win-build` (import 25.11) mają `far_field` sprzed ADR 0330 r2 i atlas kurtyn 1024×2048 (9 slotów):
  „ściana lasu” knyszyn-w `edge-west` i wysoki las 03 `edge-north` (144 m od kamery, 9,6° nad horyzontem) to stare dane, nie
  skutek pierścienia. Na aktualnym derived (przebudowa krawędzi) las 03 `edge-north` jest 385–788 m / ≤ 2,1°, knyszyn-w
  `edge-west` — linia lasu ~1,6 km. Reguła pierścienia, przycinanie na piksel i koszty z tego ADR bez zmian.
- `_FAR_RING_CLIP` i ścieżka pierścienia nie omijają mgły ani perspektywy powietrznej (kurtyny `_HLOD_EDGE`:
  `KamionFogTauExtra` z `TEXCOORD1.x`; klony budynków: `KamionFarExtraDist`) — A/B mgły w ADR 0330 dopisek 3.
- Przyczyny smug i poprawki (odświeżanie materiału atlasu przy przebudowie krawędzi, v rzutowe, pasmo per pas): ADR 0330
  dopisek 3. Dowody: `artifacts/far-forest-look-s24/`. Weryfikacja w buildzie #10 z tego ADR wymaga najpierw przebudowy
  krawędzi wszystkich kafli w `win-build`.

## Dopisek (2026-11-27, `codex-farring-diag-s24`): A/B w playerze #10

- Przejazdy #10 Knyszyn Zachód–Mońki miały aktywny streaming w obu wariantach. Kadry z kabiny patrzyły wzdłuż drogi
  między szpalerami i miały różne pozycje pojazdu. Cztery osobne pomiary PC na postoju uruchomiono bez `-stream 1`.
  Oba starty mają `needsNeighbourContext=false`, a logi nie mają `[STREAM]`. Przełącznik pierścienia działa przez
  `WorldStreamer`, więc te cztery pomiary nie izolują jego kosztu.
- Player #10 `8511a411d8`, High 1920×1080, stałe `-qacam`, `-stream 1`, clear i overcast. Przy progu
  maksymalnej różnicy kanału RGB ≥ 12/255 na północ od dw671-tykocin-03 zmienia się **1,278% / 1,279%** kadru
  (las i zabudowa, 01 i 02 Ready w obu wariantach). Na północ od dk65-07 zmienia się **1,560% / 1,469%**
  (linia lasu, 06 Ready, 08 poza promieniem streamingu). Wschodni `hv0351-far-e` na dk65-07 zmienia **0 px**,
  podniesione `biezenstwa-above` **3 / 0 px**, a wjazd na Andersa `route-onramp-andersa` **0 / 0 px**.
- GTX 1070, limit 60 FPS, 8 s próbek po rozgrzewce na wariant, bez utraty fokusu. ON dodaje **17–47 draw calls
  p95** i około **204–634 tys. trójkątów p95** w licznikach całej klatki. Poza wjazdem na Andersa zmiany p95 GPU **−3,17 do +2,39 ms**
  mają oba znaki. Zmiany szczytu VRAM procesu **−2,6 do +1,6 MiB**, prywatnej pamięci **−30,0 do +10,5 MiB**.
  To krótkie pomiary na współdzielonej maszynie. Dodatkowe draw calle są powtarzalne, izolowany koszt w ms pozostaje
  `UNVERIFIED`. Na wjeździe na Andersa p95 całej klatki w ON wynosiło 20,47–20,81 ms, w OFF 36,37–39,91 ms,
  przy braku różnic w obrazie. Pozostałe kadry w ON osiągały 16,67–16,69 ms.
- Edytor na kopii zaimportowanych scen #10, High PC, 12 przebiegów i 33 pary. Na `edge-north` dw671-tykocin-03
  (01, 02, 04 w kontekście) licznik stożka kamery rośnie **0 → 3 renderery pierścienia**, **0 → 6 podsiatek**,
  **0 → 24 331 trójkątów** przed klipem. W obrazie różni się **1,341% / 1,275%** pikseli (clear / overcast).
  Kadr osiowy `route-s2035` zmienia 1 / 0 px, a diagnostyczne ujęcie z wysoka `ring-high-e` 33 / 0 px.
  Na dk65-07 z załadowanymi 06 i 08 wschodnie `hv0351-far-e` ma **1 → 7 rendererów**,
  **25 767 → 205 259 trójkątów** przed klipem i **0 zmienionych pikseli**. `colorby:renderer` wraz z legendą
  wskazuje siatki. Podmienia ich shadery, dlatego efekt klipu oceniamy na zwykłych ujęciach.
- Zalecenie: zachować ON. Jeżeli potrzebna jest większa czytelność horyzontu, poprawić sylwetkę z danych CHM
  selektywnie na odsłoniętych kierunkach, z zachowaniem perspektywy powietrznej ADR 0330. Pary PNG 960 px,
  logi, liczniki i komendy odtworzenia w `artifacts/codex-farring-diag-s24/`.
