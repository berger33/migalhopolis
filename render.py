#!/usr/bin/env python3
"""
MIGALHÓPOLIS — Motor de Animação 2D de Curta-Metragem (Estilo Rick and Morty).
T01E01 - O Pote.
Suporta Parte 1 (blocos 1-5) e Parte 2 (blocos 6-13).

Arquitetura:
  - Decomposição em Camadas com Inpainting Difusivo de fundo
  - Recortes articulados (Puppets/Cutouts) com respiração e atuações secundárias
  - Lip Sync anatômico com Jaw Drop ativado EXCLUSIVAMENTE quando o personagem fala
  - Cenários vivos: fumaça, vapor, ventilador girando, lâmpada oscilando, varal, Zzz,
    guindaste com linguiça, esgoto com faíscas de solda, cinejornal vintage 1997 com riscos,
    placa enferrujada, tumbleweed e comício do Pardal com chuva de confetes.
  - Sound design completo: diálogos + camas musicais (beds) + efeitos sonoros (SFX)
  - Transições cinematográficas de curta-metragem (fades in/out) e legendas ASS
"""
import argparse
import json
import math
import os
import subprocess
import sys
import wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import uniform_filter, map_coordinates

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1920, 1080, 30
XF = 0.40                      # Duração do crossfade (s)
XF_FRAMES = int(round(XF * FPS))
SR = 44100
PUNCH_BLOCOS = {31, 43, 54, 79}
COR_FORÇADA = {
    "CIDA": (0xFF, 0xE0, 0x80),       # Amarelo clássico da Cida
    "MARTA": (0xFF, 0xA0, 0xE0),      # Rosa dramático da Marta
    "SEU_JORGE": (0xC0, 0xFF, 0xC0),  # Verde claro do Seu Jorge
}
FONTE_DIR = "/usr/share/fonts/truetype/dejavu"
FONTE_BOLD = os.path.join(FONTE_DIR, "DejaVuSans-Bold.ttf")

# Personagens falantes por bloco que possuem rosto em cena e devem animar boca
FALANTE_EM_TELA = {
    5: "CIDA",        # Dona Cida na porta do mercadinho
    6: "MARTA",       # Dona Marta na igreja
    7: "SEU_JORGE",   # Seu Jorge no bar/praça
    18: "ZECA",
    19: "CARAMELO",
}

# -----------------------------------------------------------------------------
# UTILITÁRIOS MATEMÁTICOS E DE IMAGEM
# -----------------------------------------------------------------------------

def ler_fonte(tamanho):
    try:
        return ImageFont.truetype(FONTE_BOLD, int(tamanho))
    except Exception:
        return ImageFont.load_default()

