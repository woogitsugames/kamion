# STATUS — perf-low-r1 (ADR 0106, rendering-perf)

## 2026-11-11 12:25 — krok 1: diagnoza (start)
- Analiza gate3 A16 Low (APK 43bc53a769-dirty): G3-A 39 klatek > 40 ms po rozgrzewce, G3-B 32; prawie wszystkie to 50 ms (3 vsync)
  przy GPU 30–48 ms i CPU main 17–24 ms → piki p99 = GPU na granicy 33,3 ms, nie GC/streaming (świat w całości załadowany,
  logcat bez zdarzeń). Jeden krótki pakiet CPU 30–50 ms w G3-A t≈51 s (wiadukt Bieżeństwa).
- Edytor (buildings-r13 r3 Low stats): instancjonowane draws 380–720 przy 230–450 instancjach (≈1 instancja/draw: wiele prototypów×submesh).
- Uruchomiony skrypt ablacji telefonu `artifacts/perf-low-r1/phone-diag.ps1` (czeka na brak Unity i PHONE_RUN), uncapped G3-B:
  base / rq_ab mirrors / shadow 0 / msaa 1 / scale 0.6 / trees 0 / sky / a8 0 / base.
- NASTĘPNY KROK: `pwsh -NoProfile -File artifacts/perf-low-r1/phone-diag.ps1 -Apk C:\Users\matma\Documents\Claude\kamion\artifacts\apk\kamion-0.1.0-43bc53a769-dirty.apk -OutTag diag0 -Segment B -Uncapped -Runs "base0=;ab_mir=rq_ab=mirrors;shadow0=rq_shadow=0;msaa1=rq_msaa=1;scale06=rq_scale=0.6;trees0=rq_trees=0;sky=rq_clouds=-1 rq_haze=0;a8off=rq_a8=0;base1="` (jeśli przerwane), potem analiza `artifacts/perf-low-r1/diag0/*/frametimes.csv`.

## 12:50 — krok 1a: ablacja A16 (G3-B Low, uncapped, APK 43bc53a769-dirty) — `artifacts/perf-low-r1/diag0/summary.txt`
- base GPU p50 27,9/28,0 ms (cap 30: 30,0 → DVFS rozciąga tylko ~2 ms; GPU naprawdę ~28 ms). Start G3-B (s≈1232–1300) 34–36 ms.
- Δ GPU p50: lusterka −0,75…−1,25 (rq_ab), cienie off −0,9, MSAA 1× 0, skala 0,6 −4,8 (→ ~13 ms zależne od pikseli przy 0,75,
  ~15 ms stałe), drzewa off −2,4 (i p99 50→33,5), niebo/mgiełka 0, A8 0.
- Wniosek: ~11 ms niezależnych od rozdzielczości i niewyjaśnionych → geometria/draws świata, ciężarówka, HUD, blit.
- Dodane przełączniki diagnostyczne rq_lod/far/mask/props/hud i rq_ab lod|scale|far|props|trees|truck|hud (ab18bf1b); build w toku.
- NASTĘPNY KROK: `pwsh -NoProfile -File artifacts/perf-low-r1/phone-diag.ps1 -Apk <apk ab18bf1b> -OutTag diag1 -Segment B -Uncapped -Runs "ab_lod=rq_ab=lod;ab_props=rq_ab=props;ab_truck=rq_ab=truck;ab_hud=rq_ab=hud;ab_far=rq_ab=far;ab_trees=rq_ab=trees;ab_scale=rq_ab=scale"`

## 13:05 — krok 1b: A/B na A16 (APK ab18bf1bac, G3-B Low uncapped, rq_ab, okna 4 s) — `diag1/summary.txt`
- GPU p50 A−B: **ciężarówka (warstwa Vehicle w kamerze głównej) +4,7…5,4 ms**, drzewa +3,0, skala −0,1 +3,3, far ×0,5 +1,4,
  LOD ×0,6 +1,4, propsy +0,3 (liczba draws to nie problem), HUD +0,3.
