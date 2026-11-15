# axleloads-tuning-0201b (ADR 0201b) — live
Gałąź `axleloads-tuning-0201b` (baza: `truckdata-0201` = PR #77, zmergowany 6732cdd27). Cel: naciski solo 73/27 % (S9 R3-013/014) + strojenie bez luzowania tolerancji.
- 15.11: baseline R3 `r3-base/` 135/135; powtórzenie n1 `exp-n1-repro/` = te same 4 FAIL.
- 15.11: kandydaci A–D (`candA..candD/`): masy skalibrowane (rama wg dims.json, oś tył 1100, przód 500, osprzęt 2,6 m) → 73,3 % bez paliwa; zawieszenie przeskalowane naciskiem; przyczyny FAIL zbadane (CSV): krawężnik = odbój tyłu lżejszej osi; kiwnięcie oka = AMT czytał pedał×ASR; zgaśnięcie = wolne anty-zgaśnięcie; pełzanie = poziomowanie miecha; soak = osiadanie (niezależne od dt/sub-kroków, `soak-dt/`).
- 15.11: AMT: harmonogram z pedału kierowcy, anty-zgaśnięcie 8/s (`amtOnly/` = 135/135 na starych masach).
- 15.11: final: przód 250 kN/m (mod podskoku = base), odbój tyłu 15 mm → `final/` **135/135**; goldeny 6 nagranych (nakładki `plots/`); .NET 273/274 (F2 mutacja chaotyczna — decyzja lidera, ADR 0201b).
- 15.11: VRD, PV §6g, ADR 0201b, PR-BODY.
- NASTĘPNY KROK (lider, Windows): decyzja F2; `pwsh scripts/test.ps1 -Platform EditMode`; `pwsh scripts/test.ps1 -Platform PlayMode`; `pwsh scripts/build-android.ps1`; `pwsh scripts/gate12-phone.ps1 -Apk artifacts/apk/kamion-<ver>-<sha>.apk -UseExistingLock -Only s080_solo_1,s080_solo_2,s080_solo_3,s080_empty,s080_40t`; feel test właściciela.
