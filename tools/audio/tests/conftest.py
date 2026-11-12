"""pytest setup for the audio tools tests.

Run from the repo root:
    uv run --project tools/audio --with pytest pytest tools/audio/tests -q

Every signal used here is synthesised inside the test process (synth_helpers);
no WAV/OGG file from the repository is read.
"""

from __future__ import annotations

import sys
from pathlib import Path

AUDIO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AUDIO))
