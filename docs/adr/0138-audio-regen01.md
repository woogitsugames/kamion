# ADR 0138 — Partia ElevenLabs REGEN-01: wybór wariantów i wiersz silnika z jednego przejazdu przez obroty
Status: Proposed (agent audio, s13), 2026-11-12. Ocena brzmienia: właściciel (telefon, głośnik i słuchawki).
Kontynuacja ADR 0137 (siatka z pomiaru, przełącznik synteza/ElevenLabs).

## Kontekst
Właściciel wygenerował partię REGEN-01 (`docs/owner/ELEVENLABS-REGEN-01.md`): 56 WAV, 14 promptów × 4 warianty.
Każdy wariant przeanalizowałem obiektywnie (`tools/audio/el_regen01.py` → `artifacts/audio-regen01/analysis/`:
`regen01.csv`, `picks.json`, arkusze `sheets/*.png` obejrzane). Mierzone wielkości: widmo, linia dominująca 20–120 Hz
(konwencja 0137: obroty = 20 × f), drabina, stabilność w oknach 1 s, poziom (zakres 250 ms), szew, LUFS, przesterowania
(0 we wszystkich 56 plikach), pasmo −60 dB. Do tego **test oktawy**: linia przy 0,5× lub 1,5× linii dominującej
(≥ 6 dB) albo okres YIN równy połowie linii oznacza, że pętla brzmi oktawę niżej, niż wynika z konwencji.

| ID | najlepszy | wynik (liczby) | spełnia prompt? |
|---|---|---|---|
| ENG_EXT_ON_HIGH | (2) | 912 obr/min; (1)(3)(4) to dodawanie gazu, a nie stałe obroty (zakres poziomu 21–25 dB) | nie |
| ENG_EXT_OFF_HIGH | (1) | linia 1859 obr/min, stabilna (4,8 %), ale linia 1,5× ma 24,9 dB, więc okres odpowiada 930 obr/min | nie (oktawa) |
| ENG_CAB_ON_HIGH | (3) | 1541 obr/min, stabilna (10,8 %), ale linia ma tylko 8,2 dB (filtr siatki ≥ 9) | tak, w siatce nie |
| ENG_CAB_OFF_HIGH | (1) | 1472 obr/min, rozrzut 15,2 %, linia 0 dB | nie |
| ENG_EXT_IDLE_SLOW | (4) | 737 obr/min, rozrzut 12,4 %; obecne źródło (883, 4,5 %) wygrywa ranking | tak, w siatce nie |
| ENG_CAB_IDLE_SLOW | (4) | 723 obr/min, rozrzut 9,2 %, linia 19,8 dB | **tak → cab/off 600** |
| TURBO_WHISTLE_LOOP | (3) | najsilniejsza wąska linia 1,5–12 kHz ma 3,5–4,5 dB nad tłem (próg 12), rozrzut 10–19 % | nie |
| ENG_EXT_ON_SWEEP | (4) | linia 904→1772 obr/min w 6,4 s, rośnie monotonicznie w 91 %, 22,7 dB, okres = linia w 100 % okien 1 s | **tak → wiersz ext/on** |
| ENG_CAB_ON_SWEEP | (3) | wzrost monotoniczny tylko w 25–77 %, okres zgodny w 11–67 %; przebiegi schodkowe lub z dwoma garbami | nie |
| ENG_STOP_CAB | (4) | koniec −2,9…−9,9 dB względem początku (próg −15); brak wybiegu, silnik pracuje do 2,5 s | nie |
| GEAR_UPSHIFT_CAB | (6) | klik 20,3 dB nad tłem HF, spadek linii o 14 %, poziom po zmianie +2 dB | tak (z sekcji C, niewpięte) |
| BRAKE_SERVICE_HISS | (7) | atak 0 ms, 94 % energii > 2 kHz, −20 dB po 0,18 s, jeden impuls, −20,4 LUFS | tak (niewpięte) |
| CAB_WIPERS_LOOP | (6) | okres ruchu 0,37 s (prompt: 1 s), CV 9,4 % | nie |
| CAB_DOOR_OPEN | (7) | zatrzask w 0,00 s, warstwa powietrza +14,2 dB nad tłem sprzed zatrzasku | tak (niewpięte) |

## Decyzja
1. **Wiersz zewnątrz/pod obciążeniem (6 komórek) z jednego przejazdu `ENG_EXT_ON_SWEEP (4)`** (`tools/audio/el_sweepcut.py`,
   `el_prepare.SWEEP_ROWS`). Śledzę jedną linię widma: okna z arkusza (`SWEEP_WINDOWS`, wpis autorski). Dla obrotów R
   biorę najdłuższy segment, w którym linia mieści się w ±20 % R/20. Segment jest **prostowany**: próbka wyjściowa n
   czyta wejście w chwili, gdy skumulowana faza linii równa się R/20 · n/fs (interpolacja sześcienna). Linia leży wtedy
   dokładnie na R/20, a pozostałe składowe przesuwają się o ten sam lokalny współczynnik. Narastanie głośności w segmencie
   wyrównuję obwiednią RMS 50 ms wygładzoną na 0,6 s, szew to crossfade 40 ms. Poniżej zakresu (600/900) używam biegu
   jałowego przed wzrostem (5–9 s, ten sam warp). Powyżej (1800/2100) używam szczytu wzrostu. Szczyt jest krótki
   (2,75 s), więc wydłużam go synchronicznym z tonem PSOLA ×1,44/×1,68, żeby każda pętla trwała > 3 s
   (wymóg `ElevenLabsEngineAudioTests`). Warp lokalny 0,63–1,48. W 0137 cała pętla była przestrajana ×0,69–×1,60
   z 3 nagrań.
   Wybór (4), a nie (2), choć `el_regen01` dawał (2) najwyższy wynik przed testem oktawy. W (2) i (3) przez cały
   wzrost biegnie stała składowa ~46 Hz. Ich komórki 1500/1800 mają okres YIN 0,49/0,51 linii (`artifacts/audio-regen01/sweepcut.txt`).
