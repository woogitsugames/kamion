# ElevenLabs — przegenerowania 02 (silnik: przejazdy przez obroty)

Wersja s13, 2026-11-12, agent audio (ADR 0138). Format jak `ELEVENLABS-REGEN-01.md`. Model **v3**, plan Pro / ElevenCreative.
Analiza REGEN-01: `artifacts/audio-regen01/analysis/` (`picks.json`, `regen01.csv`, arkusze `sheets/`).

## Co wyszło z REGEN-01 (liczby)

- **Przejazd przez obroty działa.** `ENG_EXT_ON_SWEEP (4)`: linia rośnie od 904 do 1772 obr/min w 6,4 s, monotonicznie w 91 %, 22,7 dB nad tłem. Z tego jednego nagrania powstał cały wiersz „zewnątrz, pod obciążeniem” (6 komórek, jedna maszyna). Szczyt trwał jednak tylko ok. 2,7 s, a pętle muszą mieć > 3 s. Komórki 1800/2100 trzeba więc było sztucznie wydłużyć (×1,44/×1,68).
- Warianty (2) i (3) mają stałą składową ~46 Hz przez cały wzrost, przez co brzmią oktawę za nisko. Wariant (1) przeskakuje między harmonicznymi.
- **Kabina: żaden przejazd się nie nadaje.** Linia rośnie monotonicznie tylko w 25–77 %, przebiegi są schodkowe albo mają dwa garby.
- **Pętle „high revs” opisane słowami nadal nie dają wysokich obrotów.** Model robi jaśniejszy dźwięk o tej samej okresowości ~900 obr/min albo dodawanie gazu (3 z 4 wariantów ext/on). Pętle przy stałych obrotach odpuszczamy i zostajemy przy przejazdach.
- **Gwizd turbo:** w żadnym wariancie nie ma tonu (najsilniejsza wąska linia ma 3,5–4,5 dB nad szumem). Gwizd zostaje z syntezy, jedna ostatnia próba niżej (R4).
- **Stop w kabinie:** silnik gra równo do ok. 2,5 s, potem nagranie się kończy. Brak wybiegu (koniec tylko −3…−10 dB).
- **Wycieraczki:** ruch co 0,37 s zamiast co 1 s.
- Bez poprawek: `GEAR_UPSHIFT_CAB (6)`, `BRAKE_SERVICE_HISS (7)`, `CAB_DOOR_OPEN (7)` spełniają prompt.

## Koszt

Notatka REGEN-01: 56 generacji = 1594 kredyty, 4 × 6 s = 80 kredytów, czyli ok. 3,3 kredytu za sekundę (`UNVERIFIED`: to wyliczenie z salda, nie z cennika). Ta lista: 4 przejazdy × 4 × 30 s + 3 krótkie pozycje × 4 (razem 552 s) ≈ **1800 kredytów**. Najpierw R1–R2.

## Ustawienia (wszystkie poniżej, o ile nie napisano inaczej)
| Ustawienie | Wartość |
|---|---|
| Model | **v3** |
| Pętla (∞) | **Wyłączone** (R1–R3), **Włączone** (R4, R5) |
| Czas | **ręcznie**, przejazdy **30 s** (maksimum suwaka), reszta przy pozycji |
| Wpływ podpowiedzi | **80 %** |
| Auto-poprawa (różdżka) | **Wyłączone** |
| Ile wariantów | **4** |
Zapis jak poprzednio: `art-source/audio/elevenlabs/<ID> (n).wav`. Nowe ID od (1). Dla `ENG_EXT_ON_SWEEP` i `ENG_CAB_ON_SWEEP` numeracja od (5), bez nadpisywania (1)–(4).

## R1. Przejazdy pod obciążeniem z dłuższym szczytem

Powód: szczyt `ENG_EXT_ON_SWEEP (4)` trwał 2,7 s. Kabina nie dała żadnego ciągłego wzrostu. Prompt jest teraz wolniejszy, z wyraźnym trzymaniem maksymalnych obrotów i bez zdejmowania gazu na końcu.

