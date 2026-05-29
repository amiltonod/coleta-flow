import shutil

from fastapi import FastAPI
from fastapi import Request
from fastapi import UploadFile
from fastapi import File

from fastapi.templating import Jinja2Templates

from backend.database.database import Base
from backend.database.database import engine
from backend.database.database import SessionLocal

from backend.app.models.client import Client

from backend.app.services.import_service import importar_clientes


app = FastAPI()

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(
    directory="backend/app/templates"
)


@app.get("/")
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...)
):

    file_path = "./uploads/" + file.filename

    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(file.file, buffer)

    importar_clientes(file_path)

    db = SessionLocal()

    clientes = db.query(Client).all()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="schedule.html",
        context={
            "request": request,
            "clientes": clientes
        }
    )