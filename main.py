"""Launcher de Turnos Zero. A campanha antiga permanece preservada nos arquivos legados."""
import sys
import json
import tkinter as tk
from PIL import Image, ImageOps, ImageTk
from tkinter import messagebox, simpledialog
from turnos_zero import ShiftGame, DIFFICULTIES, MISSIONS
from scene_manager import SceneManager, SceneError, scene_for_mission
from pathlib import Path

class TurnosZeroApp:
    W, H = 1024, 700
    SCENE_VIEWPORT = (40, 195, 690, 561)  # Proporção 16:9, sem achatar o cenário.
    BG = "#090d16"
    PANEL = "#141d2b"
    GOLD = "#e5b96d"
    TEXT = "#e7e5df"
    MUTED = "#91a0ad"

    def __init__(self, root):
        self.root = root
        self.root.title("TURNOS ZERO | Agência de Serviços Extraordinários")
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        initial_w = max(640, min(self.W, screen_w - 80))
        initial_h = max(440, min(self.H, screen_h - 120))
        self.root.geometry(f"{initial_w}x{initial_h}")
        self.root.minsize(640, 440)
        self.game = ShiftGame()
        self.scene_manager = SceneManager()
        self.scene_images = {}
        self.object_images = {}
        self._view_scale = 1.0
        self._view_x = 0.0
        self._view_y = 0.0
        self._has_canvas_transform = False
        self.object_scene_data = {}
        manifest_path = Path(__file__).resolve().parent / "dados" / "objetos_cenas.json"
        try:
            self.object_scene_data = json.loads(manifest_path.read_text(encoding="utf-8")).get("scenes", {})
        except (OSError, json.JSONDecodeError):
            self.object_scene_data = {}
        self.active_scene = None
        self.current_hotspot = None
        self.current_camera_hotspot = None
        self.surveillance_images = {}
        self.ambience_active = False
        self._draw_w, self._draw_h = self.W, self.H
        self.canvas = tk.Canvas(root, bg=self.BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.targets = []
        self.screen = "menu"
        self.root.bind("<Escape>", lambda _e: self.menu())
        self.root.bind("<Return>", lambda _e: self.start_shift() if self.screen == "briefing" else None)
        self.canvas.bind("<Configure>", self.resize_canvas)
        self.menu()

    def clear(self):
        self.canvas.delete("all")
        self.targets = []
        # A tela nova começa em coordenadas lógicas, sem herdar a escala anterior.
        self._view_scale = 1.0
        self._view_x = 0.0
        self._view_y = 0.0
        self._has_canvas_transform = False

    def rect(self, x1, y1, x2, y2, fill, outline=None, width=1):
        self.canvas.create_rectangle(x1,y1,x2,y2,fill=fill,outline=outline or fill,width=width)

    def text(self, x, y, value, size=15, color=None, anchor="center", width=None):
        self.canvas.create_text(x,y,text=value,fill=color or self.TEXT,
            font=("Consolas",size,"bold"),anchor=anchor,width=width,justify="left")

    def button(self, x, y, w, label, callback, h=48):
        self.rect(x+3,y+4,x+w+3,y+h+4,"#05070c")
        self.rect(x,y,x+w,y+h,self.PANEL,"#9b7444",2)
        self.rect(x+4,y+4,x+w-4,y+h-4,self.PANEL,"#d7ad68",1)
        self.text(x+w/2,y+h/2,label,12,self.GOLD)
        self.targets.append(((x,y,x+w,y+h),callback))

    def start_ambience(self):
        """Mantém o som ambiente em loop durante a exploração, no Windows."""
        path = Path(__file__).resolve().parent / "assets" / "ambiente.wav"
        if self.ambience_active or not path.is_file():
            return
        try:
            import winsound
            winsound.PlaySound(
                str(path),
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP | winsound.SND_NODEFAULT,
            )
            self.ambience_active = True
        except (ImportError, OSError):
            self.ambience_active = False

    def stop_ambience(self):
        if not self.ambience_active:
            return
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        except (ImportError, OSError):
            pass
        self.ambience_active = False

    def play_effect(self, filename):
        """Toca um WAV curto e retoma o ambiente após o efeito."""
        path = Path(__file__).resolve().parent / "assets" / filename
        if not path.is_file():
            return
        resume_ambience = self.ambience_active
        try:
            import wave
            import winsound
            duration_ms = 900
            try:
                with wave.open(str(path), "rb") as audio:
                    duration_ms = int(audio.getnframes() / max(1, audio.getframerate()) * 1000) + 120
            except (wave.Error, OSError):
                pass
            self.ambience_active = False
            winsound.PlaySound(
                str(path),
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
            )
            if resume_ambience:
                self.root.after(duration_ms, self.start_ambience)
        except (ImportError, OSError):
            try:
                self.root.bell()
            except tk.TclError:
                pass

    def resize_canvas(self, event=None):
        """Adapta a interface ao espaço disponível sem deformar o layout."""
        width = event.width if event is not None else self.canvas.winfo_width()
        height = event.height if event is not None else self.canvas.winfo_height()
        if width <= 1 or height <= 1:
            return
        scale = min(width / self.W, height / self.H)
        offset_x = (width - self.W * scale) / 2
        offset_y = (height - self.H * scale) / 2

        if self._has_canvas_transform:
            factor = scale / self._view_scale
            self.canvas.scale("all", 0, 0, factor, factor)
            self.canvas.move(
                "all",
                offset_x - self._view_x * factor,
                offset_y - self._view_y * factor,
            )
        else:
            self.canvas.scale("all", 0, 0, scale, scale)
            self.canvas.move("all", offset_x, offset_y)

        self._view_scale = scale
        self._view_x = offset_x
        self._view_y = offset_y
        self._has_canvas_transform = True

    def scaled_photo(self, path, size, cache, contain=False):
        """Carrega e redimensiona PNG mantendo transparência e referência Tk viva."""
        width, height = max(1, int(size[0])), max(1, int(size[1]))
        cache_key = (str(path), width, height, bool(contain))
        if cache_key not in cache:
            with Image.open(path) as source:
                image = source.convert("RGBA")
                if contain:
                    image = ImageOps.contain(
                        image, (width, height), method=Image.Resampling.LANCZOS
                    )
                else:
                    image = image.resize(
                        (width, height), Image.Resampling.LANCZOS
                    )
            cache[cache_key] = ImageTk.PhotoImage(image, master=self.root)
        return cache[cache_key]

    def draw_scene(self, scene_id, center_x=512, center_y=372):
        """Renderiza fundo cinematográfico, objetos independentes e hotspots clicáveis."""
        try:
            scene = self.scene_manager.get(scene_id)
            self.active_scene = scene_id
            layered = self.object_scene_data.get(scene_id)
            viewport = self.SCENE_VIEWPORT
            left, top, right, bottom = viewport
            view_w, view_h = right - left, bottom - top

            # O fundo ilustrado permanece visível; as camadas independentes são
            # desenhadas por cima e podem ser movidas/redimensionadas no manifesto.
            background = Path(__file__).resolve().parent / scene.get("background", "")
            if background.is_file():
                photo = self.scaled_photo(background, (view_w, view_h), self.scene_images)
                self.canvas.create_image(
                    (left + right) / 2, (top + bottom) / 2,
                    image=photo, anchor="center", tags=("scene_background",)
                )
            else:
                self.draw_scene_fallback(scene_id)

            if not layered:
                scene_hotspots = scene.get("hotspots", [])
            else:
                object_root = Path(__file__).resolve().parent / "assets" / "objetos"
                hotspot_by_object = {
                    item.get("object"): item.get("id")
                    for item in layered.get("hotspots", [])
                    if item.get("object")
                }
                for obj in sorted(layered.get("objects", []), key=lambda item: item.get("z", 0)):
                    if not obj.get("visible", True):
                        continue
                    hotspot_id = hotspot_by_object.get(obj["id"])
                    object_state = self.game.get_object_state(hotspot_id) if hotspot_id else "0"
                    asset_name = obj.get("asset_states", {}).get(object_state, obj.get("asset", ""))
                    asset = object_root / asset_name
                    if not asset.is_file():
                        # Variante ausente? Mantém o sprite-base para não sumir com o objeto.
                        asset = object_root / obj.get("asset", "")
                    if not asset.is_file():
                        continue

                    # x/y/w/h são frações do viewport. O sprite preserva sua
                    # proporção original dentro da caixa configurada pelo editor.
                    box_w = max(1, round(obj["w"] * view_w))
                    box_h = max(1, round(obj["h"] * view_h))
                    photo = self.scaled_photo(asset, (box_w, box_h), self.object_images, contain=True)
                    x = left + (obj["x"] + obj["w"] / 2) * view_w
                    y = top + (obj["y"] + obj["h"] / 2) * view_h
                    self.canvas.create_image(
                        x, y, image=photo, anchor="center",
                        tags=("scene_object", f"object:{obj['id']}")
                    )
                scene_hotspots = layered.get("hotspots", [])

            # Luz diegética: feixe suave projetado a partir da posição do agente.
            if self.game.get_tool_state("lanterna") and self.game.get_tool_resource("lanterna") > 0:
                beam_x = left + view_w * 0.50
                beam_y = bottom - 4
                self.canvas.create_polygon(
                    beam_x, beam_y,
                    left + view_w * 0.22, top + 8,
                    left + view_w * 0.78, top + 8,
                    fill="#e6d4a6", outline="", stipple="gray75",
                    tags=("flashlight_overlay",)
                )
                self.canvas.create_polygon(
                    beam_x, beam_y,
                    left + view_w * 0.36, top + 22,
                    left + view_w * 0.64, top + 22,
                    fill="#f0e2bd", outline="", stipple="gray75",
                    tags=("flashlight_overlay",)
                )

            # Modo câmera transforma a mesma cena em feed analógico de vigilância.
            if self.game.get_tool_state("camera"):
                for scan_y in range(top + 3, bottom - 2, 6):
                    self.canvas.create_line(left + 2, scan_y, right - 2, scan_y,
                                            fill="#102b22", width=1, tags=("camera_scanline",))
                self.rect(left + 12, top + 10, left + 156, top + 37, "#06140f", "#6caa8b", 1)
                self.canvas.create_oval(left + 20, top + 17, left + 29, top + 26,
                                        fill="#e35d4d", outline="")
                self.text(left + 39, top + 23, "REC  /  CAM-01", 7, "#9ce2b5")
                self.rect(left + 4, top + 4, right - 4, bottom - 4, "", "#70a98c", 1)

            evidence_ids = {
                item.get("id") for item in (self.game.state or {}).get("evidence", [])
                if item.get("mission") == (self.game.mission or {}).get("id")
            }
            for index, hotspot in enumerate(scene_hotspots, 1):
                bounds = SceneManager.map_bounds(hotspot["bounds"], viewport)
                x1, y1, x2, y2 = bounds
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                found = hotspot["id"] in evidence_ids
                marker = "#79c5a5" if found else "#e7b566"

                # Marcador pequeno; a área clicável cobre o objeto, não a moldura.
                self.canvas.create_oval(
                    cx - 11, cy - 11, cx + 11, cy + 11,
                    fill="#101923", outline=marker, width=2,
                    tags=("hotspot_marker",)
                )
                self.canvas.create_text(
                    cx, cy, text="✓" if found else str(index),
                    fill=marker, font=("Consolas", 9, "bold"),
                    tags=("hotspot_marker",)
                )
                self.targets.append((bounds, lambda h=hotspot: self.inspect_hotspot(h)))
        except (SceneError, tk.TclError, OSError, KeyError, ValueError):
            self.active_scene = None
            self.draw_scene_fallback(scene_id)

    def draw_scene_fallback(self, scene_id):
        # Scene-specific geometry is intentionally native Canvas and editable.
        if scene_id == "agencia":
            self.rect(110,245,914,510,"#0c1420","#a47d4b",4)
            self.rect(135,270,889,485,"#101b2a","#344354",2)
            self.rect(180,310,310,445,"#26384a")
            self.rect(650,310,780,445,"#26384a")
            self.text(480,365,"TURNOS ZERO",35,self.GOLD)
            self.text(480,410,"AGÊNCIA DE SERVIÇOS EXTRAORDINÁRIOS",11,self.TEXT)
        elif scene_id == "loja_24h":
            self.rect(110,255,300,520,"#111c27","#81909a",3)
            for y in (285,350,415,480): self.rect(125,y,285,y+35,"#344c5a")
            self.rect(390,260,555,520,"#081521","#9db0ba",4)
            self.rect(650,280,850,520,"#1d2b36","#a47c49",3)
        elif scene_id == "edificio_9":
            self.rect(160,245,360,520,"#111b27","#87919a",4)
            self.rect(600,245,800,520,"#111b27","#87919a",4)
            self.rect(410,240,550,520,"#080e16","#b59664",5)
            self.text(480,360,"0",42,self.GOLD)
        elif scene_id == "cinema_vazio":
            self.rect(250,235,710,390,"#e9e6d9","#806647",4)
            for x in (90,270,450,630,810): self.rect(x,430,x+120,520,"#442c35","#9b7854",3)
        else:
            self.rect(120,245,840,520,"#162632","#45606a",4)
            self.rect(370,280,590,485,"#172833","#b39a66",5)
            self.rect(400,310,560,395,"#08141d","#5c8e89",3)

    def toggle_field_tool(self, tool):
        try:
            self.game.toggle_tool(tool)
            self.play_effect("acerto.wav")
        except (RuntimeError, ValueError):
            self.play_effect("erro.wav")
        self.show_investigation()

    def inspect_hotspot(self, hotspot):
        """Abre a ficha de inspeção; não coleta evidência apenas por selecionar."""
        self.current_hotspot = hotspot
        self.show_inspection()

    def show_inspection(self):
        self.start_ambience()
        hotspot = self.current_hotspot
        if not hotspot:
            self.show_investigation()
            return
        self.screen = "inspection"
        self.clear()
        self.rect(0, 0, self.W, self.H, self.BG)
        self.header(
            "ANÁLISE DE CAMPO",
            hotspot.get("label", hotspot["id"]),
            "EXAMINE A EVIDÊNCIA E DEPOIS DECIDA SE VAI MANIPULAR O OBJETO."
        )
        self.rect(55, 190, 435, 660, "#101923", "#786044", 2)
        self.rect(455, 190, 969, 660, "#101923", "#786044", 2)
        self.text(80, 218, "OBJETO SOB ANÁLISE", 9, self.GOLD, "nw")

        # O mesmo sprite da missão é ampliado, sem editar ou achatar o fundo.
        scene_data = self.object_scene_data.get(self.active_scene or "", {})
        object_id = hotspot.get("object")
        obj = next(
            (item for item in scene_data.get("objects", []) if item.get("id") == object_id),
            None
        )
        state = self.game.get_object_state(hotspot["id"])
        asset_name = obj.get("asset_states", {}).get(state, obj["asset"]) if obj else None
        asset = (Path(__file__).resolve().parent / "assets" / "objetos" / asset_name) if asset_name else None
        if asset and not asset.is_file() and obj:
            asset = Path(__file__).resolve().parent / "assets" / "objetos" / obj["asset"]
        if asset and asset.is_file():
            photo = self.scaled_photo(asset, (300, 365), self.object_images, contain=True)
            self.canvas.create_image(245, 425, image=photo, anchor="center")
        else:
            self.rect(110, 275, 380, 580, "#080e14", "#364955", 1)
            self.text(245, 425, "ARQUIVO VISUAL\nINDISPONÍVEL", 12, self.MUTED)

        if hotspot["id"] == "terminal":
            # Interface diegética CRT: logs verdes, fósforo e scanlines suaves.
            self.text(485, 218, "TERMINAL DE CONTROLE // ACESSO OMEGA", 9, "#d6ad70", "nw")
            self.rect(485, 244, 940, 382, "#020a08", "#527d68", 2)
            self.rect(492, 251, 933, 375, "#03140f", "#1b4b38", 1)
            for scan_y in range(255, 373, 5):
                self.rect(496, scan_y, 929, scan_y + 1, "#0b281e")
            logs = [
                "FIELD LOG / SESSION 00011",
                "---------------------------------------",
                "SESSION STARTED: 11 YEARS AGO",
                "USER: " + self.game.state.get("player", "UNKNOWN").upper(),
                "CONNECTION: PERSISTENT",
                "EMPLOYEE STATUS: " + ("ACTIVE" if state == "1" else "UNVERIFIED"),
            ]
            for row, line in enumerate(logs):
                color = "#a0e5b6" if row != 5 else ("#e7ad65" if state == "1" else "#77bf97")
                self.text(508, 267 + row * 17, line, 8, color, "nw")
            self.text(485, 390, "SAÍDA DO TERMINAL", 9, self.GOLD, "nw")
        else:
            self.text(485, 218, "REGISTRO DE ANOMALIA", 9, "#d6ad70", "nw")
            self.text(485, 254, hotspot.get("label", hotspot["id"]).upper(), 16, self.TEXT, "nw", 440)
            self.text(
                485, 300, hotspot.get("finding", "Nenhuma evidência descrita."),
                11, self.TEXT, "nw", 435
            )

        interaction = hotspot.get("interaction", {})
        states = interaction.get("states", ["intacto", "alterado"])
        responses = interaction.get("responses", ["Nada muda.", "O objeto reage de forma anormal."])
        state_index = 1 if state == "1" else 0
        self.text(485, 390, "ESTADO DO OBJETO", 9, self.GOLD, "nw")
        self.text(485, 416, states[state_index], 12, "#83c4a8" if state_index else self.MUTED, "nw")
        self.text(485, 452, responses[state_index], 10, self.TEXT, "nw", 430)

        mission_id = self.game.mission["id"]
        evidence_found = any(
            item.get("id") == hotspot["id"] and item.get("mission") == mission_id
            for item in self.game.state.get("evidence", [])
        )
        self.text(485, 510, "RELATÓRIO DE CAMPO", 9, self.GOLD, "nw")
        if evidence_found:
            self.text(485, 535, "EVIDÊNCIA REGISTRADA", 10, "#83c4a8", "nw")
        elif self.game.get_tool_state("camera") and self.game.get_tool_resource("camera") > 0:
            self.button(
                485, 526, 410,
                f"FOTOGRAFAR E REGISTRAR  /  {self.game.get_tool_resource('camera')} RESTANTES",
                self.capture_current_evidence, 40
            )
        else:
            self.button(485, 526, 410, "EXAMINAR E REGISTRAR EVIDÊNCIA", self.collect_current_evidence, 40)

        if interaction:
            interaction_label = interaction.get("label", "INTERAGIR COM OBJETO")
            if state_index and not interaction.get("repeatable", False):
                self.text(485, 588, "INTERAÇÃO JÁ REALIZADA", 9, "#d6ad70", "nw")
            else:
                self.button(485, 575, 410, interaction_label, self.interact_current_object, 40)

        self.button(485, 625, 410, "VOLTAR AO AMBIENTE", self.show_investigation, 34)
        self.bind_clicks()

    def capture_current_evidence(self):
        hotspot = self.current_hotspot
        if not hotspot:
            return
        finding = hotspot.get("finding", "Registro fotográfico de anomalia.")
        try:
            self.game.consume_tool_resource("camera", 1)
            self.game.record_evidence(hotspot["id"], "FOTO / " + finding)
            if self.game.get_tool_state("camera"):
                self.game.toggle_tool("camera")
            self.play_effect("acerto.wav")
        except (RuntimeError, ValueError):
            self.play_effect("erro.wav")
        self.show_inspection()

    def collect_current_evidence(self):
        hotspot = self.current_hotspot
        if not hotspot:
            return
        finding = hotspot.get("finding", "Evidência visual identificada.")
        try:
            self.game.record_evidence(hotspot["id"], finding)
            self.play_effect("acerto.wav")
        except RuntimeError:
            pass
        self.show_inspection()

    def interact_current_object(self):
        hotspot = self.current_hotspot
        if not hotspot:
            return
        interaction = hotspot.get("interaction", {})
        current = self.game.get_object_state(hotspot["id"])
        if current == "1" and not interaction.get("repeatable", False):
            self.show_inspection()
            return
        next_state = "0" if current == "1" else "1"
        self.game.set_object_state(hotspot["id"], next_state)
        self.play_effect("porta.wav")
        self.show_inspection()

    def click(self, event):
        if self._view_scale <= 0:
            return
        logical_x = (event.x - self._view_x) / self._view_scale
        logical_y = (event.y - self._view_y) / self._view_scale
        if not (0 <= logical_x <= self.W and 0 <= logical_y <= self.H):
            return
        for (x1, y1, x2, y2), callback in reversed(self.targets):
            if x1 <= logical_x <= x2 and y1 <= logical_y <= y2:
                callback()
                return

    def bind_clicks(self):
        # O desenho lógico é transformado uma vez; Configure atualiza a escala.
        self.resize_canvas()
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.config(cursor="hand2")

    def header(self, eyebrow, title, subtitle=""):
        """Cabeçalho institucional compartilhado por todas as telas."""
        self.rect(0, 0, self.W, 12, "#070b12")
        self.rect(32, 22, self.W - 32, 23, "#8f7045")
        self.text(42, 42, "AGÊNCIA  /  SERVIÇOS EXTRAORDINÁRIOS", 8, self.MUTED, "nw")
        self.text(self.W - 42, 42, "ARQUIVO 00  ·  ACESSO RESTRITO", 8, self.MUTED, "ne")
        self.text(56, 76, eyebrow.upper(), 9, self.GOLD, "nw")
        self.text(56, 112, title, 25, self.TEXT, "nw")
        if subtitle:
            self.text(56, 151, subtitle, 10, self.MUTED, "nw", 900)
        self.rect(56, 174, self.W - 56, 175, "#594a35")
        self.rect(56, 178, 170, 179, "#a17c49")

    def menu(self):
        """Menu principal simétrico, com hierarquia tipográfica sem duplicação."""
        self.stop_ambience()
        self.screen = "menu"
        self.clear()
        self.rect(0, 0, self.W, self.H, "#080e18")

        # Grade arquitetônica discreta e volumes laterais; sem lettering na arte.
        for x in range(32, self.W, 80):
            self.rect(x, 0, x + 1, self.H, "#101b29")
        self.rect(0, 555, self.W, 145, "#070c14")
        for x, top, width in ((25, 250, 95), (150, 190, 72), (802, 205, 88), (920, 270, 80)):
            self.rect(x, top, x + width, 555, "#0d1724")
            for wy in range(top + 28, 520, 58):
                self.rect(x + 14, wy, x + 22, wy + 15, "#29384a")

        # Moldura principal e filetes internos, todos ancorados no centro.
        self.rect(72, 92, 952, 610, "#0d1725", "#9a7848", 2)
        self.rect(84, 104, 940, 598, "#0d1725", "#35465a", 1)
        self.rect(100, 120, 924, 582, "#0d1725", "#1e2c3d", 1)

        cx = self.W // 2
        self.text(cx, 180, "AGÊNCIA DE SERVIÇOS EXTRAORDINÁRIOS", 11, self.MUTED)
        self.text(cx, 224, "DIRETORIA DE OPERAÇÕES ANÔMALAS", 8, self.GOLD)

        # Linhas laterais não atravessam o título.
        self.rect(220, 293, 355, 295, "#b18a50")
        self.rect(669, 293, 804, 295, "#b18a50")
        self.text(cx, 292, "TURNOS ZERO", 38, self.GOLD)

        self.rect(380, 342, 664, 343, "#536174")
        self.text(cx, 376, "O EXPEDIENTE TERMINA. NEM TODOS VOLTAM PARA CASA.", 11, self.TEXT)

        # Ação principal e continuação têm dimensões idênticas e alinhamento comum.
        self.button(365, 425, 294, "NOVO CONTRATO", self.new_campaign, 50)
        if self.game.state:
            self.button(365, 492, 294, "CONTINUAR CAMPANHA", self.continue_campaign, 46)
            status = self.game.state.get("status", "—").replace("_", " ").upper()
            self.text(cx, 560, f"ARQUIVO ATUAL: {status}", 9, self.GOLD)
        else:
            self.text(cx, 515, "NENHUM CONTRATO ATIVO", 9, self.MUTED)

        self.text(cx, 660, "ARQUIVO INTERNO  ·  ACESSO RESTRITO  ·  V. 1.2", 9, self.MUTED)
        self.bind_clicks()

    def draw_backdrop(self, filename, y=390, x=None, width=None, height=None):
        path = Path(__file__).resolve().parent / "assets" / "ambientes" / filename
        if not path.is_file():
            return False
        try:
            with Image.open(path) as source:
                native_w, native_h = source.size
            target_w = width or native_w
            target_h = height or native_h
            photo = self.scaled_photo(path, (target_w, target_h), self.scene_images)
            self.canvas.create_image(
                x if x is not None else self.W // 2, y,
                image=photo, anchor="center"
            )
            return True
        except (OSError, tk.TclError, ValueError):
            return False

    def new_campaign(self):
        player = simpledialog.askstring("Novo contrato", "Nome para o crachá:", parent=self.root)
        if player is None:
            return
        self.screen = "difficulty"
        self.clear()
        self.rect(0, 0, self.W, self.H, self.BG)
        self.header(
            "RECURSOS HUMANOS / ADMISSÃO", "Escolha seu vínculo",
            "A agência oferece proteção limitada. A dívida permanece sob sua responsabilidade."
        )

        # A mesa/ambiente da agência fica à direita; os documentos ocupam uma
        # coluna à esquerda e deixam a arte visível, em vez de cobri-la inteira.
        self.draw_backdrop("agencia_menu.png", y=435, x=755, width=520, height=293)
        self.rect(58, 190, 480, 278, "#0d1521", "#9a7848", 1)
        self.text(82, 216, "DÍVIDA CONTRATUAL", 10, "#d98b75", "nw")
        self.text(82, 247, "− R$ 1.000.000", 22, "#e58d83", "nw")
        self.text(82, 273, "Cada serviço concluído reduz sua dívida.", 9, self.TEXT, "nw", 365)

        descriptions = [
            ("estagiario", "ESTAGIÁRIO", "5 estabilidade · suporta 2 violações"),
            ("efetivo", "EFETIVO", "4 estabilidade · 1 violação encerra o contrato"),
            ("terceirizado", "TERCEIRIZADO", "3 estabilidade · 1 violação encerra o contrato"),
        ]
        for i, (key, label, desc) in enumerate(descriptions):
            y = 300 + i * 112
            self.rect(58, y, 480, y + 92, "#101a28", "#8b6b45", 1)
            self.text(82, y + 28, label, 13, self.GOLD, "nw")
            self.text(82, y + 55, desc, 8, self.MUTED, "nw", 340)
            self.button(
                300, y + 27, 155, "ASSINAR",
                lambda k=key, p=player: self.create_campaign(p, k), 40
            )
        self.text(755, 610, "ARQUIVO INTERNO  ·  ACESSO RESTRITO", 8, self.MUTED)
        self.bind_clicks()

    def create_campaign(self, player, difficulty):
        self.game.start_campaign(player,difficulty)
        self.show_contract()

    def continue_campaign(self):
        state=self.game.state
        if not state:
            self.menu()
        elif state["status"]=="on_shift":
            self.show_investigation()
        elif state["status"]=="between_shifts":
            self.show_contract()
        else:
            self.show_ending()

    def show_contract(self):
        """Briefing em formato de dossiê, mantendo a arte do local visível em 16:9."""
        self.stop_ambience()
        self.screen = "briefing"
        mission = self.game.mission
        self.clear()
        self.rect(0, 0, self.W, self.H, self.BG)

        scene_id = scene_for_mission(mission["id"])
        background = {
            "loja_24h": "loja_24_horas.png",
            "edificio_9": "edificio_residencial.png",
            "cinema_vazio": "cinema_ultima_sessao.png",
            "laboratorio": "laboratorio_experimental.png",
        }.get(scene_id)

        # A imagem ocupa uma janela 16:9 própria; o dossiê fica na coluna lateral.
        if background:
            self.draw_backdrop(background, y=378, x=365, width=650, height=366)
        self.rect(40, 195, 690, 561, "", "#a47c4b", 2)
        self.rect(710, 195, 984, 561, "#0b141e", "#9a7848", 2)

        self.header(
            "ORDEM DE SERVIÇO / CONFIDENCIAL",
            mission["title"],
            mission["location"]
        )

        state = self.game.state
        debt = max(0, -state["cash"])
        reward = 50 * (2 ** state["shift_index"])
        risk = 2 ** state["shift_index"]

        self.text(730, 218, "DÍVIDA CONTRATUAL", 9, "#d6ad70", "nw")
        self.text(730, 250, f"R$ {debt:,}".replace(",", "."), 22, "#e58d83", "nw")
        self.rect(728, 270, 966, 271, "#4d3a35")
        self.text(730, 290, f"PAGAMENTO: R$ {reward:,}".replace(",", "."), 10, "#e8c17e", "nw")
        self.text(730, 312, f"NÍVEL DE RISCO: x{risk}", 9, "#db8875", "nw")

        self.text(730, 348, "OBJETIVO DO SERVIÇO", 9, self.GOLD, "nw")
        self.text(730, 372, mission["brief"], 9, self.TEXT, "nw", 230)

        self.text(730, 438, "PROTOCOLOS DE SEGURANÇA", 9, self.GOLD, "nw")
        for index, rule in enumerate(mission["rules"][:3]):
            self.text(733, 462 + index * 29, f"{index + 1:02d}  {rule}", 8, self.MUTED, "nw", 225)

        self.text(55, 595, "ARQUIVO VISUAL DO LOCAL  ·  EXAMINE O AMBIENTE APÓS ASSINAR", 8, self.MUTED, "nw")
        self.text(55, 622, "A remuneração só é creditada se o agente concluir o expediente.", 8, "#c59a72", "nw")
        self.button(710, 610, 274, "ASSINAR E INICIAR TURNO  [ENTER]", self.start_shift, 44)
        self.bind_clicks()

    def start_shift(self):
        if self.game.state["status"]=="between_shifts":
            self.game.start_shift()
        self.show_investigation()

    def show_investigation(self):
        """Tela de campo com cenário 16:9 e painel de objetos realmente examináveis."""
        self.screen = "investigation"
        self.start_ambience()
        mission = self.game.mission
        state = self.game.state
        scene_id = scene_for_mission(mission["id"])
        self.clear()
        self.rect(0, 0, self.W, self.H, self.BG)

        self.header(
            "INVESTIGAÇÃO DE CAMPO",
            mission["title"],
            f"ESTABILIDADE: {state['sanity']}  |  FALHAS: {state['mistakes']}  |  "
            f"DÍVIDA: R$ {max(0, -state['cash']):,}  |  RISCO x{state.get('risk_multiplier', 2 ** state['shift_index'])}".replace(",", ".")
        )

        # Área visual com proporção 16:9. Sprites e alvos usam o mesmo viewport.
        left, top, right, bottom = self.SCENE_VIEWPORT
        self.rect(left - 5, top - 5, right + 5, bottom + 5, "#0b111a", "#8e704c", 2)
        if scene_id:
            self.draw_scene(scene_id, (left + right) / 2, (top + bottom) / 2)

        # Painel lateral: instruções, estado das pistas e acesso por lista.
        self.rect(710, 195, 984, 561, "#0b141e", "#9a7848", 2)
        self.text(730, 218, "OBJETIVO DE CAMPO", 9, self.GOLD, "nw")
        self.text(730, 244, "Investigue os objetos, registre evidências e siga os protocolos.", 9, self.TEXT, "nw", 230)

        scene_data = self.object_scene_data.get(scene_id, {})
        hotspots = scene_data.get("hotspots", self.scene_manager.get(scene_id).get("hotspots", [])) if scene_id else []
        evidence = [
            item for item in state.get("evidence", [])
            if item.get("mission") == mission["id"]
        ]
        found_ids = {item.get("id") for item in evidence}
        self.rect(728, 293, 966, 294, "#354657")
        found_count = sum(1 for hotspot in hotspots if hotspot["id"] in found_ids)
        self.text(730, 315, f"PISTAS: {found_count}/{len(hotspots)}", 10, "#8bc9a0" if evidence else "#d6ad70", "nw")
        self.text(730, 340, "OBJETOS INTERATIVOS", 8, self.MUTED, "nw")

        for index, hotspot in enumerate(hotspots[:4], 1):
            y = 360 + (index - 1) * 45
            collected = hotspot["id"] in found_ids
            mark = "✓" if collected else f"{index:02d}"
            label = hotspot.get("label", hotspot["id"])
            self.button(
                728, y, 238,
                f"{mark}  {label[:24]}",
                lambda h=hotspot: self.inspect_hotspot(h),
                36
            )

        self.button(728, 526, 238, "ABRIR CENTRAL CCTV / 06 CANAIS", self.show_surveillance, 31)

        # Barra de equipamento fora do cenário: não obstrui os pontos clicáveis.
        tool_states = state.setdefault("tool_states", {})
        lantern_charge = self.game.get_tool_resource("lanterna")
        radio_uses = self.game.get_tool_resource("radio")
        camera_film = self.game.get_tool_resource("camera")
        lantern_label = f"LANTERNA {'ON' if tool_states.get('lanterna', True) else 'OFF'}  {lantern_charge}%"
        radio_label = f"RÁDIO {'ON' if tool_states.get('radio', False) else 'OFF'}  {radio_uses}"
        camera_label = f"CÂMERA {'ON' if tool_states.get('camera', False) else 'OFF'}  {camera_film}"
        self.button(40, 610, 150, lantern_label, lambda: self.toggle_field_tool("lanterna"), 40)
        self.button(200, 610, 150, radio_label, lambda: self.toggle_field_tool("radio"), 40)
        self.button(360, 610, 150, camera_label, lambda: self.toggle_field_tool("camera"), 40)
        self.button(520, 610, 150, "DOSSIÊ", self.show_evidence_report, 40)
        self.button(710, 610, 274, "AVANÇAR PARA A OCORRÊNCIA", self.show_task, 40)
        self.bind_clicks()

    def show_surveillance(self):
        """Central diegética de seis câmeras, com recortes reais do cenário atual."""
        self.screen = "surveillance"
        self.start_ambience()
        mission = self.game.mission
        scene_id = scene_for_mission(mission["id"])
        scene = self.scene_manager.get(scene_id)
        scene_data = self.object_scene_data.get(scene_id, {})
        hotspots = scene_data.get("hotspots", scene.get("hotspots", []))
        if hotspots and not self.current_camera_hotspot:
            self.current_camera_hotspot = hotspots[0]

        self.clear()
        self.rect(0, 0, self.W, self.H, "#050b0d")
        self.header(
            "CENTRAL DE VIGILÂNCIA / SINAL ANALÓGICO",
            "Monitoramento de campo",
            f"{mission['title']}  ·  {len(hotspots)} PONTO(S) INTERATIVO(S)  ·  "
            f"FILME: {self.game.get_tool_resource('camera')} FOTOS"
        )

        self.rect(35, 190, 682, 572, "#08120f", "#527d68", 2)
        self.text(55, 207, "MATRIZ DE CÂMERAS  /  CANAIS LOCAIS", 8, "#86c7a5", "nw")

        background_name = {
            "loja_24h": "loja_24_horas.png",
            "edificio_9": "edificio_residencial.png",
            "cinema_vazio": "cinema_ultima_sessao.png",
            "laboratorio": "laboratorio_experimental.png",
        }.get(scene_id)
        background_path = Path(__file__).resolve().parent / "assets" / "ambientes" / (background_name or "")
        source_image = None
        if background_path.is_file():
            try:
                with Image.open(background_path) as source:
                    source_image = source.convert("RGB")
            except OSError:
                source_image = None

        channel_names = [
            "ENTRADA", "CORREDOR", "ÁREA CENTRAL",
            "ACESSO LATERAL", "FUNDO", "PONTO CEGO"
        ]
        grid_x = [55, 268, 481]
        grid_y = [230, 395]
        self.surveillance_images = {}

        for index in range(6):
            col = index % 3
            row = index // 3
            x = grid_x[col]
            y = grid_y[row]
            width, height = 194, 150
            hotspot = hotspots[index % len(hotspots)] if hotspots else None
            selected = bool(
                hotspot and self.current_camera_hotspot
                and hotspot["id"] == self.current_camera_hotspot.get("id")
            )
            outline = "#d9b26d" if selected else "#38594d"
            self.rect(x, y, x + width, y + height, "#020807", outline, 2)

            feed = None
            if source_image is not None:
                src_w, src_h = source_image.size
                crop_col = index % 3
                crop_row = index // 3
                x1 = int(crop_col * src_w / 3)
                x2 = int((crop_col + 1) * src_w / 3)
                y1 = int(crop_row * src_h / 2)
                y2 = int((crop_row + 1) * src_h / 2)
                crop = source_image.crop((x1, y1, x2, y2)).resize((178, 108), Image.Resampling.LANCZOS)
                cache_key = (scene_id, index, src_w, src_h)
                if cache_key not in self.surveillance_images:
                    self.surveillance_images[cache_key] = ImageTk.PhotoImage(crop, master=self.root)
                feed = self.surveillance_images[cache_key]

            if feed is not None:
                self.canvas.create_image(x + 8, y + 8, image=feed, anchor="nw")
            else:
                self.rect(x + 8, y + 8, x + 186, y + 116, "#020807", "#27493c", 1)
                self.text(x + 97, y + 62, "SEM SINAL", 9, "#d07762")

            # CRT scanlines and timestamp make each panel read as a surveillance feed.
            for scan_y in range(y + 10, y + 115, 5):
                self.rect(x + 8, scan_y, x + 186, scan_y + 1, "#071c16")
            self.rect(x + 8, y + 8, x + 186, y + 116, "", "#48765c", 1)
            self.text(x + 14, y + 124, f"CAM-{index + 1:02d}  /  {channel_names[index]}", 7, "#94c7a7", "nw")
            self.text(x + 180, y + 124, "REC", 7, "#d76a57", "ne")

            if hotspot:
                self.targets.append((
                    (x, y, x + width, y + height),
                    lambda h=hotspot: self.select_surveillance_feed(h)
                ))

        # Painel do operador: seleciona o alvo e permite registrar foto.
        self.rect(730, 190, 985, 572, "#0b1517", "#8a7049", 2)
        self.text(750, 215, "ESTAÇÃO DO OPERADOR", 9, "#d6ad70", "nw")
        self.text(750, 250, "CANAL SELECIONADO", 8, "#8fc9a8", "nw")
        selected_label = (
            self.current_camera_hotspot.get("label", "—")
            if self.current_camera_hotspot else "Nenhum canal selecionado"
        )
        self.text(750, 280, selected_label.upper(), 13, self.TEXT, "nw", 215)
        self.text(750, 325, "Aproxime a imagem, compare o ambiente e registre uma anomalia.", 9, self.MUTED, "nw", 215)

        remaining = self.game.get_tool_resource("camera")
        camera_active = self.game.get_tool_state("camera")
        self.text(750, 390, f"FILME DISPONÍVEL: {remaining}", 10, "#d6ad70", "nw")
        if camera_active:
            self.text(750, 418, "CÂMERA ARMADA", 9, "#8bc9a0", "nw")
        else:
            self.text(750, 418, "CÂMERA EM ESPERA", 9, self.MUTED, "nw")

        if self.current_camera_hotspot:
            evidence_found = any(
                item.get("id") == self.current_camera_hotspot["id"]
                and item.get("mission") == mission["id"]
                for item in self.game.state.get("evidence", [])
            )
            if evidence_found:
                self.text(750, 455, "EVIDÊNCIA JÁ ARQUIVADA", 8, "#8bc9a0", "nw")
            elif remaining > 0:
                self.button(750, 470, 215, "FOTOGRAFAR CANAL", self.capture_surveillance_feed, 36)
            else:
                self.text(750, 480, "SEM FILME. USE A OBSERVAÇÃO MANUAL.", 8, "#d07762", "nw", 210)

        self.button(750, 520, 215, "VOLTAR À INVESTIGAÇÃO", self.show_investigation, 36)
        self.bind_clicks()

    def select_surveillance_feed(self, hotspot):
        self.current_camera_hotspot = hotspot
        self.show_surveillance()

    def capture_surveillance_feed(self):
        hotspot = self.current_camera_hotspot
        if not hotspot:
            return
        try:
            self.game.consume_tool_resource("camera", 1)
            self.game.record_evidence(
                hotspot["id"],
                "FOTO CCTV / " + hotspot.get("finding", "Anomalia registrada no circuito interno.")
            )
            self.play_effect("acerto.wav")
        except (RuntimeError, ValueError):
            self.play_effect("erro.wav")
        self.show_surveillance()

    def show_evidence_report(self):
        """Dossiê diegético com todas as evidências registradas no contrato atual."""
        self.screen = "evidence_report"
        mission = self.game.mission
        state = self.game.state
        evidence = [
            item for item in state.get("evidence", [])
            if item.get("mission") == mission["id"]
        ]
        self.clear()
        self.rect(0, 0, self.W, self.H, self.BG)
        self.header(
            "ARQUIVO DE CAMPO / CONFIDENCIAL",
            "Dossiê de evidências",
            f"{mission['title']}  ·  {len(evidence)} REGISTRO(S) ARQUIVADO(S)"
        )
        self.rect(70, 195, 954, 570, "#0b141d", "#9a7848", 2)
        self.text(100, 220, "REGISTROS CONFIRMADOS", 9, self.GOLD, "nw")
        self.text(910, 220, "ARQ / 00", 8, self.MUTED, "ne")
        self.rect(92, 244, 932, 245, "#354454")

        if not evidence:
            self.text(512, 355, "NENHUMA EVIDÊNCIA REGISTRADA", 13, "#d6ad70")
            self.text(512, 388, "Volte à investigação e examine os objetos marcados.", 9, self.MUTED)
        else:
            row_height = min(74, 300 / max(1, len(evidence)))
            for index, item in enumerate(evidence):
                y = 254 + index * row_height
                if y + row_height > 535:
                    break
                self.rect(92, y, 932, y + row_height - 5, "#101d28", "#405565", 1)
                self.text(108, y + 12, f"REGISTRO {index + 1:02d}  /  {item.get('id', '—').upper()}", 8, self.GOLD, "nw")
                task_number = item.get("task_index", 0) + 1
                self.text(910, y + 12, f"OCORRÊNCIA {task_number}", 7, self.MUTED, "ne")
                self.text(108, y + 34, item.get("description", "Sem descrição."), 9, self.TEXT, "nw", 785)

        self.text(100, 545, "ORIENTAÇÃO: use as pistas compatíveis para fundamentar suas decisões.", 8, self.MUTED, "nw", 780)
        self.button(565, 610, 180, "VOLTAR À INVESTIGAÇÃO", self.show_investigation, 42)
        self.button(765, 610, 180, "IR À OCORRÊNCIA", self.show_task, 42)
        self.bind_clicks()

    def show_task(self):
        self.screen="task"
        self.start_ambience()
        mission=self.game.mission
        task=self.game.task
        state=self.game.state
        self.clear()
        self.rect(0,0,self.W,self.H,self.BG)
        self.header(f"AO VIVO  /  {mission['location']}",mission["title"],
                    f"{state['player']}  |  ESTABILIDADE: {state['sanity']}  |  FALHAS: {state['mistakes']}  |  REPUTAÇÃO: {state['reputation']}  |  SALDO: R$ {state['cash']:,}".replace(",", "."))
        self.rect(70,195,954,575,"#111b28","#786044",2)
        self.rect(70,195,954,202,"#26343d")
        self.text(100,220,f"OCORRÊNCIA {state['task_index']+1} / 3",9,"#d6ad70","nw")
        self.text(100,252,"O QUE ESTÁ ACONTECENDO?",11,"#e7d9c5","nw")
        self.text(100,292,task["prompt"],14,self.TEXT,"nw",820)
        evidence=[item for item in state.get("evidence",[]) if item.get("mission")==mission["id"]]
        self.text(100,365,f"PISTAS NO RELATÓRIO: {len(evidence)}",9,"#82b9a7" if evidence else "#d6ad70","nw")
        self.text(100,388,"Escolha uma ação. A decisão errada pode encerrar seu contrato.",9,self.MUTED,"nw")
        for i,choice in enumerate(task["choices"]):
            y=420+i*48
            self.rect(112,y,912,y+40,"#1b2934","#536777",1)
            self.rect(112,y,118,y+40,"#a46e4c")
            self.text(138,y+20,str(i+1),10,"#e7d9c5")
            self.text(158,y+20,choice,10,self.TEXT,"nw")
            self.targets.append(((112,y,912,y+40),lambda n=i:self.choose(n)))
        self.button(112,570,250,"VOLTAR À INVESTIGAÇÃO",self.show_investigation,38)
        self.text(920,589,"[ESC] MENU",8,self.MUTED,"ne")
        self.bind_clicks()

    def choose(self,index):
        result=self.game.act(index)
        self.play_effect("acerto.wav" if result["correct"] else "erro.wav")
        self.show_result(result)

    def show_result(self,result):
        self.screen="result"
        self.clear()
        self.rect(0,0,self.W,self.H,self.BG)
        self.header("RELATÓRIO DE CAMPO","Ocorrência registrada",
                    "CONDUTA ACEITA" if result["correct"] else "VIOLAÇÃO DE PROTOCOLO")
        self.rect(80,205,944,520,"#101a28","#9a7848",2)
        color="#9bd1ad" if result["correct"] else "#e58d83"
        self.text(120,255,"✓" if result["correct"] else "!",34,color,"nw")
        self.text(180,265,result["message"],15,self.TEXT,"nw",700)
        if result.get("evidence_used"):
            self.text(120,325,"PISTA APLICADA À DECISÃO",11,self.GOLD,"nw")
            self.text(120,350,result.get("evidence_note",""),10,self.MUTED,"nw",760)
        if result.get("tool_warning"):
            self.text(120,485,"AVISO DE EQUIPAMENTO: "+result["tool_warning"],9,"#e58d83","nw",760)
        ending=result.get("ending")
        if ending=="survived":
            self.text(120,370,"TURNO CONCLUÍDO",18,self.GOLD,"nw")
            self.text(120,410,f"Pagamento recebido: R$ {self.game.state['last_payment']:,}".replace(",", "."),13,self.TEXT,"nw")
            self.button(650,535,230,"PRÓXIMO CONTRATO",self.advance_contract,44)
        elif ending=="missing":
            self.text(120,370,"FUNCIONÁRIO NÃO LOCALIZADO",18,"#e58d83","nw")
            self.text(120,415,self.game.state.get("last_reveal",""),12,self.MUTED,"nw",720)
            self.button(650,535,230,"ENCERRAR ARQUIVO",self.show_ending,44)
        else:
            self.button(650,535,230,"CONTINUAR",self.show_investigation,44)
        self.bind_clicks()

    def advance_contract(self):
        next_mission = self.game.next_shift()
        if next_mission is None:
            self.show_ending()
        else:
            self.show_contract()

    def show_ending(self):
        self.stop_ambience()
        self.screen="ending"
        self.clear()
        state=self.game.state or {}
        self.rect(0,0,self.W,self.H,self.BG)
        completed = state.get("status") == "campaign_completed"
        title = "Campanha concluída" if completed else "Contrato encerrado"
        subtitle = "TODOS OS LOCAIS FORAM INSPECIONADOS" if completed else f"FUNCIONÁRIO: {state.get('player','—')}"
        self.header("ARQUIVO DE PESSOAL / STATUS", title, subtitle)
        self.rect(100,220,924,530,"#101a28","#9a7848",2)
        self.text(150,280,f"STATUS: {state.get('status','—').upper()}",18,self.GOLD,"nw")
        self.text(150,340,f"Dívida restante: R$ {max(0,-state.get('cash',0)):,}".replace(",", "."),15,self.TEXT,"nw")
        self.text(150,375,f"Valor quitado: R$ {state.get('cash',0)+state.get('initial_debt',1000000):,}".replace(",", "."),13,self.MUTED,"nw")
        self.text(150,405,f"Reputação acumulada: {state.get('reputation',0)}",13,self.MUTED,"nw")
        if completed:
            self.text(150,415,f"Locais concluídos: {len(state.get('completed', []))}/{len(MISSIONS)}",13,self.MUTED,"nw")
            self.text(150,455,"Seu expediente terminou. O arquivo permanece aberto.",12,self.MUTED,"nw")
        else:
            self.text(150,395,state.get("last_reveal", "A agência agradece seus serviços."),12,self.MUTED,"nw",700)
        self.button(650,555,230,"VOLTAR AO MENU",self.menu,44)
        self.bind_clicks()

def terminal():
    game=ShiftGame()
    print("=== TURNOS ZERO | AGÊNCIA DE SERVIÇOS EXTRAORDINÁRIOS ===")
    while True:
        if game.state and game.state["status"] == "campaign_completed":
            print("\nCAMPANHA CONCLUÍDA — todos os contratos foram encerrados.")
            return
        if not game.state or game.state["status"]=="ended":
            player=input("Nome no crachá (ou SAIR): ").strip()
            if player.lower()=="sair": return
            print("Vínculo: 1 Estagiário | 2 Efetivo | 3 Terceirizado")
            diff={"1":"estagiario","2":"efetivo","3":"terceirizado"}.get(input("> ").strip(),"estagiario")
            game.start_campaign(player,diff)
        if game.state["status"]=="between_shifts":
            m=game.mission
            print(f"\n{m['title']} — {m['location']}\n{m['brief']}")
            for rule in m["rules"]: print("-",rule)
            input("Pressione ENTER para iniciar o turno...")
            game.start_shift()
        if game.state["status"]=="on_shift":
            t=game.task
            scene_id=scene_for_mission(game.mission["id"])
            scene = SceneManager().get(scene_id) if scene_id else {"hotspots": []}
            collected = {item.get("id") for item in game.state.get("evidence", []) if item.get("mission") == game.mission["id"]}
            print("\nINVESTIGAÇÃO — pistas disponíveis:")
            for i, hotspot in enumerate(scene.get("hotspots", []), 1):
                status = " [INVESTIGADA]" if hotspot["id"] in collected else ""
                print(f"{i} - {hotspot.get('label', hotspot['id'])}{status}")
            print("I - investigar ponto | ENTER - seguir para ocorrência")
            command = input("> ").strip().lower()
            if command == "i" and scene.get("hotspots"):
                choice = input("Número do ponto para investigar: ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(scene["hotspots"]):
                    hotspot = scene["hotspots"][int(choice)-1]
                    if game.record_evidence(hotspot["id"], hotspot.get("finding", "Pista sem descrição.")):
                        print("EVIDÊNCIA REGISTRADA:", hotspot.get("finding", ""))
                    else:
                        print("Essa evidência já foi registrada neste contrato.")
                continue
            print("\n"+t["prompt"])
            for i,c in enumerate(t["choices"],1): print(i,"-",c)
            raw=input("Decisão (1-3): ").strip()
            if raw not in ("1","2","3"): continue
            result=game.act(int(raw)-1)
            print(result["message"])
            if result.get("evidence_used"):
                print("PISTA APLICADA:", result.get("evidence_note", ""))
            if "ending" in result:
                print("FIM DO TURNO:",result["ending"])
                if result["ending"]=="missing": return
                input("ENTER para o próximo contrato...")
                game.next_shift()

if __name__=="__main__":
    if "--terminal" in sys.argv:
        terminal()
    else:
        root=tk.Tk()
        TurnosZeroApp(root)
        root.mainloop()