2. **Kabina/bez obciążenia 600** ← `ENG_CAB_IDLE_SLOW (4)` (×0,83 zamiast ×0,74). Ranking `el_prepare` sam ją wybiera
   po poszerzeniu zakresu kandydatów do 580–2000 obr/min.
3. **Filtr dwuznacznej drabiny** w `el_prepare.candidates`: źródło z linią ≥ 6 dB przy 0,5× lub 1,5× linii dominującej
   nie wchodzi do siatki. Odrzuca to `ENG_EXT_OFF_HIGH (1)`, które dałoby ext/off 1500–2100 brzmiące oktawę niżej
   niż 1200 (YIN 0,50 przy aperiodyczności 0,27–0,31). Kandydaci z niestabilnym poziomem (zakres > 8 dB) też odpadają.
4. **`el_verify`** raportuje dodatkowo okres YIN (`octave_low`) oraz krok barwy między sąsiednimi komórkami (średnia
   |Δ| znormalizowanych pasm 1/3 oktawy).
5. **Bez zmian:** gwizd turbo zostaje z syntezy (nadal brak tonu). Stop w kabinie zostaje filtrowanym stopem
   zewnętrznym (brak wybiegu). Pozostałe komórki, hamulec wydechowy i zdarzenia zostają jak w 0137. Najlepsze warianty
   C–F (`GEAR_UPSHIFT_CAB (6)`, `BRAKE_SERVICE_HISS (7)`, `CAB_DOOR_OPEN (7)`) są zapisane w `picks.json` dla
   osobnego zadania wpięcia sekcji C–G (0137: poza zakresem).
6. **Pliki:** polityka 0137 bez zmian. Do gita (LFS) trafiają tylko przetworzone klipy `ElevenLabs/Clips/**`, czyli
   7 zmienionych WAV, plus `el_manifest.json` z pochodzeniem (segment, warp, wyrównanie, stretch). Surowe 56 WAV zostają
   u właściciela, poza gitem. Dowody i odsłuchy: `artifacts/audio-regen01/`.

## Wyniki (pomiar)
- `el_verify`: 32 pętle, 0 FAIL (ton ±4 %, szew < 1, szpilka HF < 6 dB, szczyt ≤ −1 dBFS). Wiersz ext/on: błąd tonu
  −0,4…+1,1 %, okres YIN 0,98–1,02 linii przy aperiodyczności 0,12–0,35. W 0137 ten wiersz miał 0,51/0,75/0,50
  przy 1200/1500/1800.
- Krok barwy ext/on: 3,93 → 3,35 dB (1 źródło zamiast 3). Pozostałe wiersze bez zmian.
- Sweep przez lustro runtime (`el_sweep.py`): brak skoków w punktach siatki. Maks. zmiana RMS 100 ms dla ext przy
  pełnym obciążeniu 3,5 dB (0137: 2,5 dB). Wynika to z chropowatości nagrania pod obciążeniem, wahania widać na całym
  zakresie, nie przy granicach komórek (`verify/sweep.png`).
- Unity: import OK (32 pętle + 10 sfx). PlayMode 19/19 (ElevenLabsEngineAudioTests, AudioLayers, ControlSettingsPanel,
  DrivingLabScene). EditMode audio/ustawienia 20/20. Pełny EditMode: 379/402, 8 FAIL poza audio (CarPaint, Mirror,
  TruckDoorCrown, LightPost). Wymagają wygenerowanych assetów ciężarówki, których nie ma w świeżym worktree.

## Konsekwencje
- Odsłuch A/B dla właściciela (≤ 30 s, OGG): `artifacts/audio-regen01/ab/drive_{ext,cab}_{0137,0138}.ogg`,
  `sweep_ext_on_{0137,0138}.ogg`. Do oceny: czy PSOLA w 1800/2100 i wyrównanie poziomu nie dają słyszalnej
  „ziarnistości” lub pompowania.
- Siatka ma teraz 12 źródeł na 24 komórki (0137: 14). ext/off 1800/2100 to nadal ×1,62/×1,90, cab/on 1800/2100 ×1,38/×1,45.
  Prośba o przejazdy bez obciążenia i z kabiny oraz pozostałe poprawki: `docs/owner/ELEVENLABS-REGEN-02.md`.
- Wnioski o modelu (do promptów): ElevenLabs v3 nie robi stałych wysokich obrotów. Słowa „high revs” dają jaśniejszy
  dźwięk z tą samą okresowością ~900 obr/min albo dodawanie gazu. Jednorazowy przejazd przez obroty działa (1 z 4
  czysty), dlatego REGEN-02 opiera się na przejazdach.
- RAM: próbki pętli ElevenLabs 8,85 M → 8,27 M (−6,5 %, krótsze pętle ext/on), szacunek 0137 bez zmian. Do zmierzenia na A16 (PSS).
