# STATUS — shadows-0240 (F7, B-088 postrzępione cienie cienkich obiektów na Low)

- Kod (NIESKOMPILOWANE w chmurze): `ThinShadowCasterPolicy` (kategoria + bbox), `QualityProfile.Tier.thinCasterShadowsOff`
  (Low on), Low bias 1.0/1.0 -> 0.4/0.3, migracja rev 240 w `ProjectSetup`, `rq_thinshadow`, `WorldInstances` (maska cieni +
  liczniki `ShadowDraws/ShadowTriangles` w stats.txt), `RegionImporter` (`_LowNoShadow` dla fence_* słupków / barrier_post;
  siatka `fence_*_mesh` należy do ADR 0239 / PR #109), assety QualityProfile/URP_Low zsynchronizowane, testy EditMode.
- Pomiar z danych: `uv run --project tools/worldgen python tools/rendering/thin_shadow_audit.py --check` -> 153 prototypy,
  46 cienkich, 0 niezgodności; normal bias 1.0 zostawiał 33 % cienia wysięgnika sygnalizatora (0.3: 80 %).
- ADR `docs/adr/0240-cienie-cienkich-obiektow-low.md`, sekcja w `docs/PERFORMANCE_BUDGETS.md`. Scalać po #109 (F6).
- NASTĘPNY KROK (lider): `pwsh scripts/setup-project.ps1; pwsh scripts/test.ps1 -Platform EditMode;
  pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -OutputDir artifacts/visual-qa/shadows-0240/low`
