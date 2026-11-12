$ErrorActionPreference='Stop'
. ./artifacts/vegetation-r4/checkpoint.ps1
$session=Get-Content artifacts/vegetation-r4/session.json -Raw | ConvertFrom-Json
$session.phase='candidate_b2_tests_waiting_heavy_fifo'
$session.next_step='Live task87809 green-b-and-world.ps1:30focused tests then World/collision conditional in heavy. B2 exact offset corners, annulus CDT, constrained cap with consistent interior samples and split UV seam. After success candidate-b-probe.ps1 uses light pins then Unity slots. No full GIS until round end.'
$session.state_authority='Live task87809, STATUS.md and cap-study-b-annulus-cap.json. Task73347 terminal1; old loft retained in failure evidence. On-disk world remains A until B2 World succeeds.'
$session | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 artifacts/vegetation-r4/session.json
Add-Content artifacts/vegetation-r4/STATUS.md 'Aktualny main unity-slot od12:11 ma FIFO dla zwykłych sesji i Priority tylko lead-*. Własny kod od początku używa main absolute; nowyjob87809 widzi queueahead9. Ciężka sekwencja B2 startuje30testami, dopiero po0World i kolizja, bez duplikatów. Kod B2 wysłany do krytyka read-only. Dane lekkiej analizy są oznaczone nie jako testy ani wizualnyPASS.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 B2 w kolejce FIFO do testów' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/session.json','artifacts/vegetation-r4/checkpoint-b2-queue.ps1')
