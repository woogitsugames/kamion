"""Unit tests (no Data/raw): deterministic hash/seed-driven placement of objects.

Covers qa.determinism.parts_hash (mesh part hashing, incl. independence of PYTHONHASHSEED across
processes), streetscape.vegetation._seed, streetscape.foliage_policy.leaf_lod_indices and
metric_patch_field (chunk-invariant smooth placement field).

Run: uv run --project tools/worldgen pytest tests/gis -q -m unit
"""

import os
import subprocess
import sys

import numpy as np
import pytest

from qa.determinism import parts_hash
from roads.meshing import Part
from streetscape.foliage_policy import leaf_lod_indices, metric_patch_field
from streetscape.vegetation import _seed

pytestmark = pytest.mark.unit


def _sample_parts():
    rng = np.random.default_rng(3)
    parts = []
    for i in range(3):
        V = rng.normal(size=(10, 3))
        T = np.array([[0, 1, 2], [2, 1, 3]], dtype=np.int64)
        parts.append(Part(f"layer{i % 2}", "mat", V, V[:, :2], T, src=f"s{i}"))
    return parts


def test_parts_hash_deterministic_and_sensitive():
    h1, rows1 = parts_hash(_sample_parts())
    h2, rows2 = parts_hash(_sample_parts())
    assert h1 == h2 and rows1 == rows2
    parts = _sample_parts()
    parts[0].V[0, 0] += 1e-6                      # any vertex change -> different hash
    h3, _ = parts_hash(parts)
    assert h3 != h1
    assert len(h1) == 64 and all(len(r[6]) == 16 for r in rows1)


def test_parts_hash_independent_of_pythonhashseed():
    """Same parts hashed in two subprocesses with different PYTHONHASHSEED must give the same hash."""
    code = (
        "import sys; sys.path.insert(0, 'tools/worldgen');"
        "import numpy as np;"
        "from qa.determinism import parts_hash;"
        "from roads.meshing import Part;"
        "rng = np.random.default_rng(3);"
        "parts = [Part('furniture', 'barrier_steel', rng.normal(size=(8, 3)), np.zeros((8, 2)),"
        " np.array([[0,1,2],[1,2,3]]), src='unit') for _ in range(3)];"
        "print(parts_hash(parts)[0])"
    )
    hashes = set()
    for hs in ("0", "1", "42"):
        env = {**os.environ, "PYTHONHASHSEED": hs}
        out = subprocess.run([sys.executable, "-c", code], cwd=_repo_root(), env=env,
                             capture_output=True, text=True, timeout=120)
        assert out.returncode == 0, out.stderr[-1000:]
        hashes.add(out.stdout.strip())
    assert len(hashes) == 1, hashes


def _repo_root():
    from conftest import REPO
    return str(REPO)


def test_vegetation_seed_stable_and_keyed():
    assert _seed("polygon:123") == _seed("polygon:123")
    assert _seed("polygon:123") != _seed("polygon:124")
    assert 0 <= _seed("x") < 2 ** 32


def test_leaf_lod_indices_stable_subset():
    a = leaf_lod_indices(100, 42)
    b = leaf_lod_indices(100, 42)
    assert np.array_equal(a, b)
    assert len(a) == 40                                  # share=.40 of 100
    assert a.min() >= 0 and a.max() < 100
    assert len(np.unique(a)) == len(a)                   # no duplicates
    c = leaf_lod_indices(100, 42, maximum=10)
    assert len(c) == 10 and len(np.unique(c)) == 10      # capped LOD: same seed, fewer picks
    assert np.array_equal(c, leaf_lod_indices(100, 42, maximum=10))
    assert len(leaf_lod_indices(0, 42)) == 0


def test_metric_patch_field_chunk_invariant_and_bounded():
    xs = np.linspace(0, 512, 50)
    ys = np.linspace(0, 512, 50)
    big = metric_patch_field(xs, ys)                     # rows = north, cols = east
    assert big.shape == (50, 50)
    assert big.min() >= 0.0 and big.max() <= 1.0
    small = metric_patch_field(np.array([xs[10], xs[40]]), np.array([ys[2], ys[20]]))
    # sampling a small array gives the same field values as the big array at those points (no chunk seams)
    assert big[2, 10] == pytest.approx(small[0, 0], abs=1e-6)
    assert big[20, 40] == pytest.approx(small[1, 1], abs=1e-6)
