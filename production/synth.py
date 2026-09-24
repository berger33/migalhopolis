#!/usr/bin/env python3
"""MIGALHÓPOLIS — síntese de trilha sonora e efeitos (numpy puro, sem amostras).
Gera 11 bases musicais (WAV, RMS alvo) + 12 efeitos, e cópias MP3 no repo.
"""
import argparse, json, math, os, struct, subprocess
import numpy as np

SR = 44100
RNG = np.random.default_rng(77)

NOTAS = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
         "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}

def nf(nome):
    """'Bb3' -> frequência"""
    oitava = int(nome[-1])
    semi = NOTAS[nome[:-1]]
    return 440.0 * (2 ** ((semi - 9) / 12 + (oitava - 4)))

def t(d): return int(round(d * SR))

def acorde(root, tipo="maj"):
    terca = 4 if tipo.startswith("maj") else 3
    base = NOTAS[root[:-1]] + 12 * (int(root[-1]) - 4)
    if tipo.endswith("7"):
        return [nf_c(base), nf_c(base + terca), nf_c(base + 7), nf_c(base + 10)]
    return [nf_c(base), nf_c(base + terca), nf_c(base + 7)]

def nf_c(semi): return 440.0 * (2 ** ((semi - 9) / 12))

def onda(tipo, freq, n, vibrato=0.0, vrate=5.5):
    tt = np.arange(n) / SR
    if vibrato:
        f = freq * (1.0 + vibrato * np.sin(2 * np.pi * vrate * tt))
        fase = 2 * np.pi * np.cumsum(f) / SR
    else:
        fase = 2 * np.pi * freq * tt
    if tipo == "sine": return np.sin(fase)
    if tipo == "square": return np.sign(np.sin(fase)) * 0.7
    if tipo == "saw": return (2 * ((fase / (2 * np.pi)) % 1.0) - 1) * 0.8
    if tipo == "tri": return 2 * np.abs(2 * ((fase / (2 * np.pi)) % 1.0) - 1) - 1
    raise ValueError(tipo)

def env_adsr(n, a=0.01, d=0.1, s=0.7, r=0.1):
    a_n, d_n, r_n = t(a), t(d), t(r)
    sus = max(0, n - a_n - d_n - r_n)
    partes = []
    if a_n: partes.append(np.linspace(0, 1, a_n))
    if d_n: partes.append(np.linspace(1, s, d_n))
    if sus: partes.append(np.full(sus, s))
    if r_n: partes.append(np.linspace(s, 0, r_n))
    e = np.concatenate(partes) if partes else np.zeros(n)
    return e[:n] if len(e) >= n else np.pad(e, (0, n - len(e)))

def filt(x, cutoff, order=2, kind="low"):
    """Filtro espectral com resposta butterworth aproximada."""
    X = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / SR)
    if kind == "low":
        mag = 1.0 / np.sqrt(1 + (freqs / max(cutoff, 1)) ** (2 * order))
    else:
        mag = (freqs / max(cutoff, 1)) ** order / np.sqrt(1 + (freqs / max(cutoff, 1)) ** (2 * order))
    return np.fft.irfft(X * mag, len(x))

def reverb(x, mix=0.22, decay=1.6):
    n = len(x)
    ir_len = t(decay)
    ir = RNG.standard_normal(ir_len) * np.exp(-np.arange(ir_len) / (SR * 0.45))
    ir[:40] = 0
    X, H = np.fft.rfft(x, n + ir_len), np.fft.rfft(ir, n + ir_len)
    molhado = np.fft.irfft(X * H, n + ir_len)[:n]
    molhado /= (np.abs(molhado).max() + 1e-9)
    saida = x + mix * molhado
    return saida / (np.abs(saida).max() + 1e-9)

# ---------------- instrumentos ----------------
def i_bass(freq, dur, vel=1.0):
    n = t(dur)
    x = onda("sine", freq, n) * 0.8 + onda("tri", freq, n) * 0.4
    e = np.exp(-np.arange(n) / (SR * 0.35)) * env_adsr(n, 0.004, 0.06, 0.5, 0.08)
    return filt(x * e, 420) * vel

def i_brass(freq, dur, vel=1.0, seed=1):
    n = t(dur)
    r = np.random.default_rng(seed)
    x = onda("saw", freq, n, vibrato=0.004) * 0.6 + onda("square", freq * 1.004, n) * 0.3
    e = env_adsr(n, 0.035, 0.09, 0.75, 0.07)
    return filt(x * e, 1500 + 600 * r.random()) * vel

def i_whistle(freq, dur, vel=1.0, seed=1):
    n = t(dur)
    x = onda("sine", freq, n, vibrato=0.011, vrate=6.0)
    x += 0.18 * onda("sine", freq * 2, n, vibrato=0.011, vrate=6.0)
    r = np.random.default_rng(seed)
    sopro = filt(r.standard_normal(n), 2400, 3, "high") * 0.03
    e = env_adsr(n, 0.03, 0.05, 0.85, 0.06)
    return (x + sopro) * e * vel

