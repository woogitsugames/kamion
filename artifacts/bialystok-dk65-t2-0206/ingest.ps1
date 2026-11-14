$ErrorActionPreference = 'Continue'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bialystok-dk65-t2-0206'
$n = 'bialystok-dk65-t2-0206'; $R = 'bialystok-kleeberga'
uv run --project tools/worldgen tools/worldgen/ingest.py --region $R *> "artifacts/$n/ingest.log"
"ingest exit=$LASTEXITCODE $(Get-Date -Format s)" | Set-Content "artifacts/$n/ingest.done"
if ((Get-Content "artifacts/$n/ingest.done") -like 'ingest exit=0*') {
  uv run --project tools/worldgen tools/worldgen/build_region.py --region $R *> "artifacts/$n/build_region.log"
  "build_region exit=$LASTEXITCODE $(Get-Date -Format s)" | Set-Content "artifacts/$n/build_region.done"
}