- Następnie: rozbicie ciężarówki na shadery (glass / cabint / truckext / cabdisp) — nowe klucze rq_ab.

## 13:40 — krok 1c: rozbicie ciężarówki (diag2, diag3; APK d2e7f22851 / 22a104cee0)
- GPU p50 A−B: **szyba (Kamion/Truck Glass) +3,6…4,3 ms** (1 warstwa: GLASS_Windscreen_LOD0 + DoorL_LOD0, ~80 % ekranu w widoku kabiny),
  zewnętrze +0,65, wnętrze −1,2 (bez wnętrza widać świat), wyświetlacz 0.
- Szybka ścieżka szyby (SH per wierzchołek, wielomianowy atan2) tylko −0,4 ms → koszt nie w tych miejscach; bisekcja `_KamionGlassDebug` 1..5
  i A/B drzew (treeshadow/treethin/treecard) w toku: diag4 (APK 5117650d90).
- NASTĘPNY KROK: wyniki `artifacts/perf-low-r1/diag4/*/logcat.txt` ([PASSAB] summary) → wybór poprawek.

## 13:55 — krok 2: poprawka szyby + bisekcja (diag4, APK 5117650d90) — `diag4/summary.txt`
- `_KamionGlassDebug`: stała barwa −3,1 ms (raster+blend ~1,2 ms zostaje), bez filmu wycieraczek −0,85, bez fog/tone −0,2, bez env −0,15,
  bez GGX −0,06 → koszt rozłożony po całym modelu szyby (Fresnel, absorpcja, faza, SH, film).
- Drzewa: cienie drzew 0, przerzedzanie ×0,5 −0,3, karty ×0,5 0 → 3 ms drzew to HLOD/impostory (A/B hlod/impostor w diag5).
- Szybka ścieżka v2 (a1232fc3): Fresnel/absorpcja/faza/SH/fog per wierzchołek, wycieraczki w half; domyślnie Low (QualityProfile.glassFast, rev 106),
  `rq_glassfast 0` = stara ścieżka. Pomiar diag5 w toku.
- NASTĘPNY KROK: wyniki diag5 → kamery kontrolne `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Rq rq_glassfast=0 -OutputDir artifacts/perf-low-r1/r1/before-overcast` (+ after bez -Rq).

## 14:40 — KONIEC r1 (wynik PARTIAL) — liczby i decyzje: docs/adr/0106-perf-low-a16-r1.md („Wynik”, „Otwarte”)
- Finalny APK `kamion-0.1.0-fd126bf3a9.apk` (SHA256 89673f0b…f3e2), gate3 valid=True: Low G3-A 29,78 FPS p99 50,0 (27 kl. >40), GPU p50/p95 29,5/31,1;
  Low G3-B 29,85 FPS **p99 33,7** (21 kl. >40), GPU 29,1/33,7; ten sam APK z rq_glassfast 0 (G3-B): p99 50,0, GPU 30,4/34,8.
  Medium A/B ~21,7 FPS, GPU p50 ~45 ms. PSS 811–879 MB, termika 0. `final/summary.txt`.
- Przyjęte: szybka ścieżka szyby (Low+Medium) −0,9 ms GPU Low / −1,5 Medium, obraz bez zmian (PSNR 62–82 dB, `r1/960/`).
- Testy: EditMode 229/229, PlayMode 110/0/7, pytest gis 310/1 (test_export_is_deterministic — osobno PASS; poza zakresem gałęzi).
- REPORT.md nie został zapisany (reguła środowiska subagenta) — treść raportu w odpowiedzi do lidera i w ADR 0106.
- NASTĘPNY KROK (lider): `git merge perf-low-r1` → EditMode/PlayMode na main → `pwsh scripts/gate3-run.ps1 -Serial RFGL34SJYDZ -Segment A -Tier Low -Fps 30` (+ B).
