# STATUS seams-fix-s23 (Opus, s23 17.11)
Zadanie: uskok zach. ronda Knyszyna (DK65 płd.), szew knyszyn-s|knyszyn 1,84 m, DW671 linia na szwie knyszyn|knyszyn-w, linia 2,91 C|Maczka, autopilot z -scene knyszyn (route_links).
## r1 diagnoza (09:xx)
- link_seams na main 5a1c2c37b: knyszyn-s|knyszyn asfalt 7,66|7,66 (skok 1,84 m już zniknął po world3/0275) — do potwierdzenia po przebudowie.
- DW671 knyszyn|knyszyn-w: w knyszyn ciągłe ±1,75 (P-2a 20 m przed rondem, obcięte szwem po 11,5 m), w knyszyn-w przerywane od szwu (kafel nie wie o rondzie) → przeniesienie reszty P-2a przez szew.
- C|Maczka: linia dzieląca pasy DK8 (w257367422) w C ukryta pod wstęgą łącznicy w606396469 (drop_overlapping), w Maczce wychodzi spod niej 0,7 m za szwem.
- sonda: tools/worldgen/qa/seam_marking_strip.py
NASTĘPNY KROK: uv run --project tools/worldgen python tools/worldgen/qa/seam_marking_strip.py knyszyn knyszyn-w 760587.0 611964.502 -0.7577 -0.6526 30
## r2 kod (09:4x)
- (5) linki after_route knyszyn (Rynek→DW671 W 744 m / →DK65 W 765 m), bez zawracania; złącze 70–73°, R~3,9 m (narożnik Rynku) — NIESPRAWDZONE w exe.
- (1) meshing.despike_arcs (tylko rondo kompaktowe): narożniki max 0,514/0,102/0,125/0,462 → 0,116/0,102/0,125/0,132 m/m; trawa 4/4.
- (3) roads/seam_p2a.py + markings.approach_ends: mapa 39 kafli → tylko knyszyn-w (w1478765548, 8,354 m).
- (2) już OK (7,66|7,66). (4) otwarte: łącznica w606396469 na pasie DK8 (abreast shift 0); ortofoto: linia w terenie ciągła przez szew.
- buildy: knyszyn-w start 09:37:36, knyszyn start 09:38:52 (artifacts/seams-fix-s23/build-times.txt)
NASTĘPNY KROK: po buildach: uv run --project tools/worldgen python scripts/export-route.py --region knyszyn ; ... --region knyszyn-w ; potem sondy + qa.seams + route_links.py