def i_accordion(freq, dur, vel=1.0):
    n = t(dur)
    x = onda("square", freq * 0.999, n, vibrato=0.006) * 0.45 + onda("square", freq * 1.003, n, vibrato=0.006) * 0.45
    x += 0.2 * onda("saw", freq * 2, n, vibrato=0.006)
    e = env_adsr(n, 0.05, 0.08, 0.8, 0.08)
    return filt(x * e, 2600) * vel

def i_pluck(freq, dur, vel=1.0, seed=1):
    n = t(dur)
    tt = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * freq * h * tt + h) / (h ** 1.3) for h in (1, 2, 3, 4.02, 5.1))
    e = np.exp(-tt * 7.5)
    return filt(x * e, 3200) * vel * 0.8

def i_pad(freq, dur, vel=1.0, bright=900):
    n = t(dur)
    x = (onda("saw", freq * 0.9985, n) + onda("saw", freq, n) + onda("saw", freq * 1.0025, n)) / 3
    e = env_adsr(n, 0.45, 0.2, 0.85, 0.6)
    return filt(x * e, bright, 2) * vel * 0.8

def i_musicbox(freq, dur, vel=1.0):
    n = t(dur)
    tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * tt) + 0.45 * np.sin(2 * np.pi * freq * 2.71 * tt) * np.exp(-tt * 9) \
        + 0.22 * np.sin(2 * np.pi * freq * 5.43 * tt) * np.exp(-tt * 12)
    e = np.exp(-tt * 4.2)
    return x * e * vel * 0.7

def i_bell(freq, dur, vel=1.0, detune=1.0):
    n = t(dur)
    tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * detune * tt) + 0.5 * np.sin(2 * np.pi * freq * 2.4 * tt) * np.exp(-tt * 3) \
        + 0.3 * np.sin(2 * np.pi * freq * 3.9 * tt) * np.exp(-tt * 5)
    e = np.exp(-tt * 1.8)
    return x * e * vel * 0.5

def i_timpani(freq, dur, vel=1.0):
    n = t(dur)
    tt = np.arange(n) / SR
    f = freq * (1 + 0.35 * np.exp(-tt * 22))
    fase = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(fase) + 0.4 * filt(RNG.standard_normal(n), 240) * np.exp(-tt * 30)
    e = np.exp(-tt * 3.2)
    return x * e * vel

def i_kick(freq=90, dur=0.3, vel=1.0):
    n = t(dur)
    tt = np.arange(n) / SR
    f = freq * (1 + 1.1 * np.exp(-tt * 26))
    fase = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(fase) * np.exp(-tt * 11)
    return x * vel

def i_snare(dur=0.06, seed=1, tone=True, freq=196, vel=1.0):
    n = t(dur)
    r = np.random.default_rng(seed)
    tt = np.arange(n) / SR
    x = r.standard_normal(n) * np.exp(-tt * 26)
    if tone:
        x += 0.55 * np.sin(2 * np.pi * freq * tt) * np.exp(-tt * 32)
    return filt(x, 5200, 2, "high") * 0.8 * vel

def i_triangle(dur=0.09, vel=1.0, freq=4720):
    n = t(dur)
    tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * tt) * np.exp(-tt * 55)
    x += 0.12 * np.random.default_rng(5).standard_normal(n) * np.exp(-tt * 90)
    return x * vel

def i_woodblock(dur=0.05, vel=1.0, freq=1750):
    n = t(dur)
    tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * tt) * np.exp(-tt * 90)
    x += 0.3 * RNG.standard_normal(n) * np.exp(-tt * 140)
    return filt(x, 900, 1, "high") * vel

def i_metal(dur=0.9, vel=1.0, seed=9, freq=880):
    n = t(dur)
    r = np.random.default_rng(seed)
    tt = np.arange(n) / SR
    x = sum((1 / h) * np.sin(2 * np.pi * freq * h * tt + r.random() * 6) * np.exp(-tt * (2 + h)) for h in (1, 1.51, 2.13, 2.74, 3.97))
    return x * vel * 0.4

def i_drip(vel=1.0, f0=1400, f1=380, dur=0.28):
    n = t(dur)
    tt = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-tt * 26)
    fase = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(fase) * np.exp(-tt * 15) * vel

def i_crowd(dur=6.0, vel=1.0, seed=3):
    n = t(dur)
    r = np.random.default_rng(seed)
    tt = np.arange(n) / SR
    x = filt(r.standard_normal(n), 900, 2) * 0.7 + filt(r.standard_normal(n), 350, 2) * 0.5
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.9 * tt + r.random() * 6) * np.sin(2 * np.pi * 0.23 * tt)
    brados = np.zeros(n)
    for _ in range(int(dur / 1.1)):
        p = r.integers(0, n - t(0.5))
        brados[p:p + t(0.4)] += filt(r.standard_normal(t(0.4)), 1200, 2) * np.hanning(t(0.4)) * r.uniform(0.4, 1.0)
    x = (x * lfo + 0.8 * brados)
    return filt(x, 1500, 2) * vel / (np.abs(x).max() + 1e-9) * 0.9

