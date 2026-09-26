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
- Fidelidade dos personagens principais: cada geração recebe como referência a
  folha de modelo (`personagens/0N_*.jpg`, raiz do repo) **e** um still das 79
  imagens em que o personagem aparece — nada é redesenhado de memória.
- Regra "1 arquivo = 1 asset": se o gerador devolver uma folha com várias poses
  ou cabeças na mesma imagem, só a pose pedida entra no repo (recorte por
  colunas vazias do alpha); o resto fica em `raw/` (ignorado pelo Git) e não
  conta no total.

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

**Vida Urbana concluída no Lote 9: 84/84** (01–84, todos com fundo transparente).

## Personagens principais (135 assets — 8 personagens) — pasta `assets/personagens/`

Sub-plano por personagem. "Poses" = corpo inteiro para puppet/interpolação;
"cabeças" = expressões recortadas para troca de rosto; "bocas" = visemas
isolados (fechada, A, E/I, O, U, F/V…) para lip sync; "olhos" = aberto /
meio / fechado para o ciclo de piscar. Cada item é **um arquivo PNG RGBA**.

| Personagem | Poses | Cabeças | Bocas | Olhos | Extras | Total |
|---|---|---|---|---|---|---|
| Caramelo | 12 | 8 | 8 | 4 | 2 (patas, cauda) | 34 |
| Xerxes Pardal | 10 | 6 | 6 | 2 | — | 24 |
| Zeca | 8 | 4 | 6 | 2 | — | 20 |
| Marta | 5 | 3 | 4 | 2 | — | 14 |
| Cida | 4 | 2 | 3 | 1 | — | 10 |
| Seu Jorge | 4 | 2 | 3 | 1 | — | 10 |
| Fabinho | 5 | 3 | 4 | 1 | — | 13 |
| Repórter | 4 | 2 | 3 | 1 | — | 10 |
| **Total** | | | | | | **135** |

Ordem de produção: 1 herói (pose neutra de corpo inteiro) por personagem →
poses das cenas em que cada um fala → cabeças/bocas/olhos.

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

### Lote 6 — ✅ CONCLUÍDO (59/342) — ações secundárias e fechamento do carro (6/6)

| Arquivo | Descrição |
|---|---|
| `vida_urbana/50_carroceiro_descarregando.png` | Carroceiro na traseira da carroça erguendo um caixote da pilha, cavalo atrelado parado |
| `vida_urbana/51_zikas_correndo.png` | Dupla de Zikas fugindo em pânico em disparada, olhando por cima do ombro |
| `vida_urbana/52_zikas_cumprimento.png` | Dupla de Zikas de frente fazendo cumprimento de rua elaborado, mãos clasadas no alto |
| `vida_urbana/53_cachorro_correndo.png` | Vira-lata cinza em galope pleno, corpo esticado no ar, orelhas ao vento |
| `vida_urbana/54_cachorro_farejando.png` | Vira-lata cinza farejando o chão, traseira erguida e cauda em pé |
| `vida_urbana/55_gato_lambendo_pata.png` | Gato preto sentado lambendo a pata erguida, olhos semicerrados |
| `vida_urbana/56_carro_velho_fumaceando.png` | Fusca azul-bebê em vista lateral fumaceando pelo escapamento, janelas vazadas (fecha o elemento em 6/6) |
| `vida_urbana/57_crianca_pipa_vitoria.png` | Menino erguendo a pipa como troféu acima da cabeça, rabiola serpenteando |
| `vida_urbana/58_velha_cochilando.png` | Vovó cochilando desabada na cadeira de plástico, óculos tortos no nariz |
| `vida_urbana/59_vizinha_gritando_rua.png` | Vizinha debruçada na janela gritando para a rua com as mãos em concha |

Pós-processamento: recorte croma padrão + limpeza por matiz de franjas de croma
presas em frestas em `50` (vão entre vara e carroça), `53` (borda da língua) e
`58` (lente do óculos vazada); verdes de arte preservados (olhos do gato em
`55`, fitas da rabiola em `57`). 10/10 validados como PNG RGBA com alpha real.

### Lote 7 — ✅ CONCLUÍDO (69/342) — 60–69: brindes, reações e cochilos

