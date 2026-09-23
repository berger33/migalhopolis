#!/usr/bin/env python3
"""
MIGALHÓPOLIS — renderizador de partes (10 partes, T01E01 - O Pote).

Uso:
    python3 render.py --part 1          # título + blocos 1-5  -> video/parte_01.mp4
    python3 render.py --part 2          # blocos 6-13          -> video/parte_02.mp4

Recursos (especificação da Parte 1, replicável nas demais):
  * Ken Burns por bloco (zoom_in/zoom_out/pan_left/pan_right/static_push)
  * crossfade suave (vídeo linear + áudio equal-power) nas viras
  * lip sync: boca desenhada pelo envelope de áudio (pausa -> arte original)
  * legendas ASS coloridas por personagem + cartela de título
  * respiração sutil de câmera, pulso de fala, tremor de impacto em punchlines
"""
import argparse
import json
import math
import os
import subprocess
import sys
import wave
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import imageio_ffmpeg

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1920, 1080, 30
XF = 0.40                      # duração do crossfade (s)
XF_FRAMES = int(round(XF * FPS))
SR = 44100
PUNCH_BLOCOS = {31, 43, 54, 79}          # punchlines com tremor de impacto
COR_FORÇADA = {"CIDA": (0xFF, 0xE0, 0x80)}   # Cida em amarelo (decisão de produto)
FONTE_DIR = "/usr/share/fonts/truetype/dejavu"
FONTE_BOLD = os.path.join(FONTE_DIR, "DejaVuSans-Bold.ttf")

# Coordenadas de boca (frações da largura/altura da imagem ORIGINAL).
# w = largura da boca em fração da largura da imagem.
BOCAS = {
    "001": [],                                            # aérea: sem rosto
    "002": [  # montagem: churrasco / boleto / bueiro
        (0.283, 0.521, 0.026),
        (0.578, 0.540, 0.040),
        (0.849, 0.599, 0.030),
    ],
    "003": [(0.638, 0.408, 0.035)],                       # Caramelo dormindo no pote
    "004": [(0.483, 0.474, 0.052)],                       # Caramelo close "instituição"
    "005": [(0.618, 0.375, 0.040)],                       # Cida gritando na porta
    "T":   [],
}

PARTES = {
    # part: (ids de bloco na ordem; "T" = cartela de título)
    1: ["T", 1, 2, 3, 4, 5],
    2: [6, 7, 8, 9, 10, 11, 12, 13],
}


# ---------------------------------------------------------------- utilidades
def ff():
    return imageio_ffmpeg.get_ffmpeg_exe()


def carregar_blocos():
    with open(os.path.join(ROOT, "roteiro", "blocos.json"), encoding="utf-8") as f:
        dados = json.load(f)
    return {b["id"]: b for b in dados["blocos"]}, dados


def decodificar_audio(caminho):
    """mp3 -> float32 mono SR, com trim de silêncio final/inicial."""
    cmd = [ff(), "-v", "error", "-i", caminho,
           "-f", "f32le", "-acodec", "pcm_f32le", "-ac", "1", "-ar", str(SR), "pipe:1"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).copy()
    if x.size == 0:
        return x
    # trim de silêncio (limiar -40 dB), preserva 80 ms de cauda
    idx = np.where(np.abs(x) > 0.01)[0]
    if idx.size:
        x = x[: min(len(x), idx[-1] + int(0.08 * SR))]
        ini = idx[0]
        if ini > int(0.15 * SR):
            x = x[ini - int(0.05 * SR):]
    return x


def envelope(x, n_quadros):
    """Envelope de fala por quadro (0..1), ataque rápido / queda lenta."""
    if x.size == 0:
        return np.zeros(n_quadros, dtype=np.float32)
    hop = SR // FPS
    need = n_quadros * hop
    if x.size < need:
        x = np.pad(x, (0, need - x.size))
    rms = np.sqrt(np.mean(x[:need].reshape(n_quadros, hop) ** 2, axis=1))
    amp = rms / (np.percentile(rms, 97) + 1e-9)
    bruto = np.clip((amp - 0.10) / (0.42 - 0.10), 0, 1)
    bruto = bruto * bruto * (3 - 2 * bruto)           # smoothstep
    env = np.zeros_like(bruto)
    s = 0.0
    for i, b in enumerate(bruto):
        a = 0.55 if b > s else 0.22                    # ataque / release
        s = a * b + (1 - a) * s
        env[i] = s
    return env


