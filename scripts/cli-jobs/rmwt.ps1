# Usuwanie worktree zlecen po scaleniu (lider). NAJPIERW odlacz junctiony (cmd /c rmdir), potem ten skrypt,
# potem: git worktree prune; git branch -D <galaz>.
# NIGDY nie usuwaj agent-a1e9a7a0a869fb425 ani agent-a492e5af856a32ed3 (dzialajace venv; Smart App Control) ani win-build.
# Uzycie: pwsh scripts/cli-jobs/rmwt.ps1 <nazwa-worktree> [<nazwa> ...]
param([string[]]$Names)
$R='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees'; $E="$env:TEMP\empty-rmwt"; New-Item -ItemType Directory -Force $E | Out-Null
$protected = 'agent-a1e9a7a0a869fb425','agent-a492e5af856a32ed3','win-build'
foreach($n in $Names){ if($protected -contains $n){ "$n PROTECTED - skip"; continue }
  $w="$R\$n"; if(-not (Test-Path $w)){ "$n missing"; continue }
  Get-ChildItem -Recurse -Depth 4 -Force $w -Attributes ReparsePoint -EA SilentlyContinue | ForEach-Object { cmd /c rmdir "$($_.FullName)" }
  $rp=(Get-ChildItem -Recurse -Force "$w\Data\raw" -Attributes ReparsePoint -EA SilentlyContinue | Measure-Object).Count
  if($rp -ne 0){ "$n has $rp junctions - skip"; continue }
  robocopy $E $w /MIR /NFL /NDL /NJH /NJS | Out-Null; Remove-Item -Recurse -Force $w -EA SilentlyContinue; "$n removed=$(-not (Test-Path $w))" }
