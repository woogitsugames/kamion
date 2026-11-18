# Kamera z fotela kierowcy — warianty do wyboru (D84 / P1-4, agent cab-view-s24, 2026-11-18)

Render: edytor, `visual-qa.ps1 -Scene WorldC_High -Tier High -Pc -Lighting clear`, 1920×1080, region bialystok-industrial-c,
TRAKT zbudowany z main (cab LOD0 przebudowany Blenderem w tym worktree). Edytor ≠ build (FPS nie mierzone, nie dotyczy).
- `start/` — pozycja startowa WorldC (E 729.6, N −395.8 w Unity, kurs 209,4°), wszystkie warianty z tego samego miejsca.
- `rondo/` — Rondo Bieżeństwa: **poza statyczna** na pierścieniu (środek E 554.676 N −716.554, r 23.362 m z `gate3_cameras.json`;
  θ = 100°, kurs styczny 260°, przeciwnie do wskazówek zegara), naczepa sztywno na wprost (bez przegubu) — to nie klatka z jazdy fizyką.
- `*-hud.png` — ta sama kamera z HUD i okienkami lusterek klasy II (D70, `ControlSettings.mirrorInsets`, domyślnie WŁĄCZONE) = tak widzi gracz.
- `small/` — podglądy 960 px; `start/audit.tsv`, `rondo/audit.tsv` — geometria lusterek i górnej krawędzi szyby względem kadru.

## Parametry z kodu
- Oko: `DriverEyePoint` = `art-source/truck/dims.json driver_eye_point_m` [−0,55; 0,45; 2,50] m (x lewo-prawo, y za podstawą szyby, z wysokość) —
  WORKING_VALUE; offset 635 mm nad punktem R — SOURCED (UNECE R46). Wszystkie warianty: to samo oko.
- Pochylenie spoczynkowe: `DriverHead.RestPitchDownDeg` = 6° (WORKING_VALUE).
- **FOV gry dziś = 55° pionowo** (`ControlSettings.cabFov`), nie 62°: 62° ma tylko kamera QA `cab-driver`.
- **Suwak FOV już jest**: Ustawienia → „KAMERA (WIDOK Z KABINY)” → „Pole widzenia”, 45–75° co 5° (`UI/ControlSettingsPanel.cs:228`). Nie trzeba nowego UI.
- FOV poziome przy 16:9 = 2·atan(tan(v/2)·16/9) (z `CabViewVariants.HorizontalFov`, wypisane w audit.tsv).

## Geometria lusterek (zmierzone z siatek LOD0, audit.tsv; kąt od osi wzdłużnej kabiny, ujemny = lewo)
| obiekt | odchylenie poziome | wysokość kątowa |
|---|---|---|
| główne L (MainL) | −53,7…−63,2° | −6,6…+17,1° |
| szerokokątne L (WideL) | −53,6…−62,0° | −19,4…−8,5° |
| główne P (MainR) | +71,9…+76,4° | −3,3…+8,8° |
| szerokokątne P (WideR) | +72,0…+75,8° | −10,2…−4,5° |
| przednie (Front) | +49,1…+57,0° | +9,0…+12,7° |

Żeby zobaczyć całe lewe lusterko główne patrząc prosto, potrzeba poziomego FOV ≥ ~127° (pionowe ≈ 98° przy 16:9) — zniekształcenie
perspektywy nie do przyjęcia. Prawe (+76°) — ≥ 153°. **Samo FOV nie wstawi lusterek bocznych do kadru**; robią to okienka D70 lub rozglądanie.

## Warianty
| wariant | FOV pion./poz. (16:9) | pochyl. | lusterko L | lusterko P | daszek / górna część szyby | zegary | droga | ocena (docs/06) |
|---|---|---|---|---|---|---|---|---|
| 0 `cab-view-0-fov55` (gra dziś) | 55° / 85,6° | 6° | nie (0 %) | nie | nie (pas frytu poza kadrem) | częściowo, dół zegarów ucięty | dużo, b. dobra czytelność dali | najbardziej „pusty”: słupek A ledwo, brak kabiny nad szybą; teleobiektyw |
| A `cab-view-a-fov62` (= QA cab-driver) | 62° / 93,8° | 6° | nie (0 %) | nie | nie | całe zegary w okienku kierownicy | dużo | stan z recenzji P1-4: kabina ~20 % kadru |
| B `cab-view-b-fov70` | 70° / 102,4° | 6° | nie (0 %; lusterko przednie geometrycznie 11 % przy prawej krawędzi, w renderze nierozróżnialne) | nie | róg daszka pasażera w prawym górnym rogu; słupek A i szyba drzwi L widoczne | całe + przełączniki | dobra, perspektywa naturalna | kabina „otacza” kadr, bez widocznej dystorsji brzegów |
| C `cab-view-c-fov75` (max suwaka) | 75° / 107,5° | 6° | brzeg obudowy (3 % główne, 15 % szerokie geometrycznie) — w renderze praktycznie słupek | nie | pas frytu u góry szyby + daszek pasażera | całe | droga mniejsza, dal oddala się | najwięcej kabiny; brzegi lekko rozciągnięte, odległości wydają się większe (gorzej z oceną dystansu przy hamowaniu) |
| D `cab-view-d-fov70-p10` | 70° / 102,4° | 10° | nie | nie | słabiej niż B (wzrok niżej) | całe + przyciski kierownicy + ekran nawigacji P | horyzont wyżej w kadrze, mniej nieba | więcej deski/kierownicy (≈ cab-driver-ab10 z s23) |

Wszystkie warianty z HUD (`*-hud.png`): okienka lusterek L/P widoczne zawsze (górne rogi). **Uwaga P2 (nowe)**: dolny panel HUD
(prędkość, bieg, ciśnienie) zasłania fizyczny zestaw wskaźników w okienku kierownicy przy każdym wariancie — dubluje informację i chowa
najlepiej wykonany element kabiny; do rozważenia przesunięcie panelu albo ukrywanie go w widoku z kabiny na PC.

## Rekomendacja
Wariant **B (70°, pochylenie 6°)** jako domyślne na PC: kabina wypełnia brzegi kadru (słupek A, szyba drzwi, daszek), a perspektywa drogi
pozostaje naturalna; 75° zostaje na suwaku dla chętnych. Lusterka boczne zapewniają okienka D70 (domyślnie włączone) — FOV ich nie rozwiąże
(geometria wyżej). Wartości WORKING_VALUE do potwierdzenia zdjęciem z fotela (docs/07 §4) i feel testem właściciela.

## Przełączenie po decyzji (bez implementacji teraz)
- FOV: jedna liczba — `ControlSettings.cabFov` domyślnie 55 → wybrana (zapisane ustawienia graczy zostają; ewentualna migracja schematu
  tylko jeśli właściciel chce nadpisać stare 55). Kamera QA `cab-driver` (62°) wyrównać do tej samej wartości.
- Pochylenie: `DriverHead.RestPitchDownDeg` (6°), wspólne dla gry i kamer QA.
- Warianty QA: `game/Assets/_Project/Camera/CabViewVariants.cs` (lista), kamery `cab-view-*` dodaje `TruckAssetBuilder.AddControlCameras`.
