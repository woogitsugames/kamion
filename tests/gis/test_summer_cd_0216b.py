"""ADR 0216b (owner D68): summer lighting profile and LED street lamps for Bialystok tile C and Dojlidy - data only.

Checks the profile schema and ranges, the astronomy behind the dusk values (NOAA equations), and that every LED
decision for a Bialystok street has a source (an awarded city LED tender naming the street)."""
import datetime as dt
import json
import math
import re
from pathlib import Path

import pytest
import yaml

from qa import lamp_family_audit as LA, sun_noaa as SUN
from streetscape import furniture as F

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "Data/Regions"
CD = ("bialystok-industrial-c", "bialystok-dojlidy")
PROFILE_KEYS = {"id", "_doc", "regions", "season", "duskClockHour", "ledCctK", "ledColour", "sources"}
TED = json.loads((ROOT / "research/led-tenders-0216b/ted_notices.json").read_text(encoding="utf-8"))["notices"]


def _profiles():
    return json.loads((REG / "lighting_profiles.json").read_text(encoding="utf-8"))["profiles"]


def _overrides(rid):
    return (yaml.safe_load((REG / rid / "overrides.yaml").read_text(encoding="utf-8")) or {}).get("overrides") or []


def _graph_ways_by_name(rid):
    out = {}
    for e in json.loads((REG / rid / "roads.graph.json").read_text(encoding="utf-8"))["edges"]:
        n = e["attrs"].get("name", {}).get("v")
        if n:
            out.setdefault(n, set()).add(e["osm_way"])
    return out


def _apply(rid):
    """Python twin of RegionLightingProfiles.ApplyTo (C#): fields of every profile listing the region, in order."""
    env, applied = {}, []
    for p in _profiles():
        if rid in p.get("regions", []):
            for k in ("season", "duskClockHour", "ledColour"):
                if k in p:
                    env[k] = p[k]
            applied.append(p["id"])
    return ",".join(applied), env


# ------------------------------------------------------------------------------------------------ schema / ranges
def test_profiles_schema_and_ranges():
    ps = _profiles()
    ids = [p["id"] for p in ps]
    assert len(ids) == len(set(ids))
    for p in ps:
        assert set(p) <= PROFILE_KEYS, (p["id"], set(p) - PROFILE_KEYS)
        assert p["_doc"].strip() and p["regions"] and len(p["regions"]) == len(set(p["regions"]))
        for rid in p["regions"]:
            assert (REG / rid / "region.yaml").exists(), (p["id"], rid)
        if "season" in p:
            assert p["season"] in ("summer",)
        if "duskClockHour" in p:
            assert 18.0 <= p["duskClockHour"] <= 22.5          # an evening twilight hour of a Polish summer
        if "ledColour" in p:
            c = p["ledColour"]
            assert len(c) == 3 and all(0.0 <= v <= 1.0 for v in c) and max(c) == 1.0
            assert 2700 <= p["ledCctK"] <= 6500 and p["ledCctK"] == 4000     # D68 p.3: 4000 K
        if "sources" in p:
            assert all(isinstance(s, str) and s.strip() for s in p["sources"])


def test_tile_c_and_dojlidy_get_summer_and_the_knyszyn_led_colour():
    prof = {p["id"]: p for p in _profiles()}
    for rid in CD:
        applied, env = _apply(rid)
        assert applied == "summer-bialystok-cd,led-white-4000k-bialystok", rid
        assert env == {"season": "summer", "duskClockHour": 21.0, "ledColour": prof["led-white-4000k"]["ledColour"]}
    assert prof["led-white-4000k-bialystok"]["sources"]
    # ADR 0216 regions unchanged; Bialystok regions outside D68's C + Dojlidy keep the global behaviour
    assert _apply("knyszyn")[0] == "summer-dk65-knyszyn,led-white-4000k"
    assert _apply("dk65-03")[0] == "summer-dk65-knyszyn"
    for rid in ("bialystok-maczka", "bialystok-kleeberga"):
        assert _apply(rid) == ("", {}), rid


