#!/usr/bin/env python3
"""Empacota as falas do roteiro em blocos por voz (para TTS em lote).
Cada pacote = um clip de áudio contendo várias falas do MESMO personagem,
separadas por ' ...\\n'. Depois o split_speech.py recorta de volta em falas.
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROTEIRO = os.path.join(RAIZ, "production", "roteiro.json")
SAIDA = os.path.join(RAIZ, "production", "audio")
SEP = " ...\n"

# nome, voz, ids das falas EM ORDEM (agrupamento idêntico ao usado nas gravações)
PACKS = [
    ("v00_00", "voice-00", ["c00-1", "c00-2", "c00-4", "c00-5", "c01-2", "c01-3",
                             "c04-1", "c04-6", "c05-1", "c07-1", "c07-2", "c07-3", "c07-4"]),
    ("v00_01", "voice-00", ["c07-5", "c07-6", "c08-1", "c11-1", "c11-3", "c11-5", "c11-7", "c11-9",
                             "c12-1", "c12-2", "c12-3", "c12-4", "c12-5", "c13-1"]),
    ("v00_02", "voice-00", ["c13-2", "c13-9", "c14-1", "c14-3", "c14-5", "c14-7",
                             "c15-1", "c15-2", "c15-3"]),
    ("v04_03", "voice-04", ["c00-3", "c01-1", "c04-9", "c04-11", "c04-13", "c05-3",
                             "c06-2", "c06-4", "c06-6", "c06-8", "c06-10", "c06-12", "c06-14",
                             "c10-1", "c11-11"]),
    ("v03_04", "voice-03", ["c02-1", "c02-2", "c02-3", "c04-3", "c04-5", "c04-7", "c04-8",
                             "c04-10", "c04-12", "c05-2", "c05-4", "c05-6", "c05-8", "c05-10",
                             "c09-2", "c09-4", "c09-6"]),
    ("v03_05", "voice-03", ["c09-8", "c09-10", "c09-11", "c11-2", "c11-4", "c11-6", "c11-8",
                             "c11-10", "c11-13", "c11-15", "c13-4", "c13-5", "c13-6", "c13-7",
                             "c13-8", "c13-10", "c14-2", "c14-4", "c14-6", "c14-8", "c15-4"]),
    ("v01_06", "voice-01", ["c03-1", "c03-3", "c03-5", "c03-7", "c03-9", "c03-11",
                             "c08-2", "c08-4", "c08-6", "c10-7"]),
    ("v05_07", "voice-05", ["c03-2", "c03-4", "c03-6", "c03-8", "c03-10",
                             "c08-3", "c08-5", "c10-8"]),
    ("v06_08", "voice-06", ["c04-2", "c04-4", "c05-5", "c05-7", "c05-9",
                             "c06-1", "c06-3", "c06-5", "c06-7", "c06-9", "c06-11", "c06-13",
                             "c10-2", "c10-3", "c10-4", "c10-5", "c10-6", "c11-12", "c11-14", "c13-3"]),
    ("v02_09", "voice-02", ["c09-1", "c09-3", "c09-5", "c09-7", "c09-9"]),
]

def main():
    roteiro = json.load(open(ROTEIRO, encoding="utf-8"))
    voz_por_quem = {p["id"]: p["voz"] for p in roteiro["elenco"]}
    unidades = {}
    for cena in roteiro["cenas"]:
        for f in cena["falas"]:
            unidades[f["id"]] = {"quem": f["quem"], "voz": voz_por_quem[f["quem"]],
                                 "texto": f["texto"], "cena": cena["id"]}
    usados = [i for _, _, ids in PACKS for i in ids]
    assert len(usados) == len(set(usados)), "fala repetida nos pacotes"
    faltando = set(unidades) - set(usados)
    if faltando:
        print("ATENÇÃO falas fora dos pacotes:", sorted(faltando))

    packs = []
    for nome, voz, ids in PACKS:
        segs = []
        total = 0
        for i in ids:
            u = unidades[i]
            assert u["voz"] == voz, f"{i}: voz {u['voz']} != pacote {voz}"
            total += len(u["texto"]) + len(SEP)
            segs.append({"id": i, "texto": u["texto"]})
        assert total <= 1500, f"{nome}: {total} chars > 1500"
        packs.append({"nome": nome, "voz": voz, "chars": total,
                      "arquivo": f"packed/{nome}.mp3", "unidades": segs})
        print(f"{nome} [{voz}] {total} chars, {len(segs)} falas")
    os.makedirs(SAIDA, exist_ok=True)
    with open(os.path.join(SAIDA, "packlist.json"), "w", encoding="utf-8") as fp:
        json.dump({"sep": SEP, "packs": packs}, fp, ensure_ascii=False, indent=1)
    print("OK packlist.json")
    # imprime textos completos para conferência
    if "--texto" in sys.argv:
        for p in packs:
            print(f"\n===== {p['nome']} [{p['voz']}] =====")
            print(SEP.join(s["texto"] for s in p["unidades"]))

if __name__ == "__main__":
    main()
