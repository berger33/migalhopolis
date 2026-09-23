#!/usr/bin/env python3
"""Monta a linha do tempo do episódio e do teaser + legendas ASS.
Entradas: roteiro.json, corte.json, segments.json
Saídas: production/timeline.json, production/timeline_teaser.json, production/legendas.ass
"""
import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROD = os.path.join(RAIZ, "production")
ESCALA_PAUSA = 0.62

def carrega():
    roteiro = json.load(open(os.path.join(PROD, "roteiro.json"), encoding="utf-8"))
    corte = json.load(open(os.path.join(PROD, "corte.json"), encoding="utf-8"))
    segs = {f["id"]: f["dur"] for f in json.load(open(os.path.join(PROD, "audio", "segments.json"), encoding="utf-8"))["falas"]}
    return roteiro, corte, segs

def monta(roteiro, manter, segs, cartao_titulo, cartao_final, gap):
    """Cena a cena: [ini,fim] por cena; fala: [ini,fim] absoluto."""
    t = cartao_titulo
    cenas, falas = [], []
    for cena in roteiro["cenas"]:
        unidades = [f for f in cena["falas"] if f["id"] in manter]
        if not unidades:
            continue
        ini_cena = t
        for f in unidades:
            t += f.get("pre", 0.4) * ESCALA_PAUSA
            d = segs[f["id"]]
            falas.append({"id": f["id"], "cena": cena["id"], "quem": f["quem"], "texto": f["texto"],
                          "ini": round(t, 3), "fim": round(t + d, 3), "dur": round(d, 3),
                          "sfx": f.get("sfx_antes", [])})
            t += d + f.get("pos", 0.4) * ESCALA_PAUSA
        cenas.append({"id": cena["id"], "numero": cena["numero"], "rotulo": cena["rotulo"],
                      "titulo": cena["titulo"], "frame": cena["frame"],
                      "bed": cena["trilha"]["bed"], "gain": cena["trilha"]["gain"],
                      "ini": round(ini_cena, 3), "fim": round(t - min(0.4, t - ini_cena) + gap * 0.5, 3)})
        t += gap
    if cenas:
        cenas[-1]["fim"] = round(cenas[-1]["fim"] - gap * 0.5 + 0.6, 3)
        t = t - gap + 0.6
    dur = t + cartao_final
    for c in cenas:
        c["fim"] = min(c["fim"], dur)
    return {"dur": round(dur, 3), "cartao_titulo": cartao_titulo,
            "cartao_final_ini": round(dur - cartao_final, 3), "cenas": cenas, "falas": falas}

def tempo_ass(s):
    h = int(s // 3600); m = int((s % 3600) // 60); sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"

def quebra(texto, largura=44):
    palavras, linhas, atual = texto.split(), [], ""
    for p in palavras:
        if len(atual) + len(p) + 1 > largura and atual:
            linhas.append(atual); atual = p
        else:
            atual = (atual + " " + p).strip()
    if atual:
        linhas.append(atual)
    return linhas

def escreve_ass(tl, caminho, teaser=False):
    cabecalho = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Fala,DejaVu Sans,50,&H00FFFFFF,&H000000FF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,3,1.5,2,80,80,64,1
Style: Titulo,DejaVu Sans,150,&H003CF0FF,&H000000FF,&H00201508,&H96000000,-1,0,0,0,100,100,2,0,1,5,2,5,60,60,320,1
Style: SubTitulo,DejaVu Sans,56,&H00E8E8E8,&H000000FF,&H00201508,&H96000000,-1,0,0,0,100,100,1,0,1,3,1,5,60,60,500,1
Style: Aviso,DejaVu Sans,30,&H00C8C8C8,&H000000FF,&H00201508,&H00000000,0,-1,0,0,100,100,0,0,1,2,1,2,120,120,90,1
Style: Credito,DejaVu Sans,36,&H00E8E8E8,&H000000FF,&H00181818,&H60000000,-1,0,0,0,100,100,0,0,1,2,1,5,60,60,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    NL = "\\N"
    if not teaser:
        ct = tl["cartao_titulo"]
        ev.append(f"Dialogue: 0,{tempo_ass(0.5)},{tempo_ass(ct - 0.3)},Titulo,,0,0,0,,MIGALHÓPOLIS")
        ev.append(f"Dialogue: 0,{tempo_ass(0.9)},{tempo_ass(ct - 0.3)},SubTitulo,,0,0,0,,T1E1 — O Prefeito de Quatro Patas")
        ev.append(f"Dialogue: 0,{tempo_ass(1.4)},{tempo_ass(ct - 0.3)},Aviso,,0,0,0,,a cidade mais limpa do Brasil{NL}humor ácido • ficção • nenhuma linguiça foi poupada")
    for f in tl["falas"]:
        linhas = NL.join(quebra(f["texto"]))
        ini = max(f["ini"], tl["cartao_titulo"] if not teaser else 0.0)
        ev.append(f"Dialogue: 0,{tempo_ass(ini)},{tempo_ass(f['fim'] + 0.12)},Fala,,0,0,0,,{linhas}")
    if not teaser:
        cf = tl["cartao_final_ini"]
        texto_cred = NL.join([
            "MIGALHÓPOLIS — T1E1",
            "roteiro, vozes, trilha e imagem: gerados nesta sessão",
            "elenco: o narrador, a Marta, a Cida, o Fabinho,",
            "o Caramelo, o Zeca e o prefeito Pardal",
            "trilha: marchinha, xote, jingle e caixinha de música sintetizadas",
            "PRÓXIMO EPISÓDIO: “O ORÇAMENTO PARTICIPATIVO”",
            "moral: não existe cidade limpa — existe cidade com o cachorro certo",
        ])
        ev.append(f"Dialogue: 0,{tempo_ass(cf + 0.4)},{tempo_ass(tl['dur'] - 0.4)},Credito,,0,0,0,,{texto_cred}")
    with open(caminho, "w", encoding="utf-8") as fp:
        fp.write(cabecalho + "\n".join(ev) + "\n")

def main():
    roteiro, corte, segs = carrega()
    manter_ep = set(corte["episodio_manter"])
    manter_te = set(corte["teaser_manter"])
    tl = monta(roteiro, manter_ep, segs, corte["cartao_titulo"], corte["cartao_final"], corte["gap_cenas"])
    tl_te = monta(roteiro, manter_te, segs, 0.6, 1.5, 0.45)
    json.dump(tl, open(os.path.join(PROD, "timeline.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(tl_te, open(os.path.join(PROD, "timeline_teaser.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    escreve_ass(tl, os.path.join(PROD, "legendas.ass"))
    escreve_ass(tl_te, os.path.join(PROD, "legendas_teaser.ass"), teaser=True)
    voz_ep = sum(f["dur"] for f in tl["falas"])
    voz_te = sum(f["dur"] for f in tl_te["falas"])
    print(f"EPISÓDIO: {tl['dur']:.1f}s ({tl['dur']/60:.2f} min), {len(tl['falas'])} falas, voz={voz_ep:.1f}s, {len(tl['cenas'])} cenas")
    print(f"TEASER:   {tl_te['dur']:.1f}s ({tl_te['dur']/60:.2f} min), {len(tl_te['falas'])} falas")

if __name__ == "__main__":
    main()
