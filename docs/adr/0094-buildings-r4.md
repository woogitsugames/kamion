# ADR 0094: Zabudowa r4 — balkony jako płyta z balustradą, jednolity tynk, jasna podbitka, daszek pod okapem

Status: propozycja (world-builder, gałąź `worktree-buildings-r12`, z main `fa83f577`), 2026-11-11. Kontynuacja ADR 0091;
odpowiedź na `docs/reports/visual/REVIEW-2026-11-11-s9-0091.md` (P1-1…P1-5, część P2).

## Kontekst
Recenzja 0091 (PASS warunkowy): daszek nad drzwiami przebija połać (P1-1), jasny tynk w „łaty” jak przetarty gąbką
(P1-2), balkony przeniesione na stronę słoneczną zamiast dodane (P1-3), czarna płyta dachu nad skrzydłem domu L (P1-4),
balkony jako ciemne pudła (P1-5); do tego P2 (kolory domów, kalenica, komin, fala dachówki, pieprz na High, cokół na
skarpie, kamery `r10_hall_1` / `r10_shed_2`) i draws Low +3…5 % po r3.

Rozpoznanie na stanie main (`artifacts/buildings-r12/base/`, to samo co r3 z ADR 0091: szary tynk 127,3 / 131,1 przy
niebie 238,2):
- **Łaty tynku są w zestawie `plaster`**, nie w shaderze: skan `painted_plaster_wall` to stara, przemalowywana ściana;
  po r3 zostały w albedo plamy 7–50 cm (pasma 0,08–0,2 m: 1,37 %, 0,2–0,5 m: 1,00 % odchylenia liniowego; razem 3,68 %).
  Mapy AO / normal / makro są przy tym płaskie (AO 0,995, odchylenie normalnej 0,005).
- **„Ciemne pudła”**: z ulicy widać głównie BOKI balkonów (kamera patrzy wzdłuż elewacji), a boki były jednolitą
  blachą z próbki `steel_grey` / `concrete` / `galv`; ramy komórek `balf` miały 92–98 sRGB, tło 0,045.
- **Podbitka**: materiał `hall_flashing` (0,045). Silnik dodatkowo dzieli przez 2 światło otoczenia powierzchni
  patrzących w dół (`sky_occ`, ADR 0060) — pomiar pod wiatrownicą skrzydła w `r10_house_2`: 24/25/26 sRGB przy ścianie 138.
- **„Pieprz” na High nie jest cechą tynku**: w paśmie < 1,5 px samo niebo ma 1,03 poziomu na High i 0,16 na Low
  (ujemna korelacja sąsiednich pikseli) — to dithering + wyostrzanie RCAS profilu High; ściana 2,3 na High, 0,3 na Low.
- Zielony pas nad kalenicą w `r10_shed_2` (P2-2) to szyna ekranu akustycznego: kamera stała za przeszklonym ekranem
  trasy, „szew połaci” to styk paneli ekranu.
- Rzuty domów: 101 prostokątów, 26 czystych „L” (jedno wcięcie), 139 z dwoma i więcej wcięciami, 4 płaskie.

## Decyzja
1. **P1-1 daszek** (`buildings_mesh.py`): daszek nad drzwiami domu jest pomijany, gdy spód dachu nad drzwiami (linia
   ściany i krawędź okapu) leży niżej niż nadproże + 0,4 m — taki okap sam osłania drzwi. 17 domów w regionie.
2. **P1-2 tynk** (`sets_scan.py`, zestaw `plaster`): zmienność tonu grubszą niż ~4 cm spłaszczam o 95 % (było: grubszą
   niż 0,5 m o 85 %), lokalne odchylenia barwy usunięte, detal < 3 cm × 0,22 (było 0,4). Zmienność elewacji ma pochodzić
   ze strefy rozbryzgu i zacieków: `splash_h` tynków 0,6 → 1,2 m (strefę 0,6 m w całości zasłaniał cokół 0,45–0,9 m).
3. **P1-3 balkony**: krawędzie z reguły bazowej r10 (dwie długie krawędzie najdalsze od drogi, nie elewacja wejściowa)
   **plus** reguła słoneczna r3 (SSW, 25 % bloków obie strony). Żadna elewacja, która miała balkony w r10, ich nie traci.
   2369 balkonów w regionie (licznik nowy; liczby dla r3 nie mierzyłem).
