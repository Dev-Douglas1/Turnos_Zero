# Plano técnico integrado de inovação — O Último Segredo da Mansão

**Versão do plano:** 1.0  
**Data:** 17/11/2026  
**Escopo escolhido:** experiência integrada (investigação + mecanismos + narrativa + exploração), dificuldade selecionável e atmosfera híbrida de mistério psicológico, investigação criminal e terror sobrenatural.

> Este documento é um plano de evolução incremental. Não altera nem substitui os arquivos atuais de progresso, histórico ou enigmas. A implementação deve ocorrer em etapas pequenas, com cópias de segurança e testes de compatibilidade antes de qualquer migração.

## 1. Estado atual do projeto

O repositório já possui uma base funcional que deve ser preservada:

- Python com Tkinter e interface point-and-click.
- Cinco salas configuradas em `dados/enigmas.json`: hall, biblioteca, escritório, porão e câmara secreta.
- Objetos investigáveis, inventário, itens requeridos, códigos e transições entre salas.
- Motor de campanha em `Motor.gerar_campanha()`, que já sorteia ano, suspeito, crime, selo, frase, códigos e alguns tipos de mecanismo.
- Salvamento de progresso em `dados/progresso.json` e histórico em `dados/historico.json`.
- Dicas, lente de investigação, cronômetro, penalidade por erro, alerta e conquistas.
- Modo de terminal para demonstrar `input()`, `while`, `for` e condicionais.

### Limitações identificadas na leitura do código atual

1. A campanha procedural altera principalmente dados narrativos e combinações. Ainda não escolhe uma estrutura de caso com cadeia de evidências e solução alternativa completa.
2. A lista `tipos` é sorteada na campanha, mas o plano precisa garantir que cada tipo selecionado tenha um controlador de puzzle correspondente e que a solução seja comunicada por pistas coerentes.
3. A dificuldade não é selecionável na interface nem está registrada de forma padronizada no estado salvo.
4. A progressão entre salas ainda é majoritariamente linear; os objetos e transições são definidos diretamente no JSON.
5. O inventário registra itens, mas ainda não existe um quadro de evidências com relações verificáveis entre documentos, pessoas, horários e eventos.
6. O terror e a reação da mansão ainda não são dirigidos por um sistema único de eventos e consequências.

Essas limitações definem o trabalho futuro. Não se deve reescrever o jogo inteiro para resolvê-las.

## 2. Pilares de design

### 2.1 Uma investigação, não apenas uma sequência de senhas

Cada campanha deve conter:
- Um incidente central e uma pergunta dramática.
- Pessoas envolvidas, motivos e relações.
- Evidências físicas, documentos e testemunhos.
- Uma linha do tempo com fatos confirmados e contradições.
- Uma hipótese verdadeira e pistas suficientes para deduzi-la.
- Um conjunto de finais condicionado às evidências e às decisões.

### 2.2 Mecanismos táteis em 2D

Criar puzzles visuais próprios, inspirados na satisfação de manipular mecanismos de jogos de caixas de enigmas, sem copiar conteúdo protegido:
- Discos e mostradores rotativos.
- Engrenagens que precisam ser alinhadas.
- Placas deslizantes.
- Fechaduras de símbolos.
- Sequências sonoras.
- Objetos com compartimentos em etapas.

Cada puzzle deve ter estado próprio, feedback de interação, condição de solução, pista gradual e persistência. Não usar apenas uma caixa de texto para simular manipulação.

### 2.3 Atmosfera híbrida

A narrativa mistura três camadas que se reforçam:
- **Investigação criminal:** documentos, cronologia, álibis e contradições.
- **Mistério psicológico:** memória duvidosa, testemunhos ambíguos e percepção.
- **Terror sobrenatural:** eventos ambientais estranhos, sons, sombras e mudanças sutis.

Regra narrativa: o sobrenatural não deve invalidar a lógica do mistério. O jogador sempre pode reunir evidências e formular uma interpretação, mesmo quando a explicação final permanece ambígua.

## 3. Arquitetura proposta

Manter `main.py` executável durante a transição, mas separar responsabilidades em módulos gradualmente:

