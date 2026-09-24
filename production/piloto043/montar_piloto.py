#!/usr/bin/env python3
"""
Montador do animation test — bloco 043 ("De quê?").
Método cel por substituição de desenhos (padrão TV):
  - patch seco: só boca/olhos mudam (pixels do desenho gerado, re-registrados por SAD)
  - pose-a-pose com cortes secos; nada de warp/zoom gelatinoso
  - micro-movimento on 2s + fumaça cel + dolly suave + shake de impacto
Frames intermediários em /tmp (fora do workspace, para não estourar o teto de artefatos).
"""
import glob
import math
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
SRC = os.path.join(ROOT, "imagens", "043.jpg")
W1, H1 = 1408, 768
FPS = 24
DUR = 5.0
N_FRAMES = int(DUR * FPS)
FRAMES_DIR = "/tmp/mh/frames043"

BOX_BOCA = (528, 408, 932, 592)
BOX_OLHOS = (485, 232, 948, 418)


def abrir_desenho(caminho):
    im = Image.open(caminho).convert("RGB")
    if im.size != (W1, H1):
        im = im.resize((W1, H1), Image.LANCZOS)
    return im


def melhor_alinhamento(bg, gg, box, busca=22):
    bg2, gg2 = bg[::2, ::2], gg[::2, ::2]
    x0, y0, x1, y1 = box[0] // 2, box[1] // 2, box[2] // 2, box[3] // 2
    alvo = bg2[y0:y1, x0:x1].astype(np.float32)
    h, w = alvo.shape
    melhor, arg = None, (0, 0)
    b2 = busca // 2 + 1
    for dy in range(-b2, b2 + 1):
        for dx in range(-b2, b2 + 1):
            ys, xs = y0 + dy, x0 + dx
            if ys < 0 or xs < 0 or ys + h > gg2.shape[0] or xs + w > gg2.shape[1]:
                continue
            erro = np.abs(gg2[ys:ys + h, xs:xs + w].astype(np.float32) - alvo).mean()
            if melhor is None or erro < melhor:
                melhor, arg = erro, (dx * 2, dy * 2)
    return arg, melhor


def mascara_feather(box, feather=16):
    x0, y0, x1, y1 = box
    m = Image.new("L", (W1, H1), 0)
    d = ImageDraw.Draw(m)
    d.ellipse([x0, y0, x1, y1], fill=255)
    return m.filter(ImageFilter.GaussianBlur(feather))


