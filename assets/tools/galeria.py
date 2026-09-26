#!/usr/bin/env python3
"""
galeria.py — preview de validação dos assets de animação (Migalhópolis).

Sobe um servidor estático da raiz do repo em 0.0.0.0 (mesmo padrão de
`production/servidor.py`) e responde em `/` com uma galeria gerada em memória:
grade de todos os PNGs de cada categoria de `assets/` (vida_urbana,
personagens, …) sobre fundo xadrez, para conferir visualmente a transparência
real (canal alpha) de cada recorte de croma. O lote mais recente é destacado
com contorno verde.

Uso:
    python3 assets/tools/galeria.py [porta]   # padrão 8080

Nada é escrito em disco: o HTML é montado por requisição a partir do diretório
de assets, então a galeria nunca fica desatualizada.
"""

from __future__ import annotations

import http.server
import os
import socketserver
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ASSETS = RAIZ / "assets"
IGNORAR = {"tools"}
PORTA = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

CSS = """
 body{margin:0;font:14px/1.4 system-ui,sans-serif;background:#151519;color:#eee}
 header{padding:18px 22px;background:#1e1e24;border-bottom:1px solid #333}
 header h1{margin:0 0 6px;font-size:20px} header p{margin:2px 0;color:#aaa}
 h2{margin:18px 22px 0;font-size:16px;color:#ddd;border-bottom:1px solid #333;padding-bottom:6px}
 .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px;padding:18px 22px}
 figure{margin:0;border:1px solid #2c2c34;border-radius:10px;overflow:hidden;background:
   repeating-conic-gradient(#787880 0% 25%, #585860 0% 50%) 0 0/24px 24px}
 figure img{display:block;width:100%;height:190px;object-fit:contain}
 figcaption{background:#101014;padding:6px 9px;font-size:12px;color:#ccc}
 figure.novo{outline:2px solid #00b140;outline-offset:-2px}
 figure.novo figcaption{background:#06300f;color:#b6ffce}
"""


def lote_atual() -> set[str]:
    """Chaves `categoria/nn` do último lote marcado como CONCLUÍDO no manifesto."""
    import re

    readme = RAIZ / "assets" / "README.md"
    if not readme.exists():
        return set()
    texto = readme.read_text(encoding="utf-8")
    secoes = re.split(r"(?=^### )", texto, flags=re.M)
    concluidas = [s for s in secoes if s.startswith("### Lote") and "CONCLUÍDO" in s.split("\n")[0]]
    if not concluidas:
        return set()
    pares = re.findall(r"`([a-z_]+)/(\d+)[a-z_0-9]*\.png`", concluidas[-1])
    return {f"{cat}/{nn}" for cat, nn in pares}


def categorias() -> list[tuple[str, list[Path]]]:
    """Subpastas de assets/ que contêm PNGs, em ordem alfabética."""
    saida = []
    for pasta in sorted(p for p in ASSETS.iterdir() if p.is_dir() and p.name not in IGNORAR):
        pngs = sorted(pasta.glob("*.png"))
        if pngs:
            saida.append((pasta.name, pngs))
    return saida


def html_galeria() -> bytes:
    novos = lote_atual()
    blocos = []
    total = 0
    for cat, assets in categorias():
        total += len(assets)
        cards = []
        for a in assets:
            nn = a.name.split("_")[0]
            cls = "novo" if f"{cat}/{nn}" in novos else ""
            cards.append(
                f'<figure class="{cls}"><img src="/assets/{cat}/{a.name}" '
                f'alt="{a.name}" loading="lazy"><figcaption>{a.stem}</figcaption></figure>'
            )
        blocos.append(f"<h2>{cat} — {len(assets)}</h2><div class=\"grid\">{''.join(cards)}</div>")
    pagina = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Migalhópolis — galeria de assets ({total})</title>
<style>{CSS}</style></head><body>
<header><h1>Migalhópolis — assets de animação</h1>
<p><strong>{total}</strong> assets isolados com fundo transparente (PNG RGBA) ·
contorno verde = lote mais recente (aguardando revisão/merge)</p>
<p>Fundo xadrez = transparência real do canal alpha. Recorte de croma por
<code>assets/tools/chroma_key.py</code>.</p></header>
{''.join(blocos)}</body></html>"""
    return pagina.encode("utf-8")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(RAIZ), **kw)

    def do_GET(self):  # noqa: N802 (nome da API stdlib)
        if self.path in ("/", "/index.html", ""):
            corpo = html_galeria()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
        return super().do_GET()

    def log_message(self, *a):  # silencioso
        pass


class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    with Servidor(("0.0.0.0", PORTA), Handler) as httpd:
        print(f"galeria de assets em http://0.0.0.0:{PORTA}/", flush=True)
        httpd.serve_forever()
