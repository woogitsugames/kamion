# ElevenLabs — przegenerowania 04 (silnik w kabinie bez obciążenia: hamowanie silnikiem / toczenie na biegu)

Wersja s15, 2026-11-12, agent audio (ADR 0148). Format jak `ELEVENLABS-REGEN-03.md`. Model **v3**, plan Pro.
**Opcjonalne.** Główna przyczyna „dziwnego jałowego” (sprężarka powietrza głośniejsza od silnika) jest naprawiona w kodzie
bez nowych nagrań. Ta partia poprawia drugą, słabszą rzecz w zestawie ElevenLabs.

## Dlaczego

W zestawie ElevenLabs komórki **kabina / bez obciążenia 1200 i 1500 obr/min** (źródła `ENG_CAB_OFF_1800 (3)`, przestrojone)
mają słabą linię zapłonu: 7,5–7,7 dB nad tłem przy obr/min / 20. Dla porównania: zewnątrz bez obciążenia 21–25 dB, kabina
pod obciążeniem 11–19 dB, synteza 36–37 dB (`tools/audio/idle_ab.py`, pomiar w ADR 0148). Po puszczeniu gazu przy
1000–1500 obr/min (toczenie na biegu, hamowanie silnikiem) silnik w kabinie brzmi więc jak szum bez wyraźnego tonu.
Wnioski z REGEN-01/02: model nie trzyma stałych obrotów z liczby w prompcie, ale **jednorazowy przejazd przez obroty działa**,
dlatego prosimy o zjazd obrotów (spadek), z którego wytniemy komórki 900–1500 jak w `el_sweepcut.py`.

## Koszt

Ok. 3,3 kredytu za sekundę (`UNVERIFIED`, z REGEN-01). 2 pozycje × 4 warianty × 12 s = 96 s, czyli ok. **320 kredytów**.

## Ustawienia
| Ustawienie | Wartość |
|---|---|
| Model | **v3** |
| Pętla (∞) | **Wyłączone** (to przejazd, nie pętla) |
| Czas | **12 s** |
| Wpływ podpowiedzi | **80 %** |
| Auto-poprawa (różdżka) | **Wyłączone** |
| Ile wariantów | **4** |

Zapis: `art-source/audio/elevenlabs/<ID> (n).wav`, numeracja od (1).

## C1. `ENG_CAB_OVERRUN_SWEEP` (1)–(4) · 12 s
```
Inside the closed cab of a heavy truck rolling down a gentle slope in a high gear with the driver's foot completely off the accelerator: the inline-six diesel is driven by the wheels with no fuel, engine speed falls slowly and smoothly from medium revs to just above idle over the whole clip, a clear steady low engine hum with distinct firing pulses heard through the floor, soft and light, no acceleration, no gear change, no exhaust brake, no road noise, no music, no voices
```

## C2. `ENG_CAB_IDLE_STEADY` (1)–(4) · 12 s
```
Inside the closed cab of a stationary heavy truck, the inline-six diesel idling smoothly and evenly, a clear low regular throb from the engine through the floor and seat, every firing pulse even, faint injector ticking, no air compressor, no air hiss, no revving, no road noise, no music, no voices
```

## Po wygenerowaniu
Agent audio: `el_regen01.py`-podobna analiza (linia, monotoniczność spadku, okres YIN), cięcie jak `el_sweepcut.py`
(`SWEEP_ROWS` dla kab./bez obciążenia), `el_verify.py`, odsłuch A/B dla właściciela.