# ---------------- sequenciador ----------------
class Track:
    def __init__(self, dur):
        self.dur = dur
        self.buf = np.zeros(t(dur) + SR)
    def put(self, sig, t0):
        i0 = t(t0)
        i1 = min(i0 + len(sig), len(self.buf))
        if i1 > i0:
            self.buf[i0:i1] += sig[:i1 - i0]
    def note(self, t0, dur, nome_ou_freq, inst, vel=1.0, **kw):
        # durações em SEGUNDOS: cada instrumento converte internamente
        f = nome_ou_freq if isinstance(nome_ou_freq, (int, float)) else nf(nome_ou_freq)
        self.put(inst(f, dur, 1.0, **kw) if kw else inst(f, dur, 1.0), t0)
    def drum(self, t0, inst_fn, *args, **kw):
        self.put(inst_fn(*args, **kw), t0)
    def sig(self):
        return self.buf[:t(self.dur)]

def bpm_beats(bpm, compas): return 60.0 / bpm * compas

# ---------------- bases musicais ----------------
def prog_bar(track, t0, beats_per_bar, bpm, acordes, inst_pad, vel=1.0):
    bar = 60.0 / bpm * beats_per_bar
    for i, ac in enumerate(acordes):
        for f in ac:
            track.note(t0 + i * bar, bar * 0.98, f, inst_pad, vel / max(1, len(acordes[0])))

def bed_tema():
    """Marchinha de abertura em Bb, 132 bpm, 16 compassos."""
    bpm = 132.0
    bar = 60.0 / bpm * 4
    dur = bar * 16 + 2.0
    tr = Track(dur)
    prog = ["Bb", "Eb", "Bb", "F7", "Bb", "Eb", "Bb", "F7",
            "Bb", "Eb", "Bb", "F7", "Bb", "Eb", "F7", "Bb"]
    raizes = {"Bb": ("Bb1", "F2"), "Eb": ("Eb2", "Bb2"), "F7": ("F2", "C3")}
    tercas = {"Bb": ["Bb3", "D4", "F4"], "Eb": ["Eb3", "G3", "Bb3"], "F7": ["F3", "A3", "Eb4"]}
    melodia = [
        [("Bb4", 0.0, 0.5), ("D5", 0.5, 0.5), ("F5", 1.0, 0.5), ("D5", 1.5, 0.5), ("F5", 2.0, 0.5), ("G5", 2.5, 0.5), ("F5", 3.0, 1.0)],
        [("Eb5", 0.0, 0.75), ("G5", 0.75, 0.5), ("Bb5", 1.25, 0.75), ("G5", 2.0, 0.5), ("Eb5", 2.5, 0.5), ("F5", 3.0, 1.0)],
        [("D5", 0.0, 0.5), ("F5", 0.5, 0.5), ("Bb5", 1.0, 1.0), ("A5", 2.0, 0.5), ("G5", 2.5, 0.5), ("F5", 3.0, 1.0)],
        [("C5", 0.0, 0.5), ("Eb5", 0.5, 0.5), ("F5", 1.0, 0.5), ("A5", 1.5, 0.5), ("C6", 2.0, 2.0)],
        [("Bb4", 0.0, 0.5), ("D5", 0.5, 0.5), ("F5", 1.0, 0.5), ("D5", 1.5, 0.5), ("G5", 2.0, 0.5), ("F5", 2.5, 0.5), ("Eb5", 3.0, 1.0)],
        [("Eb5", 0.0, 0.5), ("G5", 0.5, 0.5), ("Bb5", 1.0, 0.5), ("G5", 1.5, 0.5), ("F5", 2.0, 0.5), ("D5", 2.5, 0.5), ("Eb5", 3.0, 1.0)],
        [("D5", 0.0, 0.75), ("E5", 0.75, 0.25), ("F5", 1.0, 0.75), ("G5", 1.75, 0.25), ("A5", 2.0, 0.75), ("Bb5", 2.75, 0.25), ("C6", 3.0, 1.0)],
        [("Bb5", 0.0, 1.5), ("F5", 1.5, 0.5), ("D5", 2.0, 0.5), ("Bb4", 2.5, 0.5), ("F5", 3.0, 1.0)],
    ]
    for volta in range(2):
        base = volta * 8 * bar
        for i, ac in enumerate(prog):
            r1, r2 = raizes[ac]
            tr.note(base + i * bar, bar * 0.45, r1, i_bass, 1.0)
            tr.note(base + i * bar + bar * 0.5, bar * 0.42, r2, i_bass, 0.85)
            for j, n in enumerate(tercas[ac]):
                tr.note(base + i * bar + bar * 0.25, 0.16, n, i_brass, 0.5, seed=i + 1)
                tr.note(base + i * bar + bar * 0.75, 0.16, n, i_brass, 0.5, seed=i + 2)
            tr.drum(base + i * bar + 0.25, i_snare, 0.06, i + 1, False)
            tr.drum(base + i * bar + bar * 0.5 + 0.25, i_snare, 0.06, i + 5, False)
        frase = melodia[volta * 4:volta * 4 + 4] if False else melodia[:4] + melodia[4:] if volta == 0 else melodia[4:] + melodia[:4]
        for bi, comp in enumerate(frase):
            for nome, beat, dur_b in comp:
                tr.note(base + bi * bar + beat * (bar / 4), dur_b * (bar / 4), nome, i_whistle, 1.15, seed=bi + 3)
    tr.drum(bar * 15, i_snare, 0.05, 9, False)
    for k in range(8):
        tr.drum(bar * 15 + k * 0.11, i_snare, 0.05, 20 + k, False)
    x = tr.sig()
    x = reverb(x, 0.16, 1.1)
    return x, dur

