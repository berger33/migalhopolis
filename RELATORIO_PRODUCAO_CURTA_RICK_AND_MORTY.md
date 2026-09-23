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

## 3. ESPECIFICAÇÃO TÉCNICA DO MOTOR DE CENA VIVA (`CenaViva`)

O novo motor em Python substitui completamente a abordagem antiga de renderização estática:

### 3.1 Separação de Camadas e Inpainting Difusivo
- Para cada personagem ou objeto que se move, é traçada uma máscara poligonal precisa.
- O fundo por trás do recorte é reconstruído uma única vez na inicialização da cena usando **Inpainting Difusivo Bounded** (filtros uniformes iterativos nas bordas conhecidas), preenchendo a silhueta oculta.
- Isso permite que o personagem se incline, respire, salte e gesticule sem revelar um buraco negro ou distorcer o cenário ao redor.

### 3.2 Atuação Corporal (Puppet Engine)
- **Respiração Orgânica:** Modulação sutil de escala vertical `scale_y = 1.0 + 0.006 * sin(2π * 0.45 * t)` ancorada na base do corpo de cada personagem.
- **Piscada de Olhos (Eye Blink):**
  - Duração de 0.14s (4 frames a 30fps): 2 frames fechando pálpebras via squash vertical na máscara dos olhos, 1 frame fechado, 1 frame abrindo.
  - Intervalos assíncronos e orgânicos (ex: Caramelo pisca a cada 4.2s com expressão de tédio).
- **Atuação Mecânica e Gestual:**
  - *Homem do Boleto (002):* Tremor de alta frequência nas mãos e cabeça `dx = 1.8 * sin(2π * 6.5 * t)`, folhas de conta tremendo no vento.
  - *Devoto no Bueiro (002):* Balanço pendular de oração `rot = 2.6° * sin(2π * 0.45 * t)` ancorado nos joelhos.
  - *Dona Cida (005):* Inclinação enfática em direção à rua `rot = -2.0° * envelope_fala`, tronco avançando, mão em concha na boca.
  - *Caramelo Andando (005):* Salto elástico de passo `dy = 5.0 * |sin(2π * 1.9 * t)|` e balanço defasado da sacola de pão `rot_sacola = 12° * sin(2π * 1.9 * t - 0.8)` com pivô no focinho.

### 3.3 Sincronia Labial Anatômica (Lip Sync)
- **Filtro de Falante Ativo:**
  ```python
  if bloco.personagem != CENA_FALANTE_EM_TELA[cena_id]:
      # PERSONAGEM NÃO ESTÁ FALANDO (ex: voz do Narrador em off)
      # Boca permanece 100% original; atuações corporais e faciais ativas.
      envelope_boca = 0.0
  ```
- **Ancoragem nos Lábios Originais:**
  - As coordenadas de ancoragem bucal foram extraídas diretamente dos pixels da arte original.
  - Ao abrir, a mandíbula inferior sofre um campo de deslocamento vertical (Jaw Drop) via `scipy.ndimage.map_coordinates`, puxando o queixo e bochechas para baixo proporcionalmente à energia da fala.
  - A cavidade bucal (com contorno escuro, dentes superiores e língua) é desenhada internamente entre os cantos da boca do personagem, respeitando a sua proporção estilística.
  - Em momentos de pausa ou silêncio (`envelope < 0.10`), os pixels originais da arte desenhada são mantidos intactos.

### 3.4 Efeitos Visuais Ambientais (VFX Procedural)
- **Grelha de Churrasco:** Emissor de fumaça cinza-quente com dispersão senoidal ascendente a 55 px/s e vento lateral a -18 px/s.
- **Vapor de Bueiro:** Coluna de vapor esbranquiçado semitransparente que se expande e desvanece no ar.
- **Ventilador de Parede:** Hélice circular com máscara que gira a 1.5 rotações por segundo com desfoque de movimento perceptivo.
- **Lâmpada de Teto e Flicker:** Oscilação pendular suave do cabo e pulso de luminosidade quente com micro-quedas estocásticas (estilo fluorescente de boteco).
- **Varal e Tecidos:** Deformação senoidal contínua horizontal no eixo X das roupas estendidas.
- **Shimmer de Calor:** Distorção horizontal nas linhas do asfalto da praça sob o sol do meio-dia.
- **Letras Zzz:** Letras estilizadas que brotam do focinho do cão dormindo e flutuam em curva senoidal ascendente com transparência gradativa.
- **Gotas de Suor e Lágrimas:** Gotas no estilo clássico de animação que brotam na têmpora do cidadão desesperado com o boleto e escorrem em velocidade acelerada.

