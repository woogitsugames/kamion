$ErrorActionPreference='Stop'
. ./artifacts/vegetation-r4/checkpoint.ps1
$session=Get-Content artifacts/vegetation-r4/session.json -Raw | ConvertFrom-Json
$session.phase='candidate_a_provenance_waiting_heavy'
$session.next_step='Live task85314 candidate-a-probe.ps1: queued heavy for snapshot and comparison, then Unity import and16frames. Task8662 terminal exit0,World538.6s and64collision digests complete. Do not rerun World.'
$session.state_authority='Live task85314 and STATUS.md; inspect input-proof and import/probe logs. candidate-a-probe.done only after all four render groups.'
$session | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 artifacts/vegetation-r4/session.json
Add-Content artifacts/vegetation-r4/STATUS.md '8662 terminalne kod 0: World 538,6 s, 130 GLB, cztery żywopłoty 94,3 m²/18 402 tris, dekodowane wejścia kolizji 64 Low chunków. Heavy zwolniony. Nowa sekwencja 85314 czeka heavy na migawkę i porównanie przed importem, bez ponownego World.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 świat gotowy i sekwencja próby rozpoczęta' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/session.json','artifacts/vegetation-r4/checkpoint-world-done.ps1')
