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


## Świat C v2 (rendering-perf, ADR 0012) — APK `kamion-0.1.0-1036492bdd` (Low/Medium, 122 MB) i `…-high` (228 MB, S24+)
Trasa startowa z autopilotem, 50 km/h, zestaw 40 t (domyślny dla `autopilot=route`), 90 s, telefony odblokowane
(`isKeyguardShowing=false` przed każdym przebiegiem). Frame cap 30 FPS, chyba że „bez limitu” (`-Uncapped`, cel 240 FPS →
ogranicza tylko odświeżanie panelu).

| Urządzenie | Scena / profil | Limit | Klatki / czas | mean FPS | p50 / p95 / p99 / max [ms] | PSS | Bateria / thermal |
|---|---|---|---|---|---|---|---|
| A16 | WorldC v2 / Low | 30 | 2468 / 82,3 s | 30,0 | 33,33 / 33,48 / 33,62 / 50,10 | **511 MB** (v1: 790) | 27,6 °C / 0 |
| A16 | WorldC v2 / Medium | 30 | 2476 / 82,6 s | 29,98 | 33,33 / 33,50 / 33,65 / 50,28 | **559 MB** | 27,6 °C / 0 |
| A16 | WorldC v2 / Medium | bez limitu | 3146 / 82,8 s | 38,0 | 33,27 / 33,44 / 33,55 / 50,14 | 560 MB | 27,7 °C / 0 |
| S24+ | WorldC_High / High | 30 | 2524 / 84,2 s | 29,98 | 33,36 / 33,57 / 34,02 / 37,82 | 966 MB | 35,7 °C / 0 |
| S24+ | WorldC_High / High | bez limitu | 5078 / 82,1 s | 61,8 | 16,68 / 25,07 / 33,39 / 50,08 | 976 MB | 39,8 °C / **2** |

Zapas (headroom): A16 Medium bez limitu ma 43 % klatek po 16,7 ms i 56 % po 33,3 ms (Unity na A16 wybiera 60 Hz, klatki
wyrównane do VSync) → realny koszt klatki ≈ 17–25 ms, czyli ~25–45 % zapasu przy celu 30 FPS. S24+ High utrzymuje ~60 FPS
(p50 16,7 ms), ale po 80 s stan termiczny 2 — High/60 to nie jest profil na długą jazdę bez strojenia.
Zrzuty z kamer kontrolnych w natywnej rozdzielczości (A16 2340×1080 Medium, S24+ 3120×1440 High, HUD ukryty, launch arg
`qacam`): `docs/reports/device/2026-11-09_v2_*`.

### Kamery kontrolne na telefonach (statyczne, 18–20 s, limit 30 FPS)
| Kamera | A16 Medium: mean FPS / p50 [ms] | S24+ High | Zrzut A16 | Zrzut S24+ |
|---|---|---|---|---|
| Andersa (kierowca) | 29,3 / 33,3 (p95 49,9) | 30,0 / 33,4 | [A16](2026-11-09_v2_A16_Medium_driver-andersa-to-putry.jpg) | [S24+](2026-11-09_v2_S24_High_driver-andersa-to-putry.jpg) |
| Rondo Putry z 40 m (widok poglądowy, nie z jazdy) | **22,9 / 49,9** | 30,0 / 33,4 | [A16](2026-11-09_v2_A16_Medium_putry-above.jpg) | [S24+](2026-11-09_v2_S24_High_putry-above.jpg) |
| Brama Kwadrat Parku | 30,0 / 33,3 | 30,0 / 33,4 | [A16](2026-11-09_v2_A16_Medium_kwadrat-park-gate.jpg) | [S24+](2026-11-09_v2_S24_High_kwadrat-park-gate.jpg) |
| Rampy | 30,0 / 33,3 | 30,0 / 33,4 | [A16](2026-11-09_v2_A16_Medium_stretch-05-docks.jpg) | [S24+](2026-11-09_v2_S24_High_stretch-05-docks.jpg) |
| **Las przy DK8** | **10,3 / 100** | **14,3 / 66,7** | [A16](2026-11-09_v2_A16_Medium_dk8-dk19-exit.jpg) | [S24+](2026-11-09_v2_S24_High_dk8-dk19-exit.jpg) |

