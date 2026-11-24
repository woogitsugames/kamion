# Start a delegated CLI job in its own worktree. Usage:
#   pwsh scripts/cli-jobs/start-job.ps1 -Name neon-x-s24 -Tool neon|mistral [-CopyDerived] [-Model gemini-4-neon-high] [-MaxPrice 3] [-TimeLimit 5400]
# Prompt: artifacts/<Name>/task.md (RULES.md is prepended). Output: artifacts/<Name>/cli.log, cli.status (exit=...).
param([Parameter(Mandatory)][string]$Name, [ValidateSet('neon','mistral')][string]$Tool = 'neon', [switch]$CopyDerived,
      [string]$Model = 'gemini-4-neon-high', [double]$MaxPrice = 3, [int]$TimeLimit = 5400)
$R = 'C:\Users\matma\Documents\Claude\kamion'; Set-Location $R
$o = "$R\artifacts\$Name"; New-Item -ItemType Directory -Force $o | Out-Null
$wt = "$R\.claude\worktrees\$Name"
if (-not (Test-Path $wt)) {
    $a = @('-NoProfile','-File','scripts/new-agent-worktree.ps1','-Name',$Name); if ($CopyDerived) { $a += '-CopyDerived' }
    pwsh @a *> "$o\worktree.log"
}
$prompt = "Worktree: $wt (gałąź $Name). Nazwa zadania: $Name.`n`n" + (Get-Content "$R\scripts\cli-jobs\RULES.md" -Raw) + "`n`n" + (Get-Content "$o\task.md" -Raw)
Set-Content "$o\prompt.full.md" $prompt -Encoding utf8
$runner = "$o\run.ps1"
if ($Tool -eq 'neon') {
@"
Set-Location '$wt'
`$p = Get-Content '$o\prompt.full.md' -Raw
& 'C:\Users\matma\AppData\Local\agy\bin\agy.exe' -p `$p --model $Model --dangerously-skip-permissions --add-dir '$wt' *> '$o\cli.log'
"exit=`$LASTEXITCODE `$(Get-Date -Format s)" | Out-File '$o\cli.status'
Get-ChildItem '$R\artifacts\locks\heavy-slots' -Filter '$Name*.slot' -EA SilentlyContinue | Remove-Item -Force
"@ | Set-Content $runner -Encoding utf8
} else {
@"
Set-Location '$wt'
& 'C:\Users\matma\.local\bin\vibe.exe' --prompt-file '$o\prompt.full.md' --workdir '$wt' --max-price $MaxPrice --time-limit $TimeLimit --output-dir '$o\vibe-out' --auto-approve *> '$o\cli.log'
"exit=`$LASTEXITCODE `$(Get-Date -Format s)" | Out-File '$o\cli.status'
Get-ChildItem '$R\artifacts\locks\heavy-slots' -Filter '$Name*.slot' -EA SilentlyContinue | Remove-Item -Force
"@ | Set-Content $runner -Encoding utf8
}
$p = Start-Process pwsh -ArgumentList '-NoProfile','-File',$runner -WindowStyle Hidden -PassThru
"started $Name tool=$Tool pid=$($p.Id) $(Get-Date -Format s)" | Tee-Object "$o\cli.status"