### 3.5 Sonoplastia e Mixagem de Curta-Metragem
O projeto conta com biblioteca completa de trilhas e foleys recuperados:
- **Camas Musicais (Beds):** `tema.mp3`, `cotidiano.mp3`, `bueiro.mp3`, `comicio.mp3`, `drama.mp3`, `fabinho.mp3`, `final.mp3`, `forro.mp3`, `jingle.mp3`, `suspense.mp3`, `tensao.mp3`.
- **Efeitos Sonoros (SFX):** `churrasqueira.mp3`, `crowd.mp3`, `agua.mp3`, `celular.mp3`, `flash.mp3`, `fogos.mp3`, `grilos.mp3`, `latido.mp3`, `moscas.mp3`, `sinos.mp3`, `ventilador.mp3`, `vento.mp3`.
- **Mixagem Master:**
  - Pista de Voz (Diálogos/Narração): normalizada a -1.0 dBFS com presença frontal nítida.
  - Pista de Trilha Sonora: posicionada a -18.0 dBFS para suporte emocional sem cobrir os textos.
  - Pista de SFX: inserida pontualmente (ex: chiado de churrasco na grelha do bloco 002 a -14.0 dBFS).

---

## 4. MAPEAMENTO DE CENAS E ANIMAÇÃO: PARTE 1 (BLOCOS 001 A 005)

| Bloco | Cena | Falante | Personagens em Tela | Ações de Animação e Atuação (Acting) | Elementos Vivos do Cenário (VFX) | Áudio e SFX |
|---|---|---|---|---|---|---|
| **Título** | `T_titulo` | N/A | Cartela de Título | Respiração de lente, vinheta dinâmica, revelação cinematográfica | Nuvens crepusculares derivando suavemente no topo | Trilha: `tema.mp3` com fade in |
| **001** | `001.jpg` | NARRADOR | Vista Aérea de Migalhópolis | Urubus empoleirados na fiação elétrica acenando a cabeça; 1 urubu voando no céu em asa batente | Nuvens em deriva lenta, faixa municipal ondulando ao vento, fumaça sutil em chaminés, partículas de poeira dourada ao sol | Trilha: `tema.mp3` transicionando para `cotidiano.mp3` |
| **002** | `002.jpg` | NARRADOR | Painel Triplo: Povo do Churrasco, Homem do Boleto, Devoto no Bueiro | **Painel Esq:** Churrasqueiro vira espeto, povo rindo com o corpo e cabeças em fases alternadas.<br>**Painel Meio:** Homem treme as mãos com o boleto, cabeça oscila de pânico, gotas de suor escorrem da testa.<br>**Painel Dir:** Homem ajoelhado balança o tronco em oração devota, lágrimas escorrem. *(NENHUMA BOCA MEXE NA NARRAÇÃO)* | **Painel Esq:** Fumaça volumétrica subindo da churrasqueira, roupas balançando no varal.<br>**Painel Meio:** Ventilador de parede girando as hélices, lâmpada oscilando no teto com flicker de energia.<br>**Painel Dir:** Vapor quente subindo do bueiro. | Narração oficial + SFX: `churrasqueira.mp3` e `crowd.mp3` sutil em segundo plano |
| **003** | `003.jpg` | NARRADOR | Praça central, cão dormindo no pote sobre o pedestal | Cachorro dormindo com respiração rítmica no abdômen, orelhas com micro-espasmo a cada 3s, pálpebras fechadas | Letras "Zzz" animadas subindo em curva senoidal, shimmer de calor térmico ondulando o asfalto sob o sol do meio-dia | Trilha: `cotidiano.mp3` + som de cigarras/vento leve |
| **004** | `004.jpg` | NARRADOR | Caramelo no gabinete (close-up) | Caramelo com expressão burocrática de desdém, pisca lentamente com as pálpebras a cada 4.2s, orelha direita tem reflexo sutil, folhas de despacho na pata tremulam com a brisa da janela *(BOCA FECHADA NA NARRAÇÃO)* | Notas adesivas na parede balançando suavemente, micro-oscilação de luz na veneziana da janela | Trilha: `cotidiano.mp3` |
| **005** | `005.jpg` | **CIDA** | Dona Cida (porta do mercadinho) e Caramelo (trotando na calçada) | **Dona Cida:** ATUAÇÃO COMPLETA DE FALA. Inclinação do tronco para a frente, braço/mão gesticulando em concha, maxilar inferior abrindo organicamente sincronizado com o áudio dela.<br>**Caramelo:** Caminha trotando na calçada com bounce vertical elástico nos passos, sacola de pão na boca oscilando como pêndulo físico. | Reflexos de luz brilhando nas garrafas do mercadinho, brisa de rua | Voz frontal da Cida gritando na porta + Trilha `cotidiano.mp3` + SFX ambiente de rua |

---

## 5. ROTEIRO DE PRODUÇÃO PARA AS PARTES SUBSEQUENTES (PARTE 2 A 10)

O mesmo rigor de recorte, acting secundário, sincronia labial restrita ao falante e cenários dinâmicos será aplicado nas 9 partes seguintes que compõem o curta-metragem:

