"""Shoulder of a carriageway edge without a kerb, resolved from data (ADR 0272).

Order: authored override (`set: {shoulder: ...}`) > OSM `shoulder=*` tags > class rules of xsec_rules.yaml. BDOT10k
carries no shoulder attribute (the graph has KLASADROGI, MATERIALNAWIERZCHNI and SZEROKOSCNAWIERZCHNI only); its
pavement width is the generator `width`, which is why a ground shoulder adds no asphalt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

RULES_FILE = Path(__file__).with_name("xsec_rules.yaml")
KINDS = ("paved", "ground")
# side `mat` code of a RURAL station with a non-legacy shoulder: SHOULDER_CODE + paved_cm * 1000 + ground_cm.
# mat 0 = the legacy profile, so regions the rules do not touch keep byte-identical side arrays.
SHOULDER_CODE = 1_000_000
LEGACY = (1.00, 0.75)
FLAT_DITCH_M = 0.06      # `ditch: 0` of an override: side_profile reads 0.05 < h < 1.5 as the ditch depth


@dataclass(frozen=True)
class Shoulder:
    kind: str                    # paved | ground
    paved_m: float               # asphalt beyond the carriageway width
    ground_m: float              # gravel / ground part
    src: str                     # rule id, "osm:shoulder" or "authored_override:<id>"
    force: str | None = None     # "open" = no kerb on this edge, "kerb" = kerb, None = the class / speed rule decides
    ditch_m: float | None = None  # authored ditch depth (0 = flat verge), None = rule

    @property
    def code(self) -> int:
        if (round(self.paved_m, 2), round(self.ground_m, 2)) == LEGACY:
            return 0
        return SHOULDER_CODE + int(round(self.paved_m * 100)) * 1000 + int(round(self.ground_m * 100))


def decode(mat: int) -> tuple[float, float]:
    """(paved_m, ground_m) of a RURAL side `mat` code."""
    if mat < SHOULDER_CODE:
        return LEGACY
    v = mat - SHOULDER_CODE
    return (v // 1000) / 100.0, (v % 1000) / 100.0


@lru_cache(maxsize=None)
def rules(path: str | None = None) -> dict:
    data = yaml.safe_load(Path(path or RULES_FILE).read_text(encoding="utf-8"))
    assert data["schema"] == "truck-sim-pl/xsec-rules/1"
    for r in data["shoulder_rules"]:
        assert r["set"]["kind"] in KINDS, r["id"]
    assert data["shoulder_rules"][-1]["match"] == {}, "the last shoulder rule must match everything"
    return data


def _matches(m: dict, sec) -> bool:
    if "class" in m and sec.cls not in m["class"]:
        return False
    if "carriageway" in m and m["carriageway"] != ("dual" if sec.oneway else "single"):
        return False
    if "highway" in m and sec.highway not in m["highway"]:
        return False
    if "ref" in m and not re.fullmatch(m["ref"], str(getattr(sec, "ref", None) or "")):
        return False
    return True


def class_rule(sec, data: dict | None = None) -> Shoulder:
    data = data or rules()
    for r in data["shoulder_rules"]:
        if _matches(r["match"], sec):
            st = r["set"]
            paved = float(st["paved_m"])
            if st["kind"] == "ground":
                paved = max(paved, float(data["min_paved_m"]))
            return Shoulder(st["kind"], paved, float(st["ground_m"]), r["id"])
    raise AssertionError("no shoulder rule matched")


def _num(v):
    try:
        return float(str(v).split(";")[0].strip().replace(",", ".").removesuffix("m").strip())
    except (TypeError, ValueError):
        return None


def resolve(sec, side: str, data: dict | None = None) -> Shoulder:
    """Shoulder of `side` ("left" / "right" in the OSM edge direction) of a section."""
    data = data or rules()
    base = class_rule(sec, data)
    au = getattr(sec, "shoulder", None) or {}
    a = au.get(side) or au.get("both")
    if a:
        kind = a.get("kind", base.kind)
        src = f"authored_override:{a.get('id', '?')}"
        if kind == "kerb":
            return Shoulder(base.kind, base.paved_m, base.ground_m, src, force="kerb")
        dflt = base if kind == base.kind else Shoulder(kind, float(data["min_paved_m"]) if kind == "ground" else LEGACY[0],
                                                        base.ground_m, "")
        paved = float(a.get("paved_m", dflt.paved_m))
        if kind == "ground":
            paved = max(paved, float(data["min_paved_m"]))
        d = a.get("ditch_m")
        return Shoulder(kind, paved, float(a.get("ground_m", dflt.ground_m)), src, force="open",
                        ditch_m=None if d is None else max(float(d), FLAT_DITCH_M))
    o = getattr(sec, "osm_shoulder", None) or {}
    val = str(o.get("shoulder") or "")
    if val in ("yes", "both", side):
        cfg = data["osm_shoulder"]
        w = _num(o.get("shoulder:width")) or float(cfg["default_width_m"])
        if str(o.get("shoulder:surface") or "") in cfg["ground_surfaces"]:
            return Shoulder("ground", float(data["min_paved_m"]), w, "osm:shoulder", force="open")
        return Shoulder("paved", w, base.ground_m, "osm:shoulder", force="open")
    return base


def open_road(sec, data: dict | None = None) -> bool:
    """Class / speed rule: a chain whose middle section passes gets kerbless edges (where no footway is attached)."""
    cfg = (data or rules())["open_road"]
    return sec.cls in cfg["classes"] and (sec.maxspeed or 50) >= float(cfg["min_speed_kmh"])


def manholes_allowed(shoulders) -> bool:
    """Carriageway manhole covers at a station, given network.side_shoulder() of both edges: (paved_m, ground_m), or
    None beside a kerb. No covers where both edges are ground shoulders (paved part <= ground_max_paved_m)."""
    cfg = rules()["drainage"]
    if cfg["manholes_beside_ground_shoulder"]:
        return True
    return not all(s is not None and s[0] <= float(cfg["ground_max_paved_m"]) for s in shoulders)
