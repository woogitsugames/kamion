$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$cameras = 'driver-andersa-to-putry,cab-dash,r10_block_3,r10_block_4,r10_house_2'
$gate = 'Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json'
foreach ($lighting in @('clear', 'overcast')) {
    foreach ($sharp in @('0', '0.25', '0.5', '0.75')) {
        $output = "artifacts/light-r1/rcas/High-$lighting-$sharp"
        & pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-light
        if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity' }
        try {
            & pwsh scripts/visual-qa.ps1 -Scene WorldC_High -Tier High -Lighting $lighting -Cameras $cameras -Gate3 $gate -Rq "rq_fsrsharp=$sharp" -OutputDir $output
            if ($LASTEXITCODE -ne 0) { throw "Nieudany render $output" }
        }
        finally {
            git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
            & pwsh scripts/unity-slot.ps1 -Release -Owner gpt-light
        }
        Add-Content artifacts/light-r1/STATUS.md "Render ablacji zakończony: $output. PNG wymagają obejrzenia i pomiarów. Następny krok: kolejny wariant w artifacts/light-r1/rcas-ablation.ps1, potem analiza."
        git add -f artifacts/light-r1/STATUS.md
        git commit -m "wip(light): zapisz render RCAS $lighting $sharp"
    }
}
