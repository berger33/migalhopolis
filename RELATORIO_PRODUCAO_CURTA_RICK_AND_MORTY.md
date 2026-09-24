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

### 3.3 Parte 3 (Cenas 014 a 020)
- **Arquivo:** `video/parte_03.mp4` (43.03s, 1080p30, 37.8 MB)
- **Destaques:** 
  1. Cidadão idoso perplexo com ponto de interrogação neon pulsante, balão de pensamento ondulando e páginas do álbum de fotos oscilando;
  2. Bueiro moderno com brilho metálico estelar, cofre aberto e Caramelo comendo no pote dourado com rabo abanando feliz;
  3. Caramelo no pedestal farejando com micro-movimentos no focinho, olhos semicerrados e fumaça aromática volumétrica em espirais subindo dos caldeirões de incenso sobre a multidão suplicante;
  4. Seu Jorge vitorioso com lip sync anatômico sincronizado, punho erguido em triunfo, prato de comida tremendo de alegria, ventilador de parede girando e burocrata desolado;
  5. Dr. Zeca advogado de 6 dedos deslizando pilhas de contratos sobre a mesa, lip sync canino perfeito na linha do sorriso com dentes e língua, e donut alienígena radioativo com glow pulsante;
  6. Caramelo em 4 painéis de liderança falando com autoridade, patas erguidas e medalha da faixa de prefeito reluzindo;
  7. Dr. Zeca comandando a logística do caixão com lip sync anatômico, braço gesticulando para a lousa e para o caminhão, cães operários empurrando caixão oscilante na rampa, faróis volumétricos e setas de giz na lousa. Zero segundos estáticos.

---

## 4. ESPECIFICAÇÃO COMPLETA: PARTE 4 (BLOCOS 021 A 028)

A **Parte 4** é o núcleo cômico e jurídico-eleitoral do episódio, onde Caramelo, Dr. Zeca e o candidato Xerxes Pardal debatem o escândalo da linguiça canábica e o peso eleitoral dos grupos de WhatsApp da Dona Marta:

### 4.1 Mapeamento Plano a Plano da Parte 4:

| Bloco | Cena | Falante | Duração | Personagens em Tela | Ações de Animação e Atuação (Puppet Acting) | Cenário Vivo e Efeitos Visuais (VFX) | Trilha Sonora e Efeitos de Foley (SFX) |
|---|---|---|---|---|---|---|---|
| **021** | `021.jpg` | **CARAMELO** | 5.48s | Prefeito Caramelo em pé na mesa apontando o dedo; filhotes operários assustados | **CARAMELO: LIP SYNC ANATÔMICO AUTORITÁRIO.** Mandíbula e dentes caninos articulando com irritação executiva; pata dianteira apontando incisivamente para a planta cancelada com X vermelho.<br>**Cães Operários:** Grupo de filhotes com capacetes treme de medo em uníssono. | Planta de engenharia desenrolada na mesa com o X vermelho piscando; lâmpada de lava ao fundo borbulhando; lousa técnica ao fundo com equações. | Voz autoritária do Caramelo + Trilha cômica de tensão `cotidiano.mp3` (-16 dBFS) + som de papel sendo estapeado. |
| **022** | `022.jpg` | **ZECA** | 5.21s | Zeca na obra lamacenta de terno cinza falando com filhotes de capacete e pá | **ZECA: LIP SYNC ANATÔMICO CÍNICO.** Boca do Zeca articulando com cinismo de operador do direito (*"associação de moradores... caninos"*); pata de 6 dedos gesticulando suavemente em conciliação.<br>**Filhotes de Obra:** Cãezinhos operários com capacete amarelo e pás balançando a cabeça afirmativamente. | Poça de lodo tóxico verde neon borbulhando com gás; retroescavadeira ao fundo com fumaça no escapamento. | Voz enroladora do Zeca + Trilha de malandragem `forro.mp3` (-16 dBFS) + som de lama borbulhando (*plop-plop*). |
| **023** | `023.jpg` | **ZECA** | 5.34s | Zeca vestido de médico com jaleco branco, estetoscópio e receituário | **ZECA: LIP SYNC DE DOUTOR.** Boca do Zeca articulando com seriedade médica fajuta (*"O cultivo é medicinal... É terapia"*); caneta na pata batendo no bloco de receitas.<br>**Olhar:** Zeca pisca um olho de forma cúmplice para a câmera. | Cruz vermelha neon na parede pulsando suavemente; planta carnívora no vaso mastigando mosca; frascos com fetos alienígenas borbulhando. | Voz professoral fajuta do Zeca + Trilha de consultório/suspense `suspense.mp3` (-16 dBFS) + bipe suave de monitor cardíaco. |
| **024** | `024.jpg` | **CARAMELO** | 4.67s | Caramelo em close segurando a linguiça radioativa com 40% de THC | **CARAMELO: LIP SYNC INDIGNADO.** Focinho de Caramelo falando com incredulidade e gravidade (*"Zeca, a linguiça tem quarenta por cento de THC"*).<br>**Gesticulação:** Pata erguida segurando a linguiça assada que emite vapor esverdeado. | Fórmula molecular do THC em neon verde brilhando e pulsando no ar; aura radioativa verde ao redor da linguiça; fumaça canábica aromática subindo. | Voz estupefata do Caramelo + Trilha de ficção científica/humor `fabinho.mp3` (-16 dBFS) + zumbido elétrico suave. |
| **025** | `025.jpg` | **ZECA** | 5.23s | Zeca carimbando violentamente a folha de cobrança "DEBT ENFORCED" | **ZECA: LIP SYNC COM IMPACTO.** Boca do Zeca sorrindo maliciosamente ao justificar o abatimento no IPTU.<br>**Ação do Carimbo:** O carimbo de madeira gigante sobe e desce com impacto sobre a folha nos momentos de ênfase. | Letras verdes fosfóricas na tela do computador antigo piscando; globo terrestre girando suavemente; carimbo levantando poeira no papel. | Voz rápida e prática do Zeca + Trilha animada `comicio.mp3` (-16 dBFS) + som de carimbada violenta na mesa (*CLACK-THUD*). |
| **026** | `026.jpg` | **PARDAL** | 5.12s | Xerxes Pardal de terno bege apontando para o poste eleitoral e humilhando moradores | **PARDAL: LIP SYNC HISTÉRICO.** Boca e queixo do Xerxes Pardal abrindo e fechando com raiva política (*"o senhor já perdeu pra um poste em 2016"*); braço apontando freneticamente para os cartazes do poste.<br>**Moradores Tristes:** Três cidadãos encostados no muro olhando desiludidos. | Cartazes eleitorais no poste rasgando com o vento; fio elétrico oscilando; folhas secas rolando na sarjeta. | Voz esganiçada e agressiva do Pardal + Trilha tensa `tensao.mp3` (-16 dBFS) + som de vento de rua e buzina ao longe. |
| **027** | `027.jpg` | **ZECA** | 6.89s | Zeca apavorado segurando celular gigante iluminado com o rosto da Dona Marta | **ZECA: OLHOS ARREGALADOS E LIP SYNC APREENSIVO.** Zeca falando com a boca trêmula de medo eleitoral; suor escorrendo pelas bochechas peludas.<br>**Celular:** Dezenas de janelas de chat do WhatsApp com fotos da Dona Marta gritando sobem pela tela do celular. | Luz verde esmeralda da tela do celular iluminando o rosto do Zeca; notificações vibrando com pequenos raios; fumaça saindo da xícara de café. | Voz preocupada do Zeca + Trilha de pânico cômico `suspense.mp3` (-15 dBFS) + enxurrada de notificações de celular (*pling-pling-pling*). |
| **028** | `028.jpg` | **PARDAL** | 7.91s | Xerxes Pardal suando em bica, segurando calculadora com número de votos | **PARDAL: LIP SYNC DESESPERADO E SUOR EM CASCATA.** Boca do Pardal tremendo e gaguejando ao calcular os 4 mil votos da Marta; gotas grossas de suor escorrendo pela testa e pingando.<br>**Olhos do Pardal:** As pupilas do Pardal giram como roletas de cassino com números eleitorais refletidos nas lentes. | Calculadora digital com números vermelhos piscando ("4,251,999"); bandeira do Brasil na parede tremulando; calculadora vibrando na mão trêmula. | Voz apavorada do Pardal + Trilha de clímax eleitoral `comicio.mp3` (-15 dBFS) + som de botões de calculadora sendo apertados furiosamente. |

---

## 5. ESPECIFICAÇÕES DOS RIGS DE PERSONAGEM NA PARTE 4

### 5.1 Prefeito Caramelo com a Linguiça de THC (Cena 024)
- **Localização Facial:** Mandíbula e focinho em `(x: 820..920, y: 220..310)`.
- **Linguiça Radioativa:** Elemento em `(x: 910..980, y: 180..260)` com pulso senoidal de brilho verde esmeralda e partículas de fumaça subindo.

### 5.2 Dr. Zeca no Celular do WhatsApp da Dona Marta (Cena 027)
- **Localização Facial:** Boca em `(x: 580..680, y: 280..380)` com expressão aterrorizada.
- **Tela do Smartphone:** `(x: 640..740, y: 240..460)` com rolagem infinita de avatares furiosos da Dona Marta.

### 5.3 Xerxes Pardal Desesperado com a Calculadora (Cena 028)
- **Localização Facial:** Boca e rugas em `(x: 810..920, y: 340..460)`.
- **Efeito Visual de Pupilas:** Reflexo dinâmico de votos e gráficos nas íris.
- **Cascata de Suor:** Gotículas descendo pela calvície e pingando no colarinho.

---

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
