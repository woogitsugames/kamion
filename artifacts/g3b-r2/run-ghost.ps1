# Ghost diagnosis (ADR 0139): camera 494288 Low overcast with render-override ablations, one Unity slot.
param([string[]]$Variants = @('base=', 'a2c0=rq_a2c=0', 'msaa1=rq_msaa=1', 'hlod0=rq_hlod=0', 'veg0=rq_vegshader=0'), [string]$Camera = 'sbs-g3-b-494288258686575', [string]$Lighting = 'overcast')
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$cameraFile = Join-Path $root 'Data/Regions/bialystok-industrial-c/sbs_cameras.json'
& pwsh -NoProfile -File $slot -Acquire -Owner claude-g3b-r2 -PollSeconds 10
try {
    Push-Location $root
    foreach ($v in $Variants) {
        $name, $rq = $v -split '=', 2
        $out = Join-Path $PSScriptRoot "diag\ghost\$name"
        $a = @{ Scene = 'WorldC'; Tier = 'Low'; Lighting = $Lighting; Width = 1280; Height = 960; Gate3 = $cameraFile; Cameras = $Camera; OutputDir = $out }
        if ($rq) { $a.Rq = $rq }
        & (Join-Path $root 'scripts/visual-qa.ps1') @a *> (Join-Path $PSScriptRoot "diag\ghost-$name.log")
        "$name exit=$LASTEXITCODE"
    }
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-g3b-r2
    Pop-Location
}
