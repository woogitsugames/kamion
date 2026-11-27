# ADR 0340 — Lusterka (D70): „biała płyta” to ściana kabiny, nie firanka; okienka jako szkło w obudowie; kurz przy kącie ślizgowym

Status: Proposed, 2026-11-24 (agent mirrors-trailer-s24, gałąź `mirrors-trailer-s24`). Zmiana dotyka wspólnego shadera
`Kamion/Truck Exterior` i kamer lusterek — do przeglądu przez rendering-perf i `visual-critic`.
Powiązane: D70 (lusterka = stałe okienka), ADR 0283 (okienka na monitorze, celowanie 7,5 % na zewnątrz), 0112 (ramka szkła
`MirrorGlassBezel`), 0068/0243 (budżet kamer lusterek), 0175 (R48/R104 na naczepie), 0083/0182 (firanka, brud).
Źródło: krytyk build #5 (`artifacts/critic-s24-build5/CRITIC.md`) pkt 5 — „lusterka: biała płyta naczepy bez faktury i
prostokątne okna PiP”; klatki build #7 `artifacts/full-build-7-s24/selected/shot_t1010.png`, `shot_t3383.png`.

## Kontekst — co naprawdę widać w okienku (zmierzone na renderach, nie założone)

Narzędzie `Editor/VisualQA/MirrorDump.cs` zapisuje natywne piksele tekstur lusterek klasy II (także ×3 do diagnozy).
Na `artifacts/mirrors-trailer-s24/iter/a1/mirror_L_veh.jpg` (lewe lusterko, ×3) od środka pojazdu na zewnątrz widać:

