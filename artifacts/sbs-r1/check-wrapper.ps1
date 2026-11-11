$ErrorActionPreference='Stop'
foreach($file in @('scripts/sbs-gate3.ps1','artifacts/sbs-r1/run-heavy.ps1','artifacts/sbs-r1/import-and-baseline.ps1','artifacts/sbs-r1/render-pose-probes.ps1')) {
    $parseErrors=$null
    [System.Management.Automation.Language.Parser]::ParseFile((Join-Path (Get-Location) $file),[ref]$null,[ref]$parseErrors) | Out-Null
    if($parseErrors.Count -gt 0){$parseErrors;throw "Błąd składni $file"}
    "PARSE OK $file"
}
