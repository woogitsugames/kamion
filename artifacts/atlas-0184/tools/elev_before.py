"""elev.py with the pre-0184 plain strip (u 0.2..1.2) - software BEFORE of the LOD1 walls."""
import sys, runpy
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from streetscape import facade_atlas as FA
FA.FAR_PLAIN_U = (0.2, 1.2)
runpy.run_path(str(Path(__file__).with_name("elev.py")), run_name="__main__")