def bed_jingle():
    """Jingle de campanha, Eb major, 140 bpm, 8 compassos."""
    bpm = 140.0
    bar = 60.0 / bpm * 4
    dur = bar * 8 + 1.5
    tr = Track(dur)
    prog = ["Eb", "Ab", "Eb", "Bb7", "Eb", "Ab", "Bb7", "Eb"]
    acordes = {"Eb": ["Eb3", "G3", "Bb3"], "Ab": ["Ab3", "C4", "Eb4"], "Bb7": ["Bb3", "D4", "Ab4"]}
    raizes = {"Eb": "Eb2", "Ab": "Ab2", "Bb7": "Bb2"}
    mel = [("Eb4", 0, .5), ("G4", .5, .5), ("Bb4", 1, .5), ("Bb4", 1.5, .5), ("C5", 2, 1.0), ("Bb4", 3, 1.0),
           ("Ab4", 0, .5), ("C5", .5, .5), ("Eb5", 1, 1.5), ("Bb4", 2.5, .5), ("G4", 3, 1.0),
           ("Eb4", 0, .5), ("F4", .5, .5), ("G4", 1, .5), ("Bb4", 1.5, .5), ("Eb5", 2, 2.0),
           ("D5", 0, .5), ("C5", .5, .5), ("Bb4", 1, .5), ("Ab4", 1.5, .5), ("G4", 2, 2.0)]
    for i, ac in enumerate(prog):
        t0 = i * bar
        tr.note(t0, bar * 0.46, raizes[ac], i_bass, 1.0)
        tr.note(t0 + bar * 0.5, bar * 0.44, raizes[ac], i_bass, 0.8)
        for n in acordes[ac]:
            tr.note(t0 + bar * 0.25, 0.18, n, i_brass, 0.55, seed=i)
            tr.note(t0 + bar * 0.75, 0.18, n, i_brass, 0.5, seed=i + 1)
        tr.drum(t0 + 0.25, i_snare, 0.06, i, False)
        tr.drum(t0 + bar * 0.5 + 0.25, i_snare, 0.06, i + 4, False)
    for bi, comp in enumerate([mel[0:2], mel[2:4]]):
        for nome, beat, dur_b in comp:
            for rep in range(2):
                tr.note(rep * 4 * bar + bi * bar + beat * (bar / 4), dur_b * (bar / 4), nome, i_brass, 0.9, seed=bi + rep)
    x = tr.sig()
    return reverb(x, 0.14, 0.9), dur

def bed_forro():
    """Xote em Am, 116 bpm, 16 compassos (2/4)."""
    bpm = 116.0
    beat = 60.0 / bpm
    bar = beat * 2
    dur = bar * 16 + 2.0
    tr = Track(dur)
    prog = ["Am", "Dm", "E7", "Am", "F", "C", "E7", "Am"] * 2
    acordes = {"Am": ["A2", "A3", "C4", "E4"], "Dm": ["D3", "D3", "F3", "A3"], "E7": ["E2", "E3", "G#3", "D4"],
               "F": ["F2", "F3", "A3", "C4"], "C": ["C3", "C4", "E4", "G4"]}
    mel = [[("A4", 0, .5), ("C5", .5, .5), ("B4", 1, .5), ("A4", 1.5, .5)],
           [("E4", 0, .5), ("F4", .5, .5), ("E4", 1, .5), ("D4", 1.5, .5)],
           [("G#4", 0, .5), ("B4", .5, .5), ("G#4", 1, .5), ("E4", 1.5, .5)],
           [("A4", 0, .75), ("E4", .75, .25), ("C5", 1, .5), ("A4", 1.5, .5)]]
    for i, ac in enumerate(prog):
        t0 = i * bar
        notas = acordes[ac]
        tr.note(t0, beat * 0.9, notas[0], i_bass, 1.0)
        tr.note(t0 + beat, beat * 0.9, notas[1], i_bass, 0.9)
        for k in range(4):  # triângulo em colcheias pontuadas
            tr.drum(t0 + k * beat * 0.5 + (0.06 if k % 2 else 0), i_triangle, 0.09, 0.8)
        tr.drum(t0, i_kick, 105, 0.3, 1.0)
        tr.drum(t0 + beat, i_snare, 0.06, i, False)
        for n in notas[1:]:
            tr.note(t0, bar * 0.95, n, i_accordion, 0.16)
        m = mel[i % 4]
        for nome, beat_off, dur_b in m:
            tr.note(t0 + beat_off * beat, dur_b * beat, nome, i_accordion, 0.8)
    x = tr.sig()
    return reverb(x, 0.12, 1.0), dur

