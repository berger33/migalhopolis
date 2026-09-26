#!/usr/bin/env python3
"""
chroma_key.py — recorte de assets de animação (Migalhópolis).

Pega uma imagem gerada sobre fundo croma sólido (verde #00B140, ou
alternativas azul/branco) e devolve um PNG RGBA com **fundo transparente
real**: matte com feather, despill (remove a franja verde da borda),
limpeza de resíduos e corte automático no bounding box do sujeito.

O fundo é identificado por flood fill a partir das bordas da imagem, então
verde que exista DENTRO do personagem (roupa, faixa, objeto) é preservado.
Buracos de croma *fechados* dentro do sujeito (vão entre raios de roda,
janelas vazadas, frestas entre pernas) também viram transparente, mantendo
as estruturas finas que os cruzam (raios, trincas de vidro).

Uso:
    python3 assets/tools/chroma_key.py raw/31_x.png assets/vida_urbana/31_x.png
    python3 assets/tools/chroma_key.py --dir raw --out assets/vida_urbana

Dependências: Pillow, numpy, scipy.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

# ---------------------------------------------------------------- paleta croma
KEYS = {
    "auto": None,
    "green": np.array([0.0, 177.0 / 255.0, 64.0 / 255.0]),
    "blue": np.array([0.0, 71.0 / 255.0, 187.0 / 255.0]),
    "white": np.array([1.0, 1.0, 1.0]),
}

MIN_HOLE = 400  # buracos opacos menores que isso são tapados (ruído interno)
MIN_OLIVE_HOLE = 1500  # olive só vaza buracos grandes (janelas), protege olhos
MIN_SPECK = 25  # resíduos de alpha menores que isso são descartados
GM = 0.06       # margem de dominância de verde (escala 0..1)


def estimate_key(rgb: np.ndarray, key: str) -> np.ndarray:
    """Cor do fundo: fixa pela paleta ou medida na moldura da imagem."""
    if KEYS[key] is not None:
        return KEYS[key]
    h, w, _ = rgb.shape
    band = max(4, min(h, w) // 40)
    border = np.concatenate(
        [
            rgb[:band].reshape(-1, 3),
            rgb[-band:].reshape(-1, 3),
            rgb[:, :band].reshape(-1, 3),
            rgb[:, -band:].reshape(-1, 3),
        ]
    )
    return np.median(border, axis=0)


def masks(f: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Máscaras de verde: croma saturado vs. vidro/olive sombreado."""
    hsv = np.asarray(Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8)).convert("HSV"),
                     dtype=np.float32)
    hue = hsv[..., 0] * 360.0 / 255.0
    sat = hsv[..., 1] / 255.0
    val = hsv[..., 2] / 255.0
    chroma_hi = (hue > 115) & (hue < 165) & (sat > 0.6)          # croma puro/sombreado
    olive = (hue > 70) & (hue < 120) & (sat > 0.15) & (val < 0.85)  # vidro sujo/olive
    return chroma_hi, olive


def build_matte(rgb: np.ndarray, key_rgb: np.ndarray, feather: float) -> np.ndarray:
    """Matte 0..1: fundo ligado à moldura = 0, sujeito = 1."""
    f = rgb.astype(np.float32)
    key = key_rgb.astype(np.float32).reshape(1, 1, 3)

    dist = np.linalg.norm(f - key, axis=2)
    d0, d1 = 0.045, 0.30  # abaixo de d0 é fundo puro, acima de d1 é sujeito puro
    matte = np.clip((dist - d0) / (d1 - d0), 0.0, 1.0)

    bg_seed = (matte < 0.25).astype(np.int8)
    labels, n = ndimage.label(bg_seed, structure=np.ones((3, 3), dtype=np.int8))
    if n == 0:
        return matte
    touching = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])))
    touching.discard(0)
    bg = np.isin(labels, list(touching))

    bg_dil = ndimage.binary_dilation(bg, iterations=2)
    matte[bg] = 0.0

    dist_bg = ndimage.distance_transform_edt(~bg_dil)
    radius = max(1.0, feather)
    edge = np.clip(dist_bg / radius, 0.0, 1.0)
    matte = np.minimum(matte, edge)
    matte = ndimage.gaussian_filter(matte, sigma=0.6)
    return np.clip(matte, 0.0, 1.0)


