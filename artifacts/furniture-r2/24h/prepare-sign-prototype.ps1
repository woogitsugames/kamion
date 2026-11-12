$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$urp=Get-ChildItem game/Library/PackageCache -Directory -Filter 'com.unity.render-pipelines.universal@*' | Select-Object -First 1
if (!$urp) { throw 'Installed URP source not found' }
$out="$PSScriptRoot/candidate-src"
New-Item -ItemType Directory -Force $out | Out-Null
$lit=Get-Content "$($urp.FullName)/Shaders/Lit.shader" -Raw
$end=$lit.IndexOf('ENDHLSL')
if ($end -lt 0) { throw 'Forward pass not found' }
$end=$lit.IndexOf('}', $end)+1
$shader=$lit.Substring(0,$end).Replace('Shader "Universal Render Pipeline/Lit"','Shader "Kamion/Furniture Sign"')
$shader=$shader.Replace('#pragma fragment LitPassFragment','#pragma fragment FurnitureSignFragment')
# The return coefficient uses the existing Lit constant-buffer slot. It is NEVER ordinary emission.
$shader=[regex]::Replace($shader,'(?m)^\s*#pragma shader_feature_local_fragment _EMISSION\r?\n','')
$shader=$shader.Replace('#include "Packages/com.unity.render-pipelines.universal/Shaders/LitForwardPass.hlsl"',
    '#include "Packages/com.unity.render-pipelines.universal/Shaders/LitForwardPass.hlsl"'+"`n"+
    '            #pragma shader_feature_local_fragment _FURNITURE_RETRO'+"`n"+
    '            #include "FurnitureSignForward.hlsl"')
$shader=$shader.Replace('[HDR] _EmissionColor("Color", Color)', '[HDR] _EmissionColor("Retro return coefficient (WORKING_VALUE)", Color)')
$shader='// URP Lit scaffold: copyright Unity Technologies ApS, Unity Companion License.'+"`n"+
    '// Forward source pinned to installed URP; all other passes and UnityPerMaterial layout remain URP Lit.'+"`n"+$shader
foreach ($pass in @('ShadowCaster','GBuffer','DepthOnly','DepthNormals','Meta','Universal2D','MotionVectors','XRMotionVectors')) {
    $shader+="`n        UsePass `"Universal Render Pipeline/Lit/$pass`""
}
$shader+="`n    }`n    FallBack `"Hidden/Universal Render Pipeline/FallbackError`"`n}`n"
Set-Content "$out/FurnitureSign.shader" $shader -Encoding utf8
$forward=Get-Content "$($urp.FullName)/Shaders/LitForwardPass.hlsl" -Raw
$start=$forward.IndexOf('void LitPassFragment(')
if ($start -lt 0) { throw 'Installed Lit fragment signature changed' }
$fragment=$forward.Substring($start,$forward.LastIndexOf('#endif')-$start)
$fragment=$fragment.Replace('void LitPassFragment(', 'void FurnitureSignFragment(')
$fragment=$fragment.Replace('    color.rgb = MixFog(color.rgb, inputData.fogCoord);',
    '    #if defined(_FURNITURE_RETRO)'+"`n"+
    '    color.rgb += FurnitureReturnedLight(inputData.positionWS, inputData.normalWS, inputData.viewDirectionWS) * surfaceData.albedo;'+"`n"+
    '    #endif'+"`n"+'    color.rgb = MixFog(color.rgb, inputData.fogCoord);')
$header=Get-Content "$out/FurnitureSignReturn.hlsl" -Raw
Set-Content "$out/FurnitureSignForward.hlsl" ($header+"`n"+$fragment) -Encoding utf8
[pscustomobject]@{urp=$urp.Name;source_shader_sha256=(Get-FileHash "$($urp.FullName)/Shaders/Lit.shader").Hash;
    source_fragment_sha256=(Get-FileHash "$($urp.FullName)/Shaders/LitForwardPass.hlsl").Hash;
    baseline_passes=([regex]::Matches($lit, '(?m)^\s*Name "').Count);candidate_passes=([regex]::Matches($shader, '(?m)^\s*(Name|UsePass) "').Count);status='PROTOTYPE, not imported or validated'} |
    ConvertTo-Json | Set-Content "$out/provenance.json" -Encoding utf8

