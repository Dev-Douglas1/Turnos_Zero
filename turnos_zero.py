"""Turnos Zero — núcleo de campanha e missões sobrenaturais.
Python 3.10+, biblioteca padrão. Saves novos ficam separados dos saves legados.
"""
from __future__ import annotations
import json
import random
import uuid
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "dados"
SAVE = DATA / "turnos_zero_progresso.json"
HISTORY = DATA / "turnos_zero_historico.json"

MISSIONS = [
    {
        "id": "loja_24h", "title": "Loja 24 horas", "location": "Unidade 07 · Avenida Norte",
        "pay": 480, "brief": "Assuma o caixa, reponha a geladeira e mantenha a porta trancada entre 02:13 e 02:17.",
        "rules": [
            "Se o telefone tocar três vezes, não atenda.",
            "Às 02:13, apague as luzes do salão por dez segundos.",
            "Se um cliente pedir algo que não está no estoque, consulte o gerente pelo rádio.",
            "Não olhe para o corredor de bebidas depois que a música parar."
        ],
        "tasks": [
            {"prompt": "02:13. A música para. Uma pessoa está parada diante da geladeira, imóvel. O que você faz?",
             "radio_hint": "GERENTE: Não fale com a pessoa no corredor. O protocolo de 02:13 existe por um motivo.",
             "choices": ["Apagar as luzes por dez segundos", "Perguntar se precisa de ajuda", "Seguir a mensagem da geladeira e ignorar a figura"],
             "correct": 0, "evidence_ids": ["geladeira"], "evidence_choices": [2], "evidence_note": "A mensagem na geladeira confirma o protocolo: não interaja com o que aparece no corredor.", "success": "No escuro, a porta da geladeira abre e fecha sozinha. Quando a luz volta, o corredor está vazio.",
             "failure": "A pessoa vira o rosto devagar. O rádio chia com uma voz que repete seu nome."},
            {"prompt": "O telefone toca. Uma vez. Duas. Na terceira chamada, a tela mostra o seu próprio número.",
             "radio_hint": "GERENTE: A linha não está conectada à rede externa. Não existe chamada legítima neste turno.",
             "choices": ["Deixar tocar", "Atender e perguntar quem é", "Desligar a linha da parede"],
             "correct": 0, "evidence_ids": ["caixa"], "evidence_choices": [2], "evidence_note": "O registro das 02:13 liga a linha telefônica ao desaparecimento do gerente; se a chamada persistir, desconectar o aparelho é uma alternativa segura.", "success": "A chamada termina. Do outro lado do vidro, alguém segura um telefone idêntico ao seu.",
             "failure": "Uma voz sussurra do aparelho: 'Você não devia ter atendido.'"},
            {"prompt": "Um cliente sem reflexo pede um produto que não existe no estoque e aponta para a porta dos fundos.",
             "radio_hint": "GERENTE: Não existe cliente registrado. Confira o livro-caixa e não abandone o balcão.",
             "choices": ["Abrir a porta dos fundos", "Consultar o gerente pelo rádio", "Dizer que acabou e sair do caixa"],
             "correct": 1, "evidence_ids": ["caixa", "geladeira", "porta"], "evidence_note": "O livro-caixa, a mensagem da geladeira e a mão no vidro confirmam que o cliente não é uma ocorrência normal; consulte o rádio sem abandonar o balcão.", "success": "O gerente responde: 'Não existe cliente. Termine o turno. Não saia do balcão.'",
             "failure": "O rádio responde com sua própria voz, pedindo para abrir a porta."}
        ],
        "reveal": "O gerente da Unidade 07 está desaparecido há onze anos. Mesmo assim, seu rádio continua respondendo."
    },
    {
        "id": "edificio_9", "title": "Edifício Residencial 9", "location": "Bloco C · Condomínio Mirante",
        "pay": 720, "brief": "Entregue três envelopes. Não utilize o elevador depois que o painel exibir o andar 0.",
        "rules": [
            "O apartamento 504 não existe, mesmo que alguém confirme o contrário.",
            "Se encontrar um vizinho carregando um guarda-chuva dentro do prédio, não o ultrapasse.",
            "O elevador pode parar em andares que não constam no painel. Não saia.",
            "Entregue o último envelope somente quando ouvir duas batidas."
        ],
        "tasks": [
            {"prompt": "O elevador para. O painel mostra 0. As portas se abrem para um corredor que não aparece na planta.",
             "radio_hint": "MANUTENÇÃO: O andar zero não consta na planta. Não atravesse a porta do elevador.",
             "choices": ["Permanecer no elevador", "Sair e procurar a escada", "Apertar todos os andares"],
             "correct": 0, "evidence_ids": ["elevador", "painel"], "evidence_note": "O elevador e o botão 0 oculto confirmam que o painel pode abrir acesso a um andar inexistente.", "success": "As portas fecham. Algo arranha o metal do lado de fora até o elevador voltar.",
             "failure": "O corredor não tem fim. O painel do elevador desaparece atrás de você."},
            {"prompt": "Um homem com guarda-chuva bloqueia a passagem. Há água escorrendo do teto, mas o guarda-chuva está seco.",
             "radio_hint": "ZELADOR: Não ultrapasse o homem. O guarda-chuva está seco porque não pertence a este prédio.",
             "choices": ["Passar por baixo do guarda-chuva", "Esperar sem ultrapassá-lo", "Perguntar em qual apartamento mora"],
             "correct": 1, "evidence_ids": ["presenca"], "evidence_note": "O reflexo da figura se move antes do corpo; mantenha distância e não tente ultrapassá-la.", "success": "Ele se afasta quando o relógio muda de minuto. Você não ouviu passos.",
             "failure": "O homem abre o guarda-chuva. Dentro dele há um céu noturno sem estrelas."},
            {"prompt": "Uma moradora pede o envelope do 504. Atrás dela, a placa da porta diz 503.",
             "radio_hint": "PORTARIA: O apartamento 504 não está cadastrado. Não entregue correspondência sem validar o endereço.",
             "choices": ["Entregar o envelope", "Conferir o registro e recusar", "Pedir que ela assine"],
             "correct": 1, "evidence_ids": ["porta", "elevador"], "evidence_note": "A placa adulterada e o andar 0 inexistente tornam o endereço 504 suspeito; confira o registro e recuse a entrega.", "success": "O envelope fica gelado. O nome escrito nele é o seu.",
             "failure": "A porta 504 aparece na parede. Alguém gira a maçaneta por dentro."}
        ],
        "reveal": "O condomínio foi construído sobre a fundação de um prédio demolido. O 504 continua ocupado."
    },
    {
        "id": "cinema_vazio", "title": "Última Sessão", "location": "Cine Orfeu · Sala 4",
        "pay": 950, "brief": "Faça a inspeção da sala, recolha os bilhetes e desligue o projetor ao fim da sessão.",
        "rules": [
            "Nunca conte as pessoas sentadas na última fileira.",
            "Se o filme começar sem operador, não entre na cabine.",
            "Quando ouvir aplausos, permaneça de costas para a tela.",
            "Não recolha bilhetes que ainda estejam quentes."
        ],
        "tasks": [
            {"prompt": "A sessão termina, mas a plateia permanece imóvel. A tela está completamente branca.",
             "radio_hint": "OPERADOR: Quando ouvir aplausos, permaneça de costas para a tela. Não tente confirmar a origem do som.",
             "choices": ["Ficar de costas para a tela", "Virar-se para conferir a projeção", "Acender todas as luzes"],
             "correct": 0, "evidence_ids": ["tela"], "evidence_note": "As marcas pelo lado interno provam que a tela não é apenas uma superfície de projeção.", "success": "Os aplausos vêm de trás de você. Quando cessam, todas as poltronas estão vazias.",
             "failure": "A tela mostra a sala vista de trás. Na imagem, alguém está olhando diretamente para você."},
            {"prompt": "O projetor liga sozinho. Uma sombra atravessa a cabine, embora você esteja do lado de fora.",
             "radio_hint": "CABINE: Não entre enquanto o projetor estiver funcionando sem operador. Aguarde o fim da sessão.",
             "choices": ["Entrar na cabine", "Esperar a sessão terminar", "Desligar o disjuntor principal"],
             "correct": 1, "evidence_ids": ["projetor"], "evidence_choices": [2], "evidence_note": "O projetor funciona sem operador e sem alimentação; aguardar o fim da sessão ou cortar a energia pelo disjuntor evita entrar na cabine.", "success": "O filme termina sem imagem. Uma voz anuncia: 'Obrigado por permanecer até o fim.'",
             "failure": "A cabine está vazia, mas uma mão surge na janela e acena para você."},
            {"prompt": "Há bilhetes espalhados. Um deles está quente e tem seu nome, com a data de amanhã.",
             "radio_hint": "BILHETERIA: Não recolha bilhetes quentes. O assento ainda está ocupado, mesmo que pareça vazio.",
             "choices": ["Guardar o bilhete", "Não tocar no bilhete quente", "Rasgar todos os bilhetes"],
             "correct": 1, "evidence_ids": ["poltronas", "espectador"], "evidence_note": "O assento deformado e o ingresso com seu nome indicam uma armadilha pessoal; não recolha o bilhete quente.", "success": "O bilhete esfria e a tinta desaparece. O relógio do saguão volta a funcionar.",
             "failure": "A tinta se move e escreve: 'Assento reservado'. Uma poltrona range atrás de você."}
        ],
        "reveal": "O Cine Orfeu fechou há décadas. A sessão de hoje foi registrada como a primeira com público."
    },
    {
        "id": "laboratorio", "title": "Protocolo de Contenção", "location": "Subsolo 03 · Centro de Pesquisa",
        "pay": 1280, "brief": "Verifique o desligamento do laboratório, confirme o isolamento da câmara fria e encerre o expediente sem responder às chamadas internas.",
        "rules": [
            "O terminal pode exibir sessões antigas como se estivessem ativas. Não informe credenciais.",
            "Se o alarme emitir dois pulsos âmbar, acione o isolamento manual.",
            "Não abra a câmara fria depois das 03:00, mesmo que alguém peça ajuda.",
            "Toda voz no intercomunicador deve ser conferida no registro de pessoal."
        ],
        "tasks": [
            {"prompt": "O terminal informa uma sessão iniciada há onze anos. O cursor continua piscando e uma mensagem pede sua senha.",
             "radio_hint": "TÉCNICA: Desligar a tela não encerra a sessão. O corte deve ser feito no quadro externo.",
             "choices": ["Digitar a senha funcional", "Desligar o terminal pelo botão frontal", "Isolar a alimentação do terminal no quadro externo"],
             "correct": 2, "evidence_ids": ["terminal"], "evidence_choices": [1], "evidence_note": "A sessão antiga continua ativa; desligar apenas a tela não encerra a conexão. Isole a alimentação no quadro externo.", "success": "O cursor para. Por um instante, a tela exibe uma lista de funcionários — inclusive o seu nome.",
             "failure": "O terminal aceita a senha antes que você termine de digitá-la. Uma nova sessão é aberta em seu nome."},
            {"prompt": "O alarme emite dois pulsos âmbar. Há condensação se formando do lado de dentro da câmara fria.",
             "radio_hint": "CONTENÇÃO: Dois pulsos âmbar indicam falha de isolamento. Use o comando manual, não abra a câmara.",
             "choices": ["Abrir a câmara para verificar", "Acionar o isolamento manual", "Pedir instruções pelo intercomunicador"],
             "correct": 1, "evidence_ids": ["camara", "camara_vazia", "luz"], "evidence_note": "A câmara reage aos seus movimentos, os fechos estão úmidos e a luz repete o número do contrato. O protocolo exige isolamento manual.", "success": "As travas descem. Algo bate três vezes do outro lado, depois fica em silêncio.",
             "failure": "A porta abre alguns centímetros. O ar que sai tem cheiro de chuva e ozônio."},
            {"prompt": "O intercomunicador chama você pelo nome e solicita a liberação da câmara. O registro de pessoal está ao lado.",
             "radio_hint": "RECURSOS HUMANOS: A voz não autentica ninguém. Confirme a identidade no registro físico antes de liberar qualquer acesso.",
             "choices": ["Responder e confirmar a liberação", "Conferir o nome no registro antes de qualquer ação", "Seguir a voz até a câmara"],
             "correct": 1, "evidence_ids": ["camara", "camara_vazia"], "evidence_note": "Os registros físicos e as câmaras indicam que a voz não corresponde a um funcionário autorizado.", "success": "O registro não contém nenhum funcionário com seu nome. O intercomunicador desliga sozinho.",
             "failure": "A voz agradece. No monitor, seu crachá muda de ATIVO para ENCERRADO."}
        ],
        "reveal": "O Centro de Pesquisa foi interditado há onze anos. O último registro de atividade foi assinado por um funcionário que ainda não havia sido contratado."
    }
]

