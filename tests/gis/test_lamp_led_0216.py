"""ADR 0216 (owner D65 p.8): white LED street lighting as region data - `kind: lamp_policy, family: led`."""
import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from streetscape import furniture as F, props as P

ROOT = Path(__file__).resolve().parents[2]
LED_REGIONS = ("knyszyn", "knyszyn-s", "knyszyn-w", "bialystok-knyszynska")



@pytest.mark.parametrize("kind,height", [("concrete", 9), ("steel", 8)])
def test_led_head_keeps_the_budget_of_the_sodium_one(kind, height):
    old, led = P.lamp_old(height, kind), P.lamp_old(height, kind, led=True)
    for a, b in zip(old[:2], led[:2]):                       # LOD0, LOD1
        pa, pb = a.out(), b.out()
        assert len(pa) == len(pb) == 4                       # material slots = draws per instance batch
        assert sum(len(p["T"]) for p in pa) == sum(len(p["T"]) for p in pb)
        assert a.pole_height == b.pole_height
        for p in pb:
            x, y, z = np.moveaxis(p["V"][p["T"]], 1, 0)
            assert np.all(np.linalg.norm(np.cross(y - x, z - x), axis=1) > 1e-10)


def test_led_head_uses_the_led_materials():
    names = lambda mesh: {str(v) for p in mesh.out() for v in p.values() if isinstance(v, str)}
    for kind, h in P.LAMP_OLD:
        led, old = names(P.lamp_old(float(h), kind, led=True)[0]), names(P.lamp_old(float(h), kind)[0])
        assert "lamp_glass" in led and "lamp_glass_sodium" not in led and "luminaire_old" not in led
        assert "lamp_glass_sodium" in old                    # the default family is unchanged


def test_policy_is_authored_only_for_the_owner_regions():
    for d in sorted((ROOT / "Data/Regions").iterdir()):
        f = d / "overrides.yaml"
        if not f.exists():
            continue
        pol = F.lamp_policy((yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("overrides"))
        assert (pol.get("family") == "led") == (d.name in LED_REGIONS), d.name
    assert F.lamp_policy(None) == {} and F.lamp_policy([{"kind": "paved_area"}]) == {}


def test_lighting_profiles_list_summer_and_led_regions():
    prof = {p["id"]: p for p in json.loads((ROOT / "Data/Regions/lighting_profiles.json").read_text(encoding="utf-8"))["profiles"]}
    summer, led = prof["summer-dk65-knyszyn"], prof["led-white-4000k"]
    assert summer["season"] == "summer" and summer["duskClockHour"] == 21.0
    assert set(led["regions"]) == set(LED_REGIONS) and led["ledCctK"] == 4000
    assert max(led["ledColour"]) == 1.0 and led["ledColour"][2] >= 0.85          # white, not the warm default 0.82
    for keep in ("bialystok-industrial-c", "bialystok-dojlidy"):                  # tile C and Dojlidy: unchanged
        assert keep not in summer["regions"] and keep not in led["regions"]


@pytest.mark.parametrize("rid", LED_REGIONS)
def test_generated_region_has_no_sodium_street_lamps(rid):
    qa = ROOT / f"Data/Regions/{rid}/generated/streetscape_qa.json"
    lamps = json.loads(qa.read_text(encoding="utf-8"))["furniture"]["lamps"]
    if lamps.get("policy") != "led":
        pytest.skip("region not regenerated with ADR 0216 yet")
    assert not [k for k in lamps["by_family"] if k in ("lamp_old_concrete_9m", "lamp_old_steel_8m")]