```text
main.py                    # ponto de entrada e compatibilidade atual
motor/
  campanha.py              # geração determinística de casos
  dificuldade.py           # perfis e parâmetros de dificuldade
  investigacao.py          # evidências, relações e hipóteses
  puzzles.py               # tipos de mecanismos e validação
  eventos.py               # eventos da mansão e consequências
  persistencia.py          # leitura, gravação, backup e migração
interface/
  telas.py                 # navegação e composição das telas
  notificacoes.py          # mensagens internas do jogo
  mecanismos.py            # controles visuais dos puzzles
  quadro_evidencias.py     # painel de investigação
dados/
  enigmas.json             # conteúdo-base das salas (manter compatível)
  progresso.json           # partida em andamento (manter compatível)
  historico.json           # partidas finalizadas (manter compatível)
  casos/                   # novos modelos de casos, adicionados gradualmente
  schemas/                 # versões documentadas dos formatos de save
tests/
  test_migracao.py
  test_campanha.py
  test_dificuldade.py
  test_puzzles.py
  test_investigacao.py
  test_persistencia.py
```

A separação é incremental: primeiro extrair funções puras do motor; depois mover a interface. Não fazer uma migração de todos os módulos em um único commit.

## 4. Dificuldade selecionável

Adicionar uma tela antes da criação da partida. A seleção deve ser gravada em `progresso.json` e permanecer igual ao retomar.

| Perfil | Tempo inicial | Penalidade por erro | Custo da dica | Tentativas por mecanismo | Assistência |
|---|---:|---:|---:|---:|---|
| História | 45 min | 0–15 s | 30 s | 5 | Pistas mais explícitas; sem bloqueio permanente |
| Investigador | 30 min | 60 s | 90 s | 3 | Equilíbrio entre dedução e pressão |
| Pesadelo | 25 min | 90 s | 120 s | 2 | Pistas indiretas, eventos mais intensos |

Os valores são parâmetros iniciais para playtest, não números definitivos. A dificuldade deve alterar pressão, quantidade de ajuda e tolerância a erros; não deve tornar uma solução logicamente impossível.

Implementação:
- Criar `PERFIS_DIFICULDADE` em módulo próprio.
- Guardar `dificuldade` e `config_dificuldade_snapshot` na partida.
- O snapshot impede que uma atualização futura altere o equilíbrio de uma campanha já iniciada.
- Para saves antigos sem dificuldade, atribuir `investigador` como padrão.
- Não recalcular tempo de uma partida antiga durante a migração.

## 5. Geração procedural de campanhas realmente diferentes

A geração deve usar uma semente por campanha e guardar todos os resultados. A mesma semente deve reproduzir exatamente o mesmo caso.

Estrutura conceitual de `campanha`:

```json
{
  "schema_version": 2,
  "seed": 123456,
  "caso_id": "desaparecimento_herdeira",
  "incidente": "desaparecimento",
  "vitima": "Helena Valença",
  "suspeitos": [],
  "motivos": [],
  "linha_tempo": [],
  "evidencias": [],
  "relacoes": [],
  "solucao_verdadeira": {},
  "puzzles": {},
  "eventos": []
}
```

A geração deve escolher um modelo de caso validado, e não combinar livremente qualquer frase com qualquer senha. Cada modelo define:
1. Personagens e relações possíveis.
2. Incidente e motivo.
3. Evidências obrigatórias e evidências opcionais.
4. Uma solução verdadeira.
5. Distratores plausíveis, mas refutáveis.
6. Puzzles que liberam evidências em ordem coerente.
7. Uma cadeia de dependências sem bloqueios impossíveis.

Primeiro conjunto de modelos:
- O desaparecimento da herdeira.
- A falsificação do testamento.
- O incêndio encoberto.
- O falso médico da família.
- A identidade trocada no retrato.

Variação adicional entre partidas:
- Ordem e posição dos objetos examináveis.
- Tipos de mecanismo compatíveis com a sala.
- Pistas ambientais e documentos alternativos.
- Eventos da mansão e momentos em que ocorrem.
- Rotas opcionais e evidências raras.

**Critério de qualidade:** cada campanha gerada deve passar por uma validação automática de alcançabilidade: todos os itens necessários para terminar devem poder ser obtidos, não pode haver dependência circular e a solução verdadeira deve ser dedutível pelas evidências disponíveis.

## 6. Sistema de investigação e quadro de evidências

Adicionar uma tela acessível durante a exploração:
- Coluna de evidências encontradas.
- Pessoas e locais citados.
- Linha do tempo.
- Área para relacionar duas evidências.
- Indicador de hipótese confirmada, refutada ou ainda inconclusiva.

Tipos de evidência:
- `documento`, `objeto`, `testemunho`, `registro_sonoro`, `observacao`.

Cada evidência deve ter ID estável, descrição, origem, entidades relacionadas e fatos que sustenta ou contradiz. Não marcar uma hipótese como verdadeira apenas porque o jogador clicou em dois cartões: validar relações no motor.

