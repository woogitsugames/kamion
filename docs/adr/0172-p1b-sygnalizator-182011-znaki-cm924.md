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
3. `gate3_sign`: nowe lica `F-10-ls` (pionowa tablica „w lewo | prosto”, 0,90 × 1,20 m WORKING_VALUE, dwa słupki)
   i `C-12` (dysk 0,60 m WORKING_VALUE, rysunek `signs.c12`); pole `photo: ["commons:<id>"]` jako proweniencja
   obok `mapillary`.
4. Nowy `kind: gate3_lamp` — pojedynczy słup oświetleniowy z istniejącego prototypu `lamp_*` w zmierzonym punkcie
   (reguła latarni nie stawia słupów na wyspach rozdzielających).
5. `overrides.yaml`: `putry-ring-s-approach-signal-mast` → `arm_m 8.8`, `arm_heads_m [5.5, 8.3]`, azymut 295;
   blok `ec-island-*` (F-10-ls, A-7 + C-12, D-6, latarnia `lamp_10m`, tablica „ul. Bitwy Białostockiej”).
6. P2 filary: `viaduct_underdeck.json` `pier_paint.color_linear` × 0,7 (ten sam odcień) → 0,102 / 0,092 / 0,055.
7. P2 kapa (494288): **bez zmiany.** Albedo już × 0,62 (ADR 0161); pozostała różnica to oświetlenie (zdjęcie pod
   słońce, kapa w cieniu ekranu, render w słońcu) — dalsze ściemnianie albedo byłoby wypalonym cieniem.

Uproszczenia jawne (WORKING_VALUE): D-6 zamiast D-6b z tabliczką; tablica ulicy na własnym słupku 0,65 m od latarni
(w rzeczywistości na wysięgniku z latarni); wysokość latarni 10 m i kierunek wysięgnika; głowice 1,5 m na wschód od
rzeczywistych (generowany maszt stoi 2,2 m na wschód — jezdnia generowana jest szersza, ADR 0161).

## 4. Walidacja

TBD
