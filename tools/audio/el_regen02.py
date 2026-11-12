"""Objective analysis of the ElevenLabs REGEN-02 batch (ADR 0142), reusing the el_regen01 metrics and sheets.

    uv run python el_regen02.py
Variants (owner notes, kamion-audio-regenerations-02-20261112/notes.txt): TURBO_WHISTLE_LOOP (5)-(8),
ENG_STOP_CAB (5)-(8), CAB_WIPERS_LOOP (9)-(12).
(The sweeps ENG_*_SWEEP of REGEN-02 are not analysed here: the engine grid stays as in ADR 0138 by the owner's decision.)
Output: artifacts/audio-fx/regen02/{regen01.json,picks.json,regen01.csv,sheets/*.png} (file names kept from el_regen01).
"""
import sys

import el_regen01 as r1
from el_prepare import ROOT

r1.VARIANTS = {"TURBO_WHISTLE_LOOP": (5, 6, 7, 8), "ENG_STOP_CAB": (5, 6, 7, 8), "CAB_WIPERS_LOOP": (9, 10, 11, 12)}
_prompt = r1.prompt_entry
r1.prompt_entry = lambda fid: dict(_prompt(fid), batch="REGEN-02 (prompt text: docs/owner/ELEVENLABS-REGEN-02.md)")

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "--out", str(ROOT / "artifacts" / "audio-fx" / "regen02")]
    r1.main()
