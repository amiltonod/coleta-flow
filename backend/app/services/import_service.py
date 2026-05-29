import pandas as pd
from datetime import timedelta
from database import SessionLocal
from backend.app.models.cliente import Cliente
from backend.app.database import SessionLocal


def importar_clientes(file_path):

    df = pd.read_excel(file_path, engine="openpyxl")

    print(df.columns)

    db = SessionLocal()

    for index, row in df.iterrows():

        try:
            # ignora linhas vazias
            if pd.isna(row.iloc[0]):
                continue

            codigo = str(row.iloc[0]).strip()

            # evita duplicados
            cliente_existente = (
                db.query(Cliente)
                .filter(Cliente.codigo == codigo)
                .first()
            )

            if cliente_existente:
                continue

            nome = str(row.iloc[1]).strip()

            # pega data da coleta
            data_coleta = row.iloc[13]

            # valida data
            if pd.isna(data_coleta):
                continue

            data_coleta = pd.to_datetime(data_coleta)

            # gera próxima coleta
            proxima_coleta = data_coleta + timedelta(days=7)

            cliente = Cliente(
                codigo=codigo,
                nome=nome,
                ultima_coleta=data_coleta,
                proxima_coleta=proxima_coleta
            )

            db.add(cliente)

        except Exception as e:
            print(f"Erro na linha {index}: {e}")

    db.commit()
    db.close()