# ADR 0124: Zabudowa r8 — działki z bliska i ulica mieszkaniowa (brama tylko z dojazdem, pas zjazdu jako wielokąt, strefy drzwi, atlas v2 + shader `PlotKit`, krawężnik 10 cm, przewody, zacieki, lusterka)

Status: propozycja, **runda r1 — jedna iteracja wizualna, przerwana limitem sesji** (world-builder, gałąź `buildings-r8`, z main
`3540bbdf`), 2026-11-11. Kontynuacja ADR 0114; odpowiedź na `docs/reports/visual/REVIEW-2026-11-11-s10-0114.md` (P1-r8-a..i,
P2-r8-b/e). Referencje: `docs/refs/posesje-bialystok.md` (oglądane; żaden piksel nie wchodzi do tekstur). Nic z telefonu,
bez `visual-critic`.

## Decyzja
1. **Brama tylko tam, gdzie krawężnik da się obniżyć** (`plots.gate_access`, `plan_access`): dojazd = jezdnia w zasięgu 14 m
   na wprost bramy ORAZ łańcuch drogi (nie łata skrzyżowania, nie koniec łańcucha; całe obniżenie z rampami leży na łańcuchu).
   Inaczej brama jest przesuwana wzdłuż frontu co 0,75 m (najbliższe miejsce), a gdy żadne nie działa — front dostaje samą
   furtkę naprzeciw drzwi. Front działki sięga teraz do ulicy (`FRONT_M` 2–9 m → 2,6–30 m): 13 bram r7 stało 15–25 m przed
   jezdnią.
2. **Pas zjazdu przed krawężnikiem jako wielokąt** (`_verge_overlay`): szerokość bramy ∩ ślad drogi (+0,35 m zakładu na
   podjazd) − jezdnia − kamień krawężnika (0,17 m). Zero kostki na asfalcie, obniżony krawężnik zostaje krawężnikiem, krawędź
   to prawdziwa linia (triangulacja wielokąta, nie schodki komórek siatki). Nawierzchnie jednej działki (podjazd, płyta
   przed garażem, dojście) są jedną unią; trawnik = działka − unia.
3. **Strefy drzwi** (`plots.door_zones`, te same reguły co `buildings_mesh`: elewacja główna = krawędź najbliższa drogi, drzwi
   w środkowym przęśle, bramy garażu szopy): schody wejściowe (1,6 × 2,1 m) i 5,5 m przed bramą garażu wycinają płot; dojście
   od furtki prowadzi do stóp schodów; brama celuje w bramę garażu, gdy ta patrzy na ulicę.
4. **Atlas `plot_kit` v2 + własny shader**:
   - rzędy płotów parami w jednym paśmie (połowa szerokości = 5,12 m = jeden panel, panel nigdy nie zawija); zwolnione 450 px
     niosą karty roślin: 3 tuje, 2 świerki, duże drzewo, rząd żywopłotu, nowy rząd szarych, niemalowanych desek;
   - iglaki ze **sfotografowanych gałązek Poly Haven `fir_tree_01` (CC0)** — wycięte po składowych, sprowadzone do
     luminancji i zabarwione na paletę tui / świerka kłującego; liście drzew liściastych nadal rysowane (soczewka z nerwem,
     stemplowana w kępach) — w repo nie ma fotografii liścia CC0;
   - tuja = 5-boczny rdzeń z kopułą + 2 skrzyżowane karty sylwetki (≤ 40 tris, było 36–60), świerk = 3 karty + pień
     (14 tris, było do 108), duże drzewo ogrodowe 7,5–12,5 m, żywopłot za płotem ażurowym;
   - `Kamion/World PlotKit` (`Environment/Shaders/WorldPlotKit.shader`, model `Kamion/Vegetation`): `COLOR_0.a = 0` —
     twarda powierzchnia, normalna odwracana na tylnej ścianie (**jedna karta na panel płotu**, koniec „ducha” grotów),
     `rgb × 2` = tint starzenia działki; `a = 1` — roślina, `rgb` = normalna od osi rośliny (karty jednej rośliny cieniują
     się jak bryła, bez szwu). Materiał wskazuje shader kluczem `shader` w `materials.py` (importer: `RegionImporter`).
