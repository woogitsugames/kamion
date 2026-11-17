# STATUS seams-fix-s23 (Opus, s23 17.11)
Zadanie: uskok zach. ronda Knyszyna (DK65 płd.), szew knyszyn-s|knyszyn 1,84 m, DW671 linia na szwie knyszyn|knyszyn-w, linia 2,91 C|Maczka, autopilot z -scene knyszyn (route_links).
## r1 diagnoza (09:xx)
- link_seams na main 5a1c2c37b: knyszyn-s|knyszyn asfalt 7,66|7,66 (skok 1,84 m już zniknął po world3/0275) — do potwierdzenia po przebudowie.
- DW671 knyszyn|knyszyn-w: w knyszyn ciągłe ±1,75 (P-2a 20 m przed rondem, obcięte szwem po 11,5 m), w knyszyn-w przerywane od szwu (kafel nie wie o rondzie) → przeniesienie reszty P-2a przez szew.
- C|Maczka: linia dzieląca pasy DK8 (w257367422) w C ukryta pod wstęgą łącznicy w606396469 (drop_overlapping), w Maczce wychodzi spod niej 0,7 m za szwem.
- sonda: tools/worldgen/qa/seam_marking_strip.py
NASTĘPNY KROK: uv run --project tools/worldgen python tools/worldgen/qa/seam_marking_strip.py knyszyn knyszyn-w 760587.0 611964.502 -0.7577 -0.6526 30