def ease(p):
    p = max(0.0, min(1.0, p))
    return p * p * (3 - 2 * p)


def cor_ass(rgb):
    r, g, b = rgb
    return f"&H00{b:02X}{g:02X}{r:02X}"


def cor_do_personagem(nome, cores_json):
    if nome in COR_FORÇADA:
        return COR_FORÇADA[nome]
    hexv = cores_json.get(nome, "&H00FFFFFF").replace("&H00", "")
    b, g, r = int(hexv[0:2], 16), int(hexv[2:4], 16), int(hexv[4:6], 16)
    return (r, g, b)


def quebrar_texto(draw, texto, fonte, max_w):
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if draw.textlength(teste, font=fonte) <= max_w:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


# ---------------------------------------------------------------- segmentos
class Segmento:
    def __init__(self, bloco, dados, idx_audio, partes_ids):
        self.bloco = bloco
        self.id = bloco["id"]
        self.eh_titulo = bloco["tipo"] in ("titulo", "creditos")
        self.movimento = bloco.get("movimento", "zoom_in")
        self.chave = f"{self.id:03d}" if isinstance(self.id, int) else "T"
        self.personagem = bloco.get("personagem", "")
        self.texto = bloco.get("texto", "")
        self.imagem = Image.open(
            os.path.join(ROOT, "imagens",
                         "T_titulo.jpg" if self.id == "T" else
                         "C_creditos.jpg" if self.id == "C" else
                         f"{self.id:03d}.jpg")
        ).convert("RGB")
        self.iw, self.ih = self.imagem.size
        self.bocas = BOCAS.get(self.chave if not isinstance(self.id, int)
                               else f"{self.id:03d}", [])

        if self.eh_titulo:
            self.audio = np.zeros(0, dtype=np.float32)
            self.dur = float(bloco.get("duracao", 4.0))
        else:
            self.audio = decodificar_audio(
                os.path.join(ROOT, "audio", f"{idx_audio:03d}_{_slug(bloco['personagem'])}.mp3"))
            self.dur = self.audio.size / SR
        self.quadros = max(1, int(round(self.dur * FPS)))
        self.env = envelope(self.audio, self.quadros)
        self.start = 0.0                                   # preenchido na linha do tempo
        self.qstart = 0

    def compor(self, q_local, t_global):
        """Quadro RGB 1920x1080 deste segmento no quadro local q_local."""
        p = q_local / max(1, self.quadros - 1)
        pe = ease(p)
        z, cx, cy = self._ken_burns(p, pe)

        # respiração sutil + pulso de fala
        fase = (self.qstart % 97) / 97.0 * 2 * math.pi
        z *= 1 + 0.0035 * math.sin(2 * math.pi * 0.19 * t_global + fase)
        e = self.env[q_local] if q_local < len(self.env) else 0.0
        z *= 1 + 0.007 * e
        # punchline: tremor de impacto decaindo
        if isinstance(self.id, int) and self.id in PUNCH_BLOCOS and q_local < 14:
            d = math.exp(-q_local / 4.0) * 9.0
            cx += d * math.sin(q_local * 2.9)
            cy += d * math.cos(q_local * 3.7)

        vw = self.iw / z
        vh = vw * H / W
        if vh > self.ih:
            vh = self.ih
            vw = vh * W / H
        vw = min(vw, self.iw)
        x0 = min(max(cx * self.iw - vw / 2, 0), self.iw - vw)
        y0 = min(max(cy * self.ih - vh / 2, 0), self.ih - vh)

        crop = self.imagem.crop((int(x0), int(y0),
                                 int(x0 + vw), int(y0 + vh)))
        quadro = crop.resize((W, H), Image.Resampling.LANCZOS)

        if self.bocas and e > 0.10:
            self._desenhar_bocas(quadro, x0, y0, vw, vh, e)
        if self.eh_titulo:
            self._cartela(quadro, t_global)
        return quadro

    def _ken_burns(self, p, pe):
        m = self.movimento
        if m == "zoom_in":
            return 1.00 + 0.14 * pe, 0.50, 0.46 + 0.04 * pe
        if m == "zoom_out":
            return 1.17 - 0.15 * pe, 0.50, 0.52 - 0.04 * pe
        if m == "pan_right":
            z = 1.07
            return z, 0.10 + 0.80 * pe, 0.50
        if m == "pan_left":
            z = 1.07
            return z, 0.90 - 0.80 * pe, 0.50
        if m == "static_push":
            return 1.02 + 0.05 * p, 0.53, 0.50      # push lento, centrado na Cida
        return 1.03, 0.5, 0.5

    def _desenhar_bocas(self, quadro, x0, y0, vw, vh, env):
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for (u, v, wf) in self.bocas:
            px = (u * self.iw - x0) / vw * W
            py = (v * self.ih - y0) / vh * H
            wp = wf * self.iw / vw * W
            hp = wp * (0.16 + 0.62 * env)
            if px < -wp or px > W + wp or py < -hp or py > H + hp:
                continue
            contorno = max(2, int(wp * 0.075))
            x0m, x1m = px - wp / 2, px + wp / 2
            y0m, y1m = py - hp / 2, py + hp / 2
            d.ellipse([x0m, y0m, x1m, y1m], fill=(38, 16, 13, 255),
                      outline=(18, 12, 10, 255), width=contorno)
            if hp > wp * 0.30:                       # dentes superiores
                th = hp * 0.24
                d.rounded_rectangle(
                    [x0m + wp * 0.14, y0m + hp * 0.10,
                     x1m - wp * 0.14, y0m + hp * 0.10 + th],
                    radius=th * 0.45, fill=(242, 236, 216, 255))
            if hp > wp * 0.42:                       # língua
                d.ellipse([px - wp * 0.32, y1m - hp * 0.40,
                           px + wp * 0.32, y1m - hp * 0.04],
                          fill=(206, 92, 101, 255))
        quadro.alpha_composite(ov) if quadro.mode == "RGBA" else quadro.paste(
            Image.alpha_composite(quadro.convert("RGBA"), ov).convert("RGB"))

    def _cartela(self, quadro, t_global):
        f_tit = ImageFont.truetype(FONTE_BOLD, 148)
        f_sub = ImageFont.truetype(FONTE_BOLD, 56)
        texto = "MIGALHÓPOLIS"
        sub = "T01E01 - O Pote"
        cx = int(W * 0.36)
        y = int(H * 0.36)
        # fade in/out da cartela (overlay RGBA composto sobre o quadro)
        a = min(1.0, t_global / 0.5, max(0.0, (self.dur - t_global) / 0.5))
        if a <= 0:
            return
        al = int(255 * a)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        larg = d.textlength(texto, font=f_tit)
        d.text((cx - larg / 2, y), texto, font=f_tit,
               fill=(31, 122, 63, al),
               stroke_width=10, stroke_fill=(242, 193, 78, al))
        larg2 = d.textlength(sub, font=f_sub)
        d.text((cx - larg2 / 2, y + 185), sub, font=f_sub,
               fill=(255, 246, 224, al),
               stroke_width=5, stroke_fill=(20, 14, 10, al))
        comp = Image.alpha_composite(quadro.convert("RGBA"), ov).convert("RGB")
        quadro.paste(comp)