**Las przy DK8 to wąskie gardło** (nakładające się karty liści i impostory z alpha-testem → overdraw na GPU kafelkowym,
plus cienie kart LOD1). Trasa 90 s go nie obejmowała (kończy się ok. 1,2 km). Poprawka w `WorldInstances`: przerzedzanie
drzew z odległością (co 2. od 90 m × LOD bias, co 4. od 225 m), limit impostorów 600 m, cienie tylko z LOD0 na Low/Medium.
Pomiar po poprawce: niżej.

### Las przy DK8 po poprawkach (APK `a5c0cfa`, kamera kontrolna `dk8-dk19-exit`, 18 s)
| Wersja | A16 Low | A16 Medium | S24+ High |
|---|---|---|---|
| przed (v2, LOD drzew skalowany LOD bias) | — | 10,3 FPS | 14,3 FPS |
| + przerzedzanie z odległością, impostory ≤ 600 m, cienie tylko LOD0 | **30,0** | 13,6 | 15,3 |
| + karty liści LOD0/LOD1 nie dalej niż 10/30 m na każdym profilu | — | **16,7** | **26,2** (telefon gorący, thermal 2) |

Pełna trasa A16 Medium 173 s (do wjazdu w las): 29,95 FPS, p95 33,48 ms.
**Wniosek:** na A16 las przy DK8 trzyma 30 FPS tylko na Low. Medium jest tam ograniczony przez GPU (MSAA 4×,
HDR + post, 2 kaskady cieni na alpha-testowanych liściach). Dalsze kroki: HLOD lasu (gotowe „ściany” lasu zamiast
pojedynczych impostorów), alpha-to-coverage tylko na High, Medium na A16 z MSAA 2× w lesie albo Low jako domyślny
profil A16 — do decyzji po pomiarze GPU (Arm Performance Studio).

## r3 — shader liści, MSAA 2× na Medium, auto-Low na A16, szarpnięcie na s≈604 m (rendering-perf, wieczór)
APK `kamion-0.1.0-4eb5901ded-dirty` (treść Low/Medium) i `…-dirty-high` (S24+); kod w commitach `4eb5901`…`2efb0fb`.
Przed każdym przebiegiem `isKeyguardShowing=false`. Wszystkie przebiegi z limitem 30 FPS. GPU/CPU = p50 z `FrameTimingManager` [ms].
Rozgrzewka 15 s. Przebiegi statyczne trwają 20 s; trasa 85 s (kończy się na s ≈ 900 m).

**Zweryfikowane**
- **Auto-tier:** przy pierwszym uruchomieniu A16 loguje `[BOOT] auto tier Low: Galaxy A16 (Helio G99)`, a S24+ `auto tier High`.
- **Kolizje liczone w runtime** (`WorldCollisionCooker`, równoległe `Physics.BakeMesh` w trakcie ładowania sceny):
  - 265 siatek na jedno ładowanie: A16 250–259 ms, S24+ 71–78 ms.
  - Liczenie kończy się przed pierwszą klatką jazdy, więc na trasie nie ma skoków klatki (max na A16 50 ms = jeden pominięty VSync).

### Las DK8 — ablacja GPU na telefonie (A16, kamera `dk8-dk19-exit`)
Przed zmianą (liście URP Lit): Medium 16,4 FPS, GPU 61,3 ms. Bez drzew: 18,4 ms. Skala renderu 0,6: 37,7 ms.

To pokazuje, że koszt to praca fragmentów na kartach liści (pełna tabela w ADR 0013).

| Wariant | A16 Low | A16 Medium |
|---|---|---|
| URP Lit, MSAA wg profilu (Low 2×, Medium 4×) | 28,1 FPS · GPU 35,5 | 16,4 FPS · GPU 61,3 |
| URP Lit, Medium MSAA 2× | — | 19,8 FPS · GPU 50,6 |
| **Kamion/Vegetation** (przebieg głębi + przebieg koloru ZWrite Off), MSAA 4× | — | 15,4 FPS · GPU 64,7 |
| **Kamion/Vegetation + Medium MSAA 2× (nowy domyślny)** | **30,0 FPS · GPU 26,1** (p95 33,4 ms) | **27,0 FPS · GPU 36,9** (p95 50,1 ms) |
| to samo, bez alpha-to-coverage | — | 28,4 FPS · GPU 35,1 |

