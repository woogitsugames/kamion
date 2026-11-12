$ErrorActionPreference='Stop'
. ./artifacts/vegetation-r4/checkpoint.ps1
$session=Get-Content artifacts/vegetation-r4/session.json -Raw | ConvertFrom-Json
$session.phase='candidate_b2_unity_import_running'
$session.next_step='Live task9518 candidate-b-probe.ps1: light snapshot/provenance passed, Unity import started12:48:05 then16probe-b frames. Task87809 terminal0:33tests10.29s,World534.6s,collision64chunks. After probe0 generate8review sheets and self-view/critic before full matrix. Do not rerun generation.'
$session.state_authority='Live task9518, candidate-b-input-proof.json, import-candidate-b.log and STATUS.md. candidate-b-probe.done only after4render groups. Snapshot-candidate-b is B2 source.'
$session | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 artifacts/vegetation-r4/session.json
Add-Content artifacts/vegetation-r4/STATUS.md '87809 terminalne0: WorldB2 534,6s oraz dekodowana kolizja64chunków. Piny B2 przeszły0: jedyna zmianaźródłowa plantings.py, wszystkie64instancje/kolizje i far_field identyczne,15Megascans bezfallback. Zmienione tylkochunk6_6 Low/High i metadata. Nasadzenia+1945tris do20347, bez zmiany4obrysów/94,3m². Nowyjob9518 importuje od12:48:05 przezUnityslot, potem16próbB. To jeszcze nie pomiar kamer/GPU ani akceptacja.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 B2 wygenerowany i importowany po kontroli danych' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/session.json','artifacts/vegetation-r4/checkpoint-b2-import.ps1')
