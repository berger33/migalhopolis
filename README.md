# Migalhópolis 🐕🌭

Série de animação ambientada em Migalhópolis: roteiro, vozes, arte, mixagem e renders produzidos por IA.

> *“Aqui, todo domingo tem churrasco. Todo boleto tem um culpado. E todo bueiro tem alguém rezando.”*

## T01E01

O primeiro episódio acompanha um vira-lata caramelo e sua campanha para a prefeitura da cidade “mais limpa do Brasil”. O repositório preserva **duas linhas de produção do episódio**: a edição animática com mixagem e teaser, e a edição construída em blocos com renders por partes. Os arquivos e pipelines ficam lado a lado; um não substitui o outro.

### Entregas

- `video/MIGALHOPOLIS_T1E1.mp4` — render do episódio com trilha, vozes e legendas queimadas.
- `video/TEASER_T1E1.mp4` — teaser renderizado.
- `video/parte_01.mp4` a `video/parte_03.mp4` — renders por partes da pipeline de 79 blocos.
- `player/index.html` — player navegável da edição animática.

## Mapa do repositório

```text
roteiro/                 roteiro por blocos, bíblia visual e dados para renderização
personagens/             referências visuais dos personagens
imagens/                 imagens das cenas da pipeline por blocos
audio/                   vozes individuais por bloco
legendas/                legendas ASS por parte
render.py                renderer da pipeline por blocos
video/                   episódios, teaser, partes e imagens de controle de qualidade

arte/                    seis quadros da edição animática
player/                  player web da edição animática
production/              roteiro, cronologias, mixagem e render da edição animática
  audio/beds/            trilhas musicais
  audio/sfx/             efeitos sonoros
  audio/packed/          pacotes de vozes usados no alinhamento/mixagem
  audio/                 mixes finais e metadados das falas
```

Veja [`production/README.md`](production/README.md) para o guia da edição animática e [`video/README.md`](video/README.md) para o catálogo dos renders.

## Pipeline por blocos

`render.py` combina os dados de `roteiro/blocos.json` com as vozes em `audio/`, as imagens em `imagens/` e as legendas de `legendas/`. O roteiro tem 79 blocos de fala, além dos cartões de título e créditos; os renders são divididos em partes para facilitar a revisão.

## Requisitos

- Python 3 e Pillow.
- FFmpeg com suporte a `zoompan`, `xfade` e `subtitles` (a pipeline da edição animática aceita `FFMPEG` para selecionar o binário).