**Decyzja (ADR 0013)**
- Low i Medium używają `Kamion/Vegetation`.
- Medium ma MSAA 2×, bo 4× kosztuje w lesie na G57 +28 ms.
- A16 domyślnie zostaje na Low.

**Wynik**
- Medium w lesie: 27 FPS. To spełnia warunek briefu ≥ 25 FPS, ale nie daje 30.
- HLOD ścian lasu odkładam, bo Low już trzyma 30.

**Na klatkach**
- Sosny są ciemniejsze niż z Lit, który refleksem sondy nakładał na impostory niebiesko-szary połysk.
- Wygląd wymaga jeszcze oceny visual-critic.

| Przed (Medium, Lit, MSAA 4×) | Po (Medium, Vegetation, 2×) | Po (Low) |
|---|---|---|
| ![](2026-11-09_r3_A16_Medium_dk8_before.jpg) | ![](2026-11-09_r3_A16_Medium_dk8_vegetation.jpg) | ![](2026-11-09_r3_A16_Low_dk8_vegetation.jpg) |

### Trasa startowa, zestaw 40 t, 50 km/h (`-Autopilot route -Trailer 40 -Extra telemetry=1`)
| Urządzenie / profil | klatki / s | mean FPS | p50 / p95 / p99 / max [ms] | GPU / CPU p50 | PSS | bateria / thermal |
|---|---|---|---|---|---|---|
| A16 Low | 2412 / 80,5 | 29,98 | 33,33 / 33,50 / 33,67 / 50,17 | 16,3 / 19,2 | 534 MB | 30,0 °C / 0 |
| A16 Medium | 2430 / 81,1 | 29,97 | 33,33 / 33,52 / 33,71 / 50,17 | 23,2 / 21,6 | 559 MB | 30,1 °C / 0 |
| **A16 Low, 30 min, las DK8 (najgorszy widok, statyczny)** | 53478 / 1783 | 29,99 | 33,33 / 33,46 / 33,55 / 50,19 (7 klatek > 50 ms) | 26,5 (p95 27,9) / 19,1 | 514 MB | **30,9 °C / 0** po 30 min |

Klatka z kabiny z lusterkami (A16 Low, natywne 2340×1080): ![](2026-11-09_r3_A16_Low_route.jpg). Oba lusterka i wstawki są czytelne.

### Szarpnięcie na s≈604 m — przyczyna (telemetria z telefonu, `tools/telemetry/route_jolt.py`)
Zmiana prędkości nadwozia |dv| na krok: mediana 0,0055 m/s, p99 0,075 m/s. Szczyty:
- A16 Low: 0,586 m/s na s = 605,8 m.
- A16 Medium: 0,711 m/s na s = 605,6 m.

Szczyt wypada w tym samym miejscu w każdym przebiegu. Test PlayMode w edytorze widzi tylko 0,249 m/s (próg 0,8):
autopilot próbkuje wejście w `Update`, więc przy 30 FPS tor jest minimalnie inny, i na telefonie w krawężnik wchodzi też lewe przednie koło.

Przebieg zdarzenia:
1. **s = 598,3 m, (343,9; −589,1):** lewe przednie koło wjeżdża na beton (surface 2 = krawężnik).
   - Ugięcie zawieszenia: 0,060 → 0,108 m w jednym kroku.
   - Fz: 35 → 239 kN w 0,02 s.
2. **s ≈ 600–604 m:** przednia oś odrywa się od ziemi.
   - Oba przednie koła są w pełni wysunięte (−0,09 m), 0 kN przez ~0,4 s.
   - Pochylenie dochodzi do +8°.
3. **s = 604,4 m:** na ten sam krawężnik wjeżdża lewe tylne koło (rear_R wisi).
4. **s = 605,7 m:** przednia oś ląduje (Fz 140 kN). To jest szarpnięcie.

