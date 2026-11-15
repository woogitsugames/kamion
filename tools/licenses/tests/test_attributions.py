"""S21 (A5): the in-game "Informacje" text carries every attribution the build requires.

Source of truth for "requires attribution": the summary table in docs/LICENSES.md ("Tabela zbiorcza źródeł",
LICENSES-AUDIT-S20). Every row whose "Wymagana atrybucja" starts with "tak" or names a licence text, and whose
"W buildzie" is not "nie", must be mapped below to the exact notice(s) the screen shows; the notices must be in the
VISIBLE text of game/Assets/_Project/UI/Resources/About/attributions.txt (comment lines `#` are not shown,
`@include <Resources path>` pulls in a full licence text). Same file format as Game.Core.About.AttributionDocument.

Run: uv run --project tools/licenses pytest tools/licenses/tests -q
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
RESOURCES = REPO / "game" / "Assets" / "_Project" / "UI" / "Resources"
ATTRIBUTIONS = RESOURCES / "About" / "attributions.txt"
LICENSES_MD = REPO / "docs" / "LICENSES.md"

# Row number in the summary table -> notices that must be visible (exact substrings).
REQUIRED = {
    1: ["© OpenStreetMap contributors", "Open Database License (ODbL) 1.0", "www.openstreetmap.org/copyright"],
    2: ["Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl)"],
    3: ["Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl)", "ortofotomapa"],
    5: ["BDOT10k"],
    6: ["LoD2", "CC BY 4.0"],
    7: ["LoD1", "CC BY 4.0"],
    8: ["© OpenStreetMap contributors", "Główny Urząd Geodezji i Kartografii"],   # second region: same sources
    18: ["research G3 s8-signs", "OpenStreetMap contributors", "Mapillary contributors", "ODbL 1.0"],
    28: ["The Inter Project Authors", "SIL OPEN FONT LICENSE Version 1.1", "Reserved Font Name"],
    32: ["Unity glTFast copyright © 2023 Unity Technologies and the Unity glTFast authors",
         "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION"],
}

# Never on screen: unresolved notes belong in `#` comments (same list as AttributionDocument.ForbiddenVisibleMarkers).
FORBIDDEN_VISIBLE = ["UNVERIFIED", "WARUNKOWO", "TODO", "[ADRES", "LEGAL_REVIEW", "WORKING_VALUE"]


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
