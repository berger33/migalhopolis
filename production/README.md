# Pipeline de produção do T01E01 — edição animática

Esta pasta reúne a pipeline da edição animática do episódio (storyboard, vozes em pacotes, mixagem, legendas e render). Ela convive com a pipeline por blocos descrita no README da raiz; ambas são mantidas porque têm materiais e entregas próprios.

## Conteúdo

- `roteiro.json` — roteiro estruturado em cenas e falas.
- `corte.json` — seleção de falas para o episódio e para o teaser.
- `timeline.json` e `timeline_teaser.json` — cronologias usadas nos renders; `build_timeline.py` as gera.
- `legendas.ass` e `legendas_teaser.ass` — legendas queimadas nos vídeos.
- `audio/packed/` — pacotes de vozes recuperados; `packlist.json` relaciona cada arquivo às falas.
- `audio/segments.json` — metadados de alinhamento das falas. A versão recuperada está incompleta; se não cobrir todo o roteiro, o construtor de cronologia usa os tempos das cronologias finais para as falas já renderizadas. Para recalcular todos os tempos, execute `split_speech.py` com os dez pacotes disponíveis.
- `audio/beds/` e `audio/sfx/` — trilhas e efeitos compartilhados com o renderer por blocos.
- `audio/ep01_mix.mp3` e `audio/teaser_mix.mp3` — mixes finais publicados.
- `synth.py`, `split_speech.py`, `build_timeline.py`, `mix_episode.py` e `render_video.py` — etapas da pipeline.
- `pack_speech.py` — prepara o texto em pacotes para uma nova gravação/TTS.
- `servidor.py` — servidor local do player.

Os seis quadros usados pelo animático ficam em `../arte/`, o player em `../player/` e as entregas em `../video/`.

## Recriar as entregas

Requisitos: Python 3, NumPy, FFmpeg e fontes DejaVu Sans. Defina `FFMPEG` se o executável não estiver em `/home/user/bin/ffmpeg`. A síntese de trilha/efeitos usa o cache configurado na produção; os pacotes de voz já gravados estão em `audio/packed/`.

```bash
# Gera trilhas e efeitos no cache e atualiza os arquivos-fonte versionados.
FFMPEG=/caminho/para/ffmpeg PYTHONPATH=/home/user/pylibs \
  python3 production/synth.py \
  --outdir /home/user/.cache/migalhopolis/audio \
  --repo production/audio

# Alinha os pacotes de voz, atualiza segments.json e monta as cronologias/legendas.
FFMPEG=/caminho/para/ffmpeg python3 production/split_speech.py
python3 production/build_timeline.py

# Gera os mixes e, por fim, o episódio e o teaser.
FFMPEG=/caminho/para/ffmpeg python3 production/mix_episode.py
FFMPEG=/caminho/para/ffmpeg python3 production/render_video.py
```

Os MP4s já versionados são as entregas recuperadas das branches antigas. Não é necessário executar a pipeline para reproduzir o player.
