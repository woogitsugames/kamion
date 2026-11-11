# ADR 0092: Kwadrat Park r12 — plandeka, zamknięcie bramy, moduł płyty na ścianie hali

Status: propozycja (world-builder, gałąź `worktree-kwadrat-r12`), 2026-11-11. Kontynuacja ADR 0071 (r10, r11); odpowiedź
na `docs/reports/visual/REVIEW-2026-11-11-s9.md` §4 (0071 r11 — PASS warunkowy, P1 × 3, P2 × 3).

## Kontekst
Recenzja r11: (P1) firanka naczepy przy doku 3 „odbija jak polerowana blacha”; (P1) szlaban da się objechać z obu
stron, brak tablicy; (P1) ściana hali w słońcu — „miękkie obłoki” dryfu makro 0,12, pas okien czysty; (P2) ślady opon
jak plamy cienia, wyspa czysta z jednym słupkiem, agregat chłodni jako biały sześcian.

## Diagnoza (zmierzone / przeczytane z kodu, nie zgadywane)
1. **Firanka.** Zestaw `curtain_folds` niesie w MaskMap gładkość średnio 0,364 (`materials_spec.json`,
   `smoothness_mean`), metaliczność 0. Manifestowe `rough` (0,7) nie było nigdzie czytane. W cieniu hali rozproszenie
   ciemnego PVC (albedo 0,20) jest słabe, a człon środowiskowy przy kącie ślizgowym w `WorldPBR.shader`
   (`grazing = smooth + F0`, sonda przy chropowatości 0,64) rysuje na plandece czytelną linię horyzontu. To nie metal —
   to za gładka i za mało rozmyta odbitka nieba.
2. **Brama.** W wygenerowanym świecie oba pasy leżą w płaskiej kostce `yard_behaton` od granicy do granicy
   (`artifacts/kwadrat-r12/topdown_gate_before60.png`): 37 m na zachód, ok. 18 m na wschód. Podpory ramion stały na
   tej kostce. Ortofoto GUGiK 2024-05-27 (0,25 m; `ortho_gate.jpg`, `ortho_gate_zoom.jpg`): po wschodniej stronie pasa
   wjazdowego wąski jasny pas z krawężnikiem (ok. 1,5 × 18 m) z dwoma słupami — cienka linia ramienia kończy się na jego
   północnym końcu; po zachodniej stronie pasa wyjazdowego trawnik z krawężnikiem i drzewem. Linii ogrodzenia ani
   tablicy nie widać; zdjęcie CC0 `20210904_101250` (Rakoon) nie obejmuje szlabanu.
3. **Ściana.** Dryf tonu to próbka mapy makro w `pw.xz / 64 m` — gładki szum bez związku z podziałem okładziny.
   Zaciek pod parapetem pasa okien istniał od r11 (TEXCOORD_1 liczony od parapetu), ale był tą samą warstwą co pod
   attyką, w jej słabym początku: z 20 m nieczytelny.
4. **Słupki wyspy.** Były dwa (r11), drugi zasłonięty szafami szlabanu w kadrze bramy.

## Decyzja
1. **Plandeka PVC (P1).** `WorldPbrMaterials`: dla `trailer_curtain_*` `_SmoothnessScale` = (1 − `rough` z manifestu) /
   `smoothness_mean` zestawu. Manifest: `rough` 0,82 (PVC matowe), 0,72 (plandeka srebrna); metaliczność 0
   (`_MetallicScale` 0 jak dotąd). WORKING_VALUE, oceniane na renderach doków.
2. **Zamknięcie bramy (P1)** — w `authored_overrides` (`kwadrat-park-gate-kit`), przeżywa regenerację:
   - `side_strips`: podniesiony pas z krawężnikiem po ZEWNĘTRZNEJ stronie każdego pasa na linii szlabanu; podpora
     ramienia stoi na nim (wjazd: kostka, 1,5 m; wyjazd: trawnik, 2,2 m). WIDZIANE na ortofoto (kształt); położenie
     wzdłuż krawędzi WYGENEROWANYCH pasów (OSM leży tu 3–5 m obok ortofoto) — ±5 m.
   - `closure`: od pasa prostopadle do końca utwardzonego placu: wschód — słupki stalowe co 1,5 m + ściana kolizyjna
     (ortofoto pokazuje tam otwartą kostkę, bez cienia ogrodzenia), zachód — ogrodzenie panelowe na podmurówce w stronę
     parkingu wieżowca. **WORKING_VALUE** (nie widać na ortofoto, brak otwartego zdjęcia z ziemi) — potrzebne, żeby
     szlaban był bramą. Linie zamknięcia są eksportowane do QA i wyłączają miejsca postojowe reguły w pasie 1,6 m.
   - Wszystko w warstwie `paved` (wyspa r11): część w `furniture` wciąga całą siatkę mebli chunku w kadr bramy.
   - **Tablica przy bramie: nie zrobiona — brak źródła** (ortofoto 0,25 m jej nie pokazuje, brak zdjęcia). Otwarte.
3. **Ściana hali (P1).** Nowy wariant `_PANELTONE` w `Kamion/World PBR`: dryf makro próbkowany raz na płytę (w środku
   płyty, w metrach UV0 ściany) + udział skrótu na płytę 0,35 + cienka linia styku czołowego co długość płyty,
   wygaszana gdy piksel jest szerszy niż 12 mm. Manifest `kp_wall.panel_m: [6.0, 1.0]`; wysokość pasa skalowana
   stosunkiem zastosowanego kafla do kafla zestawu (zestaw `sandwich_ribbed` 6 m jest nadal próbkowany co 4 m → pas
   0,667 m, zgodny z rysowanymi fugami). Siła 0,12 bez zmian.
   Zaciek pod parapetem: ściany pod parapetem pasa okien / żaluzji niosą w TEXCOORD_1.v znacznik +64; shader rysuje
   pod parapetem linię brudu 0,2 m i zacieki 1,7× gęstsze, 1,8× mocniejsze, na 2,5 m zamiast 4 m.
4. **P2.** Ślady: każdy tor koła to odcisk bliźniaka — dwa bieżniki 0,26 m z przerwą 0,08 m (0,60 m razem), twarda
   krawędź (współrzędna poprzeczna pasa 0,22–0,78: bez miękkiej rampy materiału). Wyspa i pasy boczne: otarcia opon
   na obu nosach (pas `decal_tyre` na licu i krawędzi krawężnika, 1,3 m). Agregat chłodni: kratka skraplacza z
   poziomymi lamelami (paski `louvre_slats` importera, 60 mm), ciemny pas serwisowy, drzwiczki sterownika; kratka także
   na LOD1.

Unia w `WorldPbrMaterials.cs` zachowana: zacieki `weather` ‖ `runoff`, `_Tile` = `set_tile || elementScan || atlas`.

## Liczby
(uzupełnione niżej w sekcji „Pomiary”)

## Odrzucone
- Ogrodzenie panelowe po obu stronach: po stronie wschodniej ortofoto pokazuje otwartą kostkę używaną przez sąsiednie
  lokale; słupki kłamią mniej niż płot.
- Przesunięcie pasów i mediany na ślad z ortofoto: geometria dróg należy do zadań `roads/` (ADR 0077 / 0093).
- Podniesienie chropowatości w samej teksturze `curtain_folds`: wymusza przebudowę wszystkich zestawów; skala w
  importerze daje to samo i czyta manifest, który dotąd był martwy.
- Tablica „z głowy”: zakaz zmyślania (CLAUDE.md §3).
