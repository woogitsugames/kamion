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
