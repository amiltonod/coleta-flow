import pandas as pd
from sqlalchemy.orm import Session
from backend.app.models.client import Client


def importar_clientes(file_path: str, db: Session) -> dict:
    """
    Lê um arquivo Excel e importa os clientes para o banco.
    Se o cliente já existe (pelo código), atualiza os dados.
    Se não existe, insere. Nunca duplica.
    """
    df = pd.read_excel(file_path, engine="openpyxl", header=1)

    importados = 0
    atualizados = 0
    erros = []

    for index, row in df.iterrows():

        try:
            codigo = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
            nome_completo = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else None

            if not codigo or not nome_completo:
                continue

            partes = nome_completo.split(" - ")
            nome = partes[0] if len(partes) > 0 else nome_completo
            cidade = partes[1] if len(partes) > 1 else None
            unidade = partes[2] if len(partes) > 2 else None

            observacao = str(row.iloc[15]).strip() if len(row) > 15 and pd.notna(row.iloc[15]) else None

            # Frequência em dias
            frequencia_dias = int(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else None

            # Datas
            ultima_coleta = row.iloc[8] if len(row) > 8 and pd.notna(row.iloc[8]) else None
            proxima_coleta = row.iloc[12] if len(row) > 12 and pd.notna(row.iloc[12]) else None

            # Converte para date se vier como datetime
            if hasattr(ultima_coleta, 'date'):
                ultima_coleta = ultima_coleta.date()
            if hasattr(proxima_coleta, 'date'):
                proxima_coleta = proxima_coleta.date()

            # Busca se o cliente já existe pelo código
            cliente_existente = db.query(Client).filter(Client.codigo == codigo).first()

            if cliente_existente:
                cliente_existente.nome = nome
                cliente_existente.cidade = cidade
                cliente_existente.unidade = unidade
                cliente_existente.observacao = observacao
                cliente_existente.frequencia_dias = frequencia_dias
                cliente_existente.ultima_coleta = ultima_coleta
                cliente_existente.proxima_coleta = proxima_coleta
                atualizados += 1
            else:
                cliente = Client(
                    codigo=codigo,
                    nome=nome,
                    cidade=cidade,
                    unidade=unidade,
                    observacao=observacao,
                    frequencia_dias=frequencia_dias,
                    ultima_coleta=ultima_coleta,
                    proxima_coleta=proxima_coleta,
                )
                db.add(cliente)
                importados += 1

        except Exception as e:
            erros.append({"linha": index, "erro": str(e)})

    db.commit()

    return {
        "importados": importados,
        "atualizados": atualizados,
        "erros": erros
    }