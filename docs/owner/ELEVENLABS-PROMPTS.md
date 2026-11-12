# Prompty ElevenLabs (Sound Effects v3) — dźwięki ciężarówki Kamion

Wersja s12, 2026-11-12. Do wygenerowania przez właściciela w ElevenLabs Sound Effects (model **v3**).
Prompty są po angielsku, bo ElevenLabs tak zaleca. Każdy opisuje **fikcyjny** ciężki ciągnik siodłowy: 13-litrowy rzędowy 6-cylindrowy diesel, turbo, 12-biegowa zautomatyzowana skrzynia (AMT), hamulce pneumatyczne, naczepa 40 t. **Bez marek**: nie wpisuj nazw producentów, bo to zakaz z docs/08 i CLAUDE.md p.8.

## Jak generować

- **Pętla (∞):** **Włączone** tylko tam, gdzie w tabeli jest `LOOP`. Dla dźwięków jednorazowych (`ONE-SHOT`) wyłączone.
- **Czas trwania:** zawsze **ręcznie** (suwak), wartość z opisu/tabeli — **nie Auto**.
- **Wpływ podpowiedzi:** wartość z kolumny „Wpływ”. Wyższy daje dosłowniejszy wynik, potrzebny dla pętli o stałych obrotach. Niższy zostawia więcej swobody, przydatny dla otoczenia.
- **Auto-poprawa podpowiedzi (różdżka):** **Wyłączone**, bo prompty są już dokładne, a auto-poprawka dopisuje efekty.
- Każdy prompt wygeneruj **2–4 razy**. Zachowaj wszystkie warianty, z których wybiorę (porównam spektrogramy z modelem fizyki).
- **Zapis:** `C:\Users\matma\Documents\Claude\kamion\art-source\audio\elevenlabs\<ID>_v<n>.mp3` (np. `ENG_EXT_ON_1200_v2.mp3`). Format: najwyższa jakość, jaką daje plan (WAV/MP3 320 kbps). Jeśli folder nie istnieje, utwórz go.
- **Licencja:** zanotuj nazwę planu ElevenLabs i datę generacji (np. w `notes.txt` w tym folderze). Płatny plan pozwala na użytek komercyjny, ale do `docs/LICENSES.md` wpiszę warunki z regulaminu z dnia generacji.
- Pętle silnika muszą mieć **stałe obroty**: bez wkręcania, bez zmiany wysokości tonu, bez zmiany biegu. Silnik w grze składa się z wielu takich pętli, przenikanych zależnie od obrotów i obciążenia z fizyki. Wahania wewnątrz pętli psują efekt.

## A. Silnik — pętle stałych obrotów (najważniejsze)
Zakres silnika w grze: jałowy 600 obr/min, odcięcie 2100. Wszystkie 24 pozycje mają **te same ustawienia**:
| Ustawienie w ElevenLabs | Wartość |
|---|---|
| Model | **v3** |
| Pętla (∞) | **Włączone** |
| Czas trwania | **ręcznie, 6 s** (jałowy 600: **8 s**) — NIE Auto |
| Wpływ podpowiedzi | **70 %** |
| Auto-poprawa (różdżka) | **Wyłączone** |
| Ile razy | 2–4 warianty każdej pozycji |
Nazwa pliku: `<ID>_v1.mp3`, `<ID>_v2.mp3`… w `art-source/audio/elevenlabs/`.
**Zacznij od 4 pozycji 1200 obr/min (A9–A12)** i daj mi znać — sprawdzę, czy trzymają stałe obroty, zanim wygenerujesz resztę.

### 600 obr/min

**A1. `ENG_EXT_ON_600`** — zewnątrz, pod obciążeniem · Pętla: Włączone · Czas: 8 s · Wpływ: 70 %
```
Heavy truck 13-litre inline-six diesel engine idling at a steady 600 rpm recorded from outside near the exhaust stack, deep slow firing pulse, air compressor and fan running, no revving, no pitch change, seamless loop, no music, no voices
```

**A2. `ENG_EXT_OFF_600`** — zewnątrz, bez obciążenia · Pętla: Włączone · Czas: 8 s · Wpływ: 70 %
```
Heavy truck 13-litre inline-six diesel engine idling at a steady 600 rpm recorded from outside, quiet slow firing pulse, light injector clatter, no revving, no pitch change, seamless loop, no music, no voices
```

**A3. `ENG_CAB_ON_600`** — kabina, pod obciążeniem · Pętla: Włączone · Czas: 8 s · Wpływ: 70 %
```
Interior of a heavy truck cab with the engine idling at a steady 600 rpm, muffled deep slow rumble through the floor, faint fan and compressor hum, no road noise, no revving, no pitch change, seamless loop, no music, no voices
```

