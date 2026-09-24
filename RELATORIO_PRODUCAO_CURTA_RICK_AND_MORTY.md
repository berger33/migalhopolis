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
Nas tentativas anteriores de renderização, ocorreu uma falha conceitual grave: o processo foi tratado como um **"Motion Comic" (slideshow com câmera Ken Burns e adesivo de boca)**, e **NÃO** como um **desenho animado de verdade**.

### 1.2 Os Problemas Detectados e Suas Causas Raízes:
1. **Adesivo de Boca Flutuante ao Lado do Personagem:**
   - *Causa:* Foram utilizadas coordenadas estimadas sem medição pixel-a-pixel nos recortes, sobrepondo uma elipse genérica pré-desenhada com dentes e língua que não deformava a mandíbula do personagem.
   - *Erro Fatal de Direção:* O script ativou animação de boca em personagens na tela durante falas do **NARRADOR**. O narrador é uma voz em *off* (estilo documentário morto-vivo). Quando o narrador fala, os personagens na cena **JAMAIS** devem mexer a boca como ventríloquos. Devem realizar **atuação silenciosa** (olhares, piscadas, reações, respiração).
2. **Cenários e Personagens Mortos (Sem Vida):**
   - *Causa:* A imagem original permanecia 100% estática enquanto apenas o enquadramento da câmera se deslocava.
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

## 3. STATUS DAS ENTREGAS: PARTES 1 E 2 VALIDADAS NO GITHUB

### 3.1 Parte 1 (Cold Open: Cenas 001 a 005)
- **Arquivo:** `video/parte_01.mp4` (52.93s, 1080p30, 50.85 MB)
- **Commit:** `278b167`
- **Destaques:** Cartela cinematográfica com fade; fumaça na grelha; ventilador girando; lâmpada oscilando; homem do boleto tremendo com suor; devoto no bueiro com lágrimas e vapor; cão no pedestal com respiração e "Zzz"; Caramelo com tédio no gabinete; Dona Cida com lip sync anatômico e jaw drop gritando na rua; Caramelo trotando com sacola de pão pendular. Zero segundos estáticos.

### 3.2 Parte 2 (Cenas 006 a 013)
- **Arquivo:** `video/parte_02.mp4` (75.20s, 1080p30, 55.63 MB)
- **Commit:** `1249865`
- **Destaques:** Dona Marta pregando com lip sync na igreja, celular vibrando notificações e beatas concordando; Seu Jorge com garfo de plástico apontando e vapor subindo do prato; linguiça gigante no guindaste balançando ao luar; Caramelo no pote com vergonha alheia e multidão ajoelhada; túnel de esgoto subterrâneo com faíscas de solda e operários jogando cartas; cinejornal vintage 1997 com riscos de filme, granulação e flash fotográfico; canteiro abandonado com placa enferrujada balançando e tumbleweed rolando; comício eleitoral do Xerxes Pardal com coroa de linguiça, fumaça colorida e chuva contínua de confetes. Zero segundos estáticos.

---

## 4. ESPECIFICAÇÃO COMPLETA: PARTE 3 (BLOCOS 014 A 020)

A **Parte 3** aprofunda a sátira política e burocrática de Migalhópolis, revelando a relação de poder entre o Prefeito Caramelo, o Seu Jorge e a chegada do lendário **Zeca, o cachorro advogado de seis dedos**:

### 4.1 Mapeamento Plano a Plano da Parte 3:

