import copy
from pathlib import Path

import numpy as np
import pytest
import yaml

from streetscape import plantings as PT, vegetation as VG


class Buffer:
    def __init__(self):
        self.vertices = []
        self.parts = []

    def add(self, layer, mat, V, UV, T, src="", **kwargs):
        self.vertices.append(np.asarray(V))


def group(**kwargs):
    return {"id": "trial", "kind": "tree_groups", "form": "kit",
            "points_en": [[5, 5, 17, 10, "linden"], [20, 5, 17, 10, "linden"]],
            "species": {"linden": 1.0}, **kwargs}


def build(o):
    buf, report = Buffer(), {}
    PT.authored_trees(buf, [o], lambda p: 100., report)
    return buf, report["authored_trees"]


def test_trial_has_both_lods_and_does_not_create_tree_instances():
    o = group(crown_model="garden_trial")
    buf, rep = build(o)
    assert rep["trees"] == 2 and rep["tris_high"] > rep["tris_low"] > 0
    assert all(x["crown_model"] == "garden_trial" and x["species"] == "linden" for x in rep["list"])
    vertices = np.vstack(buf.vertices)
    assert vertices[:, 2].min() < 100 and vertices[:, 2].max() > 115
    assert VG._tree_point_overrides([o]) == []


def test_default_and_explicit_kit_are_identical():
    default_buf, default = build(group())
    explicit_buf, explicit = build(group(crown_model="kit"))
    assert default == explicit
    assert len(default_buf.vertices) == len(explicit_buf.vertices)
    assert all(np.array_equal(a, b) for a, b in zip(default_buf.vertices, explicit_buf.vertices))


def test_invalid_model_or_species_fails():
    with pytest.raises(ValueError, match="unknown crown_model"):
        build(group(crown_model="invalid"))
    bad = copy.deepcopy(group(crown_model="garden_trial"))
    bad["points_en"][0][4] = "shrub"
    with pytest.raises(ValueError, match="does not support species"):
        build(bad)


def test_volume_trial_is_deterministic_and_wraps_the_crown():
    class Kit:
        def __init__(self): self.cards=[]; self.trunks=0
        def quad(self, vertices, uv, colors): self.cards.append((np.asarray(vertices),np.asarray(uv)))
        def box(self, *args, **kwargs): self.trunks+=1
    p=np.array([5.,5.]); key=("volume-test",0)
    for lite,count in ((False,12),(True,8)):
        kit=Kit(); repeat=Kit()
        for k in (kit,repeat):
            PT._authored_volume_crown(k,p,100.,5.,17.,3.57,"linden",key,lite=lite)
        assert kit.trunks==1 and len(kit.cards)==count
        assert all(np.array_equal(a[0],b[0]) and np.array_equal(a[1],b[1]) for a,b in zip(kit.cards,repeat.cards))
        centers=np.asarray([v[:,:2].mean(axis=0)-p for v,uv in kit.cards])
        assert np.all(np.linalg.norm(centers,axis=1)>1.)
        for axis in ([1.,0.],[0.,1.],[-1.,0.],[0.,-1.]):
            assert max(centers@axis)>1.
        assert all(np.isfinite(v).all() and 103. < v[:,2].min() <= v[:,2].max() <= 117. for v,uv in kit.cards)
    _,rep=build(group(crown_model="garden_volume_trial"))
    assert rep["trees"]==2 and rep["tris_high"]>rep["tris_low"]>0
    assert all(x["crown_model"]=="garden_volume_trial" for x in rep["list"])


def test_r8_replaces_only_r7_accepted_stems_with_preserved_heights():
    path = Path(__file__).resolve().parents[2] / "Data/Regions/knyszyn/overrides.yaml"
    overrides = yaml.safe_load(path.read_text(encoding="utf8"))["overrides"]
    groups = {o["id"]: o for o in overrides}
    trial = groups["rynek-lindens-r8-trial-0227"]
    expected = {(-674., -171.2): 19.6, (-662., -182.2): 16.1, (-648.5, -185.7): 18.,
                (-639.5, -192.2): 19.7, (-696., -192.2): 19.3, (-706.5, -209.2): 17.6,
                (-697., -222.2): 15.8, (-702., -243.2): 16.9, (-685.5, -248.2): 16.,
                (-676., -254.2): 17.8, (-661., -247.2): 15.4, (-646., -240.2): 19.9,
                (-638., -227.2): 17.}
    assert trial["form"] == "kit" and trial["crown_model"] == "garden_volume_trial"
    assert len(trial["points_en"]) == len(expected)
    assert {(p[0], p[1]): p[2] for p in trial["points_en"]} == expected
    assert all(p[3] > 0 and p[4] == "linden" for p in trial["points_en"])
    rejected = groups["rynek-park-broadleaf-0227"]
    assert rejected.get("form") != "kit"
    assert {tuple(p) for p in rejected["points_en"]} == {
        (-687., -167.2), (-702., -180.2), (-689., -205.2)}
    other = groups["rynek-near-lindens-kit-0227"]
    assert other["crown_model"] == "garden_volume_trial"
    other_kit = other["points_en"]
    all_kit = trial["points_en"] + other_kit
    assert all(np.linalg.norm(np.array(a[:2]) - np.array(b[:2])) >= 2.5
               for i, a in enumerate(all_kit) for b in all_kit[i + 1:])
    _, rep = build(trial)
    assert rep["trees"] == 13 and rep["tris_high"] > rep["tris_low"] > 0
