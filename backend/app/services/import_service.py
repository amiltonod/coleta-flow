import pandas as pd

from backend.app.database import SessionLocal
from backend.app.models.client import Client


def importar_clientes(file_path):

    db = SessionLocal()

    df = pd.read_excel(file_path)

    print(df.columns)

    for index, row in df.iterrows():

        try:

            codigo = str(row.iloc[0]) if pd.notna(row.iloc[0]) else None
            nome = str(row.iloc[1]) if pd.notna(row.iloc[1]) else None

            if not codigo or not nome:
                continue

            cliente = Client(
                codigo=codigo,
                nome=nome
            )

            db.add(cliente)

        except Exception as e:
            print(f"Erro na linha {index}: {e}")

    db.commit()
    db.close()