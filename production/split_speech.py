#!/usr/bin/env python3
"""Recorta os blocos empacotados de volta em falas individuais.
Alinhamento: DP por aresta minimizando o erro de duração de cada fala
(modelo: fala ≈ chars*k + pausas_internas*p_int) com bônus para pausas
longas (as junções ' ...' são as mais longas do bloco).
Saída: production/audio/segments/{id}.wav + segments.json
"""
import json, math, os, subprocess, sys
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUD = os.path.join(RAIZ, "production", "audio")
CACHE = "/home/user/.cache/migalhopolis"
FF = os.environ.get("FFMPEG", "/home/user/bin/ffmpeg")
SR = 44100
INF = 1e18

def ffmpeg_decode(mp3):
    wav = os.path.join(CACHE, "dec", os.path.basename(mp3).replace(".mp3", ".wav"))
    os.makedirs(os.path.dirname(wav), exist_ok=True)
    if not os.path.exists(wav):
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", mp3, "-ar", str(SR), "-ac", "1", wav], check=True)
    return wav

def le_wav(caminho):
    import wave
    with wave.open(caminho, "rb") as w:
        assert w.getframerate() == SR and w.getnchannels() == 1
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32768.0
    return x

def escreve_wav(caminho, x):
    import wave, struct
    x = np.clip(x, -0.999, 0.999)
    pcm = (x * 32767).astype("<i2")
    with wave.open(caminho, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())

def env_energia(x, hop_s=0.01):
    hop = int(SR * hop_s)
    nf_ = len(x) // hop
    if nf_ == 0:
        return np.zeros(1), hop
    quad = (x[:nf_ * hop] ** 2).reshape(nf_, hop)
    return np.sqrt(quad.mean(axis=1)), hop

def detecta_silencios(x, rel_db=-40.0, min_sil=0.30):
    """Retorna [(centro_s, dur_s, ini_amostra, fim_amostra), ...] ordenado."""
    e, hop = env_energia(x)
    pico = np.percentile(e, 95)
    lim = pico * (10 ** (rel_db / 20))
    quieto = e < max(lim, 1e-5)
    runs = []
    i = 0
    N = len(quieto)
    while i < N:
        if quieto[i]:
            j = i
            while j < N and quieto[j]:
                j += 1
            dur = (j - i) * (hop / SR)
            if dur >= min_sil:
                a, b = i * hop, j * hop
                runs.append(((a + b) / 2 / SR, dur, a, b))
            i = j
        else:
            i += 1
    return runs

def pausas_internas(txt):
    return max(0, sum(txt.count(c) for c in ".!?…") - 1) + txt.count("...")

def corta(x, ini, fim, borda=0.045):
    a, b = int(ini), int(fim)
    seg = x[a:b]
    e, hop = env_energia(seg)
    lim = np.percentile(e, 95) * (10 ** (-38 / 20))
    idx = np.where(e > lim)[0]
    if len(idx) == 0:
        return seg
    p0 = max(0, idx[0] * hop - int(borda * SR))
    p1 = min(len(seg), (idx[-1] + 1) * hop + int(borda * SR))
    return seg[p0:p1]

