"""ADR 0148: fine spectrogram (0-600 Hz) + envelope of a wav, for the idle diagnosis. Args: wav out.png [t0 t1]"""
import sys
import numpy as np, soundfile as sf
from scipy import signal
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
x, fs = sf.read(sys.argv[1], always_2d=True); x = x.mean(1)
if len(sys.argv) > 4: x = x[int(float(sys.argv[3]) * fs):int(float(sys.argv[4]) * fs)]
f, t, S = signal.spectrogram(x, fs, nperseg=8192, noverlap=8192 - 480)
m = f <= 600
fig, ax = plt.subplots(2, 1, figsize=(12, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
ax[0].pcolormesh(t, f[m], 10 * np.log10(S[m] + 1e-14), shading="auto", vmin=10 * np.log10(S[m].max()) - 60, cmap="magma")
ax[0].set_ylabel("Hz")
sos = signal.butter(4, [20, 400], btype="band", fs=fs, output="sos")
env = np.abs(signal.hilbert(signal.sosfiltfilt(sos, x)))
sos2 = signal.butter(2, 60, fs=fs, output="sos"); env = signal.sosfiltfilt(sos2, env)
tt = np.arange(len(env)) / fs
ax[1].plot(tt[::48], 20 * np.log10(env[::48] + 1e-6), lw=.5); ax[1].set_ylabel("env dB (20-400 Hz)"); ax[1].set_xlabel("s")
fig.tight_layout(); fig.savefig(sys.argv[2], dpi=80)
