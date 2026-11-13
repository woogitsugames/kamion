# STATUS audio-synth-0176 (ADR 0176 — synteza brakujących warstw)
- 15:50 start: przeczytane CLAUDE.md, docs/08, ADR 0156, review P5. Plan: tools/audio/synth0176.py (retarder 2 warstwy moc/obroty wału, hamulec silnikowy włącz/zwolnij, AMT rozłącz/włącz/sprzęgło, osuszacz blowdown) → render_all → C# (LayerMath + DrivelineSfx + biblioteka + importer + hook TruckAudioController) → testy EditMode → A/B + spektrogramy → ADR/LICENSES/prompty EL.
- NASTĘPNY KROK: `cd tools/audio; uv run python synth0176.py`
