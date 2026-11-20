# ADR 0313 — Głośność kabiny −18 LUFS: szyna słuchacza z kalibracją z pomiaru i limiterem

Status: Proposed (agent audio-lufs-s24, gałąź `audio-lufs-s24`), 2026-11-20. Numer: 0311 zajęty na main (dwa pliki:
embankment-cli i far-field), 0312 używa gałąź `drive-feel-s24` — wziąłem 0313. Do scalenia przez lidera.
Powiązane: **D92** (docs/11: kabina −18 LUFS, zewnątrz bez zmian, true peak ≤ −1 dBTP), ADR 0286 (wyjście audio PC,
`-audio_capture`, `pc_capture.py`), 0142/0145/0148/0176 (balans warstw kabiny), 0270 (głośności kanałów w ustawieniach).

## Kontekst
W projekcie nie ma AudioMixera: master = `AudioListener.volume` (ustawienia, ADR 0270), reszta to mnożniki w kodzie.
`AudioListener.volume` i `AudioSource.volume` nie przekraczają 1, a część źródeł kabiny gra blisko 1 — podniesienie
poziomu kabiny o kilka dB przez głośności źródeł obcinałoby je nierówno (zmiana balansu). Pomiar ADR 0286 (−20,8 LUFS)
był z rozpędzania do 80 km/h; D92 wymaga pomiaru z playera dla jazdy 50 km/h + jałowego + przyspieszania.

## Decyzja
1. **Szyna słuchacza** (`Game.Gameplay.CabinBusFilter`, `OnAudioFilterRead` na obiekcie AudioListenera; dodawana przez
   `TruckAudioController` raz, usuwana w `OnDestroy`): cały miks × gain, potem limiter. Gain =
   `CabinLoudness.BusGain(cab, interior)` = 1 na zewnątrz (dokładnie, przejście bit w bit), gain kabiny w kabinie,
   liniowo w crossfadzie 0,15 s; w bloku DSP rampa na próbkę (bez kliknięcia). Jeden gain dla wszystkiego, co słyszy
   słuchacz → **balans warstw (silnik/opony/wiatr/pneumatyka/tło/one-shoty) bez zmian**, zewnątrz bez zmian (D92).
2. **Kalibracja jako dane z pomiaru** (`Game.Core.CabinLoudness`): per zestaw dźwięków, bo poziomy kabiny EL i syntezy
   się różnią — **ElevenLabs +7,1 dB, synteza +4,8 dB** (`WORKING_VALUE` do odsłuchu właściciela). Wartość =
   stara + (−18 − zmierzone), liczona przez `tools/audio/lufs_calibrate.py` (BS.1770-4 z `pc_capture.measure` +
   niezależnie ffmpeg `ebur128`; odmawia, gdy przewidywany TP > −1 dBTP). Argument playera `-audio_cab_gain_db X`
   (−12…12) nadpisuje oba (A/B; 0 = miks sprzed D92).
3. **Limiter szyny** (`Game.Core.BusLimiter`): look-ahead 64 ramki (1,3 ms), próg −1,5 dBFS sample peak (0,5 dB zapasu na
   inter-sample), minimum w oknie + release 80 ms + uśrednienie prostokątne tej samej długości → gain na próbce nigdy nad
   żądanym, bez skoku. Pod progiem: kopia opóźniona bit w bit (test). Potrzebny, bo +7 dB stawia najgłośniejsze chwile
   (rozpędzanie pełnym gazem do 80 km/h, klakson) przy pełnej skali.
4. **Pomiar = to, co słychać:** przechwyt ADR 0286 bierze miks z szyny **po** gainie i limiterze (własny tap przechwytu
   nie jest dodawany na obiekcie z szyną).
5. Bez zmian `ProjectSettings/`, `Packages/`, asmdef. Android dostaje tę samą szynę (wspólny miks; docs/08 „−16 LUFS
   mobile” nadal nierozstrzygnięte; koszt: jeden filtr zarządzany na wątku audio, ~130 operacji/ramkę).

## Program pomiarowy (D92)
Player Windows (`-noWorld`, Medium, 1600×900, 60 FPS, maszyna deweloperska — nie referencja), DrivingLab, zestaw
40 t, widok kabiny, przechwyt 62 s od t = 8 s (`tools/audio/lufs_runs.ps1`):
- **straight** = `-autopilot straight080 -speed 50`: rozpędzanie pełnym gazem 0→50 km/h (~17 s), utrzymanie 50, hamowanie
  awaryjne (50,6 km/h → 0, 17,8 m), bieg jałowy do końca (≈38 s, −38 LUFS; bramka względna −10 LU go odcina);
- **circle** = `-autopilot circle50`: start i stała jazda 50 km/h po okręgu placu.
**Miara kalibracji: LUFS zintegrowane programu straight + circle sklejonego** (jeden program, BS.1770-4).

## Pomiary
Buildy: przed = `83226d958` (main, kod gry bez zmian), pośredni = `f8176c049` (synteza +6,2), końcowy = `7eadff67d`
(EL +7,1, synteza +4,8). BS.1770-4 (`pc_capture.py`) i ffmpeg `ebur128` zgodne do 0,1 LU / 0,1 dB w każdym przebiegu.
Dane: `artifacts/audio-lufs-s24/{before,rep,after,ab,final}/` (WAV, `*_report.json`, `*_calib.json`, spektrogramy,
logi playera).

