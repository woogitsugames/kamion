# ADR 0269 — tiery grafiki PC (Low / Medium / High / Ultra)
Status: przyjęty (scalony do main 2026-11-16, `3e9ef52fc`; status zaktualizowany 2026-11-16); pierwotnie: Proposed (chmura H r2, zadanie H7, gałąź `pc-tiers-0269`), 2026-11-15. Do weryfikacji i scalenia przez lidera.
Powiązane: D73 / ADR 0260 (Windows platformą główną), D74 (klasy sprzętu PC), ADR 0261 (build Windows, desktop domyślnie
High / 60 fps), ADR 0010 (tiery = poziomy jakości + `QualityProfile`), ADR 0012 (tier treści), ADR 0080 (SSAO Ultra),
ADR 0270 (menu ustawień PC — woła API z tego ADR).

## Kontekst
Tiery `Low/Medium/High/Ultra` są dziś skrojone pod telefony (A16 / S24+ / Fold): render scale 0,75–1,0, MSAA 2×,
cienie 35–150 m, adaptacyjna rozdzielczość i bezpieczniki termiczne. Na PC (D74: min. GTX 660 2 GB / i5-6400 / 8 GB →
Low 1080p 30 fps; zalecane GTX 1660 / i5-9600 / 12 GB → High 1080p 60 fps) te wartości są za niskie i część mechanizmów
nie ma sensu (termika). `ProjectSettings/` (QualitySettings.asset) i profile mobilne — poza zakresem agenta.

## Decyzja
1. **Dane:** `Game.Rendering.PcTierTable` (`Rendering/Runtime/PcTierTable.cs`) — tabela 4 × `PcTierSettings` jako kod-dane,
   ten sam wzorzec co `QualityProfile.Defaults()`; czysta logika bez wywołań UnityEngine (testowalna poza Unity).
   Walidacja `PcTierTable.Validate` (zakresy, rosnące podziały kaskad, monotoniczność Low ≤ Medium ≤ High ≤ Ultra).
2. **Assety:** `Rendering/Resources/PcTiers/URP_PC_{Low,Medium,High,Ultra}.asset` + `PC_Renderer.asset` (kopia
   `Mobile_Renderer`) + `PC_Renderer_SSAO.asset` (kopia `Mobile_Renderer_SSAO`, **identyczne** ustawienia SSAO).
   W `Resources`, więc trafiają do buildu bez wpisu w QualitySettings. Generator: `Game.Rendering.Editor.PcTierAssetsSetup.EnsureBatch`
   (pisze assety z tabeli); YAML w repo odpowiada wynikowi generatora, test EditMode pilnuje równości. Assety mobilne bez zmian.
3. **Runtime (bez ProjectSettings):** PC tier = poziom jakości o tej samej nazwie (tier treści `_High`, budżety lusterek,
   polityki po nazwie zostają) + na desktopie: `QualitySettings.renderPipeline = URP_PC_<tier>` (nadpisanie w runtime dla
   bieżącego poziomu), `QualitySettings.lodBias / maximumLODLevel / globalTextureMipmapLimit / anisotropicFiltering`,
   a `QualityProfileApplier` bierze tier mobilny i nakłada pola PC (`PcGraphicsTiers.Overlay`: kamera, far clip, AA, roślinność,
   capture, lampy, chmury). Haczyk w `QualityTiers.Apply` → każda ścieżka zmiany poziomu (`-tier`, zapisany wybór,
   przycisk diagnostyki, menu) dostaje wartości PC. Wywołania tylko przy zmianie tieru; nic per klatka (0 GC w pętli jazdy).
   Telefony i edytor bez zmian (`Enabled` = desktop player; edytor tylko z `ForceEnabled = true` + `RestoreEditorState()`).
   A/B: argument playera `-pc_tiers 0` = desktop na assetach/wartościach mobilnych.