def bed_cotidiano():
    """Base leve de quintal, C major, 96 bpm, cavaquinho."""
    bpm = 96.0
    bar = 60.0 / bpm * 4
    dur = bar * 8 + 1.5
    tr = Track(dur)
    prog = [["C", ["C3", "E3", "G3"]], ["F", ["F2", "A2", "C3"]], ["G", ["G2", "B2", "D3"]], ["C", ["C3", "E3", "G3"]],
            ["Am", ["A2", "C3", "E3"]], ["F", ["F2", "A2", "C3"]], ["G", ["G2", "B2", "D3"]], ["C", ["C3", "E3", "G3"]]]
    arp = [0, 1, 2, 1]
    for i, (_, notas) in enumerate(prog):
        t0 = i * bar
        for k, idx in enumerate(arp * 2):
            tr.note(t0 + k * bar / 8, 0.4, notas[idx], i_pluck, 0.8, seed=i + k)
        tr.note(t0, bar * 0.9, notas[0], i_bass, 0.7)
        if i % 2 == 0:
            mel = [("E4", 0.0), ("G4", 0.5), ("A4", 1.0), ("G4", 1.5), ("E4", 2.0), ("D4", 2.5), ("C4", 3.0)]
            for nome, beat in mel:
                tr.note(t0 + beat * bar / 4, 0.35, nome, i_musicbox, 0.35)
    x = tr.sig()
    return reverb(x, 0.15, 1.1), dur

def bed_bueiro():
    """Drone industrial do bueiro, 40 s."""
    dur = 40.0
    n = t(dur)
    tt = np.arange(n) / SR
    base = onda("saw", 55, n) * 0.5 + onda("saw", 55.7, n) * 0.4 + onda("sine", 27.5, n) * 0.5
    base = filt(base, 300)
    lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.11 * tt)
    x = base * lfo
    tr = Track(dur)
    for k in range(14):  # pingos
        p = 2.0 + k * 2.6 + float(RNG.random())
        tr.drum(p, i_drip, 0.8, 1500 + RNG.integers(-300, 300), 320, 0.3)
    for k in range(5):  # metal distante
        p = 3.5 + k * 7.3
        tr.drum(p, i_metal, 1.2, 0.35, int(RNG.integers(1, 999)), 620 + RNG.integers(-100, 200))
    disc = np.sin(2 * np.pi * 466 * tt) * 0.05 + np.sin(2 * np.pi * 493 * tt) * 0.05
    disc *= (0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * tt + 1.3))
    x = x + tr.buf[:n] + disc
    return filt(x, 1600), dur

def bed_suspense():
    """Suspense documental, 36 s: pad grave + sinos + riser."""
    dur = 36.0
    tr = Track(dur)
    for f, v in [(nf("D1"), 1.0), (nf("A1"), 0.7), (nf("D2"), 0.5)]:
        tr.note(0.5, dur - 2, f, i_pad, v * 0.5, bright=520)
    for k, p in enumerate([4.0, 12.5, 21.0, 29.5]):
        tr.note(p, 3.5, "D2" if k % 2 else "Bb1", i_bell, 0.5)
    n = t(dur)
    tt = np.arange(n) / SR
    riser = filt(RNG.standard_normal(n), 800, 2) * (0.5 + 0.5 * np.sin(2 * np.pi * tt / 9.0 - np.pi / 2)) * 0.12
    x = tr.buf[:n] + riser
    return filt(x, 1400), dur

def bed_drama():
    """Cordas de documentário, Dm, 8 compassos lentos."""
    bpm = 72.0
    bar = 60.0 / bpm * 4
    dur = bar * 8 + 2
    tr = Track(dur)
    prog = [["Dm", ["D2", "D3", "F3", "A3"]], ["Bb", ["Bb1", "Bb2", "D3", "F3"]],
            ["F", ["F2", "F3", "A3", "C4"]], ["C", ["C2", "C3", "E3", "G3"]]] * 2
    for i, (_, notas) in enumerate(prog):
        t0 = i * bar
        for f in notas:
            tr.note(t0, bar * 0.97, f, i_pad, 0.5, bright=760)
        tr.drum(t0, i_timpani, nf("D1") if i % 2 == 0 else nf("A1"), 0.5, 0.6)
    mel = [("A3", 0), ("D4", 1), ("F4", 2), ("E4", 3)]
    for i in range(8):
        for nome, beat in mel:
            tr.note(i * bar + beat * bar / 4, bar / 4.2, nome, i_pad, 0.32, bright=1100)
    x = tr.sig()
    return reverb(x, 0.2, 1.8), dur

