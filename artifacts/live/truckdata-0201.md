# truckdata-0201 (ADR 0201) — live
- 14.11: worktree + gałąź z main; baseline .NET testy 274/274; docs errata (docs/04 315/80, VRD S5 /115 40 km/h + S9, PV w.6 ≤ 52,4 m, scenariusz air_leak_rear_circuit max 52.4).
- 14.11: marki usunięte (amt12_od_class, GUID zachowany); rollingRadius 0,524 m rozdzielony od radius (kontakt) → 4/274 FAIL (goldeny).
- 15.11 R3 (chmura): baseline runnera na origin/main 5724a161b → `artifacts/truckdata-0201/before-main/summary.md`; gałąź → `after-r3/summary.md`; oba 135/135 PASS (789 kontroli).
- 15.11 R3: przyczyna 4 FAIL = goldeny nagrane z r 0,51 dla kinematyki (zmiany biegów +2,7 % prędkości, fazy ABS/blokady); nakładki obejrzane (`plots/`); 4 goldeny nagrane ponownie (tolerancje bez zmian) → .NET 274/274.
- 15.11 R3: konsumenci promienia sprawdzeni (kontakt/hardpoint/tyreFlatRadius = radius; moment/poślizg/opór/AMT/audio = rollingRadius). Naciski: solo 64/36 % vs karta 73/27 % (R3-013/014) — NIE zmienione; eksperyment przesunięcia mas obalił 4/135 scenariuszy odczucia (`exp-axleloads-n1/summary.md`) → follow-up. Grep marek = 0.
- 15.11 R3: tabela before/after w ADR 0201 (solo 0–80 13,60→13,58 s, 80→0 35,69→35,77 m; 40 t 47,52→47,54 s, 40,52→41,02 m). VRD zaktualizowane.
- NASTĘPNY KROK (lider, Windows): `pwsh scripts/test.ps1 -Platform EditMode`; `pwsh scripts/test.ps1 -Platform PlayMode`; `pwsh scripts/build-android.ps1`; `pwsh scripts/gate12-phone.ps1 -Apk <apk> -UseExistingLock -Only s080_solo_1,s080_solo_2,s080_solo_3,s080_empty,s080_40t`.
