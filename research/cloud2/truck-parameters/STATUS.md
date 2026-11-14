# STATUS — R3 truck-parameters (gałąź research/cloud2-truck-parameters)

- 2026-11-14 krok 0: worktree utworzony, przeczytane docs/04, VEHICLE_REFERENCE_DATA, PHYSICS_VALIDATION, dane JSON gry, research mistral/gptpro p4 (wymiary/masy 96/53 już tam: P4-123..P4-138 — cytujemy, nie dublujemy).
  NASTĘPNY KROK: `cd /workspace/wt/truck-parameters/research/cloud2/truck-parameters && python3 -I fetch.py` (pobranie źródeł: R13, 2020/740, karty silników/skrzyń/opon)
- 2026-11-14 krok 1: pobrane i przeczytane źródła (files/, poza gitem): R13 Rev.3 (UN digital library; tabela typ-0 obejrzana jako obraz s. 43), R13 02 (MLIT), 96/53 skonsolidowana (Cellar PL), 2020/740 (Cellar EN), Volvo D13K500/D13K460/AT2612/ATO2612F/RSS1344C/FH 42T 3A, ZF TraXon, DAF XF/CF spec, MB Powertrain Euro VI, Dunlop databook 2021, Bridgestone ×3, Nokian 315/70, Kässbohrer curtainsider ×2, Schmitz S.CS, eCFR FMVSS 121, Chalmers ODR (Karisaari 2020, Varghese 2014 i in.). Zablokowane (403): NHTSA 812176/809700, ROSA P, MDPI, Deep Blue, unece.org — luka.
  NASTĘPNY KROK: `cd /workspace/wt/truck-parameters/research/cloud2/truck-parameters && python3 -I build_manifest.py` (manifest.csv z weryfikacją cytatów w tekście PDF)
- 2026-11-14 krok 2: manifest.csv — 157 wierszy (142 SOURCED, 11 ESTIMATED, 4 UNVERIFIED), 24 dokumenty; build_manifest.py weryfikuje każdy cytat SOURCED w tekście PDF (0 błędów); fetch.py OK.
  NASTĘPNY KROK: `python3 -I audit.py` (samokontrola 20 %, seed 20261114), potem sources.md i README.md
- 2026-11-14 krok 3: samokontrola 33/157 (21 %, seed 20261114): 1. przebieg 32 PASS / 1 FAIL (R3-153 przeliczenie jednostek) → poprawione → 33 PASS / 0 FAIL; obrazy (AT2612, R13 s.43, MB s.29) ponownie obejrzane.
  NASTĘPNY KROK: napisać sources.md i README.md, commit + push
- 2026-11-14 krok 4: README.md (tabela gra vs źródło, luki, co nowe), sources.md (24 dokumenty + 6 zablokowanych). Pakiet kompletny.
  NASTĘPNY KROK: czekać na recenzję lidera (REVIEW.md); poprawki P0/P1 w tej gałęzi. Odtworzenie: `python3 -I fetch.py && python3 -I build_manifest.py && python3 -I audit.py`
- 2026-11-14 krok 5 (rewizja 2, po REVIEW.md — werdykt FIX): P1-1 (72→0 ≤ 60,9 m; 60→0 ≤ 36,7 m; 61,2 m = ekstrapolacja), P1-2 (awaryjne N /115, N3 40 km/h; resztkowe ≤ 52,4 m; errata VRD S5/PV w.6 w README), P1-3 (MLIT s. 27–28 seria 10 jako 2. źródło; seria 11 = luka), P1-4 (kolumny MEGA/STANDARD/MAXIMA). P2: marki usunięte z `przedmiot`, Karisaari = model, zastrzeżenie FMVSS 121, KASS22 usunięty, cytaty wielowartościowe, numer biegu ESTIMATED, skutek laden40. Manifest 162 wiersze; audyt 35/162 PASS.
  NASTĘPNY KROK: czekać na ponowną recenzję lidera
