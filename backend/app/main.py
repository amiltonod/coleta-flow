from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.app.database import Base, engine
from backend.app.models import client, schedule
from backend.app.routes.clientes import router as clientes_router
import os

# Cria as tabelas no banco se não existirem
Base.metadata.create_all(bind=engine)

# Cria o app PRIMEIRO
app = FastAPI(title="ColetaFlow", version="1.0.0")

# Depois monta o static
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Registra as rotas
app.include_router(clientes_router)