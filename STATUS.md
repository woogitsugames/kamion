# STATUS knyszyn-r24

- [1] meshing.despike_arcs: interpolacja oflagowanych wysokosci po odleglosci wzdluz obrysu (Codex P2 potwierdzone), test uneven (stary kod FAIL, nowy PASS).
- NASTEPNY KROK: route_links.py:76 / seam_p2a.py:52 weryfikacja; potem P1 rondo Monki.
- [2] route_links.arrival_edge: start after_route zaokraglany takze przy dojezdzie jednokierunkowym (POTWIERDZONE: c-dk8-to-maczka ma dojazd jednokierunkowy DK8, blend glowy 0 -> 0,31 m); test arrival_edge.
- [3] seam_p2a: przenoszenie przez kilka szwow (CARRY_DEPTH 3, tylko lancuchy < 20 m), test 3 kafli; 39 kafli: mapa bez zmian (tylko knyszyn-w 8,354 m).
- NASTEPNY KROK: P1 rondo Monki - uv run --project tools/worldgen python tools/worldgen/qa/link_swept_check.py
- [4] P1 Monki: swing 3,0 m w lewo na rondzie (+-30 m, yaml swing) -> opony poza nawierzchnia 15 (16 bez wyspy) -> 0, poza jezdnia 77 -> 0; link_swept_check --all (8 linkow) 0; twardy test + kontrola negatywna (bez swing >0). pytest route_links+seams 17/17.
- NASTEPNY KROK: przebudowa knyszyn/knyszyn-w (slot heavy) build_world --context
- [5] knyszyn przebudowany (14 min), swept --all 0/8 po przebudowie; import Unity knyszyn + VQA High clear w toku (artifacts/knyszyn-r24/unity1.ps1).
- NASTEPNY KROK: obejrzec artifacts/knyszyn-r24/vqa-knyszyn/look_dom_klattow.png; potem pwsh artifacts/knyszyn-r24/unity1.ps1 -Region knyszyn-w
- [6] deski: look_dom_klattow czytal sie jak podloga -> set_tile_m [6.0,2.6] (materials.py), knyszyn+knyszyn-w przebudowane 21:56. Czeka na MEASURE DONE lidera.
- NASTEPNY KROK: artifacts/knyszyn-r24/after_measure.ps1 (uruchomiony; import+VQA knyszyn, import knyszyn-w, EditMode Win64, pytest tests/gis) -> sprawdzic after_measure.log
