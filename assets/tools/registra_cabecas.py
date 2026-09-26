#!/usr/bin/env python3
"""
registra_cabecas.py — normalização de cabeças para o rig de lip sync (Migalhópolis).

Problema que resolve: as cabeças de visema (boca A / O / E-I, olhos fechados…)
precisam ser **trocáveis** sobre a cabeça neutra de referência: mesma escala e
mesmo enquadramento. O gerador devolve cada visema numa escala/framing
diferente, e redimensionar um PNG RGBA "cru" faz o RGB das áreas transparentes
(o fundo croma) vazar para a borda — o halo azul/esverdeado clássico de
recorte.

O que este script faz, para cada cabeça:

1. **Recorte** — mantém só o maior componente de alpha (descarta folhas de
   modelo em que o gerador devolveu cabeças/poses extras na mesma imagem).
2. **Registro de escala** — redimensiona para que a ALTURA do bounding box do
   sujeito seja igual à da cabeça-base (por padrão a neutra), preservando a
   proporção.
3. **Resize em alpha premultiplicado** — multiplica RGB pelo alpha antes de
   redimensionar e divide depois, eliminando o halo do fundo croma na borda.

Uso:
    python3 assets/tools/registra_cabecas.py croma/18_x.png croma/19_y.png \
        --base assets/personagens/12_caramelo_cabeca_neutra.png --out saida/

Dependências: Pillow, numpy, scipy.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def componente_principal(im: Image.Image, pad: int = 4) -> Image.Image:
    """Recorta o maior componente de alpha (folha de modelo → pose pedida)."""
    arr = np.asarray(im)
    a = arr[..., 3].astype(float) / 255
    lab, n = ndimage.label(a > 0.5)
    if n <= 1:
        return im
    tamanhos = ndimage.sum(np.ones_like(a), lab, index=range(1, n + 1))
    i = int(np.argmax(tamanhos)) + 1
    ys, xs = np.nonzero(lab == i)
    y0, y1 = max(0, int(ys.min()) - pad), min(arr.shape[0] - 1, int(ys.max()) + pad)
    x0, x1 = max(0, int(xs.min()) - pad), min(arr.shape[1] - 1, int(xs.max()) + pad)
    return im.crop((x0, y0, x1 + 1, y1 + 1))


def bbox_alpha(a: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(a > 0.02)
    return int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())


def altura_base(base: Path) -> int:
    """Altura do bounding box do sujeito na cabeça de referência."""
    a = np.asarray(Image.open(base).convert("RGBA"))[..., 3].astype(float) / 255
    y0, y1, _, _ = bbox_alpha(a)
    return y1 - y0 + 1


def resize_premult(im: Image.Image, escala: float) -> Image.Image:
    """Resize sem halo: RGB premultiplicado pelo alpha, depois despremultiplicado."""
    arr = np.asarray(im).astype(np.float32) / 255
    al = arr[..., 3:4]
    rgb = arr[..., :3]
    prem = np.concatenate([rgb * al, al], axis=2)

    novo = (max(1, round(im.width * escala)), max(1, round(im.height * escala)))
    canais = []
    for c in range(4):
        canais.append(
            np.asarray(
                Image.fromarray((prem[..., c] * 255).astype(np.uint8)).resize(novo, Image.LANCZOS),
                dtype=np.float32,
            )
            / 255
        )
    out = np.stack(canais, axis=2)
    alvo = out[..., 3:4]
    rgb_out = np.divide(out[..., :3], alvo, out=np.zeros_like(out[..., :3]), where=alvo > 1e-4)
    final = np.concatenate([rgb_out, alvo], axis=2)
    return Image.fromarray((np.clip(final, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")


def processa(src: Path, dst: Path, alvo_altura: int) -> dict:
    im = Image.open(src).convert("RGBA")
    im = componente_principal(im)
    a = np.asarray(im)[..., 3].astype(float) / 255
    y0, y1, _, _ = bbox_alpha(a)
    escala = alvo_altura / max(1, y1 - y0 + 1)
    im = resize_premult(im, escala)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, optimize=True)

    a = np.asarray(im)[..., 3].astype(float) / 255
    y0, y1, x0, x1 = bbox_alpha(a)
    return {
        "arquivo": dst.name,
        "tamanho": f"{im.width}x{im.height}",
        "escala": round(escala, 3),
        "bbox": f"{x1 - x0 + 1}x{y1 - y0 + 1}",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Registra cabeças de visema na escala da cabeça-base")
    p.add_argument("fontes", nargs="+", help="PNGs RGBA já recortados do croma")
    p.add_argument("--base", required=True, help="cabeça de referência (escala alvo)")
    p.add_argument("--out", required=True, help="diretório de saída")
    args = p.parse_args(argv)

    alvo = altura_base(Path(args.base))
    saida = Path(args.out)
    for src in args.fontes:
        info = processa(Path(src), saida / Path(src).name, alvo)
        print(
            f"OK {info['arquivo']:<40} {info['tamanho']:>10} "
            f"escala={info['escala']:<6} bbox_sujeito={info['bbox']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
