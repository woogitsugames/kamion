"""Cabin vs exterior balance of the main layers at three driving states (ADR 0142, owner: engine too loud in the cab).

    uv run python cab_mix.py

Loudness of each layer at the listener = clip loudness (BS.1770 LUFS of the imported WAV) + 20 log10(runtime gain),
with the gains of TruckAudioController / EngineAudio / AmbientAudio mirrored here (keep in sync). Engine: equal-power
load blend of the off/on cells (ElevenLabs banks are incoherent), rpm interpolated in dB between grid cells. Distance
attenuation outside is ignored (all exterior sources sit within a few metres of each other on the truck).
Targets (UNVERIFIED design values from the literature summary in ADR 0142): in the cab at 80 km/h cruise the
tyre/road layer is at least level with the engine (tyre/road noise overtakes the driveline above ~80 km/h, Johnson 1996
via Mohammadi 2022, Archives of Acoustics 47(4)), wind a few dB under the engine; at idle the engine leads the cab.
Output: artifacts/audio-fx/cab_mix.txt
"""

from __future__ import annotations

import json
import math

import soundfile as sf

from el_analyze import MAIN, lufs
from el_prepare import ROOT

FS = 48000
STATES = [  # name, speed m/s, rpm, load (WORKING_VALUE operating points of the lab truck)
    ("idle, stationary", 0.0, 600, 0.10),
    ("50 km/h, 1300 rpm, cruise", 50 / 3.6, 1300, 0.40),
    ("80 km/h, 1150 rpm, cruise", 80 / 3.6, 1150, 0.40),
]
MIX = {  # set: (cab engine scale, cab road, cab wind, cab bed)
    "procedural (pre-0142 mix)": (1.0, 0.55, 0.35, 0.50),
    "ElevenLabs (0142 mix)": (0.7, 1.35, 1.45, 0.35),
}
ROAD, WIND, BED = 0.45, 0.30, 0.30


def db(g: float) -> float:
    return 20 * math.log10(max(g, 1e-9))


def psum(*levels: float) -> float:
    return 10 * math.log10(sum(10 ** (v / 10) for v in levels))


def main() -> None:
    el = json.loads((ROOT / "game/Assets/_Project/Audio/ElevenLabs/el_manifest.json").read_text(encoding="utf-8"))
    cells = {(c["perspective"], c["layer"], c["rpm"]): c["lufs"] for c in el["clips"] if c["kind"] == "engine"}
    syn = json.loads((MAIN / "art-source/audio/generated/manifest.json").read_text(encoding="utf-8"))
    L = {s["name"]: lufs(sf.read(MAIN / s["file"])[0], FS) for s in syn["sfx"]
         if s["name"] in ("road_roll_loop", "road_roll_cab_loop", "wind_loop", "wind_cab_loop", "ambient_bed_loop", "ambient_bed_cab_loop")}

    def engine(persp: str, rpm: float, load: float) -> float:
        grid = sorted({k[2] for k in cells})
        rpm = min(max(rpm, grid[0]), grid[-1])
        hi = next(g for g in grid if g >= rpm)
        lo = max(g for g in grid if g <= rpm)
        w = 0.0 if hi == lo else (rpm - lo) / (hi - lo)
        cell = lambda layer: (1 - w) * cells[(persp, layer, lo)] + w * cells[(persp, layer, hi)]
        a = load * math.pi / 2
        return psum(cell("off") + db(math.cos(a)), cell("on") + db(math.sin(a)))

    out = []
    for setname, (ce, cr, cw, cb) in MIX.items():
        out.append(f"== {setname}: cab engine x{ce}, cab road x{cr}, cab wind x{cw}, cab bed x{cb}")
        for name, v, rpm, load in STATES:
            vn = min(v / 25, 1)
            tyre = db(ROAD * vn ** 1.6) if v > 0 else -120
            wind = db(WIND * vn ** 2.2) if v > 0 else -120
            bed = db(BED * (1 - 0.55 * min(v / 20, 1)))
            ext = {"engine": engine("ext", rpm, load), "tyres": L["road_roll_loop"] + tyre, "wind": L["wind_loop"] + wind,
                   "ambience": L["ambient_bed_loop"] + bed}
            cab = {"engine": engine("cab", rpm, load) + db(ce), "tyres": L["road_roll_cab_loop"] + tyre + db(cr),
                   "wind": L["wind_cab_loop"] + wind + db(cw), "ambience": L["ambient_bed_cab_loop"] + bed + db(cb)}
            for persp, d in (("ext", ext), ("cab", cab)):
                rel = "  ".join(f"{k} {d[k] - d['engine']:+5.1f}" for k in ("tyres", "wind", "ambience"))
                out.append(f"  {name:28s} {persp}: engine {d['engine']:6.1f} LUFS, total {psum(*d.values()):6.1f}; rel. to engine: {rel}")
    txt = "\n".join(out)
    (ROOT / "artifacts/audio-fx/cab_mix.txt").write_text(txt + "\n", encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
