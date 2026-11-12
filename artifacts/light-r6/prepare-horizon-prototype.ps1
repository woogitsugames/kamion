$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')); Set-Location $repo
$destination=Join-Path $PSScriptRoot 'horizon-prototype'
New-Item -ItemType Directory -Force $destination|Out-Null
$inventory=@()
function SaveCandidate([string]$relative,[scriptblock]$edit){
    $source=Get-Content -LiteralPath $relative -Raw
    $candidate=& $edit $source
    $target=Join-Path $destination ([IO.Path]::GetFileName($relative))
    [IO.File]::WriteAllText($target,$candidate,[Text.UTF8Encoding]::new($false))
    $script:inventory+=@{source=$relative;sourceSha=(Get-FileHash -LiteralPath $relative).Hash;candidate=$target;candidateSha=(Get-FileHash -LiteralPath $target).Hash}
}
function ReplaceOnce([string]$source,[string]$old,[string]$new){
    if([regex]::Matches($source,[regex]::Escape($old)).Count -ne 1){throw "Expected exactly one anchor: $old"}
    return $source.Replace($old,$new)
}
SaveCandidate 'game/Assets/_Project/Rendering/Runtime/Sky/WorldAtmosphere.cs' {
    param($s)
    $s=ReplaceOnce $s 'public static float? ClearCloudCoverOverride;' "public static float? ClearCloudCoverOverride;`r`n        /// <summary>rq_cloudhorizon: preserve the photographic horizon; default remains full sun alignment.</summary>`r`n        public static bool? ClearCloudHorizonOverride;"
    $s=ReplaceOnce $s 'PhotographicClouds.SourceRotation(sun, sourceSun)' 'PhotographicClouds.SourceRotation(sun, sourceSun, ClearCloudHorizonOverride ?? p.clearCloudHorizonLocked)'
    $s=ReplaceOnce $s 'public static Quaternion SourceRotation(Vector3 sun, Vector3 sourceSun)' 'public static Quaternion SourceRotation(Vector3 sun, Vector3 sourceSun, bool keepHorizon = false)'
    $s=ReplaceOnce $s 'return Quaternion.FromToRotation(yaw * sun, sourceSun) * yaw;' "// Horizon lock trades source-sun elevation matching for a stable photographic dome. No shader change.`r`n            return keepHorizon ? yaw : Quaternion.FromToRotation(yaw * sun, sourceSun) * yaw;"
    return $s
}
SaveCandidate 'game/Assets/_Project/Rendering/Runtime/Sky/LightingPreset.cs' {
    param($s)
    ReplaceOnce $s '[Range(0f, 5f)] public float clearCloudSourceMinElevationDeg;' "[Range(0f, 5f)] public float clearCloudSourceMinElevationDeg;`r`n        [Tooltip(`"Optional horizon-preserving cloud rotation. Matches source sun azimuth only, not elevation. Working visual approximation, default off.`")]`r`n        public bool clearCloudHorizonLocked;"
}
SaveCandidate 'game/Assets/_Project/Rendering/Runtime/RenderOverrides.cs' {
    param($s)
    $s=ReplaceOnce $s 'WorldAtmosphere.ClearCloudCoverOverride = F(arg("rq_clearcover"));' "WorldAtmosphere.ClearCloudHorizonOverride = B(arg(`"rq_cloudhorizon`"));`r`n            WorldAtmosphere.ClearCloudCoverOverride = F(arg(`"rq_clearcover`"));"
    ReplaceOnce $s 'gvar.HasValue || WorldAtmosphere.ClearCloudCoverOverride.HasValue' 'gvar.HasValue || WorldAtmosphere.ClearCloudHorizonOverride.HasValue || WorldAtmosphere.ClearCloudCoverOverride.HasValue'
}
SaveCandidate 'game/Assets/_Project/Rendering/Editor/LightQaBatch.cs' {
    param($s)
    $s=ReplaceOnce $s 'public bool overrideCloudSourceMin;' "public bool overrideSunElevation;`r`n            public float sunElevationDeg;`r`n            public bool overrideCloudSourceMin;"
    $s=ReplaceOnce $s '                    if (job.overrideCloudSourceMin)' @'
                    if (job.overrideSunElevation)
                    {
                        if (float.IsNaN(job.sunElevationDeg) || float.IsInfinity(job.sunElevationDeg) ||
                            job.sunElevationDeg < SkyModel.MinTwilightElevationDeg || job.sunElevationDeg > 89.5f)
                            throw new ArgumentException("Sun elevation outside model bounds");
                        presetSnapshots.Keys.Single(p => string.Equals(p.name, "LP_" + job.lighting,
                            StringComparison.OrdinalIgnoreCase)).sunElevationDeg = job.sunElevationDeg;
                    }
                    if (job.overrideCloudSourceMin)
'@
    $s=ReplaceOnce $s '                    var actualFilter = environment.sun.GetUniversalAdditionalLightData().softShadowQuality;' @'
                    if (job.overrideSunElevation && Mathf.Abs(environment.Model.TrueSunElevationDeg-job.sunElevationDeg) > 0.001f)
                        throw new InvalidOperationException("Requested sun elevation was not retained by the lighting model");
                    var actualFilter = environment.sun.GetUniversalAdditionalLightData().softShadowQuality;
'@
    return $s
}
SaveCandidate 'game/Assets/_Project/Rendering/Editor/LightQaLampProbe.cs' {
    param($s)
    $s=ReplaceOnce $s 'public Vector4 cloudSourceLimits;' "public Vector4 cloudSourceLimits;`r`n            public float actualClearCloudCover, actualClearCloudPhoto;`r`n            public Vector4 actualCloud, actualHaze, actualSkyCap;`r`n            public Vector3 actualCloudRotationUp;`r`n            public bool requestedHorizonLock;"
    $s=ReplaceOnce $s '                cloudSourceLimits = Shader.GetGlobalVector("_KamionClearCloudSourceLimits"),' @'
                cloudSourceLimits = Shader.GetGlobalVector("_KamionClearCloudSourceLimits"),
                actualClearCloudCover = Shader.GetGlobalFloat("_KamionClearCloudCover"),
                actualClearCloudPhoto = Shader.GetGlobalFloat("_KamionClearCloudPhoto"),
                actualCloud = Shader.GetGlobalVector("_KamionCloud"),
                actualHaze = Shader.GetGlobalVector("_KamionHaze"),
                actualSkyCap = Shader.GetGlobalVector("_KamionSkyCap"),
                actualCloudRotationUp = Shader.GetGlobalMatrix("_KamionClearCloudRotation").MultiplyVector(Vector3.up),
                requestedHorizonLock = WorldAtmosphere.ClearCloudHorizonOverride ?? environment.Active.clearCloudHorizonLocked,
'@
    return $s
}
$inventory|ConvertTo-Json -Depth 5|Set-Content "$destination/sources.json" -Encoding utf8
Write-Output 'Prepared uncompiled artifact copies only. No game source was changed.'