# Os identificadores antigos são mantidos para preservar saves existentes.
# Agora representam níveis de dificuldade, não vínculos empregatícios.
DIFFICULTIES = {
    "estagiario": {"label": "FÁCIL", "sanity": 5, "mistakes": 2, "salary": 1.0},
    "efetivo": {"label": "MÉDIO", "sanity": 4, "mistakes": 1, "salary": 1.5},
    "terceirizado": {"label": "DIFÍCIL", "sanity": 3, "mistakes": 1, "salary": 2.0},
}

TOOL_RESOURCES = {"lanterna": 100, "radio": 3, "camera": 3}

ANOMALY_THRESHOLD = 3
ANOMALY_PROFILES = {
    "loja_24h": {
        "triggers": {"caixa": 1, "porta": 2, "geladeira": 2},
        "hiding_spot": "atrás do balcão de aço",
        "alert": "O compressor para. Passos molhados se aproximam do balcão.",
        "caught": "A presença encontra você fora de cobertura. Algo segura seu ombro no escuro.",
        "evaded": "A presença passa pelo corredor e para exatamente onde você estava.",
        "documented": "O flash atravessa o corredor. A figura recua para dentro da geladeira, mas a fotografia mostra que ela não tem reflexo.",
    },
    "edificio_9": {
        "triggers": {"porta": 1, "elevador": 1, "presenca": 2, "painel": 2},
        "hiding_spot": "na escadaria de serviço, atrás da porta corta-fogo",
        "alert": "O elevador abre em algum lugar atrás de você. O indicador continua no andar 0.",
        "caught": "O elevador chega sem ruído. As portas se fecham com você no corredor.",
        "evaded": "As portas do elevador se fecham. O painel continua exibindo o andar 0.",
        "documented": "O flash ilumina o corredor inteiro. A presença desaparece do espelho do elevador, embora continue no visor da câmera.",
    },
    "cinema_vazio": {
        "triggers": {"projetor": 1, "tela": 2, "poltronas": 1, "espectador": 2},
        "hiding_spot": "na cabine de projeção, atrás da cortina acústica",
        "alert": "Os aplausos param de uma vez. Uma poltrona range na última fileira.",
        "caught": "A plateia inteira vira a cabeça na sua direção. Um assento fica reservado para você.",
        "evaded": "A sessão continua sem você. Os aplausos se afastam até desaparecer.",
        "documented": "O flash congela a plateia por um instante. A fotografia revela que todos os rostos estão voltados para a câmera.",
    },
    "laboratorio": {
        "triggers": {"camara_vazia": 1, "camara": 2, "terminal": 2, "luz": 1},
        "hiding_spot": "dentro do armário de descontaminação",
        "alert": "O sistema de contenção muda para ALERTA. Há movimento dentro das paredes.",
        "caught": "A câmara responde ao seu crachá. As travas fecham atrás de você.",
        "evaded": "O alarme volta ao modo de espera. Algo arranha a porta do armário e se afasta.",
        "documented": "O flash satura os sensores da câmara. A silhueta some do vidro e reaparece no monitor, alguns segundos atrasada.",
    },
}

