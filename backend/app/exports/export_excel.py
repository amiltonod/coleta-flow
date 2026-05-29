import pandas as pd

from backend.app.database.database import SessionLocal
from backend.app.models.schedule import Schedule

db = SessionLocal()

schedules = db.query(Schedule).all()

dados = []

for schedule in schedules:

    dados.append({
        "Cliente": schedule.cliente,
        "Código": schedule.codigo_cliente,
        "Data Coleta": schedule.data_coleta,
        "Dia Semana": schedule.dia_semana,
        "Status": schedule.status
    })

df = pd.DataFrame(dados)

df.to_excel(
    "programacao_coletas.xlsx",
    index=False
)

print("Excel exportado com sucesso!")

db.close()