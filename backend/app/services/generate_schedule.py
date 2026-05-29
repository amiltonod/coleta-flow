from datetime import date, timedelta
from sqlalchemy.orm import Session
from backend.app.models.client import Client
from backend.app.models.schedule import Schedule


DIAS_SEMANA = {
    0: "Segunda",
    1: "Terça",
    2: "Quarta",
    3: "Quinta",
    4: "Sexta",
    5: "Sábado",
    6: "Domingo",
}


def ajustar_para_dia_util(data: date) -> date:
    """Se cair no sábado ou domingo, avança para segunda."""
    while data.weekday() >= 5:
        data += timedelta(days=1)
    return data


def gerar_programacao(db: Session) -> dict:
    """
    Gera a programação usando: próxima coleta = última coleta + frequência de dias.
    Se não tiver última coleta ou frequência, ignora o cliente.
    Nunca agenda no sábado ou domingo.
    """
    clientes = db.query(Client).all()

    if not clientes:
        return {"gerados": 0, "mensagem": "Nenhum cliente encontrado no banco."}

    gerados = 0
    ignorados = 0

    for cliente in clientes:

        if not cliente.ultima_coleta or not cliente.frequencia_dias:
            ignorados += 1
            continue

        data_coleta = cliente.ultima_coleta + timedelta(days=cliente.frequencia_dias)
        data_coleta = ajustar_para_dia_util(data_coleta)
        dia_semana = DIAS_SEMANA.get(data_coleta.weekday(), "Segunda")

        schedule = Schedule(
            cliente=cliente.nome,
            codigo_cliente=cliente.codigo,
            unidade=cliente.unidade,
            data_coleta=data_coleta,
            dia_semana=dia_semana,
            status="Programado",
        )

        db.add(schedule)
        gerados += 1

    db.commit()

    return {
        "gerados": gerados,
        "ignorados": ignorados,
        "mensagem": "Programação criada com sucesso!"
    }