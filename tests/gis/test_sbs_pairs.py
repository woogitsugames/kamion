"""ADR 0140: SBS pair composer and world-freshness preflight (synthetic region, no real data)."""
import json
import os
import sys
import time
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/refs'))
import sbs_pairs as S  # noqa: E402

REG = 'test-region'


def _region(tmp: Path, chunk_bytes: int = 4, import_newer: bool = True):
    gen = tmp / f'Data/Regions/{REG}/generated'
    gen.mkdir(parents=True)
    world = tmp / f'Data/raw/derived/{REG}/world'
    world.mkdir(parents=True)
    (world / 'chunk_0_0.glb').write_bytes(b'abcd')
    (tmp / f'Data/Regions/{REG}/overrides.yaml').write_text('a: 1\n', encoding='utf-8')
    manifest = {'chunks': [{'file': f'Data/raw/derived/{REG}/world/chunk_0_0.glb', 'bytes': chunk_bytes}],
                'sources_sha256': {'overrides.yaml': S._sha(tmp / f'Data/Regions/{REG}/overrides.yaml')}}
    (gen / 'world_manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    inst = tmp / f'game/Assets/_Generated/World/{REG}/Instances.asset'
    inst.parent.mkdir(parents=True)
    inst.write_text('x', encoding='utf-8')
    t = time.time()
    os.utime(world / 'chunk_0_0.glb', (t, t))
    os.utime(inst, (t + 60, t + 60) if import_newer else (t - 600, t - 600))
    return tmp


def test_preflight_ok(tmp_path):
    assert S.preflight(_region(tmp_path), REG) == []


def test_preflight_detects_foreign_derived_build(tmp_path):
    problems = S.preflight(_region(tmp_path, chunk_bytes=5), REG)
    assert any('another build' in p for p in problems)


def test_preflight_detects_old_import_and_changed_overrides(tmp_path):
    root = _region(tmp_path, import_newer=False)
    (root / f'Data/Regions/{REG}/overrides.yaml').write_text('a: 2\n', encoding='utf-8')
    problems = S.preflight(root, REG)
    assert any('import older' in p for p in problems)
    assert any('overrides.yaml' in p for p in problems)


def test_pairs_width_and_before_layout(tmp_path):
    root = tmp_path
    (root / f'Data/Regions/{REG}').mkdir(parents=True)
    Image.new('RGB', (1280, 720), 'blue').save(root / 'photo.png')
    refs = {'references': [{'camera': 'cam-a', 'segment': 'G3-B', 'photo': 'photo.png', 'width': 2048, 'height': 1152,
                            'author': 'x', 'license': 'CC BY-SA 4.0', 'captured_at': '2019-01-01', 'source_id': '1'}]}
    (root / f'Data/Regions/{REG}/sbs_references.json').write_text(json.dumps(refs), encoding='utf-8')
    for d in ('after', 'before'):
        (root / d).mkdir()
        Image.new('RGB', (1280, 720), 'grey').save(root / d / 'cam-a.png')
    one = S.compose_pairs(root / 'after', root / 'out1', root=root, region=REG)
    two = S.compose_pairs(root / 'after', root / 'out2', before=root / 'before', root=root, region=REG)
    assert Image.open(one[0]).size == (960, 270)
    assert Image.open(two[0]).size == (960, 540)
