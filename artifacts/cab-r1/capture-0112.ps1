param([ValidatePattern('^(baseline|result-0112(?:-[A-Za-z0-9-]+)?)$')][string]$Stage='baseline')
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ((git branch --show-current) -ne 'gpt-cab-r1') { throw 'Uruchom wyłącznie w worktree cab rundy 1.' }
. ./scripts/env.ps1
$SlotScript='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
function Invoke-CabUnity([string]$Log,[string[]]$UnityArgs) {
    pwsh $SlotScript -Acquire -Owner gpt-cab -PollSeconds 5 -StaleHours 1000000
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
    try { $code=Invoke-UnityBatch -LogFile $Log -Arguments $UnityArgs; if ($code -ne 0) { throw "Unity exit $code, log: $Log" } }
    finally { pwsh $SlotScript -Release -Owner gpt-cab; git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings }
}
foreach ($tier in @('Low','High')) {
    $scene=if($tier -eq 'High'){'WorldC_High'}else{'WorldC'}
    foreach ($light in @('clear','overcast')) {
        $output="$PWD/artifacts/cab-r1/$Stage/$tier-$light"
        if (-not (Test-Path "$output/stats.txt")) {
            pwsh $SlotScript -Acquire -Owner gpt-cab -PollSeconds 5 -StaleHours 1000000
            if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
            try {
                pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $light -Width 1920 -Height 1080 -Cameras 'cab-driver,cab-dash,cab-mirrors-left,cab-mirrors-right,cab-mirror-front,cab-grain,cab-seat-entry' -OutputDir $output
                if ($LASTEXITCODE -ne 0) { throw "Błąd renderu $tier $light" }
            }
            finally { pwsh $SlotScript -Release -Owner gpt-cab; git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings }
        }
        if (-not (Test-Path "$output/native-mirrors/interior-pixels.tsv") -or -not (Test-Path "$output/native-mirrors/budgets.txt")) {
            Invoke-CabUnity "$PWD/artifacts/cab-r1/$Stage-native-$tier-$light.log" @('-executeMethod','Game.Editor.VisualQA.CabMirrorAudit.Run','-cabTier',$tier,'-cabLighting',$light,'-cabOutput',"$output/native-mirrors")
        }
        Add-Content artifacts/cab-r1/STATUS.md "Zapisano $Stage $tier $light, siedem kamer i sześć natywnych RT z identyfikatorem wnętrza. Następny krok: kontynuować macierz lub porównać PNG."
        git add -f artifacts/cab-r1/STATUS.md
        git commit -m "wip(cab): capture $Stage $tier $light mirror evidence"
    }
}