5. **Ulica domów**: krawężnik **10 cm** (`apply_house_kerbs`, przez istniejący hak `pipeline.build(side_edit=)` — bez zmian
   w `roads/*.py` poza `build_world.py`) na łańcuchach z ≥ 2 zjazdami i półszerokością jezdni ≤ 4 m, ostatnie 4 m przed łatą
   skrzyżowania wracają do 13 cm; **przewody napowietrzne** (`street_wires`, warstwa `wires`): wiązka od słupa do słupa po
   istniejących latarniach strony z większą liczbą lamp + przyłącze do ściany każdego domu — REGUŁA (OSM nie ma
   `power=minor_line` w kaflu, BDOT `OT_SULN_L` to tylko SN/WN), bez nowych słupów; **zużycie**: tint działki wg klasy wieku
   (old 0,80 ± 0,14 … new 1,0 ± 0,04), przechył słupków do 3° (old) / 1,2° (prl), mech / zacieki / wykwity w rzędach cegły,
   betonu i muru, siatka z brzuchem i rdzą; **zieleń**: 462 krzewy (253), 64 jabłonie (54), 15 dużych drzew, 477 m żywopłotu.
6. **Zacieki** (`WorldPBR`, blok sill v ≥ 112): per KONIEC parapetu — 28 % końców bez śladu, własna długość 0,35–1,0 i siła
   0,6–1,0; plama 15 cm pod zaślepką zwężająca się do 3,6 cm, boki rozmyte 5–9 cm, wejście na 3 cm (bez twardej górnej
   linii), wędrówka w bok; co piąty parapet kapie też ze środka; podłoga siły 0,5 → 0,62.
7. **Lusterka**: geometria kitu w osobnym węźle chunka `plots` (ta sama liczba draws co submesh `furniture`);
   `Game.World.PlotViewCull` wyłącza węzły `plots` / `plot_ground`, których bounds leżą > 70 m od kamery z
   `IExtraViewCamera` (lusterka, kamera cofania). Ziarno = chunk 256 m: działki chunka, przez który jedzie ciężarówka,
   zostają w lusterkach. `SceneStats` uwzględnia to w szacunku.

WORKING_VALUE: wszystkie progi i udziały powyżej, 10 cm, 70 m, wysokość wiązki 7,4 m, paleta atlasu.

## Liczby (edytor, szacunek przed batchingiem SRP; nic z telefonu)
Rundy w `artifacts/buildings-r16/`: `base` (= main `3540bbdf`, r7), `r1`. `budget2.py`, 67 kamer, overcast.

| r1 względem bazy (r7) | Low | High |
|---|---|---|
| draws MeshRendererów, suma / najgorsza | −6 / +2 | −49 / +3 (`trailer-34`) |
| draws instancjonowane, suma / najgorsza | −6 / +2 | −7 / +1 |
| razem, suma / najgorsza kamera | **−12 / +3** (`r10_block_3`, `r10_block_4`) | **−56 / +3** (`trailer-34`) |
| `r10_house_1` / `r10_house_2` (najgorsze r7: +11 / +10 względem świata bez działek) | −4 / −4 → ok. +7 / +6 | — |
| draws cieni MeshRendererów, suma | −32 | −123 |
| trójkąty siatek (k), suma | −8 | −46 |
| `cab-mirror-front` (widok główny z kabiny) | — | 954 → 954 draws, 1264 → 1265 k tris |
| `cab-mirrors-right` (widok główny z kabiny) | 303 → 304 inst. | 827 → 829 draws, 1138 → 1139 k tris |

Przyrosty +1…+3 to nowy węzeł `wires` w chunkach, które nie miały przewodów. Odniesienia „świat bez działek” w tej rundzie
NIE budowano — „+7” to r7 (+11 wg ADR 0114) minus zmierzona różnica, nie pomiar bezpośredni.

| inne | wartość |
|---|---|
| region High / Low: submeshe, mln tris | 4085 / 14,21 → 4073 / 14,167; 3066 / 4,609 → 3054 / 4,515 |
| `plot_kit` trójkąty | 56 964 → 52 022 |
| działki / bramy / furtki | 99 / 43 (r7: 48) / 131; bramy przesunięte 11, zamienione na furtkę 5 (3 bez jezdni, 2 łata skrzyżowania) |
| zjazdy z obniżonym krawężnikiem | **43 z 43** (r7: 28 z 48); `drop_check_r2.txt`: każdy obniżony o 10 cm do 3 cm nad rynsztokiem; miara „maks. z krawężnika − mediana asfaltu w 1,2 m” daje 3,0–8,0 cm (40 z 43 < 6 cm; reszta to spadek poprzeczny w promieniu pomiaru) |
| krawężnik ulic domów | 5 łańcuchów, 1573 m; 8 m obok zjazdów mediana 10,5 cm (p10 10,0, p90 13,1 — końce przy łatach) |
| przęsła płotu przecinające strefę schodów / bramy garażu | 0 |
| przewody | 6 łańcuchów, 15 przęseł, 469 m, 22 przyłącza, 370 tris; 1 łańcuch bez lamp (bez przewodów) |
| testy | `tests/gis/test_buildings_r5..r8` 36 passed (r8: 6 nowych). **Pełny `pytest tests/gis`, `fidelity/run.py` i EditMode NIE uruchomione** |

