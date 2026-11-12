# ElevenLabs — przegenerowania 03 (opony: szuranie w ciasnym skręcie i pisk)

Wersja s14, 2026-11-12, lider. Format jak `ELEVENLABS-REGEN-02.md`. Model **v3**, plan Pro / ElevenCreative.

## Dlaczego

Właściciel (s14): pisk opon przy mocnym skręcie brzmi źle. Diagnoza: ten dźwięk **nigdy nie był podmieniony**. To nadal synteza `tools/audio/sfx_layers.py:123` `tyre_squeal_loop`, czyli ton ~930 Hz z harmonicznymi, przez co brzmi jak gwizdek, a nie jak guma. W REGEN-01 i REGEN-02 nie było żadnej pozycji pisku ani szurania opon.

Co słychać w prawdziwym ciągniku z naczepą w ciasnym skręcie przy małej prędkości: **szuranie i skrzypienie gumy** (scrub). Tandem i tridem naczepy ciągną opony bokiem po asfalcie, słychać niskie tarcie i rwane „skrzypnięcia”, a nie wysoki gwizd. Klasyczny pisk to dopiero poślizg przy większej prędkości. Potrzebujemy obu nagrań.

## Koszt

Ok. 3,3 kredytu za sekundę (`UNVERIFIED`, wyliczone z salda w REGEN-01). Lista: 4 pozycje × 4 warianty × 10 s = 160 s, czyli ok. **530 kredytów**.

## Ustawienia
| Ustawienie | Wartość |
|---|---|
| Model | **v3** |
| Pętla (∞) | **Włączone** |
| Czas | **10 s** |
| Wpływ podpowiedzi | **80 %** |
| Auto-poprawa (różdżka) | **Wyłączone** |
| Ile wariantów | **4** |

Zapis: `art-source/audio/elevenlabs/<ID> (n).wav`, numeracja od (1).

## T1. `TYRE_SCRUB_TIGHT_TURN` (1)–(4) · 10 s, pętla
```
Close outside recording of a heavy articulated truck making a very tight slow turn on dry asphalt at walking speed: the trailer's multi-axle tyres are dragged sideways, producing a continuous low rubbery scrubbing and groaning with irregular creaks and short chirps, gravel crunch faintly under the rubber, no engine roar in the foreground, no squeal whistle, no music, no voices
```

## T2. `TYRE_SCRUB_TIGHT_TURN_CAB` (1)–(4) · 10 s, pętla
```
Inside the closed cab of a heavy truck during a very tight slow turn, heard through the floor and the rear wall: muffled low rubber scrubbing and groaning from the trailer tyres dragged sideways on asphalt, irregular dull creaks, quiet diesel idle in the background, no squeal whistle, no music, no voices
```

## T3. `TYRE_SQUEAL_HARD` (1)–(4) · 10 s, pętla
```
Outside recording of a heavy truck's large tyres squealing on dry asphalt while cornering too fast: a rough, low-pitched, wavering rubber squeal with grit and texture, not a thin whistle, varying in intensity, tyre roar underneath, no engine in the foreground, no music, no voices
```

## T4. `TYRE_SQUEAL_HARD_CAB` (1)–(4) · 10 s, pętla
```
Inside the closed cab of a heavy truck cornering too fast: muffled low rubber squeal from the tyres heard through the cab, rough and wavering, tyre and road roar underneath, steady diesel in the background, no music, no voices
```

## Po wygenerowaniu

Wrzuć pliki do `art-source/audio/elevenlabs/` i napisz „REGEN-03 gotowe”. Agent audio wybierze najlepsze warianty (`el_fx.py`), podłączy szuranie (mała prędkość, duży kąt skrętu, naczepa) i pisk (poślizg powyżej progu) w `TruckAudioController` i zrobi odsłuch A/B.
