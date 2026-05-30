import os
import shutil
from datetime import date, timedelta

from fastapi import APIRouter, Depends, File, UploadFile, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.client import Client
from backend.app.models.schedule import Schedule
from backend.app.services.import_service import importar_clientes
from backend.app.services.generate_schedule import gerar_programacao, ajustar_para_dia_util

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

router = APIRouter()

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

DIAS_SEMANA = {
    0: "Segunda",
    1: "Terça",
    2: "Quarta",
    3: "Quinta",
    4: "Sexta",
    5: "Sábado",
    6: "Domingo"
}


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    clientes = db.query(Client).all()
    schedules = db.query(Schedule).all()
    return templates.TemplateResponse(
        name="index.html",
        request=request,
        context={
            "clientes": clientes,
            "schedules": schedules,
        }
    )


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    resultado = importar_clientes(file_path, db)
    return {
        "mensagem": "Arquivo importado com sucesso!",
        "importados": resultado["importados"],
        "atualizados": resultado["atualizados"],
        "erros": resultado["erros"],
    }


@router.post("/gerar-programacao")
async def gerar(db: Session = Depends(get_db)):
    resultado = gerar_programacao(db)
    return resultado


@router.get("/programacao-semana")
async def programacao_semana(db: Session = Depends(get_db)):
    hoje = date.today()
    dias_ate_segunda = (7 - hoje.weekday()) % 7 or 7
    segunda = hoje + timedelta(days=dias_ate_segunda)
    dias_semana = [segunda + timedelta(days=i) for i in range(5)]

    resultado = {}
    for dia in dias_semana:
        resultado[dia.isoformat()] = []

    schedules = db.query(Schedule).all()
    for s in schedules:
        if s.data_coleta and s.data_coleta in dias_semana:
            resultado[s.data_coleta.isoformat()].append({
                "id": s.id,
                "codigo": s.codigo_cliente,
                "cliente": s.cliente,
                "unidade": s.unidade or "",
                "status": s.status,
                "fixo": s.fixo or False,
            })

    # Ordena: fixos no topo de cada dia
    for dia in resultado:
        resultado[dia].sort(key=lambda x: (not x["fixo"], x["cliente"]))

    return {
        "dias": [d.isoformat() for d in dias_semana],
        "programacao": resultado,
    }

@router.put("/programacao/{schedule_id}")
async def atualizar_schedule(
    schedule_id: int,
    dados: dict,
    db: Session = Depends(get_db)
):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        return {"erro": "Agendamento não encontrado"}

    if "data_coleta" in dados:
        nova_data = date.fromisoformat(dados["data_coleta"])
        schedule.data_coleta = nova_data
        schedule.dia_semana = DIAS_SEMANA.get(nova_data.weekday(), "")

    if "cliente" in dados:
        schedule.cliente = dados["cliente"]
    if "unidade" in dados:
        schedule.unidade = dados["unidade"]
    if "status" in dados:
        schedule.status = dados["status"]

    db.commit()
    return {"mensagem": "Atualizado com sucesso"}


@router.delete("/programacao/{schedule_id}")
async def deletar_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """Remove um agendamento da semana."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        return {"erro": "Agendamento não encontrado"}
    db.delete(schedule)
    db.commit()
    return {"mensagem": "Agendamento removido com sucesso"}

@router.put("/clientes/{cliente_id}/fixar")
async def fixar_cliente(
    cliente_id: int,
    dados: dict,
    db: Session = Depends(get_db)
):
    """
    Fixa ou desfixa um cliente em um dia da semana.
    Recebe: fixo (bool), dia_fixo (str)
    """
    cliente = db.query(Client).filter(Client.id == cliente_id).first()
    if not cliente:
        return {"erro": "Cliente não encontrado"}

    cliente.fixo = dados.get("fixo", False)
    cliente.dia_fixo = dados.get("dia_fixo", None)

    db.commit()
    return {"mensagem": "Cliente atualizado com sucesso"}

@router.get("/clientes/buscar")
async def buscar_clientes(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """
    Busca clientes por código ou nome.
    O % é o coringa do SQL — busca qualquer texto que contenha q.
    """
    termo = f"%{q}%"
    clientes = db.query(Client).filter(
        (Client.codigo.ilike(termo)) | (Client.nome.ilike(termo))
    ).limit(10).all()

    return [
        {
            "id": c.id,
            "codigo": c.codigo,
            "nome": c.nome,
            "unidade": c.unidade or "",
            "cidade": c.cidade or "",
            "frequencia_dias": c.frequencia_dias,
            "ultima_coleta": c.ultima_coleta.isoformat() if c.ultima_coleta else None,
        }
        for c in clientes
    ]


@router.get("/clientes/{cliente_id}")
async def get_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """Retorna os dados completos de um cliente pelo id."""
    cliente = db.query(Client).filter(Client.id == cliente_id).first()
    if not cliente:
        return {"erro": "Cliente não encontrado"}
    return {
        "id": cliente.id,
        "codigo": cliente.codigo,
        "nome": cliente.nome,
        "cidade": cliente.cidade or "",
        "unidade": cliente.unidade or "",
        "frequencia_dias": cliente.frequencia_dias,
        "observacao": cliente.observacao or "",
        "ultima_coleta": cliente.ultima_coleta.isoformat() if cliente.ultima_coleta else None,
    }


@router.put("/clientes/{cliente_id}")
async def atualizar_cliente(
    cliente_id: int,
    dados: dict,
    db: Session = Depends(get_db)
):
    """Atualiza o cadastro do cliente."""
    cliente = db.query(Client).filter(Client.id == cliente_id).first()
    if not cliente:
        return {"erro": "Cliente não encontrado"}

    if "nome" in dados:
        cliente.nome = dados["nome"]
    if "cidade" in dados:
        cliente.cidade = dados["cidade"]
    if "unidade" in dados:
        cliente.unidade = dados["unidade"]
    if "frequencia_dias" in dados:
        cliente.frequencia_dias = dados["frequencia_dias"]
    if "observacao" in dados:
        cliente.observacao = dados["observacao"]

    db.commit()
    return {"mensagem": "Cliente atualizado com sucesso"}


@router.post("/programacao/adicionar")
async def adicionar_coleta(
    dados: dict,
    db: Session = Depends(get_db)
):
    """
    Adiciona uma coleta manualmente na grade.
    Recebe: codigo_cliente, data_coleta
    """
    codigo = dados.get("codigo_cliente")
    data_str = dados.get("data_coleta")

    if not codigo or not data_str:
        return {"erro": "Código e data são obrigatórios"}

    cliente = db.query(Client).filter(Client.codigo == codigo).first()
    if not cliente:
        return {"erro": "Cliente não encontrado"}

    data_coleta = date.fromisoformat(data_str)
    dia_semana = DIAS_SEMANA.get(data_coleta.weekday(), "")

    schedule = Schedule(
        cliente=cliente.nome,
        codigo_cliente=cliente.codigo,
        unidade=cliente.unidade,
        data_coleta=data_coleta,
        dia_semana=dia_semana,
        status="Programado",
    )
    db.add(schedule)
    db.commit()

    return {"mensagem": "Coleta adicionada com sucesso"}