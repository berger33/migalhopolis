#!/usr/bin/env python3
"""Mixa o episódio e o teaser: falas + bases musicais com ducking + efeitos.
Entradas: timeline*.json, audio/segments/*.wav, cache beds/sfx
Saídas:   production/audio/ep01_mix.{wav,mp3}, teaser_mix.{wav,mp3}
"""
import json, math, os, subprocess
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROD = os.path.join(RAIZ, "production")
AUD = os.path.join(PROD, "audio")
CACHE = "/home/user/.cache/migalhopolis/audio"
FF = os.environ.get("FFMPEG", "/home/user/bin/ffmpeg")
SR = 44100

BEDS = os.path.join(CACHE, "beds")
SFX = os.path.join(CACHE, "sfx")

def le_wav(caminho):
    import wave
    with wave.open(caminho, "rb") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32768.0
    return x

def normaliza_fala(x, alvo=0.115, pico=0.85):
    rms = math.sqrt(float(np.mean(x ** 2))) + 1e-9
    x = x * (alvo / rms)
    m = np.abs(x).max()
    if m > pico:
        x = x * (pico / m)
    return x

def laca_bed(x, dur):
    """Repete a base até cobrir dur."""
    if len(x) == 0:
        return np.zeros(int(dur * SR))
    reps = int(math.ceil(dur * SR / len(x)))
    return np.tile(x, reps)[:int(dur * SR)]

def envelope_duck(n, falas, ini_janela=0.0):
    """1.0 sem fala, 0.34 sob fala; ataque 0.15s, decaimento 0.5s."""
    fs = 1.0 / SR
    mask = np.zeros(n, dtype=np.float32)
    for f in falas:
        a = int((f["ini"] - 0.12 - ini_janela) / fs)
        b = int((f["fim"] + 0.15 - ini_janela) / fs)
        a = max(a, 0); b = min(b, n)
        if b > a:
            mask[a:b] = 1.0
    suave = np.zeros(n, dtype=np.float32)
    alfa_a = math.exp(-1 / (0.15 * SR))
    alfa_r = math.exp(-1 / (0.50 * SR))
    atual = 0.0
    # percurso por blocos para velocidade
    passo = SR
    for i0 in range(0, n, passo):
        i1 = min(i0 + passo, n)
        m = mask[i0:i1]
        out = np.empty(i1 - i0, dtype=np.float32)
        for j, v in enumerate(m):
            alvo = v
            coef = alfa_a if alvo < atual else alfa_r
            atual = coef * atual + (1 - coef) * alvo
            out[j] = atual
        suave[i0:i1] = out
    return 1.0 - 0.66 * suave  # piso 0.34

def fade(x, din=0.8, dout=0.8):
    n = len(x)
    a, b = int(din * SR), int(dout * SR)
    if a > 0 and n > a:
        x[:a] *= np.linspace(0, 1, a) ** 1.5
    if b > 0 and n > b:
        x[n - b:] *= np.linspace(1, 0, b) ** 1.5
    return x

def mixa(tl_arq, saida_base, bed_extra=("tema", 0, None), bed_final=("final", None, None)):
    tl = json.load(open(tl_arq, encoding="utf-8"))
    dur = tl["dur"]
    n = int(dur * SR) + SR
    mix = np.zeros(n, dtype=np.float64)
    falas = tl["falas"]

    # 1) falas
    for f in falas:
        seg = le_wav(os.path.join(AUD, "segments", f"{f['id']}.wav"))
        seg = normaliza_fala(seg)
        i0 = int(f["ini"] * SR)
        i1 = min(i0 + len(seg), n)
        if i1 > i0:
            mix[i0:i1] += seg[:i1 - i0]

    # 2) efeitos (0.25s antes da fala, ganho 0.38)
    for f in falas:
        for sfx in f.get("sfx", []):
            cam = os.path.join(SFX, f"{sfx}.wav")
            if not os.path.exists(cam):
                continue
            s = le_wav(cam) * 0.38
            i0 = max(int((f["ini"] - 0.25) * SR), 0)
            i1 = min(i0 + len(s), n)
            if i1 > i0:
                mix[i0:i1] += s[:i1 - i0]

    # 3) bases por cena com ducking
    duck = envelope_duck(n, falas)
    cenas = tl["cenas"]
    ct = tl["cartao_titulo"]
    cfi = tl["cartao_final_ini"]
    janelas = []
    janelas.append((0.0, ct, bed_extra[0], bed_extra[1] if bed_extra[1] else 1.35))
    for i, c in enumerate(cenas):
        janelas.append((max(c["ini"] - 0.45, 0), min(c["fim"] + 0.45, dur), c["bed"], c["gain"]))
    janelas.append((cfi, dur, bed_final[0], 1.3))
    for (a, b, bed, ganho) in janelas:
        cam = os.path.join(BEDS, f"{bed}.wav")
        if not os.path.exists(cam) or b - a < 0.3:
            continue
        bedx = le_wav(cam)
        pedaco = laca_bed(bedx, b - a) * ganho
        pedaco = fade(pedaco.copy(), 0.8, 0.9)
        i0 = int(a * SR)
        i1 = min(i0 + len(pedaco), n)
        if i1 > i0:
            mix[i0:i1] += pedaco[:i1 - i0] * duck[i0:i1]

    # 4) master
    m = np.abs(mix).max()
    if m > 0:
        mix *= 0.88 / m
    mix = np.tanh(mix * 1.1) / math.tanh(1.1)
    mix = mix[:int(dur * SR)]

    import wave
    wav_out = os.path.join(AUD, f"{saida_base}.wav")
    with wave.open(wav_out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
    mp3_out = os.path.join(AUD, f"{saida_base}.mp3")
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", wav_out, "-codec:a", "libmp3lame",
                    "-b:a", "192k", mp3_out], check=True)
    rms = math.sqrt(float(np.mean(mix ** 2)))
    print(f"{saida_base}: {dur:.1f}s ({dur/60:.2f} min) pico={np.abs(mix).max():.2f} rms={rms:.3f} -> {mp3_out}")

def main():
    mixa(os.path.join(PROD, "timeline.json"), "ep01_mix")
    mixa(os.path.join(PROD, "timeline_teaser.json"), "teaser_mix",
         bed_extra=("tema", 1.2, None), bed_final=("tema", None, None))

if __name__ == "__main__":
    main()
