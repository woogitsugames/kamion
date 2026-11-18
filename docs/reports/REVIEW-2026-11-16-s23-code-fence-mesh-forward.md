# REVIEW s23 code — poprawka `FenceMeshForward.hlsl` (D18, temat 2)

- Merge: `e4fad6868` „Merge c-regen2-s23 … (+ poprawka magenty płotu FenceMeshForward)”. Poprawka: commit `a2a5dfa64`
  (1 linia + komentarz). Kontekst: ADR 0239 (siatka płotu, pokrycie zależne od odległości), recenzja #109 z s22.
- Pliki: `game/Assets/_Project/Rendering/Shaders/FenceMeshForward.hlsl:17`. Dla kontekstu przeczytałem też `FenceMeshCoverage.hlsl`,
  `WorldFenceMesh.shader`, `FenceMeshCoverage.cs`, `RegionImporter.cs:462-466`, `InstanceImporter.cs:679-682`
  oraz `FenceMeshCoverageTests.cs`.

## Werdykt: FIX (sama poprawka poprawna; P1 w zabezpieczeniu awaryjnym importera, które nie zadziałało przy tej awarii)

## Poprawność poprawki — zweryfikowana w źródłach URP 17.3 (Unity 6000.3)
Sprawdziłem `Unity-Technologies/Graphics`, gałąź `6000.3/staging`, pakiet `com.unity.render-pipelines.universal`:
- `ShaderLibrary/ShaderVariablesFunctions.hlsl:171-219`: `IsAlphaToMaskAvailable()` (razem z `SharpenAlpha*` i `AlphaClip`)
  leży w `#if defined(_ALPHATEST_ON)` z komentarzem „Only define the alpha clipping helpers when the alpha test define is present”.
  Przejście `ForwardLit` w `WorldFenceMesh.shader:109-126` celowo nie kompiluje `_ALPHATEST_ON` (pilnuje tego test
  `Shader_CompilesAndKeepsTheLitContract`), więc wywołanie było niezdefiniowane, przejście się nie kompilowało
  i płot był magentą. Diagnoza z commitu jest trafna.
- `ShaderLibrary/Input.hlsl:114-115`: `float _AlphaToMaskAvailable;` jest deklarowane bezwarunkowo, więc
  `_AlphaToMaskAvailable != 0.0` kompiluje się w każdym wariancie.
- `Runtime/Passes/DrawObjectsPass.cs:168-171`: URP ustawia global
  `(cameraTargetDescriptor.msaaSamples > 1 && isOpaque) ? 1 : 0` przed rysowaniem obiektów nieprzezroczystych.
  Materiał płotu jest w kolejce `AlphaTest` (opaque), a wszystkie tiery mają MSAA 2×/4× (`URP_*.asset:28 m_MSAA`).
  Ścieżka a2c działa więc tak, jak zakłada ADR 0239. `FenceMeshCoverage.Apply` ustawia `_AlphaToMask = 1`
  (`FenceMeshCoverage.cs:80`), więc stan renderowania i gałąź shadera są zgodne.
- Semantyka jest identyczna z helperem URP (`return _AlphaToMaskAvailable != 0.0`), więc poza samą kompilacją
  zachowanie się nie zmienia.

Kompilacja niemożliwa w chmurze. Ocena na podstawie kodu źródłowego URP, nieskompilowane w chmurze.

## Uwagi

### P1
1. **Zabezpieczenie „bez shadera zostaje stan s20” nie łapie błędu kompilacji.** ADR 0239 §2 i komentarz
   `FenceMeshCoverage.cs:35-36` obiecują: „without the shader (compile error) it keeps the coverage-preserving mips”.
   Kod sprawdza jednak tylko `Shader.Find(...) != null` (`InstanceImporter.cs:679-680`) i `fenceShader == null`
   (`FenceMeshCoverage.cs:76`, `RegionImporter.cs:464`). Shader z błędem kompilacji jest znajdowany, więc import
   przełączył materiał na shader-magentę **i** dał tej teksturze mipy box. To dokładnie przypadek tej awarii.
   **Poprawka (Editor, 2 miejsca):** pomocnik w `RegionImporter`/`InstanceImporter`:
   `static Shader FenceShaderOrNull() { var s = Shader.Find(FenceMeshCoverage.ShaderName); return s != null && !UnityEditor.ShaderUtil.ShaderHasError(s) ? s : null; }`
   użyty w obu miejscach, z `Debug.LogWarning` przy błędzie. Do tego test EditMode: przy `fenceShader == null`
   `PreserveCoverageMips(..., fenceShaderAvailable:false) == true` (ten już jest) oraz że importer korzysta z nowego
   pomocnika (sprawdzenie źródła jak w `ShaderDir` testów 0239).

### P2
2. **Test kompilacji nie wykrył błędu.** `FenceMeshCoverageTests.Shader_CompilesAndKeepsTheLitContract` ma
   `Assert.IsFalse(ShaderUtil.ShaderHasError(shader))`, a mimo to błąd przeszedł do scalenia. Są dwie możliwości:
   EditMode nie był uruchomiony na tej gałęzi przed regeneracją albo `ShaderHasError` nie widzi błędów wariantów,
   które nie zostały jeszcze skompilowane. Edytor kompiluje warianty leniwie. To jest UNVERIFIED, nie sprawdzę tego
   bez Unity. **Poprawka:** w teście przed asercją wymusić kompilację przejścia
   `ShaderUtil.CompilePass(mat, mat.FindPass("ForwardLit"), true)` (API do potwierdzenia w 6000.3), a potem
   `ShaderUtil.GetShaderMessages(shader)` bez `ShaderCompilerMessageSeverity.Error`. Do tego regresja tekstowa
   `StringAssert.DoesNotContain("IsAlphaToMaskAvailable()", src FenceMeshForward.hlsl)`.
3. **`WorldFenceMesh.shader:144-185` DepthOnly zawsze ma `a2c = false`, a kolor pod MSAA używa połówek piksela.**
   Głębia (tekstura głębi, SSAO) jest więc „pikselowa”, a kolor „subpikselowy”. Bez depth priming
   (`Mobile_Renderer*.asset m_DepthPrimingMode: 0`) nie daje to dziur, tylko niewielką niezgodność maski SSAO. To jest
   znane z recenzji #109 (brak DepthNormals). Nie blokuje.

## Zgodność z CLAUDE.md
Ścieżka renderowania: brak C#, brak GC i brak wpływu na fizykę. Bez zmian w `ProjectSettings/`. Budżet: poprawka
nie zmienia instrukcji, liczby wariantów ani geometrii, więc koszt GPU jest taki, jak oszacowano w ADR 0239.
Po poprawce lider potwierdza wizualnie (VQA `kwadrat-park-gate`, Low i High), że płot nie jest magentą. Komendy
w ADR 0239 §„Weryfikacja”.
