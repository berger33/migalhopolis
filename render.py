#!/usr/bin/env python3
"""
MIGALHÓPOLIS — Motor de Animação 2D de Curta-Metragem (Estilo Rick and Morty).
T01E01 - O Pote.

Arquitetura:
  - Decomposição em Camadas com Inpainting Difusivo de fundo
  - Recortes articulados (Puppets/Cutouts) com respiração e atuações secundárias
  - Lip Sync anatômico com Jaw Drop ativado EXCLUSIVAMENTE quando o personagem fala
  - Cenários vivos: fumaça, vapor, ventilador girando, lâmpada oscilando, varal, Zzz
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
COR_FORÇADA = {"CIDA": (0xFF, 0xE0, 0x80)}   # Amarelo clássico da Cida
FONTE_DIR = "/usr/share/fonts/truetype/dejavu"
FONTE_BOLD = os.path.join(FONTE_DIR, "DejaVuSans-Bold.ttf")

# Personagens falantes por bloco que possuem rosto em cena e devem animar boca
FALANTE_EM_TELA = {
    5: "CIDA",      # Dona Cida na porta do mercadinho
    6: "MARTA",     # Dona Marta na igreja
    7: "SEU JORGE", # Seu Jorge no bar
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
    Preenche a área oculta sob um recorte recortado usando difusão pelas bordas.
    Executado apenas 1x na inicialização do plano (bounded ao bbox).
    """
    arr = np.array(img_rgb).astype(np.float32)
    m = np.array(mask_l) > 128
    if not np.any(m):
        return Image.fromarray(arr.astype(np.uint8))
    
    # Dilatação simples via filtro
    m_dil = uniform_filter(m.astype(np.float32), size=dilate) > 0.01
    
    # Bounding box para acelerar
    ys, xs = np.where(m_dil)
    y0, y1 = max(0, ys.min() - 4), min(arr.shape[0], ys.max() + 5)
    x0, x1 = max(0, xs.min() - 4), min(arr.shape[1], xs.max() + 5)
    
    sub_arr = arr[y0:y1, x0:x1]
    sub_m = m_dil[y0:y1, x0:x1]
    
    # Média das bordas conhecidas
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
    
    # Garante que os campos tenham o formato da sub-região
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
        
        # Máscara recortada
        mask_full = criar_mascara_poligono((self.w, self.h), pontos_poly)
        if feather > 0:
            mask_arr = uniform_filter(np.array(mask_full).astype(np.float32), size=feather*2+1)
            self.mask_full = Image.fromarray(np.clip(mask_arr, 0, 255).astype(np.uint8))
        else:
            self.mask_full = mask_full
            
        # Extrai RGBA
        self.camada_rgba = img_pil.convert("RGBA")
        self.camada_rgba.putalpha(self.mask_full)
        
        if fundo_preparado is None:
            self.fundo_limpo = inpaint_difusivo(img_pil, mask_full)
        else:
            self.fundo_limpo = fundo_preparado

    def colar(self, destino_pil, dx=0.0, dy=0.0, rot=0.0, scale_y=1.0, pivot=None, camada_override=None):
        camada = camada_override if camada_override is not None else self.camada_rgba
        
        # Escala vertical de respiração
        if scale_y != 1.0 and pivot is not None:
            px, py = pivot
            coeffs = (1.0, 0.0, 0.0, 0.0, 1.0 / scale_y, py - (py / scale_y))
            camada = camada.transform(camada.size, Image.AFFINE, coeffs, resample=Image.BICUBIC)
            
        # Rotação de acting
        if rot != 0.0:
            piv = pivot if pivot is not None else (self.w // 2, self.h // 2)
            camada = camada.rotate(rot, center=piv, resample=Image.BICUBIC)
            
        # Translação
        if dx != 0.0 or dy != 0.0:
            # Cola com offset
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
            # Montagem Tripla: Homem do Boleto e Homem do Bueiro
            poly_boleto = [(685, 245), (835, 240), (865, 330), (868, 430), (850, 560), (680, 560), (670, 430), (676, 330)]
            poly_rezando = [(1105, 315), (1245, 315), (1265, 420), (1305, 470), (1308, 622), (1100, 622), (1088, 470), (1095, 400)]
            
            mask1 = criar_mascara_poligono((self.w, self.h), poly_boleto)
            fundo1 = inpaint_difusivo(self.img0, mask1)
            mask2 = criar_mascara_poligono((self.w, self.h), poly_rezando)
            self.fundo_limpo = inpaint_difusivo(fundo1, mask2)
            
            self.recortes["boleto"] = RecortePuppet(self.img0, poly_boleto, feather=4, fundo_preparado=self.fundo_limpo)
            self.recortes["rezando"] = RecortePuppet(self.img0, poly_rezando, feather=4, fundo_preparado=self.fundo_limpo)

        elif self.id == "003":
            # Cão dormindo no pedestal da praça
            poly_cao = [(695, 240), (755, 180), (845, 168), (925, 192), (978, 252), (988, 320), (962, 355), (738, 362), (698, 330)]
            self.recortes["cao_pedestal"] = RecortePuppet(self.img0, poly_cao, feather=3)
            self.fundo_limpo = self.recortes["cao_pedestal"].fundo_limpo

        elif self.id == "004":
            # Caramelo no gabinete
            poly_caramelo = [(465, 140), (518, 92), (638, 58), (762, 52), (848, 68), (878, 138), (885, 260),
                             (910, 340), (925, 450), (875, 545), (700, 568), (558, 558), (475, 470), (450, 330), (440, 205)]
            self.recortes["caramelo_gabinete"] = RecortePuppet(self.img0, poly_caramelo, feather=4)
            self.fundo_limpo = self.recortes["caramelo_gabinete"].fundo_limpo

        elif self.id == "005":
            # Dona Cida e Caramelo com Sacola
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
        else:
            return self.img0.copy()

    # ------------------ CENAS ESPECÍFICAS ------------------

    def _animar_titulo(self, t):
        frame = self.img0.copy()
        # Deriva suave das nuvens crepusculares no topo
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
        
        # 1. Nuvens no céu
        h_sky = 220
        X, Y = np.meshgrid(np.arange(self.w), np.arange(h_sky))
        dx_ceu = (np.sin(X * 0.004 + t * 0.6) * 5.0).astype(np.float32)
        dy_ceu = (np.cos(Y * 0.008 + t * 0.4) * 2.0).astype(np.float32)
        arr = deformar_regiao(arr, (0, 0, self.w, h_sky), dx_ceu, dy_ceu)
        
        # 2. Faixa municipal ondulando com o vento (550 a 860, 545 a 620)
        box_banner = (550, 545, 860, 620)
        bw, bh = box_banner[2] - box_banner[0], box_banner[3] - box_banner[1]
        BX, BY = np.meshgrid(np.arange(bw), np.arange(bh))
        dy_banner = (np.sin(BX * 0.045 - t * 4.0) * 3.5).astype(np.float32)
        dx_banner = np.zeros_like(dy_banner)
        arr = deformar_regiao(arr, box_banner, dx_banner, dy_banner)
        
        # 3. Urubus na fiação elétrica acenando a cabeça
        urubus = [(147, 140), (224, 190), (317, 215), (427, 242)]
        for i, (ux, uy) in enumerate(urubus):
            box_u = (ux - 18, uy - 18, ux + 18, uy + 18)
            uw, uh = box_u[2] - box_u[0], box_u[3] - box_u[1]
            dy_u = np.full((uh, uw), math.sin(t * 3.0 + i * 1.6) * 2.0, dtype=np.float32)
            dx_u = np.zeros_like(dy_u)
            arr = deformar_regiao(arr, box_u, dx_u, dy_u)
            
        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")
        
        # 4. Urubu voando em asa batente cruzando o horizonte
        t_voo = (t * 0.08) % 1.2
        if t_voo <= 1.0:
            vx = int(t_voo * (self.w + 100) - 50)
            vy = int(140 + math.sin(t * 2.0) * 25)
            asa = math.sin(t * 14.0) * 7.0
            # Desenha asa e corpo estilizados
            draw.line([(vx - 14, vy - int(asa)), (vx, vy), (vx + 14, vy - int(asa))], fill=(35, 30, 40, 220), width=3)
            draw.ellipse([(vx - 4, vy - 3), (vx + 4, vy + 3)], fill=(30, 25, 35, 230))
            
        # 5. Partículas de poeira dourada flutuando
        for p in range(12):
            px = int((p * 117 + t * 18) % self.w)
            py = int((p * 79 + math.sin(t * 1.5 + p) * 20 + 350) % (self.h - 100))
            draw.ellipse([(px, py), (px + 2, py + 2)], fill=(255, 240, 200, 140))
            
        return frame

    def _animar_002(self, t):
        # Montagem Tripla: Churrasco, Boleto, Bueiro
        fundo = self.fundo_limpo.copy()
        arr = np.array(fundo)
        
        # --- PAINEL ESQUERDO: CHURRASCO ---
        # 1. Varal de roupas ondulando no vento (x: 0..230, y: 265..315)
        box_varal = (0, 265, 235, 315)
        vw, vh = box_varal[2] - box_varal[0], box_varal[3] - box_varal[1]
        VX, VY = np.meshgrid(np.arange(vw), np.arange(vh))
        dx_varal = (np.sin(VY * 0.08 + t * 3.5) * 3.0).astype(np.float32)
        dy_varal = np.zeros_like(dx_varal)
        arr = deformar_regiao(arr, box_varal, dx_varal, dy_varal)
        
        # 2. Espeto girando (x: 330..550, y: 335..375)
        box_espeto = (330, 335, 550, 375)
        ew, eh = box_espeto[2] - box_espeto[0], box_espeto[3] - box_espeto[1]
        rot_esp = math.sin(t * 4.0) * 2.2
        dy_esp = np.full((eh, ew), rot_esp, dtype=np.float32)
        dx_esp = np.zeros_like(dy_esp)
        arr = deformar_regiao(arr, box_espeto, dx_esp, dy_esp)
        
        # 3. Povo rindo com o corpo (bobs alternados)
        cabecas_churrasco = [(284, 310, 35), (397, 500, 40), (602, 470, 30), (62, 490, 25)]
        for i, (cx, cy, cr) in enumerate(cabecas_churrasco):
            box_c = (cx - cr, cy - cr, cx + cr, cy + cr)
            cw, ch = box_c[2] - box_c[0], box_c[3] - box_c[1]
            dy_bob = np.full((ch, cw), abs(math.sin(t * 3.5 + i * 1.5)) * -3.5, dtype=np.float32)
            dx_bob = np.zeros_like(dy_bob)
            arr = deformar_regiao(arr, box_c, dx_bob, dy_bob)
            
        # --- PAINEL CENTRAL: HOMEM DO BOLETO ---
        # 4. Hélice do ventilador girando (centro 718, 367, raio 30)
        box_fan = (688, 337, 748, 397)
        fw, fh = box_fan[2] - box_fan[0], box_fan[3] - box_fan[1]
        fan_patch = self.img0.crop(box_fan)
        fan_rot = fan_patch.rotate(int((t * 540) % 360), resample=Image.BICUBIC)
        mask_circ = Image.new("L", (fw, fh), 0)
        ImageDraw.Draw(mask_circ).ellipse([(2, 2), (fw - 3, fh - 3)], fill=255)
        
        fundo_pil = Image.fromarray(arr)
        fundo_pil.paste(fan_rot, (box_fan[0], box_fan[1]), mask_circ)
        
        # 5. Lâmpada de teto oscilando (pivô 842, 160)
        rot_lamp = math.sin(t * 1.8) * 3.0
        lamp_patch = self.img0.crop((800, 160, 885, 260))
        lamp_rot = lamp_patch.rotate(rot_lamp, center=(42, 10), resample=Image.BICUBIC)
        fundo_pil.paste(lamp_rot, (800, 160), lamp_rot.convert("RGBA"))
        
        # 6. Colagem do Homem do Boleto com tremor de pânico
        tremor_x = math.sin(t * 40.0) * 1.8
        tremor_y = math.cos(t * 45.0) * 1.2
        rec_boleto = self.recortes["boleto"]
        rec_boleto.colar(fundo_pil, dx=tremor_x, dy=tremor_y, scale_y=1.0 + math.sin(t * 3.0) * 0.005, pivot=(760, 550))
        
        # --- PAINEL DIREITO: DEVOTO NO BUEIRO ---
        # 7. Colagem do Devoto com balanço pendular de oração
        rot_rez = math.sin(t * 2.8) * 2.5
        rec_rez = self.recortes["rezando"]
        rec_rez.colar(fundo_pil, rot=rot_rez, pivot=(1165, 615))
        
        # --- EFEITOS DE PARTÍCULAS E VFX ---
        draw = ImageDraw.Draw(fundo_pil, "RGBA")
        
        # Fumaça da grelha de churrasco (subindo e soprando para a esquerda)
        for s in range(16):
            idade = (t * 1.2 + s * 0.18) % 2.5
            fx = int(430 - idade * 22 + math.sin(idade * 4.0) * 12)
            fy = int(250 - idade * 75)
            fr = int(10 + idade * 18)
            alpha = int(max(0, (1.0 - idade / 2.5) * 150))
            draw.ellipse([(fx - fr, fy - fr), (fx + fr, fy + fr)], fill=(160, 155, 160, alpha))
            
        # Vapor do bueiro (subindo denso à direita)
        for v in range(12):
            idade_v = (t * 1.4 + v * 0.22) % 2.2
            vx = int(1050 + math.sin(idade_v * 3.0) * 14)
            vy = int(630 - idade_v * 85)
            vr = int(12 + idade_v * 20)
            alpha_v = int(max(0, (1.0 - idade_v / 2.2) * 120))
            draw.ellipse([(vx - vr, vy - vr), (vx + vr, vy + vr)], fill=(210, 215, 220, alpha_v))
            
        # Gotas de suor escorrendo no homem do boleto
        for sw in range(3):
            idade_sw = (t * 1.6 + sw * 0.4) % 1.2
            if idade_sw < 0.9:
                sx = int(785 + idade_sw * 15)
                sy = int(320 + idade_sw * 55)
                draw.ellipse([(sx, sy), (sx + 4, sy + 7)], fill=(200, 230, 255, 210))
                
        # Gotas de lágrimas no devoto
        for lr in range(2):
            idade_lr = (t * 1.3 + lr * 0.6) % 1.4
            if idade_lr < 1.0:
                lx = int(1202 + idade_lr * 6)
                ly = int(368 + idade_lr * 42)
                draw.ellipse([(lx, ly), (lx + 3, ly + 6)], fill=(180, 220, 255, 200))
                
        # Pulso sutil de luz na lâmpada
        flicker = 1.0 + (math.sin(t * 30.0) * 0.04)
        if (int(t * 15) % 19) == 0:
            flicker = 0.82
        draw.ellipse([(800, 210), (885, 290)], fill=(255, 245, 190, int(35 * flicker)))
        
        return fundo_pil

    def _animar_003(self, t):
        # Praça central: cão no pedestal
        fundo = self.fundo_limpo.copy()
        arr = np.array(fundo)
        
        # 1. Shimmer térmico no asfalto (y: 320..520)
        box_shimmer = (0, 320, self.w, 520)
        sw, sh = box_shimmer[2] - box_shimmer[0], box_shimmer[3] - box_shimmer[1]
        SX, SY = np.meshgrid(np.arange(sw), np.arange(sh))
        dx_shim = (np.sin(SY * 0.35 + t * 5.0) * 1.8).astype(np.float32)
        dy_shim = np.zeros_like(dx_shim)
        arr = deformar_regiao(arr, box_shimmer, dx_shim, dy_shim)
        
        fundo_pil = Image.fromarray(arr)
        
        # 2. Cachorro dormindo: respiração no abdômen e micro-espasmo na orelha
        rec_cao = self.recortes["cao_pedestal"]
        scale_resp = 1.0 + math.sin(t * 2.2) * 0.007
        
        # Espasmo na orelha esquerda a cada 3.2s
        espasmo = 0.0
        ciclo_esp = t % 3.2
        if ciclo_esp < 0.2:
            espasmo = math.sin(ciclo_esp / 0.2 * math.pi) * 4.0
            
        rec_cao.colar(fundo_pil, dy=0.0, rot=espasmo, scale_y=scale_resp, pivot=(850, 355))
        
        # 3. Letras "Zzz" flutuando do focinho em curva senoidal
        draw = ImageDraw.Draw(fundo_pil, "RGBA")
        fonte_z = ler_fonte(32)
        for z in range(3):
            idade_z = (t * 0.8 + z * 0.45) % 1.8
            zx = int(940 + idade_z * 45 + math.sin(idade_z * 4.0) * 14)
            zy = int(215 - idade_z * 70)
            alpha_z = int(max(0, (1.0 - idade_z / 1.8) * 220))
            tamanho = max(18, int(22 + idade_z * 16))
            draw.text((zx, zy), "z" if z % 2 == 0 else "Z", font=ler_fonte(tamanho), fill=(40, 35, 45, alpha_z))
            
        return fundo_pil

    def _animar_004(self, t):
        # Caramelo no gabinete (close-up)
        fundo = self.fundo_limpo.copy()
        arr = np.array(fundo)
        
        # 1. Notas adesivas na parede tremulando (1240 a 1285, 200 a 310)
        box_notas = (1240, 200, 1285, 310)
        nw, nh = box_notas[2] - box_notas[0], box_notas[3] - box_notas[1]
        NX, NY = np.meshgrid(np.arange(nw), np.arange(nh))
        dx_notas = (np.sin(NY * 0.15 + t * 4.5) * 2.0).astype(np.float32)
        dy_notas = np.zeros_like(dx_notas)
        arr = deformar_regiao(arr, box_notas, dx_notas, dy_notas)
        
        # 2. Brisa na janela da esquerda (luz oscilando)
        fundo_pil = Image.fromarray(arr)
        
        # 3. Atuação do Caramelo: respiração + piscar de pálpebras
        rec_car = self.recortes["caramelo_gabinete"]
        scale_resp = 1.0 + math.sin(t * 2.0) * 0.005
        rot_nod = math.sin(t * 1.2) * 1.2
        
        camada_car = rec_car.camada_rgba.copy()
        
        # Piscar lento de olhos a cada 4.2s (duração 0.15s)
        ciclo_piscar = t % 4.2
        if ciclo_piscar < 0.16:
            fase_p = math.sin((ciclo_piscar / 0.16) * math.pi)
            # Squash vertical das pálpebras nos olhos (590, 240) e (775, 233)
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
        
        # 4. Folhas de despacho na pata tremulando (760 a 950, 390 a 560)
        box_papel = (760, 390, 950, 560)
        pw, ph = box_papel[2] - box_papel[0], box_papel[3] - box_papel[1]
        PX, PY = np.meshgrid(np.arange(pw), np.arange(ph))
        dy_papel = (np.sin(PX * 0.08 + t * 6.0) * 2.5).astype(np.float32)
        dx_papel = np.zeros_like(dy_papel)
        arr_fundo = np.array(fundo_pil)
        arr_fundo = deformar_regiao(arr_fundo, box_papel, dx_papel, dy_papel)
        
        return Image.fromarray(arr_fundo)

    def _animar_005(self, t, env_fala, falante_ativo):
        # Dona Cida e Caramelo na rua
        fundo = self.fundo_limpo.copy()
        
        # --- CARAMELO ANDANDO NA RUA ---
        # 1. Ciclo de trote com passo elástico
        trote_y = abs(math.sin(t * 12.0)) * -5.0
        trote_rot = math.sin(t * 12.0) * 2.2
        rec_cao = self.recortes["cao_rua"]
        rec_cao.colar(fundo, dy=trote_y, rot=trote_rot, pivot=(400, 676))
        
        # 2. Sacola de pão balançando como pêndulo físico (pivô na boca 278, 532)
        rot_sacola = math.sin(t * 12.0 - 0.8) * 12.0
        rec_sacola = self.recortes["sacola"]
        rec_sacola.colar(fundo, dy=trote_y, rot=rot_sacola, pivot=(278, 532))
        
        # --- DONA CIDA FALANDO NA PORTA DO MERCADINHO ---
        rec_cida = self.recortes["cida"]
        camada_cida = rec_cida.camada_rgba.copy()
        
        # 3. Acting corporal da Cida: inclinação com ênfase na voz
        rot_cida = -1.8 * env_fala
        scale_cida = 1.0 + math.sin(t * 2.5) * 0.005
        
        # 4. LIP SYNC ANATÔMICO REAL COM JAW DROP
        # Cantos da boca da Cida medidos: (826, 256) até (911, 250), queixo em 320
        if falante_ativo and env_fala > 0.08:
            arr_cida = np.array(camada_cida)
            
            # Deformação real do maxilar inferior (Jaw Drop)
            # Puxa os pixels abaixo dos lábios para baixo proporcionalmente à fala
            box_mandibula = (815, 250, 925, 335)
            mw, mh = box_mandibula[2] - box_mandibula[0], box_mandibula[3] - box_mandibula[1]
            MY, MX = np.meshgrid(np.arange(mh), np.arange(mw), indexing='ij')
            
            # Deslocamento vertical decrescente em direção ao pescoço
            jaw_drop = env_fala * 12.0
            dy_jaw = (np.clip((MY - 6) / float(mh), 0.0, 1.0) * jaw_drop).astype(np.float32)
            dx_jaw = np.zeros_like(dy_jaw)
            arr_cida = deformar_regiao(arr_cida, box_mandibula, dx_jaw, dy_jaw)
            
            # Desenha a cavidade bucal integrada entre os lábios
            camada_cida = Image.fromarray(arr_cida)
            draw_boca = ImageDraw.Draw(camada_cida, "RGBA")
            
            boca_cx, boca_cy = 868, 268 + int(jaw_drop * 0.4)
            boca_rx = int(36 + env_fala * 8)
            boca_ry = int(8 + env_fala * 24)
            
            # Cavidade escura interna
            draw_boca.ellipse([(boca_cx - boca_rx, boca_cy - boca_ry),
                               (boca_cx + boca_rx, boca_cy + boca_ry)], fill=(45, 15, 20, 245), outline=(20, 10, 15, 255), width=2)
            # Dentes superiores
            draw_boca.pieslice([(boca_cx - boca_rx + 4, boca_cy - boca_ry),
                                (boca_cx + boca_rx - 4, boca_cy + int(boca_ry * 0.3))], 0, 180, fill=(245, 245, 235, 240))
            # Língua inferior
            draw_boca.ellipse([(boca_cx - int(boca_rx * 0.6), boca_cy + int(boca_ry * 0.2)),
                               (boca_cx + int(boca_rx * 0.6), boca_cy + boca_ry)], fill=(220, 90, 105, 230))
                               
        rec_cida.colar(fundo, rot=rot_cida, scale_y=scale_cida, pivot=(868, 760), camada_override=camada_cida)
        
        # 5. Reflexos de luz nas garrafas da mercearia
        draw = ImageDraw.Draw(fundo, "RGBA")
        brilho = int(abs(math.sin(t * 3.0)) * 180)
        draw.line([(1160, 565), (1170, 575)], fill=(255, 255, 240, brilho), width=2)
        draw.line([(1170, 565), (1160, 575)], fill=(255, 255, 240, brilho), width=2)
        
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
        
        # Envelope de voz
        idx_e = min(quadro_idx, len(self.env) - 1)
        val_env = float(self.env[idx_e]) if len(self.env) else 0.0
        
        # 1. Composição viva em resolução original
        quadro_vivo = self.cena_viva.compor_frame(t_local, val_env, self.falante_ativo)
        
        # 2. Dinâmica de câmera Ken Burns
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
            
        # Respiração orgânica de câmera
        respiracao = math.sin(t_local * 1.5) * 4.0
        cx += int(respiracao)
        cy += int(math.cos(t_local * 1.8) * 3.0)
        
        # Punchlines
        if self.bloco["id"] in PUNCH_BLOCOS and quadro_idx < 8:
            cx += int((np.random.rand() - 0.5) * 14)
            cy += int((np.random.rand() - 0.5) * 14)
            
        x0 = max(0, min(sw - cw, cx - cw // 2))
        y0 = max(0, min(sh - ch, cy - ch // 2))
        crop = quadro_vivo.crop((x0, y0, x0 + cw, y0 + ch))
        return crop.resize((W, H), Image.BICUBIC)

# -----------------------------------------------------------------------------
# CARTELA DE TÍTULO
# -----------------------------------------------------------------------------

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
        
        # Zoom sutil
        sw, sh = vivo.size
        s = 1.0 + 0.05 * prog
        cw, ch = int(sw / s), int((sw / s) / (W / float(H)))
        cx, cy = sw // 2, sh // 2
        x0, y0 = max(0, cx - cw // 2), max(0, cy - ch // 2)
        frame = vivo.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BICUBIC)
        
        # Cartela de texto cinematográfica
        draw = ImageDraw.Draw(frame, "RGBA")
        alpha_texto = int(min(255, max(0, math.sin(prog * math.pi) * 320)))
        
        # Vinheta escura
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
        
        # Sombra e texto
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

def mixar_audio_completo(timeline, t_total, out_wav):
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
                
    # 2. Pista de Música (Tema no título + Cotidiano no restante)
    def carregar_mp3_como_array(caminho):
        cmd = ["ffmpeg", "-v", "error", "-i", caminho, "-f", "s16le", "-acodec", "pcm_s16le", "-ar", str(SR), "-ac", "1", "-"]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0

    tema_path = os.path.join(ROOT, "production", "audio", "beds", "tema.mp3")
    cotidiano_path = os.path.join(ROOT, "production", "audio", "beds", "cotidiano.mp3")
    churrasco_sfx = os.path.join(ROOT, "production", "audio", "sfx", "churrasqueira.mp3")
    crowd_sfx = os.path.join(ROOT, "production", "audio", "sfx", "crowd.mp3")
    
    if os.path.exists(tema_path):
        arr_tema = carregar_mp3_como_array(tema_path)
        # Fade out no tema após 8 segundos
        n_t = min(len(arr_tema), int(8.5 * SR), n_amostras)
        fade_t = np.linspace(1.0, 0.0, int(2.0 * SR))
        arr_t_cut = arr_tema[:n_t].copy()
        arr_t_cut[-len(fade_t):] *= fade_t
        pista_musica[:n_t] += arr_t_cut * 0.16
        
    if os.path.exists(cotidiano_path):
        arr_cot = carregar_mp3_como_array(cotidiano_path)
        # Loop contínuo do cotidiano de 6s até o fim
        idx_c_ini = int(6.5 * SR)
        while idx_c_ini < n_amostras:
            pedaco_len = min(len(arr_cot), n_amostras - idx_c_ini)
            pista_musica[idx_c_ini:idx_c_ini + pedaco_len] += arr_cot[:pedaco_len] * 0.11
            idx_c_ini += len(arr_cot)
            
    # 3. Pista de SFX (Churrasco no bloco 002)
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

    # 4. Mixagem e Fades de Curta-Metragem
    mix = pista_voz + pista_musica + pista_sfx
    
    # Fade in inicial (0.5s) e fade out final (0.8s)
    n_fi = int(0.5 * SR)
    n_fo = int(0.8 * SR)
    mix[:n_fi] *= np.linspace(0.0, 1.0, n_fi)
    mix[-n_fo:] *= np.linspace(1.0, 0.0, n_fo)
    
    # Normalização de segurança contra clipping (-1 dBFS pico)
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
        estilo = "CIDA" if personagem == "CIDA" else "NARRADOR"
        texto = bloco.get("texto", "").replace("\n", " ").strip()
        
        linhas.append(f"Dialogue: 0,{fmt_tempo(t_ini)},{fmt_tempo(t_fim)},{estilo},,0,0,0,,{texto}")
        
    with open(out_ass, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")

# -----------------------------------------------------------------------------
# FOLHA DE CONTROLE DE QUALIDADE (QC)
# -----------------------------------------------------------------------------

def gerar_folha_qc(timeline, out_png):
    """Gera folha de contato com 8 quadros-chave para validação visual minuciosa."""
    print("Gerando folha de contato QC...")
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
    
    quadros = []
    for rotulo, t in tempos_qc:
        f_idx = int(round(t * FPS))
        # Encontra o segmento ativo
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
        
    # Monta grade 4x2
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
    else:
        raise NotImplementedError(f"Parte {parte_num} ainda não configurada.")
        
    print(f"=== INICIANDO PRODUÇÃO: PARTE {parte_num} (BLOCOS {blocos[0]['id']} A {blocos[-1]['id']}) ===")
    
    # 1. Carrega segmentos
    segmentos = [SegmentoTitulo(dur=4.0)]
    for i, b in enumerate(blocos):
        wav = os.path.join(ROOT, "audio", f"{b['id']:03d}_{b['personagem'].lower().replace(' ', '_')}.mp3")
        # Converte mp3 para wav temporário
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
        gerar_folha_qc(timeline, qc_png)
        return
        
    # 2. Mixagem de Áudio Master
    audio_master_wav = f"/tmp/parte_{parte_num:02d}_audio.wav"
    print("Mixando trilha sonora, efeitos sonoros (SFX) e vozes...")
    mixar_audio_completo(timeline, t_total, audio_master_wav)
    
    # 3. Legendas ASS
    ass_path = os.path.join(ROOT, "legendas", f"parte_{parte_num:02d}.ass")
    os.makedirs(os.path.dirname(ass_path), exist_ok=True)
    gerar_legendas_ass(timeline, ass_path)
    
    # 4. Folha de QC prévia
    gerar_folha_qc(timeline, qc_png)
    
    # 5. Renderização de Vídeo via FFmpeg Pipe
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
    
    # Render loop
    for f in range(total_frames):
        t = f / float(FPS)
        
        # Encontra os segmentos que contribuem para este frame (crossfade)
        segs_ativos = []
        for item in timeline:
            if item["t_ini"] <= t <= item["t_fim"]:
                segs_ativos.append(item)
                
        if len(segs_ativos) == 1:
            item = segs_ativos[0]
            f_seg = int(round((t - item["t_ini"]) * FPS))
            img_final = item["seg"].compor(f_seg)
        elif len(segs_ativos) >= 2:
            # Crossfade entre dois segmentos
            item_a, item_b = segs_ativos[0], segs_ativos[1]
            f_a = int(round((t - item_a["t_ini"]) * FPS))
            f_b = int(round((t - item_b["t_ini"]) * FPS))
            
            img_a = item_a["seg"].compor(f_a)
            img_b = item_b["seg"].compor(f_b)
            
            # Peso do crossfade
            alpha = float(np.clip((t - item_b["t_ini"]) / XF, 0.0, 1.0))
            img_final = Image.blend(img_a, img_b, alpha)
        else:
            img_final = Image.new("RGB", (W, H), (0, 0, 0))
            
        # Fades cinematográficos de início e fim
        if f < 15: # Fade in primeiro 0.5s
            f_in = f / 15.0
            arr_f = (np.array(img_final).astype(np.float32) * f_in).astype(np.uint8)
            img_final = Image.fromarray(arr_f)
        elif f > total_frames - 24: # Fade out últimos 0.8s
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
