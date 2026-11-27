# STATUS crown-lod-s24 (korony drzew: stipple na krawędziach + rozmyta plama LOD; krytyk build #10 TOP 3)

- Worktree `agent-a380c075164a3cedd`, gałąź `worktree-agent-a380c075164a3cedd`. Nie scalane, nie pushowane.
- Środowisko: Win64 `game/Library` + `game/Assets/_Generated` (tylko `knyszyn-w`) skopiowane z worktree tree-species-s24
  (a492e5af); derived main nietknięte (bez importu). Kamery: `artifacts/crown-lod-s24/cams.json` (widok spawnu build #10).
- [krok 0] Analiza: Vegetation.shader NIE ma LOD crossfade (zero `LOD_FADE_CROSSFADE`); WorldInstances przełącza LOD
  twardo (High: LOD0 < 20 m, LOD1 < 60 m, impostor dalej; treeCardLodScale 1.0). Liście High PC = MSAA 4 + alpha-to-coverage
  (`CoverageAlpha` = alfa wyostrzona przez fwidth). Impostor: 6 widoków 256 × 384 px, blend dwóch sąsiednich widoków (60°).
- NASTĘPNY KROK: `pwsh -NoProfile -File artifacts/crown-lod-s24/vqa.ps1 -Label before` (trwa), potem A/B `-Rq rq_a2c=0`.
- [krok 1] VQA before (`before2`, cab-driver = widok build #10) + A/B: `rq_card=1.5` zamienia rozmytą plamę na ostre karty
  LOD1 => plama = IMPOSTOR (drzewo 60-90 m, 256x384 px/widok, blend 2 widoków 60°). Koszt card 1.5 (cab-driver):
  draws inst. 96 -> 106, tris inst. 47k -> 58k, cienie +11k tris.
- [krok 2] Player A/B build #10 (`artifacts/crown-lod-s24/player/`): izolowane piksele nieba w koronie klonu: A2C 0,21 %,
  bez A2C 0,93 %, MSAA1 0,96 % => stipple to NIE dither crossfade/A2C, tylko przerwy między liśćmi kart ~1 px (aliasing
  alfa-testu); A2C go łagodzi. Edytorowe VQA nie odtwarza A2C (inne liczby) - ocena stipple tylko w playerze.
- [krok 3] Kod: High card 1.0->1.5 (Ultra 1.5->2.0); cross-fade LOD1->impostor (25 % końca LOD1, cutoff-dissolve, tier
  `treeLodFade`, `rq_lodfade`); blend widoków impostora smoothstep(0.3,0.7); A2C snap do pełnych próbek (`rq_a2cq`);
  obniżony cutoff zminiaturyzowanych liści (`VegCutoffFill`, 0.15, `rq_leaffill`); fix: rq_a2c działa w VQA.
- NASTĘPNY KROK: build knyszyn-w (`pwsh scripts/build-windows.ps1 -Regions knyszyn-w -Slot`), player A/B + pc-metrics.
- [krok 4] Player A/B buildu gałęzi (fd3869a, tylko knyszyn-w; `artifacts/crown-lod-s24/player/new-*.png`): plama znika
  (karty LOD1 do 90 m). Snap A2C do pełnych próbek: 0,9 % pikseli zmienionych, brak widocznej różnicy -> USUNIĘTY.
  Fill cutoffu zminiaturyzowanych liści: korona klonu mixed px 8,2 % (fill 0) -> 5,8 % (0,15) -> 4,2 % (0,3) -> 2,8 % (0,45);
  wybrane 0,3 (przerwy 1 px znikają, duże prześwity zostają). Ostrzeżenia fxc (VegAlpha/VegShadow, były też w buildzie #10)
  usunięte. EditMode 1631: 1509 pass / 1 fail (NavVoicePlayer0328Tests - audio, niezwiązany) / 121 skip; testy roślinności 61/61.
- NASTĘPNY KROK: (trwa) VQA `after2` + build ebcf857 + `artifacts/crown-lod-s24/metrics.ps1` (pc-metrics b10/new/new-old).
