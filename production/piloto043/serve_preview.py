#!/usr/bin/env python3
"""Player de preview do piloto de animação — serve o MP4 com Range (toca em qualquer navegador)."""
import html
import mimetypes
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PORT = 8000

PAGINA = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Migalhopolis — Animation Test 043</title>
<style>
  body { margin: 0; background: #101014; color: #eee;
         font-family: -apple-system, "Segoe UI", Roboto, sans-serif; }
  .palco { max-width: 1100px; margin: 0 auto; padding: 24px 16px 60px; }
  h1 { font-size: 20px; letter-spacing: .3px; }
  h1 small { color: #888; font-weight: normal; }
  .tela { background: #000; border-radius: 10px; overflow: hidden;
          box-shadow: 0 12px 40px rgba(0,0,0,.55); }
  video { width: 100%; display: block; }
  .acoes { display: flex; gap: 12px; margin: 16px 0 8px; flex-wrap: wrap; }
  a.btn { background: #2d6cdf; color: #fff; text-decoration: none;
          padding: 10px 18px; border-radius: 8px; font-weight: 600; }
  a.btn.sec { background: #2a2a33; }
  .nota { color: #999; font-size: 13px; line-height: 1.5; margin-top: 14px; }
  .arquivos a { color: #7fb3ff; display: block; padding: 3px 0; }
  img { width: 100%; border-radius: 8px; margin-top: 10px; }
  hr { border: 0; border-top: 1px solid #26262e; margin: 28px 0; }
</style>
</head>
<body>
  <div class="palco">
    <h1>Animation Test — bloco 043 <small>"De quê?" · método cel por substituição · 24 fps</small></h1>
    <div class="tela">
      <video id="v" controls autoplay loop muted playsinline preload="auto">
        <source src="/video/piloto_043_animtest.mp4" type="video/mp4">
      </video>
    </div>
    <div class="acoes">
      <a class="btn" href="/video/piloto_043_animtest.mp4" download="piloto_043_animtest.mp4">⬇ Baixar MP4</a>
      <a class="btn sec" href="/video/qc_piloto_043.png" download="qc_piloto_043.png">Folha QC (PNG)</a>
    </div>
    <p class="nota">Boca e olhos são <b>desenhos trocados por patch seco</b> (sem adesivo, sem warp).
    Fala real às 2,2s com estouro do punch. Faltam 7 desenhos do mouth chart/poses (limite de geração) — versão completa em seguida.</p>
    <hr>
    <h1>Quadros QC</h1>
    <img src="/video/qc_piloto_043.png" alt="Folha QC">
    <hr>
    <h1>Arquivos em video/</h1>
    <div class="arquivos">__ARQUIVOS__</div>
  </div>
</body>
</html>"""


def listar_arquivos():
    vdir = os.path.join(ROOT, "video")
    itens = []
    for nome in sorted(os.listdir(vdir)):
        if nome.lower().endswith((".mp4", ".png", ".jpg")):
            itens.append(f'<a href="/video/{html.escape(nome)}" download>{html.escape(nome)}</a>')
    return "\n".join(itens) or "(vazio)"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        caminho = self.path.split("?")[0]
        if caminho in ("/", "/index.html"):
            corpo = PAGINA.replace("__ARQUIVOS__", listar_arquivos()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
        m = re.match(r"^/video/([^/]+)$", caminho)
        if m:
            nome = os.path.basename(m.group(1))
            fpath = os.path.join(ROOT, "video", nome)
            if os.path.isfile(fpath):
                self.enviar_arquivo(fpath)
                return
        self.send_error(404)

    def enviar_arquivo(self, fpath):
        tamanho = os.path.getsize(fpath)
        ctype = mimetypes.guess_type(fpath)[0] or "application/octet-stream"
        intervalo = self.headers.get("Range")
        if intervalo:
            m = re.match(r"bytes=(\d*)-(\d*)", intervalo)
            ini = int(m.group(1)) if m and m.group(1) else 0
            fim = int(m.group(2)) if m and m.group(2) else tamanho - 1
            fim = min(fim, tamanho - 1)
            n = fim - ini + 1
            self.send_response(206)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Range", f"bytes {ini}-{fim}/{tamanho}")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(n))
            self.end_headers()
            with open(fpath, "rb") as f:
                f.seek(ini)
                self.wfile.write(f.read(n))
        else:
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(tamanho))
            self.end_headers()
            with open(fpath, "rb") as f:
                self.wfile.write(f.read())


if __name__ == "__main__":
    servidor = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Player no ar: http://0.0.0.0:{PORT}")
    servidor.serve_forever()