def fresh_state(player: str, difficulty: str = "estagiario") -> dict:
    if difficulty not in DIFFICULTIES:
        difficulty = "estagiario"
    return {
        "schema_version": 1, "player": player, "status": "between_shifts",
        "difficulty": difficulty, "cash": -1_000_000, "initial_debt": 1_000_000,
        "contract_refused": False, "forced_contract_acceptance": False,
        "advance_payment_due": 0, "loan_shark_accepted": False,
        "reputation": 0, "shift_index": 0,
        "sanity": DIFFICULTIES[difficulty]["sanity"], "mistakes": 0, "task_index": 0,
        "completed": [], "evidence": [], "object_states": {},
        "threat_level": 0, "threat_active": False, "is_hidden": False,
        "hide_used": False, "threat_disrupted": False, "threat_triggered": [],
        "inventory": ["lanterna", "radio", "camera"],
        "tool_states": {"lanterna": True, "radio": False, "camera": False},
        "tool_resources": dict(TOOL_RESOURCES),
        "current_seed": None, "shift_token": None, "created_at": datetime.now().isoformat(timespec="seconds")
    }

class ShiftGame:
    def __init__(self, save_path: Path = SAVE, history_path: Path = HISTORY):
        self.save_path, self.history_path = Path(save_path), Path(history_path)
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        history = self._read(self.history_path, {"shifts": []})
        self.history = history if isinstance(history, dict) and isinstance(history.get("shifts"), list) else {"shifts": []}
        state = self._read(self.save_path, None)
        self.state = state if self._valid_state(state) else None
        if self.state is not None:
            migrated = False
            # Migra saves anteriores sem descartar campanhas em andamento.
            if "initial_debt" not in self.state:
                self.state["initial_debt"] = 1_000_000
                self.state["cash"] -= self.state["initial_debt"]
                migrated = True
            for key, default in (
                ("contract_refused", False),
                ("forced_contract_acceptance", False),
                ("advance_payment_due", 0),
                ("loan_shark_accepted", False),
                ("threat_level", 0),
                ("threat_active", False),
                ("is_hidden", False),
                ("hide_used", False),
                ("threat_disrupted", False),
                ("threat_triggered", []),
            ):
                if key not in self.state:
                    self.state[key] = default
                    migrated = True
            if migrated:
                self.save()

    @staticmethod
    def _valid_state(state):
        if not isinstance(state, dict):
            return False
        required = {"schema_version", "player", "status", "difficulty", "shift_index", "task_index", "cash", "sanity", "mistakes", "reputation", "completed"}
        if not required.issubset(state) or state.get("schema_version") != 1:
            return False
        if state.get("status") not in {"between_shifts", "on_shift", "ended", "campaign_completed"}:
            return False
        if state.get("difficulty") not in DIFFICULTIES:
            return False
        if type(state.get("shift_index")) is not int or not 0 <= state["shift_index"] <= 60:
            return False
        if type(state.get("task_index")) is not int or not 0 <= state["task_index"] <= 3:
            return False
        shift_index = state["shift_index"]
        task_index = state["task_index"]
        status = state["status"]
        # Estados incompatíveis com a posição da campanha não podem ser retomados.
        if status == "campaign_completed" and shift_index < len(MISSIONS):
            return False
        if status == "on_shift" and task_index >= len(MISSIONS[shift_index % len(MISSIONS)]["tasks"]):
            return False
        if status == "between_shifts" and task_index not in (0, len(MISSIONS[shift_index % len(MISSIONS)]["tasks"])):
            return False
        if status == "ended" and task_index not in range(1, len(MISSIONS[shift_index % len(MISSIONS)]["tasks"]) + 1):
            return False
        if status == "campaign_completed" and task_index != len(MISSIONS[(shift_index - 1) % len(MISSIONS)]["tasks"]):
            return False
        if not isinstance(state.get("player"), str) or not state["player"].strip() or len(state["player"]) > 24:
            return False
        if (type(state.get("cash")) is not int or
            not all(type(state.get(k)) is int and state[k] >= 0 for k in ("sanity", "mistakes", "reputation"))):
            return False
        if type(state.get("initial_debt", 1_000_000)) is not int or state.get("initial_debt", 1_000_000) <= 0:
            return False
        mission_ids = {m["id"] for m in MISSIONS}
        if not isinstance(state.get("completed"), list) or not all(isinstance(x, str) and x for x in state["completed"]):
            return False
        expected_completed = shift_index + 1 if status == "between_shifts" and task_index == 3 else shift_index
        if len(state["completed"]) != expected_completed:
            return False
        for index, completed_id in enumerate(state["completed"]):
            expected_id = MISSIONS[index % len(MISSIONS)]["id"]
            if completed_id != expected_id and completed_id != expected_id + "#contrato-" + str(index + 1):
                return False
        if not isinstance(state.get("evidence", []), list):
            return False
        object_states = state.get("object_states", {})
        if not isinstance(object_states, dict):
            return False
        if any(
            not isinstance(key, str) or not isinstance(value, str) or value not in {"0", "1"}
            for key, value in object_states.items()
        ):
            return False
        inventory = state.get("inventory", ["lanterna", "radio", "camera"])
        if (not isinstance(inventory, list) or
            any(not isinstance(item, str) or item not in {"lanterna", "radio", "camera"} for item in inventory) or
            len(inventory) != len(set(inventory))):
            return False
        if not inventory:
            return False
        tool_states = state.get("tool_states", {})
        if (not isinstance(tool_states, dict) or
            any(key not in {"lanterna", "radio", "camera"} or type(value) is not bool
                for key, value in tool_states.items())):
            return False
        tool_resources = state.get("tool_resources", TOOL_RESOURCES)
        if (not isinstance(tool_resources, dict) or
            any(key not in TOOL_RESOURCES or type(value) is not int or
                not 0 <= value <= TOOL_RESOURCES[key]
                for key, value in tool_resources.items())):
            return False
        threat_level = state.get("threat_level", 0)
        if type(threat_level) is not int or not 0 <= threat_level <= 5:
            return False
        if (type(state.get("threat_active", False)) is not bool
                or type(state.get("is_hidden", False)) is not bool
                or type(state.get("hide_used", False)) is not bool
                or type(state.get("threat_disrupted", False)) is not bool):
            return False
        triggered = state.get("threat_triggered", [])
        if (not isinstance(triggered, list) or
            any(not isinstance(item, str) or not item for item in triggered) or
            len(triggered) != len(set(triggered))):
            return False
        if state.get("is_hidden", False) and not state.get("threat_active", False):
            return False
        if state.get("hide_used", False) and not state.get("threat_active", False):
            return False
        if state.get("threat_disrupted", False) and not state.get("threat_active", False):
            return False
        if state.get("threat_disrupted", False) and not state.get("threat_active", False):
            return False
        for item in state.get("evidence", []):
            if (not isinstance(item, dict) or not isinstance(item.get("id"), str) or
                not isinstance(item.get("mission"), str) or
                not any(item["mission"] == base or item["mission"].startswith(base + "#contrato-") for base in mission_ids) or
                not isinstance(item.get("description"), str) or type(item.get("task_index")) is not int or
                item["task_index"] not in (0, 1, 2)):
                return False
        return True

    @staticmethod
    def _read(path: Path, default):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default

    def save(self):
        if self.state is None:
            raise RuntimeError("Não há campanha para salvar.")
        temp = self.save_path.with_suffix(self.save_path.suffix + ".tmp")
        temp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.save_path)

    @property
    def mission(self):
        index = self.state["shift_index"]
        base = MISSIONS[index % len(MISSIONS)]
        mission = dict(base)
        mission["scene_id"] = base["id"]
        mission["pay"] = 50 * (2 ** index)
        if index >= len(MISSIONS):
            mission["id"] = base["id"] + "#contrato-" + str(index + 1)
            mission["title"] = base["title"] + " — CONTRATO " + str(index + 1)
        return mission

    @property
    def task(self):
        return self.mission["tasks"][self.state["task_index"]]

    def start_campaign(self, player: str, difficulty: str = "estagiario"):
        self.state = fresh_state(player.strip()[:24] or "Funcionário", difficulty)
        self.save()

    def start_shift(self):
        if self.state is None:
            raise RuntimeError("Crie uma campanha antes de iniciar o turno.")
        if self.state["status"] != "between_shifts":
            raise RuntimeError("O contrato não está aguardando início de turno.")
        if self.state["shift_index"] >= 60:
            raise RuntimeError("Limite técnico de contratos atingido.")
        risk_multiplier = 2 ** self.state["shift_index"]
        self.state.update(status="on_shift", task_index=0, mistakes=0,
                          risk_multiplier=risk_multiplier,
                          sanity=DIFFICULTIES[self.state["difficulty"]]["sanity"],
                          tool_resources=dict(TOOL_RESOURCES),
                          tool_states={"lanterna": True, "radio": False, "camera": False},
                          threat_level=0, threat_active=False, is_hidden=False, hide_used=False, threat_disrupted=False, threat_triggered=[],
                          current_seed=random.randrange(1, 2**31), shift_token=uuid.uuid4().hex)
        self.save()
        return self.mission

    def act(self, choice_index: int) -> dict:
        if self.state is None or self.state["status"] != "on_shift":
            raise RuntimeError("Não há turno em andamento.")
        if type(choice_index) is not int or choice_index not in range(3):
            raise ValueError("Escolha inválida.")
        task = self.task
        collected = {
            item.get("id") for item in self.state.get("evidence", [])
            if isinstance(item, dict) and item.get("mission") == self.mission["id"]
        }
        matched_evidence = sorted(collected.intersection(task.get("evidence_ids", [])))
        evidence_used = bool(matched_evidence)
        correct = (choice_index == task["correct"] or
                   (evidence_used and choice_index in task.get("evidence_choices", [])))
        if correct:
            result = {"correct": True, "message": task["success"]}
            self.state["reputation"] += 2 if evidence_used else 1
        else:
            result = {"correct": False, "message": task["failure"]}
            risk_multiplier = self.state.get("risk_multiplier", 2 ** self.state["shift_index"])
            self.state["sanity"] = max(0, self.state["sanity"] - risk_multiplier)
            self.state["mistakes"] += 1

        # A presença ataca na decisão, a menos que o agente esteja escondido
        # ou tenha conseguido interrompê-la com um flash no canal correto.
        if self.state.get("threat_active", False):
            profile = ANOMALY_PROFILES.get(self.mission["id"], {})
            if self.state.get("is_hidden", False):
                result["threat_evaded"] = True
                result["threat_message"] = profile.get("evaded", "A presença não encontrou você.")
            elif self.state.get("threat_disrupted", False):
                result["threat_documented"] = True
                result["threat_message"] = profile.get(
                    "documented",
                    "O flash interrompe a aproximação. A presença recua por um instante."
                )
            else:
                risk_multiplier = self.state.get("risk_multiplier", 2 ** self.state["shift_index"])
                self.state["sanity"] = max(0, self.state["sanity"] - risk_multiplier)
                self.state["mistakes"] += 1
                result["threat_hit"] = True
                result["threat_message"] = profile.get("caught", "A presença encontrou você.")
            self.state["threat_active"] = False
            self.state["is_hidden"] = False
            self.state["hide_used"] = False
            self.state["threat_disrupted"] = False
            self.state["threat_level"] = max(0, self.state.get("threat_level", 0) - 2)
            result["message"] += "\n\n" + result["threat_message"]

        resources = self.state.setdefault("tool_resources", dict(TOOL_RESOURCES))
        tool_states = self.state.setdefault("tool_states", {"lanterna": True, "radio": False, "camera": False})
        if tool_states.get("lanterna", True) and resources.get("lanterna", 0) > 0:
            resources["lanterna"] = max(0, resources.get("lanterna", 0) - 35)
            if resources["lanterna"] == 0:
                tool_states["lanterna"] = False
                result["tool_warning"] = "A bateria da lanterna acabou. O ambiente ficou completamente escuro."
        result["evidence_used"] = evidence_used
        if evidence_used:
            result["evidence_note"] = task.get("evidence_note", "A investigação forneceu contexto para esta decisão.")
            result["evidence_ids"] = matched_evidence
        self.state["task_index"] += 1
        finished = self.state["task_index"] >= len(self.mission["tasks"])
        max_mistakes = DIFFICULTIES[self.state["difficulty"]]["mistakes"]
        if self.state["sanity"] <= 0 or self.state["mistakes"] >= max_mistakes:
            self._finish_shift(False)
            result["ending"] = "missing"
        elif finished:
            self._finish_shift(True)
            result["ending"] = "survived"
        self.save()
        return result

    def _finish_shift(self, survived: bool):
        mission = self.mission
        token = self.state.get("shift_token")
        if not token:
            token = f"legacy-{self.state.get('created_at', 'unknown')}-{self.state['shift_index']}"
            self.state["shift_token"] = token
        shifts = self.history.setdefault("shifts", [])
        previous = next((item for item in shifts if isinstance(item, dict) and item.get("shift_token") == token), None)
        if previous:
            outcome = previous.get("outcome", "completed" if survived else "missing")
            paid = previous.get("payment", 0)
        elif survived:
            # A diária cresce por contrato e recebe multiplicador pela dificuldade.
            base_daily = 50 * (2 ** self.state["shift_index"])
            difficulty_multiplier = DIFFICULTIES[self.state["difficulty"]]["salary"]
            paid = int(round(base_daily * difficulty_multiplier))
            advance_due = max(0, int(self.state.get("advance_payment_due", 0)))
            paid = max(0, paid - advance_due)
            self.state["cash"] += paid
            self.state["advance_payment_due"] = 0
            self.state["forced_contract_acceptance"] = False
            if mission["id"] not in self.state["completed"]:
                self.state["completed"].append(mission["id"])
            outcome = "completed"
        else:
            paid = 0
            outcome = "missing"
        self.state.update(status="between_shifts" if outcome == "completed" else "ended",
                          last_outcome=outcome, last_payment=paid,
                          last_reveal=mission["reveal"])
        if previous is None:
            shifts.append({
                "shift_token": token, "player": self.state["player"], "mission": mission["title"],
                "outcome": outcome, "payment": paid, "date": datetime.now().isoformat(timespec="seconds")
            })
            temp = self.history_path.with_suffix(self.history_path.suffix + ".tmp")
            temp.write_text(json.dumps(self.history, ensure_ascii=False, indent=2), encoding="utf-8")
            temp.replace(self.history_path)

    def next_shift(self):
        if self.state is None or self.state["status"] != "between_shifts":
            raise RuntimeError("Não é possível iniciar outro turno agora.")
        self.state["shift_index"] += 1
        self.state.update(status="between_shifts", task_index=0)
        self.save()
        return self.mission

    def record_evidence(self, evidence_id: str, description: str) -> bool:
        if self.state is None or self.state.get("status") != "on_shift":
            raise RuntimeError("Só é possível registrar evidências durante um turno.")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            raise ValueError("Identificador de evidência inválido.")
        evidence = self.state.setdefault("evidence", [])
        if any(item.get("id") == evidence_id and item.get("mission") == self.mission["id"]
               for item in evidence if isinstance(item, dict)):
            return False
        evidence.append({"id": evidence_id, "description": str(description)[:240],
                         "mission": self.mission["id"], "task_index": self.state["task_index"]})
        self.save()
        return True

    def get_tool_state(self, tool: str) -> bool:
        if self.state is None:
            return False
        if tool not in self.state.get("inventory", ["lanterna", "radio", "camera"]):
            return False
        defaults = {"lanterna": True, "radio": False, "camera": False}
        return bool(self.state.setdefault("tool_states", {}).get(tool, defaults.get(tool, False)))

    def get_tool_resource(self, tool: str) -> int:
        if tool not in TOOL_RESOURCES:
            raise ValueError("Equipamento desconhecido.")
        if self.state is None:
            return 0
        return self.state.setdefault("tool_resources", dict(TOOL_RESOURCES)).get(tool, 0)

    def toggle_tool(self, tool: str) -> bool:
        if self.state is None or self.state.get("status") != "on_shift":
            raise RuntimeError("Equipamentos só podem ser usados durante um turno.")
        if tool not in self.state.get("inventory", ["lanterna", "radio", "camera"]):
            raise ValueError("Equipamento não encontrado no inventário.")
        defaults = {"lanterna": True, "radio": False, "camera": False}
        states = self.state.setdefault("tool_states", {})
        resources = self.state.setdefault("tool_resources", dict(TOOL_RESOURCES))
        activating = not bool(states.get(tool, defaults.get(tool, False)))
        if activating and resources.get(tool, 0) <= 0:
            raise RuntimeError(f"Sem carga disponível para {tool}.")
        if activating and tool == "radio":
            resources["radio"] -= 1
        states[tool] = activating
        self.state["selected_tool"] = tool
        self.save()
        return states[tool]

    def consume_tool_resource(self, tool: str, amount: int = 1) -> int:
        if self.state is None or self.state.get("status") != "on_shift":
            raise RuntimeError("Equipamentos só podem ser usados durante um turno.")
        if tool not in TOOL_RESOURCES or type(amount) is not int or amount <= 0:
            raise ValueError("Consumo de equipamento inválido.")
        resources = self.state.setdefault("tool_resources", dict(TOOL_RESOURCES))
        if resources.get(tool, 0) < amount:
            raise RuntimeError(f"Sem carga disponível para {tool}.")
        resources[tool] -= amount
        if resources[tool] == 0:
            self.state.setdefault("tool_states", {})[tool] = False
        self.save()
        return resources[tool]

    def _object_state_key(self, object_id: str) -> str:
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError("Identificador de objeto inválido.")
        return f"{self.state['shift_index']}:{object_id}"

    def get_object_state(self, object_id: str) -> str:
        if self.state is None:
            return "0"
        key = self._object_state_key(object_id)
        return self.state.setdefault("object_states", {}).get(key, "0")

    def set_object_state(self, object_id: str, value: str) -> bool:
        if self.state is None or self.state.get("status") != "on_shift":
            raise RuntimeError("Só é possível manipular objetos durante um turno.")
        if value not in {"0", "1"}:
            raise ValueError("Estado de objeto inválido.")
        key = self._object_state_key(object_id)
        object_states = self.state.setdefault("object_states", {})
        if object_states.get(key, "0") == value:
            return False
        object_states[key] = value
        self.save()
        return True

    def interact_object(self, object_id: str, repeatable: bool = False) -> dict:
        """Manipula um objeto e atualiza a pressão anômala do contrato."""
        if self.state is None or self.state.get("status") != "on_shift":
            raise RuntimeError("Só é possível manipular objetos durante um turno.")
        if self.state.get("is_hidden", False):
            raise RuntimeError("Você está escondido. Saia do abrigo antes de manipular outro objeto.")
        if type(repeatable) is not bool:
            raise ValueError("Configuração de interação inválida.")
        profile = ANOMALY_PROFILES.get(self.mission["id"], {})
        triggers = profile.get("triggers", {})
        if object_id not in triggers:
            raise ValueError("Este objeto não possui interação de campo registrada.")

        key = self._object_state_key(object_id)
        object_states = self.state.setdefault("object_states", {})
        current = object_states.get(key, "0")
        if current == "1" and not repeatable:
            return {
                "changed": False,
                "state": current,
                "threat_level": self.state.get("threat_level", 0),
                "threat_active": self.state.get("threat_active", False),
                "activated": False,
                "message": "A interação deste objeto já foi realizada.",
            }

        next_state = "0" if current == "1" else "1"
        object_states[key] = next_state
        triggered = self.state.setdefault("threat_triggered", [])
        activated = False
        message = "O objeto mudou de estado."
        if object_id not in triggered:
            triggered.append(object_id)
            self.state["threat_level"] = min(
                5,
                self.state.get("threat_level", 0) + triggers[object_id]
            )
            if self.state["threat_level"] >= ANOMALY_THRESHOLD and not self.state.get("threat_active", False):
                self.state["threat_active"] = True
                activated = True
                message = profile.get("alert", "A presença anômala começou a se aproximar.")
            else:
                message = "Você ouviu algo se mover em uma área que deveria estar vazia."
        self.save()
        return {
            "changed": True,
            "state": next_state,
            "threat_level": self.state["threat_level"],
            "threat_active": self.state["threat_active"],
            "activated": activated,
            "message": message,
        }

    def document_anomaly(self, hotspot_id: str) -> str:
        """Usa o flash da câmera para interromper a perseguição por uma decisão."""
        if self.state is None or self.state.get("status") != "on_shift":
            raise RuntimeError("Só é possível fotografar a presença durante um turno.")
        if not self.state.get("threat_active", False):
            raise RuntimeError("Nenhuma presença está visível neste momento.")
        if not self.get_tool_state("camera") or self.get_tool_resource("camera") <= 0:
            raise RuntimeError("A câmera precisa estar armada e ter filme disponível.")
        triggered = self.state.get("threat_triggered", [])
        expected_id = triggered[-1] if triggered else None
        if hotspot_id != expected_id:
            raise ValueError("Este canal não corresponde à posição da presença.")
        self.state["threat_disrupted"] = True
        message = ANOMALY_PROFILES.get(self.mission["id"], {}).get(
            "documented",
            "O flash interrompe a aproximação. A presença recua por um instante."
        )
        self.save()
        return message

    def hide_from_anomaly(self) -> str:
        """Usa o abrigo específico do local para evitar uma aproximação ativa."""
        if self.state is None or self.state.get("status") != "on_shift":
            raise RuntimeError("Só é possível se esconder durante um turno.")
        if not self.state.get("threat_active", False):
            raise RuntimeError("Nenhuma presença está procurando você neste momento.")
        if self.state.get("is_hidden", False):
            raise RuntimeError("Você já está escondido.")
        if self.state.get("hide_used", False):
            raise RuntimeError("Você já usou o abrigo nesta perseguição.")
        spot = ANOMALY_PROFILES.get(self.mission["id"], {}).get("hiding_spot")
        if not spot:
            raise RuntimeError("Este local não possui um abrigo conhecido.")
        self.state["is_hidden"] = True
        self.state["hide_used"] = True
        self.save()
        return spot

    def leave_hiding(self) -> None:
        if self.state is None or self.state.get("status") != "on_shift":
            raise RuntimeError("Não há turno em andamento.")
        if not self.state.get("is_hidden", False):
            raise RuntimeError("Você não está escondido.")
        # A ameaça continua ativa; sair agora deixa o agente exposto à próxima ocorrência.
        self.state["is_hidden"] = False
        self.save()

    def abandon(self):
        if self.state:
            self.state["status"] = "ended"
            self.save()
