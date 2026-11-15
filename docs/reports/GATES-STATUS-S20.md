# Stan bramek i Definition of Done — sesja 20 (2026-11-14)

Autor: agent Y2 (tylko dokument, bez zmian kodu, bez Unity i bez telefonu). Baza: `origin/main` `6dc816c`.
Źródła: `docs/03_ETAPY_I_BRAMKI.md`, `docs/reports/GATE-*.md` (+ szkice), `GATE12-PHONE-2026-11-14-A16.md`,
`REVIEW-2026-11-14-s20-gate3-phone.md`, `docs/PERFORMANCE_BUDGETS.md`, `docs/DEVICE_MATRIX.md`, `docs/04` §6,
`docs/PHYSICS_VALIDATION.md`, `docs/06` §5, `docs/07` §6, ADR 0046/0062/0103/0106/0111/0113/0136/0157/0177/0195,
`docs/11`, `HANDOVER.md` (blok „SESJA 20”, linie 1–123), `scripts/*.ps1`.

Zasada dokumentu: każde twierdzenie ma odnośnik `plik:linia`. Liczby przepisane, nie mierzone przez autora.
Katalogi `artifacts/` są poza gitem (`.gitignore:31`) — autor ich nie widział; liczby z nich są cytowane z raportów.
Legenda stanu: **SPEŁNIONE** (dowód) · **CZĘŚCIOWO** · **NIESPEŁNIONE** · **NIEZMIERZONE** (brak pomiaru, nie wiadomo).

## Podsumowanie

| Bramka | Werdykt w raporcie | Stan faktyczny wg dowodów | Główna blokada |
|---|---|---|---|
| Etap 0 | CZĘŚCIOWO (`GATE-0.md:5`) | prawie spełniona — pomiar Boot na A16 istnieje w `DEVICE-RUN-2026-11-09.md:7`, ale na APK `-dirty` (`:14`) i nie wpisany do GATE-0 | aktualizacja raportu + pomiar na czystym APK |
| Etap 1 | SZKIC (`GATE-1.md:6`) | CZĘŚCIOWO — 0–80 ×3 na telefonie PASS (`GATE12-PHONE…:15-17`); postój, krawężnik, oscylacje tylko symulator/edytor | przebiegi `park_flat_solo`/`c50_*` na telefonie, werdykt właściciela |
| Etap 2 | SZKIC (`GATE-2.md:6`) | CZĘŚCIOWO — 0–80 i 80→0 pusty/40 t na telefonie PASS (`GATE12-PHONE…:9-10`); feel test właściciela brak | feel test właściciela (4 manewry) |
| Tor A | brak raportu bramki | NIEZMIERZONE jako bramka — kroki A1–A8 wykonane, checklista `docs/07` §6 nieoceniona | raport toru A, profil (Medium vs Low), akceptacja właściciela |
| Etap 3 | ZALICZONA D57 (`GATE-3.md:8`) | ZALICZONA decyzją właściciela, utrzymana na telefonie s20 (`REVIEW-…-gate3-phone.md:12`); 2 z 5 punktów checklisty `docs/06` §5 otwarte | dług: zrzuty par z telefonu, kontrole automatyczne, G3-B na `edb5524993`, metryka > 40 ms |
| Etap 4 | brak raportu | NIEOTWARTA formalnie; część narzędzi istnieje (regeneracja, fidelity, walidator, QA) | raport `GATE-4.md`, regeneracja jedną komendą w gicie, przejazd całego kafla |

---

## 1. Etap 0 — Fundament

Kryteria: `docs/03_ETAPY_I_BRAMKI.md:14`. Raport: `docs/reports/GATE-0.md` (2026-11-09, werdykt „CZĘŚCIOWO ZALICZONA”, `:5`).

| # | Kryterium (dosłownie z `docs/03:14`) | Stan | Dowód |
|---|---|---|---|
| 0.1 | „APK zainstalowany i uruchomiony na Samsungu A” | SPEŁNIONE | `GATE-0.md:21` (`adb install` → `Success`), `:22` (gra startuje, Target API 36) |
| 0.2 | „logcat bez wyjątków” | SPEŁNIONE (z zastrzeżeniem) | `GATE-0.md:22` — brak wyjątków, ale scena pauzowała przez blokadę; później `DEVICE-RUN-2026-11-09.md:3` „bez wyjątków w logcat (install run)” |
| 0.3 | „pusta scena: zmierzone FPS/frame time” | CZĘŚCIOWO | `GATE-0.md:23` ❌; ale `docs/reports/device/DEVICE-RUN-2026-11-09.md:7`: A16 Boot **Medium** 30,01 FPS, p50/p95/p99/max 33,33/33,47/33,57/33,66 ms, PSS ~289 MB, 27,4 °C — na APK `kamion-0.1.0-5e1bb89e4c-dirty` (`:14`). Tag `v0.0-gate0` (commit `e421b00e`) ma opis „Gate 0: APK runs on Samsung A16, FPS measured, no exceptions”. Pomiaru na czystym APK i w profilu Low (D49, `docs/11:70`) brak |
| 0.4 | „PNG z harnessu obejrzany przez Ciebie” | SPEŁNIONE (przez agenta) | `GATE-0.md:25`, `:37-46` — 4 kamery obejrzane, 1 błąd poprawiony. „przez Ciebie” = właściciel: brak śladu akceptacji w `GATE-0.md:59-60` |
| 0.5 | „`doctor` zielony” | SPEŁNIONE | `GATE-0.md:26` — `all required checks green` |
| 0.6 | „build odtwarzalny jedną komendą z czystego klonu” | SPEŁNIONE | `GATE-0.md:20` — świeży klon → APK 33,7 MB w 167 s (uwaga MAX_PATH) |
| 0.7 | (zakres) zrzut ekranu z telefonu | CZĘŚCIOWO | `GATE-0.md:24` ❌ czarny; zrzuty z telefonu z 9.11 istnieją dla innych scen (`docs/reports/device/2026-11-09_A16_*.jpg`), nie dla Boot |

**Co blokuje zamknięcie:** (1) `GATE-0.md` nie zna pomiaru z `DEVICE-RUN-2026-11-09.md:7` — raport i `docs/PERFORMANCE_BUDGETS.md:42-43` („Not measured yet”) oraz `docs/STATUS.md:10` są nieaktualne; (2) pomiar był na APK `-dirty`, w profilu Medium, a A16 jest oficjalnie Low (D49, `docs/11:70`); (3) brak zrzutu Boot z telefonu.

**Komendy dla lidera** (A16 odblokowany, bez działającego Unity, `artifacts/locks/PHONE_RUN` założony ręcznie):
```
pwsh scripts/doctor.ps1                                                     # exit 0 = zielono
pwsh scripts/build-android.ps1 -SkipBuild -Apk artifacts/apk/kamion-0.1.0-edb5524993.apk -Install -Run -Serial RFGL34SJYDZ -LogcatSeconds 20 -Tier Low -Fps 30
pwsh scripts/device-metrics.ps1 -Serial RFGL34SJYDZ -Launch -DurationSeconds 75 -Tier Low -Fps 30
#   -> artifacts/device/RFGL34SJYDZ/<ts>/ (CSV klatek, p50/p95/p99, PSS, temperatura, zrzut ekranu)
# alternatywa w ramach zestawu bramek 1-2 (wymaga formy & ... -Only @(...), patrz HANDOVER.md:60):
& ./scripts/gate12-phone.ps1 -Apk artifacts/apk/kamion-0.1.0-edb5524993.apk -UseExistingLock -Only @('boot_idle')
pwsh scripts/visual-qa.ps1 -Scene Boot -Tier Low                            # -> artifacts/visual-qa/Boot/<id>.png
```
Parametry sprawdzone: `scripts/build-android.ps1:15-28`, `scripts/device-metrics.ps1:14-30` (domyślna scena `''` = Boot), `scripts/gate12-phone.ps1:33-45`, `:61` (`boot_idle` 75 s), `scripts/visual-qa.ps1:12-18`.

