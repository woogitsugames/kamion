$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$wt='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\seams-p3-s24'; $main='C:\Users\matma\Documents\Claude\kamion'
Set-Location $wt
$out="$wt\artifacts\seams-p3-s24"; $st="$out\rebuild.status"; New-Item -ItemType Directory -Force "$out\logs" | Out-Null
foreach ($t in 'knyszyn-w','dk65-monki-01','bialystok-knyszynska','dk65-01','knyszyn-s','knyszyn') {
  $log="$out\logs\build-$t.log"
  pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Acquire -Pool heavy -Owner seams-p3-s24 *>> $log
  $t0=Get-Date
  uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $t --context *>> $log; $e1=$LASTEXITCODE
  uv run --project tools/worldgen python scripts/export-route.py --region $t *>> $log; $e2=$LASTEXITCODE
  pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Release -Pool heavy -Owner seams-p3-s24 *>> $log
  Add-Content $st ("{0} tile={1} build_exit={2} route_exit={3} s={4:N0}" -f (Get-Date -Format s),$t,$e1,$e2,((Get-Date)-$t0).TotalSeconds)
}
Add-Content $st "$(Get-Date -Format s) DONE"
