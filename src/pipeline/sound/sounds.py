"""Every Pandaborn sound: one function per sound, a registry with its game id, kind, loudness target and the game slot
it is meant for. Synthesized from scratch (synth.py, voices.py); deterministic (seeds below).

Naming: the game finds clips by their *asset name* = the sound id, plus "_01", "_02"... for variants (AudioClipService:
name == id or name starts with id + "_"), and picks the mixer group from the id's first segment ("Environment", "UI").
So every id is "<Mixer>.<...>.Pandaborn<...>" or "<Mixer>.Pandaborn.<Name>" and never a prefix of a vanilla id.
"""
import math

import numpy as np

import synth as S
import voices as V

SR = S.SR


# ======================================================================================================= helpers
def wood_modes(f1, t60=0.12, hollow=0.0, n=5, inharm=(1.0, 2.32, 3.86, 5.41, 7.2), gains=(1.0, 0.55, 0.32, 0.18, 0.1)):
    modes = [(f1 * inharm[i], t60 / (1 + 0.7 * i), gains[i]) for i in range(min(n, len(inharm)))]
    if hollow:
        modes.append((f1 * 0.46, t60 * 1.3, hollow))  # the air in a hollow block / tube
    return modes


def knock(r, f1, t60=0.12, bright=0.6, hollow=0.0, dur=0.6, jitter=0.03):
    f1 = f1 * (1 + jitter * r.standard_normal())
    n = S.n_of(dur)
    exc = S.click(n, r, bright)
    y = S.resonator_bank(exc, wood_modes(f1, t60, hollow))
    return y / (np.max(np.abs(y)) or 1.0)


def bubble(r, f0, amp=1.0, rise=None):
    """A single bubble (van den Doel): a sine that rises in pitch as it decays."""
    d = 0.043 * f0 + 0.0014 * f0 ** 1.5
    dur = min(0.3, 6.0 / d)
    n = S.n_of(dur)
    t = S.tvec(n)
    xi = rise if rise is not None else r.uniform(0.06, 0.16)
    ph = 2 * np.pi * f0 * (t + 0.5 * xi * d * t * t)
    a = np.minimum(t / 0.0006, 1.0)
    return amp * a * np.exp(-d * t) * np.sin(ph)


def creak(r, dur, rate_lo, rate_hi, modes, swell=True, gain=1.0):
    """Stick-slip friction (a wooden axle, a rope under load): an irregular impulse train with a gliding rate driving
    wooden resonances."""
    n = S.n_of(dur)
    pts = max(3, int(dur * 5))
    rate = S.smooth_random(n, pts, r, rate_lo, rate_hi, circular=False)
    exc = np.zeros(n)
    pos = 0.0
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 0.8 if swell else np.ones(n)
    while True:
        i = int(pos)
        if i >= n:
            break
        exc[i] += env[i] * (0.4 + 0.6 * r.random()) * (1 if r.random() > 0.08 else 2.2)
        pos += SR / rate[i] * (1 + 0.18 * r.standard_normal())
        pos = max(pos, i + 8)
    exc = S.sosf(S.sos_low(3500, 1), exc)
    y = S.resonator_bank(exc, modes)
    y = S.sosf(S.sos_high(90, 2), y)
    return gain * y / (np.max(np.abs(y)) or 1.0)


AXLE_MODES = [(185, 0.14, 1.0), (312, 0.11, 0.8), (548, 0.08, 0.55), (873, 0.06, 0.35), (1390, 0.04, 0.2), (2050, 0.03, 0.1)]
ROPE_MODES = [(410, 0.06, 1.0), (760, 0.05, 0.7), (1240, 0.04, 0.45), (1980, 0.03, 0.2)]


def drip(r, amp=1.0):
    """A drop into water: a tiny impact and a high bubble."""
    f0 = r.uniform(1100, 2600)
    b = bubble(r, f0, 1.0, rise=r.uniform(0.15, 0.35))
    imp = S.noise_burst(len(b), r, 0.006, 800, 6000) * 0.25
    return amp * (b + imp)


def splash(r, dur=0.18, lo=250, hi=3500, bubbles=6, amp=1.0):
    n = S.n_of(dur + 0.25)
    y = S.noise_burst(n, r, dur, lo, hi, attack=0.004)
    y /= np.max(np.abs(y)) or 1.0
    for _ in range(bubbles):
        b = bubble(r, r.uniform(500, 1800), r.uniform(0.2, 0.6))
        i = S.n_of(r.uniform(0.0, dur * 1.2))
        k = min(len(b), n - i)
        y[i:i + k] += b[:k]
    return amp * y / (np.max(np.abs(y)) or 1.0)


def pour(r, dur, f_lo=600, f_hi=1500, density=90, amp=1.0):
    """A thin stream into a vessel: bubbles whose pitch climbs as the vessel fills, over a filtered rush."""
    n = S.n_of(dur)
    y = np.zeros(n)
    count = int(density * dur)
    for _ in range(count):
        at = r.uniform(0, dur)
        frac = at / dur
        f0 = (f_lo + (f_hi - f_lo) * frac) * np.exp(0.25 * r.standard_normal())
        b = bubble(r, f0, r.uniform(0.2, 1.0))
        i = S.n_of(at)
        k = min(len(b), n - i)
        y[i:i + k] += b[:k]
    rush = S.sosf(S.sos_band(400, 3000), r.standard_normal(n)) * 0.12
    y = y / (np.max(np.abs(y)) or 1.0) + rush
    y *= np.sin(np.pi * np.clip(np.linspace(0, 1, n) * 1.0, 0, 1)) ** 0.3
    return amp * S.fade(y, 0.02, 0.06)


def bell_partials(prime, strike=1.0, r=None, detune=0.0):
    """A small bronze bell. Ratios to the prime: hum 0.5, prime 1, tierce 1.19 (minor third), quint 1.5, nominal 2,
    upper partials. A soft (wooden) striker keeps the upper partials down; long hum and prime make it warm."""
    p = prime * (1 + detune)
    soft = 0.55 + 0.45 * strike
    table = [  # ratio, amp, t60, doublet beat (Hz)
        (0.5, 0.60, 9.0, 0.35), (1.0, 0.85, 6.5, 0.9), (1.19, 0.55, 5.0, 1.3), (1.5, 0.22, 3.6, 0.0),
        (2.0, 0.62, 4.2, 1.7), (2.51, 0.28, 2.6, 0.0), (2.68, 0.2, 2.3, 2.1), (3.01, 0.15, 1.8, 0.0),
        (4.17, 0.09, 1.1, 0.0), (5.43, 0.05, 0.7, 0.0), (6.8, 0.025, 0.45, 0.0),
    ]
    out = []
    for ratio, a, t60, beat in table:
        bright = soft ** (2.2 * max(ratio - 1.0, 0))  # soft strikes darken the upper partials
        out.append((p * ratio, a * bright, t60, beat))
    return out


def bell_strike(r, prime, strike=1.0, dur=7.0, detune=0.0):
    y = S.modal(dur, bell_partials(prime, strike, r, detune), r)
    # the strike itself: a short wooden "tock" of the striker on bronze (soft, filtered)
    n = len(y)
    tock = S.noise_burst(n, r, 0.012, 300, 2600, attack=0.0008) * 0.35 * strike
    k = knock(r, 820, t60=0.05, bright=0.3, dur=0.2)
    tock[: len(k)] += 0.12 * strike * k
    y = y / (np.max(np.abs(y)) or 1.0) + tock
    a = np.minimum(S.tvec(n) / 0.0015, 1.0)
    return y * a


