$ErrorActionPreference='Stop'
Set-Location 'C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/knyszyn-rynek-0227'
try {
 if ((Get-PSDrive C).Free -lt 60GB) { throw 'C below 60 GiB' }
 & pwsh scripts/unity-slot.ps1 -Acquire -Owner knyszyn-editmode-0227
 if ($LASTEXITCODE -ne 0) { throw 'slot acquisition failed' }
 try {
  if (Test-Path C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN) { throw 'PHONE_RUN appeared after slot acquisition' }
  & pwsh scripts/test.ps1 -Platform EditMode
  if ($LASTEXITCODE -ne 0) { throw "EditMode exit $LASTEXITCODE" }
 } finally { & pwsh scripts/unity-slot.ps1 -Release -Owner knyszyn-editmode-0227 }
 'OK' | Set-Content artifacts/knyszyn-rynek-0227/editmode-r4.done
} catch { $_ | Out-String | Set-Content artifacts/knyszyn-rynek-0227/editmode-r4.done; exit 1 }