**Program kalibracji (straight050 + circle50, kabina):**

| Zestaw | Przed (LUFS / TP) | Po, przebieg 1 | Po, przebieg 2 | Po, oba razem | Cel |
|---|---|---|---|---|---|
| ElevenLabs | −25,1 / −9,5 dBTP | −17,9 / −2,9 | −18,0 / −3,0 | **−17,9 LUFS / −2,9 dBTP** | −18 ±1, ≤ −1 |
| synteza | −24,2 · −22,8 · −23,4 (3 przebiegi) / −8,3 | −18,7 / −4,1 | −18,0 / −4,0 | **−18,3 LUFS / −4,0 dBTP** | −18 ±1, ≤ −1 |

Składowe (końcowy build, przebieg 1 / 2): EL straight050 −15,6 / −15,9, circle50 −19,3 / −19,3; synteza straight050
−18,3 / −17,5, circle50 −19,1 / −18,8. Przed: EL straight050 −23,1, circle50 −26,3; synteza straight050 −22,8 / −22,6,
circle50 −24,7 / −23,5 / −24,0.

**Powtarzalność:** ten sam build i scenariusz różni się między uruchomieniami do 1,2 LU (synteza circle50: −24,7 / −23,5 /
−24,0; losowe fazy pętli, start przechwytu względem rozpędzania). Pierwsza kalibracja syntezy (+6,2 z jednego przebiegu)
dała −16,5 → poprawka na +4,8 z powtórzonych przebiegów (A/B w buildzie pośrednim: `-audio_cab_gain_db 0` circle50 −23,5,
z gainem +6,2 −17,2 — dokładnie +6,2 dB, czyli szyna działa liniowo; rozrzut pochodzi z przebiegów).

**Kontrole:**
| Kontrola | Przed | Po | Wynik |
|---|---|---|---|
| Kabina, EL straight080 (pełny gaz do 80 km/h — najgłośniejsza zwykła jazda) | −20,8 LUFS, TP −9,0 (= ADR 0286: −20,8) | −13,7 LUFS, **TP −1,5 dBTP** | limiter: min −0,9 dB, 116 tys. ramek (≈2,4 s) |
| Zewnątrz (chase), EL straight050 | −28,5 LUFS, TP −11,1 | −28,2 LUFS, TP −11,6 | bez zmian (różnica w rozrzucie przebiegów) |
| Próbki ≥ 0 dBFS, wszystkie przebiegi | 0 | 0 | OK |
| Kliknięcia (`pc_capture` skan HF) EL kabina | 0 | 0 | OK; synteza 6–16 przed / 7–14 po (zdarzenia zmian biegu syntezy, były przed zmianą); chase: ptaki (ADR 0286) |
| Limiter na programie 50 km/h | — | nie zadziałał (brak wpisu w logu) | integrated bez wpływu limitera |

Testy: EditMode `scripts/test.ps1 -Platform EditMode -BuildTarget Win64` — 1475 testów, 1 niezaliczony
(`RegionSelectTests.ShippedCatalog_...`: `bialystok-industrial-c routeLengthM stale` — katalog regionów vs dane świata
z junction `Data/raw/derived`, niezwiązany z audio; ten sam wynik przed dodaniem limitera), nowe `CabinLoudnessTests` (9)
i `BusLimiterTests` (4) zielone. Python: `tools/audio/tests/test_lufs_calibrate.py` 5/5.

## Otwarte
- Odsłuch właściciela (głośniki PC, słuchawki): `artifacts/audio-lufs-s24/final/f1-*/capture.wav` (float 32, 48 kHz) —
  zwłaszcza rozpędzanie do 80 km/h (−13,7 LUFS, limiter pracuje do −0,9 dB): czy nie za głośno / czy limiter słychać.
- Przełączenie kabina ↔ zewnątrz: różnica poziomów rośnie z ~12–13 LU (ADR 0286) do ~19–20 LU — D92 każe zostawić
  zewnątrz; ewentualne podniesienie zewnątrz = osobna decyzja.
- LRA programu ~15–16 LU (jałowy −38 LUFS wobec rozpędzania −15): D92 ustawia poziom, nie dynamikę.
- Świat (ruch uliczny, otoczenie) nie mierzony — build `-noWorld` (main nie ma `_Generated/World`); kalibracja dotyczy
  pojazdu na placu. Ruch innych pojazdów w kabinie dostanie ten sam gain (spójnie), ale poziom programu w mieście może
  się różnić — pomiar `-scene knyszyn-w -autopilot route -speed 50` z `-audio_capture` po buildzie z regionami.
- Android: ta sama szyna i gain (wspólny miks); cel mobilny (docs/08 „−16 LUFS”) i koszt filtra na Helio G99 niezmierzone.
- Synteza: zmierzona w 2 przebiegach po zmianie; rozrzut przebiegów do 1,2 LU zjada część tolerancji ±1.
