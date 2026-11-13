# ADR 0172 — P1 bramki 3 (b): sygnalizator 182011 na Rondzie Putry, skupisko znaków na wyspie EC (cm92458760), P2 filary

Status: PROPOSED na gałęzi `p1b-0172` (2026-11-13, s18); nie scalone; ocena `visual-critic` wymagana.
Źródło: `docs/reports/visual/REVIEW-2026-11-13-s17-0161.md` (P1: 182011 „jeden sygnalizator na wysięgniku vs 3–4,
kamera ~1 pas w lewo”; cm92458760 „brak skupiska znaków frontem — D-6, tablica ulicy, C-”; P2: filary/głowice
musztardowe, kapa 494288).

## 1. Decyzja właściciela 2026-11-13 (przekazana przez lidera)

**Świat odwzorowuje stan z ortofoto GUGiK 2024, nie ze zdjęcia Mapillary 182011943700132 (gpsmapper, 2019).**
Zdjęcie z 2019 r. pokazuje układ sprzed przebudowy (dwa maszty z krótkimi wysięgnikami); na ortofoto 2024 stoi
jeden maszt z łukowym wysięgnikiem ~8,8 m (2 głowice na wysięgniku + 1 na maszcie) i osobny słupek na wysepce
żwirowej. Para SBS 182011 pozostaje więc z jawną różnicą epok (liczba masztów), co zapisano w `pose_reason`.

## 2. Ustalenia (zmierzone na ortofoto 0,08 m, WMS ORTO HighResolution; wycinki w `artifacts/p1b-0172/td/`)

- **182011** (`hr_182arm.png`): stopa masztu E −532,5 N 37,9; koniec wysięgnika E −540,5 N 41,7 → 8,8 m, azymut 295°;
  cień wysięgnika niesie dwie plamy głowic odległe o 2,8 m (E −541,5 N 45,3 i E −543,5 N 47,3); słupek na wysepce
  E −545 N 40 (cień prosty, bez wysięgnika). Dokładność ±0,3 m; wychylenie szczytu od nadiru nieskorygowane.
- **Wyspa EC** (`hr_cm924z.png`, 118 px/m): cienie biegną na NNW, ~1,1 m cienia na 1 m wysokości (z tarczy D-6).
  Stopy słupków = początek cienia: A-7 + C-12 E 540,13 N −743,7 (dwie tarcze 2,4 / 3,2 m nad ziemią); D-6
  E 537,16 N −745,26; słup latarni E 539,7 N −742,6 (pochylony obraz 3,8 m, jedna oprawa) z turkusową tablicą
  ulicy ~1,2 m na południe; tablica pasów ruchu — prostokątny cień 0,7 × 1,5 m, stopa wyliczona z wysokości środka
  tarczy 2,8 m: E 538,95 N −742,85 (±0,5 m, mniej pewne niż słupki pojedyncze).
- Generowana wyspa rozdzielająca (trawnik w krawężniku) pokrywa się z rzeczywistą do ~1 m, więc punkty z ortofoto
  leżą na niej bez przesunięć (QA `snapped_m`, §4).

## 3. Decyzja

1. `standards.SIGNAL_MAST_ARMS = {signal_mast: 6.0, signal_mast_9m: 8.8}`; `props.build_all` buduje oba prototypy
   tym samym `signal_pole` (bez nowego materiału).
2. `gate3_landmarks` — `kind: gate3_signal`: `arm_m` (wybór prototypu), `arm_heads_m: [..]` (głowice na wysięgniku,
   domyślnie `[5.0]`), `pole_head` (domyślnie true). Zła długość / głowica poza wysięgnikiem → `stale` w QA, nigdy
   po cichu.
3. `gate3_sign`: nowe lica `F-10-ls` (tablica „w lewo | prosto”, 0,80 × 0,80 m zmierzone na zdjęciu — §4, dwa słupki)
   i `C-12` (dysk 0,60 m WORKING_VALUE, rysunek `signs.c12`); pole `photo: ["commons:<id>"]` jako proweniencja
   obok `mapillary`.
4. Nowy `kind: gate3_lamp` — pojedynczy słup oświetleniowy z istniejącego prototypu `lamp_*` w zmierzonym punkcie
   (reguła latarni nie stawia słupów na wyspach rozdzielających).
5. `overrides.yaml`: `putry-ring-s-approach-signal-mast` → `arm_m 8.8`, `arm_heads_m [5.5, 8.3]`, azymut 295;
   blok `ec-island-*` (F-10-ls, A-7 + C-12, D-6, latarnia `lamp_10m`, tablica „ul. Bitwy Białostockiej”).
   Stopy z ortofoto; **wysokości, rozmiar F-10 i obroty tarcz ze zdjęcia cm92458760** (poza resekowana, §4) —
   wysokości 2,4 / 3,2 m odczytane z cieni na ortofoto (§2) okazały się o ~0,6 m za niskie.