def bed_tensao():
    """Pulso tenso, 30 s."""
    dur = 30.0
    tr = Track(dur)
    bpm = 100.0
    col = 60.0 / bpm
    k = 0
    p = 0.0
    while p < dur - 0.5:
        tr.note(p, 0.22, "E2" if k % 4 else "E1", i_bass, 0.9)
        tr.drum(p, i_woodblock, 0.05, 0.7)
        if k % 8 == 6:
            tr.drum(p + col * 0.5, i_metal, 0.5, 0.3, 11, 760)
        p += col / 2
        k += 1
    n = t(dur)
    tt = np.arange(n) / SR
    drone = filt(onda("saw", 82.4, n), 420) * 0.35
    drone *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.16 * tt)
    x = tr.buf[:n] + drone
    return x, dur

def bed_fabinho():
    """Caixinha de música em Lá menor, 3/4, lenta e sinistra."""
    bpm = 84.0
    bar = 60.0 / bpm * 3
    dur = bar * 12 + 2
    tr = Track(dur)
    prog = ["Am", "Am", "Dm", "Am", "E7", "Am", "F", "E7"] * 2
    acordes = {"Am": ["A3", "C4", "E4"], "Dm": ["D4", "F4", "A4"], "E7": ["E4", "G#4", "D5"],
               "F": ["F4", "A4", "C5"]}
    mel = [[("E5", 0, 1), ("C5", 1, 1), ("A4", 2, 1)], [("B4", 0, 1.5), ("C5", 1.5, 1.5)],
           [("D5", 0, 1), ("A4", 1, 1), ("F4", 2, 1)], [("E5", 0, 2), ("C5", 2, 1)],
           [("G#4", 0, 1), ("B4", 1, 1), ("E5", 2, 1)], [("A4", 0, 3)],
           [("F4", 0, 1), ("A4", 1, 1), ("C5", 2, 1)], [("B4", 0, 3)]]
    for i, ac in enumerate(prog):
        t0 = i * bar
        for f in acordes[ac]:
            tr.note(t0, bar * 0.96, f, i_pad, 0.16, bright=600)
        m = mel[i % 8]
        for nome, beat, dur_b in m:
            tr.note(t0 + beat * bar / 3, dur_b * bar / 3 * 0.9, nome, i_musicbox, 0.9)
    n = t(dur)
    tt = np.arange(n) / SR
    x = tr.buf[:n] + filt(RNG.standard_normal(n), 240, 2) * 0.02
    return reverb(x, 0.24, 2.0), dur

def bed_comicio():
    """Forró elétrico de comício, 128 bpm, 12 compassos."""
    bpm = 128.0
    beat = 60.0 / bpm
    bar = beat * 2
    dur = bar * 12 + 2
    tr = Track(dur)
    prog = ["Am", "Dm", "E7", "Am"] * 3
    acordes = {"Am": ["A2", "A3", "C4", "E4"], "Dm": ["D3", "D3", "F3", "A3"], "E7": ["E2", "E3", "G#3", "D4"]}
    mel = [[("A4", 0, .5), ("A4", .5, .25), ("B4", .75, .25), ("C5", 1, .5), ("B4", 1.5, .5)],
           [("E5", 0, .75), ("D5", .75, .25), ("C5", 1, .5), ("A4", 1.5, .5)],
           [("E5", 0, .5), ("G#4", .5, .5), ("B4", 1, .5), ("E5", 1.5, .5)]]
    for i, ac in enumerate(prog):
        t0 = i * bar
        notas = acordes[ac]
        tr.note(t0, beat * 0.85, notas[0], i_bass, 1.05)
        tr.note(t0 + beat, beat * 0.85, notas[1], i_bass, 0.95)
        tr.drum(t0, i_kick, 110, 0.3, 1.05)
        tr.drum(t0 + beat, i_snare, 0.05, i + 1, False)
        for k in range(4):
            tr.drum(t0 + k * beat * 0.5 + (0.05 if k % 2 else 0), i_triangle, 0.08, 0.9)
        for fn in notas[1:]:
            tr.note(t0, bar * 0.96, fn, i_brass, 0.22, seed=i + 7)
        m = mel[i % 3]
        for nome, beat_off, dur_b in m:
            tr.note(t0 + beat_off * beat, dur_b * beat * 0.95, nome, i_accordion, 0.85)
    tr.put(i_crowd(dur - 1, 0.55, seed=8) * 0.5, 0.5)
    x = tr.sig()
    return filt(x, 3400), dur

