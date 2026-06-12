from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.app.database import Base, engine
from backend.app.models import client, schedule, controle  # ← adiciona controle
from backend.app.routes.clientes import router as clientes_router
import os
import backend.app.logging_config

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ColetaFlow", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

app.include_router(clientes_router)