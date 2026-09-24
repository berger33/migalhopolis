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

### 5.1 Prefeito Caramelo Autoritário (Cena 021)
- **Localização Facial:** Mandíbula e boca desenhada aberta em `(x: 680..760, y: 290..360)`.
- **Lip Sync:** Jaw drop dinâmico proporcional a `env_fala * 12.0` com ampliação da cavidade bucal, dentes afiados e língua.
- **Puppet Acting:** Pata dianteira apontando para a planta de engenharia cancelada com X vermelho piscante. Filhotes operários tremendo em uníssono.

### 5.2 Dr. Zeca na Obra Lamacenta (Cena 022)
- **Localização Facial:** Boca e focinho com sorriso malandro em `(x: 470..550, y: 310..380)`.
- **Lip Sync:** Boca abrindo com dentes e língua articulando na linha do sorriso.
- **Cenário Vivo:** Poça de lodo tóxico verde neon borbulhando com emanação de gás; fumaça saindo do escapamento da retroescavadeira.

### 5.3 Dr. Zeca Médico Fajuta (Cena 023)
- **Localização Facial:** Focinho e boca em `(x: 780..860, y: 330..400)`.
- **Lip Sync:** Articulação de fala cínica com piscada cúmplice para o espectador.
- **VFX e Cenário:** Cruz vermelha neon pulsante na parede; planta carnívora no vaso mastigando mosca; frascos de conserva com alienígenas borbulhando.

### 5.4 Prefeito Caramelo com a Linguiça de THC (Cena 024)
- **Localização Facial:** Focinho e mandíbula em `(x: 610..750, y: 450..520)`.
- **Lip Sync:** Abertura canina expressiva e perplexa na linha inferior do focinho.
- **VFX de THC:** Fórmula química do THC em neon verde esmeralda no topo da tela pulsando; linguiça assada com aura radioativa verde e vapor aromático.

### 5.5 Dr. Zeca Carimbando no IPTU (Cena 025)
- **Localização Facial:** Boca desenhada sorridente e cheia de dentes em `(x: 730..850, y: 260..340)`.
- **Lip Sync:** Jaw drop com energia vigorosa articulando as justificativas tributárias.
- **Puppet Acting:** Pata empunhando o carimbo de madeira gigante que sobe e desce com impacto sobre a folha nos picos de ênfase vocal; texto verde em fósforo piscando no monitor CRT antigo; globo terrestre girando.

### 5.6 Xerxes Pardal no Poste Eleitoral (Cena 026)
- **Localização Facial:** Boca e queixo furioso em `(x: 390..455, y: 335..390)`.
- **Lip Sync:** Boca gritando agressivamente com jaw drop de 12 px e queixo tremendo de raiva política.
- **Puppet Acting:** Braço e dedo indicador apontando freneticamente para os cartazes no poste; cartazes rasgados oscilando com o vento da rua; moradores tristes ao fundo.

### 5.7 Dr. Zeca no Celular do WhatsApp da Dona Marta (Cena 027)
- **Localização Facial:** Boca trêmula em `(x: 760..860, y: 350..430)`.
- **Lip Sync:** Boca canina apavorada abrindo e tremendo de medo eleitoral com dentes e língua.
- **VFX do Smartphone:** Tela gigante do celular com iluminação verde esmeralda volumétrica no rosto do Zeca; feed de dezenas de avatares furiosos da Dona Marta rolando pela tela; ícones de notificação vibrando.

### 5.8 Xerxes Pardal Desesperado com a Calculadora (Cena 028)
- **Localização Facial:** Boca trêmula em `(x: 620..780, y: 480..560)`.
- **Lip Sync:** Boca gaguejando e tremendo de pânico eleitoral com jaw drop de até 14 px.
- **VFX de Pupilas e Suor:** Olhos com roleta de votação girando como cassino nas íris; cascata contínua de gotículas de suor escorrendo pela calvície e pingando no colarinho; visor da calculadora com dígitos vermelhos "4,251,999" vibrando.

---

## 6. SOUND DESIGN E MIXAGEM MULTI-PISTA DA PARTE 4

1. **Diálogos:** Caramelo, Dr. Zeca e Xerxes Pardal masterizados com clareza a -1.0 dBFS pico.
2. **Camas Musicais:**
   - 021: `cotidiano.mp3` tenso e cômico (-16 dBFS).
   - 022: `forro.mp3` de malandragem na obra (-16 dBFS).
   - 023: `suspense.mp3` de consultório médico fajuto (-16 dBFS).
   - 024: `fabinho.mp3` com sintetizadores espaciais e cômicos (-16 dBFS).
   - 025: `comicio.mp3` dinâmico e burocrático (-16 dBFS).
   - 026: `tensao.mp3` agressivo de briga eleitoral (-16 dBFS).
   - 027: `suspense.mp3` de terror psicológico digital (-15 dBFS).
   - 028: `comicio.mp3` com clímax de pânico eleitoral (-15 dBFS).
3. **SFX/Foley:**
   - Papéis estapeados, lama borbulhando, bipe de monitor cardíaco, zumbido elétrico de neon, impacto de carimbo na madeira (*CLACK-THUD*), vento de sarjeta, notificações em massa de WhatsApp (*pling-pling-pling*), e clique frenético de teclas de calculadora.

---

## 7. STATUS DE PRODUÇÃO ATUALIZADO (2026-09-24)

- **Parte 4 (blocos 021 a 028) PRODUZIDA:** animadores `_animar_021` a `_animar_028` implementados em `render.py`, com lip sync anatômico exclusivo do falante em tela (regra de ouro: narrador em off nunca mexe boca), puppets articulados (filhotes em uníssono, carimbo com impacto, calculadora trêmula, bandeira, planta carnívora, placa da associação, braço do Pardal), VFX de cenário vivo (X vermelho piscante, lâmpada de lava, lodo tóxico borbulhando, cruz neon, mosca mastigada, aura e vapor de THC, CRT verde, globo girando, cartazes ao vento, folhas na sarjeta, chats da Marta subindo, pupilas roleta, cascata de suor) e mixagem multi-pista com camas por bloco e foleys (papéis estapeados, plops de lama, bipe de monitor, zumbido de neon, CLACK-THUD do carimbo, vento e buzina, pling-pling de WhatsApp, teclas de calculadora).
- **Entregas:** `video/parte_04.mp4` (1080p30, ~49s), `video/qc_parte_04.png`, `legendas/parte_04.ass`.
- **Próximo lote:** Parte 5 (a partir do bloco 029 — programa eleitoral grátis e debate ao vivo), seguindo o mesmo cadence de produção em lotes e a montagem final do curta de ~9 minutos pela junção das 10 partes.

---
*Relatório de engenharia da Parte 4 devidamente arquivado e comitado no repositório. Status de produção atualizado após a renderização da Parte 4.*
