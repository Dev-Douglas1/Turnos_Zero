"""Launcher de Turnos Zero. A campanha antiga permanece preservada nos arquivos legados."""
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog
from turnos_zero import ShiftGame, DIFFICULTIES, MISSIONS
from scene_manager import SceneManager, SceneError
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
            # SVG is kept as editable source art. Tkinter's Canvas has no native SVG
            # renderer, so the scene is drawn with native primitives until an optional
            # SVG rasterizer is available; gameplay remains dependency-free.
            path = Path(__file__).resolve().parent / scene.get("background", "")
            if path.suffix.lower() == ".png" and path.is_file():
                if scene_id not in self.scene_images:
                    self.scene_images[scene_id] = tk.PhotoImage(file=str(path))
                self.canvas.create_image(center_x, center_y, image=self.scene_images[scene_id], anchor="center")
            else:
                self.draw_scene_fallback(scene_id)
            for hotspot in scene.get("hotspots", []):
                x1,y1,x2,y2 = hotspot["bounds"]
                self.targets.append(((x1*self.W,y1*self.H,x2*self.W,y2*self.H),
                    lambda h=hotspot:self.inspect_hotspot(h)))
        except (SceneError, tk.TclError, OSError):
            self.active_scene = None

    def draw_scene_fallback(self, scene_id):
        # Scene-specific geometry is intentionally native Canvas and editable.
        if scene_id == "loja_24h":
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
        self.header("INSPEÇÃO DE AMBIENTE", hotspot.get("label", hotspot["id"]),
                    f"CENA: {self.active_scene or '—'}")
        self.rect(100,220,924,490,self.PANEL,"#8b6b42",2)
        self.text(150,285,"PONTO DE INTERESSE IDENTIFICADO",14,self.GOLD,"nw")
        self.text(150,335,f"Referência: {hotspot.get('id')}",12,self.TEXT,"nw")
        self.text(150,375,f"Ação configurada: {hotspot.get('action','inspect')}",12,self.MUTED,"nw")
        self.text(150,430,"A análise detalhada deste objeto será ligada às evidências da missão.",11,self.MUTED,"nw",700)
        self.button(650,535,230,"VOLTAR À OCORRÊNCIA",self.show_task,44)
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
        self.text(56,38,eyebrow,11,self.GOLD,"nw")
        self.text(56,82,title,28,self.TEXT,"nw")
        if subtitle:
            self.text(56,132,subtitle,12,self.MUTED,"nw")

    def menu(self):
        self.screen = "menu"
        self.clear()
        self.rect(0,0,self.W,self.H,self.BG)
        # Abstract night skyline / office windows: intentionally generated in Tkinter,
        # so the game does not depend on optional image packages or external assets.
        for x in range(0,self.W,64):
            self.rect(x,0,x+1,self.H,"#111a28")
        self.rect(0,475,self.W,self.H,"#0d1420")
        for i in range(18):
            x=25+i*58
            self.rect(x,180+(i%4)*35,x+27,245+(i%4)*35,"#18283a")
            self.rect(x+7,190+(i%4)*35,x+12,198+(i%4)*35,"#8b704a")
        self.rect(48,175,976,590,"#101a28","#705b40",2)
        self.rect(58,185,966,580,"#101a28","#2e3948",1)
        self.draw_scene("agencia", 512, 380)
        self.text(512,245,"AGÊNCIA DE SERVIÇOS EXTRAORDINÁRIOS",12,self.MUTED)
        self.text(512,315,"TURNOS ZERO",43,self.GOLD)
        self.text(512,365,"O expediente termina. Nem todos voltam para casa.",13,self.TEXT)
        self.button(355,420,314,"NOVO CONTRATO",self.new_campaign)
        if self.game.state:
            self.button(355,480,314,"CONTINUAR / VER CONTRATO",self.continue_campaign)
        self.text(512,635,"ARQUIVO INTERNO  ·  ACESSO RESTRITO  ·  V. 1.0",9,self.MUTED)
        self.bind_clicks()

    def new_campaign(self):
        player = simpledialog.askstring("Novo contrato","Nome para o crachá:",parent=self.root)
        if player is None:
            return
        self.screen="difficulty"
        self.clear()
        self.rect(0,0,self.W,self.H,self.BG)
        self.header("RECURSOS HUMANOS / ADMISSÃO","Escolha seu vínculo","O tipo de contrato altera sua resistência e remuneração.")
        descriptions = [
            ("estagiario","ESTAGIÁRIO","5 pontos de estabilidade · salário padrão"),
            ("efetivo","EFETIVO","4 pontos de estabilidade · adicional de 25%"),
            ("terceirizado","TERCEIRIZADO","3 pontos de estabilidade · adicional de 60%")
        ]
        for i,(key,label,desc) in enumerate(descriptions):
            y=220+i*112
            self.rect(80,y,944,y+88,self.PANEL,"#715b40",2)
            self.text(110,y+27,label,17,self.GOLD,"nw")
            self.text(110,y+58,desc,11,self.MUTED,"nw")
            self.button(735,y+20,170,"ASSINAR",lambda k=key,p=player:self.create_campaign(p,k),44)
        self.bind_clicks()

    def create_campaign(self, player, difficulty):
        self.game.start_campaign(player,difficulty)
        self.show_contract()

    def continue_campaign(self):
        state=self.game.state
        if not state:
            self.menu()
        elif state["status"]=="on_shift":
            self.show_task()
        elif state["status"]=="between_shifts":
            self.show_contract()
        else:
            self.show_ending()

    def show_contract(self):
        self.screen="briefing"
        mission=self.game.mission
        self.clear()
        self.rect(0,0,self.W,self.H,self.BG)
        self.header("ORDEM DE SERVIÇO  /  CONFIDENCIAL",mission["title"],mission["location"])
        self.rect(55,190,969,575,self.PANEL,"#8b6b42",2)
        self.text(90,225,"DESCRIÇÃO DO SERVIÇO",11,self.GOLD,"nw")
        self.text(90,260,mission["brief"],14,self.TEXT,"nw",820)
        self.text(90,330,"PROTOCOLO DE SEGURANÇA",11,self.GOLD,"nw")
        for i,rule in enumerate(mission["rules"]):
            self.text(105,365+i*34,f"{i+1:02d}  {rule}",11,self.TEXT,"nw",820)
        self.text(90,520,f"REMUNERAÇÃO: R$ {mission['pay']:,}".replace(",", "."),14,self.GOLD,"nw")
        self.text(90,548,f"FUNCIONÁRIO: {self.game.state['player']}   |   VÍNCULO: {DIFFICULTIES[self.game.state['difficulty']]['label']}",10,self.MUTED,"nw")
        self.button(690,600,260,"INICIAR EXPEDIENTE  [ENTER]",self.start_shift,44)
        self.bind_clicks()

    def start_shift(self):
        if self.game.state["status"]=="between_shifts":
            self.game.start_shift()
        self.show_task()

    def show_task(self):
        self.screen="task"
        mission=self.game.mission
        task=self.game.task
        state=self.game.state
        self.clear()
        self.rect(0,0,self.W,self.H,self.BG)
        self.header(f"AO VIVO  /  {mission['location']}",mission["title"],
                    f"FUNCIONÁRIO: {state['player']}     ESTABILIDADE: {state['sanity']}     FALHAS: {state['mistakes']}")
        # Mission scene frame and environmental details
        self.rect(55,180,969,570,"#101723","#66543e",2)
        self.rect(70,195,954,555,"#131e2b","#26384a",1)
        self.rect(95,220,929,535,"#0b111c")
        scene_id = {"loja_24h":"loja_24h", "edificio_9":"edificio_9", "cinema_vazio":"cinema_vazio"}.get(mission["id"])
        if scene_id:
            self.draw_scene(scene_id, 512, 390)
        self.text(512,250,"REGISTRO DE OCORRÊNCIA",10,self.GOLD)
        self.text(512,345,task["prompt"],17,self.TEXT,width=760)
        for i,choice in enumerate(task["choices"]):
            self.button(130,410+i*54,764,f"{i+1}.  {choice}",lambda n=i:self.choose(n),44)
        self.text(512,635,f"OCORRÊNCIA {state['task_index']+1}/3     [ESC] MENU",9,self.MUTED)
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
        self.rect(80,205,944,510,self.PANEL,"#8b6b42",2)
        color="#9bd1ad" if result["correct"] else "#e58d83"
        self.text(120,255,"✓" if result["correct"] else "!",34,color,"nw")
        self.text(180,265,result["message"],15,self.TEXT,"nw",700)
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
            self.button(650,535,230,"CONTINUAR",self.show_task,44)
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
        self.rect(100,220,924,520,self.PANEL,"#8b6b42",2)
        self.text(150,280,f"STATUS: {state.get('status','—').upper()}",18,self.GOLD,"nw")
        self.text(150,340,f"Saldo acumulado: R$ {state.get('cash',0):,}".replace(",", "."),15,self.TEXT,"nw")
        if completed:
            self.text(150,395,f"Locais concluídos: {len(state.get('completed', []))}/{len(MISSIONS)}",13,self.MUTED,"nw")
            self.text(150,435,"Seu expediente terminou. O arquivo permanece aberto.",12,self.MUTED,"nw")
        else:
            self.text(150,395,state.get("last_reveal", "A agência agradece seus serviços."),12,self.MUTED,"nw",700)
        self.button(650,555,230,"VOLTAR AO MENU",self.menu,44)
        self.bind_clicks()

def terminal():
    game=ShiftGame()
    print("=== TURNOS ZERO | AGÊNCIA DE SERVIÇOS EXTRAORDINÁRIOS ===")
    while True:
        if game.state and game.state["status"] == "campaign_completed":
            print("\\nCAMPANHA CONCLUÍDA — todos os contratos foram encerrados.")
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
            print("\n"+t["prompt"])
            for i,c in enumerate(t["choices"],1): print(i,"-",c)
            raw=input("Decisão (1-3): ").strip()
            if raw not in ("1","2","3"): continue
            result=game.act(int(raw)-1)
            print(result["message"])
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
