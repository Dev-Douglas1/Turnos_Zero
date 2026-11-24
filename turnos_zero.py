"""Turnos Zero — núcleo de campanha e missões sobrenaturais.
Python 3.10+, biblioteca padrão. Saves novos ficam separados dos saves legados.
"""
from __future__ import annotations
import json
import random
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
             "choices": ["Apagar as luzes por dez segundos", "Perguntar se precisa de ajuda", "Ligar para a polícia"],
             "correct": 0, "success": "No escuro, a porta da geladeira abre e fecha sozinha. Quando a luz volta, o corredor está vazio.",
             "failure": "A pessoa vira o rosto devagar. O rádio chia com uma voz que repete seu nome."},
            {"prompt": "O telefone toca. Uma vez. Duas. Na terceira chamada, a tela mostra o seu próprio número.",
             "choices": ["Deixar tocar", "Atender e perguntar quem é", "Desligar a linha da parede"],
             "correct": 0, "success": "A chamada termina. Do outro lado do vidro, alguém segura um telefone idêntico ao seu.",
             "failure": "Uma voz sussurra do aparelho: 'Você não devia ter atendido.'"},
            {"prompt": "Um cliente sem reflexo pede um produto que não existe no estoque e aponta para a porta dos fundos.",
             "choices": ["Abrir a porta dos fundos", "Consultar o gerente pelo rádio", "Dizer que acabou e sair do caixa"],
             "correct": 1, "success": "O gerente responde: 'Não existe cliente. Termine o turno. Não saia do balcão.'",
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
             "choices": ["Permanecer no elevador", "Sair e procurar a escada", "Apertar todos os andares"],
             "correct": 0, "success": "As portas fecham. Algo arranha o metal do lado de fora até o elevador voltar.",
             "failure": "O corredor não tem fim. O painel do elevador desaparece atrás de você."},
            {"prompt": "Um homem com guarda-chuva bloqueia a passagem. Há água escorrendo do teto, mas o guarda-chuva está seco.",
             "choices": ["Passar por baixo do guarda-chuva", "Esperar sem ultrapassá-lo", "Perguntar em qual apartamento mora"],
             "correct": 1, "success": "Ele se afasta quando o relógio muda de minuto. Você não ouviu passos.",
             "failure": "O homem abre o guarda-chuva. Dentro dele há um céu noturno sem estrelas."},
            {"prompt": "Uma moradora pede o envelope do 504. Atrás dela, a placa da porta diz 503.",
             "choices": ["Entregar o envelope", "Conferir o registro e recusar", "Pedir que ela assine"],
             "correct": 1, "success": "O envelope fica gelado. O nome escrito nele é o seu.",
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
             "choices": ["Ficar de costas para a tela", "Virar-se para conferir a projeção", "Acender todas as luzes"],
             "correct": 0, "success": "Os aplausos vêm de trás de você. Quando cessam, todas as poltronas estão vazias.",
             "failure": "A tela mostra a sala vista de trás. Na imagem, alguém está olhando diretamente para você."},
            {"prompt": "O projetor liga sozinho. Uma sombra atravessa a cabine, embora você esteja do lado de fora.",
             "choices": ["Entrar na cabine", "Esperar a sessão terminar", "Desligar o disjuntor principal"],
             "correct": 1, "success": "O filme termina sem imagem. Uma voz anuncia: 'Obrigado por permanecer até o fim.'",
             "failure": "A cabine está vazia, mas uma mão surge na janela e acena para você."},
            {"prompt": "Há bilhetes espalhados. Um deles está quente e tem seu nome, com a data de amanhã.",
             "choices": ["Guardar o bilhete", "Não tocar no bilhete quente", "Rasgar todos os bilhetes"],
             "correct": 1, "success": "O bilhete esfria e a tinta desaparece. O relógio do saguão volta a funcionar.",
             "failure": "A tinta se move e escreve: 'Assento reservado'. Uma poltrona range atrás de você."}
        ],
        "reveal": "O Cine Orfeu fechou há décadas. A sessão de hoje foi registrada como a primeira com público."
    }
]

