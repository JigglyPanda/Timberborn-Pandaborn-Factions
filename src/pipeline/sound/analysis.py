"""Measurements used to check every sound without listening to it.

* loudness: ITU-R BS.1770-4 integrated loudness (K-weighting, 400 ms blocks, 75 % overlap, -70 LUFS absolute and
  -10 LU relative gates), momentary max (400 ms) and short-term max (3 s); sample peak and 4x-oversampled true peak;
  RMS; DC offset; clipping count.
* spectrum: spectral centroid, 85 % roll-off, energy share in bands (sub < 80 Hz, low 80-300, mid 300-2k, presence 2-5k,
  air > 5k): "shrill" shows up as presence + air share and a high centroid.
* envelope: attack (10 %->90 % of the peak of the 10 ms RMS envelope), time to -40 dB after the peak (decay).
* loop: the seam (last sample -> first sample) against the clip's own sample-to-sample steps, the seam's 10 ms RMS
  against the neighbouring windows, the spectrum of the 100 ms on both sides of the seam, and the strongest
  autocorrelation peak of the envelope between 0.25 s and half the clip (an obvious short period).
* spectrogram PNG (matplotlib, Agg) with the waveform and the RMS envelope.

Pure numpy/scipy; run in the E: venv with -I.
"""
import math
import wave

import numpy as np
from scipy import signal

BANDS = [("sub", 0, 80), ("low", 80, 300), ("mid", 300, 2000), ("presence", 2000, 5000), ("air", 5000, 1e9)]


# ------------------------------------------------------------------------------------------------------------ io
def read_wav(path):
    """Returns (float64 array shaped (n, channels) in -1..1, sample rate)."""
    with wave.open(path, "rb") as w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if sw == 2:
        x = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        v = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (b[:, 2].astype(np.int32) << 16))
        v = np.where(v >= 1 << 23, v - (1 << 24), v)
        x = v.astype(np.float64) / float(1 << 23)
    elif sw == 4:
        x = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    elif sw == 1:
        x = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128.0) / 128.0
    else:
        raise ValueError("unsupported sample width %d" % sw)
    return x.reshape(-1, ch), sr


