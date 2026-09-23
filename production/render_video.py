#!/usr/bin/env python3
"""Renderiza o MP4 1080p (episódio + teaser): quadros com Ken Burns,
cartões de título/encerramento, legendas ASS queimadas e a mixagem.
Renderiza segmento a segmento (memória-segura) e concatena.
"""
import json, math, os, subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROD = os.path.join(RAIZ, "production")
AUD = os.path.join(PROD, "audio")
VID = os.path.join(RAIZ, "video")
SEG = "/home/user/.cache/migalhopolis/seg"
FF = os.environ.get("FFMPEG", "/home/user/bin/ffmpeg")
FPS = 25
W, H = 1920, 1080

def sh(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg falhou:\n" + " ".join(args) + "\n" + r.stderr[-1600:])
    return r

def zoompan(i, d, dur):
    estilo = i % 4
    if estilo == 0:
        z = f"min(1.0+{0.10/d:.8f}*on,1.10)"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif estilo == 1:
        z = f"max(1.10-{0.10/d:.8f}*on,1.0)"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif estilo == 2:
        z = "1.09"
        x, y = f"(iw-iw/zoom)*on/{d}", "ih/2-(ih/zoom/2)"
    else:
        z = "1.07"
        x, y = "iw/2-(iw/zoom/2)", f"(ih-ih/zoom)*(1-on/{d})"
    return f"zoompan=z='{z}':x='{x}':y='{y}':d={d}:s={W}x{H}:fps={FPS}"

def renderiza_segmento(caminho_img, ini, fim, saida, escurece=False, idx=0):
    dur = fim - ini
    d = max(int(round(fim * FPS)) - int(round(ini * FPS)), 2)
    base = "scale=2400:1350:force_original_aspect_ratio=increase,crop=2400:1350"
    filtro = f"{base},{zoompan(idx, d, dur)},trim=end_frame={d},setpts=PTS-STARTPTS,format=yuv420p"
    if escurece:
        filtro = f"{base},colorchannelmixer=rr=0.44:gg=0.44:bb=0.44,{zoompan(idx + 1, d, dur)},trim=end_frame={d},setpts=PTS-STARTPTS,format=yuv420p"
    sh([FF, "-y", "-loglevel", "error", "-loop", "1", "-i", caminho_img,
        "-vf", filtro, "-r", str(FPS), "-frames:v", str(d),
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-an", saida])
    return d

def monta(tl_arq, ass_arq, mix_mp3, saida_mp4, cartao_frame, final_frame):
    tl = json.load(open(tl_arq, encoding="utf-8"))
    os.makedirs(SEG, exist_ok=True)
    os.makedirs(VID, exist_ok=True)
    segs = []
    total_frames = 0
    ct = tl["cartao_titulo"]
    cfi = tl["cartao_final_ini"]
    d = renderiza_segmento(cartao_frame, 0.0, ct, f"{SEG}/seg_000.mp4", escurece=True)
    segs.append(f"{SEG}/seg_000.mp4"); total_frames += d
    for i, c in enumerate(tl["cenas"], start=1):
        caminho = os.path.join(RAIZ, c["frame"])
        saida = f"{SEG}/seg_{i:03d}.mp4"
        d = renderiza_segmento(caminho, c["ini"], c["fim"], saida)
        segs.append(saida); total_frames += d
    d = renderiza_segmento(final_frame, cfi, tl["dur"], f"{SEG}/seg_999.mp4", escurece=True)
    segs.append(f"{SEG}/seg_999.mp4"); total_frames += d
    lista = f"{SEG}/lista.txt"
    with open(lista, "w") as fp:
        for s in segs:
            fp.write(f"file '{s}'\n")
    ass = os.path.join(PROD, os.path.basename(ass_arq))
    sh([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lista,
        "-i", mix_mp3,
        "-vf", f"subtitles={ass}:fontsdir=/usr/share/fonts",
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart", saida_mp4])
    mb = os.path.getsize(saida_mp4) / 1e6
    print(f"OK {saida_mp4}: {total_frames/FPS:.1f}s de vídeo, {mb:.1f} MB")

def main():
    cartao = os.path.join(RAIZ, "arte", "frame-01-praca.jpg")
    final = os.path.join(RAIZ, "arte", "frame-06-final.jpg")
    monta(os.path.join(PROD, "timeline.json"), "legendas.ass",
          os.path.join(AUD, "ep01_mix.mp3"), os.path.join(VID, "MIGALHOPOLIS_T1E1.mp4"),
          cartao, final)
    monta(os.path.join(PROD, "timeline_teaser.json"), "legendas_teaser.ass",
          os.path.join(AUD, "teaser_mix.mp3"), os.path.join(VID, "TEASER_T1E1.mp4"),
          cartao, final)

if __name__ == "__main__":
    main()
