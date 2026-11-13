# ADR 0175 — Wygląd zestawu TRAKT + naczepa firanka a przepisy (R48, R46, R58, R70, R73, R104, 96/53/WE, WT)

Status: wykonane na gałęzi `truck-regs-0175` (baza main `3a60019ff`, 2026-11-13, s17); niescalone. Ocena wizualna należy do
`visual-critic` — poniższe opisy renderów są autorskie, nie są werdyktem PASS.

Źródło wymagań: tabela dla artysty w `docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p4.md` §5 (kontrola krzyżowa GPT P4 +
Mistral M44, pewność P/S/O) oraz `research/gptpro/p4-truck-regulations/manifest.csv` (identyfikatory P4-nnn). Trzy liczby
spoza tabeli sprawdzono w pliku urzędowym `research/gptpro/p4-truck-regulations/files/P4-001.pdf` (R48 rew. 12, seria 06;
przegląd s17 potwierdził brak zmian tych punktów w serii 07): 6.17 — odblask boczny „nie wyżej niż 1200 mm, jeśli
zgrupowany ze światłem”; 6.21.7.2 — narożniki konturu częściowego jako dwie linie pod kątem 90°, każda ≥ 250 mm;
6.21.7.5 — miejsce na taśmę o szerokości ≥ 60 mm.

## Decyzja

1. Zgodność wyglądu z przepisami jest sprawdzana **liczbowo na wyjściu generatorów**, nie „na oko”:
   `tools/blender/truck/regs_audit.py` (Blender, bez bake: bryły brzegowe lamp, odblasków, taśm, osłon, lusterek) →
   `art-source/truck/regs/{tractor,trailer}.json` → `tools/blender/truck/regs_check.py` (czysty Python, tabela
   element → wymaganie → stan → wynik) → `tests/physics/test_truck_regs.py`. Zmiana generatora ciężarówki = regeneracja
   obu zrzutów.
2. Braki poprawiono w generatorach (`trailer_build.py`, `chassis.py`), a FBX, atlasy i manifesty wygenerowano kanonicznie
   (`art-source/truck/exterior/qa/generate_and_check_0115.py`). Żadnych ręcznych poprawek siatek.
3. Grupy świateł: `13 = PLATE` (naczepa używała tego id, teraz jest też w liście ciągnika), nowa `14 = FOG_REAR`
   (tylne przeciwmgłowe ciągnika i naczepy; `11 = FOG` zostaje dla przednich). `TruckLights.rearFog` steruje grupą 14
   (czerwone, tylko z mijania — R48 6.11.7; luminancja 15 000 cd/m² to WORKING_VALUE). Tekstura stanu 16 × 1 bez zmian.
4. Pozycje O / UNVERIFIED z tabeli **nie zostały zmienione** (lista na końcu).

## Audyt przed zmianą (baza `3a60019ff`): element → wymaganie → stan → różnica

Pełne tabele (135 wierszy przed, {ROWS_AFTER} po): `docs/reports/visual/truck-regs-0175/audit_before.md`, `audit_after.md`.
Przed: 111/135 zgodnych, 24 różnice. Po: {OK_AFTER}. Poniżej tylko różnice; wszystko, czego tu nie ma, było zgodne
(m.in. brak konturu R104, tablic wyróżniających i osłon R58/R73 na ciągniku; nietrójkątne odblaski tylne ciągnika;
lusterka kl. II i IV po obu stronach, kl. V po stronie pasażera, kl. VI z przodu, wszystkie ≥ 2 m; pełny czerwony kontur
tyłu naczepy; żółto-czerwone tablice bez skośnych pasów; trójkąty wierzchołkiem do góry; RUPD 130 mm / prześwit 420 mm;
osłony boczne R73; 16,47 m / 2,55 m / 3,996 m; tablica naczepy tylko z tyłu).

