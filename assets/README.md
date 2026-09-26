# ASSETS DE ANIMAÇÃO — MIGALHÓPOLIS

Biblioteca de assets para animação e interpolação das 79 imagens-base da pasta
`imagens/`. Aqui NÃO ficam "fotos comuns": cada arquivo é um **asset isolado**
(personagem, objeto, animal, efeito) com **fundo transparente** (PNG com alpha),
pronto para ser composto sobre qualquer cena.

## Padrão de produção

- Estilo: 2D cartoon de TV estilo *Rick and Morty* — traço grosso, paleta terrosa
  com acentos neon, atuação exagerada (ver `roteiro/BIBLIA_VISUAL.md`).
- Fidelidade: todos os assets são derivados dos personagens/objetos já
  estabelecidos nas 79 imagens de `imagens/`.
- Geração: imagem gerada sobre fundo verde croma → chroma key com tratamento de
  borda (feather), despill e recorte automático via `assets/tools/chroma_key.py`
  (no repo): flood fill do fundo pela moldura, vazamento de croma preso em
  buracos fechados (raios de roda, janelas, frestas) preservando estruturas
  finas, despill na franja da silhueta e trim no bounding box.
- Nomenclatura: `assets/<categoria>/<nn>_<nome>.png` (nn = ordem dentro da categoria).
- Total planejado: **~342 imagens** (ver tabela abaixo). Produção em lotes de
  **10 por turno**, 1 commit por imagem no GitHub.

## Plano geral (342 imagens)

| Categoria | Imagens | Pasta |
|---|---|---|
| Vida Urbana Guarulhos (10 elementos de rua, 84 assets) | 84 | `assets/vida_urbana/` |
| Cenários base + variações | 18 | `assets/cenarios/` |
| Personagens principais | 135 | `assets/personagens/` |
| Figurantes e grupos | 41 | `assets/figurantes/` |
| Animais (urubus, moscas etc.) | 11 | `assets/animais/` |
| Cenário/objetos animados | 31 | `assets/objetos/` |
| Natureza e efeitos | 17 | `assets/efeitos/` |
| Props | 5 | `assets/props/` |
| **TOTAL** | **~342** | |

## Elementos de Vida Urbana (84 assets — 10 elementos)

| # | Elemento | Assets previstos | Prioridade |
|---|---|---|---|
| 1 | Homem da Carroça | 9 | Alta |
| 2 | Dois Zikas/Mandrakes | 11 | Alta |
| 3 | Cachorros de Rua | 10 | Alta |
| 4 | Gato Preto | 8 | Média |
| 5 | Carro Velho | 6 | Média |
| 6 | Criança com Pipa | 9 | Alta |
| 7 | Velha com Cadeira | 9 | Alta |
| 8 | Vizinha na Janela | 8 | Média |
| 9 | Zé do Café | 9 | Média |
| 10 | Ciclista | 5 | Baixa |

### Integração com a cena c00 (praça)

| Tempo | Narrador | Ação de rua |
|---|---|---|
| 8.7–22.1s | "Migalhópolis..." | Carroça passando + cachorro + velha sentada |
| 22.7–29.1s | "Aqui, todo domingo..." | Zikas na esquina + criança com pipa |
| 29.9–37.4s | Devoto falando | Gato pulando muro + vizinha na janela |
| 38.2–44.4s | "No centro da praça..." | Ciclista passando + carro velho |
| 45.0–48.9s | "O Caramelo não é..." | Cães dormindo + Zé do café |

## Status de produção

### Lote 1 — ✅ CONCLUÍDO (10/342) — hero asset de cada elemento de rua

| Arquivo | Descrição | Poses posteriores |
|---|---|---|
| `vida_urbana/01_carroceiro.png` | Carroceiro completo: cavalo + carroça + velho do chapéu | 8 restantes (variações de pose/rollback) |
| `vida_urbana/02_zikas.png` | Dois Zikas/Mandrakes em pé (boné vermelho + óculos escuros, correntes) | 10 restantes |
| `vida_urbana/03_cachorro_rua.png` | Vira-lata cinza andando, língua de fora | 9 restantes |
| `vida_urbana/04_gato_preto.png` | Gato preto de olhos verdes, costas arqueadas | 7 restantes |
| `vida_urbana/05_carro_velho.png` | Fusca azul-bebê amassado e enferrujado, vista lateral | 5 restantes |
| `vida_urbana/06_crianca_pipa.png` | Menino correndo com pipa vermelha/amarela | 8 restantes |
| `vida_urbana/07_velha_cadeira.png` | Vovó na cadeira de plástico branca, braços cruzados | 8 restantes |
| `vida_urbana/08_vizinha_janela.png` | Vizinha fofoqueira na janela + varalzinho | 7 restantes |
| `vida_urbana/09_ze_cafe.png` | Zé do Café de bule e avental, corpo inteiro | 8 restantes |
| `vida_urbana/10_ciclista.png` | Ciclista de bicicleta velha, vista lateral | 4 restantes |