def bed_final():
    """Encerramento: caixinha + cordas em F, amargo-doce."""
    bpm = 66.0
    bar = 60.0 / bpm * 4
    dur = bar * 8 + 3
    tr = Track(dur)
    prog = [["F", ["F2", "F3", "A3", "C4"]], ["Dm", ["D2", "D3", "F3", "A3"]],
            ["Bb", ["Bb1", "Bb2", "D3", "F3"]], ["C", ["C2", "C3", "E3", "G3"]],
            ["F", ["F2", "F3", "A3", "C4"]], ["Dm", ["D2", "D3", "F3", "A3"]],
            ["Gm", ["G1", "G2", "Bb2", "D3"]], ["C", ["C2", "C3", "E3", "G3"]]]
    acordes = {"F": ["F4", "A4", "C5"], "Dm": ["D4", "F4", "A4"], "Bb": ["Bb4", "D5", "F5"],
               "C": ["C4", "E4", "G4"], "Gm": ["G4", "Bb4", "D5"]}
    mel = [[("C5", 0, 2), ("A4", 2, 1), ("F4", 3, 1)], [("D5", 0, 2), ("A4", 2, 2)],
           [("Bb4", 0, 2), ("D5", 2, 1), ("F5", 3, 1)], [("E5", 0, 4)],
           [("A4", 0, 2), ("C5", 2, 2)], [("D5", 0, 4)],
           [("G4", 0, 2), ("Bb4", 2, 2)], [("C5", 0, 3.5)]]
    for i, (ac, notas) in enumerate(prog):
        t0 = i * bar
        for f in notas:
            tr.note(t0, bar * 0.97, f, i_pad, 0.42, bright=700)
        for nome, beat, dur_b in mel[i]:
            tr.note(t0 + beat * bar / 4, dur_b * bar / 4 * 0.92, nome, i_musicbox, 0.8)
    x = tr.sig()
    return reverb(x, 0.26, 2.2), dur

# ---------------- efeitos ----------------
def sfx_latido():
    saida = np.zeros(t(2.4))
    for i, (p, f0, f1, d) in enumerate([(0.2, 340, 130, 0.22), (0.62, 300, 110, 0.3), (1.7, 360, 140, 0.18)]):
        n = t(d)
        tt = np.arange(n) / SR
        f = f1 + (f0 - f1) * np.exp(-tt * 18)
        fase = 2 * np.pi * np.cumsum(f) / SR
        lat = (np.sign(np.sin(fase)) * 0.4 + filt(RNG.standard_normal(n), 900, 2) * 0.5)
        lat *= np.exp(-tt * 16) * np.hanning(n) ** 0.5
        lat = filt(lat, 1900, 2)
        i0 = t(p)
        saida[i0:i0 + n] += lat
    return reverb(saida, 0.3, 1.2), 2.4

def sfx_moscas():
    dur = 6.0
    n = t(dur)
    tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * (190 + 26 * np.sin(2 * np.pi * 13 * tt)) * tt)
    x *= 0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 2.1 * tt + 1.0)) * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 0.37 * tt)))
    x += filt(RNG.standard_normal(n), 3000, 3, "high") * 0.05
    return x * 0.5, dur

def sfx_agua():
    dur = 7.0
    tr = Track(dur)
    for k in range(16):
        p = 0.4 + k * 0.42 + float(RNG.random()) * 0.2
        tr.drum(p, i_drip, 0.5 + RNG.random() * 0.5, 900 + RNG.integers(0, 900), 300, 0.22)
    n = t(dur)
    tt = np.arange(n) / SR
    fundo = filt(RNG.standard_normal(n), 500, 2) * 0.12
    fundo *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.7 * tt)
    x = tr.buf[:n] + fundo
    return reverb(x, 0.35, 1.6), dur

def sfx_grilos():
    dur = 7.0
    n = t(dur)
    x = np.zeros(n)
    r = np.random.default_rng(4)
    for k in range(int(dur / 0.9)):
        p = t(k * 0.9 + r.random() * 0.3)
        for j in range(5):
            i0 = p + t(j * 0.055)
            d = t(0.03)
            tt = np.arange(d) / SR
            x[i0:i0 + d] += np.sin(2 * np.pi * 4400 * tt) * np.hanning(d) * 0.5
    return x * 0.55, dur

def sfx_sinos():
    dur = 6.0
    tr = Track(dur)
    for k, p in enumerate([0.3, 1.9, 3.4]):
        tr.note(p, 3.2, "E4" if k % 2 else "B3", i_bell, 0.9, detune=1.0)
    return reverb(tr.buf[:t(dur)], 0.4, 2.4), dur

def sfx_churrasqueira():
    dur = 6.0
    n = t(dur)
    r = np.random.default_rng(12)
    x = filt(r.standard_normal(n), 5200, 3, "high") * 0.16
    for k in range(90):
        p = r.integers(0, n - t(0.05))
        d = t(r.uniform(0.008, 0.05))
        x[p:p + d] += r.standard_normal(d) * np.hanning(d) * r.uniform(0.3, 1.0)
    x += filt(r.standard_normal(n), 300, 2) * 0.10
    return filt(x, 6000, 1, "low"), dur

def sfx_ventilador():
    dur = 7.0
    n = t(dur)
    tt = np.arange(n) / SR
    ruido = filt(RNG.standard_normal(n), 420, 2)
    x = ruido * (0.75 + 0.25 * np.sin(2 * np.pi * 24 * tt))
    x += np.sin(2 * np.pi * 58 * tt) * 0.10
    return x * 0.55, dur

def sfx_celular():
    dur = 2.2
    tr = Track(dur)
    for f, p in [(1568, 0.1), (1245, 0.28)]:
        tr.note(p, 0.5, f, i_bell, 1.1, detune=1.0)
    return tr.buf[:t(dur)], dur