def membrane(r, f0, dur=1.2, t60=0.6, drop=0.18, stick=0.25):
    """A hide drum: circular-membrane modes with a small pitch drop after the hit."""
    n = S.n_of(dur)
    t = S.tvec(n)
    ratios = [1.0, 1.59, 2.14, 2.30, 2.65, 2.92]
    amps = [1.0, 0.45, 0.3, 0.22, 0.12, 0.08]
    y = np.zeros(n)
    bend = 1 + drop * np.exp(-t / 0.035)
    for i, (k, a) in enumerate(zip(ratios, amps)):
        f = f0 * k * bend
        ph = 2 * np.pi * np.cumsum(f) / SR
        y += a * np.exp(-6.9 * t / (t60 / (1 + 0.6 * i))) * np.sin(ph + r.uniform(0, 6.28))
    y += S.noise_burst(n, r, 0.03, 120, 1800) * stick
    y *= np.minimum(t / 0.0012, 1.0)  # no step at the start (random phases)
    return y / (np.max(np.abs(y)) or 1.0)


def ceramic(r, f1, t60=0.25, dur=0.8, bright=0.5, ratios=(1.0, 2.27, 3.82, 5.6), amps=(1.0, 0.5, 0.28, 0.12)):
    n = S.n_of(dur)
    exc = S.click(n, r, bright)
    modes = [(f1 * k * (1 + 0.004 * r.standard_normal()), t60 / (1 + 0.5 * i), a) for i, (k, a) in enumerate(zip(ratios, amps))]
    y = S.resonator_bank(exc, modes)
    return y / (np.max(np.abs(y)) or 1.0)


def grains(r, dur, rate, lo, hi, grain_ms=(0.2, 1.2), env=None):
    """Dense tiny crackles (dry leaves, paper): short noise grains at a (time-varying) rate."""
    n = S.n_of(dur)
    y = np.zeros(n)
    env = np.ones(n) if env is None else env
    count = int(rate * dur)
    for _ in range(count):
        i = int(r.uniform(0, n))
        if r.random() > env[i]:
            continue
        g = S.n_of(r.uniform(*grain_ms) / 1000.0)
        k = min(g, n - i)
        y[i:i + k] += r.standard_normal(k) * np.exp(-np.linspace(0, 5, k)) * r.lognormal(0, 0.6)
    y = S.sosf(S.sos_band(lo, hi, 2), y)
    return y / (np.max(np.abs(y)) or 1.0)


def finish_loop(y, sr=SR):
    """DC-free and seamless: high-pass circularly."""
    return S.remove_dc(y, circular=True, sr=sr)


# ============================================================================================ signals of the day
def shift_bell_end(v):
    """One soft strike of the Village Hall bell: the day's work ends (and the Ringtails' night begins)."""
    r = S.rng(1100 + v)
    strike = [0.86, 1.0, 0.93][v % 3]
    detune = [0.0, -0.0025, 0.002][v % 3]
    y = bell_strike(r, 392.0, strike, dur=7.5, detune=detune)
    ir = S.reverb_ir(3.0, 1.8, r, damp_hz=3500, predelay=0.012, early=[(0.043, 0.25), (0.091, 0.12)])
    y = S.reverb(y, ir, 0.18)
    return S.fade(y, 0.0, 1.2)


def shift_bell_dawn(v):
    """Dawn: the same bell, two lighter strikes (the second softer) - the day begins."""
    r = S.rng(1200 + v)
    gap = [1.05, 1.2][v % 2]
    tl = S.Timeline(8.5)
    tl.add(bell_strike(r, 392.0, 0.62, dur=7.0, detune=0.001 * v), 0.0, 1.0, wrap=False)
    tl.add(bell_strike(r, 392.0, 0.48, dur=7.0, detune=-0.001), gap, 0.62, wrap=False)
    y = tl.buf
    ir = S.reverb_ir(3.0, 1.8, r, damp_hz=3500, predelay=0.012, early=[(0.043, 0.25), (0.091, 0.12)])
    y = S.reverb(y, ir, 0.18)
    return S.fade(y, 0.0, 1.4)


def clapper_tok(r, base=1.0, gain=1.0):
    """The night watch's clapper: two hardwood blocks struck together - two close knocks, a hollow body."""
    a = knock(r, 1180 * base, t60=0.11, bright=0.85, hollow=0.5, dur=0.35)
    b = knock(r, 1430 * base, t60=0.09, bright=0.8, hollow=0.3, dur=0.35)
    off = S.n_of(r.uniform(0.0004, 0.0013))
    y = a.copy()
    y[off:] += 0.8 * b[: len(b) - off]
    return gain * y / (np.max(np.abs(y)) or 1.0)


def night_clapper(v):
    """Ringtails' "night shift begins": tok ... tok-tok (v0) or tok-tok ... tok (v1). Dry, quiet."""
    r = S.rng(1300 + v)
    pattern = [[(0.0, 1.0), (0.62, 0.85), (0.84, 0.95)], [(0.0, 0.95), (0.21, 0.8), (0.86, 1.0)]][v % 2]
    tl = S.Timeline(1.9)
    for at, g in pattern:
        tl.add(clapper_tok(r, 1.0 + 0.01 * r.standard_normal(), g), at + 0.01, 1.0, wrap=False)
    y = tl.buf
    ir = S.reverb_ir(1.2, 0.45, r, damp_hz=5000, early=[(0.085, 0.35), (0.16, 0.12)])
    return S.fade(S.reverb(y, ir, 0.12), 0.0, 0.25)


def village_hall_select(v):
    """Selecting the Village Hall: the bell, touched lightly (short)."""
    r = S.rng(1400 + v)
    y = bell_strike(r, 392.0, 0.35, dur=2.4)
    y *= S.exp_env(len(y), 2.6)
    return S.fade(y, 0.0, 0.5)


# ================================================================================================ water
def flume_water(v, seconds=16.0):
    """A thin stream running down an open bamboo trough: small bubbles over a soft rush, with the hollow bamboo body.
    Seamless loop; bubble density drifts (whole cycles per loop), no short period."""
    r = S.rng(2100 + v)
    tl = S.Timeline(seconds)
    n = tl.n
    dens = 0.65 + 0.35 * S.smooth_random(n, 9, r, 0, 1, circular=True)
    count = int(46 * seconds)
    for _ in range(count):
        at = r.uniform(0, seconds)
        if r.random() > dens[int(at * SR) % n]:
            continue
        f0 = math.exp(r.uniform(math.log(450), math.log(2400)))
        tl.add(bubble(r, f0, r.lognormal(-0.3, 0.5)), at)
    y = tl.buf / (np.max(np.abs(tl.buf)) or 1.0)
    bed = S.circ_noise(n, r, S.shape_band(350, 1800, 9, 14))
    bed *= 0.75 + 0.25 * S.smooth_random(n, 11, r, 0, 1, circular=True)
    y = y + 0.09 * bed
    # hollow bamboo body: gentle resonant lifts, then roll the top off (soft, never hissy)
    y = S.eq(y, [(340, 4.0, 3.0), (860, 3.0, 3.5), (5200, -6.0, 0.7)], circular=True)
    y = S.circ_sosfilt(S.sos_low(6500, 2), y)
    return finish_loop(y)