**Próximo lote (2):** variações de pose — carroceiro, zikas, cachorros (deitado/dormindo
para 45.0–48.9s), criança com pipa soltando/empinando, gato pulando, velha acenando.

### Lote 2 — ✅ CONCLUÍDO (20/342) — variações de pose para a cena c00 (praça)

| Arquivo | Descrição | Poses restantes |
|---|---|---|
| `vida_urbana/11_carroceiro_passando.png` | Carroceiro em pé na carroça acenando e gritando, cavalo andando (8.7–22.1s) | 7 restantes |
| `vida_urbana/12_zikas_esquina.png` | Zikas/Mandrakes encostados na esquina, um olhando o céu (22.7–29.1s) | 9 restantes |
| `vida_urbana/13_cachorro_dormindo.png` | Vira-lata cinza dormindo enrolado, olhos fechados (45.0–48.9s) | 8 restantes |
| `vida_urbana/14_gato_saltando.png` | Gato preto pulando no ar, corpo esticado (29.9–37.4s) | 6 restantes |
| `vida_urbana/15_carro_velho_andando.png` | Fusca azul-bebê rodando, fumacinha no escapamento (38.2–44.4s) | 4 restantes |
| `vida_urbana/16_crianca_pipa_empinando.png` | Menino puxando a linha com o corpo, pipa no alto (22.7–29.1s) | 7 restantes |
| `vida_urbana/17_velha_acenando.png` | Vovó sentada na cadeira de plástico, acenando com a mão, sorriso | 7 restantes |
| `vida_urbana/18_vizinha_fofocando.png` | Vizinha fofoqueira na janela com xícara de café, apontando pra rua (29.9–37.4s) | 6 restantes |
| `vida_urbana/19_ze_cafe_servindo.png` | Zé do Café oferecendo duas canecas fumegantes (45.0–48.9s) | 7 restantes |
| `vida_urbana/20_ciclista_passando.png` | Ciclista pedalando, olhando por cima do ombro (38.2–44.4s) | 3 restantes |

### Lote 3 — ✅ CONCLUÍDO (30/342) — poses intermediárias para animação

| Arquivo | Descrição | Poses restantes |
|---|---|---|
| `vida_urbana/21_carroceiro_sentado.png` | Carroceiro sentado segurando as rédeas, cavalo em passo de trote | 6 restantes |
| `vida_urbana/22_zikas_conversando.png` | Dupla conversando, um gesticulando e outro de braços cruzados | 8 restantes |
| `vida_urbana/23_segundo_cachorro_dormindo.png` | Segundo cão de rua, caramelo, dormindo ao lado do vira-lata cinza | 7 restantes |
| `vida_urbana/24_gato_aterrissando.png` | Gato preto no instante da aterrissagem | 5 restantes |
| `vida_urbana/25_carro_velho_freando.png` | Fusca azul-bebê freando, com fumaça no escapamento | 3 restantes |
| `vida_urbana/26_crianca_recolhendo_linha.png` | Menino recolhendo a linha da pipa com carretilha | 6 restantes |
| `vida_urbana/27_velha_reclamando.png` | Vovó sentada reclamando e apontando o dedo | 6 restantes |
| `vida_urbana/28_vizinha_surpresa.png` | Vizinha na janela, surpresa, cobrindo a boca | 5 restantes |
| `vida_urbana/29_ze_cafe_caminhando.png` | Zé do Café caminhando com bandeja e duas canecas | 6 restantes |
| `vida_urbana/30_ciclista_pedal_alto.png` | Ciclista em pose intermediária, joelho alto no pedal | 2 restantes |

### Lote 4 —  9/10 ENTREGUE (39/342) — fechamento dos ciclos de movimento