Ciągnik jest wtedy na linii trasy (odchyłka ≈ 0). Krawężnik stoi ~1,3 m na lewo od osi.
Przyczyna to schodek Z przy rozwidleniu jezdni: węzeł 4391371827, `tertiary_link` 2 pasy → `trunk_link` 1 pas obok Andersa.

**Naprawa**
- **Świat (do scalenia):** commit świata v3 `806e89d` „continuous kerb at carriageway splits” usuwa dokładnie ten schodek.
  Jest na gałęzi `worktree-agent-a8cc4186e1bfe4593` i nie został jeszcze scalony z main. Świata tutaj nie regenerowałem.
  - Po scaleniu sprawdzić tą samą procedurą (trasa + `telemetry=1` + `route_jolt.py`).
  - Cel: |dv| < 0,2 m/s w okolicy s = 598–606 m.
- **Fizyka (vehicle-physics):** koło promieniowe nie ma obwiedni opony. Schodek 5–14 cm daje 7× szczyt Fz i oderwanie osi.
  - Propozycja: filtr wysokości kontaktu (obwiednia na długości styku opony) albo kilka promieni na koło.
  - Dodać do `WorldCRouteTests` asercję na czas bez kontaktu przedniej osi.
  - Próg 0,8 m/s w tym teście nie wyłapał uderzenia 0,7 m/s.

### S24+ (High) — przebiegi nieważne
- Telefon przed pomiarem: 43,9 °C, thermal status 2 (nagrzany wcześniejszymi przebiegami). Wyniki tylko do wiadomości:
  - High, Lit: 14,8 FPS, GPU 68,1 ms.
  - `rq_vegshader=1`: 13,1 FPS, 72,2 ms.
  - `rq_vegshader=1 rq_msaa=2`: 21,7 FPS, 42,8 ms.
- Potem wysłałem `KEYCODE_SLEEP`, żeby go schłodzić. **To zablokowało S24+ PIN-em i dalsze pomiary High nie były możliwe.**
  To mój błąd: skrypty nie mogą usypiać ekranu.
- Do ponownego pomiaru, gdy telefon będzie chłodny i odblokowany: las DK8 Lit vs Vegetation, MSAA 4× vs 2×, trasa.

## r4 — świat v3 po regeneracji (blokada trasy na s = 571 m), S24+ High: las DK8 (build-qa, wieczór)
APK `kamion-0.1.0-1b4edcfd4b-dirty-high` (SHA256 `bd8cbafe447eb94d15775c48dcf545f42cba5d4248dc6df26ddc43c16f9a24a9`, 220,6 MB, build 67 s).
Świat zregenerowany z main (`build_world.py` + `import-region.ps1 -Build`, 64 chunki, Low 90,6 MB / High 217,2 MB) i zaimportowany.
Przed każdym przebiegiem `isKeyguardShowing=false` i bateria < 36 °C. Limit 30 FPS. Ekranu nie usypiałem.

### 1. Szarpnięcie na s ≈ 604 m — NIE DA SIĘ ZMIERZYĆ: nowa przeszkoda na s = 570,6 m
A16 Low, trasa 40 t / 50 km/h, `telemetry=1`: `artifacts/device/RFGL34SJYDZ/20261109-184909/telemetry/drive-20261109-184915.csv`.

| | r3 (stary świat) | r4 (świat v3 po regeneracji) |
|---|---|---|
| zasięg trasy | 987 m | **571 m** (zestaw staje) |
| max \|dv\| na krok | 0,586 m/s przy s = 605,8 m | **9,77 m/s przy s = 570,6 m** (43 → 16 km/h w jednym kroku) |
| \|dv\| na s ≈ 598–606 m | 0,586 | nieosiągalne |

- Uskok krawężnika z r3 nie jest już mierzalny, bo ciągnik uderza wcześniej: kolizja bryły (nie koła; koła stoją na asfalcie, surface 0).
- PlayMode `WorldCRouteTests` (Solo i zestaw) padają na tym samym miejscu: `progress 572/2401 m`, `max |dv| 13,45 m/s at s=571`.
  - Kontakt: `Chunk_5_6/col_grass` przy (363,7; 11,37; −598,8) o `Cab`, impuls 118 kN·s.
