"""DSP building blocks for the Pandaborn sounds. Everything is synthesized here from noise, impulses and sine waves:
no samples of any kind. Deterministic: every random choice comes from a seeded numpy Generator.

Loops are built *circularly* so that they are seamless by construction:
  * noise beds are shaped in the frequency domain (an FFT filter is circular), see `circ_noise`;
  * IIR filters on a loop run over two copies and keep the second (`circ_sosfilt`, `circ_lfilter`): the filter state at
    the start of the kept copy is the state at the end of the loop;
  * events (a creak, a drip, a drum hit) are added with `Timeline.add(..., wrap=True)`: whatever rings past the end is
    added back at the start;
  * slow modulations use whole numbers of cycles per loop (`lfo`);
  * reverb on a loop is an FFT (circular) convolution (`reverb(..., circular=True)`).
"""
import math

import numpy as np
from scipy import signal

SR = 48000


# --------------------------------------------------------------------------------------------------------- basics
def n_of(seconds, sr=SR):
    return int(round(seconds * sr))


def tvec(n, sr=SR):
    return np.arange(n) / sr


def rng(seed):
    return np.random.default_rng(seed)


def db(x):
    return 10 ** (x / 20.0)


def fade(x, fin=0.0, fout=0.0, sr=SR):
    """Raised-cosine fade in/out (seconds); works on (n,) and (n, ch)."""
    x = x.copy()
    a, b = n_of(fin, sr), n_of(fout, sr)
    if a > 0:
        w = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))
        x[:a] = (x[:a].T * w).T
    if b > 0:
        w = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, b))
        x[-b:] = (x[-b:].T * w).T
    return x


def exp_env(n, t60, sr=SR, delay=0):
    """Exponential decay reaching -60 dB after t60 seconds."""
    t = tvec(n, sr)
    e = np.exp(-6.907755 * t / max(t60, 1e-4))
    if delay:
        e = np.concatenate([np.zeros(delay), e[: n - delay]])
    return e


def attack_decay(n, attack, t60, sr=SR, curve=2.0):
    t = tvec(n, sr)
    a = np.clip(t / max(attack, 1e-5), 0, 1) ** curve
    return a * np.exp(-6.907755 * np.maximum(t - attack, 0) / max(t60, 1e-4))


def lfo(n, cycles, phase=0.0, sr=SR):
    """Sine with a whole number of cycles over n samples (seamless when looped)."""
    return np.sin(2 * np.pi * cycles * np.arange(n) / n + phase)


def smooth_random(n, points, r, lo=0.0, hi=1.0, circular=True):
    """A slow random curve through `points` random values (periodic cubic when circular)."""
    from scipy.interpolate import CubicSpline
    v = r.uniform(lo, hi, points)
    if circular:
        xs = np.linspace(0, n, points + 1)
        cs = CubicSpline(xs, np.append(v, v[0]), bc_type="periodic")
    else:
        xs = np.linspace(0, n, points)
        cs = CubicSpline(xs, v)
    return cs(np.arange(n))


# ---------------------------------------------------------------------------------------------------------- noise
def white(n, r):
    return r.standard_normal(n)


def circ_noise(n, r, shape, sr=SR):
    """Circular coloured noise: white noise shaped in the frequency domain by shape(f) (amplitude), unit RMS."""
    X = np.fft.rfft(r.standard_normal(n))
    f = np.fft.rfftfreq(n, 1.0 / sr)
    X *= shape(f)
    y = np.fft.irfft(X, n)
    s = np.sqrt(np.mean(y ** 2)) or 1.0
    return y / s


def shape_band(lo, hi, slope_lo=12.0, slope_hi=12.0):
    """Smooth band shape: flat between lo and hi, `slope` dB/octave outside."""
    def f(fr):
        fr = np.maximum(fr, 1.0)
        g = np.ones_like(fr)
        below = fr < lo
        above = fr > hi
        g[below] = (fr[below] / lo) ** (slope_lo / 6.02)
        g[above] = (hi / fr[above]) ** (slope_hi / 6.02)
        return g
    return f


