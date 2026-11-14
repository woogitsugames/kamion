# REVIEW 2026-11-14 (s20): bramka 3 na telefonie A16, APK `kamion-0.1.0-77cfd94bf8`

Recenzent: visual-critic (tylko odczyt, nic nie commitowano) · Źródło obrazów: **wyłącznie zrzuty z telefonu** Samsung A16 (RFGL34SJYDZ), Low, 30 FPS, APK czysty (`apkDirty=false`).
- G3-A: `artifacts/gate3/20261114-063715/RFGL34SJYDZ/cam/` (57/57 CAPTURED, duplikaty 0)
- G3-B: `artifacts/gate3/20261114-071223/RFGL34SJYDZ/cam/` (46/46 CAPTURED, duplikaty 0)
- Pomiar odniesienia (zaliczenie D57, APK `3ffbf13881`): `artifacts/gate3/20261113-081528/` (A) i `20261113-085052/` (B), te same nazwy kamer.
- Referencje: `Data/Regions/bialystok-industrial-c/sbs_references.json` -> `artifacts/sbs-gate3/rectified/*.png` oraz `Data/raw/refs/objects/kwadrat-park/commons-geo/cm*.jpg`.

Metoda: każda klatka nowa | stara (ten sam id) zmniejszona do 960 px; dla każdej kamery `eye` z referencją w promieniu ~30 m stacji (G3-A: stacja segmentu + 12 m; G3-B: + 1232 m) obejrzana siatka zdjęć.
Obejrzane: 36 par kadrów (72 obrazy) + 5 wycinków 1:1 (soczewki lamp, wieżowiec x3, cienie). Automatycznie (wszystkie 103 PNG): piksele magenta 0,000 %, czarne pola <= 5 % (tylko kadry dusk, zgodnie z porą), logcat bez błędów shaderów / brakujących zasobów (0 trafień).

## Werdykt: **UTRZYMANA**

Rozpoznawalność na telefonie jest **lepsza** niż w pomiarze zaliczenia: nowe kotwice zgodne ze zdjęciami (bramownice, otwarty wiadukt Putry z zielonym gzymsem, mur oporowy z czerwonym pasem i ekranami, zbiornik Enea, niebieski budynek Kwadrat). Brak P0, brak regresji układu. Materiały nadal „gra mobilna z 2016” (sterylny bruk, płaskie ściany, kopce jak z cegły) — zgodnie z D51 nie blokuje bramki 3.

Wydajność (z `gate3-result.json`, informacyjnie): G3-A p95 33,46 / p99 33,57 ms, > 50 ms: 2, GPU p95 34,51, PSS 917,5 MB; G3-B p95 33,45 / p99 33,62 ms, > 50 ms: 6, GPU p95 34,28, PSS 877,8 MB. Oba `valid=true`. GPU p95 nadal > 33,3 ms (brak zapasu na Low, jak w GATE-3.md).

## Punkty kontrolne (T = kierowca znający miejsce rozpozna, N = nie)

