"""Launcher de Turnos Zero. A campanha antiga permanece preservada nos arquivos legados."""
import sys
import json
import tkinter as tk
from PIL import Image, ImageDraw, ImageOps, ImageTk
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
        self.current_interaction_message = None
        self.current_camera_hotspot = None
        self.current_radio_message = None
        self.current_radio_status = "READY"
        self.surveillance_images = {}
        self.ambience_active = False
        self.ambience_path = None
        self._ambience_after_id = None
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

    def wrapped_text(self, x, y, value, size=9, color=None, width=220, spacing=2):
        """Desenha texto com quebra automática e retorna o Y após a última linha."""
        item = self.canvas.create_text(
            x, y, text=value, fill=color or self.TEXT,
            font=("Consolas", size, "bold"), anchor="nw",
            width=max(40, int(width)), justify="left", spacing2=spacing
        )
        bounds = self.canvas.bbox(item)
        return bounds[3] if bounds else y

    def button(self, x, y, w, label, callback, h=48):
        self.rect(x+3,y+4,x+w+3,y+h+4,"#05070c")
        self.rect(x,y,x+w,y+h,self.PANEL,"#9b7444",2)
        self.rect(x+4,y+4,x+w-4,y+h-4,self.PANEL,"#d7ad68",1)
        # A largura explícita impede que rótulos longos ultrapassem a moldura.
        self.canvas.create_text(
            x+w/2, y+h/2, text=label, fill=self.GOLD,
            font=("Consolas", 10, "bold"), anchor="center",
            width=max(40, w-18), justify="center"
        )
        self.targets.append(((x,y,x+w,y+h),callback))

    def _ambience_file(self):
        """Escolhe a paisagem sonora do local atual, com fallback silencioso."""
        mission_id = (self.game.mission or {}).get("id")
        if mission_id:
            candidate = Path(__file__).resolve().parent / "assets" / "som" / f"{mission_id}.wav"
            if candidate.is_file():
                return candidate
        legacy = Path(__file__).resolve().parent / "assets" / "ambiente.wav"
        return legacy if legacy.is_file() else None

    def start_ambience(self):
        """Reproduz em loop a paisagem sonora própria da missão atual (Windows)."""
        path = self._ambience_file()
        if path is None:
            return
        path = str(path)
        if self.ambience_active and self.ambience_path == path:
            return
        if self.ambience_active:
            self.stop_ambience()
        try:
            import winsound
            winsound.PlaySound(
                path,
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP | winsound.SND_NODEFAULT,
            )
            self.ambience_active = True
            self.ambience_path = path
        except (ImportError, OSError):
            self.ambience_active = False
            self.ambience_path = None

    def stop_ambience(self):
        """Interrompe o loop e cancela qualquer retomada agendada."""
        if self._ambience_after_id is not None:
            try:
                self.root.after_cancel(self._ambience_after_id)
            except tk.TclError:
                pass
            self._ambience_after_id = None
        if self.ambience_active:
            try:
                import winsound
                winsound.PlaySound(None, winsound.SND_PURGE)
            except (ImportError, OSError):
                pass
        self.ambience_active = False
        self.ambience_path = None

    def play_effect(self, filename):
        """Toca um WAV curto e retoma a paisagem sonora atual após o efeito."""
        path = Path(__file__).resolve().parent / "assets" / filename
        if not path.is_file():
            return
        resume_ambience = self.ambience_active
        self.ambience_active = False
        self.ambience_path = None
        if self._ambience_after_id is not None:
            try:
                self.root.after_cancel(self._ambience_after_id)
            except tk.TclError:
                pass
            self._ambience_after_id = None
        try:
            import wave
            import winsound
            duration_ms = 900
            try:
                with wave.open(str(path), "rb") as audio:
                    duration_ms = int(audio.getnframes() / max(1, audio.getframerate()) * 1000) + 120
            except (wave.Error, OSError):
                pass
            winsound.PlaySound(
                str(path),
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
            )
            if resume_ambience:
                self._ambience_after_id = self.root.after(duration_ms, self._resume_ambience)
        except (ImportError, OSError):
            try:
                self.root.bell()
            except tk.TclError:
                pass
            if resume_ambience:
                self._ambience_after_id = self.root.after(300, self._resume_ambience)

    def _resume_ambience(self):
        self._ambience_after_id = None
        if self.screen in {"investigation", "inspection", "task", "surveillance", "radio"}:
            self.start_ambience()

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

    def draw_scene(self, scene_id, center_x=512, center_y=372, show_hotspots=True):
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

            # Luz diegética: quando a lanterna acaba ou é desligada,
            # o ambiente escurece de verdade; os marcadores continuam legíveis.
            lantern_on = self.game.get_tool_state("lanterna") and self.game.get_tool_resource("lanterna") > 0
            if lantern_on:
                battery = self.game.get_tool_resource("lanterna")
                # O feixe deve iluminar o centro sem encobrir objetos ou pistas.
                beam_width = 0.14 if battery <= 30 else 0.18
                beam_x = left + view_w * 0.50
                beam_y = bottom - 4
                self.canvas.create_polygon(
                    beam_x, beam_y,
                    left + view_w * (0.50 - beam_width), top + 8,
                    left + view_w * (0.50 + beam_width), top + 8,
                    fill="#d9c79b", outline="", stipple="gray50",
                    tags=("flashlight_overlay",)
                )
                self.canvas.create_polygon(
                    beam_x, beam_y,
                    left + view_w * (0.50 - beam_width * 0.38), top + 22,
                    left + view_w * (0.50 + beam_width * 0.38), top + 22,
                    fill="#e5d6b4", outline="", stipple="gray75",
                    tags=("flashlight_overlay",)
                )
                if battery <= 30:
                    self.canvas.create_oval(
                        left + view_w * .47, top + 8,
                        left + view_w * .53, top + 24,
                        outline="#c49a60", width=1, tags=("flashlight_overlay",)
                    )
            else:
                self.canvas.create_rectangle(
                    left, top, right, bottom,
                    fill="#000000", outline="", stipple="gray50",
                    tags=("flashlight_overlay",)
                )
                self.text(left + 14, bottom - 18, "SEM ILUMINAÇÃO / LANTERNA DESLIGADA", 7, "#d07762", "sw")

            # A presença entra no limite do campo visual quando a caça começa.
            live_state = self.game.state or {}
            if live_state.get("threat_active", False):
                mission_id = (self.game.mission or {}).get("id")
                threat_x_ratio = {
                    "loja_24h": 0.80,
                    "edificio_9": 0.52,
                    "cinema_vazio": 0.84,
                    "laboratorio": 0.70,
                }.get(mission_id, 0.78)
                ghost_x = left + view_w * threat_x_ratio
                ghost_y = top + view_h * 0.62
                self.canvas.create_oval(
                    ghost_x - 18, ghost_y - 68, ghost_x + 18, ghost_y - 24,
                    fill="#05070a", outline="#56312e", width=1,
                    tags=("anomaly_presence",)
                )
                self.canvas.create_polygon(
                    ghost_x - 13, ghost_y - 29,
                    ghost_x + 13, ghost_y - 29,
                    ghost_x + 34, ghost_y + 65,
                    ghost_x - 35, ghost_y + 65,
                    fill="#05070a", outline="#3d2928", width=1,
                    tags=("anomaly_presence",)
                )
                if lantern_on:
                    self.canvas.create_oval(
                        ghost_x - 8, ghost_y - 52, ghost_x - 3, ghost_y - 47,
                        fill="#bb554b", outline="", tags=("anomaly_presence",)
                    )
                    self.canvas.create_oval(
                        ghost_x + 3, ghost_y - 52, ghost_x + 8, ghost_y - 47,
                        fill="#bb554b", outline="", tags=("anomaly_presence",)
                    )
                self.text(left + 12, top + 16, "PRESENÇA DETECTADA", 8, "#d17870", "nw")
            elif live_state.get("is_hidden", False):
                self.canvas.create_rectangle(
                    left, top, right, bottom, fill="#020406",
                    outline="", stipple="gray50", tags=("hiding_overlay",)
                )
                self.text((left + right) / 2, top + 24, "NÃO SE MOVA", 10, "#b8c7b8")
                self.text((left + right) / 2, top + 43, "RESPIRAÇÃO CONTIDA / AGUARDE", 7, "#8ca69a")

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

            if show_hotspots:
                evidence_ids = {
                    item.get("id") for item in (self.game.state or {}).get("evidence", [])
                    if item.get("mission") == (self.game.mission or {}).get("id")
                }
                for index, hotspot in enumerate(scene_hotspots, 1):
                    # Quando o ponto pertence a um sprite, a área clicável acompanha
                    # diretamente x/y/w/h do objeto, mesmo antes de salvar o editor.
                    object_bounds = None
                    if layered and hotspot.get("object"):
                        layer_obj = next(
                            (item for item in layered.get("objects", []) if item.get("id") == hotspot["object"]),
                            None
                        )
                        if layer_obj:
                            object_bounds = [
                                layer_obj["x"], layer_obj["y"],
                                layer_obj["x"] + layer_obj["w"],
                                layer_obj["y"] + layer_obj["h"]
                            ]
                    bounds = SceneManager.map_bounds(object_bounds or hotspot["bounds"], viewport)
                    x1, y1, x2, y2 = bounds
                    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                    # Os objetos permanecem clicáveis, mas sem círculos numerados
                    # sobre a arte: a descoberta é indicada na lista lateral.
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

    def use_radio(self):
        """Consome uma transmissão e abre um canal narrativo ligado à ocorrência atual."""
        try:
            self.game.consume_tool_resource("radio", 1)
            self.current_radio_message = self.game.task.get(
                "radio_hint",
                "A transmissão chega cortada. Siga os protocolos impressos no dossiê."
            )
            self.current_radio_status = "SINAL RECEBIDO"
            self.play_effect("porta.wav")
        except (RuntimeError, ValueError):
            self.current_radio_message = "A frequência está muda. Não restam transmissões neste contrato."
            self.current_radio_status = "SEM SINAL"
            self.play_effect("erro.wav")
        self.show_radio_screen()

    def show_radio_screen(self):
        """Rádio de campo apresentado como equipamento analógico, não caixa de diálogo."""
        self.screen = "radio"
        self.start_ambience()
        self.clear()
        self.rect(0, 0, self.W, self.H, "#060d10")
        self.header("COMUNICAÇÕES / CANAL DE CAMPO", "Rádio portátil", self.current_radio_status)
        self.rect(70, 205, 954, 585, "#101a20", "#6c765f", 2)
        self.rect(95, 230, 590, 548, "#08110f", "#54765f", 3)
        self.text(120, 257, "RECEPTOR DE CURTO ALCANCE", 9, "#d7ad70", "nw")
        self.text(120, 292, "FREQUÊNCIA  03.17  /  OPERAÇÕES", 8, "#85b99c", "nw")
        # Dial analógico e barras de sintonia.
        self.rect(120, 320, 565, 322, "#020907", "#315342", 1)
        for x in range(145, 550, 24):
            self.rect(x, 335, x + 2, 345 if x % 48 else 357, "#89b59a")
        self.canvas.create_oval(290, 365, 425, 500, fill="#172322", outline="#9b8054", width=5)
        self.canvas.create_oval(312, 387, 403, 478, fill="#050a0a", outline="#4c6958", width=2)
        self.canvas.create_line(357, 433, 391, 400, fill="#d5af70", width=4)
        self.text(357, 520, "TX / RX", 8, "#8bc9a0")
        self.rect(620, 230, 930, 548, "#06100e", "#54765f", 2)
        self.text(645, 257, "TRANSMISSÃO RECEBIDA", 9, "#d7ad70", "nw")
        self.text(645, 294, self.current_radio_message or "Nenhuma transmissão.", 13, "#c8dfce", "nw", 250)
        # Ruído de fita em pequenas linhas horizontais.
        for i in range(18):
            y = 458 + i * 3
            self.rect(645, y, 910, y + 1, "#234c39" if i % 3 else "#6c9d79")
        self.text(645, 530, "ARQUIVO DE ÁUDIO / VOLÁTIL", 7, "#77927e", "nw")
        self.button(650, 610, 270, "VOLTAR AO AMBIENTE", self.show_investigation, 42)
        self.text(95, 610, f"TRANSMISSÕES RESTANTES: {self.game.get_tool_resource('radio')}", 9, "#d6ad70", "nw")
        self.bind_clicks()

    def toggle_field_tool(self, tool):
        try:
            self.game.toggle_tool(tool)
            self.play_effect("acerto.wav")
        except (RuntimeError, ValueError):
            self.play_effect("erro.wav")
        self.show_investigation()

    def inspect_hotspot(self, hotspot):
        """Abre a ficha de inspeção; agentes abrigados não podem manipular objetos."""
        if self.game.state.get("is_hidden", False):
            messagebox.showinfo(
                "Abrigo de campo",
                "Você está escondido. Resolva a ocorrência ou saia do abrigo antes de voltar a examinar objetos."
            )
            return
        self.current_hotspot = hotspot
        self.current_interaction_message = None
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
        if self.current_interaction_message:
            self.text(
                485, 482, self.current_interaction_message,
                8, "#e58d83" if self.game.state.get("threat_active", False) else "#d6ad70",
                "nw", 430
            )

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
            # A câmera permanece armada para permitir até três registros por
            # contrato. O motor a desarma automaticamente quando o filme acaba.
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
        try:
            outcome = self.game.interact_object(
                hotspot["id"],
                repeatable=bool(interaction.get("repeatable", False))
            )
            self.current_interaction_message = outcome["message"]
            self.play_effect("erro.wav" if outcome["activated"] else "porta.wav")
        except (RuntimeError, ValueError) as exc:
            self.current_interaction_message = str(exc)
            self.play_effect("erro.wav")
        self.show_inspection()

    def hide_from_anomaly(self):
        try:
            spot = self.game.hide_from_anomaly()
            self.current_interaction_message = f"Você se escondeu em {spot}. Permaneça imóvel até a ocorrência passar."
            self.play_effect("porta.wav")
        except (RuntimeError, ValueError) as exc:
            self.current_interaction_message = str(exc)
            self.play_effect("erro.wav")
        self.show_investigation()

    def leave_hiding(self):
        try:
            self.game.leave_hiding()
            self.current_interaction_message = "Você deixou o abrigo. A presença ainda está ativa e pode encontrá-lo durante a próxima ocorrência."
            self.play_effect("porta.wav")
        except (RuntimeError, ValueError) as exc:
            self.current_interaction_message = str(exc)
            self.play_effect("erro.wav")
        self.show_investigation()

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
        self.rect(58, 190, 480, 288, "#0d1521", "#9a7848", 1)
        self.text(82, 211, "DÍVIDA CONTRATUAL", 10, "#d98b75", "nw")
        self.text(82, 239, "− R$ 1.000.000", 19, "#e58d83", "nw")
        self.text(82, 270, "Cada serviço concluído reduz sua dívida.", 8, self.TEXT, "nw", 365)

        descriptions = [
            ("estagiario", "FÁCIL", "5 estabilidade · até 2 falhas", "DIÁRIA: R$ 50", "LOJA 24H"),
            ("efetivo", "MÉDIO", "4 estabilidade · 1 falha encerra", "DIÁRIA: R$ 75", "EDIFÍCIO 9"),
            ("terceirizado", "DIFÍCIL", "3 estabilidade · 1 falha encerra", "DIÁRIA: R$ 100", "ÚLTIMA SESSÃO"),
        ]
        for i, (key, label, desc, daily, destination) in enumerate(descriptions):
            y = 300 + i * 112
            self.rect(58, y, 480, y + 92, "#101a28", "#8b6b45", 1)
            self.text(82, y + 17, label, 13, self.GOLD, "nw")
            self.text(82, y + 43, desc, 8, self.MUTED, "nw", 205)
            self.text(82, y + 66, daily, 8, "#8bc9a0", "nw")
            self.text(82, y + 80, f"DESTINO: {destination}", 7, "#c6a36a", "nw")
            self.button(
                300, y + 25, 155, "ESCOLHER",
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
        self.rect(710, 195, 984, 590, "#0b141e", "#9a7848", 2)

        self.header(
            "ORDEM DE SERVIÇO / CONFIDENCIAL",
            mission["title"],
            mission["location"]
        )

        state = self.game.state
        debt = max(0, -state["cash"])
        reward = int(round(50 * (2 ** state["shift_index"]) * DIFFICULTIES[state["difficulty"]]["salary"]))
        risk = 2 ** state["shift_index"]

        self.text(730, 218, "DÍVIDA CONTRATUAL", 9, "#d6ad70", "nw")
        # O divisor fica abaixo do valor; antes atravessava os algarismos.
        self.text(730, 244, f"R$ {debt:,}".replace(",", "."), 19, "#e58d83", "nw")
        self.rect(728, 282, 966, 283, "#4d3a35")
        self.text(730, 298, f"PAGAMENTO: R$ {reward:,}".replace(",", "."), 9, "#e8c17e", "nw")
        self.text(730, 320, f"NÍVEL DE RISCO: x{risk}", 8, "#db8875", "nw")

        self.text(730, 354, "OBJETIVO DO SERVIÇO", 9, self.GOLD, "nw")
        # Renderização direta do briefing: evita que o texto desapareça
        # quando o cálculo de bbox ocorre antes da atualização do Canvas.
        self.text(730, 378, mission["brief"], 8, self.TEXT, "nw", 238)

        self.text(730, 440, "PROTOCOLOS DE SEGURANÇA", 9, self.GOLD, "nw")
        for index, rule in enumerate(mission["rules"][:4]):
            self.text(
                733, 463 + index * 29, f"{index + 1:02d}  {rule}",
                7, self.MUTED, "nw", 238
            )

        self.text(55, 595, "ARQUIVO VISUAL DO LOCAL  ·  EXAMINE O AMBIENTE APÓS ASSINAR", 8, self.MUTED, "nw")
        if state.get("advance_payment_due", 0):
            due = state["advance_payment_due"]
            self.text(55, 622, f"PROMESSA AO AGIOTA: R$ {due:,} AMANHÃ".replace(",", "."), 8, "#e58d83", "nw")
        else:
            self.text(55, 622, "O pagamento só será liberado após a conclusão do expediente.", 8, "#c59a72", "nw")
        if state.get("forced_contract_acceptance"):
            self.button(710, 610, 274, "ACEITAR E INICIAR TURNO", self.start_shift, 44)
        else:
            self.button(520, 610, 220, "ACEITAR CONTRATO", self.start_shift, 44)
            self.button(760, 610, 224, "RECUSAR CONTRATO", self.refuse_contract, 44)
        self.bind_clicks()

    def refuse_contract(self):
        state = self.game.state
        state["contract_refused"] = True
        self.game.save()
        self.show_loan_shark()

    def show_loan_shark(self):
        self.stop_ambience()
        self.screen = "loan_shark"
        self.clear()
        self.rect(0, 0, self.W, self.H, self.BG)
        self.header(
            "COBRANÇA EXTRAJUDICIAL / 02:17",
            "O homem que esperava do lado de fora",
            "Você recusou o contrato. A dívida, porém, não recusou você."
        )
        self.rect(80, 215, 944, 555, "#101a28", "#9a7848", 2)
        self.text(125, 250, "AGIOTA", 10, "#e58d83", "nw")
        self.text(
            125, 285,
            "A porta fecha atrás de você. Um homem de luvas claras coloca uma pasta sobre a mesa. "
            "Ele conhece seu nome, o valor exato da dívida e o endereço da sua família. "
            "“Dinheiro não é a única coisa que tem valor. Posso quitar uma parte se você aceitar "
            "entregar algo que não deveria estar à venda: uma parte do próprio corpo ou seus serviços. "
            "Você escolhe. Se não aceitar, amanhã quero uma parte da dívida em dinheiro.”",
            11, self.TEXT, "nw", 760
        )
        self.text(125, 430, "A oferta parece pior do que o trabalho. A ameaça parece pior do que a oferta.", 10, "#d7ad70", "nw", 760)
        self.text(125, 475, "Você sente o estômago apertar. Ainda assim, precisa do dinheiro.", 10, self.MUTED, "nw", 760)
        self.button(125, 505, 350, "ACEITAR A OFERTA", self.accept_loan_shark, 42)
        self.button(520, 505, 350, "PAGAR UMA PARTE AMANHÃ", self.promise_payment, 42)
        self.bind_clicks()

    def accept_loan_shark(self):
        state = self.game.state
        state["loan_shark_accepted"] = True
        state["status"] = "ended"
        state["task_index"] = 1
        state["last_reveal"] = (
            "Você aceitou a proposta do agiota. O contrato da agência foi substituído "
            "por uma dívida cobrada sobre o próprio corpo. O arquivo foi encerrado."
        )
        self.game.save()
        self.show_ending()

    def promise_payment(self):
        state = self.game.state
        next_reward = int(round(50 * (2 ** state["shift_index"]) * DIFFICULTIES[state["difficulty"]]["salary"]))
        state["advance_payment_due"] = max(25, min(500, next_reward // 2))
        state["forced_contract_acceptance"] = True
        state["contract_refused"] = False
        self.game.save()
        self.show_contract()

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
        self.rect(710, 195, 984, 590, "#0b141e", "#9a7848", 2)
        self.text(730, 218, "OBJETIVO DE CAMPO", 9, self.GOLD, "nw")
        self.text(730, 242, "Investigue os objetos e respeite os protocolos.", 8, self.TEXT, "nw", 230)
        threat_level = state.get("threat_level", 0)
        threat_active = state.get("threat_active", False)
        is_hidden = state.get("is_hidden", False)
        threat_label = f"PRESSÃO ANÔMALA: {threat_level}/{3}"
        if threat_active:
            threat_label += "  /  PRESENÇA ATIVA"
        elif is_hidden:
            threat_label += "  /  AGENTE OCULTO"
        threat_color = "#e58d83" if threat_active else ("#83c4a8" if is_hidden else "#d6ad70")
        self.text(730, 270, threat_label, 8, threat_color, "nw")
        if threat_active:
            self.text(730, 288, "A presença vai atacar na próxima decisão. Esconda-se.", 7, "#e58d83", "nw", 230)
        elif is_hidden:
            self.text(730, 288, "Você está fora do campo de visão da presença.", 7, "#83c4a8", "nw", 230)
        else:
            self.text(730, 288, "Interações podem atrair a anomalia.", 7, self.MUTED, "nw", 230)

        scene_data = self.object_scene_data.get(scene_id, {})
        hotspots = scene_data.get("hotspots", self.scene_manager.get(scene_id).get("hotspots", [])) if scene_id else []
        evidence = [
            item for item in state.get("evidence", [])
            if item.get("mission") == mission["id"]
        ]
        found_ids = {item.get("id") for item in evidence}
        found_count = sum(1 for hotspot in hotspots if hotspot["id"] in found_ids)
        self.text(730, 316, f"PISTAS REGISTRADAS: {found_count}/{len(hotspots)}", 8, "#8bc9a0" if evidence else "#d6ad70", "nw")
        self.text(730, 340, "OBJETOS INTERATIVOS", 8, self.MUTED, "nw")

        for index, hotspot in enumerate(hotspots[:4]):
            y = 359 + index * 37
            collected = hotspot["id"] in found_ids
            label = hotspot.get("label", hotspot["id"])
            status = "REGISTRADO" if collected else "EXAMINAR"
            self.button(
                728, y, 238,
                f"{label[:19]}  ·  {status}",
                lambda h=hotspot: self.inspect_hotspot(h),
                29
            )

        self.button(728, 525, 238, "ABRIR CENTRAL CCTV / 06 CANAIS", self.show_surveillance, 29)
        if threat_active and is_hidden:
            self.button(728, 548, 238, "SAIR DO ESCONDERIJO", self.leave_hiding, 30)
        elif threat_active and not state.get("hide_used", False):
            self.button(728, 548, 238, "ESCONDER-SE AGORA", self.hide_from_anomaly, 30)
        elif threat_active and state.get("hide_used", False):
            self.text(730, 562, "ABRIGO JÁ UTILIZADO NESTA PERSEGUIÇÃO", 7, "#e58d83", "nw", 230)
        else:
            self.text(730, 562, "NENHUMA PRESENÇA À CAÇA", 7, self.MUTED, "nw")

        # Barra de equipamento fora do cenário: não obstrui os pontos clicáveis.
        tool_states = state.setdefault("tool_states", {})
        lantern_charge = self.game.get_tool_resource("lanterna")
        radio_uses = self.game.get_tool_resource("radio")
        camera_film = self.game.get_tool_resource("camera")
        lantern_label = f"LANTERNA {'ON' if tool_states.get('lanterna', True) else 'OFF'}  {lantern_charge}%"
        radio_label = f"RÁDIO / {radio_uses} CHAMADAS" 
        camera_label = f"CÂMERA {'ON' if tool_states.get('camera', False) else 'OFF'}  {camera_film}"
        self.button(40, 610, 150, lantern_label, lambda: self.toggle_field_tool("lanterna"), 40)
        self.button(200, 610, 150, radio_label, self.use_radio, 40)
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
        if hotspots and (
            not self.current_camera_hotspot
            or not any(item["id"] == self.current_camera_hotspot.get("id") for item in hotspots)
        ):
            threat_triggered = (self.game.state or {}).get("threat_triggered", [])
            preferred_id = threat_triggered[-1] if (self.game.state or {}).get("threat_active") and threat_triggered else None
            self.current_camera_hotspot = next(
                (item for item in hotspots if item["id"] == preferred_id),
                hotspots[0]
            )

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
        root = Path(__file__).resolve().parent
        background_path = root / "assets" / "ambientes" / (background_name or "")
        source_image = None
        threat_channel = None
        if background_path.is_file():
            try:
                manifest_size = self.object_scene_data.get("viewport", [834, 469])
                scene_w, scene_h = int(manifest_size[0]), int(manifest_size[1])
                with Image.open(background_path) as source:
                    composed = source.convert("RGBA").resize(
                        (scene_w, scene_h), Image.Resampling.LANCZOS
                    )

                # Reconstrói a cena com o mesmo z-order e os mesmos estados visuais
                # usados no Canvas. Assim, cada monitor mostra objetos reais do local.
                hotspot_by_object = {
                    item.get("object"): item.get("id")
                    for item in scene_data.get("hotspots", [])
                    if item.get("object")
                }
                for obj in sorted(scene_data.get("objects", []), key=lambda item: item.get("z", 0)):
                    if not obj.get("visible", True):
                        continue
                    hotspot_id = hotspot_by_object.get(obj["id"])
                    object_state = self.game.get_object_state(hotspot_id) if hotspot_id else "0"
                    asset_name = obj.get("asset_states", {}).get(object_state, obj.get("asset", ""))
                    asset_path = root / "assets" / "objetos" / asset_name
                    if not asset_path.is_file():
                        asset_path = root / "assets" / "objetos" / obj.get("asset", "")
                    if not asset_path.is_file():
                        continue
                    box = (
                        max(1, int(obj["w"] * scene_w)),
                        max(1, int(obj["h"] * scene_h))
                    )
                    with Image.open(asset_path) as source:
                        sprite = ImageOps.contain(
                            source.convert("RGBA"), box, method=Image.Resampling.LANCZOS
                        )
                    x = int(obj["x"] * scene_w + (box[0] - sprite.width) / 2)
                    y = int(obj["y"] * scene_h + (box[1] - sprite.height) / 2)
                    composed.alpha_composite(sprite, (x, y))
                # A presença ocupa a região do último objeto que elevou a pressão.
                threat_channel = None
                threat_state = self.game.state or {}
                if threat_state.get("threat_active", False):
                    last_trigger = (threat_state.get("threat_triggered") or [None])[-1]
                    trigger_hotspot = next(
                        (item for item in scene_data.get("hotspots", []) if item.get("id") == last_trigger),
                        None
                    )
                    trigger_object = next(
                        (item for item in scene_data.get("objects", [])
                         if trigger_hotspot and item.get("id") == trigger_hotspot.get("object")),
                        None
                    )
                    if trigger_object:
                        gx = trigger_object["x"] + trigger_object["w"] / 2
                        gy = trigger_object["y"] + trigger_object["h"] / 2
                    else:
                        gx, gy = 0.78, 0.58
                    col = min(2, max(0, int(gx * 3)))
                    row = min(1, max(0, int(gy * 2)))
                    threat_channel = row * 3 + col
                    # Silhueta aparece só na câmera que cobre o ponto anômalo.
                    px, py = int(gx * scene_w), int(gy * scene_h)
                    draw = ImageDraw.Draw(composed, "RGBA")
                    draw.ellipse((px - 15, py - 48, px + 15, py - 14),
                                 fill=(2, 5, 7, 238), outline=(126, 63, 55, 190), width=2)
                    draw.polygon(
                        [(px - 12, py - 17), (px + 12, py - 17),
                         (px + 28, py + 54), (px - 28, py + 54)],
                        fill=(2, 5, 7, 238), outline=(83, 48, 45, 190)
                    )
                    if self.game.get_tool_state("camera"):
                        draw.ellipse((px - 7, py - 35, px - 3, py - 31), fill=(211, 77, 63, 255))
                        draw.ellipse((px + 3, py - 35, px + 7, py - 31), fill=(211, 77, 63, 255))
                else:
                    threat_channel = None
                source_image = composed.convert("RGB")
            except (OSError, ValueError, KeyError, TypeError):
                source_image = None
                threat_channel = None

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
            # Cada canal fica associado ao hotspot cujo objeto está mais perto
            # do centro da região observada, em vez de repetir a lista em sequência.
            hotspot = None
            if hotspots:
                scene_objects = {
                    obj["id"]: obj for obj in scene_data.get("objects", [])
                }
                region_x = (col + 0.5) / 3
                region_y = (row + 0.5) / 2
                def camera_distance(item):
                    obj = scene_objects.get(item.get("object"))
                    if not obj:
                        return 10.0
                    ox = obj["x"] + obj["w"] / 2
                    oy = obj["y"] + obj["h"] / 2
                    return (ox - region_x) ** 2 + (oy - region_y) ** 2
                hotspot = min(hotspots, key=camera_distance)
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
        if threat_channel is not None:
            self.text(
                750, 325,
                f"SINAL SUSPEITO / CAM-{threat_channel + 1:02d}",
                9, "#e58d83", "nw"
            )
            self.text(750, 349, "Compare o feed suspeito com os demais canais.", 8, self.MUTED, "nw", 215)
        else:
            self.text(750, 325, "Aproxime a imagem, compare o ambiente e registre uma anomalia.", 9, self.MUTED, "nw", 215)

        remaining = self.game.get_tool_resource("camera")
        camera_active = self.game.get_tool_state("camera")
        if (self.game.state or {}).get("threat_disrupted", False):
            self.text(750, 375, "PRESENÇA INTERROMPIDA PELO FLASH", 8, "#8bc9a0", "nw")
        self.text(750, 410, f"FILME DISPONÍVEL: {remaining}", 10, "#d6ad70", "nw")
        if camera_active:
            self.button(750, 430, 215, "DESARMAR CÂMERA", self.toggle_surveillance_camera, 34)
        else:
            self.button(750, 430, 215, "ARMAR CÂMERA", self.toggle_surveillance_camera, 34)

        if self.current_camera_hotspot:
            evidence_found = any(
                item.get("id") == self.current_camera_hotspot["id"]
                and item.get("mission") == mission["id"]
                for item in self.game.state.get("evidence", [])
            )
            if evidence_found:
                self.text(750, 480, "EVIDÊNCIA JÁ ARQUIVADA", 8, "#8bc9a0", "nw")
            elif camera_active and remaining > 0:
                self.button(750, 475, 215, "FOTOGRAFAR CANAL", self.capture_surveillance_feed, 36)
            elif camera_active:
                self.text(750, 482, "SEM FILME. USE A OBSERVAÇÃO MANUAL.", 8, "#d07762", "nw", 210)
            else:
                self.text(750, 482, "ARME A CÂMERA PARA REGISTRAR ESTE CANAL.", 8, self.MUTED, "nw", 210)

        self.button(750, 520, 215, "VOLTAR À INVESTIGAÇÃO", self.show_investigation, 36)
        self.bind_clicks()

    def toggle_surveillance_camera(self):
        try:
            self.game.toggle_tool("camera")
            self.play_effect("acerto.wav")
        except (RuntimeError, ValueError):
            self.play_effect("erro.wav")
        self.show_surveillance()

    def select_surveillance_feed(self, hotspot):
        self.current_camera_hotspot = hotspot
        self.show_surveillance()

    def capture_surveillance_feed(self):
        hotspot = self.current_camera_hotspot
        if not hotspot:
            return
        try:
            threat_state = self.game.state or {}
            threat_hotspot_id = (
                (threat_state.get("threat_triggered") or [None])[-1]
                if threat_state.get("threat_active", False) else None
            )
            captured_presence = (
                threat_hotspot_id is not None
                and hotspot["id"] == threat_hotspot_id
            )
            # Fotografa primeiro: o último fotograma também pode interromper a presença.
            if captured_presence:
                disruption_message = self.game.document_anomaly(hotspot["id"])
                self.current_interaction_message = disruption_message
            self.game.consume_tool_resource("camera", 1)
            prefix = "PRESENÇA ANÔMALA FOTOGRAFADA / CCTV. " if captured_presence else "FOTO CCTV / "
            self.game.record_evidence(
                hotspot["id"],
                prefix + hotspot.get("finding", "Anomalia registrada no circuito interno.")
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
        """Ocorrência com o cenário visível e o registro operacional em painel lateral."""
        self.screen = "task"
        self.start_ambience()
        mission = self.game.mission
        task = self.game.task
        state = self.game.state
        scene_id = scene_for_mission(mission["id"])
        self.clear()
        self.rect(0, 0, self.W, self.H, self.BG)
        self.header(
            f"AO VIVO / {mission['location']}",
            mission["title"],
            f"AGENTE: {state['player']}  |  ESTABILIDADE: {state['sanity']}  |  "
            f"FALHAS: {state['mistakes']}  |  RISCO x{state.get('risk_multiplier', 2 ** state['shift_index'])}"
        )

        left, top, right, bottom = self.SCENE_VIEWPORT
        self.rect(left - 5, top - 5, right + 5, bottom + 5, "#0b111a", "#8e704c", 2)
        if scene_id:
            self.draw_scene(
                scene_id,
                (left + right) / 2,
                (top + bottom) / 2,
                show_hotspots=False
            )

        # Ficha operacional substitui a antiga tela genérica de texto.
        self.rect(710, 195, 984, 572, "#0b141e", "#9a7848", 2)
        self.text(730, 218, f"OCORRÊNCIA {state['task_index'] + 1} / 3", 9, "#d6ad70", "nw")
        self.text(730, 246, "REGISTRO DE INCIDENTE", 10, self.GOLD, "nw")
        self.text(730, 274, task["prompt"], 10, self.TEXT, "nw", 230)

        evidence = [
            item for item in state.get("evidence", [])
            if item.get("mission") == mission["id"]
        ]
        self.rect(728, 342, 966, 343, "#354657")
        self.text(730, 365, f"PISTAS NO DOSSIÊ: {len(evidence)}", 8, "#8bc9a0" if evidence else "#d6ad70", "nw")
        self.text(730, 387, "ESCOLHA UMA CONDUTA", 8, self.MUTED, "nw")

        for index, choice in enumerate(task["choices"]):
            y = 410 + index * 49
            self.button(
                728, y, 238,
                f"{index + 1}.  {choice}",
                lambda n=index: self.choose(n),
                42
            )

        self.button(728, 565, 112, "DOSSIÊ", self.show_evidence_report, 34)
        self.button(852, 565, 114, "VOLTAR", self.show_investigation, 34)
        self.text(55, 590, "UMA VIOLAÇÃO REDUZ A ESTABILIDADE PELO NÍVEL DE RISCO ATUAL.", 8, "#d18b70", "nw")
        self.text(55, 615, "A agência não garante resgate de funcionários desaparecidos.", 8, self.MUTED, "nw")
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
        self.text(120,255,"✓" if result.get("correct") else "!",34,color,"nw")
        # Texto do relatório em posição fixa: evita depender do bbox do Canvas
        # imediatamente após limpar/redesenhar a tela (caso que exibia apenas "!").
        message = str(result.get("message") or "A ocorrência foi registrada, mas a agência não forneceu uma descrição.")
        self.text(180, 258, message, 12, self.TEXT, "nw", 720)
        content_y = 345
        if result.get("evidence_used"):
            self.text(120, content_y, "PISTA APLICADA À DECISÃO", 10, self.GOLD, "nw")
            self.text(120, content_y + 22, result.get("evidence_note") or "A evidência foi considerada nesta decisão.", 9, self.MUTED, "nw", 760)
            content_y += 76
        if result.get("tool_warning"):
            self.text(120, content_y, "AVISO DE EQUIPAMENTO: " + str(result["tool_warning"]), 8, "#e58d83", "nw", 760)
            content_y += 28
        ending = result.get("ending")
        if ending == "survived":
            self.text(120, content_y, "TURNO CONCLUÍDO", 16, self.GOLD, "nw")
            self.text(120, content_y + 30,
                      f"Pagamento recebido: R$ {self.game.state['last_payment']:,}".replace(",", "."),
                      11, self.TEXT, "nw")
            self.button(650,535,230,"PRÓXIMO CONTRATO",self.advance_contract,44)
        elif ending == "missing":
            self.text(120, content_y, "FUNCIONÁRIO NÃO LOCALIZADO", 15, "#e58d83", "nw")
            self.wrapped_text(
                120, content_y + 30, self.game.state.get("last_reveal", ""),
                10, self.MUTED, 720, 2
            )
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
    try:
        object_manifest = json.loads(
            (Path(__file__).resolve().parent / "dados" / "objetos_cenas.json").read_text(encoding="utf-8")
        ).get("scenes", {})
    except (OSError, json.JSONDecodeError):
        object_manifest = {}
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
            print(
                f"I - registrar pista | M - manipular objeto | R - consultar rádio ({game.get_tool_resource('radio')} transmissões) | "
                + ("H - esconder-se | " if game.state.get("threat_active") and not game.state.get("is_hidden") and not game.state.get("hide_used", False) else "")
                + ("S - sair do esconderijo | " if game.state.get("is_hidden") else "")
                + "ENTER - seguir"
            )
            command = input("> ").strip().lower()
            if command == "r":
                try:
                    game.consume_tool_resource("radio", 1)
                    print("\\n[TRANSMISSÃO / CANAL 03.17]")
                    print(game.task.get("radio_hint", "A transmissão chega cortada."))
                except (RuntimeError, ValueError) as exc:
                    print("RÁDIO:", str(exc))
                continue
            if command == "h" and game.state.get("threat_active") and not game.state.get("is_hidden") and not game.state.get("hide_used", False):
                try:
                    print("ABRIGO:", game.hide_from_anomaly())
                except RuntimeError as exc:
                    print("ABRIGO:", str(exc))
                continue
            if command == "s" and game.state.get("is_hidden"):
                try:
                    game.leave_hiding()
                    print("Você saiu do esconderijo. A presença ainda está procurando por você.")
                except RuntimeError as exc:
                    print("ABRIGO:", str(exc))
                continue
            if command == "m" and scene.get("hotspots"):
                choice = input("Número do objeto para manipular: ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(scene["hotspots"]):
                    hotspot = scene["hotspots"][int(choice)-1]
                    configured = next(
                        (item for item in object_manifest.get(scene_id, {}).get("hotspots", [])
                         if item.get("id") == hotspot["id"]),
                        {}
                    )
                    repeatable = bool(configured.get("interaction", {}).get("repeatable", False))
                    try:
                        outcome = game.interact_object(hotspot["id"], repeatable=repeatable)
                        print("INTERAÇÃO:", outcome["message"])
                        print(f"PRESSÃO ANÔMALA: {outcome['threat_level']}/3")
                    except (RuntimeError, ValueError) as exc:
                        print("INTERAÇÃO:", str(exc))
                continue
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
