$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Shared Unity guard active'}
$p='game/Assets/_Project/Environment/Shaders/WorldPBR.shader'
$bytes=[IO.File]::ReadAllBytes([IO.Path]::GetFullPath($p))
try {
 $s=[IO.File]::ReadAllText([IO.Path]::GetFullPath($p))
 $anchor='half3 albedo = base.rgb * _Tint.rgb * _AlbedoScale;'
 $s=$s.Replace($anchor,"#if defined(_CARPAINT)`nreturn half4(carFilmOpacity, i.carFilm.x, saturate(um.y), 1);`n#endif`n"+$anchor)
 [IO.File]::WriteAllText([IO.Path]::GetFullPath($p),$s,[Text.UTF8Encoding]::new($false))
 & pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene WorldC_High -Tier High -Lighting overcast -Gate3 artifacts/car-paint-r1/r1-cameras.json -Cameras g_dirt_level_0,g_dirt_level_1,g_dirt_level_2,g_dirt_level_3,r10b_black_05 -OutputDir artifacts/car-paint-r1/r1-film-diagnostic
 if($LASTEXITCODE-ne0){throw 'Film diagnostic failed'}
} finally {
 [IO.File]::WriteAllBytes([IO.Path]::GetFullPath($p),$bytes)
 git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting
}