4. **P1-4 dach nad skrzydłem** (`roofs.py`): wysięg 0,5 m zostaje na okapach i wiatrownicach, a przy ścianie, od której
   pole dachu ROŚNIE (ściana skrzydła patrząca na kalenicę — „żagiel”), wynosi 0,15 m (`OVERHANG_NOTCH`). Podbitka to
   nowy materiał `soffit_boards` (0,55, bez `sky_occ` powierzchni patrzących w dół); deska czołowa biała
   (`reveal_plaster`) przy dachówce, w kolorze dachu przy blasze. Dach wielopołaciowy z koszami — nie zrobiony (niżej).
5. **P1-5 balkon** (`facade_kit.balcony`): płyta 0,16 m jako osobna bryła, 4 cm przed balustradą; balustrada (front
   **i boki** z tej samej komórki `balf`) 10 cm nad płytą na słupkach narożnych, poręcz 1,10 m; komórki `balf`: ramy
   150–154 sRGB, tło 0,13, jaśniejsze wypełnienia, mniej rdzy; zabudowa balkonu ma boki z komórki `balg` (była czarna
   płyta). Anteny: wysięgnik 0,30 m + maszt 0,42 m, czasza offsetowa, ramię z konwerterem; wszystkie patrzą na azymut
   192° (Hot Bird z Białegostoku, WORKING_VALUE ± 2°) i nie ma ich na balkonach bez widoku na południe.
   Powyżej 2. kondygnacji balkon ma 20 trójkątów (bez ścian widocznych tylko z poziomu balkonu), niżej 42.
6. **P2**: gąsior na kalenicy i narożach (LOD0, materiał dachu, 6 trójkątów na odcinek), obróbka komina idąca po
   spadku; zestaw `roof_tiles`: fala 22 → 12 mm i −14 → −6 % w rynnach, stopień rzędu 18 mm z ciemniejszą linią, ton
   per dachówka ± 10 % i per rząd ± 4 %; dachy: dachówka czerwona / brązowa 5 z 7, blacha grafitowa 2 z 7 (było 2 z 5);
   tynk domów: te same 4 materiały, beż i krem 4 z 6 (było 2 z 4); cokół: jeden ton 0,20 (był 0,16 i 0,25 —
   `plinth_grey` zostaje w tabeli, nieużywany), UV cokołu liczone od terenu przy ścianie (strefa rozbryzgu idzie za
   skarpą); rynny na materiale `downpipe` (ten sam kolor; płaci za `soffit_boards`); kamery: `r10_hall_1` 22 m od ściany,
   `r10_shed_2` poza ekranem (pozostałe kamery bez zmian — plik poprawiony punktowo).
7. Bez zmian w C#, shaderach, `ProjectSettings`, `Packages`. Unia w `WorldPbrMaterials.cs` nietknięta.
WORKING_VALUE: progi 0,4 m i 0,15 m, `splash_h` 1,2 m, kolory komórek `balf`, udziały palet, wymiary anteny.

## Liczby (edytor; nic z telefonu)
Rundy: baza → r1 → r2 → r3 → r3b (r3b = powtórka rundy 3 po dwóch wadach znalezionych w r3: klin wiatrownicy od
cięcia wysięgu po otoczce wypukłej i podbitka 38 sRGB z `plinth_dark`). Stan końcowy = r3b.

Tynk — odchylenie luminancji w pasmach, sRGB, pełny PNG (`bands_screen.py`; własny filtr, nie filtr recenzenta —
porównywać rundy; „przed r3” = render `artifacts/buildings-r11/base` tym samym skryptem):

| prostokąt (High overcast) | pasmo | przed r3 | baza (r3) | r3b |
|---|---|---|---|---|
| biurowiec `r10_fence_2`, między oknami (176) | 3–8 px | 1,23 | 1,90 | **0,61** |
| | 8–24 px | 1,52 | 2,67 | **0,42** |
| | > 24 px | 1,23 | 1,36 | **0,49** |
| | p5–p95 | 10,4 | 15,4 | **4,1** |
| | < 1,5 px (pieprz) | 2,61 | 2,33 | 2,38 |
| szczyt `r10_block_3` (128) | 3–8 / 8–24 px | 0,78 / 0,90 | 1,10 / 1,08 | **0,40 / 0,63** |
| szczyt `r10_block_1` (127) | 3–8 / 8–24 px | 0,92 / 1,15 | 1,28 / 0,93 | **0,26 / 0,40** |