**A4. `ENG_CAB_OFF_600`** — kabina, bez obciążenia · Pętla: Włączone · Czas: 8 s · Wpływ: 70 %
```
Interior of a heavy truck cab with the engine idling at a steady 600 rpm, very quiet muffled slow rumble, light ticking, no road noise, no revving, no pitch change, seamless loop, no music, no voices
```

### 900 obr/min

**A5. `ENG_EXT_ON_900`** — zewnątrz, pod obciążeniem · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Heavy truck 13-litre inline-six turbo diesel engine recorded from outside near the exhaust stack, steady constant 900 rpm under heavy load pulling a 40-tonne trailer, deep low-frequency firing pulse, gritty combustion, faint turbo whistle, no revving, no gear change, no pitch change, seamless loop, no music, no voices
```

**A6. `ENG_EXT_OFF_900`** — zewnątrz, bez obciążenia · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Heavy truck 13-litre inline-six diesel engine recorded from outside, steady constant 900 rpm with no load while coasting, softer lighter firing pulse, slight injector clatter, no turbo whistle, no revving, no pitch change, seamless loop, no music, no voices
```

**A7. `ENG_CAB_ON_900`** — kabina, pod obciążeniem · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Interior of a heavy truck cab, inline-six diesel engine heard through the floor and firewall, steady constant 900 rpm under heavy load, muffled deep low-end rumble, subtle cab vibration hum, faint turbo whine, no road noise, no revving, no pitch change, seamless loop, no music, no voices
```

**A8. `ENG_CAB_OFF_900`** — kabina, bez obciążenia · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Interior of a heavy truck cab, inline-six diesel engine heard through the floor, steady constant 900 rpm with no load while coasting, quiet muffled low rumble, light mechanical ticking, no road noise, no revving, no pitch change, seamless loop, no music, no voices
```

### 1200 obr/min

**A9. `ENG_EXT_ON_1200`** — zewnątrz, pod obciążeniem · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Heavy truck 13-litre inline-six turbo diesel engine recorded from outside near the exhaust stack, steady constant 1200 rpm under heavy load pulling a 40-tonne trailer, deep low-frequency firing pulse, gritty combustion, faint turbo whistle, no revving, no gear change, no pitch change, seamless loop, no music, no voices
```

**A10. `ENG_EXT_OFF_1200`** — zewnątrz, bez obciążenia · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Heavy truck 13-litre inline-six diesel engine recorded from outside, steady constant 1200 rpm with no load while coasting, softer lighter firing pulse, slight injector clatter, no turbo whistle, no revving, no pitch change, seamless loop, no music, no voices
```

**A11. `ENG_CAB_ON_1200`** — kabina, pod obciążeniem · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Interior of a heavy truck cab, inline-six diesel engine heard through the floor and firewall, steady constant 1200 rpm under heavy load, muffled deep low-end rumble, subtle cab vibration hum, faint turbo whine, no road noise, no revving, no pitch change, seamless loop, no music, no voices
```

**A12. `ENG_CAB_OFF_1200`** — kabina, bez obciążenia · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Interior of a heavy truck cab, inline-six diesel engine heard through the floor, steady constant 1200 rpm with no load while coasting, quiet muffled low rumble, light mechanical ticking, no road noise, no revving, no pitch change, seamless loop, no music, no voices
```

### 1500 obr/min

**A13. `ENG_EXT_ON_1500`** — zewnątrz, pod obciążeniem · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Heavy truck 13-litre inline-six turbo diesel engine recorded from outside near the exhaust stack, steady constant 1500 rpm under heavy load pulling a 40-tonne trailer, deep low-frequency firing pulse, gritty combustion, faint turbo whistle, no revving, no gear change, no pitch change, seamless loop, no music, no voices
```

**A14. `ENG_EXT_OFF_1500`** — zewnątrz, bez obciążenia · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Heavy truck 13-litre inline-six diesel engine recorded from outside, steady constant 1500 rpm with no load while coasting, softer lighter firing pulse, slight injector clatter, no turbo whistle, no revving, no pitch change, seamless loop, no music, no voices
```

**A15. `ENG_CAB_ON_1500`** — kabina, pod obciążeniem · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Interior of a heavy truck cab, inline-six diesel engine heard through the floor and firewall, steady constant 1500 rpm under heavy load, muffled deep low-end rumble, subtle cab vibration hum, faint turbo whine, no road noise, no revving, no pitch change, seamless loop, no music, no voices
```

**A16. `ENG_CAB_OFF_1500`** — kabina, bez obciążenia · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Interior of a heavy truck cab, inline-six diesel engine heard through the floor, steady constant 1500 rpm with no load while coasting, quiet muffled low rumble, light mechanical ticking, no road noise, no revving, no pitch change, seamless loop, no music, no voices
```