def criar_mascara_poligono(tamanho, pontos):
    mask = Image.new("L", tamanho, 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon([tuple(p) for p in pontos], fill=255)
    return mask

def inpaint_difusivo(img_rgb, mask_l, dilate=14, iters=45):
    """
    Preenche a área oculta sob um recorte usando difusão pelas bordas.
    Executado apenas 1x na inicialização do plano (bounded ao bbox).
    """
    arr = np.array(img_rgb).astype(np.float32)
    m = np.array(mask_l) > 128
    if not np.any(m):
        return Image.fromarray(arr.astype(np.uint8))
    
    m_dil = uniform_filter(m.astype(np.float32), size=dilate) > 0.01
    
    ys, xs = np.where(m_dil)
    y0, y1 = max(0, ys.min() - 4), min(arr.shape[0], ys.max() + 5)
    x0, x1 = max(0, xs.min() - 4), min(arr.shape[1], xs.max() + 5)
    
    sub_arr = arr[y0:y1, x0:x1]
    sub_m = m_dil[y0:y1, x0:x1]
    
    borda = uniform_filter(sub_m.astype(np.float32), size=5) > 0.05
    borda_conhecida = borda & (~sub_m)
    if np.any(borda_conhecida):
        media = sub_arr[borda_conhecida].mean(axis=0)
    else:
        media = sub_arr.mean(axis=(0, 1))
    
    sub_arr[sub_m] = media
    
    for _ in range(iters):
        for c in range(3):
            blur = uniform_filter(sub_arr[:, :, c], size=7)
            sub_arr[sub_m, c] = blur[sub_m]
            
    arr[y0:y1, x0:x1] = sub_arr
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def deformar_regiao(arr_rgb, box, dx_field, dy_field):
    """
    Aplica campo de deslocamento vetorial via interpolação bilinear map_coordinates.
    """
    x0, y0, x1, y1 = box
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(arr_rgb.shape[1], x1), min(arr_rgb.shape[0], y1)
    if x1 <= x0 or y1 <= y0:
        return arr_rgb
        
    sub = arr_rgb[y0:y1, x0:x1].astype(np.float32)
    sh_y, sh_x = sub.shape[:2]
    
    if dx_field.shape != (sh_y, sh_x):
        dx_sub = dx_field[y0:y1, x0:x1]
        dy_sub = dy_field[y0:y1, x0:x1]
    else:
        dx_sub = dx_field
        dy_sub = dy_field
        
    Y, X = np.mgrid[0:sh_y, 0:sh_x].astype(np.float32)
    coords = [Y + dy_sub, X + dx_sub]
    
    for c in range(3):
        sub[:, :, c] = map_coordinates(sub[:, :, c], coords, order=1, mode='nearest')
        
    arr_rgb[y0:y1, x0:x1] = np.clip(sub, 0, 255).astype(np.uint8)
    return arr_rgb

class RecortePuppet:
    """Camada articulada de personagem com inpainting de fundo e transformações afins."""
    def __init__(self, img_pil, pontos_poly, feather=4, fundo_preparado=None):
        self.w, self.h = img_pil.size
        self.poly = pontos_poly
        xs = [p[0] for p in pontos_poly]
        ys = [p[1] for p in pontos_poly]
        self.box = (max(0, min(xs)-8), max(0, min(ys)-8), min(self.w, max(xs)+8), min(self.h, max(ys)+8))
        
        mask_full = criar_mascara_poligono((self.w, self.h), pontos_poly)
        if feather > 0:
            mask_arr = uniform_filter(np.array(mask_full).astype(np.float32), size=feather*2+1)
            self.mask_full = Image.fromarray(np.clip(mask_arr, 0, 255).astype(np.uint8))
        else:
            self.mask_full = mask_full
            
        self.camada_rgba = img_pil.convert("RGBA")
        self.camada_rgba.putalpha(self.mask_full)
        
        if fundo_preparado is None:
            self.fundo_limpo = inpaint_difusivo(img_pil, mask_full)
        else:
            self.fundo_limpo = fundo_preparado

    def colar(self, destino_pil, dx=0.0, dy=0.0, rot=0.0, scale_y=1.0, pivot=None, camada_override=None):
        camada = camada_override if camada_override is not None else self.camada_rgba
        
        if scale_y != 1.0 and pivot is not None:
            px, py = pivot
            coeffs = (1.0, 0.0, 0.0, 0.0, 1.0 / scale_y, py - (py / scale_y))
            camada = camada.transform(camada.size, Image.AFFINE, coeffs, resample=Image.BICUBIC)
            
        if rot != 0.0:
            piv = pivot if pivot is not None else (self.w // 2, self.h // 2)
            camada = camada.rotate(rot, center=piv, resample=Image.BICUBIC)
            
        if dx != 0.0 or dy != 0.0:
            ox, oy = int(round(dx)), int(round(dy))
            destino_pil.paste(camada, (ox, oy), camada)
        else:
            destino_pil.paste(camada, (0, 0), camada)
        return destino_pil

# -----------------------------------------------------------------------------
# MOTOR DE CENAS VIVAS (CenaViva)
# -----------------------------------------------------------------------------

class CenaViva:
    def __init__(self, cena_id, img_pil):
        self.id = cena_id
        self.img0 = img_pil
        self.w, self.h = img_pil.size
        self.recortes = {}
        self.fundo_limpo = img_pil.copy()
        self._inicializar_rigs()

    def _inicializar_rigs(self):
        if self.id == "002":
            poly_boleto = [(685, 245), (835, 240), (865, 330), (868, 430), (850, 560), (680, 560), (670, 430), (676, 330)]
            poly_rezando = [(1105, 315), (1245, 315), (1265, 420), (1305, 470), (1308, 622), (1100, 622), (1088, 470), (1095, 400)]
            mask1 = criar_mascara_poligono((self.w, self.h), poly_boleto)
            fundo1 = inpaint_difusivo(self.img0, mask1)
            mask2 = criar_mascara_poligono((self.w, self.h), poly_rezando)
            self.fundo_limpo = inpaint_difusivo(fundo1, mask2)
            self.recortes["boleto"] = RecortePuppet(self.img0, poly_boleto, feather=4, fundo_preparado=self.fundo_limpo)
            self.recortes["rezando"] = RecortePuppet(self.img0, poly_rezando, feather=4, fundo_preparado=self.fundo_limpo)

        elif self.id == "003":
            poly_cao = [(695, 240), (755, 180), (845, 168), (925, 192), (978, 252), (988, 320), (962, 355), (738, 362), (698, 330)]
            self.recortes["cao_pedestal"] = RecortePuppet(self.img0, poly_cao, feather=3)
            self.fundo_limpo = self.recortes["cao_pedestal"].fundo_limpo

        elif self.id == "004":
            poly_caramelo = [(465, 140), (518, 92), (638, 58), (762, 52), (848, 68), (878, 138), (885, 260),
                             (910, 340), (925, 450), (875, 545), (700, 568), (558, 558), (475, 470), (450, 330), (440, 205)]
            self.recortes["caramelo_gabinete"] = RecortePuppet(self.img0, poly_caramelo, feather=4)
            self.fundo_limpo = self.recortes["caramelo_gabinete"].fundo_limpo

        elif self.id == "005":
            poly_cida = [(742, 92), (862, 72), (978, 92), (1015, 168), (1038, 298), (1068, 418),
                         (1098, 558), (1092, 762), (868, 764), (852, 598), (798, 518), (758, 398), (742, 268)]
            poly_cao_rua = [(192, 445), (275, 438), (340, 452), (398, 468), (478, 498), (508, 542),
                            (502, 618), (478, 655), (398, 665), (342, 655), (318, 608), (298, 558), (200, 542), (188, 488)]
            poly_sacola = [(245, 518), (312, 525), (332, 598), (318, 668), (285, 685), (245, 668), (222, 598)]
            mask_c = criar_mascara_poligono((self.w, self.h), poly_cida)
            fundo_c = inpaint_difusivo(self.img0, mask_c)
            mask_d = criar_mascara_poligono((self.w, self.h), poly_cao_rua)
            fundo_d = inpaint_difusivo(fundo_c, mask_d)
            mask_s = criar_mascara_poligono((self.w, self.h), poly_sacola)
            self.fundo_limpo = inpaint_difusivo(fundo_d, mask_s)
            self.recortes["cida"] = RecortePuppet(self.img0, poly_cida, feather=4, fundo_preparado=self.fundo_limpo)
            self.recortes["cao_rua"] = RecortePuppet(self.img0, poly_cao_rua, feather=3, fundo_preparado=self.fundo_limpo)
            self.recortes["sacola"] = RecortePuppet(self.img0, poly_sacola, feather=2, fundo_preparado=self.fundo_limpo)

        elif self.id == "006":
            # Dona Marta na igreja
            poly_marta = [(570, 160), (690, 160), (740, 250), (750, 340), (690, 420), (680, 530), (590, 530), (580, 420), (510, 310), (510, 240)]
            self.recortes["marta"] = RecortePuppet(self.img0, poly_marta, feather=4)
            self.fundo_limpo = self.recortes["marta"].fundo_limpo

        elif self.id == "007":
            # Seu Jorge sentado na cadeira vermelha
            poly_jorge = [(180, 240), (330, 240), (440, 380), (470, 460), (460, 750), (120, 750), (90, 560), (160, 380)]
            self.recortes["seu_jorge"] = RecortePuppet(self.img0, poly_jorge, feather=4)
            self.fundo_limpo = self.recortes["seu_jorge"].fundo_limpo

        elif self.id == "008":
            # Linguiça no guindaste
            poly_linguica = [(340, 420), (730, 420), (745, 525), (335, 525)]
            self.recortes["linguica"] = RecortePuppet(self.img0, poly_linguica, feather=3)
            self.fundo_limpo = self.recortes["linguica"].fundo_limpo

        elif self.id == "009":
            # Caramelo no pote (ritual)
            poly_car_pote = [(685, 545), (785, 545), (815, 680), (675, 680)]
            self.recortes["caramelo_ritual"] = RecortePuppet(self.img0, poly_car_pote, feather=3)
            self.fundo_limpo = self.recortes["caramelo_ritual"].fundo_limpo

        elif self.id == "013":
            # Xerxes Pardal no palanque
            poly_pardal = [(740, 570), (880, 570), (885, 765), (735, 765)]
            self.recortes["pardal"] = RecortePuppet(self.img0, poly_pardal, feather=4)
            self.fundo_limpo = self.recortes["pardal"].fundo_limpo

    def compor_frame(self, t, env_fala, falante_ativo):
        """Gera o quadro da cena em resolução original com todos os efeitos vivos."""
        if self.id == "T":
            return self._animar_titulo(t)
        elif self.id == "001":
            return self._animar_001(t)
        elif self.id == "002":
            return self._animar_002(t)
        elif self.id == "003":
            return self._animar_003(t)
        elif self.id == "004":
            return self._animar_004(t)
        elif self.id == "005":
            return self._animar_005(t, env_fala, falante_ativo)
        elif self.id == "006":
            return self._animar_006(t, env_fala, falante_ativo)
        elif self.id == "007":
            return self._animar_007(t, env_fala, falante_ativo)
        elif self.id == "008":
            return self._animar_008(t)
        elif self.id == "009":
            return self._animar_009(t)
        elif self.id == "010":
            return self._animar_010(t)
        elif self.id == "011":
            return self._animar_011(t)
        elif self.id == "012":
            return self._animar_012(t)
        elif self.id == "013":
            return self._animar_013(t)
        else:
            return self.img0.copy()

    # ------------------ CENAS PARTE 1 ------------------

    def _animar_titulo(self, t):
        frame = self.img0.copy()
        arr = np.array(frame)
        h_sky = 240
        X, Y = np.meshgrid(np.arange(self.w), np.arange(h_sky))
        dx = (np.sin(X * 0.005 + t * 0.8) * 4.0).astype(np.float32)
        dy = (np.cos(Y * 0.01 + t * 0.5) * 1.5).astype(np.float32)
        arr = deformar_regiao(arr, (0, 0, self.w, h_sky), dx, dy)
        return Image.fromarray(arr)

    def _animar_001(self, t):
        frame = self.img0.copy()
        arr = np.array(frame)
        
        h_sky = 220
        X, Y = np.meshgrid(np.arange(self.w), np.arange(h_sky))
        dx_ceu = (np.sin(X * 0.004 + t * 0.6) * 5.0).astype(np.float32)
        dy_ceu = (np.cos(Y * 0.008 + t * 0.4) * 2.0).astype(np.float32)
        arr = deformar_regiao(arr, (0, 0, self.w, h_sky), dx_ceu, dy_ceu)
        
        box_banner = (550, 545, 860, 620)
        bw, bh = box_banner[2] - box_banner[0], box_banner[3] - box_banner[1]
        BX, BY = np.meshgrid(np.arange(bw), np.arange(bh))
        dy_banner = (np.sin(BX * 0.045 - t * 4.0) * 3.5).astype(np.float32)
        dx_banner = np.zeros_like(dy_banner)
        arr = deformar_regiao(arr, box_banner, dx_banner, dy_banner)
        
        urubus = [(147, 140), (224, 190), (317, 215), (427, 242)]
        for i, (ux, uy) in enumerate(urubus):
            box_u = (ux - 18, uy - 18, ux + 18, uy + 18)
            uw, uh = box_u[2] - box_u[0], box_u[3] - box_u[1]
            dy_u = np.full((uh, uw), math.sin(t * 3.0 + i * 1.6) * 2.0, dtype=np.float32)
            dx_u = np.zeros_like(dy_u)
            arr = deformar_regiao(arr, box_u, dx_u, dy_u)
            
        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")
        
        t_voo = (t * 0.08) % 1.2
        if t_voo <= 1.0:
            vx = int(t_voo * (self.w + 100) - 50)
            vy = int(140 + math.sin(t * 2.0) * 25)
            asa = math.sin(t * 14.0) * 7.0
            draw.line([(vx - 14, vy - int(asa)), (vx, vy), (vx + 14, vy - int(asa))], fill=(35, 30, 40, 220), width=3)
            draw.ellipse([(vx - 4, vy - 3), (vx + 4, vy + 3)], fill=(30, 25, 35, 230))
            
        for p in range(12):
            px = int((p * 117 + t * 18) % self.w)
            py = int((p * 79 + math.sin(t * 1.5 + p) * 20 + 350) % (self.h - 100))
            draw.ellipse([(px, py), (px + 2, py + 2)], fill=(255, 240, 200, 140))
            
        return frame

    def _animar_002(self, t):
        fundo = self.fundo_limpo.copy()
        arr = np.array(fundo)
        
        box_varal = (0, 265, 235, 315)
        vw, vh = box_varal[2] - box_varal[0], box_varal[3] - box_varal[1]
        VX, VY = np.meshgrid(np.arange(vw), np.arange(vh))
        dx_varal = (np.sin(VY * 0.08 + t * 3.5) * 3.0).astype(np.float32)
        dy_varal = np.zeros_like(dx_varal)
        arr = deformar_regiao(arr, box_varal, dx_varal, dy_varal)
        
        box_espeto = (330, 335, 550, 375)
        ew, eh = box_espeto[2] - box_espeto[0], box_espeto[3] - box_espeto[1]
        rot_esp = math.sin(t * 4.0) * 2.2
        dy_esp = np.full((eh, ew), rot_esp, dtype=np.float32)
        dx_esp = np.zeros_like(dy_esp)
        arr = deformar_regiao(arr, box_espeto, dx_esp, dy_esp)
        
        cabecas_churrasco = [(284, 310, 35), (397, 500, 40), (602, 470, 30), (62, 490, 25)]
        for i, (cx, cy, cr) in enumerate(cabecas_churrasco):
            box_c = (cx - cr, cy - cr, cx + cr, cy + cr)
            cw, ch = box_c[2] - box_c[0], box_c[3] - box_c[1]
            dy_bob = np.full((ch, cw), abs(math.sin(t * 3.5 + i * 1.5)) * -3.5, dtype=np.float32)
            dx_bob = np.zeros_like(dy_bob)
            arr = deformar_regiao(arr, box_c, dx_bob, dy_bob)
            
        box_fan = (688, 337, 748, 397)
        fw, fh = box_fan[2] - box_fan[0], box_fan[3] - box_fan[1]
        fan_patch = self.img0.crop(box_fan)
        fan_rot = fan_patch.rotate(int((t * 540) % 360), resample=Image.BICUBIC)
        mask_circ = Image.new("L", (fw, fh), 0)
        ImageDraw.Draw(mask_circ).ellipse([(2, 2), (fw - 3, fh - 3)], fill=255)
        
        fundo_pil = Image.fromarray(arr)
        fundo_pil.paste(fan_rot, (box_fan[0], box_fan[1]), mask_circ)
        
        rot_lamp = math.sin(t * 1.8) * 3.0
        lamp_patch = self.img0.crop((800, 160, 885, 260))
        lamp_rot = lamp_patch.rotate(rot_lamp, center=(42, 10), resample=Image.BICUBIC)
        fundo_pil.paste(lamp_rot, (800, 160), lamp_rot.convert("RGBA"))
        
        tremor_x = math.sin(t * 40.0) * 1.8
        tremor_y = math.cos(t * 45.0) * 1.2
        rec_boleto = self.recortes["boleto"]
        rec_boleto.colar(fundo_pil, dx=tremor_x, dy=tremor_y, scale_y=1.0 + math.sin(t * 3.0) * 0.005, pivot=(760, 550))
        
        rot_rez = math.sin(t * 2.8) * 2.5
        rec_rez = self.recortes["rezando"]
        rec_rez.colar(fundo_pil, rot=rot_rez, pivot=(1165, 615))
        
        draw = ImageDraw.Draw(fundo_pil, "RGBA")
        
        for s in range(16):
            idade = (t * 1.2 + s * 0.18) % 2.5
            fx = int(430 - idade * 22 + math.sin(idade * 4.0) * 12)
            fy = int(250 - idade * 75)
            fr = int(10 + idade * 18)
            alpha = int(max(0, (1.0 - idade / 2.5) * 150))
            draw.ellipse([(fx - fr, fy - fr), (fx + fr, fy + fr)], fill=(160, 155, 160, alpha))
            
        for v in range(12):
            idade_v = (t * 1.4 + v * 0.22) % 2.2
            vx = int(1050 + math.sin(idade_v * 3.0) * 14)
            vy = int(630 - idade_v * 85)
            vr = int(12 + idade_v * 20)
            alpha_v = int(max(0, (1.0 - idade_v / 2.2) * 120))
            draw.ellipse([(vx - vr, vy - vr), (vx + vr, vy + vr)], fill=(210, 215, 220, alpha_v))
            
        for sw in range(3):
            idade_sw = (t * 1.6 + sw * 0.4) % 1.2
            if idade_sw < 0.9:
                sx = int(785 + idade_sw * 15)
                sy = int(320 + idade_sw * 55)
                draw.ellipse([(sx, sy), (sx + 4, sy + 7)], fill=(200, 230, 255, 210))
                
        for lr in range(2):
            idade_lr = (t * 1.3 + lr * 0.6) % 1.4
            if idade_lr < 1.0:
                lx = int(1202 + idade_lr * 6)
                ly = int(368 + idade_lr * 42)
                draw.ellipse([(lx, ly), (lx + 3, ly + 6)], fill=(180, 220, 255, 200))
                
        flicker = 1.0 + (math.sin(t * 30.0) * 0.04)
        if (int(t * 15) % 19) == 0:
            flicker = 0.82
        draw.ellipse([(800, 210), (885, 290)], fill=(255, 245, 190, int(35 * flicker)))
        
        return fundo_pil

    def _animar_003(self, t):
        fundo = self.fundo_limpo.copy()
        arr = np.array(fundo)
        
        box_shimmer = (0, 320, self.w, 520)
        sw, sh = box_shimmer[2] - box_shimmer[0], box_shimmer[3] - box_shimmer[1]
        SX, SY = np.meshgrid(np.arange(sw), np.arange(sh))
        dx_shim = (np.sin(SY * 0.35 + t * 5.0) * 1.8).astype(np.float32)
        dy_shim = np.zeros_like(dx_shim)
        arr = deformar_regiao(arr, box_shimmer, dx_shim, dy_shim)
        
        fundo_pil = Image.fromarray(arr)
        
        rec_cao = self.recortes["cao_pedestal"]
        scale_resp = 1.0 + math.sin(t * 2.2) * 0.007
        
        espasmo = 0.0
        ciclo_esp = t % 3.2
        if ciclo_esp < 0.2:
            espasmo = math.sin(ciclo_esp / 0.2 * math.pi) * 4.0
            
        rec_cao.colar(fundo_pil, dy=0.0, rot=espasmo, scale_y=scale_resp, pivot=(850, 355))
        
        draw = ImageDraw.Draw(fundo_pil, "RGBA")
        for z in range(3):
            idade_z = (t * 0.8 + z * 0.45) % 1.8
            zx = int(940 + idade_z * 45 + math.sin(idade_z * 4.0) * 14)
            zy = int(215 - idade_z * 70)
            alpha_z = int(max(0, (1.0 - idade_z / 1.8) * 220))
            tamanho = max(18, int(22 + idade_z * 16))
            draw.text((zx, zy), "z" if z % 2 == 0 else "Z", font=ler_fonte(tamanho), fill=(40, 35, 45, alpha_z))
            
        return fundo_pil

    def _animar_004(self, t):
        fundo = self.fundo_limpo.copy()
        arr = np.array(fundo)
        
        box_notas = (1240, 200, 1285, 310)
        nw, nh = box_notas[2] - box_notas[0], box_notas[3] - box_notas[1]
        NX, NY = np.meshgrid(np.arange(nw), np.arange(nh))
        dx_notas = (np.sin(NY * 0.15 + t * 4.5) * 2.0).astype(np.float32)
        dy_notas = np.zeros_like(dx_notas)
        arr = deformar_regiao(arr, box_notas, dx_notas, dy_notas)
        
        fundo_pil = Image.fromarray(arr)
        
        rec_car = self.recortes["caramelo_gabinete"]
        scale_resp = 1.0 + math.sin(t * 2.0) * 0.005
        rot_nod = math.sin(t * 1.2) * 1.2
        
        camada_car = rec_car.camada_rgba.copy()
        
        ciclo_piscar = t % 4.2
        if ciclo_piscar < 0.16:
            fase_p = math.sin((ciclo_piscar / 0.16) * math.pi)
            arr_cam = np.array(camada_car)
            for ox, oy in [(590, 240), (775, 233)]:
                box_olho = (ox - 45, oy - 25, ox + 45, oy + 25)
                ow, oh = box_olho[2] - box_olho[0], box_olho[3] - box_olho[1]
                OY, OX = np.meshgrid(np.arange(oh), np.arange(ow), indexing='ij')
                dy_p = ((OY - (oh / 2.0)) * (fase_p * 0.75)).astype(np.float32)
                dx_p = np.zeros_like(dy_p)
                arr_cam = deformar_regiao(arr_cam, box_olho, dx_p, dy_p)
            camada_car = Image.fromarray(arr_cam)
            
        rec_car.colar(fundo_pil, rot=rot_nod, scale_y=scale_resp, pivot=(665, 555), camada_override=camada_car)
        
        box_papel = (760, 390, 950, 560)
        pw, ph = box_papel[2] - box_papel[0], box_papel[3] - box_papel[1]
        PX, PY = np.meshgrid(np.arange(pw), np.arange(ph))
        dy_papel = (np.sin(PX * 0.08 + t * 6.0) * 2.5).astype(np.float32)
        dx_papel = np.zeros_like(dy_papel)
        arr_fundo = np.array(fundo_pil)
        arr_fundo = deformar_regiao(arr_fundo, box_papel, dx_papel, dy_papel)
        
        return Image.fromarray(arr_fundo)

    def _animar_005(self, t, env_fala, falante_ativo):
        fundo = self.fundo_limpo.copy()
        
        trote_y = abs(math.sin(t * 12.0)) * -5.0
        trote_rot = math.sin(t * 12.0) * 2.2
        rec_cao = self.recortes["cao_rua"]
        rec_cao.colar(fundo, dy=trote_y, rot=trote_rot, pivot=(400, 676))
        
        rot_sacola = math.sin(t * 12.0 - 0.8) * 12.0
        rec_sacola = self.recortes["sacola"]
        rec_sacola.colar(fundo, dy=trote_y, rot=rot_sacola, pivot=(278, 532))
        
        rec_cida = self.recortes["cida"]
        camada_cida = rec_cida.camada_rgba.copy()
        
        rot_cida = -1.8 * env_fala
        scale_cida = 1.0 + math.sin(t * 2.5) * 0.005
        
        if falante_ativo and env_fala > 0.08:
            arr_cida = np.array(camada_cida)
            box_mandibula = (815, 250, 925, 335)
            mw, mh = box_mandibula[2] - box_mandibula[0], box_mandibula[3] - box_mandibula[1]
            MY, MX = np.meshgrid(np.arange(mh), np.arange(mw), indexing='ij')
            
            jaw_drop = env_fala * 12.0
            dy_jaw = (np.clip((MY - 6) / float(mh), 0.0, 1.0) * jaw_drop).astype(np.float32)
            dx_jaw = np.zeros_like(dy_jaw)
            arr_cida = deformar_regiao(arr_cida, box_mandibula, dx_jaw, dy_jaw)
            
            camada_cida = Image.fromarray(arr_cida)
            draw_boca = ImageDraw.Draw(camada_cida, "RGBA")
            
            boca_cx, boca_cy = 868, 268 + int(jaw_drop * 0.4)
            boca_rx = int(36 + env_fala * 8)
            boca_ry = int(8 + env_fala * 24)
            
            draw_boca.ellipse([(boca_cx - boca_rx, boca_cy - boca_ry),
                               (boca_cx + boca_rx, boca_cy + boca_ry)], fill=(45, 15, 20, 245), outline=(20, 10, 15, 255), width=2)
            draw_boca.pieslice([(boca_cx - boca_rx + 4, boca_cy - boca_ry),
                                (boca_cx + boca_rx - 4, boca_cy + int(boca_ry * 0.3))], 0, 180, fill=(245, 245, 235, 240))
            draw_boca.ellipse([(boca_cx - int(boca_rx * 0.6), boca_cy + int(boca_ry * 0.2)),
                               (boca_cx + int(boca_rx * 0.6), boca_cy + boca_ry)], fill=(220, 90, 105, 230))
                               
        rec_cida.colar(fundo, rot=rot_cida, scale_y=scale_cida, pivot=(868, 760), camada_override=camada_cida)
        
        draw = ImageDraw.Draw(fundo, "RGBA")
        brilho = int(abs(math.sin(t * 3.0)) * 180)
        draw.line([(1160, 565), (1170, 575)], fill=(255, 255, 240, brilho), width=2)
        draw.line([(1170, 565), (1160, 575)], fill=(255, 255, 240, brilho), width=2)
        
        return fundo

    # ------------------ CENAS PARTE 2 ------------------

    def _animar_006(self, t, env_fala, falante_ativo):
        # Dona Marta na igreja pregando
        fundo = self.fundo_limpo.copy()
        arr = np.array(fundo)
        
        # 1. Faixa com folha canábica ondulando no vento (340 a 470, 240 a 490)
        box_banner = (340, 240, 470, 490)
        bw, bh = box_banner[2] - box_banner[0], box_banner[3] - box_banner[1]
        BX, BY = np.meshgrid(np.arange(bw), np.arange(bh))
        dy_ban = (np.sin(BX * 0.05 + t * 3.2) * 2.5).astype(np.float32)
        dx_ban = np.zeros_like(dy_ban)
        arr = deformar_regiao(arr, box_banner, dx_ban, dy_ban)
        
        # 2. Beatas acenando com a cabeça concordando ("amém")
        beatas = [(830, 400, 35), (1000, 360, 40), (1130, 320, 35)]
        for i, (bx, by, br) in enumerate(beatas):
            box_b = (bx - br, by - br, bx + br, by + br)
            bw, bh = box_b[2] - box_b[0], box_b[3] - box_b[1]
            dy_nod = np.full((bh, bw), abs(math.sin(t * 3.2 + i * 1.3)) * -3.0, dtype=np.float32)
            dx_nod = np.zeros_like(dy_nod)
            arr = deformar_regiao(arr, box_b, dx_nod, dy_nod)
            
        fundo_pil = Image.fromarray(arr)
        
        # 3. Atuação de Dona Marta
        rec_marta = self.recortes["marta"]
        camada_marta = rec_marta.camada_rgba.copy()
        
        # Respiração + gesticulação da Bíblia
        scale_marta = 1.0 + math.sin(t * 2.8) * 0.005
        rot_marta = -2.0 * env_fala
        
        # Celular na mão direita vibrando notificações (510 a 550, 250 a 310)
        arr_m = np.array(camada_marta)
        box_cel = (510, 250, 550, 310)
        cw, ch = box_cel[2] - box_cel[0], box_cel[3] - box_cel[1]
        vibra_x = np.full((ch, cw), math.sin(t * 50.0) * 1.4, dtype=np.float32)
        vibra_y = np.zeros_like(vibra_x)
        arr_m = deformar_regiao(arr_m, box_cel, vibra_x, vibra_y)
        
        # LIP SYNC ANATÔMICO REAL DA MARTA
        # Medição: cantos em (618, 290) a (655, 292), centro (636, 295)
        if falante_ativo and env_fala > 0.08:
            box_mand = (605, 275, 670, 325)
            mw, mh = box_mand[2] - box_mand[0], box_mand[3] - box_mand[1]
            MY, MX = np.meshgrid(np.arange(mh), np.arange(mw), indexing='ij')
            
            jaw_drop = env_fala * 9.0
            dy_jaw = (np.clip((MY - 4) / float(mh), 0.0, 1.0) * jaw_drop).astype(np.float32)
            dx_jaw = np.zeros_like(dy_jaw)
            arr_m = deformar_regiao(arr_m, box_mand, dx_jaw, dy_jaw)
            
            camada_marta = Image.fromarray(arr_m)
            draw_m = ImageDraw.Draw(camada_marta, "RGBA")
            
            mcx, mcy = 636, 292 + int(jaw_drop * 0.4)
            mrx = int(18 + env_fala * 4)
            mry = int(5 + env_fala * 12)
            
            draw_m.ellipse([(mcx - mrx, mcy - mry), (mcx + mrx, mcy + mry)], fill=(40, 12, 18, 245), outline=(15, 8, 12, 255), width=2)
            draw_m.pieslice([(mcx - mrx + 2, mcy - mry), (mcx + mrx - 2, mcy + int(mry * 0.3))], 0, 180, fill=(245, 245, 235, 240))
            draw_m.ellipse([(mcx - int(mrx * 0.5), mcy + int(mry * 0.2)), (mcx + int(mrx * 0.5), mcy + mry)], fill=(220, 85, 100, 230))
        else:
            camada_marta = Image.fromarray(arr_m)
            
        rec_marta.colar(fundo_pil, rot=rot_marta, scale_y=scale_marta, pivot=(635, 520), camada_override=camada_marta)
        
        # 4. Ícone de notificação do celular pulsando no ar
        draw_f = ImageDraw.Draw(fundo_pil, "RGBA")
        alpha_notif = int(abs(math.sin(t * 8.0)) * 220)
        draw_f.ellipse([(528, 228), (542, 242)], fill=(60, 200, 90, alpha_notif))
        draw_f.ellipse([(531, 231), (539, 239)], fill=(255, 255, 255, alpha_notif))
        
        return fundo_pil

    def _animar_007(self, t, env_fala, falante_ativo):
        # Seu Jorge na fila da praça com garfo
        fundo = self.fundo_limpo.copy()
        arr = np.array(fundo)
        
        # 1. Fila de pessoas ao fundo fazendo bobs lentos de cansaço às 5h
        box_fila = (500, 440, 1200, 580)
        fw, fh = box_fila[2] - box_fila[0], box_fila[3] - box_fila[1]
        FX, FY = np.meshgrid(np.arange(fw), np.arange(fh))
        dy_fila = (np.sin(FX * 0.015 + t * 2.0) * 1.8).astype(np.float32)
        dx_fila = np.zeros_like(dy_fila)
        arr = deformar_regiao(arr, box_fila, dx_fila, dy_fila)
        
        fundo_pil = Image.fromarray(arr)
        
        # 2. Seu Jorge na cadeira
        rec_jorge = self.recortes["seu_jorge"]
        camada_jorge = rec_jorge.camada_rgba.copy()
        
        scale_j = 1.0 + math.sin(t * 2.2) * 0.006
        rot_j = math.sin(t * 1.5) * 1.2
        
        arr_j = np.array(camada_jorge)
        
        # Garfo na mão apontando com ênfase
        box_garfo = (380, 480, 470, 580)
        gw, gh = box_garfo[2] - box_garfo[0], box_garfo[3] - box_garfo[1]
        dy_g = np.full((gh, gw), -6.0 * env_fala, dtype=np.float32)
        dx_g = np.zeros_like(dy_g)
        arr_j = deformar_regiao(arr_j, box_garfo, dx_g, dy_g)
        
        # LIP SYNC ANATÔMICO REAL DO SEU JORGE
        # Medição: cantos (318, 386) a (368, 386), centro (343, 388)
        if falante_ativo and env_fala > 0.08:
            box_mand_j = (305, 370, 380, 435)
            mw, mh = box_mand_j[2] - box_mand_j[0], box_mand_j[3] - box_mand_j[1]
            MY, MX = np.meshgrid(np.arange(mh), np.arange(mw), indexing='ij')
            
            jaw_drop_j = env_fala * 11.0
            dy_jaw_j = (np.clip((MY - 5) / float(mh), 0.0, 1.0) * jaw_drop_j).astype(np.float32)
            dx_jaw_j = np.zeros_like(dy_jaw_j)
            arr_j = deformar_regiao(arr_j, box_mand_j, dx_jaw_j, dy_jaw_j)
            
            camada_jorge = Image.fromarray(arr_j)
            draw_j = ImageDraw.Draw(camada_jorge, "RGBA")
            
            jcx, jcy = 343, 388 + int(jaw_drop_j * 0.4)
            jrx = int(24 + env_fala * 5)
            jry = int(5 + env_fala * 14)
            
            draw_j.ellipse([(jcx - jrx, jcy - jry), (jcx + jrx, jcy + jry)], fill=(35, 15, 20, 245), outline=(15, 8, 10, 255), width=2)
            draw_j.pieslice([(jcx - int(jrx * 0.7), jcy + int(jry * 0.2)), (jcx + int(jrx * 0.7), jcy + jry)], 180, 360, fill=(230, 230, 220, 240))
            draw_j.ellipse([(jcx - int(jrx * 0.5), jcy + int(jry * 0.1)), (jcx + int(jrx * 0.5), jcy + jry)], fill=(200, 80, 95, 230))
        else:
            camada_jorge = Image.fromarray(arr_j)
            
        rec_jorge.colar(fundo_pil, rot=rot_j, scale_y=scale_j, pivot=(300, 740), camada_override=camada_jorge)
        
        # 3. Vapor quente subindo do prato/copo de comida
        draw_vap = ImageDraw.Draw(fundo_pil, "RGBA")
        for st in range(6):
            idade_st = (t * 1.5 + st * 0.25) % 1.6
            sx = int(345 + math.sin(idade_st * 4.0) * 8)
            sy = int(550 - idade_st * 65)
            alpha_st = int(max(0, (1.0 - idade_st / 1.6) * 110))
            draw_vap.ellipse([(sx - 6, sy - 6), (sx + 6, sy + 6)], fill=(235, 230, 225, alpha_st))
            
        return fundo_pil

    def _animar_008(self, t):
        # Ritual da Linguiça no Guindaste (Narrador em off - zero boca mexendo)
        fundo = self.fundo_limpo.copy()
        
        # 1. Linguiça gigante balançando no guindaste como pêndulo
        rot_ling = math.sin(t * 1.6) * 2.2
        rec_ling = self.recortes["linguica"]
        rec_ling.colar(fundo, rot=rot_ling, pivot=(535, 340))
        
        draw = ImageDraw.Draw(fundo, "RGBA")
        
        # 2. Vapores quentes saindo das pontas da linguiça
        for p in range(8):
            idade_p = (t * 1.3 + p * 0.2) % 1.8
            # Ponta esquerda
            lx = int(365 - idade_p * 8 + math.sin(idade_p * 3.0) * 6)
            ly = int(465 - idade_p * 60)
            alpha_l = int(max(0, (1.0 - idade_p / 1.8) * 130))
            draw.ellipse([(lx - 8, ly - 8), (lx + 8, ly + 8)], fill=(225, 220, 220, alpha_l))
            # Ponta direita
            rx = int(710 + idade_p * 8 + math.sin(idade_p * 3.0) * 6)
            ry = int(465 - idade_p * 60)
            draw.ellipse([(rx - 8, ry - 8), (rx + 8, ry + 8)], fill=(225, 220, 220, alpha_l))
            
        # 3. Reflexo do luar no binóculo do vereador na sacada (110, 440)
        glint = int(abs(math.sin(t * 2.5)) * 220)
        draw.line([(106, 440), (114, 440)], fill=(255, 255, 240, glint), width=2)
        draw.line([(110, 436), (110, 444)], fill=(255, 255, 240, glint), width=2)
        
        # 4. Estrelas piscando no céu noturno
        for st in range(8):
            sx = int((st * 163 + 120) % self.w)
            sy = int((st * 89 + 40) % 240)
            s_brilho = int(abs(math.sin(t * 3.0 + st)) * 200)
            draw.ellipse([(sx - 1, sy - 1), (sx + 1, sy + 1)], fill=(255, 255, 240, s_brilho))
            
        return fundo

    def _animar_009(self, t):
        # Terça-feira ritual: Caramelo no pote diante do povo (Narrador em off)
        fundo = self.fundo_limpo.copy()
        
        # 1. Caramelo no pote: respiração + piscar de tédio
        rec_car = self.recortes["caramelo_ritual"]
        scale_resp = 1.0 + math.sin(t * 2.0) * 0.006
        
        # Espasmo de orelha a cada 2.8s
        rot_esp = 0.0
        ciclo_e = t % 2.8
        if ciclo_e < 0.18:
            rot_esp = math.sin(ciclo_e / 0.18 * math.pi) * 3.5
            
        rec_car.colar(fundo, rot=rot_esp, scale_y=scale_resp, pivot=(745, 680))
        
        # 2. Multidão de joelhos fazendo reverência em onda
        arr = np.array(fundo)
        box_povo_esq = (500, 680, 700, 768)
        box_povo_dir = (780, 680, 980, 768)
        for box in [box_povo_esq, box_povo_dir]:
            pw, ph = box[2] - box[0], box[3] - box[1]
            PX, PY = np.meshgrid(np.arange(pw), np.arange(ph))
            dy_rev = (np.sin(t * 2.2 + PX * 0.02) * 2.0).astype(np.float32)
            dx_rev = np.zeros_like(dy_rev)
            arr = deformar_regiao(arr, box, dx_rev, dy_rev)
            
        return Image.fromarray(arr)

    def _animar_010(self, t):
        # Túnel do esgoto 12 metros abaixo da praça (Narrador em off)
        frame = self.img0.copy()
        arr = np.array(frame)
        
        # 1. Esgoto correndo no fundo (y: 580 a 768)
        box_esg = (0, 580, self.w, self.h)
        ew, eh = box_esg[2] - box_esg[0], box_esg[3] - box_esg[1]
        EX, EY = np.meshgrid(np.arange(ew), np.arange(eh))
        dx_esg = (np.sin(EX * 0.08 + t * 4.0) * 2.5).astype(np.float32)
        dy_esg = np.zeros_like(dx_esg)
        arr = deformar_regiao(arr, box_esg, dx_esg, dy_esg)
        
        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")
        
        # 2. Lâmpadas fluorescentes industriais com micro-cortes e flicker verde-água
        flicker_ind = 1.0 + (math.sin(t * 35.0) * 0.05)
        if (int(t * 12) % 17) == 0:
            flicker_ind = 0.78
        for lx in [200, 320, 540]:
            draw.ellipse([(lx - 50, 140), (lx + 50, 200)], fill=(140, 255, 210, int(30 * flicker_ind)))
            
        # 3. Operário soldando tubo à direita com faíscas estalando (1140, 520)
        brilho_solda = int(abs(math.sin(t * 25.0)) * 240)
        draw.ellipse([(1136, 516), (1144, 524)], fill=(255, 255, 220, brilho_solda))
        draw.ellipse([(1120, 500), (1160, 540)], fill=(255, 220, 100, int(brilho_solda * 0.4)))
        for sp in range(8):
            ang = (t * 30.0 + sp * 0.8) % (2.0 * math.pi)
            dist = 12 + (sp * 7) % 25
            spx = int(1140 + math.cos(ang) * dist)
            spy = int(520 + math.sin(ang) * dist + (dist * 0.4))
            draw.ellipse([(spx - 1, spy - 1), (spx + 1, spy + 1)], fill=(255, 240, 140, 220))
            
        return frame

    def _animar_011(self, t):
        # Cinejornal vintage 1997 ("O Progresso")
        frame = self.img0.copy()
        arr = np.array(frame).astype(np.float32)
        
        # 1. Tratamento sépia/vintage
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.08, 0, 255)
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.82, 0, 255)
        
        # 2. Granulação de película antiga (Film grain)
        ruido = (np.random.randn(*arr.shape) * 12.0).astype(np.float32)
        arr = np.clip(arr + ruido, 0, 255).astype(np.uint8)
        
        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")
        
        # 3. Riscos verticais pretos e brancos passando (Scratches)
        for sc in range(3):
            sx = int((sc * 419 + int(t * 15) * 83) % self.w)
            cor = (240, 240, 235, 160) if sc % 2 == 0 else (25, 20, 20, 180)
            draw.line([(sx, 0), (sx, self.h)], fill=cor, width=1)
            
        # 4. Estouro de flash fotográfico (t ≈ 1.2s e t ≈ 3.5s)
        for ft in [1.2, 3.5]:
            dt = t - ft
            if 0.0 <= dt <= 0.18:
                alpha_flash = int((1.0 - dt / 0.18) * 240)
                draw.rectangle([(0, 0), (self.w, self.h)], fill=(255, 255, 250, alpha_flash))
                
        return frame

    def _animar_012(self, t):
        # Obra paralisada / Verba de 200 mil reais (Narrador em off)
        frame = self.img0.copy()
        arr = np.array(frame)
        
        # 1. Placa enferrujada "OBRA PARALISADA" oscilando na haste (580 a 720, 400 a 620)
        box_placa = (580, 400, 720, 620)
        pw, ph = box_placa[2] - box_placa[0], box_placa[3] - box_placa[1]
        rot_placa = math.sin(t * 2.2) * 2.8
        dy_p = np.full((ph, pw), rot_placa, dtype=np.float32)
        dx_p = np.zeros_like(dy_p)
        arr = deformar_regiao(arr, box_placa, dx_p, dy_p)
        
        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")
        
        # 2. Tumbleweed rolando na terra batida
        tx = int((t * 85) % (self.w + 100) - 50)
        ty = int(680 + abs(math.sin(t * 6.0)) * -18)
        tr = 22
        draw.ellipse([(tx - tr, ty - tr), (tx + tr, ty + tr)], outline=(110, 85, 55, 210), width=3)
        draw.line([(tx - tr + 4, ty), (tx + tr - 4, ty)], fill=(120, 95, 60, 200), width=2)
        draw.line([(tx, ty - tr + 4), (tx, ty + tr - 4)], fill=(120, 95, 60, 200), width=2)
        
        # 3. Poeira de terra batida soprando no chão
        for d in range(15):
            dx_p = int((d * 97 + t * 45) % self.w)
            dy_p = int((d * 33 + math.sin(t * 2.0 + d) * 12 + 650) % (self.h - 20))
            draw.ellipse([(dx_p, dy_p), (dx_p + 3, dy_p + 2)], fill=(185, 155, 120, 110))
            
        return frame

    def _animar_013(self, t):
        # Churrasco do Pardal / Clímax (Narrador em off)
        fundo = self.fundo_limpo.copy()
        
        # 1. Xerxes Pardal no palanque erguendo os braços com coroa de linguiça
        rot_pardal = math.sin(t * 4.2) * 3.5
        rec_p = self.recortes["pardal"]
        rec_p.colar(fundo, rot=rot_pardal, pivot=(810, 750))
        
        draw = ImageDraw.Draw(fundo, "RGBA")
        
        # 2. Chuva contínua de confetes caindo sobre a multidão
        cores_confete = [
            (255, 60, 60, 230),   # Vermelho
            (60, 220, 70, 230),   # Verde
            (255, 220, 40, 230),  # Amarelo
            (50, 140, 255, 230),  # Azul
            (220, 70, 240, 230)   # Roxo
        ]
        for c in range(45):
            cx = int((c * 43 + math.sin(t * 3.0 + c) * 25) % self.w)
            cy = int((c * 27 + t * 95) % self.h)
            cw_c = int(5 + (c % 4) * 2)
            ch_c = int(3 + ((c * 3) % 4) * 2)
            cor = cores_confete[c % len(cores_confete)]
            draw.rectangle([(cx, cy), (cx + cw_c, cy + ch_c)], fill=cor)
            
        # 3. Fumaça volumétrica subindo das churrasqueiras
        for sm in range(14):
            idade_sm = (t * 1.5 + sm * 0.18) % 2.0
            smx = int(180 + idade_sm * 15 + math.sin(idade_sm * 4.0) * 12)
            smy = int(380 - idade_sm * 90)
            smr = int(12 + idade_sm * 22)
            alpha_sm = int(max(0, (1.0 - idade_sm / 2.0) * 140))
            draw.ellipse([(smx - smr, smy - smr), (smx + smr, smy + smr)], fill=(180, 140, 200, alpha_sm))
            
        return fundo