| Pojazd | Element | Wymaganie (źródło, pewność) | Stan przed | Po |
|---|---|---|---|---|
| ciągnik | odblaski tylne nietrójkątne | ≤ 400 mm od krawędzi (R48 6.14.4, P4-045, S) | 472 mm (wewnętrzna komora lampy) | 343 mm — osobny element `rear_reflex` między stop a cofania |
| ciągnik | tylne przeciwmgłowe | 1–2, pojedyncze po lewej, 250–1000 mm, > 100 mm od stop (R48 6.11, P4-031/035..037, P/S) | brak | 1 lampa po lewej na wsporniku, 775–865 mm, 238 mm od stop |
| ciągnik | odblaski boczne | obowiązkowe; 250–900 mm; pierwszy ≤ 3 m, odstęp ≤ 3 m, ostatni ≤ 1 m od tyłu (R48 6.17, WT §12 ust. 1 pkt 11, P) | brak (były tylko światła obrysowe boczne) | 3 na stronę: przy obu lampach bocznych (410–440 mm) i na końcu obudowy lampy tylnej; pierwszy 2,90 m od przodu |
| naczepa | światła cofania | 2 (naczepa > 6 m; R48 6.4.2.2, P4-060, S) | 1 (tylko prawa lampa) | 2 — sekcja cofania w obu lampach |
| naczepa | tylne przeciwmgłowe | ≤ 1000 mm; > 100 mm od stop (P4-036, P4-031) | 1006 mm; 0 mm (sekcja obok stop) | 986 mm; 107 mm (sekcja cofania między stop a przeciwmgłowym), po jednej w każdej lampie |
| naczepa | pozycyjne przednie | 2 białe, ≤ 150 mm od krawędzi, 250–1500 mm (R48 6.9, P4-053..055, P/S) | brak (białe lampy tylko na 3,87 m = obrysowe) | 2 lampy na dolnej belce ściany przedniej, 1395–1437 mm, 115 mm od krawędzi |
| naczepa | odblaski przednie | 2 białe, ≤ 150 mm od krawędzi, 250–900 (1500) mm (R48 6.16, P4-063..065, P) | brak | 2 w tej samej obudowie, 1343–1387 mm (wyjątek 1500: ściana zaczyna się na 1,28 m) |
| naczepa | odblaski tylne trójkątne | ≤ 400 mm od krawędzi, 250–900 mm (R48 6.15.4, P4-068, S) | 660 mm; górna krawędź 950 mm | 150 mm; 700–830 mm (pod lampą, panel lamp przedłużony w dół do 0,68 m) |
| naczepa | obrysowe boczne | odstęp ≤ 3 m (R48 6.18.4, P4-049, S) | 3,60 m (−4,1 → oś 2) | 2,50 / 2,50 / 3,00 / 2,54 / 1,97 m |
| naczepa | odblaski boczne | pierwszy ≤ 3 m od przodu, odstęp ≤ 3 m, ostatni ≤ 1 m od tyłu (R48 6.17.4, P4-047/069, P) | 1 na stronę (5,68 m od przodu, 7,92 m od tyłu) | 6 + 1 na stronę: w każdej lampie obrysowej bocznej (1032–1063 mm, zgrupowane ze światłem) + istniejący na osłonie |
| naczepa | kontur tył | > 200 mm od stop (R48 6.21.7.3, P4-077, S); taśma 60 mm (6.21.7.5, P4-079; R104 50 +10/−0) | 174 mm; 50 mm | 211 mm (linia progu 1,19–1,25 m, lampy 20 mm niżej); 60 mm |
| naczepa | kontur bok | częściowy = linia + górne narożniki 2 × ≥ 250 mm (R48 6.21.1.2.2, 6.21.7.2, P); taśma 60 mm | sama linia 50 mm | linia 60 mm (≥ 70 % długości) + żółte narożniki na firance przy pierwszym i ostatnim pasie, 310 + 310 mm |
| naczepa | tablice wyróżniające | wysokość 200 +30/−5 mm, łącznie 1130–2300 mm (R70 zał. 12 wg przeglądu, S) | 2 × 565 × 110 mm | 2 × 565 × 200 mm (355–555 mm nad jezdnią) |

