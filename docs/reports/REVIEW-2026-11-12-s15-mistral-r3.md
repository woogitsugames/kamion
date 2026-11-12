# Recenzja i integracja Mistral — runda 3 (s15, 2026-11-12)

Gałąź integracyjna: `mistral-r3-int` (od `origin/main` 830698a90), worktree `.claude/worktrees/mistral-r3-int`.
Zadania: `docs/owner/MISTRAL-TASKS-3.md` (M16–M20) + zaległe M9. Wzór: `REVIEW-2026-11-12-s14-mistral-r2.md`.
Komentarze po polsku są na każdym PR (`gh pr comment`).

## Tabela PR

| PR | Zadanie | Gałąź | Werdykt | Poprawki lidera (osobne commity) |
|---|---|---|---|---|
| #16 | M16 oktawa `comb_estimate` | `mistral/16-audio-octave` | **SCAL** | — (konflikt add/add `test_engine_rpm.py` → wersja z PR) |
| #15 | M9 audyt znaków pionowych | `mistral/9-signs-pl` | **SCAL po drobnych poprawkach** | marker `unit`; usunięty pusty test LFS czytający całe pliki `generated`; literówka |
| #17 | M17 źródła fizyki (raport) | `mistral/17-physics-sources-2` | **SCAL po drobnych poprawkach** | „Uwagi lidera”: P5 i P10 — rekomendacje „wdrożyć” bez oparcia w źródłach → „zostawić/zmierzyć” |
| #18 | M19 `ExpectedFailureTests` | `mistral/19-expected-failures` | **SCAL** | konflikt: JSON scenariusza z main (bez checku przegubu usuniętego w s14), `expectedFailMetrics = [radius_error_m]` |
| #20 | M18 oznakowanie poziome (ISAP) | `mistral/18-markings-verify` | **SCAL po drobnych poprawkach** | dopisek: t.j. 2019 nie zawiera zmian 2021+; wyniki kontroli wyrywkowej |
| #19 | M20 HUD zero-alloc | `mistral/20-hud-zero-alloc` | **NIE** (niescalony) | — (merge na próbę, przerwany; dowody w `artifacts/mistral-r3-int/` repo lidera) |

## Kontrola zakazów

Żaden PR nie dotyka `Data/**/generated/**`, `*.glb`, `*_meta.json`, `game/ProjectSettings/**`, `game/Packages/**`,
`.gitattributes`, LFS. #19 zmienia `game/Assets/_Project/UI/Game.UI.asmdef` (dodaje `Unity.TextMeshPro`) — wg CLAUDE.md
asmdef zmienia tylko lider.

## Kontrola źródeł (wyrywkowo, 2026-11-12)