| Arquivo | Descrição |
|---|---|
| `vida_urbana/60_ze_cafe_brindando.png` | Zé do Café erguendo a caneca num brinde, bule na outra mão, sorrisão |
| `vida_urbana/61_carroceiro_acenando_chapeu.png` | Carroceiro a pé ao lado da carroça erguendo o chapéu de palha em saudação; cavalo atrelado parado |
| `vida_urbana/62_zikas_sentados_celular.png` | Dupla de Zikas sentada no meio-fio, um mostrando a tela do celular para o outro |
| `vida_urbana/63_cachorro_cocando_orelha.png` | Vira-lata coçando a orelha com a pata traseira, cabeça inclinada, língua de fora |
| `vida_urbana/64_gato_espreguicando.png` | Gato preto em espreguiçada profunda de gato, bocejando com a língua de fora |
| `vida_urbana/65_crianca_apontando_ceu.png` | Menino com a pipa na mão apontando o céu, boca aberta gritando de alegria |
| `vida_urbana/66_velha_tapando_ouvidos.png` | Vovó sentada na cadeira tampando os dois ouvidos, olhos apertados, cara de aborrecimento |
| `vida_urbana/67_vizinha_falando_celular.png` | Vizinha na janela falando no celular com cara de fofoqueira, outra mão gesticulando |
| `vida_urbana/68_ze_cafe_cansado.png` | Zé do Café sentado no caixote, exausto, enxugando o suor com a toalha, bule no chão |
| `vida_urbana/69_carroceiro_cochilando.png` | Carroceiro cochilando sentado no bordo da carroça, chapéu sobre o rosto, cavalo parado |

Pós-processamento do lote: recorte croma padrão + remoção do letreiro pintado
"VELHARIAS & JUNK" no painel lateral da carroça do `61` (texto fora do padrão —
o caibro do `50` é plano; reconstrução do grão de madeira por interpolação
horizontal). Observação: o `63` saiu com o corpo levemente mais robusto que as
poses `03/43/53/54` do mesmo cão — mesmo personagem (pelagem, olhos amarelos),
variância aceitável de estilização; se atrapalhar a interpolação, re-gerar em
lote futuro. 10/10 validados como PNG RGBA com alpha real.

### Lote 8 — 9/10 ENTREGUE (78/342) — reações finais e fechamento de 4 elementos

| Arquivo | Descrição |
|---|---|
| `vida_urbana/70_zikas_discutindo.png` | Dupla de Zikas discutindo face a face: um apontando pro peito do outro, o outro jogando os braços pro alto indignado |
| `vida_urbana/71_cachorro_sentado.png` | Vira-lata sentado e atento, orelhas em pé, cauda enrolada nas patas |
| `vida_urbana/72_crianca_pulando.png` | Menino pulando no ar com os dois punhos erguidos, pipa balançando na mão |
| `vida_urbana/73_velha_orando.png` | Vovó de mãos postas em oração, olhos fechados, rezando baixinho |
| `vida_urbana/74_vizinha_rindo.png` | Vizinha gargalhando com a cabeça jogada pra trás, mão na barriga |
| `vida_urbana/75_zikas_se_escondendo.png` | Dupla de Zikas agachada se escondendo atrás de um muro invisível, mãos na cabeça, cara de medo |
| `vida_urbana/76_cachorro_rolando.png` | Vira-lata rolando de barriga pra cima, patas no ar, língua de fora (fecha cachorros 10/10) |
| `vida_urbana/77_crianca_procurando_pipa.png` | Entregue no Lote 9 (ver abaixo) — a pose original (criança enroscada na linha) foi bloqueada pela moderação; substituída por pose segura |
| `vida_urbana/78_velha_conversando.png` | Vovó sentada conversando animada, gesticulando com as duas mãos (fecha velha 9/9) |
| `vida_urbana/79_vizinha_acenando.png` | Vizinha acenando da janela com sorriso, cotovelo no peitoril (fecha vizinha 8/8) |

Pós-processamento: recorte croma padrão; verde do vestido floral do `78` conferido por HSV — são folhas pintadas (0,1% pixels croma-like), não resíduo. 9/9 entregues validados como PNG RGBA com alpha real. 10 gerações por turno respeitadas (1 bloqueada, sem re-tentativa).

### Lote 9 — ✅ CONCLUÍDO (88/342) — fecha Vida Urbana (84/84) + heróis dos 4 protagonistas