def shape_pink(lo=20.0, hi=20000.0):
    def f(fr):
        fr = np.maximum(fr, 1.0)
        g = 1.0 / np.sqrt(fr)
        g[fr < lo] *= (fr[fr < lo] / lo) ** 2
        g[fr > hi] *= (hi / fr[fr > hi]) ** 2
        return g
    return f


def shape_brown(lo=20.0, hi=2000.0):
    def f(fr):
        fr = np.maximum(fr, 1.0)
        g = 1.0 / fr
        g[fr < lo] *= (fr[fr < lo] / lo) ** 2
        g[fr > hi] *= (hi / fr[fr > hi]) ** 2
        return g
    return f


# -------------------------------------------------------------------------------------------------------- filters
def sos_band(lo, hi, order=2, sr=SR):
    return signal.butter(order, [lo, hi], btype="bandpass", fs=sr, output="sos")


def sos_low(fc, order=2, sr=SR):
    return signal.butter(order, fc, btype="lowpass", fs=sr, output="sos")


def sos_high(fc, order=2, sr=SR):
    return signal.butter(order, fc, btype="highpass", fs=sr, output="sos")


def sosf(sos, x):
    return signal.sosfilt(sos, x, axis=0)


def circ_sosfilt(sos, x):
    """IIR filtering of a loop: run over two copies, keep the second (state wraps around)."""
    n = len(x)
    y = signal.sosfilt(sos, np.concatenate([x, x]), axis=0)
    return y[n:]


def peaking(f0, gain_db, q, sr=SR):
    """RBJ peaking EQ biquad as (b, a)."""
    A = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / sr
    al = np.sin(w0) / (2 * q)
    b = np.array([1 + al * A, -2 * np.cos(w0), 1 - al * A])
    a = np.array([1 + al / A, -2 * np.cos(w0), 1 - al / A])
    return b / a[0], a / a[0]


def eq(x, bands, circular=False, sr=SR):
    """bands: [(f0, gain_db, q)] applied in series."""
    for f0, g, q in bands:
        b, a = peaking(f0, g, q, sr)
        if circular:
            n = len(x)
            x = signal.lfilter(b, a, np.concatenate([x, x]), axis=0)[n:]
        else:
            x = signal.lfilter(b, a, x, axis=0)
    return x


def resonator(x, f0, t60, sr=SR):
    """Two-pole resonator (unit peak gain roughly) driven by x; rings at f0 with the given T60."""
    rr = math.exp(-6.907755 / (t60 * sr))
    w = 2 * math.pi * f0 / sr
    a = [1.0, -2 * rr * math.cos(w), rr * rr]
    b = [(1 - rr * rr) * 0.5]
    return signal.lfilter(b, a, x)


def resonator_bank(x, modes, sr=SR, circular=False):
    """modes: [(freq, t60, gain)]. Sum of resonators driven by the same excitation."""
    y = np.zeros(len(x))
    if circular:
        n = len(x)
        xx = np.concatenate([x, x])
        for f0, t60, g in modes:
            if f0 < sr / 2 * 0.95:
                y += g * resonator(xx, f0, t60, sr)[n:]
        return y
    for f0, t60, g in modes:
        if f0 < sr / 2 * 0.95:
            y += g * resonator(x, f0, t60, sr)
    return y


# ---------------------------------------------------------------------------------------------------- excitations
def click(n_len, r, bright=0.5, sr=SR):
    """A short strike excitation: a raised-cosine pulse (soft mallet) mixed with a little noise.
    bright 0..1: 0 = soft felt-like thud, 1 = hard click."""
    width = int(sr * (0.0035 - 0.0029 * bright))  # 3.5 ms soft .. 0.6 ms hard
    width = max(width, 4)
    p = np.zeros(n_len)
    w = 0.5 - 0.5 * np.cos(np.linspace(0, 2 * np.pi, width))
    p[:width] = w
    nz = r.standard_normal(width * 3) * np.exp(-np.linspace(0, 6, width * 3)) * (0.15 + 0.5 * bright)
    p[: width * 3] += nz * 0.3
    return p