| Cytat | Źródło sprawdzone | Wynik |
|---|---|---|
| RA 1,24 dla typowego ciągnika z naczepą (#17 P2) | fhwa.dot.gov/policy/otps/truck/wusr/chap07.cfm | zgodne („Figure VII-4 shows… 1.24”, próg ≤ 2,0) |
| R13 par. 5.2.1.13.1 bez progu 6,5 bar (#17 P3) | EUR-Lex CELEX 42016X0218(01) | zgodne (wymóg funkcyjny; 650 kPa w 5.2.1.28.5) |
| ZF sprzęgła „above 3,500 Nm” (#17 P5) | zf.com/products/en/cv/products_65885.html | cytat zgodny, **wniosek „4000 Nm poza klasą” sprzeczny z cytatem** |
| Volvo I-Shift bieg startowy 1.–6. (#17 P10) | karta stpi.it.volvo.com (PDF, ENG v11) | cytat zgodny, **„przy 40 t 1.–2.” nie ma w źródle** |
| P-21a 0,24/0,39, P-21b 0,60/0,98 m (#20) | dziennikustaw.gov.pl/D2019000231102.pdf, str. Dz.U. 587 i Tab. 5.3 str. 589 | zgodne |
| P-10 szerokość ≤ 16,0 m (#20) | ten sam PDF, str. Dz.U. 567 | zgodne |
| Status Dz.U. 2019 poz. 2311 i nowelizacje (#15, #20) | api.sejm.gov.pl/eli/acts/DU/2019/2311 | zgodne („obowiązujący”, zm. 2021/438, 2021/2066, 2022/2377, 2026/132); **t.j. 2019 nie zawiera tych zmian** — błąd w #20 poprawiony dopiskiem |

## Uwagi szczegółowe

- **#16** `el_analyze.py:155-163` poprawne. Nowe testy `test_comb_octave.py` (30/46/60/90 Hz, brakująca podstawowa, szum)
  przechodzą także na starym kodzie — nie odróżniają poprawki; regresję łapie tylko `test_engine_rpm.py::…wav_roundtrip`
  (stary kod: comb_rpm 2980 vs 1500).
- **#15** test bez markera `unit` nie był w CI; `test_generated_sign_assets_not_lfs_pointers` czytał w całości każdy plik
  `generated` i niczego nie sprawdzał.
- **#18** gałąź oparta na starszym stanie — przywracała check `max_articulation_deg ≤ 6°` usunięty w s14; zachowano main.
  Test negatywny: dopisanie przechodzącej metryki → „naprawione? zdejmij expectedFail — metryki [lat_accel_ms2]”.
- **#19 (NIE)** — `UiFonts.cs:33` `TMP_FontAsset.CreateFontAsset` rzuca `NullReferenceException` (`TMP_FontAsset.cs:596`,
  `TMP_Settings` == null: w projekcie brak TMP Essential Resources; `Shader.Find("TextMeshPro/Mobile/Distance Field")` = null).
  `DrivingHud.Build()` buduje panel telemetrii i gyro bezwarunkowo (`DrivingHud.cs:322,372`), `DiagnosticsOverlay.cs:96` też →
  HUD i overlay przestałyby się budować. Dodatkowo: zmiana asmdef (tylko lider), `enableWordWrapping` obsolete (nowe ostrzeżenie),
  `Text`→`TextMeshProUGUI` zmienia wygląd (zadanie wymagało identycznego). Konflikt z main w `DrivingHud.cs` (wspólny throttling
  0,2 s z s14) rozwiązany na próbę — plik w `artifacts/mistral-r3-int/DrivingHud.resolved-pr19.cs`.

## Wyniki testów (gałąź `mistral-r3-int`)

| Zestaw | Wynik |
|---|---|
| audio `uv run --project tools/audio --with pytest pytest tools/audio/tests -q` | **46 passed** (stary `comb_estimate`: 45 passed, 1 failed) |
| `dotnet test tools/physics-runner/PhysicsRunner.sln -c Release` | **221/221** |
| Runner `dotnet run -c Release --project tools/physics-runner/Runner` | **112/112 scenariuszy, 589 checków** |
| gis `pytest tests/gis -q -m unit` | **72 passed, 2 xfailed (strict)** (nowe: 16 audytu znaków + 2 xfail oznakowania) |
| Unity PlayMode `HudTextAllocTests` (dodany przez lidera, merge #19 na próbę; licznik `GC.Alloc` przez `Profiling.Recorder`, 500 aktualizacji) | `TextBuffer` (format telemetrii PR #19): **0 GC.Alloc**; stara ścieżka `Text.text = "Gyro: " + x.ToString("F1")`: **1003 GC.Alloc**; `UiFonts.DefaultTmp`: **NullReferenceException** → 1/3 passed. `GC.GetAllocatedBytesForCurrentThread()` w edytorze Unity (Mono) zwracał 0 B także dla starej ścieżki — nie nadaje się jako dowód. |
| Unity EditMode (z #19 na próbę) | 416: 393 passed, 8 failed, 10 skipped — porażki środowiskowe świeżego worktree (brak zbudowanego prefabu ciężarówki/TRAKT: `TruckDoorCrownTests`×3, `MirrorPresentationTests`×2, `LightPostPolicyTests`×1; znane `CarPaintMaterialTests.DepositionChannel`×2), żadna w UI. Scalone PR-y nie zmieniają C# Unity. |

Pełnego `pytest tests/gis` nie uruchamiano: PR-y dodają wyłącznie testy `unit` (czyste stałe), bez zmian w generatorach.

## Osobne zadania wynikłe z recenzji

1. Audio: test oktawy, który pada na starym `comb_estimate` bez WAV (np. tłumione nieparzyste harmoniczne).
2. Znaki pionowe (M9): `SIGN_SIZE["square"]`/`["diamond"]` 0,80 → 0,60 m (Tab. 5.1), ośmiokąt B-20 = 0,80/cos(π/8)
   między narożnikami; klasa folii typ 2 dla A-7/B-2/B-20/D-6; weryfikacja U-4a i tabliczek T (zał. 4 / rozdz. 9).
   Wymaga regeneracji świata i visual QA.
3. Oznakowanie poziome (M18): `P11_SQUARE/P11_GAP` 0,40 → 0,50 m; `p21_hatch` 0,5/1,0 → 0,24/0,39 (≤ 70 km/h) i
   0,60/0,98 m — po decyzji właściciela, zdjąć xfail; łącznice WA ≤ 6 % (§ 62 ust. 2 PTB2022).
   Sprawdzić zmiany zał. 2 z Dz.U. 2021 poz. 2066 / 2022 poz. 2377 / 2026 poz. 132 (poza t.j. 2019).
4. Fizyka (M17): decyzja właściciela co do `maxLaunchGear` (4 vs 2) i `clutchMaxTorque` (4000 Nm) — źródła ich nie
   rozstrzygają; P8 strona Gillespie.
5. HUD zero-alloc (M20, ponownie): wybór lidera/właściciela — (a) import TMP Essential Resources jako kodu (generator,
   `docs/LICENSES.md`, shader TMP w buildzie, visual QA + telefon) albo (b) zostać przy `UnityEngine.UI.Text` z tablicami
   gotowych stringów (gyro ±90,0° co 0,1). Do wzięcia z #19 bez TMP: `9608e6a94` (tabela stringów obrotów), etykiety
   przycisków diagnostyki tylko przy zmianie, helpery `TextBuffer`, test `HudTextAllocTests` (`artifacts/mistral-r3-int/`).
