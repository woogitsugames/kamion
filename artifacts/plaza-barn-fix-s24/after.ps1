# plaza-barn-fix-s24: wait until both "before" pipelines are done (their imports read derived), then build + render "after"
$ErrorActionPreference = 'Continue'
$logs = "$PSScriptRoot\logs"
foreach ($f in 'pipeline-before-tykocin.log', 'pipeline-before-dk65.log') {
    while (-not (Select-String -Path "$logs\$f" -Pattern 'PIPELINE DONE|exit 1' -Quiet -ErrorAction SilentlyContinue)) { Start-Sleep 30 }
}
pwsh -NoProfile -File "$PSScriptRoot\pipeline.ps1" -Tag after