# ------------------------------------------------------------------------------------------------ astronomy
def test_noaa_sun_reproduces_the_adr_0216_table():
    """ADR 0216 (artifacts/summer-led-0216/sun_summer.json, computed in s20): -6 deg 1 VII 21:48 / 323, 15 VII 21:34 /
    319, 31 VII 21:07 / 311, 15 VIII 20:34 / 303; sunset 31 VII 20:24 / 303."""
    want = {(7, 1): ("21:48", 323), (7, 15): ("21:34", 319), (7, 31): ("21:07", 311), (8, 15): ("20:34", 303)}
    for (mo, d), (hm, az) in want.items():
        t, a = SUN.evening_crossing(dt.date(2026, mo, d), SUN.CIVIL_DUSK_DEG)
        h, m = map(int, hm.split(":"))
        assert abs((t.hour * 60 + t.minute + t.second / 60) - (h * 60 + m)) <= 2.0, (mo, d, t)
        assert abs(a - az) <= 1.0, (mo, d, a)
    t, a = SUN.evening_crossing(dt.date(2026, 7, 31), SUN.SUNSET_DEG)
    assert abs((t.hour * 60 + t.minute) - (20 * 60 + 24)) <= 2 and abs(a - 303) <= 1.0


def test_owner_dusk_values_against_the_sun():
    """D68: azimuth 300 deg at -6 deg is 19-20 August (20:22-20:25 CEST); 21:00 at -6 deg is 3 August (azimuth
    309.8 deg). The profile keeps the owner pair (WORKING_VALUE) - both within 45 min / 12 deg of the sun."""
    rows = {}
    for d in range(1, 32):
        for mo in (7, 8):
            t, a = SUN.evening_crossing(dt.date(2026, mo, d), SUN.CIVIL_DUSK_DEG)
            rows[(mo, d)] = (t.hour + t.minute / 60 + t.second / 3600, a)
    day300 = min(rows, key=lambda k: abs(rows[k][1] - 300.0))
    assert day300 in [(8, d) for d in range(17, 24)] and 20.2 <= rows[day300][0] <= 20.6
    day21 = min(rows, key=lambda k: abs(rows[k][0] - 21.0))
    assert day21 in [(8, d) for d in range(1, 6)] and 309.0 <= rows[day21][1] <= 311.0
    clock = {p["id"]: p for p in _profiles()}["summer-bialystok-cd"]["duskClockHour"]
    assert abs(clock - rows[day300][0]) <= 0.75 and abs(rows[day21][1] - 300.0) <= 12.0


def test_noaa_sun_agrees_with_the_cab_clock_formula():
    """SolarClock.cs (cab clock from the scene sun, no equation of time) vs NOAA at the same sun: within |EoT| (16 min)
    plus 2 min. LP_Dusk (-6 deg / 300 deg): ADR 0216 says the cab clock shows 20:20."""
    def solar_clock_minutes(elev, az, lat=SUN.BIALYSTOK_LAT, lon=SUN.BIALYSTOK_LON):   # port of SolarClock.LocalMinutes
        D = math.pi / 180
        phi, e, a = lat * D, elev * D, az * D
        sd = max(math.sin(-23.44 * D), min(math.sin(23.44 * D), math.sin(phi) * math.sin(e) + math.cos(phi) * math.cos(e) * math.cos(a)))
        dec = math.asin(sd)
        ch = (math.sin(e) - math.sin(phi) * sd) / max(1e-6, math.cos(phi) * math.cos(dec))
        h = math.acos(max(-1, min(1, ch))) / D
        h = -h if az % 360 < 180 else h
        clock = 12 + h / 15 - lon / 15 + (2 if dec > 0 else 1)
        return round(clock * 60) % 1440
    assert solar_clock_minutes(-6.0, 300.0) == 20 * 60 + 20
    for mo, d in ((6, 21), (7, 31), (8, 20)):
        t, a = SUN.evening_crossing(dt.date(2026, mo, d), SUN.CIVIL_DUSK_DEG)
        assert abs(solar_clock_minutes(-6.0, a) - (t.hour * 60 + t.minute)) <= 18, (mo, d)


# ------------------------------------------------------------------------------------------------ LED sources
def _ted(pub):
    return next(n for n in TED if n["publication_number"] == pub)


