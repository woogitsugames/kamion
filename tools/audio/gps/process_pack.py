"""GPS voice pack processing (ADR 0328): ElevenLabs takes -> one normalised WAV per sentence + manifest + demo sentences.

    uv run --project tools/audio python tools/audio/gps/process_pack.py [--raw <dir>] [--demo <dir>]

Input: art-source/audio/elevenlabs/gps/raw (gitignored; files "<take> (n).mp3" as downloaded from the owner's ElevenLabs
account). Batch takes are split per sentence (split_take.py), the sentence count must match pack.py. Clips whose batch take
was rejected (speech rate check) come from the single-sentence takes in TAKE_OVERRIDES.
Output: game/Assets/_Project/Audio/Voice/Gps/GPS_Bxx_ii.wav (44.1 kHz mono PCM16) and
game/Assets/_Project/Audio/Voice/gps_manifest.json (read by Game.Editor.Audio.GpsVoiceImporter). Loudness: every clip at TARGET_LUFS (BS.1770 integrated, own
implementation in voice_qa.py); plosive peaks above PEAK_CEIL_DBFS go through a 3 ms look-ahead limiter (gain reduction per clip in the manifest).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).parent))
from pack import PACK, key  # noqa: E402
from split_take import cut, speech_segments  # noqa: E402
from voice_qa import SR, decode, integrated_lufs  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
MAIN_RAW = Path(r"C:\Users\matma\Documents\Claude\kamion\art-source\audio\elevenlabs\gps\raw")
OUT_DIR = REPO / "game/Assets/_Project/Audio/Voice/Gps"
MANIFEST = REPO / "game/Assets/_Project/Audio/Voice/gps_manifest.json"

TARGET_LUFS = -16.0      # docs/08 (mobile) + prompt pack; WORKING_VALUE
PEAK_CEIL_DBFS = -1.0
MAX_LIMIT_DB = 6.0       # largest allowed limiter gain reduction on a transient; WORKING_VALUE
MAX_SYL_PER_S = 8.0      # above = words swallowed by the TTS (batch B12 #1..#8 hit 9-11 syl/s); WORKING_VALUE

VOICE = {"name": "Kamion GPS", "voice_id": "QsH1g7itRvwZbnuW1zc5", "design_model": "eleven_multilingual_ttv_v2",
         "design_seed": 2411, "design_preview": 2, "tts_model": "eleven_multilingual_v2",
         "settings": "service defaults of the voice (the MCP connector exposes no stability/similarity controls)",
         "plan": "ElevenLabs Pro (ElevenCreative Pro, owner's account, commercial use)", "date": "2026-11-23"}

# batch take per block: (raw file, ElevenLabs generation id)
TAKES = {
    1: ("GPS_B01 (1).mp3", "xh6Sg3G7mZvaQCtcP4gs"), 2: ("GPS_B02 (1).mp3", "kGbzmAlbEXxMkKhwo1eO"),
    3: ("GPS_B03 (1).mp3", "8jv7dsXCXh3vwaEPCeMI"), 4: ("GPS_B04 (1).mp3", "jAZC8Pg127Wv8QCGlsWN"),
    5: ("GPS_B05 (1).mp3", "Cb19J1KXRJJH2zW5RIV2"), 6: ("GPS_B06 (1).mp3", "u2vjao4dVlJfPq7V12t5"),
    7: ("GPS_B07 (1).mp3", "Q2Kreg6FMxxn0Hd4lVUJ"), 8: ("GPS_B08 (1).mp3", "kHzyjLtz4FRkHjtPXHyV"),
    9: ("GPS_B09 (1).mp3", "k6nX1hKAiunOidcuEES1"), 10: ("GPS_B10 (1).mp3", "LvbM98sP8uh9j8nozaKM"),
    12: ("GPS_B12 (1).mp3", "UQOAHECIfCe554e0GgjB"), 13: ("GPS_B13 (1).mp3", "DyOqtPlLPRDam1KaVm8o"),
    14: ("GPS_B14 (1).mp3", "QDCSu0gfHkvuQ0I3WCc3"),
}
# clip key -> (raw file, generation id, segment index in that take (0-based), number of sentences in the take)
TAKE_OVERRIDES = {
    "GPS_B12_01": ("GPS_TEST (1).mp3", "OnygSV0bnXZCTbE5YxLy", 3, 4),
    "GPS_B12_02": ("GPS_B12_02 (2).mp3", "b75LCRJ4KnIGVALhB6as", 0, 1),
    "GPS_B12_03": ("GPS_B12_03 (2).mp3", "F3uCGWuQneWXaMri4M2D", 0, 1),
    "GPS_B12_04": ("GPS_B12_04 (2).mp3", "WaCtEyxyp4B10WYHTb9s", 0, 1),
    "GPS_B12_05": ("GPS_B12_05 (2).mp3", "wtU7UtlGoqmPcedhB3pj", 0, 1),
    "GPS_B12_06": ("GPS_B12_06 (2).mp3", "d1WL2wC6U0SWXOKkAIkC", 0, 1),
    "GPS_B12_07": ("GPS_B12_07 (2).mp3", "IKva5MZdRWmcDh08Khhu", 0, 1),
    "GPS_B12_08": ("GPS_B12_08 (2).mp3", "5m7piXRxu5cupugTUwY3", 0, 1),
    "GPS_B12_09": ("GPS_B12_09 (2).mp3", "tTPFsHn6QG4PJtN1P7iV", 0, 1),
    # B15 (ADR 0329 addendum): ring names in the nominative, two single-sentence takes, voice Kamion GPS, eleven_multilingual_v2
    "GPS_B15_01": ("GPS_B15_01 (1).mp3", "zu1PKMApKUX6yqBbZket", 0, 1),
    "GPS_B15_02": ("GPS_B15_02 (1).mp3", "nZI6TQI6g5gkDrDd5yUb", 0, 1),
    "GPS_B15_03": ("GPS_B15_03 (1).mp3", "fEc10YgtpHptsewVlKur", 0, 1),
    "GPS_B15_04": ("GPS_B15_04 (1).mp3", "ebsm0Yus1QCBR8zGNVHM", 0, 1),
}

DEMO_GAP_S = 0.08   # = NavVoicePlayer.ClipGapS
DEMOS = [
    ("demo1_300m_prawo_andersa", ["GPS_B04_01", "GPS_B12_01"]),
    ("demo2_200m_rondo_2zjazd_putry", ["GPS_B03_08", "GPS_B07_02", "GPS_B15_01"]),
    ("demo3_teraz_lewo_nastepnie_prawo_pas", ["GPS_B01_02", "GPS_B08_01", "GPS_B09_01"]),
    ("demo4_1km_prawo_wilenska", ["GPS_B06_01", "GPS_B12_10"]),
    ("demo5_500m_lewo_cel", ["GPS_B05_02", "GPS_B13_05", "GPS_B08_07"]),
]


def syllables(t: str) -> int:
    v, t, n = "aąeęioóuy", t.lower(), 0
    for i, c in enumerate(t):
        if c in v and not (c == "i" and i + 1 < len(t) and t[i + 1] in v):
            n += 1
    return n


def limit(y: np.ndarray, ceil_dbfs: float, look_s: float = 0.003, release_s: float = 0.06) -> tuple[np.ndarray, float]:
    """Look-ahead peak limiter: gain = running min of ceil/|x| over the look-ahead, attack within it, exponential release.
    Returns the limited signal and the largest gain reduction [dB]."""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    c = 10 ** (ceil_dbfs / 20)
    need = np.minimum(1.0, c / (np.abs(y) + 1e-12))
    la = max(1, int(look_s * SR))
    g = minimum_filter1d(need, size=2 * la + 1, mode="nearest")
    rel = np.exp(-1.0 / (release_s * SR))
    out = np.empty_like(g)
    cur = 1.0
    for i, v in enumerate(g):
        cur = v if v < cur else v + (cur - v) * rel
        out[i] = cur
    # attack smoothing: symmetric moving average over the look-ahead, then re-clamp to the requirement
    sm = np.minimum(uniform_filter1d(out, size=la, mode="nearest"), out)
    y2 = y * sm
    y2 = np.clip(y2, -c, c)
    return y2, float(-20 * np.log10(np.min(sm)))


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(MAIN_RAW))
    ap.add_argument("--demo")
    ap.add_argument("--only", type=int, nargs="*", help="process only these blocks and merge them into the existing manifest")
    a = ap.parse_args()
    raw = Path(a.raw)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cache: dict[str, tuple[np.ndarray, list]] = {}

    def segments(fname: str):
        if fname not in cache:
            x = decode(raw / fname)
            cache[fname] = (x, speech_segments(x, SR))
        return cache[fname]

    clips, errors = [], []
    for b in sorted(PACK):
        if a.only and b not in a.only:
            continue
        if b in TAKES:
            fname, gen = TAKES[b]
            x, segs = segments(fname)
        else:   # every clip of the block comes from TAKE_OVERRIDES
            fname, gen, x, segs = None, None, None, [None] * len(PACK[b])
        if len(segs) != len(PACK[b]):
            errors.append(f"B{b:02d}: {len(segs)} segments, want {len(PACK[b])}")
            continue
        for n, (idx, text) in enumerate(PACK[b]):
            k = key(b, idx)
            src, sgen, si = fname, gen, n
            if k in TAKE_OVERRIDES:
                src, sgen, si, want = TAKE_OVERRIDES[k]
                ox, osegs = segments(src)
                if len(osegs) != want:
                    errors.append(f"{k}: override take {src} has {len(osegs)} segments, want {want}")
                    continue
                y = cut(ox, SR, osegs[si])
                speech_s = (osegs[si][1] - osegs[si][0]) / SR
            else:
                y = cut(x, SR, segs[si])
                speech_s = (segs[si][1] - segs[si][0]) / SR
            rate = syllables(text) / speech_s
            if rate > MAX_SYL_PER_S:
                errors.append(f"{k}: {rate:.1f} syl/s > {MAX_SYL_PER_S} (swallowed words?) '{text}'")
            lufs = integrated_lufs(y, SR)
            gain_db = TARGET_LUFS - lufs
            y = y * 10 ** (gain_db / 20)
            y, gr_db = limit(y, PEAK_CEIL_DBFS)
            if gr_db > MAX_LIMIT_DB:
                errors.append(f"{k}: limiter {gr_db:.1f} dB > {MAX_LIMIT_DB}")
            out = OUT_DIR / f"{k}.wav"
            sf.write(out, y, SR, subtype="PCM_16")
            clips.append({
                "key": k, "block": b, "index": idx, "text": text, "file": f"Gps/{k}.wav", "sha256": sha256(out),
                "duration_s": round(len(y) / SR, 3), "lufs": round(integrated_lufs(y, SR), 2),
                "peak_dbfs": round(float(20 * np.log10(np.max(np.abs(y)) + 1e-12)), 2), "gain_db": round(gain_db, 2), "limiter_gr_db": round(gr_db, 2),
                "syllables_per_s": round(rate, 2), "source_take": src, "source_segment": si,
                "elevenlabs_generation_id": sgen,
            })
    if errors:
        print("ERRORS:\n  " + "\n  ".join(errors))
    if a.only:
        old = json.loads(MANIFEST.read_text(encoding="utf-8"))
        keep = [c for c in old["clips"] if c["block"] not in a.only]
        clips = sorted(keep + clips, key=lambda c: (c["block"], c["index"]))
    manifest = {
        "generator": "tools/audio/gps/process_pack.py (ADR 0328)", "pack": "docs/owner/ELEVENLABS-GPS-VOICE.md",
        "voice": VOICE, "target_lufs": TARGET_LUFS, "peak_ceiling_dbfs": PEAK_CEIL_DBFS, "sample_rate": SR,
        "processed": dt.date.today().isoformat(), "clip_count": len(clips), "clips": clips,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(clips)} clips -> {OUT_DIR}; manifest {MANIFEST}")
    if a.demo:
        d = Path(a.demo)
        d.mkdir(parents=True, exist_ok=True)
        gap = np.zeros(int(DEMO_GAP_S * SR))
        for name, keys in DEMOS:
            parts = []
            for k in keys:
                y, _ = sf.read(OUT_DIR / f"{k}.wav")
                parts += [y, gap]
            sf.write(d / f"{name}.wav", np.concatenate([np.zeros(int(0.2 * SR))] + parts[:-1] + [np.zeros(int(0.3 * SR))]),
                     SR, subtype="PCM_16")
        print(f"{len(DEMOS)} demo sentences -> {d}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