| Kamera (telefon) | Referencja | Rozpozn. | Zmiana vs 13.11 | Uwagi |
|---|---|---|---|---|
| g3a_eye_s0012 | — | T | = | hala z czerwonym portalem, kominy EC, wieżowiec (szczyt bez okien w LOD1, P2-4) |
| g3a_eye_s0062 | — | T | ~ | wieżowiec: szczyt jako jednolita khaki ściana, kolumna okien ledwo widoczna (P2-4) |
| g3a_eye_s0112 | — | T | = | — |
| g3a_eye_s0162 | — | T | + | hala po lewej teraz granatowa (spójna z Kwadrat), wieżowiec z pasami 0180 |
| g3a_eye_s0212 | — | T | = | — |
| g3a_eye_s0262 | cm92458760 (częściowo) | T | + | kominy + zbiornik; linia środkowa przez zebrę (P2-6) |
| g3a_eye_s0312 | cm92458760 | T | **+** | wrócił zbiornik Enea (biały z niebieskim pasem) |
| g3a_eye_s0362 | 2818555, 201270, 1398898 | T | = | wiadukt z czerwonym gzymsem; żwirowa wyspa i tablica z nazwą ronda poza kadrem |
| g3a_eye_s0412 | 482392, 500263, 1259231 | T | = | przyczółek widoczny; brak niebieskiej tablicy pod wiaduktem (P2-12); poszarpany cień w poprzek pasa (P1-3) |
| kwadrat_park_gate | cm109685822 | T | **+** | budynek po prawej niebiesko-szary jak na zdjęciu (był beżowy) |
| g3a_rondo_bie_approach, photo_biezenstwa_ground | cm92458760 | T | **+** | zbiornik Enea, znaki A-7 / C-12 / D-6 |
| biezenstwa_above, putry_above, rondo_*_above | — | T | ~ | wyspa ronda pod wiaduktem = jasny płaski placek (P2-7) |
| g3b_eye_s1232 | 381800, 2279538 | T | + | blok, niebieska hala, U-3a, gęstszy las (0170) |
| g3b_eye_s1282 | 275528, 837235 | T | **+** | **bramownica z zielonymi tablicami widoczna** (wcześniej brak) — zgodna z 275528 |
| g3b_eye_s1332 | 150280, 297817 (kierunek przeciwny) | T | = | pary nieporównywalne (heading 118–131°) |
| g3b_eye_s1382 | 3678296 | T | **+** | dwuramienne latarnie w pasie dzielącym + bariera jak na zdjęciu; ekrany, słup WN |
| g3b_eye_s1432 | 1528935, 962702 | T | **+** | powierzchnia wyłączona (P-21) zamiast trawy z „pływającą” szarą skrzynką |
| g3b_eye_s1482 | 810896, 810525 | T | **+** | mur oporowy z czerwonym pasem i ekranami jak 810525; bramownica Warszawa/Ełk/Augustów |
| g3b_eye_s1532 | 209622, 326454 | T | **+** | j.w., wiadukt na filarach w głębi |
| g3b_eye_s1582 | 339463, 468026 | T | **+** | wiadukt otwarty na okrągłych filarach z zielonym gzymsem (był pełny mur), strzałki P-8 |
| g3b_eye_s1632 | 4312632, 494288 | T | **+** | zniknęły betonowe bloki na pasie; bramownica przed s1632 (zgodnie z 339463/468026) |
| g3b_eye_s1682 | 182011, 1801374 | T | + | sygnalizator 182011 (0172); cień wysięgnika poszarpany (P1-3) |
| g3b_rondo_put_approach, g3b_rondo_putry_approach | — | T | + | wiadukt otwarty; chodnik na „wiszącej” płycie (P1-1) |
| driver_andersa_to_putry | — | T | = | — |

Wynik: **24/24 T, 0 N**. Na 13.11 ten sam zestaw też był rozpoznawalny, ale s0312, s1282, s1582, s1632 i kwadrat_park_gate miały błędne lub brakujące kotwice — teraz zgodne ze zdjęciami.

## Kamery pojazdu i światła
- `truck-34_{lowsun,overcast,dusk}`: soczewki lamp (0181) widoczne na telefonie: biały prostokąt DRL + bursztynowy pas kierunkowskazu; w dusk świecą bez przesadnego bloomu. Czytają się jednak jak płaska naklejka — brak głębi odbłyśnika i szkła (P2-8). Za przednią szybą we wszystkich oświetleniach jasnoszary prostokąt (zasłona / ściana kabiny?) wyglądający jak pusty quad (P2-8).
- `cab-driver_dusk`: wiązka świateł na drodze OK, okna nocne (0192) zapalone wybiórczo — wiarygodne. `cab-left_dusk`: 3 z 4 okien zapalone, emisja płaska, akceptowalna.
- `truck-34_dusk`: **pod latarniami nie widać plam światła (0191)** na kostce — wyłączone na Low albo za słabe (UNVERIFIED; P2-9).
- Kabina dzień/overcast: bez zmian, bez artefaktów.

## Problemy

### P0 — brak