---

## 2. Etap 1 — Laboratorium jazdy: ciągnik (tor F)

Kryteria: `docs/03_ETAPY_I_BRAMKI.md:18`. Raport: `docs/reports/GATE-1.md` (werdykt „SZKIC — czeka na telefon”, `:6`) + dopisek s20 z telefonu (`:95-102`).
Pomiar telefonu s20: A16 RFGL34SJYDZ, Low/30, APK `kamion-0.1.0-77cfd94bf8` (czysty, `GATE12-PHONE-2026-11-14-A16.md:3`), wyłącznie przebiegi `s080_*` (`HANDOVER.md:38`, tabela `GATE12-PHONE…:7-13` — innych przebiegów brak).

| # | Kryterium (dosłownie z `docs/03:18`) | Stan | Dowód (symulator / edytor / telefon) |
|---|---|---|---|
| 1.1 | „testy z `docs/04` §6 dla ciągnika solo zielone w tolerancjach” | CZĘŚCIOWO | symulator 132/132 scenariuszy, 750 kontroli; PlayMode 155/163 (0 fail, 8 skip) (`GATE-1.md:21`). Telefon: tylko §6.3 (0–60/0–80) i §6.5 (80→0 suche z ABS) — solo 0–60 10,00 s, 0–80 13,66 s, 80→0 35,85 m, MFDD 7,44 m/s², blokada kół 0 s, PASS (`GATE12-PHONE…:11-13`) |
| 1.2 | „brak dryfu na postoju” | NIEZMIERZONE na telefonie | symulator: dryf 2,2e-16 m płasko, 2,8/4,5 mm na 12 % (`GATE-1.md:46-47`); edytor 2–5 mm/60 s (`GATE-1.md:22`). Przebieg `park_flat_solo` (330 s, `scripts/gate12-phone.ps1:62`) nie był uruchomiony w s20 (`HANDOVER.md:38` `-Only s080_*`) |
| 1.3 | „brak oscylacji” | NIEZMIERZONE na telefonie | symulator `soak_30min_parked`, `straight_after_steer_pulse@solo` (`GATE-1.md:23`) |
| 1.4 | „krawężnik nie teleportuje” | CZĘŚCIOWO | symulator max \|Δv\|/krok 0,050–0,096 m/s ≤ 0,35 (`GATE-1.md:24`, `:55`); PlayMode `KerbStrikeParityTests` (`:24`). Telefon: tylko jazda po płaskiej prostej, max \|Δv\|/krok 0,080 m/s (`GATE12-PHONE…:11`); krawężnik 8/15 cm na telefonie — tylko ręcznie (`GATE-1.md:85`, `scripts/gate12-phone.ps1:16-17`) |
| 1.5 | „3 przejazdy 0–80 km/h powtarzalne ±3%” | SPEŁNIONE | telefon: 13,66 / 13,66 / 13,66 s, odchyłka 0,00 % → PASS (`GATE12-PHONE…:15-17`); edytor 13,67 ×3 (`docs/adr/0195-autopilot-prosta-0-80-0.md:47`) |
| 1.6 | „wszystko na telefonie” | CZĘŚCIOWO | z telefonu tylko 1.1 (część), 1.4 (część), 1.5. Koszt kroku fizyki A16 p50 594–627 µs, p99 ≤ 989 µs (`GATE12-PHONE…:9-13`); FPS 30,0, p99 33,5–33,8 ms, PSS 386–412 MB (`GATE-1.md:99`) |
| 1.7 | „Koła są nudne i stabilne” = sukces (ocena) | CZĘŚCIOWO | D55 (Fold): „jest spoko, już lepiej się jeździ” (`docs/11:76`) — ocena kierowania, nie test bramki (`GATE-1.md:15`) |

**Co blokuje zamknięcie:**
1. Werdykt w `GATE-1.md:6` i tabela `:19-26` nieaktualne (nadal „❌ brak” przy 0–80 na telefonie, `:25`) mimo dopisku s20 `:95-102`; HANDOVER oddaje status do decyzji właściciela (`HANDOVER.md:60`).
2. Brak przebiegów telefonu dla postoju (`park_flat_solo`) i okręgów (`c50_solo_1..3`, `c25_solo`) — skrypt je ma (`scripts/gate12-phone.ps1:62-66`).
3. Nieautomatyzowalne: postój 12 %, krawężnik 8/15 cm, próg, koleiny, kierunek gyro — ręcznie z „Nagraj CSV” (`GATE-1.md:82-87`, `scripts/gate12-phone.ps1:16-17`).
4. Otwarta decyzja właściciela: zakres kierownicy 270° vs 900° (`GATE-1.md:93`).

**Komendy dla lidera** (A16 odblokowany, bez Unity, PHONE_RUN ręcznie; lista `-Only` tylko w formie `& ... @(...)` — `HANDOVER.md:60`):
```
dotnet test tools/physics-runner -c Release                    # ostatnio 274/274 (docs/adr/0195-...:41)
dotnet run -c Release --project tools/physics-runner/Runner    # ALL ... SCENARIOS PASSED
pwsh scripts/test.ps1 -Platform EditMode                       # -> artifacts/tests/editmode-<ts>.xml
pwsh scripts/test.ps1 -Platform PlayMode                       # -> artifacts/tests/playmode-<ts>.xml
& ./scripts/gate12-phone.ps1 -Apk artifacts/apk/kamion-0.1.0-edb5524993.apk -UseExistingLock -Only @('park_flat_solo','c50_solo_1','c50_solo_2','c50_solo_3','c25_solo')
uv run --project tools/perf python scripts/gate12_telemetry.py artifacts/gate12/<ts>     # -> artifacts/gate12/<ts>/gate12-summary.md
```
Ręcznie (właściciel lub lider z telefonem w dłoni): podjazd 12 % z hamulcem postojowym, krawężnik 8/15 cm, próg — „Nagraj CSV”, potem
`adb -s RFGL34SJYDZ pull /sdcard/Android/data/com.woogitsugames.kamion/files/telemetry` i ten sam `gate12_telemetry.py` (`GATE-1.md:87`).

---

## 3. Etap 2 — Naczepa, pneumatyka, pełny układ napędowy (tor F)

Kryteria: `docs/03_ETAPY_I_BRAMKI.md:22`. Raport: `docs/reports/GATE-2.md` (werdykt „SZKIC — czeka na telefon”, `:6`) + dopisek s20 (`:72-79`).

