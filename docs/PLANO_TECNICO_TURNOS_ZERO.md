# Plano técnico — Turnos Zero

## 1. Visão do produto

Turnos Zero é um jogo 2D de horror sobrenatural e sobrevivência burocrática. O jogador trabalha para uma agência de serviços extraordinários, recebe contratos em locais anômalos e precisa investigar, seguir protocolos, evitar a presença e quitar uma dívida inicial de R$ 1.000.000.

A direção visual combina documentos e inspeção tátil (*Papers, Please*), ferramentas e terminais analógicos (*Alien: Isolation*), equipamento diegético (*Dead Space*) e arquitetura opressiva (*Control*). As referências orientam a linguagem de interação; agência, personagens, cenários, textos e eventos são originais.

## 2. Loop principal

1. Admissão e escolha do vínculo.
2. Dossiê: dívida, pagamento, risco, local e protocolos.
3. Preparação de equipamentos.
4. Investigação do ambiente e registro de pistas.
5. Manipulação de objetos, com mudança visual e pressão anômala.
6. Consulta ao rádio e à central de vigilância.
7. Resolução de três ocorrências.
8. Sobrevivência: decidir quando avançar, esconder-se ou usar equipamentos.
9. Pagamento e progressão para o próximo contrato.

## 3. Economia e dificuldade

- Dívida inicial: **R$ 1.000.000**.
- Pagamento do primeiro contrato: **R$ 50**.
- Pagamento dobra a cada contrato: **R$ 50, R$ 100, R$ 200, R$ 400, R$ 800...**.
- Risco também dobra: **x1, x2, x4, x8, x16...**.
- A estabilidade inicial depende do vínculo; violações e ataques da presença descontam estabilidade conforme o risco do contrato.
- A campanha continua em ciclos dos quatro ambientes até o limite técnico de 60 contratos.

## 4. Arquitetura

- `main.py`: interface Tkinter Canvas, modo terminal, telas de briefing, investigação, inspeção, decisão, CFTV e rádio.
- `turnos_zero.py`: motor, economia, dificuldade, evidências, equipamentos, estados de objetos, pressão anômala, abrigos e persistência.
- `scene_manager.py`: catálogo, validação, hit testing e coordenadas.
- `dados/cenas.json`: catálogo de fundos e hotspots de fallback.
- `dados/objetos_cenas.json`: objetos, posições, dimensões, z-order, visibilidade, hotspots, ações e variantes.
- `assets/ambientes/`: seis fundos SVG/PNG, exportados em 834×469.
- `assets/objetos/`: 16 sprites independentes e 15 variantes SVG/PNG, exportados em 512×512.
- `assets/som/`: quatro loops WAV de 10 segundos.
- `tools/editor_cenas.py`: edição visual de camadas e hotspots.
- `tools/export_assets.py`: exportação de SVGs e geração dos loops de áudio.
- `tools/generate_audio.py`: síntese de ambientes com biblioteca padrão do Python.
- `tests/`: testes do motor, campanha, cenas, objetos, equipamentos, ameaça e áudio.

## 5. Sistemas implementados

### Renderização e edição
- Fundo arquitetônico 16:9 e objetos como sprites independentes.
- Objetos com coordenadas normalizadas `x/y/w/h`, ordem `z` e visibilidade.
- Variantes de sprite para objetos manipulados.
- Hotspots seguem o retângulo da camada editável.
- Editor suporta arrastar, redimensionar, entrada numérica, ocultar, reordenar, substituir PNG e salvar.

### Investigação
- Cada hotspot abre uma ficha de inspeção.
- Evidência só é registrada por exame ou fotografia; selecionar o objeto não coleta automaticamente.
- Estados de objetos e evidências são persistidos e isolados por contrato.
- O dossiê permite revisar pistas antes das decisões.

### Equipamentos
- Lanterna com bateria e cone de iluminação; o cenário escurece quando fica sem carga.
- Rádio com três transmissões contextualizadas por contrato.
- Câmera com três exposições, modo CFTV de seis canais e fotografia de evidências. Um flash no canal correto interrompe a presença até a próxima decisão.
- Ferramentas são repostas no início do próximo contrato.

