# ADR 0312 — Głośność kabiny −18 LUFS: szyna słuchacza z kalibracją z pomiaru i limiterem

Status: Proposed (agent audio-lufs-s24, gałąź `audio-lufs-s24`), 2026-11-20. Numer: 0311 zajął w międzyczasie
embankment-cli (`e1ff11678`) — wziąłem następny wolny. Do scalenia przez lidera.
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
   się różnią — **ElevenLabs +7,1 dB, synteza +6,2 dB** (`WORKING_VALUE` do odsłuchu właściciela). Wartość =
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
Przed = build `83226d958` (main, kod gry bez zmian); po = build `f8176c049` (ta gałąź). BS.1770-4 (`pc_capture.py`) /
ffmpeg `ebur128` zgodne do 0,1 LU / 0,1 dB we wszystkich przebiegach.

| Zestaw | Przebieg | Przed LUFS | Przed TP | Po LUFS | Po TP |
|---|---|---|---|---|---|
| ElevenLabs | straight050 | −23,1 | −9,5 | −15,6 | −3,0 |
| ElevenLabs | circle50 | −26,3 | −10,5 | −19,3 | −3,7 |
| ElevenLabs | **program (kalibracja)** | **−25,1** | −9,5 | **−17,9** | **−3,0** |
| synteza | straight050 | −22,8 | −8,3 | −16,5 | −2,8 |
| synteza | circle50 | −24,7 | −9,0 | −17,2 | −2,8 |
| synteza | **program (kalibracja)** | **−24,2** | −8,3 | **TODO** | TODO |

TODO: powtarzalność, straight80, chase.

## Otwarte
- Odsłuch właściciela (głośniki PC, słuchawki): `artifacts/audio-lufs-s24/after/*/capture.wav` (float 32, 48 kHz).
- LRA programu ~15–16 LU (jałowy −38 LUFS wobec rozpędzania −15): D92 ustawia poziom, nie dynamikę.
- Świat (ruch uliczny, otoczenie) nie mierzony — build bez świata; kalibracja dotyczy pojazdu na placu.
