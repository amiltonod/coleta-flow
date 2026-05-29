import os
import shutil

from fastapi import APIRouter, Depends, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.client import Client
from backend.app.models.schedule import Schedule
from backend.app.services.import_service import importar_clientes
from backend.app.services.generate_schedule import gerar_programacao

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

router = APIRouter()

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Página principal: lista clientes e programação."""
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
    """Recebe planilha Excel e importa os clientes."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    resultado = importar_clientes(file_path, db)

    return {
        "mensagem": "Arquivo importado com sucesso!",
        "importados": resultado["importados"],
        "erros": resultado["erros"],
    }


@router.post("/gerar-programacao")
async def gerar(db: Session = Depends(get_db)):
    """Gera a programação de coletas para todos os clientes."""
    resultado = gerar_programacao(db)
    return resultado
