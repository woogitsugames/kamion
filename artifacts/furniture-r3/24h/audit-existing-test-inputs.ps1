param([ValidateSet('pre','final')][string]$Phase='pre')
# Small read-only hash audit; never a pytest, generator, GLB or image job.
$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r3/24h'
$baseline='162214c3'
$region='Data/Regions/bialystok-industrial-c'
$report="$region/generated/fidelity_qa.json"
$qa=Get-Content -LiteralPath $report -Raw|ConvertFrom-Json
$sha=[Security.Cryptography.SHA256]::Create()
try{
    $rows=@(foreach($entry in $qa.inputs_sha256.PSObject.Properties){
        $path=if($entry.Name.Contains('/')){$entry.Name}else{"$region/$($entry.Name)"}
        $bytes=[IO.File]::ReadAllBytes((Join-Path (Get-Location) $path))
        $actual=[Convert]::ToHexString($sha.ComputeHash($bytes)).ToLowerInvariant()
        $lf=[Text.Encoding]::UTF8.GetBytes([Text.Encoding]::UTF8.GetString($bytes).Replace("`r`n","`n"))
        $normalized=[Convert]::ToHexString($sha.ComputeHash($lf)).ToLowerInvariant()
        $baseBlob=(& git rev-parse ('{0}:{1}' -f $baseline,$path)).Trim()
        $headBlob=(& git rev-parse ('HEAD:{0}' -f $path)).Trim()
        $workingBlob=(& git hash-object -- $path).Trim()
        [pscustomobject]@{file=$path;expected_sha256=$entry.Value;actual_sha256=$actual;lf_sha256=$normalized;
            raw_matches=$actual -eq $entry.Value;lf_matches=$normalized -eq $entry.Value;
            baseline_blob=$baseBlob;current_blob=$headBlob;working_blob=$workingBlob;
            unchanged_from_round_base=($baseBlob -eq $headBlob -and $headBlob -eq $workingBlob)}
    })
    $reportBase=(& git rev-parse ('{0}:{1}' -f $baseline,$report)).Trim()
    $reportCurrent=(& git hash-object -- $report).Trim()
    $physics=@(foreach($path in @('tests/physics/test_scenario_strictness.py','tests/physics/generate_stage2_scenarios.py','tests/physics/scenarios/top_speed_flat_comb.json')){
        $base=(& git rev-parse ('{0}:{1}' -f $baseline,$path)).Trim()
        $current=(& git hash-object -- $path).Trim()
        [pscustomobject]@{file=$path;baseline_blob=$base;current_blob=$current;unchanged=$base -eq $current}
    })
    $out=[pscustomobject]@{phase=$Phase;checked_at=(Get-Date -Format o);head=(& git rev-parse HEAD);baseline=$baseline;
        kind='read-only input audit, not a test result';inputs=$rows.Count;
        raw_stale=@($rows|Where-Object {!$_.raw_matches}).Count;
        lf_stale=@($rows|Where-Object {!$_.lf_matches}).Count;
        all_inputs_unchanged=@($rows|Where-Object {!$_.unchanged_from_round_base}).Count -eq 0;
        report_unchanged=$reportBase -eq $reportCurrent;fidelity=$rows;physics=$physics}
    $out|ConvertTo-Json -Depth 6|Set-Content "$ev/existing-test-input-audit-$Phase.json"
    $out|Select-Object phase,baseline,kind,inputs,raw_stale,all_inputs_unchanged,report_unchanged|ConvertTo-Json -Compress
}finally{$sha.Dispose()}