## Samokrytyka (docs/06) — co widać w renderach r1
- **Jedna runda, bez poprawek po obejrzeniu.** Obejrzane: `r10_house_2` Low, `r16_drive_0/1`, `r16_kerb_0`, `r16_cab_0`,
  `r16_door_0`, `r16_garden_0`, pary `ref_chainlink_P10`, `ref_brick_bars_P24`, `ref_cab0_P08`, `base_r14_plot2_eye_az70`.
  Reszty z 59 kamer przeglądowych i `extra_low` nie obejrzałem.
- **P1-r8-b zamknięte tylko częściowo**: kostka nie leży już na jezdni i krawężnik jej nie przebija, ale na zjazdach skośnych
  do drogi nadal widać **klin trawy między płytą podjazdu a pasem przy krawężniku** (`r16_kerb_0`, `ref_brick_bars_P24`) —
  zakład 0,35 m nie wystarcza, gdy ślad drogi jest szerszy niż profil z nawierzchnią.
- **Żywopłot ma za duże liście** (z 5 m czytają się jak ~20 cm, `ref_brick_bars_P24`) i wygląda jak tapeta — do zmniejszenia
  skali stempla i dodania nieregularnej góry w geometrii.
- **Tuje**: sylwetka miękka i zaokrąglona, ale rdzeń ma rozciągniętą w pionie teksturę (pionowe smugi, `r16_door_0`).
  **Jabłonie** bez szwu światła, nadal czytelne jako skrzyżowane karty z rysowanymi liśćmi. Świerków i dużych drzew z bliska
  nie obejrzałem.
- **Zacieki niezmierzone** (para Runoff on/off i `sill_marks.py` nie uruchomione): cel „najsłabsze 10 % ≥ 6 poziomów z 20 m”
  jest NIEZWERYFIKOWANY; kształt nieobejrzany.
- **Koszt kamer RT lusterek niezmierzony**: `cab-mirror-front` / `cab-mirrors-right` w `stats.txt` to widok główny z kabiny,
  nie lusterka (recenzja 0114 przypisała je lusterkom). `PlotViewCull` jest w scenie, ale `MirrorCostProfiler` z
  `PlotViewCull.Enabled` on/off nie został uruchomiony — oszczędność w lusterkach nieznana.
- Garaż z `r10_house_2`: płot już go nie przecina, ale przed bramą nadal jest głównie trawnik (płyta przed garażem nie
  łączy się z podjazdem).
- Siatka na Low nadal blada / prawie niewidoczna (P2-r8-a nietknięte). Mur i beton nadal skosem po terenie (P2-r8-d).
- Kamery `r16_door_*` i `r16_garden_*` są źle ustawione (ściana w kadrze) — do poprawy.
- Podjazdy do 14 m długości przez pas między płotem a jezdnią (5 zjazdów > 10 m) — wyglądu nie sprawdziłem.
- Działki nadal z reguły, nie z EGiB; przewody z reguły, nie z danych.

## Pliki wspólne (addytywnie)
`materials.py` (klucze `vertex_color`, `shader` w `plot_kit`), `stage.py` (`items=pl.items`), `build_world.py` (LAYERS / NODES
+ `plots`, hak `_plot_side_edit`, estymator liczy `plots`), `RegionImporter.cs` (warstwa `plots`, klucz `shader`),
`WorldSceneBuilder.cs` (tabele LOD, cienie, `PlotViewCull`), `WorldSkyBake.cs`, `SceneStats.cs` (1 linia), `WorldPBR.shader`
(blok sill). Nowe: `WorldPlotKit.shader`, `World/Runtime/PlotViewCull.cs`, `tests/gis/test_buildings_r8.py`.
Nie ruszone: `roads/*.py` poza `build_world.py`, `furniture.py`, bariery, krawężniki tras głównych.

## Otwarte / następna runda
1. Klin trawy na zjazdach skośnych; płyta przed garażem połączona z podjazdem.
2. Skala liści żywopłotu, UV rdzenia tui, obejrzeć świerki / duże drzewa / `extra_low`.
3. Pomiar zacieków (5 m, 20 m) i lusterek RT; pełny `pytest tests/gis`, `fidelity/run.py`, EditMode.
4. `visual-critic`, A16 Low; wpis `fir_tree_01` (CC0) dla `plot_kit` w `docs/LICENSES.md` jest dodany — raw poza gitem,
   przy braku pliku atlas spada do rysowanych gałązek (`plot_kit.SOURCE`).

