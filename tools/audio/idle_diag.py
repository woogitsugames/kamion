"""ADR 0148: diagnosis of the owner's Fold recording (engine idle / overrun sound).

Usage: uv run --project tools/audio python tools/audio/idle_diag.py <audio.wav> <outdir>
Segment spectra (Welch), notch search, harmonic (f0) via autocorrelation, amplitude-modulation spectrum.
"""
import sys, json
from pathlib import Path
import numpy as np, soundfile as sf
from scipy import signal

def load(p):
    x, fs = sf.read(p, always_2d=True)
    return x.mean(1), fs

def welch_db(x, fs, nper=16384):
    f, p = signal.welch(x, fs, nperseg=nper, noverlap=nper * 3 // 4)
    return f, 10 * np.log10(p + 1e-20)

def notches(f, db, lo=40, hi=1200):
    m = (f >= lo) & (f <= hi)
    ff, dd = f[m], db[m]
    # local depth vs median of +-20 Hz
    out = []
    for i in range(len(ff)):
        w = (ff > ff[i] - 25) & (ff < ff[i] + 25)
        depth = np.median(dd[w]) - dd[i]
        out.append(depth)
    out = np.array(out)
    pk, _ = signal.find_peaks(out, height=6, distance=10)
    return [(round(float(ff[k]), 1), round(float(out[k]), 1)) for k in pk]

def acf_f0(x, fs, fmin=25, fmax=120):
    x = x - x.mean()
    sos = signal.butter(4, [20, 600], btype="band", fs=fs, output="sos")
    y = signal.sosfiltfilt(sos, x)
    r = signal.fftconvolve(y, y[::-1])[len(y) - 1:]
    r /= r[0]
    lo, hi = int(fs / fmax), int(fs / fmin)
    k = lo + int(np.argmax(r[lo:hi]))
    return fs / k, float(r[k])

def am_spectrum(x, fs, band=(20, 400)):
    sos = signal.butter(4, band, btype="band", fs=fs, output="sos")
    env = np.abs(signal.hilbert(signal.sosfiltfilt(sos, x)))
    env = signal.decimate(env, 48)  # 1 kHz
    efs = fs / 48
    env = env - env.mean()
    f, p = signal.welch(env, efs, nperseg=1024)
    m = (f > 2) & (f < 100)
    k = np.argmax(p[m])
    cv = float(np.std(env) / (np.mean(np.abs(signal.hilbert(signal.sosfiltfilt(sos, x)))) + 1e-12))
    return float(f[m][k]), cv

def main():
    x, fs = load(sys.argv[1])
    out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    segs = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {"gas": [8.5, 14.5], "lift": [16.5, 26.0]}
    rep = {}
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(11, 5))
    for name, (t0, t1) in segs.items():
        s = x[int(t0 * fs):int(t1 * fs)]
        f, db = welch_db(s, fs)
        f0, r = acf_f0(s, fs)
        amf, amcv = am_spectrum(s, fs)
        rep[name] = {"t": [t0, t1], "rms_dbfs": round(20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-12), 1),
                     "notches": notches(f, db), "acf_f0_hz": round(f0, 1), "acf_peak": round(r, 2),
                     "am_peak_hz": round(amf, 1), "env_cv": round(amcv, 2)}
        ax.semilogx(f, db, label=f"{name} {t0}-{t1}s")
    ax.set_xlim(20, 4000); ax.grid(True, which="both", alpha=.3); ax.legend(); ax.set_xlabel("Hz"); ax.set_ylabel("dB")
    fig.savefig(out / "segments_spectrum.png", dpi=90)
    print(json.dumps(rep, indent=1))
    (out / "diag.json").write_text(json.dumps(rep, indent=1))

if __name__ == "__main__":
    main()
