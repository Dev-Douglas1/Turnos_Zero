import json
import tempfile
import unittest
from pathlib import Path
from scene_manager import SceneManager, SceneError, scene_for_mission

class SceneManagerTests(unittest.TestCase):
    def write_config(self, root, scenes):
        path = root / "scenes.json"
        path.write_text(json.dumps({"scenes": scenes}), encoding="utf-8")
        return path


    def test_todos_os_contratos_possuem_cena_unificada(self):
        expected = {
            "loja_24h": "loja_24h",
            "edificio_9": "edificio_9",
            "cinema_vazio": "cinema_vazio",
            "laboratorio": "laboratorio",
        }
        for mission_id, scene_id in expected.items():
            with self.subTest(mission=mission_id):
                self.assertEqual(scene_for_mission(mission_id), scene_id)
        self.assertIsNone(scene_for_mission("missao_inexistente"))

    def test_converte_hotspot_para_area_da_cena(self):
        bounds = SceneManager.map_bounds([0.1, 0.2, 0.5, 0.8], (100, 200, 900, 600))
        self.assertEqual(bounds, (180.0, 280.0, 500.0, 520.0))

    def test_carrega_catalogo_e_encontra_hotspot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self.write_config(root, [{"id":"room","background":"assets/room.png","hotspots":[{"id":"door","bounds":[0.1,0.1,0.5,0.5],"action":"open"}]}])
            manager = SceneManager(path)
            self.assertEqual(manager.get("room")["name"] if "name" in manager.get("room") else manager.get("room")["id"], "room")
            self.assertEqual(manager.hit_test("room", 0.2, 0.2)["id"], "door")
            self.assertIsNone(manager.hit_test("room", 0.8, 0.8))

    def test_rejeita_caminho_fora_do_projeto(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_config(Path(tmp), [{"id":"bad","background":"../../secret.png","hotspots":[]}])
            with self.assertRaises(SceneError):
                SceneManager(path)

    def test_rejeita_coordenadas_invalidas(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_config(Path(tmp), [{"id":"bad","hotspots":[{"id":"x","bounds":[0.8,0.1,0.2,0.9]}]}])
            with self.assertRaises(SceneError):
                SceneManager(path)

    def test_rejeita_ids_duplicados(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_config(Path(tmp), [{"id":"same"},{"id":"same"}])
            with self.assertRaises(SceneError):
                SceneManager(path)

    def test_rejeita_hotspots_duplicados(self):
        with tempfile.TemporaryDirectory() as tmp:
            hotspot = {"id": "same", "bounds": [0.1, 0.1, 0.5, 0.5]}
            path = self.write_config(Path(tmp), [{"id": "room", "hotspots": [hotspot, hotspot]}])
            with self.assertRaises(SceneError):
                SceneManager(path)

    def test_rejeita_booleano_em_coordenadas(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_config(Path(tmp), [{"id": "room", "hotspots": [
                {"id": "bad", "bounds": [False, 0.1, 0.5, 0.5]}
            ]}])
            with self.assertRaises(SceneError):
                SceneManager(path)

    def test_rejeita_background_com_tipo_invalido(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_config(Path(tmp), [{"id": "room", "background": 42}])
            with self.assertRaises(SceneError):
                SceneManager(path)

if __name__ == "__main__":
    unittest.main()
