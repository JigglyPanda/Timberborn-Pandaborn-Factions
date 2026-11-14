"""Source-filter voice synthesis for the panda calls (UI.Beavers.Pandaborn.Selected.*).

Additive glottal source: harmonics k*f0(t) with a -12 dB/octave glottal roll-off and +6 dB/octave lip radiation,
shaped at every instant by a cascade vocal-tract magnitude (formants F1..F4 with bandwidths) evaluated at each
harmonic's frequency, so the sound is band-limited by construction (no aliasing at high pitch) and formants can glide.
Jitter (pitch wobble), shimmer, a "bleat" quaver (pitch + amplitude modulation at 8-14 Hz, the goat-like call of a
giant panda) and pitch-synchronous breath noise make it less mechanical. Nothing here is recorded.
"""
import numpy as np

import synth as S


def _curve(points, n):
    """points: [(t_frac 0..1, value)] -> smooth curve of n samples (monotone cubic)."""
    from scipy.interpolate import PchipInterpolator
    ts = np.array([p[0] for p in points]) * (n - 1)
    vs = np.array([p[1] for p in points], dtype=float)
    return PchipInterpolator(ts, vs)(np.arange(n))


def tract_gain(f, formants):
    """Cascade vocal-tract magnitude at frequencies f (array) for formants [(F, B)] (each normalised to 1 at DC)."""
    g = np.ones_like(f)
    for F, B in formants:
        g *= F * F / np.sqrt((F * F - f * f) ** 2 + (B * f) ** 2)
    return g


def voice(dur, f0_pts, amp_pts, formant_pts, r, sr=S.SR, quaver_hz=0.0, quaver_depth=0.0, quaver_amp=0.0,
          jitter=0.006, shimmer=0.04, breath=0.08, tilt_db_oct=-6.0, sub=0.0):
    """
    f0_pts / amp_pts: [(t_frac, value)]; formant_pts: [(t_frac, [(F1,B1),(F2,B2),(F3,B3),(F4,B4)])].
    quaver: periodic pitch (depth, fraction) and amplitude (quaver_amp, 0..1) modulation at quaver_hz.
    sub: amount of a subharmonic (f0/2) for gruff calls.
    """
    n = S.n_of(dur, sr)
    t = S.tvec(n, sr)
    f0 = _curve(f0_pts, n)
    amp = np.clip(_curve(amp_pts, n), 0, None)
    # slow random wander + fast jitter
    wander = S.smooth_random(n, max(3, int(dur * 6)), r, -1, 1, circular=False)
    jit = S.sosf(S.sos_low(40.0, 1, sr), r.standard_normal(n))
    jit /= np.max(np.abs(jit)) or 1.0
    f0 = f0 * (1 + 0.012 * wander + jitter * jit)
    if quaver_hz:
        qrate = quaver_hz * (1 + 0.08 * wander)
        qph = 2 * np.pi * np.cumsum(qrate) / sr
        f0 = f0 * (1 + quaver_depth * np.sin(qph))
        amp = amp * (1 - quaver_amp * 0.5 * (1 - np.cos(qph)))
    shim = 1 + shimmer * S.sosf(S.sos_low(30.0, 1, sr), r.standard_normal(n)) / 0.2
    amp = amp * np.clip(shim, 0.5, 1.5)
    phase = 2 * np.pi * np.cumsum(f0) / sr

    # formant tracks per sample (interpolate each F and B)
    nf = len(formant_pts[0][1])
    Fs, Bs = [], []
    for i in range(nf):
        Fs.append(_curve([(p[0], p[1][i][0]) for p in formant_pts], n))
        Bs.append(_curve([(p[0], p[1][i][1]) for p in formant_pts], n))

    y = np.zeros(n)
    kmax = int(sr * 0.45 / max(np.min(f0), 40.0))
    kmax = min(kmax, 120)
    step = 64  # evaluate the spectral envelope every 64 samples, interpolate in between
    idx = np.arange(0, n, step)
    for k in range(1, kmax + 1):
        fk = k * f0
        valid = fk < sr * 0.45
        if not valid.any():
            break
        fk_s = fk[idx]
        g = np.ones_like(fk_s)
        for i in range(nf):
            F, B = Fs[i][idx], Bs[i][idx]
            g *= F * F / np.sqrt((F * F - fk_s ** 2) ** 2 + (B * fk_s) ** 2)
        g = np.interp(np.arange(n), idx, g)
        src = k ** (tilt_db_oct / 6.02)  # net source tilt (glottis -12 dB/oct + lips +6 dB/oct = -6)
        y += np.where(valid, src * g * np.sin(k * phase + r.uniform(0, 0.3)), 0.0)
    if sub:
        g = tract_gain(f0 / 2, [(Fs[i][0], Bs[i][0]) for i in range(nf)])
        y += sub * g * np.sin(0.5 * phase)
    y /= np.max(np.abs(y)) or 1.0
    # breath: noise through the mean formants, pulsed with the glottal cycle
    if breath:
        nz = r.standard_normal(n)
        F2m = float(np.mean(Fs[1])) if nf > 1 else 1200.0
        F3m = float(np.mean(Fs[2])) if nf > 2 else 2500.0
        nz = S.sosf(S.sos_band(max(250.0, F2m * 0.45), min(F3m * 1.4, sr * 0.45), 2, sr), nz)
        nz *= 0.6 + 0.4 * (0.5 + 0.5 * np.cos(phase))
        nz /= np.max(np.abs(nz)) or 1.0
        y = y + breath * nz
    return y * amp


def breath_noise(dur, r, lo, hi, amp_pts, flutter_hz=0.0, flutter_depth=0.0, sr=S.SR):
    """Unvoiced breath (huff, inhale, exhale); optional flutter (a soft snore)."""
    n = S.n_of(dur, sr)
    amp = np.clip(_curve(amp_pts, n), 0, None)
    nz = S.sosf(S.sos_band(lo, hi, 2, sr), r.standard_normal(n))
    nz /= np.max(np.abs(nz)) or 1.0
    if flutter_hz:
        t = S.tvec(n, sr)
        fl = 1 - flutter_depth * (0.5 + 0.5 * np.sin(2 * np.pi * flutter_hz * t + r.uniform(0, 6.28)))
        nz = nz * fl
    return nz * amp


# vowel-ish formant sets for a big animal (scaled down from human values: a longer vocal tract)
def formants(kind, scale=1.0):
    table = {
        "m": [(280, 80), (900, 200), (2200, 300), (3200, 400)],   # closed mouth hum
        "e": [(560, 90), (1500, 120), (2350, 170), (3300, 250)],
        "a": [(720, 100), (1150, 110), (2300, 170), (3250, 250)],
        "o": [(520, 90), (850, 100), (2250, 170), (3200, 250)],
        "u": [(360, 80), (720, 110), (2150, 180), (3150, 260)],
        "i": [(330, 70), (1900, 130), (2600, 180), (3400, 260)],
    }
    return [(F * scale, B * (0.8 + 0.2 * scale)) for F, B in table[kind]]
