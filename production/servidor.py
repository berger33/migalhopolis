#!/usr/bin/env python3
"""Servidor estático com suporte a Range (seek de áudio). Uso:
python3 production/servidor.py [porta]   — serve a raiz do repo em 0.0.0.0
"""
import http.server, os, re, socketserver, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTA = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=RAIZ, **kw)
    def send_head(self):
        faixa = self.headers.get("Range")
        if not faixa:
            return super().send_head()
        try:
            caminho = self.translate_path(self.path)
            tamanho = os.path.getsize(caminho)
            m = re.match(r"bytes=(\d*)-(\d*)", faixa)
            i0 = int(m.group(1) or 0)
            i1 = int(m.group(2) or tamanho - 1)
            i1 = min(i1, tamanho - 1)
            with open(caminho, "rb") as fp:
                fp.seek(i0)
                dados = fp.read(i1 - i0 + 1)
            self.send_response(206)
            self.send_header("Content-Type", self.guess_type(caminho))
            self.send_header("Content-Range", f"bytes {i0}-{i1}/{tamanho}")
            self.send_header("Content-Length", str(len(dados)))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            return open(caminho, "rb") if False else _Bytes(dados)
        except Exception:
            return super().send_head()

class _Bytes:
    def __init__(self, dados):
        self.dados = dados
    def read(self, n=-1):
        return self.dados if n == -1 else self.dados[:n]
    def close(self):
        pass

class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    with Servidor(("0.0.0.0", PORTA), Handler) as httpd:
        print(f"MIGALHÓPOLIS em http://0.0.0.0:{PORTA}/player/", flush=True)
        httpd.serve_forever()