def bamboo_tok(v):
    """The hollow knock of a bamboo pipe tipping onto stone as a flume fills (used sparingly)."""
    r = S.rng(2200 + v)
    pitch = [1.0, 0.94, 1.07][v % 3]
    n = S.n_of(1.2)
    exc = S.click(n, r, 0.7)
    f_air = 300 * pitch  # air column of a ~28 cm closed tube
    modes = [(f_air, 0.22, 1.0), (f_air * 3.02, 0.12, 0.35), (f_air * 5.05, 0.07, 0.12),
             (1150 * pitch, 0.07, 0.55), (2480 * pitch, 0.04, 0.25)]
    y = S.resonator_bank(exc, modes)
    y /= np.max(np.abs(y)) or 1.0
    # a little water spills after the knock
    tail = np.zeros(n)
    for i in range(5):
        b = drip(r, r.uniform(0.05, 0.12))
        at = S.n_of(0.09 + 0.05 * i + r.uniform(0, 0.03))
        k = min(len(b), n - at)
        tail[at:at + k] += b[:k]
    y = y + tail
    ir = S.reverb_ir(1.0, 0.5, r, damp_hz=4500, early=[(0.06, 0.2)])
    return S.fade(S.reverb(y, ir, 0.15), 0.0, 0.3)


def scoop_wheel(v, rev=6.0, revs=3):
    """A bamboo scoop wheel in a current: a slow wooden creak once a turn, buckets tipping into the trough, drips."""
    r = S.rng(2300 + v)
    seconds = rev * revs
    tl = S.Timeline(seconds)
    n = tl.n
    for k in range(revs):
        base = k * rev
        tl.add(creak(r, r.uniform(0.7, 1.1), 35, 85, AXLE_MODES), base + 0.4 + r.uniform(-0.1, 0.1), 0.55)
        if r.random() < 0.7:
            tl.add(creak(r, r.uniform(0.4, 0.6), 60, 110, AXLE_MODES), base + rev * 0.55 + r.uniform(-0.2, 0.2), 0.3)
        for b in range(8):  # eight buckets tip into the trough each turn
            at = base + rev * (b / 8.0) + r.uniform(-0.05, 0.05)
            tl.add(pour(r, r.uniform(0.28, 0.4), 700, 1300, density=70), at, r.uniform(0.25, 0.4))
        tl.add(knock(r, 260, t60=0.1, bright=0.35, dur=0.4), base + rev * 0.8, 0.18)
    for _ in range(int(5 * seconds)):  # drips falling back into the stream
        tl.add(drip(r), r.uniform(0, seconds), r.uniform(0.05, 0.22))
    y = tl.buf
    stream = S.circ_noise(n, r, S.shape_band(180, 1400, 8, 14))
    stream *= 0.8 + 0.2 * S.lfo(n, revs * 2, 0.3)
    y = y + 0.12 * stream
    y = S.circ_sosfilt(S.sos_low(7000, 2), y)
    return finish_loop(y)


def bamboo_water_wheel(v, rev=4.5, revs=4):
    """A bigger bamboo power wheel: paddles slapping the current in a steady churn, a deeper axle creak, the stream."""
    r = S.rng(2400 + v)
    seconds = rev * revs
    tl = S.Timeline(seconds)
    n = tl.n
    paddles = 12
    deep_axle = [(f * 0.72, t * 1.2, g) for f, t, g in AXLE_MODES]
    for k in range(revs):
        base = k * rev
        for p in range(paddles):
            at = base + rev * p / paddles + r.uniform(-0.02, 0.02)
            tl.add(splash(r, r.uniform(0.12, 0.2), 200, 2600, bubbles=4), at, r.uniform(0.25, 0.45))
        tl.add(creak(r, r.uniform(0.8, 1.2), 30, 70, deep_axle), base + r.uniform(0.2, 0.6), 0.5)
        tl.add(creak(r, r.uniform(0.5, 0.8), 40, 80, deep_axle), base + rev * 0.5 + r.uniform(-0.2, 0.2), 0.3)
    for _ in range(int(4 * seconds)):
        tl.add(drip(r), r.uniform(0, seconds), r.uniform(0.04, 0.15))
    y = tl.buf / (np.max(np.abs(tl.buf)) or 1.0)
    stream = S.circ_noise(n, r, S.shape_band(120, 1100, 8, 14))
    stream *= 0.75 + 0.25 * S.lfo(n, revs, 1.1)
    y = y + 0.3 * stream
    y = S.circ_sosfilt(S.sos_low(6500, 2), y)
    return finish_loop(y)


# ================================================================================================ wind
def kite_windmill(v, rev=3.2, revs=5):
    """Cloth sails on a bamboo frame: a soft whoosh as each of four sails passes, cloth flutter that rises with the
    gusts, now and then a rope creak and the wooden hub's tick."""
    r = S.rng(2500 + v)
    seconds = rev * revs
    tl = S.Timeline(seconds)
    n = tl.n
    t = S.tvec(n)
    gust = 0.55 + 0.45 * (0.5 + 0.5 * S.lfo(n, 1, -1.2))  # one gust per loop
    gust *= 0.85 + 0.15 * S.smooth_random(n, 7, r, 0, 1, circular=True)
    # sail passes: band noise swelling 4x per revolution
    sails = 4
    passes = 0.5 + 0.5 * np.cos(2 * np.pi * sails * revs * t / seconds)
    passes = passes ** 3
    whoosh = S.circ_noise(n, r, S.shape_band(250, 1100, 10, 16)) * (0.25 + 0.75 * passes)
    # cloth flutter: amplitude modulated noise at 7-13 Hz, irregular, depth with the gusts
    fl_rate = 9.0
    cyc = round(fl_rate * seconds)
    flut = 0.5 + 0.5 * S.lfo(n, cyc, 0.0) * (0.6 + 0.4 * S.lfo(n, round(cyc * 0.37), 1.0))
    cloth = S.circ_noise(n, r, S.shape_band(180, 1600, 10, 14)) * (flut ** 4) * gust
    y = 0.6 * whoosh * gust + 0.7 * cloth
    y = y / (np.max(np.abs(y)) or 1.0)
    for k in range(revs):
        tl.add(knock(r, 520, t60=0.06, bright=0.4, dur=0.25), k * rev + 0.13, 0.06)
    for _ in range(3):
        tl.add(creak(r, r.uniform(0.35, 0.6), 90, 160, ROPE_MODES), r.uniform(0, seconds), r.uniform(0.18, 0.28))
    y = y + tl.buf
    wind = S.circ_noise(n, r, S.shape_band(60, 400, 6, 18)) * gust
    y = y + 0.08 * wind
    y = S.circ_sosfilt(S.sos_low(5000, 2), y)
    return finish_loop(y)


