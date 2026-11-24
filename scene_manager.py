"""Carregador declarativo de cenas e áreas interativas de Turnos Zero."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCENE_CONFIG = ROOT / "dados" / "cenas.json"

class SceneError(ValueError):
    """Configuração de cena inválida ou referência insegura."""

class SceneManager:
    def __init__(self, config_path: Path = SCENE_CONFIG):
        self.config_path = Path(config_path)
        self.scenes = self._load()

    def _load(self):
        try:
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SceneError(f"Não foi possível carregar cenas: {exc}") from exc
        if not isinstance(raw, dict) or not isinstance(raw.get("scenes"), list):
            raise SceneError("O arquivo de cenas precisa conter uma lista 'scenes'.")
        result = {}
        for scene in raw["scenes"]:
            if not isinstance(scene, dict):
                raise SceneError("Cada cena deve ser um objeto.")
            sid = scene.get("id")
            if not isinstance(sid, str) or not sid.strip() or sid in result:
                raise SceneError(f"ID de cena ausente ou duplicado: {sid!r}")
            background = scene.get("background")
            if background is not None:
                path = Path(background)
                if path.is_absolute() or ".." in path.parts:
                    raise SceneError(f"Caminho de fundo não permitido na cena {sid}.")
            hotspots = scene.get("hotspots", [])
            if not isinstance(hotspots, list):
                raise SceneError(f"Hotspots inválidos na cena {sid}.")
            for hotspot in hotspots:
                if not isinstance(hotspot, dict) or not isinstance(hotspot.get("id"), str):
                    raise SceneError(f"Hotspot sem ID válido na cena {sid}.")
                bounds = hotspot.get("bounds")
                if (not isinstance(bounds, list) or len(bounds) != 4 or
                    any(not isinstance(v, (int, float)) for v in bounds) or
                    not (0 <= bounds[0] < bounds[2] <= 1 and 0 <= bounds[1] < bounds[3] <= 1)):
                    raise SceneError(f"Coordenadas inválidas no hotspot {hotspot['id']}.")
            result[sid] = scene
        return result

    def get(self, scene_id: str) -> dict:
        try:
            return self.scenes[scene_id]
        except KeyError as exc:
            raise SceneError(f"Cena desconhecida: {scene_id}") from exc

    def hit_test(self, scene_id: str, x: float, y: float) -> dict | None:
        """Retorna hotspot sob coordenadas normalizadas (0..1)."""
        for hotspot in self.get(scene_id).get("hotspots", []):
            x1, y1, x2, y2 = hotspot["bounds"]
            if x1 <= x <= x2 and y1 <= y <= y2:
                return hotspot
        return None
