$ErrorActionPreference='Stop'
. ./artifacts/vegetation-r4/checkpoint.ps1
$session=Get-Content artifacts/vegetation-r4/session.json -Raw | ConvertFrom-Json
$session.phase='candidate_b_tests_waiting_heavy'
$session.next_step='Live task73347 green-b-and-world.ps1: focused tests then World and collision in heavy. A rejected after8sheets. B fixes self-intersecting polygon offsets; no texture change. After success light snapshot/compare, import and probe-b; no full GIS until round end.'
$session.state_authority='Live task73347 and STATUS.md; green-b-and-world.done only on success. Probe A and snapshots retained.'
$session | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 artifacts/vegetation-r4/session.json
Add-Content artifacts/vegetation-r4/STATUS.md 'Próba B na czterech obrysach z płaskim gruntem: 11 560 tris zamiast18 402, po równomiernym próbkowaniu bez gęstych krótkich fragmentów obwodu. Capy poprawne, maksymalne krawędzie<0,98m. To mała analiza0,79s bez build/testów i bez potwierdzenia kamery czyGPU. Jedyna sekwencja ciężka73347 czeka heavy na27celowanych testów, a World będzie warunkowy po ich powodzeniu. Poprzednie12586 terminalne0; żadne Unity teraz nie działa w tej sesji.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 pomiar geometrii B i aktywna kolejka testów' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/session.json','artifacts/vegetation-r4/checkpoint-b-queue.ps1','artifacts/vegetation-r4/inspect_cap.py','artifacts/vegetation-r4/cap-study-b-counts.json')
