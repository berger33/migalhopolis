# Migalhópolis 🐕🌭

Série de desenho animado (estilo Rick and Morty) gerada por IA: roteiro, vozes, arte e render.

> *"Aqui, todo domingo tem churrasco. Todo boleto tem um culpado. E todo bueiro tem alguém rezando."*

## Episódio 1 — "O Pote" (~9 min)

Um cachorro vira-lata caramelo é eleito prefeito de Migalhópolis, cidade eleita três vezes
"a mais limpa do Brasil" por uma revista que ninguém leu. Política, sociedade, religião
e cannabis — tudo na comédia, tudo no ácido, tudo com sotaque de Grande São Paulo.

## Estrutura

```
roteiro/ROTEIRO_T01E01.md   roteiro completo (79 blocos + título + créditos)
roteiro/BIBLIA_VISUAL.md    bíblia visual: personagens, cenários, estilo
roteiro/blocos.json         machine-readable: texto, cena, movimento de câmera
audio/                      arquivos de voz (1 por bloco)
imagens/                    arquivos de imagem (1 por bloco)
personagens/                character sheets (referência de consistência)
video/                      renders (mp4)
scripts/render.py           renderer: imagem + voz + legenda -> mp4 1080p30
```

## Pipeline

1. **Roteiro** — `roteiro/blocos.json` (79 blocos de fala + título + créditos).
2. **Vozes** — TTS pt-BR, um arquivo por bloco em `audio/NNN_personagem.mp3`.
3. **Imagens** — um still por bloco em `imagens/NNN.jpg`, prompts em inglês,
   personagens fixos da bíblia visual para consistência.
4. **Render** — `scripts/render.py`: cada still vira um plano com movimento de câmera
   (zoom/pan), transições suaves, legendas ASS sincronizadas e áudio contínuo.
   Saída: `video/MIGALHOPOLIS_T01E01.mp4` (1080p, 30fps, H.264 + AAC).

## Workflow

Entregas em **lotes de 10 arquivos** (10 áudios + 10 imagens por lote), com commit
a cada lote. Ao final de cada lote, confirmação antes de seguir.

## Requisitos

- ffmpeg (usar `/home/user/bin/ffmpeg` — build estática com zoompan/xfade/subtitles)
- Python 3 + Pillow (pré-processamento das imagens para 1920x1080)
