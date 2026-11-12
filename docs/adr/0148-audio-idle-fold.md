# ADR 0148 — „Dziwny dźwięk na jałowym” (nagranie Fold): sprężarka powietrza głośniejsza od silnika
Status: Proposed (agent audio, s15), 2026-11-12. Ocena brzmienia: właściciel (telefon, głośnik i słuchawki).

## Kontekst
Właściciel nagrał grę na Samsungu Fold (`artifacts/owner-feedback/2026-11-12-fold-video/`, 27 s, 48 kHz) i zgłosił:
„dźwięk na jałowym jest dziwny”. APK: `artifacts/orientation/kamion-0.1.0-387a492d24.apk` (zbudowany 19:52, nagranie 20:03;
zawiera opony 0145). Przebieg z HUD (klatki 1080×1200, ffmpeg): 0–15 s gaz, D4→D8, 1000–1600 obr/min; od ~15 s gaz puszczony,
D9, 41→31 km/h, 1200→900 obr/min (13 s: 1500, 16 s: 1150, 19 s: 1050, 21 s: 1000, 23 s: 950, 25 s: 900). Kamera w kabinie.

## Diagnoza (pomiar)
Narzędzia: `tools/audio/idle_diag.py`, `idle_spec.py`, `idle_render.py`, `idle_mix_report.py`; dowody `artifacts/audio-idle/`.
1. **Który zestaw grał:** widmo odcinka z gazem (11–14,5 s, 1500 obr/min) pokrywa się z syntezą `engine_cab_on_1500`
   (drabina 75/150/225/300 Hz, spadek powyżej 300 Hz), a nie z ElevenLabs `el_engine_cab_on_1500` (dominująca linia 235 Hz,
   której w nagraniu nie ma) — `diag/fingerprint.png`. Telefon miał w Ustawieniach zestaw **synteza** (PlayerPrefs przeżywa
   `adb install -r`; domyślny jest ElevenLabs).
2. **Odcinek po puszczeniu gazu (17–25 s):** RMS −29,6 dBFS (gaz −20,5). Linia zapłonu jest (49 Hz ≈ 980 obr/min / 20),
   ale nad nią szeroki garb 70–110 Hz zamiast drabiny harmonicznych, a obwiednia pasma 60–130 Hz jest modulowana
   z **14,2–15,1 Hz** (CV 0,66; przy gazie 0,27). Lustro runtime syntezy (sam silnik, 1150→900 obr/min, obciążenie 0)
   daje czystą drabinę i CV 0,21 — sam silnik tego nie robi.
3. **Źródło:** pętla sprężarki powietrza syntezy (`sfx_layers.compressor_loop`: 14 suwów/s przy 1000 obr/min, „thump”
   88 Hz) ma modulację **14,2 Hz** (CV 0,71) i energię w 60–120 Hz. HUD pokazuje 11,1/11,4 bar przy progu załączenia 11,0 bar,
   więc sprężarka ładowała. Wzmocnienie sprężarki 0,35 (kabina ×0,75) nie zależy od obciążenia silnika, a silnik bez obciążenia
   jest o ~10 dB cichszy niż pod gazem. Poziomy (RMS klipów × wzmocnienia runtime):

| | silnik bez obciążenia | sprężarka 0,35 | sprężarka − silnik |
|---|---|---|---|
| kabina, 600 obr/min, synteza / ElevenLabs | −34,2 / −36,4 dBFS | −30,0 / −31,1 | **+4,2 / +5,3 dB** |
| kabina, 900–1000 obr/min (hamowanie silnikiem), synteza / EL | −28,9 / −34,3 | −30,0 / −31,1 | −1,1 / **+3,2 dB** |
| zewnątrz, 600 obr/min, synteza / EL | −36,3 / −39,1 | −29,1 / −30,8 | **+7,2 / +8,3 dB** |

   Na jałowym i przy hamowaniu silnikiem sprężarka była głośniejsza od silnika (w obu zestawach), więc słychać było jej
   „pu-pu-pu” 14 Hz w paśmie, w którym powinny być harmoniczne zapłonu.
4. **Wycięcie ~110 Hz (hipoteza lidera): niepotwierdzone.** W widmie Welcha z rozdzielczością 1 Hz (0,5–26 s, 16–26 s) nie ma
   dołka przy 100–120 Hz (wahania ±2 dB), na spektrogramie STFT też nie. Ciemny pas na `spec.png` to artefakt skali
   logarytmicznej `showspectrumpic`. Brak też śladu filtra grzebieniowego (kolejne dołki 330/550 Hz).

