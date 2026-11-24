import tempfile
import unittest
from pathlib import Path
from turnos_zero import ShiftGame, MISSIONS, fresh_state, DIFFICULTIES

class TurnosZeroTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.game = ShiftGame(root / "save.json", root / "history.json")
        self.game.start_campaign("Teste", "estagiario")

    def tearDown(self):
        self.tmp.cleanup()

    def test_nova_campanha_tem_estado_isolado(self):
        self.assertEqual(self.game.state["player"], "Teste")
        self.assertEqual(self.game.state["status"], "between_shifts")
        self.assertEqual(self.game.state["cash"], 0)

    def test_tres_decisoes_corretas_concluem_turno(self):
        self.game.start_shift()
        for task in self.game.mission["tasks"]:
            result = self.game.act(task["correct"])
        self.assertEqual(result["ending"], "survived")
        self.assertEqual(self.game.state["status"], "between_shifts")
        self.assertGreater(self.game.state["cash"], 0)
        self.assertEqual(len(self.game.state["completed"]), 1)

    def test_duas_falhas_encerram_contrato(self):
        self.game.start_shift()
        self.game.act((self.game.task["correct"] + 1) % 3)
        result = self.game.act((self.game.task["correct"] + 1) % 3)
        self.assertEqual(result["ending"], "missing")
        self.assertEqual(self.game.state["status"], "ended")
        self.assertEqual(self.game.state["last_payment"], 0)

    def test_salvamento_reabre_estado(self):
        self.game.start_shift()
        self.game.act(self.game.task["correct"])
        reopened = ShiftGame(self.game.save_path, self.game.history_path)
        self.assertEqual(reopened.state["task_index"], 1)
        self.assertEqual(reopened.state["status"], "on_shift")

    def test_proximo_contrato_muda_missao_sem_iniciar_turno(self):
        self.game.start_shift()
        for task in self.game.mission["tasks"]:
            result = self.game.act(task["correct"])
        first = self.game.mission["id"]
        self.game.next_shift()
        self.assertNotEqual(self.game.mission["id"], first)
        self.assertEqual(self.game.state["status"], "between_shifts")

    def test_dificuldades_configuradas(self):
        self.assertEqual(set(DIFFICULTIES), {"estagiario", "efetivo", "terceirizado"})
        self.assertGreater(DIFFICULTIES["terceirizado"]["salary"], DIFFICULTIES["estagiario"]["salary"])
        self.assertEqual(len(MISSIONS), 3)

if __name__ == "__main__":
    unittest.main()
