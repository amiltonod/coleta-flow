from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.app.database.database import Base, SessionLocal, engine

from backend.app.models.client import Client
from backend.app.models.schedule import Schedule

Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="backend/app/templates")

app.mount(
    "/static",
    StaticFiles(directory="backend/app/static"),
    name="static"
)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    db = SessionLocal()

    clientes = db.query(Client).all()
    schedules = db.query(Schedule).all()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "clientes": clientes,
            "schedules": schedules
        }
    )