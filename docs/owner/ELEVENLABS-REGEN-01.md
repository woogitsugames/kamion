# ElevenLabs — przegenerowania 01 (silnik)

Wersja s12, 2026-11-12, agent audio (ADR 0137). Format jak `ELEVENLABS-PROMPTS.md`. Model **v3**, plan ElevenCreative Pro.
Analiza wszystkich 248 plików: `artifacts/audio-el/analysis/` (tabela `analysis.csv`, arkusze spektrogramów `sheets/`).

## Co wyszło z pierwszej partii (liczby)

- **Pętle silnika (A, 96 plików):** obroty są **stałe** w pliku (mediana wahania linii dominującej 9 % w oknach 1 s, czyli mniej więcej szum pomiaru; na spektrogramach są poziome linie, bez wkręcania). **ElevenLabs nie rozumie jednak liczby obrotów z promptu.** Dominująca linia w 67 plikach z wyraźnym tonem leży przy 36–72 Hz. Daje to ok. 700–1450 obr/min, mediana **933 obr/min**, i tak samo dla promptów 600 i 2100 obr/min. Korelacja „obroty w prompcie → obroty zmierzone” wynosi r = 0,24. Mediany zmierzone dla promptów 600/900/1200/1500/1800/2100: 876/928/953/960/1236/912 obr/min.
- Gra i tak ich używa: brałem najlepsze stabilne pętle z całej puli danej perspektywy i obciążenia i przestroiłem je offline do 600…2100 obr/min. Przy 1800–2100 obr/min oznacza to podwyższenie tonu ×1,4–1,9, a przy 600 obniżenie ×0,68. Przy dużym przestrojeniu szum spalania też zmienia barwę (wyżej brzmi „cieniej”, niżej „mętniej”). Dlatego proszę o pętle wysokich obrotów i wolnego biegu jałowego **opisane słowami, bez liczb**.
- **B:** `TURBO_SPOOL`: na spektrogramie nie ma rosnącego gwizdu (żadnej linii tonalnej 2–8 kHz), jest tylko narastający szum. Nie jest użyty. Gwizd zostaje z syntezy i jest sterowany doładowaniem z fizyki. Prośba R3 dotyczy stałego gwizdu jako pętli. Pozostałe pliki B są w grze: start zewn./kabina, stop, klekot, wastegate, hamulec wydechowy, retarder.
- **C–G:** wszystkie pętle mają szew bez klika (skok < 1 × p99,9, z wyjątkiem `REVERSE_BEEPER_LOOP (4)`), nic nie jest przesterowane (0 próbek ≥ 0,999). Nie trzeba ich przegenerowywać; wpięcie w osobnym zadaniu.

## Koszt

Według `elevenlabs.io/pricing` (stan 2026-11-12) efekt dźwiękowy kosztuje **200 kredytów za generację**. `UNVERIFIED`: przy ręcznie ustawionym czasie licznik może liczyć za sekundę, sprawdź na koncie po pierwszej generacji. Ta lista to **10 promptów × 4 warianty = 40 generacji ≈ 8 000 kredytów** (1,3 % z 600 tys. miesięcznie).

## Ustawienia (wszystkie poniżej, o ile nie napisano inaczej)
| Ustawienie | Wartość |
|---|---|
| Model | **v3** |
| Pętla (∞) | **Włączone** (R1–R3), **Wyłączone** (R4, R5) |
| Czas | **ręcznie**, wartość przy pozycji — NIE Auto |
| Wpływ podpowiedzi | **80 %** (pętle silnika: dosłowniej niż 70 % w pierwszej partii) |
| Auto-poprawa (różdżka) | **Wyłączone** |
| Ile wariantów | **4** |
Zapis jak poprzednio: `art-source/audio/elevenlabs/<ID> (n).wav`.

## R1. Wysokie obroty (zastępują 1800/2100 z partii A)

Powód: zmierzone 796–1449 obr/min zamiast 1800–2100. Teraz komórki 1800/2100 to przestrojenie ×1,4–1,9.