## Runda r2 (s11 / s12) — po scaleniu main `76b3fb76`
Rundy: `r2`, `r2b` (kod r2 przed scaleniem), `r2c` (po `git merge main`, świat i import od zera). Dowody: `artifacts/buildings-r16/r2c/`.

**Zmiany r2**
- **Błąd metody r1**: `-Scene WorldC -Tier High` to treść LOW w jakości High (LOD0 budynków tylko ≤ 60 m od trasy). Prawdziwa treść
  High = `-Scene WorldC_High` (`extra_hc`). Tabela „High” z r1 opisuje więc treść Low w jakości High.
- LOD1 domów (Low, > 60 m od trasy): okna i drzwi jako ciemne quady 5 cm przed ścianą (`buildings_mesh.LOD1_HOUSE_OPENINGS`),
  w materiale, który chunk już ma — nigdy własny draw.
- Klin trawy na zjazdach: pas zjazdu prostokreślny, nie niżej niż grunt w 0,8 m + 3 cm; grunt działki czyta wysokości drogi na śladzie
  (`plots._verge_overlay`). `r16_drive_0..3`, `r16_kerb_0/1`: klina nie widać.
- Mur / beton / podmurówka: przęsła poziome, schodkowane na słupkach (P2-r8-d).
- Żywopłot: stempel liścia 7,5 → 3,6 cm w atlasie (WORKING_VALUE; rząd 1,5 m rozciągany do ~2,1 m dawał liść ~18 cm) — `r2c/sheets/hedge_r2b_vs_r2c.jpg`.
- Scalenie: `RegionImporter.cs` — unia `car_plate` (`PreserveLitPasses`) + klucz `shader`; generated odtworzone.

**Liczby r2c (edytor, szacunek przed batchingiem SRP; nic z telefonu)**, `budget2.py`, overcast:

| względem r1 | Low (67 kamer) | „High” = treść Low, jakość High (67) | `extra_hc` = treść High (59) |
|---|---|---|---|
| draws MeshRendererów, suma / najgorsza | **+0 / +0** | **+0 / +0** | −296 / +217 (`r16_garden_0`, kamera przestawiona) |
| draws cieni MR, suma | +0 | +0 | −141 |
| draws instancjonowane, suma / najgorsza | −160 / +9 | −546 / +9 | — |
| trójkąty siatek (k), suma / najgorsza | +191 / +15 | +315 / +16 | −580 |

Zmiana własna tej gałęzi (r2b względem r1, ten sam main): draws MR i instancjonowane **+0 / +0** na obu tierach. Różnice instancji
(−160 / −546, najgorsza +9 `r10_block_1`, `driver-andersa-to-putry`) i część trójkątów pochodzą z treści main s11 (r2c względem r2b).
Kamery `r16_door_*` / `r16_garden_*` w `extra_hc` stoją w innych miejscach niż w r1 — ich delty nie są porównaniem tej samej sceny.
Region: High 4073 submeshy / 14,184 mln tris, Low 3054 / 4,532 mln (r1: 4073 / 14,167; 3054 / 4,515).

| testy (po regeneracji r2c) | wynik |
|---|---|
| `pytest tests/gis` (pełny) | **624 passed, 1 xfailed**, 858 s (testy świeżości zielone) |
| EditMode | **317 / 317** |
| `fidelity/run.py` | exit 0 |
| zacieki, 20 m (r1 na `WorldC_High`, para Runoff on/off) | mediana 9,1 poz. sRGB, p10 5,5 (cel ≥ 6 — o 0,5 poniżej); 5 m: 14,5. Po r2 nie powtórzone |

**Samokrytyka r2c** (obejrzane: `r2c/sheets/*.jpg`, `pairs_r2c/ref_*`)
- Układ ulicy domów (płot — zjazd z kostki — obniżony krawężnik — dom ze spadzistym dachem — przewody na słupach) czyta się jak na
  zdjęciach Mapillary P08 / P09 / P24; brakuje tego, co na zdjęciach dominuje: wysokich drzew i gęstej zieleni przy płotach.
- Żywopłot: liście już w skali, ale płaska „półka” wierzchu wystaje ponad boki (widać ją jako poziomy pasek) — do poprawy w geometrii.
- LOD1 na Low: otwory czarne, bez ram — z bliska (`extra_low/r16_cab_*`) czytelne jako uproszczenie; z trasy (> 60 m) wystarcza.
- Tuje: rdzeń nadal z pionowymi smugami; jabłonie nadal jak karty. Wiata w `r16_garden_0` ma zbyt cienkie słupy / dach bez grubości.
- Kamera `r16_door_2` stoi przy ścianie (do przestawienia). Lusterka RT (MirrorCostProfiler) nadal niezmierzone. Bez telefonu.
