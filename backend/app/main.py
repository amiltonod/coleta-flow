from fastapi import FastAPI

from backend.app.database.database import engine, Base
from backend.app.models.client import Client

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def home():
    return {"message": "ColetaFlow API Online"}