def write_wav(path, x, sr):
    """x: float array (n,) or (n, ch) in -1..1 -> 16-bit PCM with TPDF dither (deterministic seed)."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    rng = np.random.default_rng(12345)
    d = (rng.random(x.shape) - rng.random(x.shape)) / 32768.0
    q = np.clip(np.round((x + d) * 32767.0), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(q.tobytes())


def mono(x):
    return x.mean(axis=1) if x.ndim == 2 else x


# ------------------------------------------------------------------------------------------------------- loudness
def _k_filters(sr):
    """BS.1770 K-weighting as two biquads, designed for any sample rate (same constants as pyloudnorm)."""
    # stage 1: high shelf
    G, Q, fc = 3.999843853973347, 0.7071752369554196, 1681.974450955533
    A = 10 ** (G / 40.0)
    w0 = 2.0 * math.pi * fc / sr
    alpha = math.sin(w0) / (2.0 * Q)
    b0 = A * ((A + 1) + (A - 1) * math.cos(w0) + 2 * math.sqrt(A) * alpha)
    b1 = -2 * A * ((A - 1) + (A + 1) * math.cos(w0))
    b2 = A * ((A + 1) + (A - 1) * math.cos(w0) - 2 * math.sqrt(A) * alpha)
    a0 = (A + 1) - (A - 1) * math.cos(w0) + 2 * math.sqrt(A) * alpha
    a1 = 2 * ((A - 1) - (A + 1) * math.cos(w0))
    a2 = (A + 1) - (A - 1) * math.cos(w0) - 2 * math.sqrt(A) * alpha
    shelf = (np.array([b0, b1, b2]) / a0, np.array([1.0, a1 / a0, a2 / a0]))
    # stage 2: high pass
    Q, fc = 0.5003270373238773, 38.13547087602444
    w0 = 2.0 * math.pi * fc / sr
    alpha = math.sin(w0) / (2.0 * Q)
    b0, b1, b2 = (1 + math.cos(w0)) / 2, -(1 + math.cos(w0)), (1 + math.cos(w0)) / 2
    a0, a1, a2 = 1 + alpha, -2 * math.cos(w0), 1 - alpha
    hp = (np.array([b0, b1, b2]) / a0, np.array([1.0, a1 / a0, a2 / a0]))
    return shelf, hp


def _k_weighted_power(x, sr):
    if x.ndim == 1:
        x = x[:, None]
    shelf, hp = _k_filters(sr)
    y = signal.lfilter(shelf[0], shelf[1], x, axis=0)
    y = signal.lfilter(hp[0], hp[1], y, axis=0)
    return y ** 2  # (n, ch); channel weights are 1.0 for L/R/C/mono


def _block_loudness(p, sr, win_s, hop_s):
    n = p.shape[0]
    win, hop = int(round(win_s * sr)), int(round(hop_s * sr))
    if n < win:
        z = p.mean(axis=0).sum()
        return np.array([-0.691 + 10 * math.log10(z) if z > 0 else -120.0]), np.array([z])
    starts = range(0, n - win + 1, hop)
    cs = np.vstack([np.zeros((1, p.shape[1])), np.cumsum(p, axis=0)])
    z = np.array([((cs[s + win] - cs[s]) / win).sum() for s in starts])
    with np.errstate(divide="ignore"):
        l = -0.691 + 10 * np.log10(np.maximum(z, 1e-30))
    return l, z


def integrated_lufs(x, sr):
    p = _k_weighted_power(x, sr)
    l, z = _block_loudness(p, sr, 0.4, 0.1)
    keep = l > -70.0
    if not keep.any():
        return -120.0
    rel = -0.691 + 10 * math.log10(z[keep].mean()) - 10.0
    keep2 = keep & (l > rel)
    if not keep2.any():
        return -120.0
    return -0.691 + 10 * math.log10(z[keep2].mean())


def momentary_max(x, sr):
    l, _ = _block_loudness(_k_weighted_power(x, sr), sr, 0.4, 0.1)
    return float(l.max())


def short_term_max(x, sr):
    l, _ = _block_loudness(_k_weighted_power(x, sr), sr, 3.0, 0.1)
    return float(l.max())


def true_peak_db(x, sr):
    m = x if x.ndim == 1 else x
    up = signal.resample_poly(m, 4, 1, axis=0)
    pk = float(np.max(np.abs(up)))
    return 20 * math.log10(pk) if pk > 0 else -120.0


# -------------------------------------------------------------------------------------------------------- spectrum
def spectrum(xm, sr, nfft=8192):
    f, pxx = signal.welch(xm, fs=sr, nperseg=min(nfft, max(256, len(xm))), scaling="spectrum")
    return f, pxx


def spectral_stats(xm, sr):
    f, p = spectrum(xm, sr)
    tot = p.sum() or 1e-30
    centroid = float((f * p).sum() / tot)
    c = np.cumsum(p) / tot
    rolloff = float(f[np.searchsorted(c, 0.85)])
    bands = {name: float(p[(f >= lo) & (f < hi)].sum() / tot) for name, lo, hi in BANDS}
    return centroid, rolloff, bands


# -------------------------------------------------------------------------------------------------------- envelope
def rms_envelope(xm, sr, win_s=0.01):
    win = max(1, int(sr * win_s))
    n = len(xm) // win
    if n == 0:
        return np.array([float(np.sqrt(np.mean(xm ** 2)))]), win_s
    e = np.sqrt((xm[: n * win].reshape(n, win) ** 2).mean(axis=1))
    return e, win_s


def envelope_stats(xm, sr):
    e, dt = rms_envelope(xm, sr)
    pk = e.max() or 1e-12
    i_pk = int(e.argmax())
    above10 = np.nonzero(e >= 0.1 * pk)[0]
    above90 = np.nonzero(e >= 0.9 * pk)[0]
    attack = (above90[0] - above10[0]) * dt if len(above10) and len(above90) else 0.0
    after = e[i_pk:]
    below = np.nonzero(after < pk * 10 ** (-40 / 20))[0]
    decay40 = below[0] * dt if len(below) else None
    return {"attack_s": round(float(attack), 3), "peak_at_s": round(i_pk * dt, 3),
            "decay_to_-40dB_s": None if decay40 is None else round(float(decay40), 3)}


# ------------------------------------------------------------------------------------------------------------ loop
def loop_stats(xm, sr):
    """How seamless the clip is when played on repeat (end -> start)."""
    d = np.abs(np.diff(xm))
    seam = abs(xm[0] - xm[-1])
    ref = float(np.percentile(d, 99.9)) or 1e-12
    # 10 ms RMS across the seam vs. the median of all windows
    w = int(0.01 * sr)
    wrapped = np.concatenate([xm[-w:], xm[:w]])
    e_seam = float(np.sqrt(np.mean(wrapped ** 2)))
    e_all, _ = rms_envelope(xm, sr)
    e_med = float(np.median(e_all)) or 1e-12
    # spectra of the 100 ms before the end and after the start
    k = int(0.1 * sr)
    fa, pa = signal.welch(xm[-k:], fs=sr, nperseg=min(2048, k))
    fb, pb = signal.welch(xm[:k], fs=sr, nperseg=min(2048, k))
    la, lb = 10 * np.log10(pa + 1e-20), 10 * np.log10(pb + 1e-20)
    band = (fa > 60) & (fa < 8000)
    spec_diff = float(np.mean(np.abs(la[band] - lb[band])))
    # repetition inside the clip: autocorrelation of the 10 ms envelope (mean removed)
    e = e_all - e_all.mean()
    ac = np.correlate(e, e, mode="full")[len(e) - 1:]
    ac = ac / (ac[0] or 1e-12)
    lo, hi = int(0.25 / 0.01), max(int(0.25 / 0.01) + 1, len(e) // 2)
    # the most *prominent* local maximum of the autocorrelation: its height above the lowest point between lag 0 and
    # it. A repeating envelope dips and comes back (high prominence); a slowly varying one just correlates with itself
    # at short lags (prominence near 0), which a plain argmax would wrongly report as a period.
    period, strength = None, None
    if hi > lo + 2:
        best = 0.0
        for j in range(lo, hi):
            if ac[j] > ac[j - 1] and ac[j] >= ac[j + 1]:
                prom = float(ac[j] - ac[1:j].min())
                if prom > best:
                    best, period = prom, j * 0.01
        strength = best if period is not None else None
    return {"seam_jump": round(float(seam), 5), "seam_jump_vs_p99.9_step": round(float(seam / ref), 3),
            "seam_rms_vs_median": round(e_seam / e_med, 3), "seam_spectrum_diff_db": round(spec_diff, 2),
            "envelope_period_s": None if period is None else round(period, 2),
            "envelope_period_prominence": None if strength is None else round(strength, 3)}


# ------------------------------------------------------------------------------------------------------- one call
def measure(x, sr, loop=False):
    xm = mono(x)
    centroid, rolloff, bands = spectral_stats(xm, sr)
    pk = float(np.max(np.abs(x))) or 1e-12
    r = {
        "seconds": round(len(xm) / sr, 3),
        "rate": sr,
        "channels": 1 if x.ndim == 1 else x.shape[1],
        "lufs_integrated": round(integrated_lufs(x, sr), 2),
        "lufs_momentary_max": round(momentary_max(x, sr), 2),
        "lufs_short_term_max": round(short_term_max(x, sr), 2),
        "rms_db": round(20 * math.log10(float(np.sqrt(np.mean(xm ** 2))) or 1e-12), 2),
        "peak_db": round(20 * math.log10(pk), 2),
        "true_peak_db": round(true_peak_db(x, sr), 2),
        "dc": round(float(np.mean(xm)), 6),
        "clipped_samples": int(np.sum(np.abs(x) >= 0.9999)),
        "centroid_hz": round(centroid),
        "rolloff85_hz": round(rolloff),
        "bands": {k: round(v, 3) for k, v in bands.items()},
    }
    r.update(envelope_stats(xm, sr))
    if loop:
        r["loop"] = loop_stats(xm, sr)
    return r


# ---------------------------------------------------------------------------------------------------- spectrogram
def spectrogram_png(x, sr, path, title, loop=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xm = mono(x)
    xs = np.concatenate([xm, xm[: int(min(len(xm), sr * 1.0))]]) if loop else xm
    fig, axes = plt.subplots(3, 1, figsize=(11, 7.5), gridspec_kw={"height_ratios": [1, 1, 3]}, sharex=True)
    t = np.arange(len(xs)) / sr
    axes[0].plot(t, xs, lw=0.4, color="#334")
    axes[0].set_ylim(-1, 1)
    axes[0].set_ylabel("wave")
    e, dt = rms_envelope(xs, sr)
    with np.errstate(divide="ignore"):
        axes[1].plot(np.arange(len(e)) * dt, 20 * np.log10(np.maximum(e, 1e-6)), lw=0.8, color="#a33")
    axes[1].set_ylim(-80, 0)
    axes[1].set_ylabel("RMS dB")
    nper = 2048 if sr >= 44100 else 1024
    f, tt, s = signal.spectrogram(xs, fs=sr, nperseg=nper, noverlap=nper * 3 // 4, scaling="spectrum")
    with np.errstate(divide="ignore"):
        sd = 10 * np.log10(s + 1e-14)
    vmax = sd.max()
    axes[2].pcolormesh(tt, f, sd, vmin=vmax - 90, vmax=vmax, shading="auto", cmap="magma")
    axes[2].set_yscale("symlog", linthresh=500)
    axes[2].set_ylim(30, sr / 2)
    axes[2].set_ylabel("Hz")
    axes[2].set_xlabel("s" + ("  (clip + first 1 s again: the loop seam is at %.2f s)" % (len(xm) / sr) if loop else ""))
    if loop:
        for a in axes:
            a.axvline(len(xm) / sr, color="#3a3", lw=0.8, ls="--")
    fig.suptitle(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=80)
    plt.close(fig)
