$ErrorActionPreference='Stop'
. ./artifacts/vegetation-r4/checkpoint.ps1
$session=Get-Content artifacts/vegetation-r4/session.json -Raw | ConvertFrom-Json
$session.phase='candidate_a_world_running'
$session.next_step='Live task8662:18 focused tests passed in3.27s; World running, then collision digest and heavy release. After successful terminal result run candidate-a-probe.ps1. No duplicate generation.'
$session | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 artifacts/vegetation-r4/session.json
Add-Content artifacts/vegetation-r4/STATUS.md 'Kandydat A: 18 testów celowanych passed w 3,27 s. Zadanie 8662 po otrzymaniu heavy uruchomiło World około 10:35:28. Log: pass1 72,1 s, planowanie działek 190,5 s. Żywy proces Python 5324; nie uruchomiono drugiej generacji. Po World w tym samym slocie powstanie dekodowana migawka kolizji.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 utrwalony postęp generacji kandydata A' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/session.json','artifacts/vegetation-r4/checkpoint-world-running.ps1')
