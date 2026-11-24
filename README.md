# Turnos Zero — Agência de Serviços Extraordinários

**Turnos Zero** é um jogo 2D de horror sobrenatural e sobrevivência burocrática. Você é um funcionário de uma agência que envia trabalhadores temporários para locais anômalos. O objetivo é cumprir contratos perigosos, sobreviver e quitar uma dívida inicial de **R$ 1.000.000**.

A direção mistura dossiês e inspeção tátil (*Papers, Please*), tecnologia analógica (*Alien: Isolation*), equipamento diegético (*Dead Space*) e arquitetura institucional opressiva (*Control*). As referências orientam a linguagem visual e de interação; a agência, os locais, personagens, textos e acontecimentos são originais.

## Requisitos e execução

- Python 3.10 ou superior.
- Tkinter (incluído na distribuição padrão do Python para Windows).
- Pillow, instalado por meio de `requirements.txt`.

Na pasta do projeto:

```powershell
python -m pip install -r requirements.txt
python main.py
```

Modo terminal:

```powershell
python main.py --terminal
```

Testes automatizados:

```powershell
python -m unittest discover -s tests -v
```

Para editar e exportar as fontes SVG localmente, instale também CairoSVG e execute o exportador:

```powershell
python -m pip install cairosvg
python tools/export_assets.py
```

O exportador cria os fundos PNG, sprites PNG e loops de áudio por missão. O GitHub Actions executa esse processo automaticamente e publica os arquivos gerados.

## Como jogar

1. Crie o crachá e escolha o vínculo: Estagiário, Efetivo ou Terceirizado.
2. Leia a ordem de serviço, o risco, o pagamento e os protocolos.
3. Inicie o expediente e explore o ambiente.
4. Clique nos objetos para examinar e manipular. Examiná-los registra pistas; manipulá-los altera seu estado visual e pode atrair a presença.
5. Consulte o rádio para receber uma orientação contextual, use a câmera para registrar evidências e administre a bateria da lanterna.
6. Abra o CFTV de seis canais. Quando uma presença está ativa, um dos feeds pode revelar sua posição.
7. Ao atingir o limite de pressão anômala, a presença começa a caçar o agente. Use o abrigo específico do local antes da próxima decisão. O abrigo pode ser usado uma vez por perseguição.
8. Resolva as três ocorrências. Evidências compatíveis podem fundamentar decisões alternativas e elevar a reputação.
9. Sobreviva para receber o pagamento e avançar ao próximo contrato.

## Economia e dificuldade

- Dívida inicial: **R$ 1.000.000**.
- Primeiro pagamento: **R$ 50**.
- Pagamento dobra a cada contrato: **R$ 50, R$ 100, R$ 200, R$ 400, R$ 800...**.
- O multiplicador de risco também dobra: **x1, x2, x4, x8, x16...**.
- A estabilidade depende do vínculo. Violações e ataques da presença reduzem a estabilidade conforme o risco atual.
- A campanha percorre ciclos dos quatro ambientes e eleva remuneração e risco até o limite técnico definido no motor.

## Missões disponíveis

- **Loja 24 horas:** caixa, porta de vidro, geladeira e protocolo de 02:13.
- **Edifício Residencial 9:** elevador no andar zero, presença no corredor e apartamento 504.
- **Última Sessão:** projetor, tela de projeção, poltronas e espectador.
- **Protocolo de Contenção:** câmaras experimentais, terminal com sessão persistente e luz de emergência.

Cada missão possui objetos manipuláveis, pistas, três ocorrências e um abrigo específico.

## Sistemas implementados

### Ambientes e objetos
- Quatro ambientes de missão, com fundos 16:9 (834×469).
- 16 objetos independentes em PNG 512×512, com 15 variantes visuais para estados alterados.
- Cada camada usa posição, tamanho, profundidade e visibilidade editáveis.
- Os hotspots acompanham os limites do objeto, inclusive depois de editar e salvar no editor visual.
- Os fundos contêm arquitetura e atmosfera; os equipamentos e objetos interativos são camadas separadas.

### Investigação e sobrevivência
- Ficha de inspeção individual por objeto.
- Evidências vinculadas ao contrato e ao ponto investigado.
- Estados persistentes de objetos e variantes visuais.
- Pressão anômala acumulada pelas interações. Ao atingir o limite, a presença inicia uma perseguição.
- A presença aparece no limite do campo visual e pode ser identificada pelo CFTV.
- Se o agente avançar exposto, a presença causa dano adicional proporcional ao risco.
- Cada perseguição permite um único uso do abrigo; sair dele deixa o agente exposto até a ameaça ser resolvida.

### Equipamentos
- **Lanterna:** 100% de bateria inicial, consome 35 pontos por decisão enquanto ligada. Quando acaba ou é desligada, o ambiente escurece.
- **Rádio:** três transmissões por contrato, com orientação contextual para cada ocorrência.
- **Câmera:** três fotos por contrato. O modo CFTV apresenta seis canais e permite registrar evidências.
- Os recursos são repostos no início de cada contrato.
- Os estados de equipamentos e objetos são salvos no progresso.

### Áudio
- Quatro paisagens sonoras originais de 10 segundos, uma por missão, em loop.
- Efeitos curtos de interação, evidência, acerto e violação.
- Os arquivos WAV são validados no CI como mono, 16-bit e 22.050 Hz. A reprodução de áudio no Windows usa `winsound`; em plataformas sem suporte, o jogo usa o beep do Tk como fallback para os efeitos.

## Estrutura do projeto

- `main.py` — interface Tkinter Canvas, modo terminal, inspeção, CFTV, rádio e equipamentos.
- `turnos_zero.py` — motor de campanha, economia, ocorrências, evidências, pressão anômala, abrigos e salvamento.
- `scene_manager.py` — catálogo e validação de cenas, coordenadas e hotspots.
- `dados/cenas.json` — fundos e hotspots de fallback.
- `dados/objetos_cenas.json` — manifesto de camadas, estados visuais e áreas clicáveis.
- `assets/ambientes/` — seis fundos SVG e PNG.
- `assets/objetos/` — 16 sprites-base e 15 variantes de estado, em SVG e PNG.
- `assets/som/` — quatro loops de áudio ambiente.
- `tools/editor_cenas.py` — editor visual de objetos.
- `tools/export_assets.py` — exportador de fundos, sprites e áudio.
- `tools/generate_audio.py` — gerador de loops WAV com a biblioteca padrão.
- `tests/` — testes de motor, economia, campanhas, cenas, objetos, equipamentos, perseguição e áudio.

Os saves antigos do projeto Mansão permanecem separados. A nova campanha usa `dados/turnos_zero_progresso.json` e `dados/turnos_zero_historico.json`.

## Editor visual de cenários

Execute:

```powershell
python tools/editor_cenas.py
```

No editor, escolha uma missão e uma camada para:
- arrastar e ajustar posição;
- redimensionar por arrasto ou por valores numéricos;
- alterar a ordem de desenho;
- ocultar ou mostrar o objeto;
- substituir o PNG;
- salvar o manifesto e sincronizar a área clicável.

Os valores de `x`, `y`, `w` e `h` são normalizados entre 0 e 1.

## Qualidade e validação

O GitHub Actions executa a matriz de testes em Python 3.10, 3.11 e 3.12. O fluxo compila os módulos, exporta as imagens, executa os testes e valida JSONs, sprites, fundos e áudio.

**Limite de validação:** os testes automatizados e a exportação passam no CI, mas a renderização final e a experiência de áudio ainda precisam ser conferidas manualmente no Windows. O CI não substitui esse teste visual.

## Referências de direção de arte

- Lucas Pope — [devlog de *Papers, Please*: inspeção e documentos](https://dukope.com/devlogs/papers-please/mobile/).
- Feral Interactive — [manual de *Alien: Isolation*: lanterna e motion tracker](https://www.feralinteractive.com/en/manuals/alienisolation/latest/steam/).
- PlayStation Blog — [ambientes e arquitetura de *Control*](https://blog.playstation.com/2019/08/08/everything-we-learned-playing-the-first-2-hours-of-control/).

Turnos Zero utiliza conceitos gerais de horror burocrático e equipamentos analógicos, sem reproduzir personagens, cenas, textos ou roteiros das obras de referência.
