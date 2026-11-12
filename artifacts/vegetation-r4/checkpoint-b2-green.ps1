$ErrorActionPreference='Stop'
. ./artifacts/vegetation-r4/checkpoint.ps1
$session=Get-Content artifacts/vegetation-r4/session.json -Raw | ConvertFrom-Json
$session.phase='candidate_b2_world_running'
$session.next_step='Live task87809:33focused tests passed10.29s, World B2 now running in same heavy slot, then collision digest and release. Do not duplicate generation. After exit0 and green-b-and-world.done run candidate-b-probe.ps1 for light pins, Unity import and16frames; review and critic before full matrix.'
$session.state_authority='Live task87809, pytest-green-b.log timestamp12:39 and STATUS.md. Old loft failure retained separately. World B2 pending, no candidate-b snapshot/probe yet.'
$session | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 artifacts/vegetation-r4/session.json
Add-Content artifacts/vegetation-r4/STATUS.md 'B2:33passed w10,29s po otrzymaniu heavy wFIFO. Testy obejmują wspólny podział capów i pełny prześwit, granice pasów/CDT, UV, Z, bliskie punkty krawędzi i pędy; to nie wizualnyPASS. Job87809 uruchomił World B2 około12:39 wtym samym slocie, potem zapisze kolizję. Nie uruchomiono drugiej kopii ani materiałów. Następny krok po0: candidate-b-probe.ps1.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 B2 33 testy passed i generacja w toku' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/session.json','artifacts/vegetation-r4/checkpoint-b2-green.ps1')