# ============================================================================================ workshops
def steamer(v, seconds=14.0):
    """Bamboo steamer baskets over a pot: a low simmer, breathing steam through the lid, a lid knock now and then."""
    r = S.rng(3100 + v)
    tl = S.Timeline(seconds)
    n = tl.n
    for _ in range(int(55 * seconds)):  # big slow bubbles in the pot
        tl.add(bubble(r, math.exp(r.uniform(math.log(160), math.log(650))), r.lognormal(-0.4, 0.5)), r.uniform(0, seconds))
    sim = tl.buf / (np.max(np.abs(tl.buf)) or 1.0)
    breath = 0.5 + 0.5 * S.lfo(n, 4, 0.0) * 0.6 + 0.2 * S.smooth_random(n, 9, r, -1, 1)
    steam = S.circ_noise(n, r, S.shape_band(1000, 3200, 10, 20)) * np.clip(breath, 0.1, 1.2)
    tl2 = S.Timeline(seconds)
    for at in (r.uniform(2, 4), r.uniform(8.5, 10.5)):
        for j in range(r.integers(2, 4)):  # the lid lifts and settles: two or three quick bamboo taps
            tl2.add(knock(r, 690, t60=0.08, bright=0.5, hollow=0.4, dur=0.3), at + j * r.uniform(0.07, 0.12), 0.35 * (0.85 ** j))
    y = 0.75 * sim + 0.09 * steam + tl2.buf
    y = S.circ_sosfilt(S.sos_low(6000, 2), y)
    return finish_loop(y)


def tea_roastery(v, seconds=12.8):
    """Tea leaves tumbled in a hot wok by hand: a dry rustle with each toss (every 1.6 s), the faint scrape of the
    wok, a low fire underneath."""
    r = S.rng(3200 + v)
    tl = S.Timeline(seconds)
    n = tl.n
    tosses = int(round(seconds / 1.6))
    gaps = r.uniform(0.8, 1.2, tosses)          # a hand, not a machine: uneven gaps that still fill the loop exactly
    starts = np.concatenate([[0.0], np.cumsum(gaps / gaps.sum() * seconds)[:-1]])
    for at0 in starts:
        d = r.uniform(0.7, 1.0)
        m = S.n_of(d)
        env = np.sin(np.pi * np.linspace(0, 1, m)) ** 1.5
        tl.add(grains(r, d, 2600, 900, 5200, env=env) * env, at0, r.uniform(0.7, 1.0))
        scrape = S.noise_burst(S.n_of(0.5), r, 0.4, 700, 2600, attack=0.05)
        scrape = S.eq(scrape, [(1130, 8, 12), (2290, 6, 12)])
        tl.add(scrape / (np.max(np.abs(scrape)) or 1.0), at0 + 0.45, 0.12)
    y = tl.buf
    fire = S.circ_noise(n, r, S.shape_brown(40, 500)) * (0.8 + 0.2 * S.smooth_random(n, 8, r, 0, 1))
    y = y + 0.05 * fire
    y = S.circ_sosfilt(S.sos_low(5500, 2), y)
    return finish_loop(y)


def pickle_yard(v, seconds=16.0):
    """Stoneware jars: a heavy glazed lid set down and lifted, brine sloshing as a jar is stirred."""
    r = S.rng(3300 + v)
    tl = S.Timeline(seconds)
    n = tl.n
    for at in (1.2, 6.9, 11.8):
        at += r.uniform(-0.3, 0.3)
        tl.add(ceramic(r, r.uniform(560, 700), t60=0.22, bright=0.35, dur=0.6), at, 0.55)
        tl.add(ceramic(r, r.uniform(560, 700), t60=0.15, bright=0.25, dur=0.5), at + r.uniform(0.09, 0.16), 0.25)
    for at in (3.0, 9.2, 14.0):
        d = r.uniform(1.4, 2.0)
        m = S.n_of(d)
        slosh = S.sosf(S.sos_band(140, 900), r.standard_normal(m))
        sw = 0.5 + 0.5 * np.sin(2 * np.pi * r.uniform(1.6, 2.2) * S.tvec(m))
        slosh = slosh * sw ** 2 * np.sin(np.pi * np.linspace(0, 1, m))
        slosh /= np.max(np.abs(slosh)) or 1.0
        tl.add(slosh, at, 0.35)
        for _ in range(int(14 * d)):
            tl.add(bubble(r, r.uniform(250, 900), r.uniform(0.1, 0.3)), at + r.uniform(0, d))
    y = tl.buf
    room = S.circ_noise(n, r, S.shape_pink(80, 3000)) * 0.02
    y = y + room
    ir = S.reverb_ir(1.0, 0.5, r, damp_hz=3500)
    y = S.reverb(y, ir, 0.15, circular=True)
    return finish_loop(y)


def lantern_workshop(v, seconds=16.0):
    """Paper and bamboo: paper smoothed over a frame (soft crinkle), thin bamboo strips flexed and tapped, a brush."""
    r = S.rng(3400 + v)
    tl = S.Timeline(seconds)
    n = tl.n
    for at in np.arange(0.5, seconds, 2.7):
        d = r.uniform(0.5, 1.1)
        m = S.n_of(d)
        env = np.sin(np.pi * np.linspace(0, 1, m)) ** 2
        tl.add(grains(r, d, 900, 700, 4200, grain_ms=(0.4, 2.5), env=env) * env, at + r.uniform(-0.2, 0.2), 0.55)
    for _ in range(9):
        tl.add(knock(r, r.uniform(900, 1300), t60=0.05, bright=0.7, hollow=0.2, dur=0.2), r.uniform(0, seconds), r.uniform(0.15, 0.3))
    for _ in range(3):
        tl.add(creak(r, r.uniform(0.25, 0.4), 140, 260, ROPE_MODES), r.uniform(0, seconds), 0.14)
    for at in (4.1, 12.2):  # a brush stroke of paste
        m = S.n_of(0.6)
        sw = S.sosf(S.sos_band(500, 2800), r.standard_normal(m)) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2
        tl.add(sw / (np.max(np.abs(sw)) or 1.0), at, 0.18)
    y = tl.buf + S.circ_noise(n, r, S.shape_pink(80, 2500)) * 0.015
    y = S.circ_sosfilt(S.sos_low(5500, 2), y)
    return finish_loop(y)


def smoke_kiln(v, seconds=15.0):
    """A low wood fire under bamboo poles: a soft roar that breathes, sparse crackles, the odd bigger pop."""
    r = S.rng(3500 + v)
    n = S.n_of(seconds)
    roar = S.circ_noise(n, r, S.shape_brown(70, 650))
    roar *= 0.7 + 0.3 * S.smooth_random(n, 10, r, 0, 1)
    tl = S.Timeline(seconds)
    for _ in range(int(14 * seconds)):
        m = S.n_of(0.02)
        p = r.standard_normal(m) * np.exp(-np.linspace(0, 9, m))
        f = r.uniform(900, 3800)
        p = S.resonator(p, f, 0.01)
        tl.add(p / (np.max(np.abs(p)) or 1.0), r.uniform(0, seconds), r.lognormal(-1.6, 0.6))
    for _ in range(4):
        m = S.n_of(0.12)
        p = S.noise_burst(m, r, 0.06, 150, 2500, attack=0.0005)
        tl.add(p / (np.max(np.abs(p)) or 1.0), r.uniform(0, seconds), 0.5)
    y = 0.22 * roar + tl.buf
    y = S.circ_sosfilt(S.sos_low(5000, 2), y)
    return finish_loop(y)