**R1a. `ENG_EXT_ON_SWEEP` (5)–(8)** · 30 s
```
Heavy truck inline-six turbo diesel recorded outside by the exhaust stack, climbing a long steep hill in one low gear under full load: the engine starts at a low lazy speed and very slowly, smoothly and continuously gains revs for twenty seconds, then holds its maximum revs steadily until the end, no gear change, no throttle lift, no pauses, no music, no voices
```
**R1b. `ENG_CAB_ON_SWEEP` (5)–(8)** · 30 s
```
Inside a heavy truck cab climbing a long steep hill in one low gear under full load: the diesel drone starts low and very slowly, smoothly and continuously rises in pitch for twenty seconds, then stays at the highest pitch steadily until the end, engine heard through the floor and firewall, no gear change, no throttle lift, no road noise, no music, no voices
```

## R2. Przejazdy bez obciążenia (hamowanie silnikiem, zamknięty gaz)

Powód: wiersze „bez obciążenia” mają przy 1800/2100 przestrojenie ×1,62/×1,90 (ext) i ×1,26/×1,47 (kabina), a każda komórka pochodzi z innego nagrania. Wolny spadek obrotów z zamkniętym gazem da cały wiersz z jednej maszyny, tak jak R1 dał wiersz pod obciążeniem.

**R2a. `ENG_EXT_OFF_SWEEP`** · 30 s
```
Heavy truck inline-six diesel recorded outside, rolling down a long hill in one gear with the throttle fully closed: the engine starts at its maximum revs and very slowly, smoothly and continuously loses revs for twenty-five seconds down to a low idle, light hollow overrun sound, no exhaust brake, no gear change, no pauses, no music, no voices
```
**R2b. `ENG_CAB_OFF_SWEEP`** · 30 s
```
Inside a heavy truck cab rolling down a long hill in one gear with the throttle fully closed: the light diesel drone through the floor starts high and very slowly, smoothly and continuously falls in pitch for twenty-five seconds down to a low idle, no exhaust brake, no gear change, no road noise, no music, no voices
```

## R3. Wyłączenie silnika w kabinie (ponownie)

Powód: w REGEN-01 silnik pracował równo do końca i brakowało wybiegu. Teraz wyłączenie jest na początku, a po nim cisza. Czas 5 s, wpływ **70 %**.

**R3. `ENG_STOP_CAB`** · 5 s
```
Inside a heavy truck cab: the idling diesel engine is switched off after half a second, the engine speed sinks quickly, the cab gives one heavy shudder and the engine stops completely within two seconds, then quiet cab with only a faint tick of cooling metal, no music, no voices
```

## R4. Gwizd turbo (ostatnia próba, opcjonalnie)

Powód: w REGEN-01 nie było tonu. Jeśli tym razem też go nie będzie, gwizd na stałe zostaje z syntezy (sterowany doładowaniem z fizyki, ADR 0137) i nie wracamy do tematu. Pętla, 5 s, wpływ **90 %**.

**R4. `TURBO_WHISTLE_LOOP`** (5)–(8)
```
A single pure steady high-pitched whine, like a small turbine spinning at constant speed, one clean tone with almost no noise, no engine, no rumble, no air rush, no pitch change, seamless loop, no music, no voices
```

## R5. Wycieraczki (ponownie)

Powód: ruch co 0,37 s (prompt: co 1 s). Model zwykle przyspiesza rytm, więc prosimy o wolny tryb przerywany. Pętla, 8 s, wpływ **70 %**.

**R5. `CAB_WIPERS_LOOP`** (9)–(12)
```
Truck windscreen wipers on the slow intermittent setting: one slow sweep across wet glass with a soft rubber squeak, then a pause, then the next sweep, an even lazy rhythm of about one sweep every two seconds, faint motor hum, seamless loop, no music, no voices
```

## Co z nimi zrobię

`uv run python tools/audio/el_regen01.py` (dopiszę ID REGEN-02) → `el_prepare.py` (`SWEEP_ROWS`: wiersze ext/on, cab/on, ext/off, cab/off z przejazdów). Pętle wytnę i wyprostuję tak jak w ADR 0138. Ocena brzmienia na telefonie należy do Ciebie: **DŹWIĘK → Silnik: synteza / ElevenLabs** w ustawieniach, odsłuchy A/B w `artifacts/audio-regen01/ab/`.
