# Roteiro de apresentação — Turnos Zero

> Roteiro-base de 5 a 7 minutos. Ajustar a duração ao tempo definido pelo professor.

## 1. Abertura — 40 segundos

**Turnos Zero** é um jogo narrativo de investigação e horror sobrenatural. O jogador trabalha para uma agência fictícia que envia funcionários a locais com ocorrências anômalas. Cada contrato exige observar o ambiente, interpretar protocolos e tomar decisões sob risco.

## 2. Problema e proposta — 50 segundos

A proposta é transformar leitura de pistas e tomada de decisão em mecânicas de jogo. Em vez de apenas escolher uma resposta, o jogador pode investigar o cenário, registrar evidências e usar essas informações para justificar decisões ou desbloquear alternativas.

## 3. Tecnologias e arquitetura — 60 segundos

- **Python:** regras, progressão, persistência e lógica das missões.
- **Tkinter Canvas:** interface gráfica e interação por clique.
- **JSON:** catálogo de cenas e armazenamento local da campanha e do histórico.
- **SVG e PNG:** ilustrações editáveis e imagens carregadas pelo jogo.
- **unittest e GitHub Actions:** testes automatizados e validação contínua.

Arquivos centrais:
- `main.py`: interface gráfica e modo terminal.
- `turnos_zero.py`: motor de jogo, decisões, dificuldade, pagamentos e salvamento.
- `scene_manager.py`: validação das cenas e identificação dos hotspots.
- `dados/cenas.json`: ambientes, áreas clicáveis e evidências.

## 4. Demonstração — 2 a 3 minutos

1. Abrir o menu e criar um contrato.
2. Mostrar os três vínculos e explicar que estabilidade e tolerância a falhas variam.
3. Mostrar a dívida, o primeiro pagamento e o fator de risco.
4. Abrir a ordem de serviço e ler os protocolos.
5. Entrar na investigação da Loja 24 horas e demonstrar a lanterna, rádio e câmera.
6. Selecionar a geladeira, abrir a ficha de inspeção, examinar e manipular o objeto.
7. Mostrar a alteração visual persistente e o registro da evidência.
8. Avançar para a ocorrência e demonstrar a influência da pista na decisão.
9. Mostrar o relatório, a reputação e a consequência; se houver tempo, abrir o terminal CRT do laboratório.

**Rota reserva:** executar `python main.py --terminal` e demonstrar a investigação textual se a interface gráfica apresentar problema no computador da apresentação.

## 5. Escopo do jogo — 40 segundos

A campanha inicial possui quatro contratos:
1. Loja 24 horas.
2. Edifício Residencial 9.
3. Última Sessão.
4. Protocolo de Contenção.

Cada contrato possui três ocorrências, regras próprias e um desfecho narrativo.

## 6. Economia e progressão — 30 segundos

A dívida começa em R$ 1.000.000. O primeiro contrato paga R$ 50 e os valores dobram a cada trabalho concluído. O risco também dobra, tornando cada expediente progressivamente mais perigoso.

## 7. Qualidade e validação — 40 segundos

O projeto possui testes automatizados para progressão, salvamento, retomada, evidências, escolhas, dificuldade, pagamento, histórico e validação de cenas. O GitHub Actions compila os módulos, exporta os PNGs, executa os testes e valida os arquivos JSON.

Não apresentar o teste automatizado como substituto do teste manual da interface no Windows. Essa validação deve ser realizada no computador usado na apresentação.

## 8. Encerramento — 20 segundos

Turnos Zero demonstra a integração entre programação, interface gráfica, estruturas de dados, persistência JSON, testes e narrativa interativa. O projeto pode crescer com novos contratos, ferramentas, personagens e consequências entre missões.

---

## Checklist antes de apresentar

- [ ] Executar `python main.py` no Windows e conferir a abertura do menu.
- [ ] Testar clique em todos os hotspots dos quatro contratos.
- [ ] Testar uma decisão alternativa com e sem a evidência necessária.
- [ ] Conferir salvamento e retomada da campanha.
- [ ] Conferir resolução e escala da janela no computador da apresentação.
- [ ] Deixar o repositório e este roteiro acessíveis.
- [ ] Gravar um vídeo curto de reserva, caso a interface falhe.
- [ ] Não usar um save com campanha concluída para a demonstração inicial; preparar um save de demonstração separado.