O jogador pode terminar com:
- Conclusão correta sustentada por evidências.
- Conclusão incompleta, mas plausível.
- Acusação errada.
- Fuga sem acusação.

## 7. Sistema de puzzles mecânicos

Criar uma interface por tipo de mecanismo com contrato comum:

- `iniciar(estado_salvo, contexto_campanha)`
- `interagir(acao)`
- `verificar()`
- `obter_estado()`
- `pista(nivel)`

Tipos planejados:
1. Discos rotativos: alinhar símbolos, números ou horários.
2. Engrenagens: transmitir movimento e alinhar marcas.
3. Placas deslizantes: organizar um padrão com movimentos limitados.
4. Fechadura de símbolos: selecionar sequência com base em evidências.
5. Puzzle sonoro: repetir ou interpretar uma sequência de tons.
6. Compartimento em camadas: descobrir travas ocultas em um objeto.

A campanha escolhe somente mecanismos que tenham arte, controlador e pistas disponíveis. Guardar o progresso parcial de cada mecanismo no save. A interface deve oferecer feedback visual e sonoro sem abrir diálogos nativos do sistema operacional.

## 8. A mansão como sistema reativo

Criar um controlador de eventos com condições explícitas, por exemplo:

- `evidencia_encontrada`
- `puzzle_resolvido`
- `alerta_atingiu`
- `tempo_abaixo_de`
- `sala_visitada`
- `objeto_removido`
- `hipotese_formulada`

Cada evento pode acionar mudanças de ambiente, áudio, texto, luzes, aparições breves ou alterações em objetos. Eventos devem ser determinísticos dentro da mesma campanha e não podem destruir pistas essenciais.

Criar um nível de tensão separado do contador de erros:
- `tensao`: controla intensidade atmosférica.
- `alerta`: registra erros e consequências de gameplay.

Isso evita confundir sustos e eventos narrativos com punições.

## 9. Finais e consequências

Finais não devem depender apenas de possuir dois itens. Considerar:
- Evidências reunidas.
- Hipótese escolhida.
- Pessoa acusada.
- Decisões durante a campanha.
- Sobrevivência e tempo restante.
- Eventos que o jogador provocou ou evitou.

Finais iniciais:
1. Fuga: escapar sem concluir o caso.
2. Verdade comprovada: revelar a conspiração com evidências suficientes.
3. Acusação precipitada: apontar o suspeito errado.
4. Pacto: aceitar uma proposta ligada à mansão.
5. Desaparecimento: falhar em escapar.
6. Final secreto: reunir evidências raras e descobrir a origem do fenômeno.

Os finais existentes `Fuga`, `Verdade revelada` e `Capturado pela mansão` devem continuar reconhecidos pelo histórico antigo.

## 10. Persistência e preservação dos dados existentes

Arquivos atuais que não podem ser apagados nem sobrescritos em lote:
- `dados/enigmas.json`
- `dados/progresso.json`
- `dados/historico.json`