def delta_cor(base, gerado, box, dxy, margem=12):
    x0, y0, x1, y1 = box
    dx, dy = dxy
    mb = np.array(base).astype(np.float32)
    mg = np.array(gerado).astype(np.float32)
    ys0, ys1 = max(0, y0 - margem), min(H1, y1 + margem)
    xs0, xs1 = max(0, x0 - margem), min(W1, x1 + margem)
    faixa_b = mb[ys0:ys1, xs0:xs1]
    faixa_g = mg[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    if faixa_b.shape != faixa_g.shape:
        return np.zeros(3, np.float32)
    return (faixa_b.reshape(-1, 3).mean(axis=0) - faixa_g.reshape(-1, 3).mean(axis=0)).astype(np.float32)


def aplicar_patch(base, gerado, box, feather=16, busca=22):
    bg = np.array(base.convert("L"))
    gg = np.array(gerado.convert("L"))
    (dx, dy), erro = melhor_alinhamento(bg, gg, box, busca)
    x0, y0, x1, y1 = box
    patch = np.array(gerado.crop((x0 + dx, y0 + dy, x1 + dx, y1 + dy))).astype(np.float32)
    dc = delta_cor(base, gerado, box, (dx, dy))
    patch = np.clip(patch + dc, 0, 255).astype(np.uint8)
    saida = base.copy()
    mask = mascara_feather(box, feather).crop(box)
    saida.paste(Image.fromarray(patch), (x0, y0), mask)
    return saida, (dx, dy, round(float(erro), 1))


def desenhar_fumaca(canvas, cx, cy, r, alpha):
    nuvem = Image.new("L", (W1, H1), 0)
    dn = ImageDraw.Draw(nuvem)
    lobos = [(0.0, 0.0, 1.0), (-0.75, 0.28, 0.72), (0.72, 0.30, 0.68),
             (-0.35, -0.55, 0.78), (0.38, -0.58, 0.62), (0.05, 0.55, 0.55)]
    for ox, oy, k in lobos:
        rr = r * k
        dn.ellipse([cx + ox * r - rr, cy + oy * r - rr, cx + ox * r + rr, cy + oy * r + rr], fill=255)
    interior = nuvem.filter(ImageFilter.MinFilter(9))
    contorno = Image.fromarray(np.clip(
        np.array(nuvem).astype(np.int16) - np.array(interior).astype(np.int16), 0, 255).astype(np.uint8))
    camada = Image.new("RGBA", (W1, H1), (198, 198, 206, 255))
    camada.putalpha(nuvem.point(lambda v: int(v * (alpha / 255.0))))
    out_img = Image.new("RGBA", (W1, H1), (40, 40, 48, 255))
    out_img.putalpha(contorno.point(lambda v: min(255, int(v * 1.5))))
    canvas.alpha_composite(camada)
    canvas.alpha_composite(out_img)


def camada_fumaca(t):
    lay = Image.new("RGBA", (W1, H1), (0, 0, 0, 0))
    for k in range(3):
        fase = (t * 0.24 + 0.33 * k) % 1.0
        cy = 640 - 380 * fase
        cx = 300 + 40 * math.sin(fase * 5.0 + k) + 26 * k
        r = 26 + 52 * fase
        alpha = 150 * (1.0 - fase) * min(1.0, fase * 6.0)
        if alpha > 6:
            desenhar_fumaca(lay, cx, cy, r, alpha)
    return lay


def montar_audio(saida_wav):
    sr = 44100
    n = int(DUR * sr)
    mix = np.zeros(n, np.float32)
    vozes = sorted(glob.glob(os.path.join(ROOT, "audio", "043_*.mp3")))
    if vozes:
        cmd = ["ffmpeg", "-v", "error", "-i", vozes[0], "-f", "s16le", "-acodec", "pcm_s16le",
               "-ar", str(sr), "-ac", "1", "-"]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        voz = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
        ini = int(2.20 * sr)
        fim = min(n, ini + len(voz))
        if fim > ini:
            mix[ini:fim] += voz[:fim - ini] * 1.05
    rng = np.random.default_rng(7)
    tt = np.arange(int(0.10 * sr)) / sr
    clack = (rng.standard_normal(len(tt)) * np.exp(-tt * 90.0) * 0.30).astype(np.float32)
    clack += (np.sin(2 * math.pi * 2400 * tt) * np.exp(-tt * 120.0) * 0.25).astype(np.float32)
    i0 = int(2.16 * sr)
    mix[i0:i0 + len(clack)] += clack
    tt2 = np.arange(int(0.45 * sr)) / sr
    thud = (np.sin(2 * math.pi * 72 * tt2) * np.exp(-tt2 * 9.0) * 0.34).astype(np.float32)
    i1 = int(2.24 * sr)
    mix[i1:i1 + len(thud)] += thud
    pico = np.max(np.abs(mix)) or 1.0
    if pico > 0.89:
        mix *= 0.89 / pico
    dados = np.clip(mix * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(saida_wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(dados.tobytes())


def carregar_catalogo():
    base_a = abrir_desenho(SRC)
    chaves = ["A", "A_m1", "A_m2", "A_m3", "A_m4", "A_m5", "A_blink", "A_blinkhalf", "A_glare",
              "B", "B_m1", "B_m2", "B_m3", "B_m4", "C", "C_m1", "C_m2", "C_blink"]
    cat = {k: base_a for k in chaves}
    carregados = set()
    for nome in sorted(os.listdir(BASE_DIR)):
        if nome.endswith(".png") and nome[0] in "ABC" and "_" in nome:
            chave = nome[:-4]
            if chave == "B_base":
                chave = "B"
            if chave in cat:
                cat[chave] = abrir_desenho(os.path.join(BASE_DIR, nome))
                carregados.add(chave)
    faltantes = []
    for chave, fb in (("B", "A"), ("B_m2", "B_m1"), ("B_m3", "B_m1"), ("B_m4", "B"),
                      ("C", "A"), ("C_m1", "A_m1"), ("C_m2", "A"), ("C_blink", "A_blink")):
        if chave not in carregados:
            cat[chave] = cat[fb]
            faltantes.append(f"{chave}→{fb}")
    return cat, faltantes


TIMELINE = [
    (0, 13, "A", None, None),
    (13, 16, "A", None, "A_blink"),
    (16, 30, "A", None, None),
    (30, 35, "A", None, "A_blinkhalf"),
    (35, 49, "A", None, None),
    (49, 52, "A", None, "A_glare"),
    (52, 54, "B", "A", None),
    (54, 58, "B", "B_m1", None),
    (58, 65, "B", "A_m3", None),
    (65, 71, "B", "A_m2", None),
    (71, 76, "B", "A", None),
    (76, 85, "B", None, None),
    (85, 90, "C", None, None),
    (90, 93, "C", None, "C_blink"),
    (93, 102, "C", "A_m1", None),
    (102, 108, "C", "A_m5", None),
    (108, 120, "C", None, None),
]


def composicao_desenho(cat, cache, pose, boca, olhos):
    chave = f"{pose}|{boca}|{olhos}"
    if chave in cache:
        return cache[chave][0]
    img = cat[pose]
    regs = []
    if boca is not None and cat[boca] is not cat[pose]:
        img, reg = aplicar_patch(img, cat[boca], BOX_BOCA)
        regs.append((boca, reg))
    if olhos is not None and cat[olhos] is not cat[pose]:
        img, reg = aplicar_patch(img, cat[olhos], BOX_OLHOS)
        regs.append((olhos, reg))
    cache[chave] = (img, regs)
    return img


def main():
    cat, faltantes = carregar_catalogo()
    if faltantes:
        print("DESENHOS PENDENTES (fallback honesto):", ", ".join(faltantes))
    cache = {}
    for _, _, p, b, o in TIMELINE:
        composicao_desenho(cat, cache, p, b, o)
    print("Registro dos patches (dx, dy, sad):")
    for chave in sorted(cache):
        for nome, reg in cache[chave][1]:
            print(f"  {chave:16s} ← {nome:12s} {reg}")

    os.makedirs(FRAMES_DIR, exist_ok=True)
    for f in range(N_FRAMES):
        t = f / float(FPS)
        pose, boca, olhos = "A", None, None
        for (f0, f1, p, b, o) in TIMELINE:
            if f0 <= f < f1:
                pose, boca, olhos = p, b, o
                break
        comp = composicao_desenho(cat, cache, pose, boca, olhos).convert("RGBA")
        comp.alpha_composite(camada_fumaca(t))
        comp = comp.convert("RGB")
        bob = -1 if (f // 2) % 2 else 0
        shake_x = 0
        if 58 <= f < 62:
            shake_x = (7, -6, 5, -3)[f - 58]
            bob += (4, -4, 3, -2)[f - 58]
        prog = f / float(max(1, N_FRAMES - 1))
        e = prog * prog * (3 - 2 * prog)
        s = 1.0 + 0.035 * e
        cw, ch = int(W1 / s), int(H1 / s)
        cx, cy = (W1 - cw) // 2 + shake_x, (H1 - ch) // 2 + bob
        cx = max(0, min(W1 - cw, cx))
        cy = max(0, min(H1 - ch, cy))
        quadro = comp.crop((cx, cy, cx + cw, cy + ch)).resize((W1, H1), Image.LANCZOS)
        q1920 = quadro.resize((1975, 1080), Image.LANCZOS).crop((27, 0, 27 + 1920, 1080))
        q1920.save(os.path.join(FRAMES_DIR, f"f{f:04d}.jpg"), quality=94)

    wav = "/tmp/mh/audio043.wav"
    montar_audio(wav)
    mp4 = os.path.join(ROOT, "video", "piloto_043_animtest.mp4")
    cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS),
           "-i", os.path.join(FRAMES_DIR, "f%04d.jpg"), "-i", wav,
           "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", mp4]
    subprocess.run(cmd, check=True)
    print("MP4:", mp4)

    tempos = [0.3, 0.6, 1.4, 2.1, 2.5, 2.9, 3.9, 4.6]
    rotulos = ["0.3 nojo", "0.6 piscada", "1.4 meio", "2.1 antecipa",
               "2.5 QUE?!", "2.9 careta", "3.9 hmph", "4.6 fim"]
    grade = Image.new("RGB", (1920, 540), (18, 18, 22))
    for i, (tt, rot) in enumerate(zip(tempos, rotulos)):
        fi = min(N_FRAMES - 1, int(tt * FPS))
        quad = Image.open(os.path.join(FRAMES_DIR, f"f{fi:04d}.jpg")).resize((480, 270), Image.LANCZOS)
        d = ImageDraw.Draw(quad)
        d.rectangle([0, 0, 480, 30], fill=(0, 0, 0))
        d.text((8, 6), f"{rot} ({tt:.1f}s)", fill=(255, 220, 120))
        grade.paste(quad, ((i % 4) * 480, (i // 4) * 270))
    qc = os.path.join(ROOT, "video", "qc_piloto_043.png")
    grade.save(qc)
    print("QC:", qc)


if __name__ == "__main__":
    main()
