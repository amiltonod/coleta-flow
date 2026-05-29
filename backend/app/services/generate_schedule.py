from datetime import date, timedelta

from backend.app.database import SessionLocal
from backend.app.models.client import Client
from backend.app.models.schedule import Schedule

db = SessionLocal()

clientes = db.query(Client).all()

data_inicial = date.today()

for index, cliente in enumerate(clientes):

    data_coleta = data_inicial + timedelta(days=index % 5)

    dias_semana = {
        0: "Segunda",
        1: "Terça",
        2: "Quarta",
        3: "Quinta",
        4: "Sexta",
        5: "Sábado",
        6: "Domingo"
    }

    dia_semana = dias_semana.get(data_coleta.weekday(), "Segunda")

    schedule = Schedule(
        cliente=cliente.nome,
        codigo_cliente=cliente.codigo,
        data_coleta=data_coleta,
        dia_semana=dia_semana,
        status="Programado"
    )

    db.add(schedule)

db.commit()

print("Programação criada com sucesso!")

db.close()