- Geometria z `chunk_5_6.glb`: droga jest na U = 140,7, a 1,8 m od punktu uderzenia stoi `collision_grass` do U ≈ 142,9 (+2,2 m).
  Za nim jest wyżej położona `collision_asphalt` z barierą stalową na 143,3–143,8. To skarpa lub rampa wchodząca w pas ruchu.
- Zmiana vs r3: regeneracja świata. Zmiana wymiarów pojazdu (`c3a9b5a`) jest drobna, więc kolizji nie tłumaczy.
- Do world-builder: skarpa/rampa przy (369; −600), chunk 5_6. Po poprawce powtórzyć pomiar (procedura bez zmian).
- Nie zmieniałem kodu ani świata w trakcie pomiaru.

### 2. S24+ (High), las DK8, kamera `dk8-dk19-exit` — ważne (bateria 32–36 °C, thermal 0, okno 23–27 s po 30 s rozgrzewki)
| Wariant | FPS (mean) | GPU p50 / p95 [ms] | CPU p50 | PSS | bateria po |
|---|---|---|---|---|---|
| Lit (URP), MSAA 4× (obecny High) | 25,7 | 38,7 / 39,8 | 17,4 | 996 MB | 37,8 °C |
| Kamion/Vegetation, MSAA 4× | 30,0 | 31,3 / 32,5 | 17,5 | 990 MB | 37,9 °C |
| **Kamion/Vegetation, MSAA 2×** | 30,0 | **18,0** / 19,9 | 17,2 | 919 MB | 37,3 °C |
| **Lit, MSAA 2×** | 30,0 | **21,6** / 24,2 | 16,6 | 914 MB | 38,0 °C |

- Wartości r3 (68 ms Lit, 72 ms Vegetation) były zawyżone przez przegrzanie (44 °C).
- Na S24+ 4× kosztuje +17–18 ms względem 2× niezależnie od shadera liści (Lit 38,7 vs 21,6; Vegetation 31,3 vs 18,0). To ten sam wzorzec co na Mali-G57.
- Vegetation oszczędza dodatkowo 3,6 ms przy 2× (18,0 vs 21,6) i 7,4 ms przy 4×.
- Przy 4× High nie trzyma 30 FPS w lesie (25,7 FPS, p95 klatki 66,8 ms). Przy 2× trzyma z zapasem 12 ms (Lit).
- Przebiegi A–D: `artifacts/device/RZCX60VE8ZY/20261109-185818`, `-190233`, `-190638`, `-190952`. Zrzutów nie oceniałem wizualnie.

### 3. S24+ trasa 40 t, 90 s — NIE WYKONANA
- Trasa i tak urywa się na s = 571 m (pkt 1).
- Od ok. 19:10 aplikacja `com.woogitsugames.kamion` na S24+ jest uruchamiana przez innego agenta. Bateria rosła 36 → 43,6 °C przy moim wyłączonym przebiegu, więc warunek < 36 °C nie był spełniony.
- Nie startowałem w trakcie cudzego przebiegu. Nie zmieniałem stanu ekranu.

### Testy
- EditMode: 22/22 zielone.
- PlayMode: 25 zielonych, 3 pominięte, **2 czerwone** (`WorldCRouteTests`, Solo i zestaw: skarpa na s = 571 m, pkt 1). Wcześniej zielone.
- Data/Regions/…/world_manifest.json, streetscape_qa.json i art-source/world/props/props_meta.json zmieniły się po regeneracji (liczby trójkątów ±2, przeliczone hashe). Nie commituję ich, dopóki świat nie jest poprawiony.

## r5 — D23 v2 (ADR 0016), forest HLOD (ADR 0015), High MSAA 2×, TRAKT r4 + interior LOD0 (rendering-perf, 21:14–21:57)
APK `kamion-0.1.0-0908719f0c` (Low/Medium content, 134,0 MB) on the A16, `…-99ba0320df-high` (247,5 MB) on the S24+. Static QA cameras, 30 FPS cap,
window after 20 s (A16) / 25 s (S24+) warm-up. Before every run: `isKeyguardShowing=false`, battery < 36 °C (one S24+ repeat started at 37 °C, marked).
Screen never put to sleep by the scripts. Frames (native 2340×1080): `docs/reports/visual/truck-A7/device-r2/`.