- **Parte 2 (Blocos 006 a 013):**
  - *Marta na Igreja (006):* Bíblia na mão, celular vibrando notificações, boca da Marta sincronizada, ventilador de teto da paróquia girando.
  - *Seu Jorge no Bar (007):* Garfo na mão, espetinho, cerveja com espuma borbulhando, Seu Jorge falando com a boca dele sincronizada.
  - *Noite e Bueiro (008 a 013):* Luzes da cidade acendendo, névoa noturna, vapor denso de bueiro com iluminação volumétrica verde/amarela, grilos noturnos.
- **Parte 3 (Blocos 014 a 020):**
  - *Gabinete e Conspiração:* Caramelo e Seu Jorge negociando; introdução de Zeca (o cachorro advogado de terno com seis dedos). Zeca gesticulando com a pasta executiva.
- **Parte 4 (Blocos 021 a 028):**
  - *Entrada de Xerxes Pardal:* O ex-prefeito tentando puxar assunto e exibindo crachás. Atuação cômica de desespero político, gravata torta oscilando.
- **Parte 5 (Blocos 029 a 035):**
  - *Comício e Coletiva da TV Migalha:* Repórter com microfone tremendo, flash de câmeras fotográficas estourando em tela, multidão com cartazes balançando.
- **Parte 6 (Blocos 036 a 043):**
  - *Tensão no Tribunal de Contas:* Caramelo encarando auditores com calma impassível; papéis voando na mesa, ventilador no máximo.
- **Parte 7 (Blocos 044 a 053):**
  - *A Revelação do Pote e a Madrugada:* Planos cinematográficos com sombras longas, iluminação dramática contrastada, fumaça e neblina.
- **Parte 8 (Blocos 054 a 063):**
  - *Encontro com Fabinho:* O garoto de 8 anos andando de bicicleta pela praça, rodas girando, Caramelo observando do pedestal.
- **Parte 9 (Blocos 064 a 072):**
  - *O Grande Clímax Político de Migalhópolis:* Conflito verbal entre Caramelo, Pardal e Marta; chuva de papel picado, bandeiras e tensão máxima.
- **Parte 10 (Blocos 073 a 079 + Créditos):**
  - *Desfecho Irônico e Créditos Finais:* O retorno ao status quo do bairro. Fade out com o troféu reaparecendo misteriosamente no lixo; créditos finais com trilha completa e cartaz oficial.

---

## 6. ONDE PARAMOS E PRÓXIMOS PASSOS IMEDIATOS

### 6.1 Onde Paramos:
1. **Acervo Completo Recuperado:** Todos os 79 áudios oficiais, 79 imagens originais dos planos, character sheets e biblioteca de áudio incidental (beds e sfx) estão agora integrados e preservados no branch de trabalho `arena/01a0d098-migalhopolis`.
2. **Medição Anatômica Concluída:** Os pontos de pivô, contornos poligonais dos personagens principais (Dona Cida, Caramelo Gabinete, Caramelo Andando, Homem do Boleto, Homem do Bueiro, Cão da Praça) e os emissores de partículas foram precisamente catalogados.
3. **Refatoração do Motor de Renderização:** O script `render.py` foi reestruturado para implementar o motor `CenaViva` com recortes reais, inpainting de fundo, acting secundário, física de tecidos, partículas e sincronia labial restrita ao falante ativo.

### 6.2 O Que Será Executado a Seguir:
1. **Correção dos Shapes de Deslocamento no Script:** Ajustar o tratamento dimensional no cálculo de rotação e gradiente térmico em `render.py` para execução sem travamentos.
2. **Geração de Quadro de Controle de Qualidade (QC Contact Sheet):** Extrair e inspecionar visualmente os fotogramas-chave da Parte 1 para verificar:
   - Posicionamento perfeito da boca da Dona Cida durante a fala.
   - Ausência absoluta de bocas mexendo nos blocos do Narrador.
   - Presença viva da fumaça na grelha, ventilador girando, lâmpada oscilando, vapor no bueiro e letras Zzz.
   - Troca de passos do Caramelo e pêndulo da sacola de pão.
3. **Renderização Master da Parte 1 (`video/parte_01.mp4`):**
   - Duração aproximada de 52 segundos, integrando trilha sonora (`tema.mp3`, `cotidiano.mp3`), efeito de foley (`churrasqueira.mp3`) e fades cinematográficos.
4. **Validação de Movimento:** Execução de teste de métrica de diferença inter-quadros (frame-difference metric) para garantir que 100% da linha do tempo contenha vida e ação animada, eliminando qualquer aspecto de imagem estática.
5. **Apresentação e Subida no GitHub:** Subir o vídeo master e os scripts atualizados no GitHub e apresentar ao usuário para aprovação antes de expandir para as partes seguintes.

---
*Relatório salvo no repositório para preservação de sessão e referência de engenharia de animação.*