def test_every_led_street_in_bialystok_has_an_awarded_tender():
    """ADR 0216b: an LED head on a Bialystok street only where a contract-award notice of the city names it; the
    override targets exactly the graph ways of those street names."""
    pol = F.lamp_policy(_overrides("bialystok-dojlidy"))
    assert pol["family"] == "led" and pol["cct_k"] == 4000 and pol["reason"].strip() and pol["verify"].strip()
    teds = [re.search(r"detail/(\d+-\d{4})$", s).group(1) for s in pol["sources"] if "ted.europa.eu" in s]
    award = [_ted(t) for t in teds if _ted(t)["notice_type"] == "can-standard"]
    assert award, "no contract-award notice among the sources"
    text = " ".join(n["description_pol"] for n in award)
    ways = _graph_ways_by_name("bialystok-dojlidy")
    for name, item in pol["streets"].items():
        assert item in text, (name, item)                  # the notice names the street (quoted item, verbatim)
        assert name in ways, name                          # and the street is in the tile
    want = set().union(*(ways[n] for n in pol["streets"]))
    assert set(pol["target"]["osm_way"]) == want
    assert not set(pol["streets"]) & set(pol["unverified_streets"])
    for name in pol["unverified_streets"]:
        if not name.startswith("("):
            assert name in ways, name


def test_tile_c_has_no_led_heads_without_a_source():
    pol = F.lamp_policy(_overrides("bialystok-industrial-c"))
    assert pol["family"] == "unchanged" and not pol.get("target") and pol["unverified_streets"]
    assert F.lamp_led_scope(_overrides("bialystok-industrial-c")) == (False, set())
    ways = _graph_ways_by_name("bialystok-industrial-c")
    assert all(n in ways for n in pol["unverified_streets"] if not n.startswith("("))
    # tender of 2023 for the C route streets (K69 section 4): cited by the LED colour profile
    assert "658997-2023" in " ".join({p["id"]: p for p in _profiles()}["led-white-4000k-bialystok"]["sources"])


def test_ted_excerpt_has_no_contractor_or_product_names():
    for n in TED:
        assert set(n) == {"publication_number", "publication_date", "notice_type", "title", "url", "description_pol"}
        assert n["url"].startswith("https://ted.europa.eu/") and n["notice_type"] in ("cn-standard", "can-standard")
        assert "tunelu" not in n["title"]


# ------------------------------------------------------------------------------------------------ generator rule
def test_led_scope_of_the_policy():
    assert F.lamp_led_scope(None) == (False, set())
    assert F.lamp_led_scope([{"kind": "lamp_policy", "family": "led"}]) == (True, set())
    assert F.lamp_led_scope([{"kind": "lamp_policy", "family": "led", "target": {"osm_way": [5, "7"]}}]) == (False, {"5", "7"})
    assert F.lamp_led_scope([{"kind": "lamp_policy", "family": "unchanged", "target": {"osm_way": [5]}}]) == (False, set())
    assert F._edge_way("w107761797:1-2") == "107761797"


@pytest.fixture(scope="module")
def dojlidy_audit():
    ov = _overrides("bialystok-dojlidy")
    return LA.audit("bialystok-dojlidy"), LA.audit("bialystok-dojlidy", [o for o in ov if o.get("kind") != "lamp_policy"])


def test_dojlidy_led_heads_only_on_the_tender_streets(dojlidy_audit):
    with_pol, without = dojlidy_audit
    streets = set(F.lamp_policy(_overrides("bialystok-dojlidy"))["streets"])
    led = [r for r in with_pol["by_street"] if "_led_" in r["proto"]]
    assert led and {r["street"] for r in led} <= streets
    assert not [r for r in without["by_street"] if "_led_" in r["proto"]]
    # same poles, same places: only the head of the older family changes
    norm = lambda res: sorted((r["proto"].replace("_led_", "_"), r["street"], r["est_poles"]) for r in res["by_street"])
    merged = {}
    for p, s, n in norm(with_pol):
        merged[(p, s)] = merged.get((p, s), 0) + n
    assert merged == {(p, s): n for p, s, n in norm(without)}
    tot = with_pol["totals_est"]
    old = sum(v for k, v in tot.items() if k.startswith(LA.OLD))
    nled = sum(v for k, v in tot.items() if "_led_" in k)
    assert 0 < nled < old                                  # partial: sodium stays on the unlisted streets
