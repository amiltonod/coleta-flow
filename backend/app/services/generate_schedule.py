from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
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

# Criamos o dicionário reverso totalmente em minúsculo para ignorar erros de digitação
DIAS_SEMANA_REVERSO = {v.lower(): k for k, v in DIAS_SEMANA.items()}


def ajustar_para_dia_util(data: date) -> date:
    while data.weekday() >= 5:
        data += timedelta(days=1)
    return data


def proxima_data_para_dia(dia_nome: str, segunda: date) -> date:
    nome_limpo = dia_nome.strip().lower()
    offset = DIAS_SEMANA_REVERSO.get(nome_limpo)
    
    # Se não for um dia válido (ex: texto "Por solicitação" jogado no campo errado), retorna None
    if offset is None:
        return None
        
    return segunda + timedelta(days=offset)


def ja_agendado_na_data(db: Session, codigo: str, data: date) -> bool:
    """Verifica duplicidade limpando espaços, tratando zeros à esquerda e isolando apenas a DATA."""
    cod_limpo = str(codigo).strip()
    # Cria uma variação sem zeros à esquerda se for numérico (ex: "015" vira "15")
    cod_alternativo = str(int(cod_limpo)) if cod_limpo.isdigit() else cod_limpo

    existente = db.query(Schedule).filter(
        or_(
            Schedule.codigo_cliente == cod_limpo,
            Schedule.codigo_cliente == cod_alternativo
        ),
        func.date(Schedule.data_coleta) == data  # func.date ignora componentes de hora/timestamp do banco
    ).first()
    
    return existente is not None


def gerar_programacao(db: Session) -> dict:
    """
    Gera a programação da próxima semana de forma blindada.
    """
    clientes = db.query(Client).all()

    if not clientes:
        return {"gerados": 0, "mensagem": "Nenhum cliente encontrado."}

    hoje = date.today()
    dias_ate_segunda = (7 - hoje.weekday()) % 7 or 7
    segunda = hoje + timedelta(days=dias_ate_segunda)
    dias_semana = [segunda + timedelta(days=i) for i in range(5)]

    gerados = 0
    ignorados = 0
    duplicados = 0
    solicitacao = 0

    for cliente in clientes:

        # ── BLINDAGEM 1: Checagem ultra-segura de "Por Solicitação" (com ou sem acento)
        obs_texto = (cliente.observacao or "").lower()
        dia_fixo_texto = (cliente.dia_fixo or "").lower()
        
        if "solicita" in obs_texto or "solicita" in dia_fixo_texto:
            solicitacao += 1
            continue

        # Cliente fixo — aceita múltiplos dias separados por vírgula
        if cliente.fixo and cliente.dia_fixo:
            dias_fixos = [d.strip() for d in cliente.dia_fixo.split(",")]

            for dia_nome in dias_fixos:
                data_coleta = proxima_data_para_dia(dia_nome, segunda)

                # Se o texto do dia for inválido, ignora para não agendar na segunda por erro
                if data_coleta is None:
                    continue

                if ja_agendado_na_data(db, cliente.codigo, data_coleta):
                    duplicados += 1
                    continue

                schedule = Schedule(
                    cliente=cliente.nome,
                    codigo_cliente=cliente.codigo,
                    unidade=cliente.unidade,
                    data_coleta=data_coleta,
                    dia_semana=dia_nome.strip().capitalize(),
                    status="Programado",
                    fixo=True,
                )
                db.add(schedule)
                gerados += 1

        # Cliente normal — ultima_coleta + frequencia_dias
        elif cliente.ultima_coleta and cliente.frequencia_dias:
            data_coleta = cliente.ultima_coleta + timedelta(
                days=cliente.frequencia_dias
            )
            data_coleta = ajustar_para_dia_util(data_coleta)
            dia_semana = DIAS_SEMANA.get(data_coleta.weekday(), "Segunda")

            if data_coleta not in dias_semana:
                ignorados += 1
                continue

            if ja_agendado_na_data(db, cliente.codigo, data_coleta):
                duplicados += 1
                continue

            schedule = Schedule(
                cliente=cliente.nome,
                codigo_cliente=cliente.codigo,
                unidade=cliente.unidade,
                data_coleta=data_coleta,
                dia_semana=dia_semana,
                status="Programado",
                fixo=False,
            )
            db.add(schedule)
            gerados += 1

        else:
            ignorados += 1

    db.commit()

    return {
        "gerados": gerados,
        "ignorados": ignorados,
        "duplicados": duplicados,
        "solicitacao": solicitacao,
        "mensagem": "Programação criada com sucesso!"
    }