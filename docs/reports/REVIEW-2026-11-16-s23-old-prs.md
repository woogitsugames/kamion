# Przegląd starych otwartych PR — s23, 2026-11-16 (agent pr-triage-s23, bez Unity)

Main w chwili przeglądu: `origin/main` @ `eebb9813c`. Próbne scalenia: `git merge-tree --write-tree origin/main <PR>`.
Testy uruchomione na drzewie po próbnym scaleniu (commit-tree w worktree `.claude/worktrees/pr-triage-s23`, odłączony HEAD).
.NET: SDK 10.0.403 z `%LOCALAPPDATA%\Microsoft\dotnet` + `DOTNET_ROLL_FORWARD=Major` (w `Program Files\dotnet` nie ma SDK, tylko runtime).
Nic nie scalono, nie zamknięto i nie skomentowano.

## Podsumowanie

| PR | gałąź @ sha | za main | merge-tree | zastąpiony? | testy bez Unity (po scaleniu) | Google / marki | Rekomendacja |
|---|---|---|---|---|---|---|---|
| #79 | `lights-0197` @ `ad93ea1ff` | 1409 | czysto | nie (ADR 0197, `LampPhotometry.cs` brak w main) | `dotnet test tools/lamp-check` **186/186** | 0 / 0 | **POPRAW** (weryfikacja Unity, potem SCAL) |
| #92 | `research/mistral-p16-truck-lamps-fix-s21` @ `fb68478b2` | 578 | czysto | nie (zastępuje zamknięty #55) | — (research) | tylko deklaracje „bez Google”; marki tylko na kadrach referencyjnych | **SCAL** (z jawną luką pkt 4 = UNVERIFIED) |
| #100 | `research/codex-refs-s21` @ `2ff91ed8b` | 1164 | **konflikt** `docs/LICENSES.md` | nie | — (research) | „Google” tylko jako „nie użyto”; ~1960 wzmianek marek w tekstach research | **POPRAW** (WIP wstrzymany; zostawić otwarty) |
| #106 | `seams-0224` @ `eeb3878e6` | 1165 | **konflikt** `overrides.yaml` tykocin, `STATUS.md` | **tak — #143 `seam-taper-0275`** | — | 0 / 0 | **ZAMKNIJ** po scaleniu #143 (world2-s23) |
| #113 | `jackknife-0228` @ `a84ad5e14` | 641 | czysto | nie | `dotnet test tools/physics-runner/Tests` **328/329** — FAIL golden `brake_80_0_dry_abs_comb@laden40` (main 9/9 golden zielone) | 0 / 0 | **POPRAW** |
| #116 | `g3-poses-0246` @ `08d93731a` | 578 | **konflikt** `docs/adr/README.md` | nie | dotnet `tests/g3poses` **17/17**; pytest `tests/gate3/test_g3_poses.py` **11 pass / 2 FAIL / 6 skip** (także na samej głowie PR) | 0 / 0 | **POPRAW** (lekko) |

## #79 lights-0197 (ADR 0197) — POPRAW, potem SCAL

- **Co zmienia:** limiter odcienia 0178 z poziomem odniesienia (stop:pozycyjne 15,4:1, R148 ≥ 5:1), osobne komory TAIL/STOP naczepy
  (eksportery Blendera + `TruckLights`, tekstura stanu 32×1), bursztyn (1; 0,22; 0) na granicy gamutu R48, `_PlateIllum` 0,006
  (tablica ≥ 2,5 cd/m²). Liczby w `Vehicle/Runtime/LampPhotometry.cs` (bez UnityEngine) + `tools/lamp-check` (19 plików).
- **Kolizje:** merge-tree czysto. Main zmienił od bazy te same pliki: `TruckAssetBuilder.cs`, `a6_export.py`, ADR 0178/0181
  (commity brand-neutral f9101ad00/f32b75af3, statusy ADR ee51223e9). Scalenie tekstowe czyste, ale przy integracji sprawdzić,
  że nazwy obiektów/komór lamp w eksporterze nie wróciły do starych (brand sweep).
- **Testy:** `dotnet test tools/lamp-check` 186/186 na drzewie po scaleniu.
- **Do zrobienia (z PR, nadal otwarte):** (1) eksport FBX naczepy `trailer_export.py -- --no-renders`; (2) EditMode
  `LampRegulationTests`, `TruckRegulationLampTests.Trailer_TailAndStopChambers_HaveSeparateLightGroups`, `TruckLampEncodingTests`
  (`pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64`); (3) rendery kontrolne/zrzut z playera Windows nocą
  (pętla visual-qa). Autor sam oznaczył „Gotowe: NIE” do czasu tych kroków.

