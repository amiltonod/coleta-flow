from fastapi import FastAPI
from backend.app.database import Base, engine
from backend.app.models.client import Client

Base.metadata.create_all(bind=engine)
from fastapi import Request
from fastapi import UploadFile
from fastapi import File

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import shutil
import os

from backend.app.services.import_service import importar_clientes

app = FastAPI()

templates = Jinja2Templates(directory="backend/app/templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request
        }
    )


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    os.makedirs("backend/app/uploads", exist_ok=True)

    file_path = f"backend/app/uploads/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    importar_clientes(file_path)

    return {
        "mensagem": "Arquivo importado com sucesso!"
    }