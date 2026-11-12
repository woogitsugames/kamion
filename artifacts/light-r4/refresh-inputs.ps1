$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$main='C:/Users/matma/Documents/Claude/kamion'
foreach($relative in @('Data/raw/derived','Data/raw/cc0','art-source/world/cc0/_raw','art-source/world/megascans')) {
    $source=Join-Path $main $relative;$destination=Join-Path $repo $relative
    if(-not(Test-Path -LiteralPath $source)){throw "Missing authorized source$relative"}
    & robocopy $source $destination /E /R:1 /W:1 /NFL /NDL /NP /NJH /NJS
    if($LASTEXITCODE -gt 7){throw "Raw refresh failed$relative"}
}
git lfs checkout
if($LASTEXITCODE){throw 'LFS checkout failed'}
Add-Content "$PSScriptRoot/STATUS.md" 'Krok 1: surowe wejścia odświeżone z main przez robocopy bez usuwania i bez Library; git lfs checkout zakończony. Junctiony referencji pozostają tylko do odczytu. Następny krok: plansza i świeży generator/fidelity/import.'
git add -f artifacts/light-r4/STATUS.md
git commit -m 'WIP light r4: refresh raw inputs after current-main merge'

