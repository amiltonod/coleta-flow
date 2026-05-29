import os
import shutil
from datetime import date, timedelta

from fastapi import APIRouter, Depends, File, UploadFile, Request
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
    """
    Retorna os clientes agrupados por dia da próxima semana.
    """
    hoje = date.today()
    # Próxima segunda-feira
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
            })

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
    """Atualiza um agendamento (usado ao editar na tela)."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        return {"erro": "Agendamento não encontrado"}
    if "cliente" in dados:
        schedule.cliente = dados["cliente"]
    if "unidade" in dados:
        schedule.unidade = dados["unidade"]
    if "status" in dados:
        schedule.status = dados["status"]
    db.commit()
    return {"mensagem": "Atualizado com sucesso"}