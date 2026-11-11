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