def punch_green_holes(f: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Fundo croma preso DENTRO do sujeito vira transparente.

    Componentes de "fundo provável" (alpha baixo, croma saturado ou olive)
    que não tocam a moldura são buracos fechados: se o conteúdo é
    majoritariamente verde, vaza o verde e preserva as estruturas finas que
    cruzam o buraco (raios de roda, trincas de vidro). Buracos pequenos
    não-verdes são tapados (ruído interno).
    """
    alpha = alpha.copy()
    chroma_hi, olive = masks(f)
    verde = chroma_hi | olive
    bglike = (alpha <= 0.5) | verde
    labels, n = ndimage.label(bglike, structure=np.ones((3, 3), dtype=np.int8))
    if n == 0:
        return alpha
    touching = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])))
    touching.discard(0)
    for i in range(1, n + 1):
        if i in touching:
            continue
        comp = labels == i
        size = int(comp.sum())
        frac = float(verde[comp].mean())
        olive_frac = float(olive[comp].mean())
        if frac > 0.6 and (chroma_hi[comp].mean() > 0.3 or size >= MIN_OLIVE_HOLE):
            # buraco é croma preso: vaza o verde, preserva raios/trincas;
            # olive só em buracos grandes (janelas), nunca em olhos/detalhes
            alpha[comp & verde] = 0.0
        elif size < MIN_HOLE:  # microfuro não-verde: tampa
            alpha[comp] = np.maximum(alpha[comp], 0.55)
    return alpha


def punch_edge_blobs(alpha: np.ndarray, f: np.ndarray) -> np.ndarray:
    """Bolhas de croma pintadas sobre a silhueta, na franja da borda."""
    chroma_hi, _ = masks(f)
    dist_zero = ndimage.distance_transform_edt(alpha > 0.02)
    band = (alpha > 0.02) & (dist_zero <= 8)
    alpha = alpha.copy()
    alpha[band & chroma_hi] = 0.0
    return alpha


def remove_specks(alpha: np.ndarray) -> np.ndarray:
    specks, ns = ndimage.label(alpha > 0.02, structure=np.ones((3, 3), dtype=np.int8))
    if ns:
        sizes = ndimage.sum(np.ones_like(alpha), specks, index=range(1, ns + 1))
        alpha = np.where(np.isin(specks, [i + 1 for i, s in enumerate(sizes) if s < MIN_SPECK]), 0.0, alpha)
    return alpha


def despill(f: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Tira o verde vazado: forte na franja da silhueta, leve no interior."""
    out = f.copy()
    r, g, b = out[..., 0], out[..., 1], out[..., 2]
    ceiling = np.maximum(r, b)
    spill = np.clip(g - ceiling, 0.0, None)

    # banda de borda: até 5px do transparente → despill forte
    dist_zero = ndimage.distance_transform_edt(alpha > 0.02)
    band = (alpha > 0.02) & (dist_zero <= 5)
    strength = np.where(band, 0.85, 0.10)
    out[..., 1] = g - spill * strength
    return out


def process(src: Path, dst: Path, key: str = "auto", feather: float = 2.0, pad: int = 8,
            trim: bool = True) -> dict:
    f = np.asarray(Image.open(src).convert("RGB"), dtype=np.float32) / 255.0
    key_rgb = estimate_key(f, key)

    alpha = build_matte(f, key_rgb, feather)
    alpha = punch_green_holes(f, alpha)
    alpha = punch_edge_blobs(alpha, f)
    alpha = remove_specks(alpha)
    f = despill(f, alpha)

    out = np.dstack([np.clip(f, 0, 1), alpha[..., None]])
    out = (np.clip(out, 0, 1) * 255.0 + 0.5).astype(np.uint8)

    if trim:
        ys, xs = np.nonzero(alpha > 0.02)
        if ys.size:
            y0, y1 = max(int(ys.min()) - pad, 0), min(int(ys.max()) + pad + 1, out.shape[0])
            x0, x1 = max(int(xs.min()) - pad, 0), min(int(xs.max()) + pad + 1, out.shape[1])
            out = out[y0:y1, x0:x1]

    dst.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out, "RGBA").save(dst, optimize=True)

    a = out[..., 3]
    return {
        "file": dst.name,
        "size": f"{out.shape[1]}x{out.shape[0]}",
        "mode": "RGBA",
        "transparent_pct": round(float((a < 10).mean()) * 100, 1),
        "opaque_pct": round(float((a > 245).mean()) * 100, 1),
        "green_left": round(float(out[..., 1][a > 200].mean()) if (a > 200).any() else 0.0, 1),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Recorte croma -> PNG RGBA transparente")
    p.add_argument("src", nargs="?", help="imagem croma de entrada")
    p.add_argument("dst", nargs="?", help="PNG RGBA de saída")
    p.add_argument("--dir", help="processa todas as .png/.jpg de um diretório")
    p.add_argument("--out", default=".", help="diretório de saída (com --dir)")
    p.add_argument("--key", default="auto", choices=sorted(KEYS), help="cor do fundo croma")
    p.add_argument("--feather", type=float, default=2.0, help="raio do feather de borda (px)")
    p.add_argument("--no-trim", action="store_true", help="mantém o canvas original")
    args = p.parse_args(argv)

    jobs: list[tuple[Path, Path]] = []
    if args.dir:
        srcs = sorted(list(Path(args.dir).glob("*.png")) + list(Path(args.dir).glob("*.jpg")))
        if not srcs:
            print(f"nada encontrado em {args.dir}", file=sys.stderr)
            return 1
        jobs = [(s, Path(args.out) / (s.stem + ".png")) for s in srcs]
    elif args.src and args.dst:
        jobs = [(Path(args.src), Path(args.dst))]
    else:
        p.error("informe <src> <dst> ou --dir <pasta> --out <pasta>")

    for src, dst in jobs:
        info = process(src, dst, key=args.key, feather=args.feather, trim=not args.no_trim)
        print(
            f"OK {info['file']:<40} {info['size']:>10} {info['mode']} "
            f"transp={info['transparent_pct']:>5}% opaco={info['opaque_pct']:>5}% "
            f"verde_restante={info['green_left']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
