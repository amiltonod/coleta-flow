import pandas as pd

from backend.app.database.database import SessionLocal
from backend.app.models.client import Client

FILE_PATH = "coletas.xlsx"

# Ler Excel
df = pd.read_excel(FILE_PATH, engine="openpyxl")

# Conexão banco
db = SessionLocal()

# Percorrer linhas
for index, row in df.iterrows():

    codigo = str(row["Unnamed: 0"]) if pd.notna(row["Unnamed: 0"]) else None

    nome = str(
        row["                      Planejamento das Coletas (Caixas para Trocas)"]
    ) if pd.notna(
        row["                      Planejamento das Coletas (Caixas para Trocas)"]
    ) else None

    observacao = str(row["Unnamed: 15"]) if pd.notna(row["Unnamed: 15"]) else None

    # Ignorar linhas vazias
    if not codigo or not nome:
        continue

    # Criar cliente
    client = Client(
        codigo=codigo,
        nome=nome,
        frequencia_dias=None
    )

    db.add(client)

# Salvar banco
db.commit()

print("Importação concluída com sucesso!")

db.close()