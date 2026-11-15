## truckdata-0201 (ADR 0201) — dane ciężarówki z R3
**Co zmienione:** opona: `radius` (geometria/kontakt/hardpoint, 0,51/0,515 m) rozdzielony od `rollingRadius` 0,524 m (ω↔v, moment, opór toczenia, AMT, dźwięk wału; DERIVED z obwodów toczenia R3-108…118); konsumenci sprawdzeni. Marki usunięte z danych/kodu (`amt12_od_class`, GUID zachowany; grep = 0). Errata: docs/04 315/80, VRD/PV hamowanie awaryjne N /115 z 40 km/h, resztkowe 52,4 m. 4 goldeny nagrane ponownie (przyczyna 4/274 FAIL: nagrane z r 0,51). Naciski: sprawdzone vs karta (64/36 vs 73/27 %), NIE zmienione — eksperyment obalił 4/135 scenariuszy odczucia → follow-up. ADR 0201, VRD, live.
**Testy uruchomione:** `dotnet test tools/physics-runner/PhysicsRunner.sln` → 274/274 PASS. Runner main (5724a161b) i gałąź → 135/135 scenariuszy, 789 kontroli PASS. Wykresy `artifacts/truckdata-0201/plots/` obejrzane.
| | main runner | gałąź | Δ | bramka A16 |
|---|---|---|---|---|
| solo 0–80 / 80→0 | 13,60 s / 35,69 m | 13,58 s / 35,77 m | −0,15 % / +0,22 % | 13,66 / 35,85 |
| 40 t 0–80 / 80→0 | 47,52 s / 40,52 m | 47,54 s / 41,02 m | +0,04 % / +1,23 % | 47,79 / 40,72 |
**NIEuruchomione:** EditMode, PlayMode, build APK, telefon (chmura bez Unity/adb); pytest `tests/physics` (scenariusze JSON bez zmian w tej rundzie).
**Komendy dla lidera (PowerShell):**
`pwsh scripts/test.ps1 -Platform EditMode` · `pwsh scripts/test.ps1 -Platform PlayMode` (m.in. `StraightRunAutopilotTests`, `DrivelineSfxTests`)
`pwsh scripts/build-android.ps1` → `pwsh scripts/gate12-phone.ps1 -Apk artifacts/apk/kamion-<ver>-<sha>.apk -UseExistingLock -Only s080_solo_1,s080_solo_2,s080_solo_3,s080_empty,s080_40t`
`$env:DOTNET_ROOT='C:\Users\matma\AppData\Local\Microsoft\dotnet'; & $env:DOTNET_ROOT\dotnet.exe test tools/physics-runner/PhysicsRunner.sln`
Po scaleniu: wpis 0201 w `docs/adr/README.md` (plik wspólny — nie ruszany).
**Otwarte:** rozkład mas ciągnika 73/27 % (strojenie zawieszenia/kabiny + test odczucia właściciela); siodło 0,68 vs 0,375 m (R3-019); bramki 1–2 na telefonie po scaleniu.
**Gotowe do scalenia po weryfikacji lidera: TAK** (po zielonym EditMode/PlayMode).
