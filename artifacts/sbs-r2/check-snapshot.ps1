$ErrorActionPreference='Stop'
$scriptAst=[System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path scripts/sbs-gate3.ps1),[ref]$null,[ref]$null)
$definition=$scriptAst.Find({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Save-EvidenceInputs'},$true)
. ([scriptblock]::Create($definition.Extent.Text))
$fixtureRoot=Join-Path $PSScriptRoot ('snapshot-fixture-'+[Guid]::NewGuid().ToString('N'))
$taskRoot=$fixtureRoot;$output=Join-Path $fixtureRoot 'evidence';$Tiers=@('Low');$Lighting=@('clear');$IncludeDiagnostics=$false;$Photometry=''
$region=Join-Path $taskRoot 'Data/Regions/bialystok-industrial-c'
New-Item -ItemType Directory -Force "$region/generated","$taskRoot/art-source/world/materials","$output/renders/Low-clear","$output/sheets/Low-clear" | Out-Null
$cameraFile=Join-Path $region 'sbs_cameras.json'
$coreFiles=@{cameras_sha256=$cameraFile;references_sha256="$region/sbs_references.json";world_manifest_sha256="$region/generated/world_manifest.json";materials_spec_sha256="$taskRoot/art-source/world/materials/materials_spec.json"}
$capture=@{status='OK';git_sha='fixture-epoch'}
foreach($key in $coreFiles.Keys){'{"fixture":true}' | Set-Content -LiteralPath $coreFiles[$key] -Encoding utf8;$capture[$key]=(Get-FileHash $coreFiles[$key]).Hash.ToLowerInvariant()}
$photo="$region/sbs_photometry.json";'{"annotations":[]}' | Set-Content $photo -Encoding utf8
$metrics=@{photometry_sha256=(Get-FileHash $photo).Hash.ToLowerInvariant();landmarks_sha256=$null}
$capture | ConvertTo-Json | Set-Content "$output/renders/Low-clear/capture-test.json" -Encoding utf8
$metrics | ConvertTo-Json | Set-Content "$output/sheets/Low-clear/metrics.json" -Encoding utf8
Save-EvidenceInputs
if(!(Test-Path "$output/inputs.zip") -or !(Test-Path "$output/inputs/sbs_photometry.json")){throw 'Initial snapshot missing'}
# Removing a sidecar must not preserve an old optional copy in final inputs.
Remove-Item -LiteralPath $photo
$metrics.photometry_sha256=$null;$metrics | ConvertTo-Json | Set-Content "$output/sheets/Low-clear/metrics.json" -Encoding utf8
Save-EvidenceInputs
if(Test-Path "$output/inputs/sbs_photometry.json"){throw 'Obsolete annotation survived'}
$zip=[IO.Compression.ZipFile]::OpenRead("$output/inputs.zip")
try{if($zip.Entries.Name -contains 'sbs_photometry.json'){throw 'Obsolete ZIP annotation survived'}}finally{$zip.Dispose()}
# A changed sidecar cannot be published over the valid snapshot.
'{"annotations":[1]}' | Set-Content $photo -Encoding utf8
$rejected=$false
try{Save-EvidenceInputs}catch{if($_.Exception.Message -notlike '*annotations differ*'){throw};$rejected=$true}
if(!$rejected){throw 'Changed annotation accepted'}
if(Test-Path "$output/inputs/sbs_photometry.json"){throw 'Failed snapshot was published'}
# A changed core input cannot be published either.
Remove-Item -LiteralPath $photo
'{"changed":true}' | Set-Content $cameraFile -Encoding utf8
$rejected=$false
try{Save-EvidenceInputs}catch{if($_.Exception.Message -notlike '*differs from captures*'){throw};$rejected=$true}
if(!$rejected){throw 'Changed camera accepted'}
Write-Output 'PASS: initial snapshot, optional removal, ZIP roster, changed annotation rejection, changed camera rejection, preserved valid snapshot.'
