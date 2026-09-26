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

### Lote 11 — ✅ CONCLUÍDO (101/342) — `05` Cida (slot reservado) + 3 assets novos (15–17)

| Arquivo | Descrição |
|---|---|
| `personagens/05_cida_em_pe.png` | **Cida** herói (slot reservado no Lote 10): em pé 3/4, cabelo de bobes com rede, avental floral sobre blusa estampada, uma mão em concha na boca gritando e a outra na cintura (ref.: `personagens/05_cida.jpg` + `imagens/005.jpg`) |
| `personagens/15_seu_jorge_cadeira.png` | **Seu Jorge** sentado na cadeira de plástico — pose de cena (007/017), chapéu bucket, regata manchada, garfo de plástico erguido e prato de papel; distinto do herói em pé `06` (ref.: `06_seu_jorge.jpg` + `imagens/007.jpg`) |
| `personagens/16_fabinho_lanterna.png` | **Fabinho** com a lanterna no túnel — pose de cena (059/060), boné virado pra trás, camiseta com estampa de cachorro, olhos grandes esperançosos (ref.: `07_fabinho.jpg` + `imagens/059.jpg`) |
| `personagens/17_zeca_celular_notificacoes.png` | **Zeca** com o celular explodindo em notificações verdes do WhatsApp — cena 027; complementa o `14` (tela neutra) com a tempestade de bolhas em camada única, 6 dedos visíveis (ref.: `03_zeca.jpg` + `imagens/027.jpg`) |

Pós-processamento do lote: as 10 imagens foram geradas **antes** do merge do
Lote 10 (PR #12), então o plano do turno colidiu com os slots `06`–`14` que já
estavam aprovados. Critério adotado: comparação automática de silhueta
(IoU após normalização de escala) + posição relativa das patas de apoio contra
os assets já aprovados.

- **1 geração virou o slot reservado**: `05` Cida (fecha o Lote 10 em 98/342).
- **3 gerações viraram assets novos** (`15`–`17`): IoU 0,43–0,52 e área/tipo de
  pose distintos (sentado × em pé; com lanterna; tela com notificações × tela
  neutra) — todos dentro do sub-plano de poses de cada personagem.
- **6 gerações foram descartadas como takes duplicados** dos slots aprovados:
  `08` repórter (IoU 0,77), `10` Caramelo dormindo (IoU 0,71, área idêntica),
  `12` cabeça neutra (IoU 0,85), `13` Pardal calculadora (IoU 0,52, mesma
  intenção de cena), `11` Caramelo no pote (o pote vinha embutido no asset,
  contra a regra "1 arquivo = 1 asset") e `09` Caramelo andando (IoU 0,45 mas
  **mesma fase de passo**: 4 patas em posições relativas 0,20/0,41/0,60/0,74
  contra 0,22/0,43/0,65/0,84 do `09` aprovado — não serve como passo oposto do
  ciclo). Arquivos preservados em `raw/lote11_duplicados/` (fora do Git) para
  eventual reuso.
- Recorte refeito com a ferramenta já corrigida (`KEY_GUARD`) sobre os RAW do
  croma — nenhum buraco indevido; franja de croma zero em 3/4; no `17` o
  verde restante (0,08%) é arte legítima: tela e bolhas do WhatsApp.
- 4/4 validados como PNG RGBA com alpha real 0–255. **10 gerações no turno**
  (limite respeitado; sem re-tentativa).

### Lote 12 — ✅ CONCLUÍDO (111/342) — primeiro set de visemas do Caramelo + 5 poses de cena

| Arquivo | Descrição | Croma |
|---|---|---|
| `personagens/18_caramelo_cabeca_olhos_fechados.png` | Caramelo cabeça 3/4 — **olhos fechados** (piscar), boca neutra igual à base `12` | azul |
| `personagens/19_caramelo_cabeca_boca_a.png` | Caramelo cabeça — **boca "A"**: mandíbula caída, língua e caninos à mostra | azul |
| `personagens/20_caramelo_cabeca_boca_o.png` | Caramelo cabeça — **boca "O"**: focinho projetado, abertura redonda pequena | azul |
| `personagens/21_caramelo_cabeca_boca_ei.png` | Caramelo cabeça — **boca "E/I"**: focinho esticado na horizontal, dentes em careta | azul |
| `personagens/22_caramelo_farejando.png` | Caramelo em pé com o focinho erguido farejando o ar, orelhas atentas (cena 016) | azul |
| `personagens/23_pardal_macacao_mop.png` | Pardal de **macacão azul** e botas, passando mop no bueiro, ar derrotado (cena 040/070) | verde |
| `personagens/24_zeca_carimbando_iptu.png` | Zeca esmagando o **carimbo** na folha do IPTU, sorriso safado, 6 dedos (cena 025) | verde |
| `personagens/25_marta_pregando.png` | Marta pregando de **braços abertos**, celular numa mão e bíblia na outra (cena 006) | verde |
| `personagens/26_fabinho_ajoelhado.png` | Fabinho **ajoelhado**, lanterna baixa, olhar preocupado (cena 062) | verde |
| `personagens/27_cida_apontando.png` | Cida **apontando o dedo** indignada, pacote de linguiça na outra mão (cena 074) | verde |

#### Rig de lip sync — convenção de registro

As cabeças de visema precisam ser **trocáveis** sobre a cabeça neutra `12`.
Cada geração devolveu uma escala diferente, então todas foram normalizadas pela
**altura do bounding box do sujeito** (= 701 px, medida na base `12`):

| Cabeça | Tamanho final | bbox do sujeito | IoU vs. base `12` |
|---|---|---|---|
| `12` neutra (base) | 753×717 | 737×701 | — |
| `19` boca A | 739×707 | 727×701 | 0,90 |
| `20` boca O | 732×708 | 716×700 | 0,88 |
| `18` olhos fechados | 629×709 | 613×701 | 0,73 |
| `21` boca E/I | 680×701 | 680×701 | 0,69 |

- `19` e `20` encaixam direto (IoU ≥ 0,88).
- `18` veio com recorte mais fechado (menos ombro) e `21` com a careta mais
  larga — alinhar pelo **centro do bbox + escala pela largura** no rig.
- IoU baixa em `21` é esperada: a careta "E/I" muda a silhueta do focinho.

#### Ferramentas

- `assets/tools/chroma_key.py`: **despill agora é ciente da cor do fundo** — com
  `--key blue` remove o vazamento de azul na franja (antes só tratava verde), o
  que viabiliza gerar o Caramelo em croma azul sem halo.
- `assets/tools/registra_cabecas.py` (**novo**): recorta o maior componente
  (folha de modelo), registra a escala pela cabeça-base e faz o resize em
  **alpha premultiplicado** — sem isso o RGB do fundo croma vaza para a borda e
  cria halo azul/esverdeado.

#### Pós-processamento e validação

- `21` saiu como **folha de modelo** (cabeça + elemento extra no canto): só a
  cabeça pedida foi mantida (maior componente + dilatação de 2 px), resto
  descartado.
- `26`: franja verde presa na borda — 4 rodadas de limpeza por matiz (1.738 px)
  + despill forte nos 123 px restantes; verde de arte preservado (0,10%).
- `24`: 1 buraco fechado de 7.205 px entre braço e tronco — vão legítimo.
- 10/10 validados como PNG RGBA com alpha real 0–255; franja de croma zero em
  todos (os pixels quase transparentes das cabeças têm alpha ≈ 0,04, invisíveis
  na composição). **10 gerações no turno.**

**Próximo lote (13):** fecha o set de cabeças do Caramelo — boca "U" (28), boca
"F/V" (29), olhos arregalados (30), olhos semicerrados (31) e cabeça de êxtase
(32), todos em croma azul — e abre as **cabeças-base dos demais** para bocas:
Pardal (33), Zeca (34), Marta (35), Cida (36) e Seu Jorge (37) — 10 gerações.

### Lote 13 — ✅ CONCLUÍDO (120/342) — visemas restantes do Caramelo + cabeças-base

Fecha o set de cabeças do Caramelo (croma **azul**, registradas na escala da
base `12`) e abre as **cabeças-base** de Pardal, Zeca, Cida e Seu Jorge
(croma verde). O slot `35` de Marta falhou sem imagem na geração original e
foi concluído no Lote 14, sem deslocar os demais assets do lote.

| Arquivo | Descrição |
|---|---|
| `personagens/28_caramelo_cabeca_boca_u.png` | Visema **"U"** — focinho franzido, abertura redonda pequena; mesmos olhos semicerrados da base `12` (croma azul; IoU vs `12` = 0,95) |
| `personagens/29_caramelo_cabeca_boca_fv.png` | Visema **"F/V"** — lábio superior sobre os dentes da frente, boca quase fechada (croma azul; IoU vs `12` = 0,99) |
| `personagens/30_caramelo_cabeca_olhos_abertos.png` | Olhos **arregalados** (frame "aberto" do piscar) — boca fechada da base, pálpebras erguidas (croma azul; IoU vs `12` = 0,99) |
| `personagens/31_caramelo_cabeca_olhos_semicerrados.png` | Olhos **semicerrados** (frame "meio" do piscar) — fenda de creme, boca fechada da base (croma azul; IoU vs `12` = 0,99) |
| `personagens/32_caramelo_cabeca_extase.png` | Cabeça de **êxtase** — olhos fechados em prazer, sorriso contente, dente à mostra; orelhas mais abertas (croma azul; IoU vs `12` = 0,81, silhueta distinta pela pose) |
| `personagens/33_pardal_cabeca_neutra.png` | **Pardal** cabeça-base 3/4: calvo suado, boca fechada nervosa, botton 29, gravata verde/laranja — base para troca de visemas (ref.: `02_pardal.jpg` + herói `02`) |
| `personagens/34_zeca_cabeca_neutra.png` | **Zeca** cabeça-base 3/4: sorriso malandro fechado, terno cinza, gravata vermelha — base para troca de visemas (ref.: `03_zeca.jpg` + herói `03`) |
| `personagens/35_marta_cabeca_neutra.png` | Finalizado no Lote 14: cabeça-base 3/4, boca fechada, olhos abertos — ver tabela abaixo |
| `personagens/36_cida_cabeca_neutra.png` | **Cida** cabeça-base 3/4: bobes coloridos, lenço floral, óculos, boca fechada em sorriso — base para troca de visemas (ref.: `05_cida.jpg` + herói `05`) |
| `personagens/37_seu_jorge_cabeca_neutra.png` | **Seu Jorge** cabeça-base 3/4: chapéu bucket oliva, barba grisalha, regata, boca fechada cansada — base para troca de visemas (ref.: `06_seu_jorge.jpg` + herói `06`) |

Pós-processamento do lote:

- Caramelo 28–32 gerados sobre croma **azul** (`--key blue`) e **registrados**
  na altura de bbox da base `12` (700 px) com `registra_cabecas.py` (resize em
  alpha premultiplicado, sem halo).
- Pardal/Zeca/Cida/Jorge gerados sobre croma verde; recorte padrão + limpeza
  de franja por matiz (só a borda de 5 px) + punch de pixels ainda colados na
  cor do fundo (`dist < 0.22`). No `34` isso removeu 29 px de croma preso no
  tufo entre as orelhas; verde/oliva de arte (gravata do Pardal, chapéu do
  Jorge, lenço da Cida) preservado.
- `despill` do `chroma_key.py` agora é ciente da cor do fundo (croma azul
  remove excesso de azul na franja).
- 9/9 validados como PNG RGBA com alpha real 0–255. **10 gerações no turno**
  (1 falhou sem imagem; sem re-tentativa).

### Lote 14 — ✅ CONCLUÍDO (130/342) — Marta + rig de visemas de Pardal/Zeca + novas cabeças

| Arquivo | Descrição | Croma |
|---|---|---|
| `personagens/35_marta_cabeca_neutra.png` | **Marta** cabeça-base 3/4: boca fechada, olhos abertos, cachos pretos com mechas douradas, argolas e cruz; base para visemas | verde |
| `personagens/38_pardal_cabeca_boca_a.png` | **Pardal** visema **"A"** — mandíbula caída, língua e dentes; mesma cabeça-base `33` | verde |
| `personagens/39_pardal_cabeca_boca_o.png` | **Pardal** visema **"O"** — lábios arredondados; mesma cabeça-base `33` | verde |
| `personagens/40_pardal_cabeca_olhos_fechados.png` | **Pardal** olhos fechados — frame de piscar, boca fechada | verde |
| `personagens/41_zeca_cabeca_boca_a.png` | **Zeca** visema **"A"** — boca vertical aberta, língua e dentes; mesma cabeça-base `34` | verde |
| `personagens/42_zeca_cabeca_boca_o.png` | **Zeca** visema **"O"** — focinho projetado e abertura redonda; mesma cabeça-base `34` | verde |
| `personagens/43_zeca_cabeca_olhos_fechados.png` | **Zeca** olhos fechados — frame de piscar, boca fechada | verde |
| `personagens/44_reporter_cabeca_neutra.png` | **Repórter** cabeça-base 3/4: expressão neutra de estúdio, cabelo loiro e ombro do blazer; microfone fica em camada própria | verde |
| `personagens/45_fabinho_cabeca_neutra.png` | **Fabinho** cabeça-base 3/4: boné teal virado, olhos abertos e expressão esperançosa; lanterna fica em camada própria | verde |
| `personagens/46_caramelo_pata_erguida.png` | **Caramelo**: uma única pata dianteira erguida, almofadas visíveis, para gesto/aceno em camada independente | azul |

Pós-processamento e validação:

- Foram feitas **exatamente 10 gerações** neste turno; uma por arquivo da tabela.
- Os nove assets de personagem foram gerados em croma verde; a pata do Caramelo
  usou croma azul para não conflitar com a faixa verde do personagem. Todos
  passaram por `chroma_key.py` e são PNG **RGBA** com alpha real de 0 a 255.
- Os visemas de Pardal foram registrados em alpha premultiplicado na altura de
  bbox da cabeça `33` (**740 px**); os de Zeca, na altura da base `34`
  (**718 px**). Assim, cada trio encaixa no rig sem redimensionamento manual.
- Revisão visual em fundo escuro: silhuetas limpas, sem cenário ou fundo
  incorporado; a Repórter não leva microfone e Fabinho não leva lanterna, pois
  ambos são props/camadas independentes.

**Próximo lote (15):** concluir visemas e piscadas de Marta, Cida e Seu Jorge,
seguindo as folhas de modelo e stills das 79 cenas; depois retomar poses de
corpo dos protagonistas. Serão novamente no máximo 10 assets isolados.

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
- [x] Lote 11 — 4 novos de 10 gerações (05 Cida fecha o slot reservado do Lote 10; 15 Seu Jorge na cadeira, 16 Fabinho com lanterna, 17 Zeca notificações; 6 takes duplicados de 06–14 descartados) — 101/342
- [x] Lote 12 — 10 imagens (visemas 18–21 + Caramelo farejando 22 em croma azul; poses 23–27 de Pardal/Zeca/Marta/Fabinho/Cida) — 111/342
- [x] Lote 13 — 9 imagens (visemas 28–32 e cabeças-base 33–34, 36–37); o slot `35_marta_cabeca_neutra` foi concluído no Lote 14 — 120/342
- [x] Lote 14 — 10 imagens (`35`, 38–46): Marta, rig de visemas/piscadas de Pardal e Zeca, cabeças-base de Repórter/Fabinho e pata do Caramelo — **130/342**
- [ ] Lote 15 — visemas/piscadas de Marta, Cida e Seu Jorge; continuidade das poses principais
- [ ] Personagens principais restantes e demais categorias