4. **API dla ADR 0270:** `enum PcTier {Low, Medium, High, Ultra}`, `PcGraphicsTiers.Apply(PcTier tier, bool persist = false)`,
   `PcGraphicsTiers.Current`, `PcGraphicsTiers.DefaultFor(PcHardwareInfo)` (+ wariant z `out string reason`),
   `PcGraphicsTiers.DetectHardware()`, `PcGraphicsTiers.Settings(tier)`, zdarzenie `Changed`.
5. **Autodetekcja (pierwsze uruchomienie, integracja z ADR 0261):** `GameBootstrap` w gałęzi „desktop bez `-tier` i bez zapisu”
   woła `DefaultFor(DetectHardware())` zamiast stałego High. Reguły (WORKING_VALUE, z klas D74): renderer programowy lub iGPU
   (Intel HD/UHD/Iris, Radeon Graphics/Vega/7x0M) → Low; RAM < 7 000 MB → Low; VRAM nieznany → Medium; VRAM < 3 500 MB → Low;
   < 5 500 MB → Medium; inaczej High; High wymaga RAM ≥ 11 000 MB (D74: 12 GB), inaczej Medium. **Nigdy Ultra** (sufit = High
   z ADR 0261; Ultra tylko z menu). `GameBootstrap.DesktopDefaultTier` ("High") zostaje jako fallback.
6. **Limit klatek** nie jest częścią tieru (ADR 0261: 60 fps, `-fps`, menu 0270). `targetFps` w tabeli to budżet D74 do pomiaru.

## Tabela wartości i źródła
Wszystkie wartości: **WORKING_VALUE / ESTIMATED — nic nie zmierzono na klasach D74** (brak PC referencyjnego).
Pomiar dev (RTX 5070, ADR 0261: High mobilny ~425 fps na postoju) nie jest referencją i nie był robiony na tych assetach.

