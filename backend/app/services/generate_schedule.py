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

DIAS_SEMANA_REVERSO = {v: k for k, v in DIAS_SEMANA.items()}


def ajustar_para_dia_util(data: date) -> date:
    """Se cair no sábado ou domingo, avança para segunda."""
    while data.weekday() >= 5:
        data += timedelta(days=1)
    return data


def proxima_data_para_dia(dia_nome: str, segunda: date) -> date:
    """
    Dado o nome do dia (ex: 'Terça') e a segunda-feira da semana,
    retorna a data correta daquele dia na mesma semana.
    """
    offset = DIAS_SEMANA_REVERSO.get(dia_nome, 0)
    return segunda + timedelta(days=offset)


def gerar_programacao(db: Session) -> dict:
    """
    Gera a programação da semana seguinte.
    Clientes fixos vão pro dia fixo.
    Clientes normais usam ultima_coleta + frequencia_dias.
    NÃO DUPLICA se já existir coleta pro cliente no mesmo dia.
    """
    clientes = db.query(Client).all()

    if not clientes:
        return {"gerados": 0, "mensagem": "Nenhum cliente encontrado no banco."}

    hoje = date.today()
    dias_ate_segunda = (7 - hoje.weekday()) % 7 or 7
    segunda = hoje + timedelta(days=dias_ate_segunda)

    gerados = 0
    ignorados = 0

    for cliente in clientes:

        # Cliente fixo — vai sempre pro dia fixo da semana
        if cliente.fixo and cliente.dia_fixo:
            data_coleta = proxima_data_para_dia(cliente.dia_fixo, segunda)
            dia_semana = cliente.dia_fixo

        # Cliente normal — calcula pela última coleta + frequência
        elif cliente.ultima_coleta and cliente.frequencia_dias:
            data_coleta = cliente.ultima_coleta + timedelta(days=cliente.frequencia_dias)
            data_coleta = ajustar_para_dia_util(data_coleta)
            dia_semana = DIAS_SEMANA.get(data_coleta.weekday(), "Segunda")

            # Se a data calculada não cair na próxima semana, ignora
            dias_semana_proxima = [segunda + timedelta(days=i) for i in range(5)]
            if data_coleta not in dias_semana_proxima:
                ignorados += 1
                continue

        else:
            ignorados += 1
            continue

        # ------------------------------------------------------------
        # TRAVA CONTRA DUPLICIDADE: Verifica se já existe agendamento
        # para este cliente na data calculada
        # ------------------------------------------------------------
        existe = db.query(Schedule).filter(
            Schedule.codigo_cliente == cliente.codigo,
            Schedule.data_coleta == data_coleta
        ).first()

        if existe:
            ignorados += 1
            continue  # Pula para o próximo cliente sem duplicar registro

        # Se passou pela trava, cria a nova coleta normalmente
        schedule = Schedule(
            cliente=cliente.nome,
            codigo_cliente=cliente.codigo,
            unidade=cliente.unidade,
            data_coleta=data_coleta,
            dia_semana=dia_semana,
            status="Programado",
            fixo=cliente.fixo,
        )

        db.add(schedule)
        gerados += 1

    db.commit()

    return {
        "gerados": gerados,
        "ignorados": ignorados,
        "mensagem": "Programação processada com sucesso!"
    }