def trip_hammer(v, cycle=3.0, cycles=4):
    """A water-driven trip hammer: water trickles into the lever's spoon, the spoon tips with a splash, the heavy
    wooden head drops into the mortar with a deep thump, the lever creaks back."""
    r = S.rng(3600 + v)
    seconds = cycle * cycles
    tl = S.Timeline(seconds)
    n = tl.n
    for k in range(cycles):
        base = k * cycle
        tl.add(pour(r, cycle * 0.55, 500, 1100, density=45), base + 0.15, 0.22)          # spoon filling
        tl.add(splash(r, 0.22, 200, 2200, bubbles=8), base + cycle * 0.72, 0.45)        # spoon tips
        tl.add(creak(r, 0.35, 45, 80, AXLE_MODES), base + cycle * 0.74, 0.25)           # lever swings
        m = S.n_of(1.0)                                                                 # head hits the mortar
        th = membrane(r, 62, dur=1.0, t60=0.35, drop=0.25, stick=0.0)
        wood = knock(r, 340, t60=0.12, bright=0.5, hollow=0.6, dur=1.0)
        crunch = grains(r, 0.12, 4000, 300, 2500)
        hit = th + 0.6 * wood
        hit[: len(crunch)] += 0.25 * crunch
        tl.add(hit / (np.max(np.abs(hit)) or 1.0), base + cycle * 0.92 + r.uniform(-0.02, 0.02), 1.0)
    y = tl.buf
    y = y + 0.06 * S.circ_noise(n, r, S.shape_band(150, 1200, 8, 14))
    ir = S.reverb_ir(1.2, 0.6, r, damp_hz=3000)
    y = S.reverb(y, ir, 0.12, circular=True)
    return finish_loop(y)


def simmer(v, seconds=15.0):
    """A broth pot on a low fire (Kitchen, Hot Pot Hall): dense low bubbling, a ladle against the pot now and then."""
    r = S.rng(3700 + v)
    tl = S.Timeline(seconds)
    n = tl.n
    dens = 0.6 + 0.4 * S.smooth_random(n, 8, r, 0, 1)
    for _ in range(int(120 * seconds)):
        at = r.uniform(0, seconds)
        if r.random() > dens[int(at * SR) % n]:
            continue
        tl.add(bubble(r, math.exp(r.uniform(math.log(180), math.log(900))), r.lognormal(-0.5, 0.5)), at)
    y = tl.buf / (np.max(np.abs(tl.buf)) or 1.0)
    tl2 = S.Timeline(seconds)
    for at in (3.3, 10.6):
        tl2.add(ceramic(r, 880, t60=0.3, bright=0.3, dur=0.7, ratios=(1.0, 2.71, 5.1), amps=(1.0, 0.4, 0.15)), at, 0.18)
    fire = S.circ_noise(n, r, S.shape_brown(40, 400)) * 0.12
    y = y + tl2.buf + fire
    y = S.eq(y, [(320, 3, 1.5)], circular=True)
    y = S.circ_sosfilt(S.sos_low(5000, 2), y)
    return finish_loop(y)


# ============================================================================================== festival
def festival_drum(v, bpm=100.0, bars=4):
    """A soft barrel drum and a wooden rim click: a gentle festival walking rhythm (seamless loop)."""
    r = S.rng(4100 + v)
    beat = 60.0 / bpm
    seconds = bars * 4 * beat
    tl = S.Timeline(seconds)
    n = tl.n
    # per bar (16ths): B . . k | B . k . | . . B . | k . k .   (B = drum, k = rim)
    bar = ["B", "", "", "k", "B", "", "k", "", "", "", "B", "", "k", "", "k", ""]
    for b in range(bars):
        for i, s in enumerate(bar):
            at = (b * 16 + i) * beat / 4 + beat / 2 + r.uniform(-0.006, 0.006)
            if s == "B":
                acc = 1.0 if i == 0 else 0.72
                tl.add(membrane(r, 118 * (1 + 0.01 * r.standard_normal()), 1.2, 0.7, 0.15, 0.3), at, acc)
            elif s == "k":
                tl.add(knock(r, 1650, t60=0.04, bright=0.8, dur=0.15), at, 0.45)
    y = tl.buf
    ir = S.reverb_ir(2.0, 1.1, r, damp_hz=3000, predelay=0.01)
    y = S.reverb(y, ir, 0.2, circular=True)
    return finish_loop(y)


def firecrackers(v):
    """A short string of small firecrackers, heard from a little way off: soft pops, not startling."""
    r = S.rng(4200 + v)
    dur = 2.6
    tl = S.Timeline(dur + 1.0)
    t = 0.05
    while t < dur:
        m = S.n_of(0.03)
        pop = r.standard_normal(m) * np.exp(-np.linspace(0, 10, m))
        pop = S.sosf(S.sos_band(400, 5500), pop)
        thump = membrane(r, r.uniform(110, 160), 0.08, 0.05, 0.0, 0.0) * 0.4
        pop = pop / (np.max(np.abs(pop)) or 1.0)
        pop = np.pad(pop, (0, max(0, len(thump) - len(pop))))
        pop[: len(thump)] += thump
        intensity = math.sin(math.pi * min(t / dur, 1.0)) ** 0.5
        tl.add(pop, t, r.uniform(0.35, 1.0) * (0.5 + 0.5 * intensity), wrap=False)
        t += r.exponential(0.045) + 0.012
    y = S.sosf(S.sos_low(4500, 2), tl.buf)
    ir = S.reverb_ir(2.5, 1.4, r, damp_hz=2500, predelay=0.03)
    y = S.reverb(y, ir, 0.3)
    return S.fade(y, 0.0, 0.5)


def lantern_rise(v):
    """One paper sky lantern lifting off: a soft airy rise and a faint warm shimmer (replaces a rocket's trail)."""
    r = S.rng(4300 + v)
    dur = 2.2
    n = S.n_of(dur)
    t = S.tvec(n)
    nz = r.standard_normal(n)
    y = np.zeros(n)
    # sweep a band upwards in short blocks (time-varying band-pass by overlap-add)
    blk = 1024
    win = np.hanning(blk * 2)
    for s in range(0, n - blk * 2, blk):
        c = 400 * (1 + 2.2 * (s / n) ** 1.3)
        seg = S.sosf(S.sos_band(c * 0.6, c * 1.6, 2), nz[s:s + blk * 2]) * win
        y[s:s + blk * 2] += seg
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.6
    y = y / (np.max(np.abs(y)) or 1.0) * env
    shimmer = S.modal(dur, [(1176 * (1 + 0.02 * v), 0.08, 1.4), (1568, 0.05, 1.0), (2352, 0.025, 0.7)], r)
    y = y + shimmer * np.clip(t / 0.4, 0, 1)
    return S.fade(y, 0.05, 0.4)


