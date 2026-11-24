"""Editor visual das camadas de cenário de Turnos Zero.

Execute: python tools/editor_cenas.py
Requer Pillow apenas para pré-visualizar/redimensionar sprites no editor.
O jogo continua sem depender de Pillow.
"""
from __future__ import annotations
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import shutil
from PIL import Image, ImageOps, ImageTk

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "dados" / "objetos_cenas.json"
SCENE_CONFIG = ROOT / "dados" / "cenas.json"
SPRITES = ROOT / "assets" / "objetos"
W, H = 834, 315

class SceneEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("TURNOS ZERO | Editor de cenários")
        self.root.geometry("1180x650")
        self.data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.scene_catalog = json.loads(SCENE_CONFIG.read_text(encoding="utf-8"))["scenes"]
        self.backgrounds = {item["id"]: ROOT / item["background"] for item in self.scene_catalog}
        self.scene_id = next(iter(self.data["scenes"]))
        self.selected = None
        self.drag_origin = None
        self.photos = {}
        self.tk_images = []
        self.background_photo = None
        self._build()
        self.render()

    def _build(self):
        left = ttk.Frame(self.root, padding=10)
        left.pack(side="left", fill="y")
        ttk.Label(left, text="MISSÃO").pack(anchor="w")
        self.scene_var = tk.StringVar(value=self.scene_id)
        self.scene_box = ttk.Combobox(left, textvariable=self.scene_var,
            values=list(self.data["scenes"]), state="readonly", width=27)
        self.scene_box.pack(fill="x", pady=(2, 12))
        self.scene_box.bind("<<ComboboxSelected>>", self.change_scene)
        ttk.Label(left, text="OBJETOS / CAMADAS").pack(anchor="w")
        self.object_list = tk.Listbox(left, width=31, height=19, exportselection=False)
        self.object_list.pack(fill="both", expand=True, pady=4)
        self.object_list.bind("<<ListboxSelect>>", self.select_from_list)
        self.visible_btn = ttk.Button(left, text="Mostrar / ocultar", command=self.toggle_visible)
        self.visible_btn.pack(fill="x", pady=3)
        self.front_btn = ttk.Button(left, text="Trazer para frente", command=lambda: self.change_z(1))
        self.front_btn.pack(fill="x", pady=3)
        self.back_btn = ttk.Button(left, text="Enviar para trás", command=lambda: self.change_z(-1))
        self.back_btn.pack(fill="x", pady=3)
        self.scale_up_btn = ttk.Button(left, text="Aumentar 10%", command=lambda: self.scale(1.1))
        self.scale_up_btn.pack(fill="x", pady=3)
        self.scale_down_btn = ttk.Button(left, text="Diminuir 10%", command=lambda: self.scale(.9))
        self.scale_down_btn.pack(fill="x", pady=3)
        ttk.Button(left, text="Salvar alterações", command=self.save).pack(fill="x", pady=(12, 3))
        ttk.Label(left, text="Arraste objetos no cenário.\nSetas movem 1%; Shift+seta move 5%.",
                  justify="left").pack(anchor="w", pady=8)

        self.canvas = tk.Canvas(self.root, width=W, height=H, bg="#080d14",
                                highlightthickness=1, highlightbackground="#9a7848")
        self.canvas.pack(side="left", padx=18, pady=40, anchor="n")
        self.canvas.bind("<Button-1>", self.select_at)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.root.bind("<Up>", lambda e: self.nudge(0, -.01))
        self.root.bind("<Down>", lambda e: self.nudge(0, .01))
        self.root.bind("<Left>", lambda e: self.nudge(-.01, 0))
        self.root.bind("<Right>", lambda e: self.nudge(.01, 0))
        self.root.bind("<Shift-Up>", lambda e: self.nudge(0, -.05))
        self.root.bind("<Shift-Down>", lambda e: self.nudge(0, .05))
        self.root.bind("<Shift-Left>", lambda e: self.nudge(-.05, 0))
        self.root.bind("<Shift-Right>", lambda e: self.nudge(.05, 0))

    @property
    def scene(self):
        return self.data["scenes"][self.scene_id]

    def change_scene(self, _event=None):
        self.scene_id = self.scene_var.get()
        self.selected = None
        self.render()

    def select_from_list(self, _event=None):
        selection = self.object_list.curselection()
        if selection:
            self.selected = self.scene["objects"][selection[0]]["id"]
            self.render()

    def select_at(self, event):
        for obj in sorted(self.scene["objects"], key=lambda x: x.get("z", 0), reverse=True):
            if not obj.get("visible", True):
                continue
            x1, y1 = obj["x"]*W, obj["y"]*H
            x2, y2 = (obj["x"]+obj["w"])*W, (obj["y"]+obj["h"])*H
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.selected = obj["id"]
                self.drag_origin = (event.x, event.y, obj["x"], obj["y"])
                self.render()
                return
        self.selected = None
        self.render()

    def drag(self, event):
        if not self.selected or not self.drag_origin:
            return
        ox, oy, x, y = self.drag_origin
        obj = self.get_selected()
        obj["x"] = min(1-obj["w"], max(0, x+(event.x-ox)/W))
        obj["y"] = min(1-obj["h"], max(0, y+(event.y-oy)/H))
        self.render()

    def get_selected(self):
        return next((o for o in self.scene["objects"] if o["id"] == self.selected), None)

    def nudge(self, dx, dy):
        obj = self.get_selected()
        if obj:
            obj["x"] = min(1-obj["w"], max(0, obj["x"]+dx))
            obj["y"] = min(1-obj["h"], max(0, obj["y"]+dy))
            self.render()

    def toggle_visible(self):
        obj = self.get_selected()
        if obj:
            obj["visible"] = not obj.get("visible", True)
            self.render()

    def change_z(self, delta):
        obj = self.get_selected()
        if obj:
            obj["z"] = obj.get("z", 0) + delta
            self.render()

    def replace_asset(self):
        obj = self.get_selected()
        if not obj:
            messagebox.showwarning("Editor de cenários", "Selecione um objeto antes de trocar a imagem.")
            return
        selected = filedialog.askopenfilename(
            title="Selecionar imagem do objeto",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp *.bmp"), ("Todos os arquivos", "*.*")]
        )
        if not selected:
            return
        try:
            with Image.open(selected) as source:
                image = source.convert("RGBA")
                filename = f"{obj['id']}_custom.png"
                destination = SPRITES / filename
                image.save(destination, format="PNG", optimize=True)
            obj["asset"] = filename
            self.render()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Editor de cenários", f"Não foi possível importar a imagem: {exc}")

    def scale(self, factor):
        obj = self.get_selected()
        if obj:
            obj["w"] = min(.95, max(.04, obj["w"]*factor))
            obj["h"] = min(.98, max(.04, obj["h"]*factor))
            self.render()

    def render(self):
        self.canvas.delete("all")
        background_path = self.backgrounds.get(self.scene_id)
        self.background_photo = None
        if background_path and background_path.is_file():
            with Image.open(background_path) as source:
                background = source.convert("RGBA").resize(
                    (W, H), Image.Resampling.LANCZOS
                )
            self.background_photo = ImageTk.PhotoImage(background)
            self.canvas.create_image(W/2, H/2, image=self.background_photo)
        else:
            bg = self.scene.get("backdrop", {})
            self.canvas.create_rectangle(0, 0, W, H, fill=bg.get("wall", "#101923"), outline="")
            self.canvas.create_rectangle(0, H*.72, W, H, fill=bg.get("floor", "#070b12"), outline="")

        self.object_list.delete(0, "end")
        self.tk_images = []
        for obj in sorted(self.scene["objects"], key=lambda x: x.get("z", 0)):
            visible = obj.get("visible", True)
            self.object_list.insert("end", ("● " if visible else "○ ") + obj["label"])
            if not visible:
                continue
            path = SPRITES / obj["asset"]
            if not path.is_file():
                continue
            box = (max(1, int(obj["w"]*W)), max(1, int(obj["h"]*H)))
            with Image.open(path) as source:
                image = ImageOps.contain(
                    source.convert("RGBA"), box, method=Image.Resampling.LANCZOS
                )
            photo = ImageTk.PhotoImage(image)
            self.tk_images.append(photo)
            x = (obj["x"]+obj["w"]/2)*W
            y = (obj["y"]+obj["h"]/2)*H
            self.canvas.create_image(x, y, image=photo, tags=("object", obj["id"]))
            if obj["id"] == self.selected:
                self.canvas.create_rectangle(obj["x"]*W, obj["y"]*H,
                    (obj["x"]+obj["w"])*W, (obj["y"]+obj["h"])*H,
                    outline="#f2c46e", width=2, dash=(5, 3))
        for i, obj in enumerate(self.scene["objects"]):
            if obj["id"] == self.selected:
                self.object_list.selection_set(i)
                self.object_list.see(i)
                break

    def save(self):
        MANIFEST.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        messagebox.showinfo("Turnos Zero", "Camadas salvas em dados/objetos_cenas.json")

if __name__ == "__main__":
    root = tk.Tk()
    try:
        SceneEditor(root)
        root.mainloop()
    except Exception as exc:
        messagebox.showerror("Editor de cenários", str(exc))
