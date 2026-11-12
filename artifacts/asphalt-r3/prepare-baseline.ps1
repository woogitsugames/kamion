$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ((& git branch --show-current).Trim() -ne 'gpt-asphalt-r3') { throw 'Wrong round' }
$main='C:/Users/matma/Documents/Claude/kamion'
$work=(Get-Location).Path
if ([IO.Path]::GetFullPath($work) -ne [IO.Path]::GetFullPath("$main/.claude/worktrees/gpt-asphalt")) { throw 'Unexpected worktree' }
$copies=@('Data/raw/cc0','art-source/world/cc0/_raw','art-source/world/megascans')
foreach($rel in $copies){
    if(-not(Test-Path -LiteralPath "$main/$rel")){throw "Missing raw source $rel"}
    $log="artifacts/asphalt-r3/copy-$($rel -replace '/','-').log"
    & robocopy "$main/$rel" "$work/$rel" /E /XJ /MT:2 /R:2 /W:2 /NFL /NDL /NP "/LOG:$log"
    if($LASTEXITCODE -ge 8){throw "Raw resource copy failed: $rel"}
}
Add-Content artifacts/asphalt-r3/STATUS.md "$(Get-Date -Format o): Przyrostowo uzupełniono rawCC0 i Megascans z main bez usuwania plików. Następne Materials/World pod heavy; nie kopiowano Library ani nie używano Unity."
git add -f artifacts/asphalt-r3/STATUS.md
git commit -q -m 'wip(asphalt): refresh baseline raw material dependencies from main' 2> artifacts/asphalt-r3/git-checkpoint-warnings.log
& pwsh artifacts/asphalt-r3/run-heavy.ps1 -Stage Materials -Label baseline
if($LASTEXITCODE -ne 0){throw 'Baseline material build failed'}
& pwsh artifacts/asphalt-r3/run-heavy.ps1 -Stage World -Label baseline
if($LASTEXITCODE -ne 0){throw 'Baseline world build failed'}
if(Select-String -Path artifacts/asphalt-r3/baseline-World.log -SimpleMatch 'fallback=True' -Quiet){throw 'Megascans fallback present'}
Add-Content artifacts/asphalt-r3/STATUS.md "$(Get-Date -Format o): Materiały i świat baseline r3 zakończone; brak fallback=True. Następny krok: źródłowa sonda materiałów placu i wysokości, przygotowanie kamer oraz import/capture Low/High clear/overcast."
git add -f artifacts/asphalt-r3/STATUS.md
git commit -q -m 'wip(asphalt): checkpoint fresh round three material and world baseline' 2> artifacts/asphalt-r3/git-checkpoint-warnings.log
'Baseline producers complete; no Unity capture has run yet.'