def sfx_fogos():
    dur = 6.0
    tr = Track(dur)
    r = np.random.default_rng(21)
    for k in range(6):
        p = 0.3 + k * 0.9 + r.random() * 0.4
        wh = np.zeros(t(0.5))
        tt = np.arange(t(0.5)) / SR
        f = 600 + tt * 2600
        wh[:len(f)] = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.hanning(len(f)) * 0.25
        tr.put(wh, p)
        boom = filt(r.standard_normal(t(0.8)), 160, 2) * np.exp(-np.arange(t(0.8)) / SR * 7) * 1.1
        tr.put(boom, p + 0.5)
        crac = filt(r.standard_normal(t(0.5)), 3800, 2, "high") * np.exp(-np.arange(t(0.5)) / SR * 11) * 0.5
        tr.put(crac, p + 0.52)
    x = tr.buf[:t(dur)]
    return reverb(x, 0.25, 1.4), dur

def sfx_flash():
    dur = 1.4
    n = t(dur)
    x = np.zeros(n)
    r = np.random.default_rng(33)
    for k in range(9):
        p = t(0.15 + k * 0.13 + r.random() * 0.04)
        d = t(0.03)
        x[p:p + d] += r.standard_normal(d) * np.hanning(d) * 0.8
    x += filt(np.sin(2 * np.pi * 5200 * np.arange(n) / SR) * 0.08, 5000, 2, "high")
    return x * 0.7, dur

def sfx_vento():
    dur = 7.0
    n = t(dur)
    tt = np.arange(n) / SR
    x = filt(RNG.standard_normal(n), 620, 3)
    x *= 0.55 + 0.45 * np.sin(2 * np.pi * 0.23 * tt + 0.8)
    return x * 0.8, dur

def sfx_crowd():
    return i_crowd(8.0, 1.0, seed=5) * 0.9, 8.0

BEDS = {"tema": bed_tema, "jingle": bed_jingle, "forro": bed_forro, "cotidiano": bed_cotidiano,
        "bueiro": bed_bueiro, "suspense": bed_suspense, "drama": bed_drama, "tensao": bed_tensao,
        "fabinho": bed_fabinho, "comicio": bed_comicio, "final": bed_final}
SFX = {"latido": sfx_latido, "moscas": sfx_moscas, "agua": sfx_agua, "grilos": sfx_grilos,
       "sinos": sfx_sinos, "churrasqueira": sfx_churrasqueira, "ventilador": sfx_ventilador,
       "celular": sfx_celular, "fogos": sfx_fogos, "flash": sfx_flash, "vento": sfx_vento,
       "crowd": sfx_crowd}

def write_wav(caminho, x, sr=SR, alvo_rms=0.10, pico=0.9):
    x = np.asarray(x, dtype=np.float64)
    if np.abs(x).max() < 1e-9:
        x = np.zeros(1024)
    rms = math.sqrt(float(np.mean(x ** 2)))
    if rms > 1e-9:
        x = x * (alvo_rms / rms)
    m = np.abs(x).max()
    if m > pico:
        x = x * (pico / m)
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with open(caminho, "wb") as fp:
        n = len(pcm)
        fp.write(b"RIFF" + struct.pack("<I", 36 + n * 2) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, sr, sr * 2, 2, 16))
        fp.write(b"data" + struct.pack("<I", n * 2) + pcm.tobytes())

def mp3_de(wav_path, mp3_path, kbps=160):
    os.makedirs(os.path.dirname(mp3_path), exist_ok=True)
    ff = os.environ.get("FFMPEG", "/home/user/bin/ffmpeg")
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", wav_path, "-codec:a", "libmp3lame",
                    "-b:a", f"{kbps}k", mp3_path], check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--repo", default=None, help="diretório production/audio do repo p/ cópias mp3")
    ap.add_argument("--so", default="todos", help="nome específico ou 'todos'")
    args = ap.parse_args()
    beds_dir = os.path.join(args.outdir, "beds")
    sfx_dir = os.path.join(args.outdir, "sfx")
    os.makedirs(beds_dir, exist_ok=True)
    os.makedirs(sfx_dir, exist_ok=True)
    manifest = {"beds": {}, "sfx": {}}
    trabalhos = list(BEDS.items()) + list(SFX.items())
    for nome, fn in trabalhos:
        if args.so != "todos" and args.so != nome:
            continue
        x, dur = fn()
        eh_bed = nome in BEDS
        alvo = 0.10 if eh_bed else 0.12
        cam = os.path.join(beds_dir if eh_bed else sfx_dir, f"{nome}.wav")
        write_wav(cam, x, alvo_rms=alvo)
        (manifest["beds"] if eh_bed else manifest["sfx"])[nome] = round(dur, 2)
        print(f"{nome}: {dur:.1f}s pico={np.abs(x).max():.2f} rms={math.sqrt(np.mean(x**2)):.3f}")
        if args.repo:
            sub = "beds" if eh_bed else "sfx"
            mp3_de(cam, os.path.join(args.repo, sub, f"{nome}.mp3"))
    with open(os.path.join(args.outdir, "manifest.json"), "w") as fp:
        json.dump(manifest, fp, indent=1)
    print("OK", args.outdir)

if __name__ == "__main__":
    main()