Low overcast, między oknami: 3–8 px 1,08 → 0,32, 8–24 px 1,65 → 0,26. High clear: 0,90 → 0,23, 1,18 → 0,15.
Zestaw `plaster` (albedo liniowe, `bands.py`): razem 3,68 % → 1,26 %; 0,08–0,2 m 1,37 → 0,16 %; 0,2–0,5 m 1,00 → 0,13 %;
p05–p95 w `materials_spec.json` 0,060 → 0,020. Prostokąt „nad oknami” (zacieki pod attyką) zostaje zmienny: p5–p95
24,2 → 18,8.

Tony (`measure.py`, te same prostokąty co recenzja), baza → r3b:

| prostokąt | High overcast | Low overcast | High clear |
|---|---|---|---|
| niebo `r10_block_3` | 238,2 (bez zmian) | — | — |
| szary tynk, szczyt | 127,3 → 128,0 | 121,8 → 122,4 | 106,1 → 106,4 |
| szary tynk, front | 131,1 → 131,9 | 126,2 → 126,8 | 108,0 → 108,4 |
| cokół | 52,4 → 63,9 | 47,1 → 58,1 | 54,8 → 64,0 |
| cegła R/B (`r10_block_4`) | 1,66 (bez zmian) | — | — |

Podbitka i balkony (pełny PNG, `soffit_tone.txt`, `balcony_tone.py`):

| miejsce | baza | r3b | cel recenzji |
|---|---|---|---|
| podbitka pod wiatrownicą skrzydła, `r10_house_2`, High overcast | 24/25/26 | 87/89/84 | ≥ 90 — **brak 3 poziomów** |
| ta sama, High clear / Low overcast | 39 / 22 | 103 / 80 | |
| bok balkonu „brązowy” / ściana, `r10_block_4` | 0,30 | 0,44 | ≥ 0,5 — **niespełniony** |
| bok balkonu „zielony” / ściana (w bazie szara blacha 0,86) | — | 0,68 | ≥ 0,5 |
| bok balkonu z szarej blachy / ściana | 0,79 | 0,83 | ≥ 0,5 |
| front balkonu „zielony” / ściana | 0,71 | 0,94 | ≥ 0,5 |

Podbitka po drodze: biała `reveal_plaster` 72, materiał ściany 70–73, `plinth_dark` 38 — dopiero materiał bez `sky_occ`
dał 87.

Budżet Low na kamerach kontrolnych (`stats.txt`, estymata edytora przed SRP batching; 57 kamer bez dwóch
przestawionych), baza → r3b (`budget.py`):
- draws: suma 16 982 → 16 643 (**−2,0 %**); żadna kamera nie jest gorsza niż w bazie (najgorsze 0,0 %:
  `dk8-dk19-exit` 81 → 81, `r10_house_1/2` 144 → 144); `r10_fence_1` 318 → 312, `putry-above` 302 → 297,
  `r10_block_3` 387 → 379, `r10_block_1` 465 → 456. Kamer > 400 draws: 10 → 10. **`dk8-dk19-exit` nie odzyskana**
  (w kadrze nie ma zabudowy tego zadania).
- trójkąty: suma 15 071 → 15 113 tys. (**+0,3 %**), najgorsza `fire-station-ref7197` 319 → 326 tys. (+2,2 %), kamery
  bloków +1,8…2,0 % (limit +3 %). W r1 było +4,6…5,0 % — stąd odchudzenie balkonów wyższych kondygnacji.
- Region (GLB): High 4085 → 4025 submeshy, 13,941 → 13,959 mln trójkątów (+0,13 %); Low 3024 → 3004 submeshy,
  4,489 → 4,490 mln (+0,02 %). Zabudowa LOD0 800,8 → 818,3 tys. (+2,2 %), LOD1 79,5 → 79,9 tys.
- Tekstury: rozmiary zestawów bez zmian (te same rozdzielczości i formaty).

Testy: `pytest tests/gis` na stanie końcowym (r3b) — 352 passed, 2 xfailed (345 + 7 nowych w `test_buildings_r4.py`;
baza w tym worktree zielona; tak samo na r3). EditMode na stanie r3: 212, 209 passed, 3 failed — `TruckDoorGlassTests`
× 3 (materiał ciężarówki, te same nazwy co w ADR 0091; czy padają na main — nie sprawdzałem w tej sesji, UNVERIFIED);
w tym zadaniu nie zmieniono żadnego pliku C#, po r3 zmienił się tylko Python.