def alinha_edge(textos, cand, total):
    """DP: escolhe len(textos)-1 silêncios como cortes minimizando
    soma dos erros relativos de duração por fala."""
    nseg = len(textos)
    P = [0.0] + [c[0] for c in cand] + [total]
    S = [0.0] + [c[1] for c in cand] + [0.0]
    N = len(P)
    chars = np.array([max(len(t), 1) for t in textos], float)
    npins = np.array([pausas_internas(t) for t in textos], float)
    soma_sil = sum(c[1] for c in cand)
    fala_total = max(total - soma_sil, 1.0)
    k0 = fala_total / chars.sum()
    melhor, melhores_params = None, None
    for p_int in (0.45, 0.65, 0.85):
        for bonus in (0.4, 0.9, 1.6):
            exp = chars * k0 + npins * p_int + 0.22
            custo = np.full((nseg, N), INF)
            volta = np.full((nseg, N), -1, int)
            for b in range(1, min(N - 1, nseg)):
                act = max(P[b] - P[0] - 0.5 * (S[0] + S[b]), 0.05)
                custo[0, b] = abs(act - exp[0]) / exp[0] - bonus * min(S[b], 1.2)
                volta[0, b] = 0
            for i in range(1, nseg - 1):
                for b in range(i + 1, N - 1):
                    melhor_c, melhor_a = INF, -1
                    for a in range(i, b):
                        if custo[i - 1, a] >= INF:
                            continue
                        act = max(P[b] - P[a] - 0.5 * (S[a] + S[b]), 0.05)
                        c = custo[i - 1, a] + abs(act - exp[i]) / exp[i] - bonus * min(S[b], 1.2)
                        if c < melhor_c:
                            melhor_c, melhor_a = c, a
                    if melhor_a >= 0:
                        custo[i, b], volta[i, b] = melhor_c, melhor_a
            for a in range(nseg - 1, N - 1):
                if custo[nseg - 2, a] >= INF:
                    continue
                act = max(P[N - 1] - P[a] - 0.5 * (S[a] + S[N - 1]), 0.05)
                c = custo[nseg - 2, a] + abs(act - exp[nseg - 1]) / exp[nseg - 1]
                if c < custo[nseg - 1, N - 1]:
                    custo[nseg - 1, N - 1], volta[nseg - 1, N - 1] = c, a
            if custo[nseg - 1, N - 1] >= INF:
                continue
            # reestima k com o corte atual e refaz uma vez
            b_node = volta[nseg - 1, N - 1]
            cortes = [b_node]
            b_node_ = b_node
            for i in range(nseg - 1, 1, -1):
                b_node_ = volta[i - 1, b_node_]
                cortes.append(b_node_)
            cortes = sorted(cortes)
            nos = [0] + cortes + [N - 1]
            ativos = []
            for i in range(nseg):
                span = P[nos[i + 1]] - P[nos[i]] - 0.5 * (S[nos[i]] + S[nos[i + 1]])
                ativos.append(max(span, 0.05))
            k1 = max(sum(ativos) - npins.sum() * p_int, 1.0) / chars.sum()
            if abs(k1 - k0) / k0 < 0.02:
                if melhor is None or custo[nseg - 1, N - 1] < melhor:
                    melhor, melhores_params = custo[nseg - 1, N - 1], cortes
                continue
            exp2 = chars * k1 + npins * p_int + 0.22
            custo2 = np.full((nseg, N), INF)
            volta2 = np.full((nseg, N), -1, int)
            for b in range(1, min(N - 1, nseg)):
                act = max(P[b] - P[0] - 0.5 * (S[0] + S[b]), 0.05)
                custo2[0, b] = abs(act - exp2[0]) / exp2[0] - bonus * min(S[b], 1.2)
                volta2[0, b] = 0
            for i in range(1, nseg - 1):
                for b in range(i + 1, N - 1):
                    melhor_c, melhor_a = INF, -1
                    for a in range(i, b):
                        if custo2[i - 1, a] >= INF:
                            continue
                        act = max(P[b] - P[a] - 0.5 * (S[a] + S[b]), 0.05)
                        c = custo2[i - 1, a] + abs(act - exp2[i]) / exp2[i] - bonus * min(S[b], 1.2)
                        if c < melhor_c:
                            melhor_c, melhor_a = c, a
                    if melhor_a >= 0:
                        custo2[i, b], volta2[i, b] = melhor_c, melhor_a
            for a in range(nseg - 1, N - 1):
                if custo2[nseg - 2, a] >= INF:
                    continue
                act = max(P[N - 1] - P[a] - 0.5 * (S[a] + S[N - 1]), 0.05)
                c = custo2[nseg - 2, a] + abs(act - exp2[nseg - 1]) / exp2[nseg - 1]
                if c < custo2[nseg - 1, N - 1]:
                    custo2[nseg - 1, N - 1], volta2[nseg - 1, N - 1] = c, a
            if custo2[nseg - 1, N - 1] >= INF:
                continue
            if melhor is None or custo2[nseg - 1, N - 1] < melhor:
                b_node = volta2[nseg - 1, N - 1]
                cortes2 = [b_node]
                for i in range(nseg - 1, 1, -1):
                    b_node = volta2[i - 1, b_node]
                    cortes2.append(b_node)
                melhor, melhores_params = custo2[nseg - 1, N - 1], sorted(cortes2)
    return melhores_params

def processa_pacote(pac):
    mp3 = os.path.join(AUD, pac["arquivo"])
    x = le_wav(ffmpeg_decode(mp3))
    textos = [u["texto"] for u in pac["unidades"]]
    nseg = len(textos)
    for rel, minsil in ((-40.0, 0.30), (-36.0, 0.24), (-44.0, 0.26)):
        cand = detecta_silencios(x, rel, minsil)
        if len(cand) >= nseg - 1:
            break
    if len(cand) < nseg - 1:
        print(f"  !! {pac['nome']}: só {len(cand)} silêncios p/ {nseg-1} cortes")
        return None
    cortes = alinha_edge(textos, cand, len(x) / SR)
    if cortes is None:
        print(f"  !! {pac['nome']}: alinhamento falhou")
        return None
    # DP retorna índices de nós (1..len(cand)); converter para amostras.
    nos = [0] + [int((cand[i - 1][2] + cand[i - 1][3]) / 2) for i in cortes] + [len(x)]
    saida = []
    chars = np.array([max(len(t), 1) for t in textos], float)
    durs = []
    for i, u in enumerate(pac["unidades"]):
        seg = corta(x, nos[i], nos[i + 1])
        durs.append(len(seg) / SR)
        cam = os.path.join(AUD, "segments", f"{u['id']}.wav")
        escreve_wav(cam, seg)
        saida.append({"id": u["id"], "dur": round(len(seg) / SR, 3)})
    durs = np.array(durs)
    s_char = durs / chars
    cv = float(s_char.std() / s_char.mean())
    suspeitas = [pac["unidades"][i]["id"] for i in range(nseg)
                 if s_char[i] > s_char.mean() * 1.9 or s_char[i] < s_char.mean() * 0.45]
    print(f"  {pac['nome']}: {nseg} falas, {durs.sum():.1f}s, cv={cv:.2f}" +
          (f" suspeitas={suspeitas}" if suspeitas else ""))
    return saida, cv

def main():
    packlist = json.load(open(os.path.join(AUD, "packlist.json"), encoding="utf-8"))
    os.makedirs(os.path.join(AUD, "segments"), exist_ok=True)
    todas, cvs = [], []
    for pac in packlist["packs"]:
        r = processa_pacote(pac)
        if r:
            todas += r[0]
            cvs.append(r[1])
    with open(os.path.join(AUD, "segments.json"), "w", encoding="utf-8") as fp:
        json.dump({"falas": todas}, fp, ensure_ascii=False, indent=1)
    tot = sum(f["dur"] for f in todas)
    print(f"OK {len(todas)} falas, {tot:.1f}s de voz ({tot/60:.2f} min), cv médio={np.mean(cvs):.2f}")

if __name__ == "__main__":
    main()