def noise_burst(n_len, r, dur, lo, hi, attack=0.002, sr=SR):
    k = min(n_len, n_of(dur, sr))
    b = r.standard_normal(k) * attack_decay(k, attack, dur * 0.9, sr)
    b = sosf(sos_band(lo, min(hi, sr * 0.45), 2, sr), b)
    out = np.zeros(n_len)
    out[:k] = b
    return out


# --------------------------------------------------------------------------------------------------------- modal
def modal(dur, partials, r, sr=SR, phase_random=True):
    """Directly summed decaying sines: partials [(freq, amp, t60)] (+ optional 'beat' doublet width in Hz as 4th)."""
    n = n_of(dur, sr)
    t = tvec(n, sr)
    y = np.zeros(n)
    for p in partials:
        f, a, t60 = p[0], p[1], p[2]
        beat = p[3] if len(p) > 3 else 0.0
        if f >= sr * 0.45:
            continue
        ph = r.uniform(0, 2 * np.pi) if phase_random else 0.0
        e = np.exp(-6.907755 * t / t60)
        if beat:
            # a doublet: two close modes (slightly unequal) -> slow beating, as in a real bell
            y += a * e * (0.62 * np.sin(2 * np.pi * (f - beat / 2) * t + ph) + 0.38 * np.sin(2 * np.pi * (f + beat / 2) * t + ph * 1.7))
        else:
            y += a * e * np.sin(2 * np.pi * f * t + ph)
    return y


# ------------------------------------------------------------------------------------------------------- timeline
class Timeline:
    """A buffer events are mixed into. wrap=True adds the overflow past the end back at the start (for loops)."""

    def __init__(self, seconds, sr=SR, channels=1):
        self.sr = sr
        self.n = n_of(seconds, sr)
        self.buf = np.zeros((self.n, channels)) if channels > 1 else np.zeros(self.n)

    def add(self, x, at_s, gain=1.0, wrap=True):
        i = int(round(at_s * self.sr)) % self.n if wrap else int(round(at_s * self.sr))
        x = np.asarray(x) * gain
        k = len(x)
        if not wrap:
            if i >= self.n:
                return
            k = min(k, self.n - i)
            self.buf[i:i + k] += x[:k]
            return
        pos = 0
        while pos < len(x):
            take = min(len(x) - pos, self.n - i)
            self.buf[i:i + take] += x[pos:pos + take]
            pos += take
            i = 0


# -------------------------------------------------------------------------------------------------------- reverb
def reverb_ir(seconds, rt60, r, sr=SR, damp_hz=4000.0, predelay=0.0, channels=1, early=()):
    """Exponentially decaying noise, darkening over time (a stand-in for a small outdoor / wooden space)."""
    n = n_of(seconds, sr)
    t = tvec(n, sr)
    outs = []
    for c in range(channels):
        nz = r.standard_normal(n) * np.exp(-6.907755 * t / rt60)
        # time-varying darkening: blend a low-passed copy in as the tail grows
        lp = sosf(sos_low(damp_hz, 1, sr), nz)
        lp2 = sosf(sos_low(damp_hz * 0.35, 1, sr), nz)
        mix = np.clip(t / rt60, 0, 1)
        ir = (1 - mix) * lp + mix * lp2
        ir = sosf(sos_high(120, 1, sr), ir)
        ir /= np.sqrt(np.sum(ir ** 2)) or 1.0
        pd = n_of(predelay, sr)
        if pd:
            ir = np.concatenate([np.zeros(pd), ir[:-pd]])
        for d, g in early:  # discrete reflections (delay s, gain)
            k = n_of(d, sr)
            if k < n:
                ir[k] += g * (1 if c == 0 else -1 if (k % 2) else 1)
        outs.append(ir)
    return np.stack(outs, axis=1) if channels > 1 else outs[0]


