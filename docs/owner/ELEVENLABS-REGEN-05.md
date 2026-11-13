# ElevenLabs — przegenerowania 05 (retarder, przepustnica hamulca silnikowego, fazy AMT, osuszacz)

Wersja s17, 2026-11-13, agent audio (ADR 0176). Format jak `ELEVENLABS-REGEN-04.md`. Model **v3**, plan Pro.
**Opcjonalne.** Warstwy są już zsyntezowane (`tools/audio/synth0176.py`) i wpięte w grę. Ta partia daje nagrania do
porównania A/B z syntezą; nic nie zostało wysłane — generuje właściciel.

## Dlaczego
Trzy poszukiwania (G9, P5, M55) nie znalazły wolnych nagrań tych zjawisk. Synteza ma model fizyczny i sterowanie
telemetrią, ale jej barwa to `WORKING_VALUE`. Nagranie z generatora może dać bardziej „prawdziwą” fakturę (zwłaszcza
retarder i skrzynię). Z nagrań bierzemy tylko fragmenty, które da się sterować tak samo (pętla retardera o stałej prędkości,
pojedyncze zdarzenia).

## Koszt
Ok. 3,3 kredytu za sekundę (`UNVERIFIED`, z REGEN-01). 6 pozycji × 4 warianty, razem 4×(10+10+4+4+4+6) = 152 s, czyli ok.
**500 kredytów**.

## Ustawienia
| Ustawienie | Wartość |
|---|---|
| Model | **v3** |
| Pętla (∞) | **Włączone** tylko dla R1, R2; reszta **wyłączone** |
| Czas | jak przy pozycji |
| Wpływ podpowiedzi | **80 %** |
| Auto-poprawa (różdżka) | **Wyłączone** |
| Ile wariantów | **4** |

Zapis: `art-source/audio/elevenlabs/<ID> (n).wav`, numeracja od (1).

## R1. `RETARDER_STEADY_EXT` (1)–(4) · 10 s · pętla
```
Underneath a heavy truck descending a long highway hill at constant speed with the hydraulic driveline retarder fully applied: a steady smooth mechanical whine from the transmission tunnel, a turbulent rushing of oil inside a spinning bladed wheel, constant pitch, constant speed, no engine revving, no gear change, no brakes squealing, no air hiss, no wind gusts, no music, no voices
```

## R2. `RETARDER_STEADY_CAB` (1)–(4) · 10 s · pętla
```
Inside the closed cab of a heavy truck descending a long hill at constant speed with the hydraulic driveline retarder fully applied: a soft steady whine and muffled oil rush coming through the floor behind the seats, constant pitch, quiet engine hum underneath, no gear change, no air hiss, no music, no voices
```

## R3. `EXHAUST_BRAKE_ON_OFF_EXT` (1)–(4) · 4 s
```
Close to the exhaust of a large diesel truck coasting at medium revs: a small valve click and a metallic flap snapping shut inside the exhaust pipe, the exhaust note turns deep and choked for two seconds, then the flap opens with a short soft whoosh of released exhaust pressure, single event, no compression-release engine brake rattle, no music, no voices
```

## R4. `AMT_UPSHIFT_EXT` (1)–(4) · 4 s
```
Next to the gearbox of a heavy truck with an automated manual transmission doing one upshift under load: the engine pulls, torque drops, a short pneumatic valve click and small puff of air, a solid metallic clunk of a dog clutch engaging inside the gearbox housing with a faint rattle, the engine pulls again at lower revs, single shift, no music, no voices
```

## R5. `AMT_UPSHIFT_CAB` (1)–(4) · 4 s
```
Inside the closed cab of a heavy truck with an automated manual transmission, one upshift while accelerating: engine drone dips, a soft pneumatic click and muffled clunk from under the floor, the drone returns at lower pitch, single shift, no music, no voices
```

## R6. `AIR_DRYER_PURGE` (1)–(4) · 6 s
```
Beside a parked heavy truck with the engine idling: the air compressor stops and the air dryer purge valve suddenly opens under the chassis, a loud sharp burst of compressed air through a small silencer that decays over about one second, followed by a faint fading hiss, single event, no brake release, no horn, no music, no voices
```

## Po wygenerowaniu
Agent audio: analiza jak `el_regen03.py` (szew pętli, brak tonów obcych, okno), dla R1/R2 pomiar częstotliwości linii przejścia
łopatek (pitch odniesienia pętli = obroty wału), dla R3–R6 cięcie zdarzeń i normalizacja LUFS jak `el_fx.py`; A/B z syntezą
0176 (`tools/audio/synth0176_ab.py`). Rejestr w `docs/LICENSES.md` jak partie REGEN-03/04.
