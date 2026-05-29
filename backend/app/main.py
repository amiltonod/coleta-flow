from fastapi import FastAPI
from backend.app.database import Base, engine
from backend.app.models import client, schedule  # garante que os models são registrados
from backend.app.routes.clientes import router as clientes_router

# Cria as tabelas no banco se não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ColetaFlow", version="1.0.0")

# Registra as rotas
app.include_router(clientes_router)