**R1a. `ENG_EXT_ON_HIGH`** — zewnątrz, pod obciążeniem · Pętla · 6 s · 80 %
```
Heavy truck inline-six turbo diesel at high revs near its governed maximum, recorded outside by the exhaust stack, pulling hard uphill in a low gear, fast busy firing rhythm blending into a gritty high drone, loud turbo whistle, held perfectly steady, no gear change, no pitch change, seamless loop, no music, no voices
```
**R1b. `ENG_EXT_OFF_HIGH`** — zewnątrz, bez obciążenia · Pętla · 6 s · 80 %
```
Heavy truck inline-six diesel spinning at high revs with the throttle closed, recorded outside, fast light firing rhythm, hollow high-pitched drone, no turbo whistle, held perfectly steady, no pitch change, seamless loop, no music, no voices
```
**R1c. `ENG_CAB_ON_HIGH`** — kabina, pod obciążeniem · Pętla · 6 s · 80 %
```
Inside a heavy truck cab while the inline-six diesel works hard at high revs in a low gear, fast busy engine drone through the floor and firewall, buzzing cab panels, turbo whine, held perfectly steady, no road noise, no pitch change, seamless loop, no music, no voices
```
**R1d. `ENG_CAB_OFF_HIGH`** — kabina, bez obciążenia · Pętla · 6 s · 80 %
```
Inside a heavy truck cab, diesel engine spinning fast with the throttle closed, light high-pitched drone through the floor, faint mechanical whir, held perfectly steady, no road noise, no pitch change, seamless loop, no music, no voices
```

## R2. Wolny bieg jałowy (zastępuje 600 z partii A)

Powód: zmierzone 717–1004 obr/min zamiast 600. Teraz komórka 600 to obniżenie ×0,68 (ton i szum ciemnieją).

**R2a. `ENG_EXT_IDLE_SLOW`** — zewnątrz · Pętla · 8 s · 80 %
```
Big heavy truck diesel engine at a very slow low idle, recorded outside, deep lazy lumpy rhythm with each combustion thump clearly separate, soft exhaust puffs, faint injector tick, steady, no revving, no pitch change, seamless loop, no music, no voices
```
**R2b. `ENG_CAB_IDLE_SLOW`** — kabina · Pętla · 8 s · 80 %
```
Inside a parked heavy truck cab with the diesel engine at a very slow low idle, deep slow throb felt through the seat, each combustion thump separate and muffled, very faint ticking, steady, no road noise, no revving, no pitch change, seamless loop, no music, no voices
```

## R3. Gwizd turbo jako pętla (zamiast `TURBO_SPOOL`)

Powód: `TURBO_SPOOL` 1–4 nie ma rosnącej linii tonalnej. Jednorazowego dźwięku nie da się zgrać z doładowaniem z fizyki. Stały gwizd gra podnosi lub obniża sama, w zależności od ciśnienia doładowania.

**R3. `TURBO_WHISTLE_LOOP`** · Pętla · 5 s · 80 %
```
Steady high-pitched whistle of a heavy truck turbocharger at constant boost, close to the engine, clean continuous tone with soft air rush, no engine rumble, no pitch change, seamless loop, no music, no voices
```

## R4. Przejazd przez obroty (opcjonalnie, do wycinania pętli)

Powód: jedno nagranie z wolnym, ciągłym wzrostem obrotów pozwala wyciąć pętle dla dowolnych obrotów z tej samej „maszyny”. Barwa jest wtedy spójna między komórkami, a dziś każda komórka pochodzi z innego nagrania. Pętla **Wyłączona**, czas: **maksimum suwaka** (`UNVERIFIED` ile pozwala v3; ≥ 20 s), wpływ 80 %.

**R4a. `ENG_EXT_ON_SWEEP`**
```
Heavy truck inline-six turbo diesel recorded outside by the exhaust stack, accelerating slowly and continuously from low idle all the way to maximum revs in one gear under heavy load, smooth steady rise in engine speed with no gear change, no pauses, no music, no voices
```
**R4b. `ENG_CAB_ON_SWEEP`**
```
Inside a heavy truck cab, the inline-six diesel accelerates slowly and continuously from low idle to maximum revs in one gear under heavy load, smooth steady rise of the engine drone through the floor, no gear change, no pauses, no road noise, no music, no voices
```

## R5. Wyłączenie silnika w kabinie (brakuje)

Powód: dziś `ENG_STOP_CAB` to `ENG_STOP_EXT (3)` przepuszczony przez filtr kabiny (ADR 0017). Wiarygodne, ale nagranie z kabiny będzie lepsze. Pętla **Wyłączona**, 3 s, 60 %.

**R5. `ENG_STOP_CAB`**
```
Inside a heavy truck cab, the idling diesel engine is switched off, the cab shudders once and the engine runs down to silence, a soft dashboard click at the end, no music, no voices
```

## Co z nimi zrobię

`uv run python tools/audio/el_analyze.py` → wybór → `el_prepare.py`. R1/R2 zastąpią źródła komórek 600, 1800 i 2100, R3 zastąpi gwizd z syntezy, R4 (jeśli trzyma ciągły wzrost) da spójną siatkę z jednego nagrania. Ocena na telefonie należy do Ciebie: w ustawieniach **DŹWIĘK → Silnik: synteza / ElevenLabs**.
