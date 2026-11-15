# STATUS — shadows-0240 (F7, B-088 postrzępione cienie cienkich obiektów na Low)

- Krok 1 (kod, NIESKOMPILOWANE w chmurze): `ThinShadowCasterPolicy` (kategoria + bbox), `QualityProfile.Tier.thinCasterShadowsOff`
  (Low on), Low bias 1.0/1.0 -> 0.4/0.3, migracja rev 240 w `ProjectSetup`, `rq_thinshadow`, `WorldInstances` (maska cieni),
  `RegionImporter` (`_LowNoShadow` dla fence_*/barrier_post), assety QualityProfile/URP_Low zsynchronizowane, testy EditMode.
- Pomiar z danych: `tools/rendering/thin_shadow_audit.py --check` -> 153 prototypy, 46 cienkich, 0 niezgodności reguły z pomiarem;
  normal bias 1.0 zostawiał 33 % cienia wysięgnika sygnalizatora (0.3: 80 %). JSON: `docs/reports/shadows-0240/`.
- NASTĘPNY KROK: ADR `docs/adr/0240-…md`, PERFORMANCE_BUDGETS, PR. Lider: `pwsh scripts/setup-project.ps1; pwsh scripts/test.ps1 -Platform EditMode`
