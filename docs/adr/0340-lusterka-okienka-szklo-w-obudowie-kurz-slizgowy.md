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
