# STATUS knyszyn-r24

- [1] meshing.despike_arcs: interpolacja oflagowanych wysokosci po odleglosci wzdluz obrysu (Codex P2 potwierdzone), test uneven (stary kod FAIL, nowy PASS).
- NASTEPNY KROK: route_links.py:76 / seam_p2a.py:52 weryfikacja; potem P1 rondo Monki.
- [2] route_links.arrival_edge: start after_route zaokraglany takze przy dojezdzie jednokierunkowym (POTWIERDZONE: c-dk8-to-maczka ma dojazd jednokierunkowy DK8, blend glowy 0 -> 0,31 m); test arrival_edge.
- [3] seam_p2a: przenoszenie przez kilka szwow (CARRY_DEPTH 3, tylko lancuchy < 20 m), test 3 kafli; 39 kafli: mapa bez zmian (tylko knyszyn-w 8,354 m).
- NASTEPNY KROK: P1 rondo Monki - uv run --project tools/worldgen python tools/worldgen/qa/link_swept_check.py
- [4] P1 Monki: swing 3,0 m w lewo na rondzie (+-30 m, yaml swing) -> opony poza nawierzchnia 15 (16 bez wyspy) -> 0, poza jezdnia 77 -> 0; link_swept_check --all (8 linkow) 0; twardy test + kontrola negatywna (bez swing >0). pytest route_links+seams 17/17.
- NASTEPNY KROK: przebudowa knyszyn/knyszyn-w (slot heavy) build_world --context