### 1800 obr/min

**A17. `ENG_EXT_ON_1800`** — zewnątrz, pod obciążeniem · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Heavy truck 13-litre inline-six turbo diesel engine recorded from outside near the exhaust stack, steady constant 1800 rpm under heavy load pulling a 40-tonne trailer, deep low-frequency firing pulse, gritty combustion, faint turbo whistle, no revving, no gear change, no pitch change, seamless loop, no music, no voices
```

**A18. `ENG_EXT_OFF_1800`** — zewnątrz, bez obciążenia · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Heavy truck 13-litre inline-six diesel engine recorded from outside, steady constant 1800 rpm with no load while coasting, softer lighter firing pulse, slight injector clatter, no turbo whistle, no revving, no pitch change, seamless loop, no music, no voices
```

**A19. `ENG_CAB_ON_1800`** — kabina, pod obciążeniem · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Interior of a heavy truck cab, inline-six diesel engine heard through the floor and firewall, steady constant 1800 rpm under heavy load, muffled deep low-end rumble, subtle cab vibration hum, faint turbo whine, no road noise, no revving, no pitch change, seamless loop, no music, no voices
```

**A20. `ENG_CAB_OFF_1800`** — kabina, bez obciążenia · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Interior of a heavy truck cab, inline-six diesel engine heard through the floor, steady constant 1800 rpm with no load while coasting, quiet muffled low rumble, light mechanical ticking, no road noise, no revving, no pitch change, seamless loop, no music, no voices
```

### 2100 obr/min

**A21. `ENG_EXT_ON_2100`** — zewnątrz, pod obciążeniem · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Heavy truck 13-litre inline-six turbo diesel engine recorded from outside near the exhaust stack, steady constant 2100 rpm under heavy load pulling a 40-tonne trailer, deep low-frequency firing pulse, gritty combustion, faint turbo whistle, no revving, no gear change, no pitch change, seamless loop, no music, no voices
```

**A22. `ENG_EXT_OFF_2100`** — zewnątrz, bez obciążenia · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Heavy truck 13-litre inline-six diesel engine recorded from outside, steady constant 2100 rpm with no load while coasting, softer lighter firing pulse, slight injector clatter, no turbo whistle, no revving, no pitch change, seamless loop, no music, no voices
```