# -----------------------------------------------------------------------------
# SEGMENTO E COMPOSIÇÃO DE CÂMERA
# -----------------------------------------------------------------------------

class Segmento:
    def __init__(self, bloco, mov="zoom_in", img_path=None, wav_path=None):
        self.bloco = bloco
        self.mov = mov
        self.img_path = img_path or os.path.join(ROOT, "imagens", f"{bloco['id']:03d}.jpg")
        self.wav_path = wav_path
        self.img0 = Image.open(self.img_path).convert("RGB")
        self.sw, self.sh = self.img0.size
        self.dur = 0.0
        self.frames = 0
        self.env = np.zeros(1, dtype=np.float32)
        self.cena_viva = CenaViva(f"{bloco['id']:03d}", self.img0)
        self.falante_ativo = (FALANTE_EM_TELA.get(bloco["id"]) == bloco.get("personagem"))

    def carregar_audio(self):
        with wave.open(self.wav_path, "rb") as wf:
            self.dur = wf.getnframes() / float(wf.getframerate())
            self.frames = int(round(self.dur * FPS))
            dados = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
            if wf.getnchannels() == 2:
                dados = dados.reshape(-1, 2).mean(axis=1)
                
            tam_bloco = int(round(wf.getframerate() / float(FPS)))
            n_bf = int(math.ceil(len(dados) / float(tam_bloco)))
            envelope = []
            for i in range(n_bf):
                pedaco = dados[i * tam_bloco:(i + 1) * tam_bloco]
                rms = float(np.sqrt(np.mean(pedaco ** 2))) if len(pedaco) else 0.0
                envelope.append(rms)
            env_arr = np.array(envelope, dtype=np.float32)
            p95 = float(np.percentile(env_arr, 95)) if len(env_arr) else 1.0
            if p95 > 1e-4:
                env_arr = np.clip(env_arr / p95, 0.0, 1.0)
            self.env = env_arr

    def compor(self, quadro_idx):
        t_local = quadro_idx / float(FPS)
        prog = quadro_idx / float(max(1, self.frames - 1))
        
        idx_e = min(quadro_idx, len(self.env) - 1)
        val_env = float(self.env[idx_e]) if len(self.env) else 0.0
        
        quadro_vivo = self.cena_viva.compor_frame(t_local, val_env, self.falante_ativo)
        
        sw, sh = quadro_vivo.size
        ar_out = W / float(H)
        
        if self.mov == "zoom_in":
            s0, s1 = 1.0, 1.12
            s = s0 + (s1 - s0) * prog
            cw, ch = int(sw / s), int((sw / s) / ar_out)
            cx, cy = sw // 2, sh // 2
        elif self.mov == "zoom_out":
            s0, s1 = 1.12, 1.0
            s = s0 + (s1 - s0) * prog
            cw, ch = int(sw / s), int((sw / s) / ar_out)
            cx, cy = sw // 2, sh // 2
        elif self.mov == "pan_left":
            s = 1.06
            cw, ch = int(sw / s), int((sw / s) / ar_out)
            cx = int((sw - cw) * (1.0 - prog) + cw / 2.0)
            cy = sh // 2
        elif self.mov == "pan_right":
            s = 1.06
            cw, ch = int(sw / s), int((sw / s) / ar_out)
            cx = int((sw - cw) * prog + cw / 2.0)
            cy = sh // 2
        else: # static_push
            s = 1.02 + 0.03 * prog
            cw, ch = int(sw / s), int((sw / s) / ar_out)
            cx, cy = sw // 2, sh // 2
            
        respiracao = math.sin(t_local * 1.5) * 4.0
        cx += int(respiracao)
        cy += int(math.cos(t_local * 1.8) * 3.0)
        
        if self.bloco["id"] in PUNCH_BLOCOS and quadro_idx < 8:
            cx += int((np.random.rand() - 0.5) * 14)
            cy += int((np.random.rand() - 0.5) * 14)
            
        x0 = max(0, min(sw - cw, cx - cw // 2))
        y0 = max(0, min(sh - ch, cy - ch // 2))
        crop = quadro_vivo.crop((x0, y0, x0 + cw, y0 + ch))
        return crop.resize((W, H), Image.BICUBIC)

class SegmentoTitulo:
    def __init__(self, dur=4.0):
        self.bloco = {"id": 0, "personagem": "TÍTULO"}
        self.dur = dur
        self.frames = int(round(dur * FPS))
        img_path = os.path.join(ROOT, "imagens", "T_titulo.jpg")
        self.cena_viva = CenaViva("T", Image.open(img_path).convert("RGB"))

    def compor(self, quadro_idx):
        t_local = quadro_idx / float(FPS)
        prog = quadro_idx / float(max(1, self.frames - 1))
        vivo = self.cena_viva.compor_frame(t_local, 0.0, False)
        
        sw, sh = vivo.size
        s = 1.0 + 0.05 * prog
        cw, ch = int(sw / s), int((sw / s) / (W / float(H)))
        cx, cy = sw // 2, sh // 2
        x0, y0 = max(0, cx - cw // 2), max(0, cy - ch // 2)
        frame = vivo.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BICUBIC)
        
        draw = ImageDraw.Draw(frame, "RGBA")
        alpha_texto = int(min(255, max(0, math.sin(prog * math.pi) * 320)))
        draw.rectangle([(0, 0), (W, H)], fill=(0, 0, 0, int(70 * (alpha_texto / 255.0))))
        
        fonte_tit = ler_fonte(72)
        fonte_sub = ler_fonte(36)
        
        txt_tit = "M I G A L H Ó P O L I S"
        txt_sub = "T01E01 — O POTE"
        
        bbox_t = draw.textbbox((0, 0), txt_tit, font=fonte_tit)
        bbox_s = draw.textbbox((0, 0), txt_sub, font=fonte_sub)
        
        tx = (W - (bbox_t[2] - bbox_t[0])) // 2
        ty = (H // 2) - 60
        sx = (W - (bbox_s[2] - bbox_s[0])) // 2
        sy = ty + 90
        
        draw.text((tx + 3, ty + 3), txt_tit, font=fonte_tit, fill=(0, 0, 0, alpha_texto))
        draw.text((tx, ty), txt_tit, font=fonte_tit, fill=(255, 235, 170, alpha_texto))
        
        draw.text((sx + 2, sy + 2), txt_sub, font=fonte_sub, fill=(0, 0, 0, alpha_texto))
        draw.text((sx, sy), txt_sub, font=fonte_sub, fill=(220, 220, 225, alpha_texto))
        
        return frame

# -----------------------------------------------------------------------------
# TIMELINE E PROCESSAMENTO DE ÁUDIO
# -----------------------------------------------------------------------------

def construir_timeline(segmentos):
    timeline = []
    t_global = 0.0
    for i, seg in enumerate(segmentos):
        t_ini = t_global
        t_fim = t_ini + seg.dur
        timeline.append({"idx": i, "seg": seg, "t_ini": t_ini, "t_fim": t_fim})
        t_global = t_fim - XF
    t_total = t_global + XF
    total_frames = int(round(t_total * FPS))
    return timeline, t_total, total_frames

def mixar_audio_completo(timeline, t_total, out_wav, parte_num=1):
    """Mixagem master multi-pista: Diálogos + Camas Musicais (Beds) + Efeitos (SFX)."""
    n_amostras = int(math.ceil(t_total * SR))
    pista_voz = np.zeros(n_amostras, dtype=np.float32)
    pista_musica = np.zeros(n_amostras, dtype=np.float32)
    pista_sfx = np.zeros(n_amostras, dtype=np.float32)
    
    # 1. Pista de Voz com crossfades
    for item in timeline:
        seg = item["seg"]
        if not getattr(seg, "wav_path", None):
            continue
        with wave.open(seg.wav_path, "rb") as wf:
            dados = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
            if wf.getnchannels() == 2:
                dados = dados.reshape(-1, 2).mean(axis=1)
                
            idx_ini = int(round(item["t_ini"] * SR))
            n = min(len(dados), n_amostras - idx_ini)
            if n > 0:
                pista_voz[idx_ini:idx_ini + n] += dados[:n]
                
    def carregar_mp3_como_array(caminho):
        cmd = ["ffmpeg", "-v", "error", "-i", caminho, "-f", "s16le", "-acodec", "pcm_s16le", "-ar", str(SR), "-ac", "1", "-"]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0

    if parte_num == 1:
        tema_path = os.path.join(ROOT, "production", "audio", "beds", "tema.mp3")
        cotidiano_path = os.path.join(ROOT, "production", "audio", "beds", "cotidiano.mp3")
        churrasco_sfx = os.path.join(ROOT, "production", "audio", "sfx", "churrasqueira.mp3")
        crowd_sfx = os.path.join(ROOT, "production", "audio", "sfx", "crowd.mp3")
        
        if os.path.exists(tema_path):
            arr_tema = carregar_mp3_como_array(tema_path)
            n_t = min(len(arr_tema), int(8.5 * SR), n_amostras)
            fade_t = np.linspace(1.0, 0.0, int(2.0 * SR))
            arr_t_cut = arr_tema[:n_t].copy()
            arr_t_cut[-len(fade_t):] *= fade_t
            pista_musica[:n_t] += arr_t_cut * 0.16
            
        if os.path.exists(cotidiano_path):
            arr_cot = carregar_mp3_como_array(cotidiano_path)
            idx_c_ini = int(6.5 * SR)
            while idx_c_ini < n_amostras:
                pedaco_len = min(len(arr_cot), n_amostras - idx_c_ini)
                pista_musica[idx_c_ini:idx_c_ini + pedaco_len] += arr_cot[:pedaco_len] * 0.11
                idx_c_ini += len(arr_cot)
                
        t_b2_ini = timeline[2]["t_ini"]
        t_b2_fim = timeline[2]["t_fim"]
        idx_sfx_ini = int(t_b2_ini * SR)
        idx_sfx_fim = min(n_amostras, int(t_b2_fim * SR))
        len_sfx = idx_sfx_fim - idx_sfx_ini
        
        if os.path.exists(churrasco_sfx) and len_sfx > 0:
            arr_churr = carregar_mp3_como_array(churrasco_sfx)
            tiled_ch = np.tile(arr_churr, int(math.ceil(len_sfx / float(len(arr_churr)))))[:len_sfx]
            pista_sfx[idx_sfx_ini:idx_sfx_fim] += tiled_ch * 0.22
            
        if os.path.exists(crowd_sfx) and len_sfx > 0:
            arr_crowd = carregar_mp3_como_array(crowd_sfx)
            tiled_cr = np.tile(arr_crowd, int(math.ceil(len_sfx / float(len(arr_crowd)))))[:len_sfx]
            pista_sfx[idx_sfx_ini:idx_sfx_fim] += tiled_cr * 0.14

    elif parte_num == 2:
        # Camas musicais para Parte 2
        cotidiano_path = os.path.join(ROOT, "production", "audio", "beds", "cotidiano.mp3")
        tensao_path = os.path.join(ROOT, "production", "audio", "beds", "tensao.mp3")
        bueiro_path = os.path.join(ROOT, "production", "audio", "beds", "bueiro.mp3")
        comicio_path = os.path.join(ROOT, "production", "audio", "beds", "comicio.mp3")
        forro_path = os.path.join(ROOT, "production", "audio", "beds", "forro.mp3")
        
        vento_sfx = os.path.join(ROOT, "production", "audio", "sfx", "vento.mp3")
        agua_sfx = os.path.join(ROOT, "production", "audio", "sfx", "agua.mp3")
        flash_sfx = os.path.join(ROOT, "production", "audio", "sfx", "flash.mp3")
        churr_sfx = os.path.join(ROOT, "production", "audio", "sfx", "churrasqueira.mp3")
        crowd_sfx = os.path.join(ROOT, "production", "audio", "sfx", "crowd.mp3")
        
        # 006 a 007: Cotidiano
        t_marta_fim = timeline[1]["t_fim"]
        idx_cot_fim = min(n_amostras, int(t_marta_fim * SR))
        if os.path.exists(cotidiano_path):
            arr_cot = carregar_mp3_como_array(cotidiano_path)
            tiled_cot = np.tile(arr_cot, int(math.ceil(idx_cot_fim / float(len(arr_cot)))))[:idx_cot_fim]
            pista_musica[:idx_cot_fim] += tiled_cot * 0.12
            
        # 008 a 009: Tensão
        t_008_ini = timeline[2]["t_ini"]
        t_009_fim = timeline[3]["t_fim"]
        idx_t_ini = int(t_008_ini * SR)
        idx_t_fim = min(n_amostras, int(t_009_fim * SR))
        if os.path.exists(tensao_path) and idx_t_fim > idx_t_ini:
            arr_t = carregar_mp3_como_array(tensao_path)
            len_t = idx_t_fim - idx_t_ini
            tiled_t = np.tile(arr_t, int(math.ceil(len_t / float(len(arr_t)))))[:len_t]
            pista_musica[idx_t_ini:idx_t_fim] += tiled_t * 0.16
            
        # 010: Bueiro
        t_010_ini = timeline[4]["t_ini"]
        t_010_fim = timeline[4]["t_fim"]
        idx_b_ini = int(t_010_ini * SR)
        idx_b_fim = min(n_amostras, int(t_010_fim * SR))
        if os.path.exists(bueiro_path) and idx_b_fim > idx_b_ini:
            arr_b = carregar_mp3_como_array(bueiro_path)
            len_b = idx_b_fim - idx_b_ini
            tiled_b = np.tile(arr_b, int(math.ceil(len_b / float(len(arr_b)))))[:len_b]
            pista_musica[idx_b_ini:idx_b_fim] += tiled_b * 0.16
            
        # 011 a 013: Comício e Forró
        t_011_ini = timeline[5]["t_ini"]
        idx_c_ini = int(t_011_ini * SR)
        if os.path.exists(comicio_path) and n_amostras > idx_c_ini:
            arr_com = carregar_mp3_como_array(comicio_path)
            len_c = n_amostras - idx_c_ini
            tiled_c = np.tile(arr_com, int(math.ceil(len_c / float(len(arr_com)))))[:len_c]
            pista_musica[idx_c_ini:] += tiled_c * 0.16

        # SFX Pontuais
        if os.path.exists(vento_sfx):
            arr_v = carregar_mp3_como_array(vento_sfx)
            # Vento noturno no bloco 008
            idx_v_ini = int(timeline[2]["t_ini"] * SR)
            len_v = min(len(arr_v), n_amostras - idx_v_ini)
            if len_v > 0:
                pista_sfx[idx_v_ini:idx_v_ini + len_v] += arr_v[:len_v] * 0.16
                
        if os.path.exists(flash_sfx):
            arr_fl = carregar_mp3_como_array(flash_sfx)
            # Flash fotográfico no bloco 011
            idx_fl = int((timeline[5]["t_ini"] + 1.2) * SR)
            len_fl = min(len(arr_fl), n_amostras - idx_fl)
            if len_fl > 0:
                pista_sfx[idx_fl:idx_fl + len_fl] += arr_fl[:len_fl] * 0.25

        if os.path.exists(churr_sfx) and os.path.exists(crowd_sfx):
            # Churrasco do Pardal no bloco 013
            arr_ch = carregar_mp3_como_array(churr_sfx)
            arr_cr = carregar_mp3_como_array(crowd_sfx)
            idx_p_ini = int(timeline[7]["t_ini"] * SR)
            len_p = n_amostras - idx_p_ini
            if len_p > 0:
                t_ch = np.tile(arr_ch, int(math.ceil(len_p / float(len(arr_ch)))))[:len_p]
                t_cr = np.tile(arr_cr, int(math.ceil(len_p / float(len(arr_cr)))))[:len_p]
                pista_sfx[idx_p_ini:] += t_ch * 0.20 + t_cr * 0.18

    mix = pista_voz + pista_musica + pista_sfx
    
    n_fi = int(0.5 * SR)
    n_fo = int(0.8 * SR)
    mix[:n_fi] *= np.linspace(0.0, 1.0, n_fi)
    mix[-n_fo:] *= np.linspace(1.0, 0.0, n_fo)
    
    pico = np.max(np.abs(mix))
    if pico > 0.89:
        mix = mix * (0.89 / pico)
        
    dados_16 = np.clip(mix * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(out_wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(dados_16.tobytes())

# -----------------------------------------------------------------------------
# GERAÇÃO DE LEGENDAS (.ASS)
# -----------------------------------------------------------------------------

def gerar_legendas_ass(timeline, out_ass):
    linhas = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: NARRADOR,DejaVu Sans,52,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,1.5,2,90,90,70,1",
        "Style: CIDA,DejaVu Sans,54,&H0080E0FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,1.5,2,90,90,70,1",
        "Style: MARTA,DejaVu Sans,54,&H00E0A0FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,1.5,2,90,90,70,1",
        "Style: SEU_JORGE,DejaVu Sans,54,&H00C0FFC0,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,1.5,2,90,90,70,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]
    
    def fmt_tempo(s):
        h = int(s // 3600)
        m = int((s % 3600) // 60)
        seg = s % 60
        return f"{h:01d}:{m:02d}:{seg:05.2f}"

    for i, item in enumerate(timeline):
        seg = item["seg"]
        bloco = seg.bloco
        if bloco["id"] == 0:
            continue
            
        t_ini = item["t_ini"] + (XF / 2.0 if i > 1 else 0.0)
        t_fim = item["t_fim"] - (XF / 2.0 if i < len(timeline) - 1 else 0.0)
        
        personagem = bloco.get("personagem", "NARRADOR")
        if personagem == "CIDA":
            estilo = "CIDA"
        elif personagem == "MARTA":
            estilo = "MARTA"
        elif personagem in ("SEU_JORGE", "SEU JORGE"):
            estilo = "SEU_JORGE"
        else:
            estilo = "NARRADOR"
            
        texto = bloco.get("texto", "").replace("\n", " ").strip()
        linhas.append(f"Dialogue: 0,{fmt_tempo(t_ini)},{fmt_tempo(t_fim)},{estilo},,0,0,0,,{texto}")
        
    with open(out_ass, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")

# -----------------------------------------------------------------------------
# FOLHA DE CONTROLE DE QUALIDADE (QC)
# -----------------------------------------------------------------------------

def gerar_folha_qc(timeline, out_png, parte_num=1):
    """Gera folha de contato com quadros-chave para validação visual minuciosa."""
    print("Gerando folha de contato QC...")
    if parte_num == 1:
        tempos_qc = [
            ("TÍTULO", 1.5),
            ("001 AÉREA / URUBU", 7.0),
            ("002 CHURRASCO / FUMAÇA", 18.0),
            ("002 BOLETO / TREMOR", 20.5),
            ("002 BUEIRO / VAPOR", 22.8),
            ("003 PRAÇA / CÃO ZZZ", 25.5),
            ("004 GABINETE / CARAMELO", 33.0),
            ("005 CIDA / LIP SYNC", 44.5),
        ]
    else:
        tempos_qc = [
            ("006 MARTA / LIP SYNC", 6.0),
            ("007 SEU JORGE / GARFO", 17.0),
            ("008 GUINDASTE / LINGUIÇA", 26.0),
            ("009 RITUAL / CARAMELO", 36.0),
            ("010 TÚNEL DO ESGOTO", 45.0),
            ("011 CINEJORNAL 1997", 51.5),
            ("012 OBRA PARALISADA", 60.0),
            ("013 PARDAL / CHURRASCO", 71.5),
        ]
    
    quadros = []
    for rotulo, t in tempos_qc:
        f_idx = int(round(t * FPS))
        seg_ativo = timeline[0]["seg"]
        seg_f_idx = 0
        for item in timeline:
            if item["t_ini"] <= t < item["t_fim"]:
                seg_ativo = item["seg"]
                seg_f_idx = int(round((t - item["t_ini"]) * FPS))
                break
                
        img = seg_ativo.compor(seg_f_idx).resize((480, 270), Image.BICUBIC)
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, 0), (480, 32)], fill=(0, 0, 0, 180))
        draw.text((10, 6), f"{rotulo} (t={t:.1f}s)", font=ler_fonte(18), fill=(255, 230, 140))
        quadros.append(img)
        
    grade = Image.new("RGB", (1920, 540), (20, 20, 25))
    for i, q in enumerate(quadros):
        gx = (i % 4) * 480
        gy = (i // 4) * 270
        grade.paste(q, (gx, gy))
        
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    grade.save(out_png, "PNG")
    print(f"Folha QC salva em: {out_png}")

# -----------------------------------------------------------------------------
# PIPELINE PRINCIPAL DE RENDERIZAÇÃO
# -----------------------------------------------------------------------------

def obter_id_int(b):
    try:
        return int(b["id"])
    except (ValueError, TypeError):
        return -1

def renderizar_parte(parte_num, so_qc=False):
    blocos_path = os.path.join(ROOT, "roteiro", "blocos.json")
    with open(blocos_path, "r", encoding="utf-8") as f:
        dados_json = json.load(f)
        todos_blocos = dados_json["blocos"] if isinstance(dados_json, dict) and "blocos" in dados_json else dados_json
        
    if parte_num == 1:
        blocos = [b for b in todos_blocos if 1 <= obter_id_int(b) <= 5]
        movs = ["pan_left", "pan_right", "static_push", "zoom_in", "zoom_out"]
        tem_titulo = True
    elif parte_num == 2:
        blocos = [b for b in todos_blocos if 6 <= obter_id_int(b) <= 13]
        movs = ["pan_left", "zoom_out", "pan_left", "zoom_in", "zoom_out", "zoom_in", "pan_right", "zoom_in"]
        tem_titulo = False
    else:
        raise NotImplementedError(f"Parte {parte_num} ainda não configurada.")
        
    print(f"=== INICIANDO PRODUÇÃO: PARTE {parte_num} (BLOCOS {blocos[0]['id']} A {blocos[-1]['id']}) ===")
    
    segmentos = []
    if tem_titulo:
        segmentos.append(SegmentoTitulo(dur=4.0))
        
    for i, b in enumerate(blocos):
        wav = os.path.join(ROOT, "audio", f"{b['id']:03d}_{b['personagem'].lower().replace(' ', '_')}.mp3")
        wav_tmp = f"/tmp/b_{b['id']:03d}.wav"
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", wav, "-ac", "1", "-ar", str(SR), wav_tmp]
        subprocess.run(cmd, check=True)
        
        seg = Segmento(b, mov=movs[i % len(movs)], wav_path=wav_tmp)
        seg.carregar_audio()
        segmentos.append(seg)
        
    timeline, t_total, total_frames = construir_timeline(segmentos)
    print(f"Timeline construída: {len(timeline)} segmentos, {t_total:.2f}s ({total_frames} frames).")
    
    qc_png = os.path.join(ROOT, "video", f"qc_parte_{parte_num:02d}.png")
    if so_qc:
        gerar_folha_qc(timeline, qc_png, parte_num=parte_num)
        return
        
    audio_master_wav = f"/tmp/parte_{parte_num:02d}_audio.wav"
    print("Mixando trilha sonora, efeitos sonoros (SFX) e vozes...")
    mixar_audio_completo(timeline, t_total, audio_master_wav, parte_num=parte_num)
    
    ass_path = os.path.join(ROOT, "legendas", f"parte_{parte_num:02d}.ass")
    os.makedirs(os.path.dirname(ass_path), exist_ok=True)
    gerar_legendas_ass(timeline, ass_path)
    
    gerar_folha_qc(timeline, qc_png, parte_num=parte_num)
    
    out_mp4 = os.path.join(ROOT, "video", f"parte_{parte_num:02d}.mp4")
    os.makedirs(os.path.dirname(out_mp4), exist_ok=True)
    
    cmd_ffmpeg = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-i", audio_master_wav,
        "-vf", f"ass={ass_path}",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        out_mp4
    ]
    
    print(f"Renderizando {total_frames} frames para {out_mp4}...")
    proc = subprocess.Popen(cmd_ffmpeg, stdin=subprocess.PIPE)
    
    for f in range(total_frames):
        t = f / float(FPS)
        segs_ativos = []
        for item in timeline:
            if item["t_ini"] <= t <= item["t_fim"]:
                segs_ativos.append(item)
                
        if len(segs_ativos) == 1:
            item = segs_ativos[0]
            f_seg = int(round((t - item["t_ini"]) * FPS))
            img_final = item["seg"].compor(f_seg)
        elif len(segs_ativos) >= 2:
            item_a, item_b = segs_ativos[0], segs_ativos[1]
            f_a = int(round((t - item_a["t_ini"]) * FPS))
            f_b = int(round((t - item_b["t_ini"]) * FPS))
            
            img_a = item_a["seg"].compor(f_a)
            img_b = item_b["seg"].compor(f_b)
            
            alpha = float(np.clip((t - item_b["t_ini"]) / XF, 0.0, 1.0))
            img_final = Image.blend(img_a, img_b, alpha)
        else:
            img_final = Image.new("RGB", (W, H), (0, 0, 0))
            
        if f < 15:
            f_in = f / 15.0
            arr_f = (np.array(img_final).astype(np.float32) * f_in).astype(np.uint8)
            img_final = Image.fromarray(arr_f)
        elif f > total_frames - 24:
            f_out = (total_frames - f) / 24.0
            arr_f = (np.array(img_final).astype(np.float32) * f_out).astype(np.uint8)
            img_final = Image.fromarray(arr_f)
            
        proc.stdin.write(img_final.tobytes())
        
        if f % 150 == 0:
            progresso = (f / float(total_frames)) * 100.0
            print(f"Progresso: {f}/{total_frames} frames ({progresso:.1f}%)")
            
    proc.stdin.close()
    proc.wait()
    print(f"=== PRODUÇÃO CONCLUÍDA COM SUCESSO: {out_mp4} ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--part", type=int, default=1, help="Número da parte (1 a 10)")
    parser.add_argument("--so-qc", action="store_true", help="Gera apenas a folha de controle de qualidade")
    args = parser.parse_args()
    
    renderizar_parte(args.part, so_qc=args.so_qc)
