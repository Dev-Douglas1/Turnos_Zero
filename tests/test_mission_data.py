import unittest

from scene_manager import SceneManager
from turnos_zero import MISSIONS


class MissionDataTests(unittest.TestCase):
    def setUp(self):
        self.scenes = SceneManager()

    def test_missoes_tem_ids_unicos_e_tres_ocorrencias(self):
        ids = [mission["id"] for mission in MISSIONS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 4)
        for mission in MISSIONS:
            with self.subTest(mission=mission["id"]):
                self.assertEqual(len(mission["tasks"]), 3)
                self.assertTrue(mission["rules"])
                self.assertGreater(mission["pay"], 0)

    def test_escolhas_e_resultados_estao_completos(self):
        for mission in MISSIONS:
            for index, task in enumerate(mission["tasks"]):
                with self.subTest(mission=mission["id"], task=index):
                    self.assertEqual(len(task["choices"]), 3)
                    self.assertIs(type(task["correct"]), int)
                    self.assertIn(task["correct"], range(3))
                    self.assertTrue(task.get("prompt"))
                    self.assertTrue(task.get("success"))
                    self.assertTrue(task.get("failure"))
                    self.assertTrue(task.get("radio_hint"), "Cada ocorrência precisa de uma transmissão contextualizada.")

    def test_evidencias_referenciam_hotspots_reais(self):
        for mission in MISSIONS:
            scene = self.scenes.get(mission["id"])
            hotspot_ids = {item["id"] for item in scene.get("hotspots", [])}
            for index, task in enumerate(mission["tasks"]):
                with self.subTest(mission=mission["id"], task=index):
                    self.assertTrue(set(task.get("evidence_ids", [])).issubset(hotspot_ids))
                    alternatives = task.get("evidence_choices", [])
                    self.assertTrue(set(alternatives).issubset({0, 1, 2}))
                    if alternatives:
                        self.assertTrue(task.get("evidence_ids"))
                        self.assertTrue(task.get("evidence_note"))


if __name__ == "__main__":
    unittest.main()
