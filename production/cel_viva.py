#!/usr/bin/env python3
"""
CelViva — cena viva por SUBSTITUIÇÃO DE DESENHOS (método aprovado no piloto 043).
Substitui a antiga CenaViva (warp de pixels) mantendo a interface:
    compor_frame(t, env_fala, falante_ativo) -> PIL Image 1408x768
Regras de ouro:
  - boca/olhos mudam apenas por patch seco de desenho (re-registrado por SAD);
  - com NARRADOR em off, bocas ficam MUDAS (só piscadas/vida silenciosa);
  - zero deformação gelatinosa; micro-movimento = cortes de desenho + VFX cel.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
W1, H1 = 1408, 768


def abrir(caminho):
    im = Image.open(caminho).convert("RGB")
    if im.size != (W1, H1):
        im = im.resize((W1, H1), Image.LANCZOS)
    return im


def melhor_alinhamento(bg, gg, box, busca=48):
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
    ImageDraw.Draw(m).ellipse([x0, y0, x1, y1], fill=255)
    return m.filter(ImageFilter.GaussianBlur(feather))


def delta_cor(base, gerado, box, dxy, margem=12):
    x0, y0, x1, y1 = box
    dx, dy = dxy
    mb = np.array(base).astype(np.float32)
    mg = np.array(gerado).astype(np.float32)
    ys0, ys1 = max(0, y0 - margem), min(H1, y1 + margem)
    xs0, xs1 = max(0, x0 - margem), min(W1, x1 + margem)
    fb = mb[ys0:ys1, xs0:xs1]
    fg = mg[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    if fb.shape != fg.shape:
        return np.zeros(3, np.float32)
    return (fb.reshape(-1, 3).mean(axis=0) - fg.reshape(-1, 3).mean(axis=0)).astype(np.float32)


def aplicar_patch(base, gerado, box, feather=16, busca=48):
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
    return saida


# ---------------------------------------------------------------------------
# VFX cel (contorno do traço, estilo do desenho)
# ---------------------------------------------------------------------------

def nuvem_cel(canvas, cx, cy, r, alpha, tom=(198, 198, 206)):
    nuvem = Image.new("L", (W1, H1), 0)
    dn = ImageDraw.Draw(nuvem)
    for ox, oy, k in ((0.0, 0.0, 1.0), (-0.75, 0.28, 0.72), (0.72, 0.30, 0.68),
                      (-0.35, -0.55, 0.78), (0.38, -0.58, 0.62), (0.05, 0.55, 0.55)):
        rr = r * k
        dn.ellipse([cx + ox * r - rr, cy + oy * r - rr, cx + ox * r + rr, cy + oy * r + rr], fill=255)
    interior = nuvem.filter(ImageFilter.MinFilter(9))
    contorno = Image.fromarray(np.clip(
        np.array(nuvem).astype(np.int16) - np.array(interior).astype(np.int16), 0, 255).astype(np.uint8))
    camada = Image.new("RGBA", (W1, H1), tom + (255,))
    camada.putalpha(nuvem.point(lambda v: int(v * (alpha / 255.0))))
    out_img = Image.new("RGBA", (W1, H1), (40, 40, 48, 255))
    out_img.putalpha(contorno.point(lambda v: min(255, int(v * 1.5))))
    canvas.alpha_composite(camada)
    canvas.alpha_composite(out_img)


def coluna_fumaca(t, x0, y_base, alt=380, r0=26, r1=58, alpha_max=150, tom=(198, 198, 206), fase0=0.0):
    lay = Image.new("RGBA", (W1, H1), (0, 0, 0, 0))
    for k in range(3):
        fase = (t * 0.24 + 0.33 * k + fase0) % 1.0
        cy = y_base - alt * fase
        cx = x0 + 36 * math.sin(fase * 5.0 + k) + 22 * k
        r = r0 + (r1 - r0) * fase
        alpha = alpha_max * (1.0 - fase) * min(1.0, fase * 6.0)
        if alpha > 6:
            nuvem_cel(lay, cx, cy, r, alpha, tom)
    return lay


def faiscas(draw, t, pontos, raio=14):
    for k, (px, py) in enumerate(pontos):
        fa = (1.0 + math.sin(t * 3.2 + 1.7 * k)) / 2.0
        r = raio * (0.55 + 0.45 * fa)
        alfa = int(90 + 130 * fa)
        draw.line([(px - r, py), (px + r, py)], fill=(255, 245, 180, alfa), width=2)
        draw.line([(px, py - r), (px, py + r)], fill=(255, 245, 180, alfa), width=2)
        draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 250, 220, alfa))


def brilho_varredura(img, t, larg=160, periodo=6.0, forca=42, ang=0.55):
    faixa = Image.new("RGBA", (W1, H1), (0, 0, 0, 0))
    d = ImageDraw.Draw(faixa)
    fase = ((t % periodo) / periodo) * 1.6 - 0.3
    xc = fase * (W1 + 400) - 200
    for i in range(-larg, larg):
        alfa = int(forca * (1.0 - abs(i) / float(larg)) ** 2)
        if alfa <= 2:
            continue
        x = xc + i
        d.line([(x + ang * H1, 0), (x, H1)], fill=(255, 255, 245, alfa), width=2)
    out = img.convert("RGBA")
    out.alpha_composite(faixa)
    return out.convert("RGB")


def cintilar_regiao(img, t, boxes, forca=0.10):
    arr = np.array(img)
    for k, (x0, y0, x1, y1) in enumerate(boxes):
        br = 1.0 + forca * math.sin(t * 5.5 + 1.9 * k)
        reg = arr[y0:y1, x0:x1].astype(np.float32) * br
        arr[y0:y1, x0:x1] = np.clip(reg, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


# ---------------------------------------------------------------------------
# Catálogo + visemas
# ---------------------------------------------------------------------------

CONFIG = {
    "T": {
        "vfx": "titulo",
    },
    "001": {
        "vfx": "rua_noite",   # fumaça de chaminé + cintilação de janelas
    },
    "002": {
        "vfx": "triptico",
    },
    "003": {
        "vfx": "pote",
    },
    "004": {
        "vfx": "gabinete",
    },
    "005": {
        "dur": 14.06,
        "falante": True,
        "boca": {
            "box": (765, 365, 1055, 575),
            "feather": 18,
            "chart": {
                "fechada": "005_m1", "A": "005_m2", "E": "005_m3", "I": "005_m4",
                "O": "005_m5", "U": "005_m6", "RISO": "005_m7",
            },
        },
        "olhos": {
            "box": (775, 175, 1065, 345),
            "feather": 14,
            "blink": "005_blink",
            "squint": "005_squint",
            "periodo": 3.1,
        },
        "poseB": {
            "arq": "005_poseB",
            "janelas": [(0.17, 0.205), (0.60, 0.645)],
        },
        "vfx": "mercearia",
    },
}


def escolher_boca(env, t, ultimo, trocado_em):
    """Visema por envelope (televisão de gaveta) com tempo mínimo de permanência."""
    if env < 0.10:
        alvo = "fechada"
    elif env >= 0.78:
        alvo = "RISO" if int(t * 8) % 3 == 0 else "A"
    elif env >= 0.52:
        alvo = "E" if int(t * 7) % 2 == 0 else "O"
    elif env >= 0.28:
        alvo = "I" if int(t * 6) % 2 == 0 else "U"
    else:
        alvo = "U" if int(t * 5) % 2 == 0 else "fechada"
    if alvo != ultimo and (t - trocado_em) < 0.066:
        return ultimo
    return alvo


class CelViva:
    def __init__(self, cena_id, img_pil):
        self.id = cena_id
        self.img0 = img_pil if img_pil.size == (W1, H1) else img_pil.resize((W1, H1), Image.LANCZOS)
        self.cfg = CONFIG.get(cena_id, {})
        self.cache = {}
        self.desenhos = {}
        self._ultimo_boca = "fechada"
        self._t_boca = -1.0
        pasta = os.path.join(BASE, "cel_p1")
        if os.path.isdir(pasta):
            for nome in os.listdir(pasta):
                if nome.endswith(".png"):
                    self.desenhos[nome[:-4]] = abrir(os.path.join(pasta, nome))

    # ---- patches com cache (alinhados 1x por combinação) ----
    def _compor(self, base, chave_patch, box, feather):
        cache_k = (id(base), chave_patch)
        if cache_k in self.cache:
            return self.cache[cache_k]
        out = aplicar_patch(base, self.desenhos[chave_patch], box, feather=feather)
        self.cache[cache_k] = out
        return out

    def _base_atual(self, t):
        poseB = self.cfg.get("poseB")
        if poseB:
            for (f0, f1) in poseB["janelas"]:
                f = t / self.cfg.get("dur", 1.0)
                if f0 <= f < f1:
                    return self.desenhos.get(poseB["arq"], self.img0), True
        return self.img0, False

    # ---- VFX por cena ----
    def _vfx(self, frame, t):
        modo = self.cfg.get("vfx")
        if modo == "titulo":
            frame = brilho_varredura(frame, t, larg=140, periodo=5.5, forca=46)
            d = ImageDraw.Draw(frame, "RGBA")
            faiscas(d, t, [(365, 235), (700, 190), (1045, 250)], raio=16)
        elif modo == "rua_noite":
            lay = coluna_fumaca(t, 300, 300, alt=300, r0=18, r1=44, alpha_max=120, tom=(170, 175, 190))
            lay.alpha_composite(coluna_fumaca(t, 880, 320, alt=280, r0=16, r1=40, alpha_max=110,
                                              tom=(170, 175, 190), fase0=0.5))
            frame = frame.convert("RGBA")
            frame.alpha_composite(lay)
            frame = frame.convert("RGB")
            frame = cintilar_regiao(frame, t, [(180, 120, 320, 240), (1050, 100, 1180, 220)], forca=0.08)
        elif modo == "triptico":
            lay = coluna_fumaca(t, 980, 520, alt=240, r0=16, r1=38, alpha_max=110, tom=(185, 185, 195))
            frame = frame.convert("RGBA")
            frame.alpha_composite(lay)
            frame = frame.convert("RGB")
            d = ImageDraw.Draw(frame, "RGBA")
            br = (1.0 + math.sin(t * 4.0)) / 2.0
            d.ellipse([395, 255, 445, 315], fill=(255, 200, 120, int(30 + 40 * br)))
            faiscas(d, t, [(420, 285)], raio=10)
        elif modo == "pote":
            lay = coluna_fumaca(t, 700, 330, alt=220, r0=14, r1=34, alpha_max=120, tom=(205, 205, 212))
            frame = frame.convert("RGBA")
            frame.alpha_composite(lay)
            frame = frame.convert("RGB")
            d = ImageDraw.Draw(frame, "RGBA")
            faiscas(d, t, [(640, 355), (775, 350)], raio=13)
        elif modo == "gabinete":
            frame = brilho_varredura(frame, t + 2.0, larg=110, periodo=7.0, forca=34)
            d = ImageDraw.Draw(frame, "RGBA")
            faiscas(d, t, [(980, 175), (300, 250)], raio=12)
        elif modo == "mercearia":
            d = ImageDraw.Draw(frame, "RGBA")
            br = (1.0 + math.sin(t * 3.0)) / 2.0
            d.ellipse([1005, 120, 1085, 200], fill=(255, 230, 160, int(18 + 26 * br)))
            faiscas(d, t, [(1130, 165)], raio=10)
        return frame

    # ---- interface do pipeline ----
    def compor_frame(self, t, env_fala, falante_ativo):
        base, em_poseB = self._base_atual(t)
        frame = base

        cfg_b = self.cfg.get("boca")
        cfg_o = self.cfg.get("olhos")

        # pose de reforço entra crua (a boca desenhada dela já acompanha o gesto)
        if not em_poseB:
            # piscadas / sorriso (patch de olhos)
            if cfg_o and (cfg_o.get("blink") in self.desenhos):
                dur = self.cfg.get("dur", 1.0)
                per = cfg_o.get("periodo", 3.1)
                fase = (t % per) / per
                piscando = fase < 0.045
                sorrindo = falante_ativo and env_fala > 0.62
                if sorrindo and cfg_o.get("squint") in self.desenhos:
                    frame = self._compor(frame, cfg_o["squint"], cfg_o["box"], cfg_o.get("feather", 14))
                elif piscando and cfg_o.get("blink") in self.desenhos:
                    frame = self._compor(frame, cfg_o["blink"], cfg_o["box"], cfg_o.get("feather", 14))

            # boca: SOMENTE quando o falante do bloco está em tela (regra de ouro)
            if cfg_b and falante_ativo:
                alvo = escolher_boca(env_fala, t, self._ultimo_boca, self._t_boca)
                if alvo != self._ultimo_boca:
                    self._t_boca = t
                    self._ultimo_boca = alvo
                chave = cfg_b["chart"].get(alvo, cfg_b["chart"]["fechada"])
                if chave in self.desenhos:
                    frame = self._compor(frame, chave, cfg_b["box"], cfg_b.get("feather", 18))

        frame = self._vfx(frame, t)
        return frame