| Arquivo | Descrição |
|---|---|
| `vida_urbana/77_crianca_procurando_pipa.png` | Menino parado com a mão em pala sobre os olhos procurando a pipa no céu, carretel na outra mão (fecha criança 9/9; substitui a pose bloqueada) |
| `vida_urbana/80_zikas_dancando.png` | Dupla de Zikas dançando passinho lado a lado, joelhos dobrados e braço no alto (fecha zikas 11/11) |
| `vida_urbana/81_carroceiro_dando_agua_cavalo.png` | Carroceiro a pé dando água ao cavalo num balde amassado e fazendo carinho no pescoço — sem carroça (fecha carroceiro 9/9) |
| `vida_urbana/82_gato_dormindo_enrolado.png` | Gato preto dormindo enrolado em bola, rabo sobre o focinho (fecha gato 8/8) |
| `vida_urbana/83_ze_cafe_chamando_fregues.png` | Zé do Café chamando freguês: mão em concha na boca, bule erguido no alto |
| `vida_urbana/84_ze_cafe_contando_moedas.png` | Zé do Café contando moedas na palma com o indicador, olhar desconfiado, bule pendurado no pulso (fecha zé 9/9) |
| `personagens/01_caramelo_sentado.png` | **Caramelo** herói: sentado 3/4 de frente, faixa verde/ouro com medalhão, coleira cinza, peito branco, olhos semicerrados de tédio digno (ref.: `personagens/01_caramelo.jpg` + `imagens/077.jpg`) |
| `personagens/02_pardal_em_pe.png` | **Xerxes Pardal** herói: em pé 3/4, terno marrom-oliva amarrotado, gravata curta listrada, botton 29, sorriso nervoso de político, mão erguida em aceno tímido, gotas de suor (ref.: `02_pardal.jpg` + `imagens/026.jpg`) |
| `personagens/03_zeca_em_pe.png` | **Zeca** herói: em pé 3/4, terno cinza largo, gravata vermelha, prancheta numa pata e a outra aberta em gesto de "confia" (ref.: `03_zeca.jpg` + `imagens/018.jpg`) |
| `personagens/04_marta_em_pe.png` | **Marta** herói: em pé 3/4, mão na cintura, celular erguido lendo mensagem com boca escandalizada, argolas, cruz, vestido teal estampado (ref.: `04_marta.jpg` + `imagens/006.jpg`) |

Pós-processamento do lote: recorte croma padrão; `80` e `04_marta` vieram
como folha de modelo (segundo par de zikas / vista lateral + 6 cabeças de
expressão da Marta) — só a pose pedida foi mantida (recorte pelas colunas
vazias do alpha), o restante ficou em `raw/`; limpeza por matiz de franja de
croma presa nas rédeas e no balde do `81` e na alça do bule do `83`; verdes
legítimos de arte preservados (faixa do Caramelo, gravata do Pardal, vestido da
Marta). 10/10 validados como PNG RGBA com alpha real 0–255. 10 gerações no
turno.

### Lote 10 — 9/10 ENTREGUE (97/342) — heróis restantes + poses de cena do Caramelo, Pardal e Zeca

| Arquivo | Descrição |
|---|---|
| `personagens/05_cida_em_pe.png` | **RESERVADO** — o gerador devolveu resposta sem imagem (falha do modelo, não moderação); sem re-tentativa no turno (limite de 10 gerações). Entra no Lote 11 |
| `personagens/06_seu_jorge_em_pe.png` | **Seu Jorge** herói: em pé 3/4, chapéu bucket oliva, regata manchada, jeans, sandália, prato de isopor com carne e garfo (ref.: `06_seu_jorge.jpg` + `imagens/007.jpg`) |
| `personagens/07_fabinho_em_pe.png` | **Fabinho** herói: em pé 3/4, boné teal pra trás, camiseta com carinha de cachorro, bermuda, all-star vermelho, sorriso esperançoso (ref.: `07_fabinho.jpg` + `imagens/078.jpg`) |
| `personagens/08_reporter_em_pe.png` | **Repórter** herói: em pé 3/4, blazer azul-marinho, saia lápis, microfone com cubo TV MIGALHA, mão apresentando algo fora de quadro (ref.: `08_reporter.jpg`) |
| `personagens/09_caramelo_andando.png` | Caramelo andando de perfil (esquerda), meio passo, cauda baixa, faixa e medalhão de lado — ciclo de caminhada (ref.: folha + herói 01) |
| `personagens/10_caramelo_dormindo.png` | Caramelo dormindo enrolado em bola, faixa visível no dorso — cenas 003 / créditos (ref.: folha + herói 01) |
| `personagens/11_caramelo_apoiado.png` | Caramelo em pé nas patas traseiras, patas dianteiras apoiadas numa borda invisível — para compor dentro do pote (003/004/077) com o pote em camada própria (ref.: folha + `imagens/077.jpg`) |
| `personagens/12_caramelo_cabeca_neutra.png` | Cabeça do Caramelo 3/4, boca fechada, olhos semicerrados, até a coleira — **base para troca de bocas e olhos** (ref.: folha + `imagens/043.jpg`) |
| `personagens/13_pardal_suando_calculadora.png` | Pardal em pânico com a calculadora, mão na cabeça, gotas de suor voando, botton 29 — cena 028 (ref.: folha + `imagens/028.jpg`) |
| `personagens/14_zeca_celular.png` | Zeca segurando o celular com as duas patas, olhos arregalados, careta nervosa; tela neutra sem brilho verde (o verde do WhatsApp entra na composição) — cena 027 (ref.: folha + `imagens/027.jpg`) |

