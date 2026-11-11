Set-Location (Split-Path (Split-Path $PSScriptRoot))
$o = 'artifacts/perf-low-r2/vqa'
foreach ($r in @(@('overcast','before','rq_forestfast=0'), @('overcast','after',''), @('clear','before','rq_forestfast=0'), @('clear','after',''))) {
    while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
    $a = @('-NoProfile','-File','scripts/visual-qa.ps1','-Scene','WorldC','-Tier','Low','-Lighting',$r[0],'-OutputDir',"$o/$($r[1])-$($r[0])")
    if ($r[2]) { $a += @('-Rq', $r[2]) }
    pwsh @a *> "$o-$($r[1])-$($r[0]).log"
}
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
'done' | Out-File "$o.done"