**A23. `ENG_CAB_ON_2100`** — kabina, pod obciążeniem · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Interior of a heavy truck cab, inline-six diesel engine heard through the floor and firewall, steady constant 2100 rpm under heavy load, muffled deep low-end rumble, subtle cab vibration hum, faint turbo whine, no road noise, no revving, no pitch change, seamless loop, no music, no voices
```

**A24. `ENG_CAB_OFF_2100`** — kabina, bez obciążenia · Pętla: Włączone · Czas: 6 s · Wpływ: 70 %
```
Interior of a heavy truck cab, inline-six diesel engine heard through the floor, steady constant 2100 rpm with no load while coasting, quiet muffled low rumble, light mechanical ticking, no road noise, no revving, no pitch change, seamless loop, no music, no voices
```

## B. Silnik — zdarzenia

| ID | Prompt | Typ | Czas | Wpływ |
|---|---|---|---|---|
| ENG_START_EXT | `Heavy truck inline-six diesel engine cold start from outside, starter motor cranking for about one second, engine catches, brief rev flare then settles into a steady idle, no music, no voices` | ONE-SHOT | 5 s | 60 % |
| ENG_START_CAB | `Inside a heavy truck cab, starter motor cranking, inline-six diesel engine catches and settles into idle, heard muffled through the cab floor, dashboard warning chime once, no music, no voices` | ONE-SHOT | 5 s | 60 % |
| ENG_STOP_EXT | `Heavy truck inline-six diesel engine switched off from idle outside, engine shudders and runs down to silence, small metallic tick at the end, no music, no voices` | ONE-SHOT | 3 s | 60 % |
| ENG_IDLE_CLATTER | `Close-up mechanical clatter of a heavy truck diesel engine idling, injector ticking and valve train chatter, steady, seamless loop, no music, no voices` | LOOP | 5 s | 65 % |
| TURBO_SPOOL | `Heavy truck turbocharger spooling up during hard acceleration, rising whistle from low to high over two seconds, diesel rumble underneath, no music, no voices` | ONE-SHOT | 3 s | 60 % |
| TURBO_WASTEGATE | `Heavy truck turbo blow-off, short pneumatic psst and fluttering air release when the driver lifts off the throttle, no music, no voices` | ONE-SHOT | 1.5 s | 60 % |
| EXHAUST_BRAKE_LOOP | `Heavy truck engine exhaust brake engaged while descending, steady harsh throaty roar from the exhaust at constant engine speed, no gear change, seamless loop, no music, no voices` | LOOP | 6 s | 65 % |
| RETARDER_LOOP | `Hydraulic retarder of a heavy truck working at speed, low steady whining hum with a soft rushing oil sound under the cab, constant, seamless loop, no music, no voices` | LOOP | 6 s | 65 % |

## C. Skrzynia biegów (12-biegowa AMT)

| ID | Prompt | Typ | Czas | Wpływ |
|---|---|---|---|---|
| GEAR_UPSHIFT_CAB | `Inside a heavy truck cab, automated manual gearbox upshift: engine note drops as the clutch disengages, short pneumatic actuator click and hiss, gear engages with a soft clunk, engine pulls again at lower rpm, no music, no voices` | ONE-SHOT | 2 s | 60 % |
| GEAR_DOWNSHIFT_CAB | `Inside a heavy truck cab, automated gearbox downshift: brief engine rev-match blip, pneumatic shift click and hiss, gear engages with a clunk, no music, no voices` | ONE-SHOT | 2 s | 60 % |
| GEARBOX_WHINE_LOOP | `Heavy truck gearbox gear whine heard in the cab at steady cruising speed, faint high-pitched mechanical whine, constant, seamless loop, no engine revving, no music, no voices` | LOOP | 6 s | 60 % |

## D. Pneumatyka i hamulce

| ID | Prompt | Typ | Czas | Wpływ |
|---|---|---|---|---|
| AIR_PARKING_RELEASE | `Heavy truck parking brake released, loud sharp pneumatic hiss of compressed air, short, recorded outside near the axle, no music, no voices` | ONE-SHOT | 1.5 s | 65 % |
| AIR_PARKING_APPLY | `Heavy truck parking brake applied, short loud burst of compressed air exhaust psshh, outside, no music, no voices` | ONE-SHOT | 1.5 s | 65 % |
| AIR_DRYER_PURGE | `Heavy truck air dryer purge when the compressor cuts out, loud sudden blast of air from under the chassis followed by a short tail, no music, no voices` | ONE-SHOT | 2 s | 65 % |
| AIR_COMPRESSOR_LOOP | `Heavy truck air compressor running at idle, rhythmic low mechanical chugging under the engine, steady, seamless loop, no music, no voices` | LOOP | 5 s | 60 % |
| BRAKE_SERVICE_HISS | `Heavy truck service brake pedal released after a stop, short soft pneumatic hiss from the brake valves, no music, no voices` | ONE-SHOT | 1 s | 60 % |
| BRAKE_SQUEAL_STOP | `Heavy truck with trailer coming to a stop at low speed, drum brakes squealing softly, last metallic groan, short air release at the end, no music, no voices` | ONE-SHOT | 3 s | 55 % |
| BRAKE_ROLL_LOOP | `Heavy truck braking steadily at moderate speed on asphalt, low rumbling friction from drum brakes and tyres, constant, seamless loop, no music, no voices` | LOOP | 5 s | 55 % |
| TRAILER_COUPLE | `Semi-trailer fifth wheel coupling: heavy truck reverses under the trailer, loud metallic clunk as the kingpin locks, then air lines hiss when connected, no music, no voices` | ONE-SHOT | 4 s | 60 % |

## E. Opony, droga, zawieszenie

| ID | Prompt | Typ | Czas | Wpływ |
|---|---|---|---|---|
| TYRE_ASPHALT_50 | `Heavy truck tyres rolling on dry asphalt at 50 km/h heard from inside the cab, steady low road rumble and tyre hum, no engine, seamless loop, no music, no voices` | LOOP | 6 s | 60 % |
| TYRE_ASPHALT_80 | `Heavy truck tyres rolling on dry asphalt at 80 km/h heard from inside the cab, steady louder road roar and tyre hum, no engine, seamless loop, no music, no voices` | LOOP | 6 s | 60 % |
| TYRE_PAVERS_20 | `Heavy truck tyres rolling slowly over concrete paving stones in a yard at 20 km/h, rhythmic soft thumping over the joints, no engine, seamless loop, no music, no voices` | LOOP | 6 s | 60 % |
| TYRE_GRAVEL_15 | `Heavy truck tyres rolling slowly on loose gravel, crunching and popping stones, no engine, seamless loop, no music, no voices` | LOOP | 6 s | 60 % |
| TYRE_WET_60 | `Heavy truck tyres on a wet asphalt road at 60 km/h, steady water spray hiss and swish, no engine, seamless loop, no music, no voices` | LOOP | 6 s | 60 % |
| SUSP_BUMP | `Heavy truck cab going over a pothole, single hard thump from the suspension with a metallic rattle of the cab and trailer, no music, no voices` | ONE-SHOT | 1.5 s | 55 % |
| TRAILER_RATTLE_LOOP | `Empty semi-trailer rattling behind a truck on an uneven road, loose metallic clanking and body creaks, steady, seamless loop, no music, no voices` | LOOP | 6 s | 50 % |

## F. Kabina — przełączniki i drobne

| ID | Prompt | Typ | Czas | Wpływ |
|---|---|---|---|---|
| CAB_INDICATOR_LOOP | `Truck turn signal indicator relay ticking inside the cab, steady tick-tock at about 1.5 ticks per second, seamless loop, no music, no voices` | LOOP | 4 s | 75 % |
| CAB_SWITCH | `Single click of a chunky plastic rocker switch on a truck dashboard, close-up, no music, no voices` | ONE-SHOT | 0.5 s | 70 % |
| CAB_DOOR_OPEN | `Heavy truck cab door unlatched and swung open, solid metal latch clunk, outside air noise, no music, no voices` | ONE-SHOT | 2 s | 60 % |
| CAB_DOOR_CLOSE | `Heavy truck cab door slammed shut from inside, deep solid thud and latch, cab goes quieter, no music, no voices` | ONE-SHOT | 1.5 s | 60 % |
| CAB_WIPERS_LOOP | `Truck windscreen wipers sweeping back and forth on a wet windscreen, motor hum and rubber squeak, steady rhythm, seamless loop, no music, no voices` | LOOP | 6 s | 60 % |
| CAB_RAIN_ROOF_LOOP | `Steady rain falling on the metal roof and windscreen of a parked truck cab heard from inside, constant, seamless loop, no thunder, no music, no voices` | LOOP | 10 s | 50 % |
| HORN_AIR | `Heavy truck air horn, one long blast of about 1.5 seconds, outside, no music, no voices` | ONE-SHOT | 2.5 s | 65 % |
| REVERSE_BEEPER_LOOP | `Truck reversing alarm, steady beep-beep warning heard from outside, seamless loop, no music, no voices` | LOOP | 4 s | 75 % |

## G. Otoczenie (Białystok, strefa przemysłowa)

| ID | Prompt | Typ | Czas | Wpływ |
|---|---|---|---|---|
| AMB_INDUSTRIAL_DAY | `Outdoor ambience of a quiet industrial zone on the edge of a city on an overcast day, distant traffic on a dual carriageway, occasional far-off truck, light wind, a few birds, no music, no voices, seamless loop` | LOOP | 20 s | 40 % |
| AMB_YARD_LOGISTICS | `Logistics yard ambience, distant forklift beeping, a truck idling far away, faint metallic clanks, light wind, no music, no voices, seamless loop` | LOOP | 20 s | 40 % |
| AMB_WIND_CAB_80 | `Wind noise around a heavy truck cab at 80 km/h heard from inside, steady airy rush around the mirrors and A-pillars, seamless loop, no engine, no music, no voices` | LOOP | 8 s | 55 % |
| AMB_PASSING_CAR | `A car passing a stationary truck at about 60 km/h on a wet road, quick doppler whoosh, no music, no voices` | ONE-SHOT | 3 s | 55 % |

## Kolejność generacji

Wygeneruj najpierw A9–A12 (1200 obr/min), potem `ENG_START_EXT`, `GEAR_UPSHIFT_CAB`, `AIR_PARKING_RELEASE` i `TYRE_ASPHALT_50`. Sprawdzę, czy ElevenLabs trzyma stałe obroty i czysto zapętla. Jeśli tak, robimy resztę. Jeśli nie, poprawię prompty.

## Co zrobię z plikami

1. Analiza: spektrogram, stałość obrotów, szew pętli, LUFS.
2. Wybór wariantów i dopasowanie wysokości tonu do obrotów z fizyki.
3. Wpięcie do `TruckAudioController` jako warstwy obok syntezy proceduralnej.
4. Wpis w `docs/LICENSES.md` i ADR.

Ostateczna ocena należy do Ciebie, na telefonie (głośnik i słuchawki).
