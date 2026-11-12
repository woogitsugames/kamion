$ErrorActionPreference='Stop'
. ./artifacts/vegetation-r4/checkpoint.ps1
$session=Get-Content artifacts/vegetation-r4/session.json -Raw | ConvertFrom-Json
$session.phase='candidate_a_unity_import_running'
$session.next_step='Live task12586: provenance passed, Unity import running then16probe frames. Task85314 intentionally cancelled during redundant heavy wait; no generator rerun. Review probe after terminal success.'
$session.state_authority='Live task12586, candidate-a-input-proof.json and STATUS.md; candidate-a-probe.done only after all four render groups.'
$session | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 artifacts/vegetation-r4/session.json
Add-Content artifacts/vegetation-r4/STATUS.md 'Po lekkiej kontroli kod 0: 617 pinów źródeł z jedyną zmianą plantings.py; wszystkie 64 instancje i 64 chunki dekodowanej kolizji identyczne, far_field GLB bez zmian, nasadzenia bez zmian, 15 Megascans bez fallback. Wyjścia zmienione tylko streetscape_qa/world_manifest oraz chunk_6_6 Low/High. Sekwencja 12586 importuje przez slot Unity od 11:08:28. Poprzednią anulowaną kolejkę zatrzymano około 11:08, nie 11:09 jak oszacowano w poprzednim wpisie.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 zgodność danych i aktywny import kandydata' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/session.json','artifacts/vegetation-r4/checkpoint-import-running.ps1')