## Budżet (trójkąty / materiały LOD; manifesty przed → po)

| | LOD0 | LOD1 | LOD2 | limit | sloty materiałów |
|---|---|---|---|---|---|
| ciągnik | 104 514 → {E0} | 43 000 → {E1} | 17 690 → {E2} | 140 000 / 45 000 / 17 900 | 6, bez zmian |
| naczepa | 89 000 → 88 988 | 24 500 → 24 497 | 7 849 → 7 850 | 90 000 / 25 000 / 8 000 | 5, bez zmian |

Siatki źródłowe: ciągnik 131 506 → {SRC_T} trójkątów, naczepa 107 506 → 108 202; nadwyżkę zbiera istniejąca decymacja do celu
LOD. Liczba obiektów i atlasów bez zmian (16 obiektów naczepy na LOD; narożniki konturu należą do `CHASSIS`, więc
`CURTAIN_L/R` zostają przy 2 materiałach). `check_export.py`: PASS dla obu pojazdów. Koszt na telefonie: UNVERIFIED (ta
sama liczba wywołań rysowania i tekstur; pomiar należy do lidera).

## Nie zmieniono — pozycje O / UNVERIFIED albo poza zakresem

- Płyta tablicy rejestracyjnej 520 × 114 mm (P4-153, UNVERIFIED; zmiany Dz.U. 2025 poz. 939 i 2026 poz. 891 niesprawdzone)
  — model ma 520 × 114, miejsce 520 × 120 spełnione (zmierzone 520 mm, dolna krawędź 600 / 810 mm, górna ≤ 1200 mm).
- Rysunek tablic wyróżniających z zał. 10 WT / R70 (O): szerokość czerwonego obrzeża 40 mm to WORKING_VALUE.
- CMS zamiast lusterek kl. II/IV (O) — w grze lusterka; wariant kamer w generatorze nietknięty.
- Miejsce tachografu (O) — wnętrze poza zakresem tego ADR.
- Serie R46 05–07 i R48 08 (UNVERIFIED) — nieużyte.
- Kierunkowskazy boczne naczepy kat. 5 (3 na stronę) „chyba że ≥ 3 migające obrysowe boczne” (S): geometrycznie jest
  6 lamp bocznych na stronę, ale grupa `MARKER_SIDE` jest wspólna dla obu stron i nie miga z kierunkowskazem —
  wymaga rozdzielenia grupy na L/P (2 nowe id), do decyzji lidera.
- Dodatkowe 2 kierunkowskazy tylne O4 (S, tylko Mistral) — nie dodano.
- Oświetlenie tylnej tablicy ciągnika (P4-038, S; nie ma go w tabeli §5): ciągnik nie ma lampki tablicy — otwarte.
- Osłony boczne R73: ostatnie 250 mm ≤ 30 mm w głąb od obrysu (poza tabelą; model 48 mm) — otwarte.
- Długość ciągnika 5,995 m (< 6 m): światła obrysowe boczne i 2 światła cofania są na nim nadobowiązkowe; zostają.
- Pola widzenia lusterek (kl. II/IV/V/VI) — pokryte istniejącymi `MirrorFieldOfVisionTests`, bez zmian.
- Znak „TOP” i znaki homologacji na taśmach (R104 5.5 / 4.1.2) — poniżej rozdzielczości atlasu, nie modelowane.

## Dowody

- Rendery: `artifacts/truck-regs-0175/` — `sbs/*_sbs.jpg` (źródła przed/po, pochmurno), `export/` (FBX LOD0 z atlasami,
  lampy zapalone), `unity/` (kamery kontrolne DrivingLab, w tym widok z kabiny w lusterka).
- `python tools/blender/truck/regs_check.py --tractor art-source/truck/regs/tractor.json --trailer art-source/truck/regs/trailer.json` → {OK_AFTER}.
- `pytest tests/physics/test_truck_regs.py tests/physics/test_dims_sync.py`; EditMode `TruckRegulationLampTests` — wyniki w raporcie agenta.
