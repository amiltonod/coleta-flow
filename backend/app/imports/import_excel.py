import pandas as pd

from backend.app.database import SessionLocal
from backend.app.models.client import Client

FILE_PATH = "coletas.xlsx"

# Ler Excel
df = pd.read_excel(FILE_PATH, engine="openpyxl")

# Conexão banco
db = SessionLocal()

# Percorrer linhas
for index, row in df.iterrows():

    codigo = str(row["Unnamed: 0"]) if pd.notna(row["Unnamed: 0"]) else None

    nome_completo = str(
        row["                      Planejamento das Coletas (Caixas para Trocas)"]
    ) if pd.notna(
        row["                      Planejamento das Coletas (Caixas para Trocas)"]
    ) else None

    observacao = str(row["Unnamed: 15"]) if pd.notna(row["Unnamed: 15"]) else None

    if not codigo or not nome_completo:
        continue

    partes = nome_completo.split(" - ")

    nome = partes[0] if len(partes) > 0 else None
    cidade = partes[1] if len(partes) > 1 else None
    unidade = partes[2] if len(partes) > 2 else None

    client = Client(
        codigo=codigo,
        nome=nome,
        cidade=cidade,
        unidade=unidade,
        observacao=observacao,
        frequencia_dias=None,
        dia_preferencial=None
    )

    db.add(client)

db.commit()

print("Importação concluída com sucesso!")

db.close()