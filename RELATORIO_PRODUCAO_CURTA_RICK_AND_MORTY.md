# RELATÓRIO TÉCNICO E BÍBLIA DE PRODUÇÃO: MIGALHÓPOLIS T01E01
## PRODUÇÃO DO CURTA-METRAGEM ANIMADO EM ESTILO 2D (RICK AND MORTY / LIMITED CARTOON)

**Data de emissão:** 2026-09-23  
**Repositório:** `berger33/migalhopolis`  
**Branch de Produção:** `arena/01a0d098-migalhopolis`  
**Episódio:** Temporada 01, Episódio 01 — *"O Pote"*  
**Duração Alvo:** Curta-metragem completo (~9 minutos, dividido em 10 partes interligadas)  
**Formato de Entrega:** Vídeo 1080p (1920x1080), 30 fps, H.264 High Profile, Áudio AAC 48kHz Stereo, Mixagem Broadcast (-1dBFS Diálogos, -14dBFS SFX, -18dBFS Trilha Musical).

---

## 1. RESUMO EXECUTIVO E DIAGNÓSTICO DOS ERROS ANTERIORES

### 1.1 O Erro de Interpretação Crítico
Nas tentativas anteriores de renderização da Parte 1, ocorreu uma falha conceitual grave: o processo foi tratado como um **"Motion Comic" (slideshow com câmera Ken Burns e adesivo de boca)**, e **NÃO** como um **desenho animado de verdade**.

### 1.2 Os Problemas Detectados e Suas Causas Raízes:
1. **Adesivo de Boca Flutuante ao Lado do Personagem:**
   - *Causa:* Foram utilizadas coordenadas estimadas sem medição pixel-a-pixel nos recortes, sobrepondo uma elipse genérica pré-desenhada com dentes e língua que não deformava a mandíbula do personagem.
   - *Erro Fatal de Direção:* O script ativou animação de boca em personagens na tela durante falas do **NARRADOR**. O narrador é uma voz em *off* (estilo documentário morto-vivo). Quando o narrador fala, os personagens na cena **JAMAIS** devem mexer a boca como ventríloquos. Devem realizar **atuação silenciosa** (olhares, piscadas, reações, respiração).
2. **Cenários e Personagens Mortos (Sem Vida):**
   - *Causa:* A imagem original permanecia 100% estática enquanto apenas o enquadramento da câmera se deslocava.
   - *Consequência:* O churrasco do domingo não tinha fumaça saindo da grelha nem espeto girando; o varal de roupas não balançava com a brisa; o ventilador de parede da repartição pública não girava; a lâmpada pendurada não oscilava nem piscava; o homem desesperado com o boleto não tremia as mãos nem suava; o devoto no bueiro não balançava o corpo em prece nem havia vapor saindo do esgoto; o cachorro no pedestal da praça não respirava nem piscava; o Caramelo na rua não trotava e sua sacola não balançava.
3. **Falta de Estrutura de Curta-Metragem:**
   - *Causa:* Ausência de mixagem sonora ambiental, camas musicais incidentais, efeitos sonoros (foleys), cortes rítmicos de comédia ácida e transições cinematográficas de fade in / fade out.

---

## 2. A VERDADEIRA ARQUITETURA DE ANIMAÇÃO 2D ESTILO RICK AND MORTY

No estilo consagrado por animações de comédia adulta para TV (Rick and Morty, BoJack Horseman, Solar Opposites, Smiling Friends, Tom & Jerry contemporâneo), a animação 2D recortada (Puppet / Cutout Animation) opera sob cinco pilares fundamentais:

