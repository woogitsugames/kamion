# Pomiary na urządzeniach — 2026-11-09 (pierwsze z telefonu)

Frame cap = 30 FPS (profil docelowy 30). Wszystkie przebiegi: thermal status 0, bez wyjątków w logcat (install run).

| Urządzenie | Scena | Profil | Klatki / czas | mean FPS | p50 / p95 / p99 / max [ms] | PSS | Bateria |
|---|---|---|---|---|---|---|---|
| A16 (Helio G99) | Boot | Medium | 2036 / 67,8 s | 30,01 | 33,33 / 33,47 / 33,57 / 33,66 | ~289 MB | 27,4 °C |
| A16 | DrivingLab, ciągnik solo, autopilot R50 40 km/h | Medium | 2462 / 82 s | 30,01 | 33,33 / 33,46 / 33,53 / 33,66 | — | — |
| A16 | DrivingLab, zestaw 40 t, R50 40 km/h | Medium | 2457 / 81,9 s | 30,01 | 33,33 / 33,45 / 33,54 / 33,66 | 333 MB | 26,7 °C |
| A16 | WorldC (świat v1), trasa, 50 km/h | Medium | 2580 / 86 s | 29,99 | 33,33 / 33,45 / 33,56 / 50,04 | **790 MB** | 26,8 °C |
| S24+ (Exynos 2400) | Boot | High | (brak licznika klatek w przebiegu) | — | — | 498 MB | 30,3 °C |
| S24+ | DrivingLab, 40 t | High | 2441 / 81,4 s | 29,98 | 33,36 / 33,77 / 34,58 / 42,61 | 535 MB | 30,9 °C |
| S24+ | WorldC, trasa | High | 2632 / 87,8 s | 29,98 | 33,36 / 33,56 / 33,98 / 36,51 | 767 MB | 31,9 °C |

APK: A16 — `kamion-0.1.0-5e1bb89e4c-dirty`; S24+ — `kamion-0.1.0-ccad5bedb7-dirty` (nowszy build agenta Unity).

## Wnioski
- Cel 30 FPS trzymany na obu telefonach z zapasem w p99; zapas (headroom) nieznany, bo klatki są limitowane — następny pomiar bez limitu / 60 FPS.
- **Pamięć WorldC na A16: 790 MB** — za dużo dla telefonu 4 GB; trwa odchudzanie (cel świata Low ≤ ~150 MB siatek).
- Problemy widoczne na zrzutach: w WorldC naczepa zostaje odpięta daleko za ciągnikiem (spawn), na S24+ autopilot stanął (0 km/h, D4), tekst diagnostyczny zasłania widok, lusterka-wstawki działają.

![A16 WorldC](2026-11-09_A16_WorldC.jpg)
![S24+ WorldC](2026-11-09_S24_WorldC.jpg)