| Arquivo | Descrição |
|---|---|
| `vida_urbana/31_carroceiro_puxando_redeas.png` | Carroceiro em pé puxando as rédeas, cavalo em meio-trote (ciclo de passo) |
| `vida_urbana/32_zikas_andando.png` | Dupla de Zikas caminhando lado a lado em passada larga |
| `vida_urbana/33_cachorro_andando.png` | Vira-lata cinza em passo de caminhada, pata dianteira estendida |
| `vida_urbana/34_gato_andando.png` | Gato preto em passo de ronda, pata dianteira erguida, cauda alta |
| `vida_urbana/35_carro_velho_estacionado.png` | Fusca azul-bebê parado, janelas vazadas transparentes com vidro trincado |
| `vida_urbana/36_crianca_correndo.png` | Menino correndo puxando a linha, pipa e rabiola no alto |
| `vida_urbana/37_velha_levantando.png` | Vovó no meio do movimento de levantar da cadeira de plástico |
| `vida_urbana/38_vizinha_fechando_janela.png` | Entregue no Lote 5 (ver abaixo) — geração havia estourado o limite de 10 imagens do turno |
| `vida_urbana/39_ze_cafe_limpando_balcao.png` | Zé do Café limpando o balcão com pano e bule na outra mão |
| `vida_urbana/40_ciclista_pedal_baixo.png` | Ciclista com pedalada completa (perna estendida embaixo), roda com raios vazados |

Todos os arquivos do lote foram pós-processados e validados como PNG RGBA com
fundo transparente real (canal alpha), sem cenário incorporado.

### Lote 5 — ✅ CONCLUÍDO (49/342) — fechamento do Lote 4 + reações e ciclos

| Arquivo | Descrição |
|---|---|
| `vida_urbana/38_vizinha_fechando_janela.png` | Vizinha espremendo o rosto entre as folhas da janela enquanto empurra para fechar (completa o Lote 4) |
| `vida_urbana/41_carroceiro_a_pe.png` | Carroceiro a pé ao lado da carroça, puxando o cavalo pelas rédeas em passo lento |
| `vida_urbana/42_zikas_rindo_apontando.png` | Dupla de Zikas rindo alto, um apontando para a rua e o outro batendo na barriga |
| `vida_urbana/43_cachorro_latindo.png` | Vira-lata cinza sentado latindo, boca escancarada, orelhas para trás |
| `vida_urbana/44_gato_agachado_pulo.png` | Gato preto espreitando, corpo agachado com pata dianteira erguida antes do bote |
| `vida_urbana/45_carro_velho_frente.png` | Fusca azul-bebê com farol aceso e janelas vazadas transparentes (vista lateral com luz) |
| `vida_urbana/46_crianca_pipa_caida.png` | Menino ajoelhado segurando a pipa caída e murcha, beicinho de choro |
| `vida_urbana/47_velha_abanando.png` | Vovó sentada na cadeira de plástico abanando-se com jornal dobrado |
| `vida_urbana/48_ze_cafe_bule_alto.png` | Zé do Café servindo café de longe: bule erguido no alto e xícara baixa na outra mão |
| `vida_urbana/49_ciclista_parado.png` | Ciclista parado com o pé no chão, olhando por cima do ombro (fecha o ciclo do ciclista, 5/5) |

Pós-processamento do lote: recorte croma padrão + limpeza de resíduos de croma
por matiz em `45` (luz de farol pintada de verde e reflexo do fundo nos vidros)
e `47` (franja verde na fresta entre cabeça e jornal); verdes legítimos de arte
(olhos do gato em `44`, fitas da rabiola em `46`) preservados. Todos validados
como PNG RGBA com alpha real.

**Próximo lote (6):** 50–59 — ciclos restantes: carroceiro (50), zikas (51–52),
cachorros (53–54), gato (55), carro (56, fecha o elemento em 6/6), criança (57),
velha (58) e vizinha (59), mantendo 10 gerações por turno.

### Progresso

- [x] Lote 1 — 10 imagens (heroes dos 10 elementos)
- [x] Lote 2 — 10 imagens (variações de pose da cena c00)
- [x] Lote 3 — 10 imagens (poses intermediárias e segundo cão)
- [x] Lote 4 — 10 imagens (38 entregue junto com o Lote 5)
- [x] Lote 5 — 10 imagens (reações, ciclos e fechamento do ciclista 5/5) — 49/342
- [ ] Lote 6..9 — Vida Urbana completa (35 restantes)
- [ ] Demais categorias (258)