1. **Ścianę boczną kabiny TRAKT** (~18 % szerokości okienka): biały lakier z bezbarwną warstwą oglądany 3–15° od
   powierzchni. Człon Fresnela lakieru (`0,04 + 0,96 (1 − NoV)^5`) daje tam 0,5–0,8, więc panel był niemal czystym
   lustrem nieba, horyzontu i trawy — to jest „biała / szara płyta bez faktury”. W słońcu (build #7) dochodzi
   przepalona biel lakieru (kamery lusterek są LDR, bez tonemappingu).
2. **Przedni słupek naczepy** (biały, `MI_Trl_Paint`) i lampę obrysową na wysięgniku.
3. **Firankę naczepy** — wąski pasek 5–14 % szerokości (tak celuje ADR 0283, żeby korpus nie zasłaniał drogi), ciemnoszary,
   z rytmem pasów i fałd, żółtą taśmą konturową i kołami na dole.
4. **Czarne zaokrąglone obrysy** „wiszące” w obu lusterkach w każdej klatce buildu: własna ramka szkła (ADR 0112,
   głębokość 9 mm). Kamera lusterka stoi w obrazie oka za głowicą, a jej płaszczyzna near leżała 2 % przed środkiem
   szkła (`MirrorOptics.NearClipFor`) — pochylona ramka przecinała tę płaszczyznę i jej dalsza ścianka wewnętrzna
   rysowała się w obrazie.

**Model naczepy nie jest placeholderem.** `tools/blender/truck/trailer/trailer_build.py` + `trailer_export.py` już
zawierają to, o co prosi zadanie: tkaninę PVC z wybrzuszeniami między pasami, falami luzu i wachlarzami napięcia od
napinaczy (siatka + normal mapa), 23 pasy i napinacze na stronę, zgrzewy i łaty, taśmę konturową boczną (UN R48
6.21 częściowe oznakowanie konturowe, taśma R104 klasy C żółta 60 mm, ≥ 70 % długości — wg komentarza w kodzie i
`research/gptpro/p4` P4-079; tekst pierwotny regulaminu w tym zadaniu nie był czytany: `UNVERIFIED`), narożniki
górne, światła obrysowe boczne, osłony boczne, koła, chlapacze oraz brud od kół liczony w shaderze (`CurtainGrime`:
pas bryzgu 0,3–0,5 m, gęstszy za osiami, film za tyłem, zacieki od słupków). Budżet: LOD0 89 000 / LOD1 24 499 /
LOD2 7 847 trójkątów (limity 90 000 / 25 000 / 8 000 z `trailer_export.py`; `docs/07` §3 podaje budżet tylko dla
ciągnika). Dowód stanu: `artifacts/mirrors-trailer-s24/before/vqa/trailer-34.jpg`, `iter/a1/truck-rear34.jpg`.
Dlatego **nie robiono ponownego bake'u** — nie zmieniłby pikseli, które krytyk wskazał.

## Decyzja

### 1. Kamera lusterka: near za własnym szkłem (`MirrorOptics.NearClipBeyondGlass`, `RenderTextureMirror.EnsureTarget`)
Dla klas II i IV near = największa głębokość obwiedni szkła wzdłuż osi widzenia + 2 cm (klasy V/VI bez zmian: ADR
0112 wymaga tam bliskiego near, żeby został dach). Obcinany klin przestrzeni przed szkłem ma kilka centymetrów — nic
tam nie ma. Bez zmiany prefabów (liczone przy każdym `EnsureTarget`, 8 mnożeń, zero alokacji); `rq_mirror_legacy` = stare.

### 2. Kurz przy kącie ślizgowym w `Kamion/Truck Exterior` (`_GrazingDust`, domyślnie 0,12)
Nadwozie z kurzem drogowym (`_Dirt`, flota 0,5) nie jest czystym lustrem przy spojrzeniu wzdłuż blachy: ziarna
przesłaniają lakier tym bardziej, im dłuższa droga przez warstwę, x = 1/NoV − 1. Udział zakrytej powierzchni:
`film = 1 − exp(−_Dirt · _GrazingDust · x^1,5)` — **0 na wprost** (panele zwrócone do kamery bez zmiany), 6 % przy
60° od normalnej, 19 % przy 73°, 48 % przy 80°, 80 % przy 84° (flota 0,5). Czysty Beer–Lambert dałby x^1; wykładnik
1,5 jest **empiryczny** (pierwsza próba x^1 z 0,16 zostawiała ~60 % lustra na ścianie kabiny w lusterku —
`artifacts/mirrors-trailer-s24/iter/cmp_L_res3.jpg` — a mocniejsze x^1 matowiło widoki 3/4). Zakryta część jest matowa:
bez clearcoatu, lob metaliczny ×0,3, chropowatość ≥ 0,85, 25 % koloru kurzu w albedo. Opony i gładkie klosze lamp
wyłączone. `WORKING_VALUE` (kierunek artystyczny — ocenia krytyk / właściciel); `_GrazingDust = 0` = stary wygląd.
Koszt: `exp`, `sqrt`, `normalize` na piksel nadwozia. Istniejące materiały dostają wartość domyślną z shadera (bez
przebudowy prefabów).

### 3. Okienka lusterek jako szkło w obudowie (UI, zgodnie z D70 — nadal stałe okienka, ten sam prostokąt układu)
- `UI/Driving/MirrorGlassImage.cs` (`RawImage` z własną siatką 8 × 14): **krzywizna** — mapowanie beczkowe UV
  (`MirrorWindowLayout.Barrel`, k = 0,07: środek powiększony ~1,09×, rogi zostają w rogach tekstury, nic nie jest
  przycinane ani próbkowane poza teksturą) i **winieta** w kolorze wierzchołków (do −26 % w rogach, środek bez zmian).
  Jeden draw call, domyślny materiał UI, bez nowego shadera.
- `MirrorWindowArt`: **obudowa** — pierścień 9-slice generowany proceduralnie (ciemne tworzywo `UiPalette.MirrorBezel`,
  zaokrąglenie 11 j., faza oświetlona z góry, cień uszczelki i cień wargi na szkle), szerokość 7 j. (monitor) / 6 j.
  (dotyk); **film na szkle** — kurz zebrany przy dolnej krawędzi i w rogach + kilka zaschniętych kropli (alfa ≤ ~0,16
  przy samym dole, < 0,03 w środku), w prawym okienku odbity.
- `DesktopHudLayout.MirrorBezel` 3 → 6 (wcięcie szkła pod wargę). ADR 0283 celowo dał 3 („cienka krawędź, nie ramka
  PiP”) — na buildzie czytało się to właśnie jak surowy prostokąt wideo; test `HudRedesign0283Tests` zaktualizowany.
- Bez marek, bez plików graficznych (tekstury generowane raz przy starcie: 96×96 ×2 i 96×176 RGBA, ~100 KB).

## Skutki
- Okienko: +2 draw calle na lusterko (film, obudowa), siatka szkła 135 wierzchołków zamiast 4. Nie zmierzono na
  playerze (`UNVERIFIED`); rozmiar i położenie okienek bez zmian (testy układu ADR 0283/0265 nietknięte).
- Lakier TRAKT i naczepy przy ostrych kątach (krawędzie brył, boki oglądane wzdłuż) jest mniej lustrzany także w
  widoku głównym — zamierzone (docs/06: „plastik”, „idealna czystość”), do potwierdzenia przez `visual-critic`.
- Pliki: `Rendering/Shaders/TruckExterior.shader`, `Vehicle/Runtime/{MirrorOptics,RenderTextureMirror}.cs`,
  `Camera/MirrorWindowLayout.cs`, `Input/Display/DesktopHudLayout.cs`, `UI/Driving/{MirrorGlassImage,DrivingHud,
  DrivingHud.Desktop}.cs`, `Editor/VisualQA/MirrorDump.cs`, testy `MirrorWindow0340Tests`, `HudRedesign0283Tests`.

## Otwarte (poza zakresem / do decyzji lidera)
1. **Aliasing obrazu lusterka**: RT 211 × 384 px bez MSAA (`ConfigureCheapCamera`), okienko ~1:1 — pasy firanki i
   krawędzie kabiny schodkują (porównaj `iter/b1/mirrors_LR.jpg` z `iter/b1_res3`). Na PC tani zysk: MSAA 4× na RT
   lusterek albo `mirrorResolutionScale` > 1 w tierach PC (ADR 0265 P2-5 nadal otwarte) — decyzja rendering-perf + pomiar.
2. **Brak cieni w lusterkach** (`renderShadows = false`): zestaw nie rzuca cienia na jezdnię w odbiciu. Budżet PC to zniesie
   (do pomiaru).
3. **Ściana boczna kabiny TRAKT** jest dużą, gładką powierzchnią; w lusterku zajmuje więcej niż firanka. Detal (lampka
   obrysowa, klapa schowka, przetłoczenie, zacieki pod rynienką) wymaga rundy modelu kabiny — osobne zadanie.
4. Promień krzywizny lusterka klasy II wg R46 — `UNVERIFIED`; k = 0,07 to wartość robocza „ledwie widoczna”.
5. Zrzut z playera (build Windows) po scaleniu — w tym zadaniu dowody są z edytora (kamery kontrolne, tier PC High).

## Dopisek (2026-11-27, `mirror-housing-s24`) — okienko jako głowica lusterka; „szara tafla naczepy” to czoło słupka

Źródło: krytyk build #10 (`artifacts/critic-s24-build10/CRITIC.md` pkt 8: „lusterka bez obudowy / naczepa płaska”). Status: Proposed,
ocenia `visual-critic` i właściciel (autor nie zatwierdza). Wszystkie wymiary i siły `WORKING_VALUE`.

**Diagnoza (zmierzone na `r2/before/mirror_L.png`, RT natywna i ×3):** jasnoszara kolumna obok lampy obrysowej, którą krytyk
czyta jako „płaską taflę naczepy”, to **czoło przedniego słupka narożnego** (0,11 m, widziane niemal na wprost obok narożnika kabiny,
ok. 8-9 % szerokości okienka) — gładki, malowany walec o przekroju zaokrąglonego prostokąta. Firanka to nadal wąski pasek obok.

1. **Głowica lusterka w okienku (monitor; okienka dotykowe ADR 0079 bez zmian).** Prostokąt okienka i szkło klasy II nie zmieniają
   położenia ani rozmiaru (testy układu 0283/0265 nietknięte). Wokół nich rysowane są (`MirrorWindowArt`, tekstury proceduralne, bez
   plików i bez marek): `Head()` — formowana obudowa 9-slice wystająca 14 j. poza okienko (zaokrąglenie 27 j., walcowana krawędź
   oświetlona z góry z pseudonormalnej pola odległości, ziarno tworzywa, kurz na górnej ściance, linia podziału skorup, cień
   kontaktowy 4 j.); `Arm()` — dwa ramiona (górne, dolne) w stronę kabiny: rura 68 × 54 j. zakończona pionową tuleją zawiasu, jak na
   modelu TRAKT (`cab-mirrors-left`); stary pierścień ADR 0340 zostaje jako warga/uszczelka przy szkle.
2. **Szkło szerokokątne (klasa IV) pod szkłem głównym**, w tej samej obudowie: żywa tekstura istniejącego lusterka `MIRROR_Wide*`
   (bez nowej kamery), szerokość okienka, proporcja 1,30, kadr z dołu tekstury (niebo obcinane pierwsze, `MirrorWindowLayout.WideCrop`,
   nigdy nie ściskane), krzywizna beczkowa 0,16. To dekoracja okienka, nie strefa: `DesktopHudLayout.SolveMirrorWide` pokazuje ją
   tylko, gdy oba szkła (z zapasem 18 j.) nie dotykają żadnej strefy HUD (GPS, pasek, panel deweloperski) i mieszczą się w treści;
   inaczej głowica ma samo szkło główne. Telemetria deweloperska = wyłączone. Okienka główne nigdy się dla niej nie przesuwają
   (test `MirrorHead0340Tests`, 6 monitorów × 3 rozmiary × 3 położenia × 2 odsunięcia × 128 stanów).
3. **Harmonogram:** `RenderTextureMirror.ForceWide` (ustawia `DrivingLabBootstrap`, gdy HUD pokazuje szkła IV) dopuszcza lusterka
   klasy IV jako kandydatów, gdy ich szkło 3D jest poza kadrem. Limit `MirrorsPerFrame` i interwały bez zmian (High: II co 2 klatki,
   IV co 4 — zapotrzebowanie 1,5 ≤ limit 2; podczas jazdy lusterka IV zajmują sloty, które dotąd dobierała para główna). Koszt w
   playerze `UNVERIFIED` — do pomiaru `pc-metrics` (polecenie w raporcie); wyłącznik: nie podawać `Left/RightWideMirrorTexture`.
4. **Szkło mniej „czyste”:** `FilmHead()` 128 × 232 — (a) jednolity welon alfa 0,06 w kolorze szaro-niebieskim (czerń ≈ +0,035,
   biel ≈ −0,025: kontrast × 0,94), (b) brud trzymany przy wardze (pas kilku procent szerokości, najgęstszy w dolnych rogach,
   rozbity szumem), (c) zaschnięte krople: 2/3 drobne plamki, 1/3 większe ślady z przerwaną obwódką, część z zaciekiem. Środkowa
   tercja szkła ≤ 0,16 alfa (test `MirrorHeadArtTests`). Obraz mnożony przez (0,92; 0,94; 0,95) jak materiał szkła 3D.
5. **Naczepa — słupek przedni jako profil** (`trailer_build.py front_wall()`): kanał kedrowy 28 × 6 mm w czole, rowek 24 × 4,5 mm
   w ścianie bocznej, stopa i odlew narożny ocynk (4 mm przed lakierem) ze śrubami, rząd 9 nitów blachy czołowej co 0,24 m.
   Lico lakieru cofnięte o 6 mm, okucia kończą się na obrysie 13,6 m (`physics_crosscheck` PASS); promień naroża i obrys 2,55 m bez
   zmian. LOD1 traci nity i śruby, LOD2 także stopę i odlew. Taśmy konturowe i odblaski (ADR 0175) nietknięte.

**Zmierzone:** naczepa LOD0 89 000 → 88 999 / 90 000, LOD1 24 499 → 24 496 / 25 000, LOD2 7 847 → 7 849 / 8 000 (`check_export.py`
PASS; eksport z bake'iem 835 s). Kamery kontrolne (edytor, PC High, 1920 × 1080, clear): `drawsEst` bez zmian na wszystkich 11 kamerach
(np. `cab-driver` 236 → 236, `trailer-34` 315 → 315). UI: okienko 3 → 6 obrazów (+ obudowa, 2 ramiona), z szybą IV 9 (łącznie
+12 obrazów UI na oba lusterka; rzeczywiste draw calle po batchowaniu uGUI — `UNVERIFIED`). Tekstury proceduralne: 160², 136 × 108,
128 × 232 RGBA (~230 KB). Testy: EditMode 1481 / 0 / 123 pominięte (`artifacts/tests/editmode-20261127-094616.xml`), PlayMode HUD
(filtr 5 klas) 56 / 0.
**Dowody:** `artifacts/mirrors-trailer-s24/r2/` — `before/`, `after/` (11 kamer + `mirror_L/R.png`, `stats.txt`), `cmp_cab-view-b-fov70-hud.jpg`,
`cmp_mirror_L_native.png`, `iter2/zoom.jpg` (głowice 1:1).
**Otwarte:** (1) w lusterku nowy słupek daje linię kanału i odlew ze śrubami — zmiana jest mała w pikselach (RT ~211 px szerokości);
dalszy zysk wymaga decyzji o celowaniu lusterka (ADR 0283) albo większej RT; (2) przełącznik szkła IV w ustawieniach (dziś zawsze,
gdy się mieści) i jego rozmiar — decyzja właściciela; (3) ramiona kończą się tuleją „w powietrzu” (okienko nie jest przypięte do
słupka A w 3D) — kierunek artystyczny do oceny; (4) pomiar playera Windows.

## Dopisek 2 (2026-11-27, `mirror-mounts-s24`) — wspornik głowicy do słupka A, RT kl. II ≥ 512 × 1024, ciemniejsze szkło

Źródło: krytyk `artifacts/critic-s24-day27/CRITIC.md` zestaw 3 („ramiona wiszą w powietrzu; obraz rozmyty; odbicie za jasne/mgliste”).
Status: Proposed, ocenia `visual-critic` i właściciel. Wymiary i siły `WORKING_VALUE`; zamyka „Otwarte (3)” dopisku 1.

**Diagnoza (kadry `before/`):** głowica HUD stoi nad lewą krawędzią słupka A (prawdziwe ramiona 3D wychodzą spod niej), prawa — w szybie,
słupek prawy jest poza kadrem. Stary kikut (68 j., tuleja) miał stałą długość i nie wiedział, gdzie jest kabina. RT kl. II miała 171 × 384 px
(szkło TRAKT ma proporcję 0,445, nie 0,55). Kamera lusterka renderuje bez gradacji widoku głównego, a film dawał welon 0,06.

1. **Wspornik zakotwiczony w kabinie.** `RenderTextureMirror.CabMountWorld()` = punkt na wewnętrznej ścianie słupka A przy przedniej krawędzi
   drzwi (offset od środka szkła kl. II: 0,372 m do osi, +0,123 m w górę, +0,138 m w przód; z `body.py mirrors()`), rzutowany co klatkę do
   okienka (`DrivingHudContext.Left/RightMirrorMountViewport`, bez alokacji). `MirrorWindowLayout.SolveMount` (czysta funkcja): rura pozioma
   (34 j.) z boku głowicy do punktu + zastrzał (21 j.) z niższego miejsca głowicy do tej samej stopy; stopa 44 × 112 j. z piastą i dwiema
   śrubami, cień kontaktowy (`MirrorWindowArt.Tube()` 9-slice, `Foot()`; proceduralne, bez marek). Punkt za głowicą lub < 10 j. obok = nic
   (głowica zasłania mocowanie, np. FOV 55°); punkt poza kadrem = rura wychodzi z kadru (prawa głowica przy domyślnym FOV); dalej niż 2,2
   szerokości głowicy (rozglądanie) = wspornik wygasa zamiast rozciągać się przez widok. Przeliczenie tylko przy ruchu punktu > 0,25 j.
2. **RT lusterka głównego:** pola tieru `mirrorMainMinWidth/Height` (PC High i Ultra 512 × 1024; Low/Medium/telefon 0 = bez zmian) →
   `VehicleCameraBudget.MainMirrorHeight`: tekstura co najmniej tak szeroka I tak wysoka — dla szkła 0,445 to **512 × 1151** (było 171 × 384).
   Lusterka IV–VI bez zmian. Tekstura większa od okienka dostaje mipmapy + trilinear. Bez zmian w `ProjectSettings`. A/B: `rq_mirror_main=<px|0>`.
3. **Jasność:** `MirrorWindowLayout.GlassTint` 0,92 → 0,80 (−13 %), `FilmVeil` 0,06 → 0,03 (czerń +0,018 zamiast +0,035). Mgły w kamerze
   lusterka nie ruszano (lusterko widzi tę samą atmosferę). Sprawdzona i **odrzucona jako domyślna** gradacja widoku głównego w kamerze lusterka
   (`mirrorPost`, HDR + post): średnia obrazu 0,645 → 0,665 (bez widocznej zmiany), koszt +0,5–0,7 ms/parę w edytorze, a szkło 3D byłoby
   gradowane dwukrotnie. Przełącznik zostaje do A/B w playerze (`rq_mirror_post=1`), w tierach wyłączony.

**Zmierzone (edytor, DrivingLab, PC High 1920 × 1080, proxy — NIE player):** `MIRROR_BENCH` mediana ms/parę, 2 przebiegi: MSAA 4 171 × 384
3,75 / 3,77; MSAA 4 512 × 1151 **3,57 / 3,68** (w szumie — koszt w edytorze jest po stronie CPU); + post 4,27 / 4,43. Piksele na lusterko
0,066 → 0,589 Mpx (× 9, MSAA 4; ok. 28 % pikseli widoku 1080p przy odświeżaniu pary co 2. klatkę) — koszt GPU w playerze `UNVERIFIED`.
`cab-view-b-fov70-hud`: `drawsEst` 147 → 147, `trisExact` 175 023 → 175 023 (geometria kabiny nietknięta, ≤ 120 000 LOD0 bez zmian). UI: 3 obrazy na
głowicę (zastrzał, rura, stopa) zamiast 2. Okienko (wycinek szkła, sRGB): średnia 0,804 → 0,766. Testy: EditMode 1639 / 1516 zielonych / 0 / 123
pominięte (`editmode-20261127-152203.xml`), PlayMode HUD + lusterka (5 klas) 54 / 0 (`playmode-20261127-154849.xml`); nowe `MirrorMount0340Tests` (8).
**Dowody:** `artifacts/mirror-mounts-s24/` — `before/`, `after/`, `cmp_cab-view-b-fov70-hud.jpg`, `before_b_L.png` | `after_b_L.png` (1:1),
`cmp_mirror_L_native_iter1.jpg` (RT natywna 171 × 384 ×3 | 512 × 1151), `after_fov_variants.jpg` (FOV 55 / 75 / 70 p10).
**Otwarte:** (1) pomiar playera: `pwsh scripts/pc-metrics.ps1 -Exe <build> -Scene knyszyn-w -Tier High -Fps 60 -Width 1920 -Height 1080 -DurationSeconds 90 -Class zalecany`
z `rq_mirror_main=0` vs domyślne (przy przekroczeniu budżetu: 384 × 864 = `mirrorMainMinWidth 384, mirrorMainMinHeight 768`); (2) prawa głowica
przy domyślnym FOV ma mocowanie poza kadrem — w kadrach QA (margines bezpieczny 4 %) głowica dotyka krawędzi i wspornika nie widać; w playerze
(margines ~20 px) widać krótki odcinek rury do krawędzi — do oceny krytyka; (3) wspornik sięga wnętrza słupka (czyta się jak monitor na słupku),
offsety dobrane dla TRAKT; (4) szkło 3D (`_BaseColor` 0,92) nie przyciemnione.

## Dopisek 3 (2026-11-27, `codex-mirror-right-s24`) — wspornik prawej głowicy od krawędzi kadru

Prawe okienko w `DrivingLab` przy symulowanym asymetrycznym safe area dochodziło do krawędzi, a rzut prawego słupka wypadał poza nią. Układ monitora w widoku kabiny rezerwuje teraz 72 j. między obrysem głowicy a fizyczną krawędzią ekranu (`WORKING_VALUE`). Liczy lewy i prawy margines względem rzeczywistego położenia obszaru treści. Przy symetrycznym obszarze oba okna mają symetryczny układ. Rozmiar obu okien nadal wynika ze wspólnego limitu miejsca obok wolnego pola widzenia.

`SolveMount` wyznacza oba odcinki w jednostkach okienka z rzutu słupka A. Po stronie widocznego słupka rura i zastrzał schodzą się w stopie. Przy bocznej krawędzi stopa wygasa, a odcinki biegną po swoich osiach przez krawędź ku punktowi zbiegu. Głębokość punktu zbiegu poza ekranem jest ograniczona do 72 j. (`WORKING_VALUE`). Dzięki temu przy dalekim rzucie słupka wspornik pozostaje krótki, a oba człony czytelne. Ta sama geometria działa w odbiciu po lewej stronie. Próg odświeżenia przy ruchu rzutu to nadal 0,25 j.

UI używa istniejących obrazów rury i zastrzału. Przy bocznym wyjściu z kadru aktywne są dwa z trzech elementów mocowania, a pozycja rzutu korzysta ze współrzędnych ekranu zapisanych podczas układania HUD. Przybyło 0 komponentów, tekstur, materiałów i kamer. Czas GPU i liczba batchy uGUI w playerze pozostają `UNVERIFIED`.

Visual QA DrivingLab, Win64 PC High, 1920 × 1080, clear i overcast. Przed zmianą w 6/6 kadrów obrys prawej głowicy dochodził do brzegu, a oba człony były niewidoczne. Po zmianie w 6/6 widać pełną głowicę oraz rurę i zastrzał dochodzące do brzegu. Przy 70° i 75° lewa stopa pozostaje na słupku A. Przy 55° pokrywa ją obrys lewej głowicy tak jak w kadrze bazowym. Niezależny `visual-critic` zgłosił PASS. Przy 75° górna rura nakłada się częściowo na ciemny element kabiny, ale pozostaje czytelna.

| FOV | `drawsEst` przed → po | `trisExact` przed → po |
| --- | ---: | ---: |
| 55° | 131 → 131 | 172 815 → 172 815 |
| 70° | 147 → 147 | 175 023 → 175 023 |
| 75° | 152 → 152 | 175 513 → 175 513 |

Statystyki obu wariantów pogody pochodzą z `stats.txt` i opisują scenę 3D. Dowody w `artifacts/codex-mirror-right-s24/` obejmują `before/`, `after/`, zestawienia `comparison-{clear,overcast}.png` (960 × 870) i zbliżenia `right-detail-{clear,overcast}.png`.
