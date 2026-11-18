# STATUS night-truck-s24 (ADR 0297)

## 2026-11-18 22:5x baseline
- Worktree + Library (robocopy z win-build) + LOD0 kabiny; Truck/Trailer BuildBatch OK; build-lab Win64.
- Baseline (artifacts/night-truck-s24/base, base-lamps.txt, base-cab.txt): pozycyjne ciągnik High noc 54.7 R (stop 192.9, 14:1 lin),
  tablica naczepy 205 (max 254), pierścień obudowy 9.2 bez zmiany przy stopie; kabina noc High: niebo 12.0, deska 12.4, słupek A 17.7, droga 8.2.
- Przyczyny: tablica nie jest ograniczona wobec lamp (limiter tylko na lampach); brak poświaty (bloom wyłączony, lampy display-limited);
  noc kabiny = mnożnik lokalnego podbicia cieni (_CabShadowLift k=8) + jednolity panelGlow × albedo (jasna tapicerka słupka A);
  schodkowe cienie = CabInterior.shader bez wariantów _SHADOWS_SOFT (twarde 1 próbka niezależnie od tieru).
- NASTĘPNY KROK: implementacja (halo shader, plate shoulder, TailNits, spill zegarów, soft shadows w CabInterior), potem
  `pwsh -NoProfile -File artifacts/night-truck-s24/go.ps1 -Name after1 -Unity -Cmd '...assets.ps1; lamps.ps1 -Tag after1; cab.ps1 -Tag after1'`

## 23:1x after1 (pierwsza implementacja)
- TailNits 3800 (5,26:1), halo `Kamion/Truck Lamp Halo` (1 quad/emiter, 5 ciągnik + 10 naczepa), plate shoulder 0,55, cab soft shadows (PC), spill zegarów/nawigacji, lift nocą ×0,2, panelGlow 0,015.
- after1: pozycyjne 54,7 → 89,7 R; tablica 205 → 143; kabina noc: deska 12,4 → 5,7, słupek A 17,7 → 6,9 (niebo 12); cienie gładkie (crop). Halo miało ciemny pierścień (wycięcie rdzenia) → after2 bez wycięcia, K 0,25; spill słaby (powierzchnie współpłaszczyznowe z ekranami fizycznie ciemne).
- NASTĘPNY KROK: `pwsh -NoProfile -File artifacts/night-truck-s24/go.ps1 -Name after2 -Unity -Cmd 'pwsh artifacts/night-truck-s24/assets.ps1; ...lamps.ps1 -Tag after2; cab.ps1 -Tag after2; ab.ps1 -Tag after2'`

## 23:3x after2 → after3
- after2: pozycyjne 110,7 R (cel 110–150 ✓), stop 236, tablica 143 (< stop ✓), kabina noc deska 6,1 / słupek 7,1 / niebo 12.
- Błąd: halo tylko po lewej — normalne klastrów soczewek z eksportu skierowane do wnętrza lampy (9/10 +Z) → orientacja na zewnątrz od środka siatki (test).
- Spill fizyczny ≤ +7/255 (A/B rq_cabspill) → spillScale 4 (WORKING_VALUE, brakujące źródła: pierścienie zegarów, legendy, odbicia).
- Timing edytora GTX 1070: soft cab cab-driver 1,90 → 1,93 ms, Ultra 7,06 → 7,19; cab-dash 2,54 → 4,48 (podejrzany warm-up, powtórka w after3).
- NASTĘPNY KROK: czekać na after3 (`artifacts/night-truck-s24/after3.status`), zmierzyć, EditMode Win64, ADR 0297.

## 23:5x KONIEC (gotowe do review / scalenia)
- final: pozycyjne 54,7 → 110,7 R (High noc, z bliska), z dystansu 54,6 → 120,9; stop 236; tablica 205 → 143 (< stop); poświata obudowy wokół stopu 9 → 24 R (2 m) / 120 R (4 m); stop:pozycyjne 5,26:1 (regulamin, test).
- Kabina noc High: deska 12,4 → 6,1, słupek A 17,7 → 7,1, niebo 12 (kabina ciemniejsza od nieba); spill zegarów/nawigacji +1–7/255 (fizycznie lekki, ×4).
- Cienie kabiny PC: miękkie (warianty _SHADOWS_SOFT w CabInterior + gałąź telefonów), krawędź 10 → 22 px High; koszt w szumie edytora.
- Testy: EditMode Win64 1296/1393 (3 porażki jak na main), NightTruck0297Tests 6/6, LampRegulationTests 19/19, lamp-check 187/187.
- Dowody: artifacts/night-truck-s24/view (worktree + main). ADR 0297.
- NASTĘPNY KROK (lider): scal `night-truck-s24`, potem BuildBatch truck+trailer, build Windows i `pc-metrics.ps1` (czas GPU spill/soft w buildzie), zrzut z playera nocą, visual-critic.