# =========================================================================================== the wonder
def sky_lantern_launch(v=0):
    """The Sky Lantern wonder takes off: a deep drum, a rising airy swell lifting a warm chord, the bell's shimmer at
    the top, a second drum as it clears the cliffs. Stereo, about 7.5 s."""
    r = S.rng(5100 + v)
    dur = 7.6
    n = S.n_of(dur)
    t = S.tvec(n)
    out = np.zeros((n, 2))
    # airy swell (decorrelated L/R), band sweeping up 280 Hz -> 2.4 kHz
    for ch in range(2):
        nz = r.standard_normal(n)
        y = np.zeros(n)
        blk = 1024
        win = np.hanning(blk * 2)
        for s in range(0, n - blk * 2, blk):
            frac = s / n
            c = 280 * (2.4e3 / 280) ** min(frac / 0.75, 1.0)
            y[s:s + blk * 2] += S.sosf(S.sos_band(c * 0.55, min(c * 1.8, 20000), 2), nz[s:s + blk * 2]) * win
        y /= np.max(np.abs(y)) or 1.0
        out[:, ch] += 0.5 * y
    swell = (0.15 + 0.85 * np.clip(t / 4.6, 0, 1) ** 1.5) * np.exp(-np.maximum(t - 4.8, 0) / 1.2) * np.clip(t / 0.3, 0, 1)
    out *= swell[:, None]
    # warm rising chord (pentatonic: G3 D4 G4 B4 -> up a fourth), soft sine organ with slow attack
    chord = [196.0, 293.66, 392.0, 493.88]
    glide = 1 + 0.335 * np.clip((t - 1.2) / 3.6, 0, 1) ** 2   # up a fourth while rising
    pad = np.zeros(n)
    for i, f in enumerate(chord):
        ph = 2 * np.pi * np.cumsum(f * glide * (1 + 0.002 * np.sin(2 * np.pi * (0.3 + 0.1 * i) * t))) / SR
        pad += (0.9 ** i) * (np.sin(ph) + 0.2 * np.sin(2 * ph))
    pad /= np.max(np.abs(pad)) or 1.0
    pad_env = np.clip((t - 0.25) / 2.0, 0, 1) ** 1.2 * np.exp(-np.maximum(t - 5.0, 0) / 1.1)
    out[:, 0] += 0.32 * pad * pad_env
    out[:, 1] += 0.32 * np.roll(pad, S.n_of(0.011)) * pad_env
    # two deep drums
    for at, g in ((0.08, 0.55), (4.55, 1.0)):
        d = membrane(r, 58, 2.2, 1.4, 0.2, 0.15)
        i = S.n_of(at)
        k = min(len(d), n - i)
        out[i:i + k, 0] += 0.75 * g * d[:k]
        out[i:i + k, 1] += 0.75 * g * d[:k]
    # the bell's shimmer at the top (same bronze as the Village Hall bell, high and quiet)
    sh = bell_strike(r, 784.0, 0.4, dur=3.0)
    i = S.n_of(4.5)
    k = min(len(sh), n - i)
    out[i:i + k, 0] += 0.16 * sh[:k]
    out[i:i + k, 1] += 0.16 * np.roll(sh, 240)[:k]
    ir = S.reverb_ir(4.0, 2.4, r, damp_hz=4000, predelay=0.02, channels=2)
    out = S.reverb(out, ir, 0.25)
    return S.fade(out, 0.0, 1.2)


# ========================================================================================= attractions
def ks_pluck(r, f, dur, bright=0.7, decay=0.996):
    """Karplus-Strong plucked string (a pipa-like plucked phrase)."""
    n = S.n_of(dur)
    N = max(2, int(round(SR / f - 0.5)))
    exc = np.zeros(n)
    burst = r.standard_normal(N)
    burst = S.sosf(S.sos_low(1500 + 6000 * bright, 1), burst)
    exc[:N] = burst
    a = np.zeros(N + 2)
    a[0] = 1.0
    a[N] = -decay * 0.5
    a[N + 1] = -decay * 0.5
    from scipy import signal as sg
    y = sg.lfilter([1.0], a, exc)
    y *= np.minimum(1.0, S.tvec(n) / 0.002)
    return y / (np.max(np.abs(y)) or 1.0)


def opera_stage(v, seconds=24.0):
    """Very quiet: a plucked-string phrase on a pentatonic scale with tremolo on the long notes, a wooden clapper on
    the downbeats (the face-changing opera heard from the street)."""
    r = S.rng(4400 + v)
    tl = S.Timeline(seconds)
    G = 196.0
    scale = [1, 9 / 8, 5 / 4, 3 / 2, 5 / 3, 2, 9 / 4, 5 / 2, 3]  # G A B D E G A B D
    # (start beat, scale degree, beats, tremolo)
    phrase = [(0, 5, 1, 0), (1, 4, 0.5, 0), (1.5, 3, 0.5, 0), (2, 4, 2, 1), (4, 2, 1, 0), (5, 3, 1, 0),
              (6, 1, 0.5, 0), (6.5, 2, 0.5, 0), (7, 0, 1, 1), (8, 3, 1, 0), (9, 5, 1, 0), (10, 6, 0.5, 0),
              (10.5, 5, 0.5, 0), (11, 4, 2, 1), (13, 3, 1, 0), (14, 2, 1, 0), (15, 3, 1, 1)]
    beat = seconds / 32.0
    for rep in range(2):
        for st, deg, ln, trem in phrase:
            at = (rep * 16 + st) * beat
            f = G * scale[deg] * 2
            if trem:
                k = 0.0
                while k < ln * beat * 0.9:
                    tl.add(ks_pluck(r, f, 0.6, 0.5), at + k, 0.45 + 0.1 * r.random())
                    k += 1 / 13.0
            else:
                tl.add(ks_pluck(r, f, 1.6, 0.8), at + r.uniform(0, 0.01), 0.9)
        for b in range(0, 16, 4):
            tl.add(knock(r, 1500, t60=0.05, bright=0.9, hollow=0.2, dur=0.2), (rep * 16 + b) * beat, 0.4)
    y = tl.buf
    ir = S.reverb_ir(2.5, 1.3, r, damp_hz=3500, predelay=0.015)
    y = S.reverb(y, ir, 0.25, circular=True)
    y = S.circ_sosfilt(S.sos_low(5500, 2), y)
    return finish_loop(y)


def teahouse(v, seconds=18.0):
    """Tea poured into small cups, a porcelain lid set back, cups placed on wood."""
    r = S.rng(4500 + v)
    tl = S.Timeline(seconds)
    n = tl.n
    for at in (0.8, 9.4):
        tl.add(pour(r, r.uniform(1.6, 2.2), 650, 1500, density=110), at, 0.55)
    for at in (3.4, 5.1, 12.6, 15.7):  # cup clinks and lids (porcelain, softened)
        tl.add(ceramic(r, r.uniform(1800, 2300), t60=0.35, bright=0.3, dur=0.9, ratios=(1.0, 2.43, 4.1), amps=(1.0, 0.35, 0.12)),
               at + r.uniform(-0.2, 0.2), 0.22)
    for at in (6.6, 14.2):
        tl.add(knock(r, 420, t60=0.08, bright=0.4, dur=0.3), at, 0.25)  # cup set on a wooden table
    y = tl.buf + S.circ_noise(n, r, S.shape_pink(80, 2500)) * 0.015
    ir = S.reverb_ir(1.2, 0.55, r, damp_hz=4000)
    y = S.reverb(y, ir, 0.15, circular=True)
    y = S.circ_sosfilt(S.sos_low(6000, 2), y)
    return finish_loop(y)