| Bloco | Cena | Falante | Duração | Personagens em Tela | Ações de Animação e Atuação (Puppet Acting) | Cenário Vivo e Efeitos Visuais (VFX) | Trilha Sonora e Efeitos de Foley (SFX) |
|---|---|---|---|---|---|---|---|
| **014** | `014.jpg` | NARRADOR | 8.05s | Cidadão idoso coçando a cabeça; silhueta em balão de pensamento; álbum de fotos | **NENHUMA BOCA MEXE (Voz do Narrador em off).**<br>**Cidadão Idoso:** Mão coçando a cabeça com movimento rítmico perplexo; sobrancelhas erguidas em dúvida cômica.<br>**Silhueta Misteriosa:** No balão de pensamento, a mão da silhueta desce alimentando o cachorrinho. | Ponto de interrogação gigante em neon amarelo piscando acima da cabeça; nuvem do balão de pensamento ondulando suavemente; folhas do álbum de fotos folheando com a brisa; partículas de poeira da memória. | Narração oficial de documentário + Cama incidental nostálgica/irônica `suspense.mp3` (-17 dBFS) + som sutil de páginas de álbum virando. |
| **015** | `015.jpg` | NARRADOR | 8.59s | Tampa de bueiro reluzente de um lado, cofre vazio do outro, Caramelo no centro comendo em tigela de ouro | **NENHUMA BOCA MEXE (Voz do Narrador em off).**<br>**Caramelo:** Cabeça mergulhando na tigela de ouro mastigando ração; rabinho balançando com felicidade gastronômica; faixa verde de prefeito reluzindo.<br>**Cofre:** Porta aberta vazia revelando o vazio institucional. | Tampa de bueiro com brilho metálico estelar estalando (`+` sparkle); teias de aranha dentro do cofre vazio balançando com o vento; raios de luz dourada saindo da tigela de ouro. | Narração + Trilha de cinismo financeiro `cotidiano.mp3` (-18 dBFS) + som de mastigação e lambidas de cão + eco metálico de cofre vazio. |
| **016** | `016.jpg` | NARRADOR | 4.49s | Close-up do Caramelo no pedestal farejando a multidão faminta | **NENHUMA BOCA MEXE (Voz do Narrador em off).**<br>**Caramelo:** Focinho arrebitado farejando o ar com espasmo rítmico nas narinas; olhos semicerrados de morto-vivo olhando de cima para baixo com superioridade moral e burocrática; orelha direita tem reflexo sutil. | Brisa matinal da praça agitando os pelos do peito; multidão ao fundo fazendo micro-movimentos de súplica silenciosa. | Narração + Trilha de expectativa e tensão `tensao.mp3` (-16 dBFS) + efeito sonoro de farejada de cachorro. |
| **017** | `017.jpg` | **SEU_JORGE** | 5.38s | Seu Jorge comemorando o prato cheio; morador rejeitado com esfregão e balde | **SEU JORGE: LIP SYNC ANATÔMICO COM JAW DROP.** Boca do Seu Jorge mexendo com expressão vitoriosa e debochada (`x: 343, y: 388`); o prato cheio de churrasco é levantado para o alto em comemoração; Seu Jorge dá um riso de canto.<br>**Morador Rejeitado:** Ao fundo, o homem rejeitado abaixa os ombros em decepção e segura o cabo do esfregão cabisbaixo. | Vapor quente subindo do prato de carne do Seu Jorge; água suja ondulando no balde do morador rejeitado. | Voz triunfante do Seu Jorge ("Quem ele não escolhe...") + Trilha `cotidiano.mp3` (-17 dBFS) + som de talheres e prato batendo. |
| **018** | `018.jpg` | **ZECA** | 7.37s | Zeca (o cachorro advogado de terno cinza largo, gravata vermelha e seis dedos) na mesa bagunçada | **ZECA: LIP SYNC ANATÔMICO PRÓPRIO.** Focinho de cão advogado abrindo e fechando com dentes pontiagudos e língua malandra; sorriso cínico de operador do direito.<br>**Pata de Seis Dedos:** A pata direita bate na mesa apontando com firmeza as linhas do contrato nos momentos exatos (*"aqui, e aqui, e aqui"*); a gravata vermelha balança com a ênfase corporal. | Pilha de contratos e despachos deslizando na mesa em direção à câmera; carimbo da prefeitura oscilando; caneta tinteiro brilhando. | Voz rouca e malandra do Zeca + Trilha de jazz/suspense de repartição pública `tensao.mp3` / `bueiro.mp3` (-16 dBFS) + som de papel sendo batido na mesa (*thump*). |
| **019** | `019.jpg` | **CARAMELO** | 5.86s | Close-up do Prefeito Caramelo no gabinete: erguendo as quatro patas | **CARAMELO: LIP SYNC ANATÔMICO PRÓPRIO DE PREFEITO.** Pela primeira vez o Prefeito Caramelo fala com a própria voz!<br>Focinho abrindo com autoridade executiva e dentes caninos; olhos semicerrados de desprezo burocrático; ergue a pata direita com firmeza impondo autoridade institucional (*"Respeite a hierarquia"*); corrente de ouro de prefeito balançando no peito. | Bandeira do município ao fundo ondulando sutilmente com a brisa do ar-condicionado; veneziana da janela com oscilação de luz natural. | Voz grave, seca e autoritária do Caramelo + Trilha de poder e autoridade `drama.mp3` / `tema.mp3` (-15 dBFS) + balanço metálico de medalha/corrente de ouro. |
| **020** | `020.jpg` | **ZECA** | 6.07s | Zeca na central logística dirigindo o roubo/transporte do caixão para a caçamba do caminhão | **ZECA: LIP SYNC ANATÔMICO COM JAW DROP.** Boca do Zeca articulando com cinismo administrativo (*"Roubar caixão não é corrupção... É logística"*).<br>**Gesticulação:** Zeca segura a prancheta com a pata de seis dedos e gesticula com a outra apontando para o caminhão e para o fluxograma da lousa.<br>**Operários Caninos:** Cachorros com capacete de obra operam as cordas do guincho. | Caixão funerário balançando nas cordas enquanto é içado para a caçamba; faróis do caminhão acesos com feixes de luz volumétrica; setas e gráficos na lousa branca com brilho. | Voz cínica e convincente do Zeca + Trilha animada e irônica de trambique `forro.mp3` / `comicio.mp3` (-16 dBFS) + motor de caminhão a diesel em marcha lenta + rangido de cordas e metal. |

---

## 5. ESPECIFICAÇÕES DOS RIGS DE PERSONAGEM NA PARTE 3

### 5.1 Zeca — O Cachorro Advogado de Seis Dedos (Cenas 018 e 020)
- **Localização Facial:** Focinho e boca canina em `(x: 360..480, y: 240..340)`.
- **Lip Sync Canino:** Abertura da mandíbula inferior proporcional à energia de fala com dentes afiados e língua pontiaguda.
- **Pata de Seis Dedos:** Elemento cômico central da Bíblia Visual do desenho. Pata articulada com 6 dedos visíveis que gesticula e bate na mesa em sincronia com os três picos de ênfase do áudio (*"assina aqui [1], e aqui [2], e aqui [3]"*).

### 5.2 Caramelo — O Prefeito Falando (Cena 019)
- **Localização Facial:** Mandíbula e focinho em `(x: 610..740, y: 260..360)`.
- **Lip Sync de Autoridade:** Abertura precisa e contida, estilo político cansado e inabalável que não grita porque não precisa.
- **Gesticulação:** Pata dianteira erguida em ângulo de autoridade hierárquica.

### 5.3 Seu Jorge Triunfante (Cena 017)
- **Localização Facial:** Mandíbula em `(x: 343, y: 388)`.
- **Gesticulação:** Prato de churrasco erguido em vitória; vapor subindo do alimento.

---

## 6. SOUND DESIGN E MIXAGEM MULTI-PISTA DA PARTE 3

1. **Diálogos:** Zeca, Caramelo, Seu Jorge e Narrador masterizados a -1.0 dBFS.
2. **Camas Musicais:**
   - 014: `suspense.mp3` nostálgico (-17 dBFS).
   - 015-016: `cotidiano.mp3` e `tensao.mp3` (-16 dBFS).
   - 017: `cotidiano.mp3` com swing brasileiro (-16 dBFS).
   - 018: `bueiro.mp3` de repartição soturna (-16 dBFS).
   - 019: `tema.mp3` solene de autoridade municipal (-15 dBFS).
   - 020: `forro.mp3` / `comicio.mp3` cômico de operação logística (-16 dBFS).
3. **SFX/Foley:**
   - Notificações, talheres, papéis de contrato, motor diesel de caminhão, guincho do caixão e faróis.

---
*Relatório de engenharia da Parte 3 devidamente arquivado e comitado no repositório.*
