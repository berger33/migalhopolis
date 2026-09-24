#!/usr/bin/env python3
"""
Remonta a PARTE 1 inteira no método cel aprovado (piloto 043).
Aproveita o pipeline validado do render.py — timeline, mix de áudio, legendas
queimadas, QC e câmera — trocando apenas a cena viva (warp) pela CelViva
(substituição de desenhos). Áudio e legendas originais permanecem válidos.

Uso:  python3 production/remontar_parte01.py [--so-qc]
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
sys.path.insert(0, ROOT)
sys.path.insert(0, BASE)

import render                      # noqa: E402
from cel_viva import CelViva       # noqa: E402

# ---- a grande troca: cena por desenhos, sem warp ----
render.CenaViva = CelViva

if __name__ == "__main__":
    so_qc = "--so-qc" in sys.argv
    render.renderizar_parte(1, so_qc=so_qc)
