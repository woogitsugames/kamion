"""Before/after spectrogram of the 'siren' fix (ADR 0142): owner's APK 0138 recording vs the ambient path at idle in the cab
rendered offline with the runtime gains (AmbientAudio: bed 0.30 x cab 0.5; forklift 0.16 x cab 0.7 x swell ~1 before, 0 after).

    uv run python siren_ab.py
Output: artifacts/audio-fx/verify/siren_before_after.png (<= 960 px).
"""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
from scipy import signal  # noqa: E402

from el_analyze import MAIN  # noqa: E402
from el_prepare import ROOT  # noqa: E402

FS = 48000
ART = ROOT / "artifacts" / "audio-fx"


def loop(name: str, seconds: float) -> np.ndarray:
    man = json.loads((MAIN / "art-source/audio/generated/manifest.json").read_text(encoding="utf-8"))
    f = next(s["file"] for s in man["sfx"] if s["name"] == name)
    x = sf.read(MAIN / f)[0]
    x = x.mean(axis=1) if x.ndim > 1 else x
    return np.tile(x, int(np.ceil(seconds * FS / len(x))))[: int(seconds * FS)]


def main() -> None:
    T = 16.0
    bed = 0.30 * 0.5 * loop("ambient_bed_cab_loop", T)
    fork = 0.16 * 0.7 * loop("forklift_cab_loop", T)
    owner = sf.read(ART / "owner-video" / "owner.wav")[0][: int(T * FS)]
    fig, axs = plt.subplots(3, 1, figsize=(12.8, 9))
    for ax, (title, x) in zip(axs, [("owner recording, APK 0138 (idle + driving)", owner),
                                    ("ambient path in the cab, before (bed + procedural forklift)", bed + fork),
                                    ("ambient path in the cab, after ADR 0142 (forklift muted)", bed)]):
        f, t, S = signal.spectrogram(x, FS, nperseg=8192, noverlap=8192 - 1200)
        L = 10 * np.log10(S + 1e-14)
        ax.pcolormesh(t, f, L, shading="auto", cmap="magma", vmin=L.max() - 80, vmax=L.max())
        ax.set_ylim(0, 3000)
        ax.set_title(title, fontsize=10)
        ax.set_ylabel("Hz")
    axs[-1].set_xlabel("s")
    fig.tight_layout()
    out = ART / "verify" / "siren_before_after.png"
    fig.savefig(out, dpi=75)
    print(out)


if __name__ == "__main__":
    main()
