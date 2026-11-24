# Turnos Zero — Agência de Serviços Extraordinários

Jogo narrativo de horror sobrenatural em Python 3.10+, com interface Tkinter e modo terminal. Você trabalha para uma agência misteriosa, recebe ordens de serviço em locais anômalos e precisa seguir protocolos para concluir cada expediente.

## Executar

No Windows, abra a pasta do projeto no VS Code e execute:

```powershell
python main.py
```

Modo terminal:

```powershell
python main.py --terminal
```

Testes:

```powershell
python -m unittest discover -s tests -v
```

Não são necessárias bibliotecas externas. A interface usa Canvas do Tkinter e o motor usa apenas a biblioteca padrão do Python.

## Como jogar

1. Crie um contrato e informe o nome do crachá.
2. Escolha o vínculo: Estagiário, Efetivo ou Terceirizado.
3. Leia a ordem de serviço e os protocolos.
4. Em cada expediente, resolva três ocorrências escolhendo uma das três ações.
5. Decisões corretas aumentam reputação. Violações reduzem estabilidade.
6. Duas violações ou estabilidade zerada encerram o contrato. Sobreviver gera pagamento.
7. Avance para o próximo local e descubra a história da agência.

## Missões da primeira versão

- **Loja 24 horas:** o telefone toca, a música para e um cliente sem reflexo aparece.
- **Edifício Residencial 9:** elevador no andar zero, vizinho com guarda-chuva e apartamento inexistente.
- **Última Sessão:** uma plateia imóvel, um projetor autônomo e um bilhete com data futura.

## Estrutura

- main.py — interface Tkinter e modo terminal.
- turnos_zero.py — motor de jogo, missões, decisões, remuneração e salvamento.
- scene_manager.py — carregamento e validação de cenas e hotspots.
- dados/cenas.json — catálogo de ambientes e coordenadas normalizadas.
- assets/ambientes/ — seis cenários PNG renderizados para o jogo; os SVGs originais permanecem como fontes editáveis.
- dados/turnos_zero_progresso.json — campanha nova.
- dados/turnos_zero_historico.json — histórico dos expedientes.
- tests/test_turnos_zero.py — testes automatizados do novo motor.
- docs/PLANO_TECNICO_TURNOS_ZERO.md — arquitetura, etapas e roadmap.

Os saves antigos da Mansão continuam preservados em seus arquivos originais. A nova campanha usa arquivos separados e não os sobrescreve.

## Estado do desenvolvimento

A fundação jogável está implementada: menu, criação de contrato, três missões com escolhas, estabilidade, falhas, reputação, pagamentos, progressão, persistência e modo terminal. A interface usa um catálogo declarativo de cenas e hotspots. Os seis cenários são exportados para PNG em `assets/ambientes/` e renderizados diretamente pelo Tkinter. Os SVGs originais permanecem versionados como fontes editáveis; `tools/export_assets.py` gera os PNGs em 834×315 pixels para encaixe na área de jogo. Hotspots usam coordenadas normalizadas de 0 a 1.

Ainda estão planejados: renderização direta dos SVGs ou exportação PNG otimizada, animações, áudio ambiente e rádio, inventário de ferramentas, entidades com padrões de comportamento, economia expandida, funcionários recorrentes, mais missões e finais. A interface gráfica precisa de teste manual no Windows.

## Identidade original

Turnos Zero utiliza o conceito geral de expedientes sobrenaturais e protocolos de segurança fictícios, mas possui agência, personagens, locais, textos, regras e acontecimentos próprios. Não reproduz personagens, cenas ou roteiros de outras séries.