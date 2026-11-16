// URP Lit fragment scaffold: copyright Unity Technologies ApS, Unity Companion License.
// ADR 0239: URP Lit lighting unchanged (same UnityPerMaterial buffer, same PBR, fog, lights); only the alpha of the
// welded fence mesh is replaced by FenceMeshAlpha. _ALPHATEST_ON is not compiled in this pass, so
// InitializeStandardLitSurfaceData returns the raw texture alpha and does not discard.
#include "FenceMeshCoverage.hlsl"

void FenceMeshFragment(Varyings input, out half4 outColor : SV_Target0)
{
    UNITY_SETUP_INSTANCE_ID(input);
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);

    SurfaceData surfaceData;
    InitializeStandardLitSurfaceData(input.uv, surfaceData);
    // Derivatives are taken before the discard inside.
    // URP declares IsAlphaToMaskAvailable() only under _ALPHATEST_ON (ShaderVariablesFunctions.hlsl), which this pass does not
    // compile; the global behind it (Input.hlsl) is always declared. With the helper the pass failed to compile (magenta fence).
    half coverage = FenceMeshAlpha(surfaceData.alpha, _Cutoff, input.uv, input.positionCS.xy, _AlphaToMaskAvailable != 0.0);

    InputData inputData;
    InitializeInputData(input, surfaceData.normalTS, inputData);
    SETUP_DEBUG_TEXTURE_DATA(inputData, UNDO_TRANSFORM_TEX(input.uv, _BaseMap));

    InitializeBakedGIData(input, inputData);

    half4 color = UniversalFragmentPBR(inputData, surfaceData);
    color.rgb = MixFog(color.rgb, inputData.fogCoord);
    color.a = coverage;
    outColor = color;
}
