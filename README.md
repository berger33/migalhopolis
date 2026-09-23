# MIGALHÓPOLIS — T1E1: “O Prefeito de Quatro Patas”

Desenho animado de humor ácido estilo *Mr. Pickles* ambientado no Brasil interiorano,
produzido **inteiramente por agente** (roteiro, dublagem sintetizada, trilha sonora
original sintetizada, storyboard/arte, mixagem e renderização).

> ⚠ 14 anos — humor ácido, política ficcional e linguiça artesanal.

## O que é o episódio

Em Migalhópolis, “a cidade mais limpa do Brasil”, um vira-lata caramelo resolve
concorrer à prefeitura. Ninguém acha graça. Ninguém reclama. Ninguém é encontrado.

- **Formato:** animático (storyboard animado com Ken Burns) + dublagem + trilha + legendas
- **Duração:** episódio ~10 min + teaser de ~1 min
- **Vídeo:** `video/MIGALHOPOLIS_T1E1.mp4` (1080p, legendas queimadas)
- **Player web:** `player/index.html` (animático navegável, com legendas e seleção de cena)

## Estrutura

```
arte/            6 quadros de arte (estilo cartoon TV brasileira anos 70)
production/      pipeline completa (Python + ffmpeg + numpy)
  roteiro.json       roteiro estruturado: 16 cenas, 131 falas, 11 personagens
  synth.py           sintetizador da trilha (marchinha, xote, jingle, bueiro…) + SFX
  pack_speech.py     agrupa falas por voz para gravação em lote
  split_speech.py    recorta os blocos de voz em falas (DP por duração)
  build_timeline.py  linha do tempo + corte de 10 min + legendas ASS
  mix_episode.py     mixagem (voz + trilha com ducking + efeitos)
  render_video.py    MP4 1080p (segmentos + concat + legendas queimadas)
  servidor.py        servidor estático com Range p/ o player
player/          player web do animático
video/           MP4s finais
audio/           mixes finais (mp3)
```

## Como rodar

```bash
python3 production/servidor.py 8080   # e abrir /player/
# rebuild completo:
FFMPEG=/home/user/bin/ffmpeg PYTHONPATH=/home/user/pylibs \
  python3 production/synth.py --outdir /home/user/.cache/migalhopolis/audio --repo production/audio
python3 production/build_timeline.py
python3 production/mix_episode.py
python3 production/render_video.py
```

## Elenco (vozes escolhidas por audition)

Narrador (documentário) · Marta (fofocas) · Cida (grave) · Fabinho (criança) ·
Sr. Caramelo (melífluo e sinistro) · Zeca (advogado rato) · Prefeito Pardal (comício) —
além de Xavier, Devoto, Repórter e Os Meninos do Bueiro.

## Próximos episódios

T1E2 — “O Orçamento Participativo”: a Câmara aprova a castração… do orçamento.
