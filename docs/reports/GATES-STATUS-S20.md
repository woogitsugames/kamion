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
| 2.1 | „pełny pakiet walidacyjny `docs/04` §6 (pusty i 40 t)” | CZĘŚCIOWO | symulator 132/132, 750 kontroli; PlayMode `CombinationLabTests` 15/15 (`GATE-2.md:17`), szczegóły `:27-48`. Telefon: §6.3 i §6.5 — pusty 0–80 20,67 s / 80→0 39,67 m; 40 t 0–80 47,79 s / 80→0 40,72 m, MFDD 7,00, błąd siodła ≤ 0,17 mm, PASS (`GATE12-PHONE…:9-10`). §6.13 (floating origin) bez osobnego scenariusza (`GATE-2.md:51`); §6.10 cofanie pod rampę poza runnerem (`docs/PHYSICS_VALIDATION.md:315`) — w tabeli GATE-2 wiersz `reverse_dock_s_maneuver_comb` (`GATE-2.md:43`) |
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
