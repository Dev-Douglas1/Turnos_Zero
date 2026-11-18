"""Sistemas incrementais para O Último Segredo da Mansão.
Compatibilidade com saves legados: nunca descarta campos desconhecidos.
"""
from __future__ import annotations
import copy
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

PERFIS = {
    "historia": {"tempo": 2700, "penalidade_erro": 15, "custo_dica": 30, "tentativas": 5,
                 "descricao": "Mais tempo, dicas acessíveis e tolerância a erros."},
    "investigador": {"tempo": 1800, "penalidade_erro": 60, "custo_dica": 90, "tentativas": 3,
                     "descricao": "Equilíbrio entre dedução e pressão."},
    "pesadelo": {"tempo": 1500, "penalidade_erro": 90, "custo_dica": 120, "tentativas": 2,
                 "descricao": "Pouca assistência, pressão e consequências severas."},
}

def novo_estado_investigacao():
    return {"evidencias": [], "hipotese": None, "conclusao": None, "relacoes": []}

def migrar_estado(estado):
    """Migração em memória; não grava nem substitui o JSON original automaticamente."""
    if not isinstance(estado, dict):
        estado = {}
    novo = copy.deepcopy(estado)
    novo.setdefault("schema_version", 1)
    novo.setdefault("dificuldade", "investigador")
    novo.setdefault("tensao", 0)
    novo.setdefault("investigacao", novo_estado_investigacao())
    novo.setdefault("eventos", [])
    novo.setdefault("mecanismos", {})
    novo.setdefault("config_dificuldade_snapshot", copy.deepcopy(PERFIS[novo["dificuldade"]]))
    novo.setdefault("campanha", {})
    novo["schema_version"] = 2
    novo["dificuldade"] = novo["dificuldade"] if novo["dificuldade"] in PERFIS else "investigador"
    for campo, padrao in (("inventario", []), ("vistos", []), ("resolvidos", []),
                          ("tentativas", {}), ("conquistas", []), ("dicas", 0),
                          ("alerta", 0), ("tempo_restante", 1200), ("sala", 0)):
        novo.setdefault(campo, copy.deepcopy(padrao))
    return novo

def backup_jsons(pasta):
    """Cria backup único datado antes da primeira migração persistente."""
    pasta = Path(pasta)
    backup = pasta / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup.mkdir(parents=True, exist_ok=True)
    for nome in ("progresso.json", "historico.json", "enigmas.json"):
        origem = pasta / nome
        destino = backup / nome
        if origem.exists() and not destino.exists():
            shutil.copy2(origem, destino)
    return backup

def gerar_caso(seed):
    """Gera caso determinístico: mesma seed sempre produz as mesmas evidências."""
    import random
    rng = random.Random(seed)
    casos = [
        ("desaparecimento", "Helena Valença", "o mordomo", "desvio da herança"),
        ("testamento_falso", "Artur Valença", "a governanta", "falsificação do testamento"),
        ("incendio", "Cecília Valença", "o médico da família", "incêndio criminoso"),
        ("identidade_trocada", "Tomás Valença", "o advogado", "troca de identidade")
    ]
    tipo, vitima, culpado, motivo = rng.choice(casos)
    suspeitos = [culpado, "o jardineiro", "a governanta", "o advogado"]
    rng.shuffle(suspeitos)
    evidencias = [
        {"id":"ev_retrato","sala":"hall","objeto":"retrato","tipo":"documento",
         "titulo":"Data no retrato","fato":f"{vitima} está ligada ao ano do incidente.","entidades":[vitima]},
        {"id":"ev_livro","sala":"biblioteca","objeto":"livro","tipo":"registro",
         "titulo":"Registro da biblioteca","fato":f"O desaparecimento de {vitima} foi ocultado.","entidades":[vitima]},
        {"id":"ev_carta","sala":"escritorio","objeto":"carta","tipo":"documento",
         "titulo":"Carta rasgada","fato":"A cronologia oficial apresenta contradições.","entidades":[culpado]},
        {"id":"ev_registro","sala":"porao","objeto":"registro","tipo":"objeto",
         "titulo":"Registro do porão","fato":f"Há vestígios que contradizem a versão de {culpado}.","entidades":[culpado]},
        {"id":"ev_diario","sala":"camara","objeto":"diario","tipo":"testemunho",
         "titulo":"Diário final","fato":f"{culpado} encobriu {motivo}.","entidades":[culpado,vitima]}
    ]
    return {"id":tipo,"incidente":tipo,"vitima":vitima,"culpado":culpado,
            "motivo":motivo,"suspeitos":suspeitos,"evidencias":evidencias,
            "solucao":{"culpado":culpado,"motivo":motivo},
            "linha_tempo":[{"hora":"23:00","evento":"Último registro confirmado"},
                           {"hora":"23:47","evento":"Incidente na mansão"},
                           {"hora":"23:59","evento":"Relógio interrompido"}]}

def registrar_evidencia(estado, caso, chave):
    if not caso:
        return
    for ev in caso.get("evidencias", []):
        if f"{ev['sala']}:{ev['objeto']}" == chave:
            inv = estado.setdefault("investigacao", novo_estado_investigacao())
            if ev["id"] not in [x.get("id") for x in inv.setdefault("evidencias", [])]:
                inv["evidencias"].append(copy.deepcopy(ev))
            return

def avaliar_hipotese(estado, suspeito):
    caso = estado.get("campanha", {}).get("caso", {})
    evidencias = estado.get("investigacao", {}).get("evidencias", [])
    ids = {e.get("id") for e in evidencias}
    suficiente = {"ev_retrato", "ev_livro", "ev_diario"}.issubset(ids)
    correta = suspeito == caso.get("culpado")
    return {"correta": correta, "fundamentada": suficiente,
            "resultado": "verdade_comprovada" if correta and suficiente else
                         "acusacao_precipitada" if not correta else "inconclusiva"}

def eventos_disparados(estado):
    """Eventos narrativos determinísticos por marcos; não removem itens nem travam salas."""
    eventos = estado.setdefault("eventos", [])
    novos = []
    regras = [
        ("primeira_evidencia", len(estado.get("investigacao", {}).get("evidencias", [])) >= 1,
         "Um estalo ecoa no andar superior. A mansão percebeu sua presença."),
        ("tensao_alta", estado.get("tensao", 0) >= 30, "Uma sombra atravessa o limite da luz."),
        ("tres_evidencias", len(estado.get("investigacao", {}).get("evidencias", [])) >= 3,
         "O relógio da mansão volta a funcionar por alguns segundos.")
    ]
    for codigo, condicao, texto in regras:
        if condicao and codigo not in eventos:
            eventos.append(codigo)
            novos.append(texto)
    return novos
