from datetime import date, timedelta
from sqlalchemy.orm import Session
from backend.app.models.client import Client
from backend.app.models.schedule import Schedule
from backend.app.models.controle import Controle


def obter_segunda_da_semana(data: date) -> date:
    """Retorna a segunda-feira da semana de uma data."""
    return data - timedelta(days=data.weekday())


def fechar_semana(db: Session) -> dict:
    """
    Verifica se há semanas passadas não fechadas.
    Se houver, atualiza ultima_coleta de cada cliente
    com a última data agendada daquela semana.
    Não processa semanas já fechadas.
    """
    hoje = date.today()
    segunda_atual = obter_segunda_da_semana(hoje)
    sexta_semana_passada = segunda_atual - timedelta(days=3)  # sexta da semana anterior
    segunda_semana_passada = segunda_atual - timedelta(weeks=1)

    # Busca ou cria o registro de controle
    controle = db.query(Controle).first()
    if not controle:
        controle = Controle(ultima_semana_fechada=None)
        db.add(controle)
        db.commit()
        db.refresh(controle)

    # Verifica se a semana passada já foi fechada
    if controle.ultima_semana_fechada and \
       controle.ultima_semana_fechada >= segunda_semana_passada:
        return {"fechado": False, "mensagem": "Semana já fechada anteriormente"}

    # Só fecha se já passou a semana (hoje é segunda ou depois)
    if hoje < segunda_atual:
        return {"fechado": False, "mensagem": "Semana ainda não terminou"}

    # Busca todos os agendamentos da semana passada
    dias_semana_passada = [
        segunda_semana_passada + timedelta(days=i) for i in range(5)
    ]

    # Agrupa por cliente — pega a ÚLTIMA data agendada de cada um
    agendamentos = db.query(Schedule).filter(
        Schedule.data_coleta.in_(dias_semana_passada)
    ).all()

    clientes_atualizados = 0
    mapa_clientes = {}

    for ag in agendamentos:
        codigo = ag.codigo_cliente
        # Guarda a maior data (última coleta da semana)
        if codigo not in mapa_clientes:
            mapa_clientes[codigo] = ag.data_coleta
        else:
            if ag.data_coleta > mapa_clientes[codigo]:
                mapa_clientes[codigo] = ag.data_coleta

    # Atualiza ultima_coleta e recalcula proxima_coleta
    for codigo, data_coleta in mapa_clientes.items():
        cliente = db.query(Client).filter(Client.codigo == codigo).first()
        if not cliente:
            continue

        cliente.ultima_coleta = data_coleta

        # Recalcula proxima_coleta se tiver frequencia
        if cliente.frequencia_dias:
            from datetime import timedelta
            cliente.proxima_coleta = data_coleta + timedelta(
                days=cliente.frequencia_dias
            )

        clientes_atualizados += 1

    # Marca a semana como fechada
    controle.ultima_semana_fechada = segunda_semana_passada
    db.commit()

    return {
        "fechado": True,
        "semana": str(segunda_semana_passada),
        "clientes_atualizados": clientes_atualizados,
        "mensagem": f"Semana fechada. {clientes_atualizados} clientes atualizados."
    }