```
+-----------------------------------------------------------------------------------+
|                            PIPELINE DE ANIMAÇÃO 2D VIVA                           |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ARTE ORIGINAL (1408x768)]                                                       |
|             │                                                                     |
|             ├──► 1. SEPARAÇÃO DE CAMADAS (LAYERS & INPAINTING)                    |
|             │      ├── Background Plate Limpo (Inpainting difusivo do fundo)      |
|             │      ├── Puppets / Recortes com Máscaras Suavizadas (Alpha Feather) |
|             │      └── Objetos de Cena Móveis (Props Dinâmicos)                   |
|             │                                                                     |
|             ├──► 2. MOTOR DE ATUAÇÃO E MOVIMENTO SECUNDÁRIO (ACTING)              |
|             │      ├── Ciclo de Respiração Corporal (Squash & Stretch senoidal)   |
|             │      ├── Piscar de Olhos Procedural (Blink cycle a cada 3.5s)       |
|             │      ├── Reações Corporais (Tremor de pânico, oscilação de prece)   |
|             │      ├── Gestos e Ênfase de Tronco/Cabeça                           |
|             │      └── Ciclos de Caminhada / Trote (Saltos e pêndulo de sacola)   |
|             │                                                                     |
|             ├──► 3. SINCRONIA LABIAL RIGOROSA (ANATOMICAL LIP SYNC)               |
|             │      ├── Regra de Ouro: Fala do Narrador = ZERO boca em tela        |
|             │      ├── Ativação EXCLUSIVA quando o personagem do bloco fala       |
|             │      ├── Deformação Real de Mandíbula (Jaw Drop) e Bochechas        |
|             │      └── Cavidade Bucal Ancorada Milimetricamente nos Cantos Reais  |
|             │                                                                     |
|             ├──► 4. AMBIENTE VIVO E EFEITOS VISUAIS (VFX PROCEDURAL)              |
|             │      ├── Emissores de Fumaça e Vapor (Grelha, bueiro, chaminé)      |
|             │      ├── Deformação de Vento em Tecidos e Papéis (Varal, banner)    |
|             │      ├── Movimento Mecânico (Hélice de ventilador, lâmpada de teto) |
|             │      ├── Shimmer de Calor Asfáltico (Distorção senoidal horizontal) |
|             │      └── Letras Zzz flutuantes, gotas de suor e lágrimas saltando   |
|             │                                                                     |
|             └──► 5. COMPOSIÇÃO, CINEMATOGRAFIA E ÁUDIO MULTIPISTA                 |
|                    ├── Enquadramento Dinâmico com Respiração de Lente             |
|                    ├── Transições de Cinema (Fade In / Fade Out / Cortes Secos)   |
|                    ├── Mixagem Multi-pista: Diálogos + Trilha Musical + SFX/Foley |
|                    └── Renderização Final 1080p30 H.264 + AAC Masterizado         |
+-----------------------------------------------------------------------------------+
```

---

## 3. STATUS DE PRODUÇÃO: PARTE 1 VALIDADA E ENTREGUE

A **Parte 1 (Cold Open: Cenas 001 a 005)** foi totalmente renderizada, aprovada e comitada no branch de produção:
- **Arquivo:** `video/parte_01.mp4` (52.93s, 1080p30, 50.85 MB)
- **Commit:** `278b167`
- **Resultados de QC:** Zero segundos estáticos (100% dos segundos com movimento contínuo e acting); Lip sync orgânico na Dona Cida com Jaw Drop; Fumaça na grelha, ventilador girando, lâmpada oscilando, vapor no bueiro e letras Zzz.

---

## 4. ESPECIFICAÇÃO COMPLETA: PARTE 2 (BLOCOS 006 A 013)

A **Parte 2** cobre a continuação imediata do episódio, introduzindo Dona Marta na igreja, Seu Jorge na fila da praça, o ritual noturno da linguiça no guindaste, o bueiro subterrâneo com os operários jogando cartas e a retrospectiva histórica do escândalo de 1997 com o churrasco do Xerxes Pardal.

### 4.1 Mapeamento Plano a Plano da Parte 2:

| Bloco | Cena | Falante | Duração | Personagens em Tela | Ações de Animação e Atuação (Puppet Acting) | Cenário Vivo e Efeitos Visuais (VFX) | Trilha Sonora e Efeitos de Foley (SFX) |
|---|---|---|---|---|---|---|---|
| **006** | `006.jpg` | **MARTA** | 12.79s | Dona Marta pregando na escadaria da igreja para três beatas | **Dona Marta:** LIP SYNC ANATÔMICO COM JAW DROP. Tronco gesticulando com a Bíblia levantada na mão esquerda; smartphone na mão direita vibrando notificações; brincos de argola dourada balançando com inércia física.<br>**Beatas:** As três senhoras acenam com a cabeça em uníssono concordando ("amém"). | Faixa de arrecadação da igreja com folha de maconha ondulando ao vento; reflexo de luz na cruz da fachada; folhas de árvore caindo suavemente. | Voz frontal da Marta pregando enfática + Trilha `cotidiano.mp3` transicionando para `bueiro.mp3` + som de notificação de celular vibrando. |
| **007** | `007.jpg` | **SEU_JORGE** | 9.38s | Seu Jorge sentado na cadeira de plástico na fila da praça | **Seu Jorge:** LIP SYNC ANATÔMICO PRÓPRIO. O garfo de plástico na mão dele aponta e oscila com a ênfase de cada frase; o chapéu de catador tem micro-movimento; respiração no peito magro.<br>**Fila do Povo:** Pessoas ao fundo fazendo bobs lentos de cansaço às 5h da manhã. | Vapor quente subindo do copinho de café descartável; neblina matinal roxa da alvorada derivando no horizonte. | Voz cansada e firme do Seu Jorge + Cama sutil de amanhecer + som de talheres de plástico batendo ao fundo. |
| **008** | `008.jpg` | NARRADOR | 10.21s | Povo ajoelhado na praça olhando para o alto; vereador na sacada | **NENHUMA BOCA MEXE (Voz do Narrador em off).**<br>**Vereador:** Na sacada do prédio, mexe os braços ajustando o binóculo; reflexo da lua pisca nas lentes do binóculo.<br>**Povo:** Ondulação coletiva de corpos de joelhos olhando para cima. | **Linguiça no Guindaste:** Uma linguiça gigante suspensa por cabo de aço balança no vento noturno como um pêndulo solene; facho de luz lunar dramático cortando o céu; estrelas cintilando; partículas de poeira noturna flutuando. | Voz de documentário morto-vivo do Narrador + Trilha dramática `tensao.mp3` + som de vento noturno uivando (`vento.mp3`). |
| **009** | `009.jpg` | NARRADOR | 10.03s | Terça-feira ritual: multidão prostrada diante do Caramelo no pote | **NENHUMA BOCA MEXE (Voz do Narrador em off).**<br>**Caramelo:** Deitado no pote com a faixa verde, pisca lentamente com as pálpebras em tédio e vergonha alheia; orelha direita tem espasmo sutil de pulga.<br>**Multidão:** Onda senoidal de reverência com troncos baixando e subindo. | Estátua de santo caída na grama com folhinhas de grama balançando ao redor; nuvens do meio-dia derivando suavemente no céu europeizado da praça. | Narração oficial + Trilha `tensao.mp3` desacelerando + murmúrio solene de multidão (`crowd.mp3` filtrado em passa-baixa). |
| **010** | `010.jpg` | NARRADOR | 8.75s | Subsolo: túnel de esgoto de concreto 12 metros abaixo da praça | **NENHUMA BOCA MEXE (Voz do Narrador em off).**<br>**Operário Trabalhando:** Golpes de picareta rítmicos na parede do túnel com faíscas minúsculas estalando.<br>**Operários Jogando Cartas:** Braço de um deles joga uma carta na mesa improvisada em cima do tubo; o outro leva a caneca de café à boca. | Lâmpadas fluorescentes industriais piscando com micro-cortes e flicker verde-água; vapor quente saindo da água escura do esgoto; esgoto correndo no canal com pequenas ondas reflexivas. | Narração + Trilha de ambiente `bueiro.mp3` + gotejamento de água ecoando no túnel (`agua.mp3`). |
| **011** | `011.jpg` | NARRADOR | 5.22s | Cartela de capítulo: cinejornal vintage de 1997 ("O Progresso") | **EFEITO VISUAL DE PELÍCULA ANTIGA (Cinejornal 1997):**<br>Prefeito e autoridade estadual sorrindo artificialmente enquanto seguram o cheque de papelão gigante. | Riscos verticais pretos e brancos passando aleatoriamente pela imagem (scratch film); granulação pesada (film grain 35mm); oscilação de quadro (film gate weave jitter ±2px); flash fotográfico estourando na entrega do cheque. | Narração em tom irônico + Trilha de comício/fanfarra antiga com filtro passa-faixa telefônico (som de TV analógica antiga) + estalo de flash fotográfico (`flash.mp3`). |
| **012** | `012.jpg` | NARRADOR | 14.84s | Cheque gigante de 200 mil reais ao lado de canteiro de obra abandonado | **NENHUMA BOCA MEXE (Voz do Narrador em off).**<br>Plano amplo desolado do canteiro abandonado. | Vento da decadência soprando o capim seco e a poeira de terra batida; a placa enferrujada "OBRA PARALISADA" oscila na haste de madeira; um urubu solitário plana no horizonte desértico. | Narração com ritmo cômico sobre o bueiro que nunca existiu + Trilha de violão seco / solidão (`forro.mp3` lento ou `suspense.mp3`) + vento desértico (`vento.mp3`). |
| **013** | `013.jpg` | NARRADOR | 7.16s | Churrasco da eleição: montanha de linguiça e Xerxes Pardal no palanque | **NENHUMA BOCA MEXE (Voz do Narrador em off).**<br>**Xerxes Pardal:** No palanque, com coroa de linguiça e botão 29, ergue os dois braços em comemoração populista oscilando o tronco.<br>**Palanque e Povo:** Multidão ao redor agitando cartazes de campanha do 29 em ritmo acelerado. | Fumaça densa e volumétrica saindo da churrasqueira gigante ao fundo; chuva contínua de confetes coloridos caindo sobre o palanque; bandeiras eleitorais tremulando. | Narração arrematando o clímax da Parte 2 + Trilha animada de campanha eleitoral (`comicio.mp3` / `forro.mp3`) + euforia de multidão e aplausos (`crowd.mp3`) + chiado de linguiça assando (`churrasqueira.mp3`). |

