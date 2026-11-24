"""Launcher de Turnos Zero. A campanha antiga permanece preservada nos arquivos legados."""
import sys
import json
import tkinter as tk
from tkinter import messagebox, simpledialog
from turnos_zero import ShiftGame, DIFFICULTIES, MISSIONS
from scene_manager import SceneManager, SceneError, scene_for_mission
from pathlib import Path

class TurnosZeroApp:
    W, H = 1024, 700
    BG = "#090d16"
    PANEL = "#141d2b"
    GOLD = "#e5b96d"
    TEXT = "#e7e5df"
    MUTED = "#91a0ad"

    def __init__(self, root):
        self.root = root
        self.root.title("TURNOS ZERO | Agência de Serviços Extraordinários")
        self.root.geometry(f"{self.W}x{self.H}")
        self.root.minsize(900, 620)
        self.game = ShiftGame()
        self.scene_manager = SceneManager()
        self.scene_images = {}
        self.object_images = {}
        self.object_scene_data = {}
        manifest_path = Path(__file__).resolve().parent / "dados" / "objetos_cenas.json"
        try:
            self.object_scene_data = json.loads(manifest_path.read_text(encoding="utf-8")).get("scenes", {})
        except (OSError, json.JSONDecodeError):
            self.object_scene_data = {}
        self.active_scene = None
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

    def resize_canvas(self, event):
        if event.width <= 1 or event.height <= 1:
            return
        sx, sy = event.width / self._draw_w, event.height / self._draw_h
        if abs(sx - 1) > 0.001 or abs(sy - 1) > 0.001:
            self.canvas.scale("all", 0, 0, sx, sy)
            self._draw_w, self._draw_h = event.width, event.height

    def draw_scene(self, scene_id, center_x=512, center_y=390):
        try:
            scene = self.scene_manager.get(scene_id)
            self.active_scene = scene_id
            layered = self.object_scene_data.get(scene_id)
            viewport = (95, 235, 929, 510)
            object_root = Path(__file__).resolve().parent / "assets" / "objetos"
            layers_ready = bool(layered) and all((object_root / item.get("asset", "")).is_file() for item in layered.get("objects", []))
            if layers_ready:
                # Cenário por camadas: cada objeto é um PNG independente e
                # suas coordenadas/visibilidade ficam em dados/objetos_cenas.json.
                left, top, right, bottom = viewport
                backdrop = layered.get("backdrop", {})
                self.rect(left, top, right, bottom, backdrop.get("wall", "#101923"))
                self.rect(left, top + (bottom-top)*0.72, right, bottom, backdrop.get("floor", "#070b12"))
                self.rect(left, top+8, right, top+10, backdrop.get("light", "#9a7848"))
                self.rect(left+12, top+12, right-12, bottom-12, "", "#344657", 1)
                for obj in sorted(layered.get("objects", []), key=lambda item: item.get("z", 0)):
                    if not obj.get("visible", True):
                        continue
                    asset = Path(__file__).resolve().parent / "assets" / "objetos" / obj["asset"]
                    if not asset.is_file():
                        continue
                    cache_key = (scene_id, obj["id"])
                    if cache_key not in self.object_images:
                        self.object_images[cache_key] = tk.PhotoImage(file=str(asset))
                    x = left + (obj["x"] + obj["w"]/2) * (right-left)
                    y = top + (obj["y"] + obj["h"]/2) * (bottom-top)
                    self.canvas.create_image(x, y, image=self.object_images[cache_key], anchor="center",
                                             tags=("scene_object", obj["id"]))
                scene_hotspots = layered.get("hotspots", [])
            else:
                path = Path(__file__).resolve().parent / scene.get("background", "")
                if path.suffix.lower() == ".png" and path.is_file():
                    try:
                        if scene_id not in self.scene_images:
                            self.scene_images[scene_id] = tk.PhotoImage(file=str(path))
                        self.canvas.create_image(center_x, center_y, image=self.scene_images[scene_id], anchor="center")
                    except tk.TclError:
                        self.scene_images.pop(scene_id, None)
                        self.draw_scene_fallback(scene_id)
                else:
                    self.draw_scene_fallback(scene_id)
                scene_hotspots = scene.get("hotspots", [])

            evidence_ids = {
                item.get("id") for item in (self.game.state or {}).get("evidence", [])
                if item.get("mission") == (self.game.mission or {}).get("id")
            }
            for index, hotspot in enumerate(scene_hotspots, 1):
                bounds = SceneManager.map_bounds(hotspot["bounds"], viewport)
                x1, y1, x2, y2 = bounds
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                found = hotspot["id"] in evidence_ids
                marker = "#75b9a5" if found else "#e0a65b"
                self.canvas.create_oval(cx-13, cy-13, cx+13, cy+13,
                                        fill="#101923", outline=marker, width=3)
                self.canvas.create_text(cx, cy, text="✓" if found else str(index),
                                        fill=marker, font=("Consolas", 10, "bold"))
                label = hotspot.get("label", hotspot["id"]).upper()
                tag_w = min(190, max(76, len(label) * 7 + 18))
                tag_y = max(238, cy - 34)
                self.rect(cx-tag_w/2, tag_y-10, cx+tag_w/2, tag_y+10, "#101923", marker, 1)
                self.text(cx, tag_y, label, 7, marker)
                self.targets.append((bounds, lambda h=hotspot:self.inspect_hotspot(h)))
        except (SceneError, tk.TclError, OSError, KeyError):
            self.active_scene = None

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

    def inspect_hotspot(self, hotspot):
        self.screen = "inspection"
        self.clear()
        self.rect(0,0,self.W,self.H,self.BG)
        self.header("ANÁLISE DE CAMPO", hotspot.get("label", hotspot["id"]),
                    "OBSERVE O REGISTRO. USE A PISTA PARA DECIDIR COMO AGIR.")
        self.rect(82,220,942,520,"#111b28","#786044",2)
        self.rect(82,220,91,520,"#a64f45")
        self.text(125,270,"ANOMALIA IDENTIFICADA",10,"#d98b75","nw")
        self.text(125,322,hotspot.get("label", hotspot["id"]).upper(),19,"#e7d9c5","nw")
        self.rect(125,352,895,353,"#394b59")
        finding = hotspot.get("finding", "O ambiente apresenta uma alteração que não pode ser explicada.")
        recorded = self.game.record_evidence(hotspot["id"], finding) if self.game.state and self.game.state.get("status") == "on_shift" else False
        self.text(125,392,"RELATO / EVIDÊNCIA",9,"#d6ad70","nw")
        self.text(125,430,finding,14,"#e7e5df","nw",735)
        self.text(125,480,"A pista foi adicionada ao seu relatório de campo." if recorded else "Esta pista já consta no relatório deste contrato.",10,"#82b9a7","nw")
        self.text(125,555,"PRÓXIMO PASSO",9,"#d6ad70","nw")
        self.text(125,580,"Volte ao ambiente, examine os outros pontos e só então avance para a ocorrência.",10,self.MUTED,"nw",760)
        self.button(650,615,245,"VOLTAR AO AMBIENTE",self.show_investigation,42)
        self.bind_clicks()

    def click(self, event):
        logical_x = event.x * self.W / max(1, self.canvas.winfo_width())
        logical_y = event.y * self.H / max(1, self.canvas.winfo_height())
        for (x1,y1,x2,y2), callback in reversed(self.targets):
            if x1 <= logical_x <= x2 and y1 <= logical_y <= y2:
                callback()
                return

    def bind_clicks(self):
        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())
        self.canvas.scale("all", 0, 0, width / self.W, height / self.H)
        self._draw_w, self._draw_h = width, height
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

    def draw_backdrop(self, filename, y=390):
        path = Path(__file__).resolve().parent / "assets" / "ambientes" / filename
        if not path.is_file():
            return False
        try:
            key = "backdrop:" + filename
            if key not in self.scene_images:
                self.scene_images[key] = tk.PhotoImage(file=str(path))
            self.canvas.create_image(self.W//2, y, image=self.scene_images[key], anchor="center")
            return True
        except tk.TclError:
            return False

    def new_campaign(self):
        player = simpledialog.askstring("Novo contrato","Nome para o crachá:",parent=self.root)
        if player is None:
            return
        self.screen="difficulty"
        self.clear()
        self.rect(0,0,self.W,self.H,self.BG)
        self.draw_backdrop("agencia_menu.png", 385)
        self.header("RECURSOS HUMANOS / ADMISSÃO","Escolha seu vínculo","A agência oferece proteção limitada. A dívida permanece sob sua responsabilidade.")
        self.rect(58,190,966,305,"#101a28","#9a7848",2)
        self.text(86,220,"DÍVIDA CONTRATUAL",10,"#d98b75","nw")
        self.text(86,255,"− R$ 1.000.000",24,"#e58d83","nw")
        self.text(86,286,"Cada serviço concluído reduz sua dívida. A remuneração dobra a cada contrato.",10,self.TEXT,"nw",820)
        descriptions = [
            ("estagiario","ESTAGIÁRIO","5 estabilidade · suporta 2 violações"),
            ("efetivo","EFETIVO","4 estabilidade · 1 violação encerra o contrato"),
            ("terceirizado","TERCEIRIZADO","3 estabilidade · 1 violação encerra o contrato")
        ]
        for i,(key,label,desc) in enumerate(descriptions):
            y=320+i*58
            self.rect(82,y,942,y+50,"#14202d","#8b6b45",1)
            self.text(108,y+20,label,13,self.GOLD,"nw")
            self.text(108,y+36,desc,9,self.MUTED,"nw")
            self.button(750,y+4,165,"ASSINAR",lambda k=key,p=player:self.create_campaign(p,k),42)
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
        self.screen="briefing"
        mission=self.game.mission
        self.clear()
        self.rect(0,0,self.W,self.H,self.BG)
        scene_id=scene_for_mission(mission["id"])
        background={"loja_24h":"loja_24_horas.png","edificio_9":"edificio_residencial.png","cinema_vazio":"cinema_ultima_sessao.png","laboratorio":"laboratorio_experimental.png"}.get(scene_id)
        if background:
            self.draw_backdrop(background, 385)
        self.header("ORDEM DE SERVIÇO / CONFIDENCIAL",mission["title"],mission["location"])
        state=self.game.state
        debt=max(0,-state["cash"])
        reward=50*(2**state["shift_index"])
        risk=2**state["shift_index"]
        self.rect(55,185,969,226,"#0d1521","#9a7848",1)
        self.text(78,204,"OBJETIVO: QUITAR A DÍVIDA CONTRATUAL",10,self.GOLD,"nw")
        self.text(78,222,f"DÍVIDA R$ {debt:,}  |  PAGAMENTO R$ {reward:,}  |  RISCO x{risk}".replace(",", "."),10,self.TEXT,"nw")
        self.rect(55,550,969,680,"#0d1521","#9a7848",1)
        self.text(78,568,"ORDEM DE SERVIÇO",9,self.GOLD,"nw")
        self.text(78,590,mission["brief"],9,self.TEXT,"nw",850)
        rules="   •   ".join(mission["rules"][:3])
        self.text(78,618,"PROTOCOLOS: "+rules,8,self.MUTED,"nw",850)
        self.button(690,635,250,"ACEITAR CONTRATO  [ENTER]",self.start_shift,38)
        self.bind_clicks()
    def start_shift(self):
        if self.game.state["status"]=="between_shifts":
            self.game.start_shift()
        self.show_investigation()

    def show_investigation(self):
        self.screen="investigation"
        mission=self.game.mission
        state=self.game.state
        scene_id=scene_for_mission(mission["id"])
        self.clear()
        self.rect(0,0,self.W,self.H,self.BG)
        self.header("INVESTIGAÇÃO DE CAMPO",mission["title"],
                    f"ESTABILIDADE: {state['sanity']}  |  FALHAS: {state['mistakes']}  |  REPUTAÇÃO: {state['reputation']}  |  DÍVIDA: R$ {max(0,-state['cash']):,}  |  RISCO x{state.get('risk_multiplier',2**state['shift_index'])}".replace(",", "."))
        self.rect(55,190,969,575,"#101723","#786044",2)
        self.rect(70,205,954,555,"#131e2b","#35485a",1)
        self.text(512,220,"INVESTIGUE OS MARCADORES NUMERADOS — CLIQUE PARA EXAMINAR AS PISTAS",8,"#d6ad70")
        self.rect(95,235,929,510,"#080e17")
        if scene_id:
            self.draw_scene(scene_id,512,372)
        evidence=[item for item in state.get("evidence",[]) if item.get("mission")==mission["id"]]
        scene_layers = self.object_scene_data.get(scene_id, {})
        total_hotspots = len(scene_layers.get("hotspots", self.scene_manager.get(scene_id).get("hotspots", []))) if scene_id else 0
        self.text(512,548,f"RELATÓRIO DE CAMPO: {len(evidence)}/{total_hotspots} PISTAS ENCONTRADAS",10,"#82b9a7" if evidence else "#d6ad70")
        if evidence:
            labels = "  ·  ".join(item.get("description", item.get("id", "Pista"))[:48] for item in evidence[-2:])
            self.text(512,570,labels,8,self.MUTED,width=850)
        self.button(690,610,260,"AVANÇAR PARA A OCORRÊNCIA",self.show_task,44)
        self.bind_clicks()

    def show_task(self):
        self.screen="task"
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