### Horror e sobrevivência
- Cada missão possui um perfil de pressão anômala associado a objetos interativos.
- Interações aumentam pressão; no limite, a presença inicia uma perseguição.
- A presença aparece no campo visual e pode ser identificada no feed CCTV correspondente.
- Se o agente avançar exposto, a presença causa dano adicional escalado pelo risco.
- Cada perseguição permite um único uso do abrigo específico do local. Sair do abrigo deixa o agente exposto até a ameaça ser resolvida.
- Os estados de ameaça, perseguição e abrigo são persistidos; saves antigos recebem valores padrão.

### Áudio
- Quatro paisagens sonoras originais por missão: loja, edifício, cinema e laboratório.
- Efeitos curtos para interação, evidência, acerto e violação.
- WAV mono, 16-bit, 22.050 Hz; playback de loop e one-shot pelo Windows `winsound`, com fallback simples de som do Tk.

## 6. Missões

1. **Loja 24 horas:** caixa, geladeira e porta de vidro; abrigo atrás do balcão.
2. **Edifício Residencial 9:** elevador, porta 503/504, painel e presença; abrigo na escadaria de serviço.
3. **Última Sessão:** projetor, tela, poltrona e espectador; abrigo na cabine de projeção.
4. **Protocolo de Contenção:** câmaras, terminal e iluminação; abrigo no armário de descontaminação.

Cada ambiente possui três ocorrências, protocolos, evidências e interações próprias. A campanha repete os ambientes com identificadores de contrato e dificuldade crescente.

## 7. Roadmap e aceite

### Fundação e conteúdo — concluído por CI
- [x] Motor de campanha, dívida, pagamentos e risco exponencial.
- [x] Quatro contratos originais com três ocorrências por contrato.
- [x] Save/load, histórico e prevenção de duplicação de pagamento.
- [x] Modo terminal para investigação, rádio e manipulação de objetos.

### Renderização e interação — implementado
- [x] Fundos 16:9 e objetos separados por camada.
- [x] Editor de camadas e sincronização de áreas clicáveis.
- [x] Ficha de inspeção e variantes visuais.
- [x] Estados persistidos por objeto e contrato.

### Interface diegética — implementada
- [x] Dossiê/briefing com dívida, risco, remuneração e protocolos.
- [x] Rádio com transmissões contextualizadas.
- [x] Central CCTV de seis canais e fotografias.
- [x] Terminal CRT e relatórios de evidência.

### Horror e sobrevivência — implementado na base atual
- [x] Pressão anômala ligada às interações.
- [x] Perseguição e ataque na próxima decisão, com dano escalado.
- [x] Presença visual no ambiente e em um canal CCTV suspeito.
- [x] Flash fotográfico no canal correto interrompe a perseguição por uma decisão.
- [x] Abrigo específico por missão, com um uso por perseguição.
- [x] Áudio ambiente próprio por missão.
- [ ] Animações de entrada/saída da presença e variações visuais de perseguição.
- [ ] Mais eventos dinâmicos independentes das ocorrências principais.
- [ ] Efeitos de áudio por evento e posicionamento espacial.

### Qualidade e entrega — parcial
- [x] CI em Python 3.10, 3.11 e 3.12.
- [x] Validação de cenas, hotspots, PNGs, variantes, estados e áudio.
- [ ] Teste manual das quatro missões no Windows.
- [ ] Validação de playback e balanceamento de áudio no Windows.
- [ ] Teste de campanha longa e preparação de save de demonstração.
- [ ] Empacotamento executável.

## 8. Estados persistidos

- `between_shifts`: aguardando início do contrato.
- `on_shift`: expediente em andamento.
- `ended`: contrato encerrado por falha.
- `campaign_completed`: limite técnico da campanha atingido.

O motor valida posição da campanha, economia, evidências, estados de objetos, equipamentos, pressão anômala, perseguição e abrigo. Saves antigos são migrados para os novos campos padrão. A gravação usa arquivo temporário e substituição.

## 9. Validação automatizada

O GitHub Actions:
1. instala Pillow e CairoSVG;
2. exporta fundos, sprites e loops WAV;
3. compila os módulos e ferramentas;
4. executa a suíte unittest;
5. valida JSONs e referências de cenas.

A matriz atual usa Python 3.10, 3.11 e 3.12. O CI não substitui testes visuais e de áudio no Windows.