### P1
1. **Chodnik na wiszącej płycie, widoczny spód** — `g3b_rondo_putry_approach.png` (prawa połowa; w 960 px x 600–780, y 290–420). Bez zmian od 13.11. Poprawka: skarpa/dociągnięcie terenu pod krawędź chodnika przy ekranach w generatorze.
2. **Szew muru oporowego** — `g3b_ext34_s1482.png` (960 px: x 620–700, y 255–285): koniec muru z zieloną „czapą” ponad terenem i samotny panel ekranu w powietrzu. Nowe po regeneracji. Poprawka: zakończenie muru skrzydłem do terenu, ekran kończyć na ostatnim słupku.
3. **Postrzępione cienie cienkich obiektów na Low** — `g3b_eye_s1682.png` (środek jezdni: wysięgnik sygnalizatora jako przerywana łukowata czarna smuga + 2 plamy głowic), `g3a_eye_s0412.png` (960 px: x 340–440, y 330 — kreskowana smuga w poprzek pasa; schodkowy cień bariery). Na telefonie w polu uwagi kierowcy wygląda jak ubytki asfaltu. Poprawka: `ShadowCastingMode.Off` dla wysięgników / przewodów / cienkich rur na Low albo większy normal bias kaskady; sprawdzić, czy przewody WN rzucają cień.

### P2
4. Wieżowiec: ściana szczytowa jako jednolita khaki płaszczyzna, kolumna okien o zbyt niskim kontraście (s0062); w LOD1 (s0012) kolumny brak -> widoczne „dorastanie” okien przy zbliżaniu. Poprawka: kolumna szczytu w atlasie LOD1 (0184), ciemniejsze szyby.
5. Granatowa elewacja (s0162, `g3a_ext34_s0214_overcast`) wyraźnie bardziej nasycona i ciemniejsza niż szaroniebieska blacha na `cm109685822` — obniżyć nasycenie/jasność albedo (sprawdzić histogramem).
6. Oznakowanie poziome: linia środkowa przechodzi przez zebrę (s0262, x ~465); ciemne przerwy w pasach zebry (`g3b_rondo_put_approach`, prawa strona); ostrokątna jednolita łata na jezdni (s1382, x 540–760, y 290–340).
7. Wyspa ronda Bieżeństwa pod wiaduktem = jasny jednolity dysk (`biezenstwa_above`) — kierunek dobry (żwir na 2818555), ale bez ziarna i obrzeża. Czerwonobrunatne „kopce z cegły” (rabaty) na rondzie (`g3a_rondo_bie_approach`, s0312 prawy dolny róg, s0362) — klasyczny slop: jedna tekstura, zero roślin.
8. Ciężarówka: soczewki jako płaskie prostokąty; szary quad za przednią szybą (`truck-34_*`).
9. Plamy światła latarni (0191) niewidoczne w `truck-34_dusk` na Low — potwierdzić w ADR, czy zamierzone dla Low.
10. Mur oporowy (s1482, s1532) w teksturze kamienia/gabionu, na 810525/209622 gładkie prefabrykowane płyty; brak rzędu młodych drzew przy murze (na obu zdjęciach). Czerwony pas jako szeroka pozioma półka (wyraźne w overcast), na zdjęciu wąski pionowy gzyms.
11. Powtarzalność: te same białe kombi/vany na parkingach (s0012, s0162, s0212); stożkowe „tuje” low-poly przy hali (s1282).
12. s0412: brak niebieskiej tablicy kierunkowej pod wiaduktem (widoczna na 482392 i 500263).

## Oceny (1–10, telefon Low)
Rozpoznawalność 8 · skala i proporcje 6 · światło i ekspozycja 5 · materiały 4 · zużycie i osadzenie 4 · powtarzalność 5 · polskie realia (znaki, oznakowanie, latarnie) 7 · czytelność 7 · artefakty (bez magenty / brakujących tekstur; cienie Low) 6.

Co odróżnia telefon od zdjęcia: idealnie czyste, jednolite powierzchnie (kostka, asfalt, trawa bez krawędzi zużycia), brak drobnej zieleni przy murach i krawężnikach, brak ruchu, te same chmury na każdej kamerze, mur i rabaty jako jedna tekstura bez wariacji. Migotania i LOD pop w ruchu nie da się ocenić ze stopklatek — poza P2-4 nie stwierdzono.

Pliki robocze recenzenta (zestawienia nowa|stara, wycinki): katalog scratchpad sesji, nieprzenoszone do repo.
