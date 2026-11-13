"""ADR 0173: two runs of the world generator give identical output.

Fast checks on a slice: source hashes do not depend on the checkout line endings, and the compare tool reports
identical / order-only / content differences correctly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qa.compare_world import compare  # noqa: E402
from streetscape.far_field import _sha256  # noqa: E402


def test_source_hash_ignores_crlf(tmp_path):
    lf, crlf = tmp_path / "a.yaml", tmp_path / "b.yaml"
    lf.write_bytes(b"x: 1\ny: [2, 3]\n")
    crlf.write_bytes(b"x: 1\r\ny: [2, 3]\r\n")
    assert _sha256(lf) == _sha256(crlf)
    g1, g2 = tmp_path / "a.geojson", tmp_path / "b.geojson"
    g1.write_bytes(b'{"a":\n1}')
    g2.write_bytes(b'{"a":\r\n1}')
    assert _sha256(g1) == _sha256(g2)


def test_build_world_hashes_lf_normalised():
    src = (Path(__file__).resolve().parents[1] / "roads" / "build_world.py").read_text(encoding="utf-8")
    assert 'sha(p.read_bytes().replace(b"\\r\\n", b"\\n"))' in src


def test_compare_world_classifies(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    i1 = [{"p": "tree", "e": 1.0, "n": 2.0}, {"p": "lamp", "e": 3.0, "n": 4.0}]
    (a / "instances_0_0.json").write_text(json.dumps({"instances": i1}))
    (b / "instances_0_0.json").write_text(json.dumps({"instances": i1}))
    assert compare(a, b) == []
    (b / "instances_0_0.json").write_text(json.dumps({"instances": i1[::-1]}))
    assert "ORDER ONLY" in compare(a, b)[0]
    (b / "instances_0_0.json").write_text(json.dumps({"instances": i1[:1]}))
    assert "CONTENT" in compare(a, b)[0]