| # | Kryterium (dosłownie z `docs/03:22`) | Stan | Dowód |
|---|---|---|---|
| 2.1 | „pełny pakiet walidacyjny `docs/04` §6 (pusty i 40 t)” | CZĘŚCIOWO | symulator 132/132, 750 kontroli; PlayMode `CombinationLabTests` 15/15 (`GATE-2.md:17`), szczegóły `:27-48`. Telefon: §6.3 i §6.5 — pusty 0–80 20,67 s / 80→0 39,67 m; 40 t 0–80 47,79 s / 80→0 40,72 m, MFDD 7,00, błąd siodła ≤ 0,17 mm, PASS (`GATE12-PHONE…:9-10`). §6.13 (floating origin) bez osobnego scenariusza (`GATE-2.md:51`); §6.10 cofanie pod rampę „poza runnerem” wg `docs/PHYSICS_VALIDATION.md:316`, ale w GATE-2 jest wiersz `reverse_dock_s_maneuver_comb` (`GATE-2.md:43`) |
| 2.2 | „jackknife możliwy przy błędzie kierowcy” | SPEŁNIONE (symulator) | 80,6° / 92,1° ≥ 30° (`GATE-2.md:18`); na telefonie nie sprawdzane |
| 2.3 | „brak eksplozji solvera” | SPEŁNIONE (symulator) / CZĘŚCIOWO (telefon) | max Δv ≤ 0,35 m/s, soak 30 min NaN 0, dryf energii 1,4 J (`GATE-2.md:19`); telefon: max \|Δv\|/krok 0,074–0,077 m/s na prostej (`GATE12-PHONE…:9-10`) |
| 2.4 | „golden telemetry w `tests/golden/`” | SPEŁNIONE | 9 plików + `tolerances.json`, `Stage2Tests.GoldenTelemetry_Matches` zielone (`GATE-2.md:20`, `GATE-1.md:61`) |
| 2.5 | „feel test właściciela na telefonie (ruszanie pod górę z 40 t, hamowanie awaryjne, rondo, cofanie pod rampę) z listą uwag i ich realizacją” | NIESPEŁNIONE | `GATE-2.md:21` „4 manewry bramki nieocenione”; częściowo D55/D58/D59 (`docs/11:76-80`). Instrukcja: `docs/owner/FEEL-TEST.md`, `docs/PHYSICS_VALIDATION.md:325-336`; D25: test jazdy właściciela „po raporcie bramki 3” (`docs/11:47`) — bramka 3 zaliczona (D57), test wciąż nie wykonany |

**Co blokuje zamknięcie:**
1. Feel test właściciela (2.5) — wyłącznie właściciel.
2. Werdykt `GATE-2.md:6` i tabela `:17` nieaktualne wobec dopisku s20 `:72-79`.
3. Brak przebiegów okręgu z naczepą na telefonie (`c50_empty`, `c50_40t`: przegub w stanie ustalonym, koszt kroku 2 brył + 152 promieni, lusterka, kamera cofania — `GATE-2.md:55-57`, `:67`).
4. S24+ nie mierzony w rundzie bramek 1–2 (`GATE-2.md:79`).
5. Otwarta decyzja właściciela z 9.11: lusterka w kabinie jako okienka czy rozglądanie (`GATE-2.md:70`).

**Komendy dla lidera:**
```
& ./scripts/gate12-phone.ps1 -Apk artifacts/apk/kamion-0.1.0-edb5524993.apk -UseExistingLock -Only @('c50_empty','c50_40t','s080_empty','s080_40t')
uv run --project tools/perf python scripts/gate12_telemetry.py artifacts/gate12/<ts>
# S24+ (telefon właściciela — tylko za zgodą w tej sesji; skrypt startuje przy baterii >= 40 %, przerywa < 30 %, czeka < 36 °C — scripts/gate12-phone.ps1:21-23):
& ./scripts/gate12-phone.ps1 -Apk artifacts/apk/kamion-0.1.0-<sha>-high.apk -UseExistingLock -S24Only -S24Tier High -S24Fps 30
```
Zestaw S24+ to `park_flat_solo`, `c50_solo_1`, `c50_40t` (`scripts/gate12-phone.ps1:77-81`). Feel test: właściciel wg `docs/owner/FEEL-TEST.md`, uwagi → lista zadań → wpis w `GATE-2.md` (`GATE-2.md:62-64`).

---

## 4. Tor A — Ciężarówka premium (bramka przed Etapem 5)

Kryteria: `docs/03_ETAPY_I_BRAMKI.md:27` + checklista `docs/07_CIEZAROWKA_3D.md:44`. **Raportu bramki toru A nie ma** (brak `GATE-A*.md` w `docs/reports/`; w `docs/reports/visual/` są raporty kroków `truck-A2`…`truck-A8`, `trailer-curtainsider`). Plan `docs/plan/TRACK-A.md:7-16` ma tabelę kroków zatrzymaną na A6 („A7–A8 … później”, `:16`), choć raport A7 istnieje (`docs/reports/visual/truck-A7/README.md:1`) i A7 jest zmierzony (`docs/PERFORMANCE_BUDGETS.md:88-98`).