| Device / view | FPS | frame p50 / p95 / p99 / max [ms] | GPU p50 / p95 | CPU p50 | PSS MB | battery °C / thermal |
|---|---|---|---|---|---|---|
| A16 Low cab-dash overcast / low sun / dusk | 30,1 / 30,1 / 30,0 | 33,3 / 33,5 / 33,6 / ≤ 50 | 16,1–16,2 / ≤ 18,0 | 18,0–18,6 | 610–613 | 29,4 / 0 |
| A16 Low street (Andersa) / truck-34 | 30,1 / 30,0 | 33,3 / 33,5 / 33,6 | 16,2 / 16,0 | 18,7 / 17,9 | 610 / 615 | 29,4 / 0 |
| A16 Low DK8 forest, HLOD on / `rq_hlod=0` | 30,1 / 30,1 | 33,3 / 33,4 / 33,5 | **26,7** / 27,8 | 15,8 / 17,9 | 610 / 612 | 29,3 / 0 |
| **A16 Low DK8 forest, 30 min** (53 016 frames) | 29,98 | 33,3 / 33,5 / 33,6 / 100 (22 frames > 50 ms) | 27,4 / 29,0 | 18,8 | 575 | **30,5 / 0** after 30 min |
| S24+ High cab-dash overcast / low sun / dusk | 30,0 | 33,4 / 33,6–33,7 / 34,1–35,1 | 12,2 / 14,9 / 21,6 | 18,6–19,4 | 1000–1055 | 34,6–37,2 / 0 |
| S24+ High street / truck-34 | 30,0 | 33,4 / 33,6–33,8 / 34,1–34,7 | 12,9 / 12,7 | 19,5 / 18,2 | 994 | 36,2–36,4 / 0 |
| S24+ High DK8, MSAA 2× (new) HLOD on (repeat, start 37 °C) / off | 30,0 / 30,0 | 33,4 / 33,6 / 33,8 | **18,7** / 18,3 | 16,8 / 16,9 | 983 / 991 | 38,4 / 0 |
| S24+ High DK8, `rq_msaa=4` (old High) | 26,8 | 33,4 / 66,8 / 67,2 | 36,3 / 37,4 | 17,4 | 1058 | 37,0 / 0 |

- High MSAA 4× → 2×: −17,6 ms GPU in the forest (36,3 → 18,7), 26,8 → 30 FPS; confirms r4. The 10 s motion recording (review r3 condition)
  needs the route through DK8, blocked by the s ≈ 583–606 m world fault → after the world fix, with gate 3.
- Forest HLOD: −1,1 ms GPU on the A16 (the A16 already culls trees at 300 m × LOD bias); no gain measurable on the S24+ here (QA camera looks along the
  road, near trees dominate). Draws in the High truck-34 view 742 → 282 with the per-chunk merge (editor stats).
- Interior LOD0 on every tier: A16 cab-dash GPU 16,1 ms (A7: 16,0–16,3 ms with LOD2) — no measurable cost; PSS 571–581 → 610–615 MB (+35 MB: LOD0 interior
  mesh + AO atlas, HLOD meshes). S24+ cab-dash 12,2 ms overcast (A7: 29 ms on a hot phone; cool now).
- One S24+ DK8 run with HLOD fell to 10 FPS (frame p50 100 ms, GPU 22,6 ms, CPU 26 ms) right after the low-sun/dusk runs at 35,9 °C; the 60 s repeat was a
  clean 30 FPS, GPU 18,7 ms. Cause UNVERIFIED (no logcat hint) — watch for it in gate 3.
- Tests: EditMode 27/27; PlayMode 35 passed, 4 skipped, 2 failed (`WorldCRouteTests`: stuck at s ≈ 583–606 m, world v3.1 fault — the world agent's fix).