def _slug(personagem):
    return personagem.lower()


def _indice_audio(bloco):
    """ bloco id 1..79 -> arquivo audio/NNN_personagem.mp3 (mesma numeração)."""
    return int(bloco["id"])


# ---------------------------------------------------------------- legenda ASS
def gerar_ass(segmentos, caminho, cores_json):
    cab = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""
    usados = {}
    for s in segmentos:
        if not s.eh_titulo and s.personagem:
            usados[s.personagem] = cor_do_personagem(s.personagem, cores_json)
    linhas = [cab]
    for nome, rgb in usados.items():
        linhas.append(
            f"Style: {nome},DejaVu Sans,58,{cor_ass(rgb)},&H00FFFFFF,"
            "&H00101010,&H96000000,-1,0,0,0,100,100,0,0,1,3.2,1.6,2,70,70,64,1\n")
    linhas.append("\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

    # quebra de textos (mesma métrica do render)
    tmp = Image.new("RGB", (10, 10))
    dd = ImageDraw.Draw(tmp)
    fonte = ImageFont.truetype(FONTE_BOLD, 58)
    for k, s in enumerate(segmentos):
        if s.eh_titulo or not s.texto:
            continue
        linhas_txt = quebrar_texto(dd, s.texto, fonte, int(W * 0.86))
        texto = "\\N".join(linhas_txt)
        # troca de legenda no MEIO do crossfade: sem sobreposição de eventos
        meio_vira = XF / 2
        ini = 0.08 if k == 0 else s.start + meio_vira
        fim = (segmentos[k + 1].start + meio_vira
               if k < len(segmentos) - 1 else s.start + s.dur - 0.06)
        linhas.append(
            f"Dialogue: 0,{_ass_time(ini)},{_ass_time(fim)},{s.personagem},,0,0,0,,{texto}\n")
    with open(caminho, "w", encoding="utf-8") as f:
        f.writelines(linhas)


def _ass_time(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


# ---------------------------------------------------------------- montagem QC
def montagem_qc(segmentos, momentos, caminho):
    """2 linhas: FALANDO (env alto) vs PAUSA (env baixo), com barra identificadora."""
    cel = (640, 360)
    grade = Image.new("RGB", (cel[0] * 4, cel[1] * 2 + 56), (12, 12, 12))
    d = ImageDraw.Draw(grade)
    f = ImageFont.truetype(FONTE_BOLD, 26)
    f2 = ImageFont.truetype(FONTE_BOLD, 22)
    col = 0
    for rotulo, cor, itens in momentos:
        for (seg, q) in itens:
            if col >= 4:
                col = 0
            quadro = seg.compor(q, seg.start + q / FPS).resize(cel, Image.Resampling.LANCZOS)
            faixa_y = (0 if rotulo == "FALANDO" else cel[1] + 28)
            grade.paste(quadro, (col * cel[0], faixa_y + 28))
            dd = ImageDraw.Draw(grade)
            dd.rectangle([col * cel[0], faixa_y, col * cel[0] + cel[0], faixa_y + 28], fill=cor)
            dd.text((col * cel[0] + 10, faixa_y + 2),
                    f"{rotulo} · bloco {seg.id} · {q / FPS:.1f}s",
                    font=f2, fill=(15, 15, 15))
            col += 1
        col = 0
    grade.save(caminho)
    print(f"[qc] montagem -> {caminho}")


# ---------------------------------------------------------------- render main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, default=1)
    args = ap.parse_args()

    if args.part not in PARTES:
        sys.exit(f"parte {args.part} indefinida em PARTES")
    ids = PARTES[args.part]
    mapa, dados = carregar_blocos()
    segmentos = [Segmento(mapa[i], dados, _indice_audio(mapa[i]) if i != "T" else 0, ids)
                 for i in ids]

    # linha do tempo (crossfade de XF entre segmentos)
    t = 0.0
    for s in segmentos:
        s.start = t
        s.qstart = int(round(t * FPS))
        t += s.dur - (XF if s is not segmentos[-1] else 0.0)
    total = segmentos[-1].start + segmentos[-1].dur
    n_quadros = int(round(total * FPS))
    print(f"[tempo] segmentos: " +
          ", ".join(f"{s.id}@{s.start:.2f}s({s.dur:.2f}s)" for s in segmentos))
    print(f"[tempo] total = {total:.2f}s = {n_quadros} quadros")

    # ---- áudio master (equal-power nas viras)
    master = np.zeros(int(math.ceil(total * SR)) + SR, dtype=np.float32)
    for k, s in enumerate(segmentos):
        if s.audio.size == 0:
            continue
        i0 = int(round(s.start * SR))
        seg = s.audio.astype(np.float32).copy()
        xf_n = int(XF * SR)
        if k > 0 and seg.size > xf_n:                       # fade-in equal-power
            ramp = np.sqrt(np.linspace(0, 1, xf_n))
            seg[:xf_n] *= ramp
        if k < len(segmentos) - 1 and seg.size > xf_n:      # fade-out equal-power
            ramp = np.sqrt(np.linspace(1, 0, xf_n))
            seg[-xf_n:] *= ramp
        master[i0:i0 + seg.size] += seg
    master = master[:int(round(total * SR))]
    stereo = np.stack([master, master], axis=1)
    pcm = np.clip(stereo, -1, 1)
    pcm = (pcm * 32767).astype(np.int16)
    os.makedirs(os.path.join(ROOT, "video", "intermediario"), exist_ok=True)
    wav_path = os.path.join(ROOT, "video", "intermediario", f"parte_{args.part:02d}.wav")
    with wave.open(wav_path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())

    # ---- legenda ASS
    ass_path = os.path.join(ROOT, "legendas", f"parte_{args.part:02d}.ass")
    os.makedirs(os.path.dirname(ass_path), exist_ok=True)
    gerar_ass(segmentos, ass_path, dados["legenda"]["destaque_personagem"])

    # ---- momentos de QC (fala x pausa) por segmento falado
    momentos = {"FALANDO": [], "PAUSA": []}
    for s in segmentos:
        if s.eh_titulo or s.env.size == 0:
            continue
        q_fala = int(np.argmax(s.env))
        if s.env[q_fala] < 0.3:
            continue
        candidatos = np.where(s.env < 0.10)[0]
        q_pausa = int(candidatos[len(candidatos) // 2]) if candidatos.size else 0
        momentos["FALANDO"].append((s, q_fala))
        momentos["PAUSA"].append((s, q_pausa))

    # ---- vídeo: quadros raw -> ffmpeg (com queima de ASS + mux do áudio)
    out = os.path.join(ROOT, "video", f"parte_{args.part:02d}.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    ass_rel = os.path.relpath(ass_path, ROOT)
    cmd = [ff(), "-y", "-v", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-framerate", str(FPS), "-i", "pipe:0",
           "-i", wav_path,
           "-vf", f"subtitles={ass_rel}:fontsdir={FONTE_DIR}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-ac", "2",
           "-movflags", "+faststart", "-shortest", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    cache = {}
    def quadro_de(seg, q_local, t_glob):
        chave = (id(seg), q_local)
        if chave not in cache:
            if len(cache) > 4:
                cache.clear()
            cache[chave] = seg.compor(q_local, t_glob)
        return cache[chave]

    for f in range(n_quadros):
        t_glob = f / FPS
        # segmento ativo + eventuais crossfades
        idx_ativo = max(i for i, s in enumerate(segmentos) if s.start <= t_glob + 1e-6)
        s = segmentos[idx_ativo]
        q = min(int(round((t_glob - s.start) * FPS)), s.quadros - 1)
        quadro = quadro_de(s, q, t_glob)
        # crossfade com o anterior
        if idx_ativo > 0:
            s_prev = segmentos[idx_ativo - 1]
            rel = f - s.qstart                      # 0..XF_FRAMES-1 na virada
            if 0 <= rel < XF_FRAMES:
                a = (rel + 1) / (XF_FRAMES + 1)
                qp = min(int(round((t_glob - s_prev.start) * FPS)),
                         s_prev.quadros - 1)
                quadro_prev = quadro_de(s_prev, qp, t_glob)
                quadro = Image.blend(quadro_prev, quadro, a)
        proc.stdin.write(quadro.tobytes())
        if f % 300 == 0:
            print(f"[render] {f}/{n_quadros} ({100 * f / n_quadros:.0f}%)", flush=True)

    proc.stdin.close()
    ret = proc.wait()
    if ret != 0:
        sys.exit(f"ffmpeg falhou ({ret})")

    qc_path = os.path.join(ROOT, "video", f"qc_parte_{args.part:02d}.png")
    montagem_qc(segmentos,
                [("FALANDO", (140, 225, 140), momentos["FALANDO"]),
                 ("PAUSA", (190, 190, 190), momentos["PAUSA"])],
                qc_path)

    sz = os.path.getsize(out) / 1e6
    print(f"[ok] {out} — {total:.2f}s, {sz:.1f} MB")
    # ffprobe
    info = subprocess.run([ff(), "-i", out], capture_output=True, text=True).stderr
    for linha in info.splitlines():
        if "Duration" in linha or "Stream" in linha:
            print("  " + linha.strip())


if __name__ == "__main__":
    main()
