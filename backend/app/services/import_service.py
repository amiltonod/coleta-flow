import pandas as pd

from datetime import timedelta

from backend.app.database.database import SessionLocal

from backend.app.models.client import Client

def importar_clientes(file_path):

    df = pd.read_excel(
        file_path,
        engine="openpyxl",
        header=2
    )

    db = SessionLocal()

    for index, row in df.iterrows():

        try:

            codigo = str(row.iloc[0]) if pd.notna(row.iloc[0]) else None

            nome = str(row.iloc[1]) if pd.notna(row.iloc[1]) else None

            frequencia = None

            if pd.notna(row.iloc[3]):

                try:

                    frequencia = int(float(row.iloc[3]))

                except:

                    frequencia = None
            

            penultima = pd.to_datetime(
                row.iloc[5],
                errors="coerce"
            )

            ultima = pd.to_datetime(
                row.iloc[8],
                errors="coerce"
            )

            if pd.isna(penultima):
                penultima = None
            else:
                penultima = penultima.date()

            if pd.isna(ultima):
                ultima = None
            else:
                ultima = ultima.date()

            if not codigo or not nome:
                continue

            proxima = None

            if ultima is not pd.NaT and frequencia:

                proxima = ultima + timedelta(days=frequencia)

            cliente_existente = db.query(Client).filter(
                Client.codigo == codigo
            ).first()

            if cliente_existente:
                continue

            client = Client(
                codigo=codigo,
                nome=nome,
                frequencia_dias=frequencia,
                penultima_coleta=penultima,
                ultima_coleta=ultima,
                proxima_coleta=proxima
            )

            db.add(client)

        except Exception as e:

            print(f"Erro linha {index}: {e}")

    db.commit()

    db.close()