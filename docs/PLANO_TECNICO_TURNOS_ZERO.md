# Plano técnico — Turnos Zero

## 1. Visão do produto

Turnos Zero substitui o Escape Room da mansão por uma antologia narrativa de horror sobrenatural. O jogador é contratado por uma agência de serviços extraordinários e recebe ordens de serviço em locais com ocorrências inexplicáveis. O foco é cumprir tarefas, interpretar protocolos, decidir sob pressão e sobreviver ao expediente.

A inspiração é o formato de episódios de trabalhos perigosos e regras anômalas. O universo, nomes, locais, personagens, diálogos, regras, eventos e criaturas são originais; não reproduzem roteiros ou elementos protegidos de outra obra.

## 2. Loop principal
1. Recrutamento: escolher nome de crachá e vínculo de trabalho.
2. Ordem de serviço: ler local, remuneração, descrição e protocolos.
3. Expediente: resolver três ocorrências por meio de escolhas.
4. Consequências: decisões corretas elevam reputação; erros reduzem estabilidade e aumentam risco.
5. Fechamento: funcionário recebe pagamento se concluir o turno; falha encerra o contrato.
6. Progressão: liberar o próximo local, acumular saldo e descobrir a história oculta da agência.

## 3. Arquitetura implementada nesta primeira etapa
- main.py: interface Tkinter e modo terminal.
- scene_manager.py: validação de catálogo de cenas e hotspots.
- assets/ambientes/*.svg: seis ilustrações vetoriais editáveis dos ambientes.
- dados/cenas.json: definição declarativa de ambientes, fundos e áreas interativas.
- turnos_zero.py: regras do jogo, catálogo de missões, dificuldades, decisões, remuneração e persistência.
- dados/turnos_zero_progresso.json: campanha nova, separada dos saves antigos.
- dados/turnos_zero_historico.json: histórico dos expedientes.
- tests/test_turnos_zero.py: testes unitários do novo motor.
- sistemas.py e arquivos antigos de progresso permanecem no repositório para referência e recuperação, mas não são importados pelo novo launcher.

## 4. Conteúdo jogável inicial
- Loja 24 horas: protocolos de luz, telefone e cliente sem reflexo.
- Edifício Residencial 9: elevador no andar zero, vizinho com guarda-chuva e apartamento inexistente.
- Última Sessão: plateia imóvel, projetor autônomo e bilhete com data futura.

Cada missão tem três ocorrências, escolhas, respostas narrativas e remuneração. O contrato define estabilidade inicial e multiplicador salarial:
- Estagiário: 5 pontos de estabilidade, pagamento padrão.
- Efetivo: 4 pontos, adicional de 25%.
- Terceirizado: 3 pontos, adicional de 60%.

Duas violações de protocolo encerram o turno. A estabilidade também pode chegar a zero.

## 5. Persistência e compatibilidade

A campanha nova utiliza arquivos próprios para não sobrescrever progresso.json e historico.json do projeto anterior. O salvamento é feito por arquivo temporário e substituição atômica. O histórico registra funcionário, missão, resultado, pagamento e data.

## 6. Próximas etapas
### Etapa A — Fundação (implementada)
- Novo título, menu e identidade textual.
- Motor de turnos e três missões jogáveis.
- Vínculos de trabalho, estabilidade, reputação e pagamento.
- Escolhas com sucesso/falha, finais de turno e histórico.
- Salvamento e retomada.
- Modo terminal com investigação de evidências e decisões.
- Testes unitários.

### Etapa B — Apresentação e atmosfera
- Catálogo declarativo de cenas e coordenadas normalizadas: implementado.
- Integração das seis artes em PNG no runtime e SVGs preservados como fontes editáveis: concluída.
- Efeitos de luz, chuva, ruído, rádio e transições.
- Animações e feedback visual para ocorrências.

### Etapa C — Sistemas de jogo
- Inventário de ferramentas, evidências e documentos.
- Regras contraditórias e verificação de autenticidade.
- Eventos dinâmicos, entidades com padrões de comportamento e encontros.
- Loja, equipamentos, reputação, dívidas e melhorias persistentes.

### Etapa D — Campanha narrativa
- Funcionários recorrentes e diálogos ramificados.
- Arquivos secretos e revelação gradual da agência.
- Mais contratos, finais alternativos e consequências entre missões.

### Etapa E — Qualidade
- Testes de interface no Windows.
- Testes de regressão de salvamento e migração.
- Ajustes de acessibilidade, escala de janela e desempenho.
- Empacotamento executável, se necessário.

## 7. Limites conhecidos da versão atual

Esta é a primeira base jogável da reconstrução, não a versão final. A arquitetura de cenas e hotspots está separada do motor. As seis artes vetoriais SVG permanecem como fontes editáveis e são exportadas para PNG no fluxo de CI. O histórico identifica cada expediente para impedir duplicação de pagamentos e registros em retomadas. O modo terminal também permite coletar evidências. Áudio direcional, entidades animadas, inventário e expansão de conteúdo continuam planejados. A interface gráfica precisa de validação manual em Windows.