## #92 P16 M59-FIX (research lamp) — SCAL (katalog), luka jawna

- **Co zmienia:** tylko `research/mistral/p16-truck-lamps/` (17 plików, 12 JPG ≤ 1280 px) + 1 wiersz `docs/LICENSES.md`.
- **Stan FIX r2** (recenzja `REVIEW-2026-11-15-s21-cloudD-92-…`): pkt 1 (kolumna `wartość` z obrazu) — sprawdzone wyrywkowo
  P16-201 i P16-206: zgodne z opisem kadru („nie gładki”, kształt L, UNVERIFIED tam gdzie trzeba); pkt 2 (75 cd warunkowo,
  README l. 53) ✓; pkt 3 (§9) ✓; pkt 5 (gamut R48) ✓. **Pkt 4 (≥ 15 zbliżeń ECE, ≥ 5 lampek tablicy) NIESPEŁNIONY**, ale
  uczciwie oznaczony UNVERIFIED w STATUS/README.
- **Kolizje:** czysto (gałąź ma merge main z 16.11). Licencje: wpis w LICENSES.md (Commons CC0/CC BY/BY-SA).
- **Rekomendacja:** SCAL — wartość już jest (fotometria, errata, przeklasyfikowane kadry), a brakujące kadry to osobne zlecenie
  (część pokrywa #100 `01-lampy`). Jeśli lider woli kryterium 4 jako twarde: POPRAW (nowe kadry Commons/Openverse/Panoramax).

## #100 codex-refs-s21 — POPRAW (WIP, zostawić otwarty)

- **Co zmienia:** 1449 plików w `research/codex-refs-s21/` (01-lampy 357, 02-brud 426, 03-knyszyn 165, 04-dk65 141, 05-kolej38 97,
  06-region-ring 146, 07-dojlidy 107), 99 rastrów ≈ 14,4 MB. Codex wstrzymany (limit tygodniowy, HANDOVER 16.11 09:2x).
- **Kolizje:** konflikt `docs/LICENSES.md` (main ma już wpis s23 „codex-refs #100”, 9f129a637) — przy integracji wziąć wersję main
  i dopisać tylko brakujące wiersze.
- **Licencje:** zdjęcia all-rights-reserved opisane jako „link-only, 0 pobrań” (np. zamekwtykocinie.pl). Google tylko w zdaniach
  „nie użyto”. Marki (Scania/Renault/Actros itd.) w tekstach research — dopuszczalne jako materiał badawczy, **nie do gry**
  (HANDOVER 15.11 23:3x).
- **Do zrobienia przed scaleniem:** dokończyć lub uciąć zakres (README głównego katalogu „co gotowe / co nie”), audyt licencji
  każdego z 99 rastrów względem manifestu (żaden „link-only” nie może mieć pliku), rozwiązać konflikt LICENSES. Integrować
  samym katalogiem (`git checkout <gałąź> -- research/codex-refs-s21`), nie całą gałęzią.

## #106 seams-0224 (ADR 0224) — ZAMKNIJ po scaleniu #143

- **Zastąpiony:** #143 `seam-taper-0275` (OPEN) zawiera ADR 0224, `tools/worldgen/qa/seams.py` (+206/−86 względem #106),
  `tests/gis/test_seams_0224.py` (rozszerzony) oraz ADR 0275, który wprost mówi: „`qa/seams.py` (z PR #106) w gicie” i
  „override `seam-knyszyn-s-field-road-98071886` z #106 **nie** został przeniesiony (szerokość łączy przejście)”.
  #143 jest już w `origin/world2-s23` (sprawdzone `merge-base --is-ancestor`); tam tykocin dostaje regułę
  `seam-field-road-98071886-unlit` (roads_qa.json).
- **#115** (pierścień 0231) nie dotyczy szwów 0224 — nie zastępuje #106 sam; robi to #143.
- **Kolizje:** konflikty `overrides.yaml` tykocin i `STATUS.md` — kolejny powód, żeby nie scalać.
- **Rekomendacja:** ZAMKNIJ jako zastąpiony, gdy world2-s23 (z #143) wejdzie na main. Do tego czasu bez działań.

## #113 jackknife-0228 (ADR 0228) — POPRAW

- **Co zmienia:** kontakt kabina–naczepa (`CouplingContact` w `FifthWheel`/`CombinationModel`), `bodyBoxes` w JSON ciągnika i naczepy
  jako jedno źródło geometrii, histereza odbojnika (Hunt–Crossley), nowe scenariusze, przepisana złota telemetria
  `brake_80_0_dry_abs_comb@laden40`, dowody `artifacts/jackknife-0228/` (108 plików).
- **Głowa bez zmian od integracji int-h3** (`a84ad5e14`) → znany FIX nadal otwarty: **`KerbStrikeParityTests` (PlayMode) 5 faili**,
  stałe referencyjne `KerbStrikeParityTests.cs:270-277` nieaktualne (raport `INTEGRATION-2026-11-16-int-h3-s23.md` §„#113 → FIX”).
- **Nowy problem (ten przegląd):** main od bazy #113 zmienił geometrię naczepy — king pin → środek tridemu 7,63 m (D79;
  bec798465, 5fe05662c, b0a59d936, 664b9c18f: `TrailerModel.cs`, `CombinationModel.cs`, `curtainsider_tridem_13_6.trailer.json`,
  `brake_80_0_dry_abs_comb.json`). Scalenie tekstowe jest czyste, ale **`GoldenTelemetry_Matches(brake_80_0_dry_abs_comb@laden40)`
  pada po scaleniu** (a_long max |diff| 2,04; kingpin_fz 1,7e4 N, 32,5 % odstających; front_L_fz, rear_L_fz). Na main ten sam
  test zielony (9/9 golden), więc złota telemetria z #113 jest nagrana na starej geometrii. Pozostałe 328 testów zielone.
- **Lista POPRAW:** (1) merge main do gałęzi; sprawdzić, że `bodyBoxes` naczepy (przód 2,029 m od king pina) zgadza się z nowym
  JSON-em 7,63 m (ten sam plik edytowały obie strony); (2) przegrać złotą telemetrię `brake_80_0_dry_abs_comb@laden40` na
  drzewie po scaleniu i opisać przyczynę w ADR 0228; (3) przeliczyć stałe `KerbStrikeParityTests` z runnera (bez poszerzania
  tolerancji; pochylenie 1,38° zweryfikować na runnerze); (4) `dotnet test tools/physics-runner/Tests` + pełny runner +
  PlayMode `CombinationLabTests|KerbStrikeParityTests` Win64; (5) potem feel test B-075.

## #116 g3-poses-0246 (ADR 0246) — POPRAW (lekko)

- **Co zmienia:** 42 pozy par zdjęciowych G3 (`G3PoseRunner/Capture/Set/Args`, `CaptureCameraTier`), `scripts/g3-poses.ps1` +
  `g3_poses.py`, dane `g3_poses.json` (region i Resources), testy. Od triage s23 r1 doszedł **tryb playera Windows `-Exe`**
  (08d93731a), więc wcześniejszy FIX „tylko adb” jest zrobiony — PR nie zależy już od telefonu (D73).
- **Kolizje:** konflikt tylko w `docs/adr/README.md` (indeks — wziąć wersję main i wygenerować indeks ponownie).
- **Testy:** dotnet `tests/g3poses` 17/17. pytest `tests/gate3/test_g3_poses.py`: 2 FAIL
  (`test_both_copies_are_current_and_identical`, `test_every_pose_equals_its_photo_pair_camera`) — `g3_poses.py check` mówi:
  oba `g3_poses.json` „stale” (sha listy kamer par zdjęciowych 5317a18… ≠ 7e8e6b6…). Pada też na samej głowie PR — dane kamer
  zmieniły się po regeneracjach C.
- **Lista POPRAW:** (1) merge main; (2) `python scripts/g3_poses.py export --region bialystok-industrial-c` i commit obu kopii;
  (3) pytest zielony; (4) EditMode `G3PoseTests` + próba `scripts/g3-poses.ps1 -Exe … -Only 1-2` na buildzie Windows;
  (5) P2 z recenzji s22 (`CaptureCameraTier.Apply` woła pełne `QualityProfileApplier.Apply`) — poprawić komentarz lub wydzielić `ApplyCamera`.

## Komendy odtworzenia

```
git fetch origin pull/<N>/head:refs/triage/pr<N>
git merge-tree --write-tree --name-only origin/main refs/triage/pr<N>
# testy na drzewie po scaleniu (DOTNET_ROOT=%LOCALAPPDATA%\Microsoft\dotnet, DOTNET_ROLL_FORWARD=Major):
dotnet test tools/lamp-check                       # #79
dotnet test tools/physics-runner/Tests             # #113
dotnet test tests/g3poses; uv run --no-project --with pytest python -m pytest tests/gate3/test_g3_poses.py -q   # #116
```
