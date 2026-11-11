$ErrorActionPreference='Stop'
if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned'}
pwsh -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot/../../scripts/test.ps1" -Platform EditMode -Filter TruckDoorCrownTests
exit $LASTEXITCODE