def reverb(x, ir, mix, circular=False):
    """Dry/wet with an impulse response. circular=True for loops (FFT convolution of the loop length)."""
    if x.ndim == 1 and ir.ndim == 2:
        x = np.stack([x] * ir.shape[1], axis=1)
    if circular:
        n = len(x)
        nf = n
        if ir.shape[0] > n:
            ir = ir[:n]
        X = np.fft.rfft(x, nf, axis=0)
        H = np.fft.rfft(ir, nf, axis=0)
        if X.ndim == 2 and H.ndim == 1:
            H = H[:, None]
        wet = np.fft.irfft(X * H, nf, axis=0)
    else:
        wet = signal.fftconvolve(x, ir if ir.ndim == x.ndim else ir[:, None], axes=0)[: len(x)] if x.ndim == 2 \
            else signal.fftconvolve(x, ir)[: len(x)]
    return (1 - mix) * x + mix * wet


# ------------------------------------------------------------------------------------------------------- dynamics
def peak_limit(x, ceiling_db=-1.0, lookahead_s=0.003, release_s=0.08, sr=SR):
    """Transparent-ish lookahead peak limiter on sample peaks (applied after loudness normalisation)."""
    ceil = db(ceiling_db)
    a = np.abs(x) if x.ndim == 1 else np.abs(x).max(axis=1)
    need = np.minimum(1.0, ceil / np.maximum(a, 1e-12))
    la = max(1, n_of(lookahead_s, sr))
    # running minimum over the lookahead window (so gain is down before the peak arrives)
    from scipy.ndimage import minimum_filter1d
    g = minimum_filter1d(need, size=2 * la + 1, mode="nearest")
    # release smoothing (one-pole, only upward)
    rel = math.exp(-1.0 / (release_s * sr))
    out = np.empty_like(g)
    cur = 1.0
    for i in range(len(g)):  # simple loop, clips are short
        v = g[i]
        cur = v if v < cur else v + (cur - v) * rel
        out[i] = cur
    # attack smoothing so the gain dip itself has no corner; never above what the peaks need
    if len(out) > 20:
        out = np.minimum(signal.filtfilt([1 - 0.995], [1, -0.995], out), out)
    y = x * (out if x.ndim == 1 else out[:, None])
    # safety: hard bound (never hit in practice after the limiter)
    return np.clip(y, -ceil, ceil)


def normalize_lufs(x, target, measure_fn, ceiling_db=-1.0, sr=SR, loop=False):
    """Scale to the target integrated loudness, then keep sample peaks under the ceiling: a lookahead limiter for
    one-shots; for loops a memoryless soft knee (a limiter's gain state would not wrap around the seam)."""
    cur = measure_fn(x, sr)
    y = x * db(target - cur)
    if loop:
        c = db(ceiling_db)
        for _ in range(4):
            if np.max(np.abs(y)) <= c:
                break
            k = 0.7 * c  # linear below the knee, tanh above it
            a = np.abs(y)
            over = a > k
            y = np.where(over, np.sign(y) * (k + (c - k) * np.tanh((a - k) / (c - k))), y)
            y = y * db(min(target - measure_fn(y, sr), 0.5))
        return np.clip(y, -c, c)
    if np.max(np.abs(y)) > db(ceiling_db):
        y = peak_limit(y, ceiling_db, sr=sr)
        # limiting lowers loudness a little: one correction pass (without pushing peaks over again)
        cur2 = measure_fn(y, sr)
        g = db(min(target - cur2, 1.0))
        y = y * g
        if np.max(np.abs(y)) > db(ceiling_db):
            y = peak_limit(y, ceiling_db, sr=sr)
    return y


def remove_dc(x, circular=False, sr=SR):
    sos = sos_high(18.0, 2, sr)
    return circ_sosfilt(sos, x) if circular else sosf(sos, x)


def soft_sat(x, drive=1.0):
    """Gentle tanh saturation (glues transients, never clips)."""
    return np.tanh(drive * x) / np.tanh(drive)
