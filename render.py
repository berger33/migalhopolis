#!/usr/bin/env python3
"""
MIGALHÓPOLIS — Motor de Animação 2D de Curta-Metragem (Estilo Rick and Morty).
T01E01 - O Pote.
Suporta Partes 1 a 4 (blocos 1-28).

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
    17: "SEU_JORGE",  # Seu Jorge vitorioso com o prato cheio
    18: "ZECA",       # Zeca advogado de seis dedos na mesa
    19: "CARAMELO",   # Caramelo no gabinete falando
    20: "ZECA",       # Zeca na logística do caminhão
    21: "CARAMELO",   # Caramelo na mesa apontando a planta cancelada
    22: "ZECA",       # Zeca na obra lamacenta com filhotes operários
    23: "ZECA",       # Zeca médico fajuto no consultório
    24: "CARAMELO",   # Caramelo em close com a linguiça de THC
    25: "ZECA",       # Zeca carimbando o abatimento no IPTU
    26: "PARDAL",     # Pardal humilhando moradores no poste eleitoral
    27: "ZECA",       # Zeca apavorado com o celular da Dona Marta
    28: "PARDAL",     # Pardal desesperado com a calculadora de votos
    30: "REPORTER",   # Repórter TV Onze Crônica no debate ao vivo da praça
    31: "PARDAL",     # Pardal em close absoluto (PUNCH) — "Como assim, senhor?"
    32: "REPORTER",   # Repórter na sabatina da juventude
    33: "PARDAL",     # Pardal diante da máquina pública
    34: "REPORTER",   # Repórter no estúdio com globo holográfico
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

def deformar_jaw(arr, box, env_fala, forca, t=0.0, tremor=0.0):
    """
    Lip sync anatômico: jaw drop da mandíbula proporcional ao envelope de fala.
    A porção inferior da caixa desce mais (peso_y^1.5); tremor opcional para
    gagueira/raiva/pânico (boca e queixo oscilando na horizontal).
    """
    x0, y0, x1, y1 = box
    mw, mh = x1 - x0, y1 - y0
    if mw <= 0 or mh <= 0:
        return arr
    MY, MX = np.meshgrid(np.arange(mh), np.arange(mw), indexing='ij')
    jaw = env_fala * forca
    peso_y = np.clip((MY - 5) / float(max(1, mh - 5)), 0.0, 1.0) ** 1.5
    dy = (peso_y * jaw).astype(np.float32)
    dx = np.zeros_like(dy)
    if tremor > 0.0:
        dx += (peso_y * np.sin(t * 38.0) * (tremor * env_fala)).astype(np.float32)
    return deformar_regiao(arr, box, dx, dy)

def desenhar_boca(draw, cx, cy, rx, ry, canino=True):
    """
    Cavidade bucal ancorada nos cantos reais da boca do desenho:
    interior escuro + arcada dentária + língua; presas quando canino=True.
    """
    draw.ellipse([(cx - rx, cy - ry), (cx + rx, cy + ry)],
                 fill=(45, 15, 20, 245), outline=(20, 10, 15, 255), width=2)
    draw.pieslice([(cx - rx + 4, cy - ry), (cx + rx - 4, cy + int(ry * 0.3))],
                  0, 180, fill=(245, 245, 235, 240))
    if canino:
        d = max(2, int(rx * 0.10))
        draw.polygon([(cx - int(rx * 0.55), cy - int(ry * 0.55)),
                      (cx - int(rx * 0.55) + d * 2, cy - int(ry * 0.55)),
                      (cx - int(rx * 0.55) + d, cy + int(ry * 0.25))], fill=(250, 250, 245, 245))
        draw.polygon([(cx + int(rx * 0.55), cy - int(ry * 0.55)),
                      (cx + int(rx * 0.55) - d * 2, cy - int(ry * 0.55)),
                      (cx + int(rx * 0.55) - d, cy + int(ry * 0.25))], fill=(250, 250, 245, 245))
    draw.ellipse([(cx - int(rx * 0.6), cy + int(ry * 0.2)), (cx + int(rx * 0.6), cy + max(1, ry))],
                 fill=(220, 90, 105, 230))

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

        elif self.id == "021":
            # Filhotes operários com capacete M (medo em uníssono)
            poly_filhotes = [(945, 455), (1015, 385), (1105, 375), (1195, 385), (1265, 455),
                             (1275, 585), (1245, 672), (1125, 685), (1005, 675), (955, 595)]
            self.recortes["filhotes"] = RecortePuppet(self.img0, poly_filhotes, feather=4)
            self.fundo_limpo = self.recortes["filhotes"].fundo_limpo

        elif self.id == "022":
            # Filhotes de obra com pá + placa ASSOCIACAO DE MORADORES CANINOS
            poly_filhotes2 = [(855, 435), (915, 388), (1015, 378), (1125, 385), (1205, 405),
                              (1262, 485), (1268, 605), (1215, 678), (1105, 692), (975, 682),
                              (885, 625), (848, 525)]
            poly_placa = [(1168, 425), (1338, 418), (1345, 520), (1330, 552), (1180, 555), (1162, 505)]
            mask1 = criar_mascara_poligono((self.w, self.h), poly_filhotes2)
            fundo1 = inpaint_difusivo(self.img0, mask1)
            mask2 = criar_mascara_poligono((self.w, self.h), poly_placa)
            self.fundo_limpo = inpaint_difusivo(fundo1, mask2)
            self.recortes["filhotes2"] = RecortePuppet(self.img0, poly_filhotes2, feather=4, fundo_preparado=self.fundo_limpo)
            self.recortes["placa"] = RecortePuppet(self.img0, poly_placa, feather=3, fundo_preparado=self.fundo_limpo)

        elif self.id == "023":
            # Planta carnívora no vaso (mastigando mosca)
            poly_planta = [(245, 445), (275, 365), (335, 338), (405, 345), (465, 395),
                           (475, 475), (445, 555), (415, 645), (405, 715), (300, 722), (252, 645), (238, 535)]
            self.recortes["planta"] = RecortePuppet(self.img0, poly_planta, feather=4)
            self.fundo_limpo = self.recortes["planta"].fundo_limpo

        elif self.id == "024":
            # Linguiça radioativa na pata erguida do Caramelo
            poly_linguica_pata = [(905, 505), (955, 425), (1045, 335), (1155, 305), (1255, 335),
                                  (1292, 425), (1265, 545), (1215, 625), (1125, 645), (1025, 635),
                                  (955, 595), (912, 555)]
            self.recortes["linguica_pata"] = RecortePuppet(self.img0, poly_linguica_pata, feather=4)
            self.fundo_limpo = self.recortes["linguica_pata"].fundo_limpo

        elif self.id == "025":
            # Carimbo de madeira gigante (sobe e desce com impacto)
            poly_carimbo = [(520, 345), (575, 328), (625, 345), (645, 405), (652, 465),
                            (628, 512), (555, 518), (518, 475), (512, 405)]
            self.recortes["carimbo"] = RecortePuppet(self.img0, poly_carimbo, feather=4)
            self.fundo_limpo = self.recortes["carimbo"].fundo_limpo

        elif self.id == "026":
            # Braço do Pardal apontando freneticamente para o poste
            poly_braco = [(448, 392), (505, 378), (565, 385), (588, 415), (565, 452),
                          (515, 468), (462, 462), (440, 432)]
            self.recortes["braco"] = RecortePuppet(self.img0, poly_braco, feather=3)
            self.fundo_limpo = self.recortes["braco"].fundo_limpo

        elif self.id == "028":
            # Calculadora na mão trêmula + bandeira do Brasil tremulando
            poly_calc = [(855, 505), (915, 462), (1025, 452), (1105, 468), (1132, 535),
                         (1125, 615), (1075, 652), (955, 655), (882, 615), (848, 555)]
            poly_bandeira = [(1105, 95), (1245, 85), (1352, 105), (1365, 185), (1335, 238),
                             (1225, 252), (1125, 228), (1098, 165)]
            mask1 = criar_mascara_poligono((self.w, self.h), poly_calc)
            fundo1 = inpaint_difusivo(self.img0, mask1)
            mask2 = criar_mascara_poligono((self.w, self.h), poly_bandeira)
            self.fundo_limpo = inpaint_difusivo(fundo1, mask2)
            self.recortes["calculadora"] = RecortePuppet(self.img0, poly_calc, feather=3, fundo_preparado=self.fundo_limpo)
            self.recortes["bandeira"] = RecortePuppet(self.img0, poly_bandeira, feather=3, fundo_preparado=self.fundo_limpo)

        elif self.id == "035":
            # Urna de papelão sendo comida pelo Caramelo (sacode a cada mordida)
            poly_urna = [(412, 632), (505, 622), (612, 618), (652, 640), (658, 700),
                         (648, 764), (500, 768), (415, 760), (405, 700)]
            self.recortes["urna"] = RecortePuppet(self.img0, poly_urna, feather=4)
            self.fundo_limpo = self.recortes["urna"].fundo_limpo

        elif self.id == "036":
            # Martelo do juiz vibrando sobre a mesa da lei
            poly_martelo = [(898, 512), (965, 495), (1018, 505), (1042, 545),
                            (1030, 600), (985, 635), (930, 628), (895, 575)]
            self.recortes["martelo"] = RecortePuppet(self.img0, poly_martelo, feather=3)
            self.fundo_limpo = self.recortes["martelo"].fundo_limpo

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
        elif self.id == "014":
            return self._animar_014(t)
        elif self.id == "015":
            return self._animar_015(t)
        elif self.id == "016":
            return self._animar_016(t)
        elif self.id == "017":
            return self._animar_017(t, env_fala, falante_ativo)
        elif self.id == "018":
            return self._animar_018(t, env_fala, falante_ativo)
        elif self.id == "019":
            return self._animar_019(t, env_fala, falante_ativo)
        elif self.id == "020":
            return self._animar_020(t, env_fala, falante_ativo)
        elif self.id == "021":
            return self._animar_021(t, env_fala, falante_ativo)
        elif self.id == "022":
            return self._animar_022(t, env_fala, falante_ativo)
        elif self.id == "023":
            return self._animar_023(t, env_fala, falante_ativo)
        elif self.id == "024":
            return self._animar_024(t, env_fala, falante_ativo)
        elif self.id == "025":
            return self._animar_025(t, env_fala, falante_ativo)
        elif self.id == "026":
            return self._animar_026(t, env_fala, falante_ativo)
        elif self.id == "027":
            return self._animar_027(t, env_fala, falante_ativo)
        elif self.id == "028":
            return self._animar_028(t, env_fala, falante_ativo)
        elif self.id == "029":
            return self._animar_029(t)
        elif self.id == "030":
            return self._animar_030(t, env_fala, falante_ativo)
        elif self.id == "031":
            return self._animar_031(t, env_fala, falante_ativo)
        elif self.id == "032":
            return self._animar_032(t, env_fala, falante_ativo)
        elif self.id == "033":
            return self._animar_033(t, env_fala, falante_ativo)
        elif self.id == "034":
            return self._animar_034(t, env_fala, falante_ativo)
        elif self.id == "035":
            return self._animar_035(t)
        elif self.id == "036":
            return self._animar_036(t)
        elif self.id == "037":
            return self._animar_037(t)
        elif self.id == "038":
            return self._animar_038(t)
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

    # ------------------ CENAS PARTE 3 ------------------

    def _animar_014(self, t):
        # Homem idoso com dúvida existencial / Álbum de fotos (Narrador em off - zero boca mexendo)
        frame = self.img0.copy()
        draw = ImageDraw.Draw(frame, "RGBA")
        
        # 1. Ponto de interrogação neon pulsando acima da cabeça (675, 75)
        pulso_neon = 0.7 + 0.3 * math.sin(t * 5.0)
        alpha_neon = int(180 * pulso_neon)
        raio_neon = int(22 + 4 * pulso_neon)
        draw.ellipse([(675 - raio_neon, 75 - raio_neon), (675 + raio_neon, 75 + raio_neon)], fill=(255, 230, 80, int(alpha_neon * 0.3)))
        draw.ellipse([(675 - int(raio_neon * 0.6), 75 - int(raio_neon * 0.6)), (675 + int(raio_neon * 0.6), 75 + int(raio_neon * 0.6))], fill=(255, 245, 120, int(alpha_neon * 0.6)))
        
        # 2. Balão de pensamento ondulando suavemente no ar (50 a 420, 20 a 220)
        box_balao = (50, 20, 420, 220)
        bw, bh = box_balao[2] - box_balao[0], box_balao[3] - box_balao[1]
        BX, BY = np.meshgrid(np.arange(bw), np.arange(bh))
        dy_balao = (np.sin(BX * 0.03 + t * 2.5) * 2.2).astype(np.float32)
        dx_balao = (np.cos(BY * 0.03 + t * 2.0) * 1.5).astype(np.float32)
        arr = np.array(frame)
        arr = deformar_regiao(arr, box_balao, dx_balao, dy_balao)
        
        # 3. Páginas do álbum de fotos oscilando sutilmente (920 a 1180, 120 a 320)
        box_album = (920, 120, 1180, 320)
        aw, ah = box_album[2] - box_album[0], box_album[3] - box_album[1]
        AX, AY = np.meshgrid(np.arange(aw), np.arange(ah))
        dy_album = (np.sin(AX * 0.04 + t * 3.2) * 1.8).astype(np.float32)
        dx_album = np.zeros_like(dy_album)
        arr = deformar_regiao(arr, box_album, dx_album, dy_album)
        
        frame = Image.fromarray(arr)
        draw2 = ImageDraw.Draw(frame, "RGBA")
        
        # 4. Partículas de poeira suspensas no feixe de luz
        for p in range(12):
            px = int((p * 113 + t * 15) % self.w)
            py = int((p * 67 + math.sin(t * 1.8 + p) * 16 + 180) % (self.h - 100))
            draw2.ellipse([(px, py), (px + 2, py + 2)], fill=(255, 245, 200, 120))
            
        return frame

    def _animar_015(self, t):
        # Bueiro reluzente e Caramelo no cofre aberto (Narrador em off - zero boca mexendo)
        frame = self.img0.copy()
        arr = np.array(frame)
        
        # 1. Caramelo comendo no pote dourado dentro do cofre (880 a 1150, 340 a 600)
        box_caramelo = (880, 340, 1150, 600)
        cw, ch = box_caramelo[2] - box_caramelo[0], box_caramelo[3] - box_caramelo[1]
        CY, CX = np.meshgrid(np.arange(ch), np.arange(cw), indexing='ij')
        mastiga = abs(math.sin(t * 6.0)) * -4.0
        dy_mast = (np.clip((ch - CY) / float(ch), 0.0, 1.0) * mastiga).astype(np.float32)
        dx_mast = np.zeros_like(dy_mast)
        arr = deformar_regiao(arr, box_caramelo, dx_mast, dy_mast)
        
        # 2. Rabinho abanando feliz no cofre (1080 a 1160, 480 a 560)
        box_rabo = (1080, 480, 1160, 560)
        rw, rh = box_rabo[2] - box_rabo[0], box_rabo[3] - box_rabo[1]
        RY, RX = np.meshgrid(np.arange(rh), np.arange(rw), indexing='ij')
        abano = math.sin(t * 14.0) * 4.0
        dx_rabo = (np.clip((rh - RY) / float(rh), 0.0, 1.0) * abano).astype(np.float32)
        dy_rabo = np.zeros_like(dx_rabo)
        arr = deformar_regiao(arr, box_rabo, dx_rabo, dy_rabo)
        
        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")
        
        # 3. Brilho metálico estelar pulsante na tampa do bueiro (480, 580)
        ciclo_brilho = (t * 0.45) % 1.0
        if ciclo_brilho < 0.25:
            fase_b = math.sin(ciclo_brilho / 0.25 * math.pi)
            bx, by = 480, 580
            br = int(fase_b * 16)
            alpha_b = int(fase_b * 240)
            draw.line([(bx - br, by), (bx + br, by)], fill=(255, 255, 240, alpha_b), width=2)
            draw.line([(bx, by - br), (bx, by + br)], fill=(255, 255, 240, alpha_b), width=2)
            draw.ellipse([(bx - 3, by - 3), (bx + 3, by + 3)], fill=(255, 255, 255, alpha_b))
            
        # 4. Reflexos de luz no ouro do cofre
        for g in range(4):
            gx = int(950 + g * 60)
            gy = int(540 + math.sin(t * 3.0 + g) * 8)
            g_alpha = int(abs(math.sin(t * 2.5 + g * 1.2)) * 180)
            draw.ellipse([(gx - 2, gy - 2), (gx + 2, gy + 2)], fill=(255, 240, 180, g_alpha))
            
        return frame

    def _animar_016(self, t):
        # Caramelo no pedestal farejando / Multidão faminta (Narrador em off - zero boca mexendo)
        frame = self.img0.copy()
        arr = np.array(frame)
        
        # 1. Focinho farejando o ar (590 a 640, 250 a 290)
        box_focinho = (590, 250, 640, 290)
        fw, fh = box_focinho[2] - box_focinho[0], box_focinho[3] - box_focinho[1]
        farejo = math.sin(t * 9.0) * 2.2
        dy_farejo = np.full((fh, fw), farejo, dtype=np.float32)
        dx_farejo = np.zeros_like(dy_farejo)
        arr = deformar_regiao(arr, box_focinho, dx_farejo, dy_farejo)
        
        # 2. Olhos semicerrados do Caramelo piscando a cada 3.2s
        ciclo_p = t % 3.2
        if ciclo_p < 0.14:
            fase_p = math.sin((ciclo_p / 0.14) * math.pi)
            box_olhos = (560, 210, 680, 250)
            ow, oh = box_olhos[2] - box_olhos[0], box_olhos[3] - box_olhos[1]
            OY, OX = np.meshgrid(np.arange(oh), np.arange(ow), indexing='ij')
            dy_o = ((OY - (oh / 2.0)) * (fase_p * 0.8)).astype(np.float32)
            dx_o = np.zeros_like(dy_o)
            arr = deformar_regiao(arr, box_olhos, dx_o, dy_o)
            
        # 3. Multidão faminta abaixo suplicando com movimentos sutis (50 a 580, 480 a 760)
        box_povo = (50, 480, 580, 760)
        pw, ph = box_povo[2] - box_povo[0], box_povo[3] - box_povo[1]
        PY, PX = np.meshgrid(np.arange(ph), np.arange(pw), indexing='ij')
        dy_povo = (np.sin(PX * 0.05 + t * 3.0) * 2.5).astype(np.float32)
        dx_povo = np.zeros_like(dy_povo)
        arr = deformar_regiao(arr, box_povo, dx_povo, dy_povo)
        
        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")
        
        # 4. Fumaça aromática subindo dos caldeirões de incenso (50, 680) e (1220, 680)
        for f in range(12):
            idade_f = (t * 1.2 + f * 0.2) % 2.0
            fx1 = int(75 + math.sin(idade_f * 3.5) * 12 + idade_f * 15)
            fy1 = int(660 - idade_f * 95)
            fr1 = int(10 + idade_f * 18)
            alpha_f1 = int(max(0, (1.0 - idade_f / 2.0) * 120))
            draw.ellipse([(fx1 - fr1, fy1 - fr1), (fx1 + fr1, fy1 + fr1)], fill=(200, 195, 210, alpha_f1))
            
            fx2 = int(1230 - math.sin(idade_f * 3.5) * 12 - idade_f * 15)
            fy2 = int(660 - idade_f * 95)
            fr2 = int(10 + idade_f * 18)
            alpha_f2 = int(max(0, (1.0 - idade_f / 2.0) * 120))
            draw.ellipse([(fx2 - fr2, fy2 - fr2), (fx2 + fr2, fy2 + fr2)], fill=(200, 195, 210, alpha_f2))
            
        return frame

    def _animar_017(self, t, env_fala, falante_ativo):
        # Seu Jorge vitorioso com o prato de comida / Ventilador girando
        frame = self.img0.copy()
        
        # 1. Ventilador de parede girando (1020, 50, 1080, 110)
        box_fan = (1020, 50, 1080, 110)
        fw, fh = box_fan[2] - box_fan[0], box_fan[3] - box_fan[1]
        fan_patch = self.img0.crop(box_fan)
        fan_rot = fan_patch.rotate(int((t * 540) % 360), resample=Image.BICUBIC)
        mask_circ = Image.new("L", (fw, fh), 0)
        ImageDraw.Draw(mask_circ).ellipse([(2, 2), (fw - 3, fh - 3)], fill=255)
        frame.paste(fan_rot, (box_fan[0], box_fan[1]), mask_circ)
        arr = np.array(frame)
        
        # 2. Punho erguido de Seu Jorge vibrando vitorioso (800 a 870, 40 a 140)
        fist_bob = abs(math.sin(t * 5.0)) * -4.0
        box_fist = (800, 40, 870, 140)
        fw_f, fh_f = box_fist[2] - box_fist[0], box_fist[3] - box_fist[1]
        dy_fist = np.full((fh_f, fw_f), fist_bob, dtype=np.float32)
        dx_fist = np.zeros_like(dy_fist)
        arr = deformar_regiao(arr, box_fist, dx_fist, dy_fist)
        
        # 3. Prato de comida tremendo de alegria (720 a 820, 310 a 390)
        box_prato = (720, 310, 820, 390)
        pw, ph = box_prato[2] - box_prato[0], box_prato[3] - box_prato[1]
        dy_prato = np.full((ph, pw), math.sin(t * 8.0) * 1.5, dtype=np.float32)
        dx_prato = np.zeros_like(dy_prato)
        arr = deformar_regiao(arr, box_prato, dx_prato, dy_prato)
        
        # 4. Triste burocrata ao fundo com o esfregão abaixando ombros (1040 a 1220, 280 a 680)
        box_bur = (1040, 280, 1220, 680)
        bw, bh = box_bur[2] - box_bur[0], box_bur[3] - box_bur[1]
        BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        dy_bur = (np.clip((bh - BY) / float(bh), 0.0, 1.0) * (math.sin(t * 1.5) * 2.0)).astype(np.float32)
        dx_bur = np.zeros_like(dy_bur)
        arr = deformar_regiao(arr, box_bur, dx_bur, dy_bur)
        
        # 5. Lip sync anatômico de Seu Jorge
        if falante_ativo and env_fala > 0.06:
            box17 = (830, 215, 935, 330)
            mw, mh = box17[2] - box17[0], box17[3] - box17[1]
            MY, MX = np.meshgrid(np.arange(mh), np.arange(mw), indexing='ij')
            jaw_drop = env_fala * 14.0
            peso_y = np.clip((MY - 8) / float(mh - 8), 0.0, 1.0) ** 1.8
            dy_jaw = (peso_y * jaw_drop).astype(np.float32)
            arr = deformar_regiao(arr, box17, np.zeros_like(dy_jaw), dy_jaw)
            
        return Image.fromarray(arr)

    def _animar_018(self, t, env_fala, falante_ativo):
        # Zeca advogado de 6 dedos / Mesa cheia de processos
        frame = self.img0.copy()
        arr = np.array(frame)
        
        # 1. Pata de 6 dedos deslizando a pilha de processos sobre a mesa (530 a 750, 280 a 440)
        deslize_papeis = -6.0 * (env_fala if falante_ativo else 0.0) + math.sin(t * 2.0) * 1.5
        box_pap = (530, 280, 750, 440)
        pw, ph = box_pap[2] - box_pap[0], box_pap[3] - box_pap[1]
        dx_pap = np.full((ph, pw), deslize_papeis, dtype=np.float32)
        dy_pap = np.zeros_like(dx_pap)
        arr = deformar_regiao(arr, box_pap, dx_pap, dy_pap)
        
        # 2. Lip sync anatômico do Dr. Zeca na linha do sorriso com dentes caninos e língua
        if falante_ativo and env_fala > 0.08:
            box18 = (790, 240, 910, 350)
            mw, mh = box18[2] - box18[0], box18[3] - box18[1]
            MY, MX = np.meshgrid(np.arange(mh), np.arange(mw), indexing='ij')
            jaw_drop = env_fala * 9.0
            peso_y = np.clip((MY - 5) / float(mh - 5), 0.0, 1.0)
            dy_jaw = (peso_y * jaw_drop).astype(np.float32)
            arr = deformar_regiao(arr, box18, np.zeros_like(dy_jaw), dy_jaw)
            
            frame = Image.fromarray(arr)
            d18 = ImageDraw.Draw(frame, "RGBA")
            cx, cy = 855, 268 + int(jaw_drop * 0.3)
            rx, ry = int(18 + env_fala * 5), int(8 + env_fala * 6)
            d18.ellipse([(cx - rx, cy - ry), (cx + rx, cy + ry)], fill=(35, 12, 18, 245), outline=(20, 10, 15, 255), width=2)
            d18.polygon([(cx - 14, cy - ry + 1), (cx - 10, cy - 1), (cx - 6, cy - ry + 1)], fill=(245, 245, 235, 240))
            d18.polygon([(cx + 6, cy - ry + 1), (cx + 10, cy - 1), (cx + 14, cy - ry + 1)], fill=(245, 245, 235, 240))
            d18.ellipse([(cx - 12, cy + 1), (cx + 12, cy + ry)], fill=(215, 50, 70, 220))
        else:
            frame = Image.fromarray(arr)
            
        draw = ImageDraw.Draw(frame, "RGBA")
        
        # 3. Donut radioativo alienígena na mesa pulsando com brilho verde/rosa neon (640, 600)
        pulso_donut = 0.6 + 0.4 * math.sin(t * 4.0)
        alpha_donut = int(140 * pulso_donut)
        draw.ellipse([(620, 580), (660, 620)], fill=(80, 255, 120, int(alpha_donut * 0.4)))
        draw.ellipse([(628, 588), (652, 612)], fill=(255, 100, 220, int(alpha_donut * 0.6)))
        
        return frame

    def _animar_019(self, t, env_fala, falante_ativo):
        # Caramelo nos 4 painéis de liderança / Lip sync nos painéis ativos
        frame = self.img0.copy()
        arr = np.array(frame)
        
        # 1. Piscar de olhos semicerrados com desdém de governante a cada 3.5s
        ciclo_p = t % 3.5
        if ciclo_p < 0.15:
            fase_p = math.sin((ciclo_p / 0.15) * math.pi)
            for ox in [170, 520, 870, 1220]:
                box_olho = (ox - 45, 310, ox + 45, 360)
                ow, oh = box_olho[2] - box_olho[0], box_olho[3] - box_olho[1]
                OY, OX = np.meshgrid(np.arange(oh), np.arange(ow), indexing='ij')
                dy_o = ((OY - (oh / 2.0)) * (fase_p * 0.75)).astype(np.float32)
                arr = deformar_regiao(arr, box_olho, np.zeros_like(dy_o), dy_o)
                
        # 2. Pata erguida com gesto de comando nos painéis 3 e 4 (810 a 890, 530 a 640)
        box_pata = (810, 530, 890, 640)
        pw, ph = box_pata[2] - box_pata[0], box_pata[3] - box_pata[1]
        rot_pata = math.sin(t * 3.0) * 3.0
        dy_pata = np.full((ph, pw), rot_pata, dtype=np.float32)
        arr = deformar_regiao(arr, box_pata, np.zeros_like(dy_pata), dy_pata)
        
        frame = Image.fromarray(arr)
        
        # 3. Lip sync anatômico do Caramelo nos painéis com caninos afiados e língua
        if falante_ativo and env_fala > 0.08:
            d19 = ImageDraw.Draw(frame, "RGBA")
            for cx, cy in [(430, 448), (880, 448)]:
                rx = int(18 + env_fala * 5)
                ry = int(9 + env_fala * 5)
                d19.ellipse([(cx - rx, cy - ry), (cx + rx, cy + ry)], fill=(35, 12, 18, 245), outline=(20, 10, 15, 255), width=2)
                d19.polygon([(cx - 14, cy - ry + 2), (cx - 10, cy - 1), (cx - 6, cy - ry + 2)], fill=(245, 245, 235, 240))
                d19.polygon([(cx + 6, cy - ry + 2), (cx + 10, cy - 1), (cx + 14, cy - ry + 2)], fill=(245, 245, 235, 240))
                d19.ellipse([(cx - 12, cy + 1), (cx + 12, cy + ry)], fill=(215, 50, 70, 220))
                
        draw = ImageDraw.Draw(frame, "RGBA")
        
        # 4. Brilho metálico dourado na medalha da faixa de prefeito (painéis 3 e 4)
        for mx in [890, 1240]:
            my = 635
            glint = int(abs(math.sin(t * 3.5 + (mx / 500.0))) * 220)
            draw.line([(mx - 6, my), (mx + 6, my)], fill=(255, 255, 220, glint), width=2)
            draw.line([(mx, my - 6), (mx, my + 6)], fill=(255, 255, 220, glint), width=2)
            
        return frame

    def _animar_020(self, t, env_fala, falante_ativo):
        # Zeca na logística do caixão / Whiteboard / Caminhão escuro
        frame = self.img0.copy()
        arr = np.array(frame)
        
        # 1. Caixão oscilando na rampa do caminhão (580 a 820, 440 a 620)
        box_caixao = (580, 440, 820, 620)
        cw, ch = box_caixao[2] - box_caixao[0], box_caixao[3] - box_caixao[1]
        balanco_caixao = math.sin(t * 3.2) * 2.2
        dy_c = np.full((ch, cw), balanco_caixao, dtype=np.float32)
        arr = deformar_regiao(arr, box_caixao, np.zeros_like(dy_c), dy_c)
        
        # 2. Cão operário com capacete empurrando o caixão (560 a 640, 520 a 680)
        box_oper = (560, 520, 640, 680)
        ow, oh = box_oper[2] - box_oper[0], box_oper[3] - box_oper[1]
        empurrao = abs(math.sin(t * 4.5)) * -3.0
        dy_op = np.full((oh, ow), empurrao, dtype=np.float32)
        arr = deformar_regiao(arr, box_oper, np.zeros_like(dy_op), dy_op)
        
        # 3. Braço de Zeca gesticulando para a lousa e para o caminhão (870 a 950, 540 a 620)
        box_braco = (870, 540, 950, 620)
        bw, bh = box_braco[2] - box_braco[0], box_braco[3] - box_braco[1]
        rot_braco = math.sin(t * 4.0) * 3.0
        dy_b = np.full((bh, bw), rot_braco, dtype=np.float32)
        arr = deformar_regiao(arr, box_braco, np.zeros_like(dy_b), dy_b)
        
        # 4. Lip sync anatômico do Zeca na boca desenhada existente
        if falante_ativo and env_fala > 0.07:
            box20 = (840, 385, 930, 480)
            mw, mh = box20[2] - box20[0], box20[3] - box20[1]
            MY, MX = np.meshgrid(np.arange(mh), np.arange(mw), indexing='ij')
            jaw_drop = env_fala * 10.0
            peso_y = np.clip((MY - 5) / float(mh - 5), 0.0, 1.0) ** 1.5
            dy_jaw = (peso_y * jaw_drop).astype(np.float32)
            arr = deformar_regiao(arr, box20, np.zeros_like(dy_jaw), dy_jaw)
            
        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")
        
        # 5. Faróis do caminhão emitindo feixe sutil de luz volumétrica (750 a 1050, 180 a 350)
        feixe_alpha = int(45 + 15 * math.sin(t * 2.5))
        draw.polygon([(780, 200), (810, 200), (960, 340), (740, 340)], fill=(255, 255, 220, feixe_alpha))
        
        # 6. Seta e fluxograma na lousa pulsando com giz suave (1020 a 1280, 420 a 580)
        giz_alpha = int(120 + 60 * math.sin(t * 3.0))
        draw.ellipse([(1180, 460), (1210, 490)], outline=(255, 255, 255, giz_alpha), width=2)
        
        return frame

    # ------------------ CENAS PARTE 4 (BLOCOS 021-028) ------------------

    def _animar_021(self, t, env_fala, falante_ativo):
        # Caramelo autoritário: planta cancelada com X, filhotes tremendo, lava lamp, lousa
        fundo = self.fundo_limpo.copy()

        # 1. Filhotes operários tremendo de medo em uníssono
        trem = math.sin(t * 26.0) * (1.2 + 1.8 * env_fala)
        self.recortes["filhotes"].colar(fundo, dx=trem, dy=abs(math.sin(t * 31.0)) * -1.0,
                                        rot=math.sin(t * 23.0 + 1.0) * 0.7, pivot=(1110, 685))

        arr = np.array(fundo)

        # 2. Pata apontando com ênfase executiva (batidas sincronizadas à fala)
        box_braco = (825, 330, 935, 405)
        bw, bh = box_braco[2] - box_braco[0], box_braco[3] - box_braco[1]
        empurrao = (abs(math.sin(t * 7.5)) ** 3) * -4.5 * (0.4 + 0.6 * env_fala)
        dy_b = np.full((bh, bw), empurrao, dtype=np.float32)
        arr = deformar_regiao(arr, box_braco, np.zeros_like(dy_b), dy_b)

        # 3. Respiração do tronco (squash & stretch sutil)
        box_tronco = (555, 335, 835, 620)
        tw_, th_ = box_tronco[2] - box_tronco[0], box_tronco[3] - box_tronco[1]
        dy_t = np.full((th_, tw_), math.sin(t * 2.1) * 1.4, dtype=np.float32)
        arr = deformar_regiao(arr, box_tronco, np.zeros_like(dy_t), dy_t)

        # 4. Lip sync anatômico autoritário (mandíbula + presas)
        if falante_ativo and env_fala > 0.07:
            arr = deformar_jaw(arr, (655, 255, 775, 365), env_fala, 12.0, t=t, tremor=0.6)

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        if falante_ativo and env_fala > 0.07:
            desenhar_boca(draw, 712, 305 + int(env_fala * 4.8), int(34 + env_fala * 6), int(8 + env_fala * 22), canino=True)

        # 5. X vermelho piscando na planta de engenharia cancelada
        x_alpha = int(150 + 105 * math.sin(t * 5.2))
        draw.line([(378, 268), (528, 438)], fill=(255, 30, 30, x_alpha), width=12)
        draw.line([(528, 268), (378, 438)], fill=(255, 30, 30, x_alpha), width=12)

        # 6. Brilho de papel desenrolado na mesa
        brilho_papel = int(40 + 25 * math.sin(t * 1.7))
        draw.line([(300, 240), (520, 250)], fill=(255, 255, 255, brilho_papel), width=3)

        # 7. Lava lamp borbulhando (285-345, 345-425)
        for k in range(3):
            fase = (t * 0.35 + k * 0.33) % 1.0
            y_blob = 420 - fase * 70
            rx_b = int(14 + 7 * math.sin(fase * math.pi))
            alpha_b = int(120 + 60 * math.sin(t * 2.2 + k))
            draw.ellipse([(312 - rx_b, y_blob - rx_b), (312 + rx_b, y_blob + rx_b)],
                         fill=(255, 110, 190, alpha_b))

        # 8. Lâmpada verde pulsando no trilho (235-315, 85-135)
        glow_g = int(70 + 45 * math.sin(t * 2.8))
        draw.ellipse([(238, 88), (312, 132)], fill=(140, 255, 120, glow_g))

        # 9. Equações na lousa técnica reluzindo
        giz = int(60 + 35 * math.sin(t * 1.3))
        draw.line([(1095, 215), (1275, 225)], fill=(235, 245, 255, giz), width=2)
        draw.line([(1120, 315), (1335, 305)], fill=(235, 245, 255, giz), width=2)

        return frame

    def _animar_022(self, t, env_fala, falante_ativo):
        # Zeca na obra: conciliação canina, filhotes afirmando, lama tóxica, retroescavadeira
        fundo = self.fundo_limpo.copy()

        # 1. Filhotes de obra balançando a cabeça afirmativamente (uníssono deslocado)
        self.recortes["filhotes2"].colar(fundo, dy=math.sin(t * 3.4) * 2.2,
                                         rot=math.sin(t * 3.4 + 0.4) * 0.8, pivot=(1055, 690))
        # 2. Placa da associação balançando com o vento da obra
        self.recortes["placa"].colar(fundo, rot=math.sin(t * 1.8) * 2.4, pivot=(1255, 555))

        arr = np.array(fundo)

        # 3. Pata de 6 dedos gesticulando em conciliação suave
        box_pata = (540, 310, 685, 390)
        pw_, ph_ = box_pata[2] - box_pata[0], box_pata[3] - box_pata[1]
        MYp, MXp = np.meshgrid(np.arange(ph_), np.arange(pw_), indexing='ij')
        dx_p = np.full((ph_, pw_), math.sin(t * 2.3) * 3.2 * (0.5 + 0.5 * env_fala), dtype=np.float32)
        dy_p = (np.sin(t * 2.9 + MXp * 0.02) * 1.6).astype(np.float32)
        arr = deformar_regiao(arr, box_pata, dx_p, dy_p)

        # 4. Tronco do Zeca respirando
        box_tr = (355, 375, 555, 640)
        tw_, th_ = box_tr[2] - box_tr[0], box_tr[3] - box_tr[1]
        dy_tr = np.full((th_, tw_), math.sin(t * 1.9) * 1.3, dtype=np.float32)
        arr = deformar_regiao(arr, box_tr, np.zeros_like(dy_tr), dy_tr)

        # 5. Lip sync cínico na linha do sorriso malandro
        if falante_ativo and env_fala > 0.07:
            arr = deformar_jaw(arr, (455, 300, 565, 395), env_fala, 9.0, t=t)

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        if falante_ativo and env_fala > 0.07:
            desenhar_boca(draw, 508, 345 + int(env_fala * 3.6), int(30 + env_fala * 5), int(7 + env_fala * 16), canino=True)

        # 6. Poças de lodo tóxico verde borbulhando (plop-plop) + gás
        for (bx, by, n) in ((300, 500, 3), (385, 610, 2)):
            for k in range(n):
                fase = (t * 0.9 + k * 0.37 + bx * 0.01) % 1.0
                raio = int(4 + 8 * fase)
                alpha = int(200 * (1.0 - fase))
                draw.ellipse([(bx + k * 28 - raio, by - raio - int(fase * 10)),
                              (bx + k * 28 + raio, by + raio - int(fase * 10))],
                             outline=(140, 255, 90, alpha), width=2)
        ga = int(70 + 40 * math.sin(t * 2.0))
        draw.arc([(250, 430), (330, 505)], 200, 340, fill=(140, 255, 90, ga), width=3)

        # 7. Fumaça do escapamento da retroescavadeira
        for k in range(3):
            fase = (t * 0.5 + k * 0.33) % 1.0
            cx_s = 760 + math.sin(t * 1.2 + k * 2.0) * 8 + k * 6
            cy_s = 165 - fase * 55
            r_s = int(6 + 14 * fase)
            alpha_s = int(110 * (1.0 - fase))
            draw.ellipse([(cx_s - r_s, cy_s - r_s), (cx_s + r_s, cy_s + r_s)],
                         fill=(210, 210, 205, alpha_s))

        return frame

    def _animar_023(self, t, env_fala, falante_ativo):
        # Zeca médico fajuto: cruz neon, planta carnívora, frascos alienígenas, caneta batendo
        fundo = self.fundo_limpo.copy()

        # 1. Planta carnívora balançando com pivot na base do vaso
        self.recortes["planta"].colar(fundo, rot=math.sin(t * 1.6) * 1.8,
                                      scale_y=1.0 + 0.004 * math.sin(t * 2.2), pivot=(355, 722))

        arr = np.array(fundo)

        # 2. Tronco do Zeca respirando (jaleco branco)
        box_tr = (585, 400, 905, 680)
        tw_, th_ = box_tr[2] - box_tr[0], box_tr[3] - box_tr[1]
        dy_tr = np.full((th_, tw_), math.sin(t * 2.0) * 1.2, dtype=np.float32)
        arr = deformar_regiao(arr, box_tr, np.zeros_like(dy_tr), dy_tr)

        # 3. Caneta na pata batendo no bloco de receitas
        box_caneta = (625, 675, 785, 740)
        cw_, ch_ = box_caneta[2] - box_caneta[0], box_caneta[3] - box_caneta[1]
        dy_c = np.full((ch_, cw_), -abs(math.sin(t * 6.5)) * 3.5, dtype=np.float32)
        arr = deformar_regiao(arr, box_caneta, np.zeros_like(dy_c), dy_c)

        # 4. Lip sync médico fajuto
        if falante_ativo and env_fala > 0.07:
            arr = deformar_jaw(arr, (700, 315, 885, 435), env_fala, 9.0, t=t)

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        if falante_ativo and env_fala > 0.07:
            desenhar_boca(draw, 812, 356 + int(env_fala * 3.6), int(38 + env_fala * 6), int(9 + env_fala * 18), canino=True)

        # 5. Piscada normal a cada 3.5s + piscada cúmplice para a câmera (2.3-2.85s)
        ciclo = t % 3.5
        if ciclo < 0.13 or 2.3 < t < 2.85:
            draw.rectangle([(645, 230), (735, 268)], fill=(120, 88, 55, 255))
            draw.line([(645, 268), (735, 262)], fill=(60, 40, 25, 255), width=3)

        # 6. Cruz vermelha neon pulsando na parede (415-545, 105-245)
        pulso = int(80 + 60 * math.sin(t * 3.2))
        draw.rectangle([(462, 115), (502, 238)], fill=(255, 70, 80, pulso // 3))
        draw.rectangle([(422, 152), (542, 198)], fill=(255, 70, 80, pulso // 3))
        draw.rectangle([(462, 115), (502, 238)], outline=(255, 60, 70, pulso), width=4)
        draw.rectangle([(422, 152), (542, 198)], outline=(255, 60, 70, pulso), width=4)

        # 7. Mosca orbitando a planta carnívora... e mastigada a cada ciclo
        ciclo_mosca = (t * 0.45) % 1.0
        if ciclo_mosca < 0.8:
            ang = ciclo_mosca * 8.0
            mx_ = 420 + math.cos(ang) * 45
            my_ = 330 + math.sin(ang * 1.4) * 28
            draw.ellipse([(mx_ - 3, my_ - 3), (mx_ + 3, my_ + 3)], fill=(25, 25, 25, 230))
            draw.line([(mx_ - 7, my_ - 5), (mx_ + 7, my_ + 5)], fill=(200, 200, 255, 90), width=2)
        elif ciclo_mosca < 0.92:
            draw.ellipse([(395, 315), (445, 355)], fill=(90, 160, 70, 60))

        # 8. Bolhas subindo nos frascos com fetos alienígenas
        for k in range(4):
            fase = (t * 0.6 + k * 0.25) % 1.0
            y_b = 515 - fase * 130
            r_b = int(3 + 5 * (1 - fase))
            draw.ellipse([(1322 - r_b + (k % 2) * 18, y_b - r_b),
                          (1322 + r_b + (k % 2) * 18, y_b + r_b)],
                         outline=(200, 255, 230, 150), width=2)

        # 9. Vidrinhos coloridos brilhando na prateleira
        glow_f = int(50 + 30 * math.sin(t * 2.4))
        draw.rectangle([(965, 395), (1125, 515)], fill=(120, 255, 170, glow_f // 4))

        return frame

    def _animar_024(self, t, env_fala, falante_ativo):
        # Caramelo close com a linguiça de THC: fórmula neon, aura verde, vapor canábico
        fundo = self.fundo_limpo.copy()

        # 1. Linguiça + pata oscilando suavemente
        self.recortes["linguica_pata"].colar(fundo, dy=math.sin(t * 2.2) * 2.4,
                                             rot=math.sin(t * 1.7) * 1.2, pivot=(1050, 635))
        arr = np.array(fundo)

        # 2. Respiração ampliada (close de peito/cachaço)
        box_peito = (430, 500, 1015, 768)
        pw_, ph_ = box_peito[2] - box_peito[0], box_peito[3] - box_peito[1]
        dy_p = np.full((ph_, pw_), math.sin(t * 1.9) * 1.8, dtype=np.float32)
        arr = deformar_regiao(arr, box_peito, np.zeros_like(dy_p), dy_p)

        # 3. Lip sync indignado na linha inferior do focinho
        if falante_ativo and env_fala > 0.07:
            arr = deformar_jaw(arr, (615, 445, 800, 555), env_fala, 14.0, t=t)

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        if falante_ativo and env_fala > 0.07:
            desenhar_boca(draw, 702, 478 + int(env_fala * 4.9), int(42 + env_fala * 7), int(7 + env_fala * 26), canino=True)

        # 4. Aura radioativa verde pulsante ao redor da linguiça
        aura = int(60 + 35 * math.sin(t * 3.0))
        draw.ellipse([(900, 295), (1295, 615)], outline=(90, 255, 120, aura), width=6)
        draw.ellipse([(935, 330), (1260, 580)], outline=(140, 255, 160, aura // 2), width=3)

        # 5. Vapor canábico espiralando para cima da linguiça
        for k in range(3):
            fase = (t * 0.45 + k * 0.33) % 1.0
            vy = 320 - fase * 200
            vx = 1095 + math.sin(fase * 7.0 + k * 2.1) * 42
            va = int(120 * (1.0 - fase))
            draw.arc([(vx - 18, vy - 12), (vx + 18, vy + 12)], 30, 300, fill=(150, 255, 160, va), width=3)

        # 6. Fórmula molecular do THC em neon verde pulsando
        neon = int(140 + 90 * math.sin(t * 2.6))
        for (nx, ny, nr) in ((335, 135, 34), (475, 105, 30), (615, 105, 30), (755, 95, 28), (835, 135, 22)):
            draw.ellipse([(nx - nr, ny - nr), (nx + nr, ny + nr)], outline=(80, 255, 110, neon), width=4)
        draw.line([(369, 125), (445, 108)], fill=(80, 255, 110, neon), width=4)
        draw.line([(505, 105), (585, 105)], fill=(80, 255, 110, neon), width=4)
        draw.line([(645, 105), (727, 98)], fill=(80, 255, 110, neon), width=4)
        draw.line([(783, 108), (818, 122)], fill=(80, 255, 110, neon), width=4)

        # 7. Faísca de zumbido elétrico no neon
        if (t % 1.7) < 0.08:
            draw.line([(500, 60), (525, 85), (505, 95), (535, 120)], fill=(220, 255, 220, 220), width=2)

        # 8. Luz esverdeada cintilante no rosto do Caramelo
        flick = int(8 + 6 * math.sin(t * 5.0))
        draw.rectangle([(430, 150), (1015, 700)], fill=(60, 255, 110, flick))

        return frame

    def _animar_025(self, t, env_fala, falante_ativo):
        # Zeca carimbando DEBT ENFORCED: carimbo com impacto, CRT verde, globo girando
        fundo = self.fundo_limpo.copy()

        # 1. Ciclo do carimbo: sobe rápido e BATE no papel (2 carimbadas por cena)
        ciclo = t % 2.4
        if ciclo < 0.32:
            dy_car = -(0.32 - ciclo) / 0.32 * 58.0
        elif ciclo < 0.42:
            dy_car = 0.0
        else:
            dy_car = -6.0 * min(1.0, (ciclo - 0.42) * 2.0)
        impacto = 0.32 <= ciclo < 0.52
        self.recortes["carimbo"].colar(fundo, dy=dy_car, rot=dy_car * 0.04, pivot=(582, 515))

        arr = np.array(fundo)

        # 2. Papel treme no impacto
        if impacto:
            px_, py_ = 430, 223
            dx_sh = (np.random.rand(py_, px_).astype(np.float32) - 0.5) * 3.2
            arr = deformar_regiao(arr, (445, 545, 875, 768), dx_sh, dx_sh * 0.4)

        # 3. Lip sync com impacto (sorriso malicioso de dentes)
        if falante_ativo and env_fala > 0.07:
            arr = deformar_jaw(arr, (720, 235, 885, 350), env_fala, 11.0, t=t)

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        if falante_ativo and env_fala > 0.07:
            desenhar_boca(draw, 802, 278 + int(env_fala * 4.4), int(38 + env_fala * 8), int(8 + env_fala * 22), canino=True)

        # 4. Poeira do impacto subindo do papel
        if impacto:
            fase = (ciclo - 0.32) / 0.20
            for k in range(4):
                ang = k * 1.7
                dxk = 582 + math.cos(ang) * 30 * (0.3 + fase)
                dyk = 505 - fase * 28 - math.sin(ang) * 8
                r_k = int(3 + 7 * fase)
                draw.ellipse([(dxk - r_k, dyk - r_k), (dxk + r_k, dyk + r_k)],
                             fill=(200, 190, 170, int(120 * (1 - fase))))

        # 5. Texto verde fósforo piscando/rolando no monitor CRT antigo
        for i in range(5):
            y_lin = 355 + i * 20
            seg = int((t * 6 + i * 3) % 22) + 2
            x_ini = 105 + int(15 * math.sin(i * 2.4 + t * 0.8))
            alpha_t = 160 if ((t * 2 + i) % 1.0) < 0.82 else 60
            draw.line([(x_ini, y_lin), (x_ini + seg * 8, y_lin)], fill=(60, 255, 110, alpha_t), width=3)

        # 6. Globo terrestre girando suavemente
        mer = int(math.sin(t * 0.9) * 34)
        draw.arc([(1215, 415), (1365, 575)], 90, 270, fill=(40, 60, 120, 130), width=3)
        draw.line([(1240 + mer, 430), (1240 + mer, 560)], fill=(30, 80, 60, 110), width=3)

        # 7. Selo DEBT ENFORCED reluzindo na folha
        selo = int(200 + 55 * math.sin(t * 4.0)) if impacto else 150
        draw.ellipse([(545, 585), (775, 655)], outline=(210, 40, 40, selo), width=5)

        return frame

    def _animar_026(self, t, env_fala, falante_ativo):
        # Pardal no poste: apontando frenético, cartazes ao vento, folhas na sarjeta
        fundo = self.fundo_limpo.copy()

        # 1. Braço apontando freneticamente para os cartazes do poste
        apont = math.sin(t * 11.0) * 5.0 + math.sin(t * 23.0) * 1.6
        self.recortes["braco"].colar(fundo, dx=apont, dy=abs(math.sin(t * 9.0)) * -2.0,
                                     rot=apont * 0.25, pivot=(455, 430))

        arr = np.array(fundo)

        # 2. Moradores desiludidos: cabeça caindo devagar
        box_md = (905, 275, 1235, 395)
        mw2, mh2 = box_md[2] - box_md[0], box_md[3] - box_md[1]
        MYm, MXm = np.meshgrid(np.arange(mh2), np.arange(mw2), indexing='ij')
        dy_md = ((MYm / float(mh2)) * (1.5 + 1.0 * math.sin(t * 1.2))).astype(np.float32)
        arr = deformar_regiao(arr, box_md, np.zeros_like(dy_md), dy_md)

        # 3. Lip sync histérico com queixo tremendo de raiva política
        if falante_ativo and env_fala > 0.07:
            arr = deformar_jaw(arr, (370, 325, 480, 410), env_fala, 12.0, t=t, tremor=1.5)

        # 4. Cartazes eleitorais oscilando com o vento da sarjeta
        for (bx0, by0, bx1, by1) in ((585, 55, 895, 255), (585, 385, 895, 575)):
            bw_, bh_ = bx1 - bx0, by1 - by0
            MYc, MXc = np.meshgrid(np.arange(bh_), np.arange(bw_), indexing='ij')
            dx_c = (np.sin(t * 2.8 + MYc * 0.03) * 2.6).astype(np.float32)
            dy_c = (np.sin(t * 3.3 + MXc * 0.04) * 1.8).astype(np.float32)
            arr = deformar_regiao(arr, (bx0, by0, bx1, by1), dx_c, dy_c)

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        if falante_ativo and env_fala > 0.07:
            desenhar_boca(draw, 422, 355 + int(env_fala * 4.2), int(26 + env_fala * 6), int(6 + env_fala * 18), canino=False)

        # 5. Retalho de cartaz rasgado tremendo
        onda = math.sin(t * 6.5) * 4
        draw.polygon([(705, 228), (772 + onda, 240), (748, 262)], fill=(235, 225, 180, 160))

        # 6. Fio elétrico oscilando no topo
        sag = 18 + 6 * math.sin(t * 1.4)
        draw.line([(215, 42), (330, 42 + sag), (455, 45 + sag), (635, 40)], fill=(25, 25, 30, 220), width=3)

        # 7. Folhas secas rolando na sarjeta
        for k in range(3):
            x_l = 215 + ((t * 85 + k * 175) % 640)
            y_l = 655 + math.sin(t * 3 + k * 2.0) * 6
            draw.ellipse([(x_l - 8, y_l - 4), (x_l + 8, y_l + 4)], fill=(150, 110, 55, 200))
            draw.line([(x_l - 8, y_l), (x_l + 8, y_l)], fill=(110, 80, 40, 220), width=2)

        return frame

    def _animar_027(self, t, env_fala, falante_ativo):
        # Zeca apavorado: celular da Marta, enxurrada de notificações, suor, café
        arr = np.array(self.img0)

        # 1. Micro-tremor de pânico no rosto peludo
        MYf, MXf = np.meshgrid(np.arange(255), np.arange(285), indexing='ij')
        dx_f = (np.sin(t * 31.0 + MYf * 0.05) * 1.1).astype(np.float32)
        dy_f = (np.cos(t * 27.0 + MXf * 0.05) * 0.9).astype(np.float32)
        arr = deformar_regiao(arr, (585, 255, 870, 510), dx_f, dy_f)

        # 2. Lip sync apreensivo com boca trêmula de medo eleitoral
        if falante_ativo and env_fala > 0.07:
            arr = deformar_jaw(arr, (685, 350, 860, 465), env_fala, 10.0, t=t, tremor=1.8)

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        if falante_ativo and env_fala > 0.07:
            desenhar_boca(draw, 775, 402 + int(env_fala * 4.0), int(36 + env_fala * 8), int(8 + env_fala * 24), canino=True)

        # 3. Luz verde esmeralda volumétrica do celular no rosto do Zeca
        luz = int(16 + 10 * math.sin(t * 4.2))
        draw.polygon([(855, 320), (855, 545), (520, 640), (505, 250)], fill=(40, 255, 120, luz))

        # 4. Tela do celular: dezenas de chats da Dona Marta subindo sem parar
        draw.rectangle([(862, 292), (1138, 588)], fill=(15, 45, 25, 60))
        for i in range(6):
            y_b = 585 - ((t * 42 + i * 62) % 330)
            x_b = 880 + (i % 2) * 125
            draw.rounded_rectangle([(x_b, y_b), (x_b + 105, y_b + 42)], radius=8,
                                   fill=(220, 255, 230, 175))
            draw.ellipse([(x_b + 6, y_b + 8), (x_b + 34, y_b + 36)], fill=(200, 120, 160, 230))
            draw.ellipse([(x_b + 14, y_b + 22), (x_b + 26, y_b + 32)], fill=(60, 20, 40, 230))
            draw.line([(x_b + 42, y_b + 14), (x_b + 95, y_b + 14)], fill=(60, 60, 70, 200), width=2)
            draw.line([(x_b + 42, y_b + 24), (x_b + 85, y_b + 24)], fill=(60, 60, 70, 160), width=2)

        # 5. Notificações vibrando em ondas + faíscas
        for k in range(3):
            fase = (t * 1.3 + k * 0.33) % 1.0
            r_n = int(6 + 14 * fase)
            draw.ellipse([(1112 - r_n, 305 - r_n), (1112 + r_n, 305 + r_n)],
                         outline=(120, 255, 150, int(200 * (1 - fase))), width=3)
        if (t % 0.9) < 0.07:
            draw.line([(1118, 330), (1138, 330)], fill=(230, 255, 240, 220), width=2)
            draw.line([(1128, 320), (1128, 340)], fill=(230, 255, 240, 220), width=2)

        # 6. Gotas de suor escorrendo pelas bochechas peludas
        for (gx0, gy0) in ((655, 420), (832, 412), (612, 445)):
            fase = (t * 0.55 + gx0 * 0.01) % 1.0
            gy_ = gy0 + fase * 85
            ga_ = int(230 * (1 - fase * 0.5))
            draw.ellipse([(gx0 - 4, gy_ - 7), (gx0 + 4, gy_ + 7)], fill=(200, 235, 255, ga_))

        # 7. Vapor subindo da xícara de café
        for k in range(2):
            fase = (t * 0.5 + k * 0.5) % 1.0
            vy = 545 - fase * 110
            vx = 278 + math.sin(fase * 6.0 + k * 3) * 16
            draw.arc([(vx - 12, vy - 9), (vx + 12, vy + 9)], 40, 300,
                     fill=(235, 235, 235, int(110 * (1 - fase))), width=3)

        return frame

    def _animar_028(self, t, env_fala, falante_ativo):
        # Pardal desesperado: calculadora trêmula, pupilas roleta, suor em cascata, bandeira
        fundo = self.fundo_limpo.copy()

        # 1. Calculadora vibrando na mão trêmula
        vib = math.sin(t * 37.0) * 2.2 + math.sin(t * 23.0) * 1.2
        self.recortes["calculadora"].colar(fundo, dx=vib, dy=abs(math.sin(t * 29.0)) * -1.4,
                                           rot=vib * 0.2, pivot=(990, 655))
        # 2. Bandeira do Brasil tremulando na parede
        self.recortes["bandeira"].colar(fundo, rot=math.sin(t * 2.4) * 2.8,
                                        scale_y=1.0 + 0.01 * math.sin(t * 3.1), pivot=(1335, 250))

        arr = np.array(fundo)

        # 3. Lip sync gaguejante com queixo tremendo (jaw drop até 14px)
        if falante_ativo and env_fala > 0.07:
            gaguejo = 1.0 + 0.25 * math.sin(t * 47.0)
            arr = deformar_jaw(arr, (615, 475, 815, 585), env_fala * gaguejo, 14.0, t=t, tremor=1.2)

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        if falante_ativo and env_fala > 0.07:
            desenhar_boca(draw, 712, 522 + int(env_fala * 4.9), int(34 + env_fala * 8), int(7 + env_fala * 24), canino=False)

        # 4. Pupilas girando como roleta de cassino com números eleitorais
        for (ox, oy) in ((545, 305), (715, 305)):
            ang = t * 9.0
            for k in range(3):
                a0 = math.degrees(ang + k * 2.1)
                draw.arc([(ox - 34, oy - 34), (ox + 34, oy + 34)], a0, a0 + 55,
                         fill=(120, 255, 140, 200), width=4)
            if (t * 3 + ox) % 1.0 < 0.6:
                draw.text((ox - 18, oy - 8), str(int(t * 7 + ox) % 4321), font=ler_fonte(16),
                          fill=(200, 255, 210, 220))

        # 5. Cascata de suor: testa -> bochechas -> colarinho
        for k, gx0 in enumerate((475, 585, 695, 795)):
            fase = (t * 0.5 + k * 0.25) % 1.0
            gy_ = 195 + fase * 380
            ga_ = int(240 * (1 - fase * 0.35))
            draw.ellipse([(gx0 - 5, gy_ - 9), (gx0 + 5, gy_ + 9)], fill=(205, 238, 255, ga_))
            if fase > 0.93:
                draw.ellipse([(gx0 - 3, 585), (gx0 + 3, 595)], fill=(205, 238, 255, 220))

        # 6. Visor da calculadora: 4.251.999 piscando em vermelho
        disp = 230 if (t * 2.2 % 1.0) < 0.75 else 90
        draw.rectangle([(898, 498), (1082, 538)], fill=(20, 15, 10, 200))
        draw.text((915, 505), "4,251,999", font=ler_fonte(24), fill=(255, 45, 45, disp))

        # 7. Tecla sendo apertada em disparada
        if (t * 4.0) % 1.0 < 0.1:
            draw.ellipse([(1045, 585), (1095, 625)], fill=(255, 255, 255, 120))

        return frame

    # ------------------ CENAS PARTE 5 ------------------

    def _animar_029(self, t):
        # Família no sofá assistindo ao programa eleitoral gratuito na TV de tubo
        # (NARRADOR em off — nenhuma boca anima; só atuação silenciosa e a TV viva)
        arr = np.array(self.img0.copy())

        # 1. Cintilação do tubo + projeção cênica da luz da TV na sala
        brilho = 1.0 + 0.05 * math.sin(t * 11.0) + 0.035 * math.sin(t * 4.3 + 1.2)
        if (t * 2.7) % 1.0 < 0.05:
            brilho *= 1.14
        x0, y0, x1, y1 = 235, 140, 418, 298
        arr[y0:y1, x0:x1] = np.clip(arr[y0:y1, x0:x1].astype(np.float32) * brilho, 0, 255).astype(np.uint8)
        sala_b = 1.0 + 0.022 * math.sin(t * 11.0 + 0.7)
        arr[250:740, 420:1260] = np.clip(arr[250:740, 420:1260].astype(np.float32) * sala_b, 0, 255).astype(np.uint8)

        # 2. Respiração do grupo familiar em fases dessincronizadas (mudos)
        for k, (bx0, by0, bx1, by1) in enumerate(((470, 330, 640, 700),
                                                  (660, 320, 850, 700),
                                                  (900, 330, 1080, 700),
                                                  (1080, 380, 1230, 720))):
            bw, bh = bx1 - bx0, by1 - by0
            BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
            dy = np.sin(t * 1.15 + k * 1.7) * (1.5 + 0.5 * (k % 2)) * np.clip(BY / float(bh), 0, 1)
            arr = deformar_regiao(arr, (bx0, by0, bx1, by1), np.zeros_like(dy), dy.astype(np.float32))

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        # 3. Varredura de scanline descendo a tela + cone de luz do tubo na família
        ys = y0 + ((t * 60.0) % max(1.0, (y1 - y0)))
        draw.line([(x0, ys), (x1, ys)], fill=(180, 220, 255, 70), width=2)
        cone = int(24 + 10 * math.sin(t * 9.0))
        draw.polygon([(x1 - 4, y0 + 20), (x1 + 330, 330), (x1 + 330, 650), (x1 - 4, y1 - 15)],
                     fill=(150, 190, 255, cone))
        for gx_, gy1_ in ((x0 + 25, y0 + 18), (x0 + 130, y0 + 12)):
            draw.line([(gx_, gy1_), (gx_ + 70, gy1_ + 38)], fill=(235, 245, 255, 60), width=5)

        # 4. Intermitência do bloco do programa dentro do tubo
        if (t * 1.8) % 1.0 < 0.30:
            draw.rectangle([(x0 + 18, y0 + 14), (x0 + 92, y0 + 46)], fill=(255, 70, 60, 55))
        return frame

    def _animar_030(self, t, env_fala, falante_ativo):
        # Debate ao vivo da praça: a repórter apura a fome; Pardal suando no microfone
        arr = np.array(self.img0.copy())

        # 1. Multidão atrás das grades balançando em bandas com fases
        for k, (by0, by1) in enumerate(((430, 560), (545, 680), (665, 768))):
            bh = by1 - by0
            BY, BX = np.meshgrid(np.arange(bh), np.arange(1408), indexing='ij')
            dx = np.sin(t * 1.7 + k * 2.1 + BY * 0.02) * (1.8 + 0.4 * k)
            arr = deformar_regiao(arr, (0, by0, 1408, by1), dx.astype(np.float32), np.zeros_like(dx))

        # 2. Cintilação dos letreiros de neon + luz forte da câmera de TV
        for (nx0, ny0, nx1, ny1, fase) in ((1055, 60, 1385, 320, 0.0),
                                           (250, 95, 460, 260, 1.7),
                                           (60, 40, 240, 200, 3.1)):
            br = 1.0 + 0.09 * math.sin(t * 6.0 + fase) + (0.15 if (t * 3.0 + fase) % 1.0 < 0.07 else 0.0)
            arr[ny0:ny1, nx0:nx1] = np.clip(arr[ny0:ny1, nx0:nx1].astype(np.float32) * br, 0, 255).astype(np.uint8)
        bl = (1.0 + 0.07 * math.sin(t * 13.0)) * 1.06
        arr[100:230, 55:145] = np.clip(arr[100:230, 55:145].astype(np.float32) * bl, 0, 255).astype(np.uint8)

        # 3. Tremor nervoso do Pardal ouvindo (boca muda: quem fala é a repórter)
        bx0, by0, bx1, by1 = 775, 335, 885, 450
        bw, bh = bx1 - bx0, by1 - by0
        BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        dxp = np.sin(t * 29.0) * 0.9 * np.clip(BY / float(bh), 0, 1)
        arr = deformar_regiao(arr, (bx0, by0, bx1, by1), dxp.astype(np.float32), np.zeros_like(dxp))

        # 4. Lip sync anatômico da repórter (falante do bloco)
        if falante_ativo and env_fala > 0.07:
            arr = deformar_jaw(arr, (950, 290, 1085, 425), env_fala, 9.0, t=t, tremor=0.35)

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        if falante_ativo and env_fala > 0.07:
            desenhar_boca(draw, 1008, 353 + int(env_fala * 3), int(13 + env_fala * 9),
                          int(5 + env_fala * 11), canino=False)

        # 5. Pingos de suor do Pardal escorrendo pela têmpora
        for k, gx0 in enumerate((795, 825, 852)):
            fase = (t * 0.42 + k * 0.33) % 1.0
            gy_ = 355 + fase * 80
            draw.ellipse([(gx0 - 3, gy_ - 5), (gx0 + 3, gy_ + 5)], fill=(205, 238, 255, 220))

        # 6. Piscada nervosa do Pardal + flashes da imprensa
        if (t * 0.9) % 2.2 < 0.10:
            for (ex, ey) in ((800, 368), (845, 366)):
                draw.ellipse([(ex - 11, ey - 6), (ex + 11, ey + 6)], fill=(168, 184, 128, 255))
        if (t * 0.53) % 1.0 < 0.04:
            draw.rectangle([(0, 0), (1408, 768)], fill=(255, 255, 255, 26))
        return frame

    def _animar_031(self, t, env_fala, falante_ativo):
        # Close absoluto do Pardal (PUNCH): "Como assim, senhor?" — pânico em câmera lenta
        arr = np.array(self.img0.copy())

        # 1. Tremor fino de pânico percorrendo o rosto gigante
        bw, bh = 520, 420
        BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        dx_ = (np.sin(t * 31.0) * 0.9 + np.sin(t * 17.0) * 0.5) * np.clip(BY / float(bh), 0, 1)
        arr = deformar_regiao(arr, (420, 290, 940, 710), dx_.astype(np.float32), np.zeros_like(dx_))

        # 2. Lip sync anatômico do Pardal (falante) — mandíbula grande, queixo trêmulo
        if falante_ativo and env_fala > 0.07:
            arr = deformar_jaw(arr, (450, 470, 900, 660), env_fala, 18.0, t=t, tremor=0.8)

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        if falante_ativo and env_fala > 0.07:
            desenhar_boca(draw, 655, 535 + int(env_fala * 9), int(105 + env_fala * 20),
                          int(14 + env_fala * 34), canino=False)

        # 3. Pupilas em alfinete dilatando de medo + brilhos
        for (ox, oy) in ((623, 317), (867, 312)):
            r = 5.5 + 3.5 * (0.5 + 0.5 * math.sin(t * 2.3 + ox * 0.01))
            draw.ellipse([(ox - r, oy - r), (ox + r, oy + r)], fill=(18, 14, 16, 255))
            draw.ellipse([(ox + r * 0.3, oy - r * 0.8), (ox + r * 0.3 + 3, oy - r * 0.8 + 3)],
                         fill=(245, 250, 255, 230))

        # 4. Suor em cachoeira: gotas correndo testa, têmporas e queixo
        for k, gx0 in enumerate((505, 585, 705, 825, 905)):
            fase = (t * 0.55 + k * 0.2) % 1.0
            gy_ = 300 + fase * 320
            ga_ = int(235 * (1 - fase * 0.3))
            draw.ellipse([(gx0 - 6, gy_ - 11), (gx0 + 6, gy_ + 11)], fill=(205, 238, 255, ga_))
            if fase > 0.92:
                draw.ellipse([(gx0 - 4, 625), (gx0 + 4, 640)], fill=(205, 238, 255, 230))

        # 5. Piscada nervosa única + halo dos spots de estúdio tremendo
        if 0.58 < (t % 3.4) < 0.74:
            for (ex, ey, rx_, ry_) in ((620, 320, 72, 52), (865, 315, 70, 50)):
                draw.ellipse([(ex - rx_, ey - ry_), (ex + rx_, ey + ry_)], fill=(168, 184, 128, 255))
                draw.line([(ex - rx_, ey), (ex + rx_, ey)], fill=(90, 70, 60, 220), width=4)
        halo = int(16 + 8 * math.sin(t * 7.0))
        draw.polygon([(0, 0), (330, 0), (150, 330)], fill=(170, 210, 255, halo))
        draw.polygon([(1408, 0), (1080, 0), (1260, 330)], fill=(170, 210, 255, halo))
        return frame

    def _animar_032(self, t, env_fala, falante_ativo):
        # Sabatina da juventude: repórter grita apontando; adolescentes só no celular
        arr = np.array(self.img0.copy())

        # 1. Faixa rasgada "MIGALHOPOLIS" balançando + línguas de tecido tremendo
        bw, bh = 458, 240
        BYg, BXg = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        dyb = (np.sin(BXg * 0.035 - t * 2.6) * 4.2 * np.clip((BYg + 30) / 120.0, 0, 1)).astype(np.float32)
        arr = deformar_regiao(arr, (950, 60, 1408, 300), np.zeros_like(dyb), dyb)
        bw, bh = 180, 190
        BXg, BYg = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        dxp = (np.sin(t * 4.4 + BYg * 0.05) * 3.2 * np.clip(BXg / 90.0, 0, 1)).astype(np.float32)
        arr = deformar_regiao(arr, (1180, 130, 1360, 320), dxp, np.zeros_like(dxp))

        # 2. Braço apontando da repórter oscilando com a gesticulação
        bw, bh = 320, 120
        BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        dya = (math.sin(t * 3.3) * 2.8 + math.sin(t * 7.1) * 0.8) * np.clip((bw - BX) / float(bw), 0, 1)
        arr = deformar_regiao(arr, (150, 320, 470, 440), np.zeros_like(dya), dya.astype(np.float32))

        # 3. Lip sync gritado da repórter (falante do bloco)
        if falante_ativo and env_fala > 0.07:
            arr = deformar_jaw(arr, (795, 305, 960, 450), env_fala * 1.1, 10.0, t=t, tremor=0.5)

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        if falante_ativo and env_fala > 0.07:
            desenhar_boca(draw, 873, 378 + int(env_fala * 4), int(28 + env_fala * 10),
                          int(9 + env_fala * 16), canino=False)

        # 4. Telas dos celulares dos adolescentes bruxuleando (geração TikTok)
        for k, (px, py) in enumerate(((255, 470), (352, 505), (432, 432), (475, 512), (395, 552))):
            gl = 55 + int(55 * (0.5 + 0.5 * math.sin(t * 5.0 + k * 1.3)))
            draw.rounded_rectangle([(px - 9, py - 13), (px + 9, py + 13)], 4,
                                   fill=(160, 220, 255, gl))

        # 5. Teias de aranha vibrando na quina + luz fluorescente do ginásio cintilando
        bw, bh = 60, 340
        BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        dxw = (np.sin(t * 1.6 + BY * 0.02) * 2.0).astype(np.float32)
        arr2 = np.array(frame)
        arr2 = deformar_regiao(arr2, (740, 95, 800, 435), dxw, np.zeros_like(dxw))
        frame = Image.fromarray(arr2)
        draw = ImageDraw.Draw(frame, "RGBA")
        fluo = int(20 + 14 * abs(math.sin(t * 9.5)))
        draw.rectangle([(760, 82), (1150, 104)], fill=(230, 255, 245, fluo))
        return frame

    def _animar_033(self, t, env_fala, falante_ativo):
        # Pardal diante da MÁQUINA PÚBLICA: caldeira enferrujada cospe lodo verde
        arr = np.array(self.img0.copy())

        # 1. A máquina sacudindo com a trituração burocrática
        bw, bh = 770, 660
        BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        dxm = (np.sin(t * 34.0 + BY * 0.004) * 1.6 + np.sin(t * 21.0 + 1.0) * 0.9).astype(np.float32)
        dym = (np.sin(t * 27.0 + 2.0 + BX * 0.003) * 1.1).astype(np.float32)
        arr = deformar_regiao(arr, (80, 60, 850, 720), dxm, dym)

        # 2. Urubus no topo da caldeira em cabeçadas rítmicas
        for k, (ux0, uy0, ux1, uy1) in enumerate(((215, 75, 345, 215), (355, 65, 500, 205))):
            bw, bh = ux1 - ux0, uy1 - uy0
            BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
            dyu = np.sin(t * 2.8 + k * 1.9) * 3.0 * np.clip(BY / float(bh), 0, 1)
            arr = deformar_regiao(arr, (ux0, uy0, ux1, uy1), np.zeros_like(dyu), dyu.astype(np.float32))

        # 3. Nuvem de interrogações balançando sobre o Pardal
        bw, bh = 440, 220
        BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        dyq = np.sin(t * 1.8 + BX * 0.01) * 4.5 * np.clip((bh - BY) / float(bh), 0, 1)
        arr = deformar_regiao(arr, (900, 40, 1340, 260), np.zeros_like(dyq), dyq.astype(np.float32))

        # 4. Lip sync histérico do Pardal (falante) — queixo trêmulo de desespero
        if falante_ativo and env_fala > 0.07:
            arr = deformar_jaw(arr, (1030, 235, 1235, 405), env_fala * 1.1, 13.0, t=t, tremor=1.4)

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        if falante_ativo and env_fala > 0.07:
            desenhar_boca(draw, 1120, 288 + int(env_fala * 5), int(24 + env_fala * 13),
                          int(8 + env_fala * 20), canino=False)

        # 5. Cascata de lodo verde escorrendo das válvulas + poça borbulhando
        for k, (gx0, gy0) in enumerate(((625, 400), (775, 395), (455, 470))):
            fase = (t * 0.55 + k * 0.3) % 1.0
            gy_ = gy0 + fase * 260
            draw.ellipse([(gx0 - 7, gy_ - 12), (gx0 + 7, gy_ + 12)], fill=(125, 235, 95, 210))
            if fase > 0.90:
                draw.ellipse([(gx0 - 13, 688), (gx0 + 13, 712)], fill=(125, 235, 95, 180))
        for k in range(4):
            fase = (t * 0.8 + k * 0.25) % 1.0
            r = 3 + fase * 9
            cx_ = 540 + 60 * math.sin(t * 1.1 + k * 2.0)
            draw.ellipse([(cx_ - r, 715 - r * 0.5), (cx_ + r, 715 + r * 0.5)],
                         outline=(150, 255, 120, 200), width=2)

        # 6. Faíscas de solda caindo + vapor das válvulas
        for k in range(5):
            fase = (t * 1.6 + k * 0.37) % 1.0
            sx = 700 + 30 * math.sin(t * 3.0 + k)
            sy = 265 + fase * 95
            draw.line([(sx, sy), (sx + 4, sy + 10)], fill=(255, 230, 120, 230), width=2)
        for k in range(4):
            fase = (t * 0.4 + k * 0.25) % 1.0
            r = 10 + fase * 26
            cx_ = 505 + 18 * math.sin(t * 1.2 + k)
            cy_ = 355 - fase * 130
            draw.ellipse([(cx_ - r, cy_ - r * 0.7), (cx_ + r, cy_ + r * 0.7)],
                         fill=(200, 210, 200, int(70 * (1 - fase))))

        # 7. Suor em spray do candidato (mãos erguidas em rendição)
        for k, gx0 in enumerate((1030, 1150, 1225)):
            fase = (t * 0.6 + k * 0.35) % 1.0
            gy_ = 240 + fase * 130
            draw.ellipse([(gx0 - 3, gy_ - 5), (gx0 + 3, gy_ + 5)], fill=(205, 238, 255, 215))
        return frame

    def _animar_034(self, t, env_fala, falante_ativo):
        # Estúdio da TV: globo holográfico dos Assuntos Externos + mini-Pardal coadjuvante
        arr = np.array(self.img0.copy())

        # 1. Mini-Pardal trocando de peso nas pernas (coadjuvante mudo)
        bw, bh = 115, 170
        BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        dxs = (math.sin(t * 1.3) * 1.6) * np.clip(BY / float(bh), 0, 1)
        arr = deformar_regiao(arr, (900, 515, 1015, 685), dxs.astype(np.float32), np.zeros_like(dxs))

        # 2. Monitores do estúdio piscando na parede + luzes de cena cintilando
        for (mx0, my0, mx1, my1, fase) in ((60, 320, 300, 470, 0.4),
                                           (1130, 330, 1395, 480, 1.9)):
            br = 1.0 + 0.08 * math.sin(t * 5.2 + fase)
            arr[my0:my1, mx0:mx1] = np.clip(arr[my0:my1, mx0:mx1].astype(np.float32) * br, 0, 255).astype(np.uint8)

        # 3. Lip sync da repórter (falante) com o microfone sob o queixo
        if falante_ativo and env_fala > 0.07:
            arr = deformar_jaw(arr, (655, 195, 800, 310), env_fala, 6.0, t=t, tremor=0.25)

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        if falante_ativo and env_fala > 0.07:
            desenhar_boca(draw, 715, 249 + int(env_fala * 2), int(15 + env_fala * 7),
                          int(5 + env_fala * 9), canino=False)

        # 4. Globo holográfico: meridianos girando + anéis orbitais precessionando + brilho
        gx, gy = 878, 335
        brilho_h = 150 + int(60 * math.sin(t * 2.2))
        draw.ellipse([(gx - 130, gy - 130), (gx + 130, gy + 130)],
                     outline=(120, 235, 255, brilho_h), width=3)
        for k in range(3):
            rx_ = 130 - k * 35
            sq = 0.22 + 0.62 * abs(math.sin(t * 1.2 + k * 1.1))
            draw.ellipse([(gx - rx_, gy - 130 * sq), (gx + rx_, gy + 130 * sq)],
                         outline=(120, 235, 255, int(brilho_h * 0.85)), width=2)

        def _elipse_girada(cx, cy, a, b, ang, passos=48):
            pts = []
            ca, sa = math.cos(ang), math.sin(ang)
            for i in range(passos + 1):
                th = 2 * math.pi * i / passos
                x_, y_ = a * math.cos(th), b * math.sin(th)
                pts.append((cx + x_ * ca - y_ * sa, cy + x_ * sa + y_ * ca))
            return pts

        draw.line(_elipse_girada(gx, gy, 138, 36, 0.4 * math.sin(t * 0.6)),
                  fill=(190, 140, 255, 155), width=3)
        draw.line(_elipse_girada(gx, gy, 126, 26, -0.5 + 0.3 * math.sin(t * 0.45 + 1.2)),
                  fill=(120, 255, 220, 145), width=3)
        for k in range(8):
            fase = (t * 0.9 + k * 0.125) % 1.0
            ang = k * 2.4 + t * 0.8
            px = gx + 95 * math.cos(ang) * (1 - fase * 0.25)
            py = gy + 95 * math.sin(ang) * 0.8 - fase * 60
            draw.ellipse([(px - 2, py - 2), (px + 2, py + 2)], fill=(180, 255, 255, int(200 * (1 - fase))))

        # 5. Piscada da repórter + holofote de estúdio oscilando
        if (t * 0.7) % 2.8 < 0.09:
            for (ex, ey) in ((700, 213), (735, 215)):
                draw.ellipse([(ex - 13, ey - 7), (ex + 13, ey + 7)], fill=(232, 200, 175, 255))
        hol = int(14 + 8 * math.sin(t * 3.7))
        draw.polygon([(500, 0), (900, 0), (760, 210), (640, 210)], fill=(190, 220, 255, hol))
        return frame

    def _animar_035(self, t):
        # Apuração: o povo sacode boletos e o Caramelo COME a urna de uma seção
        # (NARRADOR em off — bocas mudas; a mordida conta pela reação do objeto)
        fundo = self.fundo_limpo.copy()

        # 1. Urna de papelão sacudindo a cada mordida (boneco articulado com impacto)
        mord = (t * 2.2) % 1.0
        shake = 0.0
        if mord < 0.28:
            shake = math.sin(mord * 42.0) * (1.0 - mord / 0.28)
        self.recortes["urna"].colar(fundo, dx=shake * 5.0, dy=-abs(shake) * 3.0,
                                    rot=shake * 2.2, pivot=(530, 760))

        arr = np.array(fundo)

        # 2. Caramelo ruminando a democracia: corpo pulsa em sincrono com as mordidas
        bw, bh = 250, 213
        BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        mast = max(0.0, math.sin(t * 6.9)) * 2.4
        dyc = (-np.clip(BY / float(bh), 0, 1) * mast + np.sin(t * 3.1) * 0.8).astype(np.float32)
        arr = deformar_regiao(arr, (500, 555, 750, 768), np.zeros_like(dyc), dyc)

        # 3. Multidão em pânico tremendo em três blocos + fila do cadastro
        for k, (bx0, by0, bx1, by1) in enumerate(((0, 300, 480, 768),
                                                  (480, 280, 980, 620),
                                                  (980, 300, 1408, 768))):
            bw, bh = bx1 - bx0, by1 - by0
            BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
            dx = np.sin(t * 21.0 + k * 1.9) * 1.3 * np.clip(BY / float(bh), 0, 1)
            arr = deformar_regiao(arr, (bx0, by0, bx1, by1), dx.astype(np.float32), np.zeros_like(dx))

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        # 4. Nevasca de boletos/cédulas girando pelo plenário
        for k in range(14):
            fase = (t * 0.30 + k * 0.071) % 1.0
            px = (k * 127 + int(t * 40) + int(30 * math.sin(t * 1.5 + k))) % 1480 - 36
            py = fase * 810 - 30
            giro = math.sin(t * 2.2 + k)
            w_ = 24 + 10 * giro
            draw.rectangle([(px - w_ / 2, py - 13), (px + w_ / 2, py + 13)],
                           fill=(250, 248, 235, 215), outline=(90, 85, 80, 200), width=2)

        # 5. Telas da apuração piscando + faíscas dos flashes da imprensa
        if (t * 1.9) % 1.0 < 0.5:
            draw.rectangle([(8, 395), (128, 528)], fill=(40, 160, 120, 70))
        if (t * 0.77) % 1.3 < 0.045:
            draw.rectangle([(0, 0), (1408, 768)], fill=(255, 255, 255, 30))

        # 6. Lasca de papelão voando da mordida (a boca do cão permanece muda)
        if mord < 0.28:
            px = 640 + shake * 30
            py = 620 - abs(shake) * 18
            draw.polygon([(px, py), (px + 16, py - 8), (px + 10, py + 10)], fill=(214, 178, 120, 235))
        return frame

    def _animar_036(self, t):
        # Fórum: o juiz descobre que o terceiro turno não existia na lei
        # (NARRADOR em off — boca do juiz muda; só o cenário respira)
        fundo = self.fundo_limpo.copy()

        # 1. Martelo vibrando sobre a mesa com micro-quiques de revolta
        vib = math.sin(t * 31.0) * 2.0 + math.sin(t * 19.0) * 1.2
        quique = -abs(math.sin(t * 2.4)) * 2.2
        self.recortes["martelo"].colar(fundo, dx=vib, dy=quique, rot=vib * 0.25, pivot=(930, 620))

        arr = np.array(fundo)

        # 2. Teias de aranha do cartório balançando em contracorrente
        for k, (wx0, wy0, wx1, wy1) in enumerate(((0, 150, 260, 500),
                                                  (1150, 120, 1408, 420),
                                                  (0, 520, 200, 740))):
            bw, bh = wx1 - wx0, wy1 - wy0
            BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
            dxw = np.sin(t * 1.3 + k * 2.2 + BY * 0.015) * (1.2 + 0.5 * k)
            arr = deformar_regiao(arr, (wx0, wy0, wx1, wy1), dxw.astype(np.float32), np.zeros_like(dxw))

        # 3. Respiração pesada do juiz (ombros) + canto da página mordida tremulando
        bw, bh = 650, 300
        BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        dyj = np.sin(t * 0.9) * 2.2 * np.clip(BY / float(bh), 0, 1)
        arr = deformar_regiao(arr, (300, 420, 950, 720), np.zeros_like(dyj), dyj.astype(np.float32))
        bw, bh = 150, 120
        BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        dyp = np.sin(t * 3.6 + BX * 0.04) * 2.6 * np.clip((bh - BY) / float(bh), 0, 1)
        arr = deformar_regiao(arr, (700, 500, 850, 620), np.zeros_like(dyp), dyp.astype(np.float32))

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        # 4. Abajur burocrático cintilando + poeira suspensa nos fótons
        glow = int(24 + 12 * math.sin(t * 5.5))
        draw.ellipse([(60, 330), (260, 520)], fill=(255, 220, 130, glow))
        for k in range(10):
            px = 90 + ((k * 79 + int(t * 8)) % 300)
            py = 250 + ((k * 131 + int(t * 12)) % 380)
            draw.ellipse([(px, py), (px + 3, py + 3)], fill=(255, 240, 200, 150))

        # 5. Placa "JUSTICE IS GONE?" oscilando no fio + ponteiro do relógio girando
        bw, bh = 240, 130
        BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        dys = np.sin(t * 1.1 + BX * 0.02) * 2.4 * np.clip((bh - BY) / float(bh), 0, 1)
        arr2 = deformar_regiao(np.array(frame), (120, 60, 360, 190), np.zeros_like(dys), dys.astype(np.float32))
        frame = Image.fromarray(arr2)
        draw = ImageDraw.Draw(frame, "RGBA")
        seg_ang = math.radians((t * 6.0) % 60.0 * 6.0)
        draw.line([(1025, 207),
                   (1025 + 24 * math.sin(seg_ang), 207 - 24 * math.cos(seg_ang))],
                  fill=(240, 235, 220, 220), width=2)
        draw.ellipse([(1021, 203), (1029, 211)], fill=(240, 235, 220, 220))
        return frame

    def _animar_037(self, t):
        # Posse: 43 mil pessoas na praça de uma cidade de 11 mil — confete e onda humana
        # (NARRADOR em off — bocas mudas; só o Caramelo respira no palanque da mesa)
        arr = np.array(self.img0.copy())

        # 1. Onda humana percorrendo a praça em três bandas com fases
        for k, (by0, by1) in enumerate(((255, 420), (410, 590), (580, 768))):
            bh = by1 - by0
            BY, BX = np.meshgrid(np.arange(bh), np.arange(1408), indexing='ij')
            dx = np.sin(t * 1.9 + k * 2.0 + BX * 0.004) * (2.2 + 0.5 * k)
            dy = np.sin(t * 1.3 + k * 1.1) * 1.2 * np.clip(BY / float(bh), 0, 1)
            arr = deformar_regiao(arr, (0, by0, 1408, by1), dx.astype(np.float32), dy.astype(np.float32))

        # 2. Caramelo eleito na mesa de pau: respiração ampla + orelhas ao vento
        bw, bh = 180, 195
        BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        dyc = np.sin(t * 2.2) * 1.5 * np.clip(BY / float(bh), 0, 1)
        arr = deformar_regiao(arr, (540, 500, 720, 695), np.zeros_like(dyc), dyc.astype(np.float32))

        # 3. Varal de linguiças e bandeirinhas tremulando no alto da praça
        bw, bh = 850, 160
        BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        dyb = (np.sin(BX * 0.03 - t * 3.2) * 5.0 * np.clip(BY / 60.0, 0, 1)).astype(np.float32)
        arr = deformar_regiao(arr, (300, 40, 1150, 200), np.zeros_like(dyb), dyb)

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        # 4. Nevasca de confete vermelho-e-branco do carnaval eleitoral
        for k in range(26):
            fase = (t * 0.35 + k * 0.038) % 1.0
            px = (k * 57 + int(t * 30) * (1 + k % 3) + int(24 * math.sin(t * 2.0 + k))) % 1460 - 20
            py = fase * 800 - 20
            cor = (235, 60, 70, 225) if k % 2 == 0 else (250, 245, 235, 225)
            draw.rectangle([(px, py), (px + 9, py + 6)], fill=cor)

        # 5. Piscada solene do Caramelo + brilho do microfone improvisado na mesa
        if (t * 0.55) % 2.6 < 0.09:
            for (ex, ey) in ((600, 535), (645, 532)):
                draw.line([(ex - 10, ey), (ex + 10, ey)], fill=(120, 80, 40, 255), width=4)
        brilho_m = 40 + int(30 * math.sin(t * 4.4))
        draw.ellipse([(688, 470), (712, 495)], fill=(255, 255, 230, brilho_m))
        return frame

    def _animar_038(self, t):
        # Close do morador: nos olhos, o reflexo de uma pergunta que ninguém faz
        # (NARRADOR em off — boca muda; o "?" brilha nas pupilas)
        arr = np.array(self.img0.copy())

        # 1. Respiração mínima do rosto — quem engoliu a pergunta mal respira
        bw, bh = 750, 550
        BY, BX = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
        dy_ = np.sin(t * 0.85) * 1.3 * np.clip(BY / float(bh), 0, 1)
        arr = deformar_regiao(arr, (350, 150, 1100, 700), np.zeros_like(dy_), dy_.astype(np.float32))

        frame = Image.fromarray(arr)
        draw = ImageDraw.Draw(frame, "RGBA")

        # 2. Cintilação dos "?" nas pupilas + brilho úmido nos olhos
        for k, (ox, oy) in enumerate(((567, 302), (893, 312))):
            fa = 0.5 + 0.5 * math.sin(t * 2.6 + k * 1.8)
            draw.text((ox - 7, oy - 12), "?", font=ler_fonte(22), fill=(235, 250, 245, int(150 + 100 * fa)))
            draw.ellipse([(ox + 14, oy - 16), (ox + 18, oy - 12)], fill=(255, 255, 255, int(160 + 70 * fa)))

        # 3. Piscada lenta (atuação silenciosa permitida) — tampa em couro cansado
        ciclo = (t % 4.2)
        if 3.55 < ciclo < 3.85:
            f_ = math.sin((ciclo - 3.55) / 0.30 * math.pi)
            for (ex, ey, rx_, ry_) in ((567, 302, 52, 34), (893, 312, 52, 34)):
                h_ = max(2.0, ry_ * (1 - f_))
                draw.ellipse([(ex - rx_, ey - ry_), (ex + rx_, ey - ry_ + (ry_ - h_) * 2 + 2)],
                             fill=(196, 168, 138, 255))
                draw.line([(ex - rx_, ey), (ex + rx_, ey)], fill=(95, 70, 55, 230), width=3)

        # 4. Poeira flutuando na penumbra do beco + pulso de vinheta
        for k in range(12):
            fase = (t * 0.10 + k * 0.083) % 1.0
            px = (k * 127 + int(t * 6) * (1 + k % 2)) % 1440 - 16
            py = (k * 211 + int(t * 9)) % 760
            draw.ellipse([(px, py), (px + 3, py + 3)], fill=(230, 225, 210, int(120 * (1 - fase * 0.5))))
        vin = int(18 * (0.5 + 0.5 * math.sin(t * 0.7)))
        draw.rectangle([(0, 0), (1408, 768)], outline=(0, 0, 0, vin + 40), width=40)
        return frame
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
            
        # respiracao desativada (decisao de direcao: camera limpa, sem wobble)
        
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

    elif parte_num == 3:
        # Camas musicais para Parte 3 (Blocos 014 a 020)
        suspense_path = os.path.join(ROOT, "production", "audio", "beds", "suspense.mp3")
        cotidiano_path = os.path.join(ROOT, "production", "audio", "beds", "cotidiano.mp3")
        tensao_path = os.path.join(ROOT, "production", "audio", "beds", "tensao.mp3")
        bueiro_path = os.path.join(ROOT, "production", "audio", "beds", "bueiro.mp3")
        drama_path = os.path.join(ROOT, "production", "audio", "beds", "drama.mp3")
        comicio_path = os.path.join(ROOT, "production", "audio", "beds", "comicio.mp3")
        
        vento_sfx = os.path.join(ROOT, "production", "audio", "sfx", "vento.mp3")
        agua_sfx = os.path.join(ROOT, "production", "audio", "sfx", "agua.mp3")
        crowd_sfx = os.path.join(ROOT, "production", "audio", "sfx", "crowd.mp3")
        vent_sfx = os.path.join(ROOT, "production", "audio", "sfx", "ventilador.mp3")
        
        # 014: Suspense (Dúvida do idoso)
        t_014_fim = timeline[0]["t_fim"]
        idx_014_fim = min(n_amostras, int(t_014_fim * SR))
        if os.path.exists(suspense_path):
            arr_sus = carregar_mp3_como_array(suspense_path)
            tiled_sus = np.tile(arr_sus, int(math.ceil(idx_014_fim / float(len(arr_sus)))))[:idx_014_fim]
            pista_musica[:idx_014_fim] += tiled_sus * 0.14
            
        # 015: Bueiro / Cotidiano (Cofre e banquete)
        t_015_ini = timeline[1]["t_ini"]
        t_015_fim = timeline[1]["t_fim"]
        idx_15_ini = int(t_015_ini * SR)
        idx_15_fim = min(n_amostras, int(t_015_fim * SR))
        if os.path.exists(cotidiano_path) and idx_15_fim > idx_15_ini:
            arr_cot = carregar_mp3_como_array(cotidiano_path)
            len_15 = idx_15_fim - idx_15_ini
            tiled_cot = np.tile(arr_cot, int(math.ceil(len_15 / float(len(arr_cot)))))[:len_15]
            pista_musica[idx_15_ini:idx_15_fim] += tiled_cot * 0.13
            
        # 016: Tensão (Multidão faminta / Pedestal)
        t_016_ini = timeline[2]["t_ini"]
        t_016_fim = timeline[2]["t_fim"]
        idx_16_ini = int(t_016_ini * SR)
        idx_16_fim = min(n_amostras, int(t_016_fim * SR))
        if os.path.exists(tensao_path) and idx_16_fim > idx_16_ini:
            arr_t = carregar_mp3_como_array(tensao_path)
            len_16 = idx_16_fim - idx_16_ini
            tiled_t = np.tile(arr_t, int(math.ceil(len_16 / float(len(arr_t)))))[:len_16]
            pista_musica[idx_16_ini:idx_16_fim] += tiled_t * 0.16
            
        # 017: Cotidiano alegre (Seu Jorge vitorioso)
        t_017_ini = timeline[3]["t_ini"]
        t_017_fim = timeline[3]["t_fim"]
        idx_17_ini = int(t_017_ini * SR)
        idx_17_fim = min(n_amostras, int(t_017_fim * SR))
        if os.path.exists(cotidiano_path) and idx_17_fim > idx_17_ini:
            arr_cot = carregar_mp3_como_array(cotidiano_path)
            len_17 = idx_17_fim - idx_17_ini
            tiled_cot = np.tile(arr_cot, int(math.ceil(len_17 / float(len(arr_cot)))))[:len_17]
            pista_musica[idx_17_ini:idx_17_fim] += tiled_cot * 0.15
            
        # 018: Bueiro / Suspense (Zeca 6 dedos)
        t_018_ini = timeline[4]["t_ini"]
        t_018_fim = timeline[4]["t_fim"]
        idx_18_ini = int(t_018_ini * SR)
        idx_18_fim = min(n_amostras, int(t_018_fim * SR))
        if os.path.exists(bueiro_path) and idx_18_fim > idx_18_ini:
            arr_b = carregar_mp3_como_array(bueiro_path)
            len_18 = idx_18_fim - idx_18_ini
            tiled_b = np.tile(arr_b, int(math.ceil(len_18 / float(len(arr_b)))))[:len_18]
            pista_musica[idx_18_ini:idx_18_fim] += tiled_b * 0.15
            
        # 019: Drama solene (Caramelo prefeito)
        t_019_ini = timeline[5]["t_ini"]
        t_019_fim = timeline[5]["t_fim"]
        idx_19_ini = int(t_019_ini * SR)
        idx_19_fim = min(n_amostras, int(t_019_fim * SR))
        if os.path.exists(drama_path) and idx_19_fim > idx_19_ini:
            arr_dr = carregar_mp3_como_array(drama_path)
            len_19 = idx_19_fim - idx_19_ini
            tiled_dr = np.tile(arr_dr, int(math.ceil(len_19 / float(len(arr_dr)))))[:len_19]
            pista_musica[idx_19_ini:idx_19_fim] += tiled_dr * 0.16
            
        # 020: Comício / Fanfarra rápida (Zeca na logística do caminhão)
        t_020_ini = timeline[6]["t_ini"]
        idx_20_ini = int(t_020_ini * SR)
        if os.path.exists(comicio_path) and n_amostras > idx_20_ini:
            arr_com = carregar_mp3_como_array(comicio_path)
            len_20 = n_amostras - idx_20_ini
            tiled_com = np.tile(arr_com, int(math.ceil(len_20 / float(len(arr_com)))))[:len_20]
            pista_musica[idx_20_ini:] += tiled_com * 0.16

        # SFX Pontuais Parte 3
        if os.path.exists(vento_sfx):
            arr_v = carregar_mp3_como_array(vento_sfx)
            len_v = min(len(arr_v), idx_014_fim)
            if len_v > 0:
                pista_sfx[:len_v] += arr_v[:len_v] * 0.12
                
        if os.path.exists(agua_sfx):
            arr_ag = carregar_mp3_como_array(agua_sfx)
            len_ag = min(len(arr_ag), idx_15_fim - idx_15_ini)
            if len_ag > 0:
                pista_sfx[idx_15_ini:idx_15_ini + len_ag] += arr_ag[:len_ag] * 0.10
                
        if os.path.exists(crowd_sfx):
            arr_cr = carregar_mp3_como_array(crowd_sfx)
            len_cr = min(len(arr_cr), idx_16_fim - idx_16_ini)
            if len_cr > 0:
                pista_sfx[idx_16_ini:idx_16_ini + len_cr] += arr_cr[:len_cr] * 0.12
                
        if os.path.exists(vent_sfx):
            arr_vn = carregar_mp3_como_array(vent_sfx)
            len_vn = min(len(arr_vn), idx_17_fim - idx_17_ini)
            if len_vn > 0:
                t_vn = np.tile(arr_vn, int(math.ceil(len_vn / float(len(arr_vn)))))[:len_vn]
                pista_sfx[idx_17_ini:idx_17_ini + len_vn] += t_vn * 0.14

    elif parte_num == 4:
        # Camas musicais Parte 4 (blocos 021 a 028) — spec. §6 do relatório
        beds = os.path.join(ROOT, "production", "audio", "beds")
        sfx_dir = os.path.join(ROOT, "production", "audio", "sfx")
        cotidiano_path = os.path.join(beds, "cotidiano.mp3")
        forro_path = os.path.join(beds, "forro.mp3")
        suspense_path = os.path.join(beds, "suspense.mp3")
        fabinho_path = os.path.join(beds, "fabinho.mp3")
        comicio_path = os.path.join(beds, "comicio.mp3")
        tensao_path = os.path.join(beds, "tensao.mp3")
        agua_sfx = os.path.join(sfx_dir, "agua.mp3")
        moscas_sfx = os.path.join(sfx_dir, "moscas.mp3")
        vento_sfx = os.path.join(sfx_dir, "vento.mp3")
        crowd_sfx = os.path.join(sfx_dir, "crowd.mp3")
        celular_sfx = os.path.join(sfx_dir, "celular.mp3")

        def _trecho(i):
            return int(timeline[i]["t_ini"] * SR), min(n_amostras, int(timeline[i]["t_fim"] * SR))

        def _add_bed(path, i, gain):
            if not os.path.exists(path):
                return
            a, b = _trecho(i)
            if b <= a:
                return
            arr = carregar_mp3_como_array(path)
            n = b - a
            tiled = np.tile(arr, int(math.ceil(n / float(len(arr)))))[:n]
            pista_musica[a:b] += tiled * gain

        def _add_sfx_loop(path, i, gain):
            if not os.path.exists(path):
                return
            a, b = _trecho(i)
            if b <= a:
                return
            arr = carregar_mp3_como_array(path)
            n = b - a
            tiled = np.tile(arr, int(math.ceil(n / float(len(arr)))))[:n]
            pista_sfx[a:b] += tiled * gain

        def _add_estalo(t_local, i, dur=0.05, freq=0.0, gain=0.30, grave=False):
            a = int((timeline[i]["t_ini"] + t_local) * SR)
            n = int(dur * SR)
            if a < 0 or a + n > n_amostras:
                return
            tt = np.arange(n, dtype=np.float32) / SR
            if grave:
                grave_s = np.exp(-tt * 30.0) * np.sin(2 * math.pi * 70.0 * tt) * gain
                ruido = np.exp(-tt * 80.0) * (np.random.rand(n).astype(np.float32) - 0.5) * gain * 0.9
                pista_sfx[a:a + n] += grave_s + ruido
            elif freq > 0:
                pista_sfx[a:a + n] += np.exp(-tt * 45.0) * np.sin(2 * math.pi * freq * tt) * gain
            else:
                pista_sfx[a:a + n] += np.exp(-tt * 55.0) * (np.random.rand(n).astype(np.float32) - 0.5) * gain

        # 021: cotidiano tenso e cômico (-16 dBFS) + papéis estapeados
        _add_bed(cotidiano_path, 0, 0.13)
        for tl_ in (0.45, 1.95, 3.75, 5.2):
            _add_estalo(tl_, 0, dur=0.07, gain=0.34)
        # 022: forró de malandragem na obra + lama borbulhando (plop-plop)
        _add_bed(forro_path, 1, 0.13)
        _add_sfx_loop(agua_sfx, 1, 0.10)
        for tl_ in (0.6, 1.4, 2.3, 3.4, 4.5):
            _add_estalo(tl_, 1, dur=0.06, freq=180, gain=0.18)
        # 023: suspense de consultório fajuto + bipe de monitor cardíaco + moscas
        _add_bed(suspense_path, 2, 0.13)
        _add_sfx_loop(moscas_sfx, 2, 0.05)
        t_bip = 0.4
        while t_bip < 7.8:
            _add_estalo(t_bip, 2, dur=0.09, freq=1680, gain=0.16)
            t_bip += 1.15
        # 024: sci-fi cômica do fabinho + zumbido elétrico do neon
        _add_bed(fabinho_path, 3, 0.13)
        a24, b24 = _trecho(3)
        if b24 > a24:
            tt = np.arange(b24 - a24, dtype=np.float32) / SR
            hum = (np.sin(2 * math.pi * 120.0 * tt) * 0.5 + np.sin(2 * math.pi * 60.0 * tt)) * 0.045
            trem_ = 0.8 + 0.2 * np.sin(2 * math.pi * 7.0 * tt)
            pista_sfx[a24:b24] += hum * trem_
        # 025: comício burocrático + carimbadas violentas CLACK-THUD
        _add_bed(comicio_path, 4, 0.13)
        for tl_ in (0.32, 2.72):
            _add_estalo(tl_, 4, dur=0.05, gain=0.42)
            _add_estalo(tl_ + 0.04, 4, dur=0.16, gain=0.55, grave=True)
        # 026: tensão de briga eleitoral + vento de rua + buzina ao longe
        _add_bed(tensao_path, 5, 0.13)
        _add_sfx_loop(vento_sfx, 5, 0.12)
        _add_sfx_loop(crowd_sfx, 5, 0.07)
        for tl_ in (1.9, 4.2):
            a_b = int((timeline[5]["t_ini"] + tl_) * SR)
            n_b = int(0.5 * SR)
            if 0 <= a_b and a_b + n_b <= n_amostras:
                tt = np.arange(n_b, dtype=np.float32) / SR
                buzina = (np.sin(2 * math.pi * 415.0 * tt) + np.sin(2 * math.pi * 523.0 * tt)) * 0.08
                env_b = np.minimum(1.0, tt * 30.0) * np.exp(-tt * 4.0)
                pista_sfx[a_b:a_b + n_b] += buzina * env_b
        # 027: suspense de terror psicológico digital + enxurrada de notificações
        _add_bed(suspense_path, 6, 0.15)
        _add_sfx_loop(celular_sfx, 6, 0.13)
        t_pling = 0.3
        while t_pling < 8.2:
            _add_estalo(t_pling, 6, dur=0.07, freq=2350, gain=0.14)
            t_pling += 0.55
        # 028: comício em clímax de pânico + clique frenético de teclas
        _add_bed(comicio_path, 7, 0.15)
        t_tecla = 0.25
        while t_tecla < 8.3:
            _add_estalo(t_tecla, 7, dur=0.03, gain=0.22)
            t_tecla += 0.30
        for tl_ in (7.4, 7.65, 7.9):
            _add_estalo(tl_, 7, dur=0.05, gain=0.30)

    elif parte_num == 5:
        # Camas musicais Parte 5 (blocos 029 a 038) — programa eleitoral, debate e posse
        beds = os.path.join(ROOT, "production", "audio", "beds")
        sfx_dir = os.path.join(ROOT, "production", "audio", "sfx")
        jingle_path = os.path.join(beds, "jingle.mp3")
        comicio_path = os.path.join(beds, "comicio.mp3")
        tensao_path = os.path.join(beds, "tensao.mp3")
        cotidiano_path = os.path.join(beds, "cotidiano.mp3")
        bueiro_path = os.path.join(beds, "bueiro.mp3")
        fabinho_path = os.path.join(beds, "fabinho.mp3")
        suspense_path = os.path.join(beds, "suspense.mp3")
        crowd_sfx = os.path.join(sfx_dir, "crowd.mp3")
        grilos_sfx = os.path.join(sfx_dir, "grilos.mp3")
        flash_sfx = os.path.join(sfx_dir, "flash.mp3")
        celular_sfx = os.path.join(sfx_dir, "celular.mp3")
        agua_sfx = os.path.join(sfx_dir, "agua.mp3")
        moscas_sfx = os.path.join(sfx_dir, "moscas.mp3")
        latido_sfx = os.path.join(sfx_dir, "latido.mp3")
        sinos_sfx = os.path.join(sfx_dir, "sinos.mp3")
        fogos_sfx = os.path.join(sfx_dir, "fogos.mp3")
        vento_sfx = os.path.join(sfx_dir, "vento.mp3")

        def _trecho(i):
            return int(timeline[i]["t_ini"] * SR), min(n_amostras, int(timeline[i]["t_fim"] * SR))

        def _add_bed(path, i, gain):
            if not os.path.exists(path):
                return
            a, b = _trecho(i)
            if b <= a:
                return
            arr = carregar_mp3_como_array(path)
            n = b - a
            tiled = np.tile(arr, int(math.ceil(n / float(len(arr)))))[:n]
            pista_musica[a:b] += tiled * gain

        def _add_sfx_loop(path, i, gain):
            if not os.path.exists(path):
                return
            a, b = _trecho(i)
            if b <= a:
                return
            arr = carregar_mp3_como_array(path)
            n = b - a
            tiled = np.tile(arr, int(math.ceil(n / float(len(arr)))))[:n]
            pista_sfx[a:b] += tiled * gain

        def _add_estalo(t_local, i, dur=0.05, freq=0.0, gain=0.30, grave=False):
            a = int((timeline[i]["t_ini"] + t_local) * SR)
            n = int(dur * SR)
            if a < 0 or a + n > n_amostras:
                return
            tt = np.arange(n, dtype=np.float32) / SR
            if grave:
                grave_s = np.exp(-tt * 30.0) * np.sin(2 * math.pi * 70.0 * tt) * gain
                ruido = np.exp(-tt * 80.0) * (np.random.rand(n).astype(np.float32) - 0.5) * gain * 0.9
                pista_sfx[a:a + n] += grave_s + ruido
            elif freq > 0:
                pista_sfx[a:a + n] += np.exp(-tt * 45.0) * np.sin(2 * math.pi * freq * tt) * gain
            else:
                pista_sfx[a:a + n] += np.exp(-tt * 55.0) * (np.random.rand(n).astype(np.float32) - 0.5) * gain

        def _add_sfx_once(path, t_local, i, gain):
            if not os.path.exists(path):
                return
            a = int((timeline[i]["t_ini"] + t_local) * SR)
            if a < 0 or a >= n_amostras:
                return
            arr = carregar_mp3_como_array(path)
            n = min(len(arr), n_amostras - a)
            if n > 0:
                pista_sfx[a:a + n] += arr[:n] * gain

        # 029: jingle do programa eleitoral na TV de tubo + zumbido de transformador
        _add_bed(jingle_path, 0, 0.15)
        a29, b29 = _trecho(0)
        if b29 > a29:
            tt = np.arange(b29 - a29, dtype=np.float32) / SR
            hum = (np.sin(2 * math.pi * 120.0 * tt) * 0.4 + np.sin(2 * math.pi * 60.0 * tt) * 0.6) * 0.035
            trem_ = 0.85 + 0.15 * np.sin(2 * math.pi * 6.0 * tt)
            pista_sfx[a29:b29] += hum * trem_
        # 030: debate ao vivo — comício + multidão + grilos da noite + flashes da imprensa
        _add_bed(comicio_path, 1, 0.12)
        _add_sfx_loop(crowd_sfx, 1, 0.08)
        _add_sfx_loop(grilos_sfx, 1, 0.07)
        for tl_ in (1.2, 5.8):
            _add_sfx_once(flash_sfx, tl_, 1, 0.30)
        # 031: PUNCH em close — tensão cirúrgica + batimento cardíaco abafado
        _add_bed(tensao_path, 2, 0.15)
        for tl_ in (0.25, 0.85):
            _add_estalo(tl_, 2, dur=0.20, gain=0.5, grave=True)
        # 032: sabatina da juventude — cotidiano + notificações dos celulares
        _add_bed(cotidiano_path, 3, 0.12)
        _add_sfx_loop(celular_sfx, 3, 0.05)
        t_pl = 0.35
        while t_pl < 4.9:
            _add_estalo(t_pl, 3, dur=0.06, freq=2350, gain=0.11)
            t_pl += 0.7
        # 033: máquina pública — bueiro industrial + lodo + moscas dos urubus
        _add_bed(bueiro_path, 4, 0.14)
        _add_sfx_loop(agua_sfx, 4, 0.08)
        _add_sfx_loop(moscas_sfx, 4, 0.05)
        t_rat = 0.3
        while t_rat < 4.2:
            _add_estalo(t_rat, 4, dur=0.04, gain=0.24)
            _add_estalo(t_rat + 0.05, 4, dur=0.08, gain=0.3, grave=True)
            t_rat += 0.55
        _add_estalo(1.5, 4, dur=0.5, gain=0.10)
        # 034: Assuntos Externos — sci-fi do globo holográfico
        _add_bed(fabinho_path, 5, 0.13)
        a34, b34 = _trecho(5)
        if b34 > a34:
            tt = np.arange(b34 - a34, dtype=np.float32) / SR
            hum = (np.sin(2 * math.pi * 90.0 * tt) * 0.6 + np.sin(2 * math.pi * 45.0 * tt) * 0.4) * 0.04
            trem_ = 0.75 + 0.25 * np.sin(2 * math.pi * 3.5 * tt)
            pista_sfx[a34:b34] += hum * trem_
        # 035: apuração — comício em caos + multidão histérica + mordidas na urna
        _add_bed(comicio_path, 6, 0.14)
        _add_sfx_loop(crowd_sfx, 6, 0.12)
        t_mord = 0.18
        while t_mord < 11.0:
            _add_estalo(t_mord, 6, dur=0.07, gain=0.36)
            _add_estalo(t_mord + 0.06, 6, dur=0.10, gain=0.34, grave=True)
            t_mord += 0.45
        for tl_ in (2.2, 2.5):
            _add_sfx_once(latido_sfx, tl_, 6, 0.26)
        for tl_ in (3.2, 7.1):
            _add_sfx_once(flash_sfx, tl_, 6, 0.24)
        # 036: fórum da lei — suspense + relógio do cartório + martelada dupla
        _add_bed(suspense_path, 7, 0.14)
        t_tic = 0.25
        while t_tic < 5.3:
            _add_estalo(t_tic, 7, dur=0.03, freq=2400, gain=0.10)
            _add_estalo(t_tic + 0.5, 7, dur=0.03, freq=1900, gain=0.08)
            t_tic += 1.0
        _add_estalo(2.2, 7, dur=0.05, gain=0.45)
        _add_estalo(2.25, 7, dur=0.18, gain=0.5, grave=True)
        # 037: posse de 43 mil — comício triunfal + sinos + fogos + latido na mesa
        _add_bed(comicio_path, 8, 0.15)
        _add_sfx_loop(crowd_sfx, 8, 0.15)
        _add_sfx_loop(sinos_sfx, 8, 0.10)
        _add_sfx_loop(fogos_sfx, 8, 0.08)
        _add_sfx_once(latido_sfx, 0.6, 8, 0.34)
        _add_sfx_once(latido_sfx, 3.4, 8, 0.22)
        # 038: "ninguém pergunta" — suspense grave + grilos + vento de beco
        _add_bed(suspense_path, 9, 0.15)
        _add_sfx_loop(grilos_sfx, 9, 0.05)
        _add_sfx_loop(vento_sfx, 9, 0.05)
        a38, b38 = _trecho(9)
        if b38 > a38:
            tt = np.arange(b38 - a38, dtype=np.float32) / SR
            drone = np.sin(2 * math.pi * 70.0 * tt) * (0.8 + 0.2 * np.sin(2 * math.pi * 0.35 * tt)) * 0.04
            pista_sfx[a38:b38] += drone

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
        "Style: ZECA,DejaVu Sans,54,&H00FFB0B0,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,1.5,2,90,90,70,1",
        "Style: CARAMELO,DejaVu Sans,54,&H0080F0FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,1.5,2,90,90,70,1",
        "Style: PARDAL,DejaVu Sans,54,&H0080B4FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,1.5,2,90,90,70,1",
        "Style: REPORTER,DejaVu Sans,54,&H00FFD780,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,1.5,2,90,90,70,1",
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
        elif personagem == "ZECA":
            estilo = "ZECA"
        elif personagem == "CARAMELO":
            estilo = "CARAMELO"
        elif personagem == "PARDAL":
            estilo = "PARDAL"
        elif personagem == "REPORTER":
            estilo = "REPORTER"
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
    elif parte_num == 2:
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
    elif parte_num == 3:
        tempos_qc = [
            ("014 DÚVIDA / NEON ?", 4.0),
            ("015 COFRE / BUEIRO", 12.0),
            ("016 PEDESTAL / FUMAÇA", 18.0),
            ("017 SEU JORGE / PRATO", 22.0),
            ("018 ZECA 6 DEDOS / MESA", 28.0),
            ("019 CARAMELO / 4 PAINÉIS", 34.0),
            ("020 ZECA / LOGÍSTICA CAIXÃO", 39.0),
            ("020 ZECA / LIP SYNC", 41.5),
        ]
    elif parte_num == 4:
        tempos_qc = [
            ("021 CARAMELO / LIP SYNC", 3.4),
            ("022 ZECA / OBRA + LAMA", 8.9),
            ("023 ZECA / MEDICO + CRUZ", 15.6),
            ("024 CARAMELO / LINGUICA THC", 21.2),
            ("025 ZECA / CARIMBO", 25.2),
            ("026 PARDAL / POSTE", 30.2),
            ("027 ZECA / CELULAR MARTA", 36.9),
            ("028 PARDAL / CALCULADORA", 45.3),
        ]
    elif parte_num == 5:
        tempos_qc = [
            ("029 TV / FAMILIA NO SOFA", 4.0),
            ("030 REP / LIP SYNC DEBATE", 18.2),
            ("031 PARDAL / CLOSE PUNCH", 23.3),
            ("032 REP / SABATINA JUVENTUDE", 26.2),
            ("033 PARDAL / MAQUINA PUBLICA", 30.6),
            ("034 REP / GLOBO HOLOGRAFICO", 33.4),
            ("035 URNA COMIDA / CARAMELO", 39.5),
            ("036 JUIZ / LEI MORDIDA", 48.2),
            ("037 POSSE / 43 MIL PESSOAS", 54.3),
            ("038 PUPILAS ? / NINGUEM PERGUNTA", 59.5),
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
        
    n_linhas = max(2, -(-len(quadros) // 4))
    grade = Image.new("RGB", (1920, n_linhas * 270), (20, 20, 25))
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
    elif parte_num == 3:
        blocos = [b for b in todos_blocos if 14 <= obter_id_int(b) <= 20]
        movs = ["pan_left", "zoom_out", "zoom_in", "static_push", "pan_right", "zoom_in", "pan_left"]
        tem_titulo = False
    elif parte_num == 4:
        blocos = [b for b in todos_blocos if 21 <= obter_id_int(b) <= 28]
        movs = [b.get("movimento", "static_push") for b in blocos]
        tem_titulo = False
    elif parte_num == 5:
        blocos = [b for b in todos_blocos if 29 <= obter_id_int(b) <= 38]
        movs = [b.get("movimento", "static_push") for b in blocos]
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
