# STATUS signs-p1-s23 (D25, chmura D r7) — ADR 0279 „P1 — wdrożenie” (baza: PR #147 signs-audit-0279 scalony do gałęzi)
- krok 1: (1) urządzenia przejazdu: `rail.device_stations` — sygnalizator/G-3/G-4 ≥ 5 m od skrajnej szyny (1105 § 77 ust. 2 pkt 1; 2311 zał. 1 pkt 2.2.11), rogatka ≥ 5 m od osi toru po osi drogi (§ 54 ust. 1); było ≈ 3,55 m. Testy -k "rail or p1_0279": 139 passed.
- NASTĘPNY KROK: (2)+(3) markings.py P-14 przy sygnalizatorze / P-12 przy B-20 — `uv run --project tools/worldgen python -m pytest tests/gis -k "sign or marking or rail or 0279" -q`
