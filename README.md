# Turnos Zero — Agência de Serviços Extraordinários

Jogo narrativo de horror sobrenatural em Python 3.10+, com interface Tkinter e modo terminal. Você trabalha para uma agência misteriosa, recebe ordens de serviço em locais anômalos e precisa seguir protocolos para concluir cada expediente.

## Executar

No Windows, abra a pasta do projeto no VS Code e execute:

```powershell
python main.py
```

Modo terminal (com investigação de pistas por texto):

```powershell
python main.py --terminal
```

Testes:

```powershell
python -m unittest discover -s tests -v
```

Dependência gráfica para redimensionar os objetos PNG: instale com `python -m pip install -r requirements.txt`. O jogo usa Tkinter/Canvas; a exportação das artes SVG é feita pelo GitHub Actions com CairoSVG.

## Como jogar

1. Crie um contrato e informe o nome do crachá.
2. Escolha o vínculo: Estagiário (duas falhas permitidas), Efetivo ou Terceirizado (uma falha permitida).
3. Leia a ordem de serviço e os protocolos.
4. Use o cinto de equipamentos: lanterna (100% de carga, consome 35 por decisão), rádio (3 transmissões) e câmera (3 fotos); os recursos são repostos a cada contrato.
5. Investigue o ambiente clicando nos objetos; a inspeção mostra a pista e permite manipular o objeto.
6. Abra o dossiê para revisar as evidências antes de avançar.
6. As pistas ficam vinculadas ao contrato; fotografar ou examinar registra evidências que podem apoiar decisões.
7. Resolva três ocorrências escolhendo uma das três ações. Violações reduzem estabilidade conforme o risco crescente.
8. A dívida começa em R$ 1.000.000; o pagamento começa em R$ 50 e dobra em cada contrato.
9. Avance para o próximo local; o multiplicador de risco também dobra.

## Missões da primeira versão

- **Loja 24 horas:** o telefone toca, a música para e um cliente sem reflexo aparece.
- **Edifício Residencial 9:** elevador no andar zero, vizinho com guarda-chuva e apartamento inexistente.
- **Última Sessão:** uma plateia imóvel, um projetor autônomo e um bilhete com data futura.
- **Protocolo de Contenção:** um laboratório interditado, sessões persistentes e uma câmara fria sob isolamento.

## Estrutura

- main.py — interface Tkinter e modo terminal.
- turnos_zero.py — motor de jogo, missões, decisões, remuneração e salvamento.
- scene_manager.py — carregamento e validação de cenas e hotspots.
- dados/cenas.json — catálogo de ambientes e coordenadas normalizadas.
- assets/ambientes/ — fundos PNG e SVGs editáveis das missões.
- assets/objetos/ — 16 objetos PNG independentes e seus SVGs-fonte, mais cinco variantes de estado; posição, escala, ordem e visibilidade são controladas por `dados/objetos_cenas.json`.
- dados/turnos_zero_progresso.json — campanha nova.
- dados/turnos_zero_historico.json — histórico dos expedientes.
- tests/test_turnos_zero.py — testes automatizados do novo motor.
- tools/editor_cenas.py — editor visual de objetos: arrastar, redimensionar, ordenar, ocultar e substituir sprites.
- docs/PLANO_TECNICO_TURNOS_ZERO.md — arquitetura, etapas e roadmap.
- docs/ROTEIRO_APRESENTACAO.md — roteiro de demonstração e checklist para apresentação.

Os saves antigos da Mansão continuam preservados em seus arquivos originais. A nova campanha usa arquivos separados e não os sobrescreve.

## Estado do desenvolvimento

A fundação jogável está implementada: menu, criação de contrato, quatro missões com escolhas, estabilidade, falhas, reputação, pagamentos, progressão, persistência e modo terminal. A interface gráfica e o modo terminal separam a fase de investigação da fase de decisão. O histórico usa identificador único por expediente para evitar duplicação em retomadas, e o carregamento valida a estrutura do progresso antes de aceitar um save. Os seis cenários são exportados para PNG em `assets/ambientes/` e carregados pelo Tkinter; os SVGs originais permanecem versionados como fontes editáveis. `tools/export_assets.py` gera fundos em 834×315 e objetos em 512×512. O renderizador redimensiona cada sprite conforme x/y/w/h, preserva a proporção do objeto e mantém hotspots ligados aos mesmos limites. Hotspots usam coordenadas normalizadas de 0 a 1. Evidências ficam associadas à missão e só influenciam decisões compatíveis com a pista coletada.

Já existem interação e estado persistente de objetos, ficha de inspeção, cinto de ferramentas com recursos limitados e feedback sonoro de acerto/falha. Ainda estão planejados: animações, áudio ambiente por missão, ameaças com padrões de comportamento, esconderijos, recursos limitados, funcionários recorrentes, mais missões e finais. O editor visual e o jogo usam a mesma área normalizada de 834×315. A interface gráfica ainda precisa de teste manual no Windows.

## Direção de arte e referências

A direção combina inspeção tátil de documentos (*Papers, Please*), ferramentas analógicas e detector de movimento (*Alien: Isolation*), equipamento diegético (*Dead Space*) e arquitetura institucional opressiva (*Control*). As referências orientam a linguagem de interação e atmosfera; os assets e conteúdos do jogo são originais.

- Lucas Pope, [devlog de *Papers, Please* — inspect mode e documentos](https://dukope.com/devlogs/papers-please/mobile/).
- Feral Interactive, [manual de *Alien: Isolation* — lanterna, motion tracker e radial menu](https://www.feralinteractive.com/en/manuals/alienisolation/latest/steam/).
- PlayStation Blog, [ambientes e arquitetura de *Control*](https://blog.playstation.com/2019/08/08/everything-we-learned-playing-the-first-2-hours-of-control/).

## Identidade original

Turnos Zero utiliza o conceito geral de expedientes sobrenaturais e protocolos de segurança fictícios, mas possui agência, personagens, locais, textos, regras e acontecimentos próprios. Não reproduz personagens, cenas ou roteiros de outras séries.

## Edição de cenários

Execute `python tools/editor_cenas.py` para abrir o editor visual. Selecione a missão e uma camada para arrastar, ajustar x/y/largura/altura, aumentar ou diminuir, alterar a ordem, ocultar ou substituir a imagem. Os PNGs de objetos ficam em `assets/objetos/`; o manifesto `dados/objetos_cenas.json` guarda os parâmetros editáveis. Fundos exportados preservam a proporção 16:9.