6. P2 filary: `viaduct_underdeck.json` `pier_paint.color_linear` × 0,7 (ten sam odcień) → 0,102 / 0,092 / 0,055.
7. P2 kapa (494288): **bez zmiany.** Albedo już × 0,62 (ADR 0161); pozostała różnica to oświetlenie (zdjęcie pod
   słońce, kapa w cieniu ekranu, render w słońcu) — dalsze ściemnianie albedo byłoby wypalonym cieniem.

Uproszczenia jawne (WORKING_VALUE): D-6 zamiast D-6b z tabliczką; tablica ulicy na własnym słupku 0,65 m od latarni
(w rzeczywistości na wysięgniku z latarni); wysokość latarni 10 m i kierunek wysięgnika; głowice 1,5 m na wschód od
rzeczywistych (generowany maszt stoi 2,2 m na wschód — jezdnia generowana jest szersza, ADR 0161).

## 4. Walidacja (r5, 2026-11-13, s19)

Przebieg: r1–r3 (s18) → r4, r5 (s19); każda runda = `build_world` + import + pary SBS Low + kamery kontrolne
Low/High + EditMode. Narzędzia i logi: `artifacts/p1b-0172/{tools,logs}`.

**Poza cm92458760 (pewność B)** — resekcja 4-parametrowa na latarni, słupkach A-7 i D-6 oraz obu kominach EC:
E 533,9 N −737,1, kurs 134,7°, hfov 67,6°, oko 2,1 m; reszty ≤ 0,6°. Ogniskowa 2868 px (3840 px), horyzont
y = 1137 px ze stopy latarni (8,0 m wg ortofoto); kontrola niezależna: stopa słupka A-7 → 9,37 m wobec 9,07 m
z ortofoto (+3 %).

**Pomiary na zdjęciu przy tej pozie** (kadry w równej skali: `artifacts/p1b-0172/cmp/`):

| obiekt | zdjęcie | r3 | r5 |
|---|---|---|---|
| F-10 wysokość tablicy | 338 px na 6,75 m → 0,80 m (±0,05) | 1,20 m | 0,80 m |
| F-10 szerokość w kadrze | 0,42 m | ~0,3 m | 0,40 m (obrót 200° → 190°) |
| F-10 dolna krawędź | 2,26 m | 2,2 m | 2,2 m |
| C-12 (tarcza) | 2,58–3,27 m | 2,1–2,7 m | 2,7–3,3 m |
| A-7 (trójkąt) | 3,56–4,18 m | 2,75–3,53 m | 3,35–4,13 m |
| tablica ulicy, dolna krawędź | 3,11 m | 3,3 m | 3,1 m |

Pozostałe różnice, jawne: trójkąt A-7 0,9 m (grupa średnia, `standards.SIGN_SIZE`) wobec ~0,72 m na zdjęciu
i odstęp tarcz 5 cm wobec ~0,29 m (stąd dolna krawędź 2,7 zamiast 2,58 m — kompromis na oba lica); słupki F-10
co 0,6 szerokości tablicy (zdjęcie ~0,8); średnica tarczy C-12 0,60 m wobec ~0,69 m z pomiaru (między grupą małą
a średnią — bez zmiany, UNVERIFIED); słup latarni cieńszy (~0,14 m wobec ~0,21 m przy stopie).

**182011** — render r5 obok ortofoto `td/hr_182arm.png`: maszt z łukowym wysięgnikiem, 2 głowice na wysięgniku
+ 1 na maszcie, osobny słupek na wysepce po lewej; jezdnia na całej szerokości kadru. Różnica epok wobec zdjęcia
z 2019 r. (dwa maszty) zamierzona (§1).

**QA danych** (`generated/streetscape_qa.json` → `furniture.gate3_landmarks`): `stale = []`; pięć obiektów wyspy EC
i oba sygnalizatory `snapped_m = 0.0`; `top_m`: F-10 3,05, A-7 + C-12 4,18, D-6 2,85, tablica ulicy 3,40.

**Testy:** `tests/gis/test_p1b_0172.py` 9/9; pytest `tests/gis` PYTEST_R5; EditMode 517/518 (1 pominięty,
Ignored), 0 nieudanych; fidelity exit 0; preflight SBS OK; 42 pary × 2 oświetlenia.

**Budżet Low** (48 kamer kontrolnych, r5 wobec bazy sprzed zmian, `logs/budget-low-r5.txt`): draw calle −6…+11
(maks. `g3a-rondo-bie-approach` 443 → 454), trójkąty −1,95…+1,95 % (`g3a-rondo-bie-approach` +1,42 %,
`g3b-rondo-putry-approach` +0,01 %). Pomiar edytorowy — telefon nie był mierzony w tym zadaniu.

**Pary do oceny `visual-critic`:** `artifacts/p1b-0172/sbs-r5/pairs/Low-{overcast,clear}/sbs-g3-a-cm92458760.jpg`,
`.../sbs-g3-b-182011943700132.jpg`, kadry `artifacts/p1b-0172/cmp/cm92458760-cluster-r{3,4,5}-*.jpg`.
