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
## r3 (12:4x)
- knyszyn-w zbudowany 09:37:36–09:42:46, knyszyn 09:38:52–09:52:50 (derived/knyszyn w main = seams-fix-s23 od 09:52:50).
- sondy: uskok zach. 0,506→0,218 m (mediana 0,152), wsch. 0,191 bez zmian; DW671 szew: ciągłe ±1,75 m 0–8,35 m w knyszyn-w; link_seams knyszyn-s|knyszyn 7,66|7,66.
- qa.seams: FAIL 16 (było 19 w ADR 0275; pozostałe = referencje rozstawu linii, pobocza DK8 kleeberga), PRZEJŚCIE 11.
- pytest tests/gis 2405/3: reader seam_p2a (naprawione), fidelity C stale (run.py w toku), test_hero_bridge 0,003 m (C, nie z tej gałęzi).
NASTĘPNY KROK: bash artifacts/seams-fix-s23/unity-chain.sh (import Win64 + vqa High) — w toku; potem obejrzeć PNG, commit fidelity C.
## r4 KONIEC (13:1x)
- import Win64 knyszyn 12:57:13 / knyszyn-w 12:59:29 exit 0; vqa High 13:02:58 / 13:03:22 (artifacts/seams-fix-s23/vqa, kopia w main/artifacts).
- obejrzane: rondo-dk65-from-south / above — trawa przy krawężnikach obu narożników płd., bez widocznego uskoku; fidelity C odświeżone (tylko hashe).
NASTĘPNY KROK (lider): git merge origin/seams-fix-s23; EditMode WorldStreamerRouteLinksTests (Win64); test jazdy exe -scene knyszyn -stream 1 -autopilot route.
## r5 STOP (13:3x, właściciel przenosi maszynę)
- po merge main e0a0ccc21: knyszyn 13:12–13:20, knyszyn-w 13:27–13:29 (kamera dw671_seam_east_lines), fidelity C; import Win64 13:31/13:32, vqa High 13:33 (artifacts/seams-fix-s23/vqa2, NIEOBEJRZANE), EditMode WorldStreamerRouteLinksTests exit 0 (13:34).
- ADR 0287 zajęty w main -> moje to 0288.
NASTĘPNY KROK: obejrzeć artifacts/seams-fix-s23/vqa2/knyszyn-w-High/dw671-seam-east-lines.png i vqa2/knyszyn-High/rondo-dk65-from-south.png; potem lider: git merge origin/seams-fix-s23 && uv run --project tools/worldgen python tools/worldgen/streaming/route_links.py --check