5. **Odtworzenie w grze (Unity, nie lustro):** `IdleAudioCaptureTests` (PlayMode) jedzie zestawem 40 t z ciśnieniem 10,9 bar
   (sprężarka ładuje jak na nagraniu), 0,55 gazu przez 25 s, potem puszcza gaz: D9, 36–39 km/h, 1058–1159 obr/min,
   obciążenie 0,000, hamulec silnikowy 0. Co klatkę (0,01 s) zapisuje stan wszystkich AudioSource (klip, głośność, pitch,
   timeSamples); `idle_render.py` miksuje klipy dokładnie z tymi parametrami. Wynik zestawu synteza przed zmianą: po puszczeniu
   gazu modulacja 60–130 Hz z **15,6 Hz** (CV 0,58; 1100 obr/min × 14/1000 = 15,4 Hz), sprężarka −30,0 dBFS przy silniku
   −29,1 dBFS, garb 60–130 Hz zamiast drabiny — jak na nagraniu (`compare_owner_synth_before_after.jpg`: nagranie,
   przed, po). Po zmianie modulacja przechodzi na linię zapłonu (57 Hz), CV 0,46, sprężarka −45,3 dBFS.

| capture, kabina, toczenie ~1100 obr/min | silnik | sprężarka | opony | tło | miks |
|---|---|---|---|---|---|
| synteza przed / po | −29,1 / −28,8 | **−30,0 / −45,3** | −41,7 | −40,2 | −26,2 / −28,2 dBFS |
| ElevenLabs przed / po | −33,3 / −33,4 | **−31,1 / −46,6** | −34,2 / −34,6 | −43,4 | −27,7 / −30,3 dBFS |

6. **Dodatkowo (ElevenLabs, nie przyczyna zgłoszenia):** komórki kabina/bez obciążenia 1200 i 1500 mają słabą linię zapłonu
   (7,5–7,7 dB nad tłem; zewnątrz 21–25 dB, synteza 36–37 dB), a opony w kabinie (×1,35, ADR 0142) są przy 37 km/h na
   poziomie silnika bez obciążenia. Toczenie na biegu w zestawie ElevenLabs zostaje więc szumowe także po zmianie.
   Silnik ElevenLabs ma zostać bez zmian (decyzja właściciela, ADR 0142), dlatego tylko prośba o nagrania:
   `docs/owner/ELEVENLABS-REGEN-04.md` (opcjonalne, ~320 kredytów).

## Decyzja
`TruckAudioController.compressorVolume` 0,35 → **0,06** (−15,3 dB), w obu zestawach, kabina i zewnątrz (współczynnik kabiny
0,75 bez zmian). Sprężarka jest teraz ~10–11 dB pod silnikiem na jałowym w kabinie i 7–8 dB na zewnątrz (`WORKING_VALUE`,
ocena właściciela). Materiał ElevenLabs nie jest przyczyną zgłoszenia (nagranie było w trybie synteza, a ta sama nadwyżka
sprężarki występuje w obu zestawach).

Sprężarka − silnik po zmianie (lustro runtime, stała praca, sprężarka ładuje; `ab_levels.json`):

| kabina | 600 jałowy | 900 bez obc. | 900 pełne obc. | 900 + hamulec silnikowy |
|---|---|---|---|---|
| synteza przed / po | +4,2 / −11,1 dB | −0,1 / −15,4 | −12,6 / −27,9 | −8,7 / −24,1 |
| ElevenLabs przed / po | +5,4 / −10,0 dB | +3,3 / −12,0 | −8,3 / −23,7 | −7,1 / −22,4 |

## Odsłuch dla właściciela
`artifacts/audio-idle/ab/<zestaw>_<przypadek>_{before,after}.wav` (8 s, 48 kHz, wspólne wzmocnienie w parze): przypadki
`600_idle`, `900_noload`, `900_load`, `900_ebrake` (lustro runtime, postój, silnik + sprężarka) i `coast_capture`
(capture z gry: toczenie na D9 z oponami i tłem). Widma: `artifacts/audio-idle/ab_spectra.png`.

## Konsekwencje
- Sprężarka jest dalej słyszalna na postoju z bliska (zewnątrz), w kabinie ledwo.
- Do sprawdzenia przez właściciela: Ustawienia → DŹWIĘK → Zestaw dźwięków (nagranie było w trybie synteza).