def hot_spring(v, seconds=17.0):
    """A warm pool: slow lapping water, a trickle from a bamboo spout, a faint breath of steam."""
    r = S.rng(4600 + v)
    tl = S.Timeline(seconds)
    n = tl.n
    lap = S.circ_noise(n, r, S.shape_band(90, 700, 8, 14))
    lap *= (0.5 + 0.5 * S.lfo(n, 7, 0.0)) ** 2 * (0.7 + 0.3 * S.smooth_random(n, 6, r, 0, 1))
    for _ in range(int(20 * seconds)):
        tl.add(bubble(r, r.uniform(500, 2000), r.lognormal(-0.8, 0.5)), r.uniform(0, seconds))
    steam = S.circ_noise(n, r, S.shape_band(1200, 3500, 10, 18)) * (0.5 + 0.5 * S.lfo(n, 2, 0.4))
    y = 0.5 * lap + 0.5 * tl.buf / (np.max(np.abs(tl.buf)) or 1.0) + 0.05 * steam
    y = S.circ_sosfilt(S.sos_low(5500, 2), y)
    return finish_loop(y)


# ============================================================================================ panda calls
def _norm(y):
    return y / (np.max(np.abs(y)) or 1.0)


def panda_content(v, child=False):
    """A contented call: an adult's soft bleat "mmeh-eh" with a quaver; a cub's chirps."""
    r = S.rng(6100 + v + (50 if child else 0))
    if child:
        parts = []
        for k in range(r.integers(2, 4)):
            d = r.uniform(0.11, 0.17)
            f = r.uniform(620, 740)
            y = V.voice(d, [(0, f * 0.85), (0.4, f * 1.15), (1, f * 0.92)], [(0, 0), (0.15, 1), (0.8, 0.8), (1, 0)],
                        [(0, V.formants("e", 1.15)), (1, V.formants("a", 1.15))], r, breath=0.08, jitter=0.01,
                        tilt_db_oct=-10.0)
            parts.append((k * r.uniform(0.17, 0.24), y))
        tl = S.Timeline(1.0)
        for at, y in parts:
            tl.add(y, at + 0.02, 1.0, wrap=False)
        return S.fade(tl.buf, 0, 0.05)
    d = r.uniform(0.62, 0.85)
    f = [300, 335, 280, 318][v % 4]
    y = V.voice(d, [(0, f * 0.82), (0.18, f * 1.05), (0.6, f), (1, f * 0.86)],
                [(0, 0), (0.1, 0.6), (0.2, 1), (0.75, 0.85), (1, 0)],
                [(0, V.formants("m", 0.85)), (0.16, V.formants("e", 0.85)), (0.7, V.formants("e", 0.85)), (1, V.formants("a", 0.85))],
                r, quaver_hz=r.uniform(9, 12), quaver_depth=0.035, quaver_amp=0.45, breath=0.07)
    out = np.zeros(S.n_of(d + 0.25))
    out[S.n_of(0.02):S.n_of(0.02) + len(y)] = y
    return S.fade(out, 0, 0.05)


def panda_discontent(v, child=False):
    """Unhappy: a huff through the nose and a short low moan (adult); a whiny falling squeal (cub)."""
    r = S.rng(6200 + v + (50 if child else 0))
    if child:
        d = r.uniform(0.45, 0.6)
        f = r.uniform(680, 780)
        y = V.voice(d, [(0, f), (0.3, f * 1.08), (1, f * 0.7)], [(0, 0), (0.1, 1), (0.7, 0.8), (1, 0)],
                    [(0, V.formants("e", 1.15)), (1, V.formants("u", 1.15))], r, quaver_hz=14, quaver_depth=0.03,
                    quaver_amp=0.3, breath=0.12, jitter=0.012, tilt_db_oct=-10.0)
        out = np.zeros(S.n_of(d + 0.2))
        out[S.n_of(0.02):S.n_of(0.02) + len(y)] = y
        return S.fade(out, 0, 0.05)
    huff = V.breath_noise(0.22, r, 300, 2200, [(0, 0), (0.1, 1), (1, 0)])
    huff2 = V.breath_noise(0.18, r, 300, 2000, [(0, 0), (0.1, 0.7), (1, 0)])
    moan_d = r.uniform(0.45, 0.6)
    moan = V.voice(moan_d, [(0, 175), (0.3, 190), (1, 140)], [(0, 0), (0.15, 1), (0.8, 0.7), (1, 0)],
                   [(0, V.formants("o", 0.8)), (1, V.formants("u", 0.8))], r, breath=0.12, jitter=0.02, sub=0.3)
    tl = S.Timeline(1.3)
    tl.add(_norm(huff), 0.02, 0.8, wrap=False)
    tl.add(_norm(huff2), 0.27, 0.55, wrap=False)
    tl.add(_norm(moan), 0.55 + 0.05 * v, 0.9, wrap=False)
    return S.fade(tl.buf, 0, 0.08)


def panda_sleepy(v, child=False):
    """A yawn: opens with a rising breathy moan, falls and closes to a hum."""
    r = S.rng(6300 + v + (50 if child else 0))
    sc = 1.35 if child else 0.85
    f = (520 if child else 250) * (1 + 0.04 * v)
    d = r.uniform(1.1, 1.35)
    y = V.voice(d, [(0, f * 0.9), (0.2, f * 1.15), (0.7, f * 0.75), (1, f * 0.6)],
                [(0, 0), (0.15, 0.8), (0.4, 1), (0.85, 0.45), (1, 0)],
                [(0, V.formants("e", sc)), (0.3, V.formants("a", sc)), (0.75, V.formants("o", sc)), (1, V.formants("m", sc))],
                r, breath=0.35, jitter=0.01)
    smack = knock(r, 1800, t60=0.02, bright=0.9, dur=0.05) * 0.05
    out = np.zeros(S.n_of(d + 0.35))
    out[S.n_of(0.02):S.n_of(0.02) + len(y)] = y
    i = S.n_of(d + 0.12)
    out[i:i + len(smack)] += smack[: len(out) - i]
    return S.fade(out, 0, 0.08)


def panda_sleeping(v, child=False):
    """Asleep: two slow breaths with the softest snore on the in-breath."""
    r = S.rng(6400 + v + (50 if child else 0))
    tl = S.Timeline(2.3 if not child else 1.7)
    t0 = 0.03
    for k in range(2):
        ind = r.uniform(0.55, 0.75) if not child else r.uniform(0.35, 0.5)
        inh = V.breath_noise(ind, r, 180 if not child else 400, 1300 if not child else 2400,
                             [(0, 0), (0.4, 1), (1, 0)], flutter_hz=28 if not child else 40, flutter_depth=0.7 if not child else 0.4)
        exd = ind * 1.25
        exh = V.breath_noise(exd, r, 250 if not child else 500, 1800 if not child else 3000, [(0, 0), (0.2, 0.6), (1, 0)])
        tl.add(_norm(inh), t0, 1.0, wrap=False)
        tl.add(_norm(exh), t0 + ind + 0.06, 0.55, wrap=False)
        t0 += ind + exd + (0.18 if not child else 0.1)
    return S.fade(tl.buf, 0, 0.1)


# ============================================================================================== registry
# slot: what plays it in the game. "data": a blueprint field adopted by the catalogue lane; "code": the code lane plays it.
SOUNDS = []


def reg(id, fn, variants, kind, lufs, slot, ceiling=-1.0, channels=1, period=None, ref=None, priority="A", note=""):
    SOUNDS.append(dict(id=id, fn=fn, variants=variants, kind=kind, lufs=lufs, slot=slot, ceiling=ceiling,
                       channels=channels, period=period, ref=ref, priority=priority, note=note))


