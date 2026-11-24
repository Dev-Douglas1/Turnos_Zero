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
        self.assertEqual(self.game.state["cash"], -1_000_000)

    def test_tres_decisoes_corretas_concluem_turno(self):
        self.game.start_shift()
        for task in self.game.mission["tasks"]:
            result = self.game.act(task["correct"])
        self.assertEqual(result["ending"], "survived")
        self.assertEqual(self.game.state["status"], "between_shifts")
        self.assertEqual(self.game.state["cash"], -999_950)
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
        self.assertEqual(len(MISSIONS), 4)

    def test_contratos_continuam_e_recompensas_dobram(self):
        expected_rewards = [50, 100, 200, 400, 800]
        expected_risks = [1, 2, 4, 8, 16]
        for index, reward in enumerate(expected_rewards):
            self.assertEqual(self.game.mission["pay"], reward)
            self.game.start_shift()
            self.assertEqual(self.game.state["risk_multiplier"], expected_risks[index])
            for task in self.game.mission["tasks"]:
                result = self.game.act(task["correct"])
            self.assertEqual(result["ending"], "survived")
            if index < len(expected_rewards) - 1:
                self.game.next_shift()
        self.assertEqual(self.game.state["shift_index"], 4)
        self.assertEqual(self.game.state["cash"], -998_450)
        self.assertEqual(self.game.state["status"], "between_shifts")

    def test_save_entre_contratos_e_valido_apos_turno_concluido(self):
        self.game.start_shift()
        for task in self.game.mission["tasks"]:
            self.game.act(task["correct"])
        reopened = ShiftGame(self.game.save_path, self.game.history_path)
        self.assertIsNotNone(reopened.state)
        self.assertEqual(reopened.state["status"], "between_shifts")
        self.assertEqual(reopened.state["task_index"], 3)

    def test_contrato_recorrente_persiste_apos_reabrir(self):
        for _ in range(4):
            self.game.start_shift()
            for task in self.game.mission["tasks"]:
                self.game.act(task["correct"])
            self.game.next_shift()
        reopened = ShiftGame(self.game.save_path, self.game.history_path)
        self.assertIsNotNone(reopened.state)
        self.assertEqual(reopened.state["shift_index"], 4)
        self.assertEqual(reopened.mission["pay"], 800)

    def test_save_corrompido_nao_quebra_abertura(self):
        self.game.save_path.write_text("{json inválido", encoding="utf-8")
        reopened = ShiftGame(self.game.save_path, self.game.history_path)
        self.assertIsNone(reopened.state)

    def test_estado_com_schema_invalido_e_descartado(self):
        self.game.save_path.write_text('{"schema_version":99,"status":"on_shift"}', encoding="utf-8")
        reopened = ShiftGame(self.game.save_path, self.game.history_path)
        self.assertIsNone(reopened.state)

    def test_escolha_invalida_nao_altera_turno(self):
        self.game.start_shift()
        with self.assertRaises(ValueError):
            self.game.act(True)
        self.assertEqual(self.game.state["task_index"], 0)

    def test_nao_inicia_turno_duas_vezes(self):
        self.game.start_shift()
        with self.assertRaises(RuntimeError):
            self.game.start_shift()

    def test_evidencia_fica_salva_e_nao_duplica(self):
        self.game.start_shift()
        self.assertTrue(self.game.record_evidence("caixa", "Livro-caixa com registro anômalo"))
        self.assertFalse(self.game.record_evidence("caixa", "Livro-caixa com registro anômalo"))
        reopened = ShiftGame(self.game.save_path, self.game.history_path)
        self.assertEqual(len(reopened.state["evidence"]), 1)
        self.assertEqual(reopened.state["evidence"][0]["id"], "caixa")

    def test_evidencia_so_pode_ser_registrada_durante_turno(self):
        with self.assertRaises(RuntimeError):
            self.game.record_evidence("caixa", "Pista")

    def test_evidencia_aplicada_a_decisao_aumenta_reputacao(self):
        self.game.start_shift()
        self.game.record_evidence("geladeira", "A mensagem confirma o protocolo.")
        result = self.game.act(self.game.task["correct"])
        self.assertTrue(result["evidence_used"])
        self.assertIn("evidence_note", result)
        self.assertEqual(self.game.state["reputation"], 2)

    def test_evidencia_desbloqueia_decisao_alternativa(self):
        self.game.start_shift()
        self.game.record_evidence("geladeira", "A mensagem diz para não interagir.")
        result = self.game.act(2)
        self.assertTrue(result["correct"])
        self.assertTrue(result["evidence_used"])
        self.assertEqual(self.game.state["reputation"], 2)

    def test_decisao_alternativa_sem_evidencia_e_violacao(self):
        self.game.start_shift()
        result = self.game.act(2)
        self.assertFalse(result["correct"])
        self.assertFalse(result["evidence_used"])
        self.assertEqual(self.game.state["mistakes"], 1)

    def test_decisao_sem_evidencia_nao_recebe_bonus(self):
        self.game.start_shift()
        result = self.game.act(self.game.task["correct"])
        self.assertFalse(result["evidence_used"])
        self.assertEqual(self.game.state["reputation"], 1)

    def test_evidencia_de_outro_contrato_nao_influencia_decisao(self):
        self.game.start_shift()
        self.game.state["evidence"].append({
            "id": "geladeira", "description": "Pista antiga",
            "mission": "edificio_9", "task_index": 0
        })
        self.game.save()
        result = self.game.act(self.game.task["correct"])
        self.assertFalse(result["evidence_used"])
        self.assertEqual(self.game.state["reputation"], 1)

    def test_rejeita_estado_com_tipos_invalidos(self):
        state = fresh_state("Teste")
        state["cash"] = True
        self.assertFalse(ShiftGame._valid_state(state))

    def test_rejeita_evidencia_malformada(self):
        state = fresh_state("Teste")
        state["evidence"] = [{"id": "pista", "mission": "inexistente", "description": "x", "task_index": 0}]
        self.assertFalse(ShiftGame._valid_state(state))

    def test_historico_nao_duplica_mesmo_turno(self):
        self.game.start_shift()
        for task in self.game.mission["tasks"]:
            self.game.act(task["correct"])
        cash_before = self.game.state["cash"]
        completed_before = list(self.game.state["completed"])
        self.game._finish_shift(True)
        self.assertEqual(len(self.game.history["shifts"]), 1)
        self.assertEqual(self.game.state["cash"], cash_before)
        self.assertEqual(self.game.state["completed"], completed_before)

    def test_save_antigo_em_andamento_sem_token_e_compativel(self):
        state = fresh_state("Legado")
        state.update(status="on_shift", task_index=1)
        state.pop("shift_token", None)
        self.assertTrue(ShiftGame._valid_state(state))

    def test_vinculo_efetivo_encerra_com_uma_violacao(self):
        self.game.start_campaign("Teste", "efetivo")
        self.game.start_shift()
        result = self.game.act((self.game.task["correct"] + 1) % 3)
        self.assertEqual(result["ending"], "missing")
        self.assertEqual(self.game.state["status"], "ended")

    def test_vinculo_terceirizado_encerra_com_uma_violacao(self):
        self.game.start_campaign("Teste", "terceirizado")
        self.game.start_shift()
        result = self.game.act((self.game.task["correct"] + 1) % 3)
        self.assertEqual(result["ending"], "missing")

    def test_estagiario_suporta_duas_violacoes(self):
        self.game.start_shift()
        first = self.game.act((self.game.task["correct"] + 1) % 3)
        self.assertNotIn("ending", first)
        result = self.game.act((self.game.task["correct"] + 1) % 3)
        self.assertEqual(result["ending"], "missing")

    def test_rejeita_progresso_com_contratos_fora_de_ordem(self):
        state = fresh_state("Teste")
        state["shift_index"] = 1
        state["completed"] = ["cinema_vazio"]
        self.assertFalse(ShiftGame._valid_state(state))

    def test_rejeita_contrato_concluido_sem_registro_de_conclusao(self):
        state = fresh_state("Teste")
        state["task_index"] = 3
        self.assertFalse(ShiftGame._valid_state(state))

    def test_proximo_contrato_reinicia_indice_e_pode_ser_reaberto(self):
        self.game.start_shift()
        for task in self.game.mission["tasks"]:
            self.game.act(task["correct"])
        self.game.next_shift()
        self.assertEqual(self.game.state["task_index"], 0)
        reopened = ShiftGame(self.game.save_path, self.game.history_path)
        self.assertEqual(reopened.state["shift_index"], 1)
        self.assertEqual(reopened.state["task_index"], 0)

    def test_laboratorio_usa_evidencia_para_desbloquear_alternativa(self):
        for index, mission in enumerate(MISSIONS[:-1]):
            self.game.start_shift()
            for task in mission["tasks"]:
                self.game.act(task["correct"])
            self.game.next_shift()
        self.assertEqual(self.game.mission["id"], "laboratorio")
        self.game.start_shift()
        self.game.record_evidence("terminal", "Sessão antiga ainda ativa.")
        reputation_before = self.game.state["reputation"]
        result = self.game.act(1)
        self.assertTrue(result["correct"])
        self.assertTrue(result["evidence_used"])
        self.assertEqual(self.game.state["reputation"], reputation_before + 2)

    def test_estabilidade_zero_encerra_sem_pagamento(self):
        self.game.start_shift()
        self.game.state["sanity"] = 1
        self.game.save()
        result = self.game.act((self.game.task["correct"] + 1) % 3)
        self.assertEqual(result["ending"], "missing")
        self.assertEqual(self.game.state["last_payment"], 0)
        self.assertEqual(self.game.state["status"], "ended")

    def test_estado_de_objeto_persiste_apos_reabrir(self):
        self.game.start_shift()
        self.assertEqual(self.game.get_object_state("geladeira"), "0")
        self.assertTrue(self.game.set_object_state("geladeira", "1"))
        reopened = ShiftGame(self.game.save_path, self.game.history_path)
        self.assertEqual(reopened.get_object_state("geladeira"), "1")

    def test_estado_de_objeto_nao_vaza_para_contrato_seguinte(self):
        self.game.start_shift()
        self.game.set_object_state("geladeira", "1")
        for task in self.game.mission["tasks"]:
            self.game.act(task["correct"])
        self.game.next_shift()
        self.game.start_shift()
        self.assertEqual(self.game.get_object_state("geladeira"), "0")

    def test_estado_de_objeto_invalido_corrompe_save(self):
        state = fresh_state("Teste")
        state["object_states"] = {"0:geladeira": "destruido"}
        self.assertFalse(ShiftGame._valid_state(state))

    def test_estado_encerrado_persiste_apos_reabrir(self):
        self.game.start_campaign("Teste", "efetivo")
        self.game.start_shift()
        self.game.act((self.game.task["correct"] + 1) % 3)
        reopened = ShiftGame(self.game.save_path, self.game.history_path)
        self.assertEqual(reopened.state["status"], "ended")

if __name__ == "__main__":
    unittest.main()
