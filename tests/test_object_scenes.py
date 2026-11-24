import json
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "dados" / "objetos_cenas.json"


class EditableSceneManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_viewport_matches_runtime_scene(self):
        self.assertEqual(self.data["viewport"], [834, 469])

    def test_all_four_missions_have_independent_objects(self):
        scenes = self.data["scenes"]
        self.assertEqual(set(scenes), {"loja_24h", "edificio_9", "cinema_vazio", "laboratorio"})
        for scene_id, scene in scenes.items():
            with self.subTest(scene=scene_id):
                self.assertGreaterEqual(len(scene["objects"]), 3)
                ids = [obj["id"] for obj in scene["objects"]]
                self.assertEqual(len(ids), len(set(ids)))

    def test_object_properties_are_editable_and_bounded(self):
        for scene_id, scene in self.data["scenes"].items():
            for obj in scene["objects"]:
                with self.subTest(scene=scene_id, obj=obj["id"]):
                    self.assertTrue(obj["asset"].endswith(".png"))
                    self.assertTrue(0 <= obj["x"] < 1)
                    self.assertTrue(0 <= obj["y"] < 1)
                    self.assertTrue(0 < obj["w"] <= 1)
                    self.assertTrue(0 < obj["h"] <= 1)
                    self.assertLessEqual(obj["x"] + obj["w"], 1)
                    self.assertLessEqual(obj["y"] + obj["h"], 1)
                    self.assertNotIn("..", Path(obj["asset"]).parts)
                    self.assertIsInstance(obj["z"], int)
                    self.assertIsInstance(obj["visible"], bool)

    def test_all_independent_object_pngs_are_exported(self):
        for scene_id, scene in self.data["scenes"].items():
            for obj in scene["objects"]:
                path = ROOT / "assets" / "objetos" / obj["asset"]
                with self.subTest(scene=scene_id, asset=obj["asset"]):
                    self.assertTrue(path.is_file(), f"Sprite não exportado: {path}")
                    data = path.read_bytes()
                    self.assertEqual(data[:8], bytes.fromhex("89504e470d0a1a0a"))
                    self.assertEqual(struct.unpack(">II", data[16:24]), (512, 512))
                    for state, variant in obj.get("asset_states", {}).items():
                        variant_path = ROOT / "assets" / "objetos" / variant
                        self.assertTrue(variant_path.is_file(), f"Sprite alternativo ausente: {variant_path}")
                        variant_data = variant_path.read_bytes()
                        self.assertEqual(variant_data[:8], bytes.fromhex("89504e470d0a1a0a"))
                        self.assertEqual(struct.unpack(">II", variant_data[16:24]), (512, 512))

    def test_hotspots_are_inside_the_scene_and_follow_their_objects(self):
        for scene_id, scene in self.data["scenes"].items():
            objects = {obj["id"]: obj for obj in scene["objects"]}
            hotspot_ids = [item["id"] for item in scene["hotspots"]]
            self.assertEqual(len(hotspot_ids), len(set(hotspot_ids)))
            for hotspot in scene["hotspots"]:
                with self.subTest(scene=scene_id, hotspot=hotspot["id"]):
                    x1, y1, x2, y2 = hotspot["bounds"]
                    self.assertTrue(0 <= x1 < x2 <= 1)
                    self.assertTrue(0 <= y1 < y2 <= 1)
                    self.assertTrue(hotspot["finding"])
                    object_id = hotspot.get("object")
                    self.assertIn(object_id, objects)
                    obj = objects[object_id]
                    expected = [obj["x"], obj["y"], obj["x"] + obj["w"], obj["y"] + obj["h"]]
                    for actual, target in zip(hotspot["bounds"], expected):
                        self.assertAlmostEqual(actual, target, places=6)
                    interaction = hotspot.get("interaction")
                    self.assertIsInstance(interaction, dict)
                    self.assertTrue(interaction.get("label"))
                    self.assertEqual(len(interaction.get("states", [])), 2)
                    self.assertEqual(len(interaction.get("responses", [])), 2)


    def test_background_pngs_preserve_16_9_ratio(self):
        config = json.loads((ROOT / "dados" / "cenas.json").read_text(encoding="utf-8"))
        for scene in config["scenes"]:
            asset = scene.get("background")
            if not asset:
                continue
            path = ROOT / asset
            data = path.read_bytes()
            self.assertEqual(data[:8], bytes.fromhex("89504e470d0a1a0a"))
            self.assertEqual(struct.unpack(">II", data[16:24]), (834, 469))

if __name__ == "__main__":
    unittest.main()