| Pole | Low | Medium | High | Ultra | Źródło / uzasadnienie |
|---|---|---|---|---|---|
| Rozdzielczość / render scale | 1,0 | 1,0 | 1,0 | 1,0 | D74: 1080p natywnie; brak adaptacji (`adaptiveScaleMin` 0) — przewidywalny obraz; adaptacja na Low dopiero po pomiarze GTX 660 |
| Upscaler | brak | brak | brak | brak | skala 1,0 → FSR zbędny ([URP asset: Upscaling Filter](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/manual/universalrp-asset.html)) |
| MSAA | 2× | 4× | 4× | 8× | liście/impostory używają alpha-to-coverage (ADR 0013, wymaga MSAA); 8× = więcej poziomów pokrycia krawędzi liści; ESTIMATED koszt |
| Post AA | brak | brak | brak | brak | FXAA/SMAA rozmywa teksturę drogi; pole i jakość SMAA są w danych (przełącznik). **TAA/STP wykluczone**: URP TAA nie działa z MSAA ([URP anti-aliasing](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/manual/anti-aliasing.html)), duchy na liniach i drutach przy prędkości (docs/06) |
| HDR + tonemapping Neutral | tak | tak | tak | tak | jeden skalibrowany wygląd na wszystkich tierach (docs/06 §4); mobilny Low bez post — na PC koszt pomijalny (ESTIMATED) |
| Dystans cieni | 60 m | 100 m | 150 m | 250 m | mobilne 35/60/100/150 m; PC +~50 %; Ultra 250 m (ESTIMATED) |
| Kaskady | 2 | 3 | 4 | 4 | [URP shadows](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/manual/universalrp-asset.html#shadows) |
| Podział 2/3/4 | 0,25 / 0,1–0,3 / 0,067–0,2–0,467 | jw. | jw. | 0,04–0,12–0,35 | domyślne URP (0,25; 0,067/0,2/0,467) jak w mobilnych Low/Medium; Ultra ciaśniej, by zachować gęstość bliskiej kaskady przy 250 m |
| Atlas cieni | 2048 | 2048 | 4096 | 8192 | 4 kaskady w 4096 → 2048/kaskadę; 8192 (max URP) tylko Ultra (VRAM ≥ ~10 GB) |
| Soft shadows | off | Low | Low | High | tylko jakości używane przez assety mobilne (Low w High, High w Ultra) — wariant Medium byłby wycięty (patrz Ryzyka) |
| Bias głęb./norm. | 0,4/0,3 | 0,4/0,3 | 0,6/0,6 | 0,6/0,6 | jak mobilne o tej samej liczbie kaskad (Medium/High: 0,4/0,3; Ultra 4 kask.: 0,6/0,6) |
| LOD bias | 1,0 | 1,25 | 1,5 | 2,0 | mobilne 0,5/0,8/1,5/2,0 ([QualitySettings.lodBias](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/QualitySettings-lodBias.html)) |
| maximumLODLevel | 0 | 0 | 0 | 0 | wymuszanie LOD1 = popping blisko; zostawione jako przełącznik ([QualitySettings.maximumLODLevel](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/QualitySettings-maximumLODLevel.html)) |
| Tekstury (globalTextureMipmapLimit) | 1 (½) | 0 | 0 | 0 | D74 min = 2 GB VRAM; ½ rozdzielczości ≈ ¼ pamięci tekstur ([doc](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/QualitySettings-globalTextureMipmapLimit.html)) |
| Anizotropia (global / świat) | Enable / 4 | Enable / 8 | ForceEnable / 16 | ForceEnable / 16 | [QualitySettings.anisotropicFiltering](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/QualitySettings-anisotropicFiltering.html); linie drogi pod kątem |
| Far clip | 1 500 m | 2 000 m | 3 000 m | 4 000 m | mobilne 900/1400/2500/3500 m; reversed-Z na D3D |
| Światła dodatkowe / obiekt | 4 | 4 | 8 | 8 | max URP Forward = 8 |
| SSAO | off | off | tak | tak | renderer z ADR 0080 (po opaque, połowa rozdz., słabe 1,0 / 0,6 m) |
| Drzewa: start przerzedzania / cull | 90 / 600 m | 120 / 800 m | 150 / 1 000 m | 200 / 1 500 m | mobilne 90/600 m wszędzie; `WorldInstances` (× LOD bias) |
| Karty liści (treeCardLodScale) | 0,5 | 0,5 | 0,75 | 1,0 | mobilne 0,5 |
| Cienie drzew (LOD mask) | LOD0+1 | LOD0+1 | LOD0+1 | LOD0+1 | pc-shadows-s23 (2026-11-16): sam LOD0 przy karcie 0,5 i końcach LOD drzew 20/60 m = cień tylko do 10 m od kamery → brak cieni drzew na jezdni z kabiny (player knyszyn-s). LOD0+1 = zasięg 30 m (Low/Medium), 45 m (High), 60 m (Ultra). Mobilne Low/Medium zostają przy LOD0 (koszt A16). Koszt na GTX 660-klasie ESTIMATED |
| Las HLOD przełącz. / cull | 70 / 1 500 m | 90 / ∞ | 150 / ∞ | 200 / ∞ | ADR 0015; mobilne 70–120 m |
| Pojazdy parkujące cull | 200 m | 300 m | 400 m | 600 m | ADR 0136 r2 (mobilny Low 150 m, reszta 300 m) |
| Szybkie ścieżki (foliage / forest / glass) | tak/tak/tak | tak/nie/nie | tak/nie/nie | tak/nie/nie | `simpleFoliage` wszędzie (wygląd zatwierdzony ADR 0013; Lit liście = zmiana wyglądu bez visual QA); forest/glass fast tylko Low |
| Capture odbić (px / co N klatek) | 64 / 6 | 128 / 4 | 256 / 2 | 256 / 1 | mobilne 64/10 … 256/2 |
| Latarnie (światła / pule) | 0 / 6 | 2 / 8 | 6 / 8 | 8 / 8 | ADR 0062 / 0191 |
| Chmury (cloudQuality) | 1 | 1 | 2 | 2 | ADR 0080 |
| Lusterka (mnożnik RT) | 1,0 | 1,0 | 1,0 | 1,0 | docs/06: zawsze użyteczne; walidacja ≥ 1 |
| Trawa (źdźbła) | — | — | — | — | **w main nie ma systemu trawy** (tylko materiał terenu); „gęstość roślinności” = przerzedzanie/cull drzew i HLOD powyżej |
| Cel (budżet D74) | 30 fps | 60 fps | 60 fps | 60 fps | D74 WORKING_VALUE; nie limit klatek |

Pola niewymienione (lakier, brud, cab lift, okna nocą, sky vis itd.) = tier mobilny o tej samej nazwie.
Budżety mobilne (PERFORMANCE_BUDGETS: High < 1,5–2 M tris) — bez zmian; treść PC = te same sceny `_High`/Low co telefon.

## Ryzyka
- **Stripping wariantów shaderów:** URP wycina warianty wg assetów URP przypisanych w Quality/Graphics settings, nie wg
  assetów w `Resources` ([URP shader stripping](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/manual/shader-stripping.html);
  UNVERIFIED w naszym buildzie). Dlatego assety PC używają **tylko** cech obecnych w assetach mobilnych (soft Low/High, ≤ 4 kaskady,
  SSAO o tych samych ustawieniach, te same tryby świateł/cookies/warstw); test `PcAssets_UseOnlyFeaturesTheQualityLevelAssetsKeepInTheBuild`.
  Pełne rozwiązanie (gdy PC zechce np. Forward+, soft Medium, inne SSAO) = propozycja dla lidera niżej.
- Zmiana assetu URP w runtime odtwarza pipeline (jednorazowy przestój przy zmianie tieru) — akceptowalne w menu.
- Na High/Ultra lusterka (`RenderTextureMirror.SetRenderer(0)`) renderują przez renderer SSAO — tak samo jak mobilny Ultra dziś;
  koszt do zmierzenia (`ExtraViewCostMonitor`), ewentualna zmiana kolejności rendererów = osobne zadanie (ADR 0152: capture z indeksem 1).
- Autodetekcja po VRAM jest zgrubna (GTX 1060 6 GB → High). Do kalibracji po pomiarach klas D74.

## Propozycje dla lidera (ProjectSettings / skrypty — NIE zrobione)
1. **Niepotrzebne do działania.** Opcjonalnie, by warianty liczyły się z assetami PC: dodać do `QualitySettings.asset` 4 poziomy
   `PC_Low…PC_Ultra` z `customRenderPipeline: URP_PC_*` i `excludedTargetPlatforms: [Android, iPhone]` — **odradzam teraz**:
   kod porównuje nazwy poziomów (`"High"`, `"Ultra"`, `QualityTiers.Names`) w ~20 miejscach. Zamiast tego: po pierwszym buildzie
   Windows sprawdzić w logu buildu liczbę wariantów (`Kamion.variants.txt`) z `-noShaderStrip` vs bez — różnica w Lit/SSAO = problem.
2. **visual-qa.ps1 / VisualQaRunner** znają `Ultra`, ale nie tiery PC (renderują assety mobilne). Patch (Editor/VisualQA, właściciel visual-qa):
   ```diff
   # scripts/visual-qa.ps1 (param)
   +    [switch]$Pc,
   # po $qaArgs
   +if ($Pc) { $qaArgs += @('-qaPcTiers', '1') }
   // VisualQaRunner.Render, przed QualityTiers.Apply(tier):
   +            bool pc = EditorTools.Arg("-qaPcTiers", "0") == "1";
   +            if (pc) PcGraphicsTiers.ForceEnabled = true;
               QualityTiers.Apply(tier);
   // po profile.TryGet(tier, out tierSettings):
   +            if (hasTier && pc) tierSettings = PcGraphicsTiers.Overlay(tierSettings);
   // na końcu Render (finally):
   +            if (pc) { PcGraphicsTiers.RestoreEditorState(); PcGraphicsTiers.ForceEnabled = null; }
   ```
3. `build-windows.ps1` — zmiana zbędna: ma już `-Tier Low|Medium|High|Ultra`, `-Width/-Height`, `-Fps`, `-ExtraPlayerArgs`.

## Walidacja
- **Uruchomione (chmura, bez Unity):** `PcGraphicsTierTableTests` (8 testów: walidacja tabeli, nazwy = poziomy jakości,
  monotoniczność, lusterka/MSAA/HDR, odrzucanie złych danych, klasy D74, krawędzie i sufit autodetekcji, monotoniczność po VRAM)
  skompilowane z `PcTierTable.cs` w .NET 8 + NUnit 3.14 z atrapą `TooltipAttribute`: **8/8 zielone**. Zgodność YAML assetów
  z tabelą sprawdzona skryptem (msaa, atlas, dystans, kaskady, podziały, biasy, soft, SSAO): zgodne.
- **NIEuruchomione:** kompilacja w Unity, `PcGraphicsTierAssetTests` (6 testów: assety = tabela, cechy ⊆ assety poziomów,
  SSAO renderer = mobilny, Overlay, edytor/telefon bez zmian, podgląd w edytorze + przywrócenie), build Windows, render kamer,
  jakikolwiek pomiar FPS/VRAM.
- Komendy dla lidera (Windows):
  ```
  pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 -Filter PcGraphicsTier   # potem pełny przebieg
  pwsh scripts/build-windows.ps1 -Slot -Regions 'knyszyn-w'
  pwsh scripts/build-windows.ps1 -SkipBuild -Run -Scene knyszyn-w -Autopilot route -Speed 50 -Tier Low  -Width 1920 -Height 1080 -Fps 1000 -RunSeconds 90 -ShotSeconds 45
  pwsh scripts/build-windows.ps1 -SkipBuild -Run -Scene knyszyn-w -Autopilot route -Speed 50 -Tier High -Width 1920 -Height 1080 -Fps 1000 -RunSeconds 90 -ShotSeconds 45
  # A/B z mobilnymi assetami: dodać -ExtraPlayerArgs '-pc_tiers','0'
  # po scaleniu #130 (scripts/pc-metrics.ps1): pwsh scripts/pc-metrics.ps1 -Exe <exe> -Scene knyszyn-w -Tier High -Fps 60 -Width 1920 -Height 1080 -Class zalecany
  pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting overcast   # dziś = assety mobilne; tiery PC po patchu z pkt 2 (-Pc)
  ```
  W logu playera: `[PC_TIER] <tier> urp=URP_PC_<tier> …` i `[BOOT] desktop default tier … (gpu=… vram=… ram=…)`.

## Otwarte
- Pomiar Low na GTX 660/HD 630-klasie i High na GTX 1660-klasie (p50/p95/p99, VRAM, 30 min) — dopiero to zamienia WORKING_VALUE na liczby.
- Visual QA tierów PC (patch pkt 2) + krytyk wizualny: MSAA 8×, cienie 250 m, SSAO na High.
- Trawa: brak systemu — osobne zadanie świata, wtedy dodać pola gęstości/dystansu do `PcTierSettings`.
- Lusterka przez renderer SSAO na High/Ultra (koszt).
- Cienie drzew za zasięgiem kart LOD1 (Low/Medium 30–60/100 m, High 45–150 m): impostory i HLOD lasu nie rzucają cienia. Opcje (wymagają pomiaru): wyższy `treeCardLodScale` na PC albo osobny caster LOD1 dla passu cieni (pc-shadows-s23).
