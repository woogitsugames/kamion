# STATUS pc-tiers-0269 (H7, ADR 0269)

- [15.11] Start. Gałąź pc-tiers-0269 z origin/main c45cf8d60. Przeczytane: QualityProfile/QualityTiers/QualityProfileApplier, GameBootstrap (0261 desktop High/60), URP_*.asset, Mobile_Renderer(_SSAO), ProjectSetup.
  NASTĘPNY KROK: dane tierów PC (PcTierTable) + PcGraphicsTiers + assety URP_PC_* + testy.
- [15.11] Zrobione: PcTierTable (dane + walidacja + DefaultFor), PcGraphicsTiers (Apply/Current/DefaultFor/Overlay, haczyk w QualityTiers.Apply, Applier), URP_PC_* + PC_Renderer(_SSAO) w Resources/PcTiers, generator PcTierAssetsSetup, GameBootstrap autodetekcja (gałąź desktop 0261), testy EditMode (8 czystych: .NET 8 8/8 zielone; 6 assetowych NIEuruchomionych), ADR 0269, PERFORMANCE_BUDGETS/DEVICE_MATRIX PC. Merge z origin/main i pc-settings-0270: czysty.
  NASTĘPNY KROK (lider, Windows): `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 -Filter PcGraphicsTier`, potem build + run z ADR 0269 §Walidacja.