---

## 5. ESPECIFICAÇÕES DOS RIGS DE PERSONAGEM NA PARTE 2

### 5.1 Dona Marta (Cena 006)
- **Localização Facial:** Cantos da boca em `(x: 440..510, y: 260..305)`.
- **Jaw Drop:** Deslocamento vertical de mandíbula ativado exclusivamente quando `bloco == 6` e `envelope > 0.08`.
- **Props Móveis:**
  - Smartphone na mão direita: vibração senoidal de alta frequência (`dx = 1.2 * sin(50t)`) com ícone de mensagem pulsa.
  - Bíblia na mão esquerda: rotação de ênfase teatral (`rot = -3° * env`).
  - Brincos de argola: pêndulo com inércia física acompanhando o movimento da cabeça.

### 5.2 Seu Jorge (Cena 007)
- **Localização Facial:** Cantos da boca em `(x: 460..540, y: 310..360)`.
- **Jaw Drop:** Abertura orgânica da mandíbula de trabalhador cansado com dentes inferiores e língua.
- **Props Móveis:**
  - Garfo de plástico na mão: oscilação vertical apontando para a frente durante as palavras-chave ("sete em ponto", "garfo na mão").
  - Copo de café: emissor de partículas de vapor sutil subindo a 30 px/s.

### 5.3 O Cinejornal de 1997 (Cenas 011 e 012)
- **Shader de Película Degradada:**
  - Aplicação de ruído estocástico de granulação (Gaussian film grain).
  - Três linhas verticais de riscos pretos e brancos que saltam de coordenada X a cada 2 frames.
  - Flash de lâmpada de magnésio (flash fotográfico estourando em branco nos frames 15 a 18).

### 5.4 O Comício de Linguiça do Pardal (Cena 013)
- **Emissor de Confetes:** 35 partículas retangulares multicoloridas (vermelho, amarelo, azul, verde) girando e caindo em velocidade terminal diferenciada.
- **Fumaça de Churrasco Eleitoral:** Emissor triplo de partículas na base da grelha de tambor.
- **Movimento de Povo com Cartazes:** Três grupos de cartazes com o número 29 balançando em ângulos defasados.

---

## 6. SOUND DESIGN E MIXAGEM MULTI-PISTA DA PARTE 2

1. **Pista de Diálogos / Narração:** Masterizada a -1.0 dBFS (Marta, Seu Jorge e Narrador com presença e equalização de estúdio).
2. **Pista de Trilha Sonora:**
   - Cenas 006-007: `cotidiano.mp3` (-18 dBFS).
   - Cenas 008-010: `bueiro.mp3` e `tensao.mp3` (-16 dBFS).
   - Cena 011: `comicio.mp3` com filtro de rádio AM antigo (-16 dBFS).
   - Cena 012: `suspense.mp3` / `vento.mp3` (-17 dBFS).
   - Cena 013: `comicio.mp3` / `forro.mp3` (-15 dBFS) em clima de festa de vitória política.
3. **Pista de Efeitos Sonoros (SFX):**
   - Notificações de celular e passos (006).
   - Café e pratos plásticos (007).
   - Vento noturno uivando e metal rangendo no guindaste (008).
   - Goteiras e picareta no esgoto (010).
   - Estalo de flash de máquina fotográfica (011).
   - Vento árido (012).
   - Chiado potente de linguiça e ovações da multidão (013).

---
*Relatório de engenharia da Parte 2 devidamente arquivado e comitado no repositório.*