# --- signals of the day (code)
reg("Environment.Pandaborn.ShiftBell.End", shift_bell_end, 3, "oneshot", -18.0,
    "code: Bell module, at the end of the Inkpaw working day (WorkingHoursTransitionedEvent to off-duty)",
    ref="Environment.Buildings.BellToll")
reg("Environment.Pandaborn.ShiftBell.Dawn", shift_bell_dawn, 2, "oneshot", -20.0,
    "code: Bell module, at the start of the Inkpaw working day (dawn)", ref="Environment.Buildings.BellToll")
reg("Environment.Pandaborn.NightClapper", night_clapper, 2, "oneshot", -24.0,
    "code: Ringtails module, when the Ringtail night shift starts", ceiling=-3.0, ref="Environment.Buildings.Speaker.Chime_01")
reg("UI.Buildings.Selected.Pandaborn.VillageHall", village_hall_select, 1, "oneshot", -25.0,
    "data: BuildingSpec.SelectionSoundName = \"Pandaborn.VillageHall\" on PandabornVillageHall.Inkpaws", ceiling=-7.0,
    ref="UI.Buildings.Selected.Bell")
# --- water
reg("Environment.Pandaborn.FlumeWater", flume_water, 1, "loop", -24.0,
    "code: Water module, one area sound over every flowing flume tile (ISoundSystem.AddLargeAreaSound + IEmitterMap)",
    ceiling=-3.0, ref="Environment.Buildings.Loop.WateringPlace")
reg("Environment.Pandaborn.BambooTok", bamboo_tok, 3, "oneshot", -26.0,
    "code: Water module, sparingly (a flume run first fills; a gate opens)", ceiling=-4.0,
    ref="Environment.Buildings.Speaker.Chime_01")
reg("Environment.Buildings.Loop.Pandaborn.ScoopWheel", scoop_wheel, 1, "loop", -19.0,
    "data: BuildingSpec.LoopingSoundName = \"Pandaborn.ScoopWheel\" (plays while the pump works); later the Water module",
    period=6.0, ref="Environment.Buildings.Loop.WaterWheel")
reg("Environment.Buildings.Loop.Pandaborn.BambooWaterWheel", bamboo_water_wheel, 1, "loop", -18.0,
    "data: BuildingSpec.LoopingSoundName = \"Pandaborn.BambooWaterWheel\" (PowerGeneratorSoundsSpec: plays while it makes power)",
    period=4.5, ref="Environment.Buildings.Loop.WaterWheel")
reg("Environment.Buildings.Loop.Pandaborn.KiteWindmill", kite_windmill, 1, "loop", -20.0,
    "data: BuildingSpec.LoopingSoundName = \"Pandaborn.KiteWindmill\" on both kite windmills (PowerGeneratorSoundsSpec)",
    period=3.2, ref="Environment.Buildings.Loop.Gristmill")
# --- the wonder
reg("UI.Buildings.Wonder.PandabornSkyLantern", sky_lantern_launch, 1, "oneshot", -19.0,
    "data: FactionWonderSpec.WonderLaunchSound on the faction (played 2D when the wonder is launched)", channels=2,
    ref="UI.Buildings.Wonder.EarthRecultivator")
# --- workshops (data: LoopingSoundName, plays while the workshop is working)
for sid, fn, lufs, ref, note in [
    ("Steamer", steamer, -20.0, "Environment.Buildings.Loop.Bakery", "PandabornSteamer"),
    ("TeaRoastery", tea_roastery, -21.0, "Environment.Buildings.Loop.Grill", "PandabornTeaRoastery"),
    ("PickleYard", pickle_yard, -22.0, "Environment.Buildings.Loop.Bakery", "PandabornPickleYard"),
    ("LanternWorkshop", lantern_workshop, -22.0, "Environment.Buildings.Loop.PaperMill", "PandabornLanternWorkshop"),
    ("SmokeKiln", smoke_kiln, -21.0, "Environment.Buildings.Fire", "PandabornSmokeKiln"),
    ("TripHammer", trip_hammer, -19.0, "Environment.Buildings.Loop.Gristmill", "PandabornTripHammerMill"),
    ("Simmer", simmer, -21.0, "Environment.Buildings.Loop.Grill", "PandabornKitchen, PandabornHotPotHall"),
]:
    reg("Environment.Buildings.Loop.Pandaborn." + sid, fn, 1, "loop", lufs,
        "data: BuildingSpec.LoopingSoundName = \"Pandaborn.%s\" on %s" % (sid, note), ref=ref, priority="B",
        period=3.0 if sid == "TripHammer" else (1.6 if sid == "TeaRoastery" else None))
# --- festival (code)
reg("Environment.Pandaborn.FestivalDrum", festival_drum, 1, "loop", -20.0,
    "code: Festival module, LoopSingle3DSound on each Festival Square while the evening gathering lasts",
    period=2.4, ref="Environment.Buildings.Loop.DanceHall", priority="B")
reg("Environment.Pandaborn.Firecrackers", firecrackers, 2, "oneshot", -25.0,
    "code: Festival module, at the festival's start (dawn) and as the gathering begins", ceiling=-6.0,
    ref="Environment.Fireworks.Burst_01", priority="B")
reg("Environment.Pandaborn.LanternRise", lantern_rise, 3, "oneshot", -29.0,
    "code: Festival module, per rising lantern (or data: an Inkpaws-only modifier on Firework.CometRed/CometWhite TrailSound)",
    ceiling=-10.0, ref="Environment.Fireworks.Trail_01", priority="B")
# --- attractions (data: LoopingSoundName, plays while visitors are inside)
for sid, fn, lufs, ref, note in [
    ("OperaStage", opera_stage, -27.0, "Environment.Buildings.Loop.DanceHall", "PandabornOperaStage"),
    ("Teahouse", teahouse, -24.0, "Environment.Buildings.Loop.Agora", "PandabornTeahouse"),
    ("HotSpring", hot_spring, -24.0, "Environment.Buildings.Loop.WateringPlace", "PandabornHotSpringBath"),
]:
    reg("Environment.Buildings.Loop.Pandaborn." + sid, fn, 1, "loop", lufs,
        "data: BuildingSpec.LoopingSoundName = \"Pandaborn.%s\" on %s (attraction: plays while visitors are inside)" % (sid, note),
        ref=ref, priority="C", period=None)
# --- panda calls (data: FactionSpec.SoundId = "Pandaborn"; all eight are required once SoundId is switched)
for who, child in (("Adult", False), ("Child", True)):
    for mood, fn, nv in (("Content", panda_content, 4), ("Discontent", panda_discontent, 2),
                         ("Sleepy", panda_sleepy, 2), ("Sleeping", panda_sleeping, 2)):
        reg("UI.Beavers.Pandaborn.Selected.%s_%s" % (who, mood), (lambda f, c: (lambda v: f(v, c)))(fn, child), nv,
            "oneshot", -24.0, "data: FactionSpec.SoundId = \"Pandaborn\" (selecting a colonist; the new-game faction panel plays Adult_Content)",
            ceiling=-10.0, ref="UI.Beavers.Common.Selected.%s_%s_01" % (who, mood), priority="A")
