"""ADR0070 r7: hero-local palette, old atlas protection, clean fallback and Low batching contract."""
import ast
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from conftest import REPO


@pytest.fixture
def atlas(monkeypatch):
    src = REPO / "art-source/world/materials/_src"
    monkeypatch.syspath_prepend(str(src))
    spec = importlib.util.spec_from_file_location("test_fire_station_r7_atlas", src / "sets_fire_station.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_new_cell_preserves_every_old_alpha_pixel(atlas, monkeypatch, tmp_path):
    monkeypatch.setattr(atlas, "_conifer_sprite", lambda: Image.new("RGBA", (64, 96)))
    old = np.array(Image.open(atlas.alpha_texture(tmp_path / "old.png")))
    monkeypatch.setattr(atlas, "_conifer_sprite", lambda: Image.new("RGBA", (64, 96), (55, 85, 34, 255)))
    new = np.array(Image.open(atlas.alpha_texture(tmp_path / "new.png")))
    r = atlas.ALPHA_LAYOUT["conifer_bough"]; h, w = old.shape[:2]
    outside = np.ones(old.shape[:2], bool)
    outside[h-int(r["v"][1]*h):h-int(r["v"][0]*h),int(r["u"][0]*w):int(r["u"][1]*w)] = False
    assert np.array_equal(old[outside], new[outside])
    assert not np.array_equal(old[~outside], new[~outside])
    # This is base-pixel protection; Unity's global coverage-preserving mips still require render QA.


def test_clean_clone_fallback_is_explicit_and_deterministic(atlas, monkeypatch, tmp_path):
    source = json.loads((atlas.LANDMARK / "conifer_source.json").read_text())
    landmark = tmp_path / "landmark"; landmark.mkdir()
    (landmark / "conifer_source.json").write_text(json.dumps(source))
    monkeypatch.setattr(atlas, "LANDMARK", landmark); monkeypatch.setattr(atlas, "REPO", tmp_path)
    def offline(*args, **kwargs):
        raise OSError("offline unit fixture")
    monkeypatch.setattr(atlas.urllib.request, "urlopen", offline)
    a, b = np.array(atlas._conifer_sprite()), np.array(atlas._conifer_sprite())
    assert np.array_equal(a, b) and (a[..., 3] >= 128).sum() > 100
    status = json.loads((landmark / "conifer_foliage_meta.json").read_text())
    assert status["applied"] is False and "NOT verified Picea" in status["species_status"]


def test_hero_palette_alias_leaves_all_route_hedges_unchanged():
    from streetscape import materials as m
    from streetscape.hedge_textures import shell
    assert m.M["hedge_thuja"]["color"] == [.016, .028, .012]
    assert m.M["hedge_shell_thuja"]["color"] == [1, 1, 1]
    hero = m.M["fire_station_thuja_shell"]
    assert hero["texture"] == "hedge_shell_thuja" and hero["rough"] == .97 and hero["alpha_cutoff"] == .5
    pixels = np.array(shell("thuja")); srgb = pixels[..., :3] / 255
    linear = np.where(srgb <= .04045, srgb / 12.92, ((srgb + .055) / 1.055) ** 2.4)
    target = json.loads((REPO / "art-source/world/landmarks/fire_station_jrg2/atlas_layout.json").read_text())["atlas"]["foliage_linear"]
    np.testing.assert_allclose(linear[pixels[..., 3] >= 128].mean(0) * hero["color"], target, rtol=2e-5)


def test_new_geometry_keeps_two_low_slots_and_original_plant_budget(monkeypatch):
    # Definition-only load: no bpy import, writer main(), Blender or output mutation.
    source = REPO / "tools/blender/world/landmarks/make_fire_station.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    tree.body = [n for n in tree.body if not (
        isinstance(n, ast.Import) and any(a.name in ("bpy", "bmesh") for a in n.names)
        or isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and n.value.func.id == "main")]
    spec = REPO / "Data/Regions/bialystok-industrial-c/generated/landmarks/fire_station_jrg2.spec.json"
    if not spec.exists():
        pytest.skip("generated source spec unavailable")
    monkeypatch.setattr(sys, "argv", [str(source), "--", "--spec", str(spec)])
    namespace = {"__file__": str(source)}; exec(compile(tree, str(source), "exec"), namespace)
    mb = namespace["MB"]()
    for e,n,z,height,radius,key in namespace["SPEC"]["ground"]["thuja"]:
        namespace["build_thuja"](mb,namespace["en_to_uvz"]([e,n,z]),height,radius,key,1)
    for e,n,z,height,radius,key in namespace["SPEC"]["ground"]["spruce"]:
        namespace["build_conifer"](mb,namespace["en_to_uvz"]([e,n,z]),height,radius,key,1)
    assert set(mb.M) == {"fire_station", "fire_station_alpha"}
    assert sum(len(face)-2 for face in mb.F) <= 888
    r = namespace["ALAY"]["conifer_bough"]; u0,v0,u1,v1 = r["inner_uv"]
    for material, uv in zip(mb.M, mb.UV):
        if material == "fire_station_alpha":
            a = np.array(uv)
            assert a[:,0].min() >= u0 and a[:,0].max() <= u1
            assert a[:,1].min() >= v0 and a[:,1].max() <= v1
