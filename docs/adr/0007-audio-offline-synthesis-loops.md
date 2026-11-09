# ADR 0007 — Engine audio: offline synthesis into seamless loops, runtime crossfade
Status: Accepted (proposed by audio agent), 2026-11-09
Decision: Engine sound is synthesised offline in Python (tools/audio) into phase-aligned seamless loops on an rpm × load grid (exterior + cab, plus engine-brake bank); the game crossfades loops by rpm/load (EngineAudio, zero GC). Real-time synthesis on device is deferred — too expensive for the Helio G99 minimum device. All sound is our own synthesis (no manufacturer recordings).
Consequences: Bank ~13 MB RAM (ADPCM). Generated WAVs stay out of git; reproducible via `uv run python tools/audio/render_all.py`. Subjective quality gated by owner listening test.