| # | Kryterium | Stan | Dowód |
|---|---|---|---|
| A.1 | „checklista `docs/07` §6 zaliczona” (całość) | NIEZMIERZONE | nigdzie w repo nie ma oceny checklisty „quality-ready” (szukane `quality-ready`, `07 §6`) |
| A.1a | wymiary i proporcje zweryfikowane | CZĘŚCIOWO | `docs/plan/TRACK-A.md:9` — wymiary `WORKING_VALUE` „do potwierdzenia zdjęciami”; research R3 chmury #2 scalony, follow-upy: promień toczenia 0,51 vs 0,521–0,528 m, naciski 65/35 vs karta (`HANDOVER.md:97`); zadanie truckdata-0201 (`HANDOVER.md:102`) |
| A.1b | brak błędów normalnych, UV, prześwitów | NIEZMIERZONE | brak raportu kontroli dla ciężarówki |
| A.1c | właściwe materiały | CZĘŚCIOWO | P2-8 „soczewki jako płaskie prostokąty; szary quad za przednią szybą” (`REVIEW-2026-11-14-s20-gate3-phone.md:50`, `:69`) |
| A.1d | kabina jezdna z FPP, wskaźniki z fizyki | NIEZMIERZONE | brak raportu (D20: tylko ekran 12,3", `docs/11:37`) |
| A.1e | lusterka użyteczne | CZĘŚCIOWO | 6 lusterek z limitem renderów per tier (`docs/PERFORMANCE_BUDGETS.md:36`); decyzja „okienka vs rozglądanie” otwarta (`GATE-2.md:70`) |
| A.1f | światła i ich grupy działają | CZĘŚCIOWO | soczewki widoczne na telefonie, DRL + kierunkowskaz (`REVIEW-…-gate3-phone.md:50`); ADR 0197 (stop:pozycyjne) zlecone (`HANDOVER.md:95`) |
| A.1g | LOD-y bez widocznego przeskoku | NIEZMIERZONE | „Migotania i LOD pop w ruchu nie da się ocenić ze stopklatek” (`REVIEW-…-gate3-phone.md:78`) |
| A.1h | „zrzuty z telefonu (Samsung A Medium) i z edytora (High)” | CZĘŚCIOWO | z telefonu są kadry `truck-34_*`, `cab-*` na A16 **Low** (`REVIEW-…-gate3-phone.md:50-53`); Medium tylko z 9.11 (`docs/reports/visual/truck-A7/README.md:45-46`) |
| A.1i | `visual-critic` PASS | NIEZMIERZONE | brak recenzji toru A jako całości (są recenzje kroków, np. `docs/reports/visual/REVIEW-2026-11-12-s12-0130-truck-r3.md`) |
| A.1j | akceptacja właściciela | CZĘŚCIOWO | wybory: sylwetka B (D16), TRAKT (D17), koniak (D19), front `modern` (D28), pochylenie 1,5° (D29), naczepa bez pasa (D47) — `docs/11:33-36,49-50,68`; brak akceptacji gotowego modelu |
| A.2 | „zrzuty z telefonu” | CZĘŚCIOWO | j.w. A.1h |
| A.3 | „budżet trójkątów/draw calli/pamięci spełniony na profilu Medium (Samsung A)” | NIEZMIERZONE dla Medium | trójkąty: zewn. 82,9k/43,0k/14,5k, wnętrze 75,4k/34,9k/19,0k (`truck-A7/README.md:65`) vs hipoteza LOD0 120–250k (`docs/07:30`); draw calli ciężarówki z telefonu nie mierzono (cel „< 30 draws dla zestawu”, `docs/PERFORMANCE_BUDGETS.md:64-65`); koszt GPU własnej ciężarówki na A16 Low 4,7–5,4 ms (`docs/PERFORMANCE_BUDGETS.md:128`) |

**Co blokuje zamknięcie:** (1) brak raportu bramki toru A i oceny checklisty `docs/07` §6; (2) profil: `docs/03:27` i `docs/07:44` każą Medium na Samsungu A, a D49 ustanowił A16 jako Low (`docs/11:70`) — sprzeczność do rozstrzygnięcia; (3) naczepa: A8 wykonane wizualnie (`docs/reports/visual/trailer-curtainsider/`), bez oceny bramki; (4) akceptacja właściciela.

**Komendy dla lidera:**
```
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High   -Lighting overcast -Cameras cab-driver,cab-dash,cab-left,cab-right,truck-34
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Medium -Lighting lowsun   -Cameras cab-driver,cab-dash,cab-left,cab-right,truck-34
#   -> artifacts/visual-qa/WorldC/<id>.png (albo -OutputDir <dir>)
pwsh scripts/device-metrics.ps1 -Serial RFGL34SJYDZ -Launch -Scene WorldC -QaCamera truck-34 -Tier Medium -Fps 30 -DurationSeconds 60 -Extra lighting=overcast
pwsh scripts/device-metrics.ps1 -Serial RFGL34SJYDZ -Launch -Scene WorldC -QaCamera cab-dash  -Tier Medium -Fps 30 -DurationSeconds 60 -Extra lighting=lowsun
#   -> artifacts/device/RFGL34SJYDZ/<ts>/ (GPU p50, PSS, zrzut) — wzór komendy: truck-A7/README.md:17
```
Parametry: `scripts/visual-qa.ps1:12-19`, `scripts/device-metrics.ps1:14-30`. Draw calle/trójkąty z telefonu wymagają Frame Debuggera / Arm Performance Studio (`docs/PERFORMANCE_BUDGETS.md:74-75`) — w skryptach brak komendy.

---

## 5. Etap 3 — Referencyjna próbka jakości (bramka anty-slop)

Kryteria: `docs/03_ETAPY_I_BRAMKI.md:31`. Raport: `docs/reports/GATE-3.md` — **ZALICZONA decyzją D57** (`:8`, `docs/11:78`), przy priorytecie D51 „rozpoznawalność > materiały” (`docs/11:72`).
Pomiary kontrolne s20: A16 Low/30 na `77cfd94bf8` (`GATE-3.md:109-115`), S24+ High/30 na `18e368be69-high` (`:117-122`), A16 G3-A na `edb5524993` (`:124-129`). Recenzja zrzutów z telefonu: **UTRZYMANA** (`REVIEW-2026-11-14-s20-gate3-phone.md:12`; 24/24 T, `:47`).

| # | Kryterium (dosłownie z `docs/03:31`) | Stan | Dowód |
|---|---|---|---|
| 3.1 | „porównanie side-by-side z **zdjęciami właściciela z tego miejsca** w tych samych ujęciach” | SPEŁNIONE z odstępstwem | pakiet 12 par, referencje z otwartych źródeł zamiast zdjęć właściciela (D43, `docs/11:64`), odstępstwo przyjęte D57 (`GATE-3.md:19`) |
| 3.2 | „checklista `docs/06` §5 zaliczona” | CZĘŚCIOWO | rozpisane niżej (1 punkt SPEŁNIONY, 3 CZĘŚCIOWO, 1 NIESPEŁNIONY, wynik decyzją) |
| 3.3 | „zmierzony koszt na Samsungu A (Medium)” | SPEŁNIONE dla Low (D49) | s20 A16 Low: G3-A 29,99 FPS, p95/p99 33,46/33,57 ms, GPU p50 32,1, PSS 917,5 MB; G3-B 29,95, 33,45/33,62, GPU p50 31,3, PSS 877,8 — budżet OK (`GATE-3.md:113-114`); `edb5524993` G3-A 29,97 FPS, p99 33,56, PSS 900,8 (`:127`). **G3-B na `edb5524993` NIEZMIERZONY** (`:128`, `HANDOVER.md:96`). Medium nie mierzone (D49: A16 Medium 21,7 FPS, `docs/11:70`) |
| 3.4 | „oszacowany zapas dla High” | SPEŁNIONE jako oszacowanie (wynik: brak zapasu na 60 FPS) | S24+ High/30: GPU p50 23,0 / 22,5 ms, PSS 1670/1644 MB, kamery 56/57 i 46/46 (`GATE-3.md:120-121`); „High/60 nie jest osiągalne bez optymalizacji” (`:122`, `HANDOVER.md:64`). Tabela kryteriów `GATE-3.md:22` nadal mówi „tylko starsze buildy” — nieaktualne |
| 3.5 | „**akceptacja kierunku artystycznego przez właściciela**” | SPEŁNIONE dla bramki 3 | D57 (`docs/11:78`, `GATE-3.md:23`); D51 odkłada materiały; recenzja s20: „materiały nadal ‚gra mobilna z 2016’” (`REVIEW-…-gate3-phone.md:14`), oceny materiały 4/10, zużycie 4/10 (`:76`) |

Checklista `docs/06_GRAFIKA_ANTI_AI_SLOP.md:40-46` dla bramki 3:

| Punkt | Stan | Dowód |
|---|---|---|
| 1. zestaw kamer kontrolnych | CZĘŚCIOWO | 57 + 46 kamer CAPTURED (`GATE-3.md:67`, s20 `:113-114`); z listy `docs/06:41` brak „kabina noc”, „deszcz noc” (noc/deszcz → Etap 5, `docs/plan/STAGE-3.md:30`) |
| 2. render z edytora i zrzut z telefonu | CZĘŚCIOWO | kamery kontrolne PASS; **brak zrzutów A16 dla 42 póz par zdjęciowych** (`GATE-3.md:68`, `:96`) |
| 3. side-by-side z referencją | SPEŁNIONE | pakiet 12 (`GATE-3.md:69`) |
| 4. przegląd `visual-critic` | CZĘŚCIOWO | pełny zestaw 42 par FAIL (27 R / 15 P / 0 N), pakiet 12 PASS warunkowy (`GATE-3.md:70`); s20 telefon UTRZYMANA, P1 ×3: chodnik na wiszącej płycie, szew muru oporowego, postrzępione cienie na Low (`REVIEW-…-gate3-phone.md:59-62`) |
| 5. kontrole automatyczne | NIESPEŁNIONE | ostatni raport z 10.11 FAIL (albedo, normalne/UV, obiekty vs teren), nieodświeżony (`GATE-3.md:71`) |
| 6. wynik PASS/FAIL | ZALICZONA decyzją | `GATE-3.md:72` — punkty 2 i 5 jako dług |

**Co blokuje pełne domknięcie (zaliczenie D57 stoi):**
1. G3-B na APK `edb5524993` niezmierzony — A16 offline (`GATE-3.md:128`, `HANDOVER.md:96`).
2. Metryka „≤ 12 klatek > 40 ms na przejazd” czeka na decyzję właściciela (`GATE-3.md:57-61`, `docs/adr/0177-perf-p99-pso-refresh.md:48-53`, `HANDOVER.md:120`); **dla przebiegów kontrolnych s20 liczba klatek > 40 ms nie jest wpisana** (tabele `GATE-3.md:111-128` mają tylko „> 50 ms”). HANDOVER podaje liczby z przebiegów PSO refresh (A 4/2, B 4/2, `HANDOVER.md:60`), nie z przebiegów kontrolnych.
3. Punkty 2 i 5 checklisty (`GATE-3.md:96`).
4. GPU A16 bez zapasu: GPU p95 34,5 / 34,3 ms > 33,3 ms klatki (`GATE-3.md:113-114`, `REVIEW-…-gate3-phone.md:16`); PSS zbliża się do limitu 1000 MB (§9, rozbieżność R23).
5. Test „feelingu” na odcinku niewypełniony (`GATE-3.md:97`).
6. Brak tagu git po bramce 3 — `docs/03:7` wymaga tagu i aktualizacji `docs/STATUS.md` i `docs/ROADMAP.md`; na origin jest tylko tag `v0.0-gate0`, `docs/STATUS.md:1` ma datę 2026-11-09, `docs/ROADMAP.md` nie istnieje.

**Komendy dla lidera** (A16 odblokowany, bez Unity — „Argon/sesja kodu uruchamiają Unity → adb może padać”, `HANDOVER.md:96`; PHONE_RUN ręcznie, `GATE-3.md:100-101`):
```
& ./scripts/gate3-run.ps1 -Serial RFGL34SJYDZ -Segment B -Tier Low -Fps 30 -SkipBuild -Apk artifacts/apk/kamion-0.1.0-edb5524993.apk
#   -> artifacts/gate3/<ts>/RFGL34SJYDZ/gate3-result.json + cam/*.png + drive/frametimes.csv
uv run --project tools/perf python tools/perf/p99_spikes.py --summary 20261114-063715 20261114-071223 20261114-182955 <ts-B-edb>
#   -> klatki > 40/45/50/60 ms na przejazd (metryka ADR 0177) dla wszystkich przebiegów s20
pwsh scripts/gate3-evidence.ps1 -Tiers Low -Lightings overcast,lowsun -PhoneDir artifacts/gate3/20261114-063715 -Apk artifacts/apk/kamion-0.1.0-edb5524993.apk
#   -> artifacts/gate3/evidence/gate3-evidence.md (punkt 5 checklisty; exit 0 = PASS, 1 = FAIL, 2 = błąd)
# S24+ High 60 (tylko za zgodą właściciela; bateria >= 40 % — docs/owner/S24-HIGH-RUN.md:3-4):
pwsh scripts/gate3-run.ps1 -Serial RZCX60VE8ZY -Segment A -Tier High -Fps 60 -WorldHigh -SkipBuild -Apk artifacts/apk/kamion-0.1.0-<sha>-high.apk
```
Parametry: `scripts/gate3-run.ps1:25-49`, `scripts/gate3-evidence.ps1:24-38`, `tools/perf/p99_spikes.py:1-6,14-21` (argument = znacznik czasu katalogu `artifacts/gate3/<ts>`; ścieżka bazowa na sztywno `C:\Users\matma\…\artifacts\gate3`, `:11`). Zrzuty par zdjęciowych z telefonu: `scripts/sbs-gate3.ps1:2-12` renderuje tylko w edytorze — **komendy dla zrzutów 42 póz z telefonu nie ma** (do zrobienia: pozy jako kamery bramki + `gate3-run.ps1 -CameraFilter`).

---

## 6. Etap 4 — Pipeline świata na 2×2 km (następna bramka)

Kryteria: `docs/03_ETAPY_I_BRAMKI.md:35`. **Raportu `GATE-4.md` nie ma i bramka nie jest formalnie otwarta.** Narzędzia i dane istnieją z pracy nad bramką 3 (region `bialystok-industrial-c` = kafel 2048 × 2048 m, `docs/DATA_QA.md:22`).

| # | Kryterium (dosłownie z `docs/03:35`) | Stan | Dowód |
|---|---|---|---|
| 4.1 | „regeneracja 2×2 km jedną komendą” | CZĘŚCIOWO | regeneracja C działa: „build_world 8,7 min, fidelity OK, import OK” (`HANDOVER.md:50`); ale lider uruchamia ją skryptem spoza gita (`artifacts/lead-s20/regen.ps1`, `HANDOVER.md:47`; wcześniej `artifacts/lead-s17/regen.ps1`, `:117`). W gicie łańcuch to 3 kroki (`CLAUDE.md:39`); `scripts/import-region.ps1 -Build` uruchamia `build_world.py` + `export-route.py` + import (`scripts/import-region.ps1:34-42`), ale nie `build_region.py`/ingest (`docs/DATA_QA.md:12-16`) |
| 4.2 | „ręczne poprawki przeżywają reimport” | CZĘŚCIOWO (mechanizm jest, test całościowy niezmierzony) | `authored_overrides` w `Data/Regions/bialystok-industrial-c/overrides.yaml` „przeżywają reimport” wg ADR (`docs/adr/0077-junction-islands-from-osm.md:97`, `0167-budynki-p1-kadry-bramki-3.md:35`); testy gis z override'ami per funkcja (np. `tests/gis/test_barriers_0159.py`); brak jednego testu „regeneracja od zera → wszystkie override'y obecne” |
| 4.3 | „zestaw przejeżdża całość bez wpadnięcia pod teren” | NIEZMIERZONE dla całego kafla | tylko trasa G3: `driveLog.suspiciousLines: 0` (`GATE-3.md:42`, `GATE-2.md:51`); autopilot `route` jeździ jedną trasą (`game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:208,217`), brak przejazdu całej sieci 2×2 km |
| 4.4 | „zero dziur w kolizjach” | NIEZMIERZONE | brak raportu/testu kolizji dla całego kafla; walidator świata: 558 znalezisk, error 56, na trasie G3 56 (`docs/reports/WORLD-VALIDATOR-2026-11-13-mistral.md:9`) — nie mierzy dziur kolizji |
| 4.5 | „odchyłka osi drogi od źródła w zadanej tolerancji” | CZĘŚCIOWO | `tools/worldgen/fidelity/run.py` + `tests/gis/test_road_fidelity.py` (`tools/worldgen/fidelity/STATUS.md:22`); „fidelity OK” po regeneracji s20 (`HANDOVER.md:50`); liczb odchyłki w raporcie bramki brak |
| 4.6 | „raport `low_confidence`” | CZĘŚCIOWO | `tools/worldgen/qa_report.py` → `docs/reports/map/<region>_qa.json`; jawna lista `low_confidence` (`docs/DATA_QA.md:3`, `:47`); `roads_qa.json` (`docs/WORLD_GENERATION.md:37`) |
| 4.7 | (zakres) chunki → Addressables | NIEZMIERZONE | D24: na razie bez Play Asset Delivery (`docs/11:45`); Addressables wymienione tylko jako opcja (`docs/PERFORMANCE_BUDGETS.md:164`) |

**Co blokuje zamknięcie:** (1) brak `GATE-4.md` i decyzji lidera o otwarciu etapu (Etap 3 zaliczony D57, `docs/11:78`); (2) skrypt „regeneracja jedną komendą” w gicie (dziś `artifacts/lead-s20/regen.ps1` poza repo); (3) przejazd całej sieci kafla i test dziur kolizji — brak narzędzia; (4) test „override'y przeżywają pełny reimport”.

**Komendy dla lidera** (pełna regeneracja wg `CLAUDE.md:39` i `docs/DATA_QA.md:12-16`):
```
uv run --project tools/worldgen tools/worldgen/ingest.py       --region bialystok-industrial-c
uv run --project tools/worldgen tools/worldgen/build_region.py --region bialystok-industrial-c
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c -Build      # build_world + export-route + import (Low,High)
uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c
uv run --project tools/worldgen pytest tests/gis -q                       # ostatnio 1105 pass / 2 xfail (HANDOVER.md:50)
uv run --project tools/worldgen tools/worldgen/qa_report.py    --region bialystok-industrial-c   # -> docs/reports/map/<region>_qa.json
uv run --project tools/worldgen tools/worldgen/validate/run.py --region bialystok-industrial-c --fail-on-error
pwsh scripts/device-metrics.ps1 -Serial RFGL34SJYDZ -Launch -Scene WorldC -Autopilot route -Speed 50 -Trailer 40 -Tier Low -Fps 30 -DurationSeconds 600
#   -> artifacts/device/RFGL34SJYDZ/<ts>/ (tylko trasa startowa, nie cały kafel)
```
Parametry: `scripts/import-region.ps1:24-29` (brak `-SkipCopy` wymienionego w `CLAUDE.md:39`), `scripts/device-metrics.ps1:14-30`, walidator `docs/reports/WORLD-VALIDATOR-2026-11-13-mistral.md` (sekcja „Uruchomienie”).

---

## 7. Definition of Done (`CLAUDE.md:48`) w praktyce bramek

| Element DoD | Jak jest spełniany | Braki (dowód) |
|---|---|---|
| „Kompiluje się na Androidzie” | czyste APK s20: `77cfd94bf8` (`HANDOVER.md:60`), `18e368be69-high` (`:64`), `edb5524993` 222,9 MB (`:89`); wcześniejszy czysty build „0 err” (`:52`) | metadane APK `dirty=False`, ale ciąg wersji w grze z „-dirty” (pliki nieśledzone w katalogu głównym, `GATE-1.md:102`) — mylące dla walidatorów `-dirty` |
| „testy zielone” | EditMode 580/581, 0 fail (`HANDOVER.md:56`, `:88`); pytest gis 1105 pass / 2 xfail (`:50`); .NET 274/274 (`docs/adr/0195-autopilot-prosta-0-80-0.md:41`) | pełny PlayMode po integracji s20 niezgłoszony — ostatni pełny 155/163, 0 fail, 8 skip z 13.11 (`GATE-1.md:38`); po 0195 tylko podzbiór 8/8 (`HANDOVER.md:38`) |
| „brak nowych krytycznych ostrzeżeń” | build „0 err” (`HANDOVER.md:52`) | liczba ostrzeżeń buildu s20 nie jest raportowana (ostatnia jawna: `errors=0 warnings=0`, `GATE-0.md:19`, 9.11) — NIEZMIERZONE |
| „dowód (log/zrzut/telemetria)” | raporty cytują `artifacts/gate12/…`, `artifacts/gate3/…`, `gate3-result.json` | `artifacts/` jest poza gitem (`.gitignore:31`) — dowody istnieją tylko na komputerze lidera; agenci w chmurze nie mogą ich sprawdzić (ten raport również) |
| „budżet wydajności nie pogorszony” | A16 Low p95/p99/PSS w budżecie we wszystkich przebiegach s20 (`GATE-3.md:113-114`, `:127`; `GATE12-PHONE…:9-13`) | GPU p95 A16 > 33,3 ms (`GATE-3.md:38`, `:113-114`); PSS rośnie (R23); S24+ High 60 FPS niespełnione (`GATE-3.md:122`); metryka > 40 ms nieraportowana dla s20 (§5) |
| „review innego agenta” | bramka 3 s20: `REVIEW-2026-11-14-s20-gate3-phone.md`; bramka 3 D57: `docs/reports/visual/REVIEW-2026-11-13-s16b-final.md` (`GATE-3.md:70`) | brak recenzji innego agenta dla `GATE-1.md`, `GATE-2.md` (gałąź `gates-s19`) i `GATE12-PHONE-2026-11-14-A16.md` — w `docs/reports/` nie ma pliku REVIEW, który by je obejmował |
| „docs/ADR/licencje zaktualizowane” | dopiski s20 w GATE-1/2/3 | nieaktualne: `GATE-0.md`, `docs/PERFORMANCE_BUDGETS.md:27,40,43`, `docs/STATUS.md` (2026-11-09), `docs/PHYSICS_VALIDATION.md:97,101,289,314,316`, `docs/plan/TRACK-A.md:16`, `docs/DEVICE_MATRIX.md:11`, statusy ADR 0177/0195 (R26); `docs/ROADMAP.md` nie istnieje (`docs/03:7`) |
| „commit” | wszystko w gicie | po bramce brak tagu (`docs/03:7`): na origin tylko `v0.0-gate0` |

Wniosek: DoD jest spełniane dla kodu i pomiarów A16, ale **dokumentacja bramek nie nadąża za pomiarami** (werdykty GATE-1/2 i wiersze tabel GATE-3 sprzeczne z własnymi dopiskami s20) i **brakuje recenzji innego agenta dla bramek 1–2**.

---

## 8. Decyzje właściciela potrzebne do zamknięcia

| # | Decyzja | Odnośniki | Proponowane opcje |
|---|---|---|---|
| W1 | Metryka „≤ 12 klatek > 40 ms na przejazd G3” (A16 Low) | `docs/adr/0177-perf-p99-pso-refresh.md:48-53`, `GATE-3.md:57-61`, `HANDOVER.md:120` | (a) przyjąć ≤ 12/przejazd jako WORKING_VALUE (konsekwencja: przebiegi D57 miały 14/14 — byłyby nad progiem, `GATE-3.md:59`; D57 nie jest odwoływane, `:60`); (b) przyjąć wersję na minutę ~≤ 11/min (`0177:51`); (c) tylko raportować bez progu; (d) odrzucić, zostaje p99 ≤ 40 ms |
| W2 | S24+ High 60 FPS nieosiągalne (GPU p50 ~23 ms przy limicie 30) | `GATE-3.md:120-122`, `HANDOVER.md:64`, `docs/PERFORMANCE_BUDGETS.md:13`, `docs/adr/0046-high-tier-gate3-60fps-headroom.md:16` (cel GPU p50 ≤ 12 ms), D36 (`docs/11:57`, A/B na S24+ „przed zamknięciem” — niezrobione) | (a) cel High na S24+ = 30 FPS, 60 jako opcja (zmiana `PERFORMANCE_BUDGETS.md:13` i `docs/06:52`); (b) runda optymalizacji GPU High (research R8 scalony, `HANDOVER.md:97`) + pomiar bez limitu/60 FPS — **liczba 23 ms pochodzi z przebiegu z limitem 30 FPS** (na A16 limit dodaje ~2 ms przez DVFS, `docs/adr/0106-perf-low-a16-r1.md:18`), więc wniosek „nieosiągalne” wymaga pomiaru `-Fps 60` (R25); (c) 60 FPS na S24+ w profilu Medium. Każdy przebieg S24+ wymaga zgody (`docs/owner/S24-HIGH-RUN.md:3-4`) |
| W3 | Feel test właściciela bramki 2 (+ „koła nudne i stabilne” bramki 1) | `docs/03:18,22`, `GATE-2.md:21,62-64`, `docs/owner/FEEL-TEST.md`, `docs/PHYSICS_VALIDATION.md:325-336`, D25 (`docs/11:47`) | (a) pełny test wg `FEEL-TEST.md` na A16 (APK `edb5524993`); (b) skrócony: 4 manewry bramki z `docs/03:22`; (c) na Foldzie jak D55 (`docs/11:76`) + jeden przebieg na A16. Uwagi → zadania → wpis w GATE-2 |
| W4 | Werdykt bramek 1 i 2 | `HANDOVER.md:60` („status bramek do decyzji właściciela”), `GATE-1.md:6`, `GATE-2.md:6` | (a) zaliczyć na podstawie telefonu s080 (0–80 ×3, 80→0) + symulator/edytor dla reszty; (b) warunkowo — po `park_flat_solo` i `c50_*` na telefonie (§2, §3); (c) pełne — dodatkowo ręczne przejazdy (krawężnik, 12 %) i feel test |
| W5 | Zdjęcia właściciela do side-by-side | `docs/03:31` (wymóg), D41 → D43 (`docs/11:62`, `:64` — właściciel nie robi zdjęć), odstępstwo przyjęte D57 (`GATE-3.md:19`); lista ujęć `docs/owner/PHOTO-LIST.md`; zdjęcia ciężarówki `docs/07:36` | (a) ADR + zmiana `docs/03:31`: referencje z otwartych źródeł jako standard bramek dzielnic (Etap 6); (b) właściciel robi zdjęcia tylko miejsc bez pokrycia (np. pierwsze 300 m G3-A bez pary, `docs/adr/0111-sbs-evidence-confidence.md:10`); (c) zdjęcia ciężarówki dla toru A (`docs/07:36`) zamiast zdjęć ulic |
| W6 | Akceptacja kierunku artystycznego — dalej niż D57 | D51/D57 (`docs/11:72,78`); recenzja s20: materiały 4/10, „gra mobilna z 2016” (`REVIEW-…-gate3-phone.md:14,76`); tor A: „akceptacja właściciela” (`docs/07:44`) | (a) ustalić, przed którą bramką materiały przestają być „po bramce” (propozycja: przed Etapem 5 — `docs/03:39` wymaga raportu wizualnego z telefonu); (b) osobna akceptacja modelu TRAKT (tor A) na zrzutach z telefonu |
| W7 | Profil A16 dla toru A (Medium w `docs/03:27`, `docs/07:44` vs Low wg D49) | `docs/11:70` (D49 dotyczy bramki 3) | (a) rozszerzyć D49 na tor A (Low); (b) zostawić Medium dla toru A (A16 Medium 21,7 FPS — tylko budżet ciężarówki, nie FPS); (c) Medium mierzone na S24+ |
| W8 | Decyzje otwarte od 9.11 | `GATE-1.md:93` (kierownica 270° vs 900°), `GATE-2.md:70` (lusterka: okienka vs rozglądanie) | wybór wariantu lub odłożenie do Etapu 5 (HUD, D52 `docs/11:73`) |
| W9 | Rozmiar świata w APK (D24 ≤ 110 MB) | `docs/11:45`; APK `edb5524993` 222,9 MB (`HANDOVER.md:89`), udział świata niezmierzony od `docs/PERFORMANCE_BUDGETS.md:159` (R30) | decyzja dopiero po pomiarze (komenda: APK `-noWorld` jak w `PERFORMANCE_BUDGETS.md:182`); jeśli > 110 MB: (a) podnieść limit, (b) PAD/Addressables (`:191`), (c) cięcia z `:162-164` |
| W10 | Brak zapasu GPU na A16 Low wobec dalszego wzrostu świata | `GATE-3.md:38`, D50 (`docs/11:71`: bez obniżania skali do 70 %) | (a) utrzymać D50, kolejna runda optymalizacji przed Etapem 4/5; (b) dopuścić skalę < 0,75 na Low (`docs/PERFORMANCE_BUDGETS.md:130`: 0,70 = −2,0 ms GPU) |

---

## 9. Spójność liczb między dokumentami

Skróty: `0046…`, `0062…`, `0177…`, `0195…` = `docs/adr/<nr>-*.md`; `GATE12-PHONE…` = `docs/reports/GATE12-PHONE-2026-11-14-A16.md`; `REVIEW-…-gate3-phone.md` = `docs/reports/REVIEW-2026-11-14-s20-gate3-phone.md`; `DEVICE-RUN…` = `docs/reports/device/DEVICE-RUN-2026-11-09.md`; pozostałe pliki bez katalogu leżą w `docs/` lub `docs/reports/`.

| # | Wartość A (plik:linia) | Wartość B (plik:linia) | Komentarz — co wygląda na aktualne |
|---|---|---|---|
| R1 | Boot A16: „❌ zablokowany telefon” (`GATE-0.md:23`); „Not measured yet” (`PERFORMANCE_BUDGETS.md:43`); „Blocked … PIN” (`STATUS.md:10`) | A16 Boot Medium 30,01 FPS, p95 33,47, p99 33,57 ms, PSS ~289 MB (`device/DEVICE-RUN-2026-11-09.md:7`); tag `v0.0-gate0` „FPS measured” | B aktualne (APK `-dirty`, `DEVICE-RUN…:14`); GATE-0/PB/STATUS do poprawy |
| R2 | DrivingLab A16 z autopilotem „not measured — phone locked” (`PERFORMANCE_BUDGETS.md:27`, `:40`) | Medium 30,01 FPS, PSS 333 MB (`DEVICE-RUN…:8-9`); Low 30,0 FPS, PSS 385–412 MB (`GATE12-PHONE…:9-13`) | B aktualne (s20, czysty APK) |
| R3 | Bramka 1: „SZKIC — czeka na telefon”, 0–80 telefon „❌ brak” (`GATE-1.md:6`, `:25`) | 0–80 ×3 PASS na A16 (`GATE-1.md:95-101`, `GATE12-PHONE…:15-17`, `HANDOVER.md:60`) | B aktualne; werdykt do decyzji właściciela (W4) |
| R4 | Bramka 2: „SZKIC”, „❌ telefon” (`GATE-2.md:6`, `:17`) | s080 pusty/40 t PASS (`GATE-2.md:72-79`) | B aktualne |
| R5 | „S24+ High na końcowym APK nie zmierzony” (`GATE-3.md:22`, `:95`) | S24+ High/30 G3-A/B zmierzone (`GATE-3.md:117-122`) | B aktualne |
| R6 | „Na main nie ma jeszcze świeżych kolekcji PSO” (`GATE-3.md:54-55`, `:94`) | PSO odświeżone `77cfd94bf` (`HANDOVER.md:60`) | B aktualne |
| R7 | 0–80 solo 13,60 s runner (`GATE-1.md:49`); 13.8 s (`PHYSICS_VALIDATION.md:97`, run `stage2-final`) | edytor 13,67 (`0195…:47`); telefon 13,66 (`GATE12-PHONE…:11`) | 13,60/13,67/13,66 spójne (< 0,5 %); `PHYSICS_VALIDATION.md:97` historyczne |
| R8 | 0–80 40 t 47,52 s runner (`GATE-2.md:33`); 46.2 s (`PHYSICS_VALIDATION.md:97`) | edytor 47,80 (`0195…:49`); telefon 47,79 (`GATE12-PHONE…:9`) | PV:97 historyczne (−3 %); pozostałe spójne |
| R9 | 80→0 solo 34,69 m `brake_80_0_dry` (`GATE-1.md:52`); 34.9 m (`PHYSICS_VALIDATION.md:101`) | 35,69 m runner `straight_0_80_0` (`0195…:35`), edytor 35,62 (`:47`), telefon 35,85 (`GATE12-PHONE…:11`) | różne scenariusze (prosta: hamowanie od 80,6 km/h, `0195…:35`); różnica ~1 m (3 %), oba w paśmie 32–55 m; w raportach podawać nazwę scenariusza |
| R10 | 80→0 pusty 38,79 m (`GATE-2.md:35`); 38,9 Unity / 39,0 symulator (`GATE-2-draft.md:47`); 39.0 (`PHYSICS_VALIDATION.md:101`) | 39,49 runner prosta (`0195…:36`), edytor 39,45 (`:48`), telefon 39,67 (`GATE12-PHONE…:10`) | jak R9 — inny scenariusz; telefon = edytor (+0,6 %) |
| R11 | 80→0 40 t 40,80 m (`GATE-2.md:35`); 40,6/40,5 (`GATE-2-draft.md:48`); 40.5 (`PHYSICS_VALIDATION.md:101`); test oczekuje 40,5 ±10 % (`game/Assets/_Project/Tests/PlayMode/CombinationLabTests.cs:250`) | 40,52 runner (`0195…:37`), edytor 40,78 (`:49`), telefon 40,72 (`GATE12-PHONE…:9`) | wszystkie w ±1 %; wartość odniesienia w teście z przebiegu historycznego |
| R12 | granica 80→0 „SOURCED: UN R13 zał. 4” (`GATE-2.md:35`), „SOURCED” (`0195…:39`) | „R13 N3 type-0 figures UNVERIFIED” (`PHYSICS_VALIDATION.md:101`) | sprzeczność statusu źródła — sprawdzić, czy ktoś otworzył R13 zał. 4 (PV:101 starsze) |
| R13 | runner 132 scenariusze / 750 kontroli (`GATE-1.md:21`, `:36`) | 107 / 550 (`PHYSICS_VALIDATION.md:289`), 98 / 482 (`:245`) | A aktualne; PV zawiera stany historyczne bez sumy bieżącej |
| R14 | `dotnet test` 266/266 (`GATE-1.md:35`) | 274/274 z `StraightRunTests` (`0195…:41`, `HANDOVER.md:38`) | B aktualne (po 0195); GATE-1 do aktualizacji |
| R15 | EditMode 532/535, 2 fail (`GATE-1.md:37`, `GATE-2.md:25`) | 580/581, 0 fail (`HANDOVER.md:56`, `:88`) | B aktualne |
| R16 | „Not run in Unity or on the phone” (`PHYSICS_VALIDATION.md:314`) | przebiegi telefonu zestawu (`GATE-2.md:72-79`) | B aktualne; PV §7 nieaktualne |
| R17 | §6.10 cofanie pod rampę „not covered by the runner” (`PHYSICS_VALIDATION.md:316`) | `reverse_dock_s_maneuver_comb@laden40` w runnerze, przegub 91,7° (`GATE-2.md:43`) | B aktualne |
| R18 | p95 ≤ 33 ms (Samsung A), ≤ 16,6 ms (High) (`06_GRAFIKA…:53`) | p95 ≤ 34,0 ms, ≤ 17,0 ms (`PERFORMANCE_BUDGETS.md:11-13`) | skrypty bramek używają PB (`GATE-3.md:35`); docs/06 to „hipotezy startowe” (`:48`) |
| R19 | draw calls ≤ 300–400, trójkąty ≤ 400–600 tys. (`06_GRAFIKA…:54-55`) | Low 250 / Medium 350 draws, 350 k / 550 k tris (`PERFORMANCE_BUDGETS.md:52-53`) | PB bardziej szczegółowe; uzgodnić |
| R20 | Ultra: 30 FPS (`06_GRAFIKA…:52`) | S24+ High–Ultra 60 FPS (`PERFORMANCE_BUDGETS.md:13`) | do decyzji razem z W2 |
| R21 | A16 Medium dla bramki 3 i toru A (`03_ETAPY…:27`, `:31`; `07_CIEZAROWKA_3D.md:44`) | A16 oficjalnie Low (D49, `11_DECYZJE…:70`; `DEVICE_MATRIX.md:5`) | B aktualne dla bramki 3; tor A — W7 |
| R22 | A16 Medium „DK8 forest 27 FPS” (`DEVICE_MATRIX.md:5`; `PERFORMANCE_BUDGETS.md:83` 27,0 FPS) | A16 Medium 21,7 FPS (D49, `11_DECYZJE…:70`, ADR 0106) | różne widoki i daty; B (G3, 11.11) właściwe dla bramki |
| R23 | PSS A16 G3-A: 700,7 MB (10.11, `GATE-3-draft.md:94`) → 880,2 (13.11, `GATE-3.md:32`) | 917,5 (s20, `GATE-3.md:113`), 900,8 (`:127`); limit 1000 MB (`PERFORMANCE_BUDGETS.md:12`) | trend, nie sprzeczność: zapas ~8 % |
| R24 | GPU p95 A16 G3-A: 25,5 ms (10.11, `GATE-3-draft.md:94`) | 34,15 (13.11, `GATE-3.md:32`), 34,5 (s20, `:113`) | trend; budżet klatki 33,3 ms przekroczony przez GPU p95 |
| R25 | S24+ High GPU p50 14,8 ms (60 FPS, `fefd804`, `0046…:10`) | 23,0 / 22,5 ms (limit 30 FPS, s20, `GATE-3.md:120-121`) | różne buildy/świat i limit; wniosek „High/60 nieosiągalne” (`GATE-3.md:122`) z pomiaru przy 30 FPS — UNVERIFIED do pomiaru `-Fps 60` (W2) |
| R26 | ADR 0195 „kandydat … nie scalone” (`0195…:3`); ADR 0177 „propozycja” (`0177…:3`); ADR 0046/0062 „proposed … UNVERIFIED” (`0046…:3`, `0062…:3`) | 0195 SCALONE `ea6fdf840` (`HANDOVER.md:38`); 0177 „scalone w s18” (`GATE-3.md:51`) | B aktualne; statusy ADR do aktualizacji |
| R27 | „A7–A8 … później” (`plan/TRACK-A.md:16`) | raport A7 (`visual/truck-A7/README.md:1`), pomiar A7 (`PERFORMANCE_BUDGETS.md:88-98`), katalogi `truck-A8`, `trailer-curtainsider` | B aktualne |
| R28 | `import-region.ps1 … [-SkipCopy]` (`CLAUDE.md:39`) | brak parametru `-SkipCopy` (`scripts/import-region.ps1:24-29`) | B (skrypt) aktualne; CLAUDE.md do poprawy |
| R29 | walidator: error 56, na trasie G3 56 (`WORLD-VALIDATOR-2026-11-13-mistral.md:9`) | error 61, na trasie 61 (`:67`) | A aktualne (korekta r6, `:8-9`); B to liczby z PR |
| R30 | APK 122,0 MB, udział świata ≈ 71 MB (`PERFORMANCE_BUDGETS.md:158-159`); limit świata ≤ 110 MB (D24, `11_DECYZJE…:45`) | APK 219,1 MB (`HANDOVER.md:52`), 222,9 MB (`:89`) | udział świata w obecnym APK niezmierzony (W9) |
| R31 | pamięć siatek świata ≈ 88 MB Low / ≈ 205 MB High (`PERFORMANCE_BUDGETS.md:156`) | „import OK: Low 123,0 MB / High 265,8 MB” (`HANDOVER.md:50`) | prawdopodobnie inna miara (rozmiar importu?) — do wyjaśnienia przez lidera |
| R32 | „Target 30 FPS … WORKING_VALUE until measured”, „once Stage 0 measures” (`DEVICE_MATRIX.md:11`) | 30 FPS trzymane na A16 w każdym przebiegu bramek (`GATE-3.md:113-114`, `GATE12-PHONE…:9-13`) | B aktualne |

Liczba wierszy: **32** (30 rozbieżności lub nieaktualnych wpisów + 2 trendy R23, R24).

Nie znaleziono rozbieżności (sprawdzone): p95 D57 33,4 ms (`11_DECYZJE…:78`) vs 33,45 (`GATE-3.md:32-33`) — zaokrąglenie; klatki > 40 ms przebiegów D57 14/14 (`GATE-3.md:41`) = `0177…:39` = `HANDOVER.md:116`; liczby s20 A16 i S24+ w `GATE-3.md:113-121` = `HANDOVER.md:61-65` = `REVIEW-…-gate3-phone.md:16`; liczby telefonu w `GATE-1.md:99-101` = `GATE12-PHONE…:9-13` (zaokrąglenia); `VehicleLabTests` 7/7 (`GATE-2.md:51`) = 7 przypadków w pliku testu.
