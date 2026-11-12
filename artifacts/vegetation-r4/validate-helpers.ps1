$ErrorActionPreference='Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
$result=@()
foreach($file in Get-ChildItem artifacts/vegetation-r4 -Filter *.ps1) {
    $parseTokens=$null
    $parseErrors=$null
    [Management.Automation.Language.Parser]::ParseFile($file.FullName,[ref]$parseTokens,[ref]$parseErrors) | Out-Null
    $result += [pscustomobject]@{file=$file.Name;errors=@($parseErrors | ForEach-Object Message)}
}
$result | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 artifacts/vegetation-r4/powershell-syntax.json
if (@($result | Where-Object {$_.errors.Count -gt 0}).Count) { throw 'PowerShell helper syntax errors' }