Política obrigatória:
1. Fazer cópia de segurança datada antes de qualquer migração.
2. Nunca substituir o histórico existente por uma lista vazia.
3. Migrar dados em memória e gravar somente após validação.
4. Usar gravação atômica em arquivo temporário, como o projeto já faz.
5. Manter leitura de saves antigos sem campos novos.
6. Adicionar `schema_version` para identificar formatos.
7. Manter IDs atuais de salas e objetos (`hall`, `biblioteca`, `escritorio`, `porao`, `camara); não renomear IDs usados em saves.
8. Se um campo opcional estiver ausente, preencher com padrão seguro sem descartar os demais dados.
9. Não mudar os códigos ou a campanha de uma partida já iniciada.
10. Manter um teste de ida e volta: carregar save antigo, migrar, salvar, reabrir e comparar jogador, sala, inventário, vistos, resolvidos, tentativas, dicas, tempo e histórico.

Migração planejada:
- Save sem `schema_version` → versão 1 legada.
- Versão 1 → versão 2 adiciona dificuldade, seed e estado de investigação com valores padrão.
- Versão 2 → futuras versões somente com migrações explícitas e testadas.

## 11. Plano de execução em fases

### Fase 0 — Segurança e linha de base
- Criar cópias dos três JSON atuais.
- Registrar commit de referência.
- Criar testes para o fluxo atual de cinco salas, códigos, inventário, finais e modo terminal.
- Confirmar que uma partida salva pode ser retomada.

**Entrega:** baseline reproduzível e testes de regressão.

### Fase 1 — Dificuldade e persistência versionada
- Adicionar escolha História / Investigador / Pesadelo.
- Guardar dificuldade e snapshot de parâmetros.
- Migrar saves antigos sem perder progresso.
- Testar início, salvamento, retomada e histórico.

**Entrega:** dificuldade selecionável sem alterar a estrutura das salas.

### Fase 2 — Motor procedural por modelos de caso
- Introduzir seed e modelos de caso.
- Gerar personagens, cronologia, evidências, códigos e pistas coerentes.
- Validar alcançabilidade de cada campanha.
- Preservar campanhas em andamento.

**Entrega:** partidas distintas e reproduzíveis.

### Fase 3 — Quadro de investigação
- Adicionar evidências com IDs estáveis.
- Criar painel e relações entre evidências.
- Implementar hipóteses e validação pelo motor.
- Integrar conquistas de investigação.

**Entrega:** investigação dedutiva além de encontrar senhas.

### Fase 4 — Puzzles mecânicos
- Implementar primeiro discos rotativos e placas deslizantes.
- Integrar os mecanismos aos objetos atuais.
- Persistir estado parcial.
- Acrescentar engrenagens, símbolos e áudio em iterações seguintes.

**Entrega:** interação visual real e reutilizável.

### Fase 5 — Mansão reativa e áudio
- Implementar eventos condicionais.
- Separar tensão de alerta.
- Adicionar variações de iluminação, som e aparições.
- Garantir que eventos não bloqueiem a progressão.

**Entrega:** ambiente responsivo às ações do jogador.

### Fase 6 — Narrativa ramificada, finais e balanceamento
- Ligar evidências, hipóteses e decisões aos finais.
- Criar finais alternativos.
- Balancear os três níveis com testes e sessões de jogo.
- Revisar textos, acessibilidade, feedback e tutorial.

**Entrega:** campanha completa, rejogável e testada.

## 12. Testes obrigatórios

### Testes unitários
- Mesma seed gera o mesmo caso.
- Seeds diferentes produzem variações válidas.
- Códigos e pistas sempre correspondem.
- Cada puzzle aceita solução correta e rejeita solução incorreta.
- Cada dificuldade aplica seus próprios parâmetros.
- Eventos não repetem indevidamente nem removem evidências essenciais.

### Testes de integração
- Nova partida → escolher dificuldade → jogar → salvar → fechar → continuar.
- Completar cada puzzle e avançar por todas as salas.
- Obter evidências em ordem alternativa.
- Terminar por fuga, verdade, acusação errada e falha.
- Rodar modo gráfico e modo `--terminal`.

### Testes de compatibilidade
- Abrir o `progresso.json` atual sem campos novos.
- Preservar `historico.json` com todas as partidas anteriores.
- Preservar os IDs e conteúdos atuais de `enigmas.json`.
- Simular JSON incompleto ou corrompido sem apagar o arquivo original.
- Confirmar que os assets ausentes geram fallback legível.

### Critérios para considerar uma fase concluída
- Testes automatizados aprovados.
- Nenhum dado antigo perdido.
- Uma partida antiga continua carregando.
- Nova partida funciona em todos os níveis de dificuldade.
- O jogador consegue terminar a campanha sem softlock.
- A interface não abre caixas de diálogo nativas para ações comuns.

## 13. Regras de trabalho e commits

- Uma fase por branch/commit lógico.
- Não misturar refatoração, arte e mudanças de balanceamento no mesmo commit.
- Não substituir os JSON de produção por arquivos de exemplo.
- Não declarar teste visual como aprovado sem executar a interface.
- Antes de cada migração: backup, teste, diff e validação dos JSON.
- Manter `python main.py --terminal` funcionando para a apresentação escolar.

## 14. Primeira entrega recomendada

Começar pela **Fase 0 + Fase 1**. É a fundação de segurança para todas as funcionalidades seguintes: preserva os dados atuais, adiciona dificuldade selecionável e cria testes que impedem regressões. Só depois introduzir os modelos de caso procedural mais complexos.

---

**Decisão de produto consolidada:** O Último Segredo da Mansão será um Escape Room point-and-click 2D de investigação, com campanhas procedurais reproduzíveis, puzzles mecânicos, dedução por evidências, dificuldade selecionável e uma mansão que reage às decisões. A atmosfera combina conspiração familiar, tensão psicológica e fenômenos sobrenaturais, mantendo sempre pistas lógicas para o jogador resolver o caso.
