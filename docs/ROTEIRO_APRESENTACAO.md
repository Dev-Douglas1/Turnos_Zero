# Roteiro de apresentação — Turnos Zero

> Roteiro-base de 5 a 7 minutos. Ajustar ao tempo definido pelo professor.

## 1. Abertura — 40 segundos

**Turnos Zero** é um jogo 2D de investigação e horror sobrenatural. O jogador trabalha para uma agência fictícia que envia funcionários a locais com ocorrências anômalas. Cada contrato exige observar o ambiente, interpretar protocolos, manipular objetos e sobreviver à presença.

## 2. Problema e proposta — 50 segundos

A proposta é transformar observação e tomada de decisão em mecânicas. O jogador não apenas escolhe respostas: explora ambientes ilustrados, examina objetos independentes, registra evidências, consulta equipamentos e decide quando se esconder.

## 3. Tecnologias e arquitetura — 60 segundos

- **Python:** regras de jogo, progressão, ameaças e persistência.
- **Tkinter Canvas:** interface gráfica e interação por clique.
- **JSON:** catálogo de ambientes, camadas e armazenamento de campanha.
- **SVG e PNG:** fundos e objetos editáveis.
- **WAV:** paisagens sonoras originais por missão.
- **unittest e GitHub Actions:** testes automatizados em Python 3.10, 3.11 e 3.12.

Arquivos centrais:
- `main.py`: interface gráfica, terminal, CCTV e equipamentos.
- `turnos_zero.py`: economia, ocorrências, ameaças e salvamento.
- `scene_manager.py`: cenas e hotspots.
- `dados/objetos_cenas.json`: camadas, estados visuais e áreas clicáveis.

## 4. Demonstração — 2 a 3 minutos

1. Abrir o menu e criar um contrato.
2. Mostrar dívida de R$ 1.000.000, pagamento de R$ 50 e risco x1.
3. Ler o dossiê e os protocolos da Loja 24 horas.
4. Entrar na investigação e apontar os objetos independentes no cenário.
5. Examinar o balcão ou a geladeira; mostrar a ficha e a evidência.
6. Manipular um segundo objeto até a pressão anômala ativar a presença.
7. Mostrar a silhueta na borda do ambiente e abrir a central CCTV.
8. Localizar o canal suspeito, armar a câmera e fotografar a evidência.
9. Voltar ao ambiente, usar o abrigo atrás do balcão e resolver a ocorrência.
10. Mostrar a consequência da ameaça, o relatório e a recompensa.

**Rota reserva:** executar `python main.py --terminal` para demonstrar investigação textual, manipulação, rádio e abrigo se houver problema na interface gráfica.

## 5. Escopo do jogo — 40 segundos

A campanha inicial possui quatro ambientes:
1. Loja 24 horas.
2. Edifício Residencial 9.
3. Última Sessão.
4. Protocolo de Contenção.

Cada missão possui objetos e protocolos próprios, três ocorrências, evidências e um abrigo específico.

## 6. Economia e progressão — 30 segundos

A dívida começa em R$ 1.000.000. O primeiro contrato paga R$ 50; os valores dobram a cada trabalho concluído. O risco também dobra, tornando cada expediente progressivamente mais perigoso.

## 7. Qualidade e validação — 40 segundos

O projeto possui testes automatizados para progressão, salvamento, retomada, evidências, equipamentos, pressão anômala, abrigo e referências das cenas. O GitHub Actions exporta as artes, compila os módulos e executa a suíte em três versões do Python.

Não apresentar o CI como substituto de teste manual da interface e do áudio no Windows. Essa validação deve ser feita no computador da apresentação.

## 8. Encerramento — 20 segundos

Turnos Zero integra programação, interface gráfica, estruturas de dados, persistência JSON, edição de assets, testes e narrativa interativa. O projeto pode crescer com novos contratos, eventos ambientais, funcionários recorrentes e finais alternativos.

---

## Checklist antes de apresentar

- [ ] Executar `python main.py` no Windows e conferir o menu.
- [ ] Conferir os fundos 16:9 e os objetos clicáveis nas quatro missões.
- [ ] Testar exame e manipulação de objetos.
- [ ] Testar ativação da presença, CCTV e uso único do abrigo.
- [ ] Testar lanterna, rádio, câmera e reprodução de áudio.
- [ ] Conferir salvamento e retomada da campanha.
- [ ] Preparar um save de demonstração separado.
- [ ] Gravar um vídeo curto de reserva.
