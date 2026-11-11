# STATUS — perf-low-r1 (ADR 0106, rendering-perf)

## 2026-11-11 12:25 — krok 1: diagnoza (start)
- Analiza gate3 A16 Low (APK 43bc53a769-dirty): G3-A 39 klatek > 40 ms po rozgrzewce, G3-B 32; prawie wszystkie to 50 ms (3 vsync)
  przy GPU 30–48 ms i CPU main 17–24 ms → piki p99 = GPU na granicy 33,3 ms, nie GC/streaming (świat w całości załadowany,
  logcat bez zdarzeń). Jeden krótki pakiet CPU 30–50 ms w G3-A t≈51 s (wiadukt Bieżeństwa).
- Edytor (buildings-r13 r3 Low stats): instancjonowane draws 380–720 przy 230–450 instancjach (≈1 instancja/draw: wiele prototypów×submesh).
- Uruchomiony skrypt ablacji telefonu `artifacts/perf-low-r1/phone-diag.ps1` (czeka na brak Unity i PHONE_RUN), uncapped G3-B:
  base / rq_ab mirrors / shadow 0 / msaa 1 / scale 0.6 / trees 0 / sky / a8 0 / base.
- NASTĘPNY KROK: `pwsh -NoProfile -File artifacts/perf-low-r1/phone-diag.ps1 -Apk C:\Users\matma\Documents\Claude\kamion\artifacts\apk\kamion-0.1.0-43bc53a769-dirty.apk -OutTag diag0 -Segment B -Uncapped -Runs "base0=;ab_mir=rq_ab=mirrors;shadow0=rq_shadow=0;msaa1=rq_msaa=1;scale06=rq_scale=0.6;trees0=rq_trees=0;sky=rq_clouds=-1 rq_haze=0;a8off=rq_a8=0;base1="` (jeśli przerwane), potem analiza `artifacts/perf-low-r1/diag0/*/frametimes.csv`.
