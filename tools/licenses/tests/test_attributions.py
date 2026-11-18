"""S21 (A5): the in-game "Informacje" text carries every attribution the build requires.

Source of truth for "requires attribution": the summary table in docs/LICENSES.md ("Tabela zbiorcza źródeł",
LICENSES-AUDIT-S20). Every row whose "Wymagana atrybucja" starts with "tak" or names a licence text, and whose
"W buildzie" is not "nie", must be mapped below to the exact notice(s) the screen shows; the notices must be in the
VISIBLE text of game/Assets/_Project/UI/Resources/About/attributions.txt (comment lines `#` are not shown,
`@include <Resources path>` pulls in a full licence text). Same file format as Game.Core.About.AttributionDocument.

Run: uv run --project tools/licenses pytest tools/licenses/tests -q
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
RESOURCES = REPO / "game" / "Assets" / "_Project" / "UI" / "Resources"
ATTRIBUTIONS = RESOURCES / "About" / "attributions.txt"
LICENSES_MD = REPO / "docs" / "LICENSES.md"

# Row number in the summary table -> notices that must be visible (exact substrings). Data, shared with the plain .NET
# tests in tools/about-runner (ADR 0230).
REQUIREMENTS = json.loads((REPO / "tools" / "licenses" / "attribution_requirements.json").read_text(encoding="utf-8"))
REQUIRED = {int(k): v for k, v in REQUIREMENTS["rows"].items()}
ALWAYS_VISIBLE = REQUIREMENTS["always_visible"]

# Never on screen: unresolved notes belong in `#` comments (same list as AttributionDocument.ForbiddenVisibleMarkers).
FORBIDDEN_VISIBLE = REQUIREMENTS["forbidden_visible"]

# City of Białystok open data (ArcGIS Online) must not feed the build: the BIP re-use terms forbid modifying the content
# (docs/LICENSES.md, "Dane Miasta Białystok — status licencyjny", ADR 0230).
CITY_DATA_PATTERNS = r"jN5LJsqeW33UjdlH|bialystok\.maps\.arcgis|bialystok-arcgis|bialystok-open-data|komunikacja\.bialystok"
BUILD_INPUTS = ["Data/Regions", "tools/worldgen", "tools/ui", "game/Assets"]


def visible_text() -> str:
    out = []
    for line in ATTRIBUTIONS.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        if line.startswith("@include"):
            path = RESOURCES / (line[len("@include"):].strip() + ".txt")
            assert path.exists(), f"@include target missing: {path.relative_to(REPO)}"
            out.append(path.read_text(encoding="utf-8"))
        else:
            out.append(line.lstrip("= ").rstrip() if line.startswith("=") else line)
    return "\n".join(out)


def summary_rows() -> dict[int, list[str]]:
    """Rows of the "Tabela zbiorcza źródeł" table: number -> cells."""
    text = LICENSES_MD.read_text(encoding="utf-8")
    start = text.index("## Tabela zbiorcza źródeł")
    rows = {}
    for line in text[start:].splitlines()[1:]:
        if line.startswith("## "):
            break
        m = re.match(r"\|\s*(\d+)\s*\|", line)
        if m:
            rows[int(m.group(1))] = [c.strip() for c in line.strip().strip("|").split("|")]
    return rows


def needs_attribution(cells: list[str]) -> bool:
    required, in_build = cells[3].lower(), cells[5].lower()
    shown = required.startswith("tak") or required.startswith("j.w.") or "tekst licencji" in required
    return shown and not in_build.startswith("nie")


def test_summary_table_parsed():
    rows = summary_rows()
    assert len(rows) >= 40 and rows[1][1].startswith("OpenStreetMap")


def test_every_row_requiring_attribution_is_mapped():
    rows = summary_rows()
    need = {n for n, c in rows.items() if needs_attribution(c)}
    missing = sorted(need - set(REQUIRED))
    assert not missing, (f"docs/LICENSES.md rows {missing} require attribution in the build but have no notice in "
                         "REQUIRED (add the notice to attributions.txt and the row here)")


@pytest.mark.parametrize("row", sorted(REQUIRED))
def test_required_notices_are_visible(row):
    text = visible_text()
    for needle in REQUIRED[row]:
        assert needle in text, f"row {row}: {needle!r} not visible in {ATTRIBUTIONS.relative_to(REPO)}"


def test_no_unresolved_marker_is_visible():
    text = visible_text()
    found = [m for m in FORBIDDEN_VISIBLE if m in text]
    assert not found, f"unresolved markers on screen: {found} (move the note to a `#` comment)"


def test_resources_have_text_importer_meta():
    for p in [ATTRIBUTIONS, RESOURCES / "About" / "gltfast-apache-license.txt"]:
        meta = p.with_name(p.name + ".meta").read_text(encoding="utf-8")
        assert re.search(r"^guid: [0-9a-f]{32}$", meta, re.M) and "TextScriptImporter:" in meta, p.name


def test_always_visible_licence_notices():
    text = visible_text()
    missing = [n for n in ALWAYS_VISIBLE if n not in text]
    assert not missing, f"licence notices missing on screen: {missing}"


def test_forbidden_markers_match_parser():
    cs = (REPO / "game/Assets/_Project/Core/About/AttributionDocument.cs").read_text(encoding="utf-8")
    m = re.search(r"ForbiddenVisibleMarkers = \{([^}]*)\}", cs)
    assert m and re.findall(r'"([^"]+)"', m.group(1)) == FORBIDDEN_VISIBLE


def test_no_city_open_data_in_build_inputs():
    try:
        r = subprocess.run(["git", "grep", "-l", "-I", "-E", CITY_DATA_PATTERNS, "--", *BUILD_INPUTS],
                           cwd=REPO, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as e:  # pragma: no cover - no git in the environment
        pytest.skip(f"git grep unavailable: {e}")
    if r.returncode not in (0, 1):
        pytest.skip(f"git grep failed: {r.stderr.strip()}")
    hits = r.stdout.split()
    assert not hits, f"City of Białystok open data referenced in build inputs (ADR 0230): {hits}"
