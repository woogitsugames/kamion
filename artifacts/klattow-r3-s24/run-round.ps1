# One round: [build_world] -> import knyszyn (High materials) -> render control cameras (High clear) -> jpg copies.
param([Parameter(Mandatory)][string]$Tag, [switch]$World, [switch]$SkipImport, [string]$Sets = '',
      [string]$Cameras = 'look_dom_klattow,look_dom_klattow_street,look_dom_klattow_yard,look_dom_klattow_gable_e,look_lamus_plebanski')
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\klattow-r3-s24'
Set-Location $wt
$out = "$wt\artifacts\klattow-r3-s24\$Tag"; New-Item -ItemType Directory -Force $out | Out-Null
$st = "$wt\artifacts\klattow-r3-s24\$Tag.status"; "start $(Get-Date -Format HH:mm:ss)" | Set-Content $st
$owner = 'klattow-r3-s24'
function Step($name, [scriptblock]$b) { "$name start $(Get-Date -Format HH:mm:ss)" | Add-Content $st; & $b *>> "$out\$name.log"; "$name exit=$LASTEXITCODE $(Get-Date -Format HH:mm:ss)" | Add-Content $st; return $LASTEXITCODE }
try {
  if ($World) {
    pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $owner | Out-Null
    if ($Sets) {
      # only the sets whose generator changed; the other PNGs are byte-identical outputs of unchanged code, so their
      # mtime is moved past _src/*.py instead of an 18 min rebuild of every set (build_all.py --check compares mtimes)
      $c = Step 'mats' { uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only $Sets }
      if ($c -ne 0) { "exit=1 mats" | Add-Content $st; return }
      Get-ChildItem art-source/world/materials -Recurse -Filter *.png | Where-Object { $_.FullName -notmatch '_src|_renders' } | ForEach-Object { $_.LastWriteTime = Get-Date }
    }
    $c = Step 'world' { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region knyszyn }
    pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $owner | Out-Null
    if ($c -ne 0) { "exit=1 world" | Add-Content $st; return }
  }
  pwsh scripts/unity-slot.ps1 -Acquire -Owner $owner | Out-Null
  if (-not $SkipImport) {
    $c = Step 'import' { pwsh scripts/import-region.ps1 -Region knyszyn -BuildTarget Win64 -MaterialTier High }
    if ($c -ne 0) { "exit=1 import" | Add-Content $st; return }
  }
  $c = Step 'vqa' { pwsh scripts/visual-qa.ps1 -Scene World_knyszyn_High -Tier High -Lighting clear -Width 1920 -Height 1080 -BuildTarget Win64 -Cameras $Cameras -OutputDir $out }
  Get-ChildItem $out -Filter *.png | ForEach-Object { magick $_.FullName -resize 960x "$out\$($_.BaseName).jpg" }
  "exit=$c done $(Get-Date -Format HH:mm:ss)" | Add-Content $st
} finally {
  pwsh scripts/unity-slot.ps1 -Release -Owner $owner | Out-Null
  pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $owner | Out-Null
  git -C $wt checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
}