Dowody: `artifacts/buildings-r12/{base,r1,r2,r3,r3b}/<Tier-light>/` (PNG, `1280/*.jpg`, `stats.txt`), w każdej rundzie
`measure_*.txt`, `bands_*.txt`, `budget.txt`, `chunk_mats.json`, arkusze `sheet_*.jpg`; skrypty `measure.py`,
`bands_screen.py`, `bands.py`, `budget.py`, `balcony_tone.py`, `chunk_mats.py`, `chain.ps1`.

## Samokrytyka (docs/06)
- **Bez oceny `visual-critic`** (zakaz subagentów w zadaniu) i bez telefonu. Rund było 3 + powtórka trzeciej (r3b):
  w r3 sam wprowadziłem dwie wady (klin wiatrownicy, podbitka 38), których nie mogłem zostawić. Ostatnia zmiana kolorów
  trzech komórek `balf` weszła do r3b bez osobnej rundy — obejrzana tylko raz.
- **Cele liczbowe niespełnione**: podbitka 87 zamiast ≥ 90; bok balkonu z brązowej blachy 0,44 zamiast ≥ 0,5 (boki stoją
  w cieniu płyty wyżej — na jasnej ścianie kolorowe wypełnienia nie dojdą do 0,5 bez wyprania koloru).
- **Dach wielopołaciowy nie zrobiony.** Skrzydło domu L dalej leży pod jednym polem wysokości: nie ma koszy, ściana
  skrzydła rośnie pod połać, a jej krótki okap to obróbka, nie okap. Tylko 26 z 270 rzutów to czyste „L”; 139 ma kilka
  wcięć — potrzebny jest ogólny rozkład rzutu na prostokąty, nie przypadek szczególny.
- **Balkony dalej wg reguły, nie danych.** `r10_block_1` i `r10_block_3` pokazują elewacje bez balkonów (nie miały ich
  też w r10). Zdjęcia CC0 bloków przy Putry pokazują galerie na całej długości — „obie długie strony wszędzie” kosztuje
  trójkąty, których w budżecie +3 % nie ma.
- **Tynk jest teraz niemal jednolity** (zestaw 1,26 %): z 2 m ściana może wyglądać jak czysta farba; ziarno niesie
  tylko mapa normalnych (relief 0,4 mm). Zacieki pod attyką zostały bez zmian (siła × 0,6), strefy rozbryzgu nad
  cokołem nie zmierzyłem osobno.
- **Pieprz na High bez zmian** (2,33 → 2,38): źródłem jest łańcuch post-process profilu High, nie zabudowa — nie
  ruszałem `WorldPBR.shader`.
- **Domy**: 4 tony, z czego beż i krem z daleka są jednym kolorem, a biel i jasna szarość drugim; w kadrach `r10_house`
  po r3b wszystkie bliskie domy wypadły kremowe. Wariant z 7 tonami (r1 / r2) dawał widoczną różnorodność, ale kosztował
  8–10 draws na kamerach z domami względem r3b (wciąż poniżej bazy na większości kamer, +1,0…1,3 % na dwóch).
- **Cokół na skarpie** (`r10_block_5`): jaśniejszy (52 → 64) i rozbryzg idzie za terenem, ale 2 m ściany to dalej jedna
  płaszczyzna — efekt rozbryzgu na ciemnym cokole jest ledwo widoczny.
- Biała ściana w świetle „clear” jest przepalona (254 w `r10_house_2` w r1 / r2) — sprawa ekspozycji presetu, nie tego ADR.
- Gąsior i obróbka komina oglądane tylko z kamer kontrolnych (10–30 m); z bliska nie sprawdzone.
- Build w tym worktree nie jest bitowo równy zatwierdzonemu `generated/` na main już dla niezmienionego kodu (np.
  1500 → 1526 miejsc parkingowych) — różnica danych worktree; po scaleniu regenerować na main.

## Otwarte / do decyzji lidera
- Ocena `visual-critic` i telefon (A16) dla draws.
- Podbitka: 3 poziomy do celu — albedo `soffit_boards` 0,55 → 0,62 albo zgoda na 87.
- Paleta domów: 4 tony (stan) czy 5–7 (koszt draws podany wyżej).
- Dach wielopołaciowy domów o złożonym rzucie; balkony wg zdjęć właściciela.
- Pieprz High: dithering / RCAS w `QualityProfile` (właściciel renderingu).
- Po scaleniu: `build_all.py --only plaster,roof_tiles,facade_atlas,facade_far`, `build_world`, `import-region`.
