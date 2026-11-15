# VERIFY 2026-11-15 — PR #90 `axleloads-tuning-0201b` (ADR 0201b)

Weryfikacja lokalna (Windows, Unity 6000.3.28f1) w worktree `verify-cloud-b`. Baza: origin/main `657b85837`; PR: `60ed99f9d`, scalony lokalnie jako `99b75be1c` (bez konfliktów). Bez telefonu.

## 1. Wynik: DONE — werdykt **SCAL** (warunki niżej)

## 2. Ustalenia
1. `dotnet test tools/physics-runner/PhysicsRunner.sln -c Release`: przed **274/274**, po **277/277** (3 nowe `F2CouplingEnergyTests`). Zgodne z PR.
2. Runner (`dotnet run -c Release --project tools/physics-runner/Runner`): przed i po **135/135 PASS (789 kontroli)**. Żadna tolerancja nie zmieniona (porównanie zakresów 898 wierszy przed/po: 0 różnic). 548 wartości zmienionych (zmiana mas i zawieszenia), 0 FAIL.
3. Liczby bramek 1–2 w runnerze (`straight_0_80_0`), zgodne z PR co do cyfry:

| wariant | metryka | bramka A16 (telefon, main) | runner przed (main) | runner po (#90) | zmiana | tolerancja scenariusza |
|---|---|---|---|---|---|---|
| solo | 0–80 | 13,66 s | 13,580 s | **14,055 s** | +3,5 % | 12–32 s |
| solo | 80→0 | 35,85 m | 35,774 m | **35,387 m** | −1,1 % | 32–55 m |
| solo | MFDD | — | 7,483 | 7,734 m/s² | +3,4 % | 5–8 |
| pusty zestaw | 0–80 | — | 20,531 s | 21,137 s | +3,0 % | 20–55 s |
| pusty zestaw | 80→0 | — | 39,592 m | 39,991 m | +1,0 % | 35–61,2 m |
| 40 t | 0–80 | 47,79 s | 47,540 s | **47,575 s** | +0,07 % | 40–95 s |
| 40 t | 80→0 | 40,72 m | 41,020 m | **41,200 m** | +0,44 % | 35–61,2 m |

   Wartości „bramka A16” to pomiar z telefonu na APK z main (ADR 0201); po #90 nie były mierzone na telefonie.
4. Powtarzalność 0–80 w runnerze przed: [13,580 ×3], odchyłka 0,00 %.
5. EditMode (`pwsh scripts/test.ps1 -Platform EditMode`, slot unity): **603 testy: 600 passed, 2 failed, 1 skipped**. Oba FAIL to `CarPaintMaterialTests.DepositionChannel_RequiresScopedYardOptInOrExistingCar` (`tractor_paint_blue`, `car_paint_blue`) — znane na main (HANDOVER: verify-a 597/600 z tymi samymi dwoma; `docs/reports/GATE-1.md` l. 40), materiał lakieru, nie fizyka. Żaden test fizyki nie padł.
6. Kompilacja Unity po scaleniu: bez błędów (testy wystartowały i się wykonały).

## 3. Zmienione pliki
Żadnych w PR. Raport: ten plik.

## 4. Dowody (`C:\Users\matma\Documents\Claude\kamion\artifacts\verify-cloud-b\pr90\`)
- `before.log`, `before/summary.md` (+ CSV) — runner na main; `after.log`, `after/summary.md` — runner po #90.
- `dotnet-test-after.log` — 277/277; `..\step01-baseline.log` — 274/274 na main.
- `editmode-20261115-154754.xml`, `..\step03-pr90-editmode.log`.

## 5. Napisane / zbudowane / uruchomione / zmierzone
- Uruchomione i zmierzone: dotnet test, runner przed/po, EditMode.
- NIE uruchomione: PlayMode, build APK, `gate12-phone.ps1` (telefon zakazany w tym zadaniu), feel test właściciela. Wykresów goldenów nie oglądałem.

## 6. Ryzyka i znane braki
- Solo 0–80 +3,5 % (zaakceptowane przez właściciela wg PR). Hamowanie 40 t +0,44 % (41,02→41,20 m) i pusty zestaw 0–80 +3,0 % (21,14 s przy dolnej granicy 20 s) nie są wymienione w akceptacji — w tolerancjach scenariuszy, ale bramka telefonu 40,72 m przesunie się o podobny ułamek.
- Cienkie zapasy po zmianie: `park_12pct_up_comb@empty trailer_creep_m` 4,97 mm / 5 mm (było 4,72); `kingpin_load_vs_static` 1,023 / 1,03; `downhill_7pct_full_lever@laden40` 70,60 / 71 km/h.
- Bramka etapu wymaga ±3 % powtarzalności 0–80 na telefonie — do zmierzenia `gate12-phone.ps1`.

## 7. Następny krok (lider)
Scalić; potem `pwsh scripts/test.ps1 -Platform PlayMode`, `pwsh scripts/build-android.ps1`, `pwsh scripts/gate12-phone.ps1 -Apk … -Only s080_solo_1,s080_solo_2,s080_solo_3,s080_empty,s080_40t`, feel test.