DIFFICULTIES = {
    "estagiario": {"label": "Estagiário", "sanity": 5, "mistakes": 2, "salary": 1.0},
    "efetivo": {"label": "Efetivo", "sanity": 4, "mistakes": 1, "salary": 1.25},
    "terceirizado": {"label": "Terceirizado", "sanity": 3, "mistakes": 1, "salary": 1.6},
}

def fresh_state(player: str, difficulty: str = "estagiario") -> dict:
    if difficulty not in DIFFICULTIES:
        difficulty = "estagiario"
    return {
        "schema_version": 1, "player": player, "status": "between_shifts",
        "difficulty": difficulty, "cash": 0, "reputation": 0, "shift_index": 0,
        "sanity": DIFFICULTIES[difficulty]["sanity"], "mistakes": 0, "task_index": 0,
        "completed": [], "current_seed": None, "created_at": datetime.now().isoformat(timespec="seconds")
    }

class ShiftGame:
    def __init__(self, save_path: Path = SAVE, history_path: Path = HISTORY):
        self.save_path, self.history_path = save_path, history_path
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        self.history = self._read(self.history_path, {"shifts": []})
        self.state = self._read(self.save_path, None)

    @staticmethod
    def _read(path: Path, default):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default

    def save(self):
        temp = self.save_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.save_path)

    @property
    def mission(self):
        return MISSIONS[self.state["shift_index"] % len(MISSIONS)]

    @property
    def task(self):
        return self.mission["tasks"][self.state["task_index"]]

    def start_campaign(self, player: str, difficulty: str = "estagiario"):
        self.state = fresh_state(player.strip()[:24] or "Funcionário", difficulty)
        self.save()

    def start_shift(self):
        if self.state is None:
            raise RuntimeError("Crie uma campanha antes de iniciar o turno.")
        if self.state["shift_index"] >= len(MISSIONS):
            self.state["shift_index"] = 0
        self.state.update(status="on_shift", task_index=0, mistakes=0,
                          sanity=DIFFICULTIES[self.state["difficulty"]]["sanity"],
                          current_seed=random.randrange(1, 2**31))
        self.save()
        return self.mission

    def act(self, choice_index: int) -> dict:
        if self.state is None or self.state["status"] != "on_shift":
            raise RuntimeError("Não há turno em andamento.")
        if choice_index not in range(3):
            raise ValueError("Escolha inválida.")
        task = self.task
        correct = choice_index == task["correct"]
        if correct:
            result = {"correct": True, "message": task["success"]}
            self.state["reputation"] += 1
        else:
            result = {"correct": False, "message": task["failure"]}
            self.state["sanity"] = max(0, self.state["sanity"] - 1)
            self.state["mistakes"] += 1
        self.state["task_index"] += 1
        finished = self.state["task_index"] >= len(self.mission["tasks"])
        if self.state["sanity"] <= 0 or self.state["mistakes"] >= 2:
            self._finish_shift(False)
            result["ending"] = "missing"
        elif finished:
            self._finish_shift(True)
            result["ending"] = "survived"
        self.save()
        return result

    def _finish_shift(self, survived: bool):
        mission = self.mission
        if survived:
            factor = DIFFICULTIES[self.state["difficulty"]]["salary"]
            paid = int(mission["pay"] * factor)
            self.state["cash"] += paid
            self.state["completed"].append(mission["id"])
            outcome = "completed"
        else:
            paid = 0
            outcome = "missing"
        self.state.update(status="between_shifts" if survived else "ended",
                          last_outcome=outcome, last_payment=paid,
                          last_reveal=mission["reveal"])
        self.history.setdefault("shifts", []).append({
            "player": self.state["player"], "mission": mission["title"],
            "outcome": outcome, "payment": paid, "date": datetime.now().isoformat(timespec="seconds")
        })
        self.history_path.write_text(json.dumps(self.history, ensure_ascii=False, indent=2), encoding="utf-8")

    def next_shift(self):
        if self.state is None or self.state["status"] != "between_shifts":
            raise RuntimeError("Não é possível iniciar outro turno agora.")
        self.state["shift_index"] += 1
        if self.state["shift_index"] >= len(MISSIONS):
            self.state["shift_index"] = 0
        return self.start_shift()

    def abandon(self):
        if self.state:
            self.state["status"] = "ended"
            self.save()
