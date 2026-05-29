from fastapi import FastAPI

from backend.app.database.database import engine, Base

from backend.app.models.client import Client
from backend.app.models.schedule import Schedule

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def home():
    return {"message": "ColetaFlow API Online"}