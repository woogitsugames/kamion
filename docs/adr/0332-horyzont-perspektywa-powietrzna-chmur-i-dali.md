# ADR 0332 — Horyzont: perspektywa powietrzna chmur i dali zamiast białego pasa mgły

Status: Proposed (agent haze-s24, gałąź `haze-s24`), 2026-11-24. Do scalenia przez lidera.
Powiązane: krytyk `artifacts/critic-s24-build5/CRITIC.md` (TOP 10 pkt 2, klatki t0950–t1020), ADR 0080 (mgła
przyziemna, KamionAtmosphere), ADR 0108 (fotograficzne chmury Clear), ADR 0113 (ForestCanopy), D68 (lato wszędzie).

## Kontekst
Krytyk build #5: „poziomy jasny pas nad polem, ostra granica pole/mgła — sztuczny gradient nieba przy ziemi”.
Pomiar na zrzutach (build #4 t1000 oraz visual-qa knyszyn-w, `artifacts/haze-s24/before/`) wskazuje dwie przyczyny:

1. **Niebo (główna).** W `Kamion/Sky` chmury fotograficzne (Clear, `clearCloudCover` 1) w dolnych ~10° były liniowo
   wygaszane do płaskiego `_SkyFogColor` (`smoothstep(0, 0.18, d.y)`), a ich krycie dodatkowo w dolnych 3,4°
   (`smoothstep(0, 0.06, d.y)`). Chmury nad pasem mają jasność z display-cap (~200–220 sRGB), kolor horyzontu jest
   fizyczny (~130–180). Wynik: bezstrukturalny gradient od bieli do szarości przez ~6–10° — „ściana mgły”, a nie
   chmury za zamgleniem. Profil pionowy (dk65-fields-nw, przed): 217 → 206 → 195 → 182 → pole.
2. **Teren (drugorzędna).** Teren kończy się na far clip kamery (PC 1500/2000/3000/4000 m, telefon 900–3500 m), gdzie
   przy V = 20 km zamglenie wynosi tylko 26–55 %. Tuż nad nim niebo poniżej horyzontu ma pełny kolor mgły (teren
   w nieskończoności) — ostra linia. Przy wysokości oka ~3 m dotyczy to tylko ostatnich pikseli, ale na Low (1500 m)
   daleka linia drzew urywała się wyraźnie.

Shader lasu HLOD na szybkiej ścieżce (`Kamion/Forest Canopy`, PC Low / telefon Low) używał unityowego `MixFog`
(bez warstwy przyziemnej ADR 0080 i bez tonu Low), więc przy Overcast las w dali był ciemniejszy niż pole za nim.

## Decyzja
1. **Chmury: perspektywa powietrzna zamiast rampy.** `cloud = lerp(_SkyFogColor, cloudY, T)`,
   `T = exp(-beta * h / sin(el))` — beta to ten sam Koschmieder z `visibilityKm`, którego używa teren
   (`_KamionHaze.x`), h = 300 m to grubość resztkowego welonu przyziemnego (`WORKING_VALUE`). Zdjęcie HDRI zawiera już
   zamglenie dnia, w którym je zrobiono, więc dodawany jest tylko resztkowy welon; 150 m dawało płaski biały bank
   przy horyzoncie (A/B `after150` vs `after300`). Krycie chmur gaśnie tylko w ostatnich ~0,7° (`smoothstep(0, 0.012)`)
   — ukrywa przedłużony wiersz źródła (`clearCloudSourceMinElevationDeg`). Clear V 20 km: T(2°) ≈ 0,19, T(5°) ≈ 0,51,
   T(10°) ≈ 0,71, T(90°) ≈ 0,94. Ten sam kolor docelowy co mgła terenu: jeden system dla ziemi i nieba.
2. **Teren przy far clip.** `KamionFogTau` dodaje do głębokości optycznej `4 · smoothstep` w ostatnich 25 % far clip
   kamery głównej (`_KamionFarFade` z `WorldAtmosphere.FarFade(tier.cameraFarClip)`; 0 = wyłączone). To zastępuje
   3–20 km lądu za płaszczyzną odcięcia: teren na far clip ma 98 % koloru horyzontu. Udział 25 % — `WORKING_VALUE`.
3. **ForestCanopy:** `KamionFogTau` + `KamionMixFog` zamiast `ComputeFogFactor` / `MixFog` (ta sama mgła wysokościowa
   i ton co teren, nadal per wierzchołek, `multi_compile_fog` usunięte — mniej wariantów).

Overcast (deck z szumu, `_KamionCloud.w`) bez zmian — jego zanik przy horyzoncie (`1 - exp(-5 el)`) był spójny;
różnica pikseli przed/po = 0 poza ostatnimi wierszami terenu.

## Koszt
Sky: `exp` + dzielenie zamiast `smoothstep` na piksel nieba (ta sama liczba odczytów tekstur, 0 nowych przebiegów).
Teren: `saturate` + 3 mnożenia na wierzchołek. ForestCanopy: `KamionFogTau` (2× `exp`) zamiast `ComputeFogFactor`
na wierzchołek. Pomiar GPU: **UNMEASURED** (edytor nie jest dowodem; do sprawdzenia w pomiarze buildu `pc-metrics`).

## Konsekwencje i otwarte
- URP Lit (las HLOD na PC Medium+, gdzie `forestFast = false`) nadal używa mgły Unity: bez warstwy przyziemnej
  (Overcast) i bez dociągnięcia przy far clip. Propozycja dla lidera: ForestCanopy także na PC Medium+ (ten sam BRDF
  co Lit wg ADR 0113, tańszy) albo `KamionFogTau` w kopii Lit — wymaga A/B cieni (shadowDistance PC > forestHlodM).
- `kCloudVeilM` 300 m i `FarFadeShare` 0,25 to wartości robocze dobrane na kamerach knyszyn-w; do potwierdzenia
  zdjęciem referencyjnym horyzontu Podlasia latem (brak `art-source/**/refs/` horyzontu).
- Dowody: `artifacts/haze-s24/` (before / after150 / after300 / after2, arkusze `sheet-*-before-after.jpg`).

## Dopisek glass-sky-s24 (2026-11-25): aureola i „dziura” przy słońcu, biały pas t0720/t0830 (krytyk build #8 P1#4, P2)
**1. Aureola, dziura w chmurze (t2370–t3140).** Nie shader, tylko mapa `T_ClearClouds.png` (ADR 0108): generator wyzerował
krycie w 1,5° od fotografowanego słońca („dziura”), a jasne, prawie neutralne niebo okołosłoneczne nie ma nadwyżki
niebieskiego, więc matowanie zostawiło je jako półprzezroczystą „chmurę” z nasyconą luminancją G = 1 („aureola”, 28 %
pikseli w 9° półprzezroczystych). `WorldAtmosphere` obraca mapę tak, że fotografowane słońce leży na słońcu gry — defekt
jest więc zawsze przy słońcu, a widać go jadąc pod słońce (DW671 na SSW, słońce Clear 200°). Naprawa danych, bez kosztu
GPU: `tools/rendering/clear_clouds_sun_repair.py` (na oryginale z hashem ADR 0108) — wypełnienie Laplace krycia w 3° (2594
teksele, gdzie R < 0,9) i luminancji tarczy do mediany pierścienia, ostry re-matte (smoothstep 0,30–0,60 + szum kłębów
0,4–3°) otoczki w 9°, przejście do 11,5°; poza tym mapa bajt w bajt bez zmian. Półprzezroczyste w 9°: 31 % → 5 %.
Skutek uboczny: tarcza słońca Clear chowa się za krawędzią tej chmury (cienie zostają ostre — jak słońce za cienką krawędzią
cumulusa). Test: `ClearCloudsSunTests` (brak dziury w 2°, < 10 % półprzezroczystych w 9°). Nowy hash w
`ClearCloudsSource.json` (`texture_sha256`; stary w `texture_sha256_adr0108`).

**2. Skośne smugi na niebie** — to szyba (grzbiet końca pióra), patrz dopisek glass-sky-s24 w ADR 0341.

**3. Biały pas (t0720 bialystok-knyszynska, t0830 dk65-02; Szosa Knyszyńska, kurs ~W–NW).** Welon chmur blendował do
`_SkyFogColor` = **średniej po azymucie** jasności horyzontu (`SkyModel.HorizonColorExposed`). Pod słońce lokalny horyzont
jest jaśniejszy od średniej (DW671: działa), z dala od słońca ciemniejszy i bardziej niebieski — dolne części chmur kończyły
się płaskim, neutralnym pasem jaśniejszym od nieba obok. Pomiar (knyszyn-w, Clear, kurs 20° = słońce za plecami, profil
pionowy x 1000–1100, `tools/profile.py`): przed 5 wierszy po 20 px 187/189/189 → 180/182/181 sRGB, B−R 1–2 (płaski szary
pas ~5°); po: 179/185/191 → 171/176/179, B−R 9–11 (gradient nieba). Zmiana: `cloud = lerp(sky, cloudY, T)` — światło
rozproszone welonu przed chmurą to światło czystego nieba w tym samym kierunku (kopuła = in-scatter całej drogi), więc
chmura gaśnie w niebo za nią. Koszt: 0 (ten sam `lerp`, inna wartość). Sprawdzone i odrzucone: `kCloudVeilM` 150 m z nowym
celem (pas znów jaśniejszy i płaski: 188/191/193, B−R 5) — zostaje 300 m. Overcast bez zmian (różnica 0,04–0,10 poziomu).
Teren przy far clip nadal blenduje do średniej (`_KamionHazeColor`) — na ten kurs nie widać tego jako pasa nad polem w
kadrach knyszyn-w; otwarte do sprawdzenia w buildzie na Szosie Knyszyńskiej (kafel bialystok-knyszynska, `UNVERIFIED`).
Dowody: `artifacts/glass-sky-s24/` (`cmp_away_3.jpg`: przed / po / welon 150 m, `cloudtex/repair_preview.jpg`,
`crop_t02_sky_after2.jpg`).

## Dopisek 2 render-artifacts-s24 (2026-11-26): jasne okrągłe plamy w chmurach i „szew” nieba (krytyk fala 11, pkt 10)
**Plamy — przyczyna:** duch flary obiektywu (lens ghost) w HDRI Poly Haven: jasny krąg ~3,5° w cumulusie 18° na wschód i 23°
poniżej fotografowanego słońca (mapa: lat 23,8° / lon 51,8°; rdzeń G 0,70 przy chmurze 0,45, krycie R 0,93 przy 0,4–0,6).
`WorldAtmosphere` obraca mapę tak, że słońce zdjęcia leży na słońcu gry, więc plama zawsze wisi w tym samym miejscu względem
słońca: dla tykocka-dw671-out (kurs 230°, słońce 200°/42°) przewidziane x 762 / y ~140, widoczne x 740 / y 165.
**Poprawka danych (0 kosztu GPU):** `tools/rendering/clear_clouds_ghost_repair.py` — w 2,3° (+0,8° przejścia) wypełnienie Laplace
R i G z pierścienia + drobna faktura chmury z sąsiedniego fragmentu tego samego cumulusa; poza tym bajt w bajt bez zmian.
Rdzeń G 0,705 → 0,481 (pierścień 0,451). Hash w `ClearCloudsSource.json` (`texture_sha256`; poprzedni w
`texture_sha256_glass_sky`). Test EditMode `ClearCloudsSunTests.LensGhost_IsNotABrightBlotInTheCloud`.
Render: `artifacts/render-artifacts-s24/sbs/crop-sky-before-after.jpg`.

**„Szew” cyjan|błękit (x~950) — pomiar, bez zmiany shadera.** Profil wierszy nieba na prawo od chmury: wszystkie kanały mają
stały spadek (R −1,2, G −0,8…−1,2, B −0,2 sRGB / 12 px) — brak skoku wartości i brak załamania pochodnej (Mach). Ablacje:
`clearSkySaturation` 1 (zamiast 2) i display-cap wyłączony — przejście zostaje w tym samym miejscu (z saturacją 1 o połowę
słabsze). Teksele LUT chromy (γ co 2,86°) przechodzą co ~70 px, więc nie dają jednej linii. Wniosek: to najstromszy odcinek
gradientu barwy okołosłonecznej (γ ≈ 25–35°), nie artefakt; wzmocniony celowo przez `clearSkySaturation` 2 (ADR 0108).
Decyzja o ewentualnym obniżeniu saturacji nieba = kierunek artystyczny (właściciel / visual-critic), nie poprawka błędu.

## Dopisek 3 agy-clouds-s24 (2026-11-27): ciemny punkt w niebie (x~1170, y~140), miękkie krawędzie chmur i 3 warianty CC0 (krytyk build #10 TOP 10 pkt 10)
**1. Ciemny punkt w niebie (x~1170, y~140) — diagnoza i naprawa u źródła.**
To **nie** piksel mapy chmur ani artefakt słońca, lecz **plama owada na przedniej szybie** (`T_Windscreen_Grime.png`, kanał B,
ADR 0341). Dowód: punkt pojawia się w dokładnie tym samym pikselu ekranu `(1170, 142)` na klatkach build #10 różnych kafli i
kursów (`knyszyn-w` spadek jasności −49,7 sRGB, `dk65-06` −29,0, `run-stream-on/shot_t0180` −29,7 mimo przesunięcia chmur w dół)
oraz w baseline visual-qa (`World_knyszyn-w_High`, `cab-driver`, High PC 1920×1080) **zarówno w Clear (−51,3 sRGB), jak i w
Overcast (−75,7 sRGB, gdzie `T_ClearClouds.png` nie jest próbkowany)**. Projekcja promienia z oka kierowcy
`EYE_POINT = (−0,55; 1,35; 0,225)` przy FOV 70° (D90) i pochyleniu −6° (`DriverHead.RestPitchDownDeg`) trafia płaszczyznę
szyby w `obj = (−0,314; 1,702)` — dokładnie środek plamy owada `B = 214` (13 tekseli, `px = (776, 273)`) w górnym klinie
między polami wycieraczek.
- **Poprawka u źródła (`tools/rendering/windscreen_grime.py`):** w górnej środkowej strefie szyby poza polami wycieraczek
  (`y > 1,45 m`, `|x| < 0,85 m`, w cieniu aerodynamicznym dachu/daszka, rzutującej prosto na otwarte niebo z fotela kierowcy)
  generator nie stawia nieprzezroczystych plam owadów; dolna/środkowa część szyby i krawędzie przy słupkach A zostają bez zmian.
  Łączne pokrycie brudu `> 0,1`: **3,81 %** (w paśmie 3–6 % ADR 0341; max B w strefie nieba `240 → 50`, 0 pikseli `> 60`).
- **Zmierzone na `cab-driver` (przed → po):** spadek jasności w `(1170, 142)` Clear `+51,3 → +7,7` sRGB (faktura chmury),
  Overcast `+75,7 → +1,0` sRGB. Test regresyjny: `WindscreenLayer0341Tests.WindscreenGrime_HasNoOpaqueDarkInsectDotInUpperSkyWedge`.

**2. Chmury Clear: miękkie krawędzie (koniec „watowych sprite'ów”) i 3 warianty CC0 + odbicie południkowe.**
Przyczyną „watowego” konturu był twardy binarny progowy matte `1 − smooth(0,25; 0,85; blueness)` (ADR 0108, skok krycia w 2–3
tekselach: gradient krawędzi `p90 = 0,162`, `p99 = 0,459`), płaskie rozjaśnienie luminancji (`^0,70`) i achromatyczne
`cloudY.xxx` w `Sky.shader` na tle nasyconego ×2 błękitu (D100 zostaje nietknięte). Powtarzalność wynikała z jednej mapy
zawsze zablokowanej na stałym słońcu `LP_Clear` (200°/42°).
- **Generator (`tools/rendering/fetch_sky_hdris.py`, `tools/rendering/build_cloud_variants.py`):** 3 zweryfikowane (MD5 + SHA256,
  `docs/LICENSES.md`) 4K HDRI CC0 Poly Haven Pure Sky → mapy 4096×2048 RGBA (`R` krycie, `G` luminancja `^0,82`):
  - `T_ClearClouds.png` (wariant 0): `kloofendal_48d_partly_cloudy_puresky` (słońce 47,9°, rozproszone cumulusy) — gradient
    krawędzi `p90/p99`: `0,162/0,459 → 0,059/0,172` (**2,7× miękcej**); zachowana naprawa tarczy słońca (`holes 0,0 % < 2 %`),
    otoczki (`semi 3,6 % < 10 %`) i ducha flary (`core−ring +0,039 < +0,08`), usunięte pojedyncze 1–2 px otworki w chmurach.
  - `T_ClearClouds_02.png` (wariant 1): `sunflowers_puresky` (słońce 43,0°, szerokie cumulusy + pasma cirrusów; `p90/p99 0,065/0,198`).
  - `T_ClearClouds_03.png` (wariant 2): `kloofendal_38d_partly_cloudy_puresky` (słońce 37,8°, lekkie altocumulusy i pasma;
    `p90/p99 0,066/0,153`).
  Matte adaptuje linię bazową błękitu czystego nieba do elewacji (90. percentyl błękitu poza stożkiem słońca), używa ciągłej
  krzywej optycznej (`w^1,35`) i zlokalizowanego na krawędzi zmiękczenia (σ ≈ 2,5 teksela), zachowując ostrość wnętrz chmur.
- **Selekcja i odbicie południkowe (`WorldAtmosphere.cs`, `PhotographicClouds`, `RenderOverrides.cs`):**
  Deterministyczny wybór `(wariant 0..2, odbicie 0..1)` z hasha `(CloudSeed, kanoniczna nazwa sceny bez sufiksu _High/_Low/_Tile,
  godzina clockHour, sektor azymutu słońca)` + jawne nadpisania QA (`rq_cloudvar`, `rq_cloudmirror`, `rq_cloudseed`).
  Odbicie Householder względem pionowej płaszczyzny południka słońca (`R = I − 2 r rᵀ`, `r = normalize(up × sourceSun)`)
  mnożone na CPU w `_KamionClearCloudRotation` zachowuje **dokładne** wyrównanie słońca i poziomu horyzontu (0° przechyłu),
  podwajając liczbę fizycznie poprawnych układów nieba (3 mapy × 2 = **6 układów**). Leniwe ładowanie tekstury wybranego
  wariantu (`Resources.Load`) utrzymuje w VRAM wyłącznie 1 aktywną mapę.
- **Shader (`Sky.shader`, tylko Clear):** subtelne, zachowujące luminancję zabarwienie cienia chmury chłodnym rozproszeniem nieba
  i oświetlonych wierzchołków ciepłą bielą słońca (`lerp((0,91;0,98;1,13), (1,02;1,00;0,97), smoothstep(0,15;0,85;G))`) oraz
  miękka krzywa krycia `a · (0,68 + 0,32 · a)`. **D100 (nasycenie nieba ×2) nietknięte** (`dk65-fields-nw` błękit: `B−R 94,9 → 93,2`).
  **Overcast nietknięty** (`dk65-fields-nw` bez szyby: `mean diff = 0,00000`, `max = 0,0`).

**3. Koszt GPU i pamięci:**
- **Shader (Clear):** nadal **1** odczyt tekstury (`SAMPLE_TEXTURE2D_GRAD`, **+0** próbek), **0** nowych przebiegów/draw calli/wariantów
  shadera, **+~6** prostych operacji ALU (`smoothstep`, `lerp`, `mul`, `mad`) na piksel nieba Clear (0 na Overcast/Dusk/Night).
- **VRAM:** leniwe ładowanie aktywnego wariantu — w czasie jazdy w VRAM 1 tekstura 4096×2048 BC1/ASTC6×6 (**+0 MB VRAM** względem
  ADR 0108); w paczce buildu +2 skompresowane tekstury (~6,5 MB PNG w repo). Pomiar czasu klatki GPU w playerze Windows: `UNVERIFIED`
  (do sprawdzenia przy następnym pomiarze `pc-metrics`).
- **Dowody i testy:** visual-qa przed|po (`World_knyszyn-w_High`, High PC 1920×1080, clear, overcast, var0/1/2, var1_mirror) w
  `artifacts/agy-clouds-s24/compare/`; EditMode (`ClearCloudsSunTests`, `SkyDisplayCapTests`, `SkyModelTests`, `LightPostPolicyTests`,
  `WindscreenLayer0341Tests`, `WorldSkyBakeTests`) 39/39 passed (1 skipped: brak zaimportowanego kafla C).

## Dopisek 4 codex-clouds-horizon-s24 (2026-11-27) — rzadszy horyzont i wybór chmur w trasie

Krytyk day27, zestaw 5 (P2). Projekcja HDRI ściska obrysy chmur przy horyzoncie, gdzie wyrównanie słońca może też
odsłonić powielony najniższy wiersz mapy. Wcześniejsze wygaszanie krycia kończyło się już przy 0,69°. W `Sky.shader`
istniejące `smoothstep(0, 0.012, d.y)` poszerzono do `smoothstep(0, 0.24, d.y)` (13,9°, `WORKING_VALUE`).
Mnożnik krycia przy 2° / 5° / 10° wynosi teraz 5,7% / 30,0% / 81,3% (poprzednio po 100%). Gładka krzywa
łączy się z pełnym kryciem powyżej 13,9°. Welon Beer–Lamberta wciąż wygasza kontrast do barwy nieba w danym kierunku.
Nasycenie ×2 wg D100 obowiązuje także po tej zmianie.

Dopisek 3 wybierał układ według sceny oświetlenia, która pozostaje sceną startową podczas streamingu. Teraz w świecie
fazę określa środek kafla w metrach EPSG:2180, `floor(E/2048) + 2·floor(N/2048)`. Ziarno, godzina i sektor słońca
przesuwają cykl sześciu układów (trzy mapy CC0 z dopisku 3, każda także w odbiciu w południku słońca).
W aktualnym grafie 54 kafli wszystkie 96 par stykających się kafli mają różne układy, a na 57 wspólnych
krawędziach różni się także mapa. Start jazdy i visual QA korzystają z tej samej kotwicy. Podczas jazdy
zmiana następuje po przesunięciu początku świata przez streamer w głąb kolejnego kafla. Krycie starej mapy
schodzi do zera, po czym krycie nowej wraca do wartości presetu (po 2 s na fazę, `WORKING_VALUE`).
Sceny bez regionu korzystają z hasha nazwy sceny. `rq_cloudvar` i `rq_cloudmirror` nadal działają w A/B.

Koszt według kodu shadera to **+0 ALU, 1 → 1 fotograficzne próbkowanie Clear** i **+0 przebiegów, draw calli oraz
wariantów shadera**. Zmiana progu wykorzystuje ten sam `smoothstep`, a wybór mapy i wygaszanie w czasie liczy CPU
przez istniejący parametr krycia. Po podmianie gra zwalnia poprzednią mapę. Czas klatki i chwilowy szczyt pamięci
podczas podmiany w playerze pozostają `UNVERIFIED`.

Visual QA z `cab-driver`, PC High 1920×1080. Dla tej samej mapy średnie bezwzględne odchylenie od kadru Clear
bez chmur w oknie x=[900,1000), y=[325,400) wyniosło 18,02 → 9,40 sRGB na `knyszyn-w` i 58,31 → 27,92 na `dk65-07`.
W domyślnym Clear (ziarno 0) `knyszyn-w` wybrał mapę 2 bez odbicia, a `dk65-07` mapę 0 z odbiciem. W Overcast
różnica na pełnym kadrze sięgała 1 poziomu sRGB w 1 / 4 pikselach odpowiednio. Obejrzane kadry, logi i pomiary są
w `artifacts/codex-clouds-horizon-s24/`. Import lokalnego cache GLB ostrzegł o 80 / 98 różnicach SHA względem
manifestów. Pary przed i po wykorzystują te same zaimportowane sceny.

Gates po zmianie. EditMode Win64 1517 passed, 0 failed i 116 skipped. Z tego Sky/Cloud i powiązane fixtury
41 passed i 1 skipped. Cztery wskazane pliki testów budżetowych GIS dały 62 passed.
