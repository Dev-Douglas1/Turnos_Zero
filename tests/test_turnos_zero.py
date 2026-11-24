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

    def test_dificuldade_define_local_inicial(self):
        expected = {
            "estagiario": "loja_24h",
            "efetivo": "edificio_9",
            "terceirizado": "cinema_vazio",
        }
        for difficulty, mission_id in expected.items():
            game = ShiftGame(self.game.save_path.parent / f"{difficulty}.json",
                             self.game.history_path.parent / f"{difficulty}-history.json")
            game.start_campaign("Teste", difficulty)
            self.assertEqual(game.mission["id"], mission_id)

    def test_ordem_de_missoes_persiste_ao_reabrir(self):
        self.game.start_campaign("Teste", "efetivo")
        self.assertEqual(self.game.mission["id"], "edificio_9")
        reopened = ShiftGame(self.game.save_path, self.game.history_path)
        self.assertEqual(reopened.mission["id"], "edificio_9")
        self.assertEqual(reopened.state["mission_order"][0], "edificio_9")

    def test_relatorio_de_ocorrencia_tem_mensagem(self):
        self.game.start_shift()
        result = self.game.act(self.game.task["correct"])
        self.assertTrue(result.get("message"))
        self.assertIn("message", result)

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

    def test_save_antigo_sem_inventario_recebe_equipamentos_padrao(self):
        self.game.state.pop("inventory", None)
        self.game.state.pop("tool_states", None)
        self.game.save()
        reopened = ShiftGame(self.game.save_path, self.game.history_path)
        self.assertIsNotNone(reopened.state)
        self.assertTrue(reopened.get_tool_state("lanterna"))
        self.assertFalse(reopened.get_tool_state("radio"))
        self.assertFalse(reopened.get_tool_state("camera"))
        reopened.start_shift()
        self.assertFalse(reopened.toggle_tool("lanterna"))

    def test_inventario_inicial_contem_tres_equipamentos(self):
        self.assertEqual(self.game.state["inventory"], ["lanterna", "radio", "camera"])
        self.assertTrue(self.game.get_tool_state("lanterna"))
        self.assertFalse(self.game.get_tool_state("radio"))
        self.assertFalse(self.game.get_tool_state("camera"))

    def test_radio_consume_uma_carga_por_ativacao(self):
        self.game.start_shift()
        self.assertEqual(self.game.get_tool_resource("radio"), 3)
        self.assertTrue(self.game.toggle_tool("radio"))
        self.assertEqual(self.game.get_tool_resource("radio"), 2)
        self.assertFalse(self.game.toggle_tool("radio"))
        self.assertEqual(self.game.get_tool_resource("radio"), 2)

    def test_consulta_radio_consume_uma_transmissao(self):
        self.game.start_shift()
        self.assertEqual(self.game.get_tool_resource("radio"), 3)
        self.game.consume_tool_resource("radio", 1)
        self.assertEqual(self.game.get_tool_resource("radio"), 2)
        self.assertTrue(self.game.task.get("radio_hint"))

    def test_camera_consume_filme_ao_fotografar(self):
        self.game.start_shift()
        self.game.toggle_tool("camera")
        self.game.consume_tool_resource("camera", 1)
        self.assertEqual(self.game.get_tool_resource("camera"), 2)
        self.assertTrue(self.game.get_tool_state("camera"))
        self.game.consume_tool_resource("camera", 2)
        self.assertFalse(self.game.get_tool_state("camera"))
        self.assertEqual(self.game.get_tool_resource("camera"), 0)

    def test_bateria_da_lanterna_diminui_a_cada_ocorrencia(self):
        self.game.start_shift()
        self.assertEqual(self.game.get_tool_resource("lanterna"), 100)
        self.game.act(self.game.task["correct"])
        self.assertEqual(self.game.get_tool_resource("lanterna"), 65)

    def test_equipamentos_sao_repostos_no_proximo_contrato(self):
        self.game.start_shift()
        self.game.toggle_tool("radio")
        self.game.consume_tool_resource("camera", 2)
        for task in self.game.mission["tasks"]:
            self.game.act(task["correct"])
        self.game.next_shift()
        self.game.start_shift()
        self.assertEqual(self.game.get_tool_resource("lanterna"), 100)
        self.assertEqual(self.game.get_tool_resource("radio"), 3)
        self.assertEqual(self.game.get_tool_resource("camera"), 3)

    def test_bateria_da_lanterna_desliga_o_item_ao_zerar(self):
        self.game.start_shift()
        self.game.state["tool_resources"]["lanterna"] = 10
        self.game.save()
        self.game.act(self.game.task["correct"])
        self.assertEqual(self.game.get_tool_resource("lanterna"), 0)
        self.assertFalse(self.game.get_tool_state("lanterna"))

    def test_equipamento_alterna_e_persiste(self):
        self.game.start_shift()
        self.assertTrue(self.game.toggle_tool("camera"))
        reopened = ShiftGame(self.game.save_path, self.game.history_path)
        self.assertTrue(reopened.get_tool_state("camera"))
        self.assertFalse(reopened.get_tool_state("radio"))

    def test_nao_permite_ativar_item_que_nao_esta_no_inventario(self):
        self.game.start_shift()
        self.game.state["inventory"] = ["lanterna"]
        self.game.save()
        with self.assertRaises(ValueError):
            self.game.toggle_tool("camera")

    def test_save_rejeita_estado_de_ferramenta_malformado(self):
        state = fresh_state("Teste")
        state["tool_states"] = {"camera": "ligada"}
        self.assertFalse(ShiftGame._valid_state(state))

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

    def test_interacoes_aumentam_pressao_e_ativam_ameaca(self):
        self.game.start_shift()
        first = self.game.interact_object("caixa")
        self.assertEqual(first["threat_level"], 1)
        self.assertFalse(first["threat_active"])
        second = self.game.interact_object("porta")
        self.assertTrue(second["activated"])
        self.assertTrue(self.game.state["threat_active"])
        self.assertEqual(self.game.state["threat_level"], 3)

    def test_objeto_repetido_nao_aumenta_pressao_indefinidamente(self):
        self.game.start_shift()
        self.game.interact_object("porta", repeatable=True)
        self.game.interact_object("porta", repeatable=True)
        self.assertEqual(self.game.state["threat_level"], 2)
        self.assertEqual(self.game.state["threat_triggered"], ["porta"])

    def test_ameaca_exposta_causa_penalidade_adicional(self):
        self.game.start_shift()
        self.game.interact_object("porta")
        self.game.interact_object("geladeira")
        self.assertTrue(self.game.state["threat_active"])
        result = self.game.act(self.game.task["correct"])
        self.assertTrue(result["threat_hit"])
        self.assertFalse(result.get("threat_evaded", False))
        self.assertEqual(self.game.state["mistakes"], 1)
        self.assertIn("\n\n", result["message"])
        self.assertNotIn("\\n\\n", result["message"])
        self.assertEqual(self.game.state["sanity"], 4)

    def test_fotografia_do_canal_suspeito_interrompe_perseguicao(self):
        self.game.start_shift()
        self.game.interact_object("porta")
        self.game.interact_object("geladeira")
        self.assertTrue(self.game.state["threat_active"])
        self.game.toggle_tool("camera")
        message = self.game.document_anomaly("geladeira")
        self.assertTrue(message)
        self.game.consume_tool_resource("camera", 1)
        self.assertTrue(self.game.state["threat_disrupted"])
        result = self.game.act(self.game.task["correct"])
        self.assertTrue(result["threat_documented"])
        self.assertFalse(result.get("threat_hit", False))
        self.assertEqual(self.game.state["mistakes"], 0)
        self.assertEqual(self.game.state["sanity"], 5)
        self.assertFalse(self.game.state["threat_active"])
        self.assertFalse(self.game.state["threat_disrupted"])

    def test_ultima_foto_ainda_interrompe_perseguicao(self):
        self.game.start_shift()
        self.game.interact_object("porta")
        self.game.interact_object("geladeira")
        self.game.state["tool_resources"]["camera"] = 1
        self.game.save()
        self.game.toggle_tool("camera")
        self.game.document_anomaly("geladeira")
        self.game.consume_tool_resource("camera", 1)
        self.assertFalse(self.game.get_tool_state("camera"))
        self.assertTrue(self.game.state["threat_disrupted"])
        result = self.game.act(self.game.task["correct"])
        self.assertTrue(result["threat_documented"])
        self.assertEqual(self.game.state["mistakes"], 0)

    def test_fotografia_de_canal_incorreto_nao_interrompe_ameaca(self):
        self.game.start_shift()
        self.game.interact_object("porta")
        self.game.interact_object("geladeira")
        self.game.toggle_tool("camera")
        with self.assertRaises(ValueError):
            self.game.document_anomaly("caixa")
        self.assertFalse(self.game.state["threat_disrupted"])

    def test_camera_desarmada_nao_interrompe_ameaca(self):
        self.game.start_shift()
        self.game.interact_object("porta")
        self.game.interact_object("geladeira")
        with self.assertRaises(RuntimeError):
            self.game.document_anomaly("geladeira")

    def test_abrigo_persiste_e_evade_ameaca(self):
        self.game.start_shift()
        self.game.interact_object("porta")
        self.game.interact_object("geladeira")
        spot = self.game.hide_from_anomaly()
        self.assertIn("balcão", spot)
        self.assertTrue(self.game.state["is_hidden"])
        reopened = ShiftGame(self.game.save_path, self.game.history_path)
        self.assertTrue(reopened.state["is_hidden"])
        result = reopened.act(reopened.task["correct"])
        self.assertTrue(result["threat_evaded"])
        self.assertFalse(result.get("threat_hit", False))
        self.assertEqual(reopened.state["mistakes"], 0)
        self.assertFalse(reopened.state["is_hidden"])

    def test_ameaca_sem_abrigo_ativo_nao_permite_esconder(self):
        self.game.start_shift()
        with self.assertRaises(RuntimeError):
            self.game.hide_from_anomaly()

    def test_agente_escondido_nao_pode_manipular_outro_objeto(self):
        self.game.start_shift()
        self.game.interact_object("porta")
        self.game.interact_object("geladeira")
        self.game.hide_from_anomaly()
        with self.assertRaises(RuntimeError):
            self.game.interact_object("caixa")

    def test_abrigo_so_pode_ser_usado_uma_vez_por_perseguicao(self):
        self.game.start_shift()
        self.game.interact_object("porta")
        self.game.interact_object("geladeira")
        self.game.hide_from_anomaly()
        self.game.leave_hiding()
        with self.assertRaises(RuntimeError):
            self.game.hide_from_anomaly()

    def test_save_antigo_migra_estado_de_ameaca_padrao(self):
        self.game.state.pop("threat_level", None)
        self.game.state.pop("threat_active", None)
        self.game.state.pop("is_hidden", None)
        self.game.state.pop("threat_triggered", None)
        self.game.save()
        reopened = ShiftGame(self.game.save_path, self.game.history_path)
        self.assertEqual(reopened.state["threat_level"], 0)
        self.assertFalse(reopened.state["threat_active"])
        self.assertFalse(reopened.state["is_hidden"])
        self.assertFalse(reopened.state["hide_used"])
        self.assertFalse(reopened.state["threat_disrupted"])
        self.assertEqual(reopened.state["threat_triggered"], [])

    def test_save_rejeita_pressao_anomala_invalida(self):
        state = fresh_state("Teste")
        state["threat_level"] = 6
        self.assertFalse(ShiftGame._valid_state(state))
        state["threat_level"] = 1
        state["threat_active"] = "yes"
        self.assertFalse(ShiftGame._valid_state(state))
        state["threat_active"] = True
        state["threat_disrupted"] = "yes"
        self.assertFalse(ShiftGame._valid_state(state))

if __name__ == "__main__":
    unittest.main()