Pós-processamento do lote:

- **Correção na ferramenta** (`chroma_key.py`, guarda `KEY_GUARD = 0.32`): o
  vazamento de "verde preso em buracos fechados" estava apagando **verde de
  arte** quando ele formava uma região fechada — a faixa lima do Caramelo
  (`09`, `11`), a parte sombreada/oliva da faixa e até verde-escuro de
  contorno (`14`). Agora só vaza pixel cuja cor está perto da cor do fundo;
  raios de roda e janelas continuam vazando normalmente.
- **`01_caramelo_sentado` (Lote 9) corrigido**: a mesma falha tinha aberto um
  buraco na faixa abaixo do medalhão (passou despercebido na revisão do
  contato). Preenchido com o lima padrão da faixa; nenhum outro asset da pasta
  tem buraco fora de vãos legítimos (braço/quadril, braço/celular).
- `10`: o gerador pintou a faixa metade creme e metade verde-croma; recolorida
  inteira para o lima da folha (dois tons = luz/sombra), medalhão preservado.
- `06` veio como folha de modelo (3 poses + 4 cabeças); só a pose pedida foi
  mantida. Franja de croma limpa por matiz em todos.
- **Recomendação para os próximos Caramelos**: gerar sobre croma **azul**
  (`--key blue`) para eliminar de vez o conflito com a faixa verde.
- 9/9 validados como PNG RGBA com alpha real 0–255. 10 gerações no turno
  (1 falhou sem imagem).

**Próximo lote (11):** `05` Cida herói (re-geração) + Caramelo cabeça olhos
fechados (piscar) (15), Caramelo cabeça boca aberta "A" (16), boca "O" (17),
boca "E/I" (18), Caramelo farejando a fila (19, cena 016), Pardal de macacão
azul com mop no bueiro (20), Zeca carimbando o IPTU (21), Marta pregando de
braços abertos (22), Fabinho ajoelhado com a mão no alambrado (23) — 10
gerações, Caramelos em croma azul.

### Progresso

- [x] Lote 1 — 10 imagens (heroes dos 10 elementos)
- [x] Lote 2 — 10 imagens (variações de pose da cena c00)
- [x] Lote 3 — 10 imagens (poses intermediárias e segundo cão)
- [x] Lote 4 — 10 imagens (38 entregue junto com o Lote 5)
- [x] Lote 5 — 10 imagens (reações, ciclos e fechamento do ciclista 5/5) — 49/342
- [x] Lote 6 — 10 imagens (ações secundárias; carro fechado em 6/6) — 59/342
- [x] Lote 7 — 10 imagens (60–69: brindes, reações e cochilos; letreiro do 61 removido) — 69/342
- [x] Lote 8 — 9 imagens (70–76, 78–79; 77 reservado por bloqueio de moderação) — 78/342
- [x] Lote 9 — 10 imagens (77, 80–84 fecham Vida Urbana 84/84; personagens 01–04: heróis Caramelo, Pardal, Zeca, Marta) — 88/342
- [x] Lote 10 — 9 imagens (personagens 06–14; 05 Cida reservado por falha do gerador; correção do 01 e da ferramenta) — 97/342
- [ ] Lote 11 — 05 Cida + cabeças/bocas do Caramelo + poses de cena (Pardal, Zeca, Marta, Fabinho) — 107/342
- [ ] Personagens principais restantes (122) e demais categorias